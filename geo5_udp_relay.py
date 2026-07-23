# -*- coding: utf-8 -*-
"""
Relay UDP GEO5/RGP: recibe mensajes GEO5, reemplaza fecha/hora GPS por UTC actual,
recalcula checksum y reenvía según REENVIOS_CONFIG_UDP.txt.

Proceso separado del servidor TCP TQ (tq_server_rpg.py).
Logs en carpeta logsUDP/.
"""

from __future__ import annotations

import argparse
import logging
import os
import socket
import sys
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

import protocolo
from reenvios_config import ForwardingRule, append_reenvio_log, load_reenvios_config, normalize_equipo_key

LOG_DIR = "logsUDP"
DEFAULT_LISTEN_PORT = 6003
DEFAULT_CONFIG_NAME = "REENVIOS_CONFIG_UDP.txt"
# Destinos generales GEO5 (omitidos si hay SERVICIO en el CSV del relay)
DEFAULT_GENERAL_DESTINATIONS = (
    ("179.43.115.190", 7007),
    ("34.95.160.245", 5032),
)


def _ensure_log_dir(log_dir: str = LOG_DIR) -> None:
    d = (log_dir or LOG_DIR).strip() or LOG_DIR
    if not os.path.exists(d):
        os.makedirs(d)


def _daily_log_path(log_dir: str = LOG_DIR) -> str:
    _ensure_log_dir(log_dir)
    return os.path.join(log_dir, f"LOG_{datetime.now().strftime('%d%m%y')}.txt")


def _append_line(log_dir: str, line: str) -> None:
    try:
        path = _daily_log_path(log_dir)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _format_fecha_hora() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def guardar_log_packet(
    log_dir: str,
    direction: str,
    transport: str,
    ip: str,
    port,
    payload: str,
    device_id: str = "",
) -> None:
    """Log de paquetes en logsUDP/LOG_DDMMYY.txt (mismo estilo que funciones.guardarLogPacket)."""
    arrow = direction if direction in ("<-", "->") else "->"
    parts = [p for p in (transport, (ip or "").strip(), str(port).strip() if port is not None else "") if p]
    dev = (device_id or "").strip()
    if dev:
        parts.append(dev)
    meta = ", ".join(parts)
    p = (payload or "")[:200]
    if len(payload or "") > 200:
        p = p + "...(trunc)"
    if meta:
        _append_line(log_dir, f"{_format_fecha_hora()}: {arrow} [{meta}] {p}")
    else:
        _append_line(log_dir, f"{_format_fecha_hora()}: {arrow} {p}")


def _equipo_5_digitos(device_id: str) -> str:
    return normalize_equipo_key(device_id) or ""


def _utc_timestamp_geo5() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    return now.strftime("%d%m%y"), now.strftime("%H%M%S")


def _normalize_geo5_message(raw: bytes) -> str:
    text = raw.decode("ascii", errors="ignore").strip()
    if text.startswith(">") and not text.startswith(">RGP") and "RGP" in text[:8]:
        idx = text.find(">RGP")
        if idx >= 0:
            text = text[idx:]
    return text


class Geo5UdpRelayServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = DEFAULT_LISTEN_PORT,
        config_path: Optional[str] = None,
        reload_interval_seconds: int = 60,
        log_dir: str = LOG_DIR,
        general_destinations: Optional[List[tuple]] = None,
    ):
        self.host = host
        self.port = int(port)
        self.log_dir = log_dir
        if general_destinations is None:
            self.general_destinations = list(DEFAULT_GENERAL_DESTINATIONS)
        else:
            self.general_destinations = [
                (str(h).strip(), int(p))
                for h, p in general_destinations
                if str(h).strip() and int(p)
            ]
        self.reload_interval_seconds = int(reload_interval_seconds)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = (
            config_path if config_path is not None else os.path.join(base_dir, DEFAULT_CONFIG_NAME)
        )
        self._config_lock = threading.RLock()
        self._rules_by_device: Dict[str, List[ForwardingRule]] = {}
        self._config_last_mtime: Optional[float] = None
        self._reload_stop = threading.Event()
        self._reload_thread: Optional[threading.Thread] = None
        self._sock: Optional[socket.socket] = None
        self.running = False
        self.message_count = 0
        self.start_time: Optional[datetime] = None
        self.logger = self._setup_logging()

        rules, warnings = load_reenvios_config(self.config_path)
        self._rules_by_device = rules
        for w in warnings:
            self.logger.warning(w)
        try:
            self._config_last_mtime = os.path.getmtime(self.config_path)
        except Exception:
            self._config_last_mtime = None

    def _setup_logging(self) -> logging.Logger:
        _ensure_log_dir(self.log_dir)
        logger = logging.getLogger("Geo5UdpRelay")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(fmt)
            logger.addHandler(sh)
            log_file = os.path.join(self.log_dir, f"Relay_{datetime.now().strftime('%Y%m%d')}.log")
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        return logger

    def _rules_for(self, equipo_5: str) -> List[ForwardingRule]:
        if not equipo_5:
            return []
        with self._config_lock:
            return list(self._rules_by_device.get(equipo_5, []))

    def reload_config_if_changed(self, force: bool = False) -> bool:
        try:
            mtime = os.path.getmtime(self.config_path)
        except Exception:
            mtime = None

        if not force and mtime is not None and self._config_last_mtime is not None:
            if mtime <= self._config_last_mtime:
                return False

        by_device, warnings = load_reenvios_config(self.config_path)
        fatal_markers = ("Reenvíos: error leyendo", "Reenvíos: no se encontró el archivo")
        fatal = any((w or "").startswith(fatal_markers) for w in warnings)
        if fatal:
            for w in warnings:
                self.logger.warning(w)
            self.logger.warning("Reenvíos UDP: se mantiene la configuración anterior.")
            return False

        with self._config_lock:
            self._rules_by_device = by_device
            self._config_last_mtime = mtime

        for w in warnings:
            self.logger.warning(w)
        n_rules = sum(len(v) for v in by_device.values())
        self.logger.info(
            f"Reenvíos UDP: reglas recargadas ({n_rules} reglas, {len(by_device)} equipos) "
            f"desde {self.config_path}"
        )
        return True

    def _reload_loop(self) -> None:
        while not self._reload_stop.is_set():
            if self.running:
                try:
                    self.reload_config_if_changed(force=False)
                except Exception as e:
                    self.logger.error(f"Reenvíos UDP: error recargando configuración: {e}")
            if self._reload_stop.wait(self.reload_interval_seconds):
                break

    def _start_reload_thread(self) -> None:
        if self.reload_interval_seconds <= 0:
            return
        self._reload_stop = threading.Event()
        self._reload_thread = threading.Thread(target=self._reload_loop, daemon=True)
        self._reload_thread.start()
        self.logger.info(
            f"Reenvíos UDP: recarga automática cada {self.reload_interval_seconds}s ({self.config_path})"
        )

    def _stop_reload_thread(self) -> None:
        self._reload_stop.set()
        if self._reload_thread and self._reload_thread.is_alive():
            self._reload_thread.join(timeout=2.0)

    def _send_one_udp(
        self,
        message: str,
        dest_ip: str,
        dest_port: int,
        tipo: str,
        cliente: str,
        dev_log: str,
    ) -> bool:
        payload_b = message.encode("utf-8")
        try:
            guardar_log_packet(self.log_dir, "->", "UDP", dest_ip, dest_port, message, dev_log)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(payload_b, (dest_ip, dest_port))
            append_reenvio_log(
                dev_log,
                tipo,
                dest_ip,
                dest_port,
                "UDP",
                "GEO5",
                cliente,
                message,
                log_dir=self.log_dir,
            )
            return True
        except Exception as e:
            self.logger.error(f"Error reenvío UDP GEO5 a {dest_ip}:{dest_port}: {e}")
            return False

    def _forward_geo5(self, message: str, device_id: str) -> int:
        """
        Reenvía el GEO5 ajustado:
          - destinos generales 179.43.115.190:7007 y 34.95.160.245:5032 si no hay SERVICIO
          - más todas las filas CSV UDP/GEO5 del equipo
        """
        dev5 = _equipo_5_digitos(device_id)
        dev_log = dev5 or device_id
        rules = self._rules_for(dev5)
        has_servicio = any(r.tipo == "SERVICIO" for r in rules)

        sent = 0
        if not has_servicio:
            for g_host, g_port in self.general_destinations:
                if self._send_one_udp(
                    message, g_host, g_port, "GENERAL", "GENERAL", dev_log
                ):
                    sent += 1

        for rule in rules:
            if rule.protocolo_gps != "GEO5":
                continue
            if rule.transporte != "UDP":
                self.logger.warning(
                    f"Reenvíos UDP: regla línea {rule.line_no} ignorada (solo UDP GEO5 en este relay)."
                )
                continue
            if self._send_one_udp(
                message, rule.ip, rule.port, rule.tipo, rule.cliente, dev_log
            ):
                sent += 1
        return sent

    def process_datagram(self, data: bytes, src_ip: str, src_port: int) -> None:
        self.message_count += 1
        message = _normalize_geo5_message(data)
        if not message.startswith(">RGP") or not message.endswith("<"):
            self.logger.warning(f"Paquete descartado (no GEO5 RGP) desde {src_ip}:{src_port}")
            return

        if not protocolo.geo5_verify_checksum(message):
            self.logger.warning(
                f"Checksum GEO5 inválido desde {src_ip}:{src_port}; se procesa igualmente."
            )

        device_id = protocolo.geo5_extract_device_id(message)
        dev_log = _equipo_5_digitos(device_id) or device_id or "?"

        guardar_log_packet(
            self.log_dir, "<-", "UDP", src_ip, src_port, message, dev_log
        )

        ddmmyy, hhmmss = _utc_timestamp_geo5()
        adjusted = protocolo.geo5_replace_datetime_and_recompute_checksum(message, ddmmyy, hhmmss)
        if not adjusted:
            self.logger.warning(f"No se pudo ajustar fecha/hora GEO5 (equipo {dev_log})")
            return

        n = self._forward_geo5(adjusted, device_id)
        if n == 0:
            self.logger.info(
                f"Mensaje de {dev_log} sin destinos "
                f"(SERVICIO o sin general/CSV en {self.config_path})"
            )

    def start(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self.running = True
        self.start_time = datetime.now()
        self._start_reload_thread()

        n_rules = sum(len(v) for v in self._rules_by_device.values())
        self.logger.info(f"Relay GEO5 UDP escuchando en {self.host}:{self.port}")
        self.logger.info(f"Config: {self.config_path} ({n_rules} reglas)")
        for g_host, g_port in self.general_destinations:
            self.logger.info(
                f"UDP general GEO5 a {g_host}:{g_port} (omitido si SERVICIO)"
            )
        self.logger.info(f"Logs: {self.log_dir}/")
        print(f"Relay GEO5 UDP en {self.host}:{self.port} (logs en {self.log_dir}/)")

        while self.running:
            try:
                data, addr = self._sock.recvfrom(65535)
                try:
                    self.process_datagram(data, addr[0], addr[1])
                except Exception as e:
                    self.logger.error(f"Error procesando datagrama desde {addr}: {e}")
            except OSError:
                if self.running:
                    self.logger.error("Error en socket UDP")
                break

    def stop(self) -> None:
        self.running = False
        self._stop_reload_thread()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        self.logger.info("Relay GEO5 UDP detenido")


def main() -> None:
    parser = argparse.ArgumentParser(description="Relay UDP GEO5/RGP con reenvío configurable")
    parser.add_argument("--host", default="0.0.0.0", help="Interfaz de escucha (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=DEFAULT_LISTEN_PORT, help="Puerto UDP (default 6003)")
    parser.add_argument(
        "--config",
        default=None,
        help=f"Ruta a REENVIOS_CONFIG_UDP.txt (default: junto al script, {DEFAULT_CONFIG_NAME})",
    )
    parser.add_argument(
        "--reload-interval",
        type=int,
        default=60,
        help="Segundos entre recargas del CSV (0 = desactivar)",
    )
    parser.add_argument("--log-dir", default=LOG_DIR, help=f"Carpeta de logs (default {LOG_DIR})")
    parser.add_argument("--daemon", action="store_true", help="Modo daemon (sin prompts)")
    args = parser.parse_args()

    print("=" * 60)
    print("Relay UDP GEO5/RGP (fecha/hora UTC + reenvío CSV + generales)")
    print("=" * 60)

    relay = Geo5UdpRelayServer(
        host=args.host,
        port=args.port,
        config_path=args.config,
        reload_interval_seconds=args.reload_interval,
        log_dir=args.log_dir,
    )

    try:
        relay.start()
    except KeyboardInterrupt:
        print("\nInterrupción detectada...")
    finally:
        relay.stop()
        print("Relay cerrado.")


if __name__ == "__main__":
    main()

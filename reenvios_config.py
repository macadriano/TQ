# -*- coding: utf-8 -*-
"""Carga de reglas de reenvío desde REENVIOS_CONFIG.txt (CSV) y log Reenvios_YYYYMMDD.log."""

from __future__ import annotations

import csv
import ipaddress
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ForwardingRule:
    tipo: str
    cliente: str
    equipo: str
    transporte: str
    protocolo_gps: str
    ip: str
    port: int
    line_no: int
    # Opcional columna CSV FORMATO_ID: para reenvío UDP GEO5, cantidad de caracteres finales
    # del ID de origen (TQ) en ID=... (None = mensaje sin retocar, últimos 5 como hoy).
    formato_id: Optional[int] = None
    # Opcional columna CSV FECHA_ALTA: DD/MM/YYYY (o YYYY-MM-DD, se normaliza a DD/MM/YYYY)
    fecha_alta: Optional[str] = None


def _ensure_logs_dir() -> None:
    if not os.path.exists("logs"):
        os.makedirs("logs")


def get_reenvios_log_path(for_date: datetime | None = None) -> str:
    _ensure_logs_dir()
    dt = for_date or datetime.now()
    return os.path.join("logs", f"Reenvios_{dt.strftime('%Y%m%d')}.log")


def append_reenvio_log(
    device_id: str,
    tipo_regla: str,
    destino_host: str,
    destino_port: int,
    transporte: str,
    formato: str,
    cliente: str = "",
    payload: str = "",
) -> None:
    try:
        path = get_reenvios_log_path()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dest = f"{destino_host}:{destino_port}"
        p = (payload or "").replace("\r", "\\r").replace("\n", "\\n")
        if len(p) > 800:
            p = p[:800] + "...(trunc)"
        c = (cliente or "").strip() or "-"
        parts = [
            ts,
            f"device_id={device_id}",
            f"tipo={tipo_regla}",
            f"destino={dest}",
            f"transporte={transporte}",
            f"formato={formato}",
            f"cliente={c}",
        ]
        if p:
            parts.append(f"payload={p}")
        line = "\t".join(parts) + "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def _normalize_protocol_gps(raw: str) -> str:
    u = (raw or "").strip().upper()
    if u in ("GEO", "GEO5"):
        return "GEO5"
    if u == "TQ":
        return "TQ"
    return ""


def _validate_ipv4(host: str) -> bool:
    try:
        ipaddress.IPv4Address(host.strip())
        return True
    except Exception:
        return False


def _normalize_fecha_alta(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%d/%m/%Y")
        except Exception:
            continue
    return ""


def load_reenvios_config(path: str) -> Tuple[Dict[str, List[ForwardingRule]], List[str]]:
    """
    Lee el CSV y devuelve (reglas_por_equipo_5dígitos, mensajes_de_advertencia).
    Si el archivo no existe, devuelve dict vacío (comportamiento legacy: solo destino general).
    """
    warnings: List[str] = []
    by_equipo: Dict[str, List[ForwardingRule]] = {}

    if not path or not os.path.isfile(path):
        warnings.append(f"Reenvíos: no se encontró el archivo ({path!r}); solo destino UDP general.")
        return by_equipo, warnings

    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            for line_no, row in enumerate(reader, start=1):
                if not row:
                    continue
                # Permitir comentarios: línea que (tras strip) empieza con '#'
                # (puede venir como fila de 1 columna para csv.reader).
                if row and (row[0] or "").strip().startswith("#"):
                    continue
                row = [c.strip() for c in row]
                if not any(row):
                    continue
                if line_no == 1 and row[0].upper() == "TIPO":
                    continue
                if len(row) < 7:
                    warnings.append(f"Reenvíos línea {line_no}: se esperan al menos 7 columnas, hay {len(row)}.")
                    continue

                tipo, cliente, equipo, transporte, proto_gps, ip_s, port_s = row[:7]
                formato_raw = row[7].strip() if len(row) > 7 else ""
                fecha_raw = row[8].strip() if len(row) > 8 else ""
                formato_id: Optional[int] = None
                if formato_raw:
                    try:
                        n = int(formato_raw)
                    except ValueError:
                        warnings.append(
                            f"Reenvíos línea {line_no}: FORMATO_ID no numérico {formato_raw!r}; se ignora."
                        )
                    else:
                        if 1 <= n <= 32:
                            formato_id = n
                        else:
                            warnings.append(
                                f"Reenvíos línea {line_no}: FORMATO_ID fuera de rango (1-32): {n}; se ignora."
                            )
                tipo_u = tipo.upper()
                if tipo_u not in ("SERVICIO", "CLONAR"):
                    warnings.append(f"Reenvíos línea {line_no}: TIPO inválido {tipo!r}.")
                    continue

                tr_u = transporte.upper()
                if tr_u not in ("UDP", "TCP"):
                    warnings.append(f"Reenvíos línea {line_no}: TRANSPORTE inválido {transporte!r}.")
                    continue

                proto = _normalize_protocol_gps(proto_gps)
                if not proto:
                    warnings.append(f"Reenvíos línea {line_no}: PROTOCOLO_GPS inválido {proto_gps!r}.")
                    continue

                eq = equipo.strip()
                if not (eq.isdigit() and len(eq) == 5):
                    warnings.append(f"Reenvíos línea {line_no}: EQUIPO debe ser 5 dígitos, recibido {equipo!r}.")
                    continue

                if not _validate_ipv4(ip_s):
                    warnings.append(f"Reenvíos línea {line_no}: IP inválida {ip_s!r}.")
                    continue

                try:
                    port = int(port_s)
                except ValueError:
                    warnings.append(f"Reenvíos línea {line_no}: PUERTO no numérico {port_s!r}.")
                    continue
                if not (1 <= port <= 65535):
                    warnings.append(f"Reenvíos línea {line_no}: PUERTO fuera de rango {port}.")
                    continue

                fecha_alta = _normalize_fecha_alta(fecha_raw)
                if fecha_raw.strip() and not fecha_alta:
                    warnings.append(f"Reenvíos línea {line_no}: FECHA_ALTA inválida {fecha_raw!r} (usar DD/MM/YYYY).")

                rule = ForwardingRule(
                    tipo=tipo_u,
                    cliente=cliente.strip(),
                    equipo=eq,
                    transporte=tr_u,
                    protocolo_gps=proto,
                    ip=ip_s.strip(),
                    port=port,
                    line_no=line_no,
                    formato_id=formato_id,
                    fecha_alta=(fecha_alta or None),
                )
                by_equipo.setdefault(eq, []).append(rule)
    except Exception as e:
        warnings.append(f"Reenvíos: error leyendo {path!r}: {e}")

    return by_equipo, warnings

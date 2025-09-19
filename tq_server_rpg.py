# tq_server_rpg.py
# Servidor que recibe paquetes TQ, filtra en tiempo real y reenvía en formato RPG por UDP.

import socket
import threading
import logging
import math
from collections import defaultdict
from datetime import datetime

import funciones
import protocolo

logger = logging.getLogger("tq_server")

# ============================================================
# Filtro en tiempo real para limpiar saltos / derivas de GPS
# ============================================================

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

class RealTimeTrackFilter:
    """
    Descarta puntos con saltos incoherentes y duplicados,
    e impide “unir” segmentos tras reconexiones.
    """
    def __init__(self,
                 max_speed_kmh=200,
                 max_dist_step_m=500,
                 short_dt_s=10,
                 min_move_to_accept_m=5,
                 max_age_seconds=None):
        self.max_speed_kmh = max_speed_kmh
        self.max_dist_step_m = max_dist_step_m
        self.short_dt_s = short_dt_s
        self.min_move_to_accept_m = min_move_to_accept_m
        self.max_age_seconds = max_age_seconds
        self.last_ok = {}     # device_id -> {'lat','lon','dt_gps','recv_dt'}
        self.segment_open = defaultdict(lambda: True)

    def _gps_datetime(self, fecha_gps: str, hora_gps: str, fallback_iso: str):
        # Combina DD/MM/YY + HH:MM:SS a datetime; cae a timestamp de recepción si falta algo.
        try:
            d, m, y = fecha_gps.split('/')
            hh, mm, ss = hora_gps.split(':')
            return datetime(int('20'+y), int(m), int(d), int(hh), int(mm), int(ss))
        except Exception:
            try:
                return datetime.fromisoformat(fallback_iso.replace('Z',''))
            except Exception:
                return datetime.utcnow()

    def filter(self, pos: dict):
        """
        pos: {'device_id','latitude','longitude','fecha_gps','hora_gps','timestamp', 'age_seconds'?}
        return: (accept:bool, reason:str, new_segment:bool)
        """
        dev = pos.get('device_id')
        lat = pos.get('latitude')
        lon = pos.get('longitude')
        if lat is None or lon is None:
            return (False, 'no_latlon', False)

        try:
            lat = float(lat); lon = float(lon)
        except Exception:
            return (False, 'bad_latlon', False)

        # (0,0) es inválido
        if abs(lat) < 1e-6 and abs(lon) < 1e-6:
            return (False, 'gps_zero', False)

        dt_gps = self._gps_datetime(pos.get('fecha_gps',''), pos.get('hora_gps',''), pos.get('timestamp',''))

        # Age Of Data si está disponible
        age_s = pos.get('age_seconds')
        if self.max_age_seconds is not None and isinstance(age_s, (int, float)):
            if age_s > self.max_age_seconds:
                # cortar segmento (no unir con lo previo)
                self.segment_open[dev] = False
                return (False, f'agedata_{age_s:.0f}s', True)

        prev = self.last_ok.get(dev)
        if not prev:
            self.last_ok[dev] = {'lat':lat,'lon':lon,'dt_gps':dt_gps,'recv_dt':datetime.utcnow()}
            self.segment_open[dev] = True
            return (True, 'first_point', True)

        delta_t = (dt_gps - prev['dt_gps']).total_seconds()

        if delta_t < 0:
            # Mensaje llegado fuera de orden: no unir hacia atrás
            self.segment_open[dev] = False
            return (False, f'out_of_order_{delta_t:.0f}s', True)

        dist_m = haversine_m(prev['lat'], prev['lon'], lat, lon)

        # Deduplicado / ruido chico
        if dist_m < self.min_move_to_accept_m and delta_t <= self.short_dt_s:
            return (False, f'dupe_or_noise_{dist_m:.1f}m', False)

        # Salto en ventana corta
        if delta_t <= self.short_dt_s and dist_m > self.max_dist_step_m:
            self.segment_open[dev] = False
            return (False, f'jump_shortdt_{dist_m:.0f}m/{delta_t:.0f}s', True)

        # Velocidad implícita
        if delta_t > 0:
            v_kmh = (dist_m/1000.0) / (delta_t/3600.0)
            if v_kmh > self.max_speed_kmh:
                self.segment_open[dev] = False
                return (False, f'jump_speed_{v_kmh:.0f}kmh', True)

        # Aceptar
        self.last_ok[dev] = {'lat':lat,'lon':lon,'dt_gps':dt_gps,'recv_dt':datetime.utcnow()}
        # Si alguien quiso forzar corte antes, al aceptar reabrimos
        self.segment_open[dev] = True
        return (True, 'ok', False)


# ============================================
# Servidor principal TQ -> (filtro) -> RPG UDP
# ============================================

class TQServerRPG:
    def __init__(self, listen_host="0.0.0.0", listen_port=55000,
                 udp_host="127.0.0.1", udp_port=56000):

        self.listen_host = listen_host
        self.listen_port = listen_port
        self.udp_host = udp_host
        self.udp_port = udp_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.listen_host, self.listen_port))

        self.logger = logging.getLogger("tq_server")
        self.terminal_id = ""   # si necesitás almacenarlo luego de detectarlo

        # --- Configuración del filtro anti-saltos ---
        self.rt_filter = RealTimeTrackFilter(
            max_speed_kmh=200,       # ajustable
            max_dist_step_m=500,     # ajustable (si reporta cada 30 s -> 1500 m)
            short_dt_s=10,
            min_move_to_accept_m=5,
            max_age_seconds=None     # poné 30 cuando uses Age Of Data
        )

        self.logger.info(f"Escuchando TQ en {listen_host}:{listen_port} | reenviando RPG a {udp_host}:{udp_port}")

    # ---------------------------
    # Parsing y construcción RPG
    # ---------------------------

    def decode_position_message(self, raw: bytes) -> dict | None:
        """
        Decodifica un paquete TQ en un dict con al menos:
        device_id, latitude, longitude, fecha_gps, hora_gps, timestamp (ISO)
        + (opcional) age_seconds.
        """
        hex_str = funciones.bytes2hexa(raw)
        if not hex_str:
            return None

        # ID del paquete / dispositivo
        dev = protocolo.get_DEVICEID_TQ(hex_str) or protocolo.getIDok(hex_str)

        lat = protocolo.getLAT_TQ(hex_str)
        lon = protocolo.getLON_TQ(hex_str)
        fecha = protocolo.getFECHA_GPS_TQ(hex_str)
        hora = protocolo.getHORA_GPS_TQ(hex_str)

        if lat is None or lon is None:
            return None

        position = {
            "device_id": dev or "UNKNOWN",
            "latitude": float(lat),
            "longitude": float(lon),
            "fecha_gps": fecha or "",
            "hora_gps": hora or "",
            "timestamp": funciones.now_iso()
        }

        # (Opcional) Age Of Data si el protocolo lo trae
        try:
            age_s = protocolo.get_AGE_TQ(hex_str)
            if age_s is not None:
                position["age_seconds"] = int(age_s)
        except Exception:
            pass

        return position

    def create_rpg_message_from_gps(self, position: dict, terminal_id: str) -> bytes | None:
        """
        Convierte la posición a tu formato RPG (placeholder).
        Reemplazá por tu armado real.
        """
        try:
            # Ejemplo de framing trivial CSV -> bytes:
            # RPG,<terminal_id>,<lat>,<lon>,<fecha>,<hora>
            payload = "RPG,{},{},{},{},{}".format(
                terminal_id,
                position.get("latitude"),
                position.get("longitude"),
                position.get("fecha_gps",""),
                position.get("hora_gps",""),
            )
            return payload.encode("ascii")
        except Exception as e:
            self.logger.error(f"Error creando RPG: {e}")
            return None

    # ---------------------------
    # Persistencia / logging
    # ---------------------------

    def save_position_to_file(self, position: dict, path="positions.csv"):
        """
        Guarda posiciones aceptadas (ya filtradas) en CSV simple.
        """
        try:
            line = "{device_id},{latitude},{longitude},{fecha_gps},{hora_gps},{timestamp}\n".format(**position)
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            self.logger.warning(f"No se pudo guardar CSV: {e}")

    def log_rpg_message(self, raw_hex: str, rpg_bytes: bytes, tag="RPG"):
        try:
            self.logger.info(f"{tag} | {rpg_bytes!r}")
        except Exception:
            pass

    def display_position(self, position: dict, client_id: tuple):
        # logging de consola resumido
        self.logger.info(f"POS {position.get('device_id')} "
                         f"{position.get('latitude')},{position.get('longitude')} "
                         f"{position.get('fecha_gps')} {position.get('hora_gps')} "
                         f"from {client_id}")

    # ---------------------------
    # Loop principal de servidor
    # ---------------------------

    def process_message_with_rpg(self, data: bytes, client_id):
        # Decodificar
        position_data = self.decode_position_message(data)
        if not position_data:
            self.logger.debug("Paquete ignorado: no es posición válida")
            return

        self.display_position(position_data, client_id)

        # -------- Filtro en tiempo real --------
        accept, reason, new_segment = self.rt_filter.filter(position_data)
        if not accept:
            self.logger.warning(f"[FILTER_DROP] id={position_data.get('device_id')} motivo={reason}")
            # Si querés guardar descartes en otro CSV, podés hacerlo aquí.
            return

        if new_segment:
            self.logger.info(f"[NEW_SEGMENT] id={position_data.get('device_id')} (no unir con punto previo)")
            # Si tu backend entiende “corte de segmento”, podés enviar una marca especial acá.

        # Opcional: actualizar terminal_id si viene en el paquete
        if not self.terminal_id:
            term = protocolo.getIDok(funciones.bytes2hexa(data))
            if term:
                self.terminal_id = term
                self.logger.info(f"TerminalID detectado: {term}")

        # Guardar aceptados
        self.save_position_to_file(position_data)

        # Reenviar como RPG (solo aceptados)
        if self.terminal_id:
            rpg_message = self.create_rpg_message_from_gps(position_data, self.terminal_id)
            if rpg_message:
                funciones.enviar_mensaje_udp(self.udp_host, self.udp_port, rpg_message)
                self.log_rpg_message(funciones.bytes2hexa(data), rpg_message, "ENVIADO_RPG_GPS")

    def serve_forever(self):
        self.logger.info("Servidor TQ iniciado.")
        while True:
            data, client = self.sock.recvfrom(4096)
            try:
                self.process_message_with_rpg(data, client)
            except Exception as e:
                self.logger.exception(f"Error procesando paquete de {client}: {e}")


# -------------
# Main runnable
# -------------
if __name__ == "__main__":
    funciones.setup_basic_logging(logging.INFO)
    srv = TQServerRPG(
        listen_host="0.0.0.0", listen_port=55000,
        udp_host="127.0.0.1", udp_port=56000
    )
    srv.serve_forever()

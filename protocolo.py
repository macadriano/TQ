# protocolo.py
# Parseo / helpers del protocolo TQ.
# Incluye imports del original para evitar errores de referencia.

import funciones
import struct
from datetime import datetime, timedelta

# -----------------------
# Helpers utilitarios
# -----------------------

def safe_float(v, default=None):
    try:
        return float(v)
    except Exception:
        return default

def safe_int(v, default=None):
    try:
        return int(v)
    except Exception:
        return default

# -----------------------
# Parsers del protocolo TQ
# (Rellenar con offsets reales cuando los tengas)
# -----------------------

def getIDok(dato_hex: str):
    """
    Extrae/valida el ID de terminal (si aplica).
    DEVUELVE: str | None
    TODO: reemplazar con el offset real del protocolo.
    """
    if not dato_hex:
        return None
    # ejemplo: return dato_hex[OFFSET:OFFSET+LARGO]
    return None

def get_DEVICEID_TQ(dato_hex: str):
    """
    Si el ID viene en cada paquete, extraelo acá.
    DEVUELVE: str | None
    """
    if not dato_hex:
        return None
    # ejemplo: return dato_hex[OFFSET:OFFSET+LARGO]
    return None

def getFECHA_GPS_TQ(dato_hex: str):
    """
    Fecha GPS DD/MM/YY como string.
    DEVUELVE: str | None
    """
    if not dato_hex:
        return None
    # ejemplo: dd = int(dato_hex[...],16); mm = ...; yy = ...
    # return f"{dd:02d}/{mm:02d}/{yy:02d}"
    return None

def getHORA_GPS_TQ(dato_hex: str):
    """
    Hora GPS HH:MM:SS como string.
    DEVUELVE: str | None
    """
    if not dato_hex:
        return None
    # ejemplo: hh = int(...); mm = int(...); ss = int(...)
    # return f"{hh:02d}:{mm:02d}:{ss:02d}"
    return None

def getLAT_TQ(dato_hex: str):
    """
    Latitud decimal (float).
    DEVUELVE: float | None
    """
    if not dato_hex:
        return None
    # ejemplo (binario -> float):
    # lat_bytes = bytes.fromhex(dato_hex[OFFSET:OFFSET+8])
    # lat = struct.unpack('>f', lat_bytes)[0]
    # return lat
    return None

def getLON_TQ(dato_hex: str):
    """
    Longitud decimal (float).
    DEVUELVE: float | None
    """
    if not dato_hex:
        return None
    # ejemplo:
    # lon_bytes = bytes.fromhex(dato_hex[OFFSET:OFFSET+8])
    # lon = struct.unpack('>f', lon_bytes)[0]
    # return lon
    return None

def getVEL_TQ(dato_hex: str):
    """
    Velocidad reportada por el equipo (si te sirve para log).
    DEVUELVE: float | None
    """
    if not dato_hex:
        return None
    # ejemplo:
    # v_hex = dato_hex[OFFSET:OFFSET+4]
    # return int(v_hex, 16) * FACTOR
    return None

def get_EVENT_FLAGS_TQ(dato_hex: str):
    """
    Flags/eventos (p.ej. baja señal) si el protocolo los trae.
    DEVUELVE: dict (p.ej. {"low_gsm": True})
    """
    flags = {}
    if not dato_hex:
        return flags
    # ejemplo:
    # flags["low_gsm"] = bool(int(dato_hex[OFFSET:OFFSET+2], 16) & 0x01)
    return flags

def get_AGE_TQ(dato_hex: str):
    """
    (Opcional) Age Of Data en segundos, si el fabricante lo incluye.
    DEVUELVE: int | None
    """
    if not dato_hex:
        return None
    # TODO: cuando te pasen el offset exacto:
    # age_hex = dato_hex[OFFSET:OFFSET+N]
    # return int(age_hex, 16)  # o según formato
    return None

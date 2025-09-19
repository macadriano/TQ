# funciones.py
# Utilidades comunes: hexa/bytes, UDP, logging, etc.

import socket
import binascii
import logging
from datetime import datetime

logger = logging.getLogger("tq_server")

def bytes2hexa(b: bytes) -> str:
    try:
        return binascii.hexlify(b).decode("ascii").lower()
    except Exception:
        return ""

def hexa2bytes(h: str) -> bytes:
    try:
        return binascii.unhexlify(h)
    except Exception:
        return b""

def enviar_mensaje_udp(host: str, port: int, payload: bytes, timeout=3.0) -> None:
    """
    Envía payload por UDP y cierra el socket (fire-and-forget).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    try:
        sock.sendto(payload, (host, port))
    finally:
        sock.close()

def now_iso() -> str:
    # ISO “naive” en UTC (coherente con lo que se usa en logs)
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

def setup_basic_logging(level=logging.INFO):
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(level=level, format=fmt, datefmt=datefmt)

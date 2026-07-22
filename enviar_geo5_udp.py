#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Envía un mensaje GEO5/RGP ya armado por UDP.

Uso:
  python enviar_geo5_udp.py --ip 179.43.115.190 --port 7007
  python enviar_geo5_udp.py --ip 200.58.98.187 --port 6003 --message ">RGP...<"
"""

from __future__ import annotations

import argparse
import socket
import sys

DEFAULT_MESSAGE = (
    ">RGP180726221512+2040.7461-10324.51810002071000001;&01;ID=11924;#0001*65<"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Envía un mensaje GEO5/RGP por UDP a IP:PUERTO"
    )
    parser.add_argument(
        "--ip",
        required=True,
        help="IP de destino (ej. 179.43.115.190)",
    )
    parser.add_argument(
        "--port",
        type=int,
        required=True,
        help="Puerto UDP de destino (ej. 7007)",
    )
    parser.add_argument(
        "--message",
        "-m",
        default=DEFAULT_MESSAGE,
        help="Mensaje GEO5 completo (default: ejemplo México ID=11924)",
    )
    args = parser.parse_args()

    if not (1 <= args.port <= 65535):
        print(f"Error: puerto inválido {args.port}", file=sys.stderr)
        return 1

    mensaje = (args.message or "").strip()
    if not mensaje:
        print("Error: mensaje vacío", file=sys.stderr)
        return 1

    payload = mensaje.encode("ascii", errors="strict")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(payload, (args.ip, args.port))
        print(f"OK UDP -> {args.ip}:{args.port} ({len(payload)} bytes)")
        print(f"payload: {mensaje}")
        return 0
    except Exception as e:
        print(f"Error enviando UDP: {e}", file=sys.stderr)
        return 1
    finally:
        sock.close()


if __name__ == "__main__":
    raise SystemExit(main())

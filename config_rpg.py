#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración para el Servidor TQ + RPG
Usa las funciones existentes de funciones.py y protocolo.py
"""

# Configuración del servidor TCP
TCP_HOST = '0.0.0.0'  # Escuchar en todas las interfaces
TCP_PORT = 5003        # Puerto para conexiones TQ

# Configuración del reenvío UDP
UDP_HOST = '179.43.115.190'  # IP de destino para mensajes RPG
UDP_PORT = 7007               # Puerto de destino para mensajes RPG

# Configuración de archivos
POSITIONS_FILE = 'positions_log.csv'  # Archivo de posiciones GPS
RPG_LOG_FILE = 'rpg_messages.log'     # Archivo de log de mensajes RPG
SERVER_LOG_FILE = 'tq_server_rpg.log' # Archivo de log del servidor

# Archivos de log existentes (usados por funciones.py)
LOG_FILE = 'log3.txt'          # Log general (funciones.guardarLog)
LOG_UDP_FILE = 'logUDP.txt'    # Log UDP (funciones.guardarLogUDP)

# Configuración de logging
LOG_LEVEL = 'INFO'  # Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Configuración del protocolo RPG
# Usa las funciones existentes de protocolo.py:
# - RGPdesdeCHINO() para protocolo chino (tipo 22)
# - RGPdesdePERSONAL() para protocolo personal

# Configuración de coordenadas (para validación)
MIN_LATITUDE = -35.0   # Latitud mínima válida (Buenos Aires)
MAX_LATITUDE = -33.0   # Latitud máxima válida
MIN_LONGITUDE = -59.0  # Longitud mínima válida
MAX_LONGITUDE = -57.0  # Longitud máxima válida

# Configuración de velocidad y rumbo
MAX_SPEED = 200.0      # Velocidad máxima válida (km/h)
MAX_HEADING = 360.0    # Rumbo máximo válido (grados)

# Configuración de timeouts
CLIENT_TIMEOUT = 10    # Timeout para clientes inactivos (segundos)
UDP_TIMEOUT = 5        # Timeout para envío UDP (segundos)

# Protocolos soportados (según protocolo.py)
SUPPORTED_PROTOCOLS = {
    "01": "Terminal Register",
    "22": "Location Data (Chinese Protocol)",
    "Other": "Personal Protocol (TQ)"
}

# config.py
"""Configuración para el sistema de monitoreo por heartbeat UDP.

Este archivo contiene la configuración para el monitor de heartbeat.
Puede usar las mismas credenciales que monitor_config.py o configurar valores específicos.
"""

import os
import sys

# Intentar importar configuración del proyecto principal si existe
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from monitor_config import (
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        SMTP_SERVER,
        SMTP_PORT,
        SMTP_USERNAME,
        SMTP_PASSWORD,
        EMAIL_RECIPIENT,
    )
    # Si se importó exitosamente, usar esos valores
    _USE_EXTERNAL_CONFIG = True
except ImportError:
    _USE_EXTERNAL_CONFIG = False

# ---------------------------------------------------------------------------
# Configuración UDP - Heartbeat
# ---------------------------------------------------------------------------
# Puerto UDP donde el monitor escuchará los heartbeats
UDP_LISTEN_PORT = 9001

# IP donde escuchar (0.0.0.0 = todas las interfaces, 127.0.0.1 = solo localhost)
UDP_LISTEN_HOST = '0.0.0.0'

# Tiempo en segundos sin recibir heartbeat antes de considerar el servidor caído
# Default: 5 minutos (300 segundos)
HEARTBEAT_TIMEOUT_SECONDS = 300

# Intervalo esperado de heartbeats (para logging y estadísticas)
EXPECTED_HEARTBEAT_INTERVAL_SECONDS = 300  # 5 minutos

# ---------------------------------------------------------------------------
# Configuración de Telegram
# ---------------------------------------------------------------------------
if not _USE_EXTERNAL_CONFIG:
    TELEGRAM_BOT_TOKEN = "8593437029:AAG_RRiP4zqcQ-IsEBKi38DWECR5KHHjqtA"
    TELEGRAM_CHAT_ID = "5266332517"

# ---------------------------------------------------------------------------
# Configuración de Email
# ---------------------------------------------------------------------------
EMAIL_ENABLED = True  # Cambiar a False para deshabilitar notificaciones por email

if not _USE_EXTERNAL_CONFIG:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USERNAME = "alertastq4994l@gmail.com"
    SMTP_PASSWORD = "Pintame7."
    EMAIL_RECIPIENT = "macadriano4994@gmail.com"

# ---------------------------------------------------------------------------
# Configuración de Logging
# ---------------------------------------------------------------------------
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "heartbeat_monitor.log")
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# ---------------------------------------------------------------------------
# Configuración de Reintentos
# ---------------------------------------------------------------------------
# Número de intentos antes de enviar una nueva alerta (evitar spam)
ALERT_COOLDOWN_SECONDS = 600  # 10 minutos entre alertas del mismo tipo

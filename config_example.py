# Configuración de ejemplo para el Servidor TQ
# Copia este archivo como config_local.py y modifica según tus necesidades

# Configuración del servidor
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8080

# Configuración de logging
LOG_FILE = 'tq_server.log'
LOG_LEVEL = 'INFO'

# Configuración de protocolo
PROTOCOL_BYTE_ORDER = 'big'  # 'big' o 'little'
PROTOCOL_DELIMITER = ','     # Delimitador para formato texto

# Configuración de validación
VALIDATE_COORDINATES = True
MAX_LATITUDE = 90.0
MIN_LATITUDE = -90.0
MAX_LONGITUDE = 180.0
MIN_LONGITUDE = -180.0

# Configuración de visualización
SHOW_RAW_DATA = True
SHOW_HEX_DATA = True
COORDINATE_PRECISION = 6

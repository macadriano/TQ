#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración del Servidor TQ
Archivo de configuración para personalizar el comportamiento del servidor
"""

# Configuración del servidor
SERVER_CONFIG = {
    'host': '0.0.0.0',           # Dirección IP del servidor
    'port': 8080,                # Puerto del servidor
    'max_connections': 100,      # Máximo número de conexiones simultáneas
    'buffer_size': 1024,         # Tamaño del buffer de recepción
    'timeout': 30,               # Timeout de conexión en segundos
}

# Configuración de logging
LOGGING_CONFIG = {
    'log_file': 'tq_server.log',     # Archivo de log
    'log_level': 'INFO',             # Nivel de log (DEBUG, INFO, WARNING, ERROR)
    'log_format': '%(asctime)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'max_log_size': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5,               # Número de archivos de backup
}

# Configuración de decodificación de protocolo
PROTOCOL_CONFIG = {
    # Orden de bytes (big-endian o little-endian)
    'byte_order': 'big',         # 'big' o 'little'
    
    # Formatos de mensaje soportados
    'formats': {
        'binary': {
            'enabled': True,
            'structure': '>IffHH',  # ID(4), LAT(4), LON(4), RUMBO(2), VEL(2)
            'min_length': 16,
        },
        'text': {
            'enabled': True,
            'delimiter': ',',        # Delimitador de campos
            'min_fields': 5,
        },
        'hex': {
            'enabled': True,
            'min_length': 16,
        }
    },
    
    # Configuración de coordenadas
    'coordinates': {
        'latitude_scale': 1.0,       # Factor de escala para latitud
        'longitude_scale': 1.0,      # Factor de escala para longitud
        'heading_range': (0, 360),   # Rango válido de rumbo
        'speed_range': (0, 200),     # Rango válido de velocidad (km/h)
    },
    
    # Configuración de validación
    'validation': {
        'check_coordinates': True,   # Validar rangos de coordenadas
        'check_checksum': False,     # Verificar checksum (si aplica)
        'max_latitude': 90.0,        # Máxima latitud válida
        'min_latitude': -90.0,       # Mínima latitud válida
        'max_longitude': 180.0,      # Máxima longitud válida
        'min_longitude': -180.0,     # Mínima longitud válida
    }
}

# Configuración de visualización
DISPLAY_CONFIG = {
    'show_raw_data': True,          # Mostrar datos raw en pantalla
    'show_hex_data': True,          # Mostrar datos en hexadecimal
    'show_position_details': True,   # Mostrar detalles de posición
    'timestamp_format': '%Y-%m-%d %H:%M:%S',
    'coordinate_precision': 6,       # Precisión decimal para coordenadas
    'speed_unit': 'km/h',           # Unidad de velocidad
    'heading_unit': '°',            # Unidad de rumbo
}

# Configuración de cliente de prueba
TEST_CLIENT_CONFIG = {
    'default_host': 'localhost',
    'default_port': 8080,
    'default_interval': 5.0,         # Intervalo entre mensajes (segundos)
    'position_update': {
        'lat_variation': 0.001,      # Variación máxima de latitud
        'lon_variation': 0.001,      # Variación máxima de longitud
        'heading_variation': 10,     # Variación máxima de rumbo
        'speed_range': (0, 80),      # Rango de velocidad
    },
    'initial_position': {
        'latitude': -34.6037,        # Buenos Aires, Argentina
        'longitude': -58.3816,
        'heading': 0,
        'speed': 0,
    }
}

# Configuración de comandos del servidor
COMMANDS_CONFIG = {
    'available_commands': ['status', 'clients', 'quit', 'help'],
    'command_prompt': 'Comando: ',
    'auto_save_logs': True,          # Guardar logs automáticamente
    'log_rotation': True,            # Rotar archivos de log
}

# Configuración de seguridad
SECURITY_CONFIG = {
    'max_message_size': 1024,        # Tamaño máximo de mensaje
    'rate_limit': {
        'enabled': False,            # Habilitar límite de tasa
        'max_messages_per_minute': 60,
    },
    'blacklist': [],                 # Lista de IPs bloqueadas
    'whitelist': [],                 # Lista de IPs permitidas (vacío = todas)
}

# Configuración de base de datos (opcional)
DATABASE_CONFIG = {
    'enabled': False,                # Habilitar almacenamiento en BD
    'type': 'sqlite',                # Tipo de base de datos
    'file': 'tq_positions.db',       # Archivo de base de datos
    'save_positions': False,         # Guardar posiciones en BD
    'save_raw_messages': False,      # Guardar mensajes raw en BD
}

# Configuración de notificaciones (opcional)
NOTIFICATION_CONFIG = {
    'enabled': False,                # Habilitar notificaciones
    'email': {
        'smtp_server': '',
        'smtp_port': 587,
        'username': '',
        'password': '',
        'recipients': [],
    },
    'webhook': {
        'url': '',
        'enabled': False,
    }
}

# Función para obtener configuración
def get_config(section: str = None):
    """
    Obtiene la configuración completa o una sección específica
    
    Args:
        section: Nombre de la sección de configuración
        
    Returns:
        Diccionario con la configuración
    """
    config = {
        'server': SERVER_CONFIG,
        'logging': LOGGING_CONFIG,
        'protocol': PROTOCOL_CONFIG,
        'display': DISPLAY_CONFIG,
        'test_client': TEST_CLIENT_CONFIG,
        'commands': COMMANDS_CONFIG,
        'security': SECURITY_CONFIG,
        'database': DATABASE_CONFIG,
        'notifications': NOTIFICATION_CONFIG,
    }
    
    if section:
        return config.get(section, {})
    return config

# Función para validar configuración
def validate_config():
    """
    Valida la configuración y retorna errores si los hay
    
    Returns:
        Lista de errores encontrados
    """
    errors = []
    
    # Validar configuración del servidor
    if SERVER_CONFIG['port'] < 1 or SERVER_CONFIG['port'] > 65535:
        errors.append("Puerto del servidor debe estar entre 1 y 65535")
    
    if SERVER_CONFIG['max_connections'] < 1:
        errors.append("Máximo de conexiones debe ser mayor a 0")
    
    # Validar configuración de logging
    if not LOGGING_CONFIG['log_file']:
        errors.append("Archivo de log no puede estar vacío")
    
    # Validar configuración de protocolo
    if PROTOCOL_CONFIG['byte_order'] not in ['big', 'little']:
        errors.append("Orden de bytes debe ser 'big' o 'little'")
    
    return errors

# Función para imprimir configuración
def print_config(section: str = None):
    """
    Imprime la configuración actual
    
    Args:
        section: Sección específica a imprimir
    """
    import json
    
    config = get_config(section)
    print(json.dumps(config, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # Validar configuración al ejecutar este archivo
    errors = validate_config()
    if errors:
        print("❌ Errores en la configuración:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Configuración válida")
        print("\n📋 Configuración actual:")
        print_config()

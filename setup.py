#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de instalación y configuración para el Servidor TQ
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica la versión de Python"""
    if sys.version_info < (3, 7):
        print("❌ Error: Se requiere Python 3.7 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def create_directories():
    """Crea directorios necesarios"""
    directories = ['logs', 'data', 'backups']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"📁 Directorio creado: {directory}")

def check_dependencies():
    """Verifica dependencias"""
    print("\n🔍 Verificando dependencias...")
    
    # Dependencias estándar de Python
    required_modules = [
        'socket', 'threading', 'logging', 'struct', 
        'binascii', 'datetime', 'typing'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module}")
    
    if missing_modules:
        print(f"\n⚠️  Módulos faltantes: {', '.join(missing_modules)}")
        print("   Estos módulos deberían estar incluidos en Python estándar")
        return False
    
    return True

def create_startup_scripts():
    """Crea scripts de inicio para diferentes sistemas operativos"""
    print("\n📝 Creando scripts de inicio...")
    
    # Script para Windows
    if os.name == 'nt':
        with open('start_server.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('echo Iniciando Servidor TQ...\n')
            f.write('python tq_server.py\n')
            f.write('pause\n')
        print("✅ start_server.bat creado")
        
        with open('start_client.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('echo Iniciando Cliente de Prueba TQ...\n')
            f.write('python tq_client_test.py\n')
            f.write('pause\n')
        print("✅ start_client.bat creado")
    
    # Script para Unix/Linux/Mac
    else:
        with open('start_server.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('echo "Iniciando Servidor TQ..."\n')
            f.write('python3 tq_server.py\n')
        os.chmod('start_server.sh', 0o755)
        print("✅ start_server.sh creado")
        
        with open('start_client.sh', 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('echo "Iniciando Cliente de Prueba TQ..."\n')
            f.write('python3 tq_client_test.py\n')
        os.chmod('start_client.sh', 0o755)
        print("✅ start_client.sh creado")

def test_server():
    """Prueba el servidor"""
    print("\n🧪 Probando servidor...")
    
    try:
        # Importar y crear instancia del servidor
        from tq_server import TQServer
        
        server = TQServer(host='127.0.0.1', port=8081)  # Puerto diferente para prueba
        
        # Verificar que se puede crear
        print("✅ Servidor creado correctamente")
        
        # Verificar configuración
        status = server.get_status()
        print(f"✅ Estado del servidor: {status['running']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando servidor: {e}")
        return False

def test_client():
    """Prueba el cliente"""
    print("\n🧪 Probando cliente...")
    
    try:
        # Importar y crear instancia del cliente
        from tq_client_test import TQClient
        
        client = TQClient(server_host='127.0.0.1', server_port=8081, device_id=9999)
        
        # Verificar que se puede crear
        print("✅ Cliente creado correctamente")
        
        # Verificar creación de mensaje
        message = client.create_position_message(1)
        print(f"✅ Mensaje creado: {len(message)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando cliente: {e}")
        return False

def create_sample_config():
    """Crea archivo de configuración de ejemplo"""
    print("\n📋 Creando configuración de ejemplo...")
    
    config_content = '''# Configuración de ejemplo para el Servidor TQ
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
'''
    
    with open('config_example.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ config_example.py creado")

def show_usage_instructions():
    """Muestra instrucciones de uso"""
    print("\n" + "="*60)
    print("🚀 INSTALACIÓN COMPLETADA")
    print("="*60)
    
    print("\n📖 INSTRUCCIONES DE USO:")
    print("\n1. INICIAR EL SERVIDOR:")
    if os.name == 'nt':
        print("   - Ejecutar: start_server.bat")
        print("   - O manualmente: python tq_server.py")
    else:
        print("   - Ejecutar: ./start_server.sh")
        print("   - O manualmente: python3 tq_server.py")
    
    print("\n2. PROBAR CON CLIENTE:")
    if os.name == 'nt':
        print("   - Ejecutar: start_client.bat")
        print("   - O manualmente: python tq_client_test.py")
    else:
        print("   - Ejecutar: ./start_client.sh")
        print("   - O manualmente: python3 tq_client_test.py")
    
    print("\n3. COMANDOS DEL SERVIDOR:")
    print("   - status: Mostrar estado del servidor")
    print("   - clients: Mostrar clientes conectados")
    print("   - quit: Salir del servidor")
    
    print("\n4. ARCHIVOS IMPORTANTES:")
    print("   - tq_server.log: Archivo de logs")
    print("   - config.py: Configuración del sistema")
    print("   - README.md: Documentación completa")
    
    print("\n5. PERSONALIZACIÓN:")
    print("   - Editar config.py para cambiar configuración")
    print("   - Modificar tq_server.py para adaptar protocolo")
    print("   - Revisar README.md para más detalles")
    
    print("\n" + "="*60)
    print("✅ ¡El servidor TQ está listo para usar!")
    print("="*60)

def main():
    """Función principal de instalación"""
    print("="*60)
    print("🔧 INSTALADOR DEL SERVIDOR TQ")
    print("="*60)
    
    # Verificar versión de Python
    if not check_python_version():
        return False
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n⚠️  Algunas dependencias pueden estar faltando")
        response = input("¿Continuar con la instalación? (s/n): ").lower()
        if response != 's':
            return False
    
    # Crear directorios
    print("\n📁 Creando estructura de directorios...")
    create_directories()
    
    # Crear scripts de inicio
    create_startup_scripts()
    
    # Crear configuración de ejemplo
    create_sample_config()
    
    # Probar componentes
    print("\n🧪 Probando componentes...")
    server_ok = test_server()
    client_ok = test_client()
    
    if not server_ok or not client_ok:
        print("\n⚠️  Algunos componentes fallaron en las pruebas")
        response = input("¿Continuar con la instalación? (s/n): ").lower()
        if response != 's':
            return False
    
    # Mostrar instrucciones
    show_usage_instructions()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Instalación completada exitosamente")
        else:
            print("\n❌ Instalación falló")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la instalación: {e}")
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar conexión al servidor TQ
"""

import socket
import time
import struct

def test_server_connection(host='200.58.98.187', port=5003):
    """Prueba la conexión al servidor TQ"""
    print(f"🔍 Probando conexión a {host}:{port}")
    
    try:
        # Crear socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Timeout de 10 segundos
        
        # Intentar conectar
        print("📡 Conectando...")
        sock.connect((host, port))
        print("✅ Conexión exitosa!")
        
        # Enviar un mensaje de prueba
        device_id = 1234
        latitude = -34.6037
        longitude = -58.3816
        heading = 45
        speed = 60
        
        # Crear mensaje de prueba (formato binario)
        message = struct.pack('>IffHH', device_id, latitude, longitude, heading, speed)
        
        print(f"📤 Enviando mensaje de prueba...")
        sock.send(message)
        print("✅ Mensaje enviado correctamente")
        
        # Esperar respuesta (opcional)
        time.sleep(2)
        
        # Cerrar conexión
        sock.close()
        print("🔌 Conexión cerrada")
        
        return True
        
    except socket.timeout:
        print("❌ Timeout: El servidor no respondió en 10 segundos")
        return False
    except ConnectionRefusedError:
        print("❌ Conexión rechazada: El servidor no está ejecutándose o el puerto está cerrado")
        return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 50)
    print("🧪 PRUEBA DE CONEXIÓN SERVIDOR TQ")
    print("=" * 50)
    
    # Probar conexión
    success = test_server_connection()
    
    if success:
        print("\n🎉 ¡Prueba exitosa! El servidor está funcionando correctamente.")
        print("💡 Ahora puedes ejecutar el cliente completo con: python tq_client_test.py")
    else:
        print("\n⚠️  La prueba falló. Verifica que:")
        print("   1. El servidor esté ejecutándose en el puerto 5003")
        print("   2. El firewall permita conexiones al puerto 5003")
        print("   3. La IP del servidor sea correcta")

if __name__ == "__main__":
    main()

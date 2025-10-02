#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el servidor TQ simplificado
Envía mensajes del formato RECORRIDO61674_011025.txt
"""

import socket
import time
import binascii
from datetime import datetime

def test_server():
    """Prueba el servidor TQ simplificado"""
    
    # Mensajes de prueba del formato TQ con diferentes IDs
    test_messages = [
        # Mensaje con ID 61674 (original)
        "24207666167410521901102534381299060583274822016334fffffbff0006fdd300000000000000df54000000",
        # Mensaje con ID diferente (ejemplo: 68133)
        "24207666813310525201102534380885060583277462002315fffffbff0006fdd300000000000000df54000001",
        # Mensaje con otro ID (ejemplo: 12345)
        "24207661234510525301102534380878060583277522003333fffffbff0006fdd300000000000000df54000002"
    ]
    
    try:
        # Conectar al servidor
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 5003))
        
        print("✅ Conectado al servidor TQ simplificado")
        print(f"📤 Enviando {len(test_messages)} mensajes de prueba...")
        
        for i, hex_message in enumerate(test_messages, 1):
            # Convertir hex a bytes
            message_bytes = binascii.unhexlify(hex_message)
            
            # Enviar mensaje
            client_socket.send(message_bytes)
            print(f"📤 Mensaje {i} enviado: {hex_message[:50]}...")
            
            # Esperar un poco entre mensajes
            time.sleep(1)
        
        print("✅ Todos los mensajes enviados correctamente")
        
    except ConnectionRefusedError:
        print("❌ Error: No se puede conectar al servidor")
        print("💡 Asegúrate de que el servidor esté ejecutándose")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client_socket.close()
        print("🔌 Conexión cerrada")

def test_invalid_message():
    """Prueba con un mensaje inválido (debe ser descartado)"""
    
    try:
        # Conectar al servidor
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 5003))
        
        print("🧪 Probando mensaje inválido...")
        
        # Mensaje inválido (no empieza con 242076661674)
        invalid_message = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        message_bytes = binascii.unhexlify(invalid_message)
        
        # Enviar mensaje inválido
        client_socket.send(message_bytes)
        print("📤 Mensaje inválido enviado (debe ser descartado por el servidor)")
        
    except ConnectionRefusedError:
        print("❌ Error: No se puede conectar al servidor")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client_socket.close()
        print("🔌 Conexión cerrada")

def main():
    """Función principal"""
    print("=" * 70)
    print("🧪 PRUEBA DEL SERVIDOR TQ SIMPLIFICADO")
    print("=" * 70)
    print("📋 Probando mensajes del formato RECORRIDO61674_011025.txt")
    print()
    
    # Prueba con mensajes válidos
    print("1️⃣ Probando mensajes válidos...")
    test_server()
    
    print("\n" + "=" * 50)
    
    # Prueba con mensaje inválido
    print("2️⃣ Probando mensaje inválido...")
    test_invalid_message()
    
    print("\n✅ Pruebas completadas")
    print("📋 Revisa los logs del servidor para ver los resultados")

if __name__ == "__main__":
    main()

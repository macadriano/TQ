#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente de prueba para Protocolo TQ
Simula equipos GPS enviando mensajes de posición
"""

import socket
import time
import struct
import random
import threading
from datetime import datetime

class TQClient:
    def __init__(self, server_host: str = 'localhost', server_port: int = 8080, device_id: int = None):
        """
        Inicializa el cliente TQ
        
        Args:
            server_host: Dirección IP del servidor
            server_port: Puerto del servidor
            device_id: ID del dispositivo (si es None, se genera aleatoriamente)
        """
        self.server_host = server_host
        self.server_port = server_port
        self.device_id = device_id or random.randint(1000, 9999)
        self.socket = None
        self.running = False
        
        # Posición inicial (Buenos Aires, Argentina)
        self.latitude = -34.6037
        self.longitude = -58.3816
        self.heading = 0
        self.speed = 0
        
    def connect(self):
        """Conecta al servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.running = True
            
            print(f"🔗 Cliente {self.device_id} conectado a {self.server_host}:{self.server_port}")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando cliente {self.device_id}: {e}")
            return False
            
    def disconnect(self):
        """Desconecta del servidor"""
        self.running = False
        if self.socket:
            self.socket.close()
        print(f"🔌 Cliente {self.device_id} desconectado")
        
    def update_position(self):
        """Actualiza la posición del dispositivo"""
        # Simular movimiento
        self.latitude += random.uniform(-0.001, 0.001)
        self.longitude += random.uniform(-0.001, 0.001)
        self.heading = (self.heading + random.uniform(-10, 10)) % 360
        self.speed = random.uniform(0, 80)
        
    def create_position_message(self, format_type: int = 1) -> bytes:
        """
        Crea un mensaje de posición según el formato especificado
        
        Args:
            format_type: 1=binario, 2=texto, 3=hexadecimal
        """
        if format_type == 1:
            # Formato binario
            return struct.pack('>IffHH', 
                             self.device_id,
                             self.latitude,
                             self.longitude,
                             int(self.heading),
                             int(self.speed))
                             
        elif format_type == 2:
            # Formato texto con delimitadores
            message = f"{self.device_id},{self.latitude:.6f},{self.longitude:.6f},{self.heading:.1f},{self.speed:.1f}"
            return message.encode('ascii')
            
        elif format_type == 3:
            # Formato hexadecimal
            lat_raw = int(self.latitude * 1000000)
            lon_raw = int(self.longitude * 1000000)
            heading_raw = int(self.heading)
            speed_raw = int(self.speed)
            
            hex_message = f"{self.device_id:08x}{lat_raw:08x}{lon_raw:08x}{heading_raw:04x}{speed_raw:04x}"
            return bytes.fromhex(hex_message)
            
        else:
            raise ValueError(f"Formato no soportado: {format_type}")
            
    def send_position(self, format_type: int = 1):
        """Envía un mensaje de posición al servidor"""
        try:
            self.update_position()
            message = self.create_position_message(format_type)
            
            if self.socket:
                self.socket.send(message)
                print(f"📤 Cliente {self.device_id} envió posición: "
                      f"Lat={self.latitude:.6f}, Lon={self.longitude:.6f}, "
                      f"Rumbo={self.heading:.1f}°, Vel={self.speed:.1f} km/h")
                      
        except Exception as e:
            print(f"❌ Error enviando posición desde cliente {self.device_id}: {e}")
            self.running = False
            
    def run(self, interval: float = 5.0, format_type: int = 1):
        """
        Ejecuta el cliente enviando mensajes periódicamente
        
        Args:
            interval: Intervalo entre mensajes en segundos
            format_type: Tipo de formato del mensaje
        """
        if not self.connect():
            return
            
        try:
            while self.running:
                self.send_position(format_type)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Cliente {self.device_id} interrumpido")
        finally:
            self.disconnect()

def create_multiple_clients(num_clients: int = 3, server_host: str = 'localhost', server_port: int = 8080):
    """
    Crea múltiples clientes simulando diferentes equipos
    
    Args:
        num_clients: Número de clientes a crear
        server_host: Dirección IP del servidor
        server_port: Puerto del servidor
    """
    clients = []
    threads = []
    
    print(f"🚀 Creando {num_clients} clientes de prueba...")
    
    for i in range(num_clients):
        # Crear cliente con ID único
        device_id = 1000 + i
        client = TQClient(server_host, server_port, device_id)
        clients.append(client)
        
        # Crear hilo para el cliente
        thread = threading.Thread(
            target=client.run,
            args=(5.0, random.randint(1, 3)),  # Intervalo aleatorio y formato aleatorio
            daemon=True
        )
        threads.append(thread)
        
    # Iniciar todos los hilos
    for thread in threads:
        thread.start()
        time.sleep(1)  # Pequeña pausa entre clientes
        
    print(f"✅ {num_clients} clientes iniciados")
    
    try:
        # Mantener el programa ejecutándose
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo clientes...")
        for client in clients:
            client.disconnect()

def main():
    """Función principal"""
    print("=" * 60)
    print("🧪 CLIENTE DE PRUEBA PROTOCOLO TQ")
    print("=" * 60)
    
    print("\nOpciones disponibles:")
    print("1. Cliente único")
    print("2. Múltiples clientes")
    print("3. Cliente con formato específico")
    
    choice = input("\nSeleccione opción (1-3): ").strip()
    
    if choice == "1":
        # Cliente único
        device_id = input("ID del dispositivo (Enter para aleatorio): ").strip()
        device_id = int(device_id) if device_id else None
        
        client = TQClient(device_id=device_id)
        client.run()
        
    elif choice == "2":
        # Múltiples clientes
        num_clients = input("Número de clientes (Enter para 3): ").strip()
        num_clients = int(num_clients) if num_clients else 3
        
        create_multiple_clients(num_clients)
        
    elif choice == "3":
        # Cliente con formato específico
        device_id = input("ID del dispositivo (Enter para aleatorio): ").strip()
        device_id = int(device_id) if device_id else None
        
        print("\nFormatos disponibles:")
        print("1. Binario (struct)")
        print("2. Texto con delimitadores")
        print("3. Hexadecimal")
        
        format_type = input("Formato (1-3): ").strip()
        format_type = int(format_type) if format_type else 1
        
        client = TQClient(device_id=device_id)
        client.run(format_type=format_type)
        
    else:
        print("❌ Opción no válida")

if __name__ == "__main__":
    main()

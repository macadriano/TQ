#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor TCP para Protocolo TQ
Maneja conexiones de equipos GPS y decodifica mensajes de posición
"""

import socket
import threading
import time
import logging
import struct
import binascii
from datetime import datetime
from typing import Dict, Optional, Tuple

class TQServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        """
        Inicializa el servidor TQ
        
        Args:
            host: Dirección IP del servidor
            port: Puerto del servidor
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients: Dict[str, socket.socket] = {}
        self.running = False
        
        # Configurar logging
        self.setup_logging()
        
        # Contador de mensajes procesados
        self.message_count = 0
        
    def setup_logging(self):
        """Configura el sistema de logging"""
        # Crear logger
        self.logger = logging.getLogger('TQServer')
        self.logger.setLevel(logging.INFO)
        
        # Crear formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para archivo
        file_handler = logging.FileHandler('tq_server.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers al logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def start(self):
        """Inicia el servidor TCP"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            self.logger.info(f"Servidor TQ iniciado en {self.host}:{self.port}")
            print(f"🚀 Servidor TQ iniciado en {self.host}:{self.port}")
            print("📡 Esperando conexiones de equipos...")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        self.logger.error(f"Error aceptando conexión: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error iniciando servidor: {e}")
            print(f"❌ Error iniciando servidor: {e}")
            
    def stop(self):
        """Detiene el servidor"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("Servidor detenido")
        print("🛑 Servidor detenido")
        
    def handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Maneja la conexión de un cliente"""
        client_id = f"{client_address[0]}:{client_address[1]}"
        self.clients[client_id] = client_socket
        
        self.logger.info(f"Nueva conexión desde {client_id}")
        print(f"🔗 Nueva conexión desde {client_id}")
        
        try:
            while self.running:
                # Recibir datos del cliente
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                # Procesar el mensaje recibido
                self.process_message(data, client_id)
                
        except Exception as e:
            self.logger.error(f"Error manejando cliente {client_id}: {e}")
            print(f"❌ Error con cliente {client_id}: {e}")
            
        finally:
            # Limpiar conexión
            client_socket.close()
            del self.clients[client_id]
            self.logger.info(f"Conexión cerrada: {client_id}")
            print(f"🔌 Conexión cerrada: {client_id}")
            
    def process_message(self, data: bytes, client_id: str):
        """Procesa un mensaje recibido del cliente"""
        self.message_count += 1
        
        # Log del mensaje raw
        hex_data = binascii.hexlify(data).decode('ascii')
        self.logger.info(f"Msg #{self.message_count} de {client_id}: {hex_data}")
        print(f"📨 Msg #{self.message_count} de {client_id}")
        print(f"   Raw: {hex_data}")
        
        try:
            # Intentar decodificar el mensaje
            position_data = self.decode_position_message(data)
            
            if position_data:
                self.logger.info(f"Posición decodificada: {position_data}")
                self.display_position(position_data, client_id)
            else:
                self.logger.warning(f"No se pudo decodificar mensaje de {client_id}")
                print(f"⚠️  No se pudo decodificar el mensaje")
                
        except Exception as e:
            self.logger.error(f"Error procesando mensaje de {client_id}: {e}")
            print(f"❌ Error procesando mensaje: {e}")
            
    def decode_position_message(self, data: bytes) -> Optional[Dict]:
        """
        Decodifica un mensaje de posición
        Esta función debe ser adaptada según el protocolo específico del PDF
        """
        try:
            # Intentar diferentes formatos de decodificación
            
            # Formato 1: Asumiendo estructura simple con campos fijos
            if len(data) >= 20:
                return self.decode_format_1(data)
                
            # Formato 2: Asumiendo estructura con delimitadores
            elif b',' in data or b';' in data:
                return self.decode_format_2(data)
                
            # Formato 3: Asumiendo estructura hexadecimal
            else:
                return self.decode_format_3(data)
                
        except Exception as e:
            self.logger.error(f"Error en decodificación: {e}")
            return None
            
    def decode_format_1(self, data: bytes) -> Optional[Dict]:
        """Decodifica formato con estructura fija"""
        try:
            # Asumiendo estructura: [ID(4)][LAT(4)][LON(4)][RUMBO(2)][VELOCIDAD(2)][CHECKSUM(4)]
            if len(data) < 20:
                return None
                
            # Extraer campos (ajustar según protocolo real)
            device_id = struct.unpack('>I', data[0:4])[0]
            latitude = struct.unpack('>f', data[4:8])[0]
            longitude = struct.unpack('>f', data[8:12])[0]
            heading = struct.unpack('>H', data[12:14])[0]
            speed = struct.unpack('>H', data[14:16])[0]
            
            return {
                'device_id': device_id,
                'latitude': latitude,
                'longitude': longitude,
                'heading': heading,
                'speed': speed,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error decodificando formato 1: {e}")
            return None
            
    def decode_format_2(self, data: bytes) -> Optional[Dict]:
        """Decodifica formato con delimitadores"""
        try:
            # Convertir a string y dividir por delimitadores
            message = data.decode('ascii', errors='ignore').strip()
            
            # Buscar delimitadores comunes
            if ',' in message:
                parts = message.split(',')
            elif ';' in message:
                parts = message.split(';')
            else:
                return None
                
            # Intentar extraer campos (ajustar según protocolo real)
            if len(parts) >= 5:
                device_id = parts[0]
                latitude = float(parts[1])
                longitude = float(parts[2])
                heading = float(parts[3])
                speed = float(parts[4])
                
                return {
                    'device_id': device_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'heading': heading,
                    'speed': speed,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error decodificando formato 2: {e}")
            return None
            
    def decode_format_3(self, data: bytes) -> Optional[Dict]:
        """Decodifica formato hexadecimal"""
        try:
            # Convertir a hexadecimal y buscar patrones
            hex_str = binascii.hexlify(data).decode('ascii')
            
            # Buscar patrones específicos (ajustar según protocolo real)
            if len(hex_str) >= 16:
                # Ejemplo: extraer valores hexadecimales
                device_id = int(hex_str[0:8], 16)
                lat_raw = int(hex_str[8:16], 16)
                lon_raw = int(hex_str[16:24], 16)
                
                # Convertir a coordenadas (ajustar fórmula según protocolo)
                latitude = lat_raw / 1000000.0
                longitude = lon_raw / 1000000.0
                
                return {
                    'device_id': device_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'heading': 0,  # Por defecto
                    'speed': 0,    # Por defecto
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error decodificando formato 3: {e}")
            return None
            
    def display_position(self, position_data: Dict, client_id: str):
        """Muestra la información de posición en pantalla"""
        print(f"\n📍 POSICIÓN RECIBIDA de {client_id}")
        print(f"   ID Equipo: {position_data['device_id']}")
        print(f"   Latitud: {position_data['latitude']:.6f}°")
        print(f"   Longitud: {position_data['longitude']:.6f}°")
        print(f"   Rumbo: {position_data['heading']}°")
        print(f"   Velocidad: {position_data['speed']} km/h")
        print(f"   Timestamp: {position_data['timestamp']}")
        print("-" * 50)
        
    def get_status(self) -> Dict:
        """Retorna el estado actual del servidor"""
        return {
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'connected_clients': len(self.clients),
            'total_messages': self.message_count,
            'clients': list(self.clients.keys())
        }

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 SERVIDOR TCP PROTOCOLO TQ")
    print("=" * 60)
    
    # Crear y configurar servidor
    server = TQServer(host='0.0.0.0', port=8080)
    
    try:
        # Iniciar servidor en un hilo separado
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Bucle principal para comandos
        while True:
            command = input("\nComandos disponibles:\n"
                          "  status - Mostrar estado del servidor\n"
                          "  clients - Mostrar clientes conectados\n"
                          "  quit - Salir\n"
                          "Comando: ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'status':
                status = server.get_status()
                print(f"\n📊 ESTADO DEL SERVIDOR:")
                print(f"   Ejecutándose: {status['running']}")
                print(f"   Host: {status['host']}")
                print(f"   Puerto: {status['port']}")
                print(f"   Clientes conectados: {status['connected_clients']}")
                print(f"   Mensajes totales: {status['total_messages']}")
            elif command == 'clients':
                status = server.get_status()
                if status['clients']:
                    print(f"\n🔗 CLIENTES CONECTADOS ({len(status['clients'])}):")
                    for client in status['clients']:
                        print(f"   - {client}")
                else:
                    print("\n📭 No hay clientes conectados")
            else:
                print("❌ Comando no válido")
                
    except KeyboardInterrupt:
        print("\n🛑 Interrupción detectada...")
    finally:
        server.stop()
        print("👋 Servidor cerrado correctamente")

if __name__ == "__main__":
    main()

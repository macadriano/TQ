#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor TQ Simplificado - Solo procesa mensajes del tipo RECORRIDO61674_011025.txt
Versión limpia y optimizada
"""

import socket
import threading
import logging
import csv
import os
import math
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# Importar las funciones existentes
import funciones
import protocolo

class TQServerSimplificado:
    def __init__(self, host: str = '0.0.0.0', port: int = 5003, 
                 udp_host: str = '179.43.115.190', udp_port: int = 7007):
        self.host = host
        self.port = port
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.server_socket = None
        self.clients: Dict[str, socket.socket] = {}
        self.running = False
        self.message_count = 0
        
        # Configurar logging
        self.setup_logging()
        
        # Configurar archivos
        self.positions_file = 'positions_log.csv'
        self.rpg_log_file = 'rpg_messages.log'
        self.setup_positions_file()
        self.setup_rpg_log_file()

    def setup_logging(self):
        """Configura el sistema de logging"""
        self.logger = logging.getLogger('TQServerSimplificado')
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler('tq_server_simplificado.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def setup_positions_file(self):
        """Configura el archivo de registro de posiciones"""
        try:
            file_exists = os.path.exists(self.positions_file)
            with open(self.positions_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                if not file_exists:
                    writer.writerow(['ID', 'LATITUD', 'LONGITUD', 'RUMBO', 'VELOCIDAD_KMH', 'VELOCIDAD_NUDOS', 'FECHAGPS', 'HORAGPS', 'FECHARECIBIDO'])
                    self.logger.info(f"Archivo de posiciones creado: {self.positions_file}")
                else:
                    self.logger.info(f"Archivo de posiciones existente: {self.positions_file}")
        except Exception as e:
            self.logger.error(f"Error configurando archivo de posiciones: {e}")
            
    def setup_rpg_log_file(self):
        """Configura el archivo de registro de mensajes RPG"""
        try:
            file_exists = os.path.exists(self.rpg_log_file)
            if not file_exists:
                with open(self.rpg_log_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Log de mensajes RPG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("# Formato: TIMESTAMP | MENSAJE_ORIGINAL | MENSAJE_RPG | ESTADO_ENVIO\n")
                    f.write("-" * 80 + "\n")
                self.logger.info(f"Archivo de log RPG creado: {self.rpg_log_file}")
            else:
                self.logger.info(f"Archivo de log RPG existente: {self.rpg_log_file}")
        except Exception as e:
            self.logger.error(f"Error configurando archivo de log RPG: {e}")

    def is_valid_message_format(self, hex_data: str) -> bool:
        """
        Verifica si el mensaje tiene el formato correcto del protocolo TQ
        Detecta por características del formato, no por ID específico
        """
        try:
            # Características del formato TQ:
            # 1. Debe empezar con "24" (header del protocolo TQ)
            # 2. Debe tener longitud específica (aproximadamente 100+ caracteres)
            # 3. Debe contener solo caracteres hexadecimales
            # 4. NO debe ser mensaje NMEA (que empiezan con "*" o contienen comas)
            
            # Verificar que empiece con "24" (protocolo TQ)
            if not hex_data.startswith('24'):
                return False
            
            # Verificar longitud (mensajes TQ suelen tener 80+ caracteres)
            if len(hex_data) < 60 or len(hex_data) > 200:
                return False
            
            # Verificar que solo contenga caracteres hexadecimales válidos
            if not all(c in '0123456789abcdefABCDEF' for c in hex_data):
                return False
            
            # Verificar que NO sea mensaje NMEA
            # Los mensajes NMEA contienen comas y empiezan con "*"
            if ',' in hex_data or hex_data.startswith('*'):
                return False
            
            # Verificar patrón específico del protocolo TQ
            # Los mensajes TQ tienen una estructura específica con timestamps y coordenadas
            # Buscar patrones típicos del protocolo TQ
            
            # Verificar que tenga la estructura típica: [header][id][timestamp][coords][data]
            # El mensaje debe tener al menos 12 caracteres para el header + ID
            if len(hex_data) < 12:
                return False
            
            # Verificar que no sea un mensaje de texto (NMEA)
            try:
                # Intentar decodificar como ASCII para detectar NMEA
                ascii_message = bytes.fromhex(hex_data).decode('ascii', errors='ignore')
                if ascii_message.startswith('*') or ',' in ascii_message:
                    return False
            except:
                pass
            
            # Verificación adicional: el mensaje TQ debe tener una estructura específica
            # Los mensajes TQ reales tienen patrones específicos en sus primeros bytes
            # Verificar que no sea un mensaje NMEA codificado en hex
            if hex_data.startswith('2a'):  # 2a = '*' en ASCII
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error validando formato de mensaje: {e}")
            return False

    def decode_position_message(self, hex_data: str) -> Optional[Dict]:
        """
        Decodifica un mensaje de posición del protocolo TQ simplificado
        """
        try:
            # Usar las funciones existentes del protocolo
            device_id = protocolo.getIDok(hex_data)
            
            # Extraer fecha y hora GPS
            fecha_gps = protocolo.getFECHA_GPS_TQ(hex_data)
            hora_gps = protocolo.getHORA_GPS_TQ(hex_data)
            
            # Extraer coordenadas
            latitude = protocolo.getLATchino(hex_data)
            longitude = protocolo.getLONchino(hex_data)
            
            # Extraer velocidad y rumbo
            speed_knots = protocolo.getVELchino(hex_data)
            heading = protocolo.getRUMBOchino(hex_data)
            
            # Convertir velocidad a km/h
            speed_kmh = speed_knots * 1.852
            
            # Crear timestamp GPS
            gps_timestamp = self.parse_gps_datetime(fecha_gps, hora_gps)
            
            return {
                'device_id': device_id,
                'latitude': latitude,
                'longitude': longitude,
                'speed_kmh': speed_kmh,
                'speed_knots': speed_knots,
                'heading': heading,
                'gps_timestamp': gps_timestamp,
                'fecha_gps': fecha_gps,
                'hora_gps': hora_gps
            }
            
        except Exception as e:
            self.logger.error(f"Error decodificando mensaje de posición: {e}")
            return None

    def parse_gps_datetime(self, fecha_gps: str, hora_gps: str) -> datetime:
        """
        Parsea fecha y hora GPS del protocolo TQ a datetime
        """
        try:
            # Formato de fecha: DD/MM/YY
            if '/' in fecha_gps:
                day, month, year = fecha_gps.split('/')
                year = 2000 + int(year)
            else:
                # Formato alternativo
                day, month, year = fecha_gps[:2], fecha_gps[2:4], fecha_gps[4:6]
                year = 2000 + int(year)
            
            # Formato de hora: HH:MM:SS
            hour, minute, second = hora_gps.split(':')
            
            return datetime(year, int(month), int(day), int(hour), int(minute), int(second))
            
        except Exception as e:
            self.logger.warning(f"Error parseando fecha GPS: {e}")
            return datetime.now()

    def save_position_to_csv(self, position_data: Dict):
        """
        Guarda la posición en el archivo CSV
        """
        try:
            with open(self.positions_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    position_data['device_id'],
                    position_data['latitude'],
                    position_data['longitude'],
                    position_data['heading'],
                    position_data['speed_kmh'],
                    position_data['speed_knots'],
                    position_data['fecha_gps'],
                    position_data['hora_gps'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ])
        except Exception as e:
            self.logger.error(f"Error guardando posición en CSV: {e}")

    def create_rpg_message(self, position_data: Dict) -> str:
        """
        Crea un mensaje RPG con formato correcto
        """
        try:
            # Formatear coordenadas para RPG
            lat_str = f"{abs(position_data['latitude']):.6f}"
            lon_str = f"{abs(position_data['longitude']):.6f}"
            
            # Agregar signo según la dirección
            if position_data['latitude'] < 0:
                lat_str += 'S'
            else:
                lat_str += 'N'
                
            if position_data['longitude'] < 0:
                lon_str += 'W'
            else:
                lon_str += 'E'
            
            # Crear mensaje RPG
            rpg_message = f"*HQ,{position_data['device_id']},V1,{position_data['hora_gps']},A,{lat_str},{lon_str},{position_data['speed_kmh']:.1f},{position_data['heading']:.0f},{position_data['fecha_gps']},#"
            
            return rpg_message
            
        except Exception as e:
            self.logger.error(f"Error creando mensaje RPG: {e}")
            return ""

    def send_rpg_message(self, rpg_message: str) -> bool:
        """
        Envía el mensaje RPG al servidor UDP
        """
        try:
            # Crear socket UDP
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Enviar mensaje
            udp_socket.sendto(rpg_message.encode('utf-8'), (self.udp_host, self.udp_port))
            udp_socket.close()
            
            self.logger.info(f"Mensaje RPG enviado: {rpg_message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enviando mensaje RPG: {e}")
            return False

    def log_rpg_message(self, original_message: str, rpg_message: str, status: str):
        """
        Registra el mensaje RPG en el archivo de log
        """
        try:
            with open(self.rpg_log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"{timestamp} | {original_message[:50]}... | {rpg_message} | {status}\n")
        except Exception as e:
            self.logger.error(f"Error registrando mensaje RPG: {e}")

    def process_message(self, data: bytes, client_address: Tuple[str, int]):
        """
        Procesa un mensaje recibido del cliente
        """
        try:
            # Log del mensaje recibido
            self.logger.info(f"Mensaje recibido de {client_address}: {data[:50]}...")
            
            # PRIMERO: Verificar si es mensaje NMEA (texto)
            try:
                text_message = data.decode('utf-8', errors='ignore')
                if text_message.startswith('*') or ',' in text_message:
                    self.logger.warning(f"Mensaje NMEA descartado de {client_address}: {text_message[:50]}...")
                    return
            except:
                pass
            
            # SEGUNDO: Verificar si es mensaje NMEA codificado en hex
            hex_data = data.hex()
            if hex_data.startswith('2a'):  # 2a = '*' en ASCII
                self.logger.warning(f"Mensaje NMEA en hex descartado de {client_address}: {hex_data[:50]}...")
                return
            
            # Verificar formato del mensaje
            if not self.is_valid_message_format(hex_data):
                self.logger.warning(f"Mensaje con formato inválido descartado de {client_address}: {hex_data[:50]}...")
                return
            
            # Log del mensaje TQ válido
            self.logger.info(f"Mensaje TQ válido recibido de {client_address}: {hex_data[:50]}...")
            
            # Decodificar mensaje
            position_data = self.decode_position_message(hex_data)
            if not position_data:
                self.logger.warning(f"Error decodificando mensaje de {client_address}")
                return
            
            # Guardar posición
            self.save_position_to_csv(position_data)
            
            # Crear y enviar mensaje RPG
            rpg_message = self.create_rpg_message(position_data)
            if rpg_message:
                success = self.send_rpg_message(rpg_message)
                status = "ENVIADO" if success else "ERROR_ENVIO"
                self.log_rpg_message(hex_data, rpg_message, status)
            
            # Log de posición procesada
            self.logger.info(f"Posición procesada: ID={position_data['device_id']}, "
                           f"Lat={position_data['latitude']:.6f}, Lon={position_data['longitude']:.6f}, "
                           f"Vel={position_data['speed_kmh']:.1f} km/h, Rumbo={position_data['heading']:.0f}°")
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {e}")

    def handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """
        Maneja la conexión de un cliente
        """
        try:
            self.logger.info(f"Cliente conectado: {client_address}")
            
            while self.running:
                try:
                    # Recibir datos
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Procesar mensaje
                    self.process_message(data, client_address)
                    self.message_count += 1
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    self.logger.error(f"Error manejando cliente {client_address}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error en conexión con cliente {client_address}: {e}")
        finally:
            client_socket.close()
            self.logger.info(f"Cliente desconectado: {client_address}")

    def start_server(self):
        """
        Inicia el servidor TCP
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Timeout para permitir verificación de self.running
            
            self.running = True
            self.logger.info(f"Servidor TQ Simplificado iniciado en {self.host}:{self.port}")
            self.logger.info(f"Reenvío RPG a {self.udp_host}:{self.udp_port}")
            self.logger.info("Solo procesa mensajes del formato RECORRIDO61674_011025.txt")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_socket.settimeout(5.0)  # Timeout para evitar conexiones colgadas
                    
                    # Crear hilo para manejar el cliente
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error aceptando conexión: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error iniciando servidor: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        """
        Detiene el servidor
        """
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("Servidor detenido")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Servidor TQ Simplificado')
    parser.add_argument('--host', default='0.0.0.0', help='Host del servidor')
    parser.add_argument('--port', type=int, default=5003, help='Puerto del servidor')
    parser.add_argument('--udp-host', default='179.43.115.190', help='Host UDP para reenvío RPG')
    parser.add_argument('--udp-port', type=int, default=7007, help='Puerto UDP para reenvío RPG')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔧 SERVIDOR TQ SIMPLIFICADO")
    print("=" * 70)
    print(f"📡 Servidor: {args.host}:{args.port}")
    print(f"🎯 Reenvío RPG: {args.udp_host}:{args.udp_port}")
    print("📋 Solo procesa mensajes del formato RECORRIDO61674_011025.txt")
    print("=" * 70)
    
    # Crear servidor
    server = TQServerSimplificado(
        host=args.host,
        port=args.port,
        udp_host=args.udp_host,
        udp_port=args.udp_port
    )
    
    try:
        # Iniciar servidor
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")
        server.stop_server()
        print("✅ Servidor detenido")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor TCP para Protocolo TQ con conversión a RPG y reenvío UDP
Maneja conexiones de equipos GPS, decodifica mensajes de posición,
convierte al protocolo RPG usando las funciones existentes y reenvía por UDP
"""

import socket
import threading
import time
import logging
import struct
import binascii
import csv
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

# Importar las funciones y protocolos existentes
import funciones
import protocolo

class TQServerRPG:
    def __init__(self, host: str = '0.0.0.0', port: int = 5003, 
                 udp_host: str = '179.43.115.190', udp_port: int = 7007):
        """
        Inicializa el servidor TQ con funcionalidad RPG
        
        Args:
            host: Dirección IP del servidor TCP
            port: Puerto del servidor TCP
            udp_host: Dirección IP para reenvío UDP
            udp_port: Puerto para reenvío UDP
        """
        self.host = host
        self.port = port
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.server_socket = None
        self.clients: Dict[str, socket.socket] = {}
        self.running = False
        
        # Configurar logging
        self.setup_logging()
        
        # Contador de mensajes procesados
        self.message_count = 0
        
        # Configurar archivo de registro de posiciones
        self.positions_file = 'positions_log.csv'
        self.setup_positions_file()
        
        # Configurar archivo de registro de mensajes RPG
        self.rpg_log_file = 'rpg_messages.log'
        self.setup_rpg_log_file()
        
        # Variable para almacenar el TerminalID
        self.terminal_id = ""
        
        # Socket UDP para reenvío
        self.udp_socket = None
        self.setup_udp_socket()

    def setup_logging(self):
        """Configura el sistema de logging"""
        # Crear logger
        self.logger = logging.getLogger('TQServerRPG')
        self.logger.setLevel(logging.INFO)
        
        # Crear formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para archivo
        file_handler = logging.FileHandler('tq_server_rpg.log', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers al logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def setup_positions_file(self):
        """Configura el archivo de registro de posiciones"""
        try:
            # Verificar si el archivo existe
            file_exists = os.path.exists(self.positions_file)
            
            # Crear o abrir el archivo para escribir
            with open(self.positions_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Si el archivo no existe, escribir el encabezado
                if not file_exists:
                    writer.writerow(['ID', 'LATITUD', 'LONGITUD', 'RUMBO', 'VELOCIDAD', 'FECHAGPS', 'FECHARECIBIDO'])
                    self.logger.info(f"Archivo de posiciones creado: {self.positions_file}")
                else:
                    self.logger.info(f"Archivo de posiciones existente: {self.positions_file}")
                    
        except Exception as e:
            self.logger.error(f"Error configurando archivo de posiciones: {e}")
            
    def setup_rpg_log_file(self):
        """Configura el archivo de registro de mensajes RPG"""
        try:
            # Verificar si el archivo existe
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
            
    def setup_udp_socket(self):
        """Configura el socket UDP para reenvío"""
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.logger.info(f"Socket UDP configurado para reenvío a {self.udp_host}:{self.udp_port}")
        except Exception as e:
            self.logger.error(f"Error configurando socket UDP: {e}")
            self.udp_socket = None

    def save_position_to_file(self, position_data: Dict):
        """Guarda una posición en el archivo CSV"""
        try:
            # Preparar los datos para el archivo
            device_id = position_data.get('device_id', '')
            latitude = position_data.get('latitude', 0.0)
            longitude = position_data.get('longitude', 0.0)
            heading = position_data.get('heading', 0.0)
            speed = position_data.get('speed', 0.0)
            
            # Filtrar posiciones con coordenadas 0,0 (sin señal GPS)
            if abs(latitude) < 0.000001 and abs(longitude) < 0.000001:
                self.logger.info(f"Posición filtrada (sin señal GPS): ID={device_id}, Lat={latitude:.6f}, Lon={longitude:.6f}")
                return
            
            # Fecha GPS (si está disponible en NMEA)
            gps_date = ''
            if 'nmea_date' in position_data and 'nmea_timestamp' in position_data:
                try:
                    # Formatear fecha GPS: DDMMYY HHMMSS
                    date_str = position_data['nmea_date']
                    time_str = position_data['nmea_timestamp']
                    if len(date_str) == 6 and len(time_str) == 6:
                        day = date_str[0:2]
                        month = date_str[2:4]
                        year = '20' + date_str[4:6]
                        hour = time_str[0:2]
                        minute = time_str[2:4]
                        second = time_str[4:6]
                        gps_date = f"{year}-{month}-{day} {hour}:{minute}:{second}"
                except:
                    gps_date = ''
            
            # Fecha de recepción
            received_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Escribir en el archivo CSV
            with open(self.positions_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    device_id,
                    f"{latitude:.6f}",
                    f"{longitude:.6f}",
                    f"{heading:.1f}",
                    f"{speed:.1f}",
                    gps_date,
                    received_date
                ])
                
            self.logger.info(f"Posición guardada en archivo: ID={device_id}, Lat={latitude:.6f}, Lon={longitude:.6f}")
            
        except Exception as e:
            self.logger.error(f"Error guardando posición en archivo: {e}")
            
    def log_rpg_message(self, original_message: str, rpg_message: str, status: str):
        """Guarda un mensaje RPG en el archivo de log"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.rpg_log_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} | {original_message} | {rpg_message} | {status}\n")
            self.logger.info(f"Mensaje RPG loggeado: {status}")
        except Exception as e:
            self.logger.error(f"Error loggeando mensaje RPG: {e}")

    def process_message_with_rpg(self, data: bytes, client_id: str):
        """
        Procesa un mensaje recibido del cliente, lo convierte a RPG usando las funciones existentes y reenvía por UDP
        """
        self.message_count += 1
        
        # Log del mensaje raw
        hex_data = funciones.bytes2hexa(data)
        self.logger.info(f"Msg #{self.message_count} de {client_id}: {hex_data}")
        print(f"📨 Msg #{self.message_count} de {client_id}")
        print(f"   Raw: {hex_data}")
        
        try:
            # Guardar el mensaje en el log usando la función existente
            funciones.guardarLog(hex_data)
            
            # Detectar el tipo de protocolo usando la función existente
            protocol_type = protocolo.getPROTOCOL(hex_data)
            self.logger.info(f"Tipo de protocolo detectado: {protocol_type}")
            
            if protocol_type == "22":
                # Protocolo de posición - convertir a RPG y reenviar
                
                # ACTUALIZAR: Extraer y guardar el ID del mensaje de posición
                position_id = protocolo.getIDok(hex_data)
                if position_id:
                    self.terminal_id = position_id  # ACTUALIZAR el TerminalID
                    self.logger.info(f"TerminalID actualizado desde mensaje de posición: {position_id}")
                
                if len(self.terminal_id) > 0:
                    # Convertir a RPG usando la función existente
                    rpg_message = protocolo.RGPdesdeCHINO(hex_data, self.terminal_id)
                    self.logger.info(f"Mensaje RPG generado: {rpg_message}")
                    
                    # Reenviar por UDP usando la función existente
                    funciones.enviar_mensaje_udp(self.udp_host, self.udp_port, rpg_message)
                    
                    # Log del mensaje RPG
                    self.log_rpg_message(hex_data, rpg_message, "ENVIADO")
                    
                    print(f"🔄 Mensaje RPG enviado por UDP: {rpg_message}")
                    
                    # También guardar en el log UDP
                    funciones.guardarLogUDP(rpg_message)
                    
                else:
                    self.logger.warning("TerminalID no disponible para conversión RPG")
                    self.log_rpg_message(hex_data, "", "SIN_TERMINAL_ID")
                    
            elif protocol_type == "01":
                # Protocolo de registro - obtener TerminalID usando la función CORREGIDA
                # Ahora usa el mismo método que tq_server.py (primeros 4 bytes)
                full_terminal_id = protocolo.getIDok(hex_data)
                self.terminal_id = full_terminal_id  # Ya viene con solo los últimos 5 caracteres
                
                self.logger.info(f"TerminalID extraído con método corregido: {full_terminal_id}")
                self.logger.info(f"TerminalID para RPG: {self.terminal_id}")
                funciones.guardarLog(f"TerminalID={self.terminal_id}")
                print(f"🆔 TerminalID configurado: {self.terminal_id}")
                
                # Enviar respuesta usando la función existente
                response = protocolo.Enviar0100(self.terminal_id)
                # Aquí podrías enviar la respuesta al cliente si es necesario
                
            else:
                # Otro tipo de protocolo - intentar decodificar como TQ
                self.logger.info(f"Protocolo {protocol_type} - intentando decodificación TQ")
                position_data = self.decode_position_message(data)
                
                if position_data:
                    self.logger.info(f"Posición decodificada: {position_data}")
                    self.display_position(position_data, client_id)
                    
                    # Guardar posición en archivo CSV
                    self.save_position_to_file(position_data)
                    
                    # Si tenemos TerminalID, convertir a RPG
                    if len(self.terminal_id) > 0:
                        # Intentar convertir usando el protocolo personal si es compatible
                        try:
                            rpg_message = protocolo.RGPdesdePERSONAL(hex_data, self.terminal_id)
                            if rpg_message:
                                # Reenviar por UDP
                                funciones.enviar_mensaje_udp(self.udp_host, self.udp_port, rpg_message)
                                self.log_rpg_message(hex_data, rpg_message, "ENVIADO_PERSONAL")
                                print(f"🔄 Mensaje RPG personal enviado por UDP: {rpg_message}")
                        except:
                            self.logger.warning("No se pudo convertir a RPG personal")
                    else:
                        self.logger.warning("TerminalID no disponible para conversión RPG")
                        
                else:
                    self.logger.warning(f"No se pudo decodificar mensaje de {client_id}")
                    print(f"⚠️  No se pudo decodificar el mensaje")
                    
        except Exception as e:
            self.logger.error(f"Error procesando mensaje de {client_id}: {e}")
            print(f"❌ Error procesando mensaje: {e}")
            self.log_rpg_message(hex_data, "", f"ERROR:{str(e)}")

    def decode_position_message(self, data: bytes) -> Optional[Dict]:
        """Decodifica un mensaje de posición del protocolo TQ"""
        try:
            # Convertir a hexadecimal
            hex_str = binascii.hexlify(data).decode('ascii')
            
            # Extraer ID del dispositivo (primeros 4 bytes)
            try:
                device_id = int(hex_str[0:8], 16)
            except:
                device_id = 0
            
            # Extraer coordenadas (posiciones 8-15 para latitud, 16-23 para longitud)
            try:
                lat_raw = int(hex_str[8:16], 16)
                lon_raw = int(hex_str[16:24], 16)
                
                # Convertir a coordenadas decimales con escala 1000000.0
                latitude = lat_raw / 1000000.0
                longitude = lon_raw / 1000000.0
                
            except:
                latitude = 0.0
                longitude = 0.0
            
            # Buscar velocidad y rumbo en el resto del mensaje
            speed = 0
            heading = 0
            
            # Analizar cada grupo de 4 bytes buscando valores razonables
            data_bytes = bytes.fromhex(hex_str)
            for i in range(24, len(data_bytes) - 4, 4):
                chunk = data_bytes[i:i+4]
                val = int.from_bytes(chunk, byteorder='big', signed=False)
                
                # Velocidad (0-200 km/h)
                if 0 <= val <= 200 and speed == 0:
                    speed = val
                
                # Rumbo (0-360 grados)
                if 0 <= val <= 360 and heading == 0:
                    heading = val
            
            return {
                'device_id': device_id,
                'latitude': latitude,
                'longitude': longitude,
                'heading': heading,
                'speed': speed,
                'timestamp': datetime.now().isoformat()
            }
                
        except Exception as e:
            self.logger.error(f"Error en decodificación: {e}")
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
            'udp_host': self.udp_host,
            'udp_port': self.udp_port,
            'terminal_id': self.terminal_id,
            'connected_clients': len(self.clients),
            'total_messages': self.message_count,
            'clients': list(self.clients.keys())
        }
        
    def start(self):
        """Inicia el servidor TCP"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            self.logger.info(f"Servidor TQ+RPG iniciado en {self.host}:{self.port}")
            print(f"🚀 Servidor TQ+RPG iniciado en {self.host}:{self.port}")
            print(f"📡 UDP configurado para reenvío a {self.udp_host}:{self.udp_port}")
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
        if self.udp_socket:
            self.udp_socket.close()
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
                    
                # Procesar el mensaje recibido con conversión RPG y reenvío UDP
                self.process_message_with_rpg(data, client_id)
                
        except Exception as e:
            self.logger.error(f"Error manejando cliente {client_id}: {e}")
            print(f"❌ Error con cliente {client_id}: {e}")
            
        finally:
            # Limpiar conexión
            client_socket.close()
            del self.clients[client_id]
            self.logger.info(f"Conexión cerrada: {client_id}")
            print(f"🔌 Conexión cerrada: {client_id}")

    def show_terminal_info(self):
        """Muestra información detallada del TerminalID"""
        if self.terminal_id:
            print(f"\n🆔 INFORMACIÓN DEL TERMINAL ID:")
            print(f"   ID para RPG: {self.terminal_id}")
            print(f"   Longitud: {len(self.terminal_id)} caracteres")
            print(f"   Tipo: {type(self.terminal_id)}")
            
            # Mostrar el ID en diferentes formatos
            try:
                # Intentar convertir a entero si es posible
                id_int = int(self.terminal_id)
                print(f"   Valor numérico: {id_int}")
                print(f"   Hexadecimal: {id_int:05X}")
            except:
                print(f"   Valor: {self.terminal_id}")
                
        else:
            print("\n⚠️  No hay TerminalID configurado")
            print("   Esperando mensaje de registro del equipo...")
            print("   El equipo debe enviar un mensaje de tipo '01' primero")

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 SERVIDOR TCP PROTOCOLO TQ + RPG")
    print("=" * 60)
    
    # Crear y configurar servidor
    server = TQServerRPG(host='0.0.0.0', port=5003, 
                         udp_host='179.43.115.190', udp_port=7007)
    
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
                          "  positions - Ver últimas posiciones guardadas\n"
                          "  rpg - Ver últimas entradas del log RPG\n"
                          "  terminal - Mostrar TerminalID actual\n"
                          "  idinfo - Información detallada del ID del equipo\n"
                          "  quit - Salir\n"
                          "Comando: ").strip().lower()
            
            if command == 'quit':
                break
            elif command == 'status':
                status = server.get_status()
                print(f"\n📊 ESTADO DEL SERVIDOR:")
                print(f"   Ejecutándose: {status['running']}")
                print(f"   Host TCP: {status['host']}")
                print(f"   Puerto TCP: {status['port']}")
                print(f"   Host UDP: {status['udp_host']}")
                print(f"   Puerto UDP: {status['udp_port']}")
                print(f"   TerminalID: {status['terminal_id']}")
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
            elif command == 'positions':
                # Implementar si es necesario
                print("Comando positions no implementado aún")
            elif command == 'rpg':
                # Implementar si es necesario
                print("Comando rpg no implementado aún")
            elif command == 'terminal':
                server.show_terminal_info()
            elif command == 'idinfo':
                server.show_terminal_info()
            else:
                print("❌ Comando no válido")
                
    except KeyboardInterrupt:
        print("\n🛑 Interrupción detectada...")
    finally:
        server.stop()
        print("👋 Servidor cerrado correctamente")

if __name__ == "__main__":
    main()

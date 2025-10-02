#dkdkdkdk
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
        self.terminal_id = ""
        
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
        Procesa un mensaje recibido del cliente - SIGUIENDO EL FLUJO EXACTO DEL SERVIDOR ORIGINAL
        """
        try:
            self.message_count += 1
            client_id = f"{client_address[0]}:{client_address[1]}"
            
            # Log del mensaje raw - USAR FUNCIONES ORIGINALES
            hex_data = funciones.bytes2hexa(data)
            self.logger.info(f"Msg #{self.message_count} de {client_id}: {hex_data}")
            print(f"📨 Msg #{self.message_count} de {client_id}")
            print(f"   Raw: {hex_data}")
            
            # Guardar el mensaje en el log - USAR FUNCIONES ORIGINALES
            funciones.guardarLog(hex_data)
            
            # DETECTAR TIPO DE PROTOCOLO - EXACTO COMO EL ORIGINAL
            protocol_type = protocolo.getPROTOCOL(hex_data)
            self.logger.info(f"Tipo de protocolo detectado: {protocol_type}")
            
            if protocol_type == "22":
                # Protocolo de posición - convertir a RPG y reenviar
                
                # IMPORTANTE: Extraer y guardar el ID del mensaje de posición
                position_id = protocolo.getIDok(hex_data)
                if position_id:
                    self.terminal_id = position_id  # ACTUALIZAR el TerminalID
                    self.logger.info(f"TerminalID actualizado desde mensaje de posición: {position_id}")
                    print(f"🆔 TerminalID actualizado: {position_id}")
                
                if len(self.terminal_id) > 0:
                    # Crear mensaje RPG SIMPLE - formato que funciona con el servidor receptor
                    rpg_message = self.create_simple_rpg_message(hex_data)
                    self.logger.info(f"Mensaje RPG generado: {rpg_message}")
                    
                    # Reenviar por UDP - USAR FUNCIONES ORIGINALES
                    funciones.enviar_mensaje_udp(self.udp_host, self.udp_port, rpg_message)
                    
                    # Log del mensaje RPG
                    self.log_rpg_message(hex_data, rpg_message, "ENVIADO")
                    
                    print(f"🔄 Mensaje RPG enviado por UDP: {rpg_message}")
                    
                    # También guardar en el log UDP - USAR FUNCIONES ORIGINALES
                    funciones.guardarLogUDP(rpg_message)
                    
                else:
                    self.logger.warning("TerminalID no disponible para conversión RPG")
                    self.log_rpg_message(hex_data, "", "SIN_TERMINAL_ID")
                    
            elif protocol_type == "01":
                # Protocolo de registro - obtener TerminalID
                full_terminal_id = protocolo.getIDok(hex_data)
                self.terminal_id = full_terminal_id
                
                self.logger.info(f"TerminalID extraído: {full_terminal_id}")
                funciones.guardarLog(f"TerminalID={self.terminal_id}")
                print(f"🆔 TerminalID configurado: {self.terminal_id}")
                
                # Enviar respuesta
                response = protocolo.Enviar0100(self.terminal_id)
                
            else:
                self.logger.warning(f"Tipo de protocolo no soportado: {protocol_type}")
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {e}")
            print(f"❌ Error procesando mensaje: {e}")
            self.log_rpg_message(hex_data, "", f"ERROR:{str(e)}")

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
            self.logger.info("Procesa mensajes TQ binarios y los convierte a formato RPG para reenvío UDP")
            
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

    def create_simple_rpg_message(self, hex_data: str) -> str:
        """
        Crea un mensaje RPG simple en el formato que funciona con el servidor receptor
        Formato: >RGP021025204356-3441.9250-05835>
        """
        try:
            # Extraer fecha y hora GPS
            fecha_gps = protocolo.getFECHA_GPS_TQ(hex_data)  # "02/10/25"
            hora_gps = protocolo.getHORA_GPS_TQ(hex_data)    # "20:43:56"
            
            # Convertir fecha de DD/MM/YY a DDMMYY
            if '/' in fecha_gps:
                day, month, year = fecha_gps.split('/')
                fecha_rpg = f"{day}{month}{year}"
            else:
                fecha_rpg = fecha_gps
            
            # Convertir hora de HH:MM:SS a HHMMSS
            if ':' in hora_gps:
                hora_rpg = hora_gps.replace(':', '')
            else:
                hora_rpg = hora_gps
            
            # Extraer coordenadas
            latitude = protocolo.getLATchino(hex_data)
            longitude = protocolo.getLONchino(hex_data)
            
            # Validar coordenadas
            if abs(latitude) < 0.000001 and abs(longitude) < 0.000001:
                return ""  # No enviar si no hay coordenadas válidas
            
            # Formatear coordenadas para RPG simple
            # Latitud: convertir a formato GGMM.MMMM
            lat_grados = abs(int(latitude))
            lat_minutos = abs((latitude - int(latitude)) * 60)
            lat_formatted = f"{lat_grados:02d}{lat_minutos:06.3f}"
            
            # Longitud: convertir a formato GGGMM.MMMM
            lon_grados = abs(int(longitude))
            lon_minutos = abs((longitude - int(longitude)) * 60)
            lon_formatted = f"{lon_grados:03d}{lon_minutos:06.3f}"
            
            # Crear mensaje RPG simple
            rpg_message = f">RGP{fecha_rpg}{hora_rpg}-{lat_formatted}-{lon_formatted}>"
            
            return rpg_message
            
        except Exception as e:
            self.logger.error(f"Error creando mensaje RPG simple: {e}")
            return ""


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
    print("📋 Procesa mensajes TQ binarios y los convierte a formato RPG para reenvío UDP")
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

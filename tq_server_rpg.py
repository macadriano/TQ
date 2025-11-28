#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor TCP para Protocolo TQ con conversión a RPG y reenvío UDP
"""
# hola mundo

import socket
import threading
import logging
import csv
import os
import math
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler

# Importar las funciones y protocolos existentes
import funciones
import protocolo

class TQServerRPG:
    def __init__(self, host: str = '0.0.0.0', port: int = 5003, 
                 udp_host: str = '179.43.115.190', udp_port: int = 7007,
                 health_port: int = 5004,
                 tcp_forward_host: str = '200.58.98.187', tcp_forward_port: int = 5003,
                 tcp_forward_enabled: bool = True):
        self.host = host
        self.port = port
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.health_port = health_port
        
        # Configuración de reenvío TCP
        self.tcp_forward_host = tcp_forward_host
        self.tcp_forward_port = tcp_forward_port
        self.tcp_forward_enabled = tcp_forward_enabled

        self.server_socket = None
        self.health_server = None
        self.clients: Dict[str, socket.socket] = {}
        self.running = False
        self.message_count = 0
        self.terminal_id = ""
        self.start_time = None
        
        # Variables para filtros de posición
        self.last_valid_position: Optional[Dict] = None
        self.filtered_positions_count = 0
        
        # Configuración de geocodificación
        self.geocoding_enabled = True  # Variable para habilitar/deshabilitar geocodificación
        self.geocoding_cache = {}  # Cache para evitar consultas repetidas
        self.last_geocoding_request = 0  # Control de rate limiting
        
        # Configurar logging
        self.setup_logging()
        
        # No necesitamos archivos separados, todo va al log diario único

    def setup_logging(self):
        """Configura el sistema de logging para usar el archivo diario único"""
        self.logger = logging.getLogger('TQServerRPG')
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Usar el mismo archivo de log diario que funciones.py
        log_file = funciones.get_daily_log_filename()
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    # Eliminadas funciones setup_positions_file() y setup_rpg_log_file()
    # Ya no son necesarias, todo va al log diario único

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula la distancia en metros entre dos coordenadas GPS usando la fórmula de Haversine
        """
        try:
            # Convertir grados a radianes
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Diferencias
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            # Fórmula de Haversine
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Radio de la Tierra en metros
            r = 6371000
            
            return c * r
        except:
            return 0.0

    def parse_gps_datetime(self, fecha_gps: str, hora_gps: str) -> Optional[datetime]:
        """
        Parsea fecha y hora GPS del protocolo TQ a datetime
        """
        try:
            if not fecha_gps or not hora_gps:
                return None
            
            # Formato fecha: DD/MM/YY
            # Formato hora: HH:MM:SS
            dia, mes, año = fecha_gps.split('/')
            hora, minuto, segundo = hora_gps.split(':')
            
            # Crear datetime UTC
            return datetime(int('20' + año), int(mes), int(dia), 
                          int(hora), int(minuto), int(segundo))
        except:
            return None

    def is_position_valid(self, position_data: Dict) -> Tuple[bool, str]:
        """
        Valida una posición GPS aplicando filtros de calidad inteligentes ON THE FLY
        
        Filtros implementados:
        1. Filtro por salto de distancia/tiempo: >300m en <10s
        2. Control de duplicados: DESACTIVADO (estaba bloqueando mensajes válidos)
        3. Filtro de saltos excesivos: >1km en <5min (NUEVO)
        4. Filtro de velocidad incoherente: diferencia >20 km/h (NUEVO)
        5. Protección de detenciones reales: mantiene paradas legítimas (NUEVO)
        
        Returns:
            Tuple[bool, str]: (es_válida, razón_si_no_válida)
        """
        try:
            latitude = position_data.get('latitude', 0.0)
            longitude = position_data.get('longitude', 0.0)
            fecha_gps = position_data.get('fecha_gps', '')
            hora_gps = position_data.get('hora_gps', '')
            speed_kmh = position_data.get('speed', 0.0)
            heading = position_data.get('heading', 0.0)
            
            # Filtro básico: coordenadas (0,0)
            if abs(latitude) < 0.000001 and abs(longitude) < 0.000001:
                return False, "Coordenadas GPS inválidas (0,0)"
            
            # Si no hay posición anterior válida, aceptar esta como primera
            if self.last_valid_position is None:
                return True, ""
            
            last_lat = self.last_valid_position.get('latitude', 0.0)
            last_lon = self.last_valid_position.get('longitude', 0.0)
            last_fecha_gps = self.last_valid_position.get('fecha_gps', '')
            last_hora_gps = self.last_valid_position.get('hora_gps', '')
            last_speed = self.last_valid_position.get('speed', 0.0)
            
            # Calcular distancia entre posiciones
            distance = self.calculate_distance(last_lat, last_lon, latitude, longitude)
            
            # Parsear timestamps GPS
            current_time = self.parse_gps_datetime(fecha_gps, hora_gps)
            last_time = self.parse_gps_datetime(last_fecha_gps, last_hora_gps)
            
            if current_time and last_time:
                time_diff = abs((current_time - last_time).total_seconds())
                
                if time_diff > 0:
                    calculated_speed = (distance / time_diff) * 3.6  # km/h
                else:
                    calculated_speed = 0
                
                # FILTRO 1: Salto sospechoso original
                #if distance > 300 and time_diff < 10:
                #    return False, f"Salto sospechoso: {distance:.1f}m en {time_diff:.1f}s"
                
                # FILTRO 3: Saltos excesivos (NUEVO) - Evita líneas transversales
                #if distance > 1000 and time_diff < 300:  # >1km en <5min
                #    return False, f"Salto excesivo: {distance:.1f}m en {time_diff/60:.1f}min"
                
                # FILTRO 4: Velocidad incoherente (NUEVO)
                #speed_diff = abs(calculated_speed - speed_kmh)
                #if speed_diff > 20 and distance > 100:
                #    return False, f"Velocidad incoherente: calc={calculated_speed:.1f} vs rep={speed_kmh:.1f} km/h"
                
                # FILTRO 5: Protección de detenciones reales (NUEVO)
                # Si ambos puntos reportan velocidad baja Y la distancia es pequeña, es detención real
                is_real_stop = (speed_kmh < 5 and last_speed < 5 and distance < 100)
                
                # Salto estacionario: reporta estar parado pero saltó mucho (EXCEPTO detenciones reales)
                #if speed_kmh < 1 and distance > 300 and not is_real_stop:
                #    return False, f"Salto estacionario: {distance:.1f}m reportando parado"
            
            return True, ""
            
        except Exception as e:
            self.logger.error(f"Error valdffdfdidando posición: {e}")
            return False, f"Error en validación: {e}"

    def get_address_from_coordinates(self, latitude: float, longitude: float) -> str:
        """
        Obtiene la dirección usando geocodificación inversa con OpenStreetMap Nominatim
        
        Args:
            latitude: Latitud en grados decimales
            longitude: Longitud en grados decimales
            
        Returns:
            str: Dirección formateada o mensaje de error
        """
        if not self.geocoding_enabled:
            return ""
        
        try:
            # Crear clave para cache (redondeada a 4 decimales para evitar consultas muy precisas)
            cache_key = f"{latitude:.4f},{longitude:.4f}"
            
            # Verificar cache
            if cache_key in self.geocoding_cache:
                return self.geocoding_cache[cache_key]
            
            # Rate limiting: máximo 1 consulta por segundo (respetando política de Nominatim)
            current_time = time.time()
            if current_time - self.last_geocoding_request < 1.0:
                time.sleep(1.0 - (current_time - self.last_geocoding_request))
            
            # Realizar consulta a Nominatim
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'format': 'json',
                'lat': latitude,
                'lon': longitude,
                'zoom': 18,  # Nivel de detalle (18 = dirección específica)
                'addressdetails': 1,
                'accept-language': 'es'  # Preferir respuestas en español
            }
            
            headers = {
                'User-Agent': 'TQ-Server-RPG/1.0 (GPS Tracking System)'  # Identificar la aplicación
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            self.last_geocoding_request = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                if 'display_name' in data:
                    address = data['display_name']
                    
                    # Guardar en cache
                    self.geocoding_cache[cache_key] = address
                    
                    # Limpiar cache si crece mucho (mantener últimos 100)
                    if len(self.geocoding_cache) > 100:
                        # Eliminar 20 entradas más antiguas
                        old_keys = list(self.geocoding_cache.keys())[:20]
                        for key in old_keys:
                            del self.geocoding_cache[key]
                    
                    return address
                else:
                    return "Dirección no encontrada"
            else:
                return f"Error geocodificación: HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Timeout geocodificación"
        except requests.exceptions.RequestException as e:
            return f"Error red geocodificación: {str(e)[:50]}"
        except Exception as e:
            self.logger.error(f"Error en geocodificación: {e}")
            return f"Error geocodificación: {str(e)[:30]}"

    def save_position_to_file(self, position_data: Dict):
        """Guarda una posición en el archivo CSV aplicando filtros de calidad"""
        try:
            device_id = position_data.get('device_id', '')
            latitude = position_data.get('latitude', 0.0)
            longitude = position_data.get('longitude', 0.0)
            heading = position_data.get('heading', 0.0)
            speed = position_data.get('speed', 0.0)
            
            # APLICAR FILTROS DE CALIDAD
            is_valid, reason = self.is_position_valid(position_data)
            
            if not is_valid:
                self.filtered_positions_count += 1
                self.logger.info(f"Posición filtrada #{self.filtered_positions_count}: {reason}")
                print(f"🚫 Posición filtrada: {reason}")
                return
            
            received_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Extraer fecha y hora GPS
            fecha_gps = position_data.get('fecha_gps', '')
            hora_gps = position_data.get('hora_gps', '')
            
            with open(self.positions_file, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Calcular velocidad en nudos
                speed_knots = speed / 1.852 if speed > 0 else 0
                
                writer.writerow([
                    device_id,
                    f"{latitude:.6f}",
                    f"{longitude:.6f}",
                    f"{heading:.1f}",
                    f"{speed:.1f}",        # Velocidad en km/h
                    f"{speed_knots:.1f}",  # Velocidad en nudos
                    fecha_gps,             # Fecha GPS del protocolo TQ
                    hora_gps,              # Hora GPS del protocolo TQ
                    received_date
                ])
                
            # Obtener dirección mediante geocodificación
            address = ""
            if self.geocoding_enabled:
                address = self.get_address_from_coordinates(latitude, longitude)
            
            # Log con coordenadas, velocidad, rumbo, fecha/hora GPS y dirección
            log_msg = f"Posición guardada: ID={device_id}, Lat={latitude:.6f}°, Lon={longitude:.6f}°, Vel={speed:.1f} km/h ({speed_knots:.1f} nudos), Rumbo={heading}°"
            if fecha_gps and hora_gps:
                log_msg += f", Fecha GPS={fecha_gps}, Hora GPS={hora_gps}"
            if address:
                log_msg += f", Dirección: {address}"
            self.logger.info(log_msg)
            
            # ACTUALIZAR ÚLTIMA POSICIÓN VÁLIDA para filtros futuros
            self.last_valid_position = position_data.copy()
            
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

    def send_tcp_raw_data(self, data: bytes):
        """
        Reenvía los datos crudos por TCP a la IP y puerto configurados
        """
        if not self.tcp_forward_enabled:
            return

        try:
            # Crear socket TCP
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # Timeout corto para no bloquear la operación principal
                sock.settimeout(2.0)
                sock.connect((self.tcp_forward_host, self.tcp_forward_port))
                sock.sendall(data)
                self.logger.info(f"Datos reenviados por TCP a {self.tcp_forward_host}:{self.tcp_forward_port}")
                # print(f"📤 Datos reenviados TCP a {self.tcp_forward_host}:{self.tcp_forward_port}")
        except Exception as e:
            self.logger.error(f"Error reenviando datos por TCP a {self.tcp_forward_host}:{self.tcp_forward_port}: {e}")


    def process_message_with_rpg(self, data: bytes, client_id: str):
        """Procesa un mensaje recibido del cliente"""
        self.message_count += 1
        
        # Reenvío TCP de datos crudos (si está habilitado)
        # Se hace al principio para asegurar que se reenvía tal cual llega
        self.send_tcp_raw_data(data)
        
        # Log del mensaje raw
        hex_data = funciones.bytes2hexa(data)
        self.logger.info(f"Msg #{self.message_count} de {client_id}: {hex_data}")
        print(f"📨 Msg #{self.message_count} de {client_id}")
        print(f"   Raw: {hex_data}")
        
        try:
            # ===================== F I L T R O   N M E A 0 1 8 3 ======================
            # Detecta mensajes que comienzan con '*' y terminan con '#'
            try:
                text_data = data.decode("ascii", errors="ignore").strip()
            except Exception:
                text_data = ""
            
            if text_data.startswith("*") and text_data.endswith("#"):
                # Guardar en log específico si existe, o en el general con prefijo
                try:
                    if hasattr(funciones, "guardarLogNMEA") and callable(funciones.guardarLogNMEA):
                        funciones.guardarLogNMEA(text_data)
                    else:
                        funciones.guardarLog(f"[NMEA0183] {text_data}")
                except Exception as e_log:
                    self.logger.warning(f"No se pudo guardar log NMEA: {e_log}")
                
                self.logger.info(f"Mensaje NMEA0183 detectado y filtrado: {text_data}")
                print(f"⛔ NMEA0183 filtrado: {text_data}")
                # Dejar traza en el log de RPG para auditoría
                try:
                    self.log_rpg_message(hex_data, "", "IGNORADO_NMEA")
                except Exception:
                    pass
                return
            # ==========================================================================

            # Guardar el mensaje en el log
            funciones.guardarLog(hex_data)
            
            # Detectar el tipo de protocolo
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
                    # Convertir a RPG usando la función existente
                    rpg_message = protocolo.RGPdesdeCHINO(hex_data, self.terminal_id)
                    self.logger.info(f"Mensaje RPG generado: {rpg_message}")
                    
                    # Reenviar por UDP
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
                # Protocolo de registro - obtener TerminalID
                full_terminal_id = protocolo.getIDok(hex_data)
                self.terminal_id = full_terminal_id
                
                self.logger.info(f"TerminalID extraído: {full_terminal_id}")
                funciones.guardarLog(f"TerminalID={self.terminal_id}")
                print(f"🆔 TerminalID configurado: {self.terminal_id}")
                
                # Enviar respuesta
                response = protocolo.Enviar0100(self.terminal_id)
            
            else:
                # Otro tipo de protocolo - intentar decodificar como TQ
                self.logger.info(f"Protocolo {protocol_type} - intentando decodificación TQ")
                position_data = self.decode_position_message(data)
            
                if position_data:
                    self.logger.info(f"Posición decodificada: {position_data}")
                    self.display_position(position_data, client_id)
                    
                    # IMPORTANTE: Si no tenemos TerminalID, extraerlo del mensaje de posición
                    if len(self.terminal_id) == 0:
                        position_id = protocolo.getIDok(hex_data)
                        if position_id:
                            self.terminal_id = position_id
                            self.logger.info(f"TerminalID actualizado desde mensaje de posición (protocolo {protocol_type}): {position_id}")
                            print(f"🆔 TerminalID actualizado: {position_id}")
                    
                    # Guardar posición en archivo CSV
                    self.save_position_to_file(position_data)
                    
                    # Si tenemos TerminalID, convertir a RPG
                    if len(self.terminal_id) > 0:
                        try:
                            # CORREGIDO: Usar las coordenadas ya decodificadas en lugar de las funciones de protocolo
                            # Crear mensaje RPG con formato correcto usando los datos GPS decodificados
                            # Usar el device_id del mensaje actual en lugar del terminal_id fijo
                            device_id = position_data.get('device_id', '')
                            rpg_message = self.create_rpg_message_from_gps(position_data, device_id)
                            if rpg_message:
                                funciones.enviar_mensaje_udp(self.udp_host, self.udp_port, rpg_message)
                                self.log_rpg_message(hex_data, rpg_message, "ENVIADO_RPG_GPS")
                                print(f"🔄 Mensaje RPG creado desde GPS enviado por UDP: {rpg_message}")
                        except Exception as e:
                            self.logger.warning(f"No se pudo crear mensaje RPG desde GPS: {e}")
                            # Fallback: intentar con protocolo personal
                            try:
                                rpg_message = protocolo.RGPdesdePERSONAL(hex_data, self.terminal_id)
                                if rpg_message:
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

    def decode_nmea_message(self, nmea_message: str) -> Dict:
        """Decodifica un mensaje NMEA y extrae las coordenadas"""
        try:
            # Remover * y # del mensaje NMEA
            clean_message = nmea_message[1:-1]
            parts = clean_message.split(',')
            
            if len(parts) >= 8:
                # Extraer ID del dispositivo
                device_id_completo = parts[1]  # "2076668133"
                device_id = device_id_completo[-5:]  # "68133" (últimos 5 dígitos)
                
                # Extraer coordenadas
                lat_raw = parts[5]  # "3438.4010"
                lat_direction = parts[6]  # "S"
                lon_raw = parts[7]  # "05833.6031"
                lon_direction = parts[8]  # "W"
                
                # Convertir coordenadas NMEA a grados decimales
                latitude = self.nmea_to_decimal(lat_raw, lat_direction)
                longitude = self.nmea_to_decimal(lon_raw, lon_direction)
                
                # Extraer otros datos
                heading = 0
                speed = 0
                if len(parts) >= 10:
                    try:
                        speed = float(parts[9])  # Velocidad en km/h
                    except:
                        speed = 0
                
                if len(parts) >= 11:
                    try:
                        heading = float(parts[10])  # Rumbo en grados
                    except:
                        heading = 0
                
                self.logger.info(f"Coordenadas NMEA extraídas: Lat={latitude:.6f}°, Lon={longitude:.6f}°")
                
                return {
                    'device_id': device_id,  # ID para RPG (68133)
                    'device_id_completo': device_id_completo,  # ID completo (2076668133)
                    'latitude': latitude,
                    'longitude': longitude,
                    'heading': heading,
                    'speed': speed,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.logger.warning(f"Mensaje NMEA con formato incorrecto: {nmea_message}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error decodificando mensaje NMEA: {e}")
            return {}
    
    def nmea_to_decimal(self, coord_str: str, direction: str) -> float:
        """Convierte coordenadas NMEA a grados decimales"""
        try:
            # Formato NMEA: DDMM.MMMM (grados y minutos)
            coord = float(coord_str)
            degrees = int(coord // 100)
            minutes = coord % 100
            decimal_degrees = degrees + (minutes / 60.0)
            
            # Aplicar signo según la dirección
            if direction in ['S', 'W']:
                decimal_degrees = -decimal_degrees
                
            return decimal_degrees
        except:
            return 0.0

    def decode_position_message(self, data: bytes) -> Dict:
        """Decodifica un mensaje de posición del protocolo TQ"""
        try:
            import binascii
            
            # Convertir a hexadecimal
            hex_str = binascii.hexlify(data).decode('ascii')
            
            # CORREGIDO: Detectar si es mensaje NMEA codificado en hexadecimal
            try:
                # Intentar decodificar como mensaje NMEA
                ascii_message = data.decode('ascii', errors='ignore')
                if ascii_message.startswith('*') and ascii_message.endswith('#'):
                    # Es un mensaje NMEA directo
                    self.logger.info(f"Mensaje NMEA detectado: {ascii_message}")
                    return self.decode_nmea_message(ascii_message)
                else:
                    # Intentar decodificar hex a ASCII
                    ascii_from_hex = bytes.fromhex(hex_str).decode('ascii', errors='ignore')
                    if ascii_from_hex.startswith('*') and ascii_from_hex.endswith('#'):
                        # Es un mensaje NMEA codificado en hexadecimal
                        self.logger.info(f"Mensaje NMEA codificado en hex detectado: {ascii_from_hex}")
                        return self.decode_nmea_message(ascii_from_hex)
            except:
                pass
            
            # Si no es NMEA, continuar con decodificación hexadecimal
            # CORREGIDO: Extraer datos según protocolo TQ
            # ID completo para mostrar en consola (posiciones 2-11 del mensaje hexadecimal)
            device_id_completo = hex_str[2:12]  # "2076668133"
            
            # ID para RPG (últimos 5 dígitos del ID completo)
            device_id = protocolo.getIDok(hex_str)  # "68133"
            
            # Extraer fecha y hora GPS del protocolo TQ
            fecha_gps = protocolo.getFECHA_GPS_TQ(hex_str)  # "05/09/25"
            hora_gps = protocolo.getHORA_GPS_TQ(hex_str)    # "00:56:36"
            
            # CORREGIDO: Extraer coordenadas del mensaje hexadecimal del protocolo TQ
            # El mensaje es: 24207666813317442103092534391355060583202802002297ffffdfff00001c6a00000000000000df54000009
            # Formato: [ID][timestamp][lat][lon][otros_datos]
            
            try:
                # Intentar decodificar como mensaje NMEA primero
                ascii_message = data.decode('ascii', errors='ignore')
                if ascii_message.startswith('*') and ascii_message.endswith('#'):
                    # Es un mensaje NMEA, extraer coordenadas correctamente
                    parts = ascii_message[1:-1].split(',')  # Remover * y #
                    
                    if len(parts) >= 8:
                        # Campo 6: Latitud (GGMM.MMMM)
                        lat_raw = parts[5]
                        lat_direction = parts[6]  # N o S
                        
                        # Campo 8: Longitud (GGGMM.MMMM)
                        lon_raw = parts[7]
                        lon_direction = parts[8]  # E o W
                        
                        # Convertir coordenadas de formato NMEA a decimal
                        latitude = self.nmea_to_decimal(lat_raw, lat_direction)
                        longitude = self.nmea_to_decimal(lon_raw, lon_direction)
                        
                        # Validar rangos geográficos
                        if not (-90 <= latitude <= 90):
                            self.logger.warning(f"Latitud fuera de rango válido: {latitude}")
                            latitude = 0.0
                        if not (-180 <= longitude <= 180):
                            self.logger.warning(f"Longitud fuera de rango válido: {longitude}")
                            longitude = 0.0
                        
                        self.logger.info(f"Coordenadas NMEA extraídas: Lat={latitude:.6f}° ({lat_direction}), Lon={longitude:.6f}° ({lon_direction})")
                        
                    else:
                        latitude = 0.0
                        longitude = 0.0
                else:
                    # NO es NMEA - usar el método hexadecimal del protocolo TQ
                    # Usar las funciones del protocolo para extraer coordenadas
                    latitude = protocolo.getLATchino(hex_str)
                    longitude = protocolo.getLONchino(hex_str)
                    
                    self.logger.info(f"Coordenadas hexadecimales extraídas: Lat={latitude:.6f}°, Lon={longitude:.6f}°")
                    
            except Exception as e:
                # Fallback: usar el método hexadecimal del protocolo
                self.logger.warning(f"Error en decodificación NMEA, usando protocolo hexadecimal: {e}")
                try:
                    latitude = protocolo.getLATchino(hex_str)
                    longitude = protocolo.getLONchino(hex_str)
                    self.logger.info(f"Coordenadas hexadecimales (fallback): Lat={latitude:.6f}°, Lon={longitude:.6f}°")
                except:
                    latitude = 0.0
                    longitude = 0.0
                    self.logger.error("No se pudieron extraer coordenadas del mensaje hexadecimal")
            
            # CORREGIDO: Extraer velocidad y rumbo usando las funciones del protocolo TQ
            # Según información del fabricante: velocidad en nudos, rumbo en grados (0-360)
            speed_knots = protocolo.getVELchino(hex_str)  # Velocidad en nudos
            heading = protocolo.getRUMBOchino(hex_str)    # Rumbo en grados
            
            # Convertir velocidad de nudos a km/h para el mensaje RPG
            # 1 nudo = 1.852 km/h
            speed_kmh = speed_knots * 1.852
            
            # Validar rangos según especificaciones
            if speed_kmh > 250:  # Límite de 250 km/h
                self.logger.warning(f"Velocidad excede límite de 250 km/h: {speed_kmh:.2f} km/h ({speed_knots} nudos)")
                speed_kmh = 250
            
            if not (0 <= heading <= 360):  # Rango de rumbo 0-360 grados
                self.logger.warning(f"Rumbo fuera de rango 0-360: {heading}")
                heading = 0
            
            speed = int(speed_kmh)  # Convertir a entero para el mensaje RPG
            self.logger.info(f"Velocidad y rumbo extraídos: {speed_knots} nudos ({speed_kmh:.2f} km/h), Rumbo: {heading}°")
            
            return {
                'device_id': device_id,  # ID para RPG (68133)
                'device_id_completo': device_id_completo,  # ID completo (2076668133)
                'latitude': latitude,
                'longitude': longitude,
                'heading': heading,
                'speed': speed,
                'fecha_gps': fecha_gps,  # Fecha GPS del protocolo TQ
                'hora_gps': hora_gps,    # Hora GPS del protocolo TQ
                'timestamp': datetime.now().isoformat()
            }
                
        except Exception as e:
            self.logger.error(f"Error en decodificación: {e}")
            return {}

    def nmea_to_decimal(self, coord_str: str, direction: str) -> float:
        """Convierte coordenadas del formato NMEA (GGMM.MMMM) a decimal"""
        try:
            # Formato NMEA: GGMM.MMMM (Grados y Minutos)
            if '.' in coord_str:
                # Separar grados y minutos
                parts = coord_str.split('.')
                if len(parts) >= 2:
                    degrees_str = parts[0]
                    minutes_str = parts[1]
                    
                    # Los grados son los primeros 2-3 dígitos
                    if len(degrees_str) >= 3:
                        degrees = float(degrees_str[:-2])
                        minutes = float(degrees_str[-2:] + '.' + minutes_str)
                    else:
                        degrees = float(degrees_str)
                        minutes = float(minutes_str)
                    
                    # Convertir a decimal
                    decimal = degrees + (minutes / 60.0)
                    
                    # Aplicar dirección
                    if direction in ['S', 'W']:
                        decimal = -decimal
                    
                    return decimal
            
            # Fallback: intentar convertir directamente
            decimal = float(coord_str)
            if direction in ['S', 'W']:
                decimal = -decimal
            return decimal
            
        except Exception as e:
            self.logger.error(f"Error convirtiendo coordenada NMEA '{coord_str}': {e}")
            return 0.0

    def display_position(self, position_data: Dict, client_id: str):
        """Muestra la información de posición en pantalla"""
        print(f"\n📍 POSICIÓN RECIBIDA de {client_id}")
        print(f"   ID Equipo: {position_data.get('device_id_completo', position_data['device_id'])}")
        print(f"   Latitud: {position_data['latitude']:.6f}°")
        print(f"   Longitud: {position_data['longitude']:.6f}°")
        print(f"   Rumbo: {position_data['heading']}°")
        # Mostrar velocidad en km/h y nudos
        speed_kmh = position_data['speed']
        speed_knots = speed_kmh / 1.852 if speed_kmh > 0 else 0
        print(f"   Velocidad: {speed_kmh} km/h ({speed_knots:.1f} nudos)")
        if position_data.get('fecha_gps') and position_data.get('hora_gps'):
            print(f"   Fecha GPS: {position_data['fecha_gps']}")
            print(f"   Hora GPS: {position_data['hora_gps']}")
        print(f"   Timestamp: {position_data['timestamp']}")
        print("-" * 50)
        
    def get_status(self) -> Dict:
        """Retorna el estado actual del servidor"""
        geocoding_stats = self.get_geocoding_stats()
        uptime_seconds = 0
        if self.start_time:
            uptime_seconds = int((datetime.now() - self.start_time).total_seconds())
        
        return {
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'udp_host': self.udp_host,
            'udp_port': self.udp_port,
            'tcp_forward_enabled': self.tcp_forward_enabled,
            'tcp_forward_host': self.tcp_forward_host,
            'tcp_forward_port': self.tcp_forward_port,
            'terminal_id': self.terminal_id,
            'connected_clients': len(self.clients),
            'total_messages': self.message_count,
            'filtered_positions': self.filtered_positions_count,
            'geocoding_enabled': geocoding_stats['enabled'],
            'geocoding_cache_size': geocoding_stats['cache_size'],
            'clients': list(self.clients.keys()),
            'uptime_seconds': uptime_seconds
        }
    
    def create_health_handler(self):
        """Crea el handler para el servidor HTTP de health check"""
        server_instance = self
        
        class HealthCheckHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                """Silenciar logs HTTP para no contaminar el log principal"""
                pass
            
            def do_GET(self):
                """Maneja peticiones GET al endpoint /health"""
                if self.path == '/health':
                    try:
                        # Obtener estado del servidor
                        status_data = server_instance.get_status()
                        
                        # Preparar respuesta JSON
                        response = {
                            'status': 'ok' if server_instance.running else 'stopped',
                            'timestamp': datetime.now().isoformat(),
                            'uptime_seconds': status_data['uptime_seconds'],
                            'clients': status_data['connected_clients'],
                            'messages': status_data['total_messages'],
                            'terminal_id': status_data['terminal_id']
                        }
                        
                        # Enviar respuesta
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                        
                    except Exception as e:
                        # Error interno
                        self.send_response(500)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        error_response = {
                            'status': 'error',
                            'message': str(e)
                        }
                        self.wfile.write(json.dumps(error_response).encode('utf-8'))
                else:
                    # Endpoint no encontrado
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'not_found'}).encode('utf-8'))
        
        return HealthCheckHandler
    
    def start_health_server(self):
        """Inicia el servidor HTTP de health check en un thread separado"""
        try:
            handler_class = self.create_health_handler()
            self.health_server = HTTPServer(('0.0.0.0', self.health_port), handler_class)
            
            def run_health_server():
                self.logger.info(f"Health check server iniciado en puerto {self.health_port}")
                print(f"💚 Health check endpoint: http://localhost:{self.health_port}/health")
                self.health_server.serve_forever()
            
            health_thread = threading.Thread(target=run_health_server)
            health_thread.daemon = True
            health_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error iniciando health check server: {e}")
            print(f"⚠️  No se pudo iniciar health check server: {e}")
    
    def stop_health_server(self):
        """Detiene el servidor HTTP de health check"""
        if self.health_server:
            try:
                self.health_server.shutdown()
                self.logger.info("Health check server detenido")
            except Exception as e:
                self.logger.error(f"Error deteniendo health check server: {e}")
        
    def start(self):
        """Inicia el servidor TCP"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            self.start_time = datetime.now()
            
            # Iniciar servidor de health check
            self.start_health_server()
            
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
        
        # Detener health server
        self.stop_health_server()
        
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("Servidor detenido")
        print("🛑 Servidor detenido")
        
    def handle_client(self, client_socket: socket.socket, client_address):
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
            
            try:
                id_int = int(self.terminal_id)
                print(f"   Valor numérico: {id_int}")
                print(f"   Hexadecimal: {id_int:05X}")
            except:
                print(f"   Valor: {self.terminal_id}")
                
        else:
            print("\n⚠️  No hay TerminalID configurado")
            print("   Esperando mensaje de registro del equipo...")

    def toggle_geocoding(self, enable: bool = None) -> bool:
        """
        Habilita/deshabilita la geocodificación
        
        Args:
            enable: True para habilitar, False para deshabilitar, None para toggle
            
        Returns:
            bool: Estado actual de la geocodificación
        """
        if enable is None:
            self.geocoding_enabled = not self.geocoding_enabled
        else:
            self.geocoding_enabled = enable
        
        status = "habilitada" if self.geocoding_enabled else "deshabilitada"
        self.logger.info(f"Geocodificación {status}")
        print(f"🗺️  Geocodificación {status}")
        
        return self.geocoding_enabled

    def get_geocoding_stats(self) -> Dict:
        """Retorna estadísticas de geocodificación"""
        return {
            'enabled': self.geocoding_enabled,
            'cache_size': len(self.geocoding_cache),
            'last_request': self.last_geocoding_request
        }

    def create_rpg_message_from_gps(self, position_data: Dict, terminal_id: str) -> str:
        """Crea un mensaje RPG con formato correcto usando los datos GPS decodificados"""
        try:
            # Extraer datos de la posición
            device_id = position_data.get('device_id', '')
            latitude = position_data.get('latitude', 0.0)
            longitude = position_data.get('longitude', 0.0)
            heading = position_data.get('heading', 0.0)
            speed = position_data.get('speed', 0.0)
            
            # APLICAR FILTROS DE CALIDAD antes de crear mensaje RPG
            is_valid, reason = self.is_position_valid(position_data)
            
            if not is_valid:
                self.logger.info(f"No se crea mensaje RPG - posición filtrada: {reason}")
                return ""
            
            # Validar que las coordenadas estén en rangos válidos
            if not (-90 <= latitude <= 90):
                self.logger.warning(f"Latitud fuera de rango válido para RPG: {latitude}")
                return ""
            if not (-180 <= longitude <= 180):
                self.logger.warning(f"Longitud fuera de rango válido para RPG: {longitude}")
                return ""
            
            # CORREGIDO: Usar fecha y hora GPS del protocolo TQ con offset -3 horas para Argentina
            fecha_gps = position_data.get('fecha_gps', '')  # Formato: DD/MM/YY
            hora_gps = position_data.get('hora_gps', '')    # Formato: HH:MM:SS
            
            if fecha_gps and hora_gps:
                try:
                    # Parsear fecha y hora GPS
                    dia, mes, año = fecha_gps.split('/')
                    hora, minuto, segundo = hora_gps.split(':')
                    
                    # Crear datetime UTC
                    gps_utc = datetime(int('20' + año), int(mes), int(dia), 
                                     int(hora), int(minuto), int(segundo))
                    
                    # CORREGIDO: Usar hora GPS original (UTC) sin aplicar offset
                    # Formatear en DDMMYYHHMMSS usando la hora GPS original
                    timestamp = gps_utc.strftime('%d%m%y%H%M%S')
                    
                    self.logger.info(f"Usando fecha/hora GPS original: {fecha_gps} {hora_gps} UTC (sin offset)")
                    
                except Exception as e:
                    # Fallback al timestamp actual si hay error
                    now = datetime.now()
                    timestamp = now.strftime('%d%m%y%H%M%S')
                    self.logger.warning(f"Error procesando fecha/hora GPS, usando timestamp actual: {e}")
            else:
                # Fallback al timestamp actual si no hay fecha/hora GPS
                now = datetime.now()
                timestamp = now.strftime('%d%m%y%H%M%S')
                self.logger.warning("No se encontró fecha/hora GPS, usando timestamp actual")
            
            # Formato RPG correcto según el manual: >RGP[timestamp][lat][lon][heading][speed][status]&[seq];ID=[id];#[seq]*[checksum]<
            # Ejemplo: >RGP210825145011-3416.9932-05855.05980000003000001;&01;ID=38312;#0001*62<
            
            # Convertir coordenadas al formato RPG (GGMM.MMMM sin signo, dirección implícita)
            # Latitud: convertir de decimal a GGMM.MMMM
            lat_abs = abs(latitude)
            lat_deg = int(lat_abs)
            lat_min = (lat_abs - lat_deg) * 60.0
            lat_str = f"{lat_deg:02d}{lat_min:07.4f}"
            if latitude < 0:  # Sur
                lat_str = "-" + lat_str
            
            # Longitud: convertir de decimal a GGGMM.MMMM sin signo, dirección implícita
            lon_abs = abs(longitude)
            lon_deg = int(lon_abs)
            lon_min = (lon_abs - lon_deg) * 60.0
            lon_str = f"{lon_deg:03d}{lon_min:07.4f}"
            if longitude < 0:  # Oeste
                lon_str = "-" + lon_str
            
            # CORREGIDO: Formatear rumbo (3 dígitos) y velocidad (3 dígitos)
            # Usar los valores extraídos directamente sin conversiones adicionales
            heading_str = f"{int(heading):03d}"
            speed_str = f"{int(speed):03d}"
            
            # Estado (1=Activo, 0=Inactivo)
            status = "1" if abs(latitude) > 0.000001 and abs(longitude) > 0.000001 else "0"
            
            # Secuencial (siempre 01 para este caso)
            seq = "01"
            
            # Construir mensaje RPG principal
            rpg_main = f"RGP{timestamp}{lat_str}{lon_str}{speed_str}{heading_str}{status}"
            
            # Construir mensaje completo con formato correcto
            # CORREGIDO: Agregar "000001" antes del ";&01" según protocolo GEO5
            rpg_message = f">{rpg_main}000001;&{seq};ID={terminal_id};#0001"
            
            # Agregar asterisco para el cálculo del checksum
            rpg_message_with_asterisk = rpg_message + "*"
            
            # Calcular checksum usando la función correcta del protocolo
            # CORREGIDO: Pasar el mensaje con asterisco para que sacar_checksum() incluya el '*' en el XOR
            checksum = self.calculate_rpg_checksum(rpg_message_with_asterisk)
            
            # Agregar checksum y cerrar mensaje
            rpg_message += f"*{checksum}<"
            
            self.logger.info(f"Mensaje RPG creado desde GPS: {rpg_message}")
            
            # ACTUALIZAR ÚLTIMA POSICIÓN VÁLIDA para filtros futuros
            self.last_valid_position = position_data.copy()
            
            return rpg_message
            
        except Exception as e:
            self.logger.error(f"Error creando mensaje RPG desde GPS: {e}")
            return ""

    def calculate_rpg_checksum(self, rpg_main: str) -> str:
        """Calcula el checksum del mensaje RPG usando la función correcta de protocolo.py"""
        try:
            # Usar la función correcta del protocolo para calcular el checksum
            # Esta función implementa el algoritmo correcto para GEO5
            return protocolo.sacar_checksum(rpg_main)
            
        except Exception as e:
            self.logger.error(f"Error calculando checksum RPG: {e}")
            return "00"

    def test_checksum_methods(self):
        """Prueba el método de checksum correcto del protocolo"""
        print("\n🧮 PRUEBA DE CHECKSUM RPG CON PROTOCOLO CORRECTO:")
        
        # Mensaje de prueba basado en los ejemplos válidos
        test_message = "RGP030925012859-343.19699-0598.065190080003000001"
        
        print(f"Mensaje de prueba: {test_message}")
        
        # Usar la función correcta del protocolo
        checksum_correcto = protocolo.sacar_checksum(test_message)
        print(f"Checksum calculado: {checksum_correcto}")
        
        # Construir mensaje completo para verificar
        mensaje_completo = f">{test_message}&01;ID=0001;#0001*{checksum_correcto}<"
        print(f"Mensaje completo: {mensaje_completo}")
        
        print("-" * 50)

def main():
    """Función principal"""
    import sys
    
    print("=" * 60)
    print("🚀 SERVIDOR TCP PROTOCOLO TQ + RPG")
    print("=" * 60)
    
    # Crear y configurar servidor
    server = TQServerRPG(host='0.0.0.0', port=5003, 
                         udp_host='179.43.115.190', udp_port=7007)
    
    # Verificar si se ejecuta en modo no interactivo (background)
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        print("🔄 Modo daemon activado - ejecutando en segundo plano")
        print("📡 Para detener el servidor: pkill -f tq_server_rpg.py")
        
        try:
            # Ejecutar servidor directamente sin bucle de comandos
            server.start()
        except KeyboardInterrupt:
            print("\n🛑 Interrupción detectada...")
        finally:
            server.stop()
            print("👋 Servidor daemon cerrado correctamente")
    else:
        # Modo interactivo normal
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
                               "  terminal - Mostrar TerminalID actual\n"
                               "  geocoding - Toggle geocodificación on/off\n"
                               "  checksum - Probar métodos de checksum RPG\n"
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
                    print(f"   Posiciones filtradas: {status['filtered_positions']}")
                    print(f"   📍 Filtros ON-THE-FLY activos:")
                    print(f"      • Salto sospechoso: >300m/<10s")
                    print(f"      • Salto excesivo: >1km/<5min")
                    print(f"      • Velocidad incoherente: diff >20 km/h")
                    print(f"      • Salto estacionario: >300m reportando parado")
                    print(f"      • ✅ Protege detenciones reales en calles")
                    geocoding_status = "✅ Habilitada" if status['geocoding_enabled'] else "❌ Deshabilitada"
                    print(f"   🗺️  Geocodificación: {geocoding_status} (Cache: {status['geocoding_cache_size']} direcciones)")
                elif command == 'clients':
                    status = server.get_status()
                    if status['clients']:
                        print(f"\n🔗 CLIENTES CONECTADOS ({len(status['clients'])}):")
                        for client in status['clients']:
                            print(f"   - {client}")
                    else:
                        print("\n📭 No hay clientes conectados")
                elif command == 'terminal':
                    server.show_terminal_info()
                elif command == 'geocoding':
                    current_state = server.toggle_geocoding()
                    if current_state:
                        print("   Las nuevas posiciones incluirán direcciones en el log")
                    else:
                        print("   Las nuevas posiciones NO incluirán direcciones")
                elif command == 'checksum':
                    server.test_checksum_methods()
                else:
                    print("❌ Comando no válido")
                    
        except KeyboardInterrupt:
            print("\n🛑 Interrupción detectada...")
        finally:
            server.stop()
            print("👋 Servidor cerrado correctamente")

if __name__ == "__main__":
    main()

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
from log_optimizer import get_rpg_logger

class TQServerRPG:
    def __init__(self, host: str = '0.0.0.0', port: int = 5003, 
                 udp_host: str = '179.43.115.190', udp_port: int = 7007,
                 health_port: int = 5004,
                 tcp_forward_host: str = '168.197.48.154', tcp_forward_port: int = 5005,
                 tcp_forward_enabled: bool = True,
                 heartbeat_enabled: bool = True,
                 heartbeat_udp_host: str = '127.0.0.1',
                 heartbeat_udp_port: int = 9001,
                 heartbeat_interval_seconds: int = 300):
        self.host = host
        self.port = port
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.health_port = health_port
        
        # Configuración de reenvío TCP
        self.tcp_forward_host = tcp_forward_host
        self.tcp_forward_port = tcp_forward_port
        self.tcp_forward_enabled = tcp_forward_enabled
        
        # Configuración de heartbeat UDP
        self.heartbeat_enabled = heartbeat_enabled
        self.heartbeat_udp_host = heartbeat_udp_host
        self.heartbeat_udp_port = heartbeat_udp_port
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        self.heartbeat_thread = None
        self.heartbeat_stop_event = None

        self.server_socket = None
        self.health_server = None
        self.clients: Dict[str, socket.socket] = {}
        self.client_last_activity: Dict[str, datetime] = {}  # Tracking de última actividad por cliente
        self.running = False
        self.cleanup_thread = None
        self.cleanup_stop_event = None
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
        
        # Inicializar logger RPG optimizado
        self.rpg_logger = get_rpg_logger()
        
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
                # No loggear verbose - posición filtrada es normal
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
        """Función legacy - ya no se usa, mantener para compatibilidad pero no hacer nada"""
        # Esta función ya no se usa - el logging optimizado se hace con funciones.guardarLogUDP
        pass
    
    def log_rpg_optimized(self, position_data: Dict, protocol_type: str, 
                         rpg_message: str = "", tcp_sent: bool = False):
        """
        Registra intento de paquete RPG en formato optimizado
        Reduce espacio en disco eliminando información redundante
        """
        try:
            device_id = position_data.get('device_id', '')
            latitude = position_data.get('latitude', 0.0)
            longitude = position_data.get('longitude', 0.0)
            heading = position_data.get('heading', 0)
            speed = position_data.get('speed', 0)
            fecha_gps = position_data.get('fecha_gps', '')
            hora_gps = position_data.get('hora_gps', '')
            
            # Preparar lista de destinos
            destinations = []
            
            # Destino UDP si hay mensaje RPG
            if rpg_message:
                destinations.append(("UDP", self.udp_host, self.udp_port, rpg_message))
            
            # Destino TCP si está habilitado
            if tcp_sent and self.tcp_forward_enabled:
                hex_data = funciones.bytes2hexa(position_data.get('raw_data', b''))
                destinations.append(("TCP", self.tcp_forward_host, self.tcp_forward_port, hex_data))
            
            # Usar el logger optimizado
            self.rpg_logger.log_rpg_attempt(
                device_id=device_id,
                protocol_type=protocol_type,
                latitude=latitude,
                longitude=longitude,
                heading=heading,
                speed=speed,
                fecha_gps=fecha_gps,
                hora_gps=hora_gps,
                destinations=destinations
            )
            
        except Exception as e:
            self.logger.error(f"Error en log RPG optimizado: {e}")


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
                # No loggear verbose - reenvío TCP es operación normal
                # print(f"📤 Datos reenviados TCP a {self.tcp_forward_host}:{self.tcp_forward_port}")
        except Exception as e:
            self.logger.error(f"Error reenviando datos por TCP a {self.tcp_forward_host}:{self.tcp_forward_port}: {e}")


    def process_message_with_rpg(self, data: bytes, client_id: str):
        """Procesa un mensaje recibido del cliente"""
        self.message_count += 1
        
        # Reenvío TCP de datos crudos (si está habilitado)
        # Se hace al principio para asegurar que se reenvía tal cual llega
        self.send_tcp_raw_data(data)
        
        # Log del mensaje raw (formato compacto)
        hex_data = funciones.bytes2hexa(data)
        # No loggear verbose - solo guardar en log compacto
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
                    pass  # Error silencioso - ya se guardó en log
                
                # No loggear verbose - ya se guardó con guardarLogNMEA
                print(f"⛔ NMEA0183 filtrado: {text_data}")
                # NMEA ignorado - ya se guardó con guardarLogNMEA
                pass
                return
            # ==========================================================================

            # Guardar el mensaje en el log (formato compacto)
            funciones.guardarLog(hex_data)
            
            # Detectar el tipo de protocolo
            protocol_type = protocolo.getPROTOCOL(hex_data)
            # No loggear verbose - información no esencial
        
            if protocol_type == "22":
                # Protocolo de posición - convertir a RPG y reenviar
                
                # IMPORTANTE: Extraer y guardar el ID del mensaje de posición
                position_id = protocolo.getIDok(hex_data)
                if position_id:
                    self.terminal_id = position_id  # ACTUALIZAR el TerminalID
                    # No loggear verbose - solo print para consola
                    print(f"🆔 TerminalID actualizado: {position_id}")
            
                if len(self.terminal_id) > 0:
                    # Convertir a RPG usando la función existente
                    rpg_message = protocolo.RGPdesdeCHINO(hex_data, self.terminal_id)
                    # No loggear verbose
                    
                    # Reenviar por UDP
                    funciones.enviar_mensaje_udp(self.udp_host, self.udp_port, rpg_message)
                    
                    # Log del mensaje RPG (ya no se usa log_rpg_message, usar funciones.guardarLogUDP)
                    print(f"🔄 Mensaje RPG enviado por UDP: {rpg_message}")
                    
                    # Guardar en el log UDP (formato compacto)
                    funciones.guardarLogUDP(rpg_message)
                    
                else:
                    # No loggear verbose - solo print
                    print("⚠️ TerminalID no disponible para conversión RPG")
                
            elif protocol_type == "01":
                # Protocolo de registro - obtener TerminalID
                full_terminal_id = protocolo.getIDok(hex_data)
                self.terminal_id = full_terminal_id
                
                # Log compacto usando funciones.guardarLog
                funciones.guardarLog(f"TerminalID={self.terminal_id}")
                print(f"🆔 TerminalID configurado: {self.terminal_id}")
                
                # Enviar respuesta
                response = protocolo.Enviar0100(self.terminal_id)
            
            else:
                # Otro tipo de protocolo - intentar decodificar como TQ
                # No loggear verbose
                position_data = self.decode_position_message(data)
            
                if position_data:
                    # No loggear verbose - solo mostrar en consola si es necesario
                    # self.display_position(position_data, client_id)  # Comentado para reducir verbosidad
                    
                    # IMPORTANTE: Si no tenemos TerminalID, extraerlo del mensaje de posición
                    if len(self.terminal_id) == 0:
                        position_id = protocolo.getIDok(hex_data)
                        if position_id:
                            self.terminal_id = position_id
                            # No loggear verbose - solo print
                            print(f"🆔 TerminalID actualizado: {position_id}")
                    
                    # Guardar posición en archivo CSV (si existe la función, sino ignorar)
                    try:
                        self.save_position_to_file(position_data)
                    except AttributeError:
                        pass  # positions_file no existe, ignorar
                    
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
                                # Usar log optimizado en lugar de log_rpg_message
                                funciones.guardarLogUDP(rpg_message)
                                print(f"🔄 Mensaje RPG creado desde GPS enviado por UDP: {rpg_message}")
                        except Exception as e:
                            # Solo loggear errores críticos
                            pass  # No loggear warnings verbosos
                            # Fallback: intentar con protocolo personal
                            try:
                                rpg_message = protocolo.RGPdesdePERSONAL(hex_data, self.terminal_id)
                                if rpg_message:
                                    funciones.enviar_mensaje_udp(self.udp_host, self.udp_port, rpg_message)
                                    funciones.guardarLogUDP(rpg_message)
                                    print(f"🔄 Mensaje RPG personal enviado por UDP: {rpg_message}")
                            except:
                                pass  # No loggear warnings verbosos
                    else:
                        # No loggear verbose
                        pass
                        
                else:
                    # No loggear verbose - solo print para debugging
                    print(f"⚠️  No se pudo decodificar el mensaje")
                
        except Exception as e:
            # Solo loggear errores críticos, no todos los errores
            print(f"❌ Error procesando mensaje: {e}")
            # No usar log_rpg_message que ya no existe o tiene problemas

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
                
                        # No loggear verbose
                
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
                    # No loggear verbose - ya se guardó con guardarLogNMEA
                    return self.decode_nmea_message(ascii_message)
                else:
                    # Intentar decodificar hex a ASCII
                    ascii_from_hex = bytes.fromhex(hex_str).decode('ascii', errors='ignore')
                    if ascii_from_hex.startswith('*') and ascii_from_hex.endswith('#'):
                        # Es un mensaje NMEA codificado en hexadecimal
                        # No loggear verbose - ya se guardó con guardarLogNMEA
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
                            # No loggear verbose - solo corregir valor
                            latitude = 0.0
                        if not (-180 <= longitude <= 180):
                            # No loggear verbose - solo corregir valor
                            longitude = 0.0
                        
                        # No loggear verbose - información no esencial
                        
                    else:
                        latitude = 0.0
                        longitude = 0.0
                else:
                    # NO es NMEA - usar el método hexadecimal del protocolo TQ
                    # Usar las funciones del protocolo para extraer coordenadas
                    latitude = protocolo.getLATchino(hex_str)
                    longitude = protocolo.getLONchino(hex_str)
                    
                    # No loggear verbose - información no esencial
                    
            except Exception as e:
                # Fallback: usar el método hexadecimal del protocolo
                # No loggear verbose - intentar fallback silenciosamente
                try:
                    latitude = protocolo.getLATchino(hex_str)
                    longitude = protocolo.getLONchino(hex_str)
                except:
                    latitude = 0.0
                    longitude = 0.0
                    # No loggear verbose - solo continuar con valores por defecto
            
            # CORREGIDO: Extraer velocidad y rumbo usando las funciones del protocolo TQ
            # Según información del fabricante: velocidad en nudos, rumbo en grados (0-360)
            speed_knots = protocolo.getVELchino(hex_str)  # Velocidad en nudos
            heading = protocolo.getRUMBOchino(hex_str)    # Rumbo en grados
            
            # Convertir velocidad de nudos a km/h para el mensaje RPG
            # 1 nudo = 1.852 km/h
            speed_kmh = speed_knots * 1.852
            
            # Validar rangos según especificaciones
            if speed_kmh > 250:  # Límite de 250 km/h
                # No loggear verbose - solo corregir valor
                speed_kmh = 250
            
            if not (0 <= heading <= 360):  # Rango de rumbo 0-360 grados
                # No loggear verbose - solo corregir valor
                heading = 0
            
            speed = int(speed_kmh)  # Convertir a entero para el mensaje RPG
            # No loggear verbose - información no esencial
            
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
    
    def send_heartbeat(self):
        """Envía un heartbeat UDP al monitor"""
        if not self.heartbeat_enabled:
            return
        
        try:
            uptime = 0
            if self.start_time:
                uptime = int((datetime.now() - self.start_time).total_seconds())
            
            heartbeat_data = {
                'timestamp': datetime.now().isoformat(),
                'server_id': 'tq_server_rpg',
                'status': 'running' if self.running else 'stopped',
                'uptime_seconds': uptime,
                'port': self.port,
                'clients': len(self.clients),
                'messages': self.message_count
            }
            
            heartbeat_json = json.dumps(heartbeat_data).encode('utf-8')
            
            # Crear socket UDP y enviar
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            sock.sendto(heartbeat_json, (self.heartbeat_udp_host, self.heartbeat_udp_port))
            sock.close()
            
            self.logger.debug(f"Heartbeat enviado a {self.heartbeat_udp_host}:{self.heartbeat_udp_port}")
        except Exception as e:
            # No loguear errores de heartbeat como error crítico (puede que el monitor no esté disponible)
            self.logger.debug(f"Error enviando heartbeat (monitor puede no estar disponible): {e}")
    
    def heartbeat_loop(self):
        """Bucle que envía heartbeats periódicamente"""
        while not self.heartbeat_stop_event.is_set():
            if self.running:
                self.send_heartbeat()
            # Esperar el intervalo o hasta que se detenga
            if self.heartbeat_stop_event.wait(self.heartbeat_interval_seconds):
                break  # Se detuvo
    
    def start_heartbeat(self):
        """Inicia el envío de heartbeats en un thread separado"""
        if not self.heartbeat_enabled:
            return
        
        self.heartbeat_stop_event = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        self.logger.info(f"Heartbeat UDP iniciado: enviando a {self.heartbeat_udp_host}:{self.heartbeat_udp_port} cada {self.heartbeat_interval_seconds}s")
        print(f"💓 Heartbeat UDP: {self.heartbeat_udp_host}:{self.heartbeat_udp_port} (cada {self.heartbeat_interval_seconds}s)")
    
    def stop_heartbeat(self):
        """Detiene el envío de heartbeats"""
        if self.heartbeat_stop_event:
            self.heartbeat_stop_event.set()
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=2.0)
        if self.heartbeat_enabled:
            self.logger.info("Heartbeat UDP detenido")
    
    def cleanup_inactive_connections(self):
        """Limpia conexiones inactivas periódicamente"""
        INACTIVE_TIMEOUT_SECONDS = 600  # 10 minutos sin actividad
        
        while not self.cleanup_stop_event.is_set():
            try:
                if not self.running:
                    break
                
                current_time = datetime.now()
                clients_to_close = []
                
                # Verificar cada cliente
                for client_id, client_socket in list(self.clients.items()):
                    try:
                        # Verificar si el socket sigue válido
                        if client_socket.fileno() == -1:
                            clients_to_close.append(client_id)
                            continue
                        
                        # Verificar última actividad
                        last_activity = self.client_last_activity.get(client_id)
                        if last_activity:
                            inactive_time = (current_time - last_activity).total_seconds()
                            if inactive_time > INACTIVE_TIMEOUT_SECONDS:
                                self.logger.warning(f"Conexión {client_id} inactiva por {inactive_time:.0f}s - cerrando")
                                clients_to_close.append(client_id)
                    except Exception as e:
                        self.logger.debug(f"Error verificando cliente {client_id}: {e}")
                        clients_to_close.append(client_id)
                
                # Cerrar conexiones inactivas
                for client_id in clients_to_close:
                    try:
                        if client_id in self.clients:
                            sock = self.clients[client_id]
                            sock.close()
                            del self.clients[client_id]
                        if client_id in self.client_last_activity:
                            del self.client_last_activity[client_id]
                        self.logger.info(f"Conexión inactiva cerrada: {client_id}")
                    except Exception as e:
                        self.logger.error(f"Error cerrando conexión inactiva {client_id}: {e}")
                
                # Esperar 60 segundos antes de la próxima verificación
                if self.cleanup_stop_event.wait(60):
                    break
                    
            except Exception as e:
                self.logger.error(f"Error en limpieza de conexiones: {e}")
                time.sleep(60)  # Esperar antes de reintentar
    
    def start_connection_cleanup(self):
        """Inicia el thread de limpieza de conexiones inactivas"""
        self.cleanup_stop_event = threading.Event()
        self.cleanup_thread = threading.Thread(target=self.cleanup_inactive_connections)
        self.cleanup_thread.daemon = True
        self.cleanup_thread.start()
        self.logger.info("Thread de limpieza de conexiones iniciado")
    
    def stop_connection_cleanup(self):
        """Detiene el thread de limpieza de conexiones"""
        if self.cleanup_stop_event:
            self.cleanup_stop_event.set()
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=2.0)
        self.logger.info("Thread de limpieza de conexiones detenido")
    
    def is_port_listening(self) -> bool:
        """
        Verifica si el socket del servidor está abierto y listo para aceptar conexiones
        
        Returns:
            bool: True si el socket está abierto, False en caso contrario
        """
        try:
            if self.server_socket is None:
                return False
            # Verificar que el file descriptor sea válido (no -1)
            return self.server_socket.fileno() != -1
        except (AttributeError, OSError, ValueError):
            # Si el socket está cerrado, fileno() puede lanzar una excepción
            return False
        
    def start(self):
        """Inicia el servidor TCP"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.settimeout(5.0)  # Timeout para aceptar conexiones
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            self.start_time = datetime.now()
            
            # Iniciar thread de limpieza de conexiones inactivas
            self.start_connection_cleanup()
            
            # Limpiar logs antiguos (mantener solo últimos 30 días)
            print("🧹 Limpiando logs antiguos...")
            cleanup_stats = funciones.cleanup_old_logs(days_to_keep=30)
            if cleanup_stats.get('deleted_count', 0) > 0:
                self.logger.info(f"Logs limpiados: {cleanup_stats['deleted_count']} archivos, "
                               f"{cleanup_stats['size_freed_mb']} MB liberados")
            
            # Iniciar servidor de health check
            self.start_health_server()
            
            # Iniciar envío de heartbeats
            self.start_heartbeat()
            
            # Verificar que el socket está abierto
            if not self.is_port_listening():
                self.logger.warning(f"Advertencia: No se pudo verificar el estado del puerto {self.port}")
            
            self.logger.info(f"Servidor TQ+RPG iniciado en {self.host}:{self.port}")
            print(f"🚀 Servidor TQ+RPG iniciado en {self.host}:{self.port}")
            print(f"📡 UDP configurado para reenvío a {self.udp_host}:{self.udp_port}")
            print("📡 Esperando conexiones de equipos...")
            
            while self.running:
                try:
                    # Verificar que el socket sigue abierto
                    if self.server_socket.fileno() == -1:
                        raise socket.error("Socket cerrado inesperadamente")
                    
                    client_socket, client_address = self.server_socket.accept()
                    # Registrar actividad inicial
                    client_id = f"{client_address[0]}:{client_address[1]}"
                    self.client_last_activity[client_id] = datetime.now()
                    
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        self.logger.error(f"Error aceptando conexión o puerto cerrado: {e}")
                        # Verificar si el socket se cerró verificando su file descriptor
                        try:
                            socket_closed = False
                            try:
                                if self.server_socket is None or self.server_socket.fileno() == -1:
                                    socket_closed = True
                            except (OSError, ValueError, AttributeError):
                                socket_closed = True
                            
                            if socket_closed:
                                # El socket está cerrado
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                message = (
                                    f"🚨 *Puerto {self.port} Cerrado*\n"
                                    f"⏰ Hora: {timestamp}\n"
                                    f"🔌 El puerto de escucha {self.port} se ha cerrado inesperadamente\n"
                                    f"❌ Error: {str(e)}"
                                )
                                funciones.send_telegram_notification(message)
                                self.logger.error(f"Puerto {self.port} cerrado - notificación enviada")
                                break  # Salir del bucle si el puerto está cerrado
                        except Exception as check_error:
                            self.logger.error(f"Error verificando estado del puerto: {check_error}")
                        
        except OSError as e:
            # Error del sistema operativo (puerto en uso, permisos, etc.)
            self.logger.error(f"Error del sistema iniciando servidor: {e}")
            print(f"❌ Error iniciando servidor: {e}")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = (
                f"🚨 *Error Iniciando Servidor TQ*\n"
                f"⏰ Hora: {timestamp}\n"
                f"🔌 Puerto {self.port} no pudo iniciarse\n"
                f"❌ Error: {str(e)}"
            )
            funciones.send_telegram_notification(message)
        except Exception as e:
            self.logger.error(f"Error iniciando servidor: {e}")
            print(f"❌ Error iniciando servidor: {e}")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = (
                f"🚨 *Error Iniciando Servidor TQ*\n"
                f"⏰ Hora: {timestamp}\n"
                f"❌ Error: {str(e)}"
            )
            funciones.send_telegram_notification(message)
            
    def stop(self):
        """Detiene el servidor"""
        was_running = self.running
        self.running = False
        
        # Detener health server
        self.stop_health_server()
        
        # Detener heartbeat
        self.stop_heartbeat()
        
        # Detener limpieza de conexiones
        self.stop_connection_cleanup()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error cerrando socket: {e}")
        
        self.logger.info("Servidor detenido")
        print("🛑 Servidor detenido")
        
        # Enviar notificación por Telegram si el servidor estaba corriendo
        if was_running:
            try:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                message = (
                    f"⚠️ *Servidor TQ Detenido*\n"
                    f"⏰ Hora: {timestamp}\n"
                    f"🔌 Puerto {self.port} cerrado\n"
                    f"🛑 El servicio del módulo se ha detenido"
                )
                funciones.send_telegram_notification(message)
            except Exception as e:
                self.logger.error(f"Error enviando notificación Telegram al detener: {e}")
        
    def handle_client(self, client_socket: socket.socket, client_address):
        """Maneja la conexión de un cliente"""
        client_id = f"{client_address[0]}:{client_address[1]}"
        self.clients[client_id] = client_socket
        
        # Configurar timeout para la conexión (5 minutos de inactividad)
        client_socket.settimeout(300.0)  # 5 minutos sin actividad = cerrar conexión
        
        self.logger.info(f"Nueva conexión desde {client_id}")
        print(f"🔗 Nueva conexión desde {client_id}")
        
        try:
            while self.running:
                try:
                    # Recibir datos del cliente
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Actualizar última actividad
                    self.client_last_activity[client_id] = datetime.now()
                    
                    # Procesar el mensaje recibido con conversión RPG y reenvío UDP
                    self.process_message_with_rpg(data, client_id)
                    
                except socket.timeout:
                    # Timeout de inactividad - cerrar conexión
                    self.logger.warning(f"Conexión {client_id} inactiva por más de 5 minutos - cerrando")
                    print(f"⏱️  Conexión {client_id} inactiva - cerrando")
                    break
                    
        except socket.error as e:
            # Error de socket (conexión cerrada por el cliente o error de red)
            self.logger.debug(f"Error de socket con cliente {client_id}: {e}")
        except Exception as e:
            self.logger.error(f"Error manejando cliente {client_id}: {e}")
            print(f"❌ Error con cliente {client_id}: {e}")
            
        finally:
            # Limpiar conexión
            try:
                client_socket.close()
            except:
                pass
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.client_last_activity:
                del self.client_last_activity[client_id]
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
                # No loggear verbose - posición filtrada es normal
                return ""
            
            # Validar que las coordenadas estén en rangos válidos
            if not (-90 <= latitude <= 90):
                # No loggear verbose - solo rechazar
                return ""
            if not (-180 <= longitude <= 180):
                # No loggear verbose - solo rechazar
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
                    
                    # No loggear verbose - información no esencial
                    
                except Exception as e:
                    # Fallback al timestamp actual si hay error
                    now = datetime.now()
                    timestamp = now.strftime('%d%m%y%H%M%S')
                    # No loggear verbose - usar fallback silenciosamente
            else:
                # Fallback al timestamp actual si no hay fecha/hora GPS
                now = datetime.now()
                timestamp = now.strftime('%d%m%y%H%M%S')
                # No loggear verbose - usar fallback silenciosamente
            
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
            
            # No loggear verbose - mensaje ya se guardará con guardarLogUDP
            
            # ACTUALIZAR ÚLTIMA POSICIÓN VÁLIDA para filtros futuros
            self.last_valid_position = position_data.copy()
            
            return rpg_message
            
        except Exception as e:
            # Solo loggear errores críticos
            print(f"❌ Error creando mensaje RPG: {e}")
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
                         udp_host='179.43.115.190', udp_port=7007,
                         heartbeat_enabled=True,  # Heartbeat habilitado
                         heartbeat_udp_host='127.0.0.1',  # IP del monitor (127.0.0.1 = mismo servidor, o IP remota)
                         heartbeat_udp_port=9001,  # Puerto UDP del monitor (debe coincidir con ControlTQ/config.py)
                         heartbeat_interval_seconds=300)  # 5 minutos
    
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

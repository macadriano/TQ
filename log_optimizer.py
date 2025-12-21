#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimizador de logs para paquetes RPG
Reduce el espacio en disco eliminando información redundante
Incluye limpieza automática de logs antiguos
"""

import os
import glob
from datetime import datetime, timedelta
from typing import Dict, Optional

class RPGLogOptimizer:
    """
    Clase para optimizar el logging de paquetes RPG
    Reduce información redundante y organiza datos en formato compacto
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Inicializa el optimizador de logs
        
        Args:
            log_dir: Directorio donde se guardarán los logs optimizados
        """
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> dict:
        """
        Elimina archivos de log más antiguos que el número de días especificado
        
        Args:
            days_to_keep: Número de días de logs a mantener (default: 30)
            
        Returns:
            dict: Estadísticas de limpieza (archivos eliminados, espacio liberado)
        """
        try:
            # Calcular fecha límite
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Buscar todos los archivos de log en el directorio
            log_patterns = [
                os.path.join(self.log_dir, "LOG_*.txt"),
                os.path.join(self.log_dir, "RPG_*.txt")
            ]
            
            deleted_files = []
            total_size_freed = 0
            
            for pattern in log_patterns:
                for log_file in glob.glob(pattern):
                    try:
                        # Obtener fecha de modificación del archivo
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                        
                        # Si el archivo es más antiguo que la fecha límite, eliminarlo
                        if file_mtime < cutoff_date:
                            file_size = os.path.getsize(log_file)
                            os.remove(log_file)
                            deleted_files.append(os.path.basename(log_file))
                            total_size_freed += file_size
                            print(f"🗑️  Log eliminado: {os.path.basename(log_file)} "
                                  f"({file_size / 1024:.2f} KB, {file_mtime.strftime('%Y-%m-%d')})")
                    
                    except Exception as e:
                        print(f"⚠️  Error eliminando {log_file}: {e}")
            
            # Convertir bytes a MB para mejor legibilidad
            size_mb = total_size_freed / (1024 * 1024)
            
            stats = {
                'deleted_count': len(deleted_files),
                'deleted_files': deleted_files,
                'size_freed_bytes': total_size_freed,
                'size_freed_mb': round(size_mb, 2),
                'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
                'days_kept': days_to_keep
            }
            
            if deleted_files:
                print(f"✅ Limpieza completada: {len(deleted_files)} archivo(s) eliminado(s), "
                      f"{size_mb:.2f} MB liberados")
            else:
                print(f"✅ No hay archivos de log anteriores a {cutoff_date.strftime('%Y-%m-%d')}")
            
            return stats
            
        except Exception as e:
            print(f"❌ Error en limpieza de logs: {e}")
            return {
                'deleted_count': 0,
                'deleted_files': [],
                'size_freed_bytes': 0,
                'size_freed_mb': 0,
                'error': str(e)
            }

    
    def get_rpg_log_filename(self) -> str:
        """
        Genera el nombre de archivo de log RPG optimizado con formato logs/RPG_DDMMYY.txt
        
        Returns:
            str: Ruta completa del archivo de log RPG del día
        """
        now = datetime.now()
        fecha_str = now.strftime('%d%m%y')  # DDMMYY
        filename = f"{self.log_dir}/RPG_{fecha_str}.txt"
        return filename
    
    def log_rpg_attempt(self, 
                       device_id: str,
                       protocol_type: str,
                       latitude: float,
                       longitude: float,
                       heading: int,
                       speed: int,
                       fecha_gps: str = "",
                       hora_gps: str = "",
                       destinations: list = None,
                       skip_duplicates: bool = True):
        """
        Registra un intento de logueo de paquete RPG en formato optimizado
        
        Args:
            device_id: ID del equipo
            protocol_type: Tipo de protocolo detectado (ej: "59")
            latitude: Latitud en grados decimales
            longitude: Longitud en grados decimales
            heading: Rumbo en grados (0-360)
            speed: Velocidad en km/h
            fecha_gps: Fecha GPS (DD/MM/YY) - opcional
            hora_gps: Hora GPS (HH:MM:SS) - opcional
            destinations: Lista de destinos de envío [(tipo, ip, puerto, dato), ...]
        """
        try:
            # Crear firma única del reporte para detectar duplicados
            report_signature = f"{device_id}|{latitude:.6f}|{longitude:.6f}|{heading}|{speed}"
            
            # Verificar si es duplicado del último reporte
            if skip_duplicates and hasattr(self, '_last_report_signature'):
                if self._last_report_signature == report_signature:
                    # Es un duplicado, no registrar
                    return
            
            # Guardar firma para próxima comparación
            self._last_report_signature = report_signature
            
            log_file = self.get_rpg_log_filename()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(log_file, 'a', encoding='utf-8') as f:
                # Línea 1: Timestamp y tipo de protocolo
                f.write(f"{timestamp} - Protocolo: {protocol_type}\n")
                
                # Línea 2: Datos GPS consolidados en una sola línea
                f.write(f"GPS: ID={device_id}, LAT={latitude:.6f}, LON={longitude:.6f}, "
                       f"RUMBO={heading}, VEL={speed} km/h\n")
                
                # Línea 3: Fecha/hora GPS si está disponible
                if fecha_gps and hora_gps:
                    f.write(f"Timestamp GPS: {fecha_gps} {hora_gps} UTC\n")
                
                # Líneas 4+: Destinos de envío (una línea por destino)
                if destinations:
                    for dest in destinations:
                        tipo, ip, puerto, dato = dest
                        # Truncar dato si es muy largo (máximo 100 caracteres)
                        dato_truncado = dato[:100] + "..." if len(dato) > 100 else dato
                        f.write(f"Envío {tipo}: {ip}:{puerto} - {dato_truncado}\n")
                
                # Línea separadora
                f.write("-" * 80 + "\n")
                
        except Exception as e:
            print(f"Error guardando log RPG optimizado: {e}")
    
    def log_rpg_compact(self, 
                       device_id: str,
                       lat: float,
                       lon: float,
                       heading: int,
                       speed: int,
                       protocol: str = "",
                       gps_time: str = "",
                       send_info: str = ""):
        """
        Versión ultra-compacta de log RPG (una sola línea por evento)
        
        Args:
            device_id: ID del equipo
            lat: Latitud
            lon: Longitud
            heading: Rumbo
            speed: Velocidad
            protocol: Tipo de protocolo (opcional)
            gps_time: Timestamp GPS (opcional)
            send_info: Información de envío compacta (opcional)
        """
        try:
            log_file = self.get_rpg_log_filename()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Formato ultra-compacto en una sola línea
            log_line = f"{timestamp}|ID:{device_id}|{lat:.6f},{lon:.6f}|H:{heading}|V:{speed}"
            
            if protocol:
                log_line += f"|P:{protocol}"
            if gps_time:
                log_line += f"|GPS:{gps_time}"
            if send_info:
                log_line += f"|{send_info}"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + "\n")
                
        except Exception as e:
            print(f"Error guardando log RPG compacto: {e}")
    
    def log_protocol_detection(self, protocol_type: str, hex_data: str = ""):
        """
        Registra detección de protocolo de forma compacta
        
        Args:
            protocol_type: Tipo de protocolo detectado
            hex_data: Datos hexadecimales (opcional, se truncarán si son muy largos)
        """
        try:
            log_file = self.get_rpg_log_filename()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Truncar hex_data si es muy largo
            hex_truncated = hex_data[:60] + "..." if len(hex_data) > 60 else hex_data
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} - Protocolo detectado: {protocol_type}")
                if hex_truncated:
                    f.write(f" - Data: {hex_truncated}")
                f.write("\n")
                
        except Exception as e:
            print(f"Error guardando detección de protocolo: {e}")
    
    def log_send_attempt(self, 
                        protocol: str,
                        destination_ip: str,
                        destination_port: int,
                        data: str,
                        success: bool = True):
        """
        Registra intento de envío de datos
        
        Args:
            protocol: TCP o UDP
            destination_ip: IP de destino
            destination_port: Puerto de destino
            data: Datos enviados
            success: Si el envío fue exitoso
        """
        try:
            log_file = self.get_rpg_log_filename()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Truncar data si es muy largo
            data_truncated = data[:80] + "..." if len(data) > 80 else data
            
            status = "OK" if success else "FAIL"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} - Envío {protocol} a {destination_ip}:{destination_port} "
                       f"[{status}] - {data_truncated}\n")
                
        except Exception as e:
            print(f"Error guardando log de envío: {e}")


# Función de conveniencia para uso global
_rpg_logger = None

def get_rpg_logger(log_dir: str = "logs") -> RPGLogOptimizer:
    """
    Obtiene la instancia global del logger RPG optimizado
    
    Args:
        log_dir: Directorio de logs
        
    Returns:
        RPGLogOptimizer: Instancia del logger
    """
    global _rpg_logger
    if _rpg_logger is None:
        _rpg_logger = RPGLogOptimizer(log_dir)
    return _rpg_logger


# Ejemplo de uso
if __name__ == "__main__":
    # Crear logger
    logger = RPGLogOptimizer()
    
    # Ejemplo 1: Log completo con destinos
    logger.log_rpg_attempt(
        device_id="95999",
        protocol_type="59",
        latitude=-40.772199,
        longitude=-71.607830,
        heading=119,
        speed=0,
        fecha_gps="03/12/25",
        hora_gps="12:02:50",
        destinations=[
            ("UDP", "179.43.115.190", 7007, ">RGP031225120250-4046.3319-07136.4698000119000001;&01;ID=95999;#0001*62<"),
            ("TCP", "200.58.98.187", 5003, "24959917442103122534046331907136469800000000df54")
        ]
    )
    
    # Ejemplo 2: Log ultra-compacto
    logger.log_rpg_compact(
        device_id="95999",
        lat=-40.772199,
        lon=-71.607830,
        heading=119,
        speed=0,
        protocol="59",
        gps_time="03/12/25 12:02:50",
        send_info="UDP:179.43.115.190:7007"
    )
    
    print("✅ Logs de ejemplo creados en logs/RPG_*.txt")

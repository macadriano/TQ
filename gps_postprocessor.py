#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Post-Procesador GPS - Filtrado de Anomalías
Filtra y corrige anomalías GPS para generar mapas más precisos
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from simple_map_generator import SimpleGPSMapGenerator

class GPSPostProcessor:
    def __init__(self, log_file: str = 'tq_server_rpg.log'):
        self.log_file = log_file
        self.generator = SimpleGPSMapGenerator(log_file)
        self.filtered_count = 0
        
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distancia entre dos coordenadas usando fórmula de Haversine"""
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
    
    def calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula el rumbo entre dos coordenadas"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)
        
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def is_point_on_line(self, point: Dict, start: Dict, end: Dict, tolerance: float = 50.0) -> bool:
        """
        Verifica si un punto está aproximadamente en la línea entre start y end
        
        Args:
            point: Punto a verificar
            start: Punto inicial de la línea
            end: Punto final de la línea
            tolerance: Tolerancia en metros
            
        Returns:
            True si el punto está en la línea dentro de la tolerancia
        """
        # Distancia del punto a la línea usando fórmula de distancia punto-línea
        lat1, lon1 = start['latitude'], start['longitude']
        lat2, lon2 = end['latitude'], end['longitude']
        lat3, lon3 = point['latitude'], point['longitude']
        
        # Convertir a coordenadas cartesianas aproximadas (para distancias cortas)
        # 1 grado ≈ 111000 metros
        x1, y1 = lon1 * 111000 * math.cos(math.radians(lat1)), lat1 * 111000
        x2, y2 = lon2 * 111000 * math.cos(math.radians(lat2)), lat2 * 111000
        x3, y3 = lon3 * 111000 * math.cos(math.radians(lat3)), lat3 * 111000
        
        # Distancia punto-línea
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        distance = abs(A * x3 + B * y3 + C) / math.sqrt(A * A + B * B)
        
        return distance <= tolerance
    
    def filter_sudden_jumps(self, positions: List[Dict]) -> List[Dict]:
        """
        Filtra saltos bruscos de posición
        
        Criterios:
        - Distancia >100m en <30s
        - Velocidad calculada muy diferente a la reportada
        """
        if len(positions) < 2:
            return positions
        
        filtered = [positions[0]]  # Siempre mantener el primer punto
        
        for i in range(1, len(positions)):
            current = positions[i]
            previous = filtered[-1]  # Último punto válido
            
            # Calcular distancia y tiempo
            distance = self.calculate_distance(
                previous['latitude'], previous['longitude'],
                current['latitude'], current['longitude']
            )
            
            time_diff = (current['timestamp'] - previous['timestamp']).total_seconds()
            
            # Filtrar saltos bruscos
            if time_diff > 0:
                calculated_speed = (distance / time_diff) * 3.6  # km/h
                
                # Criterios de filtrado MEJORADOS
                is_sudden_jump = distance > 100 and time_diff < 30
                is_speed_anomaly = abs(calculated_speed - current['speed_kmh']) > 15  # Más estricto
                is_excessive_distance = distance > 1000 and time_diff < 600  # >1km en <10min
                is_stationary_jump = current['speed_kmh'] < 1 and distance > 100  # "Parado" pero saltó >100m
                
                if is_sudden_jump or is_speed_anomaly or is_excessive_distance or is_stationary_jump:
                    self.filtered_count += 1
                    reason = []
                    if is_sudden_jump: reason.append("salto brusco")
                    if is_speed_anomaly: reason.append("velocidad incoherente")
                    if is_excessive_distance: reason.append("distancia excesiva")
                    if is_stationary_jump: reason.append("salto estacionario")
                    print(f"🚫 Filtrado #{i}: {distance:.0f}m en {time_diff:.0f}s - {', '.join(reason)}")
                    continue  # Saltar este punto
            
            filtered.append(current)
        
        return filtered
    
    def filter_crossing_lines(self, positions: List[Dict]) -> List[Dict]:
        """
        Filtra líneas que cruzan por centros de manzanas
        
        Detecta puntos que se desvían significativamente de la línea directa
        entre el punto anterior y el siguiente.
        """
        if len(positions) < 3:
            return positions
        
        filtered = [positions[0]]  # Siempre mantener el primer punto
        
        i = 1
        while i < len(positions) - 1:
            prev_pos = filtered[-1]  # Último punto válido
            curr_pos = positions[i]
            next_pos = positions[i + 1]
            
            # Distancias
            dist_prev_curr = self.calculate_distance(
                prev_pos['latitude'], prev_pos['longitude'],
                curr_pos['latitude'], curr_pos['longitude']
            )
            
            dist_curr_next = self.calculate_distance(
                curr_pos['latitude'], curr_pos['longitude'],
                next_pos['latitude'], next_pos['longitude']
            )
            
            # Distancia directa (saltando el punto intermedio)
            dist_direct = self.calculate_distance(
                prev_pos['latitude'], prev_pos['longitude'],
                next_pos['latitude'], next_pos['longitude']
            )
            
            # Desviación del punto intermedio
            total_dist = dist_prev_curr + dist_curr_next
            deviation = total_dist - dist_direct
            
            # Criterios MEJORADOS para filtrar línea transversal:
            # 1. Desviación >30m (más estricto)
            # 2. Punto no está en la línea directa
            # 3. Distancias mínimas para evitar ruido
            # 4. Detectar "puntos estacionarios separados"
            
            time_prev_curr = (curr_pos['timestamp'] - prev_pos['timestamp']).total_seconds()
            time_curr_next = (next_pos['timestamp'] - curr_pos['timestamp']).total_seconds()
            
            # Detectar puntos estacionarios que están muy separados
            is_stationary_separated = (
                curr_pos['speed_kmh'] < 1 and  # Velocidad baja
                (dist_prev_curr > 500 or dist_curr_next > 500)  # Pero muy separado
            )
            
            is_crossing_line = (
                deviation > 30 and  # Más estricto
                dist_prev_curr > 20 and  # Reducido
                dist_curr_next > 20 and  # Reducido
                not self.is_point_on_line(curr_pos, prev_pos, next_pos, tolerance=25)
            ) or is_stationary_separated
            
            if is_crossing_line:
                self.filtered_count += 1
                print(f"🚫 Filtrada línea transversal #{i}: desviación {deviation:.0f}m")
                # Saltar este punto y continuar con el siguiente
                i += 1
                continue
            
            filtered.append(curr_pos)
            i += 1
        
        # Agregar el último punto
        if len(positions) > 0:
            filtered.append(positions[-1])
        
        return filtered
    
    def smooth_trajectory(self, positions: List[Dict], window_size: int = 3) -> List[Dict]:
        """
        Suaviza la trayectoria usando promedio móvil
        
        Args:
            positions: Lista de posiciones
            window_size: Tamaño de la ventana para el promedio (debe ser impar)
        """
        if len(positions) < window_size or window_size < 3:
            return positions
        
        smoothed = []
        half_window = window_size // 2
        
        # Mantener los primeros puntos sin suavizar
        for i in range(half_window):
            smoothed.append(positions[i])
        
        # Aplicar suavizado a los puntos intermedios
        for i in range(half_window, len(positions) - half_window):
            # Calcular promedio de coordenadas en la ventana
            window_positions = positions[i - half_window:i + half_window + 1]
            
            avg_lat = sum(p['latitude'] for p in window_positions) / len(window_positions)
            avg_lon = sum(p['longitude'] for p in window_positions) / len(window_positions)
            
            # Crear nuevo punto suavizado manteniendo otros datos del punto central
            smoothed_point = positions[i].copy()
            smoothed_point['latitude'] = avg_lat
            smoothed_point['longitude'] = avg_lon
            
            smoothed.append(smoothed_point)
        
        # Mantener los últimos puntos sin suavizar
        for i in range(len(positions) - half_window, len(positions)):
            smoothed.append(positions[i])
        
        return smoothed
    
    def filter_temporal_gaps(self, positions: List[Dict], max_gap_minutes: int = 10) -> List[Dict]:
        """
        Filtra posiciones con gaps temporales muy grandes
        """
        if len(positions) < 2:
            return positions
        
        filtered = [positions[0]]
        
        for i in range(1, len(positions)):
            current = positions[i]
            previous = filtered[-1]
            
            time_diff = (current['timestamp'] - previous['timestamp']).total_seconds() / 60  # minutos
            
            if time_diff > max_gap_minutes:
                self.filtered_count += 1
                print(f"🚫 Gap temporal muy grande #{i}: {time_diff:.1f} minutos")
                # Agregar el punto pero marcarlo como inicio de nuevo segmento
                current_copy = current.copy()
                current_copy['is_segment_start'] = True
                filtered.append(current_copy)
            else:
                filtered.append(current)
        
        return filtered
    
    def process_positions(self, positions: List[Dict], enable_smoothing: bool = True) -> List[Dict]:
        """
        Aplica todos los filtros de post-procesamiento
        
        Args:
            positions: Posiciones originales
            enable_smoothing: Si aplicar suavizado de trayectoria
            
        Returns:
            Posiciones filtradas y procesadas
        """
        if not positions:
            return positions
        
        original_count = len(positions)
        self.filtered_count = 0
        
        print(f"🔧 Post-procesando {original_count} posiciones GPS...")
        print()
        
        # 1. Filtrar saltos bruscos
        print("1️⃣  Filtrando saltos bruscos...")
        processed = self.filter_sudden_jumps(positions)
        print(f"   Posiciones después del filtro: {len(processed)}")
        print()
        
        # 2. Filtrar líneas transversales
        print("2️⃣  Filtrando líneas transversales...")
        processed = self.filter_crossing_lines(processed)
        print(f"   Posiciones después del filtro: {len(processed)}")
        print()
        
        # 3. Filtrar gaps temporales
        print("3️⃣  Filtrando gaps temporales...")
        processed = self.filter_temporal_gaps(processed, max_gap_minutes=15)
        print(f"   Posiciones después del filtro: {len(processed)}")
        print()
        
        # 4. Suavizar trayectoria (opcional)
        if enable_smoothing and len(processed) > 5:
            print("4️⃣  Suavizando trayectoria...")
            processed = self.smooth_trajectory(processed, window_size=3)
            print(f"   Trayectoria suavizada con ventana de 3 puntos")
            print()
        
        final_count = len(processed)
        filtered_percentage = (self.filtered_count / original_count) * 100
        
        print(f"✅ Post-procesamiento completado:")
        print(f"   • Posiciones originales: {original_count}")
        print(f"   • Posiciones filtradas: {self.filtered_count} ({filtered_percentage:.1f}%)")
        print(f"   • Posiciones finales: {final_count}")
        print(f"   • Mejora de calidad: {filtered_percentage:.1f}% de anomalías removidas")
        
        return processed
    
    def generate_clean_map(self, device_id: str = '68133', date_filter: str = None, 
                          output_file: str = 'mapa_filtrado.html', enable_smoothing: bool = True) -> str:
        """
        Genera un mapa limpio con posiciones post-procesadas
        """
        print("=" * 70)
        print("🧹 GENERADOR DE MAPA LIMPIO - POST-PROCESAMIENTO GPS")
        print("=" * 70)
        
        # Cargar posiciones originales
        original_positions = self.generator.load_positions_from_log(device_id, date_filter)
        
        if not original_positions:
            print("❌ No hay posiciones para procesar")
            return ""
        
        # Post-procesar
        clean_positions = self.process_positions(original_positions, enable_smoothing)
        
        if not clean_positions:
            print("❌ No quedaron posiciones después del filtrado")
            return ""
        
        # Generar mapa limpio
        print()
        print("🗺️  Generando mapa limpio...")
        output_path = self.generator.create_html_map(clean_positions, output_file)
        
        if output_path:
            print()
            print("🎉 ¡Mapa limpio generado exitosamente!")
            print(f"📂 Archivo: {output_path}")
            print("💡 Comparar con el mapa original para ver las mejoras")
            
        return output_path

def main():
    """Función principal"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='Post-Procesador GPS - Filtrado de Anomalías')
    parser.add_argument('--device', '-d', default='68133', help='ID del dispositivo')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), 
                       help='Fecha en formato YYYY-MM-DD')
    parser.add_argument('--output', '-o', default='mapa_filtrado.html', 
                       help='Archivo de salida')
    parser.add_argument('--no-smooth', action='store_true', 
                       help='Deshabilitar suavizado de trayectoria')
    
    args = parser.parse_args()
    
    # Crear post-procesador
    processor = GPSPostProcessor()
    
    # Generar mapa limpio
    processor.generate_clean_map(
        device_id=args.device,
        date_filter=args.date,
        output_file=args.output,
        enable_smoothing=not args.no_smooth
    )

if __name__ == "__main__":
    main()

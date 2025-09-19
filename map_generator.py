#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Mapas GPS - TQ Server RPG
Genera mapas interactivos con las posiciones de tracking GPS
"""

import re
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import folium
from folium import plugins

class GPSMapGenerator:
    def __init__(self, log_file: str = 'tq_server_rpg.log'):
        self.log_file = log_file
        self.positions = []
        
    def parse_position_line(self, line: str) -> Optional[Dict]:
        """
        Parsea una línea del log que contiene información de posición
        
        Formato esperado:
        2025-09-19 17:24:13 - INFO - Posición guardada: ID=68133, Lat=-34.699568°, Lon=-58.594918°, 
        Vel=15.8 km/h (8.5 nudos), Rumbo=97.0°, Dirección: 2243, República de Portugal, Atalaya...
        """
        try:
            # Patrón regex para extraer todos los campos
            pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Posición guardada: ID=([^,]+), Lat=([^°]+)°, Lon=([^°]+)°, Vel=([^k]+) km/h \(([^n]+) nudos\), Rumbo=([^°,]+)°(?:, Fecha GPS=([^,]+), Hora GPS=([^,]+))?(?:, Dirección: (.+))?'
            
            match = re.search(pattern, line)
            if match:
                timestamp_str = match.group(1)
                device_id = match.group(2)
                latitude = float(match.group(3))
                longitude = float(match.group(4))
                speed_kmh = float(match.group(5))
                speed_knots = float(match.group(6))
                heading = float(match.group(7))
                fecha_gps = match.group(8)
                hora_gps = match.group(9)
                direccion = match.group(10)
                
                # Parsear timestamp del log
                log_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # Si hay fecha/hora GPS, usarla como timestamp principal
                gps_timestamp = None
                if fecha_gps and hora_gps:
                    try:
                        # Formato: DD/MM/YY HH:MM:SS
                        dia, mes, año = fecha_gps.split('/')
                        hora, minuto, segundo = hora_gps.split(':')
                        gps_timestamp = datetime(int('20' + año), int(mes), int(dia), 
                                               int(hora), int(minuto), int(segundo))
                    except:
                        gps_timestamp = log_timestamp
                else:
                    gps_timestamp = log_timestamp
                
                return {
                    'timestamp': gps_timestamp,
                    'log_timestamp': log_timestamp,
                    'device_id': device_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'speed_kmh': speed_kmh,
                    'speed_knots': speed_knots,
                    'heading': heading,
                    'fecha_gps': fecha_gps,
                    'hora_gps': hora_gps,
                    'direccion': direccion or 'Sin dirección'
                }
            
        except Exception as e:
            print(f"Error parseando línea: {e}")
            print(f"Línea: {line[:100]}...")
            
        return None
    
    def load_positions_from_log(self, device_id: str = None, date_filter: str = None) -> List[Dict]:
        """
        Carga posiciones desde el archivo de log
        
        Args:
            device_id: ID del dispositivo a filtrar (ej: "68133")
            date_filter: Fecha a filtrar en formato YYYY-MM-DD (ej: "2025-09-19")
        """
        positions = []
        
        if not os.path.exists(self.log_file):
            print(f"❌ Archivo de log no encontrado: {self.log_file}")
            return positions
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Filtrar por fecha si se especifica
                    if date_filter and date_filter not in line:
                        continue
                    
                    # Solo procesar líneas con "Posición guardada"
                    if "Posición guardada" not in line:
                        continue
                    
                    # Filtrar por device_id si se especifica
                    if device_id and f"ID={device_id}" not in line:
                        continue
                    
                    position = self.parse_position_line(line)
                    if position:
                        positions.append(position)
        
        except Exception as e:
            print(f"❌ Error leyendo archivo de log: {e}")
        
        # Ordenar por timestamp GPS
        positions.sort(key=lambda x: x['timestamp'])
        
        print(f"📍 Cargadas {len(positions)} posiciones")
        if positions:
            print(f"   Rango: {positions[0]['timestamp'].strftime('%H:%M:%S')} - {positions[-1]['timestamp'].strftime('%H:%M:%S')}")
        
        return positions
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distancia entre dos coordenadas usando fórmula de Haversine"""
        import math
        
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
    
    def get_speed_color(self, speed_kmh: float) -> str:
        """Retorna color según la velocidad"""
        if speed_kmh == 0:
            return 'red'  # Detenido
        elif speed_kmh < 10:
            return 'orange'  # Muy lento
        elif speed_kmh < 30:
            return 'yellow'  # Lento
        elif speed_kmh < 50:
            return 'lightgreen'  # Moderado
        elif speed_kmh < 80:
            return 'green'  # Rápido
        else:
            return 'darkgreen'  # Muy rápido
    
    def create_map(self, positions: List[Dict], output_file: str = 'mapa_recorrido.html') -> str:
        """
        Crea un mapa interactivo con las posiciones
        
        Args:
            positions: Lista de posiciones GPS
            output_file: Nombre del archivo HTML a generar
            
        Returns:
            str: Ruta del archivo generado
        """
        if not positions:
            print("❌ No hay posiciones para mapear")
            return ""
        
        # Calcular centro del mapa
        center_lat = sum(p['latitude'] for p in positions) / len(positions)
        center_lon = sum(p['longitude'] for p in positions) / len(positions)
        
        # Crear mapa base
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=15,
            tiles='OpenStreetMap'
        )
        
        # Agregar capa de satélite
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satélite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Crear línea del recorrido
        route_coords = [[p['latitude'], p['longitude']] for p in positions]
        
        folium.PolyLine(
            route_coords,
            color='blue',
            weight=3,
            opacity=0.8,
            popup='Recorrido GPS'
        ).add_to(m)
        
        # Agregar marcadores para cada posición
        for i, pos in enumerate(positions):
            # Color según velocidad
            color = self.get_speed_color(pos['speed_kmh'])
            
            # Icono según si es inicio, fin o punto intermedio
            if i == 0:
                icon = folium.Icon(color='green', icon='play', prefix='fa')
                popup_title = "🚀 INICIO"
            elif i == len(positions) - 1:
                icon = folium.Icon(color='red', icon='stop', prefix='fa')
                popup_title = "🏁 FIN"
            else:
                icon = folium.Icon(color=color, icon='circle', prefix='fa')
                popup_title = f"📍 Punto {i+1}"
            
            # Crear popup con información detallada
            popup_html = f"""
            <div style="width: 300px;">
                <h4>{popup_title}</h4>
                <b>🕒 Hora GPS:</b> {pos['timestamp'].strftime('%H:%M:%S')}<br>
                <b>📍 Coordenadas:</b> {pos['latitude']:.6f}, {pos['longitude']:.6f}<br>
                <b>🚗 Velocidad:</b> {pos['speed_kmh']:.1f} km/h ({pos['speed_knots']:.1f} nudos)<br>
                <b>🧭 Rumbo:</b> {pos['heading']:.0f}°<br>
                <b>📱 Equipo:</b> {pos['device_id']}<br>
                <b>🏠 Dirección:</b> {pos['direccion'][:100]}{'...' if len(pos['direccion']) > 100 else ''}
            </div>
            """
            
            folium.Marker(
                location=[pos['latitude'], pos['longitude']],
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"Punto {i+1} - {pos['timestamp'].strftime('%H:%M:%S')} - {pos['speed_kmh']:.0f} km/h",
                icon=icon
            ).add_to(m)
        
        # Agregar plugin de medición de distancias
        plugins.MeasureControl().add_to(m)
        
        # Agregar plugin de pantalla completa
        plugins.Fullscreen().add_to(m)
        
        # Agregar control de capas
        folium.LayerControl().add_to(m)
        
        # Calcular estadísticas del recorrido
        total_distance = 0
        max_speed = max(p['speed_kmh'] for p in positions)
        avg_speed = sum(p['speed_kmh'] for p in positions) / len(positions)
        duration = (positions[-1]['timestamp'] - positions[0]['timestamp']).total_seconds() / 60
        
        for i in range(1, len(positions)):
            distance = self.calculate_distance(
                positions[i-1]['latitude'], positions[i-1]['longitude'],
                positions[i]['latitude'], positions[i]['longitude']
            )
            total_distance += distance
        
        # Agregar información del recorrido
        info_html = f"""
        <div style="position: fixed; 
                    top: 10px; left: 60px; width: 300px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>📊 Estadísticas del Recorrido</h4>
        <b>🚗 Equipo:</b> {positions[0]['device_id']}<br>
        <b>📅 Fecha:</b> {positions[0]['timestamp'].strftime('%d/%m/%Y')}<br>
        <b>⏱️ Duración:</b> {duration:.0f} minutos<br>
        <b>📏 Distancia:</b> {total_distance/1000:.2f} km<br>
        <b>🏃 Vel. Máx:</b> {max_speed:.0f} km/h<br>
        <b>🚶 Vel. Prom:</b> {avg_speed:.0f} km/h
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(info_html))
        
        # Guardar mapa
        m.save(output_file)
        print(f"✅ Mapa generado: {output_file}")
        print(f"📊 Estadísticas:")
        print(f"   • Puntos GPS: {len(positions)}")
        print(f"   • Distancia total: {total_distance/1000:.2f} km")
        print(f"   • Duración: {duration:.0f} minutos")
        print(f"   • Velocidad máxima: {max_speed:.0f} km/h")
        print(f"   • Velocidad promedio: {avg_speed:.0f} km/h")
        
        return output_file

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generador de Mapas GPS - TQ Server RPG')
    parser.add_argument('--device', '-d', default='68133', help='ID del dispositivo (default: 68133)')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d'), 
                       help='Fecha en formato YYYY-MM-DD (default: hoy)')
    parser.add_argument('--output', '-o', default='mapa_recorrido.html', 
                       help='Archivo de salida (default: mapa_recorrido.html)')
    parser.add_argument('--log', default='tq_server_rpg.log', 
                       help='Archivo de log (default: tq_server_rpg.log)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🗺️  GENERADOR DE MAPAS GPS - TQ SERVER RPG")
    print("=" * 70)
    print(f"📱 Equipo: {args.device}")
    print(f"📅 Fecha: {args.date}")
    print(f"📄 Log: {args.log}")
    print(f"🎯 Salida: {args.output}")
    print()
    
    # Crear generador
    generator = GPSMapGenerator(args.log)
    
    # Cargar posiciones
    positions = generator.load_positions_from_log(device_id=args.device, date_filter=args.date)
    
    if not positions:
        print("❌ No se encontraron posiciones para los criterios especificados")
        print("💡 Sugerencias:")
        print("   • Verificar que el archivo de log existe")
        print("   • Verificar el ID del dispositivo")
        print("   • Verificar la fecha (formato: YYYY-MM-DD)")
        print("   • Verificar que hay datos GPS para esa fecha")
        return
    
    # Generar mapa
    output_file = generator.create_map(positions, args.output)
    
    if output_file:
        print()
        print("🎉 ¡Mapa generado exitosamente!")
        print(f"📂 Abrir: {os.path.abspath(output_file)}")
        print("💡 El mapa es interactivo - puedes hacer clic en los puntos para ver detalles")

if __name__ == "__main__":
    main()

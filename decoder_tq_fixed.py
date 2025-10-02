#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decodificador TQ Corregido para archivo RECORRIDO61674_011025.txt
Analiza el formato real de los datos y los decodifica correctamente
"""

import re
import os
import sys
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class TQFixedDecoder:
    def __init__(self, archivo_recorrido: str = 'RECORRIDO61674_011025.txt'):
        self.archivo_recorrido = archivo_recorrido
        self.positions = []
        
    def analyze_hex_format(self, hex_message: str) -> Dict:
        """
        Analiza el formato hexadecimal para entender la estructura
        """
        print(f"🔍 Analizando formato: {hex_message[:50]}...")
        
        # El mensaje parece tener esta estructura:
        # 24207666167410521901102534381299060583274822016334fffffbff0006fdd300000000000000df54000000
        
        # Posibles campos identificados:
        # 242076661674 - ID del equipo (12 dígitos)
        # 105219 - Timestamp (6 dígitos)
        # 011025 - Fecha GPS (6 dígitos: DDMMYY)
        # 34381299 - Latitud (8 dígitos)
        # 06058327482 - Longitud (11 dígitos)
        # 2016334 - Velocidad (7 dígitos)
        # fffffbff0006fdd300000000000000df54000000 - Datos adicionales
        
        return {
            'device_id': hex_message[2:14],  # 242076661674
            'timestamp': hex_message[14:20],  # 105219
            'date_gps': hex_message[20:26],   # 011025
            'latitude': hex_message[26:34],   # 34381299
            'longitude': hex_message[34:45],  # 06058327482
            'speed': hex_message[45:52],      # 2016334
            'additional': hex_message[52:]    # Resto de datos
        }
    
    def decode_tq_message(self, hex_message: str) -> Optional[Dict]:
        """
        Decodifica un mensaje TQ usando el formato identificado
        """
        try:
            # Analizar estructura
            fields = self.analyze_hex_format(hex_message)
            
            # Extraer ID del equipo
            device_id = fields['device_id']
            
            # Decodificar fecha GPS (DDMMYY)
            date_hex = fields['date_gps']
            day = int(date_hex[:2])
            month = int(date_hex[2:4])
            year = 2000 + int(date_hex[4:6])
            
            # Decodificar timestamp (HHMMSS)
            time_hex = fields['timestamp']
            hour = int(time_hex[:2])
            minute = int(time_hex[2:4])
            second = int(time_hex[4:6])
            
            # Crear timestamp GPS
            gps_timestamp = datetime(year, month, day, hour, minute, second)
            
            # Decodificar coordenadas
            lat_hex = fields['latitude']
            lon_hex = fields['longitude']
            
            # Convertir coordenadas (formato TQ específico)
            latitude = self.hex_to_coordinate(lat_hex, is_latitude=True)
            longitude = self.hex_to_coordinate(lon_hex, is_latitude=False)
            
            # Decodificar velocidad
            speed_hex = fields['speed']
            speed_raw = int(speed_hex, 16)
            speed_kmh = speed_raw / 100.0  # Ajustar según formato TQ
            
            # Calcular rumbo (usando datos adicionales si están disponibles)
            heading = 0  # Por defecto
            
            return {
                'device_id': device_id,
                'latitude': latitude,
                'longitude': longitude,
                'speed_kmh': speed_kmh,
                'heading': heading,
                'gps_timestamp': gps_timestamp,
                'protocol': 'TQ_Custom',
                'raw_data': hex_message
            }
            
        except Exception as e:
            print(f"❌ Error decodificando mensaje TQ: {e}")
            return None
    
    def hex_to_coordinate(self, hex_value: str, is_latitude: bool = True) -> float:
        """
        Convierte valor hexadecimal a coordenada decimal
        """
        try:
            # Convertir hex a entero
            raw_value = int(hex_value, 16)
            
            if is_latitude:
                # Para latitud: dividir por 1000000 y ajustar
                coord = raw_value / 1000000.0
                # Ajustar para Buenos Aires (latitud negativa)
                if coord > 90:
                    coord = -coord + 180
                return coord
            else:
                # Para longitud: dividir por 1000000 y ajustar
                coord = raw_value / 1000000.0
                # Ajustar para Buenos Aires (longitud negativa)
                if coord > 180:
                    coord = -coord + 360
                return coord
                
        except Exception as e:
            print(f"❌ Error convirtiendo coordenada: {e}")
            return 0.0
    
    def load_positions_from_file(self) -> List[Dict]:
        """
        Carga y decodifica todas las posiciones del archivo
        """
        positions = []
        
        if not os.path.exists(self.archivo_recorrido):
            print(f"❌ Archivo no encontrado: {self.archivo_recorrido}")
            return positions
        
        try:
            with open(self.archivo_recorrido, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Buscar mensaje hexadecimal en la línea
                    hex_match = re.search(r':\s+([0-9a-fA-F]+)', line)
                    if hex_match:
                        hex_message = hex_match.group(1)
                        
                        # Decodificar mensaje
                        position = self.decode_tq_message(hex_message)
                        if position:
                            # Agregar timestamp del log
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if timestamp_match:
                                log_timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                position['log_timestamp'] = log_timestamp
                            
                            positions.append(position)
                            print(f"✅ Línea {line_num}: {position['device_id']} - {position['gps_timestamp'].strftime('%H:%M:%S')} - {position['latitude']:.6f}, {position['longitude']:.6f}")
        
        except Exception as e:
            print(f"❌ Error leyendo archivo: {e}")
        
        # Ordenar por timestamp GPS
        positions.sort(key=lambda x: x['gps_timestamp'])
        
        print(f"\n📍 Total posiciones decodificadas: {len(positions)}")
        if positions:
            print(f"   Rango GPS: {positions[0]['gps_timestamp'].strftime('%H:%M:%S')} - {positions[-1]['gps_timestamp'].strftime('%H:%M:%S')}")
        
        return positions
    
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
    
    def get_speed_color(self, speed_kmh: float) -> str:
        """Retorna color según la velocidad"""
        if speed_kmh == 0:
            return '#FF0000'  # Rojo - Detenido
        elif speed_kmh < 10:
            return '#FF8C00'  # Naranja - Muy lento
        elif speed_kmh < 30:
            return '#FFD700'  # Amarillo - Lento
        elif speed_kmh < 50:
            return '#ADFF2F'  # Verde claro - Moderado
        elif speed_kmh < 80:
            return '#32CD32'  # Verde - Rápido
        else:
            return '#006400'  # Verde oscuro - Muy rápido
    
    def create_html_map(self, positions: List[Dict], output_file: str = 'mapa_tq_decodificado.html') -> str:
        """
        Crea un mapa HTML con las posiciones decodificadas
        """
        if not positions:
            print("❌ No hay posiciones para mapear")
            return ""
        
        # Calcular centro del mapa
        center_lat = sum(p['latitude'] for p in positions) / len(positions)
        center_lon = sum(p['longitude'] for p in positions) / len(positions)
        
        # Calcular estadísticas
        total_distance = 0
        max_speed = max(p['speed_kmh'] for p in positions)
        avg_speed = sum(p['speed_kmh'] for p in positions) / len(positions)
        duration = (positions[-1]['gps_timestamp'] - positions[0]['gps_timestamp']).total_seconds() / 60
        
        for i in range(1, len(positions)):
            distance = self.calculate_distance(
                positions[i-1]['latitude'], positions[i-1]['longitude'],
                positions[i]['latitude'], positions[i]['longitude']
            )
            total_distance += distance
        
        # Preparar datos para JavaScript
        js_positions = []
        for i, pos in enumerate(positions):
            js_positions.append({
                'lat': pos['latitude'],
                'lng': pos['longitude'],
                'time': pos['gps_timestamp'].strftime('%H:%M:%S'),
                'speed': pos['speed_kmh'],
                'heading': pos['heading'],
                'color': self.get_speed_color(pos['speed_kmh']),
                'index': i + 1,
                'isStart': i == 0,
                'isEnd': i == len(positions) - 1,
                'protocol': pos['protocol']
            })
        
        # Template HTML
        html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mapa TQ Decodificado - Equipo {positions[0]['device_id']} - {positions[0]['gps_timestamp'].strftime('%d/%m/%Y')}</title>
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        #map {{
            height: 100vh;
            width: 100%;
        }}
        .info-panel {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 1000;
            max-width: 300px;
        }}
        .info-panel h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .info-panel p {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .legend {{
            position: absolute;
            bottom: 20px;
            left: 10px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            z-index: 1000;
        }}
        .legend h4 {{
            margin: 0 0 10px 0;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .route-info {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 8px;
            z-index: 1000;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info-panel">
        <h3>📊 Estadísticas del Recorrido</h3>
        <p><strong>🚗 Equipo:</strong> {positions[0]['device_id']}</p>
        <p><strong>📅 Fecha:</strong> {positions[0]['gps_timestamp'].strftime('%d/%m/%Y')}</p>
        <p><strong>⏱️ Duración:</strong> {duration:.0f} minutos</p>
        <p><strong>📏 Distancia:</strong> {total_distance/1000:.2f} km</p>
        <p><strong>🏃 Vel. Máx:</strong> {max_speed:.0f} km/h</p>
        <p><strong>🚶 Vel. Prom:</strong> {avg_speed:.0f} km/h</p>
        <p><strong>📍 Puntos GPS:</strong> {len(positions)}</p>
    </div>
    
    <div class="legend">
        <h4>🎨 Leyenda de Velocidades</h4>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FF0000;"></div>
            <span>0 km/h - Detenido</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FF8C00;"></div>
            <span>1-9 km/h - Muy lento</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FFD700;"></div>
            <span>10-29 km/h - Lento</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #ADFF2F;"></div>
            <span>30-49 km/h - Moderado</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #32CD32;"></div>
            <span>50-79 km/h - Rápido</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #006400;"></div>
            <span>80+ km/h - Muy rápido</span>
        </div>
    </div>

    <div class="route-info">
        <strong>🔧 Decodificado TQ</strong><br>
        Inicio: {positions[0]['gps_timestamp'].strftime('%H:%M:%S')}<br>
        Fin: {positions[-1]['gps_timestamp'].strftime('%H:%M:%S')}<br>
        Puntos: {len(positions)}<br>
        <small>Formato TQ personalizado</small>
    </div>

    <!-- Leaflet JavaScript -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    
    <script>
        // Datos de posiciones decodificadas
        const positions = {json.dumps(js_positions)};

        // Crear mapa centrado en las coordenadas promedio
        const map = L.map('map').setView([{center_lat}, {center_lon}], 15);

        // Agregar capas de mapas
        const osmLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }});

        const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '© Esri',
            maxZoom: 19
        }});

        // Agregar capa por defecto
        osmLayer.addTo(map);

        // Control de capas
        const baseLayers = {{
            "OpenStreetMap": osmLayer,
            "Satélite": satelliteLayer
        }};
        L.control.layers(baseLayers).addTo(map);

        // Crear línea del recorrido
        const routePath = positions.map(pos => [pos.lat, pos.lng]);
        const routeLine = L.polyline(routePath, {{
            color: '#0066CC',
            weight: 4,
            opacity: 0.8,
            smoothFactor: 1
        }}).addTo(map);

        // Función para crear icono SVG
        function createSVGIcon(color, symbol, size = 20) {{
            const svgIcon = L.divIcon({{
                html: `<svg width="${{size}}" height="${{size}}" viewBox="0 0 ${{size}} ${{size}}" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="${{size/2}}" cy="${{size/2}}" r="${{size/2-1}}" fill="${{color}}" stroke="#000" stroke-width="1"/>
                        <text x="${{size/2}}" y="${{size/2+3}}" text-anchor="middle" fill="#FFF" font-size="10" font-weight="bold">${{symbol}}</text>
                       </svg>`,
                className: 'custom-div-icon',
                iconSize: [size, size],
                iconAnchor: [size/2, size/2]
            }});
            return svgIcon;
        }}

        // Agregar marcadores para cada posición
        positions.forEach((pos, index) => {{
            let icon;
            let title;
            
            if (pos.isStart) {{
                icon = createSVGIcon('#00FF00', '▶', 24);
                title = '🚀 INICIO';
            }} else if (pos.isEnd) {{
                icon = createSVGIcon('#FF0000', '■', 24);
                title = '🏁 FIN';
            }} else {{
                icon = createSVGIcon(pos.color, '●', 16);
                title = `📍 Punto ${{pos.index}}`;
            }}

            const marker = L.marker([pos.lat, pos.lng], {{
                icon: icon,
                title: `${{title}} - ${{pos.time}} - ${{pos.speed}} km/h`
            }}).addTo(map);

            // Popup con información detallada
            const popupContent = `
                <div style="width: 280px;">
                    <h4>${{title}}</h4>
                    <p><strong>🕒 Hora GPS:</strong> ${{pos.time}}</p>
                    <p><strong>📍 Coordenadas:</strong> ${{pos.lat.toFixed(6)}}, ${{pos.lng.toFixed(6)}}</p>
                    <p><strong>🚗 Velocidad:</strong> ${{pos.speed}} km/h</p>
                    <p><strong>🧭 Rumbo:</strong> ${{pos.heading}}°</p>
                    <p><strong>📡 Protocolo:</strong> ${{pos.protocol}}</p>
                </div>
            `;

            marker.bindPopup(popupContent);
        }});

        // Ajustar el zoom para mostrar todo el recorrido
        const group = new L.featureGroup(positions.map(pos => L.marker([pos.lat, pos.lng])));
        map.fitBounds(group.getBounds().pad(0.05));

        // Agregar control de escala
        L.control.scale().addTo(map);
    </script>
</body>
</html>
        """
        
        # Guardar archivo HTML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"✅ Mapa TQ decodificado generado: {output_file}")
        print(f"📊 Estadísticas:")
        print(f"   • Puntos GPS: {len(positions)}")
        print(f"   • Distancia total: {total_distance/1000:.2f} km")
        print(f"   • Duración: {duration:.0f} minutos")
        print(f"   • Velocidad máxima: {max_speed:.0f} km/h")
        print(f"   • Velocidad promedio: {avg_speed:.0f} km/h")
        print(f"🔧 Decodificado usando formato TQ personalizado")
        
        return output_file

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Decodificador TQ Corregido')
    parser.add_argument('--archivo', '-f', default='RECORRIDO61674_011025.txt', 
                       help='Archivo de recorrido (default: RECORRIDO61674_011025.txt)')
    parser.add_argument('--output', '-o', default='mapa_tq_decodificado.html', 
                       help='Archivo de salida (default: mapa_tq_decodificado.html)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔧 DECODIFICADOR TQ CORREGIDO")
    print("=" * 70)
    print(f"📄 Archivo: {args.archivo}")
    print(f"🎯 Salida: {args.output}")
    print()
    
    # Crear decodificador
    decoder = TQFixedDecoder(args.archivo)
    
    # Cargar y decodificar posiciones
    positions = decoder.load_positions_from_file()
    
    if not positions:
        print("❌ No se encontraron posiciones para decodificar")
        print("💡 Sugerencias:")
        print("   • Verificar que el archivo existe")
        print("   • Verificar el formato del archivo")
        print("   • Verificar que contiene mensajes GPS válidos")
        return
    
    # Generar mapa
    output_file = decoder.create_html_map(positions, args.output)
    
    if output_file:
        print()
        print("🎉 ¡Mapa TQ decodificado generado exitosamente!")
        print(f"📂 Abrir: {os.path.abspath(output_file)}")
        print("🔧 Usando formato TQ personalizado para decodificación")

if __name__ == "__main__":
    main()

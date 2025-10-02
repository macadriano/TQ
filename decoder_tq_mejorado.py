#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decodificador TQ Mejorado - Con iconos de rumbo y etiquetas detalladas
"""

import re
import os
import sys
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

# Importar las funciones existentes del servidor
import funciones
import protocolo

class TQMejoradoDecoder:
    def __init__(self, archivo_recorrido: str = 'RECORRIDO61674_011025.txt'):
        self.archivo_recorrido = archivo_recorrido
        self.positions = []
        
    def decode_tq_message(self, hex_message: str) -> Optional[Dict]:
        """
        Decodifica un mensaje TQ usando las mismas funciones que tq_server_rpg.py
        """
        try:
            # Usar las mismas funciones que el servidor
            device_id = protocolo.getIDok(hex_message)
            
            # Extraer fecha y hora GPS
            fecha_gps = protocolo.getFECHA_GPS_TQ(hex_message)
            hora_gps = protocolo.getHORA_GPS_TQ(hex_message)
            
            # Extraer coordenadas usando las funciones del protocolo
            latitude = protocolo.getLATchino(hex_message)
            longitude = protocolo.getLONchino(hex_message)
            
            # Extraer velocidad y rumbo
            speed_knots = protocolo.getVELchino(hex_message)
            heading = protocolo.getRUMBOchino(hex_message)
            
            # Convertir velocidad de nudos a km/h
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
                'hora_gps': hora_gps,
                'protocol': 'TQ_Server_Method'
            }
            
        except Exception as e:
            print(f"❌ Error decodificando mensaje TQ: {e}")
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
            print(f"❌ Error parseando fecha GPS: {e}")
            return datetime(2025, 10, 1, 7, 52, 22)  # Fecha por defecto
    
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
                        
                        # Decodificar mensaje usando las funciones del servidor
                        position = self.decode_tq_message(hex_message)
                        if position:
                            # Agregar timestamp del log
                            timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                            if timestamp_match:
                                log_timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                position['log_timestamp'] = log_timestamp
                            
                            positions.append(position)
                            print(f"✅ Línea {line_num}: {position['device_id']} - {position['gps_timestamp'].strftime('%H:%M:%S')} - {position['latitude']:.6f}, {position['longitude']:.6f} - {position['speed_kmh']:.1f} km/h - Rumbo: {position['heading']:.0f}°")
        
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
    
    def get_heading_direction(self, heading: float) -> str:
        """Convierte rumbo en grados a dirección cardinal"""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                     "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
        index = int((heading + 11.25) / 22.5) % 16
        return directions[index]
    
    def create_html_map(self, positions: List[Dict], output_file: str = 'mapa_tq_mejorado.html') -> str:
        """
        Crea un mapa HTML mejorado con iconos de rumbo y etiquetas detalladas
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
                'direction': self.get_heading_direction(pos['heading']),
                'color': self.get_speed_color(pos['speed_kmh']),
                'index': i + 1,
                'isStart': i == 0,
                'isEnd': i == len(positions) - 1,
                'protocol': pos['protocol'],
                'fecha_gps': pos['fecha_gps'],
                'hora_gps': pos['hora_gps'],
                'speed_knots': pos['speed_knots']
            })
        
        # Template HTML mejorado
        html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mapa TQ Mejorado - Equipo {positions[0]['device_id']} - {positions[0]['gps_timestamp'].strftime('%d/%m/%Y')}</title>
    
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
        .heading-icon {{
            transform: rotate({positions[0]['heading']}deg);
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
        <strong>🔧 Decodificado con TQ Server</strong><br>
        Inicio: {positions[0]['gps_timestamp'].strftime('%H:%M:%S')}<br>
        Fin: {positions[-1]['gps_timestamp'].strftime('%H:%M:%S')}<br>
        Puntos: {len(positions)}<br>
        <small>Con iconos de rumbo y etiquetas</small>
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

        // Función para crear icono de rumbo
        function createHeadingIcon(heading, color, isStart, isEnd, size = 20) {{
            const symbol = isStart ? '▶' : isEnd ? '■' : '●';
            const svgIcon = L.divIcon({{
                html: `<svg width="${{size}}" height="${{size}}" viewBox="0 0 ${{size}} ${{size}}" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="${{size/2}}" cy="${{size/2}}" r="${{size/2-1}}" fill="${{color}}" stroke="#000" stroke-width="1"/>
                        <text x="${{size/2}}" y="${{size/2+3}}" text-anchor="middle" fill="#FFF" font-size="10" font-weight="bold">${{symbol}}</text>
                        <line x1="${{size/2}}" y1="${{size/2}}" x2="${{size/2 + Math.cos((heading-90) * Math.PI / 180) * (size/2-2)}}" y2="${{size/2 + Math.sin((heading-90) * Math.PI / 180) * (size/2-2)}}" stroke="#000" stroke-width="2" marker-end="url(#arrowhead)"/>
                        <defs>
                            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                                <polygon points="0 0, 10 3.5, 0 7" fill="#000" />
                            </marker>
                        </defs>
                       </svg>`,
                className: 'custom-div-icon heading-icon',
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
                icon = createHeadingIcon(pos.heading, '#00FF00', true, false, 24);
                title = '🚀 INICIO';
            }} else if (pos.isEnd) {{
                icon = createHeadingIcon(pos.heading, '#FF0000', false, true, 24);
                title = '🏁 FIN';
            }} else {{
                icon = createHeadingIcon(pos.heading, pos.color, false, false, 16);
                title = `📍 Punto ${{pos.index}}`;
            }}

            const marker = L.marker([pos.lat, pos.lng], {{
                icon: icon,
                title: `${{title}} - ${{pos.time}} - ${{pos.speed}} km/h - Rumbo: ${{pos.heading}}° ${{pos.direction}}`
            }}).addTo(map);

            // Popup con información detallada
            const popupContent = `
                <div style="width: 320px;">
                    <h4>${{title}}</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                        <div>
                            <p><strong>🕒 Hora GPS:</strong><br>${{pos.time}}</p>
                            <p><strong>📅 Fecha GPS:</strong><br>${{pos.fecha_gps}}</p>
                            <p><strong>📍 Coordenadas:</strong><br>${{pos.lat.toFixed(6)}}<br>${{pos.lng.toFixed(6)}}</p>
                        </div>
                        <div>
                            <p><strong>🚗 Velocidad:</strong><br>${{pos.speed}} km/h<br>(${{pos.speed_knots}} nudos)</p>
                            <p><strong>🧭 Rumbo:</strong><br>${{pos.heading}}° ${{pos.direction}}</p>
                            <p><strong>📡 Protocolo:</strong><br>${{pos.protocol}}</p>
                        </div>
                    </div>
                    <div style="border-top: 1px solid #ccc; padding-top: 10px; margin-top: 10px;">
                        <small><strong>Punto ${{pos.index}} de ${{positions.length}}</strong></small>
                    </div>
                </div>
            `;

            marker.bindPopup(popupContent);
        }});

        // Ajustar el zoom para mostrar todo el recorrido
        const group = new L.featureGroup(positions.map(pos => L.marker([pos.lat, pos.lng])));
        map.fitBounds(group.getBounds().pad(0.05));

        // Agregar control de escala
        L.control.scale().addTo(map);
        
        // Agregar control de rumbo
        const headingControl = L.control({{position: 'bottomright'}});
        headingControl.onAdd = function(map) {{
            const div = L.DomUtil.create('div', 'leaflet-control-attribution');
            div.innerHTML = '<div style="background: white; padding: 5px; border-radius: 3px; font-size: 12px;"><strong>🧭 Iconos de Rumbo</strong><br>Las flechas indican la dirección de movimiento</div>';
            return div;
        }};
        headingControl.addTo(map);
    </script>
</body>
</html>
        """
        
        # Guardar archivo HTML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"✅ Mapa TQ mejorado generado: {output_file}")
        print(f"📊 Estadísticas:")
        print(f"   • Puntos GPS: {len(positions)}")
        print(f"   • Distancia total: {total_distance/1000:.2f} km")
        print(f"   • Duración: {duration:.0f} minutos")
        print(f"   • Velocidad máxima: {max_speed:.0f} km/h")
        print(f"   • Velocidad promedio: {avg_speed:.0f} km/h")
        print(f"🔧 Decodificado usando funciones de tq_server_rpg.py")
        print(f"🧭 Con iconos de rumbo y etiquetas detalladas")
        
        return output_file

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Decodificador TQ Mejorado')
    parser.add_argument('--archivo', '-f', default='RECORRIDO61674_011025.txt', 
                       help='Archivo de recorrido')
    parser.add_argument('--output', '-o', default='mapa_tq_mejorado.html', 
                       help='Archivo de salida')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔧 DECODIFICADOR TQ MEJORADO")
    print("=" * 70)
    print(f"📄 Archivo: {args.archivo}")
    print(f"🎯 Salida: {args.output}")
    print("🔧 Usando funciones de tq_server_rpg.py")
    print("🧭 Con iconos de rumbo y etiquetas detalladas")
    print()
    
    # Crear decodificador
    decoder = TQMejoradoDecoder(args.archivo)
    
    # Cargar y decodificar posiciones
    positions = decoder.load_positions_from_file()
    
    if not positions:
        print("❌ No se encontraron posiciones para decodificar")
        return
    
    # Generar mapa
    output_file = decoder.create_html_map(positions, args.output)
    
    if output_file:
        print()
        print("🎉 ¡Mapa TQ mejorado generado exitosamente!")
        print(f"📂 Abrir: {os.path.abspath(output_file)}")
        print("🔧 Usando las mismas funciones que tq_server_rpg.py")
        print("🧭 Con iconos de rumbo y etiquetas detalladas")

if __name__ == "__main__":
    main()

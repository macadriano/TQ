#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de Mapas GPS Simplificado - TQ Server RPG
Genera mapas HTML básicos con las posiciones de tracking GPS
"""

import re
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class SimpleGPSMapGenerator:
    def __init__(self, log_file: str = 'tq_server_rpg.log'):
        self.log_file = log_file
        
    def parse_position_line(self, line: str) -> Optional[Dict]:
        """
        Parsea una línea del log que contiene información de posición
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
            
        return None
    
    def load_positions_from_log(self, device_id: str = None, date_filter: str = None) -> List[Dict]:
        """
        Carga posiciones desde el archivo de log
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
    
    def create_html_map(self, positions: List[Dict], output_file: str = 'mapa_recorrido.html') -> str:
        """
        Crea un mapa HTML con Google Maps API
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
        duration = (positions[-1]['timestamp'] - positions[0]['timestamp']).total_seconds() / 60
        
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
                'time': pos['timestamp'].strftime('%H:%M:%S'),
                'speed': pos['speed_kmh'],
                'heading': pos['heading'],
                'address': pos['direccion'],
                'color': self.get_speed_color(pos['speed_kmh']),
                'index': i + 1,
                'isStart': i == 0,
                'isEnd': i == len(positions) - 1
            })
        
        # Template HTML con OpenStreetMap y Leaflet
        html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mapa GPS - Equipo {positions[0]['device_id']} - {positions[0]['timestamp'].strftime('%d/%m/%Y')}</title>
    
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
    </style>
</head>
<body>
    <div id="map"></div>
    
    <div class="info-panel">
        <h3>📊 Estadísticas del Recorrido</h3>
        <p><strong>🚗 Equipo:</strong> {positions[0]['device_id']}</p>
        <p><strong>📅 Fecha:</strong> {positions[0]['timestamp'].strftime('%d/%m/%Y')}</p>
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

    <!-- Leaflet JavaScript -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    
    <script>
        // Datos de posiciones
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
            weight: 3,
            opacity: 0.8
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
                    <p><strong>🏠 Dirección:</strong> ${{pos.address.substring(0, 100)}}${{pos.address.length > 100 ? '...' : ''}}</p>
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
        
        print(f"✅ Mapa HTML generado: {output_file}")
        print(f"📊 Estadísticas:")
        print(f"   • Puntos GPS: {len(positions)}")
        print(f"   • Distancia total: {total_distance/1000:.2f} km")
        print(f"   • Duración: {duration:.0f} minutos")
        print(f"   • Velocidad máxima: {max_speed:.0f} km/h")
        print(f"   • Velocidad promedio: {avg_speed:.0f} km/h")
        print(f"🗺️  Usando OpenStreetMap (gratuito, sin API keys)")
        
        return output_file

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generador de Mapas GPS Simplificado - TQ Server RPG')
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
    generator = SimpleGPSMapGenerator(args.log)
    
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
    output_file = generator.create_html_map(positions, args.output)
    
    if output_file:
        print()
        print("🎉 ¡Mapa generado exitosamente!")
        print(f"📂 Abrir: {os.path.abspath(output_file)}")
        print("💡 El mapa es interactivo - puedes hacer clic en los puntos para ver detalles")
        print("🗺️  Usa OpenStreetMap (gratuito) + vista satelital disponible")
        print("🌐 Requiere conexión a internet para cargar los mapas")

if __name__ == "__main__":
    main()

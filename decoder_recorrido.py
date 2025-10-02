#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decodificador de datos GPS TQ para archivo RECORRIDO61674_011025.txt
Usa las funciones existentes de funciones.py y protocolo.py
"""

import re
import os
import sys
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

# Importar funciones existentes
import funciones
import protocolo

class TQRecorridoDecoder:
    def __init__(self, archivo_recorrido: str = 'RECORRIDO61674_011025.txt'):
        self.archivo_recorrido = archivo_recorrido
        self.positions = []
        
    def parse_hex_message(self, hex_message: str) -> Optional[Dict]:
        """
        Decodifica un mensaje hexadecimal TQ usando las funciones existentes
        """
        try:
            # Limpiar el mensaje hexadecimal
            hex_clean = hex_message.strip()
            
            # Detectar tipo de protocolo
            if hex_clean.startswith('24'):  # Protocolo 66 (hexadecimal)
                return self.decode_protocol_66(hex_clean)
            elif hex_clean.startswith('2a'):  # Protocolo 2c (NMEA)
                return self.decode_protocol_2c(hex_clean)
            else:
                print(f"⚠️  Protocolo no reconocido: {hex_clean[:10]}...")
                return None
                
        except Exception as e:
            print(f"❌ Error decodificando mensaje: {e}")
            return None
    
    def decode_protocol_66(self, hex_message: str) -> Optional[Dict]:
        """
        Decodifica protocolo 66 (hexadecimal) usando funciones existentes
        """
        try:
            # Usar función existente para extraer ID
            device_id = protocolo.getIDok(hex_message)
            
            # Extraer coordenadas usando funciones existentes
            lat_hex = hex_message[24:32]  # Posiciones 24-31
            lon_hex = hex_message[32:40]  # Posiciones 32-39
            
            # Convertir coordenadas hexadecimales a decimales
            lat_raw = int(lat_hex, 16)
            lon_raw = int(lon_hex, 16)
            
            # Convertir a grados decimales (formato TQ)
            latitude = lat_raw / 1000000.0
            longitude = lon_raw / 1000000.0
            
            # Extraer velocidad y rumbo
            speed_hex = hex_message[40:44]
            heading_hex = hex_message[44:48]
            
            speed_raw = int(speed_hex, 16)
            heading_raw = int(heading_hex, 16)
            
            # Convertir velocidad (nudos a km/h)
            speed_kmh = speed_raw * 1.852
            
            # Extraer fecha y hora GPS
            fecha_hex = hex_message[8:16]
            hora_hex = hex_message[16:24]
            
            # Convertir fecha y hora
            fecha_raw = int(fecha_hex, 16)
            hora_raw = int(hora_hex, 16)
            
            # Formatear fecha (DDMMYY)
            dia = fecha_raw // 10000
            mes = (fecha_raw % 10000) // 100
            año = fecha_raw % 100
            
            # Formatear hora (HHMMSS)
            hora = hora_raw // 10000
            minuto = (hora_raw % 10000) // 100
            segundo = hora_raw % 100
            
            # Crear timestamp GPS
            gps_timestamp = datetime(2000 + año, mes, dia, hora, minuto, segundo)
            
            return {
                'device_id': device_id,
                'latitude': latitude,
                'longitude': longitude,
                'speed_kmh': speed_kmh,
                'heading': heading_raw,
                'gps_timestamp': gps_timestamp,
                'protocol': '66'
            }
            
        except Exception as e:
            print(f"❌ Error decodificando protocolo 66: {e}")
            return None
    
    def decode_protocol_2c(self, hex_message: str) -> Optional[Dict]:
        """
        Decodifica protocolo 2c (NMEA) usando funciones existentes
        """
        try:
            # Convertir hex a string NMEA
            hex_clean = hex_message[2:]  # Remover '2a'
            nmea_bytes = bytes.fromhex(hex_clean)
            nmea_string = nmea_bytes.decode('ascii', errors='ignore')
            
            # Buscar coordenadas en formato NMEA
            # Formato: *HQ,ID,V1,HHMMSS,V/A,DDMM.MMMM,N/S,DDDMM.MMMM,E/W,SPEED,HEADING,DDMMYY,...
            pattern = r'\*HQ,(\d+),V1,(\d{6}),([VA]),(\d{2})(\d{2}\.\d{4}),([NS]),(\d{3})(\d{2}\.\d{4}),([EW]),(\d+\.\d+),(\d+),(\d{6})'
            match = re.search(pattern, nmea_string)
            
            if match:
                device_id = match.group(1)
                hora_gps = match.group(2)
                valid = match.group(3)
                lat_deg = int(match.group(4))
                lat_min = float(match.group(5))
                lat_dir = match.group(6)
                lon_deg = int(match.group(7))
                lon_min = float(match.group(8))
                lon_dir = match.group(9)
                speed = float(match.group(10))
                heading = float(match.group(11))
                fecha_gps = match.group(12)
                
                # Convertir coordenadas a decimales
                latitude = lat_deg + lat_min / 60.0
                if lat_dir == 'S':
                    latitude = -latitude
                    
                longitude = lon_deg + lon_min / 60.0
                if lon_dir == 'W':
                    longitude = -longitude
                
                # Convertir velocidad (nudos a km/h)
                speed_kmh = speed * 1.852
                
                # Crear timestamp GPS
                dia = int(fecha_gps[:2])
                mes = int(fecha_gps[2:4])
                año = int(fecha_gps[4:6])
                hora = int(hora_gps[:2])
                minuto = int(hora_gps[2:4])
                segundo = int(hora_gps[4:6])
                
                gps_timestamp = datetime(2000 + año, mes, dia, hora, minuto, segundo)
                
                return {
                    'device_id': device_id,
                    'latitude': latitude,
                    'longitude': longitude,
                    'speed_kmh': speed_kmh,
                    'heading': heading,
                    'gps_timestamp': gps_timestamp,
                    'protocol': '2c',
                    'valid': valid == 'A'
                }
            
        except Exception as e:
            print(f"❌ Error decodificando protocolo 2c: {e}")
            return None
    
    def load_positions_from_file(self) -> List[Dict]:
        """
        Carga y decodifica todas las posiciones del archivo de recorrido
        """
        positions = []
        
        if not os.path.exists(self.archivo_recorrido):
            print(f"❌ Archivo de recorrido no encontrado: {self.archivo_recorrido}")
            return positions
        
        try:
            with open(self.archivo_recorrido, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Buscar mensaje hexadecimal en la línea
                    hex_match = re.search(r':\s+([0-9a-fA-F]+)', line)
                    if hex_match:
                        hex_message = hex_match.group(1)
                        
                        # Decodificar mensaje
                        position = self.parse_hex_message(hex_message)
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
    
    def create_html_map(self, positions: List[Dict], output_file: str = 'mapa_recorrido_decodificado.html') -> str:
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
    <title>Mapa GPS Decodificado - Equipo {positions[0]['device_id']} - {positions[0]['gps_timestamp'].strftime('%d/%m/%Y')}</title>
    
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
        <small>Usando funciones TQ existentes</small>
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
                    <p><strong>📡 Protocolo:</strong> TQ ${{pos.protocol}}</p>
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
        
        print(f"✅ Mapa decodificado generado: {output_file}")
        print(f"📊 Estadísticas:")
        print(f"   • Puntos GPS: {len(positions)}")
        print(f"   • Distancia total: {total_distance/1000:.2f} km")
        print(f"   • Duración: {duration:.0f} minutos")
        print(f"   • Velocidad máxima: {max_speed:.0f} km/h")
        print(f"   • Velocidad promedio: {avg_speed:.0f} km/h")
        print(f"🔧 Decodificado usando funciones TQ existentes")
        
        return output_file

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Decodificador de Recorrido GPS TQ')
    parser.add_argument('--archivo', '-f', default='RECORRIDO61674_011025.txt', 
                       help='Archivo de recorrido (default: RECORRIDO61674_011025.txt)')
    parser.add_argument('--output', '-o', default='mapa_recorrido_decodificado.html', 
                       help='Archivo de salida (default: mapa_recorrido_decodificado.html)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔧 DECODIFICADOR DE RECORRIDO GPS TQ")
    print("=" * 70)
    print(f"📄 Archivo: {args.archivo}")
    print(f"🎯 Salida: {args.output}")
    print()
    
    # Crear decodificador
    decoder = TQRecorridoDecoder(args.archivo)
    
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
        print("🎉 ¡Mapa decodificado generado exitosamente!")
        print(f"📂 Abrir: {os.path.abspath(output_file)}")
        print("🔧 Usando funciones TQ existentes para decodificación")

if __name__ == "__main__":
    main()

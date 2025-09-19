# Generador de Mapas GPS - TQ Server RPG

## Descripción
Módulo para generar mapas interactivos con los recorridos GPS basados en los logs del servidor TQ RPG.

## Archivos
- `map_generator.py` - Versión avanzada con Folium (requiere `pip install folium`)
- `simple_map_generator.py` - Versión con OpenStreetMap + Leaflet (sin dependencias externas)

## Uso Básico

### Generar mapa del día actual para equipo 68133
```bash
python simple_map_generator.py
```

### Generar mapa para fecha específica
```bash
python simple_map_generator.py --date 2025-09-19
```

### Generar mapa para otro equipo
```bash
python simple_map_generator.py --device 12345 --date 2025-09-19
```

### Especificar archivo de salida personalizado
```bash
python simple_map_generator.py --output mi_recorrido.html
```

## Parámetros

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `--device` / `-d` | ID del dispositivo GPS | `68133` |
| `--date` | Fecha en formato YYYY-MM-DD | Hoy |
| `--output` / `-o` | Archivo HTML de salida | `mapa_recorrido.html` |
| `--log` | Archivo de log a procesar | `tq_server_rpg.log` |

## Características del Mapa

### 🎨 Colores por Velocidad
- **🔴 Rojo**: 0 km/h - Detenido
- **🟠 Naranja**: 1-9 km/h - Muy lento  
- **🟡 Amarillo**: 10-29 km/h - Lento
- **🟢 Verde claro**: 30-49 km/h - Moderado
- **🟢 Verde**: 50-79 km/h - Rápido
- **🟢 Verde oscuro**: 80+ km/h - Muy rápido

### 📍 Marcadores Especiales
- **🚀 Verde con ▶**: Punto de inicio del recorrido
- **🏁 Rojo con ■**: Punto final del recorrido
- **⭕ Círculos coloreados**: Puntos intermedios (color según velocidad)

### 📊 Información Mostrada
- **Panel de estadísticas**: Distancia total, duración, velocidades
- **Tooltips**: Información rápida al pasar el mouse
- **Popups**: Información detallada al hacer clic
- **Línea de recorrido**: Conecta todos los puntos GPS

## Ejemplo de Salida

```
======================================================================
🗺️  GENERADOR DE MAPAS GPS - TQ SERVER RPG
======================================================================
📱 Equipo: 68133
📅 Fecha: 2025-09-19
📄 Log: tq_server_rpg.log
🎯 Salida: mapa_recorrido.html

📍 Cargadas 202 posiciones
   Rango: 17:23:53 - 21:06:35
✅ Mapa HTML generado: mapa_recorrido.html
📊 Estadísticas:
   • Puntos GPS: 202
   • Distancia total: 18.61 km
   • Duración: 223 minutos
   • Velocidad máxima: 42 km/h
   • Velocidad promedio: 14 km/h

🎉 ¡Mapa generado exitosamente!
📂 Abrir: C:\proyectosGIT\TQ\mapa_recorrido.html
💡 El mapa es interactivo - puedes hacer clic en los puntos para ver detalles
🌐 Requiere conexión a internet para cargar Google Maps
```

## Información en el Mapa

Cada punto del mapa muestra:
- **🕒 Hora GPS**: Timestamp basado en fecha/hora GPS del protocolo TQ
- **📍 Coordenadas**: Latitud y longitud precisas
- **🚗 Velocidad**: En km/h
- **🧭 Rumbo**: En grados (0-360°)
- **🏠 Dirección**: Obtenida mediante geocodificación (si está habilitada)

## Requisitos

### Versión con OpenStreetMap (simple_map_generator.py)
- ✅ Python 3.6+
- ✅ Sin dependencias externas
- ✅ Usa OpenStreetMap + Leaflet (gratuito, sin API keys)
- ✅ Vista satelital disponible (Esri)
- ⚠️ Requiere conexión a internet

### Versión Avanzada (map_generator.py)
- Python 3.6+
- `pip install folium`
- Genera mapas offline con OpenStreetMap

## Notas Técnicas

1. **Parseo de Logs**: Extrae automáticamente coordenadas, velocidad, rumbo y direcciones del log
2. **Filtrado Inteligente**: Filtra por equipo y fecha automáticamente
3. **Ordenamiento**: Ordena puntos por timestamp GPS (no por hora de recepción)
4. **Cálculo de Distancias**: Usa fórmula de Haversine para precisión
5. **Manejo de Errores**: Robusto ante líneas malformadas en el log

## Solución de Problemas

### "No se encontraron posiciones"
- Verificar que existe el archivo `tq_server_rpg.log`
- Verificar el ID del dispositivo (usar el que aparece en los logs)
- Verificar la fecha (formato: YYYY-MM-DD)
- Verificar que hay datos GPS para esa fecha

### "Error parseando línea"
- El formato del log puede haber cambiado
- Verificar que las líneas contienen "Posición guardada"

### El mapa no se muestra
- Verificar conexión a internet
- El archivo HTML debe abrirse en un navegador web
- OpenStreetMap y Leaflet requieren conexión activa

## Automatización

Para generar mapas automáticamente cada día:

```bash
# Crear script batch (Windows)
echo python simple_map_generator.py --output mapa_%date:~-4,4%-%date:~-7,2%-%date:~-10,2%.html > generar_mapa_diario.bat

# Ejecutar desde cron (Linux)
0 23 * * * cd /ruta/al/proyecto && python simple_map_generator.py --output mapa_$(date +\%Y-\%m-\%d).html
```

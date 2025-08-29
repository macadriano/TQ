# Servidor TCP Protocolo TQ

Este proyecto implementa un servidor TCP para manejar conexiones de equipos GPS que utilizan el protocolo TQ. El servidor decodifica mensajes de posición y extrae información de latitud, longitud, rumbo, velocidad e ID del equipo.

## Características

- ✅ Servidor TCP multihilo que maneja múltiples conexiones simultáneas
- ✅ Decodificación automática de mensajes de posición
- ✅ Soporte para múltiples formatos de mensaje (binario, texto, hexadecimal)
- ✅ Logging completo de todas las interacciones
- ✅ Visualización en tiempo real de datos de posición
- ✅ Cliente de prueba para simular equipos GPS
- ✅ Interfaz de comandos para monitoreo del servidor

## Archivos del Proyecto

- `tq_server.py` - Servidor principal TCP
- `tq_client_test.py` - Cliente de prueba para simular equipos GPS
- `tq_server.log` - Archivo de log generado automáticamente
- `README.md` - Este archivo de documentación

## Requisitos

- Python 3.7 o superior
- Bibliotecas estándar de Python (no requiere instalaciones adicionales)

## Instalación

1. Clona o descarga este proyecto
2. Navega al directorio del proyecto
3. No se requieren dependencias adicionales

## Uso

### 1. Iniciar el Servidor

```bash
python tq_server.py
```

El servidor se iniciará en `0.0.0.0:8080` por defecto.

**Comandos disponibles en el servidor:**
- `status` - Mostrar estado del servidor
- `clients` - Mostrar clientes conectados
- `quit` - Salir del servidor

### 2. Ejecutar Cliente de Prueba

En otra terminal:

```bash
python tq_client_test.py
```

**Opciones del cliente:**
1. **Cliente único** - Un solo equipo simulando movimiento
2. **Múltiples clientes** - Varios equipos conectándose simultáneamente
3. **Cliente con formato específico** - Control sobre el formato del mensaje

## Formatos de Mensaje Soportados

### Formato 1: Binario (struct)
```
[ID(4 bytes)][LAT(4 bytes)][LON(4 bytes)][RUMBO(2 bytes)][VELOCIDAD(2 bytes)]
```

### Formato 2: Texto con delimitadores
```
ID,LATITUD,LONGITUD,RUMBO,VELOCIDAD
```

### Formato 3: Hexadecimal
```
ID_HEX + LAT_HEX + LON_HEX + RUMBO_HEX + VELOCIDAD_HEX
```

## Estructura de Datos Decodificados

Cada mensaje de posición se decodifica en un diccionario con:

```python
{
    'device_id': 1234,           # ID del equipo
    'latitude': -34.6037,        # Latitud en grados decimales
    'longitude': -58.3816,       # Longitud en grados decimales
    'heading': 45.0,             # Rumbo en grados (0-360)
    'speed': 25.5,               # Velocidad en km/h
    'timestamp': '2024-01-01T12:00:00'  # Timestamp ISO
}
```

## Logging

El servidor genera logs automáticamente en `tq_server.log` con:

- Conexiones y desconexiones de clientes
- Mensajes recibidos (formato hexadecimal)
- Datos de posición decodificados
- Errores y advertencias

## Personalización del Protocolo

Para adaptar el servidor a un protocolo específico:

1. **Modificar `decode_position_message()`** en `tq_server.py`
2. **Ajustar los formatos de decodificación** según la documentación del protocolo
3. **Actualizar las estructuras de datos** según los campos requeridos

### Ejemplo de personalización:

```python
def decode_custom_protocol(self, data: bytes) -> Optional[Dict]:
    """Decodifica protocolo personalizado"""
    try:
        # Implementar decodificación específica aquí
        # Según la documentación del protocolo TQ
        
        # Ejemplo:
        # device_id = struct.unpack('>I', data[0:4])[0]
        # latitude = struct.unpack('>f', data[4:8])[0]
        # ... etc
        
        return position_data
    except Exception as e:
        self.logger.error(f"Error decodificando: {e}")
        return None
```

## Monitoreo en Tiempo Real

El servidor muestra en pantalla:

```
📍 POSICIÓN RECIBIDA de 192.168.1.100:54321
   ID Equipo: 1234
   Latitud: -34.603700°
   Longitud: -58.381600°
   Rumbo: 45.0°
   Velocidad: 25.5 km/h
   Timestamp: 2024-01-01T12:00:00
```

## Solución de Problemas

### Error de conexión
- Verificar que el puerto 8080 esté disponible
- Comprobar firewall y configuraciones de red

### Mensajes no decodificados
- Revisar el formato del protocolo en el PDF
- Ajustar las funciones de decodificación
- Verificar logs para errores específicos

### Cliente no se conecta
- Verificar que el servidor esté ejecutándose
- Comprobar host y puerto en la configuración del cliente

## Configuración Avanzada

### Cambiar puerto del servidor:

```python
server = TQServer(host='0.0.0.0', port=9090)
```

### Configurar logging personalizado:

```python
# En setup_logging()
file_handler = logging.FileHandler('mi_servidor.log', encoding='utf-8')
```

## Contribuciones

Para contribuir al proyecto:

1. Analiza el protocolo específico del PDF
2. Adapta las funciones de decodificación
3. Prueba con equipos reales
4. Documenta cualquier cambio en el protocolo

## Licencia

Este proyecto está diseñado para uso educativo y de desarrollo. Adapta según tus necesidades específicas.

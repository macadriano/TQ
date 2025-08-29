# 🚀 Inicio Rápido - Servidor TQ

## Instalación y Configuración

### 1. Verificar Python
```bash
python --version  # Debe ser 3.7 o superior
```

### 2. Ejecutar Instalador
```bash
python setup.py
```

## Uso Básico

### Paso 1: Iniciar el Servidor
```bash
# Opción 1: Script automático
start_server.bat

# Opción 2: Manual
python tq_server.py
```

**El servidor se iniciará en `0.0.0.0:8080`**

### Paso 2: Probar con Cliente
En otra terminal:
```bash
# Opción 1: Script automático
start_client.bat

# Opción 2: Manual
python tq_client_test.py
```

## Comandos del Servidor

Una vez iniciado el servidor, puedes usar estos comandos:

- `status` - Ver estado del servidor
- `clients` - Ver clientes conectados
- `quit` - Salir del servidor

## Ejemplo de Salida

```
🚀 Servidor TQ iniciado en 0.0.0.0:8080
📡 Esperando conexiones de equipos...

🔗 Nueva conexión desde 127.0.0.1:54321
📨 Msg #1 de 127.0.0.1:54321
   Raw: 000004d2c2a8f5c3c2a8f5c3002d0019

📍 POSICIÓN RECIBIDA de 127.0.0.1:54321
   ID Equipo: 1234
   Latitud: -34.603700°
   Longitud: -58.381600°
   Rumbo: 45.0°
   Velocidad: 25.5 km/h
   Timestamp: 2024-01-01T12:00:00
```

## Personalización del Protocolo

Para adaptar a tu protocolo específico:

1. **Editar `config.py`** - Configuración general
2. **Modificar `tq_server.py`** - Función `decode_position_message()`
3. **Revisar el PDF del protocolo** - Para detalles específicos

### Ejemplo de Personalización:

```python
def decode_custom_protocol(self, data: bytes) -> Optional[Dict]:
    """Decodifica tu protocolo específico"""
    try:
        # Implementar según tu protocolo
        device_id = struct.unpack('>I', data[0:4])[0]
        latitude = struct.unpack('>f', data[4:8])[0]
        longitude = struct.unpack('>f', data[8:12])[0]
        
        return {
            'device_id': device_id,
            'latitude': latitude,
            'longitude': longitude,
            'heading': 0,
            'speed': 0,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return None
```

## Solución de Problemas

### Error: Puerto en uso
```bash
# Cambiar puerto en config.py
SERVER_CONFIG = {'port': 9090}
```

### Error: No se decodifican mensajes
- Verificar formato del protocolo
- Revisar logs en `tq_server.log`
- Ajustar función de decodificación

### Cliente no se conecta
- Verificar que el servidor esté ejecutándose
- Comprobar firewall
- Verificar host y puerto

## Archivos Importantes

- `tq_server.py` - Servidor principal
- `tq_client_test.py` - Cliente de prueba
- `tq_server.log` - Archivo de logs
- `config.py` - Configuración del sistema
- `README.md` - Documentación completa

## Próximos Pasos

1. **Analizar el protocolo del PDF**
2. **Adaptar la decodificación**
3. **Probar con equipos reales**
4. **Configurar logging personalizado**
5. **Implementar validaciones adicionales**

---

**¡El servidor TQ está listo para usar!** 🎉

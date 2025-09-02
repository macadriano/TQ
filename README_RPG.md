# Servidor TQ + RPG

Este servidor extiende la funcionalidad del servidor TQ original agregando:

1. **Conversión automática al protocolo RPG** - Convierte los datos GPS recibidos al formato RPG estándar
2. **Reenvío UDP** - Envía automáticamente los mensajes RPG convertidos por UDP a la IP y puerto configurados
3. **Logging mejorado** - Mantiene registros separados de posiciones GPS y mensajes RPG

## Características

- ✅ **Servidor TCP** - Escucha conexiones en el puerto 5003
- ✅ **Decodificación TQ** - Decodifica mensajes del protocolo TQ original
- ✅ **Conversión RPG** - Convierte automáticamente a formato RPG
- ✅ **Reenvío UDP** - Envía mensajes RPG a `179.43.115.190:7007`
- ✅ **Logging dual** - Archivos separados para posiciones y mensajes RPG
- ✅ **Interfaz de comandos** - Comandos para monitorear el estado del servidor

## Archivos

- `tq_server_rpg.py` - Servidor principal con funcionalidad RPG
- `config_rpg.py` - Archivo de configuración
- `start_server_rpg.bat` - Script para iniciar el servidor en Windows
- `positions_log.csv` - Registro de posiciones GPS recibidas
- `rpg_messages.log` - Registro de mensajes RPG enviados
- `tq_server_rpg.log` - Log del servidor

## Instalación

1. Asegúrate de tener Python 3.6+ instalado
2. Copia todos los archivos al directorio de trabajo
3. Ejecuta el servidor:
   ```bash
   python tq_server_rpg.py
   ```
   
   O en Windows:
   ```cmd
   start_server_rpg.bat
   ```

## Configuración

Edita `config_rpg.py` para modificar:

- **Puerto TCP**: Puerto de escucha (por defecto: 5003)
- **IP UDP**: IP de destino para reenvío (por defecto: 179.43.115.190)
- **Puerto UDP**: Puerto de destino para reenvío (por defecto: 7007)
- **Archivos de log**: Nombres de archivos de registro

## Uso

### Comandos disponibles

- `status` - Muestra el estado del servidor
- `clients` - Lista clientes conectados
- `positions` - Muestra últimas posiciones guardadas
- `rpg` - Muestra últimas entradas del log RPG
- `quit` - Sale del servidor

### Flujo de trabajo

1. **Recepción**: El servidor recibe mensajes GPS en protocolo TQ
2. **Decodificación**: Decodifica las coordenadas, velocidad y rumbo
3. **Conversión**: Convierte los datos al formato RPG estándar
4. **Reenvío**: Envía el mensaje RPG por UDP al destino configurado
5. **Logging**: Registra tanto la posición original como el mensaje RPG enviado

## Formato RPG

Los mensajes RPG siguen el formato:
```
$RPG,ID,LAT,LON,HEADING,SPEED,TIMESTAMP,STATUS*CHECKSUM
```

Ejemplo:
```
$RPG,12345,-34.123456,-58.456789,180.0,45.5,20231201143022,A*3A
```

Donde:
- `ID`: Identificador del dispositivo GPS
- `LAT`: Latitud en grados decimales
- `LON`: Longitud en grados decimales
- `HEADING`: Rumbo en grados (0-360)
- `SPEED`: Velocidad en km/h
- `TIMESTAMP`: Fecha y hora en formato YYYYMMDDHHMMSS
- `STATUS`: Estado del dispositivo (A=Activo, V=Inactivo)
- `CHECKSUM`: Checksum calculado con XOR

## Monitoreo

### Archivo de posiciones (`positions_log.csv`)
Contiene todas las posiciones GPS recibidas con formato:
```
ID,LATITUD,LONGITUD,RUMBO,VELOCIDAD,FECHAGPS,FECHARECIBIDO
```

### Archivo de log RPG (`rpg_messages.log`)
Contiene todos los mensajes RPG enviados con formato:
```
TIMESTAMP | MENSAJE_ORIGINAL | MENSAJE_RPG | ESTADO_ENVIO
```

## Diferencias con el servidor original

| Característica | Servidor TQ Original | Servidor TQ + RPG |
|----------------|----------------------|-------------------|
| Decodificación TQ | ✅ | ✅ |
| Guardado de posiciones | ✅ | ✅ |
| Conversión RPG | ❌ | ✅ |
| Reenvío UDP | ❌ | ✅ |
| Log RPG | ❌ | ✅ |
| Comando `rpg` | ❌ | ✅ |

## Solución de problemas

### Error de conexión UDP
- Verifica que la IP y puerto UDP sean correctos
- Asegúrate de que el firewall permita tráfico UDP saliente

### Mensajes no convertidos
- Revisa el log del servidor para errores de decodificación
- Verifica que los mensajes TQ tengan el formato esperado

### Archivos de log no creados
- Verifica permisos de escritura en el directorio
- Asegúrate de que Python tenga acceso al directorio de trabajo

## Soporte

Para reportar problemas o solicitar mejoras, revisa:
1. Los logs del servidor (`tq_server_rpg.log`)
2. El archivo de posiciones (`positions_log.csv`)
3. El archivo de log RPG (`rpg_messages.log`)

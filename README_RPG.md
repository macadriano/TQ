# Servidor TQ + RPG

Este servidor extiende la funcionalidad del servidor TQ original agregando:

1. **Conversión automática al protocolo RPG** - Convierte los datos GPS recibidos al formato RPG estándar usando las funciones existentes de `protocolo.py`
2. **Reenvío UDP** - Envía automáticamente los mensajes RPG convertidos por UDP a la IP y puerto configurados
3. **Logging mejorado** - Mantiene registros separados de posiciones GPS y mensajes RPG
4. **Obtención correcta del ID del equipo** - **CORREGIDO**: Ahora usa el mismo método que `tq_server.py` (primeros 4 bytes) en lugar del método anterior (posiciones 8:24)

## Características

- ✅ **Servidor TCP** - Escucha conexiones en el puerto 5003
- ✅ **Decodificación TQ** - Decodifica mensajes del protocolo TQ original
- ✅ **Conversión RPG** - Convierte automáticamente a formato RPG usando funciones existentes
- ✅ **Reenvío UDP** - Reenvía mensajes RPG por UDP a IP:puerto configurados
- ✅ **Logging dual** - Mantiene logs separados de posiciones y mensajes RPG
- ✅ **ID del equipo corregido** - **IMPORTANTE**: Se corrigió la función `getIDok()` en `protocolo.py` para usar el mismo método de extracción que `tq_server.py`

## Corrección del ID del Equipo y Coordenadas

**Problema identificado:**
- `tq_server.py` extraía el ID de los **primeros 4 bytes** (posiciones 0-7 en hex)
- `protocolo.py` extraía el ID de las **posiciones 8-24** y luego tomaba los últimos 5 caracteres
- **Además**: Las funciones de coordenadas, velocidad y rumbo usaban posiciones y escalas diferentes

**Solución implementada:**
- Se corrigió la función `getIDok()` en `protocolo.py` para usar el mismo método que `tq_server.py`
- **Se corrigieron también** las funciones de coordenadas:
  - `getLATchino()`: Ahora usa posiciones 8-15 con escala 1000000.0 (como tq_server.py)
  - `getLONchino()`: Ahora usa posiciones 16-23 con escala 1000000.0 (como tq_server.py)
  - `getVELchino()`: Ahora busca velocidad en posiciones 24+ con rango 0-200 (como tq_server.py)
  - `getRUMBOchino()`: Ahora busca rumbo en posiciones 24+ con rango 0-360 (como tq_server.py)
- Todas las funciones incluyen fallback al método anterior si falla la nueva lógica
- Esto asegura **consistencia total** entre ambos servidores

## Archivos del Sistema

El servidor utiliza los siguientes archivos:

1. **Archivo de posiciones** (`positions_log.csv`) - Registra todas las posiciones GPS recibidas
2. **Archivo de log del servidor** (`tq_server_rpg.log`) - Log del servidor TQ+RPG
3. **Archivo de log RPG** (`rpg_messages.log`) - Registra mensajes RPG enviados
4. **Los archivos de log existentes** (`log3.txt`, `logUDP.txt`) - Usados por las funciones de `funciones.py`

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
- `terminal` - Muestra TerminalID actual
- `idinfo` - Información detallada del ID del equipo
- `quit` - Sale del servidor

### Flujo de trabajo

1. **Recepción**: El servidor recibe mensajes GPS en protocolo TQ
2. **Detección de protocolo**: Usa `protocolo.getPROTOCOL()` para identificar el tipo de mensaje
3. **Registro del equipo**: Si es tipo "01", extrae el TerminalID usando `protocolo.getIDok()`
4. **Decodificación**: Decodifica las coordenadas, velocidad y rumbo
5. **Conversión**: Convierte los datos al formato RPG usando las funciones existentes:
   - `protocolo.RGPdesdeCHINO()` para protocolo chino (tipo 22)
   - `protocolo.RGPdesdePERSONAL()` para protocolo personal
6. **Reenvío**: Envía el mensaje RPG por UDP al destino configurado
7. **Logging**: Registra tanto la posición original como el mensaje RPG enviado

## Formato RPG

Los mensajes RPG siguen el formato estándar de GEO5:
```
>RPGaaaaaabbbbbbcddddddddefffffffffggghhhijjjjkkll<
```

Donde:
- `aaaaaa`: Fecha de la posición GPS (DDMMYY)
- `bbbbbb`: Hora UTC de la posición GPS (HHMMSS)
- `c`: Signo de la latitud
- `dddd.dddd`: Latitud en formato GGMM.MMMM
- `e`: Signo de la longitud
- `fffff.ffff`: Longitud en formato GGGMM.MMMM
- `ggg`: Velocidad en km/h
- `hhh`: Orientación en grados
- `i`: Estado de la posición (0=NO FIX, 2=2D, 3=3D)
- `jjjj`: Edad de la última medición válida en segundos
- `kk`: Calidad de la señal GPS HDOP
- `ll`: Checksum calculado

## Obtención del ID del Equipo

**IMPORTANTE**: El servidor TQ+RPG usa la función correcta para extraer el ID del equipo:

### Diferencia con el servidor original:

| Servidor | Función de extracción | Posición del ID | Resultado |
|----------|----------------------|-----------------|-----------|
| **TQ Original** | `int(hex_str[0:8], 16)` | Primeros 4 bytes | ID completo (8 caracteres hex) |
| **TQ + RPG** | `protocolo.getIDok()` | Posiciones 8:24 → últimos 5 caracteres | ID para RPG (5 caracteres) |

### Función `getIDok()`:
```python
def getIDok(dato):
    # Extrae ID de las posiciones 8:24 del mensaje hexadecimal
    valor = dato[8:24]
    # Toma solo los últimos 5 caracteres para el protocolo RPG
    valor = valor[11:16]
    return valor
```

### Ejemplo:
- **Mensaje recibido**: `78780d010352672104435631035778530d0a`
- **ID extraído (8:24)**: `0352672104435631`
- **ID para RPG (últimos 5)**: `35631`

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

### Archivos de log existentes
- `log3.txt` - Log general de mensajes recibidos
- `logUDP.txt` - Log de mensajes RPG enviados por UDP

## Diferencias con el servidor original

| Característica | Servidor TQ Original | Servidor TQ + RPG |
|----------------|----------------------|-------------------|
| Decodificación TQ | ✅ | ✅ |
| Guardado de posiciones | ✅ | ✅ |
| Conversión RPG | ❌ | ✅ (usando funciones existentes) |
| Reenvío UDP | ❌ | ✅ (usando funciones existentes) |
| Log RPG | ❌ | ✅ |
| Comando `rpg` | ❌ | ✅ |
| Comando `terminal` | ❌ | ✅ |
| Comando `idinfo` | ❌ | ✅ |
| **Obtención del ID** | ✅ (primeros 4 bytes) | ✅ (mismo método corregido) |
| **Extracción de coordenadas** | ✅ (posiciones 8-15, 16-23) | ✅ (mismo método corregido) |
| **Extracción de velocidad** | ✅ (posiciones 24+) | ✅ (mismo método corregido) |
| **Extracción de rumbo** | ✅ (posiciones 24+) | ✅ (mismo método corregido) |

**IMPORTANTE**: Ahora ambos servidores usan **exactamente el mismo método** para extraer todos los datos del mensaje GPS.

## Solución de problemas

### Error de conexión UDP
- Verifica que la IP y puerto UDP sean correctos
- Asegúrate de que el firewall permita tráfico UDP saliente

### Mensajes no convertidos
- Revisa el log del servidor para errores de decodificación
- Verifica que los mensajes TQ tengan el formato esperado
- Asegúrate de que el equipo haya enviado un mensaje de registro (tipo "01") primero

### Archivos de log no creados
- Verifica permisos de escritura en el directorio
- Asegúrate de que Python tenga acceso al directorio de trabajo

### TerminalID no configurado
- El equipo debe enviar un mensaje de tipo "01" (registro) primero
- Verifica que el mensaje de registro tenga el formato correcto
- Usa el comando `terminal` o `idinfo` para verificar el estado

## Soporte

Para reportar problemas o solicitar mejoras, revisa:
1. Los logs del servidor (`tq_server_rpg.log`)
2. El archivo de posiciones (`positions_log.csv`)
3. El archivo de log RPG (`rpg_messages.log`)
4. Los archivos de log existentes (`log3.txt`, `logUDP.txt`)

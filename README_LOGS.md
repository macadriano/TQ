# Sistema de Logs Simplificado - Proyecto TQ

## Descripción

El proyecto TQ utiliza un sistema de logs simplificado con **un solo archivo diario** que contiene todos los registros del sistema. Los logs se organizan en una carpeta `logs/` con formato `LOG_DDMMYY.txt`.

## Estructura de Archivos

```
c:\proyectosGIT\TQ\
├── logs/
│   ├── LOG_241125.txt              # Log único del día 24/11/2025
│   ├── LOG_251125.txt              # Log único del día 25/11/2025
│   └── ...
├── funciones.py
├── tq_server_rpg.py
└── README_LOGS.md                  # Este archivo
```

## Formato de Nombres

Los archivos de log utilizan el formato `DDMMYY` para la fecha:

- **Formato**: `LOG_DDMMYY.txt`
- **Ejemplo**: Para el 24 de noviembre de 2025 → `LOG_241125.txt`

## Un Solo Archivo para Todo

A diferencia de sistemas complejos con múltiples archivos, este sistema usa **un solo archivo diario** que contiene:

- ✅ Logs del servidor
- ✅ Mensajes UDP
- ✅ Mensajes RPG
- ✅ Mensajes NMEA
- ✅ Logs personales
- ✅ Cualquier otro evento del sistema

Los diferentes tipos de mensajes se identifican mediante **tags** en el log:

```
24/11/2025 19:22:21: Servidor TQ+RPG iniciado en 0.0.0.0:5003
24/11/2025 19:22:25 [UDP]: Mensaje UDP enviado a 179.43.115.190:7007
24/11/2025 19:22:26 [PERSONAL]: Mensaje del protocolo personal
24/11/2025 19:22:27 [NMEA]: Mensaje NMEA0183 detectado
24/11/2025 19:22:30: Nueva conexión desde 192.168.1.100:54321
```

## Funciones de Logging

### En `funciones.py`

#### `get_daily_log_filename()`
Genera el nombre del archivo de log diario único.

```python
# Ejemplo de uso
log_file = get_daily_log_filename()
# Retorna: "logs/LOG_241125.txt"
```

#### `guardarLog(cadena)`
Guarda un mensaje en el log diario sin tag.

```python
# Ejemplo de uso
guardarLog("Servidor iniciado")
# Guarda: 24/11/2025 19:22:21: Servidor iniciado
```

#### `guardarLogUDP(cadena)`
Guarda un mensaje UDP con tag `[UDP]`.

```python
# Ejemplo de uso
guardarLogUDP("Mensaje UDP enviado")
# Guarda: 24/11/2025 19:22:21 [UDP]: Mensaje UDP enviado
```

#### `guardarLogPersonal(cadena)`
Guarda un mensaje personal con tag `[PERSONAL]`.

```python
# Ejemplo de uso
guardarLogPersonal("Mensaje personal")
# Guarda: 24/11/2025 19:22:21 [PERSONAL]: Mensaje personal
```

#### `guardarLogNMEA(cadena)`
Guarda un mensaje NMEA con tag `[NMEA]`.

```python
# Ejemplo de uso
guardarLogNMEA("*HQ,2076668133,V1,...")
# Guarda: 24/11/2025 19:22:21 [NMEA]: *HQ,2076668133,V1,...
```

#### `guardarLogArchivo(cadena, tag="")`
Guarda un mensaje con un tag personalizado opcional.

```python
# Ejemplo de uso
guardarLogArchivo("Evento importante", "ALERTA")
# Guarda: 24/11/2025 19:22:21 [ALERTA]: Evento importante

# Sin tag
guardarLogArchivo("Evento normal")
# Guarda: 24/11/2025 19:22:21: Evento normal
```

### En `tq_server_rpg.py`

El servidor utiliza automáticamente el mismo archivo de log diario:

- Todos los eventos del servidor se registran en `logs/LOG_DDMMYY.txt`
- El logger de Python escribe directamente en este archivo
- No hay archivos separados para posiciones o mensajes RPG

## Rotación Automática

Los archivos de log se rotan automáticamente cada día:

- Cada día se crea un nuevo archivo `LOG_DDMMYY.txt`
- Los archivos de días anteriores se mantienen en la carpeta `logs/`
- No hay límite automático de retención (se deben eliminar manualmente)

## Mantenimiento

### Ver logs del día actual

```bash
# Encontrar el log más reciente
ls -t logs/LOG_*.txt | head -1

# Ver en tiempo real
tail -f logs/LOG_$(date +%d%m%y).txt

# Ver últimas 50 líneas
tail -50 logs/LOG_$(date +%d%m%y).txt
```

### Buscar en logs

```bash
# Buscar mensajes UDP
grep "\[UDP\]" logs/LOG_241125.txt

# Buscar errores
grep -i "error" logs/LOG_241125.txt

# Buscar por hora
grep "19:22:" logs/LOG_241125.txt

# Buscar en todos los logs
grep "error" logs/LOG_*.txt
```

### Limpiar logs antiguos

```bash
# Eliminar logs de más de 30 días (Linux/Mac)
find logs/ -name "LOG_*.txt" -mtime +30 -delete

# Eliminar logs de más de 30 días (Windows PowerShell)
Get-ChildItem logs -Filter "LOG_*.txt" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item
```

### Comprimir logs antiguos

```bash
# Comprimir logs del mes anterior (Linux/Mac)
tar -czf logs_$(date -d "last month" +%Y%m).tar.gz logs/LOG_*$(date -d "last month" +%m%y).txt

# Comprimir logs del mes anterior (Windows PowerShell)
$lastMonth = (Get-Date).AddMonths(-1).ToString("MMyy")
Compress-Archive -Path "logs\LOG_*$lastMonth.txt" -DestinationPath "logs_$lastMonth.zip"
```

## Formato de Contenido

Cada línea del log incluye timestamp completo y opcionalmente un tag:

```
DD/MM/YYYY HH:MM:SS [TAG]: Mensaje
```

**Ejemplos**:

```
24/11/2025 19:22:21: Servidor TQ+RPG iniciado en 0.0.0.0:5003
24/11/2025 19:22:25 [UDP]: >RGP241125192225-3416.9932-05855.0598...
24/11/2025 19:22:26 [PERSONAL]: Mensaje del protocolo personal
24/11/2025 19:22:27 [NMEA]: *HQ,2076668133,V1,192225,A,3438.4010,S,05833.6031,W,0,0,241125,FFFFFBFF#
24/11/2025 19:22:30: Nueva conexión desde 192.168.1.100:54321
24/11/2025 19:22:35: Posición GPS: ID=68133, Lat=-34.640167, Lon=-58.560052
```

## Verificar Estado del Servidor

El script `server_status_rpg.sh` muestra automáticamente el log más reciente:

```bash
./server_status_rpg.sh
```

Salida:

```
=====================================
  ESTADO DEL SERVIDOR TQ+RPG
=====================================

--- ARCHIVOS DE LOG ---
[OK] Directorio de logs: logs
Total de archivos de log: 5

Ultimos archivos de log:
   logs/LOG_241125.txt (15K)
   logs/LOG_231125.txt (12K)
   logs/LOG_221125.txt (10K)

[OK] Log actual: LOG_241125.txt
   Tamaño: 15K
   Lineas: 342

Ultimas 10 lineas del log:
---
   24/11/2025 19:22:21: Servidor TQ+RPG iniciado
   24/11/2025 19:22:25 [UDP]: Mensaje enviado
   ...
---
```

## Beneficios del Sistema Simplificado

1. **Simplicidad**: Un solo archivo por día, fácil de encontrar y analizar
2. **Organización**: Todo en un lugar, no hay que buscar en múltiples archivos
3. **Rotación automática**: Un archivo nuevo cada día
4. **Tags claros**: Fácil identificar el tipo de mensaje con grep
5. **Mantenimiento simple**: Fácil eliminar o comprimir logs antiguos
6. **Compatibilidad**: Funciona igual en Linux y Windows

## Ejemplos de Uso

### Monitorear en tiempo real

```bash
# Seguir el log en tiempo real
tail -f logs/LOG_$(date +%d%m%y).txt

# Filtrar solo mensajes UDP
tail -f logs/LOG_$(date +%d%m%y).txt | grep "\[UDP\]"

# Filtrar errores
tail -f logs/LOG_$(date +%d%m%y).txt | grep -i "error"
```

### Analizar logs de un día específico

```bash
# Ver todo el log del 24 de noviembre
cat logs/LOG_241125.txt

# Contar mensajes UDP del día
grep -c "\[UDP\]" logs/LOG_241125.txt

# Ver solo mensajes entre las 19:00 y 20:00
grep "19:" logs/LOG_241125.txt
```

### Estadísticas

```bash
# Contar líneas totales
wc -l logs/LOG_241125.txt

# Contar mensajes por tipo
echo "Total: $(wc -l < logs/LOG_241125.txt)"
echo "UDP: $(grep -c '\[UDP\]' logs/LOG_241125.txt)"
echo "NMEA: $(grep -c '\[NMEA\]' logs/LOG_241125.txt)"
echo "PERSONAL: $(grep -c '\[PERSONAL\]' logs/LOG_241125.txt)"
```

## Notas Importantes

- La carpeta `logs/` se crea automáticamente al iniciar el servidor
- Los archivos se abren en modo append (`a`), por lo que no se sobrescriben
- Todos los logs usan encoding UTF-8
- El timestamp usa el formato: `DD/MM/YYYY HH:MM:SS`
- La fecha del archivo usa el formato: `DDMMYY`
- Los tags están entre corchetes: `[TAG]`

## Soporte

Para más información sobre el proyecto TQ, consulta la documentación principal o contacta al equipo de desarrollo.

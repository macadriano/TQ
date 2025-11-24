# Sistema de Logs Diarios - Proyecto TQ

## Descripción

El proyecto TQ utiliza un sistema de logs diarios que organiza todos los archivos de registro en una carpeta `logs/` con archivos separados por día usando el formato `DDMMYY`.

## Estructura de Archivos

```
c:\proyectosGIT\TQ\
├── logs/
│   ├── LOG_DDMMYY.txt              # Log general del sistema
│   ├── LOG_UDP_DDMMYY.txt          # Mensajes UDP enviados
│   ├── LOG_PERSONAL_DDMMYY.txt     # Log personal (protocolo personal)
│   ├── LOG_SERVER_DDMMYY.log       # Log del servidor TQ+RPG
│   ├── LOG_POSITIONS_DDMMYY.csv    # Posiciones GPS recibidas
│   └── LOG_RPG_DDMMYY.log          # Mensajes RPG generados
├── funciones.py
├── tq_server_rpg.py
└── README_LOGS.md                  # Este archivo
```

## Formato de Nombres

Los archivos de log utilizan el formato `DDMMYY` para la fecha:

- **Formato**: `DDMMYY` (día, mes, año de 2 dígitos)
- **Ejemplo**: Para el 24 de noviembre de 2025 → `241125`
- **Archivos**:
  - `LOG_241125.txt`
  - `LOG_SERVER_241125.log`
  - `LOG_POSITIONS_241125.csv`
  - etc.

## Funciones de Logging

### En `funciones.py`

#### `get_daily_log_filename(base_name)`
Genera el nombre de archivo de log diario con formato `logs/BASE_NAME_DDMMYY.txt`

```python
# Ejemplo de uso
log_file = get_daily_log_filename("LOG")
# Retorna: "logs/LOG_241125.txt"
```

#### `guardarLog(cadena)`
Guarda un mensaje en el log general del día.

```python
# Ejemplo de uso
guardarLog("Mensaje de prueba")
# Guarda en: logs/LOG_241125.txt
# Formato: 24/11/2025 19:22:21: Mensaje de prueba
```

#### `guardarLogUDP(cadena)`
Guarda un mensaje en el log de UDP del día.

```python
# Ejemplo de uso
guardarLogUDP("Mensaje UDP enviado")
# Guarda en: logs/LOG_UDP_241125.txt
```

#### `guardarLogPersonal(cadena)`
Guarda un mensaje en el log personal del día.

```python
# Ejemplo de uso
guardarLogPersonal("Mensaje personal")
# Guarda en: logs/LOG_PERSONAL_241125.txt
```

#### `guardarLogArchivo(cadena, base_name)`
Guarda un mensaje en un archivo de log personalizado.

```python
# Ejemplo de uso
guardarLogArchivo("Mensaje custom", "MI_LOG")
# Guarda en: logs/MI_LOG_241125.txt
```

### En `tq_server_rpg.py`

El servidor utiliza tres archivos de log principales:

1. **Log del servidor**: `logs/LOG_SERVER_DDMMYY.log`
   - Eventos del servidor (inicio, conexiones, errores)
   - Configurado automáticamente en `setup_logging()`

2. **Log de posiciones**: `logs/LOG_POSITIONS_DDMMYY.csv`
   - Posiciones GPS recibidas en formato CSV
   - Columnas: ID, LATITUD, LONGITUD, RUMBO, VELOCIDAD_KMH, VELOCIDAD_NUDOS, FECHAGPS, HORAGPS, FECHARECIBIDO

3. **Log de mensajes RPG**: `logs/LOG_RPG_DDMMYY.log`
   - Mensajes RPG generados y enviados
   - Formato: TIMESTAMP | MENSAJE_ORIGINAL | MENSAJE_RPG | ESTADO_ENVIO

## Rotación Automática

Los archivos de log se rotan automáticamente cada día:

- Cada día se crea un nuevo conjunto de archivos con la fecha del día
- Los archivos de días anteriores se mantienen en la carpeta `logs/`
- No hay límite automático de retención (se deben eliminar manualmente)

## Mantenimiento

### Ver logs del día actual

```bash
# Ver log del servidor
tail -f logs/LOG_SERVER_*.log

# Ver posiciones GPS
tail -f logs/LOG_POSITIONS_*.csv

# Ver mensajes RPG
tail -f logs/LOG_RPG_*.log
```

### Limpiar logs antiguos

```bash
# Eliminar logs de más de 30 días (Linux/Mac)
find logs/ -name "*.log" -mtime +30 -delete
find logs/ -name "*.txt" -mtime +30 -delete
find logs/ -name "*.csv" -mtime +30 -delete

# Eliminar logs de más de 30 días (Windows PowerShell)
Get-ChildItem logs -Recurse | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item
```

### Comprimir logs antiguos

```bash
# Comprimir logs del mes anterior (Linux/Mac)
tar -czf logs_$(date -d "last month" +%Y%m).tar.gz logs/*_$(date -d "last month" +%d%m%y).* 

# Comprimir logs del mes anterior (Windows PowerShell)
$lastMonth = (Get-Date).AddMonths(-1).ToString("MMyy")
Compress-Archive -Path "logs\*_*$lastMonth.*" -DestinationPath "logs_$lastMonth.zip"
```

## Formato de Contenido

### Logs de texto (.txt, .log)

Cada línea incluye timestamp completo:

```
24/11/2025 19:22:21: Mensaje de ejemplo
24/11/2025 19:22:22: Otro mensaje
```

### Log de posiciones (.csv)

Formato CSV con cabecera:

```csv
ID,LATITUD,LONGITUD,RUMBO,VELOCIDAD_KMH,VELOCIDAD_NUDOS,FECHAGPS,HORAGPS,FECHARECIBIDO
68133,-34.283350,-58.550850,180.0,45.0,24.3,24/11/25,16:22:21,2025-11-24 19:22:21
```

### Log de mensajes RPG (.log)

Formato con separadores:

```
2025-11-24 19:22:21 | 787822... | >RGP241125162221... | ENVIADO
```

## Beneficios del Sistema

1. **Organización**: Todos los logs en una carpeta dedicada
2. **Rotación automática**: Un archivo nuevo por día
3. **Fácil identificación**: El nombre del archivo indica la fecha
4. **Mantenimiento simple**: Fácil eliminar o comprimir logs antiguos
5. **Compatibilidad**: Mismo formato que otros proyectos (gpschino)
6. **Trazabilidad**: Fácil encontrar logs de una fecha específica

## Ejemplos de Uso

### Buscar eventos de un día específico

```bash
# Ver todos los logs del 24 de noviembre de 2025
cat logs/*_241125.*

# Buscar un error específico
grep "ERROR" logs/LOG_SERVER_241125.log

# Contar posiciones GPS del día
wc -l logs/LOG_POSITIONS_241125.csv
```

### Analizar posiciones GPS

```bash
# Ver últimas 10 posiciones
tail -10 logs/LOG_POSITIONS_241125.csv

# Filtrar por ID de equipo
grep "68133" logs/LOG_POSITIONS_241125.csv
```

### Monitorear en tiempo real

```bash
# Seguir el log del servidor en tiempo real
tail -f logs/LOG_SERVER_$(date +%d%m%y).log

# Seguir múltiples logs simultáneamente
tail -f logs/LOG_SERVER_*.log logs/LOG_RPG_*.log
```

## Notas Importantes

- La carpeta `logs/` se crea automáticamente al iniciar el servidor o al usar cualquier función de logging
- Los archivos se abren en modo append (`a`), por lo que no se sobrescriben
- Todos los logs usan encoding UTF-8
- El timestamp usa el formato: `DD/MM/YYYY HH:MM:SS`
- La fecha del archivo usa el formato: `DDMMYY`

## Migración desde Sistema Anterior

Si tienes logs del sistema anterior (archivos en la raíz del proyecto):

```bash
# Crear carpeta logs si no existe
mkdir -p logs

# Mover logs antiguos (opcional)
mv log3.txt logs/LOG_old.txt
mv logUDP.txt logs/LOG_UDP_old.txt
mv logPersonal.txt logs/LOG_PERSONAL_old.txt
mv tq_server_rpg.log logs/LOG_SERVER_old.log
mv positions_log.csv logs/LOG_POSITIONS_old.csv
mv rpg_messages.log logs/LOG_RPG_old.log
```

## Soporte

Para más información sobre el proyecto TQ, consulta la documentación principal o contacta al equipo de desarrollo.

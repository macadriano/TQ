# Sistema de Logging Optimizado - TQ Server RPG

## Descripción General

Este sistema optimiza el logging de paquetes RPG para reducir el espacio en disco, eliminando información redundante y consolidando datos GPS en formato compacto.

## Características Principales

### 1. **Logging Optimizado de Paquetes RPG**
- ✅ Elimina texto redundante como "Coordenadas hexadecimales extraídas..."
- ✅ Consolida datos GPS en una sola línea: `ID, LAT, LON, RUMBO, VELOCIDAD`
- ✅ Simplifica líneas de timestamp GPS
- ✅ Una línea por destino de envío (TCP/UDP) con IP, Puerto y Dato

### 2. **Limpieza Automática de Logs Antiguos**
- ✅ Elimina automáticamente logs con más de 15 días de antigüedad
- ✅ Se ejecuta al iniciar el servidor
- ✅ Reporta archivos eliminados y espacio liberado
- ✅ Mantiene logs de `LOG_*.txt` y `RPG_*.txt`

## Archivos del Sistema

### Archivos de Log Generados

```
logs/
├── LOG_DDMMYY.txt    # Log general diario (todos los eventos)
└── RPG_DDMMYY.txt    # Log optimizado de paquetes RPG
```

### Módulos Python

- **`log_optimizer.py`**: Clase principal para logging optimizado de RPG
- **`funciones.py`**: Funciones de utilidad incluyendo `cleanup_old_logs()`
- **`cleanup_logs.py`**: Script independiente para limpieza manual

### Scripts Shell

- **`cleanup_logs.sh`**: Wrapper bash para ejecutar limpieza fácilmente

## Formato de Log Optimizado

### Antes (Verbose):
```
2025-12-03 10:11:45 - INFO - Tipo de protocolo detectado: 59
2025-12-03 10:11:45 - INFO - Intentando decodificación TQ
2025-12-03 10:11:45 - INFO - Coordenadas hexadecimales extraídas: Lat=-40.772199°, Lon=-71.607830°
2025-12-03 10:11:45 - INFO - Velocidad y rumbo extraídos: 0.0 km/h, Rumbo: 119°
2025-12-03 10:11:45 - INFO - Posición decodificada: {...}
2025-12-03 10:11:45 - INFO - Usando fecha/hora GPS original: 03/12/25 12:02:50 UTC (sin offset)
2025-12-03 10:11:45 - INFO - Mensaje RPG creado desde GPS: >RGP031225120250...
2025-12-03 10:11:45 - INFO - Datos reenviados por TCP a 200.58.98.187:5003
2025-12-03 10:11:45 - INFO - Mensaje enviado por UDP a 179.43.115.190:7007
```

### Después (Optimizado):
```
2025-12-03 10:11:45 - Protocolo: 59
GPS: ID=95999, LAT=-40.772199, LON=-71.607830, RUMBO=119, VEL=0 km/h
Timestamp GPS: 03/12/25 12:02:50 UTC
Envío UDP: 179.43.115.190:7007 - >RGP031225120250-4046.3319-07136.4698000119000001;&01;ID=95999;#0001*62<
Envío TCP: 200.58.98.187:5003 - 24959917442103122534046331907136469800000000df54
--------------------------------------------------------------------------------
```

**Reducción de espacio: ~70%**

## Uso

### Limpieza Automática

La limpieza se ejecuta automáticamente al iniciar el servidor:

```bash
./server_start_rpg.sh
```

Salida esperada:
```
🧹 Limpiando logs antiguos...
🗑️  Log eliminado: LOG_151125.txt (245.32 KB, 2025-11-15)
🗑️  Log eliminado: RPG_151125.txt (89.15 KB, 2025-11-15)
✅ Limpieza completada: 2 archivo(s) eliminado(s), 0.33 MB liberados
```

### Limpieza Manual

#### Opción 1: Script Shell (Recomendado)
```bash
# Mantener 15 días (por defecto)
./cleanup_logs.sh

# Mantener 30 días
./cleanup_logs.sh 30

# Mantener 7 días
./cleanup_logs.sh 7
```

#### Opción 2: Script Python Directo
```bash
# Mantener 15 días (por defecto)
python3 cleanup_logs.py

# Mantener 30 días
python3 cleanup_logs.py 30
```

#### Opción 3: Desde Python
```python
import funciones

# Limpiar logs manteniendo 15 días
stats = funciones.cleanup_old_logs(days_to_keep=15)

print(f"Archivos eliminados: {stats['deleted_count']}")
print(f"Espacio liberado: {stats['size_freed_mb']} MB")
```

## Configuración

### Cambiar Días de Retención por Defecto

**En `tq_server_rpg.py`** (línea ~950):
```python
cleanup_stats = funciones.cleanup_old_logs(days_to_keep=15)  # Cambiar 15 por el valor deseado
```

**En `cleanup_logs.py`** (línea ~22):
```python
days_to_keep = 15  # Cambiar por defecto
```

**En `cleanup_logs.sh`** (línea ~5):
```bash
DAYS=${1:-15}  # Cambiar 15 por el valor deseado
```

## API del Log Optimizer

### Clase `RPGLogOptimizer`

```python
from log_optimizer import get_rpg_logger

# Obtener instancia del logger
logger = get_rpg_logger()

# Log completo de intento RPG
logger.log_rpg_attempt(
    device_id="95999",
    protocol_type="59",
    latitude=-40.772199,
    longitude=-71.607830,
    heading=119,
    speed=0,
    fecha_gps="03/12/25",
    hora_gps="12:02:50",
    destinations=[
        ("UDP", "179.43.115.190", 7007, ">RGP..."),
        ("TCP", "200.58.98.187", 5003, "24959917...")
    ]
)

# Log ultra-compacto (una línea)
logger.log_rpg_compact(
    device_id="95999",
    lat=-40.772199,
    lon=-71.607830,
    heading=119,
    speed=0,
    protocol="59",
    gps_time="03/12/25 12:02:50",
    send_info="UDP:179.43.115.190:7007"
)

# Limpiar logs antiguos
stats = logger.cleanup_old_logs(days_to_keep=15)
```

## Estadísticas de Limpieza

La función `cleanup_old_logs()` retorna un diccionario con:

```python
{
    'deleted_count': 5,                    # Número de archivos eliminados
    'deleted_files': ['LOG_151125.txt', ...],  # Lista de archivos
    'size_freed_bytes': 1048576,          # Bytes liberados
    'size_freed_mb': 1.0,                 # MB liberados
    'cutoff_date': '2025-11-18',          # Fecha límite
    'days_kept': 15                       # Días mantenidos
}
```

## Automatización con Cron

Para ejecutar limpieza automática diariamente:

```bash
# Editar crontab
crontab -e

# Agregar línea (ejecutar todos los días a las 3 AM)
0 3 * * * cd /ruta/a/TQ && ./cleanup_logs.sh 15 >> logs/cleanup.log 2>&1
```

## Beneficios

1. **Ahorro de Espacio**: Reducción de ~70% en tamaño de logs RPG
2. **Mejor Legibilidad**: Información consolidada y fácil de leer
3. **Gestión Automática**: No requiere intervención manual
4. **Flexibilidad**: Configurable según necesidades
5. **Auditoría**: Mantiene información esencial para debugging

## Troubleshooting

### Los logs no se eliminan

1. Verificar permisos del directorio `logs/`:
   ```bash
   ls -la logs/
   chmod 755 logs/
   ```

2. Verificar que existan archivos antiguos:
   ```bash
   ls -la logs/LOG_*.txt logs/RPG_*.txt
   ```

3. Ejecutar limpieza manual con verbose:
   ```bash
   python3 cleanup_logs.py 15
   ```

### Error de importación

Asegurarse de que todos los archivos estén en el mismo directorio:
```bash
ls -1 *.py | grep -E "(funciones|log_optimizer|cleanup_logs)"
```

## Notas Importantes

- ⚠️ Los archivos eliminados **NO** se pueden recuperar
- ✅ Se recomienda hacer backup antes de cambiar configuración
- ✅ El servidor debe tener permisos de escritura en `logs/`
- ✅ La limpieza se basa en fecha de **modificación** del archivo

## Soporte

Para más información sobre el sistema de logging, consultar:
- `tq_server_rpg.py` - Implementación del servidor
- `log_optimizer.py` - Módulo de optimización
- `funciones.py` - Funciones de utilidad

# Servidor TQ+RPG - Sistema de Tracking GPS

Sistema de servidor TCP para recibir datos de dispositivos GPS con protocolo TQ y convertirlos al protocolo RPG para reenvío UDP.

## 📋 Descripción

Este proyecto implementa un servidor que:
- ✅ Recibe datos GPS de dispositivos con protocolo TQ por TCP (puerto 5003)
- ✅ Decodifica mensajes del protocolo TQ y NMEA0183
- ✅ Convierte los datos al protocolo RPG (GEO5)
- ✅ Reenvía los mensajes RPG por UDP a servidor remoto
- ✅ Registra todo en un sistema de logs diarios simplificado

## 🚀 Inicio Rápido

### Iniciar el Servidor

```bash
./start_server_rpg.sh
```

### Ver Estado del Servidor

```bash
./server_status_rpg.sh
```

### Detener el Servidor

```bash
./stop_server_rpg.sh
```

### Ver Logs en Tiempo Real

```bash
tail -f logs/LOG_$(date +%d%m%y).txt
```

## 📁 Estructura del Proyecto

```
TQ/
├── funciones.py              # Funciones auxiliares y logging
├── protocolo.py              # Decodificación de protocolos TQ y RPG
├── tq_server_rpg.py         # Servidor principal
├── start_server_rpg.sh      # Script para iniciar servidor
├── stop_server_rpg.sh       # Script para detener servidor
├── server_status_rpg.sh     # Script para ver estado
├── logs/                    # Carpeta de logs diarios
│   ├── LOG_241125.txt      # Log del 24/11/2025
│   └── LOG_251125.txt      # Log del 25/11/2025
├── README.md               # Este archivo
├── README_LOGS.md          # Documentación del sistema de logs
├── README_GITIGNORE.md     # Documentación de .gitignore
└── .gitignore              # Archivos ignorados por Git
```

## 🔧 Componentes Principales

### 1. `tq_server_rpg.py` - Servidor Principal

Servidor TCP que:
- Escucha en puerto 5003 (configurable)
- Acepta múltiples conexiones simultáneas
- Decodifica protocolos TQ y NMEA0183
- Convierte a protocolo RPG
- Reenvía por UDP a 179.43.115.190:7007

**Características**:
- ✅ Filtros de calidad GPS (evita saltos y posiciones inválidas)
- ✅ Geocodificación inversa opcional (OpenStreetMap)
- ✅ Logging unificado en archivo diario
- ✅ Soporte para modo daemon (background)

### 2. `funciones.py` - Funciones Auxiliares

Proporciona:
- Conversión entre bytes, hexadecimal y strings
- Sistema de logging simplificado con tags
- Envío de mensajes UDP
- Cálculos de checksums (CRC-ITU)
- Ajustes de zona horaria

**Funciones de Logging**:
- `guardarLog(mensaje)` - Log sin tag
- `guardarLogUDP(mensaje)` - Log con tag [UDP]
- `guardarLogPersonal(mensaje)` - Log con tag [PERSONAL]
- `guardarLogNMEA(mensaje)` - Log con tag [NMEA]

### 3. `protocolo.py` - Decodificación de Protocolos

Maneja:
- Protocolo TQ (dispositivos GPS chinos)
- Protocolo RPG/GEO5 (servidor destino)
- Extracción de coordenadas, velocidad, rumbo
- Conversión de formatos de fecha/hora
- Cálculo de checksums

## 📝 Sistema de Logs

### Archivo Único Diario

Todo se registra en un solo archivo por día: `logs/LOG_DDMMYY.txt`

**Formato**:
```
DD/MM/YYYY HH:MM:SS [TAG]: Mensaje
```

**Ejemplo**:
```
24/11/2025 20:06:24: Servidor TQ+RPG iniciado en 0.0.0.0:5003
24/11/2025 20:06:25 [UDP]: >RGP241125200625-3416.9932-05855.0598...
24/11/2025 20:06:26 [NMEA]: *HQ,2076668133,V1,200626,A,3438.4010,S...
24/11/2025 20:06:30: Nueva conexión desde 192.168.1.100:54321
```

### Tags Disponibles

- Sin tag: Eventos generales del servidor
- `[UDP]`: Mensajes UDP enviados
- `[PERSONAL]`: Protocolo personal
- `[NMEA]`: Mensajes NMEA0183
- `[CUSTOM]`: Tags personalizados

### Comandos Útiles

```bash
# Ver log en tiempo real
tail -f logs/LOG_$(date +%d%m%y).txt

# Buscar mensajes UDP
grep "\[UDP\]" logs/LOG_241125.txt

# Buscar errores
grep -i "error" logs/LOG_*.txt

# Contar mensajes por tipo
grep -c "\[UDP\]" logs/LOG_241125.txt
```

Ver [README_LOGS.md](README_LOGS.md) para más detalles.

## 🌐 Configuración de Red

### Puerto TCP (Entrada)
- **Puerto**: 5003
- **Protocolo**: TCP
- **Función**: Recibe datos de dispositivos GPS

### Puerto UDP (Salida)
- **Host**: 179.43.115.190
- **Puerto**: 7007
- **Protocolo**: UDP
- **Función**: Reenvía mensajes RPG al servidor destino

### Puerto TCP (Salida - Reenvío)
- **Host**: 200.58.98.187
- **Puerto**: 5003
- **Protocolo**: TCP
- **Función**: Reenvía datos crudos (raw bytes) tal cual se reciben


### Modificar Configuración

Editar en `tq_server_rpg.py`:

```python
server = TQServerRPG(
    host='0.0.0.0',              # IP local (0.0.0.0 = todas las interfaces)
    port=5003,                    # Puerto TCP de entrada
    udp_host='179.43.115.190',   # IP del servidor UDP destino
    udp_port=7007,                # Puerto UDP destino
    tcp_forward_host='200.58.98.187', # IP destino reenvío TCP
    tcp_forward_port=5003,        # Puerto destino reenvío TCP
    tcp_forward_enabled=True      # Habilitar/Deshabilitar reenvío TCP
)

```

## 🔍 Protocolos Soportados

### Protocolo TQ (Entrada)

Protocolo binario usado por dispositivos GPS chinos:
- Mensajes de registro (0x01)
- Mensajes de posición (0x22)
- Mensajes de heartbeat
- Otros tipos de mensajes

### Protocolo NMEA0183 (Entrada)

Formato de texto estándar GPS:
```
*HQ,2076668133,V1,200625,A,3438.4010,S,05833.6031,W,0,0,241125,FFFFFBFF#
```

### Protocolo RPG/GEO5 (Salida)

Formato para servidor destino:
```
>RGP241125200625-3416.9932-05855.0598045180000001;&01;ID=68133;#0001*62<
```

## 🛠️ Scripts de Control

### `start_server_rpg.sh`

Inicia el servidor en modo daemon (background):
- Verifica si ya está ejecutándose
- Inicia el servidor en segundo plano
- Guarda el PID en `/tmp/tq_server_rpg.pid`
- Muestra confirmación de inicio

### `stop_server_rpg.sh`

Detiene el servidor de forma segura:
- Lee el PID del archivo
- Envía señal SIGTERM para cierre ordenado
- Espera hasta 10 segundos para cierre graceful
- Fuerza cierre con SIGKILL si es necesario
- Limpia el archivo PID

### `server_status_rpg.sh`

Muestra estado completo del servidor:
- Estado del proceso (PID, CPU, memoria)
- Archivos de log disponibles
- Últimas 10 líneas del log actual
- Puertos de red (TCP 5003)
- Conexiones activas
- Estadísticas del sistema

## 📊 Monitoreo

### Ver Estado Completo

```bash
./server_status_rpg.sh
```

Salida:
```
=====================================
  ESTADO DEL SERVIDOR TQ+RPG
=====================================

--- PROCESO DEL SERVIDOR ---
Archivo PID: /tmp/tq_server_rpg.pid
PID registrado: 12345
   [OK] Estado: Ejecutandose
   PID: 12345
   Iniciado: Sun Nov 24 20:00:00 2025
   CPU: 0.5%
   Memoria: 1.2%

--- ARCHIVOS DE LOG ---
[OK] Directorio de logs: logs
Total de archivos de log: 3

[OK] Log actual: LOG_241125.txt
   Tamaño: 15K
   Lineas: 342

Ultimas 10 lineas del log:
---
   24/11/2025 20:06:24: Servidor iniciado
   ...
---

--- PUERTOS DE RED ---
[OK] Puerto TCP 5003: Escuchando
[OK] Conexiones TCP activas: 2
```

### Logs en Tiempo Real

```bash
# Seguir el log
tail -f logs/LOG_$(date +%d%m%y).txt

# Filtrar solo mensajes UDP
tail -f logs/LOG_$(date +%d%m%y).txt | grep "\[UDP\]"
```

## 🔒 Seguridad y Filtros

### Filtros de Calidad GPS

El servidor implementa filtros inteligentes para evitar posiciones inválidas:

1. **Coordenadas (0,0)**: Rechazadas automáticamente
2. **Saltos sospechosos**: >300m en <10s (desactivado por defecto)
3. **Saltos excesivos**: >1km en <5min (desactivado por defecto)
4. **Velocidad incoherente**: Diferencia >20 km/h (desactivado por defecto)
5. **Protección de detenciones**: Mantiene paradas legítimas

Los filtros se pueden activar/desactivar en `tq_server_rpg.py` método `is_position_valid()`.

### Geocodificación

Geocodificación inversa opcional usando OpenStreetMap Nominatim:
- Rate limiting: 1 consulta por segundo
- Cache de 100 direcciones
- Se puede habilitar/deshabilitar con `toggle_geocoding()`

## 🐛 Solución de Problemas

### El servidor no inicia

```bash
# Verificar si el puerto está en uso
netstat -tln | grep 5003

# Ver logs de error
tail -20 logs/LOG_$(date +%d%m%y).txt
```

### No se reciben datos

```bash
# Verificar conexiones activas
./server_status_rpg.sh

# Ver si el puerto está escuchando
netstat -tln | grep 5003

# Revisar firewall
sudo ufw status
```

### Logs no se crean

```bash
# Verificar permisos de la carpeta logs/
ls -la logs/

# Crear manualmente si es necesario
mkdir -p logs
chmod 755 logs
```

## 📚 Documentación Adicional

- [README_LOGS.md](README_LOGS.md) - Sistema de logs detallado
- [README_GITIGNORE.md](README_GITIGNORE.md) - Configuración de Git

## 🔄 Mantenimiento

### Limpiar Logs Antiguos

```bash
# Eliminar logs de más de 30 días
find logs/ -name "LOG_*.txt" -mtime +30 -delete
```

### Comprimir Logs

```bash
# Comprimir logs del mes anterior
tar -czf logs_$(date -d "last month" +%Y%m).tar.gz logs/LOG_*$(date -d "last month" +%m%y).txt
```

### Actualizar desde Git

```bash
# Detener servidor
./stop_server_rpg.sh

# Actualizar código
git pull origin main

# Reiniciar servidor
./start_server_rpg.sh
```

## 🤝 Contribuir

Para contribuir al proyecto:

1. Hacer fork del repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto es privado y de uso interno.

## 👥 Contacto

Para soporte o consultas, contactar al equipo de desarrollo.

---

**Última actualización**: 24/11/2025

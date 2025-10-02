# Servidor TQ Simplificado

## Descripción

Servidor TQ simplificado que **solo procesa mensajes del formato específico** encontrado en `RECORRIDO61674_011025.txt`. Descarta todos los demás tipos de mensajes.

## Características

- ✅ **Solo procesa mensajes del protocolo TQ**: Mensajes que empiecen con `24` (cualquier ID de equipo)
- ❌ **Descarta todos los demás mensajes** (NMEA, otros protocolos, etc.)
- 🔧 **Código limpio y simplificado**
- 📊 **Logs detallados** de posiciones procesadas
- 🎯 **Reenvío RPG** automático
- 📁 **Guardado en CSV** de posiciones

## Archivos Generados

### Servidor Principal
- `tq_server_simplificado.py` - Servidor principal
- `start_server_simplificado.bat` - Script de inicio
- `test_server_simplificado.py` - Script de prueba

### Archivos de Log
- `tq_server_simplificado.log` - Log del servidor
- `positions_log.csv` - Posiciones GPS guardadas
- `rpg_messages.log` - Mensajes RPG enviados

## Uso

### 1. Iniciar el Servidor

**Windows:**
```bash
start_server_simplificado.bat
```

**Linux/Unix:**
```bash
./start_server_simplificado.sh
```

**Directo:**
```bash
python tq_server_simplificado.py --host 0.0.0.0 --port 5003 --udp-host 179.43.115.190 --udp-port 7007
```

### 2. Verificar Estado
```bash
./server_status_simplificado.sh
```

### 3. Probar el Servidor
```bash
# Linux/Unix
python3 test_server_simplificado.py

# Windows
python test_server_simplificado.py
```

### 4. Detener el Servidor
```bash
./stop_server_simplificado.sh
```

## Parámetros del Servidor

- `--host`: Host del servidor (default: 0.0.0.0)
- `--port`: Puerto del servidor (default: 5003)
- `--udp-host`: Host UDP para reenvío RPG (default: 179.43.115.190)
- `--udp-port`: Puerto UDP para reenvío RPG (default: 7007)

## Formato de Mensajes Aceptados

### ✅ Mensajes Válidos
```
# Cualquier ID de equipo válido:
24207666167410521901102534381299060583274822016334fffffbff0006fdd300000000000000df54000000
24207666813310525201102534380885060583277462002315fffffbff0006fdd300000000000000df54000001
24207661234510525301102534380878060583277522003333fffffbff0006fdd300000000000000df54000002
```

**Características:**
- Debe empezar con `24` (protocolo TQ)
- Longitud entre 80-200 caracteres
- Solo caracteres hexadecimales válidos
- Cualquier ID de equipo válido

### ❌ Mensajes Rechazados
- Mensajes NMEA (`*HQ,123456,V1,...`)
- Mensajes que no empiecen con `24`
- Mensajes con longitud insuficiente o excesiva
- Mensajes con caracteres no hexadecimales
- Mensajes de texto o con comas

## Logs del Servidor

### Log de Posiciones
```
2025-10-01 07:52:22 - INFO - Posición procesada: ID=61674, Lat=-34.612990, Lon=-58.327482, Vel=16.3 km/h, Rumbo=163°
```

### Log de Mensajes RPG
```
2025-10-01 07:52:22 | 24207666167410521901102534381299060583274822016334... | *HQ,61674,V1,10:52:19,A,-34.612990S,-58.327482W,16.3,163,01/10/25,# | ENVIADO
```

## Archivo CSV de Posiciones

Formato: `positions_log.csv`
```csv
ID,LATITUD,LONGITUD,RUMBO,VELOCIDAD_KMH,VELOCIDAD_NUDOS,FECHAGPS,HORAGPS,FECHARECIBIDO
61674,-34.612990,-58.327482,163,16.3,8.8,01/10/25,10:52:19,2025-10-01 07:52:22
```

## Diferencias con el Servidor Original

| Característica | Servidor Original | Servidor Simplificado |
|---|---|---|
| **Mensajes NMEA** | ✅ Procesa | ❌ Descarta |
| **Mensajes Hex** | ✅ Procesa | ✅ Solo formato específico |
| **Validación** | Básica | Estricta por formato |
| **Código** | Complejo | Simplificado |
| **Logs** | Detallados | Optimizados |
| **Rendimiento** | Medio | Alto |

## Ventajas del Servidor Simplificado

1. **🎯 Específico**: Solo procesa el tipo de mensaje que necesitas
2. **🚀 Rápido**: Menos procesamiento, mayor rendimiento
3. **🧹 Limpio**: Código más fácil de mantener
4. **📊 Eficiente**: Logs optimizados
5. **🔒 Seguro**: Rechaza mensajes no deseados

## Solución de Problemas

### Error: "No se puede conectar al servidor"
- Verifica que el servidor esté ejecutándose
- Comprueba que el puerto 5003 esté disponible

### Error: "Mensaje con formato inválido descartado"
- Verifica que el mensaje empiece con `242076661674`
- Comprueba que solo contenga caracteres hexadecimales

### Error: "Error enviando mensaje RPG"
- Verifica la conectividad con el servidor UDP
- Comprueba que el host y puerto UDP sean correctos

## Monitoreo

Para monitorear el servidor en tiempo real:

```bash
# Ver logs en tiempo real
tail -f tq_server_simplificado.log

# Ver posiciones guardadas
tail -f positions_log.csv

# Ver mensajes RPG
tail -f rpg_messages.log
```

## Configuración Avanzada

### Cambiar Puerto del Servidor
```bash
python tq_server_simplificado.py --port 5004
```

### Cambiar Destino UDP
```bash
python tq_server_simplificado.py --udp-host 192.168.1.100 --udp-port 8000
```

### Ejecutar en Segundo Plano
```bash
nohup python tq_server_simplificado.py > server.log 2>&1 &
```

---

**🔧 Desarrollado para procesar exclusivamente mensajes del formato RECORRIDO61674_011025.txt**

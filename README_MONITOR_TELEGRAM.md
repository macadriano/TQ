# README_MONITOR.md

## Sistema de Monitorización para `tq_server_rpg.py`

Este documento describe en detalle cómo funciona el **sistema de keep‑alive** que hemos añadido al proyecto TQ. Incluye la arquitectura, configuración, scripts de gestión y pasos de troubleshooting.

---

### 1. Arquitectura General

```
+-------------------+      +-------------------+      +-------------------+
|  tq_server_rpg.py | ---> |  Health HTTP API  | ---> |  monitor_server.py |
+-------------------+      +-------------------+      +-------------------+
        (puerto 5003)            (puerto 5004)            (polling cada 10 min)
```

- **`tq_server_rpg.py`**: servidor principal que ahora expone un endpoint HTTP `/health` en el puerto **5004**.  El endpoint devuelve JSON con el estado del servidor (running, uptime, número de clientes, mensajes procesados, terminal ID, etc.).
- **`monitor_server.py`**: script independiente que consulta el endpoint `/health` a intervalos configurables.  Si detecta que el servidor está caído durante `FAILURE_THRESHOLD` intentos consecutivos, envía una alerta vía **Telegram** (y opcionalmente por **email**).
- **`monitor_config.py`**: archivo de configuración con placeholders para credenciales y parámetros de monitorización.
- **Scripts de gestión** (`start_monitor.sh`, `stop_monitor.sh`, `status_monitor.sh`) permiten lanzar, detener y consultar el estado del monitor como procesos de fondo.

---

### 2. Endpoint de Health Check (`tq_server_rpg.py`)

#### 2.1. Código añadido
```python
from http.server import HTTPServer, BaseHTTPRequestHandler
# ... dentro de la clase TQServerRPG
self.health_port = health_port  # nuevo parámetro en __init__ (default 5004)
self.start_time = None
self.health_server = None
```

#### 2.2. Métodos clave
- **`get_status(self) -> Dict`**: devuelve un diccionario con información del servidor (running, uptime, clientes, mensajes, etc.).
- **`create_health_handler(self)`**: define un `BaseHTTPRequestHandler` que responde a `GET /health` con JSON.
- **`start_health_server(self)`**: inicia el servidor HTTP en un hilo separado cuando el servidor principal arranca.
- **`stop_health_server(self)`**: cierra el servidor HTTP al detener el servidor.

#### 2.3. Uso
```bash
curl http://localhost:5004/health
```
Ejemplo de respuesta:
```json
{
  "status": "ok",
  "timestamp": "2025-11-24T20:30:00",
  "uptime_seconds": 3600,
  "clients": 3,
  "messages": 125,
  "terminal_id": "68133"
}
```

---

### 3. Configuración (`monitor_config.py`)

```python
# Telegram (placeholders)
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID   = "YOUR_TELEGRAM_CHAT_ID"

# Email (opcional)
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@example.com"
SMTP_PASSWORD = "YOUR_EMAIL_PASSWORD"
EMAIL_RECIPIENT = "alert_recipient@example.com"

# Parámetros de monitorización
HEALTH_CHECK_URL = "http://localhost:5004/health"
CHECK_INTERVAL_SECONDS = 10 * 60   # 10 minutos
FAILURE_THRESHOLD = 2               # número de fallos consecutivos antes de alertar
REQUEST_TIMEOUT = 5                 # segundos
```

> **Importante**: Reemplaza `YOUR_TELEGRAM_BOT_TOKEN` y `YOUR_TELEGRAM_CHAT_ID` con los valores reales obtenidos de BotFather y de tu chat. Si prefieres usar email, completa también los campos SMTP.

---

### 4. Script de Monitor (`monitor_server.py`)

#### 4.1. Flujo principal
1. **`check_health()`**: realiza una petición GET al endpoint `/health`.  Devuelve `True` si el campo `status` es `"ok"`.
2. **`monitor_loop(stop_event)`**: bucle que llama a `check_health()` cada `CHECK_INTERVAL_SECONDS`.  Lleva un contador de fallos (`failure_count`).
3. Cuando `failure_count >= FAILURE_THRESHOLD` se envía una alerta:
   - **Telegram** mediante `send_telegram_message(message)`.
   - **Email** (opcional) mediante `send_email_alert(subject, body)`.
4. Después de enviar la alerta, el contador se reinicia para evitar spam.

#### 4.2. Notificaciones
- **Telegram**: usa la API `https://api.telegram.org/bot<token>/sendMessage`.  Si los placeholders no están configurados, el script ignora la notificación y escribe en consola.
- **Email**: utiliza `smtplib` con TLS.  También se ignora si la configuración está vacía.

---

### 5. Scripts de Gestión

| Script | Función | Comentario |
|--------|----------|------------|
| `start_monitor.sh` | Lanza `monitor_server.py` en background con `nohup`, redirige salida a `monitor.log` y guarda el PID en `monitor.pid`. | Ideal para iniciar al arranque del sistema (puedes añadirlo a `rc.local` o crear un service). |
| `stop_monitor.sh` | Lee el PID de `monitor.pid` y envía `kill`. Elimina el archivo PID. | Verifica que el proceso exista antes de matar. |
| `status_monitor.sh` | Muestra si el proceso está corriendo y muestra las últimas 10 líneas del log. | Útil para diagnóstico rápido. |

#### 5.1. Ejemplo de uso
```bash
# Iniciar monitor
./start_monitor.sh

# Ver estado
./status_monitor.sh

# Detener monitor
./stop_monitor.sh
```

---

### 6. Troubleshooting

| Síntoma | Posible causa | Acción recomendada |
|---------|---------------|-------------------|
| `curl http://localhost:5004/health` devuelve 404 | El servidor TQ no está corriendo o la versión modificada no se está ejecutando. | Asegúrate de haber reiniciado `tq_server_rpg.py` después de los cambios. |
| No se reciben alertas en Telegram | `TELEGRAM_BOT_TOKEN` o `TELEGRAM_CHAT_ID` incorrectos, o el bot no tiene permiso para escribir en el chat. | Verifica el token con BotFather, envía un mensaje al bot y revisa `getUpdates` para obtener el chat ID. |
| `monitor_server.py` se detiene inesperadamente | Excepción no capturada (p.ej., error de red). | Revisa `monitor.log` para ver la traza completa. |
| El script sigue enviando alertas repetidamente | `FAILURE_THRESHOLD` es 1 o el contador no se reinicia. | Ajusta `FAILURE_THRESHOLD` a 2 o más, o verifica que el endpoint vuelva a `ok` después de la recuperación. |

---

### 7. Extensiones Futuras
- **Integración con Prometheus**: exponer métricas `/metrics` para monitorizar con Grafana.
- **Docker**: empaquetar el servidor y el monitor en contenedores separados.
- **Systemd service**: crear unidades `tq_server.service` y `tq_monitor.service` para gestión automática.

---

## Conclusión
Con los archivos creados (`monitor_config.py`, `monitor_server.py`, los scripts `*.sh` y la documentación) tienes un sistema de keep‑alive completo que te avisará cuando el servidor deje de responder. Cuando tengas acceso al celular, simplemente actualiza `monitor_config.py` con tus credenciales de Telegram y ejecuta `./start_monitor.sh`.  Si necesitas cualquier ajuste adicional o tienes dudas, avísame.

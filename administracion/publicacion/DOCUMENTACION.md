# Documentación: publicación web de logs (TQ)

Este documento describe en detalle la implementación del módulo ubicado en `administracion/publicacion/`, pensado como **herramienta temporal** para que un operador pueda **listar, previsualizar y descargar** archivos de la carpeta `logs/` del proyecto TQ, con **autenticación mínima** y exposición posible a Internet.

---

## 1. Objetivo y alcance

- **Objetivo**: ofrecer una interfaz web sencilla sobre los archivos existentes en `<raíz_del_proyecto>/logs/`.
- **Fuera de alcance** (por diseño actual):
  - No modifica ni rota logs.
  - No integra con el servidor TQ (`tq_server_rpg.py`); corre como **proceso independiente**.
  - No indexa contenido ni ofrece búsqueda full-text dentro del archivo (solo filtro por nombre en el listado).
  - No gestiona usuarios en base de datos; la autenticación es **HTTP Basic** con credenciales definidas en código.

---

## 2. Ubicación en el repositorio

| Ruta | Rol |
|------|-----|
| `administracion/publicacion/app.py` | Aplicación Flask (rutas, auth, lectura de archivos). |
| `administracion/publicacion/requirements.txt` | Dependencias: `flask`, `waitress`. |
| `administracion/publicacion/README.md` | Guía breve de uso. |
| `administracion/publicacion/DOCUMENTACION.md` | Este documento. |

La **raíz del proyecto TQ** se infiere en código como el directorio **dos niveles arriba** de `app.py`:

- `app.py` → `administracion/publicacion/`
- `parents[1]` → `administracion/`
- `parents[2]` → raíz del repo (donde suelen estar `tq_server_rpg.py`, `logs/`, etc.)

La carpeta expuesta es:

```text
<raíz_del_proyecto>/logs/
```

resuelta de forma absoluta (`Path.resolve()`), para evitar ambigüedades si el proceso se lanza con otro directorio de trabajo.

---

## 3. Stack tecnológico

- **Python 3** (probado en entornos 3.10+; en desarrollo local se usó 3.12).
- **Flask**: enrutamiento, respuestas HTML, `send_file` para descargas.
- **Waitress** (recomendado en producción temporal): servidor WSGI multi-hilo, adecuado para exponer en `0.0.0.0`.

---

## 4. Configuración relevante (`app.py`)

### 4.1 Credenciales (hardcode)

En la cabecera del módulo se definen:

- `ADMIN_USER`: nombre de usuario HTTP Basic.
- `ADMIN_PASS`: contraseña HTTP Basic.

**Recomendación operativa**: cambiar ambos valores antes de exponer el servicio; no commitear contraseñas reales en repositorios públicos. Si el archivo ya contiene una contraseña en producción, tratarlo como **secreto** (rotación si hubo exposición).

La verificación usa `hmac.compare_digest` para comparar usuario y contraseña con **tiempo casi constante**, reduciendo filtración por tiempos de respuesta en intentos de adivinanza.

### 4.2 Directorio y tipos de archivo

- `LOGS_DIR`: `<raíz>/logs`.
- `ALLOWED_EXTS`: solo se listan y sirven archivos cuya extensión sea **`.log`** o **`.txt`** (comparación case-insensitive en el sufijo).

Archivos sin esas extensiones **no aparecen** en el listado y **no son accesibles** por URL directa (la validación lo impide).

### 4.3 Límites de visualización (“tail”)

Para no cargar archivos enormes en memoria ni enviar respuestas HTML desmesuradas:

| Constante | Valor | Efecto |
|-----------|-------|--------|
| `MAX_TAIL_LINES` | 20000 | Máximo de líneas que se pueden pedir en la vista. |
| `MAX_TAIL_BYTES` | 2_000_000 (~2 MiB) | Máximo de bytes leídos desde el **final** del archivo para reconstruir esas líneas. |

**Comportamiento**:

1. Se lee un bloque de hasta `MAX_TAIL_BYTES` desde el fin del archivo.
2. Se decodifica como UTF-8 con `errors="replace"` (bytes inválidos se sustituyen; típico en logs mixtos).
3. Se normalizan saltos de línea (`\r\n` / `\r` → `\n`).
4. Si el archivo es más grande que el bloque leído, la **primera línea del bloque puede estar truncada**; en ese caso se **descarta la primera línea** del split para no mostrar una línea cortada al inicio del `<pre>`.
5. Se toman las últimas `n` líneas (`n` entre 1 y `MAX_TAIL_LINES`).

La vista por defecto usa **400 líneas** si no se pasa el parámetro `lines`.

### 4.4 Variables de entorno (solo modo `python app.py`)

Si se ejecuta el módulo como script principal:

- `TQ_LOGVIEW_HOST` (default `0.0.0.0`)
- `TQ_LOGVIEW_PORT` (default `8088`)

Con **Waitress**, el host/puerto se definen en la línea de comandos (`--listen=...`), no en estas variables.

---

## 5. Seguridad

### 5.1 Autenticación

- Todas las rutas **excepto** `GET /health` exigen cabecera `Authorization: Basic ...` válida.
- Navegadores compatibles muestran diálogo de usuario/contraseña la primera vez.

**Limitaciones conocidas de HTTP Basic**:

- Las credenciales viajan en cada petición (base64); **es obligatorio usar HTTPS** si el tráfico cruza redes no confiables. En despliegue temporal, lo ideal es poner **TLS** delante (nginx/Caddy) o VPN.

### 5.2 Path traversal

Antes de servir un archivo:

1. Debe existir como archivo regular bajo `LOGS_DIR`.
2. `p.resolve().relative_to(LOGS_DIR)` debe tener éxito: garantiza que la ruta resuelta **no sale** del directorio permitido (mitiga `..`, symlinks maliciosos fuera del árbol, etc.).
3. La extensión debe estar en `ALLOWED_EXTS`.

Cualquier incumplimiento → **404** (`abort(404)`).

### 5.3 XSS en la vista HTML

El contenido del log se inserta en HTML tras escapar con `_escape_html` (`&`, `<`, `>`, comillas), de modo que líneas con `<script>` u otras secuencias no se ejecutan en el navegador.

### 5.4 Superficie de exposición

- El endpoint `/health` responde `ok` **sin autenticación**, pensado para balanceadores o comprobaciones locales. Si se considera información innecesaria en Internet, se puede proteger o restringir por firewall a IPs de monitorización.

---

## 6. API / rutas HTTP

| Método y ruta | Auth | Descripción |
|---------------|------|-------------|
| `GET /` | Sí | Redirección a `/logs`. |
| `GET /health` | No | Texto plano `ok` (comprobación de vida). |
| `GET /logs` | Sí | Tabla de archivos `.log`/`.txt` en `LOGS_DIR`, ordenados por fecha de modificación descendente. Query opcional: `q` (filtro por subcadena en el nombre, case-insensitive). |
| `GET /logs/<name>` | Sí | Vista HTML con las últimas `lines` líneas del archivo (bloque final del archivo, ver límites de tail). Query opcional: `lines` (entero, default 400, máx `MAX_TAIL_LINES`). Query opcional: `device` — filtra ese bloque dejando solo líneas que contengan la subcadena indicada (comparación **sin** distinguir mayúsculas): si `device` son **solo dígitos**, se busca `device_id=<dígitos>` (útil para `Reenvios_*.log`); en otro caso se usa el texto de `device` tal cual como subcadena. |
| `GET /download/<name>` | Sí | Descarga el archivo completo con `Content-Disposition: attachment`. |

El parámetro `<name>` es el nombre de archivo dentro de `logs/` (sin rutas anidadas en el diseño actual: solo `iterdir()` en el listado; la ruta sigue validada igual).

---

## 7. Despliegue

### 7.1 Instalación de dependencias

Desde la raíz del proyecto:

```bash
python3 -m pip install -r administracion/publicacion/requirements.txt
```

### 7.2 Ejecución recomendada (Waitress)

```bash
cd /ruta/al/proyecto/TQ
python3 -m waitress --listen=0.0.0.0:8088 administracion.publicacion.app:app
```

- `--listen=0.0.0.0:8088` escucha en todas las interfaces IPv4 del servidor en el puerto 8088.

### 7.3 Firewall y proveedor cloud

Si desde Internet aparece **timeout** (`ERR_CONNECTION_TIMED_OUT`), suele faltar:

1. Regla en el **firewall del SO** (firewalld/ufw/iptables) permitiendo **TCP 8088**.
2. Regla en el **firewall del panel del VPS** (si existe), además del del SO.

Comprobación en el propio servidor:

```bash
curl -sS http://127.0.0.1:8088/health
```

Si responde `ok` localmente pero no desde fuera, el problema casi siempre es red/firewall, no la app.

### 7.4 Ejecutar en segundo plano

Opciones habituales:

- **`nohup ... &`**: rápido; redirigir stdout/stderr a un archivo de log del viewer.
- **`screen` / `tmux`**: sesión recuperable tras desconectar SSH.
- **systemd**: unidad `service` con `Restart=always` para entorno más estable.

### 7.5 HTTPS (recomendado en Internet)

Para no enviar Basic Auth en claro:

- Colocar **nginx** o **Caddy** como reverse proxy en 443 con certificado (Let’s Encrypt) y proxy_pass a `127.0.0.1:8088`, **o**
- Restringir acceso por **VPN** / IP allowlist.

---

## 8. Relación con el resto del proyecto TQ

- El servidor principal de traza (`tq_server_rpg.py`) y herramientas de reenvío escriben en `logs/` según la configuración del proyecto (por ejemplo `Reenvios_YYYYMMDD.log`, `LOG_*.txt`, etc.).
- Este módulo **solo lee** esos archivos; no requiere que el servidor TQ esté corriendo para servir la web, pero los archivos deben existir en disco.

---

## 9. Mantenimiento y extensiones posibles

Ideas si deja de ser “temporal”:

- Variables de entorno para `ADMIN_USER` / `ADMIN_PASS` en lugar de hardcode.
- Soporte de subcarpetas bajo `logs/` con listado recursivo controlado.
- Búsqueda dentro del archivo (streaming o índices).
- Límite de tasa (rate limiting) y registro de accesos.
- Integración TLS terminada en el mismo proceso (menos habitual; suele preferirse reverse proxy).

---

## 10. Resolución de problemas

| Síntoma | Causa probable | Qué revisar |
|---------|----------------|-------------|
| Timeout desde el navegador | Puerto cerrado en firewall | SO + panel del VPS; `curl` local vs externo |
| 401 Unauthorized | Credenciales incorrectas o no enviadas | Usuario/clave; caché del navegador |
| Listado vacío | `logs/` inexistente o sin `.log`/`.txt` | Ruta del proyecto; permisos de lectura |
| Vista con pocas líneas | Archivo muy grande y `MAX_TAIL_BYTES` corta el bloque | Aumentar constante o usar “descargar” |
| Error al importar módulo | Dependencias no instaladas | `pip install -r requirements.txt` |

---

## 11. Referencias rápidas

- Código: `administracion/publicacion/app.py`
- Guía corta: `administracion/publicacion/README.md`

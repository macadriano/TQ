# Reenvíos configurables por equipo (CSV)

Este documento describe el **motor de reenvíos** basado en archivo, que complementa el servidor `tq_server_rpg.py`. Permite definir por **equipo** (ID de 5 dígitos) hacia qué **IP y puerto** enviar tráfico, en qué **transporte** (UDP/TCP) y con qué **formato** (mensaje GEO5/RPG o TQ crudo), y si el envío al **destino general** UDP debe omitirse o no.

**Importante:** todos los reenvíos (incluyendo TQ crudo por TCP/UDP) se configuran **exclusivamente** en `REENVIOS_CONFIG.txt` mediante reglas. No existe reenvío “por defecto” hardcodeado para el payload TQ.

## Archivos involucrados

| Archivo | Rol |
|--------|-----|
| `REENVIOS_CONFIG.txt` | Configuración en texto tipo CSV (raíz del proyecto, junto a `tq_server_rpg.py` por defecto). |
| `reenvios_config.py` | Carga y validación del CSV; estructura en memoria; escritura de `Reenvios_YYYYMMDD.log`. |
| `tq_server_rpg.py` | Integración: al iniciar carga las reglas; en cada mensaje aplica las reglas del equipo correspondiente. |

Ruta por defecto del CSV: directorio del script `tq_server_rpg.py` + `REENVIOS_CONFIG.txt`. Se puede cambiar instanciando `TQServerRPG(..., reenvios_config_path='/ruta/al/archivo.txt')`.

*** SE RECARGA AUTOMATICAMENTE CADA 1 MINUTOS EL ARCHIVO DE CONFIGURACION DE REENVIOS PARA QUE NO HAYA QUE REINICIAR A MANO EL MODULO CADA VEZ QUE SE ACTUALIZA UN DATO EN EL ARCHIVO PARA AGREGAR Y/O MODIFICAR LOS REENVIOS. ****

## Formato del CSV

- Separador: **coma** (`,`). Los campos pueden llevar espacio tras la coma; el sistema aplica **`strip()`** a cada celda.
- Primera fila: **cabecera** con los nombres de columna (la fila cuya primera celda es `TIPO` se omite como datos).
- Se permiten **comentarios**: cualquier línea que (luego de aplicar `strip()`) empiece con `#` se ignora.
- Una fila = una regla de reenvío.

### Columnas

| Columna | Descripción |
|---------|-------------|
| `TIPO` | `SERVICIO` o `CLONAR` (ver más abajo). |
| `CLIENTE` | Identificador lógico (auditoría en log; no cambia la lógica de envío). |
| `EQUIPO` | ID del equipo en **5 dígitos** (mismo criterio que el ID RPG en el flujo TQ). |
| `TRANSPORTE` | `UDP` o `TCP`. |
| `PROTOCOLO_GPS` | `GEO5` o `GEO` (equivalente a GEO5) para mensaje ya convertido a RPG/GEO5; `TQ` para **payload crudo** igual al recibido por TCP. |
| `IP` | IPv4 válida. |
| `PUERTO` | Entero entre 1 y 65535. |

Filas incompletas, IP o puerto inválidos, `TIPO`/`TRANSPORTE`/`PROTOCOLO_GPS` desconocidos generan **avisos en el log del servidor** y esa fila se **ignora**; el proceso no se detiene.

## Destino general (UDP GEO5)

- Es el **UDP primario** configurado en el servidor: por defecto **`179.43.115.190:7007`** (`udp_host` / `udp_port`).
- Solo aplica a mensajes que ya se convirtieron a **GEO5/RPG** (mismo criterio que antes: no es el reenvío TCP del TQ crudo).
- Cada vez que se envía correctamente al general, se registra en `Reenvios_*.log` con **`tipo=GENERAL`**.

## Semántica de `TIPO`

Para un mensaje con un `EQUIPO` dado, se buscan **todas** las filas cuyo `EQUIPO` coincide.

1. **¿Hay al menos una regla `SERVICIO` para ese equipo?**  
   - **Sí** → **no** se envía ese GEO5 al **destino general** UDP.  
   - **No** → se envía al destino general UDP (comportamiento histórico cuando no había excepciones por CSV).

2. **Independientemente del punto anterior**, se **ejecutan todas** las reglas del CSV para ese equipo cuyo `PROTOCOLO_GPS` y `TRANSPORTE` aplican al tipo de envío (ver siguiente sección).

### `SERVICIO`

- Indica que ese equipo está atendido “por servicio” hacia destinos del CSV: **bloquea** el envío GEO5 al UDP general si existe al menos una fila `SERVICIO` para ese `EQUIPO`.
- Las filas `SERVICIO` concretas (IP/puerto/protocolo/transporte) **sí se ejecutan**.

### `CLONAR`

- **No bloquea** el destino general: si no hay ningún `SERVICIO` para el equipo, el GEO5 sigue yendo al general; las filas `CLONAR` **añaden** envíos extra.
- Si **sí** hay algún `SERVICIO` para el mismo equipo, el general sigue bloqueado, pero las filas `CLONAR` **igual se aplican** (copias hacia los destinos indicados).

## Cuándo se aplica cada tipo de regla

### Reglas con `PROTOCOLO_GPS` = GEO5 (o GEO)

- Se evalúan cuando el servidor **ya generó** el mensaje RPG/GEO5 (mismo flujo que `send_geo5_rpg_udp`).
- **UDP**: se envía el texto GEO5 por datagrama.
- **TCP**: se abre conexión TCP y se envía el mismo contenido (UTF-8).

### Reglas con `PROTOCOLO_GPS` = TQ

- Se evalúan con el **mismo buffer binario** recibido del equipo por TCP (TQ crudo).
- **UDP** / **TCP** según la columna `TRANSPORTE`.

## Log dedicado: `logs/Reenvios_YYYYMMDD.log`

- Un archivo **por día** (fecha del calendario local del servidor).
- Formato: campos separados por tabulador, una línea por envío registrado desde el motor de reenvíos.
- Campos habituales: timestamp, `device_id`, `tipo` (`GENERAL`, `SERVICIO`, `CLONAR`), `destino=IP:puerto`, `transporte`, `formato` (p. ej. `GEO5`, `TQ`), `payload` (truncado si es muy largo), y opcionalmente `cliente`.

El log general de aplicación (`logs/LOG_*.txt`) y `guardarLogPacket` siguen usándose como antes para tráfico; `Reenvios_*.log` centraliza la trazabilidad del **motor de reglas**.

## Ejemplo (archivo real de referencia)

Con el `REENVIOS_CONFIG.txt` de ejemplo:

- Equipos `26501`, `26494`, `26504`, `26495`, `26500`: solo filas **`SERVICIO`** UDP GEO5 hacia `154.53.61.40:2101` y hacia `168.197.48.154:2101`.  
  **Efecto:** no reciben GEO5 en `179.43.115.190:7007`; sí en **ambas** IPs del CSV (dos envíos por posición, uno por cada fila aplicable).

- Equipo `95899`: una fila **`CLONAR`** UDP GEO5 a `168.197.48.154:2101`.  
  **Efecto:** sigue enviándose al **general** `179.43.115.190:7007` y además la copia al destino del CSV.

## Arranque y diagnóstico

- Al iniciar, el servidor imprime la ruta del CSV y el número de **reglas** y **equipos** cargados.
- El comando interactivo `status` muestra `reenvios_config_path`, total de reglas y listado de equipos con al menos una regla.
- Si el archivo no existe: se registra advertencia y el comportamiento de reenvío GEO5 vuelve al **solo destino general** para todos los equipos (sin reglas CSV).
 - El archivo de reenvíos se **relee automáticamente** en background (polling), por defecto **cada 60s**, y solo se aplica si cambió en disco. Si el archivo no se puede leer temporalmente, el servicio mantiene las reglas anteriores.

## Buenas prácticas

- Mantener **copia de respaldo** del CSV antes de cambios en producción.
- Revisar `Reenvios_*.log` tras cambios para confirmar `tipo`, `destino` y `formato`.
- Evitar duplicar sin querer la misma IP/puerto en muchas filas si no se desean envíos repetidos.
- Recordar: **`SERVICIO` sin filas GEO5** pero con solo reglas TQ **no** envía GEO5 al general ni a destinos GEO5 definidos solo por otras filas; el diseño del CSV debe cubrir todos los destinos GEO5 necesarios para ese equipo.

## Heartbeat y health check

El **heartbeat UDP** y el servidor HTTP de **health** no forman parte del CSV de reenvíos GPS; siguen configurados en `TQServerRPG` como hasta ahora.

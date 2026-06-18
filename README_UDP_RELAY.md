# Relay UDP GEO5/RGP

Proceso **separado** de `tq_server_rpg.py`. Escucha GEO5/RGP por UDP, reemplaza fecha y hora GPS por **UTC actual del servidor**, recalcula checksum y reenvía según `REENVIOS_CONFIG_UDP.txt`.

## Archivos

| Archivo | Rol |
|---------|-----|
| `geo5_udp_relay.py` | Proceso relay (puerto **6003** por defecto) |
| `REENVIOS_CONFIG_UDP.txt` | Reglas CSV (mismo formato que `REENVIOS_CONFIG.txt`) |
| `logsUDP/` | Logs de tráfico y reenvíos |
| `start_geo5_udp_relay.sh` / `stop_geo5_udp_relay.sh` | Arranque/parada en Linux |

## Logs (`logsUDP/`)

| Archivo | Contenido |
|---------|-----------|
| `LOG_DDMMYY.txt` | Paquetes entrantes/salientes (estilo `logs/LOG_*.txt`) |
| `Reenvios_YYYYMMDD.log` | Una línea por reenvío (tab-separated) |
| `Relay_YYYYMMDD.log` | Log de aplicación (eventos, errores, recarga CSV) |

## Configuración

`REENVIOS_CONFIG_UDP.txt` usa las mismas columnas que `REENVIOS_CONFIG.txt`:

`TIPO, CLIENTE, EQUIPO, TRANSPORTE, PROTOCOLO_GPS, IP, PUERTO, FORMATO_ID`

Solo se aplican filas con **TRANSPORTE=UDP** y **PROTOCOLO_GPS=GEO5**. No hay destino UDP general: solo destinos del CSV.

`FORMATO_ID` (opcional): igual que en el servidor TCP — ajusta `ID=...` y recalcula checksum antes de reenviar.

## Ejecución

```bash
# Manual
python3 geo5_udp_relay.py --port 6003

# Daemon (Linux)
./start_geo5_udp_relay.sh
./stop_geo5_udp_relay.sh
```

Argumentos útiles:

- `--config /ruta/REENVIOS_CONFIG_UDP.txt`
- `--reload-interval 60` (recarga CSV; 0 = desactivar)
- `--log-dir logsUDP`

## Flujo

1. Recibe datagrama GEO5 `>RGP...` en puerto 6003.
2. Extrae `;ID=...;` y resuelve equipo (5 dígitos).
3. Sustituye `aaaaaa` (ddmmyy) y `bbbbbb` (hhmmss UTC).
4. Recalcula checksum (`protocolo.sacar_checksum`).
5. Busca reglas en CSV para ese `EQUIPO` y envía por UDP a cada destino.

## Firewall

Abrir **UDP 6003** en el servidor si el origen envía desde fuera.

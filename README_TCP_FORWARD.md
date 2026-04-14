## Reenvío TCP (TQ crudo) vía reglas CSV

La funcionalidad de reenvío del **payload crudo (TQ)** ya no se configura con parámetros `tcp_forward_*` en `tq_server_rpg.py`.
Ahora se controla **exclusivamente** desde `REENVIOS_CONFIG.txt` (ver `README_REENVIOS.md`).

### Descripción

Para reenviar el TQ crudo:
- Use `PROTOCOLO_GPS=TQ` y `TRANSPORTE=TCP` (o `UDP`) en el CSV.
- El payload enviado es **exactamente** el mismo `bytes` recibido por TCP desde el equipo.

### Ejemplo CSV

```csv
TIPO, CLIENTE, EQUIPO, TRANSPORTE, PROTOCOLO_GPS, IP, PUERTO
CLONAR, TEST, 26501, TCP, TQ, 34.95.221.179, 5003
CLONAR, TEST, 26501, TCP, TQ, 35.199.119.107, 5103
```

## 🛡️ Seguridad y Performance

Esta funcionalidad ha sido diseñada para ser **crítica-safe**, asegurando que no afecte la operatoria principal del servidor:

1.  **Aislamiento de Errores**: Todo el proceso de reenvío está envuelto en un bloque `try-except`. Cualquier error de conexión o envío es capturado, logueado y **ignorado** para el flujo principal. El servidor nunca se detendrá por un fallo en este reenvío.
2.  **Timeouts Cortos**: Se utiliza un timeout estricto de **2.0 segundos** para la conexión TCP. Si el servidor destino no responde en ese tiempo, se aborta el intento inmediatamente para no retener el hilo de procesamiento.
3.  **Datos Puros**: No se realiza ninguna manipulación de los datos antes del reenvío, garantizando la integridad de la información original.

## 📝 Logging

- Cada reenvío por regla queda registrado en `logs/Reenvios_YYYYMMDD.log`.
- Además, el tráfico se registra con `guardarLogPacket` en el log diario unificado (`logs/LOG_DDMMYY.txt`).
- En `Reenvios_YYYYMMDD.log` se incluye el campo `payload=` (hex para `TQ`, texto para `GEO5`), truncado si es muy largo.

## 🔍 Verificación

Use el comando interactivo `status` y revise la sección de “Reenvíos CSV” (cantidad de reglas y equipos). Luego verifique en `logs/Reenvios_YYYYMMDD.log` que se estén generando líneas con `formato=TQ` y `transporte=TCP`.

# Documentación de Reenvío TCP (Raw Data)

Este documento detalla la funcionalidad de reenvío de datos crudos (Raw Data) vía TCP implementada en el servidor TQ+RPG.

## 📋 Descripción

El servidor tiene la capacidad de reenviar **exactamente los mismos bytes que recibe** de los dispositivos GPS a un servidor secundario vía TCP. Esta funcionalidad opera en paralelo al procesamiento principal (conversión a RPG y reenvío UDP) y está diseñada para ser no bloqueante y segura.

### Detalles del Destino
- **IP Destino**: `200.58.98.187`
- **Puerto Destino**: `5003`
- **Protocolo**: TCP
- **Formato de Datos**: Bytes crudos (sin procesar, tal cual se reciben del dispositivo)

## ⚙️ Configuración

La funcionalidad es modular y se configura en la inicialización de la clase `TQServerRPG` en el archivo `tq_server_rpg.py`.

### Parámetros

```python
server = TQServerRPG(
    # ... otros parámetros ...
    tcp_forward_host='200.58.98.187',  # IP del servidor destino
    tcp_forward_port=5003,             # Puerto del servidor destino
    tcp_forward_enabled=True           # Activar (True) o Desactivar (False)
)
```

### Cómo Desactivar
Para desactivar esta funcionalidad sin borrar código, simplemente cambie el parámetro `tcp_forward_enabled` a `False` en la instanciación del servidor al final del archivo `tq_server_rpg.py`.

## 🛡️ Seguridad y Performance

Esta funcionalidad ha sido diseñada para ser **crítica-safe**, asegurando que no afecte la operatoria principal del servidor:

1.  **Aislamiento de Errores**: Todo el proceso de reenvío está envuelto en un bloque `try-except`. Cualquier error de conexión o envío es capturado, logueado y **ignorado** para el flujo principal. El servidor nunca se detendrá por un fallo en este reenvío.
2.  **Timeouts Cortos**: Se utiliza un timeout estricto de **2.0 segundos** para la conexión TCP. Si el servidor destino no responde en ese tiempo, se aborta el intento inmediatamente para no retener el hilo de procesamiento.
3.  **Datos Puros**: No se realiza ninguna manipulación de los datos antes del reenvío, garantizando la integridad de la información original.

## 📝 Logging

El sistema registra la actividad de este módulo en el log diario unificado (`logs/LOG_DDMMYY.txt`):

- **Éxito**: `Datos reenviados por TCP a 200.58.98.187:5003`
- **Error**: `Error reenviando datos por TCP a ...: [Detalle del error]`

## 🔍 Verificación

Puede verificar si la funcionalidad está activa ejecutando el script de estado:

```bash
./server_status_rpg.sh
```

La salida incluirá una sección indicando el estado del reenvío TCP:

```
...
tcp_forward_enabled: True
tcp_forward_host: 200.58.98.187
tcp_forward_port: 5003
...
```

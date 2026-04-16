# Publicación temporal de logs (TQ)

Módulo web mínimo para **listar / ver / descargar** archivos dentro de `./logs/` del proyecto.

## Ubicación

`administracion/publicacion/`

## Requisitos

Instalar dependencias:

```bash
python -m pip install -r administracion/publicacion/requirements.txt
```

## Ejecutar (temporal)

### Opción A (simple, no recomendada para Internet)

```bash
python administracion/publicacion/app.py
```

### Opción B (mejor para exponer, Windows/Linux): waitress

```bash
python -m waitress --listen=0.0.0.0:8088 administracion.publicacion.app:app
```

Luego abrir:

- `http://<tu-host>:8088/logs`

## Autenticación

HTTP Basic Auth hardcodeado en `administracion/publicacion/app.py`:

- `ADMIN_USER`
- `ADMIN_PASS`

**IMPORTANTE:** cambiá `ADMIN_PASS` antes de exponerlo a Internet.

## Notas

- Solo lee archivos con extensiones `.log` y `.txt`.
- La vista muestra por defecto las **últimas 400 líneas**, configurable con `?lines=...` (máximo 20000).


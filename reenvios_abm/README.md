# Reenvíos ABM (local)

Interfaz web **responsive** para administrar `REENVIOS_CONFIG.txt` (ABM de reglas, vista por equipos y por clientes).

## Requisitos

- Python 3.10+

## Ejecutar en tu PC (Windows / PowerShell)

Desde la raíz del repo (`TQ`):

```powershell
py -m venv .venv
.\.venv\Scripts\pip install -r reenvios_abm\requirements.txt
.\.venv\Scripts\python reenvios_abm\app.py
```

Abrir en el navegador: `http://127.0.0.1:8090`

## Archivo a editar (configurable)

Por defecto, el ABM busca el archivo en la raíz del repo:

- `.\REENVIOS_CONFIG.txt`

Podés apuntar a otro archivo con variable de entorno:

```powershell
$env:TQ_REENVIOS_CONFIG_PATH = "C:\ruta\REENVIOS_CONFIG.txt"
.\.venv\Scripts\python reenvios_abm\app.py
```

## Seguridad

Esto es para **uso local**. Si se expone en red/Internet, agregá autenticación fuerte y HTTPS por proxy.

---

## Novedades / funcionalidades

- **UI responsiva** (mejor en pantalla tipo teléfono) y **menú desplegable** en móvil.
- **Reglas**:
  - Contador de **total de reglas** (y “mostradas” cuando se filtra).
  - Fix de edición/eliminación cuando hay filtro (los índices ahora apuntan a la regla correcta).
  - Validación de duplicados por equipo:
    - `SERVICIO`: **no permite** más de una regla `SERVICIO` por equipo (bloquea y muestra cliente(s)).
    - `CLONAR`: permite duplicados pero **avisa** cliente(s) donde ya existe.
  - Campo opcional **`FECHA_ALTA`** (se guarda como `DD/MM/YYYY`; también acepta `YYYY-MM-DD` y lo normaliza).
- **Equipos**:
  - Contadores superiores (totales).
  - Columna **Fecha alta** (toma la **más antigua** de las reglas del equipo).
- **Clientes**:
  - Contadores superiores (totales).
  - Columna **Equipos (#)** (cantidad de equipos por cliente).


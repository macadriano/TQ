# Configuración de .gitignore para Proyecto TQ

## Archivo Creado

Se ha creado el archivo **`.gitignore`** en la raíz del proyecto para controlar qué archivos y carpetas se excluyen del repositorio Git.

## Carpetas y Archivos Ignorados

### 📁 Carpetas Principales Ignoradas

1. **`logs/`** - Carpeta de logs diarios (se crea automáticamente)
2. **`BACKUP/`** - Carpeta de backups
3. **`bak*/`** - Cualquier carpeta que empiece con "bak"
4. **`__pycache__/`** - Cache de Python
5. **`-Force/`** - Carpeta temporal

### 📄 Archivos de Log Ignorados

Todos los archivos de log se ignoran automáticamente:
- `*.log` - Archivos de log
- `*.txt` - Archivos de texto (excepto README)
- `*.csv` - Archivos CSV (datos de posiciones)

**Excepciones**: Los archivos `README*.md` y `README*.txt` SÍ se incluyen en Git.

### 🐍 Archivos de Python Ignorados

- `__pycache__/` - Cache de Python
- `*.pyc`, `*.pyo`, `*.pyd` - Archivos compilados
- `.env`, `venv/`, `env/` - Entornos virtuales
- `*.egg-info/` - Información de paquetes

### 💻 Archivos de IDEs Ignorados

- **VSCode**: `.vscode/`, `*.code-workspace`
- **PyCharm**: `.idea/`, `*.iml`
- **Sublime**: `*.sublime-project`, `*.sublime-workspace`
- **Vim**: `*.swp`, `*.swo`

### 🖥️ Archivos del Sistema Operativo

- **Windows**: `Thumbs.db`, `Desktop.ini`, `$RECYCLE.BIN/`
- **macOS**: `.DS_Store`, `.AppleDouble`
- **Linux**: `.directory`, `.Trash-*`

### 🧪 Archivos de Test

- `test_*.py` - Scripts de prueba
- `*_test.py` - Scripts de prueba

### ⚙️ Archivos de Configuración Local

- `config_local.py`
- `settings_local.py`
- `.env.local`

## Archivos que SÍ se Subirán a Git

✅ **Código fuente principal**:
- `funciones.py`
- `protocolo.py`
- `tq_server_rpg.py`
- `setup.py`

✅ **Scripts de control**:
- `start_server_rpg.sh`
- `stop_server_rpg.sh`
- `server_status_rpg.sh`

✅ **Documentación**:
- `README*.md` (todos los README)
- `.gitignore`

✅ **Carpeta varios/** (si la quieres incluir):
- Actualmente está marcada como `??` (sin seguimiento)
- Puedes decidir si incluirla o no

## Verificar Archivos Ignorados

### Ver estado actual de Git

```bash
git status
```

### Ver archivos que serán ignorados

```bash
git status --ignored
```

### Verificar si un archivo específico será ignorado

```bash
git check-ignore -v nombre_archivo.txt
```

## Limpiar Archivos ya Trackeados

Si algunos archivos que ahora están en `.gitignore` ya fueron agregados a Git anteriormente, necesitas eliminarlos del índice:

```bash
# Eliminar del índice pero mantener en disco
git rm --cached nombre_archivo

# Eliminar carpeta completa del índice
git rm -r --cached nombre_carpeta/

# Ejemplo: eliminar todos los logs del índice
git rm --cached *.log
git rm -r --cached logs/
git rm -r --cached BACKUP/
git rm -r --cached __pycache__/
```

## Agregar Archivos al Repositorio

Después de configurar el `.gitignore`, puedes agregar los archivos deseados:

```bash
# Ver qué archivos se agregarán
git status

# Agregar archivos específicos
git add funciones.py
git add tq_server_rpg.py
git add README_LOGS.md
git add .gitignore

# O agregar todos los archivos permitidos
git add .

# Hacer commit
git commit -m "Implementado sistema de logs diarios y configurado .gitignore"

# Subir al repositorio remoto
git push origin main
```

## Personalizar .gitignore

Si necesitas modificar qué archivos se ignoran, edita el archivo `.gitignore`:

### Ignorar archivo específico
```
mi_archivo.txt
```

### Ignorar carpeta específica
```
mi_carpeta/
```

### Ignorar todos los archivos con extensión
```
*.extension
```

### NO ignorar un archivo (excepción)
```
!archivo_importante.txt
```

### Ignorar archivos en cualquier subcarpeta
```
**/nombre_archivo.txt
```

## Ejemplo de Flujo de Trabajo

```bash
# 1. Ver estado actual
git status

# 2. Limpiar archivos no deseados del índice (si es necesario)
git rm -r --cached logs/
git rm -r --cached BACKUP/
git rm --cached *.log

# 3. Agregar archivos importantes
git add funciones.py
git add protocolo.py
git add tq_server_rpg.py
git add *.sh
git add README*.md
git add .gitignore

# 4. Hacer commit
git commit -m "Configuración inicial con sistema de logs diarios"

# 5. Subir al repositorio
git push origin main
```

## Notas Importantes

⚠️ **Archivos ya en Git**: El `.gitignore` solo afecta archivos nuevos. Si un archivo ya está en Git, seguirá siendo trackeado hasta que lo elimines con `git rm --cached`.

⚠️ **Datos sensibles**: Nunca subas contraseñas, tokens, o datos sensibles. Agrégalos al `.gitignore`.

⚠️ **Logs grandes**: Los archivos de log pueden crecer mucho. Es mejor no subirlos a Git.

⚠️ **Backups**: Las carpetas de backup no deben estar en Git. Usa un sistema de backup separado.

## Carpeta `varios/`

La carpeta `varios/` actualmente no está en `.gitignore`. Opciones:

1. **Incluirla en Git** (si contiene código útil):
   ```bash
   git add varios/
   ```

2. **Ignorarla** (si es temporal):
   Agrega a `.gitignore`:
   ```
   varios/
   ```

## Soporte

Para más información sobre `.gitignore`:
- [Documentación oficial de Git](https://git-scm.com/docs/gitignore)
- [Generador de .gitignore](https://www.toptal.com/developers/gitignore)

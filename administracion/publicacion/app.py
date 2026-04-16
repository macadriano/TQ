from __future__ import annotations

import base64
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from flask import Flask, Response, abort, redirect, request, send_file, url_for


# =========================
# Config mínima (hardcode)
# =========================

ADMIN_USER = "admin"
ADMIN_PASS = "Maximo2025"

# Carpeta de logs a exponer (solo lectura).
# Por defecto: raíz del proyecto + /logs
BASE_DIR = Path(__file__).resolve().parents[2]
LOGS_DIR = (BASE_DIR / "logs").resolve()

# Límite para evitar que un "tail" mate el server
MAX_TAIL_LINES = 20000
MAX_TAIL_BYTES = 2_000_000  # ~2MB del final del archivo

# Extensiones permitidas (podés ampliar)
ALLOWED_EXTS = {".log", ".txt"}


app = Flask(__name__)


@dataclass(frozen=True)
class LogFile:
    name: str
    path: Path
    size_bytes: int
    mtime: float


def _unauthorized() -> Response:
    return Response(
        "Unauthorized",
        401,
        {"WWW-Authenticate": 'Basic realm="TQ Logs"'},
    )


def _basic_auth_ok(auth_header: str | None) -> bool:
    if not auth_header:
        return False
    m = re.match(r"^Basic\s+(.+)$", auth_header.strip(), flags=re.IGNORECASE)
    if not m:
        return False
    try:
        raw = base64.b64decode(m.group(1)).decode("utf-8", errors="strict")
    except Exception:
        return False
    if ":" not in raw:
        return False
    user, pw = raw.split(":", 1)
    # Comparación en tiempo constante (mínima higiene)
    return hmac.compare_digest(user, ADMIN_USER) and hmac.compare_digest(pw, ADMIN_PASS)


@app.before_request
def _require_auth() -> Optional[Response]:
    # Si querés excluir healthcheck, agregalo acá.
    if request.path == "/health":
        return None
    if _basic_auth_ok(request.headers.get("Authorization")):
        return None
    return _unauthorized()


def _is_allowed_file(p: Path) -> bool:
    if p.suffix.lower() not in ALLOWED_EXTS:
        return False
    try:
        # Asegura que p esté dentro de LOGS_DIR (anti path traversal)
        p.resolve().relative_to(LOGS_DIR)
        return True
    except Exception:
        return False


def _list_logs() -> list[LogFile]:
    if not LOGS_DIR.exists() or not LOGS_DIR.is_dir():
        return []
    out: list[LogFile] = []
    for entry in LOGS_DIR.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in ALLOWED_EXTS:
            continue
        try:
            st = entry.stat()
        except Exception:
            continue
        out.append(
            LogFile(
                name=entry.name,
                path=entry,
                size_bytes=int(st.st_size),
                mtime=float(st.st_mtime),
            )
        )
    out.sort(key=lambda x: x.mtime, reverse=True)
    return out


def _tail_bytes(path: Path, max_bytes: int) -> bytes:
    size = path.stat().st_size
    read_size = min(size, max_bytes)
    with path.open("rb") as f:
        if read_size < size:
            f.seek(size - read_size)
        return f.read()


def _tail_lines_text(path: Path, lines: int) -> str:
    lines = max(1, min(int(lines), MAX_TAIL_LINES))
    data = _tail_bytes(path, MAX_TAIL_BYTES)
    # Decodificar “lo que se pueda” (logs pueden tener bytes raros)
    text = data.decode("utf-8", errors="replace")
    # Normalizar saltos
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = text.split("\n")
    # Si leímos un chunk parcial, la primera línea puede estar cortada.
    if len(parts) > 1 and path.stat().st_size > len(data):
        parts = parts[1:]
    tail = parts[-lines:]
    return "\n".join(tail)


def _html_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 20px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 10px 8px; text-align: left; }}
    th {{ background: #f9fafb; position: sticky; top: 0; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    pre {{ background: #0b1020; color: #d1d5db; padding: 12px; border-radius: 8px; overflow: auto; }}
    a {{ color: #2563eb; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .muted {{ color: #6b7280; }}
    .row {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
    .pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: #eef2ff; color: #3730a3; font-size: 12px; }}
    input {{ padding: 8px; border: 1px solid #d1d5db; border-radius: 8px; }}
    button {{ padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 8px; background: #fff; }}
  </style>
</head>
<body>
  <div class="row" style="justify-content: space-between; margin-bottom: 12px;">
    <div>
      <div style="font-weight: 700;">TQ · Publicación de Logs</div>
      <div class="muted">Carpeta: <code>{LOGS_DIR}</code></div>
    </div>
    <div class="muted">Servidor: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
  </div>
  {body}
</body>
</html>"""


@app.get("/")
def index() -> Response:
    return redirect(url_for("logs"))


@app.get("/health")
def health() -> Response:
    return Response("ok", 200, {"Content-Type": "text/plain; charset=utf-8"})


@app.get("/logs")
def logs() -> Response:
    q = (request.args.get("q") or "").strip().lower()
    items = _list_logs()
    if q:
        items = [x for x in items if q in x.name.lower()]
    rows = []
    for it in items:
        size_kb = it.size_bytes / 1024.0
        dt = datetime.fromtimestamp(it.mtime).strftime("%Y-%m-%d %H:%M:%S")
        rows.append(
            "<tr>"
            f"<td><code>{it.name}</code></td>"
            f"<td><span class='pill'>{dt}</span></td>"
            f"<td>{size_kb:,.1f} KB</td>"
            "<td>"
            f"<a href='{url_for('view_log', name=it.name)}'>ver</a> · "
            f"<a href='{url_for('download_log', name=it.name)}'>descargar</a>"
            "</td>"
            "</tr>"
        )
    body = f"""
  <div class="row" style="margin-bottom: 10px;">
    <form method="get" action="{url_for('logs')}" class="row">
      <input name="q" placeholder="Filtrar por nombre…" value="{q}" />
      <button type="submit">Buscar</button>
      <a class="muted" href="{url_for('logs')}">limpiar</a>
    </form>
  </div>
  <table>
    <thead>
      <tr><th>Archivo</th><th>Modificado</th><th>Tamaño</th><th>Acciones</th></tr>
    </thead>
    <tbody>
      {"".join(rows) if rows else "<tr><td colspan='4' class='muted'>No hay logs para mostrar.</td></tr>"}
    </tbody>
  </table>
"""
    return Response(_html_page("Logs", body), mimetype="text/html; charset=utf-8")


@app.get("/logs/<path:name>")
def view_log(name: str) -> Response:
    p = (LOGS_DIR / name)
    if not _is_allowed_file(p) or not p.exists() or not p.is_file():
        abort(404)
    try:
        n = int(request.args.get("lines") or "400")
    except ValueError:
        n = 400
    n = max(1, min(n, MAX_TAIL_LINES))
    text = _tail_lines_text(p, n)
    safe_name = p.name
    body = f"""
  <div class="row" style="margin-bottom: 10px;">
    <div style="font-weight: 700;"><code>{safe_name}</code></div>
    <div class="muted">Mostrando últimas <b>{n}</b> líneas</div>
  </div>
  <div class="row" style="margin-bottom: 10px;">
    <a href="{url_for('logs')}">← volver</a>
    <span class="muted">·</span>
    <a href="{url_for('download_log', name=safe_name)}">descargar</a>
  </div>
  <div class="row" style="margin-bottom: 10px;">
    <form method="get" action="{url_for('view_log', name=safe_name)}" class="row">
      <input name="lines" value="{n}" style="width: 120px;" />
      <button type="submit">Aplicar</button>
      <span class="muted">máx {MAX_TAIL_LINES}</span>
    </form>
  </div>
  <pre>{_escape_html(text)}</pre>
"""
    return Response(_html_page(f"Ver {safe_name}", body), mimetype="text/html; charset=utf-8")


@app.get("/download/<path:name>")
def download_log(name: str):
    p = (LOGS_DIR / name)
    if not _is_allowed_file(p) or not p.exists() or not p.is_file():
        abort(404)
    # send_file maneja streaming; as_attachment fuerza descarga
    return send_file(p, as_attachment=True, download_name=p.name)


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


if __name__ == "__main__":
    # Para pruebas locales. Para exponer en Internet, preferir waitress/gunicorn.
    host = os.environ.get("TQ_LOGVIEW_HOST", "0.0.0.0")
    port = int(os.environ.get("TQ_LOGVIEW_PORT", "8088"))
    app.run(host=host, port=port, debug=False)


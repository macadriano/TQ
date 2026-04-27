from __future__ import annotations

import csv
import os
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from flask import Flask, abort, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = BASE_DIR / "REENVIOS_CONFIG.txt"

if str(BASE_DIR) not in sys.path:
    # Permite importar módulos del repo al ejecutar como script:
    #   .venv\Scripts\python reenvios_abm\app.py
    sys.path.insert(0, str(BASE_DIR))

from reenvios_config import ForwardingRule, load_reenvios_config  # noqa: E402


def _get_config_path() -> Path:
    raw = os.environ.get("TQ_REENVIOS_CONFIG_PATH", "").strip()
    return Path(raw).expanduser().resolve() if raw else DEFAULT_CONFIG_PATH.resolve()


def _get_config_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0


@dataclass
class RuleForm:
    tipo: str = "CLONAR"
    cliente: str = ""
    equipo: str = ""
    transporte: str = "UDP"
    protocolo_gps: str = "GEO5"
    ip: str = ""
    puerto: str = ""
    formato_id: str = ""
    fecha_alta: str = ""


def _normalize_proto(raw: str) -> str:
    u = (raw or "").strip().upper()
    return "GEO5" if u in ("GEO", "GEO5") else u


def _validate_rule(form: RuleForm) -> List[str]:
    errs: List[str] = []

    tipo = (form.tipo or "").strip().upper()
    if tipo not in ("SERVICIO", "CLONAR"):
        errs.append("TIPO debe ser SERVICIO o CLONAR.")

    eq = (form.equipo or "").strip()
    if not (eq.isdigit() and len(eq) == 5):
        errs.append("EQUIPO debe ser un ID de 5 dígitos.")

    tr = (form.transporte or "").strip().upper()
    if tr not in ("UDP", "TCP"):
        errs.append("TRANSPORTE debe ser UDP o TCP.")

    proto = _normalize_proto(form.protocolo_gps)
    if proto not in ("GEO5", "TQ"):
        errs.append("PROTOCOLO_GPS debe ser GEO5 (o GEO) o TQ.")

    ip = (form.ip or "").strip()
    # validación real la hace load_reenvios_config; acá solo chequeo mínimo
    if not ip:
        errs.append("IP es obligatoria.")

    port_s = (form.puerto or "").strip()
    try:
        port = int(port_s)
    except Exception:
        errs.append("PUERTO debe ser numérico.")
    else:
        if not (1 <= port <= 65535):
            errs.append("PUERTO fuera de rango (1-65535).")

    fmt_s = (form.formato_id or "").strip()
    if fmt_s:
        try:
            n = int(fmt_s)
        except Exception:
            errs.append("FORMATO_ID debe ser numérico (1-32) o vacío.")
        else:
            if not (1 <= n <= 32):
                errs.append("FORMATO_ID fuera de rango (1-32).")

    # regla funcional: FORMATO_ID solo aplica a UDP+GEO5; si no aplica, lo forzamos vacío
    if fmt_s and not (tr == "UDP" and proto == "GEO5"):
        errs.append("FORMATO_ID solo aplica a TRANSPORTE=UDP y PROTOCOLO_GPS=GEO5.")

    fecha_s = (form.fecha_alta or "").strip()
    if fecha_s:
        ok = False
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                datetime.strptime(fecha_s, fmt)
                ok = True
                break
            except Exception:
                continue
        if not ok:
            errs.append("FECHA_ALTA inválida. Usar DD/MM/YYYY (o seleccionar desde el calendario).")

    return errs


def _normalize_fecha_for_storage(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%d/%m/%Y")
        except Exception:
            continue
    return ""


def _normalize_fecha_for_form(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return ""


def _clients_for_equipo(rules: List[ForwardingRule], equipo: str) -> List[str]:
    eq = (equipo or "").strip()
    if not eq:
        return []
    clients = []
    for r in rules:
        if r.equipo == eq:
            c = (r.cliente or "-").strip() or "-"
            clients.append(c)
    # únicos, ordenados
    return sorted(set(clients), key=lambda x: x.lower())


def _clients_for_equipo_servicio(rules: List[ForwardingRule], equipo: str) -> List[str]:
    eq = (equipo or "").strip()
    if not eq:
        return []
    clients = []
    for r in rules:
        if r.equipo == eq and r.tipo == "SERVICIO":
            c = (r.cliente or "-").strip() or "-"
            clients.append(c)
    return sorted(set(clients), key=lambda x: x.lower())


def _read_rules(path: Path) -> Tuple[List[ForwardingRule], List[str]]:
    by_equipo, warnings = load_reenvios_config(str(path))
    rules: List[ForwardingRule] = []
    for eq, rs in by_equipo.items():
        rules.extend(rs)
    # orden estable para UI
    rules.sort(key=lambda r: (r.equipo, r.tipo, r.cliente, r.protocolo_gps, r.transporte, r.ip, r.port))
    return rules, warnings


def _write_rules_atomic(path: Path, rules: List[ForwardingRule]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    # backup si existe
    if path.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = path.with_name(f"{path.name}.{ts}.bak")
        shutil.copy2(path, backup)

    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        header = ["TIPO", "CLIENTE", "EQUIPO", "TRANSPORTE", "PROTOCOLO_GPS", "IP", "PUERTO", "FORMATO_ID", "FECHA_ALTA"]
        writer.writerow(header)
        for r in rules:
            writer.writerow(
                [
                    r.tipo,
                    r.cliente,
                    r.equipo,
                    r.transporte,
                    r.protocolo_gps,
                    r.ip,
                    str(r.port),
                    "" if r.formato_id is None else str(r.formato_id),
                    "" if getattr(r, "fecha_alta", None) is None else str(r.fecha_alta),
                ]
            )

    os.replace(tmp, path)


def _form_from_request() -> RuleForm:
    return RuleForm(
        tipo=(request.form.get("tipo") or "").strip().upper() or "CLONAR",
        cliente=(request.form.get("cliente") or "").strip(),
        equipo=(request.form.get("equipo") or "").strip(),
        transporte=(request.form.get("transporte") or "").strip().upper() or "UDP",
        protocolo_gps=_normalize_proto(request.form.get("protocolo_gps") or "GEO5"),
        ip=(request.form.get("ip") or "").strip(),
        puerto=(request.form.get("puerto") or "").strip(),
        formato_id=(request.form.get("formato_id") or "").strip(),
        fecha_alta=(request.form.get("fecha_alta") or "").strip(),
    )


def _form_from_rule(r: ForwardingRule) -> RuleForm:
    return RuleForm(
        tipo=r.tipo,
        cliente=r.cliente,
        equipo=r.equipo,
        transporte=r.transporte,
        protocolo_gps=r.protocolo_gps,
        ip=r.ip,
        puerto=str(r.port),
        formato_id="" if r.formato_id is None else str(r.formato_id),
        fecha_alta=_normalize_fecha_for_form(getattr(r, "fecha_alta", "") or ""),
    )


app = Flask(__name__)
app.secret_key = os.environ.get("TQ_ABM_SECRET", "dev-secret-change-me")


@app.get("/health")
def health():
    return "ok"


@app.get("/")
def home():
    return redirect(url_for("rules_list"))


@app.get("/rules")
def rules_list():
    path = _get_config_path()
    rules, warnings = _read_rules(path)
    indexed = list(enumerate(rules))
    total_rules = len(rules)

    q = (request.args.get("q") or "").strip().lower()
    if q:
        def match(r: ForwardingRule) -> bool:
            blob = " ".join([r.tipo, r.cliente, r.equipo, r.transporte, r.protocolo_gps, r.ip, str(r.port)]).lower()
            return q in blob

        indexed = [(i, r) for (i, r) in indexed if match(r)]

    mtime = _get_config_mtime(path)
    return render_template(
        "rules_list.html",
        config_path=str(path),
        config_mtime=mtime,
        indexed_rules=indexed,
        total_rules=total_rules,
        shown_rules=len(indexed),
        warnings=warnings,
        q=q,
    )


@app.get("/rules/new")
def rules_new():
    path = _get_config_path()
    mtime = _get_config_mtime(path)
    form = RuleForm()
    return render_template("rule_form.html", mode="new", form=form, idx=None, config_path=str(path), config_mtime=mtime)


@app.post("/rules/new")
def rules_create():
    path = _get_config_path()
    expected_mtime = float(request.form.get("config_mtime") or "0")
    current_mtime = _get_config_mtime(path)
    if expected_mtime and current_mtime and expected_mtime != current_mtime:
        flash("El archivo cambió en disco. Volvé a cargar y reintentá.", "error")
        return redirect(url_for("rules_list"))

    form = _form_from_request()
    errs = _validate_rule(form)
    if errs:
        for e in errs:
            flash(e, "error")
        return render_template("rule_form.html", mode="new", form=form, idx=None, config_path=str(path), config_mtime=current_mtime), 400

    rules, warnings = _read_rules(path)
    for w in warnings:
        flash(w, "warning")

    # Regla de negocio: permitir repetidos para CLONAR, pero no permitir más de un SERVICIO por equipo.
    if form.tipo == "SERVICIO":
        existing_clients = _clients_for_equipo_servicio(rules, form.equipo)
        if existing_clients:
            flash(
                f"El equipo {form.equipo} ya tiene una regla SERVICIO (cliente(s): {', '.join(existing_clients)}).",
                "error",
            )
            return render_template(
                "rule_form.html",
                mode="new",
                form=form,
                idx=None,
                config_path=str(path),
                config_mtime=current_mtime,
            ), 400
    else:
        # CLONAR: avisar si el equipo ya existe, pero no bloquear
        existing_clients_any = _clients_for_equipo(rules, form.equipo)
        if existing_clients_any:
            flash(
                f"Aviso: el equipo {form.equipo} ya tiene reglas cargadas (cliente(s): {', '.join(existing_clients_any)}).",
                "warning",
            )

    new_rule = ForwardingRule(
        tipo=form.tipo,
        cliente=form.cliente,
        equipo=form.equipo,
        transporte=form.transporte,
        protocolo_gps=_normalize_proto(form.protocolo_gps),
        ip=form.ip,
        port=int(form.puerto),
        line_no=0,
        formato_id=(int(form.formato_id) if form.formato_id else None),
        fecha_alta=(_normalize_fecha_for_storage(form.fecha_alta) or None),
    )
    rules.append(new_rule)
    rules.sort(key=lambda r: (r.equipo, r.tipo, r.cliente, r.protocolo_gps, r.transporte, r.ip, r.port))
    _write_rules_atomic(path, rules)
    flash("Regla creada.", "success")
    return redirect(url_for("rules_list"))


@app.get("/rules/<int:idx>/edit")
def rules_edit(idx: int):
    path = _get_config_path()
    rules, warnings = _read_rules(path)
    if idx < 0 or idx >= len(rules):
        abort(404)
    for w in warnings:
        flash(w, "warning")
    mtime = _get_config_mtime(path)
    form = _form_from_rule(rules[idx])
    return render_template("rule_form.html", mode="edit", form=form, idx=idx, config_path=str(path), config_mtime=mtime)


@app.post("/rules/<int:idx>/edit")
def rules_update(idx: int):
    path = _get_config_path()
    expected_mtime = float(request.form.get("config_mtime") or "0")
    current_mtime = _get_config_mtime(path)
    if expected_mtime and current_mtime and expected_mtime != current_mtime:
        flash("El archivo cambió en disco. Volvé a cargar y reintentá.", "error")
        return redirect(url_for("rules_list"))

    rules, warnings = _read_rules(path)
    if idx < 0 or idx >= len(rules):
        abort(404)
    for w in warnings:
        flash(w, "warning")

    form = _form_from_request()
    errs = _validate_rule(form)
    if errs:
        for e in errs:
            flash(e, "error")
        return render_template("rule_form.html", mode="edit", form=form, idx=idx, config_path=str(path), config_mtime=current_mtime), 400

    # Regla de negocio: permitir repetidos para CLONAR, pero no permitir más de un SERVICIO por equipo.
    other_rules = [r for i, r in enumerate(rules) if i != idx]
    if form.tipo == "SERVICIO":
        existing_clients = _clients_for_equipo_servicio(other_rules, form.equipo)
        if existing_clients:
            flash(
                f"El equipo {form.equipo} ya tiene otra regla SERVICIO (cliente(s): {', '.join(existing_clients)}).",
                "error",
            )
            return render_template(
                "rule_form.html",
                mode="edit",
                form=form,
                idx=idx,
                config_path=str(path),
                config_mtime=current_mtime,
            ), 400
    else:
        # CLONAR: avisar si el equipo ya existe, pero no bloquear
        existing_clients_any = _clients_for_equipo(other_rules, form.equipo)
        if existing_clients_any:
            flash(
                f"Aviso: el equipo {form.equipo} ya tiene otras reglas cargadas (cliente(s): {', '.join(existing_clients_any)}).",
                "warning",
            )

    rules[idx] = ForwardingRule(
        tipo=form.tipo,
        cliente=form.cliente,
        equipo=form.equipo,
        transporte=form.transporte,
        protocolo_gps=_normalize_proto(form.protocolo_gps),
        ip=form.ip,
        port=int(form.puerto),
        line_no=0,
        formato_id=(int(form.formato_id) if form.formato_id else None),
        fecha_alta=(_normalize_fecha_for_storage(form.fecha_alta) or None),
    )
    rules.sort(key=lambda r: (r.equipo, r.tipo, r.cliente, r.protocolo_gps, r.transporte, r.ip, r.port))
    _write_rules_atomic(path, rules)
    flash("Regla actualizada.", "success")
    return redirect(url_for("rules_list"))


@app.post("/rules/<int:idx>/delete")
def rules_delete(idx: int):
    path = _get_config_path()
    expected_mtime = float(request.form.get("config_mtime") or "0")
    current_mtime = _get_config_mtime(path)
    if expected_mtime and current_mtime and expected_mtime != current_mtime:
        flash("El archivo cambió en disco. Volvé a cargar y reintentá.", "error")
        return redirect(url_for("rules_list"))

    rules, warnings = _read_rules(path)
    if idx < 0 or idx >= len(rules):
        abort(404)
    for w in warnings:
        flash(w, "warning")

    removed = rules.pop(idx)
    _write_rules_atomic(path, rules)
    flash(f"Regla eliminada ({removed.equipo} {removed.ip}:{removed.port}).", "success")
    return redirect(url_for("rules_list"))


@app.get("/equipos")
def equipos_list():
    path = _get_config_path()
    rules, warnings = _read_rules(path)
    by_eq: Dict[str, List[ForwardingRule]] = {}
    for r in rules:
        by_eq.setdefault(r.equipo, []).append(r)
    equipos = []
    for eq, rs in sorted(by_eq.items(), key=lambda x: x[0]):
        has_servicio = any(r.tipo == "SERVICIO" for r in rs)
        clientes = sorted({(r.cliente or "-").strip() or "-" for r in rs})
        fechas = []
        for r in rs:
            fa = (getattr(r, "fecha_alta", "") or "").strip()
            if not fa:
                continue
            try:
                fechas.append(datetime.strptime(fa, "%d/%m/%Y"))
            except Exception:
                pass
        fecha_alta = min(fechas).strftime("%d/%m/%Y") if fechas else "-"
        equipos.append(
            {"equipo": eq, "count": len(rs), "has_servicio": has_servicio, "clientes": clientes, "fecha_alta": fecha_alta}
        )
    return render_template(
        "equipos.html",
        config_path=str(path),
        equipos=equipos,
        warnings=warnings,
        total_equipos=len(equipos),
        total_rules=len(rules),
    )


@app.get("/clientes")
def clientes_list():
    path = _get_config_path()
    rules, warnings = _read_rules(path)
    by_cliente: Dict[str, List[ForwardingRule]] = {}
    for r in rules:
        c = (r.cliente or "-").strip() or "-"
        by_cliente.setdefault(c, []).append(r)
    clientes = []
    for c, rs in sorted(by_cliente.items(), key=lambda x: x[0].lower()):
        equipos = sorted({r.equipo for r in rs})
        clientes.append({"cliente": c, "count": len(rs), "equipos": equipos, "equipos_count": len(equipos)})
    total_clientes = len(clientes)
    total_equipos = len({r.equipo for r in rules})
    return render_template(
        "clientes.html",
        config_path=str(path),
        clientes=clientes,
        warnings=warnings,
        total_clientes=total_clientes,
        total_equipos=total_equipos,
    )


if __name__ == "__main__":
    host = os.environ.get("TQ_ABM_HOST", "127.0.0.1")
    port = int(os.environ.get("TQ_ABM_PORT", "8090"))
    # para dev local
    app.run(host=host, port=port, debug=True)


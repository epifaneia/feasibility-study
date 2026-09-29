"""feasibility-study — servidor del formulario de diagnóstico (FastAPI).

El formulario se envía, el lead se guarda en leads/<fecha>_<empresa>/ y el informe
se genera en background con el deep research por API (de pago): research →
extracción → derivación → PDF. El PDF NO se envía solo: se revisa (qa.txt,
derivacion.json, extraccion.json → regenerar.py) y se manda a mano.

Custodia (docs/INTEGRATION.md): el servidor no arranca sin CUSTODIA_ACTOR; cada
llamada a un modelo queda en el ledger (CUSTODIA_LEDGER); el PDF se firma con
tools/signoff.py antes de enviarlo.

Arranque:  python app.py    →  http://127.0.0.1:8091
"""
from __future__ import annotations

import os
import re
import threading
import traceback
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from src import formulario, informe, research

BASE = Path(__file__).resolve().parent
LEADS = BASE / "leads"

app = FastAPI(title="feasibility-study", docs_url=None, redoc_url=None)


@app.on_event("startup")
def _custodia_identidad() -> None:
    """Cable 1 también si se arranca con `uvicorn app:app`: sin actor con nombre, no arranca."""
    from custodia.identity import require_actor
    require_actor()   # MissingActor aborta el arranque


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:40] or "empresa"


def _validar(payload: formulario.EmpresaForm) -> None:
    if not payload.contacto_email.strip() or not payload.descripcion.strip() \
            or not payload.nombre_empresa.strip() or not payload.cuello_botella.strip():
        raise HTTPException(400, "Faltan campos obligatorios.")


def _guardar_lead(payload: formulario.EmpresaForm) -> "tuple[Path, str]":
    """Carpeta del lead con form.json y brief.txt. Devuelve (carpeta, brief)."""
    brief = formulario.construir_brief(payload)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    carpeta = LEADS / f"{ts}_{_slug(payload.nombre_empresa)}"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "form.json").write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    (carpeta / "brief.txt").write_text(brief, encoding="utf-8")
    print(f"📥 Lead: {payload.nombre_empresa} <{payload.contacto_email}> → {carpeta}")
    return carpeta, brief


# ------------------------------------------------------------------ envío ----

@app.post("/api/enviar")
def enviar(payload: formulario.EmpresaForm):
    _validar(payload)
    carpeta, _ = _guardar_lead(payload)
    # El informe (research → PDF) corre en background: tarda minutos.
    threading.Thread(target=_generar_informe, args=(payload, carpeta), daemon=True).start()
    return {"ok": True, "carpeta": str(carpeta)}


def _generar_informe(payload: formulario.EmpresaForm, carpeta: Path) -> None:
    try:
        ruta = informe.generar(payload, carpeta)
        print(f"✅ Informe listo: {ruta}  (revísalo con qa.txt antes de enviarlo)")
    except Exception:  # noqa: BLE001
        print("❌ Error generando el informe:\n" + traceback.format_exc())
        print(f"   Si informe.md existe: python regenerar.py \"{carpeta}\" --desde md")


# ------------------------------------------------- panel del consultor -------

def _carpeta_lead(ref: str) -> Path:
    """Acepta el nombre de la carpeta (panel) o la ruta absoluta (formulario)."""
    c = Path(ref)
    if not c.is_absolute():
        c = LEADS / c.name
    if LEADS not in c.parents or not (c / "form.json").exists():
        raise HTTPException(400, "Carpeta de lead no válida.")
    return c


@app.get("/api/leads")
def listar_leads():
    out = []
    for c in sorted((c for c in LEADS.glob("*") if c.is_dir()), key=lambda c: c.stat().st_mtime, reverse=True):
        if not (c / "form.json").exists():
            continue
        try:
            form = formulario.EmpresaForm.model_validate_json((c / "form.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        fecha = c.name[:15]
        fecha = f"{fecha[6:8]}/{fecha[4:6]}/{fecha[0:4]} {fecha[9:11]}:{fecha[11:13]}" if len(fecha) == 15 else c.name
        qa = (c / "qa.txt").read_text(encoding="utf-8") if (c / "qa.txt").exists() else ""
        out.append({"id": c.name, "empresa": form.nombre_empresa, "contacto": form.contacto_nombre,
                    "fecha": fecha, "prompt": (c / "prompt.txt").exists(),
                    "md": (c / "informe.md").exists(), "pdf": (c / "informe.pdf").exists(),
                    "anexo": (c / "anexo_fuentes.pdf").exists(), "qa": qa})
    return out


@app.get("/api/leads/{lead}/prompt", response_class=PlainTextResponse)
def prompt_lead(lead: str):
    """El prompt enviado al deep research (para revisarlo o reutilizarlo)."""
    c = _carpeta_lead(lead)
    p = c / "prompt.txt"
    if not p.exists():                       # leads antiguos: se reconstruye del form
        form = formulario.EmpresaForm.model_validate_json((c / "form.json").read_text(encoding="utf-8"))
        p.write_text(research.construir_prompt(formulario.construir_brief(form)), encoding="utf-8")
    return p.read_text(encoding="utf-8")


_ARCHIVOS = {"informe.pdf": "application/pdf", "anexo_fuentes.pdf": "application/pdf",
             "informe.md": "text/markdown", "qa.txt": "text/plain"}


@app.get("/api/leads/{lead}/archivo/{nombre}")
def archivo_lead(lead: str, nombre: str):
    c = _carpeta_lead(lead)
    if nombre not in _ARCHIVOS or not (c / nombre).exists():
        raise HTTPException(404, "No existe.")
    return FileResponse(c / nombre, media_type=_ARCHIVOS[nombre], filename=nombre)


@app.get("/panel", response_class=HTMLResponse)
def panel():
    return (BASE / "static" / "panel.html").read_text(encoding="utf-8")


# ------------------------------------------------------------------ estático --

@app.get("/", response_class=HTMLResponse)
def index():
    return (BASE / "static" / "index.html").read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


if __name__ == "__main__":
    # --- cable 1: identidad. El servidor no corre de forma anónima. ---
    from custodia.identity import require_actor, MissingActor
    try:
        actor = require_actor()
    except MissingActor as e:
        print(f"app: {e}")
        raise SystemExit(2)
    print(f"app: actor {actor}")

    import uvicorn

    port = int(os.environ.get("PORT", "8091"))
    print(f"feasibility-study → http://127.0.0.1:{port}   "
          f"(panel del consultor: http://127.0.0.1:{port}/panel)")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

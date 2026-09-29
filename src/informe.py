"""Orquestador del informe: brief → research → extracción → derivación →
longitud → relleno → PDF. Guarda todo en la carpeta del lead (informe.md,
derivacion.json para auditar el ranking, informe.html e informe.pdf).
"""

import json
import os
from pathlib import Path

from src import anexo, derivacion, extraccion, formulario, longitud, pdf, relleno, research


ORDEN_TIPO = {"institucional": 0, "académica": 1, "academica": 1, "prensa": 2, "proveedor": 3}
MAX_FUENTES = 10


def _fmt_fuente(f: extraccion.Fuente) -> str:
    yr = f" <span class='yr'>({f.anio})</span>" if f.anio else ""
    desc = f". {f.descripcion}" if f.descripcion else ""
    return f"<b>{f.autor}.</b> {f.titulo}{yr}{desc}"


def _fuentes_ordenadas(fuentes: "list[extraccion.Fuente]") -> "list[extraccion.Fuente]":
    """Institucionales y académicas primero; las de proveedor al final. Orden estable."""
    return sorted(fuentes, key=lambda f: ORDEN_TIPO.get((f.tipo or "").strip().lower(), 2))[:MAX_FUENTES]


def _punto_partida(form: formulario.EmpresaForm) -> str:
    """Página 4: lo que la empresa ya hace y la carga actual, del formulario."""
    partes = []
    if form.horas_semana.strip():
        quien = f" entre {form.personas_tarea.strip()} personas" if form.personas_tarea.strip() else ""
        partes.append(f"Hoy la tarea consume unas {form.horas_semana.strip().replace('unas ', '')} horas a la semana{quien}.")
    if form.intentos_previos.strip():
        partes.append(form.intentos_previos.strip().rstrip(".") + ".")
    if form.entrada_formato:
        fmts = list(form.entrada_formato)
        partes.append("La información llega en " + (", ".join(fmts[:-1]) + " y " + fmts[-1] if len(fmts) > 1 else fmts[0]) + ".")
    return " ".join(partes) or "Partís de una operativa ya digital, con la información dispersa entre sistemas."


def _contacto() -> dict:
    """Contacto del consultor para el bloque 'Siguiente paso' (variables de entorno)."""
    return {k: v for k, v in {
        "contacto_nombre": os.environ.get("CONTACTO_NOMBRE", "").strip(),
        "contacto_email": os.environ.get("CONTACTO_EMAIL", "").strip(),
        "contacto_tel": os.environ.get("CONTACTO_TEL", "").strip(),
    }.items() if v}


def renderizar(form: formulario.EmpresaForm, datos: extraccion.InformeIA,
               carpeta: "str | Path") -> Path:
    """Datos extraídos → PDF. Separado de generar() para poder probar/iterar sin
    gastar las llamadas de research/extracción."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)

    # Derivación determinista: el código decide ranking, Top 3 y cifras.
    scored = derivacion.ordenar(datos.oportunidades)
    top3 = [op for op, _ in scored[:3]]
    nivel = derivacion.nivel_potencial(datos.potencial_nivel)
    pct_adopcion = derivacion.adopcion_pct_valido(datos.adopcion_pct)
    resumen = derivacion.resumen(datos)
    (carpeta / "derivacion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    # Avisos para la revisión humana antes de enviar (qa.txt + consola).
    lineas = resumen["avisos"] or ["Sin avisos automáticos. Revisa igualmente el PDF página a página."]
    (carpeta / "qa.txt").write_text("\n".join(f"- {a}" for a in lineas), encoding="utf-8")
    for a in resumen["avisos"]:
        print(f"⚠️  QA: {a}")

    matriz = [
        {"nombre": op.nombre, "descripcion": op.descripcion, "roi": op.roi,
         "viabilidad": op.viabilidad, "prioridad": p, "top": i < 3, "via": op.via}
        for i, (op, p) in enumerate(scored)
    ]

    textos = {
        "nombre_empresa": form.nombre_empresa,
        "sector": datos.sector,
        "potencial_nivel": f"Nivel {nivel}",
        "potencial_adjetivo": derivacion.potencial_adjetivo(nivel),
        "potencial_razones": datos.potencial_razones,
        "retorno_pct": str(derivacion.retorno_pct(top3)),
        "retorno_categoria": datos.retorno_categoria,
        "retorno_desc": datos.retorno_desc,
        "adopcion_pct": str(pct_adopcion),
        "adopcion_binaria": derivacion.frase_adopcion(pct_adopcion),
        "req_infra": datos.req_infra,
        "req_datos": datos.req_datos,
        "req_adopcion": datos.req_adopcion,
        **_contacto(),
    }
    if datos.ficha_fuentes.strip():
        textos["perfil_fuentes"] = datos.ficha_fuentes
    # Cumplimiento modulado por restricciones; si la extracción no lo trae,
    # el texto estándar de la plantilla se queda como está.
    for k in ("cump_aislamiento", "cump_normativa", "cump_trazabilidad"):
        v = getattr(datos, k, "").strip()
        if v:
            textos[k] = v
    for i, cond in enumerate(datos.condiciones[:3], start=1):
        textos[f"cond{i}_lbl"] = cond.titulo
        textos[f"cond{i}_desc"] = cond.descripcion
    for i, op in enumerate(top3, start=1):
        textos[f"mapeo{i}_nombre"] = op.nombre
        textos[f"mapeo{i}_problema"] = op.problema
        if op.horas_mes.strip():
            textos[f"mapeo{i}_horas"] = op.horas_mes.strip()
            if op.horas_base.strip():
                textos[f"mapeo{i}_horas_base"] = "Base: " + op.horas_base.strip()
    textos["punto_partida"] = getattr(datos, "punto_partida", "").strip() or _punto_partida(form)
    if getattr(datos, "camino_intro", "").strip():
        textos["camino_intro"] = datos.camino_intro.strip()
    if getattr(datos, "no_basta", "").strip():
        textos["no_basta"] = datos.no_basta.strip()
    for i, fr in enumerate(list(getattr(datos, "llega", []) or [])[:3], start=1):
        if fr.strip():
            textos[f"llega{i}"] = fr.strip()
    for i, lim in enumerate(list(getattr(datos, "limites", []) or [])[:4], start=1):
        if lim.titulo.strip():
            textos[f"limite{i}_t"] = lim.titulo.strip()
            textos[f"limite{i}_h"] = lim.herramienta.strip()
            textos[f"limite{i}_m"] = lim.a_medida.strip()
    for i, paso in enumerate(list(getattr(datos, "construccion", []) or [])[:5], start=1):
        if paso.strip():
            textos[f"construccion{i}"] = paso.strip()
    n_tool = sum(1 for op in datos.oportunidades if "herramienta" in (op.via or "").lower())
    if n_tool:
        num = {1: "una oportunidad", 2: "dos oportunidades", 3: "tres oportunidades", 4: "cuatro oportunidades"}.get(n_tool, f"{n_tool} oportunidades")
        verbo = "se resuelve" if n_tool == 1 else "se resuelven"
        textos["ambar_puente"] = (f"Y no todo requiere desarrollo: {num} de la matriz {verbo} hoy con herramientas "
                                  f"que ya existen, sin construir nada. {'Va' if n_tool == 1 else 'Van'} en ámbar.")
    plan = list(getattr(datos, "plan", []) or [])[:3]
    for i, paso in enumerate(plan, start=1):
        for k in ("titulo", "plazo", "cubre", "que_es", "desbloquea"):
            v = getattr(paso, k, "").strip()
            if v:
                textos[f"paso{i}_{'que' if k == 'que_es' else k}"] = v
        if paso.titulo.strip():
            textos[f"rq_paso{i}"] = paso.titulo.strip()
        for k in ("req_infra", "req_datos", "req_adopcion"):
            v = getattr(paso, k, "").strip()
            if v:
                textos[f"req_p{i}_{k[4:]}"] = v

    textos = longitud.ajustar_todos(textos)   # Qwen acota lo que se pase de largo

    # Las tres mejores de vía "herramienta existente" fuera del Top 3: página "lo que se puede abordar ya".
    tool3 = [op for op, _ in scored[3:] if "herramienta" in (op.via or "").lower()][:3]
    for i, op in enumerate(tool3, start=1):
        textos[f"mapeoT{i}_nombre"] = op.nombre
        textos[f"mapeoT{i}_problema"] = op.problema
        if op.horas_mes.strip():
            textos[f"mapeoT{i}_horas"] = op.horas_mes.strip()
            if op.horas_base.strip():
                textos[f"mapeoT{i}_horas_base"] = "Base: " + op.horas_base.strip()
    if any(k.endswith("_horas") for k in textos):
        textos["horas_nota"] = ("* Estimaciones a partir de la información de la reunión combinada con los ahorros "
                                "documentados en las fuentes del anexo. Donde no hay dato de la reunión se indica el "
                                "promedio publicado y el supuesto de volumen empleado; corregidlo con vuestras cifras "
                                "y la estimación se ajusta en proporción.")
    necesita = {i: op.necesita[:3] for i, op in enumerate(top3, start=1)}
    necesita.update({f"T{i}": op.necesita[:3] for i, op in enumerate(tool3, start=1)})
    fuentes_html = [_fmt_fuente(f) for f in _fuentes_ordenadas(datos.fuentes)]

    html = relleno.rellenar(textos, matriz, necesita, fuentes_html,
                            nivel=nivel, adopcion_pct=pct_adopcion,
                            perfil=datos.ficha_bullets[:6])
    (carpeta / "informe.html").write_text(html, encoding="utf-8")
    return pdf.html_a_pdf(html, carpeta / "informe.pdf")


def generar(form: formulario.EmpresaForm, carpeta: "str | Path",
            informe_md: "str | None" = None) -> Path:
    """Genera el PDF del informe. Si `informe_md` se pasa, reusa ese research
    (para iterar sin gastar la llamada cara)."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    brief = formulario.construir_brief(form)

    if informe_md is None:
        prompt = research.construir_prompt(brief)
        (carpeta / "prompt.txt").write_text(prompt, encoding="utf-8")   # lo que se envió al research
        informe_md = research.lanzar_research(prompt)
    (carpeta / "informe.md").write_text(informe_md, encoding="utf-8")

    # Anexo de fuentes (documento aparte, para dar peso): si falla, no rompe nada.
    try:
        ruta_anexo = anexo.generar(informe_md, carpeta, nombre_empresa=form.nombre_empresa)
        if ruta_anexo:
            print(f"📎 Anexo de fuentes: {ruta_anexo}")
    except Exception as exc:  # noqa: BLE001
        print(f"anexo: falló ({exc}); el informe sigue sin anexo.")

    datos = extraccion.extraer(informe_md, brief)
    (carpeta / "extraccion.json").write_text(datos.model_dump_json(indent=2), encoding="utf-8")
    return renderizar(form, datos, carpeta)

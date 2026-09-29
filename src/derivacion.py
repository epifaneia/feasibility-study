"""Derivación DETERMINISTA v2: prioridad, Top 3, retorno, adopción y potencial.

Filosofía: el LLM aporta las notas base (ROI, Viabilidad, % reducción, % adopción,
nivel de potencial); aquí se calcula TODO lo que no debe variar entre informes ni
contradecirse. El código es la fuente de verdad del ranking: recalcula la Prioridad
y reordena, ignore lo que ordenó el research.
"""

import math

from src.extraccion import InformeIA, Oportunidad

# --- Prioridad y ranking ----------------------------------------------------


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def prioridad(roi: float, viabilidad: float) -> float:
    """√(ROI × Viabilidad), todo en 0-10. Media geométrica: castiga el
    desequilibrio — (10,2)→4.5 pierde contra (7,8)→7.5."""
    r = _clamp(roi, 0, 10)
    v = _clamp(viabilidad, 0, 10)
    return round(math.sqrt(r * v), 1)


def ordenar(oportunidades: "list[Oportunidad]") -> "list[tuple[Oportunidad, float]]":
    """Cartera ordenada por Prioridad descendente (orden estable: a igualdad,
    conserva el orden del informe). Las 3 primeras son el Top 3."""
    scored = [(op, prioridad(op.roi, op.viabilidad)) for op in oportunidades]
    return sorted(scored, key=lambda t: -t[1])


# --- Retorno sobre la mesa (Capa 1) ------------------------------------------


def retorno_pct(top3: "list[Oportunidad]") -> int:
    """% de reducción de tiempo del resumen ejecutivo: MEDIA de los puntos medios
    de los rangos del Top 3 (acordado: creíble > vendedor). Solo cuentan las tareas
    que la empresa YA realiza (una actividad nueva no "reduce" nada); si ninguna
    lo es, se promedian todas para no dejar el hueco vacío."""
    actuales = [op for op in top3 if getattr(op, "tarea_actual", True)]
    top3 = actuales or top3
    if not top3:
        return 0
    medios = []
    for op in top3:
        rmin = _clamp(op.reduccion_min, 0, 100)
        rmax = _clamp(op.reduccion_max, 0, 100)
        if rmin > rmax:
            rmin, rmax = rmax, rmin
        medios.append((rmin + rmax) / 2)
    return round(sum(medios) / len(medios))


# --- Potencial de oportunidad (Capa 1) ----------------------------------------

ADJETIVOS = {1: "Incipiente", 2: "Moderado", 3: "Notable", 4: "Alto", 5: "Excepcional"}


def nivel_potencial(nivel: int) -> int:
    return int(_clamp(nivel, 1, 5))


def potencial_adjetivo(nivel: int) -> str:
    return ADJETIVOS[nivel_potencial(nivel)]


# --- Estado del sector (Capa 2: donut + frase binaria) -------------------------

FRASE_ADOPCION_ALTA = "El sector ya se mueve. No te quedes atrás."
FRASE_ADOPCION_BAJA = "Aún puedes ser de los primeros."


def adopcion_pct_valido(pct: int) -> int:
    return round(_clamp(pct, 0, 100))


def frase_adopcion(pct: int) -> str:
    return FRASE_ADOPCION_ALTA if adopcion_pct_valido(pct) >= 50 else FRASE_ADOPCION_BAJA


def donut_css(pct: int) -> str:
    """Estilo del pie chart del sector (conic-gradient de la plantilla)."""
    p = adopcion_pct_valido(pct)
    return f"background:conic-gradient(var(--green) 0 {p}%, #d7ddc9 {p}% 100%)"


# --- Avisos de QA (para la revisión manual antes de enviar) --------------------

PALABRAS_PROHIBIDAS = ("brief", "formulario", "cuestionario", "prompt")


def avisos(datos: InformeIA) -> "list[str]":
    """Lo que un revisor humano debe mirar antes de enviar el PDF. No bloquea."""
    scored = ordenar(datos.oportunidades)
    top3 = [op for op, _ in scored[:3]]
    out = []
    if not any(getattr(op, "aborda_cuello_botella", False) for op in top3):
        out.append("El Top 3 NO contiene el cuello de botella declarado: comprueba que el "
                   "informe explica por qué (o corrige la extracción).")
    nuevas = [op.nombre for op in top3 if not getattr(op, "tarea_actual", True)]
    if nuevas:
        out.append("Actividades nuevas en el Top 3 (no cuentan en el % de retorno): "
                   + ", ".join(nuevas))
    pct = retorno_pct(top3)
    if pct >= 60:
        out.append(f"Retorno {pct}%: muy alto para un director escéptico; revisa los rangos.")
    if len(datos.oportunidades) < 6:
        out.append(f"Solo {len(datos.oportunidades)} oportunidades (se esperaban 6-8).")
    if len(datos.condiciones) != 3:
        out.append(f"{len(datos.condiciones)} condiciones (se esperaban 3).")
    prov = [f for f in datos.fuentes if (f.tipo or "").lower().startswith("prov")]
    if datos.fuentes and len(prov) > len(datos.fuentes) / 2:
        out.append(f"{len(prov)} de {len(datos.fuentes)} fuentes son de proveedor: "
                   "credibilidad baja.")
    if not datos.fuentes:
        out.append("Sin fuentes: la página de fuentes saldrá solo con la principal.")
    textos = [datos.ficha_fuentes, datos.potencial_razones, datos.retorno_desc,
              datos.req_infra, datos.req_datos, datos.req_adopcion]
    textos += [c.descripcion for c in datos.condiciones]
    textos += [op.problema + " " + op.descripcion for op in datos.oportunidades]
    for t in textos:
        low = (t or "").lower()
        for w in PALABRAS_PROHIBIDAS:
            if w in low:
                out.append(f"Jerga interna filtrada («{w}»): «{t[:80]}…»")
                break
    return out


# --- Resumen para trazabilidad -------------------------------------------------


def resumen(datos: InformeIA) -> dict:
    """Dict con todo lo derivado (se guarda junto al lead para auditar)."""
    scored = ordenar(datos.oportunidades)
    top3 = [op for op, _ in scored[:3]]
    return {
        "avisos": avisos(datos),
        "ranking": [
            {"nombre": op.nombre, "roi": op.roi, "viabilidad": op.viabilidad, "prioridad": p}
            for op, p in scored
        ],
        "top3": [op.nombre for op in top3],
        "retorno_pct": retorno_pct(top3),
        "potencial_nivel": nivel_potencial(datos.potencial_nivel),
        "potencial_adjetivo": potencial_adjetivo(datos.potencial_nivel),
        "adopcion_pct": adopcion_pct_valido(datos.adopcion_pct),
        "adopcion_frase": frase_adopcion(datos.adopcion_pct),
    }

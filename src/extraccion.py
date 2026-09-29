"""Eslabón [2] — Extracción estructurada (2ª llamada, conocimiento anclado).

Lee el informe del deep research (7 apartados) + el brief y rellena el esquema
InformeIA v2: la cartera de oportunidades con sus notas, el potencial del negocio,
la madurez del mercado, condiciones, requisitos y fuentes.

IMPORTANTE: la extracción NO ordena ni calcula la Prioridad — devuelve ROI y
Viabilidad por oportunidad y el código (derivacion.py) es la fuente de verdad del
ranking, el Top 3 y las cifras derivadas.
"""

import os
from pathlib import Path

from google import genai
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent.parent
PLANTILLA = BASE / "plantillas" / "prompt_extraccion.txt"

MODELO = os.environ.get("GEMINI_MODELO_EXTRACCION", "gemini-3.1-pro-preview")
ENDPOINT = "https://generativelanguage.googleapis.com"   # a donde viaja el informe + brief (nube)
ENGINE_NAME = "gemini"


class Fuente(BaseModel):
    autor: str
    titulo: str
    anio: str = ""
    tipo: str = ""            # institucional · académica · prensa · proveedor
    descripcion: str = ""


class Oportunidad(BaseModel):
    nombre: str               # corto (≤6 palabras) — matriz, Top 3 y mapeo
    descripcion: str          # 1 línea — celda de la matriz
    roi: int                  # 1-10 (tal cual lo justifica el informe)
    viabilidad: int           # 1-10 (con el filtro de apalancamiento aplicado)
    reduccion_min: int        # % reducción de tiempo (precedentes)
    reduccion_max: int
    tarea_actual: bool = True         # False → actividad nueva: no entra en el % de retorno
    aborda_cuello_botella: bool = False
    horas_mes: str = ""               # horas liberadas al mes (rango), si el informe lo da
    horas_base: str = ""              # de dónde sale: dato de la reunión, o promedio publicado + supuesto de volumen
    via: str = ""                     # herramienta existente · formación · a medida
    problema: str             # 2-3 frases — solo se imprime si entra al Top 3
    necesita: "list[str]" = Field(default_factory=list)  # 2-3 ítems del catálogo


class Condicion(BaseModel):
    titulo: str               # etiqueta corta (≤3 palabras) del catálogo
    descripcion: str          # 1-2 frases aterrizadas al caso


class Paso(BaseModel):
    titulo: str = ""          # ≤4 palabras
    plazo: str = ""           # "Semanas" · "4-8 semanas" · "2-4 meses"
    cubre: str = ""           # qué oportunidades cubre (≤14 palabras)
    que_es: str = ""          # en qué consiste (≤18 palabras)
    desbloquea: str = ""      # qué lo desbloquea (≤16 palabras)
    req_infra: str = ""       # requisitos de ese paso (≤18 palabras cada uno)
    req_datos: str = ""
    req_adopcion: str = ""


class Limite(BaseModel):
    titulo: str = ""          # ≤2 palabras: Escala · Formato · Trazabilidad · Uso compartido …
    herramienta: str = ""     # qué pasa con una herramienta existente (≤22 palabras)
    a_medida: str = ""        # qué hace el sistema propio en su lugar (≤22 palabras)


class InformeIA(BaseModel):
    sector: str
    ficha_bullets: "list[str]" = Field(default_factory=list)  # 4-6 viñetas del Perfil detectado
    ficha_fuentes: str = ""   # "web corporativa · LinkedIn · …" o "Perfil inferido de: …"
    potencial_nivel: int      # 1-5, estructural (independiente de la cartera)
    potencial_razones: str    # 2-3 razones sobresalientes
    retorno_categoria: str    # UNA palabra: masivas·repetitivas·voluminosas·rutinarias·recurrentes
    retorno_desc: str         # frase corta que ancla el % a "reducción de tiempo"
    adopcion_pct: int         # 0-100, entero, con fuente en el informe
    oportunidades: "list[Oportunidad]"      # la cartera completa (6-8)
    condiciones: "list[Condicion]"          # exactamente 3
    req_infra: str
    req_datos: str
    req_adopcion: str
    # Cumplimiento, modulado por las RESTRICCIONES declaradas en el brief
    punto_partida: str = ""   # opcional: si viene, sustituye a la frase construida desde el formulario
    camino_intro: str = ""    # una frase: por qué el mayor retorno es a medida y por qué se empieza por lo mínimo
    no_basta: str = ""        # 2-3 frases (≤45 palabras): qué tiene la empresa que ninguna herramienta trae de serie
    llega: "list[str]" = Field(default_factory=list)      # 3 frases: lo que SÍ hace hoy una herramienta existente
    limites: "list[Limite]" = Field(default_factory=list) # 3-4 límites (escala, formato, trazabilidad, uso compartido)
    construccion: "list[str]" = Field(default_factory=list)  # 5 pasos de construcción (≤9 palabras cada uno)
    plan: "list[Paso]" = Field(default_factory=list)   # exactamente 3 pasos (existentes → piloto → producción)
    cump_aislamiento: str = ""
    cump_normativa: str = ""
    cump_trazabilidad: str = ""
    fuentes: "list[Fuente]" = Field(default_factory=list)


def construir_prompt(informe: str, brief: str) -> str:
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    return (
        plantilla
        .replace("{{INFORME}}", informe.strip())
        .replace("{{BRIEF}}", brief.strip())
    )


def extraer(informe: str, brief: str, client: "genai.Client | None" = None) -> InformeIA:
    from custodia.ledger import record_call, is_local
    client = client or genai.Client()
    prompt = construir_prompt(informe, brief)
    # --- cable 2: libro de custodia. Toda llamada al modelo pasa por aquí. ---
    with record_call(step="extraccion", engine=ENGINE_NAME,
                     endpoint=ENDPOINT.split("/")[2] if "//" in ENDPOINT else ENDPOINT,
                     leaves_machine=not is_local(ENDPOINT), payload=prompt) as rec:
        resp = client.models.generate_content(
            model=MODELO,
            contents=prompt,
            config={"response_mime_type": "application/json", "response_schema": InformeIA},
        )
        rec["output_chars"] = len(getattr(resp, "text", "") or "")
    if getattr(resp, "parsed", None) is not None:
        return resp.parsed
    return InformeIA.model_validate_json(resp.text)

"""Eslabón [1] — Deep Research (Interactions API de Gemini, esquema 2.x).

Toma el BRIEF de la empresa (formulario.construir_brief) y lanza un deep research
sobre oportunidades de IA en empresas similares. Devuelve el informe en texto.
"""

import os
import time
from pathlib import Path

from google import genai

BASE = Path(__file__).resolve().parent.parent
PLANTILLA = BASE / "plantillas" / "prompt_research.txt"

MODELO = "deep-research-preview-04-2026"   # "max-preview" = más exhaustivo, más lento
ENDPOINT = "https://generativelanguage.googleapis.com"   # a donde viaja el brief (nube)
ENGINE_NAME = "gemini"
INTERVALO_POLL_S = 30
TIMEOUT_S = int(os.environ.get("RESEARCH_TIMEOUT_S", str(45 * 60)))   # 45 min por defecto
_FALLOS = {"failed", "cancelled", "incomplete", "budget_exceeded"}


def construir_prompt(brief: str) -> str:
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    return plantilla.replace("{{BRIEF}}", brief.strip())


def _es_salida(step) -> bool:
    return getattr(step, "type", None) == "model_output" or type(step).__name__ == "ModelOutputStep"


def _extraer_texto(interaction) -> str:
    """El deep research devuelve el informe en VARIOS ModelOutputStep; hay que
    concatenarlos TODOS. (output_text solo trae el último bloque → truncaba.)"""
    partes = []
    for step in getattr(interaction, "steps", None) or []:
        if not _es_salida(step):
            continue
        for c in getattr(step, "content", None) or []:
            t = getattr(c, "text", None)
            if t:
                partes.append(t)
    if partes:
        return "\n".join(partes)
    if getattr(interaction, "output_text", None):
        return interaction.output_text
    raise RuntimeError("El research completó pero no devolvió texto.")


def _crear_y_esperar(client, prompt: str) -> str:
    interaction = client.interactions.create(
        input=prompt, agent=MODELO, background=True, store=True,
    )
    print(f"🔍 Research lanzado. ID: {interaction.id}")
    inicio = time.monotonic()
    while True:
        if time.monotonic() - inicio > TIMEOUT_S:
            raise TimeoutError(f"El research {interaction.id} lleva más de {TIMEOUT_S // 60} min; "
                               "abandonado (puedes consultarlo por su ID).")
        interaction = client.interactions.get(interaction.id)
        estado = str(interaction.status)
        print(f"   · estado: {estado}")
        if estado == "completed":
            return _extraer_texto(interaction)
        if estado in _FALLOS:
            raise RuntimeError(f"El research terminó en estado '{estado}'.")
        time.sleep(INTERVALO_POLL_S)


# --- cable 2: libro de custodia. Toda llamada al modelo pasa por aquí. ---
def lanzar_research(prompt: str, client: "genai.Client | None" = None) -> str:
    from custodia.ledger import record_call, is_local
    client = client or genai.Client()
    with record_call(step="research", engine=ENGINE_NAME,
                     endpoint=ENDPOINT.split("/")[2] if "//" in ENDPOINT else ENDPOINT,
                     leaves_machine=not is_local(ENDPOINT), payload=prompt) as rec:
        texto = _crear_y_esperar(client, prompt)
        rec["output_chars"] = len(texto)
        return texto

"""Control de longitud con Qwen local (Ollama).

Comprime un texto SIN perder contenido: reescribe en pasadas de objetivo
decreciente hasta que cabe en el presupuesto de caracteres. Nunca recorta — si tras
los intentos sigue rozando, el shrink-to-fit del PDF remata. Si Qwen falla, devuelve
el texto tal cual (el render no se rompe).
"""

import os

import ollama

MODELO = os.environ.get("QWEN_MODELO", "qwen2.5:7b")
ACTIVO = os.environ.get("LONGITUD_QWEN", "1") not in ("0", "false", "no")
# Mismo host que usa el cliente de ollama (OLLAMA_HOST); por defecto local, nada sale de la máquina.
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").strip()
if "//" not in OLLAMA_URL:
    OLLAMA_URL = "http://" + OLLAMA_URL
ENGINE_NAME = "ollama"
CHARS_POR_PALABRA = 6.2   # proxy español caracteres→palabras
_caido = False            # si Ollama falla una vez, no se insiste en el resto de campos


def _palabras(max_chars: int) -> int:
    return max(8, int(max_chars / CHARS_POR_PALABRA))


def ajustar(texto: str, max_chars: int, intentos: int = 3) -> str:
    """Devuelve el texto dentro de max_chars (o el mejor intento)."""
    global _caido
    texto = (texto or "").strip()
    if len(texto) <= max_chars or not ACTIVO or _caido:
        return texto

    objetivo = _palabras(max_chars)
    actual = texto
    for i in range(intentos):
        target = max(6, int(objetivo * (0.85 ** i)))   # aprieta cada vuelta
        prompt = (
            f"Reescribe el siguiente texto en español en {target} palabras o menos, "
            "conservando lo esencial y el tono profesional. No añadas comillas ni "
            "comentarios: devuelve SOLO el texto reescrito.\n\n"
            f"TEXTO:\n{actual}"
        )
        try:
            # --- cable 2: libro de custodia. Toda llamada al modelo pasa por aquí. ---
            from custodia.ledger import record_call, is_local
            with record_call(step="longitud", engine=ENGINE_NAME,
                             endpoint=OLLAMA_URL.split("/")[2] if "//" in OLLAMA_URL else OLLAMA_URL,
                             leaves_machine=not is_local(OLLAMA_URL), payload=prompt) as rec:
                r = ollama.chat(
                    model=MODELO,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.2},
                )
                nuevo = r["message"]["content"].strip().strip('"').strip()
                rec["output_chars"] = len(nuevo)
        except Exception as exc:  # noqa: BLE001
            _caido = True
            print("longitud: Qwen no disponible; se deja el texto tal cual "
                  "(el shrink-to-fit del PDF remata):", str(exc)[:120])
            return actual
        if nuevo:
            actual = nuevo
            if len(actual) <= max_chars:
                return actual
    return actual  # mejor esfuerzo; el shrink-to-fit del PDF garantiza el encaje


# Presupuestos por campo (caracteres), calibrados a la plantilla v2.
BUDGETS = {
    "potencial_razones": 220,   # ≤32 palabras (tarjeta del potencial)
    "retorno_desc": 150,        # ≤22 palabras (tras "en tareas [categoría] —")
    "cond1_desc": 155,          # ≤22 palabras por condición
    "cond2_desc": 155,
    "cond3_desc": 155,
    "mapeo1_problema": 240,     # ≤35 palabras por tarjeta del Top 3
    "mapeo2_problema": 240,
    "mapeo3_problema": 240,
    "req_infra": 240,           # ≤35 palabras por requisito
    "req_datos": 260,
    "req_adopcion": 260,
    "cump_aislamiento": 155,    # ≤22 palabras por caja de cumplimiento
    "cump_normativa": 155,
    "cump_trazabilidad": 155,
}


def ajustar_todos(textos: dict) -> dict:
    """Aplica el presupuesto a cada campo con presupuesto definido."""
    out = dict(textos)
    for campo, tope in BUDGETS.items():
        if campo in out and isinstance(out[campo], str):
            out[campo] = ajustar(out[campo], tope)
    return out

"""Formulario de la reunión de diagnóstico (modo reunión: el consultor teclea).

Construye el BRIEF que alimenta el deep research, con la jerarquía del modelo mental:
LA EMPRESA es el ancla (explica qué es realista); LA TAREA explica dónde duele; el
sector es solo contexto. Las notas del consultor de cada paso viajan dentro de su
sección como información de primera mano que prevalece sobre inferencias.
"""

from pydantic import BaseModel, Field


class EmpresaForm(BaseModel):
    # Paso 1 · Quiénes sois (identidad — ancla del perfilado/OSINT del research)
    nombre_empresa: str
    municipio: str = ""            # desambigua el OSINT y activa el anclaje territorial
    web: str = ""                  # el mejor input del Paso 0 del research
    plantilla: str                 # 1-5 | 6-20 | 21-50 | 51-250 | +250
    cliente_principal: str = ""    # consumidor final | pymes | grandes | AAPP | mixto
    areas_internas: list[str] = Field(default_factory=list)   # checkboxes
    notas_p1: str = ""             # notas del consultor durante el paso 1
    # Paso 2 · Cómo trabajáis (la organización)
    descripcion: str               # a qué se dedican + cliente ideal (ancla de sector)
    herramientas: list[str] = Field(default_factory=list)     # ERP/CRM/Excel/WhatsApp…
    herramientas_detalle: str = ""  # cuáles exactamente (Sage ≠ SAP: coste de integración)
    intentos_previos: str = ""     # qué han probado ya con IA/automatización y qué pasó
    info_vive: str                 # dónde vive la información (6 opciones)
    fisico_digital: int = 50       # 0 = 100% físico … 100 = 100% digital
    notas_p2: str = ""
    # Paso 3 · Dónde duele (la tarea — núcleo del informe)
    cuello_botella: str            # ANCLA del dolor
    horas_semana: str = ""         # horas/semana que se van en la tarea → horas liberadas
    personas_tarea: str = ""       # entre cuántas personas
    entrada_formato: list[str] = Field(default_factory=list)  # papel, PDF, audios, Excel, ERP…
    consecuencia_error: str = ""   # qué pasa si se hace mal → tolerancia, HITL
    coste_verificacion: str = ""   # revisar vs hacer → filtro de apalancamiento
    frecuencia: str = ""           # cada cuánto ocurre → ROI
    rol_ejecutor: str = ""         # quién la hace → coste laboral, riesgo
    criterio_experto: str = ""     # reglas vs juicio → viabilidad
    validacion: str = ""           # cómo se sabe hoy que está bien → evaluabilidad
    ejemplos_historicos: str = ""  # nº de ejemplos correctos → entrenamiento/eval
    dependencia_clave: str = ""    # si falta quien más sabe un mes → riesgo organizativo
    notas_p3: str = ""
    # Paso 4 · Restricciones y cierre
    restricciones: list[str] = Field(default_factory=list)    # sensibles/NDA/regulado/certificado
    restricciones_detalle: str = ""  # cuáles exactamente (ISO 9001, IATF, salud…)
    capacidad_deseada: str = ""    # opcional — contexto secundario, NO ancla
    referente: str = ""            # opcional — empresas similares (precedentes cercanos para el research)
    notas_p4: str = ""
    contacto_nombre: str
    contacto_email: str


PASOS = {1: "Quiénes sois", 2: "Cómo trabajáis", 3: "Dónde duele", 4: "Restricciones y cierre"}


def _lista(valores: list[str], vacio: str = "(no indicadas)") -> str:
    return ", ".join(valores) if valores else vacio


def _notas(f: EmpresaForm, n: int) -> list[str]:
    """Bloque de notas del paso n, si las hay: primera mano, prevalece."""
    txt = getattr(f, f"notas_p{n}", "").strip()
    if not txt:
        return []
    return ["", f"Notas de la reunión (paso {n} · {PASOS[n]}; información de primera mano, "
                f"prevalece sobre inferencias):", txt]


def construir_brief(f: EmpresaForm) -> str:
    """Texto inyectable en el prompt de deep research. LA EMPRESA primero."""
    dig = max(0, min(100, f.fisico_digital))
    herr = _lista(f.herramientas)
    if f.herramientas_detalle.strip():
        herr += f" — en concreto: {f.herramientas_detalle.strip()}"
    restr = _lista(f.restricciones, "Ninguna relevante declarada")
    if f.restricciones_detalle.strip():
        restr += f" — en concreto: {f.restricciones_detalle.strip()}"
    carga = ""
    if f.horas_semana.strip() or f.personas_tarea.strip():
        personas = f" entre {f.personas_tarea.strip()} persona(s)" if f.personas_tarea.strip() else ""
        carga = f"Carga actual: {f.horas_semana.strip() or '(horas no indicadas)'} horas/semana{personas}."

    partes = [
        "== LA EMPRESA (ancla del análisis: investígala en el Paso 0) ==",
        f"Nombre: {f.nombre_empresa}",
        f"Municipio: {f.municipio or '(no indicado — asumir Sevilla o provincia)'}",
        f"Web: {f.web.strip() or '(sin web indicada)'}",
        f"Plantilla: {f.plantilla} personas.",
        f"Cliente principal: {f.cliente_principal or '(no indicado)'}.",
        f"Áreas que gestiona con equipo interno: {_lista(f.areas_internas)}.",
        *_notas(f, 1),
        "",
        "== CÓMO TRABAJA ==",
        f"A qué se dedica y cliente ideal:\n{f.descripcion}",
        f"Herramientas habituales: {herr}.",
        f"Dónde vive la información de trabajo: {f.info_vive}.",
        f"Balance del trabajo clave: {dig}% digital / {100 - dig}% físico.",
    ]
    if f.intentos_previos.strip():
        partes.append(f"Qué han probado ya con IA o automatización, y qué pasó:\n{f.intentos_previos.strip()}")
    partes += _notas(f, 2)
    partes += [
        "",
        "== LA TAREA (dónde duele) ==",
        f"Cuello de botella (horas manuales/repetitivas):\n{f.cuello_botella}",
    ]
    if carga:
        partes.append(carga)
    if f.entrada_formato:
        partes.append(f"Formato en que llega la información de esa tarea: {_lista(f.entrada_formato)}.")
    partes += [
        "",
        "Perfil de esa tarea (para calibrar ROI y viabilidad):",
        f"- Consecuencia si se hace mal: {f.consecuencia_error or '(no indicada)'}.",
        f"- Coste de revisar vs. hacer (apalancamiento): {f.coste_verificacion or '(no indicado)'}.",
        f"- Frecuencia con que ocurre: {f.frecuencia or '(no indicada)'}.",
        f"- Quién la realiza normalmente: {f.rol_ejecutor or '(no indicado)'}.",
        f"- Dependencia de criterio experto: {f.criterio_experto or '(no indicada)'}.",
        f"- Cómo se valida hoy que está bien hecha: {f.validacion or '(no indicado)'}.",
        f"- Ejemplos correctos ya disponibles: {f.ejemplos_historicos or '(no indicado)'}.",
        f"- Si quien más sabe faltara un mes: {f.dependencia_clave or '(no indicado)'}.",
        *_notas(f, 3),
        "",
        "== RESTRICCIONES A RESPETAR ==",
        f"{restr}.",
    ]
    if f.capacidad_deseada.strip():
        partes += ["", f"Capacidad que le gustaría tener y hoy no puede (contexto secundario, "
                       f"NO es el ancla del research):\n{f.capacidad_deseada}"]
    if f.referente.strip():
        partes += ["", f"Empresas similares nombradas por la dirección (mismo tipo de negocio y tamaño; "
                       f"investiga sus procesos como precedentes cercanos, sin comparar): {f.referente}"]
    partes += _notas(f, 4)
    # El contacto NO viaja al research: se queda en form.json para el seguimiento.
    return "\n".join(partes)

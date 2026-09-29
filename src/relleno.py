"""Rellena la plantilla (plantillas/reporte_ia_plantilla.html) por su
convención de huecos data-fill="clave".

Tipos de hueco:
  · Texto plano            → se reemplaza el contenido del elemento (dict textos).
  · Contenedor con huecos  → no se toca; se rellenan sus hijos (cond*, mapeo*, req*).
  · potencial_seg          → 5 segmentos <i>, los N primeros con class="on".
  · adopcion_donut         → estilo conic-gradient recalculado del % (solo attr).
  · matriz                 → <tbody>: una <tr> por oportunidad ya ordenada;
                             las Top 3 con class="is-top"; barra = prioridad×10 %.
  · top3                   → 3 tarjetas .t3 con los nombres del Top 3.
  · mapeoN_necesita        → <ul>: un <li> por ítem.
  · fuentes                → <ol>: un <li> por fuente (HTML ya formateado);
                             sin fuentes, el bloque se oculta.
Los huecos sin valor (p.ej. cump_* fijos) conservan el texto de la plantilla, SALVO
los que llevan texto de demostración: esos se ocultan (OCULTAR_SI_VACIO) para que
nunca salga un dato inventado en el PDF.
"""

from pathlib import Path

from bs4 import BeautifulSoup

PLANTILLA = Path(__file__).resolve().parent.parent / "plantillas" / "reporte_ia_plantilla.html"

# clave sin valor → se elimina el ancestro con esta clase (el texto demo no se imprime)
OCULTAR_SI_VACIO = {
    "perfil_fuentes": "pf-src",
    "mapeo1_horas": "horas", "mapeo2_horas": "horas", "mapeo3_horas": "horas",
    "mapeoT1_horas": "horas", "mapeoT2_horas": "horas", "mapeoT3_horas": "horas",
    "mapeo1_horas_base": "hb", "mapeo2_horas_base": "hb", "mapeo3_horas_base": "hb",
    "mapeoT1_horas_base": "hb", "mapeoT2_horas_base": "hb", "mapeoT3_horas_base": "hb",
    "horas_nota": "horas-nota",
    "llega1": "llega", "llega2": "llega", "llega3": "llega",
    "limite1_t": "lim", "limite2_t": "lim", "limite3_t": "lim", "limite4_t": "lim",
    "construccion1": "cstep", "construccion2": "cstep", "construccion3": "cstep",
    "construccion4": "cstep", "construccion5": "cstep",
    "cond1_lbl": "cond-row", "cond2_lbl": "cond-row", "cond3_lbl": "cond-row",
    "mapeo1_nombre": "msol", "mapeo2_nombre": "msol", "mapeo3_nombre": "msol",
    "mapeoT1_nombre": "msol", "mapeoT2_nombre": "msol", "mapeoT3_nombre": "msol",
}
CONTACTO_KEYS = ("contacto_nombre", "contacto_email", "contacto_tel")


VIAS = {"herramienta": "Herramienta existente", "formación": "Formación", "formacion": "Formación", "medida": "A medida"}


def _via_corta(v: str) -> str:
    v = (v or "").strip().lower()
    for k, lab in VIAS.items():
        if k in v:
            return lab
    return "—"


def _fila_matriz(soup: BeautifulSoup, idx: int, fila: dict) -> "BeautifulSoup":
    """<tr> de la matriz: nombre+desc, ROI, Viabilidad y barra de Prioridad."""
    tr = soup.new_tag("tr")
    if fila.get("top"):
        tr["class"] = "is-top"
    elif _via_corta(fila.get("via", "")) == "Herramienta existente":
        tr["class"] = "is-tool"
    td_n = soup.new_tag("td", attrs={"class": "n"}); td_n.string = str(idx)
    td_p = soup.new_tag("td")
    proj = soup.new_tag("div", attrs={"class": "proj"}); proj.append(str(fila["nombre"]))
    pd = soup.new_tag("div", attrs={"class": "pd"}); pd.append(str(fila["descripcion"]))
    proj.append(pd); td_p.append(proj)
    td_roi = soup.new_tag("td", attrs={"class": "n"}); td_roi.string = str(fila["roi"])
    td_via = soup.new_tag("td", attrs={"class": "n"}); td_via.string = str(fila["viabilidad"])
    td_sc = soup.new_tag("td")
    cell = soup.new_tag("div", attrs={"class": "scorecell"})
    bar = soup.new_tag("div", attrs={"class": "scorebar"})
    fill = soup.new_tag("i"); fill["style"] = f"width:{round(fila['prioridad'] * 10)}%"
    bar.append(fill)
    val = soup.new_tag("span", attrs={"class": "scoreval"}); val.string = f"{fila['prioridad']:g}"
    cell.append(bar); cell.append(val); td_sc.append(cell)
    td_v = soup.new_tag("td", attrs={"class": "via"}); td_v.string = _via_corta(fila.get("via", ""))
    for td in (td_n, td_p, td_roi, td_via, td_sc, td_v):
        tr.append(td)
    return tr


def rellenar(textos: dict, matriz: "list[dict]", necesita: "dict[int, list[str]]",
             fuentes: "list[str]", nivel: int, adopcion_pct: int,
             perfil: "list[str] | None" = None) -> str:
    """textos: huecos de texto plano · matriz: cartera YA ordenada por prioridad
    (dicts: nombre, descripcion, roi, viabilidad, prioridad, top) · necesita:
    {1: [...], 2: [...], 3: [...]} del Top 3 · fuentes: <li> ya formateados ·
    perfil: viñetas del Perfil detectado (sin ellas, el bloque se oculta)."""
    soup = BeautifulSoup(PLANTILLA.read_text(encoding="utf-8"), "html.parser")

    if soup.title is not None:
        empresa = textos.get("nombre_empresa", "").strip()
        soup.title.string = f"Estudio de viabilidad de IA · {empresa}" if empresa else "Estudio de viabilidad de IA"

    # Requisitos: rejilla por paso si viene completa; si no, la versión de tres filas.
    hay_grid = all(textos.get(f"req_p{i}_{k}") for i in (1, 2, 3) for k in ("infra", "datos", "adopcion"))
    for el in soup.select(".reqgrid" if not hay_grid else ".reqs[data-fill=requerimientos]"):
        el.decompose()

    # Contacto del consultor: sin ninguno configurado, fuera la línea entera.
    if not any(textos.get(k) for k in CONTACTO_KEYS):
        for c in soup.select(".next-c"):
            c.decompose()
    else:
        for k in CONTACTO_KEYS:            # los que falten, fuera (y su separador)
            if not textos.get(k):
                for sp in soup.select(f"[data-fill={k}]"):
                    sep = sp.find_previous_sibling(class_="sep") or sp.find_next_sibling(class_="sep")
                    if sep:
                        sep.decompose()
                    sp.decompose()

    for el in soup.select("[data-fill]"):
        # saltar elementos ya eliminados (p.ej. el span de fuentes dentro de un
        # bloque .perfil descompuesto)
        if getattr(el, "decomposed", False) or getattr(el, "attrs", None) is None:
            continue
        key = el["data-fill"]

        # --- Rellenos de estilo (atributo, sin tocar hijos) ---
        if key == "potencial_seg":
            el.clear()
            for i in range(5):
                seg = soup.new_tag("i")
                if i < nivel:
                    seg["class"] = "on"
                el.append(seg)
            continue
        if key == "adopcion_donut":
            p = round(adopcion_pct)
            el["style"] = f"background:conic-gradient(var(--green) 0 {p}%, #d7ddc9 {p}% 100%)"
            continue  # el % de dentro lo rellena la clave adopcion_pct

        # --- Repetidores ---
        if key.endswith("_horas_blk"):
            if textos.get(key.replace("_blk", "")):      # con horas → tres columnas
                padre = el.find_parent(class_="msol-b")
                if padre is not None:
                    padre["class"] = padre.get("class", []) + ["with-horas"]
            continue                      # el contenido lo decide su hijo mapeoN_horas
        if key == "perfil_bullets":
            if not perfil:
                caja = el.find_parent(class_="perfil")
                (caja or el).decompose()   # sin ficha → fuera el bloque entero
                continue
            el.clear()
            for b in perfil:
                li = soup.new_tag("li"); li.append(str(b)); el.append(li)
            continue
        if key == "matriz":
            el.clear()
            for i, fila in enumerate(matriz, start=1):
                el.append(_fila_matriz(soup, i, fila))
            continue
        if key == "top3":
            el.clear()
            for i, fila in enumerate([f for f in matriz if f.get("top")][:3], start=1):
                card = soup.new_tag("div", attrs={"class": "t3"})
                tn = soup.new_tag("div", attrs={"class": "tn"}); tn.string = f"Intervención 0{i}"
                tt = soup.new_tag("div", attrs={"class": "tt"}); tt.append(str(fila["nombre"]))
                card.append(tn); card.append(tt); el.append(card)
            continue
        if key == "limites":
            if not textos.get("limite1_t"):                # sin límites → fuera la página entera
                pagina = el.find_parent("section")
                (pagina or el).decompose()
            continue
        if key in ("llega_box",) or key.endswith("_row"):
            continue                                        # contenedores: los deciden sus hijos
        if key.startswith("construccion") and textos.get(key):
            num = el.find("b")                              # conserva el número, cambia el texto
            el.clear()
            if num is not None:
                el.append(num)
            el.append(str(textos[key]))
            continue
        if key == "mapeo_tool":
            if not textos.get("mapeoT1_nombre"):          # sin oportunidades de herramienta existente → fuera la página
                pagina = el.find_parent("section")
                (pagina or el).decompose()
            continue
        if key.startswith("mapeoT") and key.endswith("_necesita"):
            idx = "T" + key[6]         # mapeoT1_necesita → "T1"
            el.clear()
            for item in necesita.get(idx, []):
                li = soup.new_tag("li"); li.append(str(item)); el.append(li)
            continue
        if key.startswith("mapeo") and key.endswith("_necesita"):
            idx = int(key[5])           # mapeo1_necesita → 1
            el.clear()
            for item in necesita.get(idx, []):
                li = soup.new_tag("li"); li.append(str(item)); el.append(li)
            continue
        if key == "fuentes":
            el.clear()
            if not fuentes:
                el.decompose()
                continue
            for f in fuentes:
                li = soup.new_tag("li")
                li.append(BeautifulSoup(f, "html.parser"))
                el.append(li)
            continue

        # Contenedor con huecos anidados → se rellenan los hijos por separado.
        if el.find(attrs={"data-fill": True}):
            continue

        # --- Texto plano ---
        val = textos.get(key)
        if val is None:
            clase = OCULTAR_SI_VACIO.get(key)
            if clase:         # texto demo: nunca se imprime → fuera el bloque
                caja = el.find_parent(class_=clase)
                (caja or el).decompose()
            continue          # sin valor (p.ej. cump_* fijos) → queda la plantilla
        el.clear()
        el.append(str(val))

    return str(soup)

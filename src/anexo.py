"""Anexo de fuentes: documento APARTE del informe, para dar peso.

Parsea el informe.md del deep research de forma DETERMINISTA (cero LLM):
  · Sección 1 — las fuentes principales (la tabla del apartado 7).
  · Sección 2 — TODAS las fuentes consultadas (la lista final "Sources", numerada
    igual que los marcadores [cite: N] del informe, para que todo sea trazable).

Criterios acordados:
  · Se muestran DOMINIO + título/dato, nunca la URL cruda (los enlaces de grounding
    son kilométricos y efímeros); el hipervínculo va detrás del dominio.
  · Título honesto: "Fuentes consultadas durante la investigación" — describe, no
    promete que todas sostienen el informe (ese sello queda en las 7 del PDF).
"""

import html
import re
from datetime import datetime
from pathlib import Path

from src import pdf

_CSS = """
  :root{--ink:#3a3d34;--muted:#5c6152;--faint:#8f9285;--line:#d7ddc9;
        --green:#4c5a2e;--sage:#8b9a7b;--tint:#f2f4ec;
        --serif:Georgia,'Times New Roman',serif;--sans:Arial,Helvetica,sans-serif}
  *{box-sizing:border-box}
  @page{size:A4;margin:20mm 18mm 22mm}
  body{margin:0;padding:0;font-family:var(--sans);color:var(--ink);
       font-size:13px;line-height:1.6;background:#fff}
  .salto{break-before:page}
  tr{break-inside:avoid}
  thead{display:table-header-group}
  h2{break-after:avoid}
  .eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;
           color:var(--green);font-weight:bold}
  h1{font-family:var(--serif);font-weight:normal;font-size:26px;margin:6px 0 2px}
  .sub{color:var(--muted);font-size:12.5px;margin-bottom:26px}
  h2{font-family:var(--serif);font-weight:normal;font-size:18px;margin:26px 0 4px}
  .sec-k{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;
         color:var(--sage);font-weight:bold;margin-top:8px}
  .nota{background:var(--tint);border-left:3px solid var(--sage);border-radius:0 4px 4px 0;
        padding:8px 14px;color:var(--muted);font-size:12px;margin:10px 0 18px}
  table{width:100%;border-collapse:collapse;margin-top:10px}
  th{text-align:left;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;
     color:var(--green);border-bottom:2px solid var(--green);padding:6px 8px}
  td{padding:8px;border-bottom:1px solid var(--line);vertical-align:top;font-size:12.5px}
  td.n{color:var(--faint);white-space:nowrap}
  a{color:var(--green);text-decoration:none}
  ol.todas{margin:10px 0 0;padding-left:0;list-style:none;columns:2;column-gap:26px}
  ol.todas li{padding:4px 0;border-bottom:1px solid var(--line);break-inside:avoid;font-size:11px;line-height:1.35}
  ol.todas li .dom{color:var(--faint);font-size:10px;margin-left:6px;white-space:nowrap}
  ol.todas li b{color:var(--faint);font-weight:normal;margin-right:8px}
  .pie{margin-top:26px;font-size:10.5px;color:var(--faint)}
"""


def _dominio(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url)
    return m.group(1).replace("www.", "") if m else url


def parsear_principales(md: str) -> "list[dict]":
    """Filas de la tabla del apartado 7: autor/año, título, dato."""
    m = re.search(r"^#+\s*7\.?\s.*?$(.*?)(?=^\s*\**Sources|\Z)", md, re.M | re.S)
    if not m:
        return []
    filas = []
    for linea in m.group(1).splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) < 3 or set(celdas[0]) <= set(":- ") or "Autor" in celdas[0]:
            continue
        limpiar = lambda s: re.sub(r"\[cite[^\]]*\]|\*+", "", s).strip(" .*_")
        filas.append({"autor": limpiar(celdas[0]), "titulo": limpiar(celdas[1]),
                      "dato": limpiar(celdas[2])})
    return filas


def parsear_todas(md: str) -> "list[dict]":
    """La lista final 'Sources': N. [dominio](url) — numeración = [cite: N]."""
    fuentes = []
    for m in re.finditer(r"^\s*(\d+)\.\s*\[([^\]]+)\]\((https?://[^)\s]+)\)", md, re.M):
        fuentes.append({"n": int(m.group(1)), "texto": m.group(2).strip(),
                        "url": m.group(3)})
    return fuentes


# --- Formato alternativo (informe con listas en texto plano) --------------------
# La tabla del apartado 7 llega celda por línea y las referencias como "Título, URL"
# sin numerar bajo "Obras citadas". Se parsean como alternativa al markdown.

_CABECERA = ("autor", "título", "titulo", "año", "anio", "tipo", "dato")


def parsear_principales_docx(md: str) -> "list[dict]":
    m = re.search(r"^\s*7\.\s*EVIDENCIA.*$", md, re.M | re.I)
    if not m:
        return []
    lineas = [l.strip() for l in md[m.end():].splitlines()]
    celdas = []
    for l in lineas:
        if not l:
            continue
        if re.match(r"^(Obras citadas|Evaluaci[oó]n|Fuentes consultadas)", l, re.I):
            break
        celdas.append(l)
    # cabecera: primeras celdas que son etiquetas conocidas
    n = 0
    while n < len(celdas) and celdas[n].lower().split("/")[0].strip().startswith(_CABECERA):
        n += 1
    if n < 3:
        return []
    cuerpo = celdas[n:]
    filas = []
    for i in range(0, len(cuerpo) - n + 1, n):
        fila = cuerpo[i:i + n]
        limpiar = lambda s: re.sub(r"\d+$", "", s.strip(" .*_")).strip(" .*_")   # quita la cita pegada
        filas.append({"autor": limpiar(fila[0]), "titulo": limpiar(fila[1]),
                      "dato": limpiar(fila[-1])})
    return filas


def parsear_todas_docx(md: str) -> "list[dict]":
    m = re.search(r"^\s*Obras citadas\s*$", md, re.M | re.I)
    if not m:
        return []
    fuentes = []
    for l in md[m.end():].splitlines():
        mm = re.match(r"^\s*(.+?),\s*(https?://\S+)\s*$", l.strip())
        if mm:
            fuentes.append({"n": len(fuentes) + 1, "texto": _dominio(mm.group(2)),
                            "url": mm.group(2), "titulo": mm.group(1).strip()})
    return fuentes


def leer_consultadas(carpeta: Path) -> "list[dict]":
    """fuentes_consultadas.txt en la carpeta del lead: lo que el consultor copia del
    panel de fuentes de Gemini. Acepta 'URL<tab>título' por línea o bloques de
    'dominio / título / URL'. Se deduplica por URL y se quitan las ya citadas."""
    f = carpeta / "fuentes_consultadas.txt"
    if not f.exists():
        return []
    out, vistos, pend = [], set(), None
    for raw in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        l = raw.strip()
        if not l or l.lower().startswith("se abre en"):
            continue
        m = re.match(r"^(https?://\S+)\s*	?\s*(.*)$", l)
        if m:
            url, titulo = m.group(1), m.group(2).strip() or (pend or "")
        elif "	" in l and l.split("	")[-1].startswith("http"):
            titulo, url = l.rsplit("	", 1)
        else:
            pend = l if not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", l) else pend   # título candidato
            continue
        if url in vistos:
            continue
        vistos.add(url); pend = None
        out.append({"url": url, "titulo": titulo.strip(), "texto": _dominio(url)})
    return out


def leer_extra(carpeta: Path) -> "list[dict]":
    """fuentes_extra.json en la carpeta del lead: fuentes añadidas en la revisión
    (p. ej. promedios usados para estimar horas). Campos: autor, titulo, anio, tipo,
    dato, url. Entran en la tabla de datos y, numeradas, tras las referencias del research."""
    import json
    f = carpeta / "fuentes_extra.json"
    if not f.exists():
        return []
    try:
        return [x for x in json.loads(f.read_text(encoding="utf-8")) if x.get("url")]
    except Exception:  # noqa: BLE001
        return []


def generar(informe_md: str, carpeta: "str | Path",
            nombre_empresa: str = "") -> "Path | None":
    """Escribe anexo_fuentes.html + anexo_fuentes.pdf en la carpeta del lead.
    Devuelve None (sin romper el informe) si el md no trae fuentes parseables."""
    carpeta = Path(carpeta)
    principales = parsear_principales(informe_md) or parsear_principales_docx(informe_md)
    todas = parsear_todas(informe_md) or parsear_todas_docx(informe_md)
    extra = leer_extra(carpeta)
    for x in extra:
        anio = f" ({x['anio']})" if x.get("anio") else ""
        principales.append({"autor": x.get("autor", ""), "titulo": x.get("titulo", "") + anio,
                            "dato": x.get("dato", "")})
        todas.append({"n": len(todas) + 1, "texto": _dominio(x["url"]), "url": x["url"],
                      "titulo": x.get("titulo", "")})
    if not principales and not todas:
        print("anexo: el informe.md no trae fuentes parseables; anexo omitido.")
        return None

    fecha = datetime.now().strftime("%d/%m/%Y")
    quien = f" · {html.escape(nombre_empresa)}" if nombre_empresa else ""
    partes = [
        f"<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>",
        f"<title>Anexo de fuentes · Estudio de viabilidad de IA{' · ' + html.escape(nombre_empresa) if nombre_empresa else ''}</title><style>{_CSS}</style></head><body>",
        "<div class='eyebrow'>Anexo del Estudio de Viabilidad de IA</div>",
        "<h1>Fuentes consultadas durante la investigación</h1>",
        f"<div class='sub'>Documento complementario{quien} · {fecha}</div>",
    ]
    if principales:
        partes += [
            "<div class='sec-k'>Sección 1</div>",
            "<h2>Datos citados en el estudio y su origen</h2>",
            "<table><tr><th>Autor / Medio</th><th>Investigación</th><th>Dato que aporta</th></tr>",
        ]
        for f in principales:
            partes.append(
                f"<tr><td>{html.escape(f['autor'])}</td><td>{html.escape(f['titulo'])}</td>"
                f"<td>{html.escape(f['dato'])}</td></tr>")
        partes.append("</table>")
    if todas:
        partes += [
            "<div class='sec-k' style='margin-top:30px'>Sección 2</div>",
            "<h2>Referencias de la investigación</h2>",
            "<div class='nota'>La numeración corresponde a las referencias del expediente de "
            "investigación" + (f"; las {len(extra)} últimas se añadieron en la revisión para las "
            "estimaciones de horas" if extra else "") + ". Los enlaces se facilitan tal y como "
            "fueron accedidos y su disponibilidad puede variar.</div>",
            "<ol class='todas'>",
        ]
        for f in todas:
            # El medio real es el TEXTO del enlace markdown ("ifm.com"); la URL es
            # solo la redirección de grounding (dominio siempre vertexaisearch).
            dom = f["texto"] if not f["texto"].startswith("http") else _dominio(f["texto"])
            titulo = html.escape(f.get("titulo", "")) if f.get("titulo") else ""
            if titulo:     # formato Word: título enlazado + medio en pequeño (distingue artículos del mismo sitio)
                partes.append(f"<li><b>{f['n']:02d}</b><a href='{html.escape(f['url'])}'>{titulo}</a>"
                              f"<span class='dom'>{html.escape(dom)}</span></li>")
            else:          # formato API: solo hay medio
                partes.append(f"<li><b>{f['n']:02d}</b><a href='{html.escape(f['url'])}'>{html.escape(dom)}</a></li>")
        partes.append("</ol>")
    consultadas = [c for c in leer_consultadas(carpeta) if c["url"] not in {f["url"] for f in todas}]
    if consultadas:
        partes += [
            "<div class='sec-k salto'>Sección 3</div>",
            "<h2>Otras páginas consultadas durante la investigación</h2>",
            "<div class='nota'>Páginas revisadas por la investigación que no se citan directamente en el "
            "informe. Se listan para completar la trazabilidad.</div>",
            "<ol class='todas'>",
        ]
        for i, c in enumerate(consultadas, start=1):
            tit = html.escape(c["titulo"]) if c["titulo"] else html.escape(c["texto"])
            partes.append(f"<li><b>{i:02d}</b><a href='{html.escape(c['url'])}'>{tit}</a>"
                          f"<span class='dom'>{html.escape(c['texto'])}</span></li>")
        partes.append("</ol>")
    partes.append(f"<div class='pie'>{len(principales)} datos con origen · "
                  f"{len(todas)} referencias citadas"
                  + (f" · {len(consultadas)} páginas consultadas" if consultadas else "")
                  + "</div></body></html>")

    doc = "\n".join(partes)
    (carpeta / "anexo_fuentes.html").write_text(doc, encoding="utf-8")
    return pdf.html_a_pdf(doc, carpeta / "anexo_fuentes.pdf")

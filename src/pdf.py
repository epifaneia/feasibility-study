"""HTML relleno → PDF A4 con Chromium (Playwright).

Incluye SHRINK-TO-FIT: si una página desborda el A4, se encoge con zoom hasta que
cabe — nunca se corta contenido (el seguro final acordado).
"""

from pathlib import Path

# Por cada .page: si el contenido desborda el alto A4, baja el zoom hasta que quepa.
_SHRINK_JS = """
() => {
  const out = [];
  document.querySelectorAll('.page').forEach((pg, i) => {
    let z = 1;
    while (pg.scrollHeight > pg.clientHeight + 1 && z > 0.74) {
      z = Math.round((z - 0.02) * 100) / 100;
      pg.style.zoom = z;
    }
    if (z < 1) out.push([i + 1, z]);
  });
  return out;
}
"""


def html_a_pdf(html: str, destino: "str | Path") -> Path:
    from playwright.sync_api import sync_playwright

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        page = navegador.new_page()
        page.set_content(html, wait_until="networkidle")
        page.emulate_media(media="print")     # activa el CSS @media print (alto A4)
        encogidas = page.evaluate(_SHRINK_JS)  # shrink-to-fit por página
        for n, z in encogidas:
            print(f"⚠️  PDF: la página {n} no cabía a tamaño real y se ha encogido al {int(z * 100)} %.")
        n_secciones = page.evaluate("() => document.querySelectorAll('.page').length")
        page.pdf(
            path=str(destino),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,      # si el HTML define @page con márgenes, mandan
        )
        navegador.close()
    _comprobar_paginas(destino, n_secciones)
    _metadatos(destino, html)
    return destino


def _metadatos(destino: Path, html: str) -> None:
    """Título = <title> del HTML; autor = CONTACTO_NOMBRE; sin productor/creador de Chromium."""
    try:
        import os, re
        from pypdf import PdfReader, PdfWriter
        m = re.search(r"<title>(.*?)</title>", html, re.S)
        titulo = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        autor = os.environ.get("CONTACTO_NOMBRE", "").strip()
        r = PdfReader(str(destino)); w = PdfWriter(); w.append(r)
        meta = {"/Title": titulo, "/Producer": "", "/Creator": ""}
        if autor:
            meta["/Author"] = autor
        w.add_metadata(meta)
        with open(destino, "wb") as f:
            w.write(f)
    except Exception as exc:  # noqa: BLE001
        print("pdf: no se pudieron fijar los metadatos:", exc)


def _comprobar_paginas(destino: Path, esperadas: int) -> None:
    """Aviso (no error) si el PDF tiene más páginas que secciones .page: algo ha
    desbordado y hay una página casi vacía en medio del informe."""
    try:
        from pypdf import PdfReader
        n = len(PdfReader(str(destino)).pages)
    except Exception:  # noqa: BLE001
        return
    if esperadas and n != esperadas:
        print(f"⚠️  PDF: {n} páginas, se esperaban {esperadas}. Revisa si alguna sale casi vacía.")

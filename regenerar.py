"""Regenera el informe de un lead YA capturado, sin repetir el research.

    python regenerar.py leads/<carpeta>                 # desde extraccion.json (tras corregirla a mano)
    python regenerar.py leads/<carpeta> --desde md      # desde informe.md (repite extracción + PDF)
    python regenerar.py leads/<carpeta> --sin-qwen      # sin el ajuste de longitud local

Flujo de revisión antes de enviar:
  1. lee qa.txt y derivacion.json (avisos, ranking);
  2. corrige extraccion.json a mano si algo contradice lo que dijo la empresa;
  3. python regenerar.py <carpeta>  →  informe.pdf nuevo, con la misma carpeta.
"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src import extraccion, formulario, informe


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--desde", choices=["extraccion", "md"], default="extraccion")
    ap.add_argument("--sin-qwen", action="store_true")
    args = ap.parse_args()
    if args.sin_qwen:
        os.environ["LONGITUD_QWEN"] = "0"

    carpeta = Path(args.carpeta)
    form_json = carpeta / "form.json"
    if not form_json.exists():
        raise SystemExit(f"No hay form.json en {carpeta}")
    form = formulario.EmpresaForm.model_validate_json(form_json.read_text(encoding="utf-8"))

    if args.desde == "md":
        md = (carpeta / "informe.md").read_text(encoding="utf-8")
        ruta = informe.generar(form, carpeta, informe_md=md)
    else:
        datos = extraccion.InformeIA.model_validate_json(
            (carpeta / "extraccion.json").read_text(encoding="utf-8"))
        ruta = informe.renderizar(form, datos, carpeta)
    print(f"✅ Regenerado: {ruta}")
    qa = carpeta / "qa.txt"
    if qa.exists():
        print("\nAvisos de QA:\n" + qa.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()

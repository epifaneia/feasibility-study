"""Pruebas del núcleo determinista: prioridad, Top 3, retorno, avisos de QA y
relleno de la plantilla. Sin red, sin Gemini, sin Ollama.

    python tests/test_derivacion.py

Todos los datos son sintéticos (empresa y oportunidades inventadas). La última
parte genera el PDF con Chromium si Playwright está instalado; si no, se salta.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ["LONGITUD_QWEN"] = "0"     # sin Ollama: el ajuste de longitud no se llama
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402

from src import derivacion, informe, relleno  # noqa: E402
from src.extraccion import Condicion, Fuente, InformeIA, Limite, Oportunidad, Paso  # noqa: E402
from src.formulario import EmpresaForm  # noqa: E402

fallos = 0


def check(cond: bool, msg: str) -> None:
    global fallos
    print(("  ok  " if cond else "  FAIL") + " " + msg)
    if not cond:
        fallos += 1


def op(nombre: str, roi: int, viab: int, rmin: int = 20, rmax: int = 40, **kw) -> Oportunidad:
    base = dict(nombre=nombre, descripcion=f"Descripción sintética de {nombre}.",
                roi=roi, viabilidad=viab, reduccion_min=rmin, reduccion_max=rmax,
                problema=f"Problema sintético de {nombre}.", necesita=["Datos", "Formación"])
    base.update(kw)
    return Oportunidad(**base)


def datos_limpios(**kw) -> InformeIA:
    """InformeIA sintético que no dispara ningún aviso."""
    base = dict(
        sector="Sector de prueba",
        ficha_bullets=["Viñeta uno", "Viñeta dos", "Viñeta tres", "Viñeta cuatro"],
        ficha_fuentes="web de prueba · directorio de prueba",
        potencial_nivel=3,
        potencial_razones="Razones sintéticas del potencial.",
        retorno_categoria="repetitivas",
        retorno_desc="tareas sintéticas de poco valor añadido",
        adopcion_pct=40,
        oportunidades=[
            op("Alfa", 9, 8, aborda_cuello_botella=True, horas_mes="10-20 al mes",
               horas_base="supuesto sintético"),
            op("Beta", 8, 7),
            op("Gamma", 7, 7),
            op("Delta", 5, 5, via="herramienta existente"),
            op("Épsilon", 4, 4, via="herramienta existente"),
            op("Zeta", 3, 3, via="herramienta existente"),
        ],
        condiciones=[Condicion(titulo=f"Condición {i}", descripcion=f"Descripción {i}.")
                     for i in (1, 2, 3)],
        req_infra="Infraestructura sintética.",
        req_datos="Datos sintéticos.",
        req_adopcion="Adopción sintética.",
        camino_intro="Introducción sintética al camino.",
        no_basta="Texto sintético de por qué no basta.",
        llega=["Llega uno.", "Llega dos.", "Llega tres."],
        limites=[Limite(titulo=t, herramienta="Con herramienta.", a_medida="A medida.")
                 for t in ("Límite A", "Límite B", "Límite C", "Límite D")],
        construccion=[f"Paso de construcción {i}" for i in range(1, 6)],
        plan=[Paso(titulo=f"Paso {i}", plazo=f"{i} meses", cubre="Cubre algo.", que_es="Es algo.",
                   desbloquea="Desbloquea algo.", req_infra="Infra.", req_datos="Datos.",
                   req_adopcion="Adopción.") for i in (1, 2, 3)],
        cump_aislamiento="Aislamiento sintético.",
        cump_normativa="Normativa sintética.",
        cump_trazabilidad="Trazabilidad sintética.",
        fuentes=[Fuente(autor="Organismo Ficticio", titulo="Informe ficticio", anio="2025",
                        tipo="institucional"),
                 Fuente(autor="Universidad Ficticia", titulo="Estudio ficticio", tipo="académica"),
                 Fuente(autor="Proveedor Ficticio", titulo="Caso ficticio", tipo="proveedor")],
    )
    base.update(kw)
    return InformeIA(**base)


def hay_aviso(datos: InformeIA, fragmento: str) -> bool:
    return any(fragmento in a for a in derivacion.avisos(datos))


def main() -> int:
    # --- prioridad y ranking ---
    check(derivacion.prioridad(10, 2) == 4.5, "prioridad (10,2) → 4.5")
    check(derivacion.prioridad(7, 8) == 7.5, "prioridad (7,8) → 7.5")
    check(derivacion.prioridad(15, -3) == 0.0 and derivacion.prioridad(12, 10) == 10.0,
          "prioridad acota las notas a 0-10")
    desequilibrada, equilibrada = op("Desequilibrada", 10, 2), op("Equilibrada", 7, 8)
    orden = [o.nombre for o, _ in derivacion.ordenar([desequilibrada, equilibrada])]
    check(orden == ["Equilibrada", "Desequilibrada"], "la equilibrada (7,8) gana a la desequilibrada (10,2)")
    empate = [o.nombre for o, _ in derivacion.ordenar([op("Primera", 6, 6), op("Segunda", 6, 6)])]
    check(empate == ["Primera", "Segunda"], "a igualdad de prioridad se conserva el orden del informe")

    # --- retorno ---
    check(derivacion.retorno_pct([op("A", 5, 5, 20, 40), op("B", 5, 5, 40, 60)]) == 40,
          "retorno = media de los puntos medios (30 y 50 → 40)")
    check(derivacion.retorno_pct([op("A", 5, 5, 20, 40), op("N", 5, 5, 80, 100, tarea_actual=False)]) == 30,
          "una actividad nueva no cuenta en el % de retorno")
    check(derivacion.retorno_pct([op("N", 5, 5, 80, 100, tarea_actual=False)]) == 90,
          "si todas son nuevas, se promedian todas")
    check(derivacion.retorno_pct([op("A", 5, 5, 60, 20)]) == 40, "rango invertido se corrige")
    check(derivacion.retorno_pct([]) == 0, "sin Top 3 → 0")

    # --- potencial y adopción ---
    check(derivacion.potencial_adjetivo(9) == "Excepcional" and derivacion.nivel_potencial(0) == 1,
          "potencial acotado a 1-5")
    check(derivacion.frase_adopcion(50) == derivacion.FRASE_ADOPCION_ALTA
          and derivacion.frase_adopcion(49) == derivacion.FRASE_ADOPCION_BAJA,
          "frase de adopción: umbral en 50 %")

    # --- avisos de QA: uno que salta y uno que no, por regla ---
    limpio = datos_limpios()
    check(derivacion.avisos(limpio) == [], "datos limpios → sin avisos")
    ops = limpio.oportunidades

    sin_cuello = [o.model_copy(update={"aborda_cuello_botella": False}) for o in ops]
    check(hay_aviso(datos_limpios(oportunidades=sin_cuello), "cuello de botella"),
          "Top 3 sin el cuello de botella → aviso")
    fuera = [o.model_copy(update={"aborda_cuello_botella": o.nombre == "Zeta"}) for o in ops]
    check(hay_aviso(datos_limpios(oportunidades=fuera), "cuello de botella"),
          "cuello de botella solo fuera del Top 3 → aviso")

    nueva = [ops[0].model_copy(update={"tarea_actual": False})] + ops[1:]
    check(hay_aviso(datos_limpios(oportunidades=nueva), "retorno): Alfa"),
          "actividad nueva en el Top 3 → aviso con su nombre")
    nueva_fuera = ops[:5] + [ops[5].model_copy(update={"tarea_actual": False})]
    check(not hay_aviso(datos_limpios(oportunidades=nueva_fuera), "Actividades nuevas"),
          "actividad nueva fuera del Top 3 → sin aviso")

    altas = [o.model_copy(update={"reduccion_min": 60, "reduccion_max": 80}) for o in ops]
    check(hay_aviso(datos_limpios(oportunidades=altas), "Retorno 70%"), "retorno ≥ 60 % → aviso")
    justo = [o.model_copy(update={"reduccion_min": 50, "reduccion_max": 68}) for o in ops]
    check(not hay_aviso(datos_limpios(oportunidades=justo), "Retorno"), "retorno 59 % → sin aviso")

    check(hay_aviso(datos_limpios(oportunidades=ops[:5]), "Solo 5 oportunidades"),
          "menos de 6 oportunidades → aviso")
    check(hay_aviso(datos_limpios(condiciones=limpio.condiciones[:2]), "2 condiciones"),
          "condiciones ≠ 3 → aviso")

    prov = [Fuente(autor=f"Proveedor {i}", titulo="Caso", tipo="proveedor") for i in range(2)]
    check(hay_aviso(datos_limpios(fuentes=prov + limpio.fuentes[:1]), "2 de 3 fuentes son de proveedor"),
          "mayoría de fuentes de proveedor → aviso")
    check(not hay_aviso(datos_limpios(fuentes=prov + limpio.fuentes[:2]), "de proveedor"),
          "proveedor justo en la mitad → sin aviso")
    check(hay_aviso(datos_limpios(fuentes=[]), "Sin fuentes"), "sin fuentes → aviso")

    check(hay_aviso(datos_limpios(retorno_desc="según el formulario de la reunión"), "«formulario»"),
          "jerga interna en un texto → aviso")
    jerga_op = [ops[0].model_copy(update={"problema": "Lo dice el Brief."})] + ops[1:]
    check(hay_aviso(datos_limpios(oportunidades=jerga_op), "«brief»"),
          "jerga interna en una oportunidad (sin distinguir mayúsculas) → aviso")

    res = derivacion.resumen(limpio)
    check(res["top3"] == ["Alfa", "Beta", "Gamma"] and res["ranking"][0]["prioridad"] == 8.5,
          "resumen: Top 3 y prioridad recalculados")

    # --- plantilla: ningún hueco con el texto de demostración ---
    plantilla = BeautifulSoup(relleno.PLANTILLA.read_text(encoding="utf-8"), "html.parser")
    demo = {}
    for el in plantilla.select("[data-fill]"):
        if el.find(attrs={"data-fill": True}) is None and el.get_text(strip=True):
            demo.setdefault(el["data-fill"], el.get_text(strip=True))
    form = EmpresaForm(nombre_empresa="Empresa Ficticia de Prueba", plantilla="6-20",
                       descripcion="Actividad sintética.", info_vive="Hojas de cálculo",
                       cuello_botella="Una tarea sintética lenta.", horas_semana="10",
                       contacto_nombre="Persona Ficticia", contacto_email="prueba@example.invalid")
    tmp = Path(tempfile.mkdtemp())
    pdf_real = informe.pdf.html_a_pdf
    informe.pdf.html_a_pdf = lambda html, destino: Path(destino)   # sin Chromium en esta parte
    try:
        informe.renderizar(form, limpio, tmp)
    finally:
        informe.pdf.html_a_pdf = pdf_real
    salida = BeautifulSoup((tmp / "informe.html").read_text(encoding="utf-8"), "html.parser")
    sin_rellenar = sorted({el["data-fill"] for el in salida.select("[data-fill]")
                           if el["data-fill"] in demo and el.get_text(strip=True) == demo[el["data-fill"]]})
    check(not sin_rellenar, "ningún hueco conserva el texto de demostración"
          + (f" (quedan: {', '.join(sin_rellenar)})" if sin_rellenar else ""))
    texto = salida.get_text(" ", strip=True)
    check("Empresa Ficticia de Prueba" in texto and "Alfa" in texto, "el HTML lleva los datos sintéticos")
    check((tmp / "qa.txt").read_text(encoding="utf-8").startswith("- Sin avisos"),
          "qa.txt sin avisos para los datos limpios")

    # --- PDF real (lo mismo que hace regenerar.py), si hay Chromium ---
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("  --   Playwright no instalado: se salta el PDF")
    else:
        ruta = informe.renderizar(form, limpio, tmp)
        check(ruta.is_file() and ruta.read_bytes()[:5] == b"%PDF-", "PDF generado sin red")

    print(f"\n{'TODO OK' if fallos == 0 else f'{fallos} fallos'}")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())

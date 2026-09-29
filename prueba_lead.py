"""Test A/B del anclaje a EMPRESA: dos leads del MISMO sector, escala opuesta.

    python prueba_lead.py a                    # Empresa A: tier-1, 500 empleados, PLM/Jira
    python prueba_lead.py b                    # Empresa B: taller de Sevilla, 12 empleados
    python prueba_lead.py b <ruta_informe.md>  # reusa un research ya hecho (no repaga)

CRITERIO DE ÉXITO: los dos informes deben salir RADICALMENTE distintos.
  · Si a B le aparece ingeniería de requisitos, ASPICE o visión artificial con
    sensórica → el anclaje ha fallado.
  · Si a B le salen presupuestos desde WhatsApp, facturas desde Excel y captura del
    conocimiento del veterano → el anclaje funciona.

Cada run guarda en leads/<fecha>_prueba-<empresa>/ : informe.md (a salvo ANTES de la
extracción), extraccion.json, derivacion.json, informe.html, informe.pdf.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src import formulario, informe

BASE = Path(__file__).resolve().parent

FORM_A = formulario.EmpresaForm(
    nombre_empresa="Automoción Ejemplo, S.A.",
    municipio="Sevilla (P.I. Carretera Amarilla)",
    web="www.automocion-ejemplo.example",
    plantilla="+250",
    cliente_principal="Grandes empresas",
    areas_internas=["Producción / Fabricación", "Operaciones / Logística",
                    "Legal y Compliance", "Recursos Humanos"],
    descripcion=(
        "Proveedor tier-1 de sistemas electrónicos de confort para OEMs europeos. "
        "Desarrollo con ingeniería de sistemas bajo ASPICE e ISO 26262; unos 500 "
        "empleados entre planta y oficinas técnicas."
    ),
    herramientas=["ERP", "Software propio", "Microsoft 365"],
    herramientas_detalle="SAP, Jira, Polarion (PLM), IBM DOORS en algunos proyectos",
    info_vive="Un ERP/CRM o software corporativo",
    fisico_digital=70,
    cuello_botella=(
        "Cada RFQ de un OEM llega con miles de requisitos en ReqIF, PDFs y Excels. "
        "Los ingenieros de sistemas dedican semanas a clasificarlos, detectar "
        "duplicados y contradicciones, y cargarlos en Polarion con trazabilidad."
    ),
    consecuencia_error="Impacto legal o regulatorio",
    coste_verificacion="Bastante: más rápido revisar, pero requiere atención",
    frecuencia="Semanalmente",
    rol_ejecutor="Ingeniero",
    criterio_experto="Existen reglas, pero requieren interpretación frecuente",
    validacion="Existe una validación objetiva y verificable",
    ejemplos_historicos="Más de 1.000",
    dependencia_clave="El proceso se ralentizaría significativamente",
    restricciones=["Información confidencial", "Requisitos regulatorios", "Procesos certificados"],
    capacidad_deseada="Responder RFQs completas en la mitad de tiempo.",
    referente="Grupo Ejemplo Automoción",
    contacto_nombre="Consultor de ejemplo",
    contacto_email="consultor@ejemplo.com",
)

FORM_B = formulario.EmpresaForm(
    nombre_empresa="Taller Ejemplo, S.L.",
    municipio="Sevilla (Polígono Store)",
    web="",
    plantilla="6-20",
    cliente_principal="Mixto",
    areas_internas=["Atención al cliente", "Contabilidad / Finanzas"],
    descripcion=(
        "Taller mecánico multimarca: mantenimiento y reparación de turismos y alguna "
        "flota pequeña de furgonetas. 12 personas, la mayoría mecánicos; en la "
        "oficina somos dos para todo el papeleo."
    ),
    herramientas=["Excel", "WhatsApp", "ERP", "Correo electrónico"],
    herramientas_detalle="Un ERP sencillo de taller para las órdenes; lo demás Excel y WhatsApp",
    info_vive="Mixto: un poco de todo",
    fisico_digital=25,
    cuello_botella=(
        "El papeleo de la oficina: pasar a mano los partes de los mecánicos a "
        "presupuestos y facturas, contestar los WhatsApps de clientes preguntando "
        "por su coche, y reclamar a los seguros. Se nos van las tardes enteras."
    ),
    consecuencia_error="Retrasos o molestias",
    coste_verificacion="Muchísimo: revisar es mucho más rápido que hacerlo desde cero",
    frecuencia="Varias veces al día",
    rol_ejecutor="Administrativo",
    criterio_experto="Sigo reglas claras y conocidas",
    validacion="Los errores se detectan rápidamente cuando aparecen",
    ejemplos_historicos="Entre 100 y 1.000",
    dependencia_clave="El proceso quedaría bloqueado",
    restricciones=["Ninguna relevante"],
    capacidad_deseada="Que el cliente sepa el estado de su coche sin llamarnos.",
    referente="",
    contacto_nombre="Consultor de ejemplo",
    contacto_email="consultor@ejemplo.com",
)

FORMS = {"a": ("empresa-a-tier1", FORM_A), "b": ("empresa-b-taller", FORM_B)}


def main() -> None:
    letra = (sys.argv[1] if len(sys.argv) > 1 else "b").lower()
    if letra not in FORMS:
        print("Uso: python prueba_lead.py a|b [ruta_informe.md]"); sys.exit(2)
    slug, form = FORMS[letra]
    reusar = sys.argv[2] if len(sys.argv) > 2 else None
    informe_md = Path(reusar).read_text(encoding="utf-8") if reusar else None

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    carpeta = BASE / "leads" / f"{ts}_prueba-{slug}"
    print(f"📁 Carpeta del lead: {carpeta}")
    print(f"🏢 {form.nombre_empresa} · {form.plantilla} personas · {form.municipio}")
    if reusar:
        print(f"↩️  Reusando research: {reusar}")
    else:
        print("🔍 Lanzando deep research REAL (tarda unos minutos)...")

    try:
        ruta = informe.generar(form, carpeta, informe_md=informe_md)
        print(f"\n✅ LISTO: {ruta}")
    except Exception:
        print("\n❌ Algo falló. Traza completa:\n" + traceback.format_exc())
        md = carpeta / "informe.md"
        if md.exists():
            print(f"🛟 El research SÍ se guardó: {md}")
            print(f"   Relanza sin repagar:  python prueba_lead.py {letra} \"{md}\"")
        sys.exit(1)


if __name__ == "__main__":
    main()

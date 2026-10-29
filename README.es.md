# feasibility-study · Estudio de viabilidad de IA para una pyme

*Read this in [English](README.md).*

Este repositorio son dos proyectos completos fundidos en uno. El primero transfiere conocimiento técnico sobre lo que la IA puede hacer a alguien que no lo tiene: un formulario le lleva de la mano por las preguntas que importan (quiénes sois, cómo trabajáis, dónde duele, qué hay que respetar) y, con sus respuestas, encarga una investigación a una herramienta que navega sola por cientos de páginas públicas y escribe un informe largo con sus fuentes. Ese informe ya es usable: una investigación que encaja con esa empresa, no con "el sector". El segundo convierte ese texto denso, de muchas páginas y escrito como la herramienta quiera, en un estudio nuestro: con nuestra forma de implantar herramientas de IA, nuestro orden, nuestra estética y las conclusiones que consideramos relevantes, revisado por una persona antes de enviarse. Formulario, servidor, panel del consultor y PDF: la pieza completa.

> La IA tiene riesgos. El código los acota. La norma responde de lo que queda.

[Filosofía de diseño](#filosofía-de-diseño) · [Dónde aporta valor la IA](#dónde-aporta-valor-la-ia) · [Los cinco pasos](#los-cinco-pasos-en-este-proyecto) · [Medido](#medido) · [Demo](#demo-en-cuatro-comandos) · [Limitaciones](#limitaciones) · [Seguridad y regulación](#seguridad-y-regulación)

---

## Filosofía de diseño

Cualquier aplicación con IA tiene cinco pasos. Solo el paso 4 invoca un modelo; los otros cuatro son código: reproducibles, testeables, sin red. El paso 5 nunca corrige: marca y degrada. Texto completo en [epifaneia.dev](https://epifaneia.dev).

```
 1 LIMPIEZA      2 CONTEXTO      3 GUARDARRAÍL IN    4 PROCESO        5 GUARDARRAÍL OUT
 ■ código        ■ código        ■ código            ▲ modelo         ■ código
```

## Dónde aporta valor la IA

Decir a una pyme dónde le compensa la IA exige leer: qué han hecho empresas parecidas, qué salió bien, qué costó, qué herramientas ya existen y a qué precio. Un consultor tarda días por empresa, y una búsqueda por palabras devuelve titulares. El modelo hace lo único que solo un modelo puede hacer: una investigación autónoma, lo que los proveedores llaman *deep research*: el modelo navega por cientos de páginas públicas, decide qué leer y qué descartar, y escribe un informe largo con sus fuentes. Y después, responder preguntas concretas sobre ese informe. El código hace todo lo demás: qué se investiga y con qué jerarquía de fuentes, qué preguntas se le hacen al informe y en qué esquema se responden, cómo se ordenan las oportunidades, qué cifras entran en el resumen, qué avisos recibe el revisor, y que el PDF cabe en sus páginas y no lleva texto de relleno.

---

## Los cinco pasos en este proyecto

Cada uno de los dos proyectos pasa por los cinco pasos por separado. ★ marca dónde está la mejora: el formulario que acota la investigación, y la conversión del informe de la herramienta en el nuestro.

### Primero · Investigar: del formulario al informe

| Paso | Qué hace aquí | |
|---|---|---|
| 1 · Limpieza | Vacío. La entrada es el formulario, y llega limpia por construcción. | |
| 2 · Contexto | De las respuestas del formulario sale un resumen ordenado: la empresa es el ancla, la tarea explica dónde duele, el sector es solo contexto. Ese resumen se inserta en un texto de encargo fijo. | |
| 3 · Guardarraíl de entrada | El formulario en cuatro pasos, quiénes sois, cómo trabajáis, dónde duele, qué hay que respetar, y el orden de fuentes que se exige: instituciones y estudios primero, prensa después, proveedores al final. Antes de que la herramienta empiece ya está acotado qué empresa, qué tarea y qué fuentes. | ★ |
| 4 · Proceso | La investigación: una herramienta del proveedor de IA (lo que llaman *deep research*) navega sola por cientos de páginas públicas y devuelve un informe largo con sus fuentes. | |
| 5 · Guardarraíl de salida | Mínimo, a propósito: el informe se guarda entero, tal cual, con sus fuentes. Nada se interpreta todavía. | |

### Segundo · Responder: del informe de la herramienta a nuestro estudio

| Paso | Qué hace aquí | |
|---|---|---|
| 1 · Limpieza | El informe llega como texto. Se le extraen las fuentes citadas y se ordenan por tipo: instituciones, estudios, prensa, proveedores. | |
| 2 · Contexto | El informe entero, más el resumen del primer proyecto. El modelo responde sobre lo investigado, no sobre lo que sabe de memoria. | |
| 3 · Guardarraíl de entrada | Nuestras preguntas, con formato fijo de respuesta: qué oportunidades hay, por qué vía se resuelve cada una (herramienta existente, formación o desarrollo a medida), qué necesita y qué condiciones tiene. Las notas van ancladas a escalas fijas, y las palabras internas del proceso están prohibidas en la respuesta. | |
| 4 · Proceso | Una llamada normal a un modelo: responde las preguntas en ese formato. Opcionalmente, un modelo local recorta los textos que se pasan de largo. | |
| 5 · Guardarraíl de salida | Convertir lo respondido en nuestro estudio: nuestra narrativa, nuestro orden, nuestras prioridades, nuestra estética. El código ordena las oportunidades, decide las cifras del resumen, oculta los huecos sin dato, avisa al revisor y comprueba las páginas. El PDF no sale sin revisión humana. | ★ |

### Qué produce, y dónde

| Fichero en `leads/<fecha>_<empresa>/` | Qué es |
|---|---|
| `form.json` · `brief.txt` · `prompt.txt` | Lo que dijo la empresa, ordenado, y lo que se le pidió al modelo |
| `informe.md` | La investigación completa, con sus fuentes |
| `extraccion.json` | Las respuestas a nuestras preguntas, en el esquema cerrado |
| `derivacion.json` · `qa.txt` | El orden calculado por código y los avisos para el revisor |
| `informe.pdf` · `anexo_fuentes.pdf` | El estudio y el anexo con todas las fuentes consultadas |

## Medido

No hay ground truth para "el mejor plan de IA de una pyme", así que lo que se mide es lo que se puede comprobar en cada lead:

| Qué | Cómo |
|---|---|
| Informe reproducible | `python regenerar.py leads/<carpeta>` vuelve a renderizar desde `extraccion.json` y da el mismo orden y las mismas cifras; corregir una respuesta a mano y regenerar no gasta ninguna llamada |
| Avisos de QA | Ocho reglas fijas sobre cada informe; el revisor lee `qa.txt` antes que el PDF |
| Anclaje | `prueba_lead.py` renderiza el mismo formulario para un tier-1 y para un taller de doce personas y comprueba que las conclusiones se anclan a la empresa, no al sector |
| Páginas | Cada página del PDF se encoge si desborda el A4 y se comprueba el número de páginas al final; un lead de v1 llegaba a una página 2 vacía por un comentario mal cerrado en la plantilla, y eso ya no pasa |
| Fuentes | Las de proveedor se cuentan; si son mayoría, aviso |

Lo que no está medido: la calidad de la investigación frente a un consultor humano. Por eso la revisión antes de enviar es obligatoria y el anexo lleva cada URL.

## Demo en cuatro comandos

```bash
pip install -r requirements.txt && playwright install chromium
cp .env.example .env            # GEMINI_API_KEY, CUSTODIA_ACTOR, contacto del consultor
python app.py                   # → http://127.0.0.1:8091 (formulario) · /panel (leads)
python regenerar.py leads/<carpeta>   # vuelve a renderizar sin repetir la investigación
python tests/test_derivacion.py        # ranking, retorno, avisos de QA y plantilla, sin red
```

La investigación por API es de pago y tarda minutos (tope configurable, 45 por defecto); el formulario responde al instante y el informe se genera en segundo plano. Este repositorio no lleva datos: `leads/` está fuera de git.

## Limitaciones

- La investigación necesita la web, así que no hay modo local para ella: el brief de la empresa sale a Gemini, y Google lo conserva. Es un formulario de diagnóstico, no documentación interna, y así se le dice a la empresa en el propio formulario. Para dato confidencial, este no es el pipeline.
- Sin ground truth sobre la calidad del plan: se mide la reproducibilidad, el anclaje y los avisos, no el acierto.
- La investigación puede citar fuentes flojas. Por eso las de proveedor van al final, se cuentan, y todas van al anexo con su URL.
- El PDF depende de Playwright y Chromium; el ajuste de longitud con un modelo local es opcional y sin él la plantilla recorta con shrink-to-fit.
- Un lead por carpeta y un consultor por instancia: no hay usuarios ni permisos en el panel más allá del actor exigido al arrancar.
- Identidad, eventos y firma van como contrato con un valor local por defecto (variable de entorno, fichero JSONL, clave HMAC). Los adaptadores al Entra ID, SIEM o PKI de una empresa no están aquí ni se pueden probar aquí: ver [docs/INTEGRATION.es.md](docs/INTEGRATION.es.md).

---

## Seguridad y regulación

Los mismos cuatro epígrafes en todos los repositorios. Las filas **hoy** son lo que hace el código. Las filas **cable** son los tres cables de integración que el repositorio trae como contrato (identidad, eventos, firma) y la empresa conecta a sus sistemas: ver [docs/INTEGRATION.es.md](docs/INTEGRATION.es.md). Pruebas locales: `python tests/test_custodia.py`.

| | | |
|---|---|---|
| **Confidencialidad** | El servidor escucha en `127.0.0.1`; `leads/` y `.env` están fuera de git. Lo que sale a Gemini es el brief del formulario y, en la extracción, la investigación ya hecha: dato de diagnóstico, no documentos internos. La investigación corre en modo background, que exige `store=True`: el resultado se recoge después por su ID, así que Google conserva la petición y su resultado según sus términos de servicio. La empresa lo lee en el pie del formulario antes de enviar. | **hoy** |
| **Trazabilidad** | Cada lead guarda lo que dijo la empresa, lo que se pidió, lo que respondió el modelo, el orden calculado y los avisos: seis ficheros que permiten rehacer el PDF sin volver a llamar a nadie. El anexo lleva todas las fuentes con su URL. | **hoy** |
| | **Cable 2 · eventos.** Cada llamada a un modelo (investigación, extracción, longitud) pasa por `custodia/ledger`: una línea JSON con actor, paso, motor, endpoint, si el dato salió, tamaño y hash. Nunca el texto. `logs/custody.jsonl` o stdout. La empresa apunta su SIEM ahí. | **cable** |
| **Prevención de fugas** | El modelo no tiene credenciales; la clave la tiene el proceso y solo ve el brief y la investigación. El panel sirve ficheros de la carpeta del lead y nada más. | **hoy** |
| | **Cable 1 · identidad.** `app.py` se niega a arrancar sin un actor con nombre (`custodia/identity`, por defecto `CUSTODIA_ACTOR`), también si se arranca con uvicorn; el actor se estampa en cada evento y cada firma. La empresa sustituye el proveedor por Entra ID, LDAP, Kerberos o su SSO en una llamada. | **cable** |
| **Humano en el bucle** | El PDF es una propuesta hasta que el consultor lee `qa.txt`, comprueba que las tres intervenciones responden al dolor que contó la dirección, corrige `extraccion.json` si algo contradice la reunión y regenera. El envío es manual, con un correo personal. | **hoy** |
| | **Cable 3 · firma.** `tools/signoff.py sign leads/<carpeta>/informe.pdf` escribe el manifiesto (hash, actor, fecha, firma) y `verify` pasa; un fichero cambiado o una clave distinta fallan. La empresa sustituye la clave HMAC local por su PKI registrando dos funciones. | **cable** |

Marco: EU AI Act (2024/1689) · RGPD · ISO/IEC 42001 · ISO/IEC 27001.

---

## Estructura

```
app.py           servidor FastAPI: formulario, /api/enviar, /api/leads, /panel
regenerar.py     rehace un lead desde extraccion.json (o desde informe.md)
prueba_lead.py   prueba A/B de anclaje: tier-1 frente a taller de doce personas
src/             formulario · research · extraccion · derivacion · longitud · relleno · pdf · anexo · informe
plantillas/      prompt_research.txt · prompt_extraccion.txt · reporte_ia_plantilla.html
static/          index.html (formulario en cuatro pasos) · panel.html (leads del consultor)
docs/            FORMULARIO.md · INTEGRATION.es.md
custodia/        identity · ledger · signoff · cli  — los tres cables de integración
tools/signoff.py · tests/test_custodia.py · tests/test_derivacion.py
leads/           un directorio por reunión — fuera de git
```

Daniel Martín · [epifaneia.dev](https://epifaneia.dev) · Apache-2.0

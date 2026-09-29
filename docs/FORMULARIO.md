# 📋 Formulario v4 — Estudio de viabilidad de IA (modo reunión)

> **Modelo mental:** *la TAREA explica dónde duele; la EMPRESA explica qué es
> realista.* La empresa es el ancla principal del análisis; el sector es contexto.
>
> **Modo reunión:** el formulario se rellena en una **reunión acompañada** por el
> consultor — la fricción no es restricción; 4 pasos = 4 momentos de la reunión.
>
> **Regla de admisión de preguntas:** si una respuesta no puede modificar ROI,
> viabilidad, prioridad o requisitos, la pregunta no merece existir.
>
> **Contrato:** cada pregunta existe en `EmpresaForm` (`src/formulario.py`), se
> captura en `static/index.html` y viaja vía `construir_brief` → `{{BRIEF}}` al
> prompt de research (que arranca con un **Paso 0: perfilado de la empresa**,
> OSINT + fallback territorial sevillano) y al de extracción.

```
static/index.html ──▶ EmpresaForm ──construir_brief──▶ {{BRIEF}}
                                                          │
                       PASO 0 research: FICHA de la empresa (OSINT nombre+web+municipio;
                       sin huella → pyme sevillana del tamaño/sector, suposiciones declaradas)
                                                          │
                       cartera 6-8 calibrada contra la ficha (filtro de plausibilidad
                       organizativa + escalera de cercanía de precedentes)
                                                          │
   InformeIA v2 (ficha + ROI/Viab + cump) ──▶ derivacion √(ROI×Viab) ──▶ PDF
                                                          └─ "Perfil detectado" en Capa 1
```

---

## 🟦 Paso 1 · Quiénes sois
*(La identidad — alimenta el Paso 0 del research.)*

| # | Pregunta | Campo | Control | Qué decisión cambia |
|---|----------|-------|---------|---------------------|
| 1 | **Nombre de la empresa** * | `nombre_empresa` | texto | Ancla del OSINT · encabezado del PDF. |
| 2 | **Municipio** * | `municipio` | texto | Desambigua el OSINT; activa el anclaje territorial (pyme sevillana). |
| 3 | **Página web** (con nudge) | `web` | texto | El mejor input del Paso 0. Copy: *"si la tenéis, el informe sale mucho más afinado"*. |
| 4 | **Personas en la empresa** * | `plantilla` | dropdown `1-5 · 6-20 · 21-50 · 51-250 · +250` | Escala → qué precedentes son cercanos y qué es plausible. |
| 5 | **Cliente principal** * | `cliente_principal` | dropdown (Consumidor final · Pymes · Grandes · AAPP · Mixto) | Exigencia documental, trazabilidad y regulación → viabilidad y requisitos. |
| 6 | **Áreas con equipo interno** | `areas_internas` | checkboxes | Radio de búsqueda de la cartera. |

## 🟦 Paso 2 · Cómo trabajáis
*(La organización — lo que el sistema "entendía regular".)*

| # | Pregunta | Campo | Control | Qué decisión cambia |
|---|----------|-------|---------|---------------------|
| 7 | **¿A qué os dedicáis y cliente ideal?** * | `descripcion` | textarea | Ancla de sector. |
| 8 | **Herramientas habituales** + ¿cuáles? | `herramientas` + `herramientas_detalle` | checkboxes (ERP·CRM·Excel·Google WS·M365·Correo·WhatsApp·Sw propio·Otro) + texto | **El coste real es la integración**: Sage ≠ SAP. La misma oportunidad pasa de viabilidad 9 a 4. El research nombra SUS herramientas ("conector con vuestro Holded"). |
| 9 | **¿Dónde vive la información?** * | `info_vive` | radio ×6 (Papel · PDFs · Excel · ERP/software · **Veteranos** · Mixto) | Madurez del dato → viabilidad, `req_datos`. "Veteranos" captura conocimiento tácito → oportunidades RAG/captura. |
| 10 | **¿Físico vs. digital?** | `fisico_digital` | slider 0-100 | Calidad de información (factor del potencial 1-5). |

## 🟦 Paso 3 · Una oportunidad ya detectada
*(La tarea — intacto de v3, sin acordeón, + dependencia de personas clave.)*

| # | Pregunta | Campo | Control | Qué decisión cambia |
|---|----------|-------|---------|---------------------|
| 11 | **Cuello de botella** * | `cuello_botella` | textarea | **Ancla del dolor** (gana siempre en el "qué duele"). |
| 12 | **¿Qué ocurre si se hace mal?** | `consecuencia_error` | radio 🟢🟡🟠🔴⛔ | Fiabilidad exigida, HITL, filtro de precedentes por riesgo. |
| 13 | **Al pasar de hacer la tarea a solo comprobarla, ¿cuánto ahorráis?** | `coste_verificacion` | radio ⚡🟢⚖️🔴 | **Filtro de apalancamiento**: revisar ≈ hacer → viabilidad ≤3. |
| 14 | **Frecuencia** | `frecuencia` | dropdown | ROI (volumen de ejecuciones). |
| 15 | **Quién la realiza** | `rol_ejecutor` | dropdown | Coste laboral → ROI. |
| 16 | **Reglas vs. criterio experto** | `criterio_experto` | radio 🟢🟡🔴 | Asistencia vs sustitución; % reducción conservador. |
| 17 | **¿Cómo se valida hoy?** | `validacion` | radio | Evaluabilidad → fiabilidad alcanzable. |
| 18 | **Ejemplos correctos existentes** | `ejemplos_historicos` | dropdown | Potencial de entrenamiento/evaluación. |
| 19 | **Si quien más sabe faltara un mes…** 🆕 | `dependencia_clave` | radio 🟢🟡🟠🔴 (Apenas · Dificultades · Se ralentizaría · Bloqueado) | **Riesgo organizativo y concentración de conocimiento** → oportunidades de captura (asistentes, RAG, onboarding) y urgencia. |

## 🟦 Paso 4 · Restricciones y cierre

| # | Pregunta | Campo | Control | Qué decisión cambia |
|---|----------|-------|---------|---------------------|
| 20 | **¿Limitaciones a respetar?** 🆕 | `restricciones` | checkboxes (Datos sensibles · Confidencial · Regulatorio · Certificados · Ninguna) | **Modula el bloque de cumplimiento del PDF** (`cump_*`) y el nivel de cuidado del despliegue → viabilidad y requisitos. |
| 21 | **Capacidad deseada** (opc.) | `capacidad_deseada` | textarea | Contexto secundario — nunca ancla el research. |
| 22 | **Otras empresas similares a la vuestra** (opc.) | `referente` | texto | Precedentes cercanos: el research investiga sus procesos. Sin comparaciones; la empresa líder la busca el research solo. |
| 23-24 | **Nombre + correo** * | `contacto_nombre/email` | texto/email | Routing del entregable. |

---

## Reglas del research que consumen esto (prompt v3)

1. **Paso 0 — Perfilado**: OSINT de `nombre+web+municipio`; con huella → fuente
   principal; sin huella → inferir de ubicación+tamaño+sector+cliente, suposiciones
   declaradas. Sale como **apartado 0 "Perfil detectado"** del informe (y bloque
   propio en Capa 1 del PDF).
2. **Escalera de cercanía**: misma empresa → similar tamaño → similar proceso →
   similar sector → sector general. *El sector solo NO basta*; gigantes solo como
   dirección de mercado.
3. **Filtro de plausibilidad organizativa**: nada que exija capacidades/departamentos/
   infraestructuras/datos que la empresa no tiene, salvo estrategia gradual explícita.
4. **Conflicto formulario↔ficha**: el formulario gana en el *qué duele*; la ficha
   gana en el *quiénes son*.

## Validación

`prueba_lead.py` lleva el **test A/B**: Empresa A (tier-1, +250, PLM/Jira) vs
Empresa B (taller de Sevilla, 12 personas, WhatsApp+Excel), mismo sector. Éxito =
informes radicalmente distintos; si a B le sale ingeniería de requisitos, el anclaje
ha fallado.

## v2 · Preguntas añadidas tras la primera reunión

| # | Pregunta | Campo | Control | Qué decisión cambia |
|---|----------|-------|---------|---------------------|
| 25 | **¿Qué habéis probado ya con IA o automatización, y qué pasó?** (paso 2) | `intentos_previos` | textarea | Adopción y viabilidad: un intento abandonado pesa más que cualquier inferencia. |
| 26 | **Horas a la semana y personas** en la tarea (paso 3) | `horas_semana` · `personas_tarea` | texto | ROI en horas liberadas al mes, no solo en %. |
| 27 | **¿En qué formato llega la información?** (paso 3) | `entrada_formato` | checkboxes (papel · PDF · fotos · audios · mensajes · llamadas · Excel · ERP) | Pipeline y viabilidad: cada formato tiene su coste de captura. |
| 28 | **Restricciones: ¿cuáles exactamente?** (paso 4) | `restricciones_detalle` | texto | El Nivel 0 necesita la norma concreta (9001, IATF, salud…). |
| 29 | **Notas del consultor, una por paso** | `notas_p1` … `notas_p4` | textarea al pie de cada paso | Viajan al brief **dentro de su sección** como información de primera mano que **prevalece**. Sustituyen a la caja única del final. |

Estética v2: paleta sobria, cabecera con el título del estudio, sin precio
ni promesas de captación: el formulario se rellena en la reunión, en el portátil del
consultor, con la dirección delante.

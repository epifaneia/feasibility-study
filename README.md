# feasibility-study · An AI feasibility study for a small business

*Léelo en [español](README.es.md).*

This repository is two complete projects fused into one. The first transfers technical knowledge about what AI can do to someone who does not have it: a form walks them through the questions that matter (who you are, how you work, where it hurts, what must be respected) and, with their answers, commissions a research run from a tool that browses hundreds of public pages on its own and writes a long report with its sources. That report is already usable: research that fits that company, not "the sector". The second turns that dense text, many pages long and written however the tool likes, into a study of ours: with our way of introducing AI tools, our order, our aesthetics and the conclusions we consider relevant, reviewed by a person before it is sent. Form, server, consultant panel and PDF: the whole piece.

> AI carries risk. Code bounds it. The standard answers for what remains.

[Design philosophy](#design-philosophy) · [Where AI adds value](#where-ai-adds-value) · [The five steps](#the-five-steps-in-this-project) · [Measured](#measured) · [Demo](#demo-in-four-commands) · [Limitations](#limitations) · [Security and regulation](#security-and-regulation)

---

## Design philosophy

Every AI application has five steps. Only step 4 invokes a model; the other four are code: reproducible, testable, offline. Step 5 never patches: it flags and degrades. Full text at [epifaneia.dev](https://epifaneia.dev).

```
 1 CLEANING      2 CONTEXT       3 INPUT GUARDRAIL   4 PROCESS        5 OUTPUT GUARDRAIL
 ■ code          ■ code          ■ code              ▲ model          ■ code
```

## Where AI adds value

Telling a small business where AI pays off requires reading: what similar companies did, what worked, what it cost, which tools already exist and at what price. A consultant needs days per company, and a keyword search returns headlines. The model does the only thing only a model can do: autonomous research, what vendors call *deep research*: the model browses hundreds of public pages, decides what to read and what to discard, and writes a long report with its sources. And then, answering concrete questions about that report. The code does everything else: what is researched and with which source hierarchy, which questions are put to the report and in which schema they are answered, how opportunities are ordered, which figures enter the summary, which warnings the reviewer gets, and that the PDF fits its pages and carries no filler text.

---

## The five steps in this project

Each of the two projects goes through the five steps on its own. ★ marks where the improvement lives: the form that bounds the research, and the conversion of the tool's report into ours.

### First · Research: from the form to the report

| Step | What it does here | |
|---|---|---|
| 1 · Cleaning | Empty. The input is the form, and it arrives clean by construction. | |
| 2 · Context | From the form's answers comes an ordered summary: the company is the anchor, the task explains where it hurts, the sector is only context. That summary is inserted into a fixed commissioning text. | |
| 3 · Input guardrail | The four-step form, who you are, how you work, where it hurts, what must be respected, and the required order of sources: institutions and studies first, press next, vendors last. Before the tool starts, which company, which task and which sources are already bounded. | ★ |
| 4 · Process | The research: a tool from the AI provider (what they call *deep research*) browses hundreds of public pages on its own and returns a long report with its sources. | |
| 5 · Output guardrail | Minimal, on purpose: the report is saved whole, as is, with its sources. Nothing is interpreted yet. | |

### Second · Answer: from the tool's report to our study

| Step | What it does here | |
|---|---|---|
| 1 · Cleaning | The report arrives as text. Its cited sources are extracted and ordered by type: institutions, studies, press, vendors. | |
| 2 · Context | The whole report, plus the summary from the first project. The model answers about what was researched, not about what it remembers. | |
| 3 · Input guardrail | Our questions, with a fixed answer format: which opportunities there are, by which route each one is solved (an existing tool, training or a custom build), what it needs and what conditions it has. Scores are anchored to fixed scales, and the internal words of the process are forbidden in the answer. | |
| 4 · Process | One ordinary model call: it answers the questions in that format. Optionally, a local model trims texts that run long. | |
| 5 · Output guardrail | Turning the answers into our study: our narrative, our order, our priorities, our aesthetics. The code orders the opportunities, decides the figures of the summary, hides empty slots, warns the reviewer and checks the pages. The PDF does not leave without human review. | ★ |

### What it produces, and where

| File in `leads/<date>_<company>/` | What it is |
|---|---|
| `form.json` · `brief.txt` · `prompt.txt` | What the company said, ordered, and what the model was asked |
| `informe.md` | The full research, with its sources |
| `extraccion.json` | The answers to our questions, in the closed schema |
| `derivacion.json` · `qa.txt` | The order computed by code and the warnings for the reviewer |
| `informe.pdf` · `anexo_fuentes.pdf` | The study and the annex with every source consulted |

## Measured

There is no ground truth for "the best AI plan for a small business", so what is measured is what can be checked on every lead:

| What | How |
|---|---|
| Reproducible report | `python regenerar.py leads/<folder>` re-renders from `extraccion.json` and yields the same order and the same figures; correcting an answer by hand and regenerating costs no call |
| QA warnings | Eight fixed rules over every report; the reviewer reads `qa.txt` before the PDF |
| Anchoring | `prueba_lead.py` renders the same form for a tier-1 supplier and for a twelve-person workshop and checks that the conclusions anchor to the company, not to the sector |
| Pages | Every PDF page shrinks if it overflows A4 and the page count is checked at the end; a v1 lead used to spill onto an empty page 2 because of an unclosed comment in the template, and that no longer happens |
| Sources | Vendor sources are counted; if they are the majority, a warning |

What is not measured: the quality of the research against a human consultant. That is why review before sending is mandatory and the annex carries every URL.

## Demo in four commands

```bash
pip install -r requirements.txt && playwright install chromium
cp .env.example .env            # GEMINI_API_KEY, CUSTODIA_ACTOR, consultant contact
python app.py                   # → http://127.0.0.1:8091 (form) · /panel (leads)
python regenerar.py leads/<folder>   # re-render without repeating the research
```

Research over the API is paid and takes minutes (configurable cap, 45 by default); the form responds instantly and the report is generated in the background. This repository ships no data: `leads/` is outside git.

## Limitations

- The research needs the web, so there is no local mode for it: the company's brief goes to Gemini. It is an assessment form, not internal documentation, and the form itself tells the company so. For confidential data, this is not the pipeline.
- No ground truth on plan quality: reproducibility, anchoring and warnings are measured, not correctness.
- The research may cite weak sources. That is why vendor sources go last, are counted, and all go to the annex with their URL.
- The PDF depends on Playwright and Chromium; the length adjustment with a local model is optional and without it the template trims with shrink-to-fit.
- One lead per folder and one consultant per instance: no users or permissions in the panel beyond the actor required at startup.
- Identity, events and sign-off ship as a contract with a local default (environment variable, JSONL file, HMAC key). The adapters to a company's Entra ID, SIEM or PKI are not here and cannot be tested here: see [docs/INTEGRATION.md](docs/INTEGRATION.md).

---

## Security and regulation

The same four headings in every repository. **today** rows are what the code does. **wire** rows are the three integration wires the repository ships as a contract (identity, events, sign-off) that the company connects to its own systems: see [docs/INTEGRATION.md](docs/INTEGRATION.md). Local tests: `python tests/test_custodia.py`.

| | | |
|---|---|---|
| **Confidentiality** | The server listens on `127.0.0.1`; `leads/` and `.env` are outside git. What goes to Gemini is the form's brief and, at extraction, the research already done: assessment data, not internal documents. The company reads this in the form's footer before submitting. | **today** |
| **Traceability** | Every lead keeps what the company said, what was asked, what the model answered, the computed order and the warnings: six files that allow the PDF to be rebuilt without calling anyone again. The annex carries every source with its URL. | **today** |
| | **Wire 2 · events.** Every model call (research, extraction, length) goes through `custodia/ledger`: one JSON line with actor, step, engine, endpoint, whether data left, size and hash. Never the text. `logs/custody.jsonl` or stdout. The company points its SIEM there. | **wire** |
| **Leak prevention** | The model has no credentials; the process holds the key and only sees the brief and the research. The panel serves files from the lead's folder and nothing else. | **today** |
| | **Wire 1 · identity.** `app.py` refuses to start without a named actor (`custodia/identity`, by default `CUSTODIA_ACTOR`), also when started with uvicorn; the actor is stamped on every event and every signature. The company replaces the provider with Entra ID, LDAP, Kerberos or its SSO in one call. | **wire** |
| **Human in the loop** | The PDF is a proposal until the consultant reads `qa.txt`, checks that the three interventions answer the pain management described, corrects `extraccion.json` if anything contradicts the meeting and regenerates. Sending is manual, with a personal email. | **today** |
| | **Wire 3 · sign-off.** `tools/signoff.py sign leads/<folder>/informe.pdf` writes the manifest (hash, actor, date, signature) and `verify` passes; a changed file or a different key fails. The company replaces the local HMAC key with its PKI by registering two functions. | **wire** |

Framework: EU AI Act (2024/1689) · GDPR · ISO/IEC 42001 · ISO/IEC 27001.

---

## Structure

```
app.py           FastAPI server: form, /api/enviar, /api/leads, /panel
regenerar.py     rebuilds a lead from extraccion.json (or from informe.md)
prueba_lead.py   A/B anchoring test: tier-1 supplier vs twelve-person workshop
src/             formulario · research · extraccion · derivacion · longitud · relleno · pdf · anexo · informe
plantillas/      prompt_research.txt · prompt_extraccion.txt · reporte_ia_plantilla.html
static/          index.html (four-step form) · panel.html (consultant's leads)
docs/            FORMULARIO.md · INTEGRATION.md
custodia/        identity · ledger · signoff · cli  — the three integration wires
tools/signoff.py · tests/test_custodia.py
leads/           one directory per meeting — outside git
```

Daniel Martín · [epifaneia.dev](https://epifaneia.dev) · Apache-2.0

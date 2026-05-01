# Hackathon — del boilerplate a tu app

Esta es la guía para **forkear AgentOS y construir tu app específica encima**. AgentOS te da la plataforma; vos pones el dominio del problema.

> **Tiempo objetivo**: MVP demoeable en 90 minutos. Demo pulida en 4-6 horas.

---

## Modelo mental

```
                  ┌─────────────────────────────────┐
                  │   YOUR HACKATHON APP            │
                  │   (domain logic + UX final)     │
                  └─────────────────────────────────┘
                              │
                              │  uses
                              ▼
┌─────────────────────────────────────────────────────────┐
│                     AGENTOS BOILERPLATE                  │
│  • Multi-agent reasoning (LangGraph + CrewAI)            │
│  • Auto-failover LLM cascade (Groq → OpenRouter → Gemini)│
│  • RAG, ML, Geo, Reports, Auth, Rate limit               │
│  • 3 frontends, 4 backends, deploy 100% gratis           │
└─────────────────────────────────────────────────────────┘
```

Vos no escribís un chatbot desde cero. **Conectás tu dominio** con agentes que ya razonan, fallan limpio, y se streamean.

---

## El path de 90 minutos

### Paso 1 — Fork (5 min)

```bash
gh repo fork <agentos-repo> --clone --remote
cd AgentOS
cp .env.example .env
# Pegá GROQ_API_KEY (gratis en console.groq.com)
pnpm install
pip install -e packages/llm packages/agents services/api
```

### Paso 2 — Decidí qué app vas a hacer (10 min)

Patrones que funcionan en hackatones:

| Vertical | Ejemplo concreto | Qué reusas de AgentOS |
|----------|------------------|----------------------|
| **Document QA** | "Súbeme tu contrato y respondo preguntas" | RAG + chat agent |
| **Data analyst** | "Súbeme un CSV y dame insights" | data + ml + analyst crew |
| **Research assistant** | "Investigá X y generá un reporte PDF" | research graph + reports |
| **Geo-aware** | "Encontrá los X más cercanos a mí" | geo + map UI |
| **Anomaly monitor** | "Detectá outliers en estos logs" | ml/anomaly + alerts |
| **Domain agent** | "Asistente para [médicos/abogados/...]" | chat agent + domain prompts |
| **Multi-agent dashboard** | Procurement / Operations agents working in parallel | crews + UI multi-panel |

Pickea **uno**. No hagas dos. Foco brutal.

### Paso 3 — Customizar el agente (30 min)

Edita un solo archivo: `packages/agents/agentos_agents/nodes/responder.py` (o crea uno nuevo). Acá pones tu **system prompt domain-specific**:

```python
# packages/agents/agentos_agents/nodes/responder.py

RESPONDER_SYSTEM = """Eres MediBot, un asistente médico que ayuda a triage de síntomas.

Reglas:
1. NUNCA dar diagnóstico definitivo. Recomendá siempre consultar profesional.
2. Hacé 1-2 preguntas de seguimiento antes de sugerir gravedad.
3. Si los síntomas son urgencia (dolor torácico, dificultad respirar, ...) → decir "URGENCIA: llamar emergencias" en la primera línea.
4. Tono: claro, empático, sin jerga médica.
"""
```

Eso es todo. Tu agente ya pasa por failover de 3 providers, ya está visible en el agent trace, ya streamea tokens.

### Paso 4 — Customizar la UI (20 min)

Pickeá UN frontend. Editá `apps/web-svelte/src/routes/+page.svelte` (o el equivalente Next/Vue):

1. **Cambiar el title y subtitle**:
   ```svelte
   <h1>MediBot</h1>
   <p>Triage de síntomas con AI</p>
   ```

2. **Cambiar los presets** (los 4 botones del estado vacío):
   ```svelte
   const PRESETS = [
     { label: "Dolor de cabeza", task: "Tengo dolor de cabeza desde ayer..." },
     { label: "Fiebre", task: "Tengo 38.5°C de fiebre..." },
     { label: "Dolor abdominal", task: "Me duele la barriga..." },
     { label: "Tos persistente", task: "Tengo tos hace 2 semanas..." },
   ];
   ```

3. **Cambiar el branding** (color primario):
   ```css
   /* apps/web-svelte/src/app.css */
   --color-primary-600: #c92a2a;  /* rojo médico */
   --color-primary-700: #b71c1c;
   ```

4. **Logo**: editar `apps/web-svelte/static/favicon.svg` y la letra del header.

### Paso 5 — Demo (5 min)

```bash
cd services/api && uvicorn app.main:app --reload &
pnpm dev:svelte
```

Abrí `http://localhost:5173` → enviá una pregunta → ves el panel lateral con los nodos del agente (router → responder) razonando.

### Paso 6 — Deploy (20 min)

Seguí [DEPLOY.md](DEPLOY.md). El primer deploy lleva ~15 min entre crear cuentas y configurar secrets. Los siguientes son `git push`.

---

## Customizaciones más pedidas

### A) Agregar conocimiento específico (RAG)

Si tu app necesita responder con info de docs específicos (manuales, contratos, FAQ):

```bash
# 1. Subir cada doc a la API
for f in docs/*.txt; do
  curl -X POST http://localhost:8000/rag/ingest -F "file=@$f"
done

# 2. Modificar el responder para que use RAG antes de responder
```

```python
# packages/agents/agentos_agents/nodes/responder.py
from agentos_rag import RAGPipeline

_rag = RAGPipeline()

async def responder_stream(state, factory):
    query = state.get("query", "")
    # Trae 3 chunks relevantes
    chunks = await _rag.query(query, top_k=3)
    context = "\n\n".join(f"[{c['score']:.2f}] {c['content']}" for c in chunks)

    adapter = factory.get(state.get("cascade") or "speed")
    async for token in adapter.stream(messages=[
        {"role": "system", "content": f"{RESPONDER_SYSTEM}\n\nContexto relevante:\n{context}"},
        {"role": "user", "content": query},
    ]):
        yield token
```

### B) Conectar tu propio dataset

Si trabajás con un CSV, JSON, o API externa:

```python
# services/api/app/routers/my_data.py
from fastapi import APIRouter
from agentos_data import frames

router = APIRouter()

@router.get("/insights/{region}")
async def insights(region: str):
    df = frames.load("data/sales.csv")
    filtered = df[df["region"] == region]
    return {
        "data": {
            "summary": frames.summary(filtered),
            "trend": filtered["sales"].rolling(7).mean().tolist(),
        },
        "error": None,
    }
```

Y registrarlo en `main.py`:
```python
from .routers import my_data
app.include_router(my_data.router, prefix="/insights", tags=["insights"])
```

### C) Agente que decide cuándo usar tools

Si querés tool-calling al estilo "el agente decide consultar la base":

```python
# Crear un router enriquecido
ROUTER_SYSTEM = """Clasificá la intent en una de:
- "weather": consulta meteorológica → tool=fetch_weather
- "stock": precio de acción → tool=fetch_stock
- "chat": conversación normal

Respondé JSON: {"intent":"...", "tool_args":{...}}
"""
```

Y en el orchestrator, switch sobre el `intent` para llamar al tool correcto antes del responder. Patrón clásico de ReAct.

### D) Multi-agent visible (el "wow factor" de AgentOS)

Para una demo impactante, mostrá los agentes trabajando en paralelo:

1. Usar `engine: "research"` para que se vea router → researcher → analyst → writer
2. En el panel lateral, cada nodo cambia de color cuando está activo (ya implementado en los 3 frontends)
3. **Truco**: agregá `await asyncio.sleep(0.5)` entre nodos del runner para que el usuario vea el progreso (en demo, NO en prod)

### E) Branding y theme

Editá el preset compartido `packages/ui/tailwind-preset.ts` — cambia colores en un solo lugar y los 3 frontends se actualizan.

---

## Anti-patrones (lo que NO hacer en hackatón)

| ❌ NO | ✅ SÍ |
|-------|-------|
| Reescribir el LLMFactory para "tener control" | Usar `cascade="reasoning"` y listo |
| Borrar packages que "no usás" | Dejarlos, no estorban; mañana podrías necesitarlos |
| Hacer 3 frontends "para demostrar versatilidad" | UNO solo, pulido al máximo |
| Hardcodear API keys "para ir más rápido" | `.env` desde el principio. 30 segundos extra te ahorran que se filtren |
| "Voy a integrar mi DB custom" | Supabase + RLS te da auth + DB + realtime gratis |
| Construir auth desde cero | Supabase Auth (`@supabase/auth-ui-react` o equivalente Svelte/Vue) |
| Ignorar el smoke test hasta la demo | `scripts/e2e_smoke.py` corre en 8 segundos. Hacelo cada commit |
| Empezar el deploy 30 min antes de la presentación | Deploy en hora 1. Las últimas 3 horas son polish |

---

## Demo script (5 min de presentación)

Plantilla que funciona:

**Minuto 1 — El problema** (sin mencionar AI todavía)
> "Hoy un [médico/abogado/analista] gasta X horas en Y. Eso cuesta Z al año en una clínica/firma promedio."

**Minuto 2 — La solución, en vivo**
> "Mirá lo que pasa cuando le pregunto a [TuApp] sobre [caso real]"
> Abrí la UI. Hacé la pregunta. Mostrá:
> - Token streaming desde el primer carácter (latencia percibida <500ms gracias a Groq)
> - Panel lateral con el agent trace (no es black box: ves QUÉ decide y POR QUÉ)
> - Si tenés RAG: mostrá que cita las fuentes

**Minuto 3 — Lo que hay debajo** (tech credibility)
> "Esto corre 3 LLM providers con failover automático. Si uno cae, el usuario no se entera.
> Está deployado en Koyeb + Vercel + Supabase, costo $0/mes."
> Abrí `https://agentos-api.koyeb.app/health` → mostrar los 3 UP.
> Forzá un fallo: temporariamente revocá la key de Groq → re-pregunta → sigue respondiendo (vía OpenRouter).

**Minuto 4 — Multi-agent**
> "Si la pregunta es compleja, no es un solo modelo: es un pipeline de 4 agentes especializados."
> Hacé una pregunta tipo `engine="research"`. Mostrá el agent trace ejecutándose paso a paso.

**Minuto 5 — Cierre + ask**
> "En 4 horas pasé de cero a esto. La plataforma debajo es AgentOS, open source, lista para forkear.
> Pregunta para ustedes: ¿en qué dominio les gustaría ver esto aplicado?"

---

## Submission checklist

Antes de subir a la plataforma del hackathon:

- [ ] **README del proyecto** apunta a `AgentOS` como base + describe el cambio específico tuyo
- [ ] **Demo URL** funciona en incógnito desde móvil (probálo)
- [ ] **Video de 60s** mostrando el flujo principal (Loom o similar)
- [ ] **Repo público** con tu fork + commit history visible
- [ ] **Architecture diagram** (podés reusar el de [docs/ARCHITECTURE.md](ARCHITECTURE.md))
- [ ] **License** declarada (MIT por defecto, perfecto para hackathon)
- [ ] **Equipo + roles** listados
- [ ] **Cómo correr local** en una sección "Quick start" (5 comandos máx)

---

## Recursos

- [README.md](../README.md) — overview general
- [USAGE.md](USAGE.md) — API + ejemplos + cómo extender
- [DEPLOY.md](DEPLOY.md) — paso a paso a producción
- [ARCHITECTURE.md](ARCHITECTURE.md) — diagrama del sistema
- [SYSTEM_PROMPT.md](SYSTEM_PROMPT.md) — prompt para usar Claude/GPT en el proyecto

**Comunidad / Feedback**: si AgentOS te ayudó a ganar (o no), abrí un issue contando el caso. Eso ayuda a mejorar el boilerplate para el siguiente hackathon.

---

## TL;DR

```bash
gh repo fork agentos --clone
cp .env.example .env  # poner GROQ_API_KEY
pnpm install && pip install -e packages/llm services/api
# Editá responder.py con tu system prompt
# Editá +page.svelte con tu branding
pnpm dev:svelte
# → demo lista
```

Forkear, customizar prompt, customizar UI, deploy. **Ese es el camino corto.**

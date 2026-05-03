# Usage — AgentOS hands-on

Cómo usar cada pieza del boilerplate. Todos los ejemplos son copy-paste.

**Asumimos**:
- Backend en `http://localhost:8000` (o `https://agentos-api.koyeb.app` en prod)
- `.env` con las 3 LLM keys configuradas

---

## Setup local (5 min)

```bash
# 1. Clonar y entrar
git clone <tu-fork>
cd AgentOS

# 2. Env vars
cp .env.example .env
# Editar .env y poner al menos GROQ_API_KEY (los otros 2 son opcionales)

# 3. Workspace JS (frontends + types)
pnpm install

# 4. Packages Python (editable mode)
pip install -e packages/llm
pip install -e packages/agents
pip install -e packages/rag
pip install -e packages/data
pip install -e packages/ml
pip install -e packages/geo
pip install -e packages/reports
pip install -e services/api[dev]

# 5. (Opcional) Postgres + pgvector + PostGIS local
docker compose up -d supabase-db
```

Arrancar todo:

```bash
# Terminal 1 — Backend Python
cd services/api && uvicorn app.main:app --reload

# Terminal 2 — Frontend (elegir uno)
pnpm dev:svelte    # → http://localhost:5173
pnpm dev:next      # → http://localhost:3000
pnpm dev:vue       # → http://localhost:3001

# Terminal 3 (opcional) — Backend Go
cd apps/api-go && go run cmd/server/main.go    # → :8080

# Terminal 4 (opcional) — Bot Telegram
cd apps/telegram && python bot.py
```

Verificar que todo arrancó:

```bash
python scripts/e2e_smoke.py
# → 4/4 checks passed.
```

---

## API Reference (FastAPI)

Todas las respuestas siguen `{data, error, meta}` excepto las de SSE streaming. Todos los streams emiten eventos JSON con shape:
```ts
{ type: "status" | "token" | "crew_status" | "done" | "error", ... }
```

### `GET /health`

Estado de los 3 providers + circuit breaker:

```bash
curl http://localhost:8000/health
```
```json
{
  "status": "ok",
  "providers": {
    "groq":       {"registered": true, "available": true,  "failures": 0},
    "openrouter": {"registered": true, "available": true,  "failures": 0},
    "gemini":     {"registered": true, "available": false, "failures": 3}
  },
  "timestamp": 1777655561
}
```
- `status` ∈ `{ok, degraded, down}` — `degraded` cuando al menos un provider está caído pero queda alguno UP
- `failures: 3` con `available: false` significa que el circuit breaker abrió ese provider por 60s

---

### `POST /chat/stream` — chat con LangGraph

Decide intent automáticamente: `chat` (responder simple) vs `research/analysis/writing` (pipeline completo).

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola, ¿qué puedes hacer?"}'
```

Eventos emitidos (chat simple):
```
data: {"type": "status", "node": "router", "content": "Classifying intent..."}
data: {"type": "status", "node": "router", "content": "intent: chat"}
data: {"type": "status", "node": "responder", "content": "Generating response"}
data: {"type": "token", "content": "Hola"}
data: {"type": "token", "content": "! "}
...
data: {"type": "done"}
```

Para forzar pipeline research/analysis:
```json
{"message": "...", "context_type": "research"}
```

---

### `POST /agents/run` — orchestrator multi-engine

Permite elegir explícitamente engine y cascade:

```bash
# LangGraph research pipeline (researcher → analyst → writer)
curl -N -X POST http://localhost:8000/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Compare pgvector vs FAISS for production RAG",
    "engine": "research",
    "cascade": "reasoning"
  }'

# CrewAI analysis crew
curl -N -X POST http://localhost:8000/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze this quarter sales drop",
    "engine": "crew",
    "crew": "analysis"
  }'

# CrewAI writer crew (2 agents: outliner → writer)
curl -N -X POST http://localhost:8000/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write a 200-word blog post about LangGraph",
    "engine": "crew",
    "crew": "writer",
    "context": {"style": "casual technical"}
  }'
```

| `engine` | Cuándo usar |
|----------|-------------|
| `graph` (default) | Chat normal con routing automático por intent |
| `research` | Forzar el pipeline completo: researcher → analyst → writer |
| `crew` | CrewAI sequential (más estructurado, más lento, mejor para outputs largos) |

---

### `POST /agents/complete` — completion sync (no SSE)

Cuando necesitás una respuesta JSON directa (útil para Go API o tools internos):

```bash
curl -X POST http://localhost:8000/agents/complete \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role":"user","content":"Suma 2+2 y devolvé solo el número"}],
    "cascade": "speed",
    "max_tokens": 50
  }'
```
```json
{
  "data": {
    "content": "4",
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",
    "usage": {"prompt_tokens": 24, "completion_tokens": 1},
    "latency_ms": 187.4
  },
  "error": null
}
```

Cuando todos los providers fallan, devuelve `503` con:
```json
{"data": null, "error": "all_providers_failed", "meta": {"detail": "..."}}
```

---

### `POST /rag/ingest` — subir documento al vector store

```bash
curl -X POST http://localhost:8000/rag/ingest \
  -F "file=@mi_documento.txt"
```
```json
{"data": {"chunks_created": 12}, "error": null}
```

### `POST /rag/search` — búsqueda semántica con filtros

```bash
# Búsqueda simple
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "what is pgvector", "top_k": 3}'

# Con filters (key-value sobre metadata)
curl -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "top_k": 5, "filters": {"tenant_id": "acme", "lang": ["en", "es"]}}'
```
```json
{
  "data": [
    {"id": "...", "content": "pgvector is...", "score": 0.87, "metadata": {...}}
  ],
  "error": null,
  "meta": {"top_k": 3, "count": 1}
}
```

### `POST /rag/ingest-text` — ingesta programática

Para ingestar desde otro servicio sin file upload:
```bash
curl -X POST http://localhost:8000/rag/ingest-text \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"id": "doc-1", "content": "...", "metadata": {"source": "manual"}}
    ],
    "metadata_defaults": {"tenant_id": "acme"}
  }'
```

### `DELETE /rag/source/{source_id}` — borrar todos los chunks de un doc

```bash
curl -X DELETE http://localhost:8000/rag/source/doc-1
# → {"data": {"deleted": 12}, "error": null}
```

> En dev local usa FAISS (in-memory, se pierde al reiniciar). Setear `VECTOR_BACKEND=pgvector` + `DATABASE_URL` para persistencia en Supabase. La chunking es **sentence-aware** por defecto: respeta puntos y signos en vez de cortar a media palabra.

---

### `POST /data/upload` y `POST /data/analyze`

```bash
curl -X POST http://localhost:8000/data/upload \
  -F "file=@ventas.csv"
# → {"data": {"shape":[1000,5], "columns":[...], "describe":{...}}, "error":null}
```

---

### `POST /geo/geocode` — dirección → lat/lon

```bash
curl -X POST http://localhost:8000/geo/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "Ciudad de México"}'
# → {"data": {"lat":19.43,"lon":-99.13,"label":"México, ..."}, "error":null}
```

### `POST /geo/reverse`

```bash
curl -X POST http://localhost:8000/geo/reverse \
  -H "Content-Type: application/json" \
  -d '{"lat": 19.43, "lon": -99.13, "radius_km": 5}'
```

---

### `POST /ml/anomalies` — detección de anomalías sobre CSV

```bash
curl -X POST "http://localhost:8000/ml/anomalies?method=isolation_forest&contamination=0.1" \
  -F "file=@dataset.csv"
```
```json
{
  "data": {
    "total_rows": 5000,
    "anomalies_found": 487,
    "results": [{"index": 12, "score": -0.42, "is_anomaly": true}, ...]
  },
  "error": null
}
```

`method` ∈ `{isolation_forest, lof}`.

---

### `POST /reports/generate` — HTML→PDF

```bash
curl -X POST http://localhost:8000/reports/generate \
  -H "Content-Type: application/json" \
  -o reporte.pdf \
  -d '{
    "title": "Q4 Sales Analysis",
    "description": "Generated by AgentOS",
    "summary": "Sales grew 12% YoY...",
    "metrics": [
      {"label":"Revenue","value":"$1.2M"},
      {"label":"Growth","value":"+12%"}
    ],
    "table_columns": ["Region","Sales"],
    "table_data": [{"Region":"NA","Sales":"$500K"},{"Region":"EU","Sales":"$700K"}]
  }'
```

> En Windows local, WeasyPrint requiere GTK. En Docker (Koyeb prod) está incluido.

---

### `POST /notify/send` — enviar notificación (Telegram + Email)

Envía a múltiples canales en paralelo. Cada canal lee su config de env vars:
- **Telegram**: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_IDS`
- **Email**: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_RECIPIENTS`

```bash
# Enviar a todos los canales configurados
curl -X POST http://localhost:8000/notify/send \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Anomaly detected",
    "body": "12 outliers found in last 1h batch",
    "severity": "warning"
  }'

# Solo Telegram, con destinatario override
curl -X POST http://localhost:8000/notify/send \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Job complete",
    "body": "Report ready",
    "channels": ["telegram"],
    "recipients": {"telegram": ["123456789"]}
  }'
```
```json
{
  "data": [
    {"channel":"telegram","delivered":true,"detail":"sent to 1/1 chats","latency_ms":124},
    {"channel":"email","delivered":true,"detail":"sent to 1 recipient(s)","latency_ms":890}
  ],
  "error": null
}
```

`severity` ∈ `{info, warning, error, critical}` — afecta el prefijo del título.

### `GET /notify/channels` — qué canales están configurados

```bash
curl http://localhost:8000/notify/channels
# → {"data":{"configured":["telegram"],"all":["telegram","email","slack","discord","webhook"]},"error":null}
```

> **Patrón típico**: tu agente detecta algo importante (anomaly, failure, completion) → llama a `/notify/send` desde un nodo. Los usuarios configuran sus chats Telegram + emails una vez y reciben alertas sin abrir la app.

---

### Database — conectar AgentOS a TU base de datos

Distinto de Supabase (que usa AgentOS internamente). Apuntá `DATABASE_URL_USER` a tu Postgres/MySQL/SQLite y los agentes podrán consultarla.

```env
DATABASE_URL_USER=postgresql://user:pass@host:5432/mydb
# o mysql://..., sqlite:///./local.db
```

#### `GET /database/schema` — introspección

```bash
curl http://localhost:8000/database/schema
# → {"data":[{"name":"users","columns":[...],"foreign_keys":[...]},...],"error":null}
```

#### `POST /database/query` — SQL directo (read-only por defecto)

```bash
curl -X POST http://localhost:8000/database/query \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT count(*) AS users FROM users"}'
```
- Bloquea `INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/...` automáticamente
- Bloquea multi-statements (`SELECT ...; DROP TABLE`)
- Inyecta `LIMIT 500` si la query es SELECT sin LIMIT
- Soporta params: `{"sql":"SELECT * FROM users WHERE id = :id","params":{"id":1}}`

#### `POST /database/nl-query` — pregunta en lenguaje natural → SQL

El LLM recibe el schema como contexto, genera SELECT, lo ejecuta read-only:

```bash
curl -X POST http://localhost:8000/database/nl-query \
  -H "Content-Type: application/json" \
  -d '{"question":"How many users signed up last week?","cascade":"reasoning"}'
```
```json
{
  "data": {
    "sql": "SELECT count(*) FROM users WHERE created_at > now() - interval '7 days'",
    "columns": ["count"],
    "rows": [{"count": 42}]
  },
  "error": null,
  "meta": {"row_count": 1, "elapsed_ms": 23, "provider": "gemini", "model": "gemini-2.5-flash"}
}
```

> **Seguridad**: el ejecutor está siempre en read-only mode para `nl-query`. La SQL generada por el LLM se valida antes de ejecutarse — si intenta cualquier DML/DDL, devuelve `400 unsafe_query` sin tocar la base.

---

## API Reference (Go — `apps/api-go`)

Mismas rutas pero bajo `/api/v1/*` y con auth JWT opcional. Por defecto proxea al FastAPI; con `LLM_DIRECT=true` llama directo a Groq para latencia mínima.

```bash
# Health (proxea al FastAPI + agrega service tag)
curl http://localhost:8080/health

# Sync completion (más rápido si LLM_DIRECT=true)
curl -X POST http://localhost:8080/api/v1/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hola", "system": "Sé conciso"}'

# Chat SSE (proxy a FastAPI, mantiene streaming)
curl -N -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola"}'
```

Con `AUTH_REQUIRED=true`, todas las rutas bajo `/api/v1/*` exigen `Authorization: Bearer <jwt-supabase>`.

---

## Frontends — patrones por framework

Los 3 frontends tienen UX idéntica, solo cambia el state management. Todos chatean contra el endpoint **proxy** local (`/api/chat`) que reenvía al FastAPI y maneja CORS + secrets.

### SvelteKit (`apps/web-svelte`)

```svelte
<script lang="ts">
  import { chat } from "$lib/stores/chat.svelte";
  // chat.send(msg, mode) → dispara SSE, actualiza store reactivo
  // chat.messages       → array de mensajes
  // chat.streaming      → bool, true durante el stream
  // chat.currentNode    → "router" | "researcher" | ...
</script>
```

### Next.js (`apps/web-next`)

```tsx
"use client";
import { useChatStore } from "@/lib/store";

export function MyChat() {
  const { messages, streaming, send } = useChatStore();
  return <button onClick={() => send("hola", "chat")}>...</button>;
}
```

### Nuxt 3 (`apps/web-vue`)

```vue
<script setup lang="ts">
import { useChatStore } from "~/stores/chat";
const chat = useChatStore();
// chat.send(...), chat.messages, chat.streaming
</script>
```

---

## Llamar desde código externo

### TypeScript / Node

```ts
const res = await fetch("https://agentos-api.koyeb.app/agents/complete", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    messages: [{ role: "user", content: "..." }],
    cascade: "speed",
  }),
});
const { data } = await res.json();
console.log(data.content, "from", data.provider);
```

### Streaming (SSE) en TS

```ts
const res = await fetch("/api/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "hola", context_type: "chat" }),
});
const reader = res.body!.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split("\n");
  buffer = lines.pop() ?? "";
  for (const line of lines) {
    if (!line.startsWith("data: ")) continue;
    const event = JSON.parse(line.slice(6));
    if (event.type === "token") process.stdout.write(event.content);
  }
}
```

### Python

```python
import httpx, json

async def chat(message: str):
    async with httpx.AsyncClient() as c:
        async with c.stream("POST", "http://localhost:8000/chat/stream",
                             json={"message": message}) as r:
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    if event["type"] == "token":
                        print(event["content"], end="", flush=True)
```

---

## LLM cascade — cuándo usar cada strategy

Definidas en [`packages/llm/agentos_llm/config.py`](../packages/llm/agentos_llm/config.py:5):

| Strategy | Orden de providers | Casos de uso |
|----------|--------------------|--------------|
| `speed` | Groq → OpenRouter → Gemini | Chat, clasificación, primeros tokens en <300ms |
| `reasoning` | Gemini → OpenRouter → Groq | Análisis profundo, planning, multi-step reasoning |
| `cheap` | OpenRouter → Groq → Gemini | Trabajo en background a alto volumen |
| `multimodal` | Gemini | Imagen + texto, video, structured docs |
| `quality` | OpenRouter (GLM-4.5 Air, gpt-oss-120b, DeepSeek, Qwen, Hermes-405B) → Gemini → Groq | Extraer detalle de contexto largo, comparaciones a fondo, tablas multi-columna |

**Auto-pick (writer + responder)**: ambos nodos usan [`pick_cascade()`](../packages/agents/agentos_agents/cascade.py:1) para auto-seleccionar:

1. Si el caller pasa un `cascade` explícito → ese gana.
2. Si el web context tiene body extraído → `quality` (modelo grande para extraer detalle).
3. Si la query es compleja (matches `compara`, `diferencia`, `analiza`, `tabla`, `paso a paso`, `código`, `arquitectura`, `step by step`, etc., o es multi-oración o >120 chars) → `quality`.
4. Si nada de lo anterior → `speed`.

**Regla práctica**: si forzás cascade desde el caller (`/agents/run` con `"cascade":"reasoning"`), respeta tu elección. Si no lo forzás (chat común), se elige sola por la query. **Siempre llamar via `LLMFactory.complete_with_fallback()` o `stream_with_fallback()`** — nunca instanciar adapters directos.

---

## Multi-agent flow detallado (LangGraph)

```
START
  │
  ▼
┌──────────────┐
│   ROUTER     │  classifies intent → "chat" | "research" | "analysis" | "writing"
└──────────────┘
  │
  ├─ intent=chat ─────────────► ┌───────────┐
  │                             │ RESPONDER │ → END (token streaming)
  │                             └───────────┘
  │
  └─ intent=research/analysis/writing ─┐
                                       ▼
                              ┌──────────────┐
                              │  RESEARCHER  │ → state.findings
                              └──────────────┘
                                       │
                                       ▼
                              ┌──────────────┐
                              │   ANALYST    │ → state.analysis
                              └──────────────┘
                                       │
                                       ▼
                              ┌──────────────┐
                              │    WRITER    │ → token streaming → END
                              └──────────────┘
```

Cada nodo emite eventos `{type: "status", node: <name>, content: <description>}` antes y después de ejecutar. Solo el nodo final hace `{type: "token", content: <chunk>}` para que el usuario vea reasoning + respuesta en orden.

---

## Extender — agregar un nuevo agente

### Caso 1: nuevo nodo en el grafo de chat

1. Crear `packages/agents/agentos_agents/nodes/my_agent.py`:
   ```python
   from agentos_llm import LLMFactory
   from ..state import AgentState

   async def my_agent_node(state: AgentState, factory: LLMFactory) -> AgentState:
       response = await factory.complete_with_fallback(
           messages=[
               {"role": "system", "content": "Sos un experto en X..."},
               {"role": "user", "content": state["query"]},
           ],
           cascade="reasoning",
       )
       return {"my_field": response.content}
   ```
2. Registrarlo en `nodes/__init__.py`
3. Agregarlo a `graphs/runner.py` o `graphs/chat.py` con la transición que corresponda
4. Actualizar `state.py` si necesita un nuevo campo

### Caso 2: nueva crew de CrewAI

1. Crear `packages/agents/agentos_agents/crews/my_crew.py`:
   ```python
   from crewai import Agent, Crew, Process, Task
   from .base import BaseCrew

   class MyCrew(BaseCrew):
       def kickoff(self, inputs):
           agent = Agent(
               role="Expert Y",
               goal="Do Z",
               llm=self.llm,  # ¡pasa por LLMFactory automáticamente!
               backstory="...",
           )
           task = Task(description=inputs["query"], expected_output="...", agent=agent)
           crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
           return str(crew.kickoff(inputs))
   ```
2. Registrarla en `crews/__init__.py` y `crews/runner.py` (mapping `_select_crew`)
3. Llamarla con:
   ```bash
   curl -N -X POST .../agents/run \
     -d '{"task":"...","engine":"crew","crew":"my_crew"}'
   ```

---

## Extender — agregar un nuevo endpoint

1. Crear router en `services/api/app/routers/my_feature.py`:
   ```python
   from fastapi import APIRouter, Request
   from pydantic import BaseModel

   router = APIRouter()

   class MyRequest(BaseModel):
       input: str

   @router.post("/do-thing")
   async def do_thing(body: MyRequest, request: Request):
       factory = request.app.state.llm_factory
       result = await factory.complete_with_fallback(
           messages=[{"role": "user", "content": body.input}],
           cascade="speed",
       )
       return {"data": {"output": result.content}, "error": None}
   ```
2. Importarlo en `services/api/app/main.py`:
   ```python
   from .routers import ... , my_feature
   app.include_router(my_feature.router, prefix="/my", tags=["my"])
   ```
3. Probar:
   ```bash
   curl -X POST http://localhost:8000/my/do-thing -H "Content-Type: application/json" -d '{"input":"hola"}'
   ```

---

## Tests

```bash
# Unit tests (LLM factory + circuit breaker + agent graph runner)
python -m pytest packages/llm/tests packages/agents/tests/test_graph_runner.py -q
# → 17 passed

# Smoke E2E contra el backend corriendo
python scripts/e2e_smoke.py
# → 4/4 checks passed

# Smoke contra prod
BACKEND_URL=https://agentos-api.koyeb.app python scripts/e2e_smoke.py
```

---

## Telegram bot

Una vez configurado `TELEGRAM_BOT_TOKEN` y arrancado `python apps/telegram/bot.py`:

| Comando | Acción |
|---------|--------|
| `/start` | Mensaje de bienvenida con lista de comandos |
| `/ask <pregunta>` | Chat normal (LangGraph chat path) |
| `/research <tema>` | Pipeline completo researcher → analyst → writer |
| `/report <tema>` | Genera el research + lo convierte a PDF y lo envía |
| `/status` | Muestra estado de los 3 providers |
| (texto sin comando) | Tratado como `/ask` |

El bot edita el mensaje "Thinking…" en streaming y respeta el límite de 4096 chars de Telegram.

---

## Trucos de hackathon

- **Demo offline-resilient**: cortá una key (Groq) → mostrá en logs cómo el circuit breaker abre y el sistema sigue respondiendo via OpenRouter o Gemini sin que el usuario note nada
- **Multi-agent visible**: usá `engine: "research"` y mostrá el panel lateral del agent trace — esa es la diferencia visual entre AgentOS y "otro chatbot"
- **Cascade comparison**: enviá el mismo prompt con `cascade: "speed"` y `cascade: "reasoning"` lado a lado para mostrar el trade-off latencia vs calidad
- **PDF en demo**: terminá la demo generando un PDF del análisis con `/reports/generate` — siempre impresiona en jurados

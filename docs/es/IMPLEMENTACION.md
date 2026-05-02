# Cómo Implementar Tu Propia App con AgentOS

Esta guía te lleva de "tengo AgentOS corriendo" a "tengo MI app de IA funcionando". Con ejemplos reales, no abstracciones.

> **Antes de empezar**, asegurate de que la guía rápida ya te funcionó: [GUIA-RAPIDA.md](GUIA-RAPIDA.md). Necesitás ver el chat funcionando antes de empezar a personalizar.

---

## Cambio mental importante

AgentOS NO es la app. Es la **base**. Tu app es lo que vas a construir encima.

Pensalo como WordPress: WordPress no es un blog, es una plataforma para hacer blogs. Vos hacés tu blog específico (de cocina, de tecnología, de viajes).

Acá pasa lo mismo: AgentOS no es "el chatbot médico", es la base sobre la que vas a hacer "el chatbot médico". O el asistente legal. O el analizador de ventas. Lo que necesites.

```
┌─────────────────────────────────────────────────┐
│                                                  │
│   TU APP                                         │
│   • Lógica del dominio (médico/legal/ventas)    │
│   • Reglas específicas del negocio              │
│   • Marca, branding, UX particular              │
│                                                  │
└─────────────────────────────────────────────────┘
                     │
                     │  usa
                     ▼
┌─────────────────────────────────────────────────┐
│                                                  │
│   AGENTOS (base)                                 │
│   • IA con failover                              │
│   • Multi-agente                                 │
│   • RAG, base de datos, notifs                  │
│   • Frontend, backend, deploy                    │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## Los 3 modelos de uso (qué eligen las apps reales)

No hay UNA forma "correcta" de construir sobre AgentOS. Hay tres
modelos válidos según qué tipo de app necesites. Este es el punto que
más confunde al principio, así que va explicado primero.

### Modelo A — Fork por proyecto

Clonás el repo, customizás el system prompt + branding, deploy a tu
propio dominio. Bueno para: hackathons donde vas a hacer una sola app.
Es lo que documenta [HACKATHON.md](../HACKATHON.md).

### Modelo B — Una instancia, varios profiles (chat-with-personality)

La misma instancia de AgentOS sirve N "perfiles" — cada uno es un
system prompt + presets + branding distinto. Las URLs viven en
`/apps/<slug>` dentro del frontend de AgentOS. Bueno para: cuando todas
tus apps son **chats con personalidad diferente** (asistente médico,
asistente legal, tutor, etc.).

Cada profile es un archivo TS en `packages/profiles/profiles/<slug>.ts`.
Si tu UI se parece a un chat, este modelo te ahorra escribir un
frontend nuevo.

### Modelo C — AgentOS como API headless (lo más común para apps reales)

**Tu app es un proyecto separado** (otro repo, otro dominio, otro
deploy) que solo consume AgentOS por HTTP/SSE. Este es el modelo
correcto cuando tu UI **no se parece a un chat**: dashboards, mapas,
formularios, paneles ejecutivos, integraciones (Slack, móvil, etc.).

Ejemplo concreto vivible en este repo:
[`examples/dashboard-vanilla/`](../../examples/dashboard-vanilla/) —
un mini dashboard standalone (HTML+JS sin frameworks) que llama a
`/health`, `/profiles`, `/chat/stream`, `/rag/search` y arma su propia
UI. Copiá ese archivo a cualquier servidor estático y ya tenés una app
funcional sobre AgentOS.

```
┌────────────────────────────────────────┐         ┌──────────────────────┐
│  TU APP (proyecto aparte)              │  HTTP   │  AGENTOS (este repo) │
│  React / Vue / Svelte / móvil / lo     │ ──────▶ │  - LLM cascade       │
│  que necesites. Tu propio backend si    │         │  - Multi-agente      │
│  hace falta para datos del dominio.    │  SSE    │  - RAG               │
│                                        │ ◀────── │  - NL→SQL            │
│  AgentOS lo invocás solo cuando        │         │  - Notifs            │
│  necesitás IA.                         │         │  - File adapter      │
└────────────────────────────────────────┘         └──────────────────────┘
```

### Cuál elegir

| Tu situación | Modelo |
|---|---|
| "Tengo 1 app, voy a deployar 1 vez, no me importa la modularidad" | **A** (fork) |
| "Tengo varios chats con personalidades distintas, quiero compartir backend" | **B** (profiles) |
| "Mi app es un dashboard / mapa / panel / formulario / móvil / Slack bot" | **C** (API headless) |
| "Mi app combina dashboard + chat" | **C** + opcionalmente embeber el chat de B |

Lo que sigue de esta guía cubre **Modelo A** (fork) porque es el más
simple para empezar. Para **Modelo C** mirá el ejemplo de
`dashboard-vanilla` directamente — es 30 líneas de fetch + el patrón
es el mismo en cualquier framework.

---

## Decisión 1: ¿Qué app vas a construir?

Antes de tocar código, definí en una frase qué hace tu app. Ejemplos reales:

| App | Dominio | Qué reusa de AgentOS |
|-----|---------|---------------------|
| MediBot | "Triage de síntomas para pacientes" | Chat agent + RAG (manuales médicos) + notifs |
| LegalAssist | "Asistente legal que responde sobre contratos" | RAG + multi-agente para análisis profundo |
| SalesAnalyzer | "Dashboard que responde preguntas sobre ventas" | Conexión a BD + NL→SQL + reportes PDF |
| GeoAlert | "Detecta anomalías en logs de delivery" | ML/anomaly + geo + notifs |
| InternalQA | "Pregúntale al manual de empleados" | RAG simple + auth con Supabase |

Tu app probablemente cae en uno de estos patrones. Identificá cuál.

**Regla de oro**: hacé UNA app, no tres. La tentación de "y también que haga X" mata muchos proyectos. Foco brutal.

---

## Decisión 2: ¿Cuál de las 3 frontends usás?

| Frontend | Cuándo elegirlo |
|----------|-----------------|
| **SvelteKit** (`apps/web-svelte`) | Si nunca elegiste antes. Es el más simple de modificar. |
| **Next.js** (`apps/web-next`) | Si tu equipo ya conoce React. |
| **Nuxt 3** (`apps/web-vue`) | Si tu equipo ya conoce Vue. |

Las tres tienen exactamente la misma UX. Si dudás, **andá con SvelteKit**.

Los ejemplos en esta guía van a usar SvelteKit, pero los conceptos se traducen 1:1 a las otras dos.

---

## Plan de los próximos 90 minutos

```
[ 0-15min ]  Personalizá el cerebro del agente
[15-30min ]  Personalizá la marca + UX
[30-60min ]  Conectá tu fuente de datos (RAG / DB)
[60-75min ]  Activá las notificaciones
[75-90min ]  Probá end-to-end
```

A las 2 horas tenés un MVP demoeable.

---

## Paso 1: El cerebro del agente (system prompt)

Esto es lo más importante. **El comportamiento de tu app está controlado casi enteramente por el system prompt** del agente principal.

### Dónde está

```
packages/agents/agentos_agents/nodes/responder.py
```

Abrí ese archivo. Vas a ver:

```python
RESPONDER_SYSTEM = "You are a helpful, concise AI assistant. Answer directly."
```

Ese string controla cómo se comporta tu agente. Vamos a personalizarlo.

### Ejemplo: convertirlo en MediBot

```python
RESPONDER_SYSTEM = """Eres MediBot, un asistente médico que ayuda a pacientes con triage de síntomas.

REGLAS CRÍTICAS:
1. NUNCA das un diagnóstico definitivo. Siempre recomiendas consultar a un profesional.
2. Si los síntomas sugieren urgencia (dolor torácico, dificultad respiratoria, pérdida de conciencia, sangrado abundante), respondes EN LA PRIMERA LÍNEA: "🚨 URGENCIA: llama al servicio de emergencias inmediatamente."
3. Antes de sugerir gravedad, haces 1-2 preguntas de seguimiento para entender mejor.
4. No usas jerga médica. Hablas claro, como un buen médico de cabecera.
5. Si el usuario pregunta algo no médico, responde amablemente que solo puedes ayudar con síntomas y salud.

TONO: cálido, empático, claro. Tratas al usuario como a alguien preocupado, porque probablemente lo está.

LIMITACIONES:
- No prescribes medicamentos.
- No interpretas resultados de análisis específicos sin contexto profesional.
- No reemplazas a un médico.
"""
```

Eso es todo. Tu agente ya:
- Tiene personalidad médica
- Tiene reglas de seguridad (urgencia)
- Tiene un tono definido
- Tiene límites claros

### ¿Y los otros agentes (researcher, analyst)?

Si tu app necesita investigación profunda (no solo chat directo), también vas a querer personalizar:

```
packages/agents/agentos_agents/nodes/
├── responder.py     ← chat directo (más usado)
├── researcher.py    ← agente investigador (modo research)
├── analyst.py       ← agente analista
├── writer.py        ← agente redactor
└── router.py        ← decisor que elige el camino
```

Cada uno tiene su `*_SYSTEM` arriba del archivo. Modificá los que apliquen.

### Tip avanzado: prompts contextuales

Si tu app es multi-tenant (muchos clientes con configuraciones distintas), podés hacer el system prompt **dinámico**:

```python
async def responder_stream(state, factory):
    tenant_config = state.get("tenant_config", {})
    custom_instructions = tenant_config.get("system_prompt_extra", "")

    full_prompt = RESPONDER_SYSTEM
    if custom_instructions:
        full_prompt += f"\n\nINSTRUCCIONES ESPECÍFICAS DEL CLIENTE:\n{custom_instructions}"

    adapter = factory.get(state.get("cascade") or "speed")
    async for token in adapter.stream(messages=[
        {"role": "system", "content": full_prompt},
        {"role": "user", "content": state.get("query", "")},
    ]):
        yield token
```

Así cada cliente puede tener su propio behavior sin tocar código.

---

## Paso 2: Personalizá la marca y UX

### Dónde editar

| Lo que querés cambiar | Archivo |
|----------------------|---------|
| Nombre y subtítulo | `apps/web-svelte/src/routes/+page.svelte` |
| Botones de ejemplo (presets) | mismo archivo |
| Color primario | `apps/web-svelte/src/app.css` |
| Logo / icono | `apps/web-svelte/static/favicon.svg` |
| Letra del header | `+page.svelte` (línea con `>A<`) |

### Ejemplo: cambiar nombre, presets y color

Abrí `apps/web-svelte/src/routes/+page.svelte` y cambiá:

```svelte
<!-- Header -->
<h1 class="text-base font-semibold text-surface-900">MediBot</h1>
<p class="text-xs text-surface-700">Triage de síntomas con IA</p>
```

Y los presets (los 4 botones del estado vacío):

```svelte
{#each [
  { label: "Dolor de cabeza", task: "Tengo dolor de cabeza desde ayer..." },
  { label: "Fiebre", task: "Tengo 38.5°C de fiebre, ¿qué hago?" },
  { label: "Dolor abdominal", task: "Me duele mucho la barriga..." },
  { label: "Tos persistente", task: "Tengo tos hace 2 semanas..." },
] as preset}
```

Ahora abrí `apps/web-svelte/src/app.css` y cambiá el color primario:

```css
@theme {
  /* Antes era azul (#5c7cfa). Lo cambiamos a rojo médico. */
  --color-primary-500: #c92a2a;
  --color-primary-600: #b71c1c;
  --color-primary-700: #a01717;
}
```

Recargá la página → ya parece otra app totalmente distinta.

### Logo SVG

Abrí `apps/web-svelte/static/favicon.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#c92a2a"/>
  <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle"
        font-family="Inter, sans-serif" font-weight="700" font-size="36" fill="#fff">
    M
  </text>
</svg>
```

Cambiá la `M` por tu inicial y el color por el tuyo.

### Letra del header

En `+page.svelte`, buscá esta sección:

```svelte
<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-white font-mono text-sm font-bold">
  A   <!-- ← cambialo a tu inicial -->
</div>
```

---

## Paso 3: Conectá tus datos (la parte importante)

Tu app necesita saber **algo específico** para ser útil. Acá tenés dos caminos según qué tipo de datos tenés:

### Camino A: Tenés documentos (PDFs, manuales, FAQ)

Usá **RAG**.

#### Setup

```bash
# Subí cada documento que querés que el agente "conozca"
curl -X POST http://localhost:8000/rag/ingest -F "file=@manual_medico.pdf"
curl -X POST http://localhost:8000/rag/ingest -F "file=@protocolos.pdf"
curl -X POST http://localhost:8000/rag/ingest -F "file=@guias_clinicas.pdf"
```

#### Hacer que el agente USE esos documentos

Modificá `packages/agents/agentos_agents/nodes/responder.py`:

```python
from collections.abc import AsyncGenerator
from agentos_llm import LLMFactory
from agentos_rag import RAGPipeline
from ..state import AgentState

RESPONDER_SYSTEM = """Eres MediBot..."""  # tu prompt

# Singleton: una sola instancia para no recargar el modelo SBERT cada vez
_rag = RAGPipeline()


async def responder_stream(state: AgentState, factory: LLMFactory) -> AsyncGenerator[str, None]:
    query = state.get("query", "")

    # 1. Buscá en los documentos los 3 más relevantes
    chunks = await _rag.query(query, top_k=3)

    # 2. Armá el contexto
    if chunks:
        context = "\n\n".join(
            f"[Fuente: {c['metadata'].get('filename', 'desconocida')}, relevancia: {c['score']:.2f}]\n{c['content']}"
            for c in chunks
        )
        system_with_context = (
            f"{RESPONDER_SYSTEM}\n\n"
            f"CONTEXTO RELEVANTE DE LOS MANUALES:\n{context}\n\n"
            f"Usa este contexto para responder. Si la respuesta no está en el contexto, dilo claramente."
        )
    else:
        system_with_context = RESPONDER_SYSTEM

    # 3. Pasá todo al LLM
    adapter = factory.get(state.get("cascade") or "speed")
    async for token in adapter.stream(messages=[
        {"role": "system", "content": system_with_context},
        {"role": "user", "content": query},
    ]):
        yield token
```

Listo. Ahora tu agente responde basándose en los manuales que subiste, no en su entrenamiento general.

#### Verificación

Pregúntale algo que esté **solo** en tus manuales (un protocolo específico, una política interna). Si te lo responde, está usando el RAG.

### Camino B: Tenés base de datos (clientes, ventas, transacciones)

Usá la **conexión a BD con NL→SQL**.

#### Setup

Agregá la URL de tu base al `.env`:

```env
DATABASE_URL_USER=postgresql://usuario:pass@host:5432/mi_db
# o
DATABASE_URL_USER=mysql+aiomysql://usuario:pass@host:3306/mi_db
# o
DATABASE_URL_USER=sqlite+aiosqlite:///./mi_db.db
```

#### Tu primer query en lenguaje natural

```bash
curl -X POST http://localhost:8000/database/nl-query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuántos clientes nuevos hubo este mes?"}'
```

Tu agente acaba de mirar tu schema, generar el SQL apropiado, ejecutarlo de manera segura, y devolverte la respuesta.

#### Integrar al agente principal

En `responder.py`, podés hacer que el agente use la BD cuando detecte preguntas analíticas:

```python
import re
from agentos_database import SafeQueryExecutor, SchemaIntrospector, connect

# Singleton DB
_db_conn = None
_db_executor = None
_db_introspector = None

def _ensure_db():
    global _db_conn, _db_executor, _db_introspector
    if _db_conn is None:
        try:
            _db_conn = connect()
            _db_executor = SafeQueryExecutor(_db_conn, read_only=True)
            _db_introspector = SchemaIntrospector(_db_conn)
        except RuntimeError:
            pass  # DATABASE_URL_USER no está set, está bien
    return _db_executor, _db_introspector


# Heurística simple: detecta preguntas que requieren datos
ANALYTICAL_PATTERNS = re.compile(
    r"\b(cuánt[oa]s?|how many|count|total|promedio|máximo|mínimo|últim[oa]s?|este mes|esta semana|por región|por categoría)\b",
    re.IGNORECASE,
)


async def responder_stream(state, factory):
    query = state.get("query", "")
    extra_context = ""

    # Si la pregunta parece analítica, intentá buscar en la BD primero
    if ANALYTICAL_PATTERNS.search(query):
        executor, introspector = _ensure_db()
        if executor and introspector:
            try:
                schema_text = await introspector.schema_text(max_tables=20)
                # Generá SQL con un mini-prompt
                sql_resp = await factory.complete_with_fallback(
                    messages=[
                        {"role": "system", "content": f"Genera SQL SELECT para responder. Schema:\n{schema_text}\nResponde SOLO el SQL, sin markdown."},
                        {"role": "user", "content": query},
                    ],
                    cascade="reasoning", temperature=0.0, max_tokens=300,
                )
                sql = sql_resp.content.strip().rstrip(";")
                result = await executor.execute(sql)
                if result.rows:
                    extra_context = f"\nDATOS DE LA BD:\nQuery: {sql}\nResultado: {result.rows[:5]}"
            except Exception:
                pass  # Si falla, sigue sin contexto de BD

    system = RESPONDER_SYSTEM + extra_context
    adapter = factory.get(state.get("cascade") or "speed")
    async for token in adapter.stream(messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]):
        yield token
```

Ahora tu agente puede responder preguntas como "¿cuántos pedidos urgentes tenemos?" mirando tu base directamente.

### Camino C: Tus datos están en una API externa

Si tus datos vienen de una API (Stripe, HubSpot, tu CRM), creá un nuevo nodo:

```python
# packages/agents/agentos_agents/nodes/api_fetcher.py
import httpx
from ..state import AgentState

async def fetch_external_data(state: AgentState, factory) -> AgentState:
    query = state.get("query", "")
    # Acá pegás a tu API
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.tu-servicio.com/data",
            headers={"Authorization": f"Bearer {os.getenv('TU_API_KEY')}"},
            params={"q": query},
        )
        return {"external_data": resp.json()}
```

Y registralo en el grafo (`packages/agents/agentos_agents/graphs/runner.py`).

---

## Paso 4: Activá las notificaciones

Si tu app necesita avisar al usuario cuando algo pasa, ya tenés la infraestructura.

### Cuándo te conviene

- El agente detecta una urgencia → manda Telegram al doctor de guardia
- Un análisis termina → email al cliente con el reporte
- Una métrica crítica supera un umbral → alerta al admin

### Caso real: alerta cuando MediBot detecta urgencia

Modificá `responder.py` para detectar la urgencia en la respuesta y disparar notif:

```python
import os
from agentos_notifications import NotificationDispatcher, NotificationMessage, Severity

_dispatcher = NotificationDispatcher()

async def responder_node(state, factory):
    """Versión non-streaming que captura la respuesta completa antes de emitirla."""
    chunks = []
    async for token in responder_stream(state, factory):
        chunks.append(token)
    response = "".join(chunks)

    # Si contiene la palabra clave de urgencia, notificá al admin
    if "🚨 URGENCIA" in response.upper() or "URGENCIA:" in response:
        await _dispatcher.send(NotificationMessage(
            title="Caso de urgencia detectado",
            body=f"Pregunta del paciente: {state.get('query', '')[:200]}\n\nRespuesta del bot: {response[:500]}",
            severity=Severity.CRITICAL,
        ))

    return {"response": response}
```

### Configurar canales

En `.env`:

```env
# Telegram (admin recibe alertas críticas)
TELEGRAM_BOT_TOKEN=123:ABC...
TELEGRAM_CHAT_IDS=123456789

# Email (backup)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=alerts@tu-clinica.com
SMTP_PASSWORD=app-password
EMAIL_RECIPIENTS=admin@tu-clinica.com,doctor-guardia@tu-clinica.com
```

Cuando el agente detecta urgencia, ambos canales reciben la alerta en paralelo.

---

## Paso 5: Probá end-to-end

```bash
# 1. Tests unitarios todavía verde (no rompiste nada)
python -m pytest packages/llm/tests packages/agents/tests/test_graph_runner.py -q

# 2. Reiniciá el backend para cargar tus cambios
cd services/api && uvicorn app.main:app --reload

# 3. Smoke E2E
python scripts/e2e_smoke.py

# 4. Abrí el frontend y probá tus presets
pnpm dev:svelte
```

---

## Casos comunes (recetas listas)

### "Quiero que cuando termine un análisis largo, me avise por Telegram"

```python
# En el endpoint que dispara el análisis
async def heavy_analysis(file: UploadFile, request: Request):
    # ... tu lógica de análisis ...
    result = await do_heavy_work(file)

    # Al final, notificar
    dispatcher = request.app.state.notifier
    await dispatcher.send(NotificationMessage(
        title=f"Análisis listo: {file.filename}",
        body=f"Procesé {result['rows']} filas. Anomalías encontradas: {result['anomalies']}",
        severity=Severity.INFO,
    ))
    return result
```

### "Quiero que el agente pueda mandar emails cuando lo decida"

Convertí la notificación en una "herramienta" que el LLM puede invocar:

```python
SYSTEM = """Eres un asistente. Si el usuario pide que envíes un email de seguimiento, responde con:
SEND_EMAIL: <destinatario>: <asunto>: <cuerpo>

Si no, responde normalmente."""

async def smart_responder(state, factory):
    response = await factory.complete_with_fallback(
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": state["query"]}],
        cascade="speed",
    )

    if response.content.startswith("SEND_EMAIL:"):
        # Parsear y enviar
        _, to, subject, body = response.content.split(":", 3)
        await _dispatcher.send(NotificationMessage(
            title=subject.strip(),
            body=body.strip(),
            channels=[Channel.EMAIL],
            recipients={"email": [to.strip()]},
        ))
        return {"response": f"Email enviado a {to.strip()}"}

    return {"response": response.content}
```

### "Quiero auth con Supabase para que solo usuarios logueados usen la app"

1. En el frontend, integrá `@supabase/auth-ui-svelte` (o el equivalente Next/Vue)
2. En el `.env`, activá `AUTH_REQUIRED=true`
3. El frontend manda `Authorization: Bearer <jwt>` en cada request
4. El middleware JWT del backend ya valida el token contra `SUPABASE_JWT_SECRET`

Listo. ~30 minutos.

### "Quiero guardar el historial de cada conversación en Supabase"

Las migraciones ya están: `supabase/migrations/001_initial_schema.sql` crea las tablas `chat_sessions` y `chat_messages`.

En el endpoint de chat:

```python
@router.post("/stream")
async def chat_stream(body: ChatRequest, request: Request):
    supabase = request.app.state.supabase
    user_id = ...  # del JWT
    session_id = body.session_id or supabase.create_session(user_id, body.message[:50])["id"]

    # Guardar mensaje del usuario
    supabase.append_message(session_id, "user", body.message)

    # Stream + ir acumulando la respuesta
    full_response = []
    async def event_generator():
        async for event in orchestrator.run(body.message, ...):
            if event["type"] == "token":
                full_response.append(event["content"])
            yield {"data": json.dumps(event)}
        # Al final, guardar la respuesta completa
        supabase.append_message(session_id, "assistant", "".join(full_response))

    return EventSourceResponse(event_generator())
```

### "Quiero un panel admin para ver las conversaciones"

Creá una nueva ruta en el frontend (`/admin`):

```svelte
<!-- apps/web-svelte/src/routes/admin/+page.svelte -->
<script lang="ts">
  import { onMount } from "svelte";
  let sessions = $state([]);

  onMount(async () => {
    const res = await fetch("/api/admin/sessions");
    sessions = await res.json();
  });
</script>

{#each sessions as session}
  <div>{session.title} — {session.created_at}</div>
{/each}
```

Y un endpoint nuevo en el backend (`services/api/app/routers/admin.py`).

---

## Errores comunes y cómo evitarlos

### ❌ Hardcodear API keys en el código

**Mal**:
```python
adapter = GroqAdapter(api_key="gsk_real_key_here")  # 🔥
```

**Bien**:
```python
adapter = GroqAdapter()  # lee de GROQ_API_KEY env var
```

### ❌ Llamar adapters directamente

**Mal**:
```python
groq = GroqAdapter()
result = await groq.complete(messages)  # ❌ pierde el failover
```

**Bien**:
```python
factory = request.app.state.llm_factory
result = await factory.complete_with_fallback(messages, cascade="speed")  # ✅
```

### ❌ Cargar el modelo SBERT por request

**Mal**:
```python
@router.post("/search")
async def search(body):
    pipeline = RAGPipeline()  # 🔥 carga 90MB cada request
    ...
```

**Bien**:
```python
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline

@router.post("/search")
async def search(body):
    return await get_pipeline().query(body.query)
```

### ❌ Construir features que no necesitás

**Mal**: "Voy a integrar 5 LLM providers más por si acaso"

**Bien**: "Tengo 3 ya, alcanza, voy a meter mi lógica de dominio"

---

## Anti-patrones de hackathon

| ❌ Tentación | ✅ Hacé esto |
|-------------|------------|
| "Voy a reescribir el LLMFactory para tener control total" | Usá `cascade="reasoning"` y listo |
| "Voy a hacer 3 frontends para mostrar versatilidad" | Uno solo, pulido |
| "Hardcodeo las keys mientras testeo, después las paso" | `.env` desde el primer commit |
| "Voy a migrar de Tailwind a vanilla CSS" | No |
| "Construyo auth desde cero" | Supabase Auth, 30 minutos |
| "Hago un orquestador propio mejor que LangGraph" | No |
| "Después meto los tests" | Antes. `pytest` corre en 15 segundos |

---

## Checklist antes de demo / submission

- [ ] El system prompt del agente tiene tu personalidad/dominio
- [ ] Los presets en la home invitan a usar TU app (no los genéricos de AgentOS)
- [ ] El nombre, color, logo son tuyos
- [ ] La URL en producción funciona en incógnito desde móvil
- [ ] El smoke test pasa contra producción: `BACKEND_URL=https://tu-app... python scripts/e2e_smoke.py`
- [ ] `.env` NO está commiteado (verificá con `git ls-files | grep .env`)
- [ ] El README explica qué hace TU app (no "es un fork de AgentOS")
- [ ] Tenés un video corto (60s) mostrando el flujo principal
- [ ] La cuenta del demo (si requiere login) tiene datos cargados ya

---

## Próximos pasos

| Querés... | Leé... |
|-----------|--------|
| Subirlo a internet (gratis) | [../DEPLOY.md](../DEPLOY.md) |
| Ver todas las funciones disponibles | [FUNCIONALIDADES.md](FUNCIONALIDADES.md) |
| Detalles técnicos profundos | [../USAGE.md](../USAGE.md) |
| Ideas de demo / pitching | [../HACKATHON.md](../HACKATHON.md) |

---

## Resumen de comandos clave

```bash
# Personalizar el cerebro
$EDITOR packages/agents/agentos_agents/nodes/responder.py

# Personalizar la marca
$EDITOR apps/web-svelte/src/routes/+page.svelte
$EDITOR apps/web-svelte/src/app.css

# Ingresar conocimiento (RAG)
curl -X POST http://localhost:8000/rag/ingest -F "file=@tu-doc.pdf"

# Conectar tu BD
echo 'DATABASE_URL_USER=postgresql://...' >> .env
# Reiniciá uvicorn

# Probar tu cambio
python -m pytest packages/llm/tests packages/agents/tests/test_graph_runner.py -q
python scripts/e2e_smoke.py

# Deploy
git push origin main  # dispara deploy.yml
gh run watch
```

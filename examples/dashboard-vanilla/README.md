# Dashboard de ejemplo · construido sobre AgentOS

Este es un **ejemplo concreto del modelo correcto**: tu app es un proyecto
independiente que consume AgentOS como un API HTTP. Vive **fuera** del repo
de AgentOS, en su propio servidor estático/host, y solo necesita la URL
del backend de AgentOS para funcionar.

```
┌────────────────────────────────────────┐         ┌──────────────────────┐
│  TU APP                                │  HTTP   │  AGENTOS (backend)   │
│  examples/dashboard-vanilla/           │ ──────▶ │  - /health           │
│  (HTML + JS, sin frameworks)           │         │  - /chat/stream      │
│                                        │  SSE    │  - /rag/search       │
│  KPIs · perfiles · chat · RAG search   │ ◀────── │  - /database/nl-query│
│                                        │         │  - /profiles         │
└────────────────────────────────────────┘         └──────────────────────┘
```

## Cómo correrlo

```bash
# 1. Levantar el backend de AgentOS (puerto 8000)
cd services/api && uvicorn app.main:app --reload

# 2. Servir este archivo desde cualquier puerto distinto
python -m http.server 9000 --directory examples/dashboard-vanilla
# o
npx serve examples/dashboard-vanilla -l 9000
```

Abrir `http://localhost:9000` → ver el dashboard llamando al API.

El input "AgentOS API" arriba a la derecha permite cambiar la URL del backend
en vivo: si tu API está en Koyeb (`https://agentos-api.koyeb.app`), pegá esa
URL y todos los widgets se reconectan.

## Qué demuestra el ejemplo

| Widget | Endpoint AgentOS | Propósito |
|---|---|---|
| KPI estado backend | `GET /health` | Si los proveedores LLM están up |
| KPI proveedores activos | `GET /health` | 3/3 con failover, 2/3 degradado, etc. |
| KPI canales notif | `GET /notify/channels` | Telegram/Email configurados |
| Catálogo de perfiles | `GET /profiles` | Para que tu app pueda elegir personalidad de chat |
| Q&A | `POST /chat/stream` (SSE) | Pregunta libre al agente |
| Búsqueda RAG | `POST /rag/search` | Consultar lo que subiste a `/rag/ingest` |

## Cómo lo adaptás a tu app real

1. **Tomá este `index.html` como punto de partida**, o reescribilo en
   React/Vue/Svelte/lo-que-sea (el patrón es el mismo: `fetch(url + endpoint, ...)`).
2. **Reemplazá los widgets** por los que tu dominio necesite: tabla de
   ventas, mapa de logística, formulario de altas, panel de tickets, etc.
3. **Para datos propios** (no de AgentOS), montá tu propio backend o
   usá Supabase directamente desde el frontend. AgentOS no te impone
   un único backend.
4. **Para invocar capacidades de IA**, llamá los endpoints que necesites
   con la misma forma que ves arriba.
5. **CORS**: el backend de AgentOS está configurado con `allow_origins`
   abierto por default. En producción, restringilo en
   `services/api/app/config.py` a los dominios reales de tus apps.

## Comparación con `/apps/<slug>` del frontend SvelteKit

El sistema `/apps/<slug>` que está en `apps/web-svelte/src/routes/apps/`
es **una opción**: cuando tu app es un chat con personalidad diferente,
usar profiles te ahorra escribir un frontend nuevo. **Este ejemplo cubre
el otro caso**: tu app NO es un chat, es un dashboard / mapa / panel /
formulario / lo-que-sea, y AgentOS solo provee algunas capacidades de
IA puntuales.

> Regla pragmática: si tu UI se parece a un chat, usá un profile.
> Si tu UI se parece a un dashboard, andá con este modelo.

## Referencias

- Lista completa de endpoints: `GET /` del backend devuelve el índice.
- OpenAPI interactivo: `http://localhost:8000/docs`.
- Documentación de capacidades: [`docs/es/FUNCIONALIDADES.md`](../../docs/es/FUNCIONALIDADES.md).

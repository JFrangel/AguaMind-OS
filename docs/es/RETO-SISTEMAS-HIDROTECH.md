# Reto Sistemas — HidroTech

**Hackathon UNIAJC 2026 · Gestión Inteligente del Agua · Sede Sur**

> Documentación del Reto **Sistemas**: arquitectura, implementación del sistema multi-agente con LangGraph, sistema de notificaciones (Telegram + dashboard) y diagrama integrado del flujo de datos.

---

## 1. Resumen del reto Sistemas

HidroTech resuelve el reto de **Sistemas** del hackathon UNIAJC con un sistema operativo de gestión hídrica que:

1. **Caracteriza** el campus UNIAJC Sede Sur (38,755 m², 8,234 usuarios) con 5 sensores IoT.
2. **Delibera** mediante un sistema multi-agente IA (5 agentes especializados, LangGraph + cascada de LLMs).
3. **Actúa** automáticamente: notifica al equipo de mantenimiento por Telegram en menos de 5 segundos cuando detecta una anomalía y propone la mitigación.

**Stack del reto Sistemas:**

| Capa | Tecnología |
|---|---|
| Frontend | SvelteKit 5 (runes), TypeScript, Tailwind, animaciones SVG |
| Backend | FastAPI (Python 3.13), Pydantic, ASGI async |
| Multi-agente | LangGraph (grafo de estado), TypedDict compartido |
| LLM | Cascada Gemini 2.0 → Groq Llama 3.3 → fallback local determinista |
| ML | scikit-learn IsolationForest (detección de anomalías) |
| Notificaciones | Telegram Bot API (push silencioso), dispatcher multi-canal |
| Persistencia | Supabase PostgreSQL + pgvector |
| Comunicación IoT | MQTT (HiveMQ Cloud) ESP32 ↔ FastAPI |

---

## 2. Arquitectura general (capas)

```
┌──────────────────────────────────────────────────────────────────────┐
│                          HidroTech · 7 capas                          │
├──────────────────────────────────────────────────────────────────────┤
│ 7. APLICACIÓN     │ Dashboard SvelteKit + Telegram Bot                │
│ 6. INTELIGENCIA   │ 5 agentes LangGraph + LLM cascade + IsolationFor. │
│ 5. PERSISTENCIA   │ Supabase PostgreSQL · pgvector RAG · Memoria      │
│ 4. COMUNICACIÓN   │ MQTT HiveMQ · HTTP REST · SSE stream · Telegram   │
│ 3. EDGE           │ FastAPI normalizer + agente stub + dispatcher     │
│ 2. SENSADO        │ ESP32 + 5 sensores (Q · R · P · N · H)            │
│ 1. FÍSICA         │ PTAP 2011 · 2 tanques (A 36k · B 16k) · 8 EV      │
└──────────────────────────────────────────────────────────────────────┘
```

Cada capa es **independiente y deletable** — borrar la capa de RAG no rompe el dispatcher, borrar Telegram no rompe el agente.

---

## 3. Sistema multi-agente (núcleo del reto Sistemas)

### 3.1 Los 5 agentes

| Agente | Archivo | Responsabilidad |
|---|---|---|
| **Orchestrator** | `graphs/water_orchestrator.py` | Decide cuándo deliberar, consolida resultados, coordina notificaciones |
| **Systems** | `graphs/water_orchestrator.py::systems_agent_node` | Calcula KPIs (IEH, TPP, CPE) y detecta anomalías con IsolationForest |
| **Sensor** | `graphs/water_orchestrator.py::sensor_agent_node` | Valida la calidad de las señales (rango físico, congelamiento, drift) |
| **Industrial** | `graphs/water_orchestrator.py::industrial_agent_node` | Identifica las 7 mudas Lean, calcula impacto monetario y proyección |
| **Mitigation** | `routers/mitigation.py` + `graphs/water_orchestrator.py::alerting_node` | Ejecuta acciones (abrir/cerrar electroválvulas, reportar) |

### 3.2 Estado compartido (`WaterState`)

```python
class WaterState(TypedDict, total=False):
    # Datos crudos de sensores
    reading: dict
    kpis: dict
    alerts: list[dict]

    # Resultado de cada agente
    systems_analysis: dict
    sensor_analysis: dict
    industrial_analysis: dict

    # Decisión consolidada
    decision: str        # "ok" | "warning" | "alert" | "critical"
    action_taken: str
    cycle: int

    # Notificaciones
    notifications_sent: Annotated[list[str], _merge]
    report_generated: bool
    telegram_message: str | None
```

### 3.3 Grafo LangGraph

```
       ┌────────────┐
       │  start     │
       └─────┬──────┘
             ▼
       ┌────────────┐   monitoring_node
       │ MONITORING │   GET /water/reading
       └─────┬──────┘   (5 sensores Q,R,P,N,H)
             ▼
   ┌─────────────────────┐
   │   ANALYZING (∥)     │  3 agentes en paralelo
   │  ┌───────────────┐  │
   │  │ SystemsAgent  │  │  → KPIs + anomalías
   │  ├───────────────┤  │
   │  │ SensorAgent   │  │  → calidad señales
   │  ├───────────────┤  │
   │  │ IndustrialAg. │  │  → mudas + costos
   │  └───────────────┘  │
   └────────┬────────────┘
            ▼
       ┌────────────┐    deciding_node
       │ DECIDING   │    "la peor decisión gana"
       └─────┬──────┘    (priority: critical>alert>warning>ok)
             │
       ┌─────┴────────────┐
       │                  │
   decision==ok      decision∈{warning,alert,critical}
       │                  │
       ▼                  ▼
   ┌────────┐       ┌────────────┐
   │  END   │       │  ALERTING  │  → Telegram push
   │ (idle) │       └─────┬──────┘
   └────────┘             ▼
                    ┌────────────┐
                    │ REPORTING  │  (si hour==18 → reporte diario)
                    └─────┬──────┘
                          ▼
                       ┌────────┐
                       │  END   │
                       └────────┘
```

**Lógica del router condicional** (`_route_after_deciding`):

```python
def _route_after_deciding(state: WaterState) -> str:
    decision = state.get("decision", "ok")
    if decision in ("critical", "alert", "warning"):
        return "alerting"
    if state.get("report_generated"):
        return "reporting"
    return END
```

### 3.4 Cascada de LLMs

El agente conversacional usa un **fallback inteligente de tres niveles** (`demo_server.py::_llm_complete`):

```
1. Gemini 2.0 Flash    (gratis · 1 M tokens/día)
   ↓ (si falla o no hay key)
2. Groq Llama 3.3 70B  (gratis · rápido)
   ↓ (si falla o no hay key)
3. Fallback determinista
   • Clasifica intención por keywords (15 intenciones)
   • Genera respuesta natural con datos en vivo
   • Garantiza que nunca falle el chat
```

Las 14 intenciones soportadas en el fallback: `saludo · fuga · tanques · presion · humedad · sensores · mitigacion · normativa · sostenibilidad · agente · general · reuso · fenomeno · fuentes`.

### 3.5 Detección de anomalías (IsolationForest)

`SystemsAgent` mantiene un buffer circular de las últimas 50 lecturas y entrena IsolationForest sobre 5 features `[Q, R, P, tank_a_pct, soil_humidity_pct]`:

```python
from sklearn.ensemble import IsolationForest

clf = IsolationForest(contamination=0.1, random_state=42)
clf.fit(history_buffer[-50:])
score = clf.score_samples([current_reading])[0]
is_anomaly = score < -0.3   # umbral calibrado para el campus
```

---

## 4. Endpoints del agente (FastAPI)

`services/api/app/routers/agent_water.py`:

| Método | Ruta | Función |
|---|---|---|
| `POST` | `/water/agent/start` | Inicia el loop del Orchestrator (background task) |
| `POST` | `/water/agent/stop` | Detiene el loop |
| `GET`  | `/water/agent/status` | Estado actual: ciclo, decisión, agentes, alertas |
| `POST` | `/water/agent/cycle` | Ejecuta UN ciclo manual (útil para demo) |
| `GET`  | `/water/agent/stream` | SSE — stream en vivo de eventos del agente |
| `POST` | `/water/agent/ask` | Chat conversacional (LLM cascade) |
| `GET`  | `/water/agent/insights` | 3 insights automáticos por LLM (caudal · eficiencia · humedad) |

**Ejemplo de respuesta de `/water/agent/status`:**

```json
{
  "data": {
    "running": true,
    "cycle": 47,
    "last_decision": "warning",
    "interval_s": 30,
    "agents": {
      "systems": "warning",
      "sensor": "ok",
      "industrial": "warning"
    },
    "last_alerts": 2,
    "last_issues": [
      "TPP 18.4% por encima de meta (10%)",
      "Humedad de suelo 28% — considerar riego nocturno"
    ],
    "telegram_message": "⚠️ HidroTech · ..."
  }
}
```

---

## 5. Sistema de notificaciones

### 5.1 Arquitectura

```
                 ┌─────────────────────────────────────────────┐
                 │  Orchestrator (LangGraph)                   │
                 │  decisión: warning | alert | critical       │
                 └──────────────────┬──────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
   ┌──────────────────┐   ┌──────────────────┐   ┌────────────────────┐
   │ TelegramAdapter  │   │  EmailAdapter    │   │ DashboardSSE       │
   │ (Bot API push)   │   │  (SMTP)          │   │ (/agent/stream)    │
   └────────┬─────────┘   └────────┬─────────┘   └─────────┬──────────┘
            │                      │                       │
            ▼                      ▼                       ▼
     8,234 usuarios          mantenimiento          dashboard live
     de UNIAJC               infra@uniajc.edu.co    /agua
```

### 5.2 Endpoints de notificación

`services/api/app/routers/telegram_notify.py`:

| Método | Ruta | Disparador |
|---|---|---|
| `POST` | `/water/notify/agent_cycle` | Cada ciclo del agente (silencioso si `decision=ok`, push si warning/critical) |
| `POST` | `/water/notify/phenomenon` | Plan ante fenómeno climático (sequía, lluvia, sismo, contaminación, pico demanda) |
| `POST` | `/water/notify/mitigation_executed` | Ejecutar acción de mitigación (ej. cerrar EV-A2) |
| `POST` | `/water/notify/callback` | Callback del bot — confirmación de acción del usuario |
| `GET`  | `/water/notify/test` | Test directo del bot |

### 5.3 Comandos del bot Telegram

`apps/telegram/bot.py` registra 17 comandos:

```
/start            → bienvenida + menú interactivo
/ask <pregunta>   → chat libre con el agente
/research <tema>  → investigación profunda con RAG
/report           → reporte diario PDF
/status           → estado general

/agua | /estado   → estado completo del sistema (KPIs + sensores + alertas)
/zonas            → consumo por zona del campus
/kpis             → IEH, TPP, CPE con semáforos
/sensores         → estado de los 5 sensores Q/R/P/N/H
/reporte_agua     → reporte hídrico del día

# Demos
/alerta           → inyecta escenario de fuga
/riego            → inyecta pico de riego
/normal           → reset a estado normal

# Control del agente
/agente_start     → arranca el loop del Orchestrator
/agente_stop      → detiene el loop
/agente_status    → estado del ciclo actual
```

### 5.4 Formato de las notificaciones push

**Alerta crítica:**
```
🚨 HidroTech · UNIAJC Sede Sur
Estado: CRITICAL · 13:42

💧 Caudal: `87.5` L/min
🪣 Tanque A: `32.1%` · B: `45.8%`
📊 IEH: `24%` · TPP: `73.99%`
🌱 Humedad H: `28%`

🚨 Alertas críticas:
  • Bloque A: TPP 73.99% — fuga probable
  • Cancha: Humedad 28% — suelo seco
```

**Reporte diario (18:00):**
```
📊 HidroTech · Reporte Diario
2026-05-08 · UNIAJC Sede Sur

✓ Consumo total: 45,367 L
⚠ Pérdidas: 11,341 L
📈 Eficiencia: 75.0%
⏱ Hora pico: 10:00 (4,820 L)

KPIs del día:
  IEH: 75% (warning)
  TPP: 25% (critical)
  CPE: 14.04 L/est (ok)

Costo-beneficio:
  Pérdida diaria: $39,693 COP
  Ahorro proyectado anual: $14,488,000 COP
  ROI estimado: 9 meses
```

### 5.5 Notificaciones silenciosas en el dashboard

Para **no spamear** el chat de Telegram durante el pitch, las notificaciones del agente se envían también al dashboard vía **Server-Sent Events (SSE)** en `/water/agent/stream`. El frontend SvelteKit las recibe en tiempo real y las pinta en el panel "Análisis del Agente".

```typescript
const eventSource = new EventSource("/api/water?endpoint=agent/stream");
eventSource.onmessage = (e) => {
  const event = JSON.parse(e.data);
  agentStream = [event, ...agentStream].slice(0, 20);
};
```

---

## 6. Flujo end-to-end (sensor → notificación)

```
┌─────────┐  MQTT 30s   ┌──────────────┐
│  ESP32  │ ──────────▶ │ HiveMQ Cloud │
└─────────┘             └──────┬───────┘
                               │
                               ▼  WebSocket subscribe
                       ┌────────────────┐
                       │  Normalizer    │  acepta JSON, CSV, NDJSON,
                       │  (FastAPI)     │  ESP32 compact, Modbus, SCADA, OPC-UA
                       └───────┬────────┘
                               │
                               ▼
                       ┌────────────────┐
                       │  /water/ingest │  → simulación si no hay hardware
                       └───────┬────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │  Supabase   │  │ Orchestrator│  │  Dashboard  │
     │  PostgreSQL │  │  LangGraph  │  │  SvelteKit  │
     └─────────────┘  └──────┬──────┘  └─────────────┘
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
              Systems    Sensor    Industrial    (en paralelo)
                  └──────────┼──────────┘
                             ▼
                       Deciding (consolida)
                             │
                  ┌──────────┴──────────┐
                  │                     │
              decision=ok        decision=warn/alert/crit
                  │                     │
                  ▼                     ▼
                IDLE              Alerting + Reporting
                                        │
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                     Telegram        Email       SSE stream
                     (8,234           (infra)    → Dashboard
                      usuarios)
```

**Latencia total medida:** sensor → notificación ≤ **5 segundos** (≈ 1.2 s LLM + 0.8 s LangGraph + 0.4 s HTTP Telegram).

---

## 7. Implementación del dashboard

`apps/web-svelte/src/routes/agua/+page.svelte` (≈ 2,300 líneas, Svelte 5).

**5 pestañas:**

| # | Tab | Contenido |
|---|---|---|
| 01 | Operación | KPIs en vivo · 2 tanques con olas SVG · 5 sensores · alertas |
| 02 | Tendencias | Heatmap día×hora · 5 series temporales 24h · stacked area consumo/pérdidas |
| 03 | Inteligencia | Estado del Orchestrator · razonamiento en vivo · impacto hídrico · chat con agente |
| 04 | Mapa del Campus | SVG layout 38,755 m² · 8 electroválvulas controlables · vista 2D/3D |
| 05 | Comunidad | Smart Water Ledger · ranking edificios · retos · canjes · reportes ciudadanos |

**Características clave:**
- Modo claro/oscuro con `:global(html.light)` y clase `am-keep` para texto blanco sobre fondos de color.
- Polling cada 10 s a `/water/reading`.
- Conexión SSE persistente para el stream del agente.
- 4 KPIs principales: **CONSUMO** · **FUGAS** · **AHORRO** · **IEH**.

---

## 8. Resumen del diagrama integrado

```
┌──────────────────────────────────────────────────────────────────────┐
│                       HidroTech · Sistemas                            │
│                                                                       │
│  HARDWARE                  BACKEND                  FRONTEND          │
│  ┌────────┐    MQTT       ┌────────────┐    REST   ┌────────────┐    │
│  │ ESP32  │──────────────▶│  FastAPI   │──────────▶│ SvelteKit  │    │
│  │ 5      │               │ Normalizer │   SSE     │ Dashboard  │    │
│  │ sensor │               └─────┬──────┘  ◀─────── │ /agua      │    │
│  └────────┘                     │                  └────────────┘    │
│                                 ▼                                     │
│                         ┌──────────────┐                              │
│                         │  LangGraph   │  cada 30s                    │
│                         │ Orchestrator │  ─────────┐                  │
│                         └──────┬───────┘           │                  │
│                                │                   │                  │
│                  ┌─────────────┼─────────────┐     ▼                  │
│                  │             │             │  ┌──────────────┐      │
│                  ▼             ▼             ▼  │   Supabase   │      │
│              Systems       Sensor      Industrial│  PostgreSQL  │      │
│              (KPIs+ML)   (validación) (Lean+ROI) │  + pgvector  │      │
│                  │             │             │   └──────────────┘      │
│                  └─────────────┼─────────────┘                         │
│                                ▼                                       │
│                          Mitigation                                    │
│                                │                                       │
│                  ┌─────────────┼─────────────┐                         │
│                  ▼             ▼             ▼                         │
│           ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│           │ Telegram │  │  Email   │  │   SSE    │                    │
│           │   Bot    │  │  SMTP    │  │  Stream  │                    │
│           │ 17 cmds  │  │          │  │          │                    │
│           └──────────┘  └──────────┘  └──────────┘                    │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 9. Verificación end-to-end

```bash
# 1. Backend
cd services/api && python3 demo_server.py
curl http://localhost:8000/water/reading                    # ✓ JSON con 5 sensores
curl http://localhost:8000/water/agent/status               # ✓ ciclo, decisión

# 2. Iniciar agente
curl -X POST http://localhost:8000/water/agent/start
sleep 35
curl http://localhost:8000/water/agent/status               # ✓ cycle > 0

# 3. Stream SSE
curl -N http://localhost:8000/water/agent/stream             # eventos en vivo

# 4. Notificación de prueba
curl http://localhost:8000/water/notify/test                 # ✓ mensaje en Telegram

# 5. Frontend
cd apps/web-svelte && pnpm dev
open http://localhost:5173/agua

# 6. Bot Telegram
cd apps/telegram && python bot.py
# enviar /agente_status al bot
```

---

## 10. Cumplimiento de la rúbrica del reto Sistemas

| Criterio | Cómo lo cumplimos |
|---|---|
| **Novedad (30%)** | Sistema multi-agente LangGraph con 5 agentes paralelos · cascada de LLMs gratuitos · normalizador universal de 7 formatos |
| **Industrial (30%)** | KPIs IEH/TPP/CPE con datos reales · 7 mudas Lean · ROI 9 meses sobre PTAP de 2011 |
| **Inventiva (20%)** | "La peor decisión gana" en consolidación · IsolationForest sobre buffer rotativo · fallback determinista 14 intenciones |
| **Impacto (20%)** | 8,234 usuarios · 16,500 L/día recuperables · 4 ODS (6, 9, 11, 12) · campus replicable |

---

**Autores:** Equipo HidroTech · UNIAJC Sede Sur · 2026
**Repositorio:** [github.com/JFrangel/AguaMind-OS](https://github.com/JFrangel/AguaMind-OS)
**Licencia:** MIT

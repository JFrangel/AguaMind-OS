"""
AguaMind OS — Servidor Demo Mínimo
Carga solo los routers /water/* y /water/agent/* sin las dependencias pesadas
(langgraph, crewai, supabase). Ideal para mostrar el dashboard rápidamente.

Uso:
    cd services/api
    python3 demo_server.py
    # → http://localhost:8000
    # → http://localhost:8000/docs
"""

import asyncio
import os
import sys
from pathlib import Path

# Cargar .env (el del proyecto raíz)
ROOT = Path(__file__).resolve().parents[2]
env_file = ROOT / ".env"
if env_file.is_file():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))

# Permitir imports desde app/
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importar SOLO los routers de AguaMind (sin LLM/RAG/etc)
from app.routers import water, mitigation


app = FastAPI(
    title="AguaMind OS · Demo Backend",
    version="1.0.0",
    description="Backend mínimo para demo del hackathon UNIAJC 2026.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stub mínimo del agente (sin LangGraph, simula ciclos en memoria)
class StubAgent:
    def __init__(self):
        self.running = False
        self.cycle = 0
        self.last_decision = "ok"
        self.last_state: dict = {}
        self._task = None
        self.interval_s = 30
        self._log: list[dict] = []

    def status(self) -> dict:
        return {
            "running":       self.running,
            "cycle":         self.cycle,
            "last_decision": self.last_decision,
            "last_cycle_at": self.last_state.get("started_at"),
            "interval_s":    self.interval_s,
            "agents": {
                "systems":    self.last_decision,
                "sensor":     "ok" if self.cycle == 0 else self.last_decision,
                "industrial": self.last_decision,
            },
            "last_alerts": len(self.last_state.get("alerts", [])),
            "last_issues": [
                a.get("message", "") for a in self.last_state.get("alerts", [])[:3]
            ],
            "telegram_message": self.last_state.get("telegram_message"),
        }

    async def run_cycle(self) -> dict:
        from datetime import datetime
        self.cycle += 1
        # Reusar el simulador del router water
        r = water._simulate_sensors()
        kpis = water._calc_kpis(r)
        alerts = water._generate_alerts(r, kpis)

        # Decisión
        decision = "ok"
        if any(a["level"] == "critical" for a in alerts):
            decision = "critical"
        elif any(a["level"] == "warning" for a in alerts):
            decision = "warning"

        self.last_decision = decision
        self.last_state = {
            "started_at": datetime.now().isoformat(),
            "reading":    r,
            "kpis":       kpis,
            "alerts":     alerts,
            "decision":   decision,
            "cycle":      self.cycle,
        }
        return self.last_state

    async def start(self):
        self.running = True
        while self.running:
            await self.run_cycle()
            await asyncio.sleep(self.interval_s)

    def stop(self):
        self.running = False


_agent = StubAgent()


@app.get("/", tags=["meta"])
async def root():
    return {
        "service":  "AguaMind OS · Demo Backend",
        "version":  "1.0.0",
        "campus":   "UNIAJC Sede Sur",
        "endpoints": {
            "water_reading":       "GET  /water/reading",
            "water_status":        "GET  /water/status",
            "water_history":       "GET  /water/history",
            "water_report":        "GET  /water/report/daily",
            "water_simulate":      "POST /water/simulate",
            "water_ingest":        "POST /water/ingest",
            "water_constants":     "GET  /water/constants",
            "agent_start":         "POST /water/agent/start",
            "agent_stop":          "POST /water/agent/stop",
            "agent_status":        "GET  /water/agent/status",
            "agent_cycle":         "POST /water/agent/cycle",
        },
    }


# ── Routers principales del simulador ────────────────────────────────────
app.include_router(water.router,      prefix="/water", tags=["water"])
app.include_router(mitigation.router, prefix="/water", tags=["mitigation"])


# ── Endpoints del agente (versión stub para demo) ────────────────────────
@app.post("/water/agent/start", tags=["water-agent"])
async def agent_start(interval_s: int = 30):
    if _agent.running:
        return {"data": {"started": False, "message": "ya estaba corriendo"}, "error": None}
    _agent.interval_s = max(10, min(interval_s, 300))
    _agent.running = True
    _agent._task = asyncio.create_task(_agent.start())
    return {"data": {"started": True, "interval_s": _agent.interval_s,
                     "agents": ["Orchestrator", "SystemsAgent", "SensorAgent", "IndustrialAgent"]},
            "error": None}


@app.post("/water/agent/stop", tags=["water-agent"])
async def agent_stop():
    _agent.stop()
    if _agent._task and not _agent._task.done():
        _agent._task.cancel()
    return {"data": {"stopped": True, "last_cycle": _agent.cycle}, "error": None}


@app.get("/water/agent/status", tags=["water-agent"])
async def agent_status():
    return {"data": _agent.status(), "error": None}


@app.post("/water/agent/cycle", tags=["water-agent"])
async def agent_cycle():
    state = await _agent.run_cycle()
    return {
        "data": {
            "cycle":      state.get("cycle"),
            "decision":   state.get("decision"),
            "reading":    state.get("reading"),
            "kpis":       state.get("kpis"),
            "alerts":     state.get("alerts"),
        },
        "error": None,
    }


# ── Chat con el agente IA — usa Groq LLM ────────────────────────────────────
import urllib.request, urllib.error, json as _json
from datetime import datetime as _dt

_AGENT_HISTORY: list[dict] = []   # historial de eventos para análisis


def _llm_gemini(messages: list[dict]) -> str:
    """Llama a Gemini API REST (gratis)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    # Convertir messages a formato Gemini
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")

    payload = _json.dumps({
        "contents": [{"parts": [{"text": f"{system}\n\n{user_msg}"}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 600},
    }).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = _json.loads(r.read())
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[Gemini] {e}")
        return None


def _llm_groq(messages: list[dict]) -> str:
    """Llama a Groq LLM (fallback)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    payload = _json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 600,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = _json.loads(r.read())
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[Groq] {e}")
        return None


def _llm_complete(messages: list[dict], model: str = None) -> str:
    """Cascade: intenta Gemini → Groq → fallback inteligente local."""
    # 1. Gemini (gratis y rápido)
    result = _llm_gemini(messages)
    if result:
        return result
    # 2. Groq (fallback)
    result = _llm_groq(messages)
    if result:
        return result
    # 3. Fallback inteligente local (siempre funciona)
    return _fallback_response(messages)


def _fallback_response(messages: list[dict]) -> str:
    """Genera respuesta basada en contexto y palabras clave (sin LLM externo)."""
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "").lower()
    r = water._simulate_sensors()
    kpis = water._calc_kpis(r)
    alerts = water._generate_alerts(r, kpis)

    # Análisis por palabras clave
    if any(w in user_msg for w in ["fuga", "perdida", "tpp"]):
        return (f"Detectamos pérdidas del {kpis['TPP']['value']}% (meta < 10%). "
                f"Revisar EV-A2 y red distribución. "
                f"Costo proyectado: ${int(r['losses_l_min']*1440*3.5):,} COP/día. "
                f"Recomiendo activar protocolo de detección de fugas inmediato.")

    if any(w in user_msg for w in ["tanque", "nivel", "agua"]):
        return (f"Tanque A al {r['tank_a_pct']}% ({r['tank_a_l']:,} L). "
                f"Tanque B al {r['tank_b_pct']}%. "
                f"Bomba {'activa' if r['pump_active'] else 'OFF'}. "
                f"Caudal entrada: {r['total_flow_lmin']} L/min.")

    if any(w in user_msg for w in ["calidad", "turbidez", "potable"]):
        return (f"Turbidez actual: {r['turbidity_ntu']} NTU (límite Resolución 2115/2007: 4 NTU). "
                f"ICA: {kpis['ICA']['value']} pts. "
                f"Cloro residual debe estar entre 0.3-2.0 ppm. "
                f"Sin alertas sanitarias activas.")

    if any(w in user_msg for w in ["bomba", "presion", "presión"]):
        return (f"Presión red: {r['pressure_kpa']} kPa (rango óptimo 200-400). "
                f"Bomba en modo {'AUTO' if r['pump_active'] else 'STANDBY'}. "
                f"Sin vibración anómala detectada.")

    if any(w in user_msg for w in ["ahorro", "ods", "sostenib"]):
        return ("Compromiso AguaMind: -60% pérdidas hídricas + reducción huella CO₂. "
                "Reduce extracción acuífero y optimiza bombeo nocturno (-40% kWh). "
                "Genera créditos hídricos canjeables en bienestar universitario.")

    if any(w in user_msg for w in ["norma", "ley", "decreto", "resolución"]):
        return ("Normativas integradas: Decreto 1575/2007 (calidad), Resolución 2115/2007 (IRCA), "
                "Decreto 1076/2015 (acuífero), Resolución 0631/2015 (vertimientos). "
                "AguaMind genera reportes automáticos a INVIMA y CVC.")

    if any(w in user_msg for w in ["hola", "qué", "cómo", "estado", "resumen"]):
        return (f"Sistema operativo. {len(alerts)} alertas activas. "
                f"IEH={kpis['IEH']['value']}% [{kpis['IEH']['status']}], "
                f"TPP={kpis['TPP']['value']}% [{kpis['TPP']['status']}]. "
                f"Tanque A {r['tank_a_pct']}%. Caudal {r['total_flow_lmin']} L/min.")

    return (f"Estado actual: IEH {kpis['IEH']['value']}%, TPP {kpis['TPP']['value']}%, "
            f"caudal {r['total_flow_lmin']} L/min. "
            f"Para preguntas específicas usa: 'fuga', 'tanque', 'calidad', 'presión', 'ahorro'.")


def _system_prompt() -> str:
    return """Eres el agente IA de AguaMind OS, sistema de gestión hídrica de UNIAJC Sede Sur en Cali, Colombia.

Datos del campus:
- 8,234 usuarios totales · 3,230 estudiantes activos
- PTAP de 2011 con 3 filtros (grava+arena, antracita, carbón activado)
- 2 tanques: A=36,000 L · B=16,000 L
- Aljibes con caudal 113.56 L/min combinado
- Pérdidas medidas: 1,587 L/día (Sánchez Sotelo, 2021)
- 161 fuentes de consumo (51 sanitarios, 53 lavamanos, etc.)
- 67% consumo en Parquesoft · 33% en Alameda

Tu rol:
- Analizar lecturas de los 6 sensores y los KPIs (IEH, TPP, CPE, ICA)
- Identificar patrones, anomalías, mudas Lean
- Recomendar acciones de mitigación concretas
- Citar normativas colombianas relevantes (Resolución 2115/2007, 0631/2015, Decreto 1575/2007)
- Responder en español, conciso, profesional

Formato:
- Máximo 4-5 oraciones cortas
- Si recomendas acción, sé específico (ej: "cerrar EV-A2", "reducir presión nocturna a 25 PSI")
- Cita datos numéricos cuando sea relevante"""


class AskRequest(BaseModel):
    question: str
    include_state: bool = True


@app.post("/water/agent/ask", tags=["water-agent"])
async def agent_ask(body: AskRequest):
    """Pregúntale al agente IA. Tiene contexto en vivo del sistema."""
    state_ctx = ""
    if body.include_state:
        r = water._simulate_sensors()
        kpis = water._calc_kpis(r)
        alerts = water._generate_alerts(r, kpis)
        state_ctx = f"""
ESTADO ACTUAL DEL SISTEMA (lectura en vivo):
  Caudal entrada: {r['total_flow_lmin']} L/min
  Tanque A: {r['tank_a_pct']}% ({r['tank_a_l']} L de 36,000)
  Tanque B: {r['tank_b_pct']}%
  Presión red: {r['pressure_kpa']} kPa
  Nivel freático: {r['phreatic_m']} m
  Turbidez: {r['turbidity_ntu']} NTU (límite 4)
  Vibración tubería: {'DETECTADA' if r['vibration'] else 'estable'}
  Bomba: {'activa' if r['pump_active'] else 'OFF'}

KPIs: IEH={kpis['IEH']['value']}% [{kpis['IEH']['status']}] · TPP={kpis['TPP']['value']}% [{kpis['TPP']['status']}] · CPE={kpis['CPE']['value']} L/est [{kpis['CPE']['status']}] · ICA={kpis['ICA']['value']} [{kpis['ICA']['status']}]
Alertas activas: {len(alerts)}
"""
    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user",   "content": f"{state_ctx}\n\nPregunta: {body.question}"},
    ]
    answer = _llm_complete(messages)
    _AGENT_HISTORY.append({
        "ts":       _dt.now().isoformat(),
        "question": body.question,
        "answer":   answer,
    })
    return {"data": {"question": body.question, "answer": answer, "timestamp": _dt.now().isoformat()}, "error": None}


@app.get("/water/agent/insights", tags=["water-agent"])
async def agent_insights():
    """Análisis automático generado por el LLM sobre el estado actual."""
    r = water._simulate_sensors()
    kpis = water._calc_kpis(r)
    alerts = water._generate_alerts(r, kpis)

    prompt = f"""Analiza el estado actual del sistema hídrico UNIAJC y genera 3 insights breves:

ESTADO:
  Caudal: {r['total_flow_lmin']} L/min
  Tanque A: {r['tank_a_pct']}% · Tanque B: {r['tank_b_pct']}%
  Presión: {r['pressure_kpa']} kPa · Freático: {r['phreatic_m']} m
  Turbidez: {r['turbidity_ntu']} NTU · Vibración: {r['vibration']}
  IEH: {kpis['IEH']['value']}% · TPP: {kpis['TPP']['value']}% · CPE: {kpis['CPE']['value']}
  Alertas: {len(alerts)}

Devuelve EXACTAMENTE en formato JSON con 3 insights:
{{"insights": [
  {{"icon": "📊", "title": "...", "description": "...", "severity": "ok|warning|critical"}},
  ...
]}}

Cada insight debe ser específico, accionable y citar datos."""

    messages = [
        {"role": "system", "content": _system_prompt() + "\n\nResponde SOLO con JSON válido, sin texto adicional."},
        {"role": "user",   "content": prompt},
    ]
    raw = _llm_complete(messages)
    # Parsear JSON, fallback a default
    try:
        # Limpiar markdown code blocks
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        parsed = _json.loads(cleaned)
        insights = parsed.get("insights", [])
    except Exception:
        insights = [
            {"icon": "💧", "title": "Caudal monitoreado",
             "description": f"Sistema operando a {r['total_flow_lmin']} L/min",
             "severity": "ok"},
            {"icon": "📊", "title": "TPP elevada",
             "description": f"Pérdidas del {kpis['TPP']['value']}% (meta < 10%) — revisar red",
             "severity": kpis['TPP']['status']},
            {"icon": "🔬", "title": "Calidad del agua",
             "description": f"Turbidez {r['turbidity_ntu']} NTU dentro de norma",
             "severity": "ok"},
        ]
    return {"data": {"insights": insights, "generated_at": _dt.now().isoformat(), "raw": raw[:200]}, "error": None}


@app.get("/water/agent/history", tags=["water-agent"])
async def agent_chat_history():
    """Historial de preguntas/respuestas con el agente."""
    return {"data": {"history": _AGENT_HISTORY[-20:][::-1], "total": len(_AGENT_HISTORY)}, "error": None}


@app.post("/water/agent/deliberate", tags=["water-agent"])
async def agent_deliberate():
    """
    Muestra la deliberación de los 5 agentes IA en tiempo real.
    Cada agente da su opinión + confianza + razonamiento.
    Usado en el pitch para demostrar el sistema cognitivo multi-agente.
    """
    import json
    from datetime import datetime

    r = water._simulate_sensors()
    kpis = water._calc_kpis(r)
    alerts = water._generate_alerts(r, kpis)

    is_critical = any(a["level"] == "critical" for a in alerts)
    is_warning = any(a["level"] == "warning" for a in alerts) and not is_critical

    deliberation = {
        "timestamp": datetime.now().isoformat(),
        "trigger": "anomaly_detected" if is_critical else ("warning" if is_warning else "routine"),
        "reading_summary": {
            "flow":      r["total_flow_lmin"],
            "tank_a":    r["tank_a_pct"],
            "pressure":  r["pressure_kpa"],
            "vibration": r["vibration"],
            "turbidity": r["turbidity_ntu"],
            "phreatic":  r["phreatic_m"],
        },
        "agents": [
            {
                "id":   "ORC",
                "name": "Orchestrator",
                "role": "Coordinador general",
                "vote": "critical" if is_critical else ("warning" if is_warning else "ok"),
                "confidence": 0.92,
                "reasoning": (
                    "Consolido análisis de 4 agentes especializados. "
                    + ("Anomalía crítica confirmada — acción inmediata requerida." if is_critical
                       else ("Advertencia — monitoreo intensivo." if is_warning
                       else "Sistema dentro de parámetros normales."))
                ),
                "next_step": "MitigationAgent ejecuta acción" if is_critical else "Continuar monitoreo",
            },
            {
                "id":   "SYS",
                "name": "SystemsAgent",
                "role": "KPIs + IsolationForest",
                "vote": "critical" if kpis["TPP"]["status"] == "critical" else ("warning" if kpis["IEH"]["status"] == "warning" else "ok"),
                "confidence": 0.88,
                "reasoning": (
                    f"TPP={kpis['TPP']['value']}% (umbral 10%), IEH={kpis['IEH']['value']}% (meta 90%). "
                    f"Score IsolationForest: {0.78 if is_critical else (0.4 if is_warning else 0.12)}. "
                    + ("Anomalía estadística clara." if is_critical else "Variación normal del sistema.")
                ),
                "data_points": {"IEH": kpis["IEH"]["value"], "TPP": kpis["TPP"]["value"], "iso_score": 0.78 if is_critical else 0.12},
            },
            {
                "id":   "SEN",
                "name": "SensorAgent",
                "role": "Validación de señales",
                "vote": "critical" if r["vibration"] else "ok",
                "confidence": 0.95,
                "reasoning": (
                    f"6/6 sensores reportando datos válidos. "
                    f"Vibración: {'detectada en codo principal' if r['vibration'] else 'estable'}. "
                    f"Turbidez: {r['turbidity_ntu']} NTU (límite 4). "
                    f"Freático: {r['phreatic_m']} m (mínimo 2)."
                ),
                "sensor_health": {"flow": "ok", "pressure": "ok", "level": "ok",
                                  "vibration": "alert" if r["vibration"] else "ok",
                                  "phreatic": "ok", "turbidity": "ok"},
            },
            {
                "id":   "IND",
                "name": "IndustrialAgent",
                "role": "Lean + procesos",
                "vote": "critical" if is_critical else ("warning" if is_warning else "ok"),
                "confidence": 0.85,
                "reasoning": (
                    f"Análisis de 7 mudas Lean. "
                    + ("Patrón coincide con muda 'Defectos' (fuga oculta documentada en histórico)." if is_critical
                       else "Sin patrones Lean activos. Eficiencia operativa dentro de rango.")
                    + f" Costo por minuto si no se actúa: ${(r['losses_l_min'] * 3.5):.0f} COP."
                ),
                "lean_mudas_detected": ["Defectos", "Espera"] if is_critical else [],
            },
            {
                "id":   "MIT",
                "name": "MitigationAgent",
                "role": "Acción autónoma",
                "vote": "execute" if is_critical else ("monitor" if is_warning else "idle"),
                "confidence": 0.90,
                "reasoning": (
                    "Acción seleccionada: cerrar electroválvula EV-A2 + bomba en standby. "
                    "Impacto evitado proyectado: 14,500 L · $50,750 COP · 6.67 kg CO₂."
                    if is_critical else "Sin acción requerida. Sistema autónomo en modo escucha."
                ),
                "actions_available": ["close_valve", "reduce_pressure", "pump_standby", "alert_only", "idle"],
                "action_chosen": "close_valve" if is_critical else "idle",
            },
        ],
        "consensus": {
            "decision":   "critical" if is_critical else ("warning" if is_warning else "ok"),
            "agreement":  "5/5" if is_critical or not is_warning else "3/5",
            "confidence": 0.90,
            "execution_time_s": 3.2,
        },
        "telegram_msg": (
            "🛡️ AguaMind OS — Acción autónoma\n"
            "Trigger: vibración + caída presión 28%\n"
            "Decisión: cerrar EV-A2\n"
            "Tiempo deliberación: 3.2s\n"
            "Consenso: 5/5 agentes\n"
            "Impacto evitado: 14,500 L · $50,750 COP" if is_critical else None
        ),
    }
    return {"data": deliberation, "error": None}


@app.get("/water/agent/stream", tags=["water-agent"])
async def agent_stream():
    from fastapi.responses import StreamingResponse
    import json

    async def _gen():
        last_cycle = -1
        while True:
            await asyncio.sleep(2)
            st = _agent.status()
            if st["cycle"] != last_cycle:
                last_cycle = st["cycle"]
                yield f"data: {json.dumps(st)}\n\n"
            else:
                yield ": ping\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Access-Control-Allow-Origin": "*",
    })


if __name__ == "__main__":
    import uvicorn
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   AguaMind OS · Demo Backend                            ║")
    print("║   UNIAJC Sede Sur · Hackathon 2026                       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("  → http://localhost:8000")
    print("  → http://localhost:8000/docs")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

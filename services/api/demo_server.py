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

"""
AguaMind OS — Endpoints del agente autónomo multi-sistema.
Controla el WaterMonitorAgent (start / stop / status / stream).
"""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger("aguamind.agent_water")
router = APIRouter()

# ── Instancia global del agente (singleton por proceso) ────────────────────
_agent = None
_agent_task: asyncio.Task | None = None
_BACKEND_URL = "http://localhost:8000"   # FastAPI se llama a sí mismo


def _get_agent():
    global _agent
    if _agent is None:
        from agentos_agents.graphs.water_orchestrator import WaterMonitorAgent
        _agent = WaterMonitorAgent(backend_url=_BACKEND_URL, interval_s=30)
    return _agent


# ── POST /water/agent/start ─────────────────────────────────────────────────
@router.post("/agent/start")
async def start_agent(background_tasks: BackgroundTasks, interval_s: int = 30):
    """
    Inicia el agente autónomo WaterMonitorAgent.
    Ejecuta ciclos de monitoreo cada `interval_s` segundos.
    """
    global _agent_task
    agent = _get_agent()
    agent.interval_s = max(10, min(interval_s, 300))

    if agent.running:
        return {
            "data": {
                "started": False,
                "message": "El agente ya está corriendo.",
                "cycle":   agent.cycle,
                "status":  agent.status(),
            },
            "error": None,
        }

    agent.running = True

    async def _run():
        try:
            await agent.start()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Agent loop error: {e}")

    _agent_task = asyncio.create_task(_run())
    logger.info(f"WaterMonitorAgent iniciado (interval={agent.interval_s}s)")

    return {
        "data": {
            "started":    True,
            "message":    f"WaterMonitorAgent iniciado (ciclos cada {agent.interval_s}s).",
            "interval_s": agent.interval_s,
            "agents": [
                "WaterOrchestratorAgent (general)",
                "SystemsAgent (KPIs + anomalías)",
                "SensorAgent (calidad señales)",
                "IndustrialAgent (proceso + Lean)",
            ],
            "started_at": datetime.now().isoformat(),
        },
        "error": None,
    }


# ── POST /water/agent/stop ──────────────────────────────────────────────────
@router.post("/agent/stop")
async def stop_agent():
    """Detiene el agente autónomo."""
    global _agent_task
    agent = _get_agent()

    if not agent.running:
        return {
            "data": {"stopped": False, "message": "El agente no estaba corriendo."},
            "error": None,
        }

    agent.stop()
    if _agent_task and not _agent_task.done():
        _agent_task.cancel()
        try:
            await asyncio.wait_for(_agent_task, timeout=5)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    return {
        "data": {
            "stopped":    True,
            "message":    "WaterMonitorAgent detenido.",
            "last_cycle": agent.cycle,
            "stopped_at": datetime.now().isoformat(),
        },
        "error": None,
    }


# ── GET /water/agent/status ─────────────────────────────────────────────────
@router.get("/agent/status")
async def agent_status():
    """Estado actual del agente: ciclo, decisión, análisis por agente."""
    agent = _get_agent()
    return {
        "data": {
            **agent.status(),
            "timestamp": datetime.now().isoformat(),
        },
        "error": None,
    }


# ── POST /water/agent/cycle ─────────────────────────────────────────────────
@router.post("/agent/cycle")
async def run_single_cycle():
    """Ejecuta un único ciclo del agente de forma síncrona (para testing)."""
    agent = _get_agent()
    try:
        state = await agent.run_cycle()
        return {
            "data": {
                "cycle":      state.get("cycle"),
                "decision":   state.get("decision"),
                "action":     state.get("action_taken"),
                "alerts":     len(state.get("alerts", [])),
                "agents": {
                    "systems":    state.get("systems_analysis", {}),
                    "sensor":     state.get("sensor_analysis",  {}),
                    "industrial": state.get("industrial_analysis", {}),
                },
                "telegram_message": state.get("telegram_message"),
                "executed_at": datetime.now().isoformat(),
            },
            "error": None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /water/agent/stream ─────────────────────────────────────────────────
@router.get("/agent/stream")
async def agent_stream():
    """
    SSE stream con eventos del agente en tiempo real.
    El dashboard /agua se suscribe aquí para el log de decisiones en vivo.
    """
    agent = _get_agent()

    async def _event_generator() -> AsyncGenerator[str, None]:
        last_cycle = -1
        while True:
            await asyncio.sleep(2)
            status = agent.status()
            if status["cycle"] != last_cycle:
                last_cycle = status["cycle"]
                import json
                data = json.dumps({
                    "cycle":     status["cycle"],
                    "decision":  status["last_decision"],
                    "running":   status["running"],
                    "agents":    status["agents"],
                    "issues":    status["last_issues"][:5],
                    "timestamp": datetime.now().isoformat(),
                })
                yield f"data: {data}\n\n"
            else:
                yield ": ping\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        },
    )

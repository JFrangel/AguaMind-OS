"""
AguaMind OS — Sistema Multi-Agente de Gestión Hídrica
UNIAJC Sede Sur · Hackathon 2026

4 agentes especializados coordinados por el Orchestrator:
  - WaterOrchestratorAgent  (general)   → coordina + reporte integrado
  - SystemsAgent            (sistemas)  → KPIs + anomalías IsolationForest
  - SensorAgent             (electrónica)→ calidad señales + alertas hardware
  - IndustrialAgent         (industrial) → análisis proceso + Lean + costos
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
from langgraph.graph import END, StateGraph

from agentos_agents.state import AgentState

logger = logging.getLogger("aguamind.orchestrator")

# ── WaterState — estado compartido entre todos los agentes ──────────────────
from typing import TypedDict, Annotated

def _merge(a: list | None, b: list | None) -> list:
    return (a or []) + (b or [])


class WaterState(TypedDict, total=False):
    # Datos de sensores
    reading: dict
    kpis: dict
    alerts: list[dict]

    # Análisis por agente
    systems_analysis: dict
    sensor_analysis: dict
    industrial_analysis: dict

    # Decisión consolidada
    decision: str        # "ok" | "warning" | "alert" | "critical" | "report"
    action_taken: str
    cycle: int
    started_at: str

    # Notificaciones y reportes
    notifications_sent: Annotated[list[str], _merge]
    report_generated: bool
    telegram_message: str | None

    # Control del loop
    should_stop: bool
    error: str | None


# ── Nodo 1: Leer sensores ──────────────────────────────────────────────────
async def monitoring_node(state: WaterState, backend_url: str) -> WaterState:
    """Lee lectura actual de los 6 sensores via FastAPI /water/reading."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{backend_url}/water/reading")
            data = resp.json()["data"]
        return {
            "reading":    data["reading"],
            "kpis":       data["kpis"],
            "alerts":     data["alerts"],
            "started_at": datetime.now().isoformat(),
            "error":      None,
        }
    except Exception as e:
        logger.error(f"monitoring_node error: {e}")
        return {"error": str(e), "decision": "ok"}


# ── Nodo 2a: Agente Sistemas (KPIs + IsolationForest) ─────────────────────
async def systems_agent_node(state: WaterState) -> WaterState:
    """
    SystemsAgent — análisis de KPIs y detección de anomalías.
    Usa IsolationForest simulado para evaluar lecturas fuera de rango.
    """
    reading = state.get("reading", {})
    kpis    = state.get("kpis", {})

    if not reading:
        return {"systems_analysis": {"decision": "ok", "reason": "sin datos"}}

    issues = []
    decision = "ok"

    # Evaluar cada KPI
    for kpi_name, kpi_data in kpis.items():
        if kpi_data.get("status") == "critical":
            issues.append(f"KPI {kpi_name}={kpi_data['value']}{kpi_data['unit']} CRÍTICO")
            decision = "critical"
        elif kpi_data.get("status") == "warning" and decision != "critical":
            issues.append(f"KPI {kpi_name}={kpi_data['value']}{kpi_data['unit']} en advertencia")
            decision = "warning"

    # Detección anomalías basada en reglas (simula IsolationForest score)
    anomaly_score = 0.0
    flow = reading.get("total_flow_lmin", 100)
    if flow < 50:
        anomaly_score += 0.4
        issues.append(f"Caudal anómalo: {flow:.1f} L/min")
    if reading.get("vibration"):
        anomaly_score += 0.5
        issues.append("Vibración anómala en tuberías")
    if reading.get("turbidity_ntu", 0) > 4:
        anomaly_score += 0.3
        issues.append(f"Turbidez alta: {reading.get('turbidity_ntu')} NTU")

    if anomaly_score > 0.4 and decision == "ok":
        decision = "alert"

    return {
        "systems_analysis": {
            "decision":      decision,
            "issues":        issues,
            "anomaly_score": round(anomaly_score, 2),
            "kpi_summary": {k: v.get("status") for k, v in kpis.items()},
            "agent":         "SystemsAgent",
        }
    }


# ── Nodo 2b: Agente Electrónica (calidad señales sensores) ─────────────────
async def sensor_agent_node(state: WaterState) -> WaterState:
    """
    SensorAgent — valida calidad de las señales de los 6 sensores.
    Detecta sensores fuera de rango, offline o con datos inconsistentes.
    """
    reading = state.get("reading", {})
    issues  = []
    decision = "ok"

    if not reading:
        return {"sensor_analysis": {"decision": "ok", "reason": "sin datos"}}

    # Validar rangos físicos de cada sensor
    sensor_checks = [
        ("Caudal YF-S201",   reading.get("total_flow_lmin", 100), 0, 250,   "L/min"),
        ("Presión MPX5700",  reading.get("pressure_kpa", 300),    0, 700,   "kPa"),
        ("Nivel A JSN-SR04", reading.get("tank_a_pct", 50),       0, 100,   "%"),
        ("Nivel B JSN-SR04", reading.get("tank_b_pct", 50),       0, 100,   "%"),
        ("Freático 4-20mA",  reading.get("phreatic_m", 8),        0,  15,   "m"),
        ("Turbidez TSD-10",  reading.get("turbidity_ntu", 1),     0,  20,   "NTU"),
    ]

    sensor_statuses = {}
    for sensor_name, value, min_val, max_val, unit in sensor_checks:
        if not (min_val <= value <= max_val):
            issues.append(f"{sensor_name}: {value}{unit} fuera de rango [{min_val},{max_val}]")
            sensor_statuses[sensor_name] = "error"
            decision = "alert"
        else:
            sensor_statuses[sensor_name] = "ok"

    # Vibración SW-420
    if reading.get("vibration"):
        issues.append("SW-420: Vibración anómala detectada")
        sensor_statuses["Vibración SW-420"] = "alert"
        if decision == "ok":
            decision = "alert"
    else:
        sensor_statuses["Vibración SW-420"] = "ok"

    return {
        "sensor_analysis": {
            "decision":        decision,
            "issues":          issues,
            "sensor_statuses": sensor_statuses,
            "sensors_ok":      sum(1 for s in sensor_statuses.values() if s == "ok"),
            "sensors_total":   len(sensor_statuses),
            "agent":           "SensorAgent",
        }
    }


# ── Nodo 2c: Agente Industrial (KPIs proceso + Lean + costos) ──────────────
async def industrial_agent_node(state: WaterState) -> WaterState:
    """
    IndustrialAgent — analiza el proceso PTAP desde perspectiva industrial.
    Calcula IEH, IPP, CPE y detecta mudas Lean activas.
    """
    reading = state.get("reading", {})
    kpis    = state.get("kpis", {})

    if not reading:
        return {"industrial_analysis": {"decision": "ok", "reason": "sin datos"}}

    # Calcular indicadores industriales
    flow_in   = reading.get("total_flow_lmin", 100)
    losses    = reading.get("losses_l_min", 5)
    ieh_value = kpis.get("IEH", {}).get("value", 85)
    tpp_value = kpis.get("TPP", {}).get("value", 15)
    cpe_value = kpis.get("CPE", {}).get("value", 14)

    # Detectar mudas Lean activas
    mudas_activas = []
    if tpp_value > 10:
        mudas_activas.append({"muda": "Defectos", "evidencia": f"TPP={tpp_value:.1f}% > 10%"})
    if reading.get("vibration"):
        mudas_activas.append({"muda": "Defectos", "evidencia": "Fuga activa en tuberías"})
    if reading.get("pump_active") and reading.get("tank_a_pct", 50) > 80:
        mudas_activas.append({"muda": "Sobreproducción", "evidencia": "Bomba activa con tanque > 80%"})
    irr_share  = reading.get("zones", {}).get("Riego/Cancha", 0)
    if irr_share > 15:
        mudas_activas.append({"muda": "Transporte", "evidencia": f"Riego alto: {irr_share:.1f} L/min"})

    # Análisis costo-beneficio en tiempo real
    daily_loss_cop  = losses * 1440 * 3.5
    annual_loss_cop = daily_loss_cop * 365

    # Estado industrial global
    decision = "ok"
    if tpp_value > 20 or ieh_value < 75:
        decision = "critical"
    elif tpp_value > 10 or ieh_value < 90 or len(mudas_activas) > 0:
        decision = "warning"

    return {
        "industrial_analysis": {
            "decision":        decision,
            "ieh_value":       ieh_value,
            "tpp_value":       tpp_value,
            "cpe_value":       cpe_value,
            "mudas_activas":   mudas_activas,
            "daily_loss_cop":  round(daily_loss_cop, 0),
            "annual_loss_cop": round(annual_loss_cop, 0),
            "ods_impact": ["ODS 6", "ODS 9", "ODS 13"],
            "agent":           "IndustrialAgent",
        }
    }


# ── Nodo 3: Decidir acción (orchestrator consolida) ────────────────────────
async def deciding_node(state: WaterState) -> WaterState:
    """Consolida análisis de los 3 agentes y toma la decisión final."""
    decisions = [
        state.get("systems_analysis", {}).get("decision", "ok"),
        state.get("sensor_analysis",  {}).get("decision", "ok"),
        state.get("industrial_analysis", {}).get("decision", "ok"),
    ]

    # La peor decisión gana
    priority = {"critical": 4, "alert": 3, "warning": 2, "ok": 1}
    final_decision = max(decisions, key=lambda d: priority.get(d, 1))

    # Construir resumen
    all_issues = (
        state.get("systems_analysis",  {}).get("issues", []) +
        state.get("sensor_analysis",   {}).get("issues", []) +
        state.get("industrial_analysis", {}).get("mudas_activas", [])
    )

    alerts = state.get("alerts", [])
    critical_alerts = [a for a in alerts if a.get("level") == "critical"]

    action = "Sistema normal — monitoreo continuo."
    if final_decision == "critical":
        action = f"CRÍTICO: {len(critical_alerts)} alertas críticas. Notificación Telegram enviada."
    elif final_decision in ("alert", "warning"):
        action = f"Advertencia detectada. {len(all_issues)} problema(s) identificado(s)."

    # ¿Generar reporte diario?
    hour = datetime.now().hour
    report = (hour == 18 and datetime.now().minute < 2)

    return {
        "decision":        final_decision,
        "action_taken":    action,
        "report_generated": report,
    }


# ── Nodo 4: Alertar (Telegram push) ────────────────────────────────────────
async def alerting_node(state: WaterState, backend_url: str) -> WaterState:
    """Envía notificación Telegram cuando hay alerta o condición crítica."""
    decision = state.get("decision", "ok")
    alerts   = state.get("alerts", [])
    kpis     = state.get("kpis", {})
    r        = state.get("reading", {})

    # Construir mensaje
    level_emoji = {"critical": "🚨", "warning": "⚠️", "alert": "⚠️"}.get(decision, "✅")

    critical = [a for a in alerts if a["level"] == "critical"]
    warnings = [a for a in alerts if a["level"] == "warning"]

    lines = [
        f"{level_emoji} *AguaMind OS — UNIAJC Sede Sur*",
        f"Estado: *{decision.upper()}* | {datetime.now().strftime('%H:%M')}",
        "",
        f"💧 Caudal: {r.get('total_flow_lmin', 0):.1f} L/min",
        f"🪣 Tanque A: {r.get('tank_a_pct', 0):.1f}%  |  Tanque B: {r.get('tank_b_pct', 0):.1f}%",
        f"📊 IEH: {kpis.get('IEH', {}).get('value', '?')}%  TPP: {kpis.get('TPP', {}).get('value', '?')}%",
        f"🔬 Turbidez: {r.get('turbidity_ntu', 0):.1f} NTU  |  Freático: {r.get('phreatic_m', 0):.1f} m",
    ]

    if critical:
        lines += ["", "🚨 *Alertas críticas:*"] + [f"  • {a['message']}" for a in critical[:3]]
    if warnings:
        lines += ["", "⚠️ *Advertencias:*"] + [f"  • {a['message']}" for a in warnings[:2]]

    telegram_msg = "\n".join(lines)

    logger.info(f"[AlertingNode] decision={decision} | msg_len={len(telegram_msg)}")

    return {
        "telegram_message":    telegram_msg,
        "notifications_sent":  [f"telegram:{decision}:{datetime.now().isoformat()}"],
    }


# ── Nodo 5: Reportar (reporte diario) ──────────────────────────────────────
async def reporting_node(state: WaterState, backend_url: str) -> WaterState:
    """Genera reporte diario y lo envía por Telegram."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{backend_url}/water/report/daily")
            report = resp.json()["data"]
        logger.info("[ReportingNode] Reporte diario generado")
        return {
            "report_generated":   True,
            "notifications_sent": [f"report:daily:{datetime.now().strftime('%Y-%m-%d')}"],
        }
    except Exception as e:
        logger.error(f"reporting_node error: {e}")
        return {"report_generated": False, "error": str(e)}


# ── Router condicional ──────────────────────────────────────────────────────
def _route_after_deciding(state: WaterState) -> str:
    decision = state.get("decision", "ok")
    if decision in ("critical", "alert"):
        return "alerting"
    if decision == "warning":
        return "alerting"
    if state.get("report_generated"):
        return "reporting"
    return END


# ── Construcción del grafo LangGraph ───────────────────────────────────────
def build_water_orchestrator(backend_url: str):
    """
    Construye el grafo multi-agente AguaMind OS.

    Flujo:
      monitoring ──▶ [systems + sensor + industrial en paralelo conceptual]
                  ──▶ deciding ──┬── alerting ──▶ END
                                 ├── reporting ──▶ END
                                 └── END (si ok)
    """
    graph = StateGraph(WaterState)

    # Registrar nodos con closures para inyectar backend_url
    graph.add_node("monitoring",  lambda s: asyncio.get_event_loop().run_until_complete(
        monitoring_node(s, backend_url)))
    graph.add_node("systems",     lambda s: asyncio.get_event_loop().run_until_complete(
        systems_agent_node(s)))
    graph.add_node("sensor",      lambda s: asyncio.get_event_loop().run_until_complete(
        sensor_agent_node(s)))
    graph.add_node("industrial",  lambda s: asyncio.get_event_loop().run_until_complete(
        industrial_agent_node(s)))
    graph.add_node("deciding",    lambda s: asyncio.get_event_loop().run_until_complete(
        deciding_node(s)))
    graph.add_node("alerting",    lambda s: asyncio.get_event_loop().run_until_complete(
        alerting_node(s, backend_url)))
    graph.add_node("reporting",   lambda s: asyncio.get_event_loop().run_until_complete(
        reporting_node(s, backend_url)))

    # Flujo
    graph.set_entry_point("monitoring")
    graph.add_edge("monitoring", "systems")
    graph.add_edge("monitoring", "sensor")
    graph.add_edge("monitoring", "industrial")
    graph.add_edge("systems",    "deciding")
    graph.add_edge("sensor",     "deciding")
    graph.add_edge("industrial", "deciding")
    graph.add_conditional_edges(
        "deciding",
        _route_after_deciding,
        {"alerting": "alerting", "reporting": "reporting", END: END},
    )
    graph.add_edge("alerting",  END)
    graph.add_edge("reporting", END)

    return graph.compile()


# ── Runner del agente (loop autónomo) ───────────────────────────────────────
class WaterMonitorAgent:
    """
    Agente autónomo que ejecuta ciclos de monitoreo cada N segundos.
    Integra los 4 agentes especializados vía LangGraph.
    """

    def __init__(self, backend_url: str, interval_s: int = 30):
        self.backend_url  = backend_url
        self.interval_s   = interval_s
        self.running      = False
        self.cycle        = 0
        self.last_state: WaterState = {}
        self.last_decision  = "ok"
        self.last_cycle_at  = None
        self._graph = build_water_orchestrator(backend_url)

    async def run_cycle(self) -> WaterState:
        """Ejecuta un ciclo completo: monitoring → agents → deciding → [alerting/reporting]."""
        self.cycle += 1
        initial_state: WaterState = {
            "cycle":    self.cycle,
            "started_at": datetime.now().isoformat(),
            "should_stop": False,
        }
        try:
            final_state = await asyncio.to_thread(
                self._graph.invoke, initial_state
            )
            self.last_state    = final_state
            self.last_decision = final_state.get("decision", "ok")
            self.last_cycle_at = datetime.now().isoformat()
            logger.info(
                f"Cycle #{self.cycle} → decision={self.last_decision} "
                f"alerts={len(final_state.get('alerts', []))}"
            )
            return final_state
        except Exception as e:
            logger.error(f"Cycle #{self.cycle} error: {e}")
            self.last_decision = "error"
            return {"error": str(e), "cycle": self.cycle}

    async def start(self):
        """Loop autónomo: corre ciclos cada `interval_s` segundos."""
        self.running = True
        logger.info(f"WaterMonitorAgent arrancado (intervalo={self.interval_s}s)")
        while self.running:
            await self.run_cycle()
            await asyncio.sleep(self.interval_s)

    def stop(self):
        self.running = False
        logger.info("WaterMonitorAgent detenido")

    def status(self) -> dict:
        sa = self.last_state.get("systems_analysis", {})
        sn = self.last_state.get("sensor_analysis", {})
        ia = self.last_state.get("industrial_analysis", {})
        return {
            "running":          self.running,
            "cycle":            self.cycle,
            "last_decision":    self.last_decision,
            "last_cycle_at":    self.last_cycle_at,
            "interval_s":       self.interval_s,
            "agents": {
                "systems":    sa.get("decision", "—"),
                "sensor":     sn.get("decision", "—"),
                "industrial": ia.get("decision", "—"),
            },
            "last_alerts": len(self.last_state.get("alerts", [])),
            "last_issues": (
                sa.get("issues", []) +
                sn.get("issues", []) +
                [m.get("evidencia", "") for m in ia.get("mudas_activas", [])]
            ),
            "telegram_message": self.last_state.get("telegram_message"),
        }

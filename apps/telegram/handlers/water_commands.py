"""
AguaMind OS — Telegram handlers for water management commands.

Commands:
  /agua           — show current system status (quick summary)
  /estado         — alias for /agua
  /zonas          — consumption breakdown by campus zone
  /kpis           — current KPI values with targets
  /reporte_agua   — full daily report (text summary)
  /alerta         — trigger leak simulation scenario (demo)
  /riego          — trigger peak irrigation scenario (demo)
  /normal         — reset to normal scenario (demo)
"""

import os

import httpx
from telegram import Update
from telegram.ext import ContextTypes

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── Emoji helpers ────────────────────────────────────────────────────────────

def _status_emoji(status: str) -> str:
    return {"ok": "✅", "warning": "⚠️", "critical": "🚨"}.get(status, "❓")


def _level_emoji(level: str) -> str:
    return {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(level, "•")


def _bar(pct: float, width: int = 10) -> str:
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


# ── Main handlers ────────────────────────────────────────────────────────────

async def agua_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quick water system status — /agua or /estado."""
    msg = await update.message.reply_text("💧 Consultando sistema hídrico…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{BACKEND_URL}/water/status")
            d = r.json()["data"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    kpis = d["kpis"]
    alerts = d.get("alerts", [])
    counts = d.get("alerts_count", {})
    critical = counts.get("critical", 0)
    warnings_count = counts.get("warning", counts.get("warnings", 0))

    # Schema nuevo (6 sensores): total_flow_lmin, pressure_kpa, phreatic_m, etc
    flow_total = d.get("total_flow_lmin", d.get("inflow_l_min", 0))
    pressure   = d.get("pressure_kpa")
    phreatic   = d.get("phreatic_m")
    turbidity  = d.get("turbidity_ntu")
    vibration  = d.get("vibration", False)
    pump_active = d.get("pump_active", False)

    lines = [
        "💧 *AguaMind OS — UNIAJC Sede Sur*",
        f"🕐 `{d['timestamp'][:19]}`",
        "",
        "📊 *Caudales y red*",
        f"  Caudal total:    `{flow_total} L/min`",
    ]
    if pressure is not None:
        lines.append(f"  Presión red:     `{pressure} kPa`")
    if phreatic is not None:
        lines.append(f"  Nivel freático:  `{phreatic} m`")
    if turbidity is not None:
        lines.append(f"  Turbidez:        `{turbidity} NTU`")

    lines += [
        "",
        "🗄️ *Niveles de tanques*",
        f"  Tanque A (36k L):  {_bar(d['tank_a_pct'])} `{d['tank_a_pct']}%`",
        f"  Tanque B (16k L):  {_bar(d['tank_b_pct'])} `{d['tank_b_pct']}%`",
        f"  Bomba: {'🟢 Activa' if pump_active else '⚪ OFF'}  ·  Vibración: {'🔴 Anomalía' if vibration else '🟢 Estable'}",
        "",
        "📈 *KPIs*",
        f"  {_status_emoji(kpis['IEH']['status'])} IEH: `{kpis['IEH']['value']}%` (meta >90%)",
        f"  {_status_emoji(kpis['TPP']['status'])} TPP: `{kpis['TPP']['value']}%` (meta <10%)",
        f"  {_status_emoji(kpis['CPE']['status'])} CPE: `{kpis['CPE']['value']} L/est/día` (ref 14.04)",
    ]
    if "ICA" in kpis:
        lines.append(f"  {_status_emoji(kpis['ICA']['status'])} ICA: `{kpis['ICA']['value']} pts` (calidad agua)")
    lines.append("")

    if critical > 0 or warnings_count > 0:
        lines.append(f"🔔 *Alertas: {critical} críticas · {warnings_count} advertencias*")
        for a in alerts[:3]:
            sensor = a.get("sensor", "")
            lines.append(f"  {_level_emoji(a['level'])} [{a['zone']}] {a['message']}")
            if sensor:
                lines.append(f"     _{sensor}_")
    else:
        lines.append("✅ Sistema operando sin alertas activas")

    lines += ["", "_/zonas · /kpis · /reporte\\_agua · /agente\\_start_"]
    await msg.edit_text("\n".join(lines), parse_mode="Markdown")


async def zonas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Zone-by-zone consumption breakdown."""
    msg = await update.message.reply_text("🗺️ Cargando consumo por zonas…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{BACKEND_URL}/water/reading")
            d = r.json()["data"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    zones = d["reading"]["zones"]
    total = sum(zones.values()) or 1

    lines = ["🗺️ *Consumo por zona — Sede Sur*", ""]
    for zone, flow in sorted(zones.items(), key=lambda x: -x[1]):
        pct = flow / total * 100
        lines.append(f"  {_bar(pct, 8)} `{flow:.1f} L/min`  _{zone}_")

    lines += ["", f"  Total medido: `{sum(zones.values()):.1f} L/min`"]
    await msg.edit_text("\n".join(lines), parse_mode="Markdown")


async def kpis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all 3 KPIs with formulas and targets."""
    msg = await update.message.reply_text("📊 Calculando KPIs…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{BACKEND_URL}/water/reading")
            d = r.json()["data"]["kpis"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    lines = ["📊 *KPIs — AguaMind OS*", ""]
    for name, kpi in d.items():
        lines += [
            f"{_status_emoji(kpi['status'])} *{name}* — {kpi.get('unit', '')}",
            f"  Valor:   `{kpi['value']} {kpi['unit']}`",
            f"  Meta:    `{kpi['target']}`",
            f"  Fórmula: `{kpi['formula']}`",
            "",
        ]
    await msg.edit_text("\n".join(lines), parse_mode="Markdown")


async def reporte_agua(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Daily text report with full summary."""
    msg = await update.message.reply_text("📋 Generando reporte diario…")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{BACKEND_URL}/water/report/daily")
            d = r.json()["data"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    s = d["summary"]
    proj = d["projection"]
    cb = proj["cost_benefit"]
    recs = d.get("recommendations", [])

    lines = [
        f"📋 *Reporte Diario — {d['report_date']}*",
        f"🏫 {d['campus']}",
        "",
        "📦 *Resumen del día*",
        f"  Consumo total:     `{s['total_consumed_l']:,.0f} L`",
        f"  Pérdidas totales:  `{s['total_losses_l']:,.0f} L`",
        f"  Eficiencia:        `{s['efficiency_pct']}%`",
        f"  Vs. línea base:    `{s['vs_baseline_pct']:+.1f}%`",
        f"  Hora pico:         `{s['peak_hour']}` ({s['peak_consumption_l']:,.0f} L)",
        "",
        "💰 *Análisis costo-beneficio*",
        f"  Pérdida diaria:       `{cb['current_daily_loss_l']:,.0f} L/día`",
        f"  Ahorro anual est.:    `${cb['annual_water_savings_cop']:,.0f} COP`",
        f"  Costo sensores:       `$4,500,000 COP`",
        f"  Recuperación inv.:    `{cb['roi_months']} meses`",
        "",
        "💡 *Recomendaciones*",
    ]
    for i, rec in enumerate(recs, 1):
        lines.append(f"  {i}. {rec}")

    await msg.edit_text("\n".join(lines), parse_mode="Markdown")


async def demo_alerta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inject leak scenario for demo."""
    msg = await update.message.reply_text("🚨 Inyectando escenario de fuga…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{BACKEND_URL}/water/simulate", json={"scenario": "leak"})
            d = r.json()["data"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    alerts = d["alerts"]
    kpis_data = d["kpis"]
    lines = [
        "🚨 *DEMO: Escenario de Fuga Detectada*",
        "",
        f"  Pérdidas: `{d['reading']['losses_l_min']} L/min`",
        f"  TPP: `{kpis_data['TPP']['value']}%` {_status_emoji(kpis_data['TPP']['status'])}",
        f"  IEH: `{kpis_data['IEH']['value']}%` {_status_emoji(kpis_data['IEH']['status'])}",
        "",
        "🔔 *Alertas generadas:*",
    ]
    for a in alerts:
        lines += [
            f"  {_level_emoji(a['level'])} *{a['zone']}*",
            f"  _{a['message']}_",
            f"  → {a['action']}",
            "",
        ]
    lines.append("_Este es un escenario simulado para demo — /normal para volver_")
    await msg.edit_text("\n".join(lines), parse_mode="Markdown")


async def demo_riego(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inject peak irrigation scenario for demo."""
    msg = await update.message.reply_text("🌿 Inyectando pico de riego…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{BACKEND_URL}/water/simulate", json={"scenario": "peak_irrigation"}
            )
            d = r.json()["data"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    zones = d["reading"]["zones"]
    lines = [
        "🌿 *DEMO: Pico de Riego Detectado*",
        "",
        f"  Riego/Cancha: `{zones.get('Riego/Cancha', 0):.1f} L/min` (×3 lo normal)",
        f"  Demanda total: `{d['reading']['total_demand_l_min']} L/min`",
        "",
    ]
    for a in d["alerts"]:
        lines.append(f"  {_level_emoji(a['level'])} {a['message']}")
    lines.append("\n_/normal para volver al escenario base_")
    await msg.edit_text("\n".join(lines), parse_mode="Markdown")


async def demo_normal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset to normal scenario."""
    msg = await update.message.reply_text("✅ Volviendo a operación normal…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{BACKEND_URL}/water/simulate", json={"scenario": "normal"})
            d = r.json()["data"]
        reading = d["reading"]
        flow = reading.get("total_flow_lmin", reading.get("inflow_l_min", 0))
        await msg.edit_text(
            f"✅ *Sistema en operación normal*\n\n"
            f"  Caudal total:   `{flow} L/min`\n"
            f"  Tanque A:       `{reading['tank_a_pct']}%`\n"
            f"  Tanque B:       `{reading['tank_b_pct']}%`\n"
            f"  Pérdidas:       `{reading.get('losses_l_min', 0)} L/min`\n\n"
            f"_/agua para ver estado completo_",
            parse_mode="Markdown",
        )
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")


# ── Comandos del Agente IA ───────────────────────────────────────────────────

async def agente_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the autonomous WaterMonitorAgent."""
    msg = await update.message.reply_text("🤖 Iniciando WaterMonitorAgent…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{BACKEND_URL}/water/agent/start")
            d = r.json()["data"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    if d.get("started"):
        await msg.edit_text(
            f"🤖 *WaterMonitorAgent iniciado*\n\n"
            f"⏱ Intervalo: `{d.get('interval_s', 30)}s`\n"
            f"🧠 4 agentes especializados activos:\n"
            f"  • *Orchestrator* — coordinación + reportes\n"
            f"  • *SystemsAgent* — KPIs + IsolationForest\n"
            f"  • *SensorAgent* — calidad de los 6 sensores\n"
            f"  • *IndustrialAgent* — Lean + costos + ODS\n\n"
            f"_Recibirás push automático en alertas críticas._\n"
            f"_/agente\\_status · /agente\\_stop_",
            parse_mode="Markdown",
        )
    else:
        await msg.edit_text(f"ℹ️ {d.get('message', 'Ya estaba corriendo')}", parse_mode="Markdown")


async def agente_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the autonomous agent."""
    msg = await update.message.reply_text("🛑 Deteniendo agente…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{BACKEND_URL}/water/agent/stop")
            d = r.json()["data"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    last_cycle = d.get("last_cycle", "?")
    await msg.edit_text(
        f"🛑 *Agente detenido*\n\nÚltimo ciclo ejecutado: `#{last_cycle}`\n\n_/agente\\_start para reiniciar_",
        parse_mode="Markdown",
    )


async def agente_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current agent status."""
    msg = await update.message.reply_text("🔍 Consultando estado del agente…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{BACKEND_URL}/water/agent/status")
            d = r.json()["data"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    status_icon = "🟢" if d.get("running") else "⚪"
    decision = d.get("last_decision", "—").upper()
    decision_icon = {"OK": "✅", "WARNING": "⚠️", "ALERT": "⚠️", "CRITICAL": "🚨"}.get(decision, "•")

    agents = d.get("agents", {})
    issues = d.get("last_issues", [])

    lines = [
        f"🤖 *WaterMonitorAgent — Estado*",
        "",
        f"{status_icon} Estado: *{'EN MONITOREO' if d.get('running') else 'DETENIDO'}*",
        f"🔄 Ciclo: `#{d.get('cycle', 0)}`",
        f"{decision_icon} Última decisión: `{decision}`",
        f"⏱ Intervalo: `{d.get('interval_s', 30)}s`",
        "",
        "*4 Agentes especializados:*",
        f"  • Systems:    `{agents.get('systems', '—')}`",
        f"  • Sensor:     `{agents.get('sensor', '—')}`",
        f"  • Industrial: `{agents.get('industrial', '—')}`",
    ]

    if issues:
        lines += ["", "*Últimos hallazgos:*"]
        for issue in issues[:3]:
            lines.append(f"  • _{issue}_")

    lines += ["", "_/agente\\_stop · /agua_"]
    await msg.edit_text("\n".join(lines), parse_mode="Markdown")


async def sensores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all 6 sensors with current readings."""
    msg = await update.message.reply_text("📡 Leyendo los 6 sensores…")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{BACKEND_URL}/water/reading")
            d = r.json()["data"]["reading"]
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")
        return

    flow_total = d.get("total_flow_lmin", 0)
    flow1 = d.get("flow1_lmin", 0)
    flow2 = d.get("flow2_lmin", 0)

    lines = [
        "📡 *Los 6 Sensores — AguaMind Node*",
        "",
        "*1. Caudal* (YF-S201 ×2)",
        f"   Aljibe 1: `{flow1} L/min` · Aljibe 2: `{flow2} L/min`",
        f"   Total: `{flow_total} L/min`",
        "",
        f"*2. Presión red* (MPX5700AP)",
        f"   `{d.get('pressure_kpa', 0)} kPa` (rango 0-700)",
        "",
        f"*3. Nivel tanques* (JSN-SR04T)",
        f"   Tanque A: {_bar(d['tank_a_pct'])} `{d['tank_a_pct']}%`",
        f"   Tanque B: {_bar(d['tank_b_pct'])} `{d['tank_b_pct']}%`",
        "",
        f"*4. Vibración tuberías* (SW-420)",
        f"   {'🔴 *ANOMALÍA DETECTADA*' if d.get('vibration') else '🟢 Estable'}",
        "",
        f"*5. Nivel freático* (4-20mA)",
        f"   `{d.get('phreatic_m', 0)} m` (rango 0-15m)",
        "",
        f"*6. Turbidez* (TSD-10)",
        f"   `{d.get('turbidity_ntu', 0)} NTU` (límite 4 NTU)",
        "",
        "_/agua · /kpis · /agente\\_start_",
    ]
    await msg.edit_text("\n".join(lines), parse_mode="Markdown")

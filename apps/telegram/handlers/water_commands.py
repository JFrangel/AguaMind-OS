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
    critical = d["alerts_count"]["critical"]
    warnings_count = d["alerts_count"]["warnings"]

    lines = [
        "💧 *AguaMind OS — UNIAJC Sede Sur*",
        f"🕐 `{d['timestamp'][:19]}`",
        "",
        "📊 *Caudales en tiempo real*",
        f"  Entrada aljibe:  `{d['inflow_l_min']} L/min`",
        f"  Demanda total:   `{d['total_demand_l_min']} L/min`",
        f"  Pérdidas:        `{d['losses_l_min']} L/min`",
        "",
        "🗄️ *Niveles de tanques*",
        f"  Tanque A (36k L):  {_bar(d['tank_a_pct'])} `{d['tank_a_pct']}%`",
        f"  Tanque B (16k L):  {_bar(d['tank_b_pct'])} `{d['tank_b_pct']}%`",
        "",
        "📈 *KPIs*",
        f"  {_status_emoji(kpis['IEH']['status'])} IEH: `{kpis['IEH']['value']}%` (meta >90%)",
        f"  {_status_emoji(kpis['TPP']['status'])} TPP: `{kpis['TPP']['value']}%` (meta <10%)",
        f"  {_status_emoji(kpis['CPE']['status'])} CPE: `{kpis['CPE']['value']} L/est/día` (ref 14.04)",
        "",
    ]

    if critical > 0 or warnings_count > 0:
        lines.append(f"🔔 *Alertas: {critical} críticas · {warnings_count} advertencias*")
        for a in alerts[:3]:
            lines.append(f"  {_level_emoji(a['level'])} [{a['zone']}] {a['message']}")
    else:
        lines.append("✅ Sistema operando sin alertas activas")

    lines += ["", "_/zonas · /kpis · /reporte\\_agua_"]
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
        await msg.edit_text(
            f"✅ *Sistema en operación normal*\n\n"
            f"  Caudal entrada: `{reading['inflow_l_min']} L/min`\n"
            f"  Demanda: `{reading['total_demand_l_min']} L/min`\n"
            f"  Pérdidas: `{reading['losses_l_min']} L/min`\n\n"
            f"_/agua para ver estado completo_",
            parse_mode="Markdown",
        )
    except Exception as e:
        await msg.edit_text(f"❌ Backend no disponible: {e}")

"""
AguaMind OS — Water management router.

Provides simulated sensor readings, KPI calculations, anomaly alerts,
and an autonomous monitor loop for the UNIAJC Sede Sur water system.

Real data from campus research (Arias Montoya et al., 2024):
  - Total daily consumption: ~45,367 L/day
  - Aljibe inflow: ~113.56 L/min (combined)
  - Tank capacities: 36,000 L + 16,000 L
  - Per-student: 14.04 L/student/day (university population)
  - Personal hygiene: 69.73% of total
"""

import math
import random
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# ── Campus constants ────────────────────────────────────────────────────────
DAILY_CONSUMPTION_L = 45_367          # L/day baseline
ALJIBE_INFLOW_L_MIN = 113.56          # L/min total aljibe inflow
TANK_A_CAPACITY_L = 36_000            # primary treatment tank
TANK_B_CAPACITY_L = 16_000            # secondary tank
STUDENT_POPULATION = 3_230            # estimated active users
IRRIGATION_DAILY_PEAK_L = 13_000      # peak irrigation demand

ZONES = ["Baños Bloque A", "Baños Alameda", "Cafetería", "Riego/Cancha", "Laboratorios", "Limpieza"]
ZONE_SHARES = {                        # fraction of total daily consumption
    "Baños Bloque A": 0.2873,
    "Baños Alameda":  0.2400,
    "Cafetería":      0.1200,
    "Riego/Cancha":   0.2500,
    "Laboratorios":   0.0600,
    "Limpieza":       0.0427,
}

# ── Simulation helpers ───────────────────────────────────────────────────────

def _hour_factor(hour: int) -> float:
    """Demand multiplier by hour-of-day (academic schedule peaks 7-12, 14-18)."""
    if 7 <= hour <= 9:
        return 1.6
    if 10 <= hour <= 12:
        return 1.4
    if 13 <= hour <= 14:
        return 0.8
    if 15 <= hour <= 17:
        return 1.3
    if 6 <= hour <= 18:
        return 1.0
    return 0.25


def _simulate_reading(inject_leak: bool = False, inject_peak: bool = False) -> dict:
    hour = datetime.now().hour
    factor = _hour_factor(hour)
    noise = random.uniform(0.92, 1.08)

    inflow = round(ALJIBE_INFLOW_L_MIN * factor * noise, 2)
    total_demand_per_min = round((DAILY_CONSUMPTION_L / 1440) * factor * noise, 2)

    zone_flows: dict[str, float] = {}
    for zone, share in ZONE_SHARES.items():
        z_noise = random.uniform(0.88, 1.12)
        zone_flows[zone] = round((DAILY_CONSUMPTION_L / 1440) * share * factor * z_noise, 2)

    # Tank levels drift realistically (fill when inflow > demand, drain otherwise)
    net = inflow - total_demand_per_min
    tank_a_pct = min(100.0, max(5.0, 65.0 + net * 0.4 + random.uniform(-2, 2)))
    tank_b_pct = min(100.0, max(5.0, 72.0 + net * 0.3 + random.uniform(-2, 2)))

    # Derived losses (unmetered = inflow - sum(measured zones))
    measured_sum = sum(zone_flows.values())
    losses = round(max(0.0, inflow - measured_sum), 2)

    if inject_leak:
        losses = round(losses + random.uniform(8, 15), 2)

    if inject_peak:
        zone_flows["Riego/Cancha"] = round(zone_flows["Riego/Cancha"] * 3.2, 2)
        total_demand_per_min = round(total_demand_per_min * 1.8, 2)

    return {
        "timestamp": datetime.now().isoformat(),
        "inflow_l_min": inflow,
        "total_demand_l_min": total_demand_per_min,
        "losses_l_min": losses,
        "tank_a_pct": round(tank_a_pct, 1),
        "tank_b_pct": round(tank_b_pct, 1),
        "zones": zone_flows,
        "hour": hour,
    }


def _calc_kpis(reading: dict) -> dict:
    """
    KPI 1 – IEH: Índice de Eficiencia Hídrica
      IEH = (Consumo medido / Caudal entrada) × 100
      Target: > 90%

    KPI 2 – TPP: Tasa de Pérdidas del Proceso
      TPP = (Caudal entrada - Suma consumos medidos) / Caudal entrada × 100
      Target: < 10%

    KPI 3 – CPE: Consumo Per Estudiante
      CPE = Consumo total diario / N° estudiantes activos (L/día)
      Reference: 14.04 L/estudiante/día
    """
    inflow = reading["inflow_l_min"]
    demand = reading["total_demand_l_min"]
    losses = reading["losses_l_min"]

    ieh = round(((inflow - losses) / inflow * 100) if inflow > 0 else 0, 2)
    tpp = round((losses / inflow * 100) if inflow > 0 else 0, 2)
    daily_proj = demand * 1440
    cpe = round(daily_proj / STUDENT_POPULATION, 2)

    return {
        "IEH": {"value": ieh, "unit": "%", "target": "> 90%",
                "formula": "(Inflow - Losses) / Inflow × 100",
                "status": "ok" if ieh >= 90 else "warning" if ieh >= 75 else "critical"},
        "TPP": {"value": tpp, "unit": "%", "target": "< 10%",
                "formula": "Losses / Inflow × 100",
                "status": "ok" if tpp <= 10 else "warning" if tpp <= 20 else "critical"},
        "CPE": {"value": cpe, "unit": "L/estudiante/día", "target": "≈ 14.04",
                "formula": "Consumo diario proyectado / Estudiantes activos",
                "status": "ok" if cpe <= 18 else "warning" if cpe <= 25 else "critical"},
    }


def _generate_alerts(reading: dict, kpis: dict) -> list[dict]:
    alerts = []
    if kpis["TPP"]["status"] == "critical":
        alerts.append({
            "level": "critical",
            "zone": "PTAP General",
            "message": f"Pérdidas críticas: {reading['losses_l_min']} L/min ({kpis['TPP']['value']}% del caudal).",
            "action": "Revisar red de distribución — posible fuga mayor.",
        })
    elif kpis["TPP"]["status"] == "warning":
        alerts.append({
            "level": "warning",
            "zone": "PTAP General",
            "message": f"Pérdidas elevadas: {kpis['TPP']['value']}% del caudal de entrada.",
            "action": "Inspección programada recomendada.",
        })

    if reading["tank_a_pct"] < 20:
        alerts.append({
            "level": "warning",
            "zone": "Tanque A",
            "message": f"Nivel bajo en Tanque A: {reading['tank_a_pct']}%.",
            "action": "Verificar válvula de entrada aljibe 1.",
        })
    if reading["tank_b_pct"] < 20:
        alerts.append({
            "level": "warning",
            "zone": "Tanque B",
            "message": f"Nivel bajo en Tanque B: {reading['tank_b_pct']}%.",
            "action": "Verificar válvula de entrada aljibe 2.",
        })

    irrigation = reading["zones"].get("Riego/Cancha", 0)
    expected_irrigation = (DAILY_CONSUMPTION_L / 1440) * ZONE_SHARES["Riego/Cancha"]
    if irrigation > expected_irrigation * 2.5:
        alerts.append({
            "level": "warning",
            "zone": "Riego/Cancha",
            "message": f"Pico de riego: {irrigation:.1f} L/min ({irrigation / expected_irrigation:.1f}× lo normal).",
            "action": "Verificar programación de riego — posible sobreconsumo.",
        })

    if kpis["CPE"]["status"] in ("warning", "critical"):
        alerts.append({
            "level": kpis["CPE"]["status"],
            "zone": "Campus",
            "message": f"Consumo per-cápita elevado: {kpis['CPE']['value']} L/est/día (ref 14.04).",
            "action": "Revisar campañas de concientización y posibles fugas sanitarias.",
        })
    return alerts


def _daily_projection(reading: dict) -> dict:
    l_per_day = reading["total_demand_l_min"] * 1440
    loss_per_day = reading["losses_l_min"] * 1440
    return {
        "projected_consumption_l": round(l_per_day, 0),
        "projected_losses_l": round(loss_per_day, 0),
        "vs_baseline_pct": round((l_per_day - DAILY_CONSUMPTION_L) / DAILY_CONSUMPTION_L * 100, 1),
        "tank_a_hours_remaining": round(
            (reading["tank_a_pct"] / 100 * TANK_A_CAPACITY_L)
            / max(0.1, reading["total_demand_l_min"] - reading["inflow_l_min"]) / 60, 1
        ) if reading["total_demand_l_min"] > reading["inflow_l_min"] else 999,
        "cost_benefit": {
            "current_daily_loss_l": round(loss_per_day, 0),
            "sensor_cost_cop": 4_500_000,
            "annual_water_savings_cop": round(loss_per_day * 365 * 3.5, 0),
            "roi_months": round(4_500_000 / max(1, loss_per_day * 365 * 3.5 / 12), 1),
        },
    }


def _history_series(hours: int = 24) -> list[dict]:
    """Generate realistic hourly history for the last N hours."""
    series = []
    now = datetime.now()
    random.seed(42)
    for i in range(hours, 0, -1):
        ts = now - timedelta(hours=i)
        factor = _hour_factor(ts.hour)
        noise = random.uniform(0.93, 1.07)
        inflow = round(ALJIBE_INFLOW_L_MIN * factor * noise, 2)
        demand = round((DAILY_CONSUMPTION_L / 1440) * factor * noise * 60, 0)
        losses = round(inflow * random.uniform(0.04, 0.12) * 60, 0)
        series.append({
            "hour": ts.strftime("%H:%M"),
            "date": ts.strftime("%Y-%m-%d"),
            "consumption_l": demand,
            "losses_l": losses,
            "inflow_l_min": inflow,
            "tank_a_pct": round(60 + factor * 15 + random.uniform(-5, 5), 1),
            "tank_b_pct": round(65 + factor * 12 + random.uniform(-5, 5), 1),
        })
    random.seed()
    return series


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/reading")
async def current_reading():
    """Real-time simulated sensor reading for all campus zones."""
    reading = _simulate_reading()
    kpis = _calc_kpis(reading)
    alerts = _generate_alerts(reading, kpis)
    return {
        "data": {
            "reading": reading,
            "kpis": kpis,
            "alerts": alerts,
            "projection": _daily_projection(reading),
        },
        "error": None,
    }


@router.get("/history")
async def consumption_history(hours: int = 24):
    """Hourly history series for charts (last N hours, max 168)."""
    hours = min(hours, 168)
    return {"data": _history_series(hours), "error": None}


@router.get("/status")
async def system_status():
    """Quick system-health summary for Telegram /estado command."""
    reading = _simulate_reading()
    kpis = _calc_kpis(reading)
    alerts = _generate_alerts(reading, kpis)
    critical = [a for a in alerts if a["level"] == "critical"]
    warnings = [a for a in alerts if a["level"] == "warning"]
    return {
        "data": {
            "system": "AguaMind OS",
            "campus": "UNIAJC Sede Sur",
            "timestamp": reading["timestamp"],
            "inflow_l_min": reading["inflow_l_min"],
            "total_demand_l_min": reading["total_demand_l_min"],
            "losses_l_min": reading["losses_l_min"],
            "tank_a_pct": reading["tank_a_pct"],
            "tank_b_pct": reading["tank_b_pct"],
            "kpis": {k: {"value": v["value"], "unit": v["unit"], "status": v["status"]}
                     for k, v in kpis.items()},
            "alerts_count": {"critical": len(critical), "warnings": len(warnings)},
            "alerts": alerts[:5],
            "zones": reading["zones"],
        },
        "error": None,
    }


@router.get("/report/daily")
async def daily_report():
    """Full daily report with KPIs, projections, zone breakdown and cost-benefit."""
    reading = _simulate_reading()
    kpis = _calc_kpis(reading)
    alerts = _generate_alerts(reading, kpis)
    projection = _daily_projection(reading)
    history = _history_series(24)

    peak_hour = max(history, key=lambda x: x["consumption_l"])
    total_consumed = sum(h["consumption_l"] for h in history)
    total_losses = sum(h["losses_l"] for h in history)

    return {
        "data": {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "campus": "UNIAJC Sede Sur — Cali",
            "system": "AguaMind OS v1.0",
            "summary": {
                "total_consumed_l": round(total_consumed, 0),
                "total_losses_l": round(total_losses, 0),
                "efficiency_pct": round((total_consumed - total_losses) / max(1, total_consumed) * 100, 1),
                "vs_baseline_pct": projection["vs_baseline_pct"],
                "peak_hour": peak_hour["hour"],
                "peak_consumption_l": peak_hour["consumption_l"],
            },
            "kpis": kpis,
            "zones": reading["zones"],
            "alerts": alerts,
            "projection": projection,
            "recommendations": [
                "Instalar caudalímetros en puntos críticos: entrada PTAP, salida Tanque A, Riego.",
                "Implementar válvulas solenoides programables para riego nocturno fuera de pico.",
                "Difundir indicadores de consumo en pantallas del campus (concientización).",
            ],
        },
        "error": None,
    }


class SimulateRequest(BaseModel):
    scenario: Literal["normal", "leak", "peak_irrigation"] = "normal"


@router.post("/simulate")
async def simulate_scenario(body: SimulateRequest):
    """Inject a specific scenario for demo/testing purposes."""
    reading = _simulate_reading(
        inject_leak=(body.scenario == "leak"),
        inject_peak=(body.scenario == "peak_irrigation"),
    )
    kpis = _calc_kpis(reading)
    alerts = _generate_alerts(reading, kpis)
    return {
        "data": {
            "scenario": body.scenario,
            "reading": reading,
            "kpis": kpis,
            "alerts": alerts,
        },
        "error": None,
    }

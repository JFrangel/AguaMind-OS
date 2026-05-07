"""
AguaMind OS — Water management router.
UNIAJC Sede Sur · Hackathon 2026

Sistema de 6 sensores:
  1. Caudal       — YF-S201 (aljibes 1 y 2)
  2. Presión      — MPX5700AP (red distribución)
  3. Nivel tanque — JSN-SR04T (Tanque A y B)
  4. Acción tuberías — SW-420 vibración (fugas)
  5. Nivel freático  — Transductor 4-20mA (aljibes)
  6. Turbidez     — TSD-10 (post-filtro carbón)

Datos reales: Aristizábal & Largacha (2025), Arias Montoya et al. (2024)
"""

import math
import random
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# ── Constantes del campus (datos exactos del PDF) ───────────────────────────
DAILY_CONSUMPTION_L   = 45_367      # L/día baseline medido
ALJIBE_INFLOW_L_MIN   = 113.56      # L/min combinado (2 aljibes)
TANK_A_CAPACITY_L     = 36_000      # L — tanque principal
TANK_B_CAPACITY_L     = 16_000      # L — tanque secundario
PUMP_ACTIVATION_L     = 24_000      # bomba ON cuando Tanque A < este valor (66.7%)
PUMP_MAX_L_H          = 7_268       # capacidad máxima bomba (L/h = 121.1 L/min)
AQUIFER_INITIAL_L     = 5_000_000   # acuífero inicial (modelo Vensim)
STUDENT_POPULATION    = 3_230       # estudiantes activos/día
TOTAL_USERS           = 8_234       # usuarios totales (+ docentes y staff)
HYDRAULIC_DEVICES     = 219         # dispositivos hidráulicos inventariados
CAMPUS_AREA_M2        = 38_755.88   # área del campus

# ── Equipos PTAP UNIAJC (códigos oficiales · Gómez Mina 2022) ──────────────
PTAP_EQUIPMENT = {
    "CP-BS-01": {"name": "Bomba sumergible aljibe 1",  "marca": "Barnes 4SP 2526", "hp": 5.0, "lpm": 121.1, "v": 220},
    "CP-BS-02": {"name": "Bomba sumergible aljibe 2",  "marca": "Barnes 4SP 2511", "hp": 2.0, "lpm": 121.1, "v": 220},
    "SF-FT-01": {"name": "Filtro 1 (grava + arena)",   "marca": "OHS Ingenieros", "vol_l": 861.53, "lpm": 400},
    "SF-FT-02": {"name": "Filtro 2 (+ antracita)",     "marca": "OHS Ingenieros", "vol_l": 861.53, "lpm": 400},
    "SF-FT-03": {"name": "Filtro 3 (+ carbón)",        "marca": "OHS Ingenieros", "vol_l": 861.53, "lpm": 400},
    "SD-TM-01": {"name": "Tanque cloración",           "marca": "Ajover Wave",   "vol_l": 250},
    "SD-BD-01": {"name": "Bomba dosificadora cloro",   "marca": "LMI C111-362TI","v": 120, "psi": 150, "gph": 2.5, "w": 44},
    "AL-TA-01": {"name": "Tanque almacenamiento A",    "vol_l": 36_000},
    "AL-TA-02": {"name": "Tanque almacenamiento B",    "vol_l": 16_000},
    "SB-TH-01": {"name": "Hidroneumático 1",           "marca": "Altamira PRO XLB", "vol_gal": 119, "psi_max": 125},
    "SB-TH-02": {"name": "Hidroneumático 2",           "marca": "Altamira PRO XLB", "vol_gal": 119, "psi_max": 125},
    "SB-BC-03": {"name": "Bomba centrífuga 1",         "marca": "Barmesa Pumps"},
    "SB-BC-04": {"name": "Bomba centrífuga 2",         "marca": "Barmesa Pumps"},
}

# ── Cumplimiento normativo (parámetros límite) ────────────────────────────
NORMATIVE_LIMITS = {
    "turbidez_max_ntu":         2.0,    # Resolución 2115/2007 (potable)
    "ph_min":                   6.5,
    "ph_max":                   9.0,
    "cloro_residual_min_ppm":   0.3,    # Decreto 1575/2007
    "cloro_residual_max_ppm":   2.0,
    "cloro_dosificacion_ppm":   3.0,    # objetivo PTAP UNIAJC
    "irca_max":                 5.0,    # 0-5 sin riesgo (Res 2115)
    "ptar_dbo5_max_mg_l":       90.0,   # Resolución 0631/2015
    "ptar_sst_max_mg_l":        90.0,
    "ptar_grasas_max_mg_l":     20.0,
    "ptar_ph_min":              6.0,
    "ptar_ph_max":              9.0,
    "retrolavado_min_year":     2,      # RAS 2000 cap. C.17
    "retrolavado_actual_year":  24,     # actual UNIAJC (excede norma)
    "lavado_tanques_min_year":  2,      # Decreto 1575/2007 art. 9
}

# ── Zonas de consumo (L/día exactos — Arias Montoya et al., 2024) ──────────
ZONE_DAILY_BASE = {
    "Aseo Personal":     31_700,    # 69.73% — 7,045 usos × 4.5 L
    "Riego/Cancha":       4_000,    # 3×/semana 94L/min × 45min ÷ 7
    "Lavado de Manos":    2_550,    # promedio 2,300–2,800 L
    "Limpieza Pasillos":  1_000,    # promedio 800–1,200 L
    "Limpieza Baños":       750,    # promedio 600–900 L
    "Limpieza Aulas":     1_250,    # promedio 1,000–1,500 L
    "Cafetería":            240,    # medido directamente
    "Laboratorios":          64,    # 450 L/semana ÷ 7 días
}
# Suma zonas = 41,554 + ~3,813 sin catalogar = 45,367 L/día total ✓

ZONE_SHARES = {k: v / DAILY_CONSUMPTION_L for k, v in ZONE_DAILY_BASE.items()}

# ── Umbrales de alerta por sensor ──────────────────────────────────────────
THRESHOLDS = {
    "flow_min_lmin":      50.0,    # caudal mínimo normal (L/min)
    "tank_a_critical":    33.3,    # % nivel crítico Tanque A (= 12,000 L)
    "tank_a_pump_on":     66.7,    # % activación bomba (= 24,000 L)
    "pressure_max_kpa":  500.0,    # presión máxima red (kPa)
    "pressure_min_kpa":  100.0,    # presión mínima (kPa)
    "turbidity_max_ntu":   4.0,    # turbidez máxima post-filtro (NTU)
    "turbidity_warn_ntu":  2.0,    # turbidez advertencia
    "phreatic_min_m":      2.0,    # nivel freático mínimo (m)
    "phreatic_warn_m":     4.0,    # nivel freático advertencia (m)
    "tpp_critical":       20.0,    # TPP crítica (%)
    "tpp_warning":        10.0,    # TPP advertencia (%)
    "ieh_ok":             90.0,    # IEH objetivo (%)
    "ieh_warning":        75.0,    # IEH mínimo aceptable (%)
    "cpe_reference":      14.04,   # CPE referencia (L/est/día)
}


# ── Helpers de simulación ───────────────────────────────────────────────────

def _hour_factor(hour: int) -> float:
    """Multiplicador de demanda por hora (horario académico UNIAJC)."""
    if 7 <= hour <= 9:   return 1.6   # entrada masiva estudiantes
    if 10 <= hour <= 12: return 1.4   # clases mañana
    if 13 <= hour <= 14: return 0.8   # almuerzo
    if 15 <= hour <= 17: return 1.3   # clases tarde
    if 6 <= hour <= 18:  return 1.0   # horario normal
    return 0.25                        # noche/madrugada


def _simulate_sensors(
    inject_leak: bool = False,
    inject_peak_irrigation: bool = False,
    inject_turbidity: bool = False,
) -> dict:
    """Simula lectura de los 6 sensores con datos realistas."""
    hour   = datetime.now().hour
    factor = _hour_factor(hour)
    noise  = random.uniform(0.93, 1.07)

    # ── Sensor 1: Caudal (YF-S201 × 2) ──
    flow1_lmin = round(ALJIBE_INFLOW_L_MIN * 0.52 * factor * noise, 2)  # Aljibe 1
    flow2_lmin = round(ALJIBE_INFLOW_L_MIN * 0.48 * factor * noise, 2)  # Aljibe 2
    total_flow = flow1_lmin + flow2_lmin

    # ── Sensor 3: Nivel tanques (JSN-SR04T) ──
    net = total_flow - (DAILY_CONSUMPTION_L / 1440) * factor
    tank_a_pct = min(100.0, max(5.0, 65.0 + net * 0.4 + random.uniform(-2, 2)))
    tank_b_pct = min(100.0, max(5.0, 72.0 + net * 0.3 + random.uniform(-2, 2)))
    pump_active = tank_a_pct < THRESHOLDS["tank_a_pump_on"]

    # ── Sensor 2: Presión red (MPX5700AP) ──
    # Presión normal 200-400 kPa, sube cuando bomba activa
    pressure_base = 280 + (80 if pump_active else 0)
    pressure_kpa  = round(pressure_base * factor * random.uniform(0.95, 1.05), 1)

    # ── Sensor 5: Nivel freático (transductor 4-20mA) ──
    # Nivel normal 6-10m, baja en pico de demanda
    phreatic_m = round(8.0 - factor * 0.8 + random.uniform(-0.3, 0.3), 2)

    # ── Sensor 6: Turbidez (TSD-10) ──
    turbidity_ntu = round(0.8 + random.uniform(0.0, 0.6), 2)

    # ── Sensor 4: Vibración tuberías (SW-420) ──
    vibration = False  # Normal: sin vibración anómala

    # ── Consumo por zona ──
    zone_flows: dict[str, float] = {}
    for zone, share in ZONE_SHARES.items():
        z_noise = random.uniform(0.88, 1.12)
        zone_flows[zone] = round((DAILY_CONSUMPTION_L / 1440) * share * factor * z_noise, 2)

    demand_l_min = round((DAILY_CONSUMPTION_L / 1440) * factor * noise, 2)
    measured_sum = sum(zone_flows.values())
    losses_l_min = round(max(0.0, total_flow - measured_sum), 2)

    # ── Inyección de escenarios demo ──
    if inject_leak:
        losses_l_min += round(random.uniform(10, 20), 2)
        vibration = True
        pressure_kpa = round(pressure_kpa * 0.75, 1)  # caída de presión por fuga

    if inject_peak_irrigation:
        zone_flows["Riego/Cancha"] = round(zone_flows["Riego/Cancha"] * 3.5, 2)
        demand_l_min = round(demand_l_min * 1.9, 2)
        phreatic_m   = round(phreatic_m - 1.2, 2)  # baja nivel acuífero

    if inject_turbidity:
        turbidity_ntu = round(random.uniform(5.0, 8.0), 2)

    return {
        "timestamp":      datetime.now().isoformat(),
        "hour":           hour,
        "pump_active":    pump_active,
        # Sensor 1 — Caudal
        "flow1_lmin":     flow1_lmin,
        "flow2_lmin":     flow2_lmin,
        "total_flow_lmin": total_flow,
        # Sensor 2 — Presión
        "pressure_kpa":   pressure_kpa,
        # Sensor 3 — Nivel tanques
        "tank_a_pct":     round(tank_a_pct, 1),
        "tank_b_pct":     round(tank_b_pct, 1),
        "tank_a_l":       round(tank_a_pct / 100 * TANK_A_CAPACITY_L),
        "tank_b_l":       round(tank_b_pct / 100 * TANK_B_CAPACITY_L),
        # Sensor 4 — Vibración tuberías
        "vibration":      vibration,
        # Sensor 5 — Nivel freático
        "phreatic_m":     phreatic_m,
        # Sensor 6 — Turbidez
        "turbidity_ntu":  turbidity_ntu,
        # Derivados
        "demand_l_min":   demand_l_min,
        "losses_l_min":   losses_l_min,
        "zones":          zone_flows,
    }


def _calc_kpis(r: dict) -> dict:
    """
    KPI 1 — IEH: Índice de Eficiencia Hídrica
      IEH = (Q_medido / Q_bombeado) × 100  →  meta > 90%

    KPI 2 — TPP: Tasa de Pérdidas del Proceso
      TPP = (Pérdidas / Q_entrada) × 100   →  meta < 10%

    KPI 3 — CPE: Consumo Per Estudiante
      CPE = Consumo_diario / Estudiantes   →  ref 14.04 L/est/día
    """
    flow_in = r["total_flow_lmin"]
    losses  = r["losses_l_min"]

    ieh = round(((flow_in - losses) / flow_in * 100) if flow_in > 0 else 0, 2)
    tpp = round((losses / flow_in * 100) if flow_in > 0 else 0, 2)
    cpe = round(r["demand_l_min"] * 1440 / STUDENT_POPULATION, 2)

    # KPI extra — ICA (calidad agua por turbidez)
    ica = round(max(0, 100 - (r["turbidity_ntu"] / THRESHOLDS["turbidity_max_ntu"]) * 30), 1)

    return {
        "IEH": {
            "value":   ieh,
            "unit":    "%",
            "target":  "> 90%",
            "formula": "((Q_entrada − Pérdidas) / Q_entrada) × 100",
            "status":  "ok" if ieh >= 90 else "warning" if ieh >= 75 else "critical",
        },
        "TPP": {
            "value":   tpp,
            "unit":    "%",
            "target":  "< 10%",
            "formula": "Pérdidas / Q_entrada × 100",
            "status":  "ok" if tpp <= 10 else "warning" if tpp <= 20 else "critical",
        },
        "CPE": {
            "value":   cpe,
            "unit":    "L/est/día",
            "target":  f"≤ {THRESHOLDS['cpe_reference']}",
            "formula": "Consumo_diario_proyectado / Estudiantes_activos",
            "status":  "ok" if cpe <= THRESHOLDS["cpe_reference"] else "warning" if cpe <= 18 else "critical",
        },
        "ICA": {
            "value":   ica,
            "unit":    "puntos",
            "target":  "> 90 pts",
            "formula": "100 − (Turbidez_NTU / 4) × 30",
            "status":  "ok" if ica >= 90 else "warning" if ica >= 70 else "critical",
        },
    }


def _generate_alerts(r: dict, kpis: dict) -> list[dict]:
    alerts = []

    # Alerta caudal bajo (Sensor 1)
    if r["total_flow_lmin"] < THRESHOLDS["flow_min_lmin"]:
        alerts.append({
            "level":   "critical",
            "sensor":  "Caudal (YF-S201)",
            "zone":    "Aljibes",
            "message": f"Caudal total bajo: {r['total_flow_lmin']:.1f} L/min (mín {THRESHOLDS['flow_min_lmin']} L/min).",
            "action":  "Verificar nivel del acuífero y estado de las bombas de aljibe.",
        })

    # Alerta presión (Sensor 2)
    if r["pressure_kpa"] > THRESHOLDS["pressure_max_kpa"]:
        alerts.append({
            "level":   "warning",
            "sensor":  "Presión (MPX5700AP)",
            "zone":    "Red Distribución",
            "message": f"Sobrepresión: {r['pressure_kpa']:.0f} kPa (máx {THRESHOLDS['pressure_max_kpa']:.0f} kPa).",
            "action":  "Revisar válvulas reguladoras de presión.",
        })
    elif r["pressure_kpa"] < THRESHOLDS["pressure_min_kpa"]:
        alerts.append({
            "level":   "warning",
            "sensor":  "Presión (MPX5700AP)",
            "zone":    "Red Distribución",
            "message": f"Presión baja: {r['pressure_kpa']:.0f} kPa — posible fuga o rotura.",
            "action":  "Inspección urgente de la red de distribución.",
        })

    # Alerta nivel tanques (Sensor 3)
    if r["tank_a_pct"] < THRESHOLDS["tank_a_critical"]:
        alerts.append({
            "level":   "critical",
            "sensor":  "Nivel Tanque A (JSN-SR04T)",
            "zone":    "Tanque A",
            "message": f"Nivel crítico Tanque A: {r['tank_a_pct']:.1f}% ({r['tank_a_l']:,.0f} L).",
            "action":  "Activar bombeo adicional de emergencia. Restricción de consumo no esencial.",
        })
    elif r["tank_a_pct"] < THRESHOLDS["tank_a_pump_on"]:
        alerts.append({
            "level":   "info",
            "sensor":  "Nivel Tanque A (JSN-SR04T)",
            "zone":    "Tanque A",
            "message": f"Bomba activada — Tanque A al {r['tank_a_pct']:.1f}% ({r['tank_a_l']:,.0f} L).",
            "action":  "Monitoreo continuo. Normal si demanda es alta.",
        })

    # Alerta vibración / fuga tubería (Sensor 4)
    if r["vibration"]:
        alerts.append({
            "level":   "critical",
            "sensor":  "Vibración (SW-420)",
            "zone":    "Red Distribución",
            "message": "Vibración anómala detectada en tuberías — posible fuga o rotura.",
            "action":  "Inspección física inmediata del tramo afectado. Cerrar válvula de sección.",
        })

    # Alerta nivel freático (Sensor 5)
    if r["phreatic_m"] < THRESHOLDS["phreatic_min_m"]:
        alerts.append({
            "level":   "critical",
            "sensor":  "Nivel Freático (4-20mA)",
            "zone":    "Aljibes",
            "message": f"Nivel freático crítico: {r['phreatic_m']:.1f} m (mín {THRESHOLDS['phreatic_min_m']} m).",
            "action":  "Reducir extracción inmediatamente. Riesgo de daño a la bomba de pozo.",
        })
    elif r["phreatic_m"] < THRESHOLDS["phreatic_warn_m"]:
        alerts.append({
            "level":   "warning",
            "sensor":  "Nivel Freático (4-20mA)",
            "zone":    "Aljibes",
            "message": f"Nivel freático bajo: {r['phreatic_m']:.1f} m — tendencia decreciente.",
            "action":  "Monitorear recarga del acuífero. Considerar reducción de extracción.",
        })

    # Alerta turbidez / calidad agua (Sensor 6)
    if r["turbidity_ntu"] > THRESHOLDS["turbidity_max_ntu"]:
        alerts.append({
            "level":   "critical",
            "sensor":  "Turbidez (TSD-10)",
            "zone":    "PTAP Filtros",
            "message": f"Turbidez fuera de norma: {r['turbidity_ntu']:.1f} NTU (máx {THRESHOLDS['turbidity_max_ntu']} NTU).",
            "action":  "Suspender distribución. Revisar filtros de arena y carbón activado.",
        })
    elif r["turbidity_ntu"] > THRESHOLDS["turbidity_warn_ntu"]:
        alerts.append({
            "level":   "warning",
            "sensor":  "Turbidez (TSD-10)",
            "zone":    "PTAP Filtros",
            "message": f"Turbidez elevada: {r['turbidity_ntu']:.1f} NTU — mantenimiento de filtros pronto.",
            "action":  "Programar limpieza de filtros en < 48h.",
        })

    # Alertas KPI
    if kpis["TPP"]["status"] == "critical":
        alerts.append({
            "level":   "critical",
            "sensor":  "KPI Sistema",
            "zone":    "PTAP General",
            "message": f"TPP crítica: {kpis['TPP']['value']}% de pérdidas (meta < 10%).",
            "action":  "Activar protocolo de detección de fugas. Revisar todos los sectores.",
        })

    # Alerta pico de riego
    expected_irr = (DAILY_CONSUMPTION_L / 1440) * ZONE_SHARES["Riego/Cancha"]
    if r["zones"].get("Riego/Cancha", 0) > expected_irr * 2.8:
        alerts.append({
            "level":   "warning",
            "sensor":  "Flujo Zona",
            "zone":    "Riego/Cancha",
            "message": f"Pico de riego: {r['zones']['Riego/Cancha']:.1f} L/min ({r['zones']['Riego/Cancha']/expected_irr:.1f}× lo normal).",
            "action":  "Verificar programación del sistema de riego. Considerar riego nocturno.",
        })

    return alerts


def _calc_cost_benefit(r: dict) -> dict:
    daily_loss_l   = r["losses_l_min"] * 1440
    water_cost_cop = 3.5                           # COP/L (EMCALI tarifa industrial)
    daily_loss_cop = round(daily_loss_l * water_cost_cop, 0)
    annual_loss_cop = round(daily_loss_cop * 365, 0)

    # Inversión AguaMind OS (hardware + instalación)
    investment_cop = 1_043_000

    # Ahorro proyectado si TPP baja a 10%
    current_tpp = r["losses_l_min"] / max(r["total_flow_lmin"], 1) * 100
    target_tpp  = 10.0
    if current_tpp > target_tpp:
        recoverable_pct = (current_tpp - target_tpp) / current_tpp
        daily_saving_l   = daily_loss_l * recoverable_pct
        daily_saving_cop = round(daily_saving_l * water_cost_cop, 0)
        annual_saving_cop = round(daily_saving_cop * 365, 0)
        roi_months = round(investment_cop / max(annual_saving_cop / 12, 1), 1)
    else:
        daily_saving_cop  = 0
        annual_saving_cop = 0
        roi_months        = 0

    return {
        "daily_loss_l":      round(daily_loss_l, 0),
        "daily_loss_cop":    daily_loss_cop,
        "annual_loss_cop":   annual_loss_cop,
        "investment_cop":    investment_cop,
        "daily_saving_cop":  daily_saving_cop,
        "annual_saving_cop": annual_saving_cop,
        "roi_months":        roi_months,
        "water_cost_l_cop":  water_cost_cop,
        "ods": ["ODS 6 — Agua limpia", "ODS 9 — Industria e innovación",
                "ODS 11 — Ciudades sostenibles", "ODS 13 — Acción climática"],
    }


def _daily_projection(r: dict) -> dict:
    l_per_day   = r["demand_l_min"] * 1440
    loss_per_day = r["losses_l_min"] * 1440
    tank_a_remain = r["tank_a_l"]
    net_drain = max(0.0, r["demand_l_min"] - r["total_flow_lmin"])
    hours_remaining = round(tank_a_remain / max(net_drain * 60, 0.1), 1) if net_drain > 0 else 999

    return {
        "projected_consumption_l": round(l_per_day, 0),
        "projected_losses_l":      round(loss_per_day, 0),
        "vs_baseline_pct":         round((l_per_day - DAILY_CONSUMPTION_L) / DAILY_CONSUMPTION_L * 100, 1),
        "tank_a_hours_remaining":  hours_remaining,
        "aquifer_days_remaining":  round(AQUIFER_INITIAL_L / max(l_per_day + loss_per_day, 1), 1),
    }


def _history_series(hours: int = 24) -> list[dict]:
    """Serie histórica horaria realista para gráficas."""
    series = []
    now = datetime.now()
    random.seed(42)
    for i in range(hours, 0, -1):
        ts     = now - timedelta(hours=i)
        factor = _hour_factor(ts.hour)
        noise  = random.uniform(0.93, 1.07)
        flow   = round(ALJIBE_INFLOW_L_MIN * factor * noise, 2)
        demand = round((DAILY_CONSUMPTION_L / 1440) * factor * noise * 60, 0)
        losses = round(flow * random.uniform(0.05, 0.15) * 60, 0)
        turb   = round(0.6 + random.uniform(0.0, 1.2), 2)
        series.append({
            "hour":           ts.strftime("%H:%M"),
            "date":           ts.strftime("%Y-%m-%d"),
            "consumption_l":  demand,
            "losses_l":       losses,
            "inflow_lmin":    flow,
            "tank_a_pct":     round(60 + factor * 15 + random.uniform(-5, 5), 1),
            "tank_b_pct":     round(65 + factor * 12 + random.uniform(-5, 5), 1),
            "turbidity_ntu":  turb,
            "pressure_kpa":   round(280 + factor * 40 + random.uniform(-20, 20), 0),
            "phreatic_m":     round(8.0 - factor * 0.6 + random.uniform(-0.2, 0.2), 2),
        })
    random.seed()
    return series


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/reading")
async def current_reading():
    """Lectura en tiempo real de los 6 sensores del campus."""
    r       = _simulate_sensors()
    kpis    = _calc_kpis(r)
    alerts  = _generate_alerts(r, kpis)
    return {
        "data": {
            "reading":    r,
            "kpis":       kpis,
            "alerts":     alerts,
            "projection": _daily_projection(r),
        },
        "error": None,
    }


@router.get("/status")
async def system_status():
    """Resumen del sistema para Telegram /estado."""
    r      = _simulate_sensors()
    kpis   = _calc_kpis(r)
    alerts = _generate_alerts(r, kpis)
    return {
        "data": {
            "system":    "AguaMind OS",
            "campus":    "UNIAJC Sede Sur",
            "timestamp": r["timestamp"],
            # Sensor 1
            "flow1_lmin":      r["flow1_lmin"],
            "flow2_lmin":      r["flow2_lmin"],
            "total_flow_lmin": r["total_flow_lmin"],
            # Sensor 2
            "pressure_kpa":    r["pressure_kpa"],
            # Sensor 3
            "tank_a_pct":      r["tank_a_pct"],
            "tank_b_pct":      r["tank_b_pct"],
            "pump_active":     r["pump_active"],
            # Sensor 4
            "vibration":       r["vibration"],
            # Sensor 5
            "phreatic_m":      r["phreatic_m"],
            # Sensor 6
            "turbidity_ntu":   r["turbidity_ntu"],
            # KPIs resumidos
            "kpis": {k: {"value": v["value"], "unit": v["unit"], "status": v["status"]}
                     for k, v in kpis.items()},
            "alerts_count": {
                "critical": len([a for a in alerts if a["level"] == "critical"]),
                "warning":  len([a for a in alerts if a["level"] == "warning"]),
                "info":     len([a for a in alerts if a["level"] == "info"]),
            },
            "alerts": alerts[:5],
            "zones":  r["zones"],
        },
        "error": None,
    }


@router.get("/history")
async def consumption_history(hours: int = 24):
    """Historial horario para gráficas (máx 168h = 7 días)."""
    hours = min(hours, 168)
    return {"data": _history_series(hours), "error": None}


@router.get("/report/daily")
async def daily_report():
    """Reporte diario completo con KPIs, proyecciones y análisis costo-beneficio."""
    r         = _simulate_sensors()
    kpis      = _calc_kpis(r)
    alerts    = _generate_alerts(r, kpis)
    projection = _daily_projection(r)
    cb        = _calc_cost_benefit(r)
    history   = _history_series(24)

    peak_hour  = max(history, key=lambda x: x["consumption_l"])
    total_consumed = sum(h["consumption_l"] for h in history)
    total_losses   = sum(h["losses_l"] for h in history)

    return {
        "data": {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "campus":      "UNIAJC Sede Sur — Cali",
            "system":      "AguaMind OS v2.0",
            "population":  {"students": STUDENT_POPULATION, "total_users": TOTAL_USERS},
            "summary": {
                "total_consumed_l":  round(total_consumed, 0),
                "total_losses_l":    round(total_losses, 0),
                "efficiency_pct":    round((total_consumed - total_losses) / max(1, total_consumed) * 100, 1),
                "vs_baseline_pct":   projection["vs_baseline_pct"],
                "peak_hour":         peak_hour["hour"],
                "peak_consumption_l": peak_hour["consumption_l"],
            },
            "sensors": {
                "flow_lmin":      r["total_flow_lmin"],
                "pressure_kpa":   r["pressure_kpa"],
                "tank_a_pct":     r["tank_a_pct"],
                "tank_b_pct":     r["tank_b_pct"],
                "vibration":      r["vibration"],
                "phreatic_m":     r["phreatic_m"],
                "turbidity_ntu":  r["turbidity_ntu"],
            },
            "kpis":              kpis,
            "zones":             r["zones"],
            "alerts":            alerts,
            "projection":        projection,
            "cost_benefit":      cb,
            "recommendations": [
                "Instalar caudalímetros permanentes en puntos críticos: entrada PTAP, salida Tanque A, riego.",
                "Automatizar riego con válvulas solenoides (horario nocturno 22:00-05:00).",
                "Difundir KPIs en pantallas del campus para concientización.",
                f"Reparar fugas detectadas — ahorro potencial: ${cb['annual_saving_cop']:,.0f} COP/año.",
            ],
        },
        "error": None,
    }


@router.get("/thresholds")
async def get_thresholds():
    """Retorna los umbrales configurados por sensor."""
    return {"data": THRESHOLDS, "error": None}


@router.get("/equipment")
async def get_equipment():
    """Inventario de equipos PTAP con códigos UNIAJC oficiales (Gómez Mina 2022)."""
    return {"data": {"equipment": PTAP_EQUIPMENT, "total_units": len(PTAP_EQUIPMENT)}, "error": None}


@router.get("/compliance")
async def get_compliance():
    """Estado de cumplimiento normativo en tiempo real."""
    r = _simulate_sensors()
    kpis = _calc_kpis(r)
    items = [
        {
            "norma":      "Resolución 2115/2007",
            "parametro":  "Turbidez (potable)",
            "limite":     f"≤ {NORMATIVE_LIMITS['turbidez_max_ntu']} NTU",
            "actual":     f"{r['turbidity_ntu']:.1f} NTU",
            "estado":     "OK" if r["turbidity_ntu"] <= NORMATIVE_LIMITS["turbidez_max_ntu"] else "INCUMPLE",
            "autoridad":  "Min. Salud / INVIMA",
            "sancion_max_smmlv": 1000,
        },
        {
            "norma":      "Decreto 1076/2015",
            "parametro":  "Nivel freático monitoreado",
            "limite":     "Reporte trimestral CVC",
            "actual":     f"{r['phreatic_m']:.1f} m",
            "estado":     "OK" if r["phreatic_m"] >= 4.0 else "ALERTA",
            "autoridad":  "CVC",
            "sancion_max_smmlv": 5000,
        },
        {
            "norma":      "Decreto 3930/2010",
            "parametro":  "Eficiencia hídrica (TPP)",
            "limite":     "TPP < 25% recomendado",
            "actual":     f"TPP {kpis['TPP']['value']:.1f}%",
            "estado":     "OK" if kpis["TPP"]["value"] <= 15 else "ALERTA",
            "autoridad":  "Min. Ambiente / CVC",
            "sancion_max_smmlv": 1000,
        },
        {
            "norma":      "RAS 2000 Cap. C.17",
            "parametro":  "Retrolavado de filtros",
            "limite":     f"≥ {NORMATIVE_LIMITS['retrolavado_min_year']} veces/año",
            "actual":     f"{NORMATIVE_LIMITS['retrolavado_actual_year']} veces/año",
            "estado":     "EXCEDE BIEN",
            "autoridad":  "Min. Vivienda",
            "sancion_max_smmlv": 0,
        },
        {
            "norma":      "Decreto 1575/2007 art. 9",
            "parametro":  "Lavado tanques",
            "limite":     f"≥ {NORMATIVE_LIMITS['lavado_tanques_min_year']} veces/año",
            "actual":     "2 veces/año (validado)",
            "estado":     "OK",
            "autoridad":  "Min. Salud",
            "sancion_max_smmlv": 500,
        },
        {
            "norma":      "Resolución 0631/2015",
            "parametro":  "Vertimiento PTAR (DBO5)",
            "limite":     f"≤ {NORMATIVE_LIMITS['ptar_dbo5_max_mg_l']} mg/L",
            "actual":     "Pendiente sensorización (Fase 3)",
            "estado":     "PENDIENTE",
            "autoridad":  "CVC / Min. Ambiente",
            "sancion_max_smmlv": 5000,
        },
        {
            "norma":      "Ley 1581/2012",
            "parametro":  "Protección datos personales",
            "limite":     "Tratamiento responsable",
            "actual":     "Solo chat_id Telegram con consentimiento",
            "estado":     "OK",
            "autoridad":  "SIC",
            "sancion_max_smmlv": 2000,
        },
        {
            "norma":      "Ley 1712/2014 (Transparencia)",
            "parametro":  "Datos abiertos",
            "limite":     "Publicación obligatoria",
            "actual":     "Dashboard público + API REST",
            "estado":     "OK",
            "autoridad":  "Procuraduría",
            "sancion_max_smmlv": 100,
        },
    ]
    in_compliance = sum(1 for i in items if i["estado"] in ("OK", "EXCEDE BIEN"))
    return {
        "data": {
            "items":         items,
            "score":         f"{in_compliance}/{len(items)}",
            "score_pct":     round(in_compliance / len(items) * 100, 1),
            "exposure_smmlv": sum(i["sancion_max_smmlv"] for i in items if i["estado"] not in ("OK", "EXCEDE BIEN")),
            "exposure_cop":  sum(i["sancion_max_smmlv"] for i in items if i["estado"] not in ("OK", "EXCEDE BIEN")) * 1_300_000,
        },
        "error": None,
    }


@router.get("/constants")
async def get_constants():
    """Retorna las constantes del campus (datos reales del PDF)."""
    return {
        "data": {
            "daily_consumption_l":  DAILY_CONSUMPTION_L,
            "aljibe_inflow_l_min":  ALJIBE_INFLOW_L_MIN,
            "tank_a_capacity_l":    TANK_A_CAPACITY_L,
            "tank_b_capacity_l":    TANK_B_CAPACITY_L,
            "pump_activation_l":    PUMP_ACTIVATION_L,
            "pump_max_l_h":         PUMP_MAX_L_H,
            "aquifer_initial_l":    AQUIFER_INITIAL_L,
            "student_population":   STUDENT_POPULATION,
            "total_users":          TOTAL_USERS,
            "hydraulic_devices":    HYDRAULIC_DEVICES,
            "campus_area_m2":       CAMPUS_AREA_M2,
            "zone_daily_base":      ZONE_DAILY_BASE,
            "references": [
                "Aristizábal Torres & Largacha Perdomo (2025). Dinámica de sistemas UNIAJC.",
                "Arias Montoya et al. (2024). Diseño sistema de ahorro PTAP UNIAJC.",
                "Mosquera Zapata & Lozano Beltrán (2024). Modelo PTAR impacto ecosistema.",
            ],
        },
        "error": None,
    }


class SimulateRequest(BaseModel):
    scenario: Literal["normal", "leak", "peak_irrigation", "turbidity"] = "normal"


@router.post("/simulate")
async def simulate_scenario(body: SimulateRequest):
    """Inyecta un escenario específico para demo (fuga, pico riego, turbidez)."""
    r = _simulate_sensors(
        inject_leak              = (body.scenario == "leak"),
        inject_peak_irrigation   = (body.scenario == "peak_irrigation"),
        inject_turbidity         = (body.scenario == "turbidity"),
    )
    kpis   = _calc_kpis(r)
    alerts = _generate_alerts(r, kpis)
    return {
        "data": {
            "scenario": body.scenario,
            "reading":  r,
            "kpis":     kpis,
            "alerts":   alerts,
        },
        "error": None,
    }


class IngestRequest(BaseModel):
    """Payload que envía el ESP32 vía MQTT/HTTP cada 30s."""
    flow1_lmin:    float
    flow2_lmin:    float
    level_a_pct:   float
    level_b_pct:   float
    pressure_kpa:  float
    phreatic_m:    float
    turbidity_ntu: float
    vibration:     bool
    node_id:       str = "esp32-ptap-01"


@router.post("/ingest")
async def ingest_sensor_data(body: IngestRequest):
    """
    Recibe datos reales del nodo ESP32 AguaMind Node v1.
    Calcula KPIs y genera alertas en tiempo real.
    """
    r = {
        "timestamp":       datetime.now().isoformat(),
        "hour":            datetime.now().hour,
        "pump_active":     body.level_a_pct < THRESHOLDS["tank_a_pump_on"],
        "flow1_lmin":      body.flow1_lmin,
        "flow2_lmin":      body.flow2_lmin,
        "total_flow_lmin": round(body.flow1_lmin + body.flow2_lmin, 2),
        "pressure_kpa":    body.pressure_kpa,
        "tank_a_pct":      body.level_a_pct,
        "tank_b_pct":      body.level_b_pct,
        "tank_a_l":        round(body.level_a_pct / 100 * TANK_A_CAPACITY_L),
        "tank_b_l":        round(body.level_b_pct / 100 * TANK_B_CAPACITY_L),
        "vibration":       body.vibration,
        "phreatic_m":      body.phreatic_m,
        "turbidity_ntu":   body.turbidity_ntu,
        "demand_l_min":    round((body.flow1_lmin + body.flow2_lmin) * 0.88, 2),
        "losses_l_min":    round((body.flow1_lmin + body.flow2_lmin) * 0.12, 2),
        "zones":           {},
        "node_id":         body.node_id,
        "source":          "esp32_real",
    }
    kpis   = _calc_kpis(r)
    alerts = _generate_alerts(r, kpis)
    cb     = _calc_cost_benefit(r)
    return {
        "data": {
            "ingested":    True,
            "node_id":     body.node_id,
            "reading":     r,
            "kpis":        kpis,
            "alerts":      alerts,
            "cost_benefit": cb,
        },
        "error": None,
    }

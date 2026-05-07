"""
AguaMind OS — Endpoints de Mitigación Activa.

El sistema no solo monitorea, ACTÚA. Este módulo expone los endpoints
que controlan electroválvulas, bombas y acciones comunitarias.

POST /water/mitigate/valve/close       → cierra electroválvula
POST /water/mitigate/valve/open        → abre electroválvula
POST /water/mitigate/pump/standby      → pone bomba en standby
POST /water/mitigate/pressure/reduce   → reduce presión nocturna
POST /water/mitigate/auto              → ejecuta mitigación recomendada por IA
GET  /water/mitigate/history           → historial de acciones
GET  /water/mitigate/valves            → estado de todas las válvulas
GET  /water/mitigate/impact            → impacto acumulado evitado

POST /water/report-issue               → reporte ciudadano (QR)
GET  /water/leaderboard                → ranking de edificios

Documentación: docs/es/MITIGACION-Y-ESTRATEGIA.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# ── Estado en memoria (en producción: Supabase) ─────────────────────────────
_VALVES: dict[str, dict] = {
    "EV-A1":   {"name": "Bloque A · entrada principal", "state": "open",  "controllable": True},
    "EV-A2":   {"name": "Bloque A · baños 2do piso",     "state": "open",  "controllable": True},
    "EV-AL1":  {"name": "Alameda · entrada",             "state": "open",  "controllable": True},
    "EV-RC1":  {"name": "Riego/Cancha · solenoide",      "state": "open",  "controllable": True},
    "EV-CAF1": {"name": "Cafetería · entrada",           "state": "open",  "controllable": True},
    "EV-LAB1": {"name": "Laboratorios · entrada",        "state": "open",  "controllable": True},
    "EV-OUT-A":{"name": "Salida Tanque A",               "state": "open",  "controllable": True},
    "EV-OUT-B":{"name": "Salida Tanque B",               "state": "open",  "controllable": True},
}

_PUMP = {"state": "auto", "pressure_pct": 100, "last_change": None}

_HISTORY: list[dict] = []

# Ranking simulado (en prod: lectura real desde nodos por edificio)
_BUILDINGS = [
    {"id": "alameda",   "name": "Edificio Alameda",     "credits": 320, "consumption_l_day": 14_500, "rank": 1},
    {"id": "bloque-a",  "name": "Bloque A",             "credits": 285, "consumption_l_day": 18_200, "rank": 2},
    {"id": "cafeteria", "name": "Cafetería + Plazoleta", "credits": 180, "consumption_l_day": 240,    "rank": 3},
    {"id": "labs",      "name": "Laboratorios",          "credits": 145, "consumption_l_day": 64,     "rank": 4},
    {"id": "cancha",    "name": "Cancha + Jardines",    "credits": 95,  "consumption_l_day": 4_000,  "rank": 5},
]

_REPORTS: list[dict] = []

# Acumulado de impacto (litros y dinero ahorrados por mitigación)
_IMPACT = {"liters_saved": 0, "cop_saved": 0, "co2_kg_avoided": 0.0, "actions_taken": 0}

# ── Modelos Pydantic ─────────────────────────────────────────────────────────

class ValveAction(BaseModel):
    valve_id: str = Field(..., description="ID de la electroválvula (ej. EV-A2)")
    reason:   str = Field("manual_override", description="Razón de la acción")


class PressureReduction(BaseModel):
    zone:       str = Field(..., description="Zona objetivo: 'baños' | 'riego' | 'global'")
    target_pct: int = Field(50, ge=0, le=100, description="Presión objetivo 0-100%")
    duration_h: int = Field(8,  ge=1, le=24,  description="Horas de duración")


class AutoMitigation(BaseModel):
    trigger: Literal["leak", "peak_irrigation", "turbidity", "tank_overflow", "phreatic_low"]
    severity: Literal["warning", "critical"] = "critical"


class IssueReport(BaseModel):
    location:   str = Field(..., description="Bloque/zona reportada (ej. 'bloque-a-baño-2')")
    description: str = Field(..., max_length=500)
    user_id:    str = Field("anonymous", description="Telegram chat_id o anónimo")
    photo_url:  Optional[str] = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _record(action: dict) -> dict:
    action["id"] = str(uuid4())[:8]
    action["timestamp"] = datetime.now().isoformat()
    _HISTORY.append(action)
    return action


def _telegram_format(action: dict) -> str:
    icon = {"close": "🛡️", "open": "🔓", "standby": "⏸", "reduce": "📉",
            "auto": "🤖"}.get(action.get("type", ""), "•")
    return (
        f"{icon} *AguaMind OS — Mitigación ejecutada*\n"
        f"Tipo: `{action['type']}`\n"
        f"Detalle: {action.get('detail', '—')}\n"
        f"Hora: `{action['timestamp'][:19]}`\n"
        f"Razón: _{action.get('reason', '—')}_"
    )


# ── Endpoints: control de electroválvulas ───────────────────────────────────

@router.post("/mitigate/valve/close")
async def close_valve(body: ValveAction):
    """Cierra una electroválvula (corte de flujo)."""
    if body.valve_id not in _VALVES:
        raise HTTPException(404, f"Válvula {body.valve_id} no encontrada")
    valve = _VALVES[body.valve_id]
    if not valve["controllable"]:
        raise HTTPException(403, "Válvula no controlable remotamente")

    valve["state"] = "closed"
    valve["last_change"] = datetime.now().isoformat()

    action = _record({
        "type":    "close",
        "valve":   body.valve_id,
        "valve_name": valve["name"],
        "detail":  f"Electroválvula {body.valve_id} cerrada · {valve['name']}",
        "reason":  body.reason,
        "telegram_msg": None,
    })
    action["telegram_msg"] = _telegram_format(action)

    _IMPACT["actions_taken"] += 1
    return {"data": {"executed": True, "action": action, "valve": valve}, "error": None}


@router.post("/mitigate/valve/open")
async def open_valve(body: ValveAction):
    if body.valve_id not in _VALVES:
        raise HTTPException(404, f"Válvula {body.valve_id} no encontrada")
    valve = _VALVES[body.valve_id]
    valve["state"] = "open"
    valve["last_change"] = datetime.now().isoformat()

    action = _record({
        "type":   "open",
        "valve":  body.valve_id,
        "detail": f"Electroválvula {body.valve_id} abierta · {valve['name']}",
        "reason": body.reason,
    })
    action["telegram_msg"] = _telegram_format(action)
    return {"data": {"executed": True, "action": action, "valve": valve}, "error": None}


@router.post("/mitigate/pump/standby")
async def pump_standby():
    _PUMP["state"] = "standby"
    _PUMP["pressure_pct"] = 0
    _PUMP["last_change"] = datetime.now().isoformat()
    action = _record({
        "type":   "standby",
        "detail": "Bomba principal en standby",
        "reason": "manual_override",
    })
    action["telegram_msg"] = _telegram_format(action)
    return {"data": {"executed": True, "action": action, "pump": _PUMP}, "error": None}


@router.post("/mitigate/pump/auto")
async def pump_auto():
    _PUMP["state"] = "auto"
    _PUMP["pressure_pct"] = 100
    _PUMP["last_change"] = datetime.now().isoformat()
    return {"data": {"executed": True, "pump": _PUMP}, "error": None}


@router.post("/mitigate/pressure/reduce")
async def reduce_pressure(body: PressureReduction):
    """Reduce presión vía VFD durante N horas (típicamente nocturno)."""
    _PUMP["state"] = "reduced"
    _PUMP["pressure_pct"] = body.target_pct
    _PUMP["last_change"] = datetime.now().isoformat()

    action = _record({
        "type":   "reduce",
        "zone":   body.zone,
        "detail": f"Presión zona {body.zone} reducida a {body.target_pct}% durante {body.duration_h}h",
        "reason": "scheduled_night_savings" if body.zone == "baños" else "manual",
    })
    action["telegram_msg"] = _telegram_format(action)
    return {"data": {"executed": True, "action": action, "pump": _PUMP}, "error": None}


# ── Endpoint: mitigación automática (la inteligente) ────────────────────────

@router.post("/mitigate/auto")
async def auto_mitigate(body: AutoMitigation):
    """
    Mitigación automática orquestada por el agente IA.
    Selecciona la acción correcta según el trigger y ejecuta cascada.
    """
    actions_taken = []

    if body.trigger == "leak":
        # Cierra válvula del sector afectado + bomba standby
        for vid in ("EV-A2",):
            v = _VALVES[vid]
            v["state"] = "closed"
            actions_taken.append({"type": "close", "valve": vid, "name": v["name"]})
        _PUMP["state"] = "standby"; _PUMP["pressure_pct"] = 0
        impact_l = 14_500
        action_summary = "Cerrada EV-A2 + bomba en standby"

    elif body.trigger == "peak_irrigation":
        v = _VALVES["EV-RC1"]; v["state"] = "closed"
        actions_taken.append({"type": "close", "valve": "EV-RC1", "name": v["name"]})
        impact_l = 1_800
        action_summary = "Cerrado solenoide riego — reprogramado para 22:00"

    elif body.trigger == "turbidity":
        for vid in ("EV-OUT-A", "EV-OUT-B"):
            v = _VALVES[vid]; v["state"] = "closed"
            actions_taken.append({"type": "close", "valve": vid, "name": v["name"]})
        impact_l = 0  # protección sanitaria, no ahorro
        action_summary = "Cerradas salidas tanques — protocolo calidad activado"

    elif body.trigger == "tank_overflow":
        _PUMP["state"] = "standby"; _PUMP["pressure_pct"] = 0
        impact_l = 6_500
        action_summary = "Bomba apagada antes de desborde"

    elif body.trigger == "phreatic_low":
        _PUMP["state"] = "reduced"; _PUMP["pressure_pct"] = 30
        impact_l = 3_200
        action_summary = "Reducida extracción 70% para preservar acuífero"

    else:
        raise HTTPException(400, f"Trigger no reconocido: {body.trigger}")

    # Calcular impacto evitado
    cop_saved = round(impact_l * 3.5)
    co2_kg = round(impact_l * 0.00046, 3)  # bombeo por litro

    action = _record({
        "type":     "auto",
        "trigger":  body.trigger,
        "severity": body.severity,
        "detail":   action_summary,
        "actions":  actions_taken,
        "impact":   {"liters_saved": impact_l, "cop_saved": cop_saved, "co2_kg_avoided": co2_kg},
        "reason":   f"agente_ia_{body.severity}",
    })
    action["telegram_msg"] = (
        f"🛡️ *AguaMind OS — Mitigación automática ejecutada*\n"
        f"Trigger: `{body.trigger}` ({body.severity})\n"
        f"Acción: {action_summary}\n\n"
        f"Impacto evitado:\n"
        f"  💧 `{impact_l:,}` L\n"
        f"  💰 `${cop_saved:,}` COP\n"
        f"  🌱 `{co2_kg}` kg CO₂\n\n"
        f"_Orden de trabajo OT-{action['id']} generada automáticamente_"
    )

    _IMPACT["liters_saved"] += impact_l
    _IMPACT["cop_saved"] += cop_saved
    _IMPACT["co2_kg_avoided"] += co2_kg
    _IMPACT["actions_taken"] += 1

    return {"data": action, "error": None}


# ── Endpoints de consulta ────────────────────────────────────────────────────

@router.get("/mitigate/valves")
async def list_valves():
    """Estado actual de todas las electroválvulas."""
    return {"data": {"valves": _VALVES, "pump": _PUMP}, "error": None}


@router.get("/mitigate/history")
async def history(limit: int = 20):
    """Historial de acciones de mitigación (últimas N)."""
    return {"data": {"actions": _HISTORY[-limit:][::-1], "total": len(_HISTORY)}, "error": None}


@router.get("/mitigate/impact")
async def impact_summary():
    """Impacto acumulado evitado por las acciones del agente."""
    return {
        "data": {
            **_IMPACT,
            "liters_saved_formatted": f"{_IMPACT['liters_saved']:,} L",
            "cop_saved_formatted":    f"${_IMPACT['cop_saved']:,} COP",
            "co2_kg_formatted":       f"{_IMPACT['co2_kg_avoided']:.2f} kg CO₂",
            "equivalent_pools":       round(_IMPACT["liters_saved"] / 2_500_000, 3),
        },
        "error": None,
    }


# ── Reporte ciudadano (QR) ───────────────────────────────────────────────────

@router.post("/report-issue")
async def report_issue(body: IssueReport):
    """
    Reporte de fuga/mal uso reportado por la comunidad vía QR/Telegram.
    El agente IA valida con datos de sensores y otorga puntos al usuario.
    """
    report = {
        "id":          str(uuid4())[:8],
        "location":    body.location,
        "description": body.description,
        "user_id":     body.user_id,
        "photo_url":   body.photo_url,
        "timestamp":   datetime.now().isoformat(),
        "status":      "pending_validation",
        "ai_validation": None,
        "points_awarded": 0,
    }

    # Simulación: el SensorAgent valida si hay datos anómalos en esa zona
    # En prod: cruzar con caudal de la zona, presión, hidrófono
    is_valid = "baño" in body.location.lower() or "fuga" in body.description.lower()

    if is_valid:
        report["status"] = "validated"
        report["ai_validation"] = "Anomalía confirmada por SensorAgent — caudal anómalo detectado"
        report["points_awarded"] = 20
    else:
        report["status"] = "thanks"
        report["ai_validation"] = "No se detectó anomalía pero gracias por colaborar"
        report["points_awarded"] = 5

    _REPORTS.append(report)
    return {"data": report, "error": None}


@router.get("/reports")
async def list_reports(limit: int = 20):
    return {"data": {"reports": _REPORTS[-limit:][::-1], "total": len(_REPORTS)}, "error": None}


# ── Gamificación: leaderboard de edificios ──────────────────────────────────

@router.get("/leaderboard")
async def leaderboard():
    """Ranking de edificios por créditos hídricos acumulados."""
    sorted_b = sorted(_BUILDINGS, key=lambda x: -x["credits"])
    for i, b in enumerate(sorted_b, 1):
        b["rank"] = i
    return {
        "data": {
            "buildings": sorted_b,
            "rules": {
                "credit_definition": "1 Crédito Hídrico = 1 m³ ahorrado vs línea base",
                "rewards": {
                    "100": "$350,000 COP — mejora zona común",
                    "500": "$1,750,000 COP — renovación cafetería",
                    "1000": "$3,500,000 COP — proyecto propuesto por estudiantes",
                },
            },
            "winner_this_month": sorted_b[0],
        },
        "error": None,
    }

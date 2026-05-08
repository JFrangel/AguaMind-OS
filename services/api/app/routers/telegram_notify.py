"""
HidroTech - Servicio de notificaciones a Telegram.

Permite que el dashboard dispare alertas al operador on-call cuando ocurren
eventos clave: arranque del agente, plan ante fenómenos, mitigación crítica.

Las alertas pueden incluir botones inline (callback_data) para que el operador
las apruebe/active desde el chat sin abrir el dashboard.

Configuración requerida (variables de entorno):
    TELEGRAM_BOT_TOKEN    - obtenido de @BotFather
    TELEGRAM_CHAT_ID      - chat_id del operador (run get_chat_id.py una vez)

Si no están configurados, las llamadas devuelven {sent: false, reason: "no_token"}
para que el dashboard pueda mostrar fallback (ej: "Telegram desactivado").
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import urllib.request
import urllib.parse
import json as _json

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────────

_PLACEHOLDER = {
    "", "your-token", "changeme",
    "REEMPLAZAR_CON_TOKEN_DE_BOTFATHER",
    "REEMPLAZAR_CON_TU_CHAT_ID",
}


def _find_secrets_file() -> Optional[Path]:
    """Busca bot_secrets.json subiendo desde este archivo hasta encontrar el repo root."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "bot_secrets.json"
        if candidate.is_file():
            return candidate
    return None


_SECRETS_CACHE: Optional[dict] = None


def _load_secrets() -> dict:
    global _SECRETS_CACHE
    if _SECRETS_CACHE is not None:
        return _SECRETS_CACHE
    path = _find_secrets_file()
    if not path:
        _SECRETS_CACHE = {}
        return _SECRETS_CACHE
    try:
        with path.open("r", encoding="utf-8") as f:
            _SECRETS_CACHE = _json.load(f)
    except Exception:
        _SECRETS_CACHE = {}
    return _SECRETS_CACHE


def _real(env: str) -> Optional[str]:
    """Resuelve credenciales: 1) bot_secrets.json (raíz repo), 2) variables de entorno."""
    # 1) Archivo bot_secrets.json (gitignored, persistente entre PCs si lo copias)
    secrets = _load_secrets()
    v = str(secrets.get(env, "")).strip()
    if v and v not in _PLACEHOLDER and not v.endswith("..."):
        return v
    # 2) Variables de entorno (.env / shell)
    v = (os.getenv(env) or "").strip()
    if not v or v in _PLACEHOLDER or v.endswith("..."):
        return None
    return v


def _send_telegram(text: str, *, parse_mode: str = "Markdown",
                   inline_buttons: Optional[list[list[dict]]] = None,
                   chat_id: Optional[str] = None) -> dict:
    """Envía un mensaje al chat configurado. Devuelve estado de envío."""
    token = _real("TELEGRAM_BOT_TOKEN")
    target = chat_id or _real("TELEGRAM_CHAT_ID")
    if not token or not target:
        return {
            "sent": False,
            "reason": "no_token" if not token else "no_chat_id",
            "preview": text[:280],
            "hint": "Configurar TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env",
        }

    payload: dict = {
        "chat_id": target,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    if inline_buttons:
        payload["reply_markup"] = _json.dumps({"inline_keyboard": inline_buttons})

    data = urllib.parse.urlencode(payload).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = _json.loads(resp.read().decode("utf-8"))
            return {"sent": body.get("ok", False), "message_id": body.get("result", {}).get("message_id")}
    except Exception as e:
        return {"sent": False, "reason": str(e)[:120], "preview": text[:280]}


# ── Endpoints — uno por evento del dashboard ─────────────────────────────────

class NotifyAgentStarted(BaseModel):
    cycle: int = Field(..., description="Número de ciclo del agente")
    decision: str = Field(default="ok", description="Última decisión del agente")
    issues: list[str] = Field(default_factory=list, description="Problemas detectados")


@router.post("/notify/agent_cycle")
async def notify_agent_cycle(body: NotifyAgentStarted):
    """Envía notificación cuando el dashboard ejecuta un ciclo único del agente."""
    decision_emoji = {"ok": "✅", "warning": "⚠️", "critical": "🚨"}.get(body.decision, "🔵")
    issues_text = ""
    if body.issues:
        issues_text = "\n\n*Hallazgos:*\n" + "\n".join(f"• {i}" for i in body.issues[:5])

    text = (
        f"{decision_emoji} *HidroTech — Agente IA*\n"
        f"Ciclo `#{body.cycle}` ejecutado · decisión `{body.decision}`"
        f"{issues_text}\n\n"
        f"_dashboard.uniajc.edu.co/agua_"
    )
    buttons = [[
        {"text": "📊 Ver dashboard", "callback_data": "open_dashboard"},
        {"text": "🔄 Otro ciclo",   "callback_data": "agent_cycle"},
    ]]
    return {"data": _send_telegram(text, inline_buttons=buttons), "error": None}


class NotifyPhenomenon(BaseModel):
    phenomenon: Literal["drought_mode", "flood_mode", "quake_mode",
                        "contamination_mode", "surge_mode"] = Field(...)
    severity: Literal["info", "warning", "critical"] = "warning"
    forecast_days: int = Field(30, description="Días de anticipación del pronóstico")
    suggestion: str = Field("", description="Sugerencia textual del agente")


_PHEN_LABEL = {
    "drought_mode":       ("🌵", "Sequía / fenómeno El Niño"),
    "flood_mode":         ("🌧️", "Lluvias intensas / La Niña"),
    "quake_mode":         ("🌐", "Sismo"),
    "contamination_mode": ("☣️", "Contaminación química"),
    "surge_mode":         ("📈", "Pico de demanda"),
}


@router.post("/notify/phenomenon")
async def notify_phenomenon(body: NotifyPhenomenon):
    """Envía alerta de fenómeno con sugerencia del agente + botón inline para activar."""
    emoji, label = _PHEN_LABEL.get(body.phenomenon, ("⚠️", body.phenomenon))
    sev_emoji = {"info": "🔵", "warning": "🟡", "critical": "🔴"}[body.severity]

    text = (
        f"{emoji} *HidroTech — Alerta de fenómeno*\n"
        f"{sev_emoji} *{label}*\n"
        f"Pronóstico: en `{body.forecast_days}` días\n\n"
    )
    if body.suggestion:
        text += f"*Sugerencia del agente:*\n_{body.suggestion}_\n\n"
    text += "Confirmá para que el sistema active el plan de mitigación automáticamente."

    buttons = [[
        {"text": "✅ Activar plan",   "callback_data": f"activate:{body.phenomenon}"},
        {"text": "❌ Ignorar",        "callback_data": "dismiss"},
    ], [
        {"text": "📊 Ver evidencia",  "callback_data": f"evidence:{body.phenomenon}"},
    ]]
    return {"data": _send_telegram(text, inline_buttons=buttons), "error": None}


class NotifyMitigation(BaseModel):
    trigger: str
    impact_l: int = 0
    cop_saved: int = 0
    summary: str = ""
    ot_id: str = ""


@router.post("/notify/mitigation_executed")
async def notify_mitigation(body: NotifyMitigation):
    """Confirmación tras ejecutar una acción de mitigación."""
    text = (
        f"✅ *HidroTech — Mitigación ejecutada*\n"
        f"Trigger: `{body.trigger}`\n"
        f"OT: `{body.ot_id or '—'}`\n\n"
        f"*Acción:*\n_{body.summary}_\n\n"
        f"*Impacto evitado:*\n"
        f"💧 `{body.impact_l:,}` L\n"
        f"💰 `${body.cop_saved:,}` COP\n"
    )
    return {"data": _send_telegram(text), "error": None}


# ── Webhook callback — recibe respuestas del operador desde Telegram ────────

class CallbackBody(BaseModel):
    callback_data: str = Field(..., description="Data del inline button presionado")
    operator_chat_id: Optional[str] = None


@router.post("/notify/callback")
async def callback_dispatcher(body: CallbackBody):
    """Procesa la respuesta del operador a un inline button.

    El bot de Telegram (apps/telegram/bot.py) intercepta los callbacks
    de inline buttons y los reenvía a este endpoint para que el backend
    ejecute la acción correspondiente. Cierra el círculo: dashboard →
    Telegram → operador → backend → dashboard.
    """
    cb = body.callback_data

    if cb.startswith("activate:"):
        trigger = cb.split(":", 1)[1]
        try:
            from app.routers.mitigation import auto_mitigate, AutoMitigation
            res = await auto_mitigate(AutoMitigation(trigger=trigger, severity="critical"))
            return {"data": {"ok": True, "action": "mitigation", "result": res}, "error": None}
        except Exception as e:
            return {"data": {"ok": False, "action": "mitigation", "reason": str(e)[:200]}, "error": None}

    if cb == "agent_cycle":
        return {"data": {"ok": True, "action": "agent_cycle_requested"}, "error": None}

    if cb.startswith("evidence:"):
        return {"data": {"ok": True, "action": "evidence", "phenomenon": cb.split(":")[1]}, "error": None}

    if cb == "dismiss":
        return {"data": {"ok": True, "action": "dismissed"}, "error": None}

    if cb == "open_dashboard":
        return {"data": {"ok": True, "action": "open_dashboard", "url": "/agua"}, "error": None}

    return {"data": {"ok": False, "reason": f"callback_no_reconocido: {cb}"}, "error": None}


@router.get("/notify/test")
async def notify_test():
    """Endpoint de prueba — envía un mensaje al chat configurado."""
    text = (
        "🔔 *HidroTech — Prueba de conexión*\n"
        f"Hora: `{datetime.now().strftime('%H:%M:%S')}`\n"
        "Si recibís este mensaje, las notificaciones están operativas."
    )
    return {"data": _send_telegram(text), "error": None}

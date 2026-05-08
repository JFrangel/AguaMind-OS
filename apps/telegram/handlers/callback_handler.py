"""
Callback query handler — procesa clicks en inline buttons enviados desde el dashboard.

Cuando el dashboard envía una alerta con botones (ej. "Activar plan" / "Ignorar"),
el operador presiona uno y este handler lo intercepta, lo reenvía al backend
para que ejecute la acción, y responde al chat con el resultado.

Cierra el círculo: dashboard → Telegram → operador → backend → Telegram (confirma).
"""
from __future__ import annotations

import os
import urllib.request
import urllib.parse
import json as _json

from telegram import Update
from telegram.ext import ContextTypes


BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")


def _post_json(path: str, body: dict) -> dict:
    data = _json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BACKEND}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return _json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"data": None, "error": str(e)[:120]}


_PHEN_LABEL = {
    "drought_mode":       "Modo SEQUÍA",
    "flood_mode":         "Modo LLUVIAS",
    "quake_mode":         "Modo SISMO",
    "contamination_mode": "Modo CONTAMINACIÓN",
    "surge_mode":         "Modo PICO DEMANDA",
}


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Procesa cualquier callback_query (click en inline button)."""
    query = update.callback_query
    if not query or not query.data:
        return

    cb = query.data

    # Respuesta visual inmediata para el operador (Telegram exige answerCallbackQuery)
    await query.answer()

    # ── Activar plan de mitigación ──────────────────────────────────────────
    if cb.startswith("activate:"):
        trigger = cb.split(":", 1)[1]
        label = _PHEN_LABEL.get(trigger, trigger)

        # Confirmar en el chat antes de ejecutar
        await query.edit_message_text(
            f"⏳ *Ejecutando {label}...*\nEspera unos segundos.",
            parse_mode="Markdown",
        )

        # Llamar al endpoint de mitigación del backend
        resp = _post_json("/water/mitigate/auto", {
            "trigger": trigger,
            "severity": "critical",
        })
        d = resp.get("data") or {}

        if d:
            impact = d.get("impact", {})
            await query.edit_message_text(
                f"✅ *{label} ACTIVADO*\n\n"
                f"_{d.get('detail', 'Plan ejecutado')}_\n\n"
                f"💧 Impacto: `{impact.get('liters_saved', 0):,}` L\n"
                f"💰 Ahorro: `${impact.get('cop_saved', 0):,}` COP\n"
                f"🌱 CO₂ evitado: `{impact.get('co2_kg_avoided', 0)}` kg\n\n"
                f"OT: `{d.get('id', '—')}`",
                parse_mode="Markdown",
            )
        else:
            await query.edit_message_text(
                f"❌ *Error activando {label}*\n{resp.get('error') or 'backend no respondió'}",
                parse_mode="Markdown",
            )
        return

    # ── Ignorar la alerta ───────────────────────────────────────────────────
    if cb == "dismiss":
        await query.edit_message_text(
            f"❌ *Alerta ignorada*\nEl plan no fue activado. Decisión registrada en logs.",
            parse_mode="Markdown",
        )
        return

    # ── Ver evidencia (link al dashboard) ───────────────────────────────────
    if cb.startswith("evidence:"):
        phen = cb.split(":", 1)[1]
        await query.message.reply_text(
            f"📊 *Evidencia · {_PHEN_LABEL.get(phen, phen)}*\n"
            f"Abrí el dashboard en `/agua` → tab Inteligencia → Plan ante fenómenos.\n"
            f"Vas a ver: pronóstico IDEAM, nivel freático actual, sugerencia del agente con su confianza, monetización en vivo.",
            parse_mode="Markdown",
        )
        return

    # ── Ejecutar otro ciclo del agente ──────────────────────────────────────
    if cb == "agent_cycle":
        resp = _post_json("/water/agent/cycle", {})
        d = resp.get("data") or {}
        await query.message.reply_text(
            f"🔄 *Nuevo ciclo del agente*\n"
            f"Decisión: `{d.get('decision', '—')}`\n"
            f"Issues: `{len(d.get('issues', []))}`",
            parse_mode="Markdown",
        )
        return

    # ── Abrir dashboard ─────────────────────────────────────────────────────
    if cb == "open_dashboard":
        await query.message.reply_text(
            "📊 Abrí el dashboard en `/agua` desde tu navegador.",
            parse_mode="Markdown",
        )
        return

    # ── Callback no reconocido ──────────────────────────────────────────────
    await query.message.reply_text(f"⚠️ Callback no reconocido: `{cb}`", parse_mode="Markdown")

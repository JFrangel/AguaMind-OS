import json as _json
import os
from pathlib import Path

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from handlers.callback_handler import callback_handler
from handlers.commands import ask, report, research, start, status


def _load_secrets() -> dict:
    """Lee bot_secrets.json subiendo desde este archivo hasta el repo root."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "bot_secrets.json"
        if candidate.is_file():
            try:
                with candidate.open("r", encoding="utf-8") as f:
                    return _json.load(f)
            except Exception:
                return {}
    return {}


def _resolve(key: str) -> str | None:
    """Prioridad: bot_secrets.json > variable de entorno."""
    placeholders = {"", "REEMPLAZAR_CON_TOKEN_DE_BOTFATHER", "REEMPLAZAR_CON_TU_CHAT_ID", "changeme"}
    secrets = _load_secrets()
    v = str(secrets.get(key, "")).strip()
    if v and v not in placeholders:
        return v
    v = (os.getenv(key) or "").strip()
    return v if v and v not in placeholders else None
from handlers.water_commands import (
    agente_start,
    agente_status,
    agente_stop,
    agua_status,
    demo_alerta,
    demo_normal,
    demo_riego,
    kpis,
    mitigaciones,
    mitigar,
    ranking,
    reportar,
    reporte_agua,
    sensores,
    zonas,
)


def main() -> None:
    token = _resolve("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN no configurado. Editá bot_secrets.json en la raíz del proyecto "
            "con el token de @BotFather."
        )

    app = ApplicationBuilder().token(token).build()

    # ── AgentOS core commands ──────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("research", research))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("status", status))

    # ── Camaleón OS — water management commands ────────────────────────────
    app.add_handler(CommandHandler("agua", agua_status))
    app.add_handler(CommandHandler("estado", agua_status))
    app.add_handler(CommandHandler("zonas", zonas))
    app.add_handler(CommandHandler("kpis", kpis))
    app.add_handler(CommandHandler("sensores", sensores))
    app.add_handler(CommandHandler("reporte_agua", reporte_agua))
    app.add_handler(CommandHandler("alerta", demo_alerta))
    app.add_handler(CommandHandler("riego", demo_riego))
    app.add_handler(CommandHandler("normal", demo_normal))

    # ── Camaleón OS — agente IA autónomo ───────────────────────────────────
    app.add_handler(CommandHandler("agente_start", agente_start))
    app.add_handler(CommandHandler("agente_stop", agente_stop))
    app.add_handler(CommandHandler("agente_status", agente_status))

    # ── Camaleón OS — mitigación + gamificación ────────────────────────────
    app.add_handler(CommandHandler("mitigar", mitigar))
    app.add_handler(CommandHandler("mitigaciones", mitigaciones))
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(CommandHandler("reportar", reportar))

    # ── Inline buttons (Activar plan / Ignorar / Ver evidencia) ─────────────
    app.add_handler(CallbackQueryHandler(callback_handler))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask))

    app.run_polling()


if __name__ == "__main__":
    main()

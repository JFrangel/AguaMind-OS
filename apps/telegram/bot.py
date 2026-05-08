import os

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from handlers.callback_handler import callback_handler
from handlers.commands import ask, report, research, start, status
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
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

    app = ApplicationBuilder().token(token).build()

    # ── AgentOS core commands ──────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("research", research))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("status", status))

    # ── WaterMind OS — water management commands ────────────────────────────
    app.add_handler(CommandHandler("agua", agua_status))
    app.add_handler(CommandHandler("estado", agua_status))
    app.add_handler(CommandHandler("zonas", zonas))
    app.add_handler(CommandHandler("kpis", kpis))
    app.add_handler(CommandHandler("sensores", sensores))
    app.add_handler(CommandHandler("reporte_agua", reporte_agua))
    app.add_handler(CommandHandler("alerta", demo_alerta))
    app.add_handler(CommandHandler("riego", demo_riego))
    app.add_handler(CommandHandler("normal", demo_normal))

    # ── WaterMind OS — agente IA autónomo ───────────────────────────────────
    app.add_handler(CommandHandler("agente_start", agente_start))
    app.add_handler(CommandHandler("agente_stop", agente_stop))
    app.add_handler(CommandHandler("agente_status", agente_status))

    # ── WaterMind OS — mitigación + gamificación ────────────────────────────
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

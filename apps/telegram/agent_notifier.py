"""
AguaMind OS — Notificador push del agente IA hacia Telegram.

Usado por el WaterMonitorAgent para enviar alertas críticas
automáticamente al chat configurado en TELEGRAM_CHAT_ID.

Sin polling — solo envío directo vía API HTTP de Telegram.
"""

import json
import os
import logging
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger("aguamind.notifier")

TELEGRAM_API = "https://api.telegram.org"


def send_message(text: str, chat_id: str | None = None, token: str | None = None,
                 parse_mode: str = "Markdown") -> bool:
    """
    Envía un mensaje a Telegram. Lee TOKEN/CHAT_ID del entorno si no se pasan.
    Retorna True si la API devuelve ok=True.
    """
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.warning("Telegram TOKEN/CHAT_ID no configurados — skip envío")
        return False

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id":    chat_id,
        "text":       text[:4096],   # límite Telegram
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }).encode("utf-8")

    req = Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        if data.get("ok"):
            return True
        logger.warning(f"Telegram API: {data}")
        return False
    except HTTPError as e:
        logger.error(f"Telegram HTTP {e.code}: {e.reason}")
        return False
    except (URLError, TimeoutError) as e:
        logger.error(f"Telegram conexión: {e}")
        return False
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False


def format_alert(reading: dict, kpis: dict, alerts: list[dict], decision: str) -> str:
    """Formato Markdown de alerta consolidada del agente."""
    icon = {"critical": "🚨", "warning": "⚠️", "alert": "⚠️"}.get(decision, "✅")
    ts = datetime.now().strftime("%H:%M")

    critical = [a for a in alerts if a.get("level") == "critical"]
    warnings = [a for a in alerts if a.get("level") == "warning"]

    lines = [
        f"{icon} *AguaMind OS — UNIAJC Sede Sur*",
        f"Estado: *{decision.upper()}* · {ts}",
        "",
        f"💧 Caudal: `{reading.get('total_flow_lmin', 0):.1f}` L/min",
        f"🪣 Tanque A: `{reading.get('tank_a_pct', 0):.1f}%`  ·  B: `{reading.get('tank_b_pct', 0):.1f}%`",
        f"📊 IEH: `{kpis.get('IEH', {}).get('value', '?')}%`  ·  TPP: `{kpis.get('TPP', {}).get('value', '?')}%`",
        f"🔬 Turbidez: `{reading.get('turbidity_ntu', 0):.1f}` NTU  ·  Freático: `{reading.get('phreatic_m', 0):.1f}` m",
    ]

    if reading.get("vibration"):
        lines.append("⚡ *Vibración detectada en tuberías*")

    if critical:
        lines += ["", "🚨 *Alertas críticas:*"]
        for a in critical[:3]:
            lines.append(f"  • {a.get('zone', '—')}: {a.get('message', '')}")
    if warnings:
        lines += ["", "⚠️ *Advertencias:*"]
        for a in warnings[:2]:
            lines.append(f"  • {a.get('zone', '—')}: {a.get('message', '')}")

    return "\n".join(lines)


def format_daily_report(report: dict) -> str:
    """Formato del reporte diario para envío Telegram."""
    s = report.get("summary", {})
    k = report.get("kpis", {})
    cb = report.get("cost_benefit", {})

    lines = [
        "📊 *AguaMind OS — Reporte Diario*",
        f"_{report.get('report_date', '')}_  ·  {report.get('campus', '')}",
        "",
        f"✓ Consumo total: `{s.get('total_consumed_l', 0):,}` L",
        f"⚠ Pérdidas: `{s.get('total_losses_l', 0):,}` L",
        f"📈 Eficiencia: `{s.get('efficiency_pct', 0):.1f}%`",
        f"⏱ Hora pico: `{s.get('peak_hour', '—')}` (`{s.get('peak_consumption_l', 0):,}` L)",
        "",
        "*KPIs del día:*",
        f"  IEH: `{k.get('IEH', {}).get('value', '?')}%` ({k.get('IEH', {}).get('status', '—')})",
        f"  TPP: `{k.get('TPP', {}).get('value', '?')}%` ({k.get('TPP', {}).get('status', '—')})",
        f"  CPE: `{k.get('CPE', {}).get('value', '?')}` L/est ({k.get('CPE', {}).get('status', '—')})",
        "",
        "*Costo-beneficio:*",
        f"  Pérdida diaria: `${cb.get('daily_loss_cop', 0):,}` COP",
        f"  Ahorro proyectado anual: `${cb.get('annual_saving_cop', 0):,}` COP",
        f"  ROI estimado: `{cb.get('roi_months', 0)}` meses",
    ]
    return "\n".join(lines)


def notify_critical(reading: dict, kpis: dict, alerts: list[dict]) -> bool:
    return send_message(format_alert(reading, kpis, alerts, "critical"))


def notify_warning(reading: dict, kpis: dict, alerts: list[dict]) -> bool:
    return send_message(format_alert(reading, kpis, alerts, "warning"))


def notify_daily_report(report: dict) -> bool:
    return send_message(format_daily_report(report))


# ── Test directo ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    msg = (
        "🔔 *Test AguaMind OS*\n\n"
        "Si recibes este mensaje, el bot está configurado correctamente.\n"
        f"Hora: {datetime.now().strftime('%H:%M:%S')}\n"
        f"Bot listo para recibir alertas del agente IA."
    )
    if send_message(msg):
        print("✓ Mensaje enviado correctamente")
    else:
        print("✗ Falla al enviar — verifica TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID")

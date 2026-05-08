import io
import json
import os

import httpx
from telegram import Update
from telegram.ext import ContextTypes

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "💧 HidroTech — UNIAJC Sede Sur\n"
        "Sistema inteligente de gestión hídrica\n\n"
        "── Agua ──\n"
        "/agua · /estado — estado del sistema en tiempo real\n"
        "/zonas — consumo por zona del campus\n"
        "/kpis — indicadores de desempeño (IEH · TPP · CPE)\n"
        "/reporte_agua — reporte diario completo\n\n"
        "── Demo (escenarios) ──\n"
        "/alerta — simular fuga detectada\n"
        "/riego — simular pico de riego\n"
        "/normal — volver a operación normal\n\n"
        "── IA General ──\n"
        "/ask <pregunta> — chat con los agentes\n"
        "/research <tema> — pipeline de investigación\n"
        "/report <tema> — generar reporte PDF\n"
        "/status — estado de proveedores LLM\n\n"
        "O simplemente escribe tu pregunta."
    )


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    if text.startswith("/ask "):
        text = text[5:]
    await _stream_chat(update, text, context_type="chat")


async def research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    if text.startswith("/research "):
        text = text[10:]
    if not text.strip():
        await update.message.reply_text("Usage: /research <topic>")
        return
    await _stream_chat(update, text, context_type="research")


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    if text.startswith("/report "):
        text = text[8:]
    if not text.strip():
        await update.message.reply_text("Usage: /report <topic>")
        return

    notice = await update.message.reply_text("Generating report — this can take ~20s…")
    summary = await _generate_summary(text)
    pdf_bytes = await _generate_pdf(text, summary)

    if pdf_bytes is None:
        await notice.edit_text("Failed to generate PDF. The backend may be down.")
        return

    await notice.edit_text("Done. Sending PDF…")
    await update.message.reply_document(
        document=io.BytesIO(pdf_bytes),
        filename=f"{text[:40].replace(' ', '_')}.pdf",
        caption=f"Report: {text}",
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(f"{BACKEND_URL}/health")
            data = response.json()
            providers = data.get("providers", {})
            lines = [f"Status: {data.get('status', 'unknown')}"]
            for name, info in providers.items():
                marker = "UP" if info.get("available") else "DOWN"
                fails = info.get("failures", 0)
                lines.append(f"  {name}: {marker} (fails={fails})")
            await update.message.reply_text("\n".join(lines))
        except httpx.HTTPError as e:
            await update.message.reply_text(f"Backend unreachable: {e}")


async def _stream_chat(update: Update, text: str, *, context_type: str) -> None:
    """Streams a chat reply, batching tokens to avoid Telegram rate limits."""
    if not text.strip():
        await update.message.reply_text("Empty message.")
        return

    placeholder = await update.message.reply_text("Thinking…")
    full_response = ""
    last_pushed = ""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                f"{BACKEND_URL}/chat/stream",
                json={"message": text, "context_type": context_type},
            ) as response:
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "token":
                        full_response += event.get("content", "")
                        if len(full_response) - len(last_pushed) >= 200:
                            try:
                                await placeholder.edit_text(full_response[:4096])
                                last_pushed = full_response
                            except Exception:
                                pass
                    elif event.get("type") == "error":
                        await placeholder.edit_text(f"Error: {event.get('error')}")
                        return
    except httpx.HTTPError as e:
        await placeholder.edit_text(f"Backend error: {e}")
        return

    if not full_response:
        await placeholder.edit_text("No response received.")
        return

    if len(full_response) <= 4096:
        await placeholder.edit_text(full_response)
    else:
        await placeholder.edit_text(full_response[:4096])
        for i in range(4096, len(full_response), 4096):
            await update.message.reply_text(full_response[i : i + 4096])


async def _generate_summary(topic: str) -> str:
    """Runs the research pipeline and concatenates streamed tokens."""
    full_text = ""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{BACKEND_URL}/agents/run",
                json={"task": topic, "context_type": "research", "engine": "research"},
            ) as response:
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "token":
                        full_text += event.get("content", "")
    except httpx.HTTPError:
        return ""
    return full_text


async def _generate_pdf(topic: str, summary: str) -> bytes | None:
    payload = {
        "title": topic[:80],
        "description": "Generated by AgentOS Telegram bot",
        "summary": summary or "(no summary returned)",
        "metrics": [],
        "table_columns": [],
        "table_data": [],
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{BACKEND_URL}/reports/generate", json=payload)
            if response.status_code != 200:
                return None
            return response.content
    except httpx.HTTPError:
        return None

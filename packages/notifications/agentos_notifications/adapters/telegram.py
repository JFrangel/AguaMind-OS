import os
import time

import httpx

from ..base import BaseNotifier, NotificationMessage, NotificationResult
from ..types import Channel, Severity

_SEVERITY_PREFIX = {
    Severity.INFO: "INFO",
    Severity.WARNING: "WARN",
    Severity.ERROR: "ERROR",
    Severity.CRITICAL: "CRITICAL",
}


class TelegramNotifier(BaseNotifier):
    """Sends notifications via Telegram Bot API.

    Requires:
        TELEGRAM_BOT_TOKEN — same token used by apps/telegram bot
        TELEGRAM_CHAT_IDS  — comma-separated default chat IDs (channel or user)
    """

    channel = Channel.TELEGRAM

    def __init__(self, bot_token: str | None = None, default_chat_ids: list[str] | None = None):
        self._token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        if default_chat_ids is None:
            raw = os.getenv("TELEGRAM_CHAT_IDS", "")
            default_chat_ids = [c.strip() for c in raw.split(",") if c.strip()]
        self._default_chat_ids = default_chat_ids

    def is_configured(self) -> bool:
        return bool(self._token and self._default_chat_ids)

    async def send(self, message: NotificationMessage) -> NotificationResult:
        start = time.monotonic()
        if not self._token:
            return NotificationResult(
                channel=self.channel, delivered=False, detail="TELEGRAM_BOT_TOKEN not set"
            )

        chat_ids = message.recipients.get("telegram") or self._default_chat_ids
        if not chat_ids:
            return NotificationResult(
                channel=self.channel,
                delivered=False,
                detail="no recipients (TELEGRAM_CHAT_IDS unset and no override)",
            )

        prefix = _SEVERITY_PREFIX.get(message.severity, "")
        text = f"*[{prefix}] {_md(message.title)}*\n\n{_md(message.body)}"

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        delivered_count = 0
        last_error = ""
        async with httpx.AsyncClient(timeout=10) as client:
            for chat_id in chat_ids:
                try:
                    resp = await client.post(
                        url,
                        json={
                            "chat_id": chat_id,
                            "text": text,
                            "parse_mode": "Markdown",
                            "disable_web_page_preview": True,
                        },
                    )
                    if resp.status_code == 200:
                        delivered_count += 1
                    else:
                        last_error = f"{resp.status_code}: {resp.text[:120]}"
                except httpx.HTTPError as e:
                    last_error = str(e)

        elapsed = (time.monotonic() - start) * 1000
        return NotificationResult(
            channel=self.channel,
            delivered=delivered_count > 0,
            detail=f"sent to {delivered_count}/{len(chat_ids)} chats. {last_error}".strip(),
            latency_ms=elapsed,
        )


def _md(text: str) -> str:
    """Escape Telegram Markdown reserved chars in plain content."""
    for char in ["_", "*", "`", "["]:
        text = text.replace(char, f"\\{char}")
    return text

import os
import smtplib
import ssl
import time
from email.message import EmailMessage

from ..base import BaseNotifier, NotificationMessage, NotificationResult
from ..types import Channel, Severity

_SEVERITY_LABEL = {
    Severity.INFO: "INFO",
    Severity.WARNING: "WARNING",
    Severity.ERROR: "ERROR",
    Severity.CRITICAL: "CRITICAL",
}


class EmailNotifier(BaseNotifier):
    """SMTP email notifier. Works with any provider:
        - Gmail: SMTP_HOST=smtp.gmail.com, SMTP_PORT=465, USER=<gmail>, PASSWORD=<app-password>
        - Brevo (free): smtp-relay.brevo.com:587
        - Resend, SendGrid: smtp.resend.com / smtp.sendgrid.net

    Required env:
        SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
        SMTP_FROM (defaults to SMTP_USER)
        EMAIL_RECIPIENTS (comma-separated default destinations)
    """

    channel = Channel.EMAIL

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        sender: str | None = None,
        default_recipients: list[str] | None = None,
    ):
        self._host = host or os.getenv("SMTP_HOST", "")
        self._port = port or int(os.getenv("SMTP_PORT", "587"))
        self._user = user or os.getenv("SMTP_USER", "")
        self._password = password or os.getenv("SMTP_PASSWORD", "")
        self._sender = sender or os.getenv("SMTP_FROM") or self._user
        if default_recipients is None:
            raw = os.getenv("EMAIL_RECIPIENTS", "")
            default_recipients = [r.strip() for r in raw.split(",") if r.strip()]
        self._default_recipients = default_recipients

    def is_configured(self) -> bool:
        return bool(self._host and self._user and self._password and self._default_recipients)

    async def send(self, message: NotificationMessage) -> NotificationResult:
        import asyncio

        start = time.monotonic()
        if not (self._host and self._user and self._password):
            return NotificationResult(
                channel=self.channel,
                delivered=False,
                detail="SMTP_HOST/USER/PASSWORD not configured",
            )

        recipients = message.recipients.get("email") or self._default_recipients
        if not recipients:
            return NotificationResult(
                channel=self.channel, delivered=False, detail="no email recipients configured"
            )

        msg = EmailMessage()
        label = _SEVERITY_LABEL.get(message.severity, "")
        msg["Subject"] = f"[{label}] {message.title}" if label else message.title
        msg["From"] = self._sender
        msg["To"] = ", ".join(recipients)
        msg.set_content(message.body)

        try:
            await asyncio.to_thread(self._send_blocking, msg)
            return NotificationResult(
                channel=self.channel,
                delivered=True,
                detail=f"sent to {len(recipients)} recipient(s)",
                latency_ms=(time.monotonic() - start) * 1000,
            )
        except Exception as e:
            return NotificationResult(
                channel=self.channel,
                delivered=False,
                detail=f"{type(e).__name__}: {e}",
                latency_ms=(time.monotonic() - start) * 1000,
            )

    def _send_blocking(self, msg: EmailMessage) -> None:
        """Synchronous SMTP send. Wrapped in to_thread by send().

        Picks SSL vs STARTTLS based on the port: 465 = implicit SSL, others = STARTTLS.
        """
        if self._port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self._host, self._port, context=context) as server:
                server.login(self._user, self._password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(self._host, self._port) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(self._user, self._password)
                server.send_message(msg)

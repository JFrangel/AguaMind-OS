import asyncio

from .adapters import EmailNotifier, TelegramNotifier
from .base import BaseNotifier, NotificationMessage, NotificationResult
from .types import Channel


class NotificationDispatcher:
    """Sends a notification to multiple channels in parallel.

    Each channel notifier reads its own env config — instantiate once and
    reuse. `send()` returns a list of per-channel results so callers can
    surface failures without aborting the whole batch.

    Usage:
        dispatcher = NotificationDispatcher()
        results = await dispatcher.send(
            NotificationMessage(title="Job done", body="..."),
            channels=[Channel.TELEGRAM, Channel.EMAIL],
        )
    """

    def __init__(self, notifiers: list[BaseNotifier] | None = None):
        self._notifiers: dict[Channel, BaseNotifier] = {}
        for n in notifiers or [TelegramNotifier(), EmailNotifier()]:
            self._notifiers[n.channel] = n

    def is_configured(self, channel: Channel) -> bool:
        notifier = self._notifiers.get(channel)
        return bool(notifier and notifier.is_configured())

    def configured_channels(self) -> list[Channel]:
        return [c for c, n in self._notifiers.items() if n.is_configured()]

    async def send(
        self,
        message: NotificationMessage,
        channels: list[Channel] | None = None,
    ) -> list[NotificationResult]:
        targets = channels or self.configured_channels()
        if not targets:
            return []

        tasks = []
        for channel in targets:
            notifier = self._notifiers.get(channel)
            if notifier is None:
                continue
            tasks.append(notifier.send(message))

        return list(await asyncio.gather(*tasks))

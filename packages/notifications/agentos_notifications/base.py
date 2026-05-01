from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .types import Channel, Severity


@dataclass
class NotificationMessage:
    title: str
    body: str
    severity: Severity = Severity.INFO
    metadata: dict = field(default_factory=dict)
    # Channel-specific recipient overrides. e.g. recipients={"email": ["a@b.com"]}.
    # When omitted, the notifier uses its default recipient from env config.
    recipients: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class NotificationResult:
    channel: Channel
    delivered: bool
    detail: str = ""
    latency_ms: float = 0.0


class BaseNotifier(ABC):
    channel: Channel

    @abstractmethod
    async def send(self, message: NotificationMessage) -> NotificationResult: ...

    @abstractmethod
    def is_configured(self) -> bool: ...

"""Dispatcher tests with stub notifiers — no real Telegram/SMTP traffic."""
import pytest

from agentos_notifications import (
    BaseNotifier,
    Channel,
    NotificationDispatcher,
    NotificationMessage,
    NotificationResult,
    Severity,
)


class StubNotifier(BaseNotifier):
    def __init__(self, channel: Channel, configured: bool = True, fail: bool = False):
        self.channel = channel
        self._configured = configured
        self._fail = fail
        self.calls: list[NotificationMessage] = []

    def is_configured(self) -> bool:
        return self._configured

    async def send(self, message: NotificationMessage) -> NotificationResult:
        self.calls.append(message)
        return NotificationResult(
            channel=self.channel,
            delivered=not self._fail,
            detail="stub failure" if self._fail else "stub ok",
        )


@pytest.mark.asyncio
async def test_dispatches_to_all_configured():
    tg = StubNotifier(Channel.TELEGRAM)
    em = StubNotifier(Channel.EMAIL)
    dispatcher = NotificationDispatcher([tg, em])

    results = await dispatcher.send(NotificationMessage(title="t", body="b"))
    assert len(results) == 2
    assert all(r.delivered for r in results)
    assert len(tg.calls) == 1
    assert len(em.calls) == 1


@pytest.mark.asyncio
async def test_skips_unconfigured_when_no_channels_passed():
    tg = StubNotifier(Channel.TELEGRAM, configured=True)
    em = StubNotifier(Channel.EMAIL, configured=False)
    dispatcher = NotificationDispatcher([tg, em])

    results = await dispatcher.send(NotificationMessage(title="t", body="b"))
    delivered_channels = [r.channel for r in results]
    assert Channel.TELEGRAM in delivered_channels
    assert Channel.EMAIL not in delivered_channels


@pytest.mark.asyncio
async def test_explicit_channels_override():
    tg = StubNotifier(Channel.TELEGRAM, configured=False)
    em = StubNotifier(Channel.EMAIL, configured=True)
    dispatcher = NotificationDispatcher([tg, em])

    # Explicit list overrides the configured filter — caller takes responsibility.
    results = await dispatcher.send(
        NotificationMessage(title="t", body="b"),
        channels=[Channel.TELEGRAM, Channel.EMAIL],
    )
    assert len(results) == 2


@pytest.mark.asyncio
async def test_partial_failure_does_not_abort():
    tg = StubNotifier(Channel.TELEGRAM, fail=True)
    em = StubNotifier(Channel.EMAIL)
    dispatcher = NotificationDispatcher([tg, em])

    results = await dispatcher.send(NotificationMessage(title="t", body="b"))
    delivered = {r.channel: r.delivered for r in results}
    assert delivered[Channel.TELEGRAM] is False
    assert delivered[Channel.EMAIL] is True


@pytest.mark.asyncio
async def test_severity_propagates():
    tg = StubNotifier(Channel.TELEGRAM)
    dispatcher = NotificationDispatcher([tg])

    await dispatcher.send(
        NotificationMessage(title="t", body="b", severity=Severity.CRITICAL)
    )
    assert tg.calls[0].severity == Severity.CRITICAL


def test_configured_channels_returns_only_ready():
    tg = StubNotifier(Channel.TELEGRAM, configured=True)
    em = StubNotifier(Channel.EMAIL, configured=False)
    dispatcher = NotificationDispatcher([tg, em])
    assert dispatcher.configured_channels() == [Channel.TELEGRAM]

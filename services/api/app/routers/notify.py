from fastapi import APIRouter, Request
from pydantic import BaseModel

from agentos_notifications import (
    Channel,
    NotificationDispatcher,
    NotificationMessage,
    Severity,
)

router = APIRouter()


class NotifyRequest(BaseModel):
    title: str
    body: str
    severity: Severity = Severity.INFO
    channels: list[Channel] | None = None
    metadata: dict = {}
    recipients: dict[str, list[str]] = {}


@router.post("/send")
async def send(body: NotifyRequest, request: Request):
    dispatcher: NotificationDispatcher = request.app.state.notifier
    msg = NotificationMessage(
        title=body.title,
        body=body.body,
        severity=body.severity,
        metadata=body.metadata,
        recipients=body.recipients,
    )
    results = await dispatcher.send(msg, channels=body.channels)
    return {
        "data": [
            {
                "channel": r.channel.value,
                "delivered": r.delivered,
                "detail": r.detail,
                "latency_ms": r.latency_ms,
            }
            for r in results
        ],
        "error": None,
        "meta": {"channels_attempted": len(results)},
    }


@router.get("/channels")
async def channels(request: Request):
    dispatcher: NotificationDispatcher = request.app.state.notifier
    return {
        "data": {
            "configured": [c.value for c in dispatcher.configured_channels()],
            "all": [c.value for c in Channel],
        },
        "error": None,
    }

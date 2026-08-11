"""Webhook subscription management.

Register URLs to receive platform events. Events are delivered as
`POST {url}` with body `{"event": "...", "data": {...}}`. Emitted event types:
`case.completed`, `case.action_required`, `case.pushed`.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from .. import store
from ..models import (
    EVENT_CASE_ACTION_REQUIRED,
    EVENT_CASE_COMPLETED,
    EVENT_CASE_PUSHED,
    WebhookSubscription,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

KNOWN_EVENTS = [
    EVENT_CASE_COMPLETED,
    EVENT_CASE_ACTION_REQUIRED,
    EVENT_CASE_PUSHED,
]


class WebhookCreate(BaseModel):
    url: str
    events: list[str] = []  # empty = all events


@router.post("", response_model=WebhookSubscription, status_code=201)
def create_webhook(body: WebhookCreate) -> WebhookSubscription:
    sub = WebhookSubscription(url=body.url, events=body.events)
    return store.webhooks.add(sub)


@router.get("", response_model=list[WebhookSubscription])
def list_webhooks() -> list[WebhookSubscription]:
    return store.webhooks.list()


@router.get("/events", response_model=list[str])
def list_event_types() -> list[str]:
    return KNOWN_EVENTS

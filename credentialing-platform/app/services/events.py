"""Outbound webhook dispatch.

Emits platform events (case completed / action required / pushed) to registered
subscriber URLs. Delivery is best-effort and fault-isolated: one subscriber's
failure never affects another or the request that triggered the event. The
`httpx.AsyncClient` is injectable so tests run with no network.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

from .. import store
from ..models import WebhookDelivery, WebhookSubscription


async def _deliver(
    client: httpx.AsyncClient,
    sub: WebhookSubscription,
    event: str,
    payload: dict[str, Any],
) -> WebhookDelivery:
    try:
        resp = await client.post(sub.url, json={"event": event, "data": payload})
        return WebhookDelivery(
            subscription_id=sub.id,
            event=event,
            ok=resp.status_code < 400,
            status_code=resp.status_code,
        )
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        return WebhookDelivery(
            subscription_id=sub.id,
            event=event,
            ok=False,
            error=f"{type(exc).__name__}: {exc}",
        )


async def emit(
    event: str,
    payload: dict[str, Any],
    client: Optional[httpx.AsyncClient] = None,
) -> list[WebhookDelivery]:
    """Deliver `event` to all subscribers that want it. No-op (and no network)
    when nothing is subscribed."""
    subs = store.webhooks.matching(event)
    if not subs:
        return []

    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=10.0)
    try:
        return list(
            await asyncio.gather(
                *(_deliver(client, s, event, payload) for s in subs)
            )
        )
    finally:
        if owns_client:
            await client.aclose()

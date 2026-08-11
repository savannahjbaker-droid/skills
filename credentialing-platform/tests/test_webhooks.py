import httpx
from fastapi.testclient import TestClient

from app import store
from app.main import app
from app.models import (
    EVENT_CASE_COMPLETED,
    WebhookSubscription,
)
from app.services.events import emit

client = TestClient(app)


async def test_emit_noop_without_subscribers():
    # No subscriptions -> returns empty, makes no network call.
    deliveries = await emit(EVENT_CASE_COMPLETED, {"hello": "world"})
    assert deliveries == []


async def test_emit_delivers_to_matching_subscribers_only():
    store.webhooks.add(
        WebhookSubscription(url="https://a.example/hook", events=[EVENT_CASE_COMPLETED])
    )
    store.webhooks.add(
        WebhookSubscription(url="https://b.example/hook", events=["case.pushed"])
    )

    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200)

    mock = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    deliveries = await emit(EVENT_CASE_COMPLETED, {"x": 1}, client=mock)

    assert len(deliveries) == 1
    assert deliveries[0].ok is True
    assert seen == ["https://a.example/hook"]


async def test_emit_isolates_failing_subscriber():
    store.webhooks.add(WebhookSubscription(url="https://bad.example/hook"))

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    mock = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    deliveries = await emit(EVENT_CASE_COMPLETED, {"x": 1}, client=mock)

    assert len(deliveries) == 1
    assert deliveries[0].ok is False
    assert "ConnectError" in (deliveries[0].error or "")


def test_webhook_registration_endpoints():
    resp = client.post(
        "/webhooks", json={"url": "https://c.example/hook", "events": ["case.pushed"]}
    )
    assert resp.status_code == 201
    assert resp.json()["url"] == "https://c.example/hook"

    listed = client.get("/webhooks").json()
    assert any(w["url"] == "https://c.example/hook" for w in listed)

    events = client.get("/webhooks/events").json()
    assert "case.completed" in events

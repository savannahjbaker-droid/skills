import httpx

from app.clearinghouses.innetwork import InNetworkConnector
from app.config import InNetworkSettings
from app.models import Provider, VerificationStatus


def _connector(status_by_payer):
    """Mock the documented POST /providers/status response."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/providers/status")
        assert request.headers["Authorization"].startswith("Bearer ")
        import json

        payer = json.loads(request.content)["payer"]
        return httpx.Response(
            200,
            json={
                "success": True,
                "message": "ok",
                "data": {"npi": "1234567893", "payer": payer,
                         "status": status_by_payer.get(payer, "not_found"), "entry": []},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return InNetworkConnector(client=client, settings=InNetworkSettings(api_key="sk_test_x"))


async def test_active_maps_to_in_network():
    c = _connector({"aetna": "active", "cigna": "active"})
    p = Provider(npi="1234567893", first_name="Jane", last_name="Smith",
                 target_payers=["Aetna", "Cigna"])
    result = await c.verify(p)
    assert result.status == VerificationStatus.VERIFIED
    assert result.data["payer_enrollment"] == {"Aetna": "enrolled", "Cigna": "enrolled"}


async def test_inactive_flags_gap():
    c = _connector({"aetna": "active", "humana": "not_found"})
    p = Provider(npi="1234567893", first_name="Jane", last_name="Smith",
                 target_payers=["Aetna", "Humana"])
    result = await c.verify(p)
    assert result.status == VerificationStatus.DISCREPANCY
    assert any("Humana" in d for d in result.discrepancies)


async def test_unconfigured_errors():
    c = InNetworkConnector(settings=InNetworkSettings())
    p = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    result = await c.verify(p)
    assert result.status == VerificationStatus.ERROR
    assert "not configured" in (result.error or "").lower()


async def test_no_npi_not_found():
    c = InNetworkConnector(settings=InNetworkSettings(api_key="sk_test_x"))
    p = Provider(first_name="Jane", last_name="Smith")
    result = await c.verify(p)
    assert result.status == VerificationStatus.NOT_FOUND

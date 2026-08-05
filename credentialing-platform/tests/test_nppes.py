import httpx
import pytest

from app.connectors.nppes import NPPESConnector
from app.models import Provider, VerificationStatus


def _mock_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


NPPES_MATCH = {
    "result_count": 1,
    "results": [
        {
            "number": "1234567893",
            "basic": {
                "first_name": "JANE",
                "last_name": "SMITH",
                "credential": "MD",
                "status": "A",
            },
        }
    ],
}


async def test_nppes_verified_on_match():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["number"] == "1234567893"
        return httpx.Response(200, json=NPPES_MATCH)

    connector = NPPESConnector(client=_mock_client(handler))
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    result = await connector.verify(provider)

    assert result.status == VerificationStatus.VERIFIED
    assert result.discrepancies == []
    assert result.data["credential"] == "MD"


async def test_nppes_discrepancy_on_name_mismatch():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=NPPES_MATCH)

    connector = NPPESConnector(client=_mock_client(handler))
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Doe")
    result = await connector.verify(provider)

    assert result.status == VerificationStatus.DISCREPANCY
    assert any("last_name" in d for d in result.discrepancies)


async def test_nppes_not_found_on_empty_results():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result_count": 0, "results": []})

    connector = NPPESConnector(client=_mock_client(handler))
    provider = Provider(npi="0000000000", first_name="No", last_name="Body")
    result = await connector.verify(provider)

    assert result.status == VerificationStatus.NOT_FOUND


async def test_nppes_not_found_without_npi():
    connector = NPPESConnector(client=_mock_client(lambda r: httpx.Response(200)))
    provider = Provider(first_name="No", last_name="Npi")
    result = await connector.verify(provider)

    assert result.status == VerificationStatus.NOT_FOUND
    assert "no npi" in (result.error or "").lower()

import httpx

from app.clearinghouses.availity import AvailityConnector
from app.clearinghouses.mocked import OfficeAllyConnector
from app.config import AvailitySettings
from app.models import Provider, VerificationStatus


def _availity_mock(enrollment_status: str) -> AvailityConnector:
    """Availity connector wired to a MockTransport (token + enrollment)."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/token"):
            return httpx.Response(200, json={"access_token": "test-token"})
        if request.url.path.endswith("/v1/enrollments"):
            assert request.headers["Authorization"] == "Bearer test-token"
            return httpx.Response(200, json={"status": enrollment_status})
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = AvailitySettings(client_id="id", client_secret="secret")
    return AvailityConnector(client=client, settings=settings)


async def test_availity_verified_when_enrolled_everywhere():
    connector = _availity_mock("enrolled")
    provider = Provider(
        npi="1234567893", first_name="Jane", last_name="Smith",
        target_payers=["Aetna", "Cigna"],
    )
    result = await connector.verify(provider)

    assert result.status == VerificationStatus.VERIFIED
    assert result.data["payer_enrollment"] == {"Aetna": "enrolled", "Cigna": "enrolled"}


async def test_availity_discrepancy_when_not_enrolled():
    connector = _availity_mock("not_enrolled")
    provider = Provider(
        npi="1234567893", first_name="Jane", last_name="Smith",
        target_payers=["Aetna"],
    )
    result = await connector.verify(provider)

    assert result.status == VerificationStatus.DISCREPANCY
    assert any("Aetna" in d for d in result.discrepancies)


async def test_availity_errors_when_unconfigured():
    # No injected client and no credentials -> cannot call the live API.
    connector = AvailityConnector(settings=AvailitySettings())
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    result = await connector.verify(provider)

    assert result.status == VerificationStatus.ERROR
    assert "not configured" in (result.error or "").lower()


async def test_availity_not_found_without_npi():
    connector = AvailityConnector(settings=AvailitySettings())
    provider = Provider(first_name="Jane", last_name="Smith")
    result = await connector.verify(provider)

    assert result.status == VerificationStatus.NOT_FOUND


async def test_office_ally_flags_pending_payer():
    connector = OfficeAllyConnector()
    provider = Provider(
        npi="1234567893", first_name="Jane", last_name="Smith",
        target_payers=["Aetna", "Cigna"],
    )
    result = await connector.verify(provider)

    # Last payer simulated as pending -> discrepancy on that payer only.
    assert result.status == VerificationStatus.DISCREPANCY
    assert result.data["payer_enrollment"]["Aetna"] == "enrolled"
    assert result.data["payer_enrollment"]["Cigna"] == "pending"

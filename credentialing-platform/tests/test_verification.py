import httpx

from app.connectors.mocked import CAQHConnector, PECOSConnector, StateBoardConnector
from app.connectors.nppes import NPPESConnector
from app.models import (
    CaseStatus,
    License,
    Provider,
    VerificationSource,
    VerificationStatus,
)
from app.services.verification import run_verifications


def _nppes_ok() -> NPPESConnector:
    payload = {
        "results": [
            {
                "number": "1234567893",
                "basic": {"first_name": "JANE", "last_name": "SMITH", "credential": "MD"},
            }
        ]
    }
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
    )
    return NPPESConnector(client=client)


async def test_all_sources_verified_completes_case():
    provider = Provider(
        npi="1234567893",
        first_name="Jane",
        last_name="Smith",
        licenses=[License(state="CA", number="A12345")],
    )
    connectors = [
        _nppes_ok(),
        CAQHConnector(),
        PECOSConnector(),
        StateBoardConnector(),
    ]
    case = await run_verifications(provider, connectors=connectors)

    assert case.status == CaseStatus.COMPLETED
    assert len(case.results) == 4
    assert all(r.status == VerificationStatus.VERIFIED for r in case.results)
    assert case.completed_at is not None


async def test_missing_license_triggers_action_required():
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    connectors = [_nppes_ok(), StateBoardConnector()]  # no licenses submitted
    case = await run_verifications(provider, connectors=connectors)

    assert case.status == CaseStatus.ACTION_REQUIRED
    board = next(r for r in case.results if r.source == VerificationSource.STATE_BOARD)
    assert board.status == VerificationStatus.NOT_FOUND


async def test_connector_exception_becomes_error_result():
    class Boom(StateBoardConnector):
        async def verify(self, provider):
            raise RuntimeError("upstream down")

    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    case = await run_verifications(provider, connectors=[Boom()])

    assert case.status == CaseStatus.ACTION_REQUIRED
    assert case.results[0].status == VerificationStatus.ERROR
    assert "upstream down" in case.results[0].error

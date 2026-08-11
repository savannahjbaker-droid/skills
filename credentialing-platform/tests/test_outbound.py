import httpx

from app.clearinghouses.availity import AvailityConnector
from app.clearinghouses.mocked import ChangeHealthcareConnector
from app.config import AvailitySettings
from app.models import (
    CaseStatus,
    CredentialingCase,
    EdiTransaction,
    Provider,
    PushStatus,
    VerificationResult,
    VerificationSource,
    VerificationStatus,
)
from app.outbound.systems import (
    OUTBOUND_ADAPTERS,
    SalesforceOutboundAdapter,
)
from app.services.outbound import push_case_to_systems


def _case_for(provider: Provider) -> CredentialingCase:
    case = CredentialingCase(
        provider_id=provider.id,
        results=[
            VerificationResult(
                source=VerificationSource.NPPES, status=VerificationStatus.VERIFIED
            ),
            VerificationResult(
                source=VerificationSource.CHANGE_HEALTHCARE,
                status=VerificationStatus.VERIFIED,
                data={"payer_enrollment": {"Aetna": "enrolled", "Cigna": "enrolled"}},
            ),
        ],
    )
    case.recompute_status()
    return case


async def test_push_skips_systems_without_external_id():
    provider = Provider(
        npi="1234567893", first_name="Jane", last_name="Smith",
        external_ids={"salesforce": "003xx"},
    )
    receipts = await push_case_to_systems(provider, _case_for(provider))
    by_system = {r.system.value: r for r in receipts}

    assert by_system["salesforce"].status == PushStatus.ACCEPTED
    assert by_system["ats"].status == PushStatus.SKIPPED
    assert by_system["emr"].status == PushStatus.SKIPPED


def test_salesforce_adapter_maps_case_to_custom_fields():
    provider = Provider(
        npi="1234567893", first_name="Jane", last_name="Smith",
        external_ids={"salesforce": "003xx"},
    )
    case = _case_for(provider)
    payload = SalesforceOutboundAdapter().build_update(provider, case)

    assert payload["Id"] == "003xx"
    assert payload["Credentialing_Status__c"] == CaseStatus.COMPLETED.value
    assert payload["Payer_Enrollment__c"] == "Aetna, Cigna"


async def test_mocked_clearinghouse_enrollment_and_edi():
    ch = ChangeHealthcareConnector()
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")

    sub = await ch.submit_enrollment(provider, "Aetna")
    assert sub.submitted is True
    assert sub.clearinghouse == VerificationSource.CHANGE_HEALTHCARE

    ack = await ch.submit_edi(
        EdiTransaction(transaction_set="270", payer="Aetna", control_number=5, x12="...")
    )
    assert ack.accepted is True
    assert ack.control_number == 5


async def test_availity_submit_edi_real_shaped_with_mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/v1/token"):
            return httpx.Response(200, json={"access_token": "t"})
        if request.url.path.endswith("/v1/x12"):
            assert request.headers["Content-Type"] == "application/edi-x12"
            return httpx.Response(200, json={"status": "A", "messages": ["ok"]})
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    connector = AvailityConnector(
        client=client, settings=AvailitySettings(client_id="i", client_secret="s")
    )
    ack = await connector.submit_edi(
        EdiTransaction(transaction_set="270", payer="Aetna", control_number=9, x12="ISA...~")
    )
    assert ack.accepted is True
    assert ack.status_code == "A"


async def test_availity_enrollment_errors_when_unconfigured():
    from app.services.outbound import submit_enrollment

    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    result = await submit_enrollment(provider, "Aetna", VerificationSource.AVAILITY)
    assert result.submitted is False
    assert "not configured" in (result.message or "").lower()

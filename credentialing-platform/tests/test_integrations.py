from app.integrations import get_adapter
from app.models import SourceSystem


def test_ats_adapter_maps_fields():
    adapter = get_adapter(SourceSystem.ATS)
    provider = adapter.to_provider(
        {
            "candidate_id": "C-100",
            "npi": "1234567893",
            "first_name": "Jane",
            "last_name": "Smith",
            "credential": "MD",
            "licenses": [{"state": "CA", "number": "A12345"}],
        }
    )
    assert provider.npi == "1234567893"
    assert provider.source_system == SourceSystem.ATS
    assert provider.external_ids == {"ats": "C-100"}
    assert provider.licenses[0].state == "CA"


def test_emr_adapter_handles_nested_name():
    adapter = get_adapter(SourceSystem.EMR)
    provider = adapter.to_provider(
        {
            "provider_id": "E-7",
            "name": {"given": "Jane", "family": "Smith"},
            "primary_specialty": "Cardiology",
        }
    )
    assert provider.first_name == "Jane"
    assert provider.last_name == "Smith"
    assert provider.specialty == "Cardiology"
    assert provider.external_ids == {"emr": "E-7"}


def test_salesforce_adapter_maps_custom_fields():
    adapter = get_adapter(SourceSystem.SALESFORCE)
    provider = adapter.to_provider(
        {
            "Id": "003xx",
            "FirstName": "Jane",
            "LastName": "Smith",
            "NPI__c": "1234567893",
            "Specialty__c": "Cardiology",
        }
    )
    assert provider.npi == "1234567893"
    assert provider.specialty == "Cardiology"
    assert provider.external_ids == {"salesforce": "003xx"}

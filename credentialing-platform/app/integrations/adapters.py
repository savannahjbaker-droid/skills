"""Concrete inbound adapters for ATS, EMR, and Salesforce.

Field mappings are illustrative of each system's conventions:
  * ATS (applicant tracking) uses candidate-centric fields.
  * EMR uses clinical/provider directory fields (often HL7-ish).
  * Salesforce uses Contact object fields with custom `__c` attributes.
"""

from __future__ import annotations

from typing import Any

from ..models import Provider, SourceSystem
from .base import InboundAdapter, _licenses


class ATSAdapter(InboundAdapter):
    system = SourceSystem.ATS
    external_id_field = "candidate_id"

    def to_provider(self, payload: dict[str, Any]) -> Provider:
        return Provider(
            npi=payload.get("npi"),
            first_name=payload.get("first_name", ""),
            last_name=payload.get("last_name", ""),
            credential=payload.get("credential"),
            specialty=payload.get("specialty"),
            email=payload.get("email"),
            licenses=_licenses(payload.get("licenses")),
            target_payers=payload.get("target_payers", []),
            source_system=self.system,
            external_ids=self._external_ids(payload),
        )


class EMRAdapter(InboundAdapter):
    system = SourceSystem.EMR
    external_id_field = "provider_id"

    def to_provider(self, payload: dict[str, Any]) -> Provider:
        # EMRs commonly split names into given/family.
        name = payload.get("name", {})
        return Provider(
            npi=payload.get("npi"),
            first_name=name.get("given", payload.get("first_name", "")),
            last_name=name.get("family", payload.get("last_name", "")),
            credential=payload.get("credential"),
            specialty=payload.get("primary_specialty") or payload.get("specialty"),
            email=payload.get("contact_email") or payload.get("email"),
            licenses=_licenses(payload.get("licenses")),
            target_payers=payload.get("target_payers", []),
            source_system=self.system,
            external_ids=self._external_ids(payload),
        )


class SalesforceAdapter(InboundAdapter):
    system = SourceSystem.SALESFORCE
    external_id_field = "Id"

    def to_provider(self, payload: dict[str, Any]) -> Provider:
        # Salesforce Contact with custom fields (NPI__c, Specialty__c, ...).
        return Provider(
            npi=payload.get("NPI__c") or payload.get("npi"),
            first_name=payload.get("FirstName", ""),
            last_name=payload.get("LastName", ""),
            credential=payload.get("Credential__c"),
            specialty=payload.get("Specialty__c"),
            email=payload.get("Email"),
            licenses=_licenses(payload.get("Licenses__r")),
            target_payers=payload.get("Target_Payers__c", []),
            source_system=self.system,
            external_ids=self._external_ids(payload),
        )


ADAPTERS: dict[SourceSystem, InboundAdapter] = {
    SourceSystem.ATS: ATSAdapter(),
    SourceSystem.EMR: EMRAdapter(),
    SourceSystem.SALESFORCE: SalesforceAdapter(),
}


def get_adapter(system: SourceSystem) -> InboundAdapter:
    if system not in ADAPTERS:
        raise KeyError(f"No inbound adapter registered for system '{system}'")
    return ADAPTERS[system]

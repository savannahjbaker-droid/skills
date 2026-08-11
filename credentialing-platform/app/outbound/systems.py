"""Outbound adapters — push a credentialing case back to systems of record.

The mirror image of the inbound integration adapters. Where inbound maps a
system's native payload *into* a canonical `Provider`, outbound maps a
`CredentialingCase` *out* into each system's native update shape and writes it
back — so the ATS/EMR/CRM reflects verified status without anyone re-keying it.

Transport is mocked (returns a `PushReceipt`); swap `_transport` for the real
REST/SOAP/Bulk API call to go live.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import (
    CredentialingCase,
    Provider,
    PushReceipt,
    PushStatus,
    SourceSystem,
    VerificationStatus,
)


def _enrolled_payers(case: CredentialingCase) -> list[str]:
    """Collect payers reported enrolled across clearinghouse results."""
    enrolled: list[str] = []
    for r in case.results:
        for payer, status in (r.data.get("payer_enrollment") or {}).items():
            if status == "enrolled":
                enrolled.append(payer)
    return sorted(set(enrolled))


def _verified_sources(case: CredentialingCase) -> list[str]:
    return [r.source.value for r in case.results if r.status == VerificationStatus.VERIFIED]


class OutboundSystemAdapter(ABC):
    system: SourceSystem

    @abstractmethod
    def build_update(self, provider: Provider, case: CredentialingCase) -> dict[str, Any]:
        """Map the case into this system's native update fields."""
        raise NotImplementedError

    async def push(self, provider: Provider, case: CredentialingCase) -> PushReceipt:
        ext = provider.external_ids.get(self.system.value)
        if not ext:
            return PushReceipt(
                system=self.system,
                status=PushStatus.SKIPPED,
                message=f"Provider has no {self.system.value} ID; nothing to update.",
            )
        payload = self.build_update(provider, case)
        try:
            await self._transport(ext, payload)
        except Exception as exc:  # noqa: BLE001 - surfaced as an error receipt
            return PushReceipt(
                system=self.system,
                external_id=ext,
                status=PushStatus.ERROR,
                message=f"{type(exc).__name__}: {exc}",
                payload=payload,
            )
        return PushReceipt(
            system=self.system,
            external_id=ext,
            status=PushStatus.ACCEPTED,
            message=f"Updated {len(payload)} field(s).",
            payload=payload,
        )

    async def _transport(self, external_id: str, payload: dict[str, Any]) -> None:
        """Mocked write. Replace with the real system API call."""
        return None


class ATSOutboundAdapter(OutboundSystemAdapter):
    system = SourceSystem.ATS

    def build_update(self, provider: Provider, case: CredentialingCase) -> dict[str, Any]:
        return {
            "candidate_id": provider.external_ids.get("ats"),
            "credentialing_status": case.status.value,
            "verified_sources": _verified_sources(case),
            "enrolled_payers": _enrolled_payers(case),
        }


class EMROutboundAdapter(OutboundSystemAdapter):
    system = SourceSystem.EMR

    def build_update(self, provider: Provider, case: CredentialingCase) -> dict[str, Any]:
        return {
            "provider_id": provider.external_ids.get("emr"),
            "credential_status": case.status.value,
            "npi_verified": any(
                r.source.value == "nppes" and r.status == VerificationStatus.VERIFIED
                for r in case.results
            ),
            "billable_payers": _enrolled_payers(case),
        }


class SalesforceOutboundAdapter(OutboundSystemAdapter):
    system = SourceSystem.SALESFORCE

    def build_update(self, provider: Provider, case: CredentialingCase) -> dict[str, Any]:
        return {
            "Id": provider.external_ids.get("salesforce"),
            "Credentialing_Status__c": case.status.value,
            "Last_Verified__c": (
                case.completed_at.isoformat() if case.completed_at else None
            ),
            "Payer_Enrollment__c": ", ".join(_enrolled_payers(case)),
        }


OUTBOUND_ADAPTERS: dict[SourceSystem, OutboundSystemAdapter] = {
    SourceSystem.ATS: ATSOutboundAdapter(),
    SourceSystem.EMR: EMROutboundAdapter(),
    SourceSystem.SALESFORCE: SalesforceOutboundAdapter(),
}

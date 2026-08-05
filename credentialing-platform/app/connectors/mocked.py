"""Mocked connectors for sources that require credentialed/paid access.

CAQH, PECOS, and state medical boards all require organizational credentials,
signed agreements, or per-state portal access that can't be provisioned in a
demo. These connectors mirror the real connector contract and return
deterministic, plausibly-shaped data so the orchestration, aggregation, and API
layers can be exercised end to end.

Each is a drop-in: replace the body of `verify` with the real HTTP/SFTP/SOAP
call and the rest of the platform is unchanged.
"""

from __future__ import annotations

from ..models import (
    Provider,
    VerificationResult,
    VerificationSource,
    VerificationStatus,
)
from .base import PrimarySourceConnector


class CAQHConnector(PrimarySourceConnector):
    """CAQH ProView — attestation & credentialing document repository.

    Real integration: CAQH ProView SOAP/Batch API using an organization ID and
    roster of CAQH provider IDs the provider has authorized.
    """

    source = VerificationSource.CAQH

    async def verify(self, provider: Provider) -> VerificationResult:
        # Simulate: found and attested when an NPI is present.
        if not provider.npi:
            return VerificationResult(
                source=self.source,
                status=VerificationStatus.NOT_FOUND,
                error="No NPI; cannot locate CAQH ProView profile.",
            )
        return VerificationResult(
            source=self.source,
            status=VerificationStatus.VERIFIED,
            data={
                "caqh_provider_id": f"1{provider.npi[-7:]}",
                "attestation_current": True,
                "authorization": "global",
            },
        )


class PECOSConnector(PrimarySourceConnector):
    """PECOS — Medicare enrollment status.

    Real integration: CMS PECOS via the enrollment API / Medicare data files,
    keyed on NPI.
    """

    source = VerificationSource.PECOS

    async def verify(self, provider: Provider) -> VerificationResult:
        if not provider.npi:
            return VerificationResult(
                source=self.source,
                status=VerificationStatus.NOT_FOUND,
                error="No NPI; cannot check Medicare enrollment.",
            )
        return VerificationResult(
            source=self.source,
            status=VerificationStatus.VERIFIED,
            data={"medicare_enrolled": True, "reassignment_eligible": True},
        )


class StateBoardConnector(PrimarySourceConnector):
    """State medical board license verification.

    Real integration: per-state board portal / FSMB / state API. Verifies each
    license the provider submitted.
    """

    source = VerificationSource.STATE_BOARD

    async def verify(self, provider: Provider) -> VerificationResult:
        if not provider.licenses:
            return VerificationResult(
                source=self.source,
                status=VerificationStatus.NOT_FOUND,
                error="No licenses submitted to verify.",
            )
        verified = [
            {"state": lic.state, "number": lic.number, "status": "active"}
            for lic in provider.licenses
        ]
        return VerificationResult(
            source=self.source,
            status=VerificationStatus.VERIFIED,
            data={"licenses": verified},
        )

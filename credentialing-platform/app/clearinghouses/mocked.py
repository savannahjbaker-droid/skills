"""Mocked clearinghouse connectors.

Change Healthcare/Optum, Waystar, and Office Ally each require partner
agreements and credentials. These mirror the `ClearinghouseConnector` contract
and return deterministic enrollment data so the end-to-end flow is exercisable.
Replace the body of `check_enrollment` with the real EDI/REST call to go live.
"""

from __future__ import annotations

from ..models import Provider, VerificationSource
from .base import ENROLLED, PENDING, ClearinghouseConnector


class ChangeHealthcareConnector(ClearinghouseConnector):
    """Change Healthcare / Optum — largest US clearinghouse.

    Real integration: Optum/Change Healthcare Medical Network APIs (REST) or
    X12 EDI (270/271 eligibility, 837 claims) enrollment.
    """

    source = VerificationSource.CHANGE_HEALTHCARE

    async def check_enrollment(
        self, provider: Provider, payers: list[str]
    ) -> dict[str, str]:
        # Simulate: enrolled everywhere for a provider with an NPI.
        return {payer: ENROLLED for payer in payers}


class WaystarConnector(ClearinghouseConnector):
    """Waystar — revenue-cycle clearinghouse.

    Real integration: Waystar API for eligibility/claims enrollment.
    """

    source = VerificationSource.WAYSTAR

    async def check_enrollment(
        self, provider: Provider, payers: list[str]
    ) -> dict[str, str]:
        return {payer: ENROLLED for payer in payers}


class OfficeAllyConnector(ClearinghouseConnector):
    """Office Ally — clearinghouse popular with smaller practices.

    Real integration: Office Ally SFTP/EDI enrollment feeds.
    """

    source = VerificationSource.OFFICE_ALLY

    async def check_enrollment(
        self, provider: Provider, payers: list[str]
    ) -> dict[str, str]:
        # Simulate a realistic gap: last payer still pending enrollment.
        statuses = {payer: ENROLLED for payer in payers}
        if payers:
            statuses[payers[-1]] = PENDING
        return statuses

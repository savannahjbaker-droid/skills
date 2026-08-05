"""Clearinghouse connector contract.

A clearinghouse (Availity, Change Healthcare/Optum, Waystar, Office Ally, …) is
a *payer connectivity hub*: one integration that reaches many payers for EDI
transactions. Where a PSV source answers "is this identity/license real?", a
clearinghouse answers "is this provider **enrolled** so they can submit
claims/eligibility to payer X?".

Clearinghouse connectors reuse the PSV `PrimarySourceConnector` interface — they
produce a `VerificationResult` and run through the same orchestrator — but add
payer-enrollment structure on top. A subclass implements just `check_enrollment`.
"""

from __future__ import annotations

from abc import abstractmethod

from ..connectors.base import PrimarySourceConnector
from ..models import (
    EdiAcknowledgment,
    EdiTransaction,
    EnrollmentSubmission,
    Provider,
    VerificationResult,
    VerificationStatus,
)

#: National payers checked when a provider names no `target_payers`.
DEFAULT_PAYERS = ["Aetna", "Cigna", "UnitedHealthcare", "Anthem BCBS", "Humana"]

#: Per-payer enrollment states a clearinghouse can report.
ENROLLED = "enrolled"
NOT_ENROLLED = "not_enrolled"
PENDING = "pending"


class ClearinghouseConnector(PrimarySourceConnector):
    def payers_for(self, provider: Provider) -> list[str]:
        return provider.target_payers or DEFAULT_PAYERS

    @abstractmethod
    async def check_enrollment(
        self, provider: Provider, payers: list[str]
    ) -> dict[str, str]:
        """Return `{payer: status}` where status ∈ {enrolled, not_enrolled, pending}.

        Raise only on transport/config failures; the base class converts a raise
        into an ERROR result and encodes enrollment gaps as a DISCREPANCY.
        """
        raise NotImplementedError

    async def verify(self, provider: Provider) -> VerificationResult:
        payers = self.payers_for(provider)
        if not provider.npi:
            return VerificationResult(
                source=self.source,
                status=VerificationStatus.NOT_FOUND,
                error="No NPI; cannot look up payer enrollment.",
            )
        try:
            statuses = await self.check_enrollment(provider, payers)
        except Exception as exc:  # noqa: BLE001 - surfaced as an ERROR result
            return VerificationResult(
                source=self.source,
                status=VerificationStatus.ERROR,
                error=f"{type(exc).__name__}: {exc}",
            )

        gaps = [p for p, s in statuses.items() if s != ENROLLED]
        status = (
            VerificationStatus.VERIFIED
            if not gaps
            else VerificationStatus.DISCREPANCY
        )
        return VerificationResult(
            source=self.source,
            status=status,
            discrepancies=[f"payer enrollment {statuses[p]}: {p}" for p in gaps],
            data={"payer_enrollment": statuses},
        )

    # --- Outbound: submit enrollment & EDI through the clearinghouse --------- #

    async def submit_enrollment(
        self, provider: Provider, payer: str
    ) -> EnrollmentSubmission:
        """Submit a payer EDI/transaction enrollment request via this
        clearinghouse. Default is a mocked accepted submission; real connectors
        override with the live enrollment API/EDI feed."""
        return EnrollmentSubmission(
            clearinghouse=self.source,
            payer=payer,
            submitted=True,
            tracking_id=f"{self.source.value}-{(provider.npi or 'NONPI')}-{_slug(payer)}",
            message="Enrollment request queued (mocked).",
        )

    async def submit_edi(self, transaction: EdiTransaction) -> EdiAcknowledgment:
        """Submit an X12 EDI transaction and return the acknowledgment. Default
        is a mocked 999 acceptance; real connectors override with the live EDI
        endpoint."""
        return EdiAcknowledgment(
            accepted=True,
            ack_type="999",
            status_code="A",
            control_number=transaction.control_number,
            messages=[f"Accepted {transaction.transaction_set} for {transaction.payer} (mocked)."],
        )


def _slug(value: str) -> str:
    return "".join(ch for ch in value.upper() if ch.isalnum())[:15] or "PAYER"

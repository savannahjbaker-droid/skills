"""Outbound orchestration.

Three flows, all fault-isolated:
  * push a case back to every system of record the provider exists in;
  * submit a payer enrollment through a clearinghouse;
  * build and submit an X12 270 connectivity probe through a clearinghouse.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

from ..clearinghouses import get_clearinghouse
from ..models import (
    Claim,
    CredentialingCase,
    EdiAcknowledgment,
    EdiTransaction,
    EligibilitySubscriber,
    EnrollmentSubmission,
    Provider,
    PushReceipt,
    VerificationSource,
)
from ..outbound.edi import build_270, build_837p
from ..outbound.systems import OUTBOUND_ADAPTERS


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def push_case_to_systems(
    provider: Provider, case: CredentialingCase
) -> list[PushReceipt]:
    """Write the case result back to every system of record concurrently.

    Systems the provider isn't present in return a SKIPPED receipt, so the
    response is a complete, auditable picture.
    """
    adapters = list(OUTBOUND_ADAPTERS.values())
    return list(
        await asyncio.gather(*(a.push(provider, case) for a in adapters))
    )


async def submit_enrollment(
    provider: Provider, payer: str, clearinghouse: VerificationSource
) -> EnrollmentSubmission:
    connector = get_clearinghouse(clearinghouse)
    try:
        return await connector.submit_enrollment(provider, payer)
    except Exception as exc:  # noqa: BLE001 - surfaced as a failed submission
        return EnrollmentSubmission(
            clearinghouse=clearinghouse,
            payer=payer,
            submitted=False,
            message=f"{type(exc).__name__}: {exc}",
        )


async def submit_eligibility_probe(
    provider: Provider,
    payer: str,
    clearinghouse: VerificationSource,
    control_number: int,
    subscriber: Optional[EligibilitySubscriber] = None,
    now: Optional[datetime] = None,
) -> tuple[EdiTransaction, EdiAcknowledgment]:
    """Build a 270 and submit it through the clearinghouse; return both the
    generated EDI and the acknowledgment."""
    subscriber = subscriber or EligibilitySubscriber()
    txn = build_270(provider, payer, subscriber, control_number, now or _now())
    return await _submit_txn(txn, clearinghouse, control_number)


async def submit_claim(
    provider: Provider,
    payer: str,
    claim: Claim,
    clearinghouse: VerificationSource,
    control_number: int,
    now: Optional[datetime] = None,
) -> tuple[EdiTransaction, EdiAcknowledgment]:
    """Build an 837P and submit it through the clearinghouse."""
    txn = build_837p(provider, payer, claim, control_number, now or _now())
    return await _submit_txn(txn, clearinghouse, control_number)


async def _submit_txn(
    txn: EdiTransaction, clearinghouse: VerificationSource, control_number: int
) -> tuple[EdiTransaction, EdiAcknowledgment]:
    connector = get_clearinghouse(clearinghouse)
    try:
        ack = await connector.submit_edi(txn)
    except Exception as exc:  # noqa: BLE001 - surfaced as a rejected ack
        ack = EdiAcknowledgment(
            accepted=False,
            status_code="R",
            control_number=control_number,
            messages=[f"{type(exc).__name__}: {exc}"],
        )
    return txn, ack

"""Outbound endpoints.

    POST /cases/{case_id}/push                 -> write results back to ATS/EMR/SFDC
    POST /providers/{id}/enrollment-submissions -> submit payer enrollment via clearinghouse
    POST /providers/{id}/eligibility            -> build & submit an X12 270 probe
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import store
from ..models import (
    Claim,
    EdiAcknowledgment,
    EdiTransaction,
    EligibilitySubscriber,
    EnrollmentSubmission,
    PushReceipt,
    VerificationSource,
)
from ..services.outbound import (
    push_case_to_systems,
    submit_claim,
    submit_eligibility_probe,
    submit_enrollment,
)

router = APIRouter(tags=["outbound"])


class PushResponse(BaseModel):
    case_id: str
    receipts: list[PushReceipt]


@router.post("/cases/{case_id}/push", response_model=PushResponse)
async def push_case(case_id: str) -> PushResponse:
    """Push a credentialing case back to every system of record the provider
    exists in (ATS/EMR/Salesforce), so no result is re-keyed by hand."""
    case = store.cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    provider = store.providers.get(case.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    receipts = await push_case_to_systems(provider, case)
    return PushResponse(case_id=case.id, receipts=receipts)


class EnrollmentRequest(BaseModel):
    payer: str
    clearinghouse: VerificationSource = VerificationSource.CHANGE_HEALTHCARE


@router.post(
    "/providers/{provider_id}/enrollment-submissions",
    response_model=EnrollmentSubmission,
)
async def submit_payer_enrollment(
    provider_id: str, body: EnrollmentRequest
) -> EnrollmentSubmission:
    """Submit a payer EDI/transaction enrollment through a clearinghouse."""
    provider = store.providers.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return await submit_enrollment(provider, body.payer, body.clearinghouse)


class EligibilityRequest(BaseModel):
    payer: str
    clearinghouse: VerificationSource = VerificationSource.CHANGE_HEALTHCARE
    subscriber: Optional[EligibilitySubscriber] = None


class EligibilityResponse(BaseModel):
    transaction: EdiTransaction
    acknowledgment: EdiAcknowledgment


@router.post("/providers/{provider_id}/eligibility", response_model=EligibilityResponse)
async def submit_eligibility(
    provider_id: str, body: EligibilityRequest
) -> EligibilityResponse:
    """Build an X12 270 and submit it through a clearinghouse — a post-enrollment
    connectivity probe confirming the provider can transact with the payer."""
    provider = store.providers.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    txn, ack = await submit_eligibility_probe(
        provider,
        body.payer,
        body.clearinghouse,
        control_number=store.control_numbers.next(),
        subscriber=body.subscriber,
    )
    return EligibilityResponse(transaction=txn, acknowledgment=ack)


class ClaimRequest(BaseModel):
    payer: str
    claim: Claim
    clearinghouse: VerificationSource = VerificationSource.CHANGE_HEALTHCARE


class ClaimResponse(BaseModel):
    transaction: EdiTransaction
    acknowledgment: EdiAcknowledgment


@router.post("/providers/{provider_id}/claims", response_model=ClaimResponse)
async def submit_professional_claim(
    provider_id: str, body: ClaimRequest
) -> ClaimResponse:
    """Build an X12 837P professional claim and submit it through a clearinghouse."""
    provider = store.providers.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    txn, ack = await submit_claim(
        provider,
        body.payer,
        body.claim,
        body.clearinghouse,
        control_number=store.control_numbers.next(),
    )
    return ClaimResponse(transaction=txn, acknowledgment=ack)

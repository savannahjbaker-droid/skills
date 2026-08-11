"""Credentialing / verification endpoints.

POST /providers/{id}/verify   -> run PSV across all sources, create a case
GET  /cases/{case_id}         -> fetch a case with all source results
GET  /cases                   -> list cases
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import store
from ..clearinghouses import default_clearinghouses
from ..models import (
    CaseStatus,
    CredentialingCase,
    EVENT_CASE_ACTION_REQUIRED,
    EVENT_CASE_COMPLETED,
    EVENT_CASE_PUSHED,
)
from ..services.events import emit
from ..services.outbound import push_case_to_systems
from ..services.verification import run_verifications

router = APIRouter(tags=["credentialing"])


async def _finalize(case: CredentialingCase, provider, auto_push: bool) -> CredentialingCase:
    """Persist the case, emit its completion event, and optionally push results
    back to the systems of record (emitting a `case.pushed` event)."""
    store.cases.add(case)
    event = (
        EVENT_CASE_COMPLETED
        if case.status == CaseStatus.COMPLETED
        else EVENT_CASE_ACTION_REQUIRED
    )
    await emit(event, case.model_dump(mode="json"))
    if auto_push:
        receipts = await push_case_to_systems(provider, case)
        await emit(
            EVENT_CASE_PUSHED,
            {
                "case_id": case.id,
                "receipts": [r.model_dump(mode="json") for r in receipts],
            },
        )
    return case


@router.post("/providers/{provider_id}/verify", response_model=CredentialingCase)
async def verify_provider(
    provider_id: str, auto_push: bool = False
) -> CredentialingCase:
    """Full credentialing run: PSV identity/licensure **and** clearinghouse
    payer-enrollment checks.

    Emits a `case.completed` or `case.action_required` webhook. With
    `?auto_push=true`, also pushes results to the systems of record and emits
    `case.pushed` (receipts arrive via that webhook; the HTTP response stays the
    case). Use `POST /cases/{id}/push` for receipts inline.
    """
    provider = store.providers.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    case = await run_verifications(provider)
    return await _finalize(case, provider, auto_push)


@router.post(
    "/providers/{provider_id}/payer-enrollment", response_model=CredentialingCase
)
async def check_payer_enrollment(provider_id: str) -> CredentialingCase:
    """Clearinghouse-only run: check payer enrollment across Availity, Change
    Healthcare, Waystar, and Office Ally without re-running PSV."""
    provider = store.providers.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    case = await run_verifications(provider, connectors=default_clearinghouses())
    return store.cases.add(case)


@router.get("/cases", response_model=list[CredentialingCase])
def list_cases() -> list[CredentialingCase]:
    return store.cases.list()


@router.get("/cases/{case_id}", response_model=CredentialingCase)
def get_case(case_id: str) -> CredentialingCase:
    case = store.cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

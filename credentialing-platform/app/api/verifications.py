"""Credentialing / verification endpoints.

POST /providers/{id}/verify   -> run PSV across all sources, create a case
GET  /cases/{case_id}         -> fetch a case with all source results
GET  /cases                   -> list cases
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import store
from ..clearinghouses import default_clearinghouses
from ..models import CredentialingCase
from ..services.verification import run_verifications

router = APIRouter(tags=["credentialing"])


@router.post("/providers/{provider_id}/verify", response_model=CredentialingCase)
async def verify_provider(provider_id: str) -> CredentialingCase:
    """Full credentialing run: PSV identity/licensure **and** clearinghouse
    payer-enrollment checks."""
    provider = store.providers.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    case = await run_verifications(provider)
    return store.cases.add(case)


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

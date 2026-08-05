"""Provider CRUD endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import store
from ..models import License, Provider, SourceSystem

router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderCreate(BaseModel):
    npi: Optional[str] = None
    first_name: str
    last_name: str
    credential: Optional[str] = None
    specialty: Optional[str] = None
    licenses: list[License] = []
    email: Optional[str] = None
    source_system: SourceSystem = SourceSystem.API
    external_ids: dict[str, str] = {}


@router.post("", response_model=Provider, status_code=201)
def create_provider(body: ProviderCreate) -> Provider:
    provider = Provider(**body.model_dump())
    return store.providers.add(provider)


@router.get("", response_model=list[Provider])
def list_providers() -> list[Provider]:
    return store.providers.list()


@router.get("/{provider_id}", response_model=Provider)
def get_provider(provider_id: str) -> Provider:
    provider = store.providers.get(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider

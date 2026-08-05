"""Inbound integration endpoints.

External systems of record push provider data here in their own native shape.
The matching adapter normalizes it into a canonical `Provider`, upserting on the
system's external ID so repeated syncs update rather than duplicate.

    POST /integrations/{system}/providers

where {system} is one of: ats | emr | salesforce.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import store
from ..integrations import get_adapter
from ..models import Provider, SourceSystem


class IngestResponse(BaseModel):
    provider: Provider
    created: bool  # True if a new record; False if an existing one was updated


router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/{system}/providers", response_model=IngestResponse, status_code=201)
def ingest_provider(system: SourceSystem, payload: dict[str, Any]) -> IngestResponse:
    try:
        adapter = get_adapter(system)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    incoming = adapter.to_provider(payload)

    # Upsert on the external ID for this system, if present.
    ext_id = incoming.external_ids.get(system.value)
    existing = (
        store.providers.find_by_external(system.value, ext_id) if ext_id else None
    )
    if existing:
        updated = incoming.model_copy(update={"id": existing.id})
        store.providers.add(updated)
        return IngestResponse(provider=updated, created=False)

    store.providers.add(incoming)
    return IngestResponse(provider=incoming, created=True)

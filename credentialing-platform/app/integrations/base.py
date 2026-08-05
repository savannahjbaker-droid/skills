"""Inbound integration adapters.

ATS, EMR, and Salesforce each describe a provider differently. An adapter's one
job is to map that system's payload onto the canonical `Provider`, including the
external ID that lets us upsert rather than duplicate. This is the "eliminate
manual data transfer" boundary: systems push their native shape; the platform
normalizes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import License, Provider, SourceSystem


class InboundAdapter(ABC):
    #: Which system this adapter ingests from.
    system: SourceSystem
    #: Key in the payload holding this system's provider ID.
    external_id_field: str

    @abstractmethod
    def to_provider(self, payload: dict[str, Any]) -> Provider:
        """Normalize a system-native payload into a canonical Provider."""
        raise NotImplementedError

    def _external_ids(self, payload: dict[str, Any]) -> dict[str, str]:
        ext = payload.get(self.external_id_field)
        return {self.system.value: str(ext)} if ext is not None else {}


def _licenses(raw: Any) -> list[License]:
    """Best-effort parse of a list of {state, number, expiration} dicts."""
    out: list[License] = []
    for item in raw or []:
        if isinstance(item, dict) and item.get("state") and item.get("number"):
            out.append(
                License(
                    state=item["state"],
                    number=str(item["number"]),
                    expiration=item.get("expiration"),
                )
            )
    return out

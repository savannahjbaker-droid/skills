"""NPPES connector — real-shaped against the public NPI Registry API.

NPPES is the authoritative source for National Provider Identifiers. Its API is
public (no auth) and documented at:
https://npiregistry.cms.hhs.gov/api/  (version 2.1)

This connector issues the real request shape. The `httpx.AsyncClient` is
injectable so tests can supply a `MockTransport` and run with no network.
"""

from __future__ import annotations

from typing import Optional

import httpx

from ..models import (
    Provider,
    VerificationResult,
    VerificationSource,
    VerificationStatus,
)
from .base import PrimarySourceConnector

NPPES_BASE_URL = "https://npiregistry.cms.hhs.gov/api/"


class NPPESConnector(PrimarySourceConnector):
    source = VerificationSource.NPPES

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        base_url: str = NPPES_BASE_URL,
    ) -> None:
        self._client = client
        self._base_url = base_url

    async def verify(self, provider: Provider) -> VerificationResult:
        if not provider.npi:
            return VerificationResult(
                source=self.source,
                status=VerificationStatus.NOT_FOUND,
                error="Provider has no NPI to verify against NPPES.",
            )

        params = {"version": "2.1", "number": provider.npi}
        client = self._client or httpx.AsyncClient(timeout=15.0)
        owns_client = self._client is None
        try:
            resp = await client.get(self._base_url, params=params)
            resp.raise_for_status()
            payload = resp.json()
        finally:
            if owns_client:
                await client.aclose()

        results = payload.get("results") or []
        if not results:
            return VerificationResult(
                source=self.source,
                status=VerificationStatus.NOT_FOUND,
                data={"npi": provider.npi},
            )

        record = results[0]
        basic = record.get("basic", {})
        found = {
            "npi": str(record.get("number", provider.npi)),
            "first_name": basic.get("first_name", ""),
            "last_name": basic.get("last_name", ""),
            "credential": basic.get("credential", ""),
            "status": basic.get("status", ""),
        }

        discrepancies = _diff_names(provider, found)
        status = (
            VerificationStatus.VERIFIED
            if not discrepancies
            else VerificationStatus.DISCREPANCY
        )
        return VerificationResult(
            source=self.source,
            status=status,
            discrepancies=discrepancies,
            data=found,
        )


def _diff_names(provider: Provider, found: dict) -> list[str]:
    """Compare submitted identity against the NPPES record (case-insensitive)."""
    discrepancies: list[str] = []
    if found.get("last_name") and found["last_name"].lower() != provider.last_name.lower():
        discrepancies.append(
            f"last_name: submitted '{provider.last_name}' vs NPPES '{found['last_name']}'"
        )
    if (
        found.get("first_name")
        and found["first_name"].lower() != provider.first_name.lower()
    ):
        discrepancies.append(
            f"first_name: submitted '{provider.first_name}' vs NPPES '{found['first_name']}'"
        )
    return discrepancies

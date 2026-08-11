"""InNetwork.ai (Credflow) connector — real, matches the documented v1 API.

    POST {base}/providers/status
    body:  {"npi": "1234567893", "payer": "aetna"}
    200:   {"success": true, "data": {"npi": ..., "payer": ..., "status": "active", "entry": [...]}}

Auth is a bearer API key issued in the InNetwork.ai settings page. Use a
*sandbox* key for testing (synthetic data, no payer quota). The `httpx.AsyncClient`
and settings are injectable so tests run with no network.

If a real call returns 401, the key header may differ from `Authorization:
Bearer` — check the docs' Authorize section and adjust `_auth_headers`.
"""

from __future__ import annotations

from typing import Optional

import httpx

from ..config import InNetworkSettings
from ..models import Provider, VerificationSource
from .base import ENROLLED, NOT_ENROLLED, PENDING, ClearinghouseConnector


def _payer_key(payer: str) -> str:
    """InNetwork expects a lowercase payer identifier (e.g. 'aetna')."""
    return payer.strip().lower().replace(" ", "_")


def _map_status(raw: str) -> str:
    """Map InNetwork's status onto our enrollment vocabulary."""
    s = (raw or "").strip().lower()
    if s in ("active", "in_network", "in-network", "enrolled", "participating"):
        return ENROLLED
    if s in ("pending", "in_process", "in-process"):
        return PENDING
    return s or NOT_ENROLLED


class InNetworkConnector(ClearinghouseConnector):
    source = VerificationSource.INNETWORK

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        settings: Optional[InNetworkSettings] = None,
    ) -> None:
        self._client = client
        self._settings = settings or InNetworkSettings.from_env()

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._settings.api_key}"}

    async def check_enrollment(
        self, provider: Provider, payers: list[str]
    ) -> dict[str, str]:
        if not self._settings.configured and self._client is None:
            raise RuntimeError(
                "InNetwork.ai API key not configured (set INNETWORK_API_KEY)."
            )
        client = self._client or httpx.AsyncClient(timeout=20.0)
        owns_client = self._client is None
        base = self._settings.base_url
        try:
            statuses: dict[str, str] = {}
            for payer in payers:
                resp = await client.post(
                    f"{base}/providers/status",
                    json={"npi": provider.npi, "payer": _payer_key(payer)},
                    headers=self._auth_headers(),
                )
                resp.raise_for_status()
                body = resp.json()
                data = body.get("data") or {}
                statuses[payer] = _map_status(data.get("status", ""))
            return statuses
        finally:
            if owns_client:
                await client.aclose()

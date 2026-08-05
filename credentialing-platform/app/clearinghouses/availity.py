"""Availity connector — real-shaped against the Availity REST API.

Availity authenticates with OAuth2 client-credentials and exposes REST
endpoints under https://api.availity.com/availity/ (see
https://developer.availity.com/). This connector issues the real request shape:
fetch a bearer token, then query enrollment per payer.

Auth requires credentials, so the connector is only *live* when configured
(env: AVAILITY_CLIENT_ID / AVAILITY_CLIENT_SECRET) or when a settings object and
`httpx.AsyncClient` are injected (as tests do). Unconfigured, it raises a clear
message that the base class turns into an ERROR result — mirroring reality: you
must onboard with Availity before it can verify anything.
"""

from __future__ import annotations

from typing import Optional

import httpx

from ..config import AvailitySettings
from ..models import (
    EdiAcknowledgment,
    EdiTransaction,
    EnrollmentSubmission,
    Provider,
    VerificationSource,
)
from .base import ENROLLED, NOT_ENROLLED, ClearinghouseConnector


class AvailityConnector(ClearinghouseConnector):
    source = VerificationSource.AVAILITY

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        settings: Optional[AvailitySettings] = None,
    ) -> None:
        self._client = client
        self._settings = settings or AvailitySettings.from_env()

    async def check_enrollment(
        self, provider: Provider, payers: list[str]
    ) -> dict[str, str]:
        if not self._settings.configured and self._client is None:
            raise RuntimeError(
                "Availity credentials not configured "
                "(set AVAILITY_CLIENT_ID / AVAILITY_CLIENT_SECRET)."
            )

        client = self._client or httpx.AsyncClient(timeout=20.0)
        owns_client = self._client is None
        base = self._settings.base_url
        try:
            token = await self._token(client, base)
            headers = {"Authorization": f"Bearer {token}"}
            statuses: dict[str, str] = {}
            for payer in payers:
                resp = await client.get(
                    f"{base}/v1/enrollments",
                    params={"npi": provider.npi, "payer": payer},
                    headers=headers,
                )
                resp.raise_for_status()
                body = resp.json()
                statuses[payer] = body.get("status", NOT_ENROLLED)
            return statuses
        finally:
            if owns_client:
                await client.aclose()

    async def submit_enrollment(
        self, provider: Provider, payer: str
    ) -> EnrollmentSubmission:
        if not self._settings.configured and self._client is None:
            raise RuntimeError(
                "Availity credentials not configured "
                "(set AVAILITY_CLIENT_ID / AVAILITY_CLIENT_SECRET)."
            )
        client = self._client or httpx.AsyncClient(timeout=20.0)
        owns_client = self._client is None
        base = self._settings.base_url
        try:
            token = await self._token(client, base)
            resp = await client.post(
                f"{base}/v1/transaction-enrollments",
                headers={"Authorization": f"Bearer {token}"},
                json={"npi": provider.npi, "payer": payer},
            )
            resp.raise_for_status()
            body = resp.json()
            return EnrollmentSubmission(
                clearinghouse=self.source,
                payer=payer,
                submitted=True,
                tracking_id=body.get("id"),
                message=body.get("status", "submitted"),
            )
        finally:
            if owns_client:
                await client.aclose()

    async def submit_edi(self, transaction: EdiTransaction) -> EdiAcknowledgment:
        if not self._settings.configured and self._client is None:
            raise RuntimeError(
                "Availity credentials not configured "
                "(set AVAILITY_CLIENT_ID / AVAILITY_CLIENT_SECRET)."
            )
        client = self._client or httpx.AsyncClient(timeout=20.0)
        owns_client = self._client is None
        base = self._settings.base_url
        try:
            token = await self._token(client, base)
            resp = await client.post(
                f"{base}/v1/x12",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/edi-x12",
                },
                content=transaction.x12,
            )
            resp.raise_for_status()
            body = resp.json()
            return EdiAcknowledgment(
                accepted=body.get("status", "A") in ("A", "E"),
                ack_type=body.get("ack_type", "999"),
                status_code=body.get("status", "A"),
                control_number=transaction.control_number,
                messages=body.get("messages", []),
            )
        finally:
            if owns_client:
                await client.aclose()

    async def _token(self, client: httpx.AsyncClient, base: str) -> str:
        resp = await client.post(
            f"{base}/v1/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self._settings.client_id,
                "client_secret": self._settings.client_secret,
                "scope": "hipaa",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

"""Verification orchestration.

Runs every registered connector concurrently for a provider, converts transport
failures into ERROR results (so one flaky source never sinks the whole case),
and aggregates into a `CredentialingCase` whose status is derived from the mix
of results.
"""

from __future__ import annotations

import asyncio
from typing import Optional, Sequence

from ..clearinghouses import default_clearinghouses
from ..connectors import PrimarySourceConnector, default_registry
from ..models import (
    CredentialingCase,
    Provider,
    VerificationResult,
    VerificationStatus,
)


def full_registry() -> list[PrimarySourceConnector]:
    """The complete set run for a credentialing case: PSV sources **and**
    clearinghouse payer-enrollment checks."""
    return [*default_registry(), *default_clearinghouses()]


async def _safe_verify(
    connector: PrimarySourceConnector, provider: Provider
) -> VerificationResult:
    try:
        return await connector.verify(provider)
    except Exception as exc:  # noqa: BLE001 - deliberately broad; isolate one source
        return VerificationResult(
            source=connector.source,
            status=VerificationStatus.ERROR,
            error=f"{type(exc).__name__}: {exc}",
        )


async def run_verifications(
    provider: Provider,
    connectors: Optional[Sequence[PrimarySourceConnector]] = None,
) -> CredentialingCase:
    """Verify `provider` across all sources concurrently and build a case.

    Defaults to the full registry (PSV sources + clearinghouse payer enrollment).
    Pass an explicit `connectors` list to scope the run (e.g. clearinghouses only).
    """
    connectors = list(connectors) if connectors is not None else full_registry()
    results = await asyncio.gather(
        *(_safe_verify(c, provider) for c in connectors)
    )
    case = CredentialingCase(provider_id=provider.id, results=list(results))
    case.recompute_status()
    return case

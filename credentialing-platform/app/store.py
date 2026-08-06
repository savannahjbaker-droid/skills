"""In-memory data store.

An intentionally simple repository so the MVP runs with zero infrastructure.
Swapping this for Postgres/DynamoDB later means implementing the same small
surface (`add`, `get`, `list`, `update`) behind these two repositories.
"""

from __future__ import annotations

from typing import Optional

from .models import CredentialingCase, Provider, WebhookSubscription


class ProviderRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, Provider] = {}
        # Secondary index so ATS/EMR/Salesforce upserts find existing records.
        self._by_external: dict[tuple[str, str], str] = {}

    def add(self, provider: Provider) -> Provider:
        self._by_id[provider.id] = provider
        for system, ext_id in provider.external_ids.items():
            self._by_external[(system, ext_id)] = provider.id
        return provider

    def get(self, provider_id: str) -> Optional[Provider]:
        return self._by_id.get(provider_id)

    def find_by_external(self, system: str, ext_id: str) -> Optional[Provider]:
        pid = self._by_external.get((system, ext_id))
        return self._by_id.get(pid) if pid else None

    def list(self) -> list[Provider]:
        return list(self._by_id.values())


class CaseRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, CredentialingCase] = {}

    def add(self, case: CredentialingCase) -> CredentialingCase:
        self._by_id[case.id] = case
        return case

    def get(self, case_id: str) -> Optional[CredentialingCase]:
        return self._by_id.get(case_id)

    def list(self) -> list[CredentialingCase]:
        return list(self._by_id.values())


class WebhookRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, WebhookSubscription] = {}

    def add(self, sub: WebhookSubscription) -> WebhookSubscription:
        self._by_id[sub.id] = sub
        return sub

    def list(self) -> list[WebhookSubscription]:
        return list(self._by_id.values())

    def matching(self, event: str) -> list[WebhookSubscription]:
        return [s for s in self._by_id.values() if s.wants(event)]


class ControlNumbers:
    """Monotonic source of X12 interchange control numbers (unique per process)."""

    def __init__(self) -> None:
        self._n = 0

    def next(self) -> int:
        self._n += 1
        return self._n


# Module-level singletons used by the app. Tests reset these via `reset()`.
providers = ProviderRepository()
cases = CaseRepository()
webhooks = WebhookRepository()
control_numbers = ControlNumbers()


def reset() -> None:
    """Clear all state. Used by tests for isolation."""
    global providers, cases, webhooks, control_numbers
    providers = ProviderRepository()
    cases = CaseRepository()
    webhooks = WebhookRepository()
    control_numbers = ControlNumbers()

"""Primary source verification (PSV) connector contract.

Every external source (NPPES, CAQH, PECOS, a state board, or any of the 2000+
PSV databases) implements this one small interface. The orchestrator treats
them uniformly, so adding a new source is: subclass, implement `verify`,
register. Nothing else in the system changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Provider, VerificationResult, VerificationSource


class PrimarySourceConnector(ABC):
    #: Which source this connector speaks to.
    source: VerificationSource

    @abstractmethod
    async def verify(self, provider: Provider) -> VerificationResult:
        """Query the source and return a normalized verification result.

        Implementations must not raise for expected outcomes (not found,
        discrepancy); they encode those in the returned result's `status`.
        Only unexpected transport failures should raise, and the orchestrator
        converts those into an ERROR result.
        """
        raise NotImplementedError

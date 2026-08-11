"""Clearinghouse registry.

Like the PSV connector registry, this is the single place that knows which
clearinghouses exist. Adding one is a one-line change here.
"""

from __future__ import annotations

from ..models import VerificationSource
from .availity import AvailityConnector
from .base import ClearinghouseConnector
from .innetwork import InNetworkConnector
from .mocked import (
    ChangeHealthcareConnector,
    OfficeAllyConnector,
    WaystarConnector,
)


def get_clearinghouse(source: VerificationSource) -> ClearinghouseConnector:
    """Look up a single clearinghouse connector by its source enum."""
    for ch in default_clearinghouses():
        if ch.source == source:
            return ch
    raise KeyError(f"No clearinghouse registered for '{source}'")


def default_clearinghouses() -> list[ClearinghouseConnector]:
    """Clearinghouses run for a standard credentialing case.

    Availity is real-shaped and only verifies when configured; unconfigured it
    reports an ERROR result (it can't call the live API without credentials).
    The others are mocked so the payer-enrollment flow is demonstrable.
    """
    return [
        AvailityConnector(),
        ChangeHealthcareConnector(),
        WaystarConnector(),
        OfficeAllyConnector(),
    ]


__all__ = [
    "ClearinghouseConnector",
    "AvailityConnector",
    "ChangeHealthcareConnector",
    "WaystarConnector",
    "OfficeAllyConnector",
    "InNetworkConnector",
    "default_clearinghouses",
    "get_clearinghouse",
]

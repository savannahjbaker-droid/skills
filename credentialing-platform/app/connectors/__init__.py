"""Connector registry.

The registry is the single place that knows which sources exist. The
orchestrator asks it for the set of connectors to run; adding a source to the
platform means adding one line here.
"""

from __future__ import annotations

from .base import PrimarySourceConnector
from .mocked import CAQHConnector, PECOSConnector, StateBoardConnector
from .nppes import NPPESConnector


def default_registry() -> list[PrimarySourceConnector]:
    """The connectors run for a standard credentialing case."""
    return [
        NPPESConnector(),
        CAQHConnector(),
        PECOSConnector(),
        StateBoardConnector(),
    ]


__all__ = [
    "PrimarySourceConnector",
    "NPPESConnector",
    "CAQHConnector",
    "PECOSConnector",
    "StateBoardConnector",
    "default_registry",
]

"""Runtime configuration.

Secrets/credentials for external services are read from the environment so
nothing sensitive is ever committed. Connectors that need auth accept a settings
object (injectable for tests) rather than reaching for env vars directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AvailitySettings:
    """Availity uses OAuth2 client-credentials. Register an app in the Availity
    developer portal to obtain these. https://developer.availity.com/
    """

    client_id: str | None = None
    client_secret: str | None = None
    base_url: str = "https://api.availity.com/availity"

    @classmethod
    def from_env(cls) -> "AvailitySettings":
        return cls(
            client_id=os.getenv("AVAILITY_CLIENT_ID"),
            client_secret=os.getenv("AVAILITY_CLIENT_SECRET"),
            base_url=os.getenv("AVAILITY_BASE_URL", cls.base_url),
        )

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

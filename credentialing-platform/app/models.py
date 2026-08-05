"""Core domain models for the credentialing platform.

These Pydantic models define the canonical, source-agnostic representation of a
healthcare provider and the artifacts produced while credentialing them. Every
inbound integration (ATS/EMR/Salesforce) is normalized into a `Provider`, and
every primary source verification produces a `VerificationResult`.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SourceSystem(str, Enum):
    """Systems of record that feed provider data into the platform."""

    ATS = "ats"
    EMR = "emr"
    SALESFORCE = "salesforce"
    MANUAL = "manual"
    API = "api"


class VerificationSource(str, Enum):
    """Sources we can query for verification data.

    Two families share this enum because both produce a `VerificationResult`
    and run through the same orchestrator:
      * PSV sources verify identity / licensure / enrollment eligibility.
      * Clearinghouses verify *payer enrollment* — whether the provider can
        actually submit claims/eligibility to each payer they reach.
    """

    # --- Primary source verification (PSV) ---
    NPPES = "nppes"  # National Plan & Provider Enumeration System (NPI registry)
    CAQH = "caqh"  # Council for Affordable Quality Healthcare
    PECOS = "pecos"  # Provider Enrollment, Chain, and Ownership System (Medicare)
    STATE_BOARD = "state_board"  # State medical board license verification

    # --- Clearinghouses (payer connectivity / EDI enrollment) ---
    AVAILITY = "availity"
    CHANGE_HEALTHCARE = "change_healthcare"  # Optum / Change Healthcare
    WAYSTAR = "waystar"
    OFFICE_ALLY = "office_ally"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    DISCREPANCY = "discrepancy"  # source found, but data does not match
    NOT_FOUND = "not_found"
    ERROR = "error"


class CaseStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"  # every source verified cleanly
    ACTION_REQUIRED = "action_required"  # discrepancy / not-found needs human review


class License(BaseModel):
    state: str = Field(..., description="Two-letter US state code, e.g. 'CA'")
    number: str
    expiration: Optional[date] = None


class Provider(BaseModel):
    """Canonical provider record. All integrations normalize into this shape."""

    id: str = Field(default_factory=_uuid)
    npi: Optional[str] = Field(
        default=None, description="10-digit National Provider Identifier"
    )
    first_name: str
    last_name: str
    credential: Optional[str] = Field(
        default=None, description="e.g. 'MD', 'DO', 'NP', 'PA'"
    )
    specialty: Optional[str] = None
    licenses: list[License] = Field(default_factory=list)
    email: Optional[str] = None
    # Payers this provider should be enrolled with (checked via clearinghouses).
    # Empty means "use the clearinghouse's default national payer set".
    target_payers: list[str] = Field(default_factory=list)
    source_system: SourceSystem = SourceSystem.API
    # IDs of this provider in the external systems of record, keyed by system.
    external_ids: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class VerificationResult(BaseModel):
    source: VerificationSource
    status: VerificationStatus
    # Discrepancies as human-readable "field: expected vs found" strings.
    discrepancies: list[str] = Field(default_factory=list)
    # Raw-ish normalized data returned by the source, for audit/traceability.
    data: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=_now)
    error: Optional[str] = None


class CredentialingCase(BaseModel):
    """A credentialing workflow instance for one provider across all sources."""

    id: str = Field(default_factory=_uuid)
    provider_id: str
    status: CaseStatus = CaseStatus.PENDING
    results: list[VerificationResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    completed_at: Optional[datetime] = None

    def recompute_status(self) -> None:
        """Derive the overall case status from individual source results."""
        if not self.results:
            self.status = CaseStatus.PENDING
            return
        statuses = {r.status for r in self.results}
        if statuses <= {VerificationStatus.VERIFIED}:
            self.status = CaseStatus.COMPLETED
            self.completed_at = _now()
        elif statuses & {
            VerificationStatus.DISCREPANCY,
            VerificationStatus.NOT_FOUND,
            VerificationStatus.ERROR,
        }:
            self.status = CaseStatus.ACTION_REQUIRED
        else:
            self.status = CaseStatus.IN_PROGRESS

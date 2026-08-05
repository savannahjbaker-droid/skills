"""X12 270 (Health Care Eligibility Benefit Inquiry) builder.

Produces a structurally-valid 005010X279A1 270 inquiring whether a subscriber is
eligible with a payer, sent with the provider as the information receiver. In the
credentialing platform this doubles as a **post-enrollment connectivity probe**:
once a provider is EDI-enrolled with a payer (via a clearinghouse), a test 270
confirms the pipe is live before real transactions flow.
"""

from __future__ import annotations

from datetime import datetime

from ...models import EdiTransaction, EligibilitySubscriber, Provider
from .x12 import build_interchange, segment

SENDER_ID = "CREDPLATFORM"
VERSION = "005010X279A1"


def payer_id(payer: str) -> str:
    """Derive a stable payer interchange ID from a payer name (demo heuristic).

    Real integrations map payer names to the clearinghouse's payer ID list.
    """
    return "".join(ch for ch in payer.upper() if ch.isalnum())[:15] or "PAYER"


def build_270(
    provider: Provider,
    payer: str,
    subscriber: EligibilitySubscriber,
    control_number: int,
    now: datetime,
) -> EdiTransaction:
    pid = payer_id(payer)
    trace = f"{control_number:09d}"
    ccyymmdd = now.strftime("%Y%m%d")
    hhmm = now.strftime("%H%M")
    dob = subscriber.dob.strftime("%Y%m%d")

    # Transaction set: ST through SE. SE's count includes ST and SE themselves.
    body = [
        segment("ST", "270", "0001", VERSION),
        segment("BHT", "0022", "13", trace, ccyymmdd, hhmm),
        # 2000A Information Source (payer)
        segment("HL", "1", "", "20", "1"),
        segment("NM1", "PR", "2", payer, "", "", "", "", "PI", pid),
        # 2000B Information Receiver (provider)
        segment("HL", "2", "1", "21", "1"),
        segment(
            "NM1", "1P", "1", provider.last_name, provider.first_name,
            "", "", "", "XX", provider.npi or "",
        ),
        # 2000C Subscriber
        segment("HL", "3", "2", "22", "0"),
        segment("TRN", "1", trace, SENDER_ID),
        segment(
            "NM1", "IL", "1", subscriber.last_name, subscriber.first_name,
            "", "", "", "MI", subscriber.member_id,
        ),
        segment("DMG", "D8", dob),
        segment("DTP", "291", "D8", ccyymmdd),
        segment("EQ", "30"),  # 30 = health benefit plan coverage (general)
    ]
    body.append(segment("SE", len(body) + 1, "0001"))

    x12 = build_interchange(
        transaction_set="270",
        transaction_segments=body,
        sender_id=SENDER_ID,
        receiver_id=pid,
        control_number=control_number,
        now=now,
        functional_id_code="HS",
        version=VERSION,
    )
    return EdiTransaction(
        transaction_set="270", payer=payer, control_number=control_number, x12=x12
    )

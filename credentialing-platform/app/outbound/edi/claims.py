"""X12 837P (Health Care Claim: Professional) builder.

Produces a structurally-valid 005010X222A1 837P for a single provider/claim. Like
the 270 builder it shares the `x12.py` envelope and takes an injected control
number + timestamp, so output is deterministic and testable. Scoped to the common
path (one billing provider, self-subscriber, one claim, N service lines) — the
2000/2010/2300/2400 loop skeleton real payers expect.
"""

from __future__ import annotations

from datetime import datetime

from ...models import Claim, EdiTransaction, Provider
from .eligibility import payer_id
from .x12 import build_interchange, segment

SENDER_ID = "CREDPLATFORM"
VERSION = "005010X222A1"


def build_837p(
    provider: Provider,
    payer: str,
    claim: Claim,
    control_number: int,
    now: datetime,
) -> EdiTransaction:
    pid = payer_id(payer)
    trace = f"{control_number:09d}"
    ccyymmdd = now.strftime("%Y%m%d")
    hhmm = now.strftime("%H%M")
    sub = claim.subscriber

    body = [
        segment("ST", "837", "0001", VERSION),
        segment("BHT", "0019", "00", trace, ccyymmdd, hhmm, "CH"),
        # 1000A Submitter
        segment("NM1", "41", "2", "CREDENTIALING PLATFORM", "", "", "", "", "46", SENDER_ID),
        segment("PER", "IC", "CREDENTIALING PLATFORM", "TE", "8005551212"),
        # 1000B Receiver
        segment("NM1", "40", "2", payer, "", "", "", "", "46", pid),
        # 2000A Billing Provider
        segment("HL", "1", "", "20", "1"),
        # 2010AA Billing Provider name/NPI
        segment("NM1", "85", "1", provider.last_name, provider.first_name, "", "", "", "XX", provider.npi or ""),
        segment("N3", "1 MAIN ST"),
        segment("N4", "ANYTOWN", "CA", "900010000"),
        segment("REF", "EI", "000000000"),  # billing provider tax ID
        # 2000B Subscriber
        segment("HL", "2", "1", "22", "0"),
        segment("SBR", "P", "18", "", "", "", "", "", "", "CI"),
        # 2010BA Subscriber name
        segment("NM1", "IL", "1", sub.last_name, sub.first_name, "", "", "", "MI", sub.member_id),
        # 2010BB Payer
        segment("NM1", "PR", "2", payer, "", "", "", "", "PI", pid),
        # 2300 Claim
        segment(
            "CLM", claim.patient_control_number, f"{claim.total_charge:.2f}",
            "", "", "11:B:1", "Y", "A", "Y", "Y",
        ),
        segment("HI", f"ABK:{claim.diagnosis_codes[0]}"),
    ]

    # 2400 Service lines
    for i, line in enumerate(claim.lines, start=1):
        body.append(segment("LX", i))
        body.append(
            segment("SV1", f"HC:{line.procedure_code}", f"{line.charge:.2f}", "UN", line.units, "", "", "1")
        )
        body.append(segment("DTP", "472", "D8", ccyymmdd))

    body.append(segment("SE", len(body) + 1, "0001"))

    x12 = build_interchange(
        transaction_set="837",
        transaction_segments=body,
        sender_id=SENDER_ID,
        receiver_id=pid,
        control_number=control_number,
        now=now,
        functional_id_code="HC",
        version=VERSION,
    )
    return EdiTransaction(
        transaction_set="837", payer=payer, control_number=control_number, x12=x12
    )

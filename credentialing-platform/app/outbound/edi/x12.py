"""Minimal X12 5010 envelope construction.

Just enough to build a structurally-valid interchange: the ISA/IEA interchange
envelope and GS/GE functional-group envelope wrapped around one transaction set.
Separators follow the X12 convention encoded in ISA16 (component) and ISA11
(repetition); segment terminator is `~`, element separator `*`.

Everything time/counter-dependent is passed in, so output is deterministic and
testable.
"""

from __future__ import annotations

from datetime import datetime

ELEMENT = "*"
SEGMENT = "~"
REPETITION = "^"
COMPONENT = ":"


def segment(*elements: object) -> str:
    """Join elements into a segment (no terminator; the joiner adds it)."""
    return ELEMENT.join("" if e is None else str(e) for e in elements)


def _pad(value: str, width: int) -> str:
    """Left-justify and space-pad (or truncate) to a fixed width, X12 style."""
    return value[:width].ljust(width)


def isa_segment(
    sender_id: str,
    receiver_id: str,
    control_number: int,
    now: datetime,
    usage: str = "T",  # T=test, P=production
) -> str:
    return segment(
        "ISA",
        "00",
        _pad("", 10),
        "00",
        _pad("", 10),
        "ZZ",
        _pad(sender_id, 15),
        "ZZ",
        _pad(receiver_id, 15),
        now.strftime("%y%m%d"),
        now.strftime("%H%M"),
        REPETITION,
        "00501",
        f"{control_number:09d}",
        "0",
        usage,
        COMPONENT,
    )


def build_interchange(
    transaction_set: str,
    transaction_segments: list[str],
    sender_id: str,
    receiver_id: str,
    control_number: int,
    now: datetime,
    functional_id_code: str,  # e.g. "HS" for 270 eligibility inquiry
    version: str,  # e.g. "005010X279A1"
    usage: str = "T",
) -> str:
    """Wrap `transaction_segments` (ST..SE) in GS/GE and ISA/IEA envelopes."""
    ctrl = f"{control_number:09d}"
    gs = segment(
        "GS",
        functional_id_code,
        sender_id,
        receiver_id,
        now.strftime("%Y%m%d"),
        now.strftime("%H%M"),
        control_number,
        "X",
        version,
    )
    ge = segment("GE", "1", control_number)
    isa = isa_segment(sender_id, receiver_id, control_number, now, usage)
    iea = segment("IEA", "1", ctrl)

    parts = [isa, gs, *transaction_segments, ge, iea]
    return SEGMENT.join(parts) + SEGMENT

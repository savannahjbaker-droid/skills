from datetime import date, datetime, timezone

from app.models import EligibilitySubscriber, Provider
from app.outbound.edi import build_270
from app.outbound.edi.x12 import ELEMENT, SEGMENT

NOW = datetime(2026, 8, 5, 14, 30, tzinfo=timezone.utc)


def _segments(x12: str) -> list[str]:
    return [s for s in x12.split(SEGMENT) if s]


def test_270_envelope_is_well_formed():
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    txn = build_270(provider, "Aetna", EligibilitySubscriber(), 42, NOW)
    segs = _segments(txn.x12)

    # Interchange envelope pairing.
    assert segs[0].startswith("ISA" + ELEMENT)
    assert segs[1].startswith("GS" + ELEMENT)
    assert segs[-1].startswith("IEA" + ELEMENT)
    assert segs[-2].startswith("GE" + ELEMENT)

    # ISA13 interchange control number is 9-digit zero-padded and matches IEA02.
    isa = segs[0].split(ELEMENT)
    assert isa[13] == "000000042"
    assert segs[-1].split(ELEMENT)[2] == "000000042"


def test_270_se_segment_count_is_accurate():
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    txn = build_270(provider, "Aetna", EligibilitySubscriber(), 1, NOW)
    segs = _segments(txn.x12)

    st_index = next(i for i, s in enumerate(segs) if s.startswith("ST" + ELEMENT))
    se_index = next(i for i, s in enumerate(segs) if s.startswith("SE" + ELEMENT))
    transaction_segments = segs[st_index : se_index + 1]

    se_count = int(segs[se_index].split(ELEMENT)[1])
    assert se_count == len(transaction_segments)


def test_270_carries_provider_npi_and_subscriber():
    provider = Provider(npi="1999999984", first_name="Ada", last_name="Byron")
    sub = EligibilitySubscriber(
        member_id="M123", first_name="Pat", last_name="Doe", dob=date(1985, 6, 1)
    )
    txn = build_270(provider, "Cigna", sub, 7, NOW)

    assert "1999999984" in txn.x12  # provider NPI in NM1*1P
    assert "M123" in txn.x12  # subscriber member id in NM1*IL
    assert "19850601" in txn.x12  # subscriber DOB in DMG
    assert txn.transaction_set == "270"
    assert txn.payer == "Cigna"

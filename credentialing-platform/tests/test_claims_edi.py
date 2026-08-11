from datetime import datetime, timezone

from app.models import Claim, ClaimLine, Provider
from app.outbound.edi import build_837p
from app.outbound.edi.x12 import ELEMENT, SEGMENT

NOW = datetime(2026, 8, 5, 14, 30, tzinfo=timezone.utc)


def _segments(x12: str) -> list[str]:
    return [s for s in x12.split(SEGMENT) if s]


def _claim() -> Claim:
    return Claim(
        patient_control_number="PCN42",
        diagnosis_codes=["E1165"],
        lines=[
            ClaimLine(procedure_code="99213", charge=150.0, units=1),
            ClaimLine(procedure_code="93000", charge=50.0, units=2),
        ],
    )


def test_837_envelope_and_functional_group():
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    txn = build_837p(provider, "Aetna", _claim(), 100, NOW)
    segs = _segments(txn.x12)

    assert segs[0].startswith("ISA" + ELEMENT)
    assert segs[1] == "GS*HC*CREDPLATFORM*AETNA*20260805*1430*100*X*005010X222A1"
    assert segs[2].startswith("ST*837*0001*005010X222A1")
    assert segs[-1] == "IEA*1*000000100"
    assert txn.transaction_set == "837"


def test_837_se_count_and_charges():
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    claim = _claim()
    txn = build_837p(provider, "Aetna", claim, 1, NOW)
    segs = _segments(txn.x12)

    st_i = next(i for i, s in enumerate(segs) if s.startswith("ST" + ELEMENT))
    se_i = next(i for i, s in enumerate(segs) if s.startswith("SE" + ELEMENT))
    assert int(segs[se_i].split(ELEMENT)[1]) == len(segs[st_i : se_i + 1])

    # total charge = 150*1 + 50*2 = 250.00, carried on CLM02
    clm = next(s for s in segs if s.startswith("CLM" + ELEMENT))
    assert clm.split(ELEMENT)[2] == "250.00"
    assert claim.total_charge == 250.0


def test_837_has_two_service_lines():
    provider = Provider(npi="1234567893", first_name="Jane", last_name="Smith")
    txn = build_837p(provider, "Aetna", _claim(), 1, NOW)
    segs = _segments(txn.x12)

    lx = [s for s in segs if s.startswith("LX" + ELEMENT)]
    sv1 = [s for s in segs if s.startswith("SV1" + ELEMENT)]
    assert len(lx) == 2 and len(sv1) == 2
    assert "HC:99213" in sv1[0]

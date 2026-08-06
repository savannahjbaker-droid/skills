from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_provider_with_case() -> tuple[str, str]:
    provider = client.post(
        "/providers",
        json={
            "first_name": "Jane", "last_name": "Smith", "npi": "1234567893",
            "external_ids": {"salesforce": "003xx", "ats": "C-100"},
        },
    ).json()
    case = client.post(f"/providers/{provider['id']}/payer-enrollment").json()
    return provider["id"], case["id"]


def test_push_case_returns_receipts_per_system():
    _, case_id = _make_provider_with_case()
    resp = client.post(f"/cases/{case_id}/push")
    assert resp.status_code == 200
    receipts = {r["system"]: r["status"] for r in resp.json()["receipts"]}
    assert receipts["salesforce"] == "accepted"
    assert receipts["ats"] == "accepted"
    assert receipts["emr"] == "skipped"


def test_push_unknown_case_404():
    assert client.post("/cases/nope/push").status_code == 404


def test_enrollment_submission_endpoint():
    provider_id, _ = _make_provider_with_case()
    resp = client.post(
        f"/providers/{provider_id}/enrollment-submissions",
        json={"payer": "Aetna", "clearinghouse": "change_healthcare"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["submitted"] is True
    assert body["payer"] == "Aetna"


def test_eligibility_endpoint_returns_edi_and_ack():
    provider_id, _ = _make_provider_with_case()
    resp = client.post(
        f"/providers/{provider_id}/eligibility",
        json={"payer": "Aetna", "clearinghouse": "waystar"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["transaction"]["transaction_set"] == "270"
    assert body["transaction"]["x12"].startswith("ISA*")
    assert body["acknowledgment"]["accepted"] is True


def test_claims_endpoint_builds_and_submits_837():
    provider_id, _ = _make_provider_with_case()
    resp = client.post(
        f"/providers/{provider_id}/claims",
        json={
            "payer": "Aetna",
            "clearinghouse": "change_healthcare",
            "claim": {
                "patient_control_number": "PCN9",
                "diagnosis_codes": ["E1165"],
                "lines": [{"procedure_code": "99213", "charge": 150.0, "units": 1}],
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["transaction"]["transaction_set"] == "837"
    assert "ST*837*" in body["transaction"]["x12"]
    assert body["acknowledgment"]["accepted"] is True


def test_verify_auto_push_runs_push_path():
    # With no webhook subscribers, emit() is a no-op (no network). This exercises
    # the auto_push branch end to end and confirms it still returns the case.
    # Webhook *delivery* is covered network-free in test_webhooks.py.
    provider = client.post(
        "/providers",
        json={
            "first_name": "Jane", "last_name": "Smith", "npi": "1234567893",
            "external_ids": {"salesforce": "003xx"},
        },
    ).json()

    resp = client.post(f"/providers/{provider['id']}/verify?auto_push=true")
    assert resp.status_code == 200
    assert resp.json()["provider_id"] == provider["id"]

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_get_provider():
    resp = client.post(
        "/providers",
        json={"first_name": "Jane", "last_name": "Smith", "npi": "1234567893"},
    )
    assert resp.status_code == 201
    pid = resp.json()["id"]

    got = client.get(f"/providers/{pid}")
    assert got.status_code == 200
    assert got.json()["npi"] == "1234567893"


def test_get_missing_provider_404():
    assert client.get("/providers/nope").status_code == 404


def test_integration_ingest_upserts_on_external_id():
    payload = {
        "candidate_id": "C-100",
        "first_name": "Jane",
        "last_name": "Smith",
        "npi": "1234567893",
    }
    first = client.post("/integrations/ats/providers", json=payload)
    assert first.status_code == 201
    assert first.json()["created"] is True
    pid = first.json()["provider"]["id"]

    # Same candidate_id, updated specialty -> same provider id, created=False.
    payload["specialty"] = "Cardiology"
    second = client.post("/integrations/ats/providers", json=payload)
    assert second.json()["created"] is False
    assert second.json()["provider"]["id"] == pid
    assert second.json()["provider"]["specialty"] == "Cardiology"


def test_verify_flow_end_to_end(monkeypatch):
    # Force NPPES to report NOT_FOUND (no network) by giving the provider no NPI,
    # so the case lands in ACTION_REQUIRED deterministically.
    created = client.post(
        "/providers", json={"first_name": "Jane", "last_name": "Smith"}
    ).json()

    case = client.post(f"/providers/{created['id']}/verify")
    assert case.status_code == 200
    body = case.json()
    assert body["provider_id"] == created["id"]
    assert len(body["results"]) == 4  # nppes, caqh, pecos, state_board

    fetched = client.get(f"/cases/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]

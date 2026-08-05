# Credentialing Platform (MVP)

An **API-first** provider credentialing & primary source verification (PSV)
service — a slim, working prototype of the kind of platform that integrates
seamlessly with **ATS, EMR, and Salesforce**, connects directly to
**NPPES, CAQH, PECOS, and state medical boards**, and reaches payers through the
big **clearinghouses (Availity, Change Healthcare/Optum, Waystar, Office Ally)**
— so provider data never has to be re-keyed between systems.

This is an **MVP prototype**: a few core endpoints and a couple of real-shaped
connectors, structured so the remaining ~2000 PSV sources, clearinghouses, and
outbound integrations plug into the same interfaces without touching the core.

## What's real vs. mocked

| Piece | Status |
|-------|--------|
| REST API (providers, cases, integrations) | ✅ real, runnable |
| Verification orchestration (concurrent, fault-isolated) | ✅ real |
| **NPPES** connector | ✅ real-shaped — issues the actual public NPI Registry request; HTTP client injectable for offline tests |
| **Availity** clearinghouse connector | ✅ real-shaped — OAuth2 + REST enrollment request; live when configured, injectable for offline tests |
| CAQH / PECOS / state-board connectors | 🔶 mocked — real contract, deterministic stub data (require credentials/portal access to make live) |
| Change Healthcare / Waystar / Office Ally clearinghouses | 🔶 mocked — real contract, deterministic enrollment data |
| ATS / EMR / Salesforce inbound adapters | ✅ real normalization logic; endpoints accept native payloads |
| ATS / EMR / Salesforce **outbound** push-back | ✅ real mapping logic; mocked transport |
| **X12 270** EDI builder | ✅ real, deterministic 5010 envelope; validated in tests |
| Payer enrollment + EDI submission | 🔶 mocked (Availity real-shaped: enrollment + X12 endpoints) |
| Data store | 🔶 in-memory (swap for Postgres behind the same repo interface) |

## Quick start

```bash
cd credentialing-platform
pip install -r requirements.txt

# Run the API
uvicorn app.main:app --reload
# Interactive docs: http://localhost:8000/docs

# Run tests (no network required)
pytest -q
```

## Try it

```bash
# 1. Ingest a provider from an ATS in its native shape (upserts on candidate_id)
curl -s localhost:8000/integrations/ats/providers -H 'content-type: application/json' -d '{
  "candidate_id": "C-100", "npi": "1234567893",
  "first_name": "Jane", "last_name": "Smith", "credential": "MD",
  "licenses": [{"state": "CA", "number": "A12345"}]
}'

# 2. Run full verification: PSV sources + clearinghouse payer enrollment
curl -s -X POST localhost:8000/providers/<PROVIDER_ID>/verify

# 3. Inspect the credentialing case (identity, licensure, and payer enrollment)
curl -s localhost:8000/cases/<CASE_ID>

# Or check payer enrollment only (clearinghouses), e.g. for the enrollment team
curl -s -X POST localhost:8000/providers/<PROVIDER_ID>/payer-enrollment

# 4. Push the results back to the systems of record (no re-keying)
curl -s -X POST localhost:8000/cases/<CASE_ID>/push

# 5. Submit an X12 270 connectivity probe through a clearinghouse
curl -s localhost:8000/providers/<PROVIDER_ID>/eligibility \
  -H 'content-type: application/json' \
  -d '{"payer": "Aetna", "clearinghouse": "waystar"}'
```

## Architecture at a glance

```
                                   PSV sources: NPPES · CAQH · PECOS · State boards
  ATS / EMR / Salesforce           Clearinghouses: Availity · Change HC · Waystar · Office Ally
          │  (native payloads)                     ▲ │ (verify / enroll / submit X12)
          ▼                                         │ ▼
  ┌───────────────┐   canonical    ┌────────────────────────────┐
  │ InboundAdapter │ ─ Provider ──▶ │ Verification orchestrator  │
  └───────────────┘                └────────────────────────────┘
          ▲                                         │
          │  (push results back)                    ▼
  ┌────────────────┐  ◀── case ───────────── CredentialingCase
  │ OutboundAdapter│                                │
  └────────────────┘                          Provider / Case store
```

- **One canonical `Provider` model.** Every integration normalizes into it, so
  the core never learns a vendor's field names.
- **One `PrimarySourceConnector` interface.** Every source — a PSV database or a
  clearinghouse — implements the same `verify(provider) -> result`. The
  orchestrator runs them concurrently and isolates failures per source.
- **Clearinghouses** verify *payer enrollment* (can this provider bill each
  payer) rather than identity — and carry the outbound EDI submission methods.
- **Outbound closes the loop.** Results push back to ATS/EMR/Salesforce
  (`OutboundAdapter`, mirror of inbound), and enrollment + X12 EDI (270) submit
  through the clearinghouses.

See [`docs/`](./docs) for detail:
- [`docs/architecture.md`](docs/architecture.md) — components, data flow, scaling path
- [`docs/api.md`](docs/api.md) — endpoint reference
- [`docs/connectors.md`](docs/connectors.md) — adding a PSV source
- [`docs/clearinghouses.md`](docs/clearinghouses.md) — clearinghouses & payer enrollment
- [`docs/outbound.md`](docs/outbound.md) — push-back + EDI enrollment / X12 270 submission
- [`docs/integrations.md`](docs/integrations.md) — adding an ATS/EMR/CRM adapter

## Project layout

```
app/
  models.py              Canonical domain models (Provider, Case, results)
  store.py               In-memory repositories
  connectors/            PSV sources (base + NPPES + mocked CAQH/PECOS/board)
  clearinghouses/        Payer-enrollment + EDI submission (Availity + mocked CH/Waystar/OA)
  integrations/          Inbound adapters (ATS/EMR/Salesforce → Provider)
  outbound/              Outbound adapters (Provider/Case → systems) + X12 EDI builder
  services/verification.py   Concurrent, fault-isolated PSV orchestration
  services/outbound.py       Push-back + enrollment/EDI submission orchestration
  api/                   FastAPI routers
tests/                   Pytest suite (offline; NPPES via httpx MockTransport)
docs/                    Architecture & how-to docs
```

## Disclaimer

Prototype for demonstration. The mocked connectors return synthetic data and
must not be used for real credentialing decisions. Real PSV sources require the
appropriate agreements, credentials, and compliance controls (HIPAA, data
retention, audit logging) that are out of scope for this MVP.

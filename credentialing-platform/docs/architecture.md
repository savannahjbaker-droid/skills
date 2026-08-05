# Architecture

## Design principle: two narrow interfaces

The whole platform hangs off two small contracts. Everything vendor-specific
lives at the edges; the core only ever sees canonical types.

1. **`InboundAdapter`** (integrations) — maps a system-of-record payload onto
   the canonical `Provider`. One per source system (ATS, EMR, Salesforce, …).
2. **`PrimarySourceConnector`** (verification) — `verify(provider) -> VerificationResult`.
   One per PSV source (NPPES, CAQH, PECOS, state boards, … up to 2000+).

Because both sides speak only `Provider` / `VerificationResult`, adding a source
system or a PSV database never touches routing, orchestration, or storage.

## Components

```
                         ┌──────────────────────────────────────┐
  Systems of record  ─▶  │  POST /integrations/{system}/providers│
  (ATS/EMR/SFDC)         │        └─ InboundAdapter.to_provider  │
                         └──────────────┬───────────────────────┘
                                        ▼
                               ProviderRepository  (upsert on external_id)
                                        │
                         ┌──────────────▼───────────────────────┐
  Trigger verify     ─▶  │  POST /providers/{id}/verify          │
                         │        └─ run_verifications(provider) │
                         │             ├─ NPPESConnector  ──▶ NPI Registry
                         │             ├─ CAQHConnector   ──▶ CAQH ProView
                         │             ├─ PECOSConnector  ──▶ CMS PECOS
                         │             └─ StateBoard...   ──▶ state portals
                         └──────────────┬───────────────────────┘
                                        ▼
                              CredentialingCase (aggregated results + status)
                                        │
                                  CaseRepository
```

## Data flow

1. **Ingest.** A source system POSTs its native payload to
   `/integrations/{system}/providers`. The matching adapter normalizes it to a
   `Provider` and the store **upserts** on the system's external ID — repeated
   syncs update the same record instead of duplicating it. This is the
   "no manual re-keying between systems" boundary.
2. **Verify.** `POST /providers/{id}/verify` fans out to every registered
   connector **concurrently** (`asyncio.gather`). Each connector returns a
   normalized `VerificationResult`; a connector that raises is converted into an
   `ERROR` result so one flaky source can't sink the case.
3. **Aggregate.** Results roll up into a `CredentialingCase`. Status is derived:
   all `VERIFIED` → `COMPLETED`; any `DISCREPANCY`/`NOT_FOUND`/`ERROR` →
   `ACTION_REQUIRED` (human review).

## Status model

| Result status | Meaning |
|---------------|---------|
| `VERIFIED` | Source found the provider and data matched |
| `DISCREPANCY` | Source found the provider but a field mismatched |
| `NOT_FOUND` | Source has no matching record (or insufficient input) |
| `ERROR` | Transport/upstream failure (isolated, non-fatal) |

| Case status | Meaning |
|-------------|---------|
| `PENDING` | Created, no results yet |
| `IN_PROGRESS` | Some sources still pending |
| `COMPLETED` | Every source verified cleanly |
| `ACTION_REQUIRED` | At least one source needs human review |

## From MVP to production

The MVP deliberately keeps infrastructure at zero. The path to production
replaces implementations behind the existing interfaces:

- **Storage.** Swap `ProviderRepository`/`CaseRepository` (in-memory) for
  Postgres. The API only calls `add`/`get`/`list`/`find_by_external`.
- **Async at scale.** `POST /verify` runs inline today. For 2000+ sources and
  slow portals, move orchestration to a task queue (Celery/Arq/Temporal) and
  return a case in `IN_PROGRESS`, streaming results as connectors complete.
- **Connector concurrency & rate limits.** Add per-source retry, timeout, and
  rate-limit policy in a wrapper around `PrimarySourceConnector`.
- **Webhooks out.** Emit `case.completed` / `case.action_required` events back
  to the originating ATS/EMR/CRM to close the loop.
- **Compliance.** HIPAA-grade audit logging (every `VerificationResult`
  already carries `checked_at` + raw `data` for traceability), encryption at
  rest, PII access controls, and configurable data retention.
- **Identity matching.** Replace exact NPI/name matching with a scored
  entity-resolution step for providers without an NPI.
```

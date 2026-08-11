# Architecture

## Design principle: two narrow interfaces

The whole platform hangs off two small contracts. Everything vendor-specific
lives at the edges; the core only ever sees canonical types.

1. **`InboundAdapter`** (integrations) — maps a system-of-record payload onto
   the canonical `Provider`. One per source system (ATS, EMR, Salesforce, …).
2. **`PrimarySourceConnector`** (verification) — `verify(provider) -> VerificationResult`.
   One per source: a PSV database (NPPES, CAQH, PECOS, state boards, … up to
   2000+) **or** a clearinghouse (Availity, Change Healthcare/Optum, Waystar,
   Office Ally). Clearinghouses implement the same interface via
   `ClearinghouseConnector`, which verifies *payer enrollment* rather than
   identity — see [`clearinghouses.md`](clearinghouses.md).

Because both sides speak only `Provider` / `VerificationResult`, adding a source
system, a PSV database, or a clearinghouse never touches routing, orchestration,
or storage.

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
                         │   PSV:   ├─ NPPESConnector  ──▶ NPI Registry
                         │          ├─ CAQHConnector   ──▶ CAQH ProView
                         │          ├─ PECOSConnector  ──▶ CMS PECOS
                         │          └─ StateBoard...   ──▶ state portals
                         │   Clghs: ├─ AvailityConnector ─▶ Availity API
                         │          ├─ ChangeHealthcare  ─▶ Optum/CHC
                         │          ├─ Waystar           ─▶ Waystar API
                         │          └─ OfficeAlly        ─▶ Office Ally EDI
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
   connector **concurrently** (`asyncio.gather`) — PSV sources *and*
   clearinghouse payer-enrollment checks. Each connector returns a normalized
   `VerificationResult`; a connector that raises is converted into an `ERROR`
   result so one flaky source can't sink the case. `POST
   /providers/{id}/payer-enrollment` runs the clearinghouses only.
3. **Aggregate.** Results roll up into a `CredentialingCase`. Status is derived:
   all `VERIFIED` → `COMPLETED`; any `DISCREPANCY`/`NOT_FOUND`/`ERROR` →
   `ACTION_REQUIRED` (human review).
4. **Push back (outbound).** `POST /cases/{id}/push` maps the case into each
   system of record's native shape and writes it back (mirror of ingest), so
   the ATS/EMR/CRM reflects verified status with no re-keying. Enrollment and
   X12 EDI (270) submit back through the clearinghouses. See
   [`outbound.md`](outbound.md).

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
- **Push-back automation.** Outbound push is manual today (`POST
  /cases/{id}/push`). Auto-trigger it on `case.completed` and emit
  `case.action_required` webhooks to the originating ATS/EMR/CRM. Replace the
  mocked outbound `_transport` with the real system APIs and clearinghouse EDI
  endpoints.
- **Compliance.** HIPAA-grade audit logging (every `VerificationResult`
  already carries `checked_at` + raw `data` for traceability), encryption at
  rest, PII access controls, and configurable data retention.
- **Identity matching.** Replace exact NPI/name matching with a scored
  entity-resolution step for providers without an NPI.
```

# API Reference

Base URL (local): `http://localhost:8000`. Interactive docs at `/docs`
(Swagger) and `/redoc`. The full machine-readable spec is at `/openapi.json`.

## Meta

### `GET /health`
Liveness probe. → `{"status": "ok"}`

## Providers

### `POST /providers`
Create a provider directly via the API.

Body:
```json
{
  "npi": "1234567893",
  "first_name": "Jane",
  "last_name": "Smith",
  "credential": "MD",
  "specialty": "Cardiology",
  "email": "jane@example.com",
  "licenses": [{"state": "CA", "number": "A12345", "expiration": "2027-01-31"}]
}
```
→ `201` with the created `Provider` (server-assigned `id`).

### `GET /providers`
List all providers. → `200` `Provider[]`

### `GET /providers/{provider_id}`
Fetch one provider. → `200` `Provider` / `404`.

## Credentialing

### `POST /providers/{provider_id}/verify`
Run primary source verification across every registered connector
concurrently, persist a `CredentialingCase`, and return it.
→ `200` `CredentialingCase` / `404` if provider unknown.

```json
{
  "id": "…",
  "provider_id": "…",
  "status": "action_required",
  "results": [
    {"source": "nppes", "status": "verified", "discrepancies": [], "data": {…}},
    {"source": "caqh",  "status": "verified", "data": {…}},
    {"source": "pecos", "status": "verified", "data": {…}},
    {"source": "state_board", "status": "not_found", "error": "No licenses submitted to verify."}
  ]
}
```

### `GET /cases`
List all credentialing cases. → `200` `CredentialingCase[]`

### `GET /cases/{case_id}`
Fetch one case with all source results. → `200` / `404`.

## Integrations (inbound)

### `POST /integrations/{system}/providers`
Ingest a provider from a system of record in **that system's native shape**.
`{system}` ∈ `ats | emr | salesforce`. The matching adapter normalizes the
payload and **upserts** on the system's external ID.

→ `201` `{ "provider": Provider, "created": bool }`
(`created: false` means an existing record was updated.)

Example (ATS):
```json
{
  "candidate_id": "C-100",
  "npi": "1234567893",
  "first_name": "Jane",
  "last_name": "Smith",
  "credential": "MD",
  "licenses": [{"state": "CA", "number": "A12345"}]
}
```

See [`integrations.md`](integrations.md) for each system's field mapping.

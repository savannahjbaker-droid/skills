# Clearinghouse Integrations

Clearinghouses (Availity, Change Healthcare/Optum, Waystar, Office Ally, …) are
**payer connectivity hubs**: a single integration that reaches many payers for
EDI transactions. For credentialing, the relevant function is **payer
enrollment** — confirming a provider is enrolled so they can actually submit
claims / eligibility (270/271) to each payer. Credentialing an identity is only
half the job; a provider who isn't enrolled with a payer still can't bill it.

## How they fit the architecture

A clearinghouse verifies *payer enrollment*, a PSV source verifies
*identity/licensure* — but both produce a `VerificationResult` and run through
the same orchestrator. So `ClearinghouseConnector` **is a**
`PrimarySourceConnector` with payer-enrollment structure layered on:

```python
class ClearinghouseConnector(PrimarySourceConnector):
    async def check_enrollment(self, provider, payers) -> dict[str, str]:
        """{payer: 'enrolled' | 'not_enrolled' | 'pending'}"""
```

The base class turns that map into a `VerificationResult`:
- all payers `enrolled` → `VERIFIED`
- any gap → `DISCREPANCY`, one discrepancy line per payer, full map in `data.payer_enrollment`
- no NPI → `NOT_FOUND`; a transport/config failure → `ERROR` (isolated)

Which payers get checked: the provider's `target_payers`, or a default national
set (`Aetna, Cigna, UnitedHealthcare, Anthem BCBS, Humana`) when none are named.

## Included clearinghouses

| Connector | Clearinghouse | Status | Real integration |
|-----------|---------------|--------|------------------|
| `AvailityConnector` | Availity | **real-shaped** | OAuth2 client-credentials + REST (`api.availity.com/availity`). Live only when configured. |
| `ChangeHealthcareConnector` | Change Healthcare / Optum | mocked | Optum Medical Network REST / X12 EDI (270/271, 837) |
| `WaystarConnector` | Waystar | mocked | Waystar eligibility/claims API |
| `OfficeAllyConnector` | Office Ally | mocked | Office Ally SFTP/EDI feeds |

### Availity: the real-shaped example
`AvailityConnector` issues the real request shape — fetch a bearer token, then
query enrollment per payer. Its `httpx.AsyncClient` and `AvailitySettings` are
injectable, so `tests/test_clearinghouses.py` drives it with an
`httpx.MockTransport` and no network.

Configure it for live use with environment variables:
```bash
export AVAILITY_CLIENT_ID=...
export AVAILITY_CLIENT_SECRET=...
# optional: AVAILITY_BASE_URL (defaults to https://api.availity.com/availity)
```
Unconfigured, it returns an `ERROR` result explaining it needs credentials —
matching reality: you must onboard with Availity before it can verify anything.

## Outbound: enrollment & EDI submission

A clearinghouse is also the *transport* for outbound EDI, so the connectors
carry two more methods (mocked defaults in the base, real-shaped in Availity):

```python
async def submit_enrollment(self, provider, payer) -> EnrollmentSubmission  # payer EDI enrollment
async def submit_edi(self, transaction) -> EdiAcknowledgment                # X12 (e.g. 270) transport
```

See [`outbound.md`](outbound.md) for the flows and the X12 270 builder.

## Endpoints

- `POST /providers/{id}/verify` — **full** credentialing run: PSV **and**
  clearinghouse payer enrollment, aggregated into one case.
- `POST /providers/{id}/payer-enrollment` — clearinghouse-only run for the
  enrollment team, without re-running PSV.
- `POST /providers/{id}/enrollment-submissions` — submit payer enrollment (outbound).
- `POST /providers/{id}/eligibility` — build & submit an X12 270 (outbound).

## Adding a clearinghouse

Same three steps as any connector:

1. Add the value to `VerificationSource` in `app/models.py`.
2. Subclass `ClearinghouseConnector` in `app/clearinghouses/` and implement
   `check_enrollment`.
3. Register it in `default_clearinghouses()` (`app/clearinghouses/__init__.py`).

Nothing in the API, orchestration, or case logic changes.

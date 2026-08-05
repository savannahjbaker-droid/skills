# Primary Source Connectors

A connector is the platform's adapter to one PSV source. All connectors
implement a single method:

```python
class PrimarySourceConnector(ABC):
    source: VerificationSource
    async def verify(self, provider: Provider) -> VerificationResult: ...
```

The orchestrator (`app/services/verification.py`) runs every registered
connector concurrently and never lets one source's failure affect another.

> Clearinghouses (Availity, Change Healthcare/Optum, Waystar, Office Ally) are a
> sibling connector family built on this same interface but focused on **payer
> enrollment** rather than identity/licensure. See
> [`clearinghouses.md`](clearinghouses.md).

## Included connectors

| Connector | Source | Status | Real integration |
|-----------|--------|--------|------------------|
| `NPPESConnector` | NPPES / NPI Registry | **real-shaped** | Public JSON API `https://npiregistry.cms.hhs.gov/api/` (no auth) |
| `CAQHConnector` | CAQH ProView | mocked | CAQH ProView batch/SOAP API with org ID + authorized roster |
| `PECOSConnector` | Medicare PECOS | mocked | CMS PECOS enrollment API / Medicare data files |
| `StateBoardConnector` | State medical boards | mocked | Per-state portal / FSMB / state API |

### NPPES: the real-shaped example
`NPPESConnector` issues the actual NPI Registry request. Its `httpx.AsyncClient`
is injectable, so tests pass an `httpx.MockTransport` and run fully offline
(see `tests/test_nppes.py`). It returns:
- `VERIFIED` when the NPI resolves and submitted name matches,
- `DISCREPANCY` when it resolves but a name field differs,
- `NOT_FOUND` when the NPI has no record (or none was submitted).

## Adding a new PSV source

Adding the 5th — or 2000th — source is three steps and touches nothing else:

1. **Add the enum value** in `app/models.py`:
   ```python
   class VerificationSource(str, Enum):
       ...
       OIG_LEIE = "oig_leie"   # OIG exclusion list
   ```

2. **Write the connector** in `app/connectors/`:
   ```python
   class OIGConnector(PrimarySourceConnector):
       source = VerificationSource.OIG_LEIE

       async def verify(self, provider: Provider) -> VerificationResult:
           # ... query the source, normalize into VerificationResult ...
           return VerificationResult(source=self.source, status=..., data=...)
   ```
   Encode *expected* outcomes (not found, discrepancy) in `status` — don't
   raise. The orchestrator turns unexpected exceptions into `ERROR` results.

3. **Register it** in `app/connectors/__init__.py`:
   ```python
   def default_registry():
       return [NPPESConnector(), CAQHConnector(), PECOSConnector(),
               StateBoardConnector(), OIGConnector()]
   ```

That's it — the API, orchestration, aggregation, and case-status logic pick it
up automatically.

## Design notes for live sources

- **Auth/secrets** belong in the connector's constructor, injected from config —
  never hard-coded.
- **Timeouts & retries**: wrap slow portals; the orchestrator already isolates
  failures but per-source retry/backoff belongs in the connector.
- **Traceability**: always populate `VerificationResult.data` with the
  normalized source response; it's the audit trail for a credentialing decision.

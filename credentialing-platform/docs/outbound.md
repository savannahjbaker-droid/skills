# Outbound

Verification is only half the loop. Once a case is decided, results have to flow
*back out* — to the systems of record so staff see verified status without
re-keying, and to payers so the provider can actually transact. Three outbound
flows cover this, each the mirror of an inbound counterpart.

## 1. Push results back to systems of record

`OutboundSystemAdapter` is the inverse of `InboundAdapter`: it maps a
`CredentialingCase` *out* into each system's native update shape and writes it
back. Transport is mocked (`_transport`) — swap it for the real REST/SOAP/Bulk
API call.

`POST /cases/{case_id}/push` runs every adapter concurrently and returns a
`PushReceipt` per system:
- `accepted` — the system acknowledged the update (payload echoed for audit)
- `skipped` — the provider has no ID in that system, nothing to push
- `error` — the write failed (isolated; other systems still push)

Field mapping is system-idiomatic, e.g. Salesforce:

| Case field | → Salesforce |
|------------|--------------|
| `case.status` | `Credentialing_Status__c` |
| `case.completed_at` | `Last_Verified__c` |
| enrolled payers | `Payer_Enrollment__c` |

ATS (`credentialing_status`, `verified_sources`, `enrolled_payers`) and EMR
(`credential_status`, `npi_verified`, `billable_payers`) map analogously.

## 2. Submit payer enrollment through a clearinghouse

`POST /providers/{id}/enrollment-submissions` with `{payer, clearinghouse}`
submits an EDI/transaction enrollment request via the chosen clearinghouse and
returns an `EnrollmentSubmission` (tracking ID + status). This is what gets a
provider set up to send/receive EDI with a payer. Mocked for most
clearinghouses; **Availity is real-shaped** (`POST /v1/transaction-enrollments`).

## 3. Submit an X12 270 through a clearinghouse

`POST /providers/{id}/eligibility` with `{payer, clearinghouse, subscriber?}`
builds a real **X12 5010 270** (Health Care Eligibility Benefit Inquiry) and
submits it, returning both the generated EDI and the clearinghouse's
`EdiAcknowledgment` (999/TA1-style). In credentialing this is a **post-enrollment
connectivity probe**: after a provider is EDI-enrolled, a test 270 confirms the
pipe is live before real traffic flows.

The X12 builder (`app/outbound/edi/`) is deterministic — control number and
timestamp are injected — so output is testable:
- `ISA/GS … ST/SE … GE/IEA` envelopes with matching control numbers
- accurate `SE` segment count
- provider in `NM1*1P` (NPI, `XX` qualifier), subscriber in `NM1*IL`

```
ISA*00*          *00*          *ZZ*CREDPLATFORM   *ZZ*AETNA          *260805*0702*^*00501*000000001*0*T*:~
GS*HS*CREDPLATFORM*AETNA*20260805*0702*1*X*005010X279A1~
ST*270*0001*005010X279A1~
BHT*0022*13*000000001*20260805*0702~
HL*1**20*1~   NM1*PR*2*Aetna*****PI*AETNA~
HL*2*1*21*1~  NM1*1P*1*Smith*Jane****XX*1234567893~
HL*3*2*22*0~  TRN*1*000000001*CREDPLATFORM~
NM1*IL*1*SUBSCRIBER*TEST****MI*TESTMEMBER0~  DMG*D8*19700101~  DTP*291*D8*20260805~  EQ*30~
SE*13*0001~   GE*1*1~   IEA*1*000000001~
```

The 837 (claim) and other transaction sets plug into the same `x12.py`
envelope + `submit_edi` transport — add a builder alongside `eligibility.py`.

## Where submission lives

Clearinghouse connectors carry the outbound EDI methods, since a clearinghouse
is both the enrollment-status source *and* the EDI transport:

```python
class ClearinghouseConnector(PrimarySourceConnector):
    async def check_enrollment(self, provider, payers) -> dict[str, str]: ...   # inbound
    async def submit_enrollment(self, provider, payer) -> EnrollmentSubmission: ...  # outbound
    async def submit_edi(self, transaction) -> EdiAcknowledgment: ...                # outbound
```

Base gives mocked-accepted defaults; `AvailityConnector` overrides all three
real-shaped.

# Inbound Integrations

An integration adapter maps one system-of-record's provider payload onto the
canonical `Provider`. This is how the platform "eliminates manual data transfer
between systems": each system pushes its own native shape and the adapter
normalizes it — nobody re-keys data.

```python
class InboundAdapter(ABC):
    system: SourceSystem            # ats | emr | salesforce
    external_id_field: str          # key in the payload holding this system's ID
    def to_provider(self, payload: dict) -> Provider: ...
```

The ingest endpoint (`POST /integrations/{system}/providers`) looks up the
adapter, normalizes, and **upserts** on `external_ids[system]` so repeat syncs
update rather than duplicate.

## Included adapters & field mappings

### ATS (`candidate_id`)
Candidate-centric fields, mostly flat.

| Payload field | → Provider |
|---------------|-----------|
| `candidate_id` | `external_ids["ats"]` |
| `npi` | `npi` |
| `first_name` / `last_name` | `first_name` / `last_name` |
| `credential`, `specialty`, `email` | same |
| `licenses[]` `{state, number, expiration}` | `licenses` |

### EMR (`provider_id`)
Clinical directory shape; names often nested (`given`/`family`).

| Payload field | → Provider |
|---------------|-----------|
| `provider_id` | `external_ids["emr"]` |
| `name.given` / `name.family` | `first_name` / `last_name` |
| `primary_specialty` (or `specialty`) | `specialty` |
| `contact_email` (or `email`) | `email` |

### Salesforce (`Id`)
Contact object with custom `__c` fields.

| Payload field | → Provider |
|---------------|-----------|
| `Id` | `external_ids["salesforce"]` |
| `FirstName` / `LastName` | `first_name` / `last_name` |
| `NPI__c` | `npi` |
| `Specialty__c`, `Credential__c` | `specialty`, `credential` |
| `Email` | `email` |

## Adding a new system of record

1. Subclass `InboundAdapter` in `app/integrations/adapters.py`, set `system`
   and `external_id_field`, and implement `to_provider`.
2. Register it in the `ADAPTERS` dict.
3. Add the value to `SourceSystem` in `app/models.py` if it's a new system.

The endpoint and upsert logic work unchanged.

## Outbound (future)

The MVP ingests inbound. Closing the loop — pushing verified status back to the
originating ATS/EMR/CRM — is a symmetric `OutboundAdapter` per system, triggered
by `case.completed` / `case.action_required` events. See
[`architecture.md`](architecture.md#from-mvp-to-production).

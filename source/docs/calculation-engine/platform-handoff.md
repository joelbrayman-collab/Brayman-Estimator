# Contractor Platform handoff

| Attribute | Value |
|-----------|--------|
| Status | **PREPARED / NOT IMPLEMENTED** |
| Date | 2026-09-26 |
| Result authority | Contract V1, pin `2903a45074df21b1c99390cb9aab68638970a2ff` |

This file describes what a future Platform import may receive. It does not map quantities, price them, store them, or attach them to an estimate.

The Platform repository already contains a contract checker and a later mapping step. This Website record does not call that code and does not change it.

## Handoff file

A download is one JSON object:

```text
calculation_result     Contract V1 object, unchanged
consumer_metadata      object, outside the result and outside the fingerprint
```

`calculation_result` is validated as Contract V1 before anyone treats it as quantities. Consumer metadata is never read as a quantity.

Allowed consumer metadata:

| Field | Rule |
|-------|------|
| `project_reference_name` | Optional string. Blank when the person left it empty. |
| `download_title` | Optional string. Display only. |
| `saved_at` | Optional timestamp string for the local save or download. It is not `produced_at`. It is not an acceptance time. |

No other metadata fields are defined. Email, phone, account id, and marketing identifiers are not part of the file.

## What the Platform may later do

Only under a later Platform authorization:

```text
Open the handoff file
        ↓
Validate calculation_result as Contract V1
        ↓
A person reviews the quantities
        ↓
A person confirms any mapping
        ↓
An estimate may then receive a confirmed quantity
```

Company cost, labour, margin, and proposal price are applied only after that confirmation, and only inside the Platform.

## What this handoff does not authorize

- No Platform mapping implementation.
- No pricing.
- No estimate line.
- No database row.
- No workflow state.
- No shared login.
- No change to Contract V1.

A calculated quantity does not become an estimate line by itself. An unknown quantity code stays unresolved. Company identifiers stay out of `calculation_result`.

An example wrapper, with the audit result and an empty project name, is [fixtures/concrete-slab-1.0.0/handoff-audit-10x8.example.json](fixtures/concrete-slab-1.0.0/handoff-audit-10x8.example.json). The wrapper is not itself a Contract V1 document. Only the inner `calculation_result` is.

# QuickBooks Integration — Architecture

| Attribute | Value |
|-----------|--------|
| Status | **Future architecture** (governance recorded; **not implemented**) |
| Updated | 2026-08-25 |
| Implementation | **Prohibited** until Feature Gate + Joel approval |

## Purpose

Define the long-term architecture boundary for exporting **approved customer estimates** to QuickBooks without bypassing human review or the authoritative estimate record.

## Current state

- QuickBooks is listed as a **Future** capability in [architecture.md](../architecture.md) and [platform-roadmap.md](../platform-roadmap.md).
- No QuickBooks Online API integration exists in the application today.
- Manual QuickBooks entry sheets may be used operationally outside the app (see UAT reference case).

## Governed pipeline boundary

```text
Estimator authoritative record
  → approved customer estimate
  → QuickBooks draft estimate
  → human review
  → customer send
```

| Stage | Rule |
|-------|------|
| Authoritative record | Single source ([project-document-package.md](project-document-package.md)) |
| Approval gate | Only **approved** customer estimate proceeds to QuickBooks draft |
| Draft export | System may prepare QuickBooks-ready representation; not auto-send |
| Human review | Required before customer send |
| Customer send | Explicit human action outside silent automation |

## Long-term direction

Architecture should support **QuickBooks Online API** integration when authorized, while preserving:

- Version provenance back to estimate version
- No silent overwrite of sent/exported commercial records
- Audit trail for export and send actions ([Constitution Article 6](../platform-constitution.md))
- Separation of internal costs/margins from customer-facing QuickBooks lines

## Prohibited in unauthorized work

- Implementing QuickBooks API clients
- Auto-creating or auto-sending QuickBooks estimates without review gate
- Treating QuickBooks as the authoritative commercial record (Estimator remains authoritative)

## Feature Gate prerequisites (when proposed)

1. Approved customer estimate output specification
2. Field mapping document (Estimator → QuickBooks estimate)
3. Error handling and idempotency strategy
4. ADR if integration affects ownership or financial controls
5. Joel approval of export/send workflow

## Related

- [project-document-package.md](project-document-package.md)
- [pricing-policy.md](../pricing-policy.md)
- [platform-roadmap.md](../platform-roadmap.md)

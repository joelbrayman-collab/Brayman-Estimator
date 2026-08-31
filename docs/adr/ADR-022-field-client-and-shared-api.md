# ADR-022 — Field Client and Shared API

| Field | Value |
|-------|--------|
| Title | ADR-022: Field Client and Shared API Architecture |
| Status | **Accepted** (architectural direction; no mobile/API implementation in CAR-001) |
| Date | 2026-08-28 |
| Related | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) · [ADR-020](ADR-020-build-module-boundary.md) · [FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT** |

**Current status (2026-08-31):** Shared API Foundation V1 exists as GET-only `/api/v1` over FG-018 cookie/session ([FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**). Field Web and native iOS remain **not implemented**. This ADR’s Decision is unchanged.

## Context

Field / iPhone use is a first-class CalibAi product requirement. The current application is server-rendered Flask HTML with responsive office CSS and no JSON API. Treating field as a shrunken desktop estimating UI would fail capture/Today workflows. Native-first would replace rather than extend the existing business layer.

## Decision

1. Office and field share the same **Project**, the same authoritative records, the same business rules, and the same **service layer**.
2. Field is **not** a shrunken desktop estimating UI.
3. Architectural sequence: **preserve Flask / business services → shared API when field is authorized → purpose-built field web experience → native iOS only later if evidence warrants it**.
4. **Authentication / actor identity** is a prerequisite for BUILD field capture and field web (roadmap item 5 before items 6–7). CAR-001 does not move auth ahead of M009 office sheets.
5. No API, PWA, or native implementation in CAR-001.

## Alternatives Considered

- **Responsive-only on current templates as the field product** — Rejected as insufficient for Today/Capture.
- **Native iOS first** — Rejected: requires an API; premature replacement of the Flask office spine.
- **Separate field database** — Rejected: splits the authoritative project record.

## Consequences

**Positive:** Preservation of Flask services; field can be Feature-Gated without a rewrite.  
**Negative (at acceptance):** A JSON API and auth did not exist yet; field work waited on those gates. As of 2026-08-31 office auth ([FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md)) and Shared API Foundation V1 ([FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md)) are **CLOSED / OPERATIONAL FOR UAT**. Field Web / BUILD capture remain separately gated.

## Module Ownership Impact

No new module. BUILD owns field-execution records (ADR-020). Shared API is platform infrastructure when gated.

## Data Ownership Impact

None in CAR-001. Field clients must not become a second system of record.

## Migration Impact

None in CAR-001.

## Testing Impact

None in CAR-001. Future API/field gates define tests.

## Documentation Impact

CAR-001; platform-vision; roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-28 |
| ChatGPT review | Reconciliation reviewed by Joel | 2026-08-28 |
| Cursor implementation note | Docs/governance only (CAR-001 adoption) | 2026-08-28 |

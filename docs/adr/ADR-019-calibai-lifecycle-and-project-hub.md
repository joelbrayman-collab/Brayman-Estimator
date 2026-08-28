# ADR-019 — CalibAi Lifecycle and Project Hub

| Field | Value |
|-------|--------|
| Title | ADR-019: CalibAi Lifecycle and Project as Authoritative Hub |
| Status | **Accepted** (architectural direction; implementation not authorized by CAR-001) |
| Date | 2026-08-28 |
| Related | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [platform-vision.md](../platform-vision.md) · [modules/projects.md](../modules/projects.md) |

## Context

CalibAi connects PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN through one authoritative project record. The existing platform already has a `Project` entity that parents estimates, change orders, and plan documents. A parallel “CalibAi Job” entity would split ownership.

## Decision

1. The existing **`Project` entity remains the authoritative lifecycle hub**.
2. **Do not** create a parallel CalibAi Job (or equivalent) entity.
3. CalibAi **extends** the existing Flask platform. Preserve and extend: CRM, Projects, Estimating (including estimate versions), Proposals (including snapshots/PDF and Accepted immutability), Change Orders / Project Controls, Plan Intelligence, Document Intelligence, and Sheet Intelligence architecture.
4. **Replacement** of those capabilities requires separate explicit approval.

## Alternatives Considered

- **New CalibAi Job entity beside Project** — Rejected: duplicate ownership; existing FKs already hang off `Project`.
- **Replace Flask / rewrite commercial modules** — Rejected: preservation is the default (CAR-001).

## Consequences

**Positive:** One project record for office and field; existing data and modules remain valid.  
**Negative:** Project hub UX, baseline pointer, and future BUILD/MONITOR records still require Feature-Gated work.

## Module Ownership Impact

Projects continues to own `projects`. No ownership transfer. New BUILD/MONITOR/LEARN concerns are separate ADRs.

## Data Ownership Impact

`Project` is the lifecycle anchor. Child records keep their current owners.

## Migration Impact

None in CAR-001. Future additive tables parent to `projects` unless a later ADR says otherwise.

## Testing Impact

None in CAR-001.

## Documentation Impact

CAR-001; platform-vision; architecture.md; modules/projects.md; roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-28 |
| ChatGPT review | Reconciliation reviewed by Joel | 2026-08-28 |
| Cursor implementation note | Docs/governance only (CAR-001 adoption) | 2026-08-28 |

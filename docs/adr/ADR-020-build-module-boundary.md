# ADR-020 — BUILD Module Boundary

| Field | Value |
|-------|--------|
| Title | ADR-020: BUILD Module Boundary versus Project Controls |
| Status | **Accepted** (module boundary; implementation not authorized by CAR-001) |
| Date | 2026-08-28 |
| Related | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) · [modules/build.md](../modules/build.md) · [modules/projects.md](../modules/projects.md) |

## Context

CalibAi BUILD covers field execution. Change Orders already exist under Project Controls. Absorbing COs into BUILD, or absorbing field capture into Estimating, would blur exclusive ownership (Constitution Article 4 / Rule 1).

## Decision

1. **BUILD** is a **proposed new owning module** for field-execution records, including: daily execution, crews, labour capture, subcontractor activity, material use, deliveries, equipment, progress, schedule/task updates, RFIs/issues, field notes, photos, inspections, and field documentation.
2. **Change Orders remain owned by Project Controls** (documented under Projects until a dedicated Project Controls module doc is approved).
3. BUILD **references** Change Orders; it **does not replace** them and does not own CO commercial lifecycle.
4. BUILD does not own estimates, proposals, plan file binaries, or pricing policy.
5. No BUILD tables, routes, or UI until a Feature Gate and approved Cursor prompt.

## Alternatives Considered

- **Expand Project Controls to own all field capture** — Rejected for now: CO is a commercial change instrument; field execution is a distinct record set.
- **Estimating owns labour/material actuals** — Rejected: actuals must not rewrite the estimate book (see ADR-021 / ADR-024).
- **No BUILD module until code exists** — Rejected: Rule 1 requires named ownership before expansion.

## Consequences

**Positive:** Clear CO vs field-execution split; preservation of existing CO package.  
**Negative:** Cross-module references (BUILD → CO, BUILD → Project, BUILD → plans) must use documented boundaries when implemented.

## Module Ownership Impact

New module: BUILD (`docs/modules/build.md`). Project Controls retains `change_orders` / `change_order_items`.

## Data Ownership Impact

Future BUILD records owned by BUILD. COs unchanged.

## Migration Impact

Deferred. Additive only under a future Feature Gate. None in CAR-001.

## Testing Impact

None in CAR-001.

## Documentation Impact

CAR-001; modules/build.md; modules/README.md; modules/projects.md; roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-28 |
| ChatGPT review | Reconciliation reviewed by Joel | 2026-08-28 |
| Cursor implementation note | Docs/governance only (CAR-001 adoption) | 2026-08-28 |

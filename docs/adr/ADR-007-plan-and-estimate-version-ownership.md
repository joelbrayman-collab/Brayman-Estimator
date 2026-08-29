# ADR-007 — Plan and Estimate Version Ownership

| Field | Value |
|-------|--------|
| Title | ADR-007: Plan and Estimate Version Ownership |
| Status | **Accepted** (2026-08-29; FG-010 / M012) |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · Rule 1–2 |

## Context

Plan sets, take-off packages, and estimate versions evolve independently. Ownership must be exclusive to avoid dual-write and silent drift.

## Decision

*(Accepted — 2026-08-29 with FG-010.)*

1. **Plan Intelligence** owns plan documents, sheets, measurements, take-off versions, and citations.
2. **Estimating** owns estimates, estimate versions, sections, and line items (existing).
3. A mapping/link record may reference `(take_off_version_id → estimate_version_id)` but neither module may overwrite the other’s historical versions in place.
4. New plan revision → new document version; new take-off version required to reflect it; estimate updates only via explicit mapping into an editable estimate version.

## Alternatives Considered

- Single mutable “project quantities” store shared by both — Rejected (ownership violation).
- Estimate lines store only live pointers to take-off — Rejected for issued/locked estimates (need snapshots).

## Consequences

Positive: clear boundaries. Negative: more version objects to teach users.

## Module Ownership Impact

As above; Proposals unchanged (still snapshots from estimates).

## Data Ownership Impact

Exclusive owners per Rule 1–2.

## Migration Impact

Deferred to Feature-Gated phases.

## Testing Impact

Re-upload plan must not mutate prior take-off or estimate versions.

## Documentation Impact

Module stubs; architecture docs.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Approved with FG-010 | 2026-08-29 |
| ChatGPT review | Approved with FG-010 | 2026-08-29 |
| Cursor implementation note | Docs/governance only (2026-08-29). Product implementation not authorized by this acceptance. |

---

## 2026-08-29 acceptance (FG-010 / M012)

For M012, the versioned reviewed take-off artifact is the approved **`TakeoffPackage`**. `EstimateVersion` remains a separate PRICE-side version. Neither floats when the other changes. New drawing revision → new extraction run and (if approved) a new package; prior approved packages remain immutable history.

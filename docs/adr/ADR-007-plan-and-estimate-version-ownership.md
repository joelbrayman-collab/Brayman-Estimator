# ADR-007 — Plan and Estimate Version Ownership

| Field | Value |
|-------|--------|
| Title | ADR-007: Plan and Estimate Version Ownership |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · Rule 1–2 |

## Context

Plan sets, take-off packages, and estimate versions evolve independently. Ownership must be exclusive to avoid dual-write and silent drift.

## Decision

*(Proposed)*

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
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | No implementation in this documentation sprint | |

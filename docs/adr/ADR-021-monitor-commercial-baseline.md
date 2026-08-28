# ADR-021 — MONITOR Commercial Baseline

| Field | Value |
|-------|--------|
| Title | ADR-021: MONITOR Approved Commercial Baseline |
| Status | **Proposed** |
| Date | 2026-08-28 |
| Related | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) · [ADR-002](ADR-002-accepted-proposal-immutability.md) |

## Context

CalibAi MONITOR will compare ESTIMATED ↔ ACTUAL ↔ FORECAST for labour, materials, subcontractors, total cost, schedule/progress, changes, and margin. Several commercial records already exist (estimate versions, locked statuses, proposal snapshots, change orders). Which of these is *the* MONITOR baseline is **not** decided here.

CAR-001 **does** approve the MONITOR comparison model and these invariants; it does **not** accept a specific baseline pointer.

## Decision

*(Proposed — invariants below are CAR-001 direction; baseline selection needs Joel acceptance of this ADR.)*

**Approved direction (do not implement in CAR-001):**

1. MONITOR compares estimated, actual, and forecast figures.
2. Approved estimates / commercial baselines remain **preserved**.
3. **Actuals do not rewrite** the approved estimate.
4. **Forecasts** are dated/versioned snapshots, not silently overwritten values.

**Still open (this ADR remains Proposed until accepted):**

- Whether the MONITOR estimated baseline is a specific `EstimateVersion`, an Accepted proposal snapshot, a composed baseline including approved Change Orders, or an explicit Project baseline pointer.

## Alternatives Considered

- **Always use current estimate version** — Risky: current may still be Draft.
- **Always use Accepted proposal only** — May omit post-acceptance CO commercial effects.
- **Compose estimate + approved COs as the live budget** — Plausible; needs explicit rules before acceptance.

## Consequences

Until accepted, MONITOR implementation must not guess the baseline. Feature Gate required before MONITOR code.

## Module Ownership Impact

MONITOR ownership (module vs Project Controls vs reporting) is **not** assigned by this Proposed ADR.

## Data Ownership Impact

Deferred pending acceptance.

## Migration Impact

None in CAR-001.

## Testing Impact

None in CAR-001.

## Documentation Impact

CAR-001; roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | Open item from CAR-001 | 2026-08-28 |
| Cursor implementation note | Recorded Proposed only | 2026-08-28 |

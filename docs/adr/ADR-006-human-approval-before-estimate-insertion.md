# ADR-006 — Human Approval Before Estimate Insertion

| Field | Value |
|-------|--------|
| Title | ADR-006: Human Approval Before Estimate Insertion |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · Rule 9 |

## Context

Automated take-off must not silently create or modify estimate sections/lines. Cursor and AI systems must not invent product policy.

## Decision

*(Proposed)* No take-off quantity may create, update, or delete `Estimate` / `EstimateVersion` / section / line records without an explicit human approval action in the product UI/API. Batch approve is allowed only as an explicit user command with listed items.

## Alternatives Considered

- Auto-insert above confidence threshold — Rejected for v1.
- Side-by-side “shadow estimate” auto-synced — Deferred; must still require commit action.

## Consequences

Positive: prevents silent commercial corruption. Negative: more reviewer effort.

## Module Ownership Impact

Plan Intelligence proposes; Estimating commits via documented service boundary.

## Data Ownership Impact

Estimate lines remain Estimating-owned.

## Migration Impact

None until mapping tables Feature-Gated.

## Testing Impact

Attempted auto-insert without approval must fail.

## Documentation Impact

Plan Intelligence architecture; Estimating module when mapping ships.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | No implementation in this documentation sprint | |

# ADR-006 — Human Approval Before Estimate Insertion

| Field | Value |
|-------|--------|
| Title | ADR-006: Human Approval Before Estimate Insertion |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · Rule 9 · Milestone 004 |

## Context

Automated take-off must not silently create or modify estimate sections/lines. Cursor and AI systems must not invent product policy. Milestone 004 requires an explicit human review and approval workflow before any estimate insertion.

## Decision

*(Proposed)*

1. No take-off quantity may create, update, or delete `Estimate` / `EstimateVersion` / section / line records without an **explicit human approval** action in the product UI/API.
2. Batch approve is allowed only as an explicit user command listing the items being approved.
3. Confidence above threshold does **not** authorize auto-insert (see ADR-011 for review gating only).
4. Plan Intelligence proposes mapping; Estimating commits via documented service boundary.

## Alternatives Considered

- Auto-insert above confidence threshold — Rejected for v1 / POC.
- Side-by-side “shadow estimate” auto-synced — Deferred; must still require commit action.

## Consequences

Positive: prevents silent commercial corruption. Negative: more reviewer effort.

## Module Ownership Impact

Plan Intelligence proposes; Estimating commits.

## Data Ownership Impact

Estimate lines remain Estimating-owned.

## Migration Impact

None until mapping tables Feature-Gated.

## Testing Impact

Attempted auto-insert without approval must fail.

## Documentation Impact

Plan Intelligence architecture §4 and §6; module non-goals.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | No implementation in Milestone 004 (docs only) | |

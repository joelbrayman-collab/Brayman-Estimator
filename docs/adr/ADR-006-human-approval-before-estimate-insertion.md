# ADR-006 — Human Approval Before Estimate Insertion

| Field | Value |
|-------|--------|
| Title | ADR-006: Human Approval Before Estimate Insertion |
| Status | **Accepted** (2026-08-29; FG-010 / M012) |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · Rule 9 · Milestone 004 |

## Context

Automated take-off must not silently create or modify estimate sections/lines. Cursor and AI systems must not invent product policy. Milestone 004 requires an explicit human review and approval workflow before any estimate insertion.

## Decision

*(Accepted — 2026-08-29 with FG-010.)*

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
| Joel | Approved with FG-010 | 2026-08-29 |
| ChatGPT review | Approved with FG-010 | 2026-08-29 |
| Cursor implementation note | Docs/governance only (2026-08-29). Product implementation not authorized by this acceptance. |

---

## 2026-08-29 acceptance clarification (FG-010 / M012)

This ADR establishes the **human-authority boundary**. Human approval of reviewed take-off evidence (candidate or package) does **NOT** authorize `EstimateVersion` insertion in M012.

FG-010 stops before estimate insertion. A later Feature Gate is required for PLAN → Estimate mapping. Confidence is not authorization.

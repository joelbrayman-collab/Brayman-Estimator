# ADR-002 — Accepted Proposal Immutability

| Field | Value |
|-------|--------|
| Title | ADR-002: Accepted Proposal Immutability |
| Status | **Accepted** (implemented in Milestone 003) |
| Date | 2026-07-25 |
| Related | [FG-001](../feature-gates/FG-001-proposals-module.md) · Constitution Article 5 · Architecture Rule 3 |

## Context

`PROPOSAL_STATUSES` includes `Accepted`, but `update_proposal` and `update_proposal_line_item` do not prevent edits after acceptance. Silently rewriting accepted commercial records violates Constitution Article 5 and architecture Rule 3. This gap is the highest Proposals-module governance risk identified in Milestone 002.

## Decision

1. When `proposal.status == "Accepted"`, commercial snapshot fields, narrative, section/line structure and amounts, display flags, and status are **immutable** without an explicit void/supersede/revision workflow (that workflow is **out of scope** for Milestone 003).
2. Service layer is the enforcement point (`ensure_proposal_mutable` / `ProposalServiceError` in `app/services/proposals.py`); routes/UI respect the same rules but do not replace them.
3. Hard-lock applies to **Accepted** only in Milestone 003 (other terminal statuses unchanged unless later Feature-Gated).
4. No migration for Milestone 003.

## Alternatives Considered

- **Status-only cosmetic Accepted** — Rejected: false sense of legal/commercial finality.
- **Full event-sourcing rewrite** — Deferred: disproportionate for current platform stage.
- **Database triggers** — Rejected for now: keep rules in application services for testability.

## Consequences

**Positive:** Aligns product with Constitution; enables trustworthy acceptance and downstream project baselines.  
**Negative:** Users cannot “tweak” an accepted proposal in place; may need a revise/supersede workflow (ADR-004 / later).

## Module Ownership Impact

Proposals enforces immutability. No transfer of ownership.

## Data Ownership Impact

Accepted proposal snapshots become historically protected records.

## Migration Impact

**None.**

## Testing Impact

Covered by `tests/test_proposal_immutability.py` plus existing proposal suites.

## Documentation Impact

`modules/proposals.md`, FG-001 notes, milestones, chat-workflow-log.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Accepted for Milestone 003 (per implementation prompt) | 2026-07-25 |
| ChatGPT review | | |
| Cursor implementation note | Milestone 003 — `ensure_proposal_mutable` | 2026-07-25 |

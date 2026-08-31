# ADR-004 — Proposal Acceptance Workflow

| Field | Value |
|-------|--------|
| Title | ADR-004: Proposal Acceptance Workflow |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [FG-001](../feature-gates/FG-001-proposals-module.md) · [ADR-002](ADR-002-accepted-proposal-immutability.md) · [modules/projects.md](../modules/projects.md) |

## Context

Roadmap and vision include formal proposal acceptance and eventual project/budget creation from accepted snapshots. Today, acceptance is only a status value among `PROPOSAL_STATUSES`. There is no dedicated workflow, acceptance timestamp beyond generic updates, signature, or Projects-module handoff. Implementing project creation before immutability would risk basing budgets on mutable records.

## Decision

*(Proposed for Joel approval)*

1. **Sequence:** Implement **ADR-002 immutability** before a formal acceptance workflow milestone.
2. **Acceptance workflow (future Milestone 004 candidate)** shall define at minimum:
   - Explicit user action to Accept (not only a free-form status dropdown, unless Joel prefers status-only with stronger guards)
   - Preconditions (e.g. must be Issued or Ready — Joel to confirm)
   - Recording of acceptance time (reuse/extend `issued_at` pattern or add `accepted_at` — Joel to confirm; migration only if new column required)
   - Enforcement that Accepted records follow ADR-002
3. **Electronic signature** remains **Future** and out of Milestone 004 unless Joel expands scope.
4. **Project creation from accepted proposal** is a **separate later milestone** owned at the boundary of Proposals (source snapshot) and Projects (creates project/budget records). Proposals must not own the project budget ledger.
5. Supersession: accepting a new proposal for the same job should mark prior accepted proposals `Superseded` per product rules (details in Milestone 004 Feature Gate).

**Subsequent status (2026-08-31):** Contract / Change Order e-signature reconnaissance is **complete** at [contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md). Recommendation **NATIVE V1**. Implementation **NOT AUTHORIZED**. This ADR remains **Proposed**. That recon does **not** implement Proposal e-signature and does **not** expand this ADR’s Decision.

## Alternatives Considered

- **Build project-from-proposal first** — Rejected until immutability exists.
- **Full e-signature provider now** — Deferred (roadmap Future).
- **Keep status-only forever** — Insufficient for Rule 4 / audit expectations.

## Consequences

**Positive:** Clear ordered roadmap; avoids premature Projects integration.  
**Negative:** Acceptance UX remains minimal until Milestone 004.

## Module Ownership Impact

Proposals owns acceptance state on the proposal record. Projects owns any project/budget created afterward.

## Data Ownership Impact

Accepted snapshot remains Proposals-owned historical record; derived project budgets are Projects-owned copies/baselines (future ADR).

## Migration Impact

Possibly none (status + service rules only) or additive `accepted_at` — decide in Milestone 004 Feature Gate. **No estimate-table changes.**

## Testing Impact

Acceptance preconditions; immutability after accept; no accidental project creation until that milestone; regression on preview/PDF.

## Documentation Impact

FG for Milestone 004; modules/proposals.md; modules/projects.md; roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Do not implement until after Milestone 003 (immutability) and a dedicated Feature Gate | |

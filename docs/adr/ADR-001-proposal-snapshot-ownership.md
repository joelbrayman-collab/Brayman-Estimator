# ADR-001 — Proposal Snapshot Ownership

| Field | Value |
|-------|--------|
| Title | ADR-001: Proposal Snapshot Ownership |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [FG-001](../feature-gates/FG-001-proposals-module.md) · [modules/proposals.md](../modules/proposals.md) |

## Context

Proposals are created from estimate versions. Commercial integrity requires that client-facing proposal content remain stable when estimates later change. The codebase already implements header and section/line snapshots (`build_proposal_snapshot`, `snapshot_estimate_version_content`). Module ownership and Constitution Articles 4–5 require an explicit decision that this pattern is authoritative.

## Decision

*(Proposed for Joel approval)*

1. The **Proposals module** is the exclusive owner of `proposal_templates`, `proposals`, `proposal_sections`, and `proposal_line_items`.
2. At proposal creation, commercial and presentation content is **copied** into proposal-owned tables/columns (snapshot). After create, the proposal is **not** a live view of the estimate.
3. Estimating retains ownership of live `estimate_*` structure. Proposals may reference `estimates` / `estimate_versions` / `source_line_item_id` for provenance only.
4. Preview and PDF **must** render from proposal snapshot data, never from live estimate lines.
5. Waste percent may continue to be **baked into** proposal `unit_cost` at snapshot time (current behaviour) unless a later ADR changes audit requirements.
6. Re-snapshot / refresh-from-estimate after create is **out of scope** unless a future Feature Gate explicitly allows it.

## Alternatives Considered

- **Live join to estimate lines** — Rejected: breaks historical commercial records when estimates change.
- **Dual-write estimate + proposal as one structure** — Rejected: violates exclusive module ownership.
- **Store only PDF as record** — Rejected: PDF is a render; structured snapshot remains system of record.

## Consequences

**Positive:** Aligns code with Constitution; clear ownership; existing tests remain valid.  
**Negative:** Proposal edits diverge from estimate (by design); users must understand snapshot semantics.

## Module Ownership Impact

Proposals own snapshot records. Estimating remains source-at-create only.

## Data Ownership Impact

Snapshot fields on `Proposal` and child section/line rows are authoritative for issued commercial content.

## Migration Impact

**None** for adopting this decision (already implemented).

## Testing Impact

Retain/expand snapshot independence tests (`tests/test_proposal_snapshots.py`, `tests/test_proposal_pdf.py`).

## Documentation Impact

`modules/proposals.md`, FG-001, architecture.md (current section already describes snapshots).

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | No code required if Accepted as documentation of current law | |

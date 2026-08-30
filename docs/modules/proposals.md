# Module — Proposals

| Attribute | Value |
|-----------|--------|
| Status | **Current** (engine + snapshot + PDF; Accepted immutability **enforced**) |
| Updated | 2026-08-30 |
| Code | `app/models/proposal.py`; `app/routes/proposals.py`, `proposal_templates.py`; `app/services/proposals.py`, `proposal_pdf.py` |
| Feature Gate | [FG-001](../feature-gates/FG-001-proposals-module.md) (module baseline) · [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED** (customer-output consistency) |

## Purpose

Produce client-facing proposals from estimate versions using templates, preserving commercial snapshots independent of later estimate edits.

Joel decision ([FG-012](../feature-gates/FG-012-estimate-output-consistency.md)): the existing Proposal preview/PDF **is** the customer-facing estimate. Do not create a separate Customer Estimate entity or document family. FG-012 (not started) must make Proposal commercial totals consistent with the source `EstimateVersion` / `EstimatePricingSnapshot` and must not leak internal Overhead/Profit on the customer PDF.

## Responsibilities

- Proposal templates (branding, default clauses, display flags)
- Proposal records and status lifecycle (`Draft` … `Accepted` …)
- Snapshot sections/lines at creation (`build_proposal_snapshot`, `snapshot_estimate_version_content`)
- Browser preview and PDF generation from **proposal snapshot** (not live estimate lines)

## Owned data

- `proposal_templates`
- `proposals`, `proposal_sections`, `proposal_line_items`
- Snapshot commercial fields on `Proposal` (client/project names, markups, totals, narrative, display flags)

## Referenced data

- `estimates` / `estimate_versions` (nullable FKs; may clear if version deleted while keeping snapshot — covered by tests)
- Optional `estimate_line_items.id` via `source_line_item_id` (`ON DELETE SET NULL` in migration)
- Template FK required
- Live `Client` / `Project` only at snapshot time (no `client_id` / `project_id` on proposals today — see ADR-003)

## Prohibited responsibilities

- Owning live estimate structure
- Project budget ledger (Projects / future Job Costing)
- Electronic signature providers (Future)
- Inventing CRM Company/User entities without Feature Gate

## Current implementation (accurate as of Milestone 002 review)

**Complete:** templates; create-from-estimate-version; header + section/line snapshots; metadata/line edit + recalculation; status enum including `Accepted`; **service-layer immutability when `Accepted`** (`ensure_proposal_mutable`); preview; PDF; snapshot independence tests.

**Not complete:** formal acceptance workflow (void/supersede/revision); project/budget creation from acceptance; e-signature; rich add/remove/reorder of proposal sections; optional CRM FKs.

**Known debt:** model `ondelete="SET NULL"` on proposal→estimate FKs not mirrored in create migrations; waste baked into proposal `unit_cost`. Proposal recalc currently restacks markup/overhead/profit and can diverge from an `EstimatePricingSnapshot` customer total; customer PDF can print Overhead/Profit rows that preview does not — **in scope for FG-012** (implementation not started).

## Planned capabilities

- Customer totals consistent with source pricing snapshot / version — [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED**
- Formal acceptance workflow — after immutability (ADR-004)
- Project creation from acceptance snapshot — later; Projects boundary (Rule 4)
- Electronic signature — **Future**
- Optional CRM FKs — deferred (ADR-003)

## Dependencies

- Estimating (source versions)
- Templates for presentation defaults
- CRM / Projects indirectly via estimate → project → client at snapshot time

## Invariants

- Proposal commercial lines are snapshot data, not live estimate lines (ADR-001)
- Accepted proposals must not be silently rewritten (Rule 3) — **enforced** via `ensure_proposal_mutable` in `app/services/proposals.py` (Milestone 003 / ADR-002)

## Open decisions

- Exact void / supersede / revision workflow (out of Milestone 003)
- Acceptance preconditions (Issued vs Ready vs any)
- Whether `accepted_at` column is required

## Relevant tests

- `tests/test_proposals.py`
- `tests/test_proposal_snapshots.py`
- `tests/test_proposal_preview.py`
- `tests/test_proposal_pdf.py`
- `tests/test_proposal_immutability.py`

## Relevant ADRs

- [ADR-001 Proposal Snapshot Ownership](../adr/ADR-001-proposal-snapshot-ownership.md) — Accepted (implementation assumption for M003)
- [ADR-002 Accepted Proposal Immutability](../adr/ADR-002-accepted-proposal-immutability.md) — **Accepted / implemented (Milestone 003)**
- [ADR-003 Optional CRM Foreign Keys](../adr/ADR-003-optional-crm-foreign-keys.md) — Accepted as defer
- [ADR-004 Proposal Acceptance Workflow](../adr/ADR-004-proposal-acceptance-workflow.md) — Accepted direction; workflow not built in M003

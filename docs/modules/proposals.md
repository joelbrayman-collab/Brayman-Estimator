# Module — Proposals

| Attribute | Value |
|-----------|--------|
| Status | **Current** (engine + snapshot + PDF; Accepted immutability **enforced**) |
| Updated | 2026-08-30 |
| Code | `app/models/proposal.py`; `app/routes/proposals.py`, `proposal_templates.py`; `app/services/proposals.py`, `proposal_pdf.py` |
| Feature Gate | [FG-001](../feature-gates/FG-001-proposals-module.md) (module baseline) · [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** (customer-output consistency) · [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT** (Brand Profile consumer; live current=head `a9b0c1d2e3f4`) |

## Purpose

Produce client-facing proposals from estimate versions using templates, preserving commercial snapshots independent of later estimate edits.

Joel decision ([FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**): the existing Proposal preview/PDF **is** the customer-facing estimate. Named-method (`TRUE_GROSS_MARGIN`, `COST_PLUS_MARKUP`) proposal totals copy the frozen `EstimatePricingSnapshot` commercial result and do not restack markup/overhead/profit. Legacy no-snapshot versions retain `COST_PLUS_MARKUP_STACK`. Customer PDF prints Subtotal / Tax / Grand Total only (no internal Overhead/Profit rows).

## Responsibilities

- Proposal templates (branding, default clauses, display flags)
- Proposal records and status lifecycle (`Draft` … `Accepted` …)
- Snapshot sections/lines at creation (`build_proposal_snapshot`, `snapshot_estimate_version_content`)
- Browser preview and PDF generation from **proposal snapshot** (not live estimate lines)

## Owned data

- `proposal_templates`
- `proposals`, `proposal_sections`, `proposal_line_items`
- `proposal_brand_snapshots` (issued/accepted brand freeze; FG-017)
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
- Owning the Organization Brand Profile ([ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted**; [organization-brand-profile.md](../architecture/organization-brand-profile.md)). Per-template `logo_path` is **not** the governed FG-017 render source. [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) is **CLOSED / OPERATIONAL FOR UAT**.

## Current implementation (accurate as of Milestone 002 review)

**Complete:** templates; create-from-estimate-version; header + section/line snapshots; metadata/line edit + recalculation; status enum including `Accepted`; **service-layer immutability when `Accepted`** (`ensure_proposal_mutable`); preview; PDF; snapshot independence tests; **FG-017 Proposal brand snapshot** (freeze at Issued / Accepted-without-Issued; sticky; live-migrated / office UAT on port **5010**).

**Not complete:** formal acceptance workflow (void/supersede/revision); project/budget creation from acceptance; e-signature; rich add/remove/reorder of proposal sections; optional CRM FKs.

**Known debt:** model `ondelete="SET NULL"` on proposal→estimate FKs not mirrored in create migrations; waste baked into proposal `unit_cost`. Office proposal create/detail still lists Overhead/Profit amounts (zero when a named method governs). Customer preview/PDF do not print those rows. Draft proposal line edits still restack via `recalculate_proposal` (explicit draft mutation; no automatic stale workflow).

## Planned capabilities

- Customer totals consistent with source pricing snapshot / version — **implemented / operational for UAT** ([FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**)
- Formal acceptance workflow — after immutability (ADR-004)
- Project creation from acceptance snapshot — later; Projects boundary (Rule 4)
- Electronic signature — **Future**
- Optional CRM FKs — deferred (ADR-003)
- Organization Brand Profile as document branding source — [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Pin: [organization-brand-profile.md](../architecture/organization-brand-profile.md).

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
- MONITOR implementation remains **not started**. The Accepted Proposal is the immutable customer-commitment layer of the composed MONITOR baseline ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted**). Draft Proposal restacks must not be used as the committed baseline.

## Relevant tests

- `tests/test_proposals.py`
- `tests/test_proposal_snapshots.py`
- `tests/test_proposal_preview.py`
- `tests/test_proposal_pdf.py`
- `tests/test_proposal_immutability.py`
- `tests/test_estimate_output_consistency.py` (FG-012 named-method / firewall / immutability)

## Relevant ADRs

- [ADR-001 Proposal Snapshot Ownership](../adr/ADR-001-proposal-snapshot-ownership.md) — Accepted (implementation assumption for M003)
- [ADR-002 Accepted Proposal Immutability](../adr/ADR-002-accepted-proposal-immutability.md) — **Accepted / implemented (Milestone 003)**
- [ADR-003 Optional CRM Foreign Keys](../adr/ADR-003-optional-crm-foreign-keys.md) — Accepted as defer
- [ADR-004 Proposal Acceptance Workflow](../adr/ADR-004-proposal-acceptance-workflow.md) — Accepted direction; workflow not built in M003
- [ADR-021 MONITOR Commercial Baseline](../adr/ADR-021-monitor-commercial-baseline.md) — **Accepted** (Accepted Proposal is the customer-commitment pin; MONITOR not implemented)

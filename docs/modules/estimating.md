# Module — Estimating

| Attribute | Value |
|-----------|--------|
| Status | **Current** (core implemented) |
| Updated | 2026-09-08 |
| Code | `app/models/cost_item.py`, `assembly.py`, `estimate.py`; `app/routes/cost_library.py`, `assemblies.py`, `estimates.py`; `app/services/estimates.py`, `estimate_builder.py`, `estimate_output.py` |
| Feature Gate | [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** (internal breakdown + customer consistency). [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT** (Estimating-owned insertion/citation). [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **LIVE-MIGRATED / OFFICE UAT STOPPED / NOT CLOSED** (costing approval; legacy override-provenance **REPAIRED / AWAITING UAT CONTINUATION**). |

## Purpose

Build and version construction estimates from cost libraries and assemblies, scoped to a project. The Estimator must maintain the **authoritative project/estimate record** from which governed outputs derive ([project-document-package.md](../architecture/project-document-package.md)).

`CostItem` is the **organization costing record**. It is **not** CalibAi material identity. Canonical materials (what the project requires) are defined in [material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) (**Intended**; not implemented).

## Responsibilities

- Cost item library (org costing; Material-category items may later link to a canonical material)
- Assemblies and assembly items (commercial composition; may remain one rolled-up estimate line)
- Estimates and estimate versions
- Sections and line items
- Version status / locking for issued-like statuses

## Owned data

- `cost_items`
- `assemblies`, `assembly_items`
- `estimates`, `estimate_versions`, `estimate_sections`, `estimate_line_items`
- `takeoff_estimate_insertions`, `takeoff_estimate_insertion_citations` (FG-026; Estimating-owned frozen provenance)
- `estimate_costing_snapshots`, `estimate_costing_snapshot_lines` (FG-027; Estimating-owned; additive `a5b6c7d8e9f0` **applied live**)

## Referenced data

- `projects` (FK)
- Optionally referenced by proposals and change orders via estimate / estimate_version FKs

## Prohibited responsibilities

- Owning CalibAi canonical material identity / taxonomy ([material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md))
- Final client-facing proposal layout/PDF ownership (Proposals module). [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) requires Proposals customer totals to match this module’s authoritative `EstimateVersion` / pricing snapshot; Estimating still does not own the PDF.
- Project change order lifecycle ownership (Project Controls / Projects)
- Accounting integrations
- Auto-creating `EstimateLineItem` rows from Permit Intelligence findings ([ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md); [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md)). Permit Intelligence may later **identify** cost implications; human-controlled propose-allowance is **not authorized** this pass.

## Current implementation

- Office Estimate screens use **Estimate version** / **Pricing lock** display labels ([FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) Slice 3). Estimate ≠ Proposal. Internal models unchanged.
- Estimate statuses and version statuses defined in `app/models/estimate.py`
- `AUTO_LOCK_VERSION_STATUSES` locks versions when Issued/Accepted/Rejected/Superseded
- Builder service supports structured line construction
- UI under Estimating nav section
- Internal Detailed Cost Breakdown — **implemented / operational for UAT** ([FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**). Office view at `GET /estimates/<id>/versions/<version_id>/internal-breakdown`. Direct Cost = Σ `extended_cost`. Labour snapshots display-only, labeled not in selling-price basis.
- Governed pricing policy application — **implemented / operational for UAT** ([pricing-policy.md](../pricing-policy.md); [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**; [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; versions without a snapshot still use markup/overhead/profit stack)
- Deeper productivity tooling — [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) Labour Engine Phase B **IMPLEMENTED / VERIFIED / LIVE-MIGRATED** (operational for UAT); Estimating does not own canonical tasks or production standards

## Planned capabilities

- Takeoff-to-estimate insertion + frozen citation provenance — [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Service: `app/services/takeoff_estimate_mapping.py`. UI: `/projects/<id>/plans/takeoff/packages/<package_id>/map`. Plan Intelligence remains owner of the source package. Package approval does **not** insert lines. Live current = heads **`f4a5b6c7d8e9`**.
- Costing approval + immutable costing snapshot — [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **LIVE-MIGRATED / OFFICE UAT STOPPED / NOT CLOSED**. Legacy NULL `library_unit_cost_reference` on CostItem/Assembly Draft edit freezes pre-edit working `unit_cost` (`72949f99da2b56ec06e95e16e29fa194a6730bbd`). [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. Preflight [fg-027-costing-approval-preflight.md](../architecture/fg-027-costing-approval-preflight.md). Approve All = costing approval only. Pricing Engine consumes; does not own costing.
- Future Material-category `CostItem` → canonical material link ([FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**); assembly components resolvable to canonical materials later; fulfillment uses **exploded** material quantities even when the commercial line stays rolled-up ([material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md)). Identity V1 does not explode Assemblies.
- QuickBooks and Ontario contract/warranty remain **Future**.
- Historical estimating intelligence — **Future**

## Dependencies

- Projects (and thus Clients)
- Consumed by Proposals (snapshot source) and Change Orders (optional version link)

## Invariants

- Estimate belongs to a Project
- Versions are numbered per estimate; prefer supersession over silent overwrite (Rule 5)
- Locked versions are read-only in UI/service rules (verify on change)

## Open decisions

- When estimate header status vs version status diverge—canonical source of truth for “accepted bid”
- MONITOR implementation remains **not started**. Estimated baseline for later MONITOR is the locked `EstimateVersion` plus `EstimatePricingSnapshot` when present ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted**). Draft versions must not be the committed baseline.
- How (or whether) to migrate estimate markup/overhead/profit to the governing gross-margin formula ([ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** — dual named methods; [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; existing versions without snapshots remain `COST_PLUS_MARKUP_STACK` and are not backfilled)

## Relevant tests

- `tests/test_estimates.py`
- `tests/test_estimate_builder.py`
- `tests/test_assemblies.py`
- `tests/test_estimate_output_consistency.py` (FG-012)

## Relevant ADRs

- [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**
- [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted**
- [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (MONITOR not implemented)
- [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** (LEARN must not mutate cost library / approved estimates)
- [material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) **Intended** ([ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md) / [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) / [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted**; CostItem is not CalibAi identity; living supplier evidence is not the identity row)
- [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** — Estimating owns internal breakdown; Proposal remains the customer-facing estimate

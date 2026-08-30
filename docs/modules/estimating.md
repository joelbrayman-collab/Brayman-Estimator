# Module — Estimating

| Attribute | Value |
|-----------|--------|
| Status | **Current** (core implemented) |
| Updated | 2026-08-30 |
| Code | `app/models/cost_item.py`, `assembly.py`, `estimate.py`; `app/routes/cost_library.py`, `assemblies.py`, `estimates.py`; `app/services/estimates.py`, `estimate_builder.py` |
| Feature Gate | [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED** (internal breakdown + customer consistency) |

## Purpose

Build and version construction estimates from cost libraries and assemblies, scoped to a project. The Estimator must maintain the **authoritative project/estimate record** from which governed outputs derive ([project-document-package.md](../architecture/project-document-package.md)).

## Responsibilities

- Cost item library
- Assemblies and assembly items
- Estimates and estimate versions
- Sections and line items
- Version status / locking for issued-like statuses

## Owned data

- `cost_items`
- `assemblies`, `assembly_items`
- `estimates`, `estimate_versions`, `estimate_sections`, `estimate_line_items`

## Referenced data

- `projects` (FK)
- Optionally referenced by proposals and change orders via estimate / estimate_version FKs

## Prohibited responsibilities

- Final client-facing proposal layout/PDF ownership (Proposals module). [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) requires Proposals customer totals to match this module’s authoritative `EstimateVersion` / pricing snapshot; Estimating still does not own the PDF.
- Project change order lifecycle ownership (Project Controls / Projects)
- Accounting integrations

## Current implementation

- Estimate statuses and version statuses defined in `app/models/estimate.py`
- `AUTO_LOCK_VERSION_STATUSES` locks versions when Issued/Accepted/Rejected/Superseded
- Builder service supports structured line construction
- UI under Estimating nav section

## Planned capabilities

- Internal Detailed Cost Breakdown output — [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED** (Estimating-owned office view/document of one `EstimateVersion`; Direct Cost = Σ `extended_cost`; labour snapshots display-only, not in selling-price basis). QuickBooks and Ontario contract/warranty remain **Future**.
- Governed pricing policy application — **implemented / operational for UAT** ([pricing-policy.md](../pricing-policy.md); [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**; [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; versions without a snapshot still use markup/overhead/profit stack)
- Historical estimating intelligence — **Future**
- Deeper productivity tooling — [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) Labour Engine Phase B **IMPLEMENTED / VERIFIED / LIVE-MIGRATED** (operational for UAT); Estimating does not own canonical tasks or production standards

## Dependencies

- Projects (and thus Clients)
- Consumed by Proposals (snapshot source) and Change Orders (optional version link)

## Invariants

- Estimate belongs to a Project
- Versions are numbered per estimate; prefer supersession over silent overwrite (Rule 5)
- Locked versions are read-only in UI/service rules (verify on change)

## Open decisions

- When estimate header status vs version status diverge—canonical source of truth for “accepted bid”
- MONITOR estimated baseline selection ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Proposed**)
- How (or whether) to migrate estimate markup/overhead/profit to the governing gross-margin formula ([ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** — dual named methods; [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; existing versions without snapshots remain `COST_PLUS_MARKUP_STACK` and are not backfilled)

## Relevant tests

- `tests/test_estimates.py`
- `tests/test_estimate_builder.py`
- `tests/test_assemblies.py`

## Relevant ADRs

- [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**
- [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted**
- [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Proposed**
- [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** (LEARN must not mutate cost library / approved estimates)
- [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED** — Estimating owns internal breakdown; Proposal remains the customer-facing estimate

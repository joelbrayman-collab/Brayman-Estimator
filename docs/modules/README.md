# Modules — Index

| Attribute | Value |
|-----------|--------|
| Status | Ownership map |
| Updated | 2026-08-30 |

| Module | Doc | Code evidence (current) |
|--------|-----|-------------------------|
| CRM | [crm.md](crm.md) | Clients (+ project linkage) |
| Estimating | [estimating.md](estimating.md) | Cost items, assemblies, estimates; [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** (internal breakdown owner). CostItem is **not** CalibAi material identity. |
| Proposals | [proposals.md](proposals.md) | Templates, proposals, snapshot, PDF (customer-facing estimate; FG-012 consistency **CLOSED / OPERATIONAL FOR UAT**). First Brand Profile consumer ([FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) **IMPLEMENTED / LIVE MIGRATION PENDING**) |
| Projects | [projects.md](projects.md) | Projects entity; change orders under Project Controls package; `/projects/<id>` Project Hub ([FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**). [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. Change Order document family pin **FUTURE / NOT IMPLEMENTED**. |
| Plan Intelligence | [plan-intelligence.md](plan-intelligence.md) | Phase A upload (M005) + Document Indexing (M007) + Sheets (M009) + Scale/measurement (M010) + **M012 / FG-010 take-off foundation OPERATIONAL FOR UAT** |
| Labour Engine | [labour-engine.md](labour-engine.md) | FG-008 Phase B foundation (`app/models/labour_engine.py`, `/labour-engine/`) — **CLOSED / OPERATIONAL FOR UAT**; revision `f2c3d4e5f6a7` in chain; live head `b4c5d6e7f8a9` |
| Pricing Engine | [pricing-engine.md](pricing-engine.md) | FG-009 foundation **CLOSED / OPERATIONAL FOR UAT**: `app/models/pricing_engine.py`, `/pricing-engine/`; revision `a3b4c5d6e7f8` in chain; live head `b4c5d6e7f8a9`. Versions without snapshots still use `estimate_builder.py` stack |
| BUILD | [build.md](build.md) | **None** — Proposed (ADR-020); not implemented |
| MONITOR | [monitor.md](monitor.md) | **None** — Proposed (ADR-021 **Accepted** baseline; not implemented) |
| Historical ingestion | [../architecture/historical-estimate-ingestion-architecture.md](../architecture/historical-estimate-ingestion-architecture.md) · [FG-006](../feature-gates/FG-006-historical-estimate-ingestion-phase-b.md) · [FG-013](../feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) | FG-006 engine **Current**; office upload UX **CLOSED / OPERATIONAL FOR UAT** ([ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md); revision `c5d6e7f8a9b0`) |
| Material Catalogue | [material-catalogue.md](material-catalogue.md) · [../architecture/material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) · [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) | **CLOSED / OPERATIONAL FOR UAT** — `/material-catalogue/`; live current=head `d6e7f8a9b0c1`. ADR-034/035/036 **Accepted**. |
| Permit Intelligence | [permit-intelligence.md](permit-intelligence.md) · [../architecture/permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [../architecture/permit-rules-library.md](../architecture/permit-rules-library.md) · [../architecture/jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) | Pass 1 foundation **CLOSED / OPERATIONAL FOR UAT** (Projects-owned). Pass 2 [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. Architecture **Accepted** (ADR-037/038/039). |
| Supplier Catalogue | [supplier-catalogue.md](supplier-catalogue.md) | **None** — Future (only `CostItem.supplier` text today). **Bulk onboarding pin FUTURE / NOT IMPLEMENTED.** Channel: [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (not implemented). Does **not** own CalibAi material identity. |

Project Controls (Change Orders) is documented under Projects for ownership clarity until a dedicated module doc is approved. BUILD references Change Orders; it does not own them ([ADR-020](../adr/ADR-020-build-module-boundary.md)). MONITOR is a comparison/read layer; it does not own estimates, proposals, Change Orders, or actuals ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted**).

CalibAi lifecycle: [../architecture/CAR-001-calibai-product-architecture-reconciliation.md](../architecture/CAR-001-calibai-product-architecture-reconciliation.md).
Domain architecture: [../architecture/](../architecture/).

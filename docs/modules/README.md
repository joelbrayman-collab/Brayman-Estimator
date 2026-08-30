# Modules — Index

| Attribute | Value |
|-----------|--------|
| Status | Ownership map |
| Updated | 2026-08-30 |

| Module | Doc | Code evidence (current) |
|--------|-----|-------------------------|
| CRM | [crm.md](crm.md) | Clients (+ project linkage) |
| Estimating | [estimating.md](estimating.md) | Cost items, assemblies, estimates; [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** (internal breakdown owner) |
| Proposals | [proposals.md](proposals.md) | Templates, proposals, snapshot, PDF (customer-facing estimate; FG-012 consistency **CLOSED / OPERATIONAL FOR UAT**) |
| Projects | [projects.md](projects.md) | Projects entity; change orders under Project Controls package; `/projects/<id>` Project Hub ([FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**) |
| Plan Intelligence | [plan-intelligence.md](plan-intelligence.md) | Phase A upload (M005) + Document Indexing (M007) + Sheets (M009) + Scale/measurement (M010) + **M012 / FG-010 take-off foundation OPERATIONAL FOR UAT** |
| Labour Engine | [labour-engine.md](labour-engine.md) | FG-008 Phase B foundation (`app/models/labour_engine.py`, `/labour-engine/`) — **CLOSED / OPERATIONAL FOR UAT**; revision `f2c3d4e5f6a7` in chain; live head `b4c5d6e7f8a9` |
| Pricing Engine | [pricing-engine.md](pricing-engine.md) | FG-009 foundation **CLOSED / OPERATIONAL FOR UAT**: `app/models/pricing_engine.py`, `/pricing-engine/`; revision `a3b4c5d6e7f8` in chain; live head `b4c5d6e7f8a9`. Versions without snapshots still use `estimate_builder.py` stack |
| BUILD | [build.md](build.md) | **None** — Proposed (ADR-020); not implemented |
| Supplier Catalogue | [supplier-catalogue.md](supplier-catalogue.md) | **None** — Future (only `CostItem.supplier` text today) |

Project Controls (Change Orders) is documented under Projects for ownership clarity until a dedicated module doc is approved. BUILD references Change Orders; it does not own them ([ADR-020](../adr/ADR-020-build-module-boundary.md)).

CalibAi lifecycle: [../architecture/CAR-001-calibai-product-architecture-reconciliation.md](../architecture/CAR-001-calibai-product-architecture-reconciliation.md).
Domain architecture: [../architecture/](../architecture/).

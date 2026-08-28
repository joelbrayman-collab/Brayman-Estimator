# Modules — Index

| Attribute | Value |
|-----------|--------|
| Status | Ownership map |
| Updated | 2026-08-28 |

| Module | Doc | Code evidence (current) |
|--------|-----|-------------------------|
| CRM | [crm.md](crm.md) | Clients (+ project linkage) |
| Estimating | [estimating.md](estimating.md) | Cost items, assemblies, estimates |
| Proposals | [proposals.md](proposals.md) | Templates, proposals, snapshot, PDF |
| Projects | [projects.md](projects.md) | Projects entity; change orders under Project Controls package |
| Plan Intelligence | [plan-intelligence.md](plan-intelligence.md) | Phase A upload (M005) + Document Indexing (M007); Sheets **not** implemented |
| BUILD | [build.md](build.md) | **None** — Proposed (ADR-020); not implemented |
| Supplier Catalogue | [supplier-catalogue.md](supplier-catalogue.md) | **None** — Future (only `CostItem.supplier` text today) |

Project Controls (Change Orders) is documented under Projects for ownership clarity until a dedicated module doc is approved. BUILD references Change Orders; it does not own them ([ADR-020](../adr/ADR-020-build-module-boundary.md)).

CalibAi lifecycle: [../architecture/CAR-001-calibai-product-architecture-reconciliation.md](../architecture/CAR-001-calibai-product-architecture-reconciliation.md).
Domain architecture: [../architecture/](../architecture/).

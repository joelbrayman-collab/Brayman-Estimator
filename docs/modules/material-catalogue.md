# Module — Material Catalogue

| Attribute | Value |
|-----------|--------|
| Status | **Current** — [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT** |
| Updated | 2026-08-30 |
| Code | `app/models/canonical_material.py`, `app/services/material_catalogue.py`, `app/routes/material_catalogue.py`, `/material-catalogue/` |
| Architecture | [../architecture/material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) |
| ADRs | [ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md) · [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) · [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** |

## Purpose

Own CalibAi **canonical material identity** (what the project requires): platform-seeded vocabulary, controlled requirement UOM, GENERIC vs SPECIFIED, lifecycle status.

V1 ([FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md)): dimensional lumber + sheet goods identity + office catalogue UX + optional Material-category `CostItem` link. Office kind/status labels use contractor-facing mapping ([FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) Slice 3); internal identity keys unchanged.

Living supplier price/promotion/inventory is **architected** ([ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md)) and **not** owned or implemented here until a later Feature Gate. [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) remains **Proposed**.

## Owned data (V1)

`canonical_materials`. Platform-seeded (27 V1 lumber/sheet rows). Not organization-owned.

## Referenced data

- `cost_items` (Estimating owns the row; optional FK to canonical material for category Material only)
- Assemblies only via existing `AssemblyItem → CostItem` (no AssemblyItem canonical FK in V1)

## Prohibited responsibilities

- Organization unit cost / markup (`CostItem`)
- Supplier SKU, price, promotion, inventory
- Bulk supplier catalogue onboarding / ingest / sync (future Supplier Catalogue pin; not this module’s V1 work)
- `MaterialRequirement` / TakeoffPackageItem commercial FKs. [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) V1 also does **not** create MaterialRequirement or commercial FKs on package items.
- Letting one organization mutate global identity for all organizations

## Relevant Feature Gate

[FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **LIVE-MIGRATED / UAT DEFECT — CLOSURE BLOCKED**.

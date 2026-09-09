# Module — Material Catalogue

| Attribute | Value |
|-----------|--------|
| Status | **Current** — [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. Thin `MaterialRequirement` under [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) / [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **implemented / not live-migrated**. |
| Updated | 2026-09-09 |
| Code | `app/models/canonical_material.py`, `app/models/material_requirement.py`, `app/services/material_catalogue.py`, `app/services/material_requirements.py`, `app/routes/material_catalogue.py`, `/material-catalogue/` |
| Architecture | [../architecture/material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) |
| ADRs | [ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md) · [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) · [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** |

## Purpose

Own CalibAi **canonical material identity** (what the project requires): platform-seeded vocabulary, controlled requirement UOM, GENERIC vs SPECIFIED, lifecycle status.

V1 ([FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md)): dimensional lumber + sheet goods identity + office catalogue UX + optional Material-category `CostItem` link. Office kind/status labels use contractor-facing mapping ([FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) Slice 3); internal identity keys unchanged.

Living supplier price/promotion/inventory is **architected** ([ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md)) and owned by Supplier Catalogue when implemented. [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**: this module owns thin project `MaterialRequirement` (FG-029 **implemented / not live-migrated**). [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) remains **Proposed**.

## Owned data (V1)

`canonical_materials`. Platform-seeded (27 V1 lumber/sheet rows). Not organization-owned. Thin project `material_requirements` (FG-029; supplier-neutral; **not live-migrated**).

## Referenced data

- `cost_items` (Estimating owns the row; optional FK to canonical material for category Material only)
- Assemblies only via existing `AssemblyItem → CostItem` (no AssemblyItem canonical FK in V1)

## Prohibited responsibilities

- Organization unit cost / markup (`CostItem`)
- Supplier SKU, price, promotion, inventory
- Bulk supplier catalogue onboarding / ingest / sync (future Supplier Catalogue pin; not this module’s V1 work)
- `MaterialRequirement` commercial mutation after REVIEWED except package copy. [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) assigns `MaterialRequirement` ownership here. [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) V1 does **not** create MaterialRequirement or commercial FKs on package items.
- Letting one organization mutate global identity for all organizations
- Storing scope-delivery routing on `CanonicalMaterial` or `MaterialRequirement` ([ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md); [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) Slice A **filters** Supplier Package eligibility only). Uncited MANUAL/DEMO requirements must not silently enter a Supplier Package.

## Relevant Feature Gate

[FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **LIVE-MIGRATED / UAT DEFECT — CLOSURE BLOCKED**.

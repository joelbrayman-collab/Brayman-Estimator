# Module — Supplier Catalogue

| Attribute | Value |
|-----------|--------|
| Status | **Current (partial)** — [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| Updated | 2026-09-09 |
| Code | `app/models/supplier_catalogue.py`, `app/services/supplier_catalogue.py`, `app/services/supplier_package_pdf.py`, `app/routes/supplier_package.py`, Hub PRICE `/projects/<id>/supplier-package` |
| Architecture | [../architecture/supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md) · [../architecture/supplier-channel-and-launch-partner.md](../architecture/supplier-channel-and-launch-partner.md) · [../architecture/material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) · [../architecture/fg-029-bmr-supplier-workflow-v1-preflight.md](../architecture/fg-029-bmr-supplier-workflow-v1-preflight.md) · [../architecture/fg-030-supplier-identity-and-access-isolation.md](../architecture/fg-030-supplier-identity-and-access-isolation.md) · [../architecture/fg-031-scope-delivery-make-buy-procurement-routing-preflight.md](../architecture/fg-031-scope-delivery-make-buy-procurement-routing-preflight.md) |

## Purpose

Own supplier identity, dealer SKUs, human-reviewed mapping, living inform-only price/availability evidence, and frozen Supplier Package HTML/PDF. Remain **supplier-neutral**: multiple competing suppliers are required; BMR Winchester is a contemplated **launch/reference** partner, not an exclusive supplier and not the CalibraytAI vocabulary ([ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md)).

## Owned data (FG-029)

`suppliers`, `supplier_locations`, `contractor_supplier_accounts`, `supplier_products`, `supplier_product_price_evidence`, `supplier_product_availability_evidence`, `canonical_material_supplier_maps`, `supplier_requirement_maps`, `supplier_packages`, `supplier_package_lines`. Additive migration **`b6c7d8e9f0a1` applied live**.

This module does **not** own CalibraytAI canonical material identity or thin `MaterialRequirement` (Material Catalogue).

Supplier named-user login, SupplierUserMembership, package sharing, and supplier workspace are [FG-030](../feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [ADR-047](../adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). This module will own those records **when implemented**. They do **not** exist in product code today.

[FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) later **filters** what may enter a Supplier Package: only `CONTRACTOR_PURCHASED` material is normally eligible. This module does **not** own routing. Uncited MANUAL/DEMO `MaterialRequirement` rows must not silently enter a package. FG-031 is **NOT IMPLEMENTATION-AUTHORIZED**. FG-030 remains who may see an issued package.

## Referenced data

Canonical materials and project `MaterialRequirement` (Material Catalogue); `organizations`; `projects`. Optional estimate-line citation stays on the requirement, not on the SKU.

## Future requirement pin (not implemented)

**Governed bulk supplier onboarding** is required later. Live BMR API, EDI, live inventory, PO submission, marketplace, and supplier-price → estimate cost remain out of FG-029. [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) remains **Proposed**.

## Prohibited responsibilities

- Owning CalibraytAI canonical material identity / taxonomy (Material Catalogue)
- Owning estimate or proposal commercial snapshots
- Silently refreshing prices on locked/accepted records or mutating `EstimateLineItem` / FG-027 costing / FG-009 Pricing
- Granting supplier / national / category exclusivity
- Implementing Darcy channel economics or Winchester live DEMO seed without a later Feature Gate
- Implementing bulk supplier onboarding, catalogue ingest, or live sync without a later Supplier Feature Gate

## Relevant ADRs

ADR-008, ADR-010 (Proposed). **ADR-033, ADR-034, ADR-035, ADR-036, ADR-046, ADR-047, ADR-048 Accepted**. This module does not own CalibraytAI identity. FG-030 and FG-031 are architecture only.

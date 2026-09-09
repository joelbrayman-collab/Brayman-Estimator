# Module — Supplier Catalogue

| Attribute | Value |
|-----------|--------|
| Status | **Current (partial)** — [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / NOT CLOSED** |
| Updated | 2026-09-09 |
| Code | `app/models/supplier_catalogue.py`, `app/services/supplier_catalogue.py`, `app/services/supplier_package_pdf.py`, `app/routes/supplier_package.py`, Hub PRICE `/projects/<id>/supplier-package` |
| Architecture | [../architecture/supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md) · [../architecture/supplier-channel-and-launch-partner.md](../architecture/supplier-channel-and-launch-partner.md) · [../architecture/material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) · [../architecture/fg-029-bmr-supplier-workflow-v1-preflight.md](../architecture/fg-029-bmr-supplier-workflow-v1-preflight.md) |

## Purpose

Own supplier identity, dealer SKUs, human-reviewed mapping, living inform-only price/availability evidence, and frozen Supplier Package HTML/PDF. Remain **supplier-neutral**: multiple competing suppliers are required; BMR Winchester is a contemplated **launch/reference** partner, not an exclusive supplier and not the CalibraytAI vocabulary ([ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md)).

## Owned data (FG-029)

`suppliers`, `supplier_locations`, `contractor_supplier_accounts`, `supplier_products`, `supplier_product_price_evidence`, `supplier_product_availability_evidence`, `canonical_material_supplier_maps`, `supplier_requirement_maps`, `supplier_packages`, `supplier_package_lines`. Additive migration **file** `b6c7d8e9f0a1` — **not applied live**.

This module does **not** own CalibraytAI canonical material identity or thin `MaterialRequirement` (Material Catalogue).

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

ADR-008, ADR-010 (Proposed). **ADR-033, ADR-034, ADR-035, ADR-036, ADR-046 Accepted**. This module does not own CalibraytAI identity.

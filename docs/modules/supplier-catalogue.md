# Module — Supplier Catalogue (proposed)

| Attribute | Value |
|-----------|--------|
| Status | **Future** — not implemented |
| Updated | 2026-08-30 |
| Code | None (only free-text `CostItem.supplier` exists in Estimating today) |
| Architecture | [../architecture/supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md) · [../architecture/supplier-channel-and-launch-partner.md](../architecture/supplier-channel-and-launch-partner.md) · [../architecture/material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) |

## Purpose

Manage suppliers, **supplier** catalogues (what the dealer sells), price lists, imports, and future live pricing/inventory sync; map those products **to** CalibAi Material Catalogue identity ([material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md)). Remain **supplier-neutral**: multiple competing suppliers are required; BMR Winchester is a contemplated **launch/reference** partner, not an exclusive supplier and not the CalibAi vocabulary ([ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md)).

## Owned data (intended)

Suppliers, branches, **supplier** catalogue products (SKU/pack/price), import/sync jobs. Later: contractor–supplier **procurement accounts** (relationship A) and CalibAi **channel partnerships** (relationship B) as distinct records — not a single PreferredSupplier field. This module does **not** own CalibAi canonical material identity.

## Referenced data

CalibAi canonical materials (Material Catalogue); internal cost items/assemblies via explicit mapping for costing; Projects for PO prep (future).

## Future requirement pin (not implemented)

**Governed bulk supplier onboarding** is required later: a supplier must not enter catalogue products one at a time. Lifecycle: SOURCE → BULK INGEST → SUPPLIER PRODUCTS → MAP TO CALIBAI CANONICAL MATERIALS → HUMAN REVIEW / EXCEPTIONS → ACTIVE SUPPLIER CATALOGUE → CONTINUING SYNCHRONIZATION. Initial onboarding (products + reviewed mappings) is distinct from ongoing sync (prices, promotions, inventory, availability, lifecycle) without unnecessarily remapping unchanged products.

This pin does **not** expand [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md), authorize supplier schema/ingestion, BMR/POC, live pricing/inventory, or a Supplier Feature Gate. Canonical record: [supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md).

## Prohibited responsibilities

- Owning CalibAi canonical material identity / taxonomy (Material Catalogue)
- Owning estimate or proposal commercial snapshots
- Silently refreshing prices on locked/accepted records
- Granting supplier / national / category exclusivity
- Implementing Darcy channel economics or Winchester POC analytics without a Feature Gate
- Implementing bulk supplier onboarding, catalogue ingest, or live sync without a later Supplier Feature Gate

## Relevant ADRs

ADR-008, ADR-010 (Proposed). **ADR-033, ADR-034, ADR-035, ADR-036 Accepted** (architecture only; not implemented). This module does not own CalibAi identity.

# Module — Supplier Catalogue (proposed)

| Attribute | Value |
|-----------|--------|
| Status | **Future** — not implemented |
| Updated | 2026-08-30 |
| Code | None (only free-text `CostItem.supplier` exists in Estimating today) |
| Architecture | [../architecture/supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md) · [../architecture/supplier-channel-and-launch-partner.md](../architecture/supplier-channel-and-launch-partner.md) |

## Purpose

Manage suppliers, catalogues, price lists, imports, and future live pricing/inventory sync; provide snapshottable prices to Estimating and future procurement. Remain **supplier-neutral**: multiple competing suppliers are required; BMR Winchester is a contemplated **launch/reference** partner, not an exclusive supplier ([ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md)).

## Owned data (intended)

Suppliers, branches, catalogue products, price lists, import/sync jobs. Later: contractor–supplier **procurement accounts** (relationship A) and CalibAi **channel partnerships** (relationship B) as distinct records — not a single PreferredSupplier field.

## Referenced data

Internal cost items/assemblies via explicit mapping; Projects for PO prep (future).

## Prohibited responsibilities

- Owning estimate or proposal commercial snapshots
- Silently refreshing prices on locked/accepted records
- Granting supplier / national / category exclusivity
- Implementing Darcy channel economics or Winchester POC analytics without a Feature Gate

## Relevant ADRs

ADR-008, ADR-010 (Proposed). **ADR-033 Accepted** (architecture only; not implemented).

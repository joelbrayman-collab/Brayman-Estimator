# Module — Supplier Catalogue (proposed)

| Attribute | Value |
|-----------|--------|
| Status | **Future** — not implemented |
| Updated | 2026-07-25 |
| Code | None (only free-text `CostItem.supplier` exists in Estimating today) |
| Architecture | [../architecture/supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md) |

## Purpose

Manage suppliers, catalogues, price lists, imports, and future live pricing/inventory sync; provide snapshottable prices to Estimating and future procurement.

## Owned data (intended)

Suppliers, branches, catalogue products, price lists, import/sync jobs.

## Referenced data

Internal cost items/assemblies via explicit mapping; Projects for PO prep (future).

## Prohibited responsibilities

- Owning estimate or proposal commercial snapshots
- Silently refreshing prices on locked/accepted records

## Relevant ADRs

ADR-008, ADR-010 (Proposed).

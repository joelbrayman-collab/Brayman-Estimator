# ADR-034 — Canonical Material Identity and Ownership

| Field | Value |
|-------|--------|
| Title | ADR-034: CalibAi Canonical Material Identity and Ownership |
| Status | **Accepted** (governance / architecture only; **not implemented**) |
| Date | 2026-08-30 |
| Related | [material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) · [ADR-035](ADR-035-material-quantity-uom-and-requirement-boundary.md) · [ADR-036](ADR-036-material-commercial-evidence-and-supplier-mapping.md) · [ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** · [ADR-029](ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** (labour analogy) · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) |

## Context

Estimating already owns org-scoped `CostItem` and `Assembly` (`app/models/cost_item.py`, `app/models/assembly.py`). `CostItem` carries `unit_cost`, `default_markup_percent`, mixed categories (Labour, Material, Equipment, Subcontractor, Allowance, Other), and optional free-text `supplier`. That is an organization **costing** record.

The intended CalibAi chain is plan → reviewed take-off → **what the project requires** → organization costing/composition → supplier fulfillment. If `CostItem` (or a first dealer SKU catalogue) becomes the platform vocabulary, CalibAi cannot stay supplier-neutral ([ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md)) or organization-neutral.

ADR-029 already rejected treating CostItem Labour as the production-rate engine. The same category error must not be repeated for materials.

This ADR does **not** authorize implementation, schema, migration, a Feature Gate, supplier integration, or a Winchester POC.

## Decision

### 1. CalibAi owns canonical material identity

CalibAi owns a **supplier-neutral, organization-neutral** canonical material vocabulary.

**Canonical Material answers: what does the project require?**

It does **not** own:

- organization unit cost
- organization markup
- supplier SKU
- supplier price (regular, contractor-specific, or promotional)
- inventory
- branch
- supplier availability

Organizations and suppliers **map to** the vocabulary. They do not define it.

### 2. CostItem remains the organization costing record

`CostItem` remains the **organization commercial / costing record**. Do not remove or repurpose it.

A **Material-category** `CostItem` may later reference **one** canonical material. Labour, Equipment, Subcontractor, Allowance, and Other CostItems do **not** require that link. Do not put canonical identity fields onto arbitrary CostItems.

Legacy free-text `CostItem.supplier` is not a supplier account, not a channel partnership, and not canonical identity ([ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md)).

### 3. Assemblies remain organization composition

`Assembly` / `AssemblyItem` remain organization-owned composition and costing structures. They are not the CalibAi material vocabulary. Future components may resolve to canonical materials ([ADR-035](ADR-035-material-quantity-uom-and-requirement-boundary.md)).

### 4. Supplier products map TO canonical materials

Future supplier SKUs map to canonical materials. BMR Winchester / Darcy may later be the first **reference mapping** target. They must **not** become the vocabulary ([ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md)).

### 5. GENERIC and SPECIFIED

Canonical identity supports **GENERIC** and **SPECIFIED** materials.

- GENERIC (example: 2×6 SPF No.2 or better, 12 ft) may map to multiple supplier products.
- SPECIFIED preserves genuine manufacturer/product requirements and defaults to **prohibit substitution** unless explicitly approved ([ADR-036](ADR-036-material-commercial-evidence-and-supplier-mapping.md)).

Do not force generic requirements into branded SKUs.

### 6. First bounded identity domain

First bounded identity domain: **dimensional lumber + sheet goods**.

Do not model all construction materials in V1.

### 7. User capability vs identity record

**Canonical Material** is the relatively stable identity record.

**Material Catalogue** is the future office **user-facing living intelligence capability**. That surface may later show identity, CostItem links, Assembly usage, supplier mappings, current regular/promotional prices, price history, inventory, quotes, historical org cost, and ORG-ACTUAL — without storing living commercial evidence on the identity row ([ADR-036](ADR-036-material-commercial-evidence-and-supplier-mapping.md)).

### 8. No implementation from this ADR

Accepting this ADR does **not** authorize product code, schema, migration, a Feature Gate, MaterialRequirement, Phase D, supplier SKUs, pricing, promotions, inventory, or Winchester demo.

Recommended later first Feature Gate: [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **IMPLEMENTED / VERIFIED / NOT LIVE-MIGRATED** — identity + CostItem link + office UX only.

## Alternatives Considered

- **Use CostItem as canonical identity** — Rejected: org-scoped costing, markup, mixed categories, free-text supplier; cannot be the multi-supplier vocabulary.
- **Org-owned material definitions first** — Rejected for V1 platform vocabulary: two organizations would not share identity; a first dealer mapping would attach to contractor codes rather than CalibAi.
- **Dealer SKU as identity (Winchester-first)** — Rejected: violates ADR-033 supplier neutrality.
- **Delay identity until Phase D or supplier Phase E** — Rejected: Phase D and supplier import would otherwise trap or invent vocabulary.

## Consequences

Positive: CostItem and Assemblies stay in Estimating; CalibAi can seed lumber/sheets; Winchester can later map *to* CalibAi.

Negative: a new domain (not implemented yet); CostItem will need an optional FK later; office users must learn identity vs costing.

## Module Ownership Impact

| Concern | Owner |
|---------|--------|
| Canonical material definitions / taxonomy / UOM vocabulary | **Material Catalogue** (new; not Estimating; not Supplier) |
| CostItem, Assembly, estimate lines | **Estimating** (unchanged) |
| Supplier SKU / price / inventory | **Supplier Catalogue** (future) |

## Data Ownership Impact

Canonical identity is CalibAi-seeded. Organization costing remains org-partitioned (`CostItem.organization_id`). Living commercial evidence is not stored on the identity row.

## Migration Impact

**Created** as [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) revision `d6e7f8a9b0c1`. Additive. **Not live-applied.** Do not rewrite historical cost lines into materials. Do not backfill identity from `CostItem.supplier`.

## Testing Impact

Dedicated FG-014 tests in `tests/test_material_catalogue_fg014.py`. CostItem unchanged for non-Material categories; identity has no unit_cost/SKU/price; org isolation of CostItem links.

## Documentation Impact

[material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md); ADR index; Estimating module; supplier architecture ownership wording.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Approved via Material Catalogue ADR governance prompt | 2026-08-30 |
| ChatGPT review | Architecture report + locked decisions | 2026-08-30 |
| Cursor implementation note | Docs/ADR only. No product code. | 2026-08-30 |

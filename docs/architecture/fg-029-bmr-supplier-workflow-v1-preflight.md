# FG-029 BMR / Supplier Workflow V1 — Architecture preflight

| Attribute | Value |
|-----------|--------|
| Status | **COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** (2026-09-09) |
| Date | 2026-09-09 |
| Gate | [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) |
| ADR | [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** |
| Alembic | Live current = heads **`a5b6c7d8e9f0`**. Proposed later revision **`b6c7d8e9f0a1`** — **not created**. |
| Product | CalibraytAI (formerly CalibAi) |

```text
FG-029 PREFLIGHT:
COMPLETE
NOT IMPLEMENTATION-AUTHORIZED
NO SCHEMA CREATED
NO PRODUCT CODE
ADR-008 REMAINS PROPOSED
REAL BMR INTEGRATION NOT AVAILABLE
```

This document pins the smallest additive schema, UI, outputs, and tests for a **later** implementation prompt. It does **not** authorize that prompt.

---

## 1. Honest demo spine

```text
ORG-001 PROJECT
→ HUMAN MaterialRequirement from FG-014 CanonicalMaterial
→ HUMAN map to labeled DEMO Winchester SKUs
→ INFORM-ONLY price + availability evidence
→ ISSUE Supplier Package (frozen)
→ HTML + PDF
```

FG-010 take-off remains **`INTERIOR_DOOR_OPENING` count only**. Demo lumber/OSB quantities are **not** extracted from drawings.

### Commercial story (do not overstate)

Contractor arrives with a reviewed requirement. Supplier avoids a duplicate take-off. Supplier maps to its products. Quotation and pick/load preparation are faster. Demand is visible earlier. Duplicate work drops.

**Do not claim** live BMR price, inventory, API, or a submitted purchase order.

---

## 2. Inspected existing boundaries (2026-09-09)

| Check | Result |
|-------|--------|
| A. CanonicalMaterial | **Exists.** 27 FG-014 lumber/sheet rows. Forbids SKU/price/inventory. |
| B. CostItem.canonical_material_id | **Exists** (optional, Material category). Free-text `supplier` is not an account. |
| C. TakeoffPackageItem | Quantity / citation / `element_type` only. No SKU. |
| D. FG-010 extractor | Interior door only. |
| E. FG-026 mapping | Assembly or CostItem → EstimateLineItem. No MaterialRequirement. |
| F. FG-027 costing | CURRENT snapshot required before Pricing. Recost → STALE pricing. |
| G. Supplier entity | **Does not exist.** |
| H. MaterialRequirement | **Does not exist.** |
| I. BMR files / API / CSV | **Absent.** REAL BMR INTEGRATION NOT AVAILABLE. |
| J. Purchase Orders nav | Disabled placeholder. |
| K. Construction-sequence engine | **Does not exist.** |
| L. ADR-008 | **Proposed.** |

---

## 3. Proposed additive schema (do not create now)

All FKs **ON DELETE RESTRICT** unless noted. Timestamps `DateTime`, not null on insert. Do not mutate `canonical_materials`, takeoff tables, CostItem/Assembly schemas, costing snapshots, or pricing snapshots in V1-03.

### 3.1 `suppliers` — Supplier Catalogue

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `code` | String(80) | no | Unique. Demo: `BMR-WINCHESTER` |
| `legal_name` | String(220) | no | |
| `status` | String(20) | no | `ACTIVE` \| `INACTIVE` CHECK |
| `demo_synthetic` | Boolean | no | default true for V1 seed |
| `created_at` | DateTime | no | |

**Unique:** `code`. Not a CalibraytAI tenant. Not Brand Profile.

### 3.2 `supplier_locations`

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `supplier_id` | Integer FK `suppliers.id` | no | indexed |
| `code` | String(80) | no | e.g. `WINCHESTER` |
| `display_name` | String(220) | no | |
| `status` | String(20) | no | `ACTIVE` \| `INACTIVE` |
| `demo_synthetic` | Boolean | no | |
| `created_at` | DateTime | no | |

**Unique:** (`supplier_id`, `code`).

### 3.3 `contractor_supplier_accounts` — relationship A only

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `organization_id` | String(50) FK `organizations.id` | no | indexed |
| `supplier_id` | Integer FK | no | |
| `supplier_location_id` | Integer FK | no | |
| `status` | String(20) | no | `ACTIVE` \| `INACTIVE` |
| `demo_synthetic` | Boolean | no | |
| `created_at` | DateTime | no | |

**Unique:** (`organization_id`, `supplier_id`, `supplier_location_id`). Channel partnership (B) is **not** this table.

### 3.4 `supplier_products`

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `supplier_id` | Integer FK | no | indexed |
| `sku` | String(80) | no | dealer SKU |
| `description` | String(220) | no | |
| `sales_uom` | String(20) | no | supplier pack UOM |
| `pack_qty` | Numeric(12, 4) | yes | |
| `status` | String(20) | no | `ACTIVE` \| `INACTIVE` |
| `demo_synthetic` | Boolean | no | |
| `created_at` | DateTime | no | |

**Unique:** (`supplier_id`, `sku`).

### 3.5 `supplier_product_price_evidence`

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `supplier_product_id` | Integer FK | no | indexed |
| `contractor_supplier_account_id` | Integer FK | yes | contractor-specific if present |
| `amount` | Numeric(12, 4) | no | |
| `currency` | String(8) | no | e.g. `CAD` |
| `unit` | String(20) | no | price UOM |
| `effective_from` | DateTime | yes | |
| `captured_at` | DateTime | no | |
| `source` | String(40) | no | `DEMO_SYNTHETIC` \| later `MANUAL` / adapter |
| `actor_display_name` | String(150) | no | |
| `demo_synthetic` | Boolean | no | |
| `created_at` | DateTime | no | |

Living evidence. **Not** written to `EstimateLineItem`.

### 3.6 `supplier_product_availability_evidence`

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `supplier_product_id` | Integer FK | no | |
| `supplier_location_id` | Integer FK | no | |
| `status` | String(20) | no | `IN_STOCK` \| `LIMITED` \| `UNKNOWN` CHECK |
| `captured_at` | DateTime | no | |
| `source` | String(40) | no | |
| `actor_display_name` | String(150) | no | |
| `demo_synthetic` | Boolean | no | |
| `created_at` | DateTime | no | |

No on-hand quantity. No live inventory API.

### 3.7 `canonical_material_supplier_maps`

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `canonical_material_id` | Integer FK `canonical_materials.id` | no | indexed |
| `supplier_product_id` | Integer FK | no | indexed |
| `requirement_to_sales_factor` | Numeric(12, 6) | yes | pack conversion on **mapping**, not identity |
| `status` | String(20) | no | library map `ACTIVE` \| `INACTIVE` |
| `approved_by_display_name` | String(150) | yes | |
| `approved_at` | DateTime | yes | |
| `demo_synthetic` | Boolean | no | |
| `created_at` | DateTime | no | |

**Unique** while ACTIVE: (`canonical_material_id`, `supplier_product_id`). One CanonicalMaterial → many products.

### 3.8 `material_requirements` — Material Catalogue

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `organization_id` | String(50) FK | no | indexed |
| `project_id` | Integer FK `projects.id` | no | indexed |
| `canonical_material_id` | Integer FK | no | indexed |
| `quantity` | Numeric(14, 4) | no | |
| `canonical_uom` | String(8) | no | `EA` \| `LF` \| `SF` \| `BF` |
| `status` | String(20) | no | `DRAFT` \| `REVIEWED` CHECK |
| `source_kind` | String(40) | no | `MANUAL` \| `DEMO_SYNTHETIC` \| `ESTIMATE_LINE_CITE` \| `TAKEOFF_CITE` |
| `estimate_line_item_id` | Integer FK | yes | citation only |
| `note` | Text | yes | not pricing policy |
| `actor_display_name` | String(150) | no | |
| `created_at` | DateTime | no | |
| `updated_at` | DateTime | no | DRAFT only; REVIEWED is stable until package copy |

**No** supplier_id, sku, price, availability, markup.

### 3.9 `supplier_requirement_maps` — per-package mapping review

Project-scoped mapping of a requirement to a SKU for one supplier location.

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `organization_id` | String(50) | no | indexed |
| `project_id` | Integer | no | indexed |
| `material_requirement_id` | Integer FK | no | indexed |
| `supplier_id` | Integer FK | no | |
| `supplier_location_id` | Integer FK | no | |
| `supplier_product_id` | Integer FK | yes | null when `UNRESOLVED` |
| `mapping_status` | String(20) | no | `UNRESOLVED` \| `REVIEW_REQUIRED` \| `MAPPED` CHECK |
| `actor_display_name` | String(150) | no | |
| `mapped_at` | DateTime | yes | |
| `demo_synthetic` | Boolean | no | |
| `created_at` | DateTime | no | |

**Unique:** (`material_requirement_id`, `supplier_id`, `supplier_location_id`) for the current review set (application-enforced CURRENT, or unique if one map row per triple).

### 3.10 `supplier_packages` / `supplier_package_lines` — frozen artifact

**Header** `supplier_packages`

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `organization_id` | String(50) | no | indexed |
| `project_id` | Integer | no | indexed |
| `supplier_id` | Integer | no | |
| `supplier_location_id` | Integer | no | |
| `contractor_supplier_account_id` | Integer | no | |
| `status` | String(20) | no | `DRAFT` \| `ISSUED` CHECK |
| `demo_synthetic` | Boolean | no | |
| `issued_at` | DateTime | yes | required when ISSUED |
| `issued_by_display_name` | String(150) | yes | |
| `created_at` | DateTime | no | |

**Unique application rule:** at most one `ISSUED` current package per (`project_id`, `supplier_id`, `supplier_location_id`) **or** supersession later; V1 may allow one ISSUED + prior superseded if needed. Prefer: ISSUED rows **immutable** (`before_update` / `before_delete` raise except a narrow DRAFT→ISSUED transition).

**Lines** `supplier_package_lines` — **frozen copies**, not live FKs for commercial facts after issue:

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `supplier_package_id` | Integer FK | no | indexed |
| `material_requirement_id` | Integer | no | provenance id |
| `canonical_material_code` | String(80) | no | frozen |
| `canonical_material_name` | String(220) | no | frozen |
| `requirement_qty` | Numeric(14, 4) | no | frozen |
| `requirement_uom` | String(8) | no | frozen |
| `mapping_status` | String(20) | no | frozen |
| `supplier_sku` | String(80) | yes | null if unresolved |
| `supplier_product_description` | String(220) | yes | |
| `sales_qty` | Numeric(14, 4) | yes | after conversion if mapped |
| `sales_uom` | String(20) | yes | |
| `price_amount` | Numeric(12, 4) | yes | frozen evidence |
| `price_currency` | String(8) | yes | |
| `price_captured_at` | DateTime | yes | |
| `availability_status` | String(20) | yes | |
| `availability_captured_at` | DateTime | yes | |
| `delivery_stage` | String(40) | yes | human grouping, e.g. `FRAMING` / `SHEATHING` |
| `demo_synthetic` | Boolean | no | |
| `evidence_source` | String(40) | no | |

Issued lines are **immutable**. Living catalogue changes must not rewrite them.

---

## 4. UI (later implementation)

No new lifecycle stage. Project Hub **PRICE**:

`/projects/<id>/supplier-package`

Concepts: Supplier Package · Mapping Review · Mapped · Unresolved · Price / Availability Evidence · Delivery Group · Generate / Issue Supplier Package.

Office chrome remains **Brayman Construction Platform**. Product name in package header: **CalibraytAI**. Contractor: Brand Profile / Brayman Construction Inc. Do not swap tenant identity for CalibraytAI or vice versa.

Do **not** enable Purchase Orders nav as a live module.

---

## 5. HTML + PDF output

One snapshot, two renderings (Permit-report pattern).

Must show: contractor, project, supplier, branch, package status, each line’s requirement + CanonicalMaterial + SKU/description + qty/unit + price evidence + availability + mapping status + delivery stage; unresolved items listed; **DEMO / SYNTHETIC** banner when `demo_synthetic`.

Must **not** trigger API or order side effects. Must **not** expose supplier unit cost on the **customer** Proposal (FG-012). This package is **supplier-facing**, not customer-facing estimate output.

Pick/load: SKU, sales qty, sales UOM, branch, delivery stage on the same document. Not WMS.

Delivery grouping: human `delivery_stage` string. Not fleet, routing, trucking, warehouse, ERP, or live booking.

Order: package may be labeled **order-ready / review-ready**. **Not** a submitted PO. Live electronic order submission **OUT OF V1-03**.

---

## 6. FG-027 / Pricing interaction

V1-03 **does not bypass** Costing Review, Approve All Costing, costing snapshots, or Pricing stale/reapply.

Inform-only supplier evidence **does not** change working `EstimateLineItem.unit_cost`, CURRENT costing snapshots, or `EstimatePricingSnapshot`.

Supplier price → working cost is **OUT OF FG-029**. A future authorization (ADR-008 or successor) must govern any such consumption. If ever authorized, apply would be explicit `MANUAL_OVERRIDE` and would recost / stale Pricing — **not this gate**.

---

## 7. Demo seed (do not populate now)

| Identity | Use |
|----------|-----|
| Supplier + Winchester location | Labeled DEMO |
| ORG-001 account | Relationship A |
| Products | 3–5 DEMO SKUs mapped to `CAL-LUM-2X6-12` and `CAL-SHT-OSB-7-16-4X8` (optional 2×4 stud). **Not** housewrap. **Not** ½″ drywall. **Not** a 2×6 stud identity (no FG-014 seed). |

---

## 8. Scope splits

### V1-03 required for BMR demo

ADR-046 / this gate implemented later: schema, seed, Hub UI, mapping review, frozen package, HTML/PDF, tests.

### Required for Brayman real-life UAT (supplier)

Same manual/DEMO workflow is sufficient. Live BMR **not** required. UAT still blocked by V1-10, legal fail-closed / Ontario, V1-11.

### Maturation during UAT

More SKUs; pack-rounding UX; CSV replacing seed; optional apply-to-cost **after** ADR-008.

### Post-V1

Live adapter; inventory API; EDI; POs; bulk onboarding; other dealers; channel partnership B; Darcy economics; marketplace; promotions engine.

---

## 9. Test plan (later — do not implement now)

MaterialRequirement org/project isolation · CanonicalMaterial mapping · Supplier + branch identity · SupplierProduct/SKU · `UNRESOLVED` / `REVIEW_REQUIRED` / `MAPPED` · human mapping actor/time · DEMO_SYNTHETIC provenance · price evidence · availability evidence · issued package immutability (living seed change does not float) · HTML · PDF · delivery_stage · **no PLAN mutation** · **no TakeoffPackage supplier fields** · **no silent EstimateLineItem cost mutation** · **no FG-027 costing mutation** · **no Pricing mutation** · **no external order** · tenant isolation · ADR-008 still Proposed · no LEARN

---

## 10. Unresolved Joel decisions (do not invent)

1. Optional 2×4 stud line vs lumber + OSB only.
2. Whether BMR demo script still requires a contract story (register §10.2) after V1-03 exists.
3. When to authorize FG-029 **implementation** (separate prompt).
4. Whether apply-to-estimate is ever wanted (needs ADR-008/successor).

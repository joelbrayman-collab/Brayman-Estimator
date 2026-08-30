# Feature Gate FG-014: Material Catalogue V1 — Dimensional Lumber + Sheet Goods

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-014` |
| Feature Name | Material Catalogue V1 — Dimensional Lumber + Sheet Goods |
| Target Milestone | **None.** FG-014 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Material Catalogue** (canonical identity). Estimating retains `CostItem` / `Assembly` / `EstimateLineItem`. |
| Date | 2026-08-30 |
| Status | **LIVE-MIGRATED / FLASH REPAIR APPLIED — OFFICE RE-UAT REMAINING** |
| Architecture | [material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) |
| Related ADRs | [ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md) **Accepted** · [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) **Accepted** · [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** · [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) |
| Prerequisites | FG-013 **CLOSED / OPERATIONAL FOR UAT**. ADR-034/035/036 **Accepted**. |
| Approved baseline | Gate-approval HEAD `273803b75b6bcbe6ae56fbf3274cd4a2dafcec36`. Implementation `976cc4a4942ae346b9843a77126f89969bba2b6e`. Live-migrate/UAT starting HEAD `a100caa`. Live current = head **`d6e7f8a9b0c1`**. Flash-repair starting HEAD `3e671f20a561b4c70bc837486f59f93a150f7fee`. Dedicated FG-014 **35 passed**. Full suite **345 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **LIVE-MIGRATED / FLASH REPAIR APPLIED — OFFICE RE-UAT REMAINING** |
| Implementation | **DONE** in product code. Office UX `/material-catalogue/`. Catalogue-link flash repaired 2026-08-30. |
| Schema / Alembic | **Live current = head = `d6e7f8a9b0c1`** (applied 2026-08-30). One graph head. Unchanged by the flash repair. |
| Browser / office UAT | **RE-UAT REMAINING** — product-code flash repair + dedicated tests applied. Short office re-UAT of the catalogue link error path is required before gate close. |
| Living supplier pricing / promotions / inventory | **OUT OF SCOPE** (unchanged) |
| Phase D / MaterialRequirement / supplier SKU | **OUT OF SCOPE** (unchanged) |

This gate does **not** authorize supplier integration, bulk supplier catalogue onboarding, Winchester POC, ADR-008 acceptance, Phase D, procurement, ORG-ACTUAL, or LEARN.

### Live-migrate / UAT finding (2026-08-30)

**Do not close FG-014** until the office catalogue link error path is repaired and re-UAT'd.

| Field | Content |
|-------|---------|
| Reproduction | `POST /material-catalogue/7/link` with `cost_item_id` of Labour `FG014-UAT-LAB` (id 5), Equipment 6, Subcontractor 7, Allowance 8, Other 9, or cross-org Material 10 |
| Expected | Fail closed **and** flash the service reason, e.g. `Labour cost items cannot link to a canonical material.` / `Cost item not found in current organization.` |
| Actual | Fail closed on data (`canonical_material_id` remains `NULL`) but flash is `Select a Material cost item to link.` |
| Acceptance criterion | AC 7 (improper link rejected / caller told) plus prompt rule: do not silently mishandle invalid values |
| Likely cause (do not repair here) | `MaterialCatalogueError` subclasses `ValueError`. `link_cost_item` catches `(TypeError, ValueError)` **before** `MaterialCatalogueError`, so the specific message is swallowed. Cost Library edit of Labour with a canonical id **does** show the correct `cannot link` flash. |
| Service / tests | `link_material_cost_item` still raises `MaterialCatalogueError` (`cannot link`). Dedicated tests **28 passed**. Full suite **338 passed**. |

Ordinary org UX still cannot create/edit/delete canonical identity. Material link/unlink of `FG014-UAT-MAT` worked. Isolation GET `/cost-library/10/edit` is **404**. Seed 27 rows. No supplier/Phase D leakage.

**Code:** `app/models/canonical_material.py`, `app/services/material_catalogue.py`, `app/routes/material_catalogue.py`, optional `CostItem.canonical_material_id` in `app/models/cost_item.py`, revision `migrations/versions/d6e7f8a9b0c1_add_material_catalogue_identity_fg014.py`. Platform seed is 27 lumber/sheet rows keyed by `CAL-*` codes.

### Flash repair (2026-08-30)

**Do not close FG-014** until a short office re-UAT of the catalogue link error path is recorded.

| Field | Content |
|-------|---------|
| Root cause | Confirmed: `MaterialCatalogueError` subclasses `ValueError`. `link_cost_item` caught `(TypeError, ValueError)` **before** `MaterialCatalogueError`, so service reasons were replaced by `Select a Material cost item to link.` |
| Repair | Catch `MaterialCatalogueError` first; keep `(TypeError, ValueError)` only for non-integer / empty `cost_item_id`. Unlink exception order was already correct and was not changed. Link/unlink success semantics, org isolation, Material-only enforcement, and read-only canonical identity are unchanged. |
| Tests | Dedicated FG-014 **35 passed** (was 28). Full suite **345 passed** (was 338). |
| Live POST check | `POST /material-catalogue/7/link` with Labour `FG014-UAT-LAB` (id 5) on port **5006** (repaired code) returned 302 with session flash `Labour cost items cannot link to a canonical material.` `canonical_material_id` remained `NULL`. |
| Next | Office re-UAT of non-Material / cross-org flashes on the office app, then close the gate. Do not start Permit Intelligence or another Feature Gate. |

---

## Purpose

Create the first bounded **CalibAi Material Catalogue identity** layer: a supplier-neutral, organization-neutral vocabulary for **dimensional lumber + sheet goods**, and an optional human-controlled link from **Material-category** organization `CostItem` rows to that vocabulary.

This gate is **not** supplier integration, **not** Phase D, and **not** living supplier pricing.

Office success: users can **search/browse** canonical materials and **link/unlink** their Material CostItems. Success is **IDENTITY CATALOGUE READY**, not COST MODEL COMPLETE and not SUPPLIER PRICING LIVE.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | CalibAi has no platform material vocabulary. `CostItem` is org costing (unit cost, markup, free-text supplier) and cannot be the multi-supplier identity ([ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md)). |
| 2 | Who is the user? | Office estimator / Joel on the **current unauthenticated office app**. Ordinary org actions must not mutate global canonical definitions for all organizations. |
| 3 | Which module owns it? | **Material Catalogue** owns canonical identity. **Estimating** owns `CostItem` (optional FK only). Supplier Catalogue does **not** own identity. |
| 4 | What data does it own? | `canonical_materials` (platform-seeded identity). Not CostItem unit_cost. Not SKU/price/inventory. |
| 5 | What data does it reference? | `organizations` (via CostItem). `cost_items` for optional Material-category links. Assemblies only as existing `AssemblyItem → CostItem` (read-through). |
| 6 | What may implementation change? | Canonical material model + seed; optional `CostItem.canonical_material_id`; office Material Catalogue UX; dedicated tests; governed docs; **one** additive migration under the **implementation** prompt. |
| 7 | What must it not change? | TakeoffPackageItem; Assembly schema (no direct canonical FK); labour/pricing engines; historical evidence auto-mapping; CostItem.unit_cost meaning; Desktop corpus; supplier/Winchester data; ADR-008 status. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. |
| 9 | Tests required? | Dedicated FG-014 tests; CostItem/Assembly/estimate regressions; labour; pricing; historical ingestion; full suite before closure. |
| 10 | Documentation? | This gate; module stub; architecture cross-refs; indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log. |
| 11 | ADR required? | **No new ADR.** Covered by ADR-034/035/036. If implementation exposes an uncovered conflict: **STOP** — do not invent an ADR inside the implementation prompt. |
| 12 | Migration? | **YES — one bounded additive revision** in the implementation prompt only. Expected: `canonical_materials` + optional `cost_items.canonical_material_id` + indexes/constraints + **platform seed rows**. Do not apply live until a separate live-migrate prompt if that remains the established workflow. |

---

## Owner

| Concern | Owner |
|---------|--------|
| Canonical material identity, taxonomy, controlled UOM, seed vocabulary | **Material Catalogue** ([material-catalogue.md](../modules/material-catalogue.md)) |
| CostItem, Assembly, EstimateLineItem | **Estimating** (unchanged ownership) |
| SKU / price / promotion / inventory | **Supplier Catalogue** (future; out of this gate) |

---

## Canonical identity model (V1)

Supplier-neutral identity only. Conceptual fields (exact column names are implementation detail; must not add commercial feed fields):

| Field | Notes |
|-------|--------|
| id | Durable PK |
| stable code | Unique platform code |
| display name | Office list/search |
| active / discontinued | Lifecycle; do not physically delete once referenced |
| kind | `GENERIC` or `SPECIFIED` |
| trade / category | e.g. dimensional lumber, sheathing |
| canonical UOM | Controlled vocabulary (see UOM) |
| dimensional characteristics | Nominal thickness × width; length class and/or sheet size as applicable |
| grade / species / performance class | Where appropriate for generics |
| specification / manufacturer text | **SPECIFIED only**, and only where genuinely required. Not a dealer SKU. |
| substitution policy / state | Vocabulary; specified defaults toward prohibit |
| concise description | Human-readable requirement |

**Forbidden on this table:** unit_cost, markup, supplier SKU, supplier price, promotional price, inventory, branch, quote, project pricing, supplier account, live feed timestamps as identity facts.

Do not overbuild versioning in V1. Prefer **ACTIVE / DISCONTINUED** (and supersession later if needed). Once referenced, do not physical-delete.

---

## CalibAi-seeded catalogue

**Scope:** dimensional lumber + sheet goods only. Not all construction materials.

**Seed mechanism (locked):** the **same additive Alembic revision** that creates the table **inserts** the platform seed rows, keyed by stable code (idempotent on upgrade; not ORG-001 owned). This matches governed migration-seed practice (e.g. FG-008 policy seed is org-scoped; this seed is **platform**). Do **not** bootstrap from BMR/web catalogues. Do **not** copy supplier SKUs.

The **implementation prompt** must include an explicit seed inventory (codes, names, kinds, UOMs, dimensions) large enough to prove identity, GENERIC vs SPECIFIED, UOM, search, and CostItem linking — typically on the order of **tens of rows**, not hundreds. At least one GENERIC lumber, one GENERIC sheet, and one SPECIFIED (named product, **not** a dealer SKU) are required.

Do not include BMR data or supplier pricing in the seed.

---

## CostItem link

- Optional `canonical_material_id` on `CostItem`.
- **Only** `category = Material` may set it. Non-Material categories must **fail closed** if a link is attempted.
- Do not remove or repurpose existing CostItem fields.
- Existing CostItems remain valid with **NULL** link.
- **No automatic backfill** from `CostItem.name`, `CostItem.supplier`, or historical free text.
- Link/unlink is **human-controlled** in office UX, scoped to the current organization.

Assemblies: **no redesign**. If an `AssemblyItem` points at a linked Material CostItem, canonical identity may be **displayed** as a read-through. No `AssemblyItem` canonical FK. No exploded fulfillment package.

---

## Office UX

Bounded office **MATERIAL CATALOGUE**:

- list / search
- category/trade filter
- code, description, UOM, GENERIC vs SPECIFIED, substitution policy, active/discontinued
- linked **this-organization** Material CostItems
- human link/unlink

No decorative analytics. **Do not show fake live supplier prices, promotions, or inventory.** Copy must not imply living supplier data is operational.

**Editability (V1 locked):**

| Object | Who may change |
|--------|----------------|
| Canonical identity fields / seed | **Platform-governed.** Ordinary org/office users **must not** mutate global definitions. V1 identity is seed + read-only in office UX (status visible). No org-wide rewrite path in this gate. |
| Material CostItem ↔ canonical link | **Organization-editable** (current office actor), tenant-scoped. |

---

## Controlled UOM

Smallest lumber/sheet vocabulary: **`EA`**, **`LF`**, **`SF`**, **`BF`**.

Do not implement supplier pack conversion. Do not treat free-text `CostItem.unit` as canonical authority.

---

## Waste

**No waste on Canonical Material.** Existing `AssemblyItem.waste_percent` / `EstimateLineItem.waste_percent` unchanged. No universal waste defaults.

---

## Out of scope (binding)

- `MaterialRequirement`
- Phase D; any TakeoffPackageItem FK to CostItem, Canonical Material, or SKU
- Supplier / SupplierLocation / SupplierProduct / SKU / MaterialSupplierMapping
- **Bulk supplier catalogue onboarding, ingest, feed, SFTP, API/ERP/POS, EDI, or continuing supplier sync** (future pin only — [supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md); **not** a Supplier Feature Gate)
- Price, promotion, inventory, branch, quote operationalization
- BMR Winchester demo data, Darcy portal, fulfillment, channel analytics
- Material Cost Standard; changing `CostItem.unit_cost` meaning
- Accepting or implementing ADR-008
- ORG-ACTUAL, LEARN, benchmarking, legal library
- Auth product

---

## Tenant / org boundary

Canonical materials are **platform-level shared identity**.

Organization CostItem links, unit_cost, markup, preferences, and historical mappings remain **organization-scoped**. Cross-org costing access **fails closed**.

---

## Schema / migration (implementation prompt only)

| Item | This governance pass | Implementation prompt |
|------|----------------------|------------------------|
| SCHEMA CHANGE | Expected **YES** | Create additive tables/columns |
| MIGRATION | Expected **YES** — one bounded additive revision | Create + tests; do not generate casually; live apply only if that prompt authorizes it |

Likely surfaces: `canonical_materials`; unique `code`; check constraints for kind/UOM/status; `cost_items.canonical_material_id` nullable FK; indexes.

---

## Acceptance criteria

1. CalibAi canonical materials exist independently of organizations.
2. V1 limited to dimensional lumber + sheet goods (seed + UX).
3. No supplier SKU/price/inventory fields on canonical identity.
4. GENERIC and SPECIFIED kinds supported.
5. Controlled canonical UOM (`EA` / `LF` / `SF` / `BF`) supported.
6. Material-category CostItem may link to canonical material.
7. Non-Material CostItems remain unaffected; improper link **rejected**.
8. Existing CostItems remain valid without links.
9. No automatic backfill from CostItem names/supplier text.
10. No automatic historical mapping.
11. Org CostItem links remain tenant-scoped.
12. One org cannot see another org’s costing records.
13. Platform canonical identity cannot be mutated by ordinary org actions.
14. Office Material Catalogue search/list works.
15. Human-controlled link/unlink of organization Material CostItems works.
16. Active/discontinued state behaves safely (no physical delete of referenced identity).
17. No waste on canonical identity.
18. No MaterialRequirement.
19. No Phase D / TakeoffPackageItem material FKs.
20. No Supplier/SKU model.
21. No BMR demo data.
22. No live supplier price.
23. No promotions/sales implementation.
24. No inventory.
25. No procurement/PO/fulfillment.
26. ADR-008 remains Proposed.
27. No ORG-ACTUAL/LEARN.
28. Dedicated tests pass.
29. Relevant regressions pass (CostItem/Assembly/estimate, labour, pricing, historical).
30. Full suite passes.
31. Documentation reconciled before gate closure.

---

## Test / UAT plan (implementation)

Synthetic/UAT records only. **No BMR data.**

- Seed catalogue created; stable code uniqueness
- GENERIC lumber; GENERIC sheet; SPECIFIED (non-SKU)
- Controlled UOM validation
- Active/discontinued
- Material CostItem link/unlink; NULL remains valid
- Non-Material CostItem cannot link
- No automatic backfill
- Org isolation; cross-org fail closed
- Platform identity shared (same canonical row visible to more than one org’s catalogue UX)
- No price/SKU/inventory columns
- Search/filter UX
- Assembly/Estimate regressions (read-through display only if implemented)
- Labour, pricing, historical ingestion regressions
- Full suite

---

## Explicit non-goals

Supplier integration; Winchester POC; **bulk supplier onboarding / ingest / sync**; living prices/promotions/inventory; pack conversion; MaterialRequirement; Phase D; Material Cost Standard; Assembly explosion/fulfillment; procurement; ADR-008; LEARN; legal library; modeling all construction materials. No Supplier Feature Gate.

# Architecture — CalibAi Material Catalogue

| Attribute | Value |
|-----------|--------|
| Status | **Intended architecture** (documented; **not implemented**) |
| Date | 2026-08-30 |
| Product | The Estimator / CalibAi |
| Implementation | [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED** (identity + CostItem link + office UX only). This architecture document does **not** implement product code. Governing ADRs: [ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md), [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md), [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted**. |
| Related | [ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md) **Accepted** · [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) **Accepted** · [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** · [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** · [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** (labour analogy) · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (not accepted with identity) · [supplier-catalogue-inventory-pricing.md](supplier-catalogue-inventory-pricing.md) · [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) · [modules/estimating.md](../modules/estimating.md) · [plan-intelligence-and-automated-takeoff.md](plan-intelligence-and-automated-takeoff.md) |

**Current vs intended vs future:** Today Estimating owns org-scoped `CostItem` and `Assembly` (`app/models/cost_item.py`, `app/models/assembly.py`). There is **no** Material Catalogue table, **no** canonical material identity, **no** `MaterialRequirement`, and **no** supplier SKU entity. Nothing below is claimed as implemented.

---

## 1. Purpose

The Material Catalogue is **not** merely a static product dictionary. The user-facing capability must eventually operate as a **living source of material intelligence**.

Define a **supplier-neutral, organization-neutral** CalibAi vocabulary for **what a project requires**, so that:

- organizations can cost and compose work with existing `CostItem` / `Assembly` records
- future suppliers (including a later BMR Winchester reference mapping) can fulfill the same requirement without becoming the vocabulary
- reviewed take-off can later feed both estimating and fulfillment without trapping supplier-useful quantities inside a rolled-up `EstimateLineItem`
- current estimating can consume **current valid** supplier evidence while locked commercial history stays immutable

Long-term commercial chain (intended; mostly unimplemented past take-off packages):

```text
PLAN
→ REVIEWED TAKE-OFF
→ CALIBAI MATERIAL CATALOGUE (what is required)
→ ORGANIZATION COSTITEM / ASSEMBLY (how this contractor costs / composes)
→ SUPPLIER CATALOGUE MAPPING (what a supplier sells)
→ PRICE / INVENTORY
→ PROCUREMENT / FULFILLMENT
```

[ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) is binding: CalibAi remains multi-supplier; BMR Winchester is a prospective launch/reference partner, not the material identity.

---

## 2. Binding distinctions

| Record | Meaning | Owner |
|--------|---------|--------|
| **Canonical material identity** | Relatively stable definition of **what the material is** | **CalibAi platform** (seeded vocabulary) |
| **Living commercial / supplier evidence** | Time-sensitive fulfillment facts (price, promotion, SKU, pack, inventory, quote, timestamps) | Future Supplier / Quote / Snapshot records — **not** the identity row |
| **CostItem / Assembly** | How this organization costs and composes it | **Organization** (Estimating module) |
| **Supplier Catalogue** (future) | What a supplier sells (SKU, pack, price, stock, promotions) | **Supplier module** (proposed; not implemented) |
| **Mapping** (future) | How one requirement may be fulfilled by one or more supplier products | Mapping records; not the material definition |
| **Project commercial snapshot** | Exact evidence consumed on a locked estimate, accepted proposal, accepted quote, or approved order | Project / Estimating / future Procurement |

**Material Catalogue as user capability** is the office surface that may present identity, mappings, current prices, promotions, inventory, quotes, and history together.

**Canonical material table** is one underlying domain record (identity). Do not store living commercial evidence on that row.

Do **not** collapse these into `CostItem.supplier`, a PreferredSupplier field, a single `CURRENT_PRICE`, or a dealer SKU.

---

## 3. CostItem is not canonical identity

`CostItem` remains the **organization-specific commercial / costing record**. It may continue to own:

- `organization_id`, `code`, `name`, `category`
- `unit`, `unit_cost`, `default_markup_percent`
- existing organization-specific commercial evidence
- optional free-text `supplier` (legacy convenience; not ADR-033 relationship A or B)

Do **not** remove or repurpose `CostItem`.

This follows the same boundary already accepted for labour: [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) rejected treating CostItem Labour as the production-rate engine. Lump `unit_cost`, org markup, and free-text supplier cannot serve as CalibAi material identity, multi-supplier mapping target, or platform vocabulary.

**Authorized for later FG-014 implementation (not started):** a Material-category `CostItem` may reference **one** canonical material. Labour, Equipment, Subcontractor, Allowance, and Other CostItems do **not** require that link. Do not put canonical identity fields onto arbitrary CostItems.

---

## 4. Canonical material — CalibAi-seeded

**CALIBAI CANONICAL MATERIAL = what the project requires.**

It is supplier-neutral and organization-neutral. Organizations and suppliers **map to** the vocabulary; they do not define it.

Canonical material must **not** directly contain:

- supplier SKU
- live supplier price
- contractor-specific supplier price
- inventory
- branch availability
- project quote price
- retrieved_at / effective / expiry of supplier data

Those belong to future Supplier / Quote / Snapshot records.

---

## 5. V1 identity scope

Recommended first bounded catalogue:

**Dimensional lumber + sheet goods.**

Minimum justified V1 fields (conceptual; no schema in this pass):

| Field | Role |
|-------|------|
| Stable code / id | Durable identity |
| Display name | Office search / list |
| Active / discontinued | Lifecycle |
| GENERIC vs SPECIFIED | Requirement kind |
| Trade / category | Framing lumber, sheathing, … |
| Canonical requirement UOM | Controlled list (not free-text `CostItem.unit`) |
| Dimensional characteristics | Nominal thickness × width; length class or sheet size |
| Grade / species / performance class | Where appropriate for generics |
| Specified manufacturer / product text | Only where genuinely required |
| Substitution policy / state | Allowed / equivalent-ok / prohibited |
| Concise description | Human-readable requirement |

Do **not** model all construction materials in V1. Do not add fire-rating libraries, full MasterFormat, or proprietary system catalogues in V1.

---

## 6. GENERIC vs SPECIFIED

**GENERIC** example: `2×6 SPF No.2 or better, 12 ft` — may map to many supplier products.

**SPECIFIED** example: a named proprietary membrane, connector, or engineered product — must preserve the project specification and may **prohibit substitution**.

Do not force generic requirements into branded SKUs. Do not erase a genuine specification that requires a particular product.

---

## 7. Ownership

### CalibAi platform

- Canonical taxonomy
- Canonical material definitions
- Controlled UOM vocabulary
- GENERIC / SPECIFIED classification vocabulary
- Substitution **state** vocabulary (not project decisions)

### Organization

- `CostItem`, `Assembly`, `AssemblyItem`
- Preferred materials
- Organization-specific costing (`CostItem.unit_cost` = current planning-cost evidence)
- Organization waste decisions (assembly component / estimate override)
- Reviewed historical mappings (future; not automatic)
- Eventual approved material planning standards (**deferred** — see §12)

### Supplier (future)

- Supplier product / SKU, descriptions, manufacturer SKU
- Sales UOM, pack size
- Pricing, branch, inventory, availability, discontinued state

### Project / commercial snapshot

Frozen evidence actually used: locked `EstimateVersion` lines, accepted proposal snapshots, and (later) accepted quote / approved order mapping and price snapshots.

**Governing pattern:**

```text
LIVING SUPPLIER DATA
→ CURRENT MATERIAL INTELLIGENCE
→ HUMAN / GOVERNED SELECTION
→ PROJECT COMMERCIAL SNAPSHOT
→ IMMUTABLE HISTORY
```

**New / current estimating** may consume current valid supplier evidence.

**Locked `EstimateVersion`, accepted proposal, accepted supplier quote, and approved order** must preserve the exact commercial evidence consumed at that time.

Later price increases, sales, promotion expiry, or inventory changes must **never** silently rewrite those records. No promotion may silently change a locked estimate or create an order.

---

## 8. Multi-supplier mapping

Architecture must support:

```text
ONE CALIBAI MATERIAL
  → Supplier A product
  → Supplier B product
  → Supplier C product
```

BMR Winchester / Darcy remain a prospective **design/launch partner**, **first supplier reference deployment**, and **supplier-channel BD partner** ([ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md)). Winchester may later be the first **reference mapping**. It must **not** be the material vocabulary.

Do not build the Winchester demo in this architecture pass. Do not start supplier integration.

---

## 9. Assemblies — rolled-up commercial vs exploded fulfillment

Preserve current Assembly architecture for commercial estimating: org-owned `Assembly` + `AssemblyItem` → one `EstimateLineItem` (`line_type="Assembly"`) at rolled-up `base_unit_cost` (`app/models/assembly.py`, `app/services/estimate_builder.py`).

**Locked principle:**

| Path | Presentation |
|------|----------------|
| **Commercial estimate / customer** | May remain **one rolled-up Assembly line** |
| **Supplier / fulfillment** | Must be able to use **exploded material quantities** (studs, plates, sheathing, insulation, …) |

Do **not** force fulfillment to reconstruct components from a single rolled-up `EstimateLineItem`.

**Future (not implemented):** assembly components should be capable of resolving to canonical materials. Assembly formulas and component `waste_percent` remain organization/project composition logic. Do **not** put assembly waste on the canonical material.

---

## 10. Take-off boundary

`TakeoffPackageItem` remains **quantity / citation / element evidence** (`app/plan_intelligence/models.py`).

Do **not** add Supplier SKU or CostItem ownership to `TakeoffPackageItem`. Plan Intelligence stays supplier-neutral. AI does not choose the commercial product or SKU ([FG-010](../feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md); ADR-006).

---

## 11. MaterialRequirement — future, not V1

A project-scoped **MaterialRequirement** is the likely later record that can serve both Estimating and Fulfillment:

- reviewed, supplier-neutral
- canonical material + quantity + UOM
- specification / substitution context
- source / citation / provenance

**Do not create this model now.** It requires separate Phase D / governance review before implementation.

---

## 12. Phase D sequencing

**Material Catalogue identity precedes Phase D implementation.**

Phase D remains **NOT STARTED / NOT AUTHORIZED**.

When separately gated, Phase D should map approved take-off evidence through explicit human review toward:

- Assembly
- canonical material / future MaterialRequirement
- structured estimate lines

without automatically selecting a supplier SKU (ADR-006 / ADR-007).

---

## 13. Material-cost evidence hierarchy

Do not conflate:

| Class | Role today / later |
|--------|-------------------|
| ORG-HISTORICAL estimated material cost | `HistoricalCostLineItem` (FG-006); free text is evidence, not identity |
| Supplier catalogue / list price | Future supplier records |
| Contractor-specific supplier price | Future account/contract price |
| Project supplier quote | Future project-bound quote |
| ORG-ACTUAL purchase cost | Future BUILD / MONITOR |
| Organization-approved planning cost | `CostItem.unit_cost` **today** |

`HistoricalCostLineItem.description` must not automatically become a canonical material. Future path only: free text → human-reviewed mapping → canonical material. No external AI. No silent LEARN rewrite ([ADR-024](../adr/ADR-024-learn-recommendation-boundary.md)).

### Material Cost Standard — deferred

A versioned organization **Material Cost Standard** (labour-standard analogue) is **not** part of Material Catalogue V1. It may be justified later after supplier quote, historical, and actual-purchase evidence exist. Do not create it now.

---

## 14. Waste

No universal waste factor on canonical material.

Conceptual precedence:

1. Estimate-specific override (`EstimateLineItem.waste_percent`)
2. Assembly component (`AssemblyItem.waste_percent`)
3. Future organization material-waste standard
4. None

Supplier pack rounding is **not** waste. Actual waste is future ORG-ACTUAL evidence.

---

## 15. Units and pack conversion

| Layer | Owns |
|--------|------|
| Canonical requirement UOM | Material Catalogue (controlled vocabulary) |
| Supplier sales / pack UOM | Future supplier product |
| Conversion / rounding | Future material ↔ supplier-product **mapping** |

Example: 450 LF required → supplier sells 12-ft pieces → governed conversion/rounding → piece count.

Do **not** treat current free-text `CostItem.unit` as the final canonical UOM system.

---

## 16. Substitutions

Future states (vocabulary only in this pass): equivalent; preferred; approved substitute; supplier-proposed; unavailable; specification prohibits substitution.

Human review remains authoritative. **No silent supplier substitution.** Specified materials default to no substitution unless explicitly approved.

---

## 17. Living commercial / supplier evidence

Living evidence is **associated with** fulfilling a canonical material. It is **not** the identity.

Future evidence classes may include:

- current regular / base price
- contractor-specific / account price
- promotional / sale price
- project quote price
- future effective price where the supplier actually supplies it
- effective-from date
- effective-to / expiry date
- supplier, branch, SKU
- sales / pack UOM
- inventory / availability
- retrieved_at / source timestamp
- provenance / source feed

### Price increases and sales

The architecture must support **price increase** and **promotional / sale price** as **effective-dated** supplier commercial evidence.

Do **not** model pricing as only `CURRENT_PRICE` where prior and promotional context is lost.

### Promotional pricing

Future supplier integrations must be capable of representing:

- regular / base price
- promotional price
- promotion start
- promotion expiry
- contractor / account eligibility where applicable
- project / quantity conditions where applicable

Do **not** invent promotion applicability when supplier evidence does not establish it.

### Current vs historical

The living catalogue may continuously change. Current estimating may use currently valid evidence. Locked commercial records must not float.

### ADR-008

This living-intelligence model **strengthens** the future need to resolve [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) or a successor **before** supplier pricing / promotional data becomes operational.

ADR-008 remains **Proposed**. **Do not accept ADR-008 as part of Material Catalogue identity / V1** unless separately authorized. Reconsider it at the supplier-pricing gate.

---

## 18. Winchester demo enablement (not this pass)

When a later Feature Gate authorizes a demonstration (synthetic or labeled supplier data):

```text
Brayman project
→ reviewed take-off
→ CalibAi material requirement
→ Winchester SKU mapping
→ demo / live price and inventory
→ delivery package
→ pick / load
```

The demo is proof that supplier data can **map onto** the CalibAi spine. It must not define the spine.

### Supplier-channel value (two-way)

Future supplier integrations may let suppliers transmit not only price increases and inventory but also:

- promotions
- contractor specials
- clearance opportunities
- volume offers

subject to governed eligibility, provenance, and effective dates.

That creates potential two-way channel value:

```text
CONTRACTOR MATERIAL DEMAND  →  SUPPLIER
SUPPLIER COMMERCIAL OPPORTUNITY  →  CONTRACTOR ESTIMATING / PROCUREMENT
```

No promotion may silently change a locked estimate or create an order. Channel economics remain unset ([ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md)).

---

## 19. Delivery sequencing and other boundaries

Construction-stage grouping (Foundation, Floor, Framing, Roof, Dry-In, Interior) belongs to project / assembly / procurement-package / schedule context — **not** a hard-coded field on canonical material.

Material Catalogue is **not** Industry Benchmarking, **not** LEARN, **not** BUILD actuals, and **not** the Jurisdictional Contract & Compliance Library. Applicability may later *reference* code/climate/spec; it must not own legal content.

**Future pin (not this architecture pass, not FG-014):** governed **bulk** Supplier Catalogue onboarding (file/export, scheduled feed, SFTP, API/ERP/POS, EDI where justified). A supplier must not enter products one at a time. Initial mapping is reviewed; ongoing sync must not unnecessarily remap unchanged products. Canonical record: [supplier-catalogue-inventory-pricing.md](supplier-catalogue-inventory-pricing.md). **FUTURE / NOT IMPLEMENTED.** Does not authorize supplier schema, ingest, BMR, live pricing, or a Supplier Feature Gate.

---

## 20. Recommended first Feature Gate

[FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**.

**MATERIAL IDENTITY + ORGANIZATION COSTITEM LINK + OFFICE CATALOGUE UX**

Likely first POC: dimensional lumber + sheet goods.

**Explicit non-goals of that first gate:**

- supplier SKU models, BMR/Winchester demo, supplier API
- **bulk supplier catalogue onboarding / ingest / sync** (future pin only — see [supplier-catalogue-inventory-pricing.md](supplier-catalogue-inventory-pricing.md); not a Supplier Feature Gate)
- inventory, supplier pricing, promotional / sale-price feeds
- procurement, PO, fulfillment
- Phase D, MaterialRequirement
- Material Cost Standard
- actuals, LEARN, benchmarking, legal library
- accepting ADR-008

---

## 21. Recommended sequence (documentation only)

1. FG-013 **CLOSED / OPERATIONAL FOR UAT** — done
2. Material Catalogue architecture + **ADR-034 / ADR-035 / ADR-036 Accepted** — done (not implemented)
3. Material Catalogue Feature Gate **FG-014 APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED** (identity-only lumber/sheets) — done (this pass)
4. FG-014 **implementation** (not started; separate prompt)
5. Phase D
6. Later **Supplier Catalogue architecture/governance** (includes governed **bulk** onboarding pin; not one-SKU-at-a-time; **not** authorized here)
7. Supplier Catalogue / Winchester reference demo (only after its own Feature Gate)
8. Supplier pricing / inventory / fulfillment
9. Authentication / BUILD / MONITOR / LEARN / Procurement / QuickBooks / legal library — each separately gated

Do not start supplier CSV (Phase E) or bulk supplier ingest before CalibAi material identity exists, or a dealer catalogue becomes the vocabulary. [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) does **not** authorize supplier onboarding.

---

## 22. Governing ADRs

| ADR | Governs |
|-----|---------|
| [ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md) **Accepted** | CalibAi-seeded identity; CostItem remains costing; GENERIC/SPECIFIED; lumber+sheets V1 domain |
| [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) **Accepted** | Requirement UOM vs pack UOM; waste; rolled-up vs exploded; MaterialRequirement anticipated not authorized; Phase D after identity |
| [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** | Evidence classes; multi-supplier mapping; living intelligence; promotions; substitutions; Material Cost Standard deferred; ADR-008 remains Proposed |

[ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) remains binding for supplier neutrality. [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) remains **Proposed**.

---

## 23. Module ownership (intended)

| Concern | Owner |
|---------|--------|
| Canonical material definitions / taxonomy / UOM vocabulary | **Material Catalogue identity** (new domain; not Estimating; not Supplier) |
| Living price / promotion / inventory / SKU evidence | **Supplier Catalogue** (future) |
| Bulk supplier catalogue onboarding / sync | **Supplier Catalogue** (future pin; not FG-014; not authorized) |
| CostItem, Assembly, estimate lines | **Estimating** (current) |
| Take-off packages / items | **Plan Intelligence** (current) |
| PO / delivery package | **Projects / Procurement** (future) |

Cross-module access must use documented service/repository boundaries. Estimating does not own the CalibAi vocabulary. Supplier does not own the CalibAi vocabulary.

---

## 24. Schema / migration (not this pass)

**SCHEMA CHANGE LIKELY: YES** when a later implementation Feature Gate is approved. Additive only. Do not rewrite `HistoricalCostLineItem` into materials. Do not backfill identity from `CostItem.supplier`. Do not generate Alembic from this document.

---

## 25. Office UX (future living intelligence surface)

Identity, supplier mapping, pricing, promotions, inventory, and history may be **separate authoritative records** underneath. The future office **Material Catalogue capability** may still present them through **one coherent material-intelligence surface**.

That surface may eventually show, without conflating authority classes:

- canonical definition
- organization CostItem relationship
- mapped suppliers
- current regular price
- current sale / promotional price
- price history (increases and promotions with effective dates)
- inventory / availability
- quote evidence
- historical organization cost
- later ORG-ACTUAL purchase evidence

First Feature Gate remains **identity + CostItem link + catalogue UX**, not live supplier feeds. No decorative dashboards.

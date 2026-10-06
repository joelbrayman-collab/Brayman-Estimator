# Architecture — Supplier Catalogue, Inventory and Pricing Integration

| Attribute | Value |
|-----------|--------|
| Status | **Partial Current.** FG-029 supplier identity, product, mapping, and inform-only price evidence are **CLOSED / OPERATIONAL FOR UAT**. Effective contractor-cost resolution, discount precedence, bulk ingest, and live supplier feeds remain **not implemented**. |
| Updated | 2026-10-06 |
| Module (proposed) | Supplier Catalogue / Procurement Pricing |
| Related | [platform-roadmap.md](../platform-roadmap.md) · [architecture.md](../architecture.md) · [material-catalogue-architecture.md](material-catalogue-architecture.md) · [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) · ADR-008 · **ADR-033** · ADR-010 · [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) (Material Catalogue identity only; **does not** authorize this module) |

**Current (6 Oct 2026):** `Supplier`, `SupplierLocation`, `ContractorSupplierAccount`, `SupplierProduct`, `CanonicalMaterialSupplierMap`, and `SupplierProductPriceEvidence` exist in `app/models/supplier_catalogue.py`. One canonical material can map to many supplier products. `price_class` is explicit: `PUBLIC_LIST_PRICE` or `CONTRACTOR_CONFIRMED_PRICE`. The contractor account stays provenance on a confirmed row and stays empty on a public row. `captured_at` is when Calibrayt obtained the evidence. `effective_from` is when the price becomes effective, if known. `effective_to` is when it ceases to be valid (`valid_until`), if known. Those three timestamps stay separate. A later row does not replace an earlier row. `CostItem.supplier` remains an optional free-text note and is not this catalogue. `read_supplier_price_evidence_window` returns the public and contractor-confirmed rows whose inclusive `effective_from` / `effective_to` window contains an as-of time. `captured_at` is not that window. The read does not choose a price. `resolve_effective_contractor_cost` then keeps one row for the supplier named by the contractor supplier account. A valid `CONTRACTOR_CONFIRMED_PRICE` is that result. A `PUBLIC_LIST_PRICE` is returned only when no confirmed price is valid, and the result keeps the public class. A later valid row is used for that time and the earlier row stays stored. No supplier is compared. No discount is applied. The result is not an estimate line and not an `EstimateCostingSnapshot`. **RESOLVED SUPPLIER COST → FG-027 HUMAN COST APPROVAL: ARCHITECTURAL GAP IDENTIFIED** (6 Oct 2026). FG-027 approval copies working estimate lines. It cannot store a supplier product, a price-evidence row, or a public-versus-confirmed class. A public fallback has no provisional-approval rule in FG-027. No second approval path was added. The same day the wording was corrected. A supplier does not approve Brayman’s cost. Supplier price evidence is what the supplier offers. Effective contractor cost is the resolved figure. **CONTRACTOR COST APPROVAL RECORD IMPLEMENTED / TESTED.** An authorized Brayman user accepts the resolved contractor-confirmed figure in `contractor_cost_approvals`. The row cites `SupplierProductPriceEvidence` and does not change it. The supplier is provenance only. `EstimateCostingSnapshot` remains the later freeze for one `EstimateVersion`. `CostItem` remains one mutable organization planning cost. `CanonicalMaterialSupplierMap.approved_by_display_name` approves a product map, not a cost. A public list price stays unapproved. Migration `p6c7d8e9f0a1` is in the repository and is not applied to the Mac primary or the hosted database. This record does not accept [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) and does not write an estimate line. [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) remains **Proposed**. **APPROVED CONTRACTOR COST → ESTIMATE COSTING SNAPSHOT IMPLEMENTED / TESTED.** **COSTING REVIEW — CONTRACTOR COST PROVENANCE IMPLEMENTED / TESTED.** The review reads the frozen snapshot citation and does not resolve a new supplier price. The four records stay supplier price evidence, effective contractor cost, Brayman contractor cost approval, and the estimate costing snapshot. **JOB-SPECIFIC SUPPLIER PRICING REQUEST** is the manual supplier-response workflow and is **NOT IMPLEMENTED**. Calibrayt generates the requirement. The supplier confirms product, price, and availability. Brayman approves cost. A later automated supplier integration replaces that response transport and does not replace the cost engine. The 20–30-item synthetic list is withdrawn. On 6 Oct 2026 the Mac office had no real project with a complete canonical material-requirement list. BMR remains the first proving supplier. The architecture stays multi-supplier. [ADR-056](../adr/ADR-056-approved-contractor-cost-estimate-costing-snapshot.md) lets an existing estimate line cite an APPROVED contractor cost on the existing snapshot line. Migration `q7d8e9f0a1b2` is not applied to the Mac primary or the hosted database. There is still no inventory API, EDI, price-file import, purchase-order module, or discount rule. Migration `o5b6c7d8e9f0` is in the repository and is not applied to the Mac primary or the hosted database. Supplier evidence does not write an estimate line.

**CalibraytAI multi-supplier cost engine:** this catalogue is the supplier side. It is not a second pricing engine and not a BMR engine. BMR Winchester is the first proving supplier because Brayman buys there. BMR is not the architecture. ICF manufacturers (`logix`, `nudura`, `fox_blocks`, `styrorail_buildblock`) are product-system profiles in `app/services/icf_manufacturer_profiles.py`. They are not suppliers. Proof: `tests/test_multi_supplier_cost_architecture.py`.

The sections below this note remain the future catalogue design. They are not a claim that discount stacks, bulk ingest, or estimate consumption are built.

## Job-specific supplier pricing request (intended / not implemented)

**JOB-SPECIFIC SUPPLIER PRICING REQUEST** is the manual supplier-response workflow. It is **NOT IMPLEMENTED**. It is not a BMR master catalogue, a BMR pricing engine, a supplier portal, or Supplier Pro.

Calibrayt generates the material requirement and the quantity. The supplier confirms or corrects the product and SKU, confirms availability, and returns a contractor discount, a net contractor price, a quote, an exception, a product it does not supply, or a substitute. Brayman approves the contractor cost. Darcy is not an approval actor and does not determine the project quantity.

The request is built from the project's stored `MaterialRequirement` rows, not from a static supplier list. A known `CanonicalMaterialSupplierMap` may pre-fill the supplier product and SKU. An unmapped requirement stays unmapped. The supplier action is: "Please identify the appropriate supplier product/SKU." No SKU is invented. A known `PUBLIC_LIST_PRICE` is shown as public evidence only. When none exists, the request says public price is not available. It does not show that public price as Brayman's contractor price.

The supplier response is recorded later through the existing chain. A returned net or quoted amount can become `SupplierProductPriceEvidence` with class `CONTRACTOR_CONFIRMED_PRICE`. A discount rate, an unavailable status, and a substitute product are not evidence amounts today. `SupplierProductAvailabilityEvidence` is `IN_STOCK`, `LIMITED`, or `UNKNOWN`. Applying a discount, choosing the cheapest supplier, or approving the cost is outside this request.

Transport is replaceable. The existing Supplier Package HTML and PDF remain the FG-029 inform-only freeze. They are not this request: they omit requirements that are not confirmed contractor-purchased estimate citations, and they do not ask the supplier to identify an unknown product. A later BMR API replaces the manual response transport. It does not replace `MaterialRequirement`, `CanonicalMaterial`, `SupplierProduct`, `SupplierProductPriceEvidence`, effective contractor cost, contractor cost approval, or `EstimateCostingSnapshot`.

**Real-project proof, 6 Oct 2026: NO-GO.** The Mac office database, Alembic `h8c9d0e1f2a3`, holds material requirements only on synthetic UAT projects. `read_construction_material_requirements` reads a Construction Model and does not write a `MaterialRequirement`. EST-2026-0019, the 40x80 thickened-edge slab, has custom and allowance lines. Those units are not the canonical requirement units, and the lines are not canonical material requirements. No request was generated. The cost engine was not changed.

**REAL PROJECT → MATERIAL REQUIREMENT SET: MATERIAL REQUIREMENT CAPABILITY GAP.** Linda Bushel was assessed and not modified. Its Construction Model does not store the material, size, and supplied length a canonical requirement needs. The J1 purchasing sheet was not imported. A persisted canonical requirement set is still not written.

**NO-GUESSING ≠ NO-PROGRESS.** **BEST AVAILABLE MATERIAL REQUIREMENT SET** reads that same model, keeps the known counts and named materials, and flags the unresolved facts. One gap does not drop the other items. The read writes no `MaterialRequirement` and sends no Darcy request. Proof: `tests/test_bushel_material_requirement_readiness.py`. **BUSHEL GOVERNED MEMBER FACT COMPLETION IMPLEMENTED / TESTED.** The 1 Oct tread name "Two 5/4 x 6 boards per tread" is the supplier-neutral canonical identity `CAL-LUM-5-4X6`. It carries no stock length, species, treatment, supplier, SKU, or price. Joist, stringer, post, beam, and decking members still have no material, member size, or supplied length. The 29 Sep nominal sizes stay ungoverned. The 37 in Veranda rail kit stays a named material and is not a catalogue row. **KNOWN PROJECT FACT ≠ COMPLETE PURCHASE REQUIREMENT.** **NO-GUESSING ≠ NO-PROGRESS.** No purchase quantity, estimate line, costing snapshot, or drawing was created. Official V1 remains **65% / 4 of 11**. Proof: `tests/test_bushel_governed_member_facts.py`.

---

## Purpose

Manage supplier identity and product catalogues; import or sync prices and inventory; apply contractor-specific pricing with effective dates; snapshot historical prices used on estimates; and eventually prepare procurement / purchase-order packages without silently mutating past commercial records.

---

## Supplier and branch identity

- Supplier organization (legal/trade name, account numbers).
- Branch / location (for inventory and delivery).
- Credentials and integration endpoints stored outside source control.
- Status: active / inactive.

## Product catalogue structure

CalibAi **material identity** is **not** owned here. See [material-catalogue-architecture.md](material-catalogue-architecture.md): Material Catalogue = what the project requires; this module = what a supplier sells; mapping = how a requirement is fulfilled.

- Supplier product records (supplier description, category as the **dealer** classifies it, trade).
- Manufacturer SKU and supplier SKU (may differ).
- Explicit mapping from **CalibAi canonical material** (and, for costing, organization `CostItem` / assembly components) to supplier products. Estimating owns cost items; Material Catalogue owns CalibAi identity; Supplier module owns catalogue rows.

## Governed bulk supplier onboarding (FUTURE / NOT IMPLEMENTED)

**Status:** **FUTURE / NOT IMPLEMENTED.** Requirement pin only. Preserve for a later Supplier Catalogue architecture/governance pass.

This pin does **not**:

- expand [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) Material Catalogue V1
- authorize supplier schema
- authorize supplier catalogue ingestion
- authorize BMR integration or POC
- authorize live pricing / inventory
- authorize a Supplier Feature Gate

CalibAi must eventually provide **governed bulk** Supplier Catalogue onboarding. A supplier must **not** be required to enter catalogue products one at a time.

Future supported onboarding mechanisms may include:

- bulk catalogue file/export
- scheduled feed
- SFTP or equivalent
- API / ERP / POS integration
- EDI or other enterprise integration where justified

Supplier onboarding lifecycle:

```text
SOURCE
→ BULK INGEST
→ SUPPLIER PRODUCTS
→ MAP TO CALIBAI CANONICAL MATERIALS
→ HUMAN REVIEW / EXCEPTIONS
→ ACTIVE SUPPLIER CATALOGUE
→ CONTINUING SYNCHRONIZATION
```

Initial onboarding and later synchronization are distinct:

| Mode | Purpose |
|------|---------|
| **INITIAL** | Establish supplier products and **reviewed** canonical mappings. |
| **ONGOING** | Synchronize prices, promotions, inventory, availability, and product lifecycle changes **without** unnecessarily remapping unchanged products. |

Canonical identity remains CalibAi-owned ([material-catalogue-architecture.md](material-catalogue-architecture.md)). Bulk ingest creates **supplier products**, then maps them **to** canonical materials. It must not invent CalibAi identity from a dealer file.

## Units of measure and conversions

- Stock UOM vs issue UOM (e.g. each, box, LF, SF).
- Conversion factors with audit; never silent unit mismatch into estimates.

## Package sizes

- Pack quantity, break packs, minimum order quantities.
- Affects PO quantities and price breaks.

## Contractor-specific prices

- Contract / account price lists distinct from list price.
- Priority: contract price → promotional (if eligible and in-window) → branch price → list price (product-configurable; do not invent eligibility).

## Promotional / sale prices

- Represent **regular/base price** and **promotional/sale price** as separate effective-dated evidence — not a single `CURRENT_PRICE` that discards prior or promotional context.
- Promotion start, promotion expiry, contractor/account eligibility, and project/quantity conditions **only when supplier evidence establishes them**.
- Price **increases** and **sales** are both first-class living catalogue events.
- Refresh updates living catalogue evidence; locked estimates, accepted proposals, accepted quotes, and approved orders **must not** float ([material-catalogue-architecture.md](material-catalogue-architecture.md) §17). No promotion may silently change a locked estimate or create an order.
- [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) remains **Proposed** until a supplier-pricing gate; do not treat Material Catalogue identity as accepting it.

## Effective dates

- Every price row has `effective_from` / `effective_to` (or open-ended).
- Estimate lines that consume supplier prices must snapshot the price used (ADR-008).

## Taxes and delivery charges

- Taxability flags; delivery / freight rules as separate charge lines where required.
- Do not bury tax into unit price without an explicit product rule.

## Inventory and lead-time status

- On-hand, available, lead time, backorder flags (from import or live API).
- Stale inventory indicators when sync fails.

## Integration modes

**FUTURE.** Catalogue onboarding must be **governed bulk ingest**, not one-product-at-a-time data entry. See **Governed bulk supplier onboarding** above. This table is not implementation authority.

| Mode | Phase | Notes |
|------|-------|-------|
| CSV / spreadsheet import | Phase E | First practical **bulk** supplier path |
| Manual quote import | Phase E | Paste/upload quote → mapped lines (quotes, not full catalogue onboarding) |
| Scheduled feed / SFTP or equivalent | Phase E–F | Continuing synchronization after initial onboarding |
| API / ERP / POS integrations | Phase F | Supplier-specific adapters |
| EDI | Phase F+ | Higher complexity; Feature Gate required |

**Do not claim any live supplier integration exists in the repository.** This pin does **not** authorize a Supplier Feature Gate.

Supplier **channel** rules (neutrality, no exclusivity, Winchester as launch/reference not lock-in, contractor procurement vs CalibAi channel partnership, Darcy originated-value participation without terms) live in [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) and [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md). Catalogue adapters must remain **multi-supplier**. Do not collapse channel partnership into a PreferredSupplier field. Do not hard-code BMR Winchester as the only supplier. National/enterprise capabilities (multi-branch, DC inventory, ERP/EDI, supplier roles) must remain **possible later** without being built into a first Winchester POC.

## Price refresh rules

- Scheduled or on-demand refresh.
- Refresh updates **catalogue** prices, not historical estimate snapshots.
- User must explicitly re-price an open draft estimate if desired.

## Historical price snapshots

- When a cost/estimate line adopts a supplier price (regular, promotional, or quote), store snapshot: supplier, SKU, unit price, price class (regular / promotional / contract / quote), currency, effective dating, retrieval timestamp, source (CSV/API/manual), eligibility notes if supplied.
- Accepted proposals, locked estimate versions, accepted quotes, and approved orders must not float with catalogue refresh, price increases, sale expiry, or inventory changes (Rules 3 & 5; ADR-008 still Proposed).

## Substitution and equivalency

- Approved alternates with equivalency notes, mapped to **CalibAi canonical material** (not dealer-as-identity).
- Substitutions require human acceptance on the estimate/PO path.

## Supplier comparison

- Compare price/lead-time across suppliers for the same mapped internal item.
- Comparison is advisory until user selects a source for the line.

## Purchase-order preparation (eventual)

- Build PO drafts from estimate or procurement package.
- Nav placeholder exists today; implementation is Future (Phase F+ / Project Controls–Procurement boundary).
- PO documents should snapshot prices and quantities like proposals do for commercial output.

## Failure handling

| Failure | Behaviour |
|---------|-----------|
| API timeout / outage | Serve last successful catalogue snapshot; mark stale; block live-only actions |
| Partial import | Transactional per file version; report row errors; do not half-apply silently |
| Auth failure | Alert; do not wipe catalogue |
| Ambiguous SKU match | Queue for human mapping; no auto-merge |

## Module boundaries

| Module | Owns |
|--------|------|
| Material Catalogue (intended; not implemented) | CalibAi canonical material identity, taxonomy, controlled requirement UOM |
| Supplier Catalogue (proposed) | Suppliers, branches, **supplier** catalogue (SKU/pack/price/promotions/inventory), import jobs, sync state |
| Estimating | Cost items, assemblies, estimate lines; **consumes** snapshot prices; CostItem is **not** CalibAi material identity |
| Proposals | Commercial proposal snapshots (unchanged ownership) |
| Projects / Procurement (future) | PO headers/lines when Feature-Gated |

## Security

- Supplier API keys and EDI credentials via environment / secret store only.
- Audit access to price lists (commercially sensitive).
- Do not commit sample production price files with customer-specific pricing.

## Technical risks

| Risk | Mitigation |
|------|------------|
| Price drift into historical estimates | ADR-008 snapshots; no silent refresh |
| Unit conversion errors | Explicit conversion table + tests |
| Over-building ERP purchasing | Keep PO prep thin; defer full ERP |
| Supplier API heterogeneity | Adapter pattern; CSV-first |
| Catalogue sprawl | Map supplier SKUs to CalibAi canonical materials (and org CostItems for costing) deliberately; do not treat dealer SKUs as CalibAi identity |

## Phased implementation

See roadmap Phases **E** (catalogue / price-file import) and **F** (live inventory & pricing). **Material Catalogue identity precedes Phase D and supplier Phase E** so a first dealer cannot become the CalibAi vocabulary. Plan Intelligence Phases A–C exist separately. Do not couple schemas casually.

## Related ADRs

- [material-catalogue-architecture.md](material-catalogue-architecture.md) — CalibAi material identity (what the project requires)
- [ADR-034](../adr/ADR-034-canonical-material-identity-and-ownership.md) **Accepted** — canonical identity (not implemented)
- [ADR-035](../adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) **Accepted** — UOM / waste / requirement boundary
- [ADR-036](../adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** — evidence classes and mapping; live pricing **not** authorized
- [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) — Supplier price snapshotting (**Proposed**; required or successor before operational price/promotion consumption)
- [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) — Supplier neutrality and Winchester launch-partner channel (**Accepted**; not implemented)
- [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) — Channel, launch partner, dual relationships
- [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) — Build vs buy (shared concerns for integration platforms)  

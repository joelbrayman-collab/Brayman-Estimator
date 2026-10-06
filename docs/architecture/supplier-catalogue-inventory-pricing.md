# Architecture — Supplier Catalogue, Inventory and Pricing Integration

| Attribute | Value |
|-----------|--------|
| Status | **Partial Current.** FG-029 supplier identity, product, mapping, and inform-only price evidence are **CLOSED / OPERATIONAL FOR UAT**. Effective contractor-cost resolution, discount precedence, bulk ingest, and live supplier feeds remain **not implemented**. |
| Updated | 2026-10-06 |
| Module (proposed) | Supplier Catalogue / Procurement Pricing |
| Related | [platform-roadmap.md](../platform-roadmap.md) · [architecture.md](../architecture.md) · [material-catalogue-architecture.md](material-catalogue-architecture.md) · [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) · ADR-008 · **ADR-033** · ADR-010 · [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) (Material Catalogue identity only; **does not** authorize this module) |

**Current (6 Oct 2026):** `Supplier`, `SupplierLocation`, `ContractorSupplierAccount`, `SupplierProduct`, `CanonicalMaterialSupplierMap`, and `SupplierProductPriceEvidence` exist in `app/models/supplier_catalogue.py`. One canonical material can map to many supplier products. `price_class` is explicit: `PUBLIC_LIST_PRICE` or `CONTRACTOR_CONFIRMED_PRICE`. The contractor account stays provenance on a confirmed row and stays empty on a public row. `captured_at` is when Calibrayt obtained the evidence. `effective_from` is when the price becomes effective, if known. `effective_to` is when it ceases to be valid (`valid_until`), if known. Those three timestamps stay separate. A later row does not replace an earlier row. `CostItem.supplier` remains an optional free-text note and is not this catalogue. There is still no inventory API, EDI, price-file import, purchase-order module, discount rule, or effective-cost resolver. Migration `o5b6c7d8e9f0` is in the repository and is not applied to the Mac primary or the hosted database. [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) remains **Proposed**. Supplier evidence does not write an estimate line.

**CalibraytAI multi-supplier cost engine:** this catalogue is the supplier side. It is not a second pricing engine and not a BMR engine. BMR Winchester is the first proving supplier because Brayman buys there. BMR is not the architecture. ICF manufacturers (`logix`, `nudura`, `fox_blocks`, `styrorail_buildblock`) are product-system profiles in `app/services/icf_manufacturer_profiles.py`. They are not suppliers. Proof: `tests/test_multi_supplier_cost_architecture.py`.

The sections below this note remain the future catalogue design. They are not a claim that discount stacks, bulk ingest, or estimate consumption are built.

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

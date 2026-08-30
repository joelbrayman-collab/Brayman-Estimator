# Architecture — Supplier Catalogue, Inventory and Pricing Integration

| Attribute | Value |
|-----------|--------|
| Status | **Future architecture** (not implemented) |
| Updated | 2026-07-25 |
| Module (proposed) | Supplier Catalogue / Procurement Pricing |
| Related | [platform-roadmap.md](../platform-roadmap.md) · [architecture.md](../architecture.md) · [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) · ADR-008 · **ADR-033** · ADR-010 |

**Current vs future:** Today the app has only an optional free-text `supplier` string on `CostItem` (`app/models/cost_item.py`). There is **no** supplier entity, catalogue, inventory API, EDI, price file import, or purchase-order module (Purchase Orders remain a **disabled nav placeholder**). Nothing below is claimed as implemented.

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

- Canonical product records (description, category, trade).
- Manufacturer SKU and supplier SKU (may differ).
- Links to internal `CostItem` / assembly components via explicit mapping (Estimating owns cost items; Supplier module owns catalogue rows).

## Units of measure and conversions

- Stock UOM vs issue UOM (e.g. each, box, LF, SF).
- Conversion factors with audit; never silent unit mismatch into estimates.

## Package sizes

- Pack quantity, break packs, minimum order quantities.
- Affects PO quantities and price breaks.

## Contractor-specific prices

- Contract / account price lists distinct from list price.
- Priority: contract price → branch price → list price (product-configurable).

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

| Mode | Phase | Notes |
|------|-------|-------|
| CSV / spreadsheet import | Phase E | First practical supplier path |
| Manual quote import | Phase E | Paste/upload quote → mapped lines |
| API integrations | Phase F | Supplier-specific adapters |
| EDI | Phase F+ | Higher complexity; Feature Gate required |

**Do not claim any live supplier integration exists in the repository.**

Supplier **channel** rules (neutrality, no exclusivity, Winchester as launch/reference not lock-in, contractor procurement vs CalibAi channel partnership, Darcy originated-value participation without terms) live in [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) and [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md). Catalogue adapters must remain **multi-supplier**. Do not collapse channel partnership into a PreferredSupplier field. Do not hard-code BMR Winchester as the only supplier. National/enterprise capabilities (multi-branch, DC inventory, ERP/EDI, supplier roles) must remain **possible later** without being built into a first Winchester POC.

## Price refresh rules

- Scheduled or on-demand refresh.
- Refresh updates **catalogue** prices, not historical estimate snapshots.
- User must explicitly re-price an open draft estimate if desired.

## Historical price snapshots

- When a cost/estimate line adopts a supplier price, store snapshot: supplier, SKU, unit price, currency, effective date, retrieval timestamp, source (CSV/API/manual).
- Accepted proposals and locked estimate versions must not float with catalogue refresh (Rules 3 & 5; ADR-008).

## Substitution and equivalency

- Approved alternates with equivalency notes.
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
| Supplier Catalogue (proposed) | Suppliers, branches, catalogue, price lists, import jobs, sync state |
| Estimating | Cost items, assemblies, estimate lines; **consumes** snapshot prices |
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
| Catalogue sprawl | Map to internal cost items deliberately |

## Phased implementation

See roadmap Phases **E** (catalogue / price-file import) and **F** (live inventory & pricing). Phases A–D (Plan Intelligence) may proceed in parallel as a separate program after Feature Gates—do not couple schemas casually.

## Related ADRs

- [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) — Supplier price snapshotting
- [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) — Supplier neutrality and Winchester launch-partner channel (**Accepted**; not implemented)
- [supplier-channel-and-launch-partner.md](supplier-channel-and-launch-partner.md) — Channel, launch partner, dual relationships
- [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) — Build vs buy (shared concerns for integration platforms)  

# ADR-036 — Material Commercial Evidence and Supplier-Neutral Mapping

| Field | Value |
|-------|--------|
| Title | ADR-036: Material Commercial Evidence Classes and Supplier-Neutral Mapping |
| Status | **Accepted** (governance / architecture only; **not implemented**) |
| Date | 2026-08-30 |
| Related | [material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) · [ADR-034](ADR-034-canonical-material-identity-and-ownership.md) · [ADR-035](ADR-035-material-quantity-uom-and-requirement-boundary.md) · [ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** · [ADR-008](ADR-008-supplier-price-snapshotting.md) **Proposed** · [ADR-002](ADR-002-accepted-proposal-immutability.md) · [ADR-024](ADR-024-learn-recommendation-boundary.md) · [ADR-030](ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) |

## Context

Canonical Material ([ADR-034](ADR-034-canonical-material-identity-and-ownership.md)) is identity, not price. Living supplier catalogues change: list prices rise, promotions start and expire, inventory moves, quotes have windows.

If those facts are stored on the identity row, or collapsed into a single mutable `CURRENT_PRICE`, CalibAi loses history and supplier neutrality. If fulfillment mapping is one-dealer-only, Winchester becomes the vocabulary ([ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md)).

[ADR-008](ADR-008-supplier-price-snapshotting.md) remains **Proposed**. This ADR governs **evidence classes and mapping architecture**. It does **not** accept ADR-008 and does **not** authorize live supplier pricing.

This ADR does **not** authorize product code, schema, a Feature Gate, Winchester POC, or a Material Cost Standard.

## Decision

### 1. Keep commercial evidence classes separate

Do not conflate authority:

| Class | Role |
|--------|------|
| ORG-HISTORICAL estimated material cost | FG-006 `HistoricalCostLineItem` evidence; free text is not identity |
| Organization planning cost | `CostItem.unit_cost` today |
| Supplier catalogue / list price | Future supplier records |
| Contractor-specific supplier price | Future account / contract price |
| Promotional / sale supplier price | Future effective-dated promotion evidence |
| Project supplier quote | Future project-bound quote |
| ORG-ACTUAL purchase cost | Future BUILD / MONITOR |

Canonical Material contains **no** volatile commercial price.

Historical free text may later map to canonical material only through **human-reviewed** mapping. No automatic mapping. No external AI. LEARN must not silently rewrite libraries ([ADR-024](ADR-024-learn-recommendation-boundary.md)).

### 2. Supplier-neutral mapping

```text
ONE CALIBAI MATERIAL
  → Supplier A product
  → Supplier B product
  → Supplier C product
```

BMR Winchester may later be the first reference mapping. It must not be the identity ([ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md), [ADR-034](ADR-034-canonical-material-identity-and-ownership.md)).

### 3. Future supplier-owned facts

When a later Feature Gate authorizes supplier catalogue work, supplier-owned facts include: SKU, sales UOM, pack, regular price, contractor price, promotional price, promotion effective dates, quote price, branch, inventory, availability, timestamps, provenance.

Conversion/rounding from requirement UOM to pack UOM lives on the **mapping**, not on identity ([ADR-035](ADR-035-material-quantity-uom-and-requirement-boundary.md)).

**Future pin (not this ADR, not FG-014):** when Supplier Catalogue is later gated, onboarding must be **governed bulk ingest** (not one-product-at-a-time), then map to CalibAi canonical materials with human review/exceptions, then continuing sync distinct from initial mapping. Canonical wording: [supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md). This ADR does **not** authorize that work.

### 4. Living material intelligence

```text
LIVING SUPPLIER DATA
→ CURRENT MATERIAL INTELLIGENCE
→ HUMAN / GOVERNED SELECTION
→ PROJECT SNAPSHOT
→ IMMUTABLE HISTORY
```

The living catalogue may continuously change. **New / current estimating** may later consume currently valid supplier evidence.

**Locked `EstimateVersion`, Accepted Proposal, accepted supplier quote, and approved order** must **never** float when:

- regular price changes (including increases)
- a sale begins
- a sale expires
- inventory changes
- supplier mapping changes

### 5. Price increases and promotional / sale pricing

Both **price increase** and **promotional / sale price** must be representable as **effective-dated** supplier commercial evidence.

Do **not** reduce future pricing architecture to a single mutable `CURRENT_PRICE` that discards prior or promotional context.

Promotions may later include contractor specials, clearance, and volume offers, subject to eligibility, effective dates, provenance, and human/governed selection.

**Do not invent promotion applicability** when supplier evidence does not establish it.

**No promotion may silently alter a locked estimate or create an order.**

### 6. Substitutions

Preserve states: equivalent; preferred; approved substitute; supplier-proposed substitute; unavailable; specification prohibits substitution.

**No silent supplier substitution.** Human review remains authoritative. Specified materials default to **prohibit substitution** unless explicitly approved.

### 7. Material Cost Standard — deferred

A future versioned organization **Material Cost Standard** (labour-standard analogue) remains **justified but deferred**. Do **not** create it under Material Catalogue identity V1.

### 8. ADR-008 boundary

[ADR-008](ADR-008-supplier-price-snapshotting.md) remains **Proposed**.

**Operational supplier price / quote / promotional snapshot consumption requires ADR-008 or an approved successor before implementation.**

This ADR does **not** authorize live supplier pricing, promotional feeds, inventory APIs, or Winchester demo.

### 9. Office surface vs records

The future Material Catalogue **UX** may show identity, CostItem relationship, Assembly usage, mappings, current regular and promotional prices, price history, inventory, quotes, historical org evidence, and later ORG-ACTUAL — while underlying records remain separate authority classes ([ADR-034](ADR-034-canonical-material-identity-and-ownership.md) §7).

Do not implement that UX in this pass. Identity V1 UX is catalogue-of-definitions plus CostItem link only.

## Alternatives Considered

- **Put current price on Canonical Material** — Rejected: identity would float and mix authority.
- **Single CURRENT_PRICE field** — Rejected: loses increases, sale windows, and history.
- **Accept ADR-008 in this pass** — Rejected: identity V1 does not consume supplier prices; snapshot mechanics belong to a supplier-pricing gate.
- **One PreferredSupplier / Winchester-only map** — Rejected: ADR-033.
- **Create Material Cost Standard now** — Rejected: insufficient supplier/actual evidence; deferred.
- **Separate substitution ADR** — Rejected: substitution is mapping/fulfillment policy and fits this decision.

## Consequences

Positive: promotions can exist as channel value without rewriting bids; multi-supplier comparison stays possible.

Negative: more record types later; estimators must understand current intelligence vs frozen snapshot.

## Module Ownership Impact

| Concern | Owner |
|---------|--------|
| Evidence class rules / mapping architecture | This ADR (Material Catalogue + future Supplier Catalogue) |
| Living SKU / price / promotion / inventory rows | Future Supplier Catalogue |
| Project commercial snapshots on consumption | Estimating / Proposals / future Procurement — **requires ADR-008 or successor** before operational use |
| Historical cost lines | Historical ingestion (FG-006); mapping is reviewed, not automatic |

## Data Ownership Impact

Identity remains CalibAi ([ADR-034](ADR-034-canonical-material-identity-and-ownership.md)). Volatile commercial facts are supplier/quote/snapshot records. Locked project records are immutable commercial history (Rules 3 & 5; ADR-002 for accepted proposals).

## Migration Impact

**Deferred.** No schema in this pass. Future additive mapping and price/promotion tables only after Feature Gates. Do not backfill prices onto identity.

## Testing Impact

None this pass. Future supplier-pricing tests (after ADR-008 or successor) must prove locked versions do not float on price increase, sale start, or sale expiry.

## Documentation Impact

[material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md); supplier catalogue architecture; ADR index. ADR-008 stays Proposed.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Approved via Material Catalogue ADR governance prompt | 2026-08-30 |
| ChatGPT review | Architecture report + locked decisions | 2026-08-30 |
| Cursor implementation note | Docs/ADR only. ADR-008 **not** accepted. No live pricing. | 2026-08-30 |

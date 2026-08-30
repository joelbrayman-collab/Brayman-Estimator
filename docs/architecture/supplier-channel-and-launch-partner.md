# Architecture — Supplier Channel and Launch-Partner Model

| Attribute | Value |
|-----------|--------|
| Status | **Future architecture** (direction accepted; **not implemented**) |
| Updated | 2026-08-30 |
| Related | [supplier-catalogue-inventory-pricing.md](supplier-catalogue-inventory-pricing.md) · [material-catalogue-architecture.md](material-catalogue-architecture.md) · [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) · [platform-roadmap.md](../platform-roadmap.md) Phases E–F |
| Implementation | **Not authorized** by this document. No supplier-integration Feature Gate is opened here. |

**Current vs future:** Today the app has only an optional free-text `CostItem.supplier` string. There is **no** supplier entity, catalogue, inventory API, EDI, purchase-order module, channel-partner record, or Darcy/BMR commercial participation. Nothing below is claimed as implemented.

This document is the **supplier-channel** architecture. **What the project requires** is [material-catalogue-architecture.md](material-catalogue-architecture.md). Catalogue SKU, inventory, pricing, and snapshot mechanics remain in [supplier-catalogue-inventory-pricing.md](supplier-catalogue-inventory-pricing.md). Do not collapse channel partnership into a catalogue SKU, a canonical material, or a single PreferredSupplier field.

---

## Governing principle

CalibAi remains **supplier-neutral** and must be capable of supporting **multiple competing building-material suppliers**.

**BMR, BMR Winchester, and Darcy are not exclusive CalibAi supplier partners.** Do not propose or architect supplier exclusivity, national exclusivity, category exclusivity, or perpetual rights to unrelated CalibAi supplier business unless Joel separately and expressly authorizes that grant.

**Reward Darcy for value created / business originated. Do not compensate him by surrendering CalibAi’s broader supplier-channel opportunity.**

---

## Launch-partner model (BMR Winchester)

BMR Winchester is contemplated as a potential:

1. **Design / launch partner** — real supplier-side workflow for the first connected proof.
2. **First supplier reference deployment** — a reference implementation others can be shown, not a distribution lock-in.
3. **Supplier-channel business-development partner** — help originate further supplier accounts if the Winchester implementation succeeds.

That is a **launch and reference** role. It is **not** an exclusive supplier arrangement, exclusive BMR arrangement, or exclusive CalibAi go-to-market right.

### Initial partnership concept

The intended **initial** relationship is substantially:

```text
BRAYMAN CONSTRUCTION
+
DARCY / BMR WINCHESTER
+
CALIBAI
```

| Party | Role in the initial proof |
|-------|---------------------------|
| **Brayman Construction** (`ORG-001`) | Contractor-side real-world workflow |
| **Darcy / BMR Winchester** | Supplier-side real-world workflow; launch / reference / channel-development partner |
| **CalibAi** | Platform connecting plan → reviewed take-off → **CalibAi Material Catalogue** → supplier mapping → price/inventory → delivery → fulfillment |

Together they can **prove** (when a later Feature Gate authorizes a POC — not this pass):

```text
PLAN
→ REVIEWED TAKE-OFF
→ MATERIAL CATALOGUE
→ SUPPLIER MAPPING
→ PRICE / INVENTORY
→ DELIVERY SCHEDULE
→ PICK / LOAD / FULFILLMENT
```

That creates potential two-way channel value (intended; not implemented): contractor material demand → supplier; supplier commercial opportunity (price increases, promotions, specials, clearance, volume offers) → contractor estimating / procurement. Living evidence must not silently rewrite locked estimates. See [material-catalogue-architecture.md](material-catalogue-architecture.md) §17–§18.

---

## Two relationships (do not collapse)

Architecture **must** distinguish two different relationships. They have different parties, different data, and different commercial meaning.

### A. Contractor ↔ supplier procurement relationship

**Example:** Brayman Construction → BMR Winchester.

This governs **project / material purchasing** and **authorized project-data sharing** for procurement:

- contractor account at a supplier location
- project-scoped material demand
- quotes, inventory, delivery, pick/load/fulfillment for that contractor’s jobs
- which project facts the contractor authorizes the supplier to see

This is **not** a CalibAi channel-partnership contract.

### B. CalibAi ↔ supplier channel relationship

**Example:** CalibAi ↔ Darcy / BMR Winchester.

This governs **launch partnership, integration, channel development, branding, and commercial participation**:

- who is a design/launch/reference partner
- which integration adapter is in use
- channel-development activity Darcy materially helps originate
- future participation economics (categories only in this pass)

**Do not collapse A and B into one PreferredSupplier field** on a cost item, estimate, organization, or project. Free-text `CostItem.supplier` is a legacy Estimating convenience, not a channel-partnership record and not a procurement-account record.

### Conceptual identities (future — not a schema)

These names are architectural. They are **not** tables to create in this pass.

| Concept | Owns | Relationship |
|---------|------|----------------|
| Contractor organization | CalibAi tenant (e.g. ORG-001) | Party on A |
| Supplier organization | Legal/trade supplier (dealer, banner, or national enterprise) | Party on A and/or B |
| Supplier location / branch | Inventory, delivery, local pricing | Party on A; may participate in B |
| Contractor–supplier account | Account numbers, contract price lists, authorized sharing | **A only** |
| Supplier channel partnership | Launch/reference/integration/channel terms with CalibAi | **B only** |
| Channel originator participation | Future economics for originated supplier accounts | **B only**; not in Winchester POC |

A national banner (for example BMR corporate) is **not** the same record as one dealer location (BMR Winchester). A person who helps originate accounts (Darcy) is **not** the supplier organization and **not** an exclusive agent of CalibAi’s supplier market.

---

## Channel expansion

If the Winchester implementation is successful, Darcy may help CalibAi pursue:

- other BMR dealers
- BMR corporate / broader BMR network
- other building-material organizations
- potentially large national organizations such as Home Depot or comparable suppliers

**Do not assume that all supplier organizations use the same technical or commercial integration model.**

| Implication | Architecture rule |
|-------------|-------------------|
| Winchester adapter | One supplier-specific adapter / import path |
| Other BMR dealers | May reuse, extend, or replace the Winchester adapter; do not assume identity |
| BMR corporate | May require a different commercial and technical model than a single dealer |
| Other independents | Separate supplier organizations; competing suppliers allowed |
| National enterprise | See enterprise scalability below; separate Feature Gates |

The BMR Winchester implementation should become a **reference implementation**, not an exclusive distribution arrangement.

---

## Darcy economic participation (assess later; no terms here)

Future commercial structures may reward Darcy for supplier-channel business he **materially helps originate or develop**, without transferring exclusivity over CalibAi’s supplier market.

**Models to assess later** (categories only — **no percentages, fees, durations, or contract terms in this pass**):

- originated-account referral economics
- recurring revenue participation on originated supplier accounts
- BMR-channel-specific participation
- milestone / success fees
- strategic channel-partner economics
- other performance-based structures

**Must not** be granted by this architecture:

- supplier exclusivity
- national exclusivity
- category exclusivity
- perpetual rights to unrelated CalibAi supplier business

unless Joel separately and expressly authorizes that grant.

Participation, if later approved, should attach to **originated supplier-channel relationships (B)** that Darcy materially helped create or develop — not to all CalibAi contractor procurement (A), and not to supplier accounts he did not originate.

**Do not implement channel economics in any Winchester / supplier-integration POC.**

---

## National / enterprise scalability (anticipate; do not overbuild)

A large national supplier may later require capabilities such as:

- enterprise identity
- multiple branches / stores
- regional pricing
- contractor account mapping
- corporate catalogue
- local inventory
- distribution-centre inventory
- ERP / POS integration
- API / EDI integration
- corporate security review
- supplier user roles
- enterprise permissions
- service-level requirements
- audit
- national / regional / local fulfillment

**Do not overbuild these capabilities into the Winchester POC.**

**Do ensure the Winchester architecture does not prevent them later:**

- Model supplier **organization** separately from **location**.
- Treat catalogue, contract price, branch price, and list price as distinct (see catalogue architecture).
- Use an **adapter** boundary for import/API/EDI; do not hard-code “Winchester is the only supplier.”
- Keep contractor–supplier **account mapping** distinct from CalibAi channel partnership.
- Keep inventory **location-scoped** so DC vs store can be added later.
- Do not bake exclusive branding or a single PreferredSupplier into Estimating core.

Winchester POC, when Feature-Gated, should be the **thinnest** connected slice of the plan → fulfillment chain that still produces reference evidence — typically one contractor (Brayman), one supplier location (Winchester), CSV or a single adapter, human-mapped SKUs, snapshot prices (ADR-008 when accepted/implemented).

---

## Reference-implementation evidence (measure later)

The Winchester POC should **eventually** measure evidence useful for selling the model elsewhere. The architecture should enable that evidence to be measured **later** without inventing metric formulas, targets, or dashboards now.

**Do not implement channel economics or analytics in the current supplier-integration POC** (and this pass does not start that POC).

### Contractor metrics (future measurement)

- estimating / take-off time saved
- procurement time saved
- quote turnaround
- material-order accuracy
- delivery coordination

### Supplier operational metrics (future measurement)

- supplier take-off / estimating hours avoided
- supplier review time
- quote preparation time
- pick / load preparation time
- transcription / error reduction

### Supplier commercial metrics (future measurement)

- contractor material spend captured
- project / material pipeline
- number / value of contractor projects flowing through integration
- contractor retention
- share-of-wallet where measurable

### Channel metrics (future measurement)

- contractor adoption
- contractor referrals
- supplier locations interested
- supplier accounts originated
- conversion from demonstration to deployment

Future instrumentation should prefer **dated event / duration records** attached to existing project, take-off, estimate, quote, and (future) PO/fulfillment objects — not a parallel metrics product and not industry-benchmark substitutions for observed Winchester evidence.

### Future sales story (enabled by evidence, not by this pass)

The target enterprise story should become:

> We have already deployed this workflow with a real contractor and building-material dealer. Here is the reviewed plan-to-material-to-fulfillment workflow. Here is the supplier labour it eliminated. Here is the contractor value. Here is the material purchasing activity it captured. Here is the operational evidence.

Do **not** invent those numbers now. Do **not** claim the workflow is deployed.

---

## Module and ownership boundaries

| Concern | Owner (intended) |
|---------|------------------|
| Catalogue, SKU, price lists, inventory sync, adapters | Proposed **Supplier Catalogue** module |
| Contractor–supplier procurement account and project sharing (relationship A) | Supplier Catalogue / future Procurement — **not** Estimating’s free-text field |
| CalibAi channel partnership and originator participation (relationship B) | Supplier Catalogue channel records, or a later explicitly owned Channel concern — **not** a cost-item flag |
| Estimate lines and cost items | **Estimating** (consumes price snapshots; does not own supplier identity) |
| Reviewed take-off quantities | **Plan Intelligence** |
| Purchase orders / fulfillment | Future **Projects / Procurement** (nav placeholder only today) |
| Darcy commercial terms | **Not a product module in this pass.** Future commercial/legal record; not Winchester POC code |

Cross-module access must use documented service boundaries (architecture-principles Rule 11). Estimating must not own supplier channel contracts. Supplier Catalogue must not rewrite locked estimate or proposal snapshots (ADR-008; Rules 3 and 5).

---

## POC and Feature Gate constraints

| This document authorizes | This document does **not** authorize |
|--------------------------|--------------------------------------|
| Architecture direction and ADR-033 | Supplier-integration code, schema, or migration |
| Winchester as launch/reference **intent** | A Winchester Feature Gate or POC start |
| Heterogeneous adapters later | Assuming one BMR/Home Depot/Winchester model |
| Later assessment of Darcy participation **categories** | Percentages, invoices, partner contracts, or payout code |
| Later evidence measurement design | Analytics, dashboards, or channel-economics implementation |

Supplier Phases **E** (catalogue / price-file import) and **F** (live inventory / pricing) remain **Future** and still require their own Feature Gates. CAR-001 continues to list supplier integrations as separately Feature-Gated, not V1-by-default.

---

## Related documents

- [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) — Supplier neutrality, two relationships, launch-partner channel
- [supplier-catalogue-inventory-pricing.md](supplier-catalogue-inventory-pricing.md) — Catalogue, inventory, pricing, adapters
- [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) — Price snapshots (**Proposed**)
- [modules/supplier-catalogue.md](../modules/supplier-catalogue.md)
- [platform-roadmap.md](../platform-roadmap.md) — Phases E–F
- [architecture/CAR-001-calibai-product-architecture-reconciliation.md](CAR-001-calibai-product-architecture-reconciliation.md)

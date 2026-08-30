# ADR-033 — Supplier Neutrality and Launch-Partner Channel

| Field | Value |
|-------|--------|
| Title | ADR-033: Supplier Neutrality, Dual Relationships, and Winchester Launch-Partner Channel |
| Status | **Accepted** (governance / architecture only; supplier integration **not implemented**) |
| Date | 2026-08-30 |
| Related | [supplier-channel-and-launch-partner.md](../architecture/supplier-channel-and-launch-partner.md) · [supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md) · [ADR-008](ADR-008-supplier-price-snapshotting.md) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [platform-roadmap.md](../platform-roadmap.md) Phases E–F |

## Context

CalibAi’s long-term differentiator includes plan → reviewed take-off → supplier-priced materials → procurement/fulfillment. Catalogue architecture already exists as **Future** ([supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md)). It does not say whether a first dealer is exclusive, how a launch partner is rewarded, or how contractor purchasing is distinct from CalibAi’s supplier-channel business.

A 2026-08-30 commercial clarification from Joel records that **BMR, BMR Winchester, and Darcy are not exclusive CalibAi supplier partners**. BMR Winchester is contemplated as a **design/launch partner**, **first supplier reference deployment**, and **supplier-channel business-development partner**. The initial proof is Brayman Construction + Darcy / BMR Winchester + CalibAi. Success may lead Darcy to help pursue other BMR dealers, BMR corporate, other building-material organizations, and potentially large nationals (for example Home Depot or comparable suppliers). Integration and commercial models will **not** be the same for every supplier.

Without this ADR, a future Winchester POC could incorrectly:

- treat Winchester or BMR as the only supplier
- collapse contractor purchasing and CalibAi channel partnership into one PreferredSupplier field
- grant Darcy exclusivity instead of originated-value participation
- overbuild national-enterprise capabilities into the first dealer POC
- implement channel economics or analytics before the workflow exists

Accepting this ADR **does not** authorize supplier-integration code, schema, migration, a Feature Gate, Winchester POC implementation, Darcy commercial terms, or analytics.

## Decision

### 1. Supplier neutrality (no exclusivity)

CalibAi remains **supplier-neutral** and must support **multiple competing** building-material suppliers.

Do **not** architect:

- supplier exclusivity
- national exclusivity
- category exclusivity
- perpetual rights to unrelated CalibAi supplier business

unless Joel separately and expressly authorizes that grant.

BMR, BMR Winchester, and Darcy are **not** exclusive CalibAi supplier partners.

### 2. Winchester is launch / reference, not distribution lock-in

BMR Winchester is contemplated as:

1. design / launch partner
2. first supplier **reference** deployment
3. supplier-channel business-development partner

The Winchester implementation, if later Feature-Gated and successful, is a **reference implementation** — not an exclusive distribution arrangement.

### 3. Two relationships must remain distinct

**A. Contractor ↔ supplier procurement** (example: Brayman Construction → BMR Winchester) governs project/material purchasing and authorized project-data sharing.

**B. CalibAi ↔ supplier channel** (example: CalibAi ↔ Darcy / BMR Winchester) governs launch partnership, integration, channel development, branding, and commercial participation.

**Do not collapse A and B into one PreferredSupplier field.** Legacy free-text `CostItem.supplier` is not either record.

Model (when later implemented) supplier **organization** separately from **location**, and contractor–supplier **account** separately from CalibAi **channel partnership**.

### 4. Darcy participation is value-created, not market surrender

Future structures may reward Darcy for supplier-channel business he **materially helps originate or develop**. Models to **assess later** include originated-account referral, recurring participation on originated supplier accounts, BMR-channel-specific participation, milestone/success fees, strategic channel-partner economics, and other performance-based structures.

This ADR **does not set percentages or commercial terms**.

Participation must not be implemented by granting exclusivity over CalibAi’s broader supplier-channel opportunity.

### 5. Heterogeneous supplier models

Do not assume every supplier organization uses the same technical or commercial integration model. Winchester, other BMR dealers, BMR corporate, independents, and national enterprises may each require different adapters and contracts.

### 6. Enterprise scalability without Winchester overbuild

Anticipate that a large national supplier may later need enterprise identity, multi-branch, regional pricing, contractor account mapping, corporate vs local vs DC inventory, ERP/POS, API/EDI, security review, supplier roles/permissions, SLAs, audit, and national/regional/local fulfillment.

**Do not overbuild these into the Winchester POC. Do not design the Winchester POC so that they cannot be added later.** Adapter boundaries, location-scoped inventory, and distinct organization/location/account/partnership records are the non-blocking shape.

### 7. Reference evidence later; no POC analytics or channel economics

Winchester should eventually support measurement of contractor, supplier-operational, supplier-commercial, and channel evidence families listed in the channel architecture. Enable later measurement; **do not invent metrics now**. **Do not implement channel economics or analytics in the supplier-integration POC.**

### 8. No implementation from this ADR

Supplier Phases E–F, Winchester POC, Darcy payouts, and national-enterprise integrations each require their **own** later Feature Gate and Joel authorization. CAR-001’s “supplier integrations are separately Feature-Gated” bound still holds.

## Alternatives Considered

- **Exclusive BMR / Winchester / Darcy partnership** — Rejected. Conflicts with supplier neutrality and CalibAi’s broader supplier-channel opportunity.
- **Single PreferredSupplier field on Organization or CostItem** — Rejected. Collapses procurement (A) with channel partnership (B).
- **Winchester POC as mini-enterprise platform (roles, SLAs, multi-DC, national identity)** — Rejected as first-slice scope. Must remain possible later.
- **Defer all channel rules until Phase E code** — Rejected. Neutrality and dual-relationship rules must constrain the first POC so it does not paint CalibAi into exclusivity or a single-supplier schema.
- **Set Darcy percentages in this ADR** — Rejected. Commercial terms are not architecture and are not authorized here.

## Consequences

Positive:

- First dealer can be Winchester without locking the market.
- Darcy can be rewarded later for originated value without owning unrelated CalibAi supplier business.
- Estimating/catalogue schemas are less likely to hard-code one supplier.
- National/enterprise deals remain architecturally possible.

Negative / deferred:

- Channel-partnership and originator-participation records are extra future entities.
- Commercial negotiation with Darcy remains open (no terms in repo).
- Winchester POC, when authorized, must stay thin and still leave extension points.

## Module Ownership Impact

Proposed **Supplier Catalogue** remains the owner of suppliers, locations, catalogues, adapters, and (when specified) channel-partnership records. Estimating continues to consume snapshots only. No module is implemented by this ADR. Darcy commercial contracts are not a coded module in this pass.

## Data Ownership Impact

None in the database today. Future owned records (not created here): supplier organization, location, contractor–supplier account (A), CalibAi channel partnership (B), optional originator participation. Price snapshots remain ADR-008 (**Proposed**). Locked estimates and accepted proposals remain immutable (Rules 3 and 5).

## Migration Impact

None. Deferred until a supplier Feature Gate explicitly authorizes schema.

## Testing Impact

None in this pass (docs only). Future supplier tests must include multi-supplier neutrality and must not require a single PreferredSupplier.

## Documentation Impact

- [supplier-channel-and-launch-partner.md](../architecture/supplier-channel-and-launch-partner.md) (new)
- [supplier-catalogue-inventory-pricing.md](../architecture/supplier-catalogue-inventory-pricing.md)
- [modules/supplier-catalogue.md](../modules/supplier-catalogue.md)
- architecture / ADR / roadmap / current-state / session-handoff / chat-workflow-log indexes

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman (supplier-channel commercial clarification; architecture pass) | 2026-08-30 |
| ChatGPT review | Pending review of this architecture pass | |
| Cursor implementation note | Documentation only. No product code, schema, or Feature Gate. | 2026-08-30 |

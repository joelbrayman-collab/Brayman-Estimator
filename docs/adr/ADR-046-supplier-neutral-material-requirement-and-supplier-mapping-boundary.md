# ADR-046 — Supplier-Neutral Material Requirement and Supplier Mapping Boundary

| Field | Value |
|-------|--------|
| Title | ADR-046: Supplier-Neutral Material Requirement and Supplier Mapping Boundary |
| Status | **Accepted** (governance / architecture only; **not implemented**) |
| Date | 2026-09-09 |
| Related | [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) · [fg-029-bmr-supplier-workflow-v1-preflight.md](../architecture/fg-029-bmr-supplier-workflow-v1-preflight.md) · [ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** · [ADR-034](ADR-034-canonical-material-identity-and-ownership.md) **Accepted** · [ADR-035](ADR-035-material-quantity-uom-and-requirement-boundary.md) **Accepted** · [ADR-036](ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** · [ADR-008](ADR-008-supplier-price-snapshotting.md) **Proposed** · [ADR-044](ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-007](ADR-007-plan-and-estimate-version-ownership.md) **Accepted** · [ADR-024](ADR-024-learn-recommendation-boundary.md) **Accepted** |

This ADR authorizes the **V1-03 ownership and commercial boundary**. Recording [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) does **not** authorize product code, schema, migration, live database writes, synthetic DB population, a live BMR API, or acceptance of [ADR-008](ADR-008-supplier-price-snapshotting.md).

---

## Context

CalibraytAI V1-03 must demonstrate, honestly, that a contractor can bring a **reviewed project material requirement** to BMR Winchester without forcing the dealer to perform a second take-off.

Repository evidence (2026-09-09 preflight):

- `CanonicalMaterial` exists (FG-014). It is supplier-neutral identity. It forbids SKU, price, inventory, and branch fields.
- `TakeoffPackageItem` is PLAN quantity/citation/`element_type` evidence. FG-010 authorized extractor remains **interior-door count only**. There is **no** lumber take-off.
- FG-026 maps approved take-off to existing Assembly or CostItem. It does **not** create `MaterialRequirement` or supplier SKU.
- FG-027 owns human-approved costing snapshots. Pricing Engine consumes CURRENT costing and becomes **STALE / REQUIRES RE-APPLY** if costing changes.
- No `Supplier`, `SupplierProduct`, mapping table, or Supplier Package exists. Only free-text `CostItem.supplier`.
- ADR-008 remains **Proposed**. ADR-036 forbids operational estimate/PO **consumption** of supplier price until ADR-008 or a successor is accepted.
- ADR-035 anticipated `MaterialRequirement` but did not own or authorize it. Material Catalogue V1 **prohibits** owning `MaterialRequirement`.

Without this ADR, a first Winchester slice could put SKU on take-off, treat dealer catalogue as identity, silently write supplier price onto estimate cost, or claim live BMR integration that does not exist.

---

## Decision

A. **`CanonicalMaterial` remains supplier-neutral identity.** Organizations and suppliers map **to** it. They do not define it. Winchester SKUs must not become the vocabulary ([ADR-033](ADR-033-supplier-neutrality-and-launch-partner-channel.md), [ADR-034](ADR-034-canonical-material-identity-and-ownership.md)).

B. **`MaterialRequirement` is the thin project bridge** needed for supplier workflow. It answers: *what this project requires, in canonical identity, quantity, and UOM,* in a form suitable for supplier mapping. It is **not** a duplicate estimate, **not** PLAN evidence, and **not** a supplier SKU.

C. **`MaterialRequirement` does not become PLAN evidence.** Plan Intelligence retains `TakeoffCandidate` / `TakeoffPackage` / `TakeoffPackageItem`.

D. **`TakeoffPackage` / `TakeoffPackageItem` remain PLAN-owned** and must **not** gain supplier, SKU, supplier price, inventory, or availability.

E. **Supplier mapping is downstream** of the supplier-neutral requirement. Mapping records attach a supplier product/SKU to a requirement (via canonical material). They do not rewrite identity or PLAN quantity.

F. **Supplier products / SKUs are supplier-specific identities** owned by the proposed Supplier Catalogue. They map **to** `CanonicalMaterial`. They are not canonical identity.

G. **Human review/approval remains required** for V1 supplier mapping. AI does not pick SKU. No ML confidence. No LEARN ([ADR-024](ADR-024-learn-recommendation-boundary.md), [ADR-006](ADR-006-human-approval-before-estimate-insertion.md)).

H. **Synthetic / demo supplier evidence must be explicitly labeled** (`DEMO_SYNTHETIC` or equivalent). Labeled demo data does **not** imply a live BMR API, live inventory, or live contractor pricing.

I. **Supplier Package is a frozen supplier-facing artifact / snapshot.** Issued packages must not float when living catalogue, price, availability, or mapping later changes. This freeze is **fulfillment-package evidence**. It is **not** ADR-008 estimate/PO price consumption.

J. **V1 supplier price is INFORM ONLY.** It may appear in mapping review and on the Supplier Package.

K. **V1 supplier price does not silently update** `EstimateLineItem`, FG-027 costing snapshots, FG-009 `EstimatePricingSnapshot`, or customer selling price.

L. **Supplier price → estimate working cost** requires a **separate later governed authorization** (ADR-008 or an approved successor, plus a Feature Gate slice). It is **out of FG-029**.

M. **No silent supplier-data mutation of approved costing.** FG-027 remains authoritative for human-approved project costing.

N. **No live external order submission in V1-03.** The demo may show an order-ready / review-ready package. That is **not** a submitted purchase order.

O. **No live BMR API is implied** by manual or demo supplier evidence. **REAL BMR INTEGRATION NOT AVAILABLE** in this repository.

P. **Supplier workflow does not create a new top-level lifecycle stage.**

Q. **PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN remains unchanged.** V1 UI lives under Project Hub **PRICE** / materials.

R. **[ADR-008](ADR-008-supplier-price-snapshotting.md) remains Proposed / not accepted.** This ADR does **not** accept it.

S. **Organization / project isolation** applies to project supplier workflow (`MaterialRequirement`, contractor–supplier account, Supplier Package). Supplier master/location/product rows are not CalibraytAI tenants. They must not leak across contractor organizations except via an explicit procurement account (relationship **A**).

T. **Architecture must support later replacement** of synthetic/manual evidence with real supplier integration **without rewriting issued package history** or locked estimates.

### MaterialRequirement — minimum role

| Field | V1 pin |
|-------|--------|
| Owner | **Material Catalogue** expands to own project application of identity. Estimating does **not** own it. Supplier Catalogue does **not** own the supplier-neutral requirement. PLAN does **not** own it. |
| Purpose | Thin, reviewed, supplier-neutral project requirement for mapping |
| Distinct from | `TakeoffCandidate`, `TakeoffPackageItem`, `EstimateLineItem`, `CanonicalMaterial`, `SupplierProduct` / SKU |
| Organization | `organization_id` required (contractor tenant, e.g. ORG-001) |
| Project | `project_id` required |
| Canonical material | Required FK to `canonical_materials` |
| Quantity / unit | Required; unit is canonical requirement UOM, **not** supplier pack UOM |
| Description / label | Display from canonical material; optional project note. No pricing policy. |
| Source | `MANUAL` / `DEMO_SYNTHETIC` / optional cite of `EstimateLineItem` or takeoff citation. Demo lumber lines are **manual/synthetic**, not FG-010 extraction. |
| Status | `DRAFT` \| `REVIEWED` |
| Provenance | actor, time, source_kind, optional citation ids |
| Snapshot | Living until copied into an **issued** Supplier Package; issued copies freeze |
| Pricing | **Forbidden** on the requirement row |
| Supplier SKU | **Forbidden** on the requirement row; mapping is a separate record |

`MaterialRequirement` must **not** duplicate commercial estimate presentation, waste policy, markup, or selling price.

### Supplier identity — minimum V1 model

| Concept | Role | V1 |
|---------|------|----|
| Supplier | Legal/trade dealer organization | Yes — e.g. BMR Winchester as DEMO supplier |
| Supplier location / branch | Inventory/delivery/local identity | Yes — one Winchester branch |
| Contractor–supplier account | Relationship **A** only | Yes — ORG-001 ↔ Winchester |
| CalibraytAI channel partnership | Relationship **B** | **Out of V1-03** |
| Darcy originator record | Channel economics | **Out of V1-03** |
| SupplierProduct / SKU | What the dealer sells | Yes — labeled DEMO |
| Mapping | CanonicalMaterial ↔ SupplierProduct | Human-reviewed; statuses `UNRESOLVED` \| `REVIEW_REQUIRED` \| `MAPPED` |

BMR Winchester is representable as DEMO supplier + branch **without** claiming BMR corporate systems, EDI, or live pricing.

### Commercial boundary

```text
LIVING DEMO / FUTURE SUPPLIER EVIDENCE
→ HUMAN MAPPING REVIEW
→ ISSUED SUPPLIER PACKAGE (FROZEN)
→ HTML + PDF

EstimateLineItem / FG-027 / FG-009 / customer price
remain UNCHANGED by supplier evidence in V1-03
```

---

## Alternatives Considered

- **Put SKU / price on `TakeoffPackageItem`** — Rejected: PLAN must stay supplier-neutral ([ADR-035](ADR-035-material-quantity-uom-and-requirement-boundary.md)).
- **Skip `MaterialRequirement`; put canonical identity only on Supplier Package lines** — Rejected as V1 architecture: conflates requirement with one dealer package; weaker later multi-supplier growth. Thin `MaterialRequirement` is the preflight-required bridge.
- **Use CostItem as the requirement** — Rejected: CostItem is org costing, mixed categories, optional identity link, free-text supplier.
- **Accept ADR-008 in this pass so supplier price can update estimates** — Rejected: V1-03 is inform-only; estimate consumption is a later gate.
- **Live BMR API / PO submit in V1** — Rejected: no integration evidence in repository; overstates capability.
- **New lifecycle stage SUPPLY / PROCURE** — Rejected: stays under PRICE.
- **Housewrap / ½″ drywall as V1 CanonicalMaterial** — Rejected for this gate: outside FG-014 dimensional lumber + sheet goods identity. Demo uses existing FG-014 seeds.
- **Treat FG-010 door take-off as lumber take-off** — Rejected: dishonest.

## Consequences

**Positive:** Honest BMR demo spine; identity stays CalibraytAI-owned; PLAN/PRICE costing boundaries preserved; later real integration can replace `DEMO_SYNTHETIC` without rewriting issued packages.

**Negative:** First demo lumber quantities are human/manual, not extracted from drawings. Material Catalogue module ownership expands (was identity-only). Estimators must learn requirement vs estimate line vs dealer SKU.

## Module Ownership Impact

| Concern | Owner |
|---------|--------|
| `CanonicalMaterial` identity | **Material Catalogue** (unchanged) |
| `MaterialRequirement` | **Material Catalogue** (new; project application of identity) |
| Supplier, location, product, mapping, living price/availability evidence | **Supplier Catalogue** (still unimplemented) |
| Supplier Package freeze + HTML/PDF | **Supplier Catalogue** (consume Material Catalogue + project identity) |
| `TakeoffPackageItem` | **Plan Intelligence** (unchanged) |
| `EstimateLineItem` / costing snapshots / Pricing | **Estimating** / Pricing Engine (unchanged; not written by V1-03) |
| Contractor–supplier account (A) | Supplier Catalogue |
| Channel partnership (B) | **Not in V1-03** |

## Data Ownership Impact

No tables exist today. Future additive schema is recorded in [fg-029-bmr-supplier-workflow-v1-preflight.md](../architecture/fg-029-bmr-supplier-workflow-v1-preflight.md). Issued Supplier Package lines are immutable commercial/fulfillment history for the **supplier-facing** artifact. They are not estimate history.

## Migration Impact

**Deferred.** Proposed next Alembic revision (not created): `b6c7d8e9f0a1`, `down_revision = a5b6c7d8e9f0`. Create only under a later FG-029 **implementation** authorization.

## Testing Impact

None in this recording pass. Later implementation tests are listed in FG-029 / the preflight. Do not implement tests now.

## Documentation Impact

[FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md); V1-03 preflight; V1 register (status text only; **do not rescore**); current-state; session-handoff; module docs; supplier-channel architecture current pointers. Do not rewrite closed Feature Gate narratives.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman (V1-03 ADR + FG recording authorization) | 2026-09-09 |
| ChatGPT review | Authorized docs-only prompt | 2026-09-09 |
| Cursor implementation note | Docs/ADR/FG/preflight only. No product code. ADR-008 **not** accepted. | 2026-09-09 |

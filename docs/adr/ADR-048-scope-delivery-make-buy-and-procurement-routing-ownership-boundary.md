# ADR-048 — Scope Delivery, Make-Buy, and Procurement Routing Ownership Boundary

| Field | Value |
|-------|--------|
| Title | ADR-048: Scope Delivery, Make-Buy, and Procurement Routing Ownership Boundary |
| Status | **Accepted.** Slice A product implementation is **separate** from this ADR’s architecture recording. [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **SLICE A IMPLEMENTED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / SLICE B NOT AUTHORIZED / NOT CLOSED**. |
| Date | 2026-09-09 |
| Related | [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) · [fg-031-scope-delivery-make-buy-procurement-routing-preflight.md](../architecture/fg-031-scope-delivery-make-buy-procurement-routing-preflight.md) · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-007](ADR-007-plan-and-estimate-version-ownership.md) **Accepted** · [ADR-021](ADR-021-monitor-commercial-baseline.md) **Accepted** · [ADR-024](ADR-024-learn-recommendation-boundary.md) **Accepted** · [ADR-029](ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** · [ADR-044](ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** · [ADR-046](ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** · [ADR-047](ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only) · [ADR-008](ADR-008-supplier-price-snapshotting.md) **Proposed** |

This ADR authorizes the **ownership and commercial boundary** for how project scope is delivered (who supplies material; who performs labour). Slice A product code is authorized only by a separate implementation prompt. This ADR does **not** authorize live database writes, Slice B, FG-030 implementation, V1-04, or acceptance of [ADR-008](ADR-008-supplier-price-snapshotting.md).

---

## Context

CalibraytAI must decide, before final costing is locked, **how** each commercial line is delivered. A project mixes internal labour, contractor-purchased material, complete subcontract, and hybrid combinations.

Repository evidence (2026-09-09 recon):

- PLAN owns quantities/citations (`TakeoffPackage` / `TakeoffPackageItem`). FG-026 maps takeoff to `EstimateLineItem` only.
- `EstimateLineItem` has no delivery-routing fields. `CostItem.category` includes `Subcontractor` as a reusable library label. `CostItem.supplier` is free-text.
- `ProjectCommercialContext.delivery_model` is project-level (`Self-Perform` / `Mixed` / `Primarily Subcontracted`), not line routing.
- `MaterialRequirement` is supplier-neutral (ADR-046). FG-029 Supplier Package freeze currently includes **all** project requirements for a supplier/location — no delivery filter.
- Labour snapshots are EstimateVersion-scoped and opt-in; they are **not** in default selling-price basis (ADR-044 D).
- No `Subcontractor` entity and no subcontract RFQ/package exist. Historical subcontract rows are FG-006 evidence only.
- MONITOR actuals use `labour` / `material` / `subcontract` / `other_direct` independently of planned routing.

Without this ADR, routing could be stored on PLAN, catalogues, or a single overloaded HYBRID enum — contaminating reusable identity and leaking subcontract material into BMR Supplier Packages.

---

## Decision

**Accepted as architecture.** Do **not** treat acceptance as product implementation.

A. **PLAN remains quantity/evidence authority.**

B. **PLAN does not own** who performs work, who provides material, subcontractor identity, supplier identity, delivery routing, commercial margin, or selling price.

C. **Estimating owns** project-specific scope-delivery routing.

D. **Routing is EstimateVersion-scoped and commercial-line-specific.**

E. **V1 unit:** one `EstimateScopeDelivery` per `EstimateLineItem` (1:1).

F. **Do not store routing on** `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem`, `CostItem`, `Assembly`, `AssemblyItem`, `CanonicalMaterial`, or `MaterialRequirement`.

G. **Two independent stored dimensions are authoritative.**

Material procurement:

- `CONTRACTOR_PURCHASED`
- `SUBCONTRACTOR_SUPPLIED`
- `OWNER_SUPPLIED`
- `NO_MATERIAL`
- `UNRESOLVED`

Labour delivery:

- `INTERNAL`
- `SUBCONTRACT`
- `OWNER_THIRD_PARTY`
- `NO_LABOUR`
- `UNRESOLVED`

H. **Do not store a HYBRID enum.** Hybrid is derived from the two dimensions.

I. **User-facing summary classifications** (Internal, Subcontract, Material only, Hybrid, Unresolved, Allowance) are **display language**, not stored commercial authority.

J. **One `EstimateSection` may contain mixed routing.**

K. **Assemblies and CostItems remain reusable and project-neutral.**

L. **If one Assembly requires component-level mixed delivery in V1, split it into separate commercial `EstimateLineItem` rows.** Component-level Assembly routing is **POST-V1**.

M. **Working routing may change on an editable Draft `EstimateVersion`.**

N. **Issued/locked `EstimateVersion` rows cannot change routing.**

O. **Routing must preserve version history.** Two estimate versions may route the same scope differently.

P. **Clone/version operations must copy routing onto cloned commercial lines.**

Q. **Human confirmation is required.**

R. **Deterministic suggestions are permitted** (`RULE`, `ORG_DEFAULT`, `NONE`).

S. **No ML/confidence value may silently authorize routing.** [ADR-024](ADR-024-learn-recommendation-boundary.md) remains in force.

T. **Future organization defaults may suggest routing** but must **never rewrite** historical project decisions.

U. **[FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) remains final authority** for approved direct costing. Do not reopen that gate. FG-031 adds an upstream BLOCK: `SCOPE_DELIVERY_UNRESOLVED` unless routing is **CONFIRMED** (except legitimate Allowance). `PROPOSED` is not costing authority.

V. **Routing itself does not** apply Pricing, set margin, set markup, set tax, or set contingency.

W. **Supplier Package eligibility is downstream of routing.** Only `CONTRACTOR_PURCHASED` material is normally supplier-package eligible.

X. **Supplier price remains INFORM ONLY** under [ADR-046](ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) / [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md).

Y. **Customer Estimate remains delivery-blind** unless a later commercial decision specifically authorizes disclosure. The customer must not see internal labour rates, supplier prices, subcontract quote cost, margin, markup, or internal make/buy classification.

Z. **Subcontractor workflow remains distinct from supplier workflow.**

AA. **Subcontractor identity must not be silently collapsed into `Supplier`.**

AB. **BUILD/MONITOR must eventually use frozen approved routing**, not floating Draft routing.

AC. **Historical CalibraytAI architecture/snapshots remain immutable.**

---

## Alternatives considered

- One four-way stored enum (Internal / Subcontract / Material only / Hybrid) — **Rejected.** Hybrid combinations are ambiguous; two dimensions are the authority.
- Store routing on `MaterialRequirement` or `CostItem` — **Rejected.** Contaminates supplier-neutral identity and reusable catalogues.
- Store routing on PLAN takeoff items — **Rejected.** Violates ADR-007 / ADR-046 PLAN boundary.
- Component-level Assembly routing in V1 — **Rejected for V1.** Split commercial lines instead.

---

## Consequences

**Positive:** Honest BMR demo (no subcontract HVAC material in Winchester packages); hybrid scopes without HYBRID enum; catalogues stay reusable; FG-027/Pricing/PLAN remain bounded.

**Negative:** Estimators may need two commercial lines when one Assembly mixes delivery at component level. Uncited MANUAL/DEMO `MaterialRequirement` rows need explicit contractor-purchased reconciliation before package inclusion.

---

## Module ownership impact

| Module | Role |
|--------|------|
| Estimating | Owns `EstimateScopeDelivery` (and later Slice B quote evidence / thin Subcontractor party) |
| Material Catalogue | Continues to own `CanonicalMaterial` and thin `MaterialRequirement` |
| Supplier Catalogue | Continues to own mapping and Supplier Package; **filters** by routing; does not own routing |
| Labour Engine | Continues to own `LabourTask` / snapshots; routing `INTERNAL` **permits** opt-in snapshot; does not auto-create |
| Plan Intelligence | Unchanged quantity/evidence owner |
| MONITOR / BUILD | Later consume frozen routing; do not own it |

---

## Data ownership impact

Working routing is Estimating-owned, org-isolated, EstimateVersion-scoped. Freeze `material_procurement` and `labour_delivery` onto `EstimateCostingSnapshotLine` at costing approval. Do not invent a second routing snapshot table for Slice A.

---

## Migration impact

**Slice A product:** additive file **`c7d8e9f0a1b2`** (`down_revision = b6c7d8e9f0a1`). Creates `estimate_scope_deliveries` and nullable costing-snapshot freeze columns. **Not applied live.** This ADR does **not** authorize live migrate.

---

## Testing impact

Slice A dedicated tests live in `tests/test_scope_delivery_fg031.py`. Architecture recording itself did not run product tests.

---

## Documentation impact

ADR index; FG-031; preflight; current-state; session-handoff; project-state-report; roadmap; V1 register (status text only; **no rescore**); estimating / supplier / material / labour module current-authority notes.

---

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Authorized recording via ChatGPT prompt | 2026-09-09 |
| ChatGPT review | Architecture from completed recon | 2026-09-09 |
| Cursor implementation note | Docs/governance only. Product implementation **not** authorized. |

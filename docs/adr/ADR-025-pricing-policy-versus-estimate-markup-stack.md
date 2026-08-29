# ADR-025 — Pricing Policy versus Estimate Markup Stack

| Field | Value |
|-------|--------|
| Title | ADR-025: Gross-Margin Policy versus Existing Estimate Markup Stack |
| Status | **Accepted** |
| Date | 2026-08-28 (original) · Amended and accepted 2026-08-29 |
| Related | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [pricing-policy.md](../pricing-policy.md) · [modules/estimating.md](../modules/estimating.md) · [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) · [organization-calibrated-pricing-engine-architecture.md](../architecture/organization-calibrated-pricing-engine-architecture.md) · [ADR-030](ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) |

This ADR does **not** authorize calculation-code changes. FG-009 implementation requires a **separate** bounded execution prompt.

---

## Context

CAR-001 verified a discrepancy. FG-009 architecture (2026-08-29) audited live code and historical evidence and **selects** an engine capability the original ADR left unchosen.

**Current estimate code** (`app/services/estimate_builder.py` and related models):

- Line sell price uses **markup percent** on extended cost: `extended_cost * (1 + markup_percent/100)`
- Version `subtotal` is the sum of **sell prices** (already marked up)
- Version totals then apply **overhead percent** on that subtotal and **profit percent** on `(subtotal + overhead)` (and tax percent after that)

**Governing ORG-001 pricing policy** (`docs/pricing-policy.md`):

- Labour direct cost reference: **$65 CAD / man-hour** (Labour Engine / org policy — not this ADR’s formula)
- Target gross margin: **15% true gross margin**
- `Selling Price = Direct Cost / (1 - Gross Margin)` = **Direct Cost / 0.85**
- 15% gross margin is **not** a 15% markup

**Quantified distinction** ($100 Direct Cost at 15%):

| Method | Pre-tax selling price |
|--------|------------------------|
| 15% markup | $115.00 |
| 15% true gross margin | $117.647… |

These are **not mathematically equivalent**. Historical Brayman workbooks often **label** “15% Margin” while adding 15% of cost (markup). That evidence must not silently become ORG-APPROVED true-GM policy.

Change Orders today use a **different** formula (single markup on item subtotal; UI may default markup from `overhead_percent`). That inconsistency is in scope for FG-009 architecture, not a silent CAR-001 fix.

---

## Decision

1. **CalibAi** owns named pricing **methods** and snapshot/immutability rules. **Each organization** owns which method and which rates it approves.
2. The engine **shall support multiple explicit methods**, not a silent translation:
   - `TRUE_GROSS_MARGIN` — `Sell = Direct Cost / (1 − target_gross_margin)`
   - `COST_PLUS_MARKUP` — `Sell = Direct Cost × (1 + markup_rate)`
   - `COST_PLUS_MARKUP_STACK` — the **existing** line-markup + overhead + compounding profit stack, preserved as a **named** method for legacy estimates and organizations that use it
3. **Do not replace** the live stack globally. **Do not** map 15% true GM onto `markup_percent = 15` (or onto overhead/profit fields). **Do not** relabel `COST_PLUS_MARKUP_STACK` as true gross margin.
4. **ORG-001 intended operating method** (when FG-009 is implemented): `TRUE_GROSS_MARGIN` at 15%, per `pricing-policy.md`. That is **org policy**, not a CalibAi default.
5. Existing issued/accepted/locked estimate versions **must not** be recalculated. When snapshots exist, classify them as `COST_PLUS_MARKUP_STACK` from stored fields without changing totals.
6. `$65/hr` and 15% true GM **policy text** remain authoritative for ORG-001. Code application remains blocked until an FG-009 **implementation** prompt is approved.
7. Policy **records**, resolution order, contingency/overhead treatment, and estimate **snapshots** are specified in [ADR-030](ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) (**Accepted**). This ADR decides **methods**, not the full persistence model.
8. For `TRUE_GROSS_MARGIN`, target gross margin governs selling-price mathematics. Overhead and profit must **not** be preserved invisibly as the old compounding stack inside that method. Their treatment is explicit org-policy configuration (ADR-030).

---

## Alternatives Considered

| Alternative | Disposition |
|-------------|-------------|
| **Replace markup/overhead/profit with gross-margin formula only** (all orgs, immediately) | **Rejected.** Violates organization-owned commercial intelligence; would silently rewrite live/legacy estimates. |
| **Keep markup stack only; treat true GM as aspirational documentation** | **Rejected.** ORG-001 policy is already governing; the engine must be able to apply it without pretending 15% markup equals 15% GM. |
| **Dual-mode / named methods** (true GM **and** cost-plus stack as selectable methods) | **Selected.** |
| **Map 15% margin onto existing percent fields** | **Rejected.** Incorrect if done as 15% markup; conceals method identity. |
| **Remain Proposed with no method selection** (original 2026-08-28 text) | **Superseded.** |

---

## Consequences

- Until FG-009 **implementation**, internal totals may not match ORG-001 true-GM selling price. UAT reference case (3415 Roger Stevens) must not be treated as implemented in-app true-GM pricing.
- After implementation, organizations can select methods without mixing formulas. Legacy stack remains available and named.
- Change Order economics must inherit the estimate pricing snapshot in FG-009 implementation (see ADR-030). Historical Change Orders are not rewritten.

## Module Ownership Impact

Estimating continues to host line/version calculation **execution**. Pricing Engine owns **methodology**, policy types, and snapshot contract. Pricing **values** remain organization-owned. `docs/pricing-policy.md` remains the ORG-001 governing text until seeded as org policy data.

## Data Ownership Impact

None until FG-009 implementation + ADR-030 persistence. Historical estimate versions must not be silently recalculated. Historical ingestion facts remain evidence-only.

## Migration Impact

**Deferred** to an approved FG-009 implementation prompt (Rule 7). None in this governance pass.

## Testing Impact

None until implementation. FG-009 requires tests that true GM ≠ markup at the same nominal percent, invalid margin fail-closed, legacy stack still computes as today for classified versions, and locked versions do not float.

## Documentation Impact

FG-009; organization-calibrated pricing architecture; ADR-030; pricing-policy.md; estimating module.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel | **2026-08-29** — AMEND AND ACCEPT |
| ChatGPT review | Dual-method amendment accepted with FG-009 architecture | 2026-08-29 |
| Cursor implementation note | **Accepted** as documentation. **No product code.** Implementation not authorized. | 2026-08-29 |

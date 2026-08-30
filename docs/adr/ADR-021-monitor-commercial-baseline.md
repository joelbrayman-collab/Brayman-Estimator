# ADR-021 — MONITOR Commercial Baseline

| Field | Value |
|-------|--------|
| Title | ADR-021: MONITOR Approved Commercial Baseline and Project Gross Margin |
| Status | **Accepted** (governance / architecture only; MONITOR **not implemented**) |
| Date | 2026-08-28 (Proposed); **Accepted 2026-08-30** |
| Related | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [ADR-002](ADR-002-accepted-proposal-immutability.md) · [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) · [ADR-020](ADR-020-build-module-boundary.md) · [ADR-024](ADR-024-learn-recommendation-boundary.md) · [ADR-025](ADR-025-pricing-policy-versus-estimate-markup-stack.md) · [ADR-030](ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) · [pricing-policy.md](../pricing-policy.md) · [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) · [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) |

## Context

CalibAi MONITOR will compare ESTIMATED ↔ ACTUAL ↔ FORECAST for labour, materials, subcontractors, total cost, schedule/progress, changes, and margin. Several commercial records already exist (locked estimate versions, `EstimatePricingSnapshot`, Accepted Proposal snapshots, Change Orders). CAR-001 approved the MONITOR comparison model and the invariants that approved commercial baselines remain preserved, actuals do not rewrite the approved estimate, and forecasts are dated/versioned snapshots.

Until this acceptance, the **baseline pointer** was open: a specific `EstimateVersion`, an Accepted Proposal snapshot, a composed baseline including approved Change Orders, or an explicit Project baseline pointer.

A 2026-08-30 architecture reconnaissance (calibration / benchmarking / profitability) confirmed that MONITOR and project profitability must not use a floating draft, must not treat industry benchmarks as profitability truth, and must not wait on QuickBooks or Phase D. The remaining blocker was this ADR.

Accepting this ADR **does not** authorize MONITOR code, BUILD actuals, profitability UI, industry benchmarking, historical-upload onboarding, schema, or a Feature Gate.

## Decision

### 1. MONITOR comparison model (CAR-001, unchanged)

1. MONITOR compares estimated, actual, and forecast figures.
2. Approved estimates / commercial baselines remain **preserved**.
3. **Actuals do not rewrite** the approved estimate, Accepted Proposal, or Change Order commercial records.
4. **Forecasts** are dated/versioned snapshots, not silently overwritten values.

### 2. Authoritative project profitability term

The initial authoritative CalibAi project profitability metric is **PROJECT GROSS MARGIN**.

**NET PROFIT is not** the authoritative project metric at this stage. Net profit would require additional governed policy for overhead allocation, payroll burden if outside Direct Cost, G&A, corporate expense allocation, financing, depreciation, and other indirect costs. Those policies are **not governed**. Future NET PROFIT may be introduced only after separate accounting/commercial governance.

ORG-001 optional overhead / profit / contingency treatments remain `UNSPECIFIED` ([pricing-policy.md](../pricing-policy.md); FG-009). This ADR does not invent them.

### 3. Frozen composed estimated baseline (not a floating draft)

The MONITOR estimated commercial baseline is a **frozen composed baseline**. Preserve three layers separately. Do **not** collapse them into one rewritten number.

**A. Original estimated commercial baseline**

- The locked `EstimateVersion` that is the source of the customer commitment.
- The authoritative `EstimatePricingSnapshot` **when present** (FG-009 / ADR-030): frozen estimated Direct Cost (`direct_cost_basis`), frozen pre-tax selling price (`pre_tax_selling_price`), frozen tax and customer total.
- When no pricing snapshot exists (legacy `COST_PLUS_MARKUP_STACK` path), estimated Direct Cost remains Σ `EstimateLineItem.extended_cost` (FG-012) and estimated pre-tax selling price is taken from the **Accepted Proposal** commercial snapshot (see B), not from a later draft version. Do **not** backfill a snapshot under this ADR.

**B. Customer commitment**

- The **Accepted Proposal** (ADR-002) is the immutable customer commercial commitment.
- It remains tied to its source `EstimateVersion`.
- It must **not** be mutated when a Change Order occurs.

**C. Post-commit commercial amendments**

- **Approved Change Orders** (Project Controls) are auditable commercial deltas **after** the original Accepted Proposal.
- They must remain separate records. Do not rewrite the original baseline or Accepted Proposal when a Change Order is approved.

### 4. Floating-draft prohibition

Future MONITOR / profitability calculations **must not** use any of the following as the authoritative committed baseline:

- the current Draft `EstimateVersion`
- a later revised draft estimate
- a Draft Proposal
- manually restacked Draft Proposal totals

FG-012 residual debt: Draft Proposal line edits may still invoke legacy `recalculate_proposal`. That residual **must not** contaminate profitability baselines. Accepted Proposal totals and locked version / pricing-snapshot totals remain the pins.

### 5. Original / Change / Actual reporting architecture

Future MONITOR must be capable of showing three distinct layers:

```text
ORIGINAL BASELINE
+ APPROVED CHANGE ORDER DELTAS
vs ACTUAL PERFORMANCE
```

Conceptual identities (governance only — **not implemented**):

```text
Original Estimated Direct Cost
+ Approved CO Estimated Cost Delta   (only where such estimate-cost evidence exists)
= Current Authorized Estimated Cost

Original Authorized Pre-Tax Revenue
+ Approved CO Pre-Tax Revenue Delta
− Authorized Credits / reductions    (only when a governed credit mechanism exists)
= Current Authorized Pre-Tax Revenue  (“Final Authorized Revenue” for GM)

Then compare against verified Actual Direct Cost.
```

Do not implement these formulas in product code under this ADR.

### 6. Project Gross Margin identities (conceptual)

Tax remains **outside** gross-margin arithmetic. Use **pre-tax** values. Do not use tax-collected amounts as revenue or margin.

```text
Estimated Gross Margin
  = 1 − (Estimated Direct Cost / Estimated Pre-Tax Selling Price)

Actual Gross Margin
  = 1 − (Actual Direct Cost / Final Authorized Pre-Tax Revenue)

Gross Margin Variance
  = Actual Gross Margin − Estimated Gross Margin
```

Industry benchmarks are **not** inputs to these identities.

### 7. Final Authorized Revenue

Final Authorized Revenue is the customer’s **authorized commercial commitment**, not invoiced status, cash received, accounting revenue recognition, or customer payments, unless later accounting governance expressly says otherwise.

**Current platform architecture:**

| Component | Source |
|-----------|--------|
| Base | Accepted Proposal **pre-tax** commercial amount. Prefer `EstimatePricingSnapshot.pre_tax_selling_price` when the Accepted Proposal’s source version has a snapshot (FG-012 named-method path). Legacy no-snapshot: Proposal `subtotal + overhead_amount + profit_amount` (exclude `tax_amount` / `total`). |
| Plus | Approved Change Order **pre-tax** commercial amount (`subtotal + markup` on the current CO model; tax excluded). |
| Minus | Approved customer credits / reductions **when such a governed mechanism exists**. |

**Change Order limitations (record; do not add schema):**

- CO items are **sell-side** (`quantity × unit_price`). Today’s CO total is **not** actual cost and is **not** a stored estimated Direct Cost delta.
- Statuses are a single string: `Draft`, `Pending Approval`, `Approved`, `Rejected`, `Invoiced`, `Cancelled`. `Invoiced` is a CO lifecycle label, **not** accounting revenue recognition or cash received. Future MONITOR must not treat `Invoiced` as books revenue. Implementation must also not drop a commercially authorized CO from the authorized-revenue set solely because its status later became `Invoiced` rather than the string `Approved`.
- There is **no** governed customer-credit / reduction instrument. Negative prices are not a credit policy.
- Estimated **cost** delta for changed work is **not** separately stored. Current Authorized Estimated Cost cannot include a CO cost delta until later governance adds that evidence. Do not reinterpret `unit_price` as cost.

Do not change FG-009 Change Order pricing under this ADR.

### 8. Actual Direct Cost

Actual Direct Cost is a **future** governed sum of **verified ORG-ACTUAL** direct-cost evidence. It is **not implemented**.

Potential classes (when later gated and verified):

- actual direct labour cost
- actual materials
- actual subcontract costs
- actual equipment directly attributable to the Project
- other separately approved direct-cost classes

Corporate overhead / G&A are **not** Direct Cost here. This ADR does **not** define payroll-burden policy. Ambiguous classes (burden in vs out of Direct Cost; equipment rental vs owned; small tools; warranty cost) remain for later Joel approval.

QuickBooks is **not** required for this definition. Accounting integration may later become an actual-cost feed or reconciliation source only under separate governance. Current QuickBooks architecture remains customer-estimate **export** only.

### 9. Labour estimated vs actual (comparability)

| Record | Meaning |
|--------|---------|
| `EstimateLabourSnapshot` | **Estimated** labour evidence (FG-008). Not an actual. |
| Future `LabourActualObservation` | **Actual** organization performance evidence. Architecture-only today. No model. |

Do **not** automatically include `EstimateLabourSnapshot` Direct Labour Cost in the existing estimate selling-price basis (FG-009 / FG-012: Direct Cost = Σ `extended_cost`).

**Comparability issue (documented, not corrected here):** Estimated Gross Margin uses estimated Direct Cost that **excludes** Labour Engine snapshot cost by default. Actual Gross Margin will include verified actual labour cost when captured. Estimated vs actual GM will therefore **not** be labour-apples-to-apples until a later Feature Gate decides whether estimated labour-engine cost enters estimated Direct Cost, or labour is reported as a separate variance layer. Do not invent that correction in MONITOR or LEARN.

Actual labour may later be used in profitability even though estimated snapshot labour cost is currently excluded from selling-price basis.

### 10. MONITOR ownership

MONITOR is a **Project-centered comparison / read layer** on the existing `Project` hub ([ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md)).

It **consumes** immutable evidence owned by other modules:

| Evidence | Owner |
|----------|--------|
| Estimate versions, lines, labour snapshots | Estimating / Labour Engine |
| Pricing snapshots / policy | Pricing Engine |
| Accepted Proposal | Proposals |
| Change Orders | Project Controls (documented under Projects) |
| Field actuals | BUILD (when implemented; [ADR-020](ADR-020-build-module-boundary.md)) |
| Other actual-cost domains | Later owning modules when gated |
| ORG-APPROVED standards | Labour Engine / Pricing Engine (and later material/sub domains) |

MONITOR **must not** become the authoritative owner of estimates, proposals, Change Orders, field actuals, accounting actuals, or calibration standards.

When later Feature-Gated, MONITOR may persist **dated comparison snapshots** and **dated forecast snapshots** that it owns as comparison artifacts. Those snapshots must not mutate source records.

This ADR does **not** implement MONITOR. FG-011 Project Hub may continue to label MONITOR as Future.

### 11. Forecasts

If MONITOR later shows forecasts, they are **dated / versioned snapshots**. Do not silently overwrite prior forecast states. Do not implement forecasting. Do not create schema under this ADR.

### 12. LEARN boundary ([ADR-024](ADR-024-learn-recommendation-boundary.md))

MONITOR observes and compares. LEARN may later create review-gated calibration candidates.

Neither MONITOR nor LEARN may silently rewrite: `OrganizationPricingPolicy`, `LabourTask`, `LabourTaskMapping`, `ProductionRateStandard`, `DirectLabourCostRateStandard`, historical evidence, accepted proposals, or estimates.

ADR-024’s note that actuals may be “owned by BUILD/MONITOR when they exist” is **refined here**: BUILD owns field-execution capture; MONITOR compares. MONITOR does not become the actuals system of record.

### 13. Industry benchmark boundary

Industry benchmarks are **advisory external evidence** only. They are **not** part of ADR-021 profitability truth. Project Gross Margin is calculated from this organization’s commercial baseline plus this organization’s actual performance.

Cross-organization pooling of customer commercial data remains **not authorized**.

### 14. Phase D, auth, and BUILD

Phase D (take-off → estimate mapping) is **independent**. MONITOR / profitability governance does **not** depend on it. Phase D remains **NOT STARTED / NOT AUTHORIZED**.

Future field actual capture remains dependent on authentication before field (ADR-022). This ADR defines what evidence MONITOR expects; it does not implement capture, authentication, or BUILD.

Accepting this ADR **does not** authorize a MONITOR Feature Gate.

## Alternatives Considered

- **Always use current estimate version** — Rejected: current may still be Draft; later drafts must not become the committed baseline.
- **Always use Accepted Proposal only** — Rejected as the *sole* layer: it omits post-acceptance CO commercial effects and the estimate/pricing-snapshot Direct Cost pin. Accepted Proposal remains the customer-commitment layer inside the composed baseline.
- **Compose estimate + approved COs as one mutated live budget** — Rejected: COs must remain auditable deltas; do not rewrite the original baseline.
- **Compose locked EstimateVersion + EstimatePricingSnapshot + Accepted Proposal + approved CO deltas as separate layers** — **Accepted.**
- **NET PROFIT as the first official metric** — Rejected until overhead / burden / G&A are governed.
- **QuickBooks as mandatory actuals source** — Rejected: not implemented; current architecture is customer-estimate export.
- **Industry norms as profitability inputs** — Rejected.

## Consequences

**Positive:** MONITOR and later Project Gross Margin work have an accepted baseline pointer, a profitability term, tax-outside-GM rule, floating-draft prohibition, and a three-layer reporting model without requiring product code now.

**Negative:** Actual Direct Cost, CO estimated-cost deltas, credits, and labour-basis comparability remain unimplemented or incomplete. MONITOR Feature Gate is still required before code. Versions without a pricing snapshot use the dual FG-009 path.

## Module Ownership Impact

MONITOR is a comparison/read layer, not a transfer of Estimating, Proposals, Project Controls, BUILD, or Pricing Engine ownership. Named module note: [modules/monitor.md](../modules/monitor.md) (**Proposed / not implemented**).

## Data Ownership Impact

Source commercial records stay with their owning modules. Future MONITOR comparison/forecast snapshots (when gated) are MONITOR-owned artifacts. Actuals stay with BUILD / later actual-cost domains. Accepted Proposal remains immutable (ADR-002).

## Migration Impact

**None.** No schema. No Alembic revision. Implementation of MONITOR will require a Feature Gate and, if snapshots are persisted, a later approved migration.

## Testing Impact

None in this acceptance pass (documentation only). Future MONITOR tests must not use Draft estimates or Draft Proposal restacks as the committed baseline.

## Documentation Impact

This ADR; ADR index; CAR-001; pricing-policy.md; modules (projects, estimating, proposals, build, monitor, labour-engine); current-state; session-handoff; project-state-report; platform-roadmap; chat-workflow-log; review-turnover-protocol; architecture.md.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-30 |
| ChatGPT review | Architecture reconnaissance + bounded ADR-021 decision pass | 2026-08-30 |
| Cursor implementation note | Documentation / governance only. MONITOR not implemented. No schema, migration, or product code. | 2026-08-30 |

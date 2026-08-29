# Feature Gate FG-009: Organization-Calibrated Pricing Engine

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-009` |
| Feature Name | Organization-Calibrated Pricing Engine |
| Target Milestone | Organization-Calibrated Pricing Engine (not a numbered M0xx until implementation is authorized) |
| Module | Pricing Engine (Estimating consumes snapshotted selling-price results; Proposals/Change Orders reuse the same policy snapshot) |
| Date | 2026-08-29 |
| Status | **APPROVED FOR IMPLEMENTATION** — **NOT IMPLEMENTED** |
| Architecture | [organization-calibrated-pricing-engine-architecture.md](../architecture/organization-calibrated-pricing-engine-architecture.md) **Approved** |
| Related ADRs | [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** |
| Prerequisites | FG-007 / M011 **implemented**; FG-008 **implemented**; FG-006 **implemented** (evidence only) |
| Approved baseline | `main` @ `ff5d856d52433832c8b3099cb5a17ba72fb73db3` (docs-commit of this approval will advance HEAD; product code unchanged) |

---

## Status

| Layer | State |
|-------|--------|
| Architecture / readiness | **APPROVED** (2026-08-29; Joel and ChatGPT; contingency clarification adopted) |
| Feature Gate (this document) | **APPROVED FOR IMPLEMENTATION** |
| ADR-025 / ADR-030 | **Accepted** |
| Implementation | **HAS NOT YET STARTED.** No product code. No migration. Requires a separate bounded execution prompt. |

This gate does **not** implement selling-price application, four-output generation, QuickBooks, contracts, or Labour Engine expansion.

---

## Purpose and business rationale

CalibAi must own pricing **methodology** while each organization owns its **commercial intelligence**.

Without this engine:

- ORG-001’s governed 15% **true gross margin** (`Direct Cost / 0.85`) cannot be applied without silently falsifying the live markup/overhead/profit stack.
- Other organizations would inherit Brayman economics as if they were platform defaults.
- Change Orders already use a **different** formula from estimates, so commercial inconsistency will worsen.
- Four governed outputs cannot stay consistent with one authoritative commercial policy.

This gate defines the engine, named methods, Direct Cost boundary, snapshots, and resolution. Joel approved this gate **2026-08-29**. Cursor must **not** change calculation code until a **separate** implementation prompt is issued.

---

## Current-code findings

See the architecture report §3. Summary:

- Live estimates: line **cost-plus markup** on wasted extended cost; version `subtotal` is already sell; **overhead** on that subtotal; **profit compounds**; **tax** after pre-tax stack.
- Waste is on unit cost **before** markup.
- No contingency field; Pricing Posture / Execution Risk do not enter math.
- Proposals snapshot the current stack (waste baked into unit cost); Accepted snapshots immutable.
- Change Orders: single markup on item subtotal; default markup from `version.overhead_percent` when created from an estimate.
- Historical ingestion math is **separate evidence**.
- Labour Engine direct labour cost **can** enter later as Direct Cost **without** changing selling-price **method**, provided the engine consumes the cost amount only.

---

## Commercial formulas

### True gross margin (ORG-001 intended method)

```text
pre_tax_selling_price = Direct Cost / (1 - target_gross_margin)
```

At 15%: `Direct Cost / 0.85`.

### Cost-plus markup (simple)

```text
pre_tax_selling_price = Direct Cost × (1 + markup_rate)
```

### Margin vs markup (must test)

On $100 Direct Cost at 15%:

- Markup → **$115.00** (implied GM ≈ 13.04%)
- True GM → **$117.647…** (implied markup ≈ 17.65%)

### Legacy stack (`COST_PLUS_MARKUP_STACK`) — current code, preserved as a named method

```text
extended_cost = quantity × unit_cost × (1 + waste_percent/100)
sell_price    = extended_cost × (1 + markup_percent/100)
subtotal      = Σ sell_price
overhead      = subtotal × overhead_percent/100
profit        = (subtotal + overhead) × profit_percent/100
tax           = (subtotal + overhead + profit) × tax_percent/100
```

Customer-priced contingency is **not** universally an addend outside the margin basis. Visibility (`INTERNAL_RESERVE` | `CUSTOMER_PRICED` | `NOT_APPLIED`) is separate from pricing treatment (`INCLUDED_IN_MARGIN_BASIS` | `ADDED_AFTER_BASE_PRICING`). Tax remains after pre-tax customer selling price.

---

## Pricing-policy types

V1 required named methods:

- `TRUE_GROSS_MARGIN`
- `COST_PLUS_MARKUP`
- `COST_PLUS_MARKUP_STACK` (legacy explicit)

`TIERED` is architecture-ready, not required in first implementation.

Method belongs on the **versioned organization policy**, optionally selected on `ProjectCommercialContext`, and **always frozen** on the estimate pricing snapshot. Do not mix formulas.

ORG-001 intended default after implementation: `TRUE_GROSS_MARGIN` at 15%. Not a CalibAi universal default.

---

## Direct-cost boundary

**In (typical direct inputs):** materials (including material waste on those lines), direct labour (Labour Engine direct labour cost when wired; else legacy labour `unit_cost`), subcontracts, equipment, direct packages, allowances that are true/placeholder project costs.

**Never in Direct Cost as cost facts:** gross margin, profit as recovery, tax, Pricing Posture, Execution Risk.

**Overhead and contingency:** policy-defined. Do not silently force them into or outside Direct Cost.

**Contingency:** separate **source/purpose** from **customer visibility** (`INTERNAL_RESERVE` | `CUSTOMER_PRICED` | `NOT_APPLIED`) and, when customer-priced, **pricing treatment** (`INCLUDED_IN_MARGIN_BASIS` | `ADDED_AFTER_BASE_PRICING`). The engine must know whether contingency participates in the pricing formula. Not a hidden third rate. Historical examples are not universal policy.

---

## Overhead / profit treatment

- Do **not** equate overhead + profit percentages with gross margin.
- Under `TRUE_GROSS_MARGIN`: target GM governs selling-price mathematics. Whether overhead is treated as direct/project cost, included in margin economics, separately customer priced, or not applied **must be explicit** in org policy. Do **not** preserve the old compounding stack invisibly inside this method.
- Under `COST_PLUS_MARKUP_STACK`: existing legacy behavior remains explicitly represented as line markup, then overhead, then compounded profit.
- Under simple `COST_PLUS_MARKUP`: one recovery rate; overhead is explicit policy, not a hidden extra percent.

---

## Tax boundary

Tax is organization/jurisdiction policy. ORG-001 Ontario HST 13% is not a platform default. Apply after **pre-tax customer selling price** (which already reflects snapshotted contingency/overhead treatment).

---

## Pricing Posture

Commercial strategy. Snapshot it. **Must not** alter true quantities, hours, production rates, supplier facts, or direct labour cost facts.

V1: record only. No hidden multipliers. Later gates may map posture to **already-approved** org policies or approval thresholds — not authorized as product behavior until separately gated.

---

## Execution Risk

Distinct from posture. Snapshot it. May inform contingency/reserve selection, review, or approval threshold **via org policy tables**. Must not falsify quantity, rates, hours, or supplier cost.

---

## Policy resolution

1. Approved estimate/version-specific override  
2. ProjectCommercialContext explicit policy pointer (additive schema later)  
3. Active ORG-APPROVED organization pricing policy  
4. Organization default  
5. CalibAi BASELINE/reference (flagged; never silent Brayman economics; requires review)  
6. Provisional/manual — current coded stack with review flag  

Preserve organization, policy/version, source, effective date, reason, override reason, provenance.

---

## Versioning / estimate snapshot

Versioned `OrganizationPricingPolicy` + immutable `EstimatePricingSnapshot` on `EstimateVersion`. Later policy edits must not change old estimates. Accepted proposals remain immutable (ADR-002). Legacy versions classify as `COST_PLUS_MARKUP_STACK` without rewriting totals.

---

## Change Order behavior

Inherit the linked estimate version’s pricing snapshot. Separately approved override only. Do not keep the accidental `overhead_percent`→CO markup default as the governed rule. **Do not recalculate or rewrite historical Change Orders.**

---

## Four-output consistency

Same authoritative estimate + pricing snapshot. Internal output may show direct cost, hours, margin, contingency. Customer / QuickBooks / contract outputs must not expose internal cost rates or margin mechanics. This gate does not implement the four outputs.

---

## Organization isolation

Policies and snapshots are org-scoped. No cross-org pooling. `$65` and 15% GM remain ORG-001 policy text until an approved ORG-001 policy record is seeded **as org data**, not platform defaults.

---

## Human approval

Humans approve ORG-APPROVED policies, estimate overrides, and CO policy exceptions. LEARN/AI must not mutate approved policy (ADR-024).

---

## AI authority

**MAY:** explain, compare, flag variance, suggest candidates.

**MAY NOT:** silently change target margin, approve policy, alter direct cost evidence, hide margin, manipulate historical estimates, pool private economics, set ORG-APPROVED.

---

## Legacy compatibility

Do not recalculate locked/issued/accepted estimates. Do not mutate FG-006 historical facts. Do not change Labour Engine production math. New estimates after implementation follow resolved org policy.

---

## Migration expectations

**Not authorized until a separate implementation prompt.** That prompt may add additive tables (policy + snapshot) under Rule 7 review. Existing percent columns remain until an approved mapping. No casual Alembic in this governance pass.

---

## Test expectations (future implementation — do not implement now)

True GM math; markup math; margin-vs-markup distinction; zero/invalid margin fail-closed; organization isolation; policy versioning; policy resolution order; estimate snapshot immutability; contingency visibility **and** `INCLUDED_IN_MARGIN_BASIS` vs `ADDED_AFTER_BASE_PRICING`; tax ordering; Pricing Posture non-effect on quantities/hours/cost facts; Execution Risk non-effect on those facts; Change Order policy consistency; historical Change Order non-rewrite; legacy estimate compatibility (no silent recalc); Labour Engine boundary (consume cost only); historical-ingestion non-regression; proposal immutability; full-suite regression.

---

## Protected areas

- Historical source workbooks and `HistoricalLabourItem` facts  
- Accepted proposal snapshots  
- Plan Intelligence  
- Labour Engine production-rate / mapping / calibration lifecycle (except later consume Direct Labour Cost)  
- `$65` / 15% **policy text** as ORG-001 (may be **seeded** as org policy data when implementation is approved — not rewritten as CalibAi defaults)  
- Constitution Articles 1–12  

---

## Non-goals

Product implementation in this gate; AI take-off; supplier integrations; BUILD / MONITOR / LEARN automation; QuickBooks API; contract/warranty generation; field capture; payroll; cross-org learning; ML; new Labour Engine features; historical evidence repair; four-output product UI.

---

## Scope (implementation — only after a later execution prompt)

In-scope **after** a bounded implementation prompt (gate already approved):

- Organization-owned versioned pricing policies  
- Named methods `TRUE_GROSS_MARGIN`, `COST_PLUS_MARKUP`, `COST_PLUS_MARKUP_STACK`  
- Deterministic resolution + estimate pricing snapshot  
- Change Order inheritance of snapshot  
- Tests listed above  
- Docs updates for implemented state  

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Live code implements a compounding markup/overhead/profit stack that is not 15% true GM; Change Orders use a third formula; org policy cannot be versioned or snapshotted; Brayman economics risk becoming universal. |
| 2 | Who is the user? | Office estimators and a chief estimator / approver of organization pricing policy. Not field workers. |
| 3 | Which module owns it? | **Pricing Engine** (new). Estimating owns estimate lines and remains the calculation host. Proposals own customer snapshots. Project Controls own Change Order lifecycle but **must reuse** the pricing snapshot. |
| 4 | What data does it own? | `OrganizationPricingPolicy` (conceptual), `EstimatePricingSnapshot` (conceptual), resolution/audit of pricing application. |
| 5 | What data does it reference? | `Organization`, `ProjectCommercialContext`, `EstimateVersion`, line extended costs / Labour Engine direct labour cost, historical evidence (read-only). |
| 6 | What may implementation change? | Additive policy/snapshot schema (when migration approved), estimate/CO/proposal calculation **paths** to named methods, tests, docs. Must not rewrite locked totals. |
| 7 | What must implementation not change? | Historical workbooks/facts; Accepted proposal immutability rules; Plan Intelligence; Labour production math; cross-org data; silent conversion of 15% GM into 15% markup. |
| 8 | What are the acceptance criteria? | See below. |
| 9 | What tests are required? | See **Test expectations**. Dedicated suite plus historical ingestion + labour engine + full suite non-regression. |
| 10 | What documentation must be updated? | This gate; pricing architecture; ADR-025/030 status when accepted; pricing-policy.md; estimating/pricing-engine modules; current-state; session-handoff; roadmap; chat-workflow-log. |
| 11 | Does it require an ADR? | **Yes** — ADR-025 (methods) **Accepted**; ADR-030 (policy records, snapshots, contingency treatment, CO inheritance) **Accepted**. |
| 12 | Does it require a database migration? | **Yes, when implementation is authorized.** Additive. **Not** in this architecture pass. |

---

## Acceptance criteria (for a future implementation prompt)

1. Named methods are explicit; 15% GM ≠ 15% markup in tests.  
2. ORG-001 can use `TRUE_GROSS_MARGIN` without forcing other orgs to inherit it.  
3. Legacy versions remain `COST_PLUS_MARKUP_STACK` and are not silently recalculated.  
4. Estimate pricing snapshot is immutable for locked versions.  
5. FG-009-aware Change Orders inherit the linked snapshot unless an approved override exists. Historical Change Orders are not rewritten.  
6. Pricing Posture and Execution Risk never multiply hours/qty/supplier/direct labour facts.  
7. Tax is after pre-tax customer selling price; tax rate is org/jurisdiction.  
8. Contingency source/visibility/pricing treatment is explicit; `CUSTOMER_PRICED` is not assumed to sit outside the margin basis.  
9. Labour Engine boundary preserved.  
10. Historical ingestion tests still pass; full suite passes.  
11. Customer-facing paths do not expose internal margin mechanics (when those outputs exist).

---

## Blocking conditions

Architecture, Feature Gate, ADR-025, and ADR-030 are **approved** (2026-08-29).

Implementation remains **blocked** until a **separate** bounded Cursor execution prompt is issued.

This documentation/governance pass does **not** authorize product code, migration, or selling-price change.

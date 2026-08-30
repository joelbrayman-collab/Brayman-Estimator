# Organization-Calibrated Pricing Engine — Architecture / Readiness Report

| Attribute | Value |
|-----------|--------|
| Status | **Architecture approved** — **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Date | 2026-08-29 |
| Feature Gate | [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Related ADRs | [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** |
| Prerequisites | FG-007 / M011 **implemented**; FG-008 **implemented** (Labour Engine operational for UAT); FG-006 **implemented** (historical evidence only) |
| Product code | `app/models/pricing_engine.py`, `app/services/pricing_engine.py`, `app/routes/pricing_engine.py`, additive estimate/CO pointers, migration `a3b4c5d6e7f8`. Live selling-price path: snapshot if present, else legacy stack. |

---

## 1. Purpose

Define the durable architecture for an **Organization-Calibrated Pricing Engine**.

CalibAi owns the **engine and methodology** (how selling price is computed, snapshotted, explained, and kept consistent across outputs).

Each customer organization owns its **commercial intelligence** (target margin, markup rules, contingency treatment, tax jurisdiction, overhead/profit treatment, approval of policy versions).

**Brayman Construction is `ORG-001`.** Brayman commercial policy is not the universal CalibAi pricing model.

This document is **approved architecture**. Implementation is **CLOSED / OPERATIONAL FOR UAT**. FG-009 revision `a3b4c5d6e7f8` is in the live Alembic chain. Live development/UAT current/head is `b4c5d6e7f8a9`.

---

## 2. Governing commercial principle

| Layer | Owner |
|-------|--------|
| Pricing methodology (named methods, layer distinctions, snapshot rules, output consistency) | CalibAi |
| Pricing policy values and method selection | The organization (`ORG-001`, later other orgs) |
| Estimate/proposal commercial results | Immutable once issued/accepted (Constitution Article 5; ADR-002) |

`$65 CAD / man-hour` and **15% true gross margin** are **ORG-001** governed values in [pricing-policy.md](../pricing-policy.md). They must not become platform defaults.

---

## 3. Current-code audit (read-only)

Audited 2026-08-29 against `main` @ `ff5d856d52433832c8b3099cb5a17ba72fb73db3`. No product code was modified.

### 3.1 Estimate builder (authoritative live formula)

Code: `app/services/estimate_builder.py`.

```text
extended_cost = quantity × unit_cost × (1 + waste_percent / 100)
sell_price    = extended_cost × (1 + markup_percent / 100)

version.subtotal     = Σ line sell_price     # already marked-up sell, not direct cost
overhead_amount      = subtotal × overhead_percent / 100
profit_amount        = (subtotal + overhead_amount) × profit_percent / 100
taxable              = subtotal + overhead_amount + profit_amount
tax_amount           = taxable × tax_percent / 100
total                = taxable + tax_amount
```

| Finding | Evidence |
|---------|----------|
| Direct-cost-ish quantity | `extended_cost` includes **waste on unit cost before markup** |
| Line selling method | **Cost-plus markup**, not true gross margin |
| Version `subtotal` | Sum of **sell prices**, not sum of extended costs |
| Overhead | Applied to marked-up subtotal |
| Profit | **Compounds** on `(subtotal + overhead)` |
| Tax | Downstream of the pre-tax selling stack |
| Contingency | **No field** on `EstimateVersion` |
| Pricing Posture / Execution Risk | Stored on `ProjectCommercialContext`; **do not enter this math** |
| Labour Engine | `EstimateLabourSnapshot` is **not** wired into `sell_price` |
| New-version defaults | `overhead_percent`, `profit_percent`, `tax_percent` default **0** (`app/services/estimates.py`) |
| Line markup defaults | `CostItem.default_markup_percent` or `Assembly.default_markup_percent` |
| Line types | Cost Item, Assembly, Custom, Allowance — Allowance uses the **same** markup math |

`overhead_amount`, `profit_amount`, and `tax_amount` on `EstimateVersion` are **derived properties**, not stored columns (`app/models/estimate.py`).

### 3.2 Proposal snapshots

Code: `app/services/proposals.py`.

- Snapshot copies version percents and derived amounts.
- Waste is **baked into** snapshot `unit_cost` so later proposal recalc does not re-apply waste.
- Line `unit_price = unit_cost × (1 + markup_percent / 100)` — same cost-plus markup.
- Recalc uses the same overhead-then-profit compounding as the estimate builder.
- Accepted proposals remain immutable ([ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)).

Proposal snapshots **preserve results** for the current stack. They do **not** preserve a named policy type, target gross margin, or contingency treatment, because those concepts are not in the live schema.

### 3.3 Change Orders

Code: `app/project_controls/services.py`, `app/project_controls/routes.py`.

```text
item.total        = quantity × unit_price
change_order.subtotal = Σ item.total
markup            = subtotal × markup_percent / 100
tax               = (subtotal + markup) × tax_percent / 100
total             = subtotal + markup + tax
```

This is **not** the estimate’s overhead-then-profit compound stack.

When creating a Change Order from an estimate version, UI default `markup_percent` falls back to `version.overhead_percent` (not profit, not line markup, not true GM). Copied lines use `sell_price / quantity` as `unit_price` (already-sold unit), then apply **another** markup layer on that subtotal.

**Architectural defect to close in implementation:** base estimate and Change Orders can use inconsistent economics accidentally.

### 3.4 Historical ingestion (FG-006)

Separate evidence tables. Stores source markup/margin/contingency/tax as **facts**. Does **not** drive `estimate_builder`. Historical math must remain non-authoritative for live selling price.

### 3.5 What current code implements

| Question | Answer |
|----------|--------|
| True 15% gross margin (`Direct / 0.85`)? | **No** |
| Simple 15% markup (`Direct × 1.15`) as a single policy? | **Only if** line markup is 15% and overhead/profit/tax are 0 |
| Configurable named policy methods? | **No** |
| Actual behavior | Line cost-plus markup **plus** optional compounded overhead **plus** compounded profit **plus** tax |

---

## 4. Margin versus markup (must not collapse)

Let `D` = direct cost. Let `m` = rate as a decimal.

| Method | Formula | At 15% on $100 direct |
|--------|---------|------------------------|
| Cost-plus **markup** | `Sell = D × (1 + m)` | **$115.00** (implied GM = 13.043…) |
| True **gross margin** | `Sell = D / (1 − m)` | **$117.647…** (implied markup = 17.647…) |

These are not interchangeable. Labeling a 15% add-on as “margin” does not make it true gross margin.

Historical Brayman workbooks often **label** “15% Margin” while the arithmetic is **15% of direct cost added** (markup). Example: Julia Harish (`HIST-EST-0008`) — $85,152.40 + $12,772.86 = $97,925.26. That is cost-plus 15%, not `85152.40 / 0.85`.

**Governed ORG-001 policy** remains true gross margin (`Direct / 0.85`). Historical labels are evidence of past commercial decisions, not automatic ORG-APPROVED policy.

---

## 5. Recommended Direct Cost definition

**Direct Cost** is the sum of organization/project **direct inputs** that exist before commercial recovery (margin/markup, profit) and before tax — **except** where org policy explicitly places overhead or customer-priced contingency **into** the pricing basis.

Do **not** silently force overhead or contingency into or outside Direct Cost. That placement is **policy-defined**.

### May be Direct Cost (when present)

| Component | Treatment |
|-----------|-----------|
| Materials | Yes — supplier/unit cost |
| Material waste | Yes — waste on material (and similar) lines is a **quantity/cost fact**, applied before selling-price method |
| Direct labour | Yes — Labour Engine **direct labour cost** when wired; until then, `CostItem` category `Labour` lump `unit_cost` remains a valid legacy direct input |
| Subcontracts | Yes |
| Equipment | Yes |
| Direct project packages / other direct | Yes |
| Allowances that represent known/direct project cost | Yes (still labeled ALLOWANCE / TBD / PLACEHOLDER until resolved) |

### Never Direct Cost (not policy-selectable as cost facts)

| Component | Treatment |
|-----------|-----------|
| Gross margin / profit as recovery | Commercial layer — never a cost fact |
| Tax / HST | Downstream of pre-tax customer selling price |
| Pricing Posture | Strategy — never a hidden multiplier on Direct Cost |
| Execution Risk | Risk — never a silent falsification of Direct Cost evidence |

### Overhead (policy-defined; must remain explicit)

Overhead is **not** automatically Direct Cost and is **not** equivalent to gross margin.

| Method | Overhead treatment |
|--------|-------------------|
| `TRUE_GROSS_MARGIN` | Target GM governs selling-price math. Overhead must be configured explicitly, for example: treated as **direct/project cost**, **included in margin economics**, **separately customer priced**, or **not applied**. **Do not** re-run line-markup + compounding overhead/profit invisibly inside this method. |
| `COST_PLUS_MARKUP` | Simple one-rate markup on the configured basis. Overhead is explicit policy, not a hidden second percent. |
| `COST_PLUS_MARKUP_STACK` | Legacy method remains **explicit**: line markup, then overhead on sell-subtotal, then compounded profit. |

### Contingency — source/purpose vs pricing treatment

Do **not** define `CUSTOMER_PRICED` contingency universally as an addend always outside the margin basis.

Separate:

1. **Source / purpose** — why the reserve exists (org-defined; not a silent quantity/hour/cost multiplier).
2. **Customer visibility**
   - `UNSPECIFIED` — no additional layer has been selected yet (not a commercial decision)
   - `INTERNAL_RESERVE` — tracked internally; **not** customer priced
   - `CUSTOMER_PRICED` — included in the customer commercial amount
   - `NOT_APPLIED` — organization **approved** that the layer is not applied

`UNSPECIFIED` and `NOT_APPLIED` must not be collapsed. Absence of a decision is not an approved `NOT_APPLIED` policy. Base `TRUE_GROSS_MARGIN` still calculates when optional layers are unspecified.
3. **Pricing treatment** (required when `CUSTOMER_PRICED`)
   - `INCLUDED_IN_MARGIN_BASIS` — participates in the named method’s basis **before** GM or markup
   - `ADDED_AFTER_BASE_PRICING` — added **after** the named method computes base pre-tax selling price

**Invariant:** the system must know whether contingency **participates in the pricing formula**. No hidden assumption. Historical Harish (internal 5% off customer price) and Pratt (5% in pre-tax sell) are **evidence**, not universal policy. ORG-001 selects treatment through human-approved org policy.

Allowances remain direct-cost (or placeholder) lines, not a margin mechanism. Job-specific general-conditions packages are Direct Cost if they are true project costs. Historical “GC Work 12.5%” (Mike Pratt) is a **markup layer**, not proof that GC is always Direct Cost.

Change Orders are commercial adjustments to the customer price. They are not a second definition of Direct Cost. They must **reuse the snapshotted method** of the linked estimate (see §12).

---

## 6. Commercial layers (must remain distinct)

These must never silently collapse into one percentage:

| Layer | Meaning |
|-------|---------|
| DIRECT COST | Cost facts before commercial recovery |
| CONTINGENCY / RESERVE | Source/purpose **and** visibility **and** whether it is in the margin basis (policy; never one collapsed percent) |
| GROSS MARGIN | `(Sell − Direct) / Sell` — true GM method uses this as the target |
| MARKUP | `(Sell − Direct) / Direct` — cost-plus method uses this as the target |
| OVERHEAD | Recovery layer in the **legacy stack** method (on marked-up subtotal today) |
| PROFIT | Recovery layer in the **legacy stack** method (compounds after overhead today) |
| TAX | Jurisdiction tax on pre-tax selling price |
| ALLOWANCE | Explicit unresolved or stipulated direct amount |
| DISCOUNT | Commercial concession after (or as part of) selling policy — must be explicit |
| PRICING POSTURE | Commercial strategy (M011) |
| EXECUTION RISK | Delivery/risk classification (M011) |

---

## 7. Pricing-policy types (named methods)

The engine must support **organization-selectable named methods**. Formulas must not be mixed in one calculation.

| Method ID | Base formula (then apply snapshotted contingency/overhead treatment) | V1 |
|-----------|---------------------------------------------------------------------|----|
| `TRUE_GROSS_MARGIN` | `base_pre_tax = MarginBasis / (1 − target_gross_margin)` | **Required** |
| `COST_PLUS_MARKUP` | `base_pre_tax = MarkupBasis × (1 + markup_rate)` | **Required** (simple, one recovery rate) |
| `COST_PLUS_MARKUP_STACK` | Current live stack: per-line markup, then overhead on sell-subtotal, then profit on `(subtotal + overhead)` | **Required** as the **legacy/explicit** method |
| `TIERED` | Category-specific rates (historical Mike Pratt pattern) | **Architecture-ready; not required in first implementation** |

`MarginBasis` / `MarkupBasis` include Direct Cost plus any customer-priced contingency marked `INCLUDED_IN_MARGIN_BASIS`, and include overhead only when org policy says overhead is in that basis. Amounts marked `ADDED_AFTER_BASE_PRICING` are applied after the named method. Tax is applied after the resulting **pre-tax customer selling price**.

**ORG-001 intended operating method** (when FG-009 is implemented): `TRUE_GROSS_MARGIN` at 15%, per [pricing-policy.md](../pricing-policy.md).

**Do not:**

- Map 15% true GM onto existing `markup_percent = 15` fields.
- Silently replace the live stack for all organizations.
- Treat `overhead_percent + profit_percent` as equivalent to 15% GM.

Invalid `target_gross_margin` (`< 0` or `≥ 1`) must fail closed (no sale price). Zero margin is allowed only if the policy explicitly permits it (`sell = Direct Cost`).

---

## 8. Policy resolution (deterministic)

Reconciled with M011: `EstimateVersion.commercial_context_id` already **pins** commercial context. It does **not** currently select a pricing method or rates.

Recommended resolution order (first match wins):

1. **Approved estimate/version-specific pricing override** (human + reason + provenance).
2. **`ProjectCommercialContext` explicit policy selection** (optional pointer; **not in schema today** — additive later).
3. **Active ORG-APPROVED `OrganizationPricingPolicy`** for that organization.
4. **Organization default policy** pointer.
5. **CalibAi BASELINE / reference** — flagged generic; **never** silent Brayman economics; requires review.
6. **Provisional / manual** — continue the **current coded stack** (`COST_PLUS_MARKUP_STACK`) with an explicit review flag until a policy is approved.

Every resolution record must preserve: `organization_id`, policy id/version, method type, source (which step fired), effective date, reason, override reason (if any), provenance.

Changing a later org policy **must not** float old estimate versions.

---

## 9. Versioning and estimate pricing snapshot

Minimum durable architecture (conceptual — not implemented):

| Record | Role |
|--------|------|
| `OrganizationPricingPolicy` | Org-owned, versioned, supersedable; method type; rates; contingency source/visibility/pricing treatment; overhead/profit treatment; tax rule; approval status; effective dates; provenance |
| `EstimatePricingSnapshot` | Frozen copy of policy type/version, Direct Cost basis, GM or markup parameters, legacy stack parameters if applicable, contingency treatment, overhead/profit treatment, Pricing Posture, Execution Risk, tax, override reason, provenance |

Later changes to target margin, method, contingency, tax, overhead/profit treatment, or Pricing Posture **must not** recalculate Issued/Accepted/Rejected/Superseded versions.

Accepted **Proposal** snapshots remain immutable (ADR-002). Implementation must also snapshot **policy identity**, not only numeric percents, so a future engine cannot “re-interpret” 15% markup as 15% GM.

Locked estimate versions today store percents, not a named method. Migration (when authorized) must **classify existing versions as `COST_PLUS_MARKUP_STACK`** from stored fields — never rewrite totals.

---

## 10. Pricing Posture architecture

M011 stores Pricing Posture on `ProjectCommercialContext` (`Lean / Strategic`, `Competitive`, `Fair Market`, `Selective`, `Premium`). Premium requires a reason for ORG-001.

**Must not alter:** true material quantities, true labour hours, true production rates, supplier quote facts, direct labour cost facts, historical evidence.

Pricing Posture is **commercial strategy**. It is not a hidden multiplier.

| Potential later effect | Authorized in this architecture? |
|------------------------|----------------------------------|
| Record on estimate pricing snapshot | **Yes** (context) |
| Silent factor on hours/qty/cost | **Never** |
| Select among already-approved org policies / margin bands | **Possible later**, only with explicit org mapping tables — **not authorized as V1 product behavior** |
| Discount authority / approval thresholds | **Possible later** — same constraint |
| Change Direct Cost evidence | **Never** |

V1 Pricing Engine implementation (when gated) must **snapshot** posture and **must not** apply it as a number unless a later Feature Gate approves an explicit mapping.

---

## 11. Execution Risk architecture

Keep distinct from Pricing Posture. M011 values: `Low`, `Normal`, `Elevated`, `High`. High requires a reason for ORG-001.

**Must not silently falsify:** quantity, production rate, labour hours, supplier cost, direct cost evidence.

Recommended mechanisms (choose via **org policy**, not a hidden default):

- Inform **which contingency/reserve rule** applies (internal vs customer-priced vs none).
- Trigger **review** / raise **approval threshold**.
- Select a **governed reserve** from a versioned org table.

Not a silent hour or cost multiplier (FG-008 already forbids `execution_risk_factor` on labour).

---

## 12. Change Order policy recommendation

| Rule | Recommendation |
|------|----------------|
| Linked to an estimate version | **Inherit that version’s `EstimatePricingSnapshot`** (method + rates + tax + contingency treatment + overhead/profit treatment) |
| Override | Allowed only as a **separately approved** exception with reason and provenance |
| Unlinked CO | Resolve current project/org policy **or** require explicit method selection — never silently use `overhead_percent` as markup |
| Historical Change Orders | **Do not recalculate or rewrite.** Legacy COs remain historical facts |
| Formula | Must not invent a third economics accidentally |

Current CO math (`markup on already-sold copied lines`, defaulting markup from `overhead_percent`) is a **known inconsistency** for **legacy** Change Orders without a snapshot.

**Implementation (working tree):** FG-009-aware Change Orders attach the linked `EstimatePricingSnapshot` and **apply the snapshotted method** via `price_change_order_from_snapshot` (`app/services/pricing_engine.py`). Historical Change Orders without a snapshot keep the legacy formula and are not rewritten.

---

## 13. Tax architecture

Tax remains **downstream of pre-tax selling price** unless a future legal/org policy proves otherwise.

ORG-001 currently uses **Ontario HST 13%**. That is **organization/jurisdiction policy**, not a CalibAi universal default.

Do not implement tax-engine product changes in the architecture pass. When implemented, tax percent and jurisdiction must be on the org policy and frozen on the estimate snapshot.

---

## 14. Four-output consistency

One authoritative `EstimateVersion` + one `EstimatePricingSnapshot` must feed all four governed outputs ([project-document-package.md](project-document-package.md)):

1. Internal Detailed Cost Breakdown — may expose direct costs, hours, DLCR, contingency, margin, reconciliation.
2. Customer-Facing Estimate — **must not** expose internal direct costs, internal labour cost rates, or internal margin mechanics.
3. QuickBooks Estimate/Entry — customer-facing commercial amounts from the same snapshot (API remains Future).
4. Contract + Warranty — approved customer price from the same snapshot (Legal Content Gate; not this engine).

The Pricing Engine must not make these outputs inconsistent. This gate does **not** implement the outputs.

---

## 15. Labour Engine boundary

FG-008 produces: **man-hours**, **direct labour cost rate**, **direct labour cost**.

| Pricing Engine MAY | Pricing Engine MUST NOT |
|--------------------|-------------------------|
| Consume **Direct Labour Cost** as a Direct Cost input | Modify production rate, man-hours, or direct labour cost rate |
| Explain that labour entered Direct Cost | Apply Pricing Posture or Execution Risk to labour facts |

Labour overrides remain an **upstream** Labour Engine / human action, not a pricing-engine side effect.

---

## 16. Historical evidence (use as evidence only)

| Anchor | Pattern | Policy implication |
|--------|---------|-------------------|
| Allen Jacques | Cost-plus **15% markup** on direct; HST 13% after pre-tax sell | Historical cost-plus, not proof of true GM |
| Julia Harish | Labeled “15% Margin” but arithmetic is **15% of cost**; 5% contingency **internal, not in customer sell** | Labels ≠ method; contingency treatment is policy-selectable |
| Mike Pratt | Tiered 12.5% GC work + 5% contingency **included** in pre-tax sell | Supports `TIERED` as a future method; not ORG-001 default |

Do **not** convert historical behavior automatically into ORG-APPROVED policy.

---

## 17. Organization isolation, human approval, AI authority

**Isolation:** Pricing policies, snapshots, and rates are organization-scoped. No cross-org pooling of private economics. CalibAi BASELINE must not copy ORG-001 values into other orgs.

**Human approval:** ORG-APPROVED pricing policy, estimate-specific overrides, and Change Order policy exceptions require a human. AI cannot approve.

**AI MAY:** explain calculations; compare scenarios; identify margin variance; identify historical patterns; suggest **policy candidates**; flag inconsistent commercial treatment.

**AI MAY NOT:** silently change target margin; approve pricing policy; alter direct cost evidence; hide margin; manipulate historical estimates; pool private organization economics; set ORG-APPROVED policy.

---

## 18. Legacy compatibility

- Existing live estimates continue to mean `COST_PLUS_MARKUP_STACK` until an implementation prompt migrates **new** work to org policy.
- Locked / issued / accepted versions **must not** be recalculated.
- Historical ingestion tables remain evidence-only.
- Labour Engine snapshots remain independent until an explicit later wire-up consumes Direct Labour Cost.

---

## 19. Out of scope (this architecture / FG-009)

Product pricing implementation; ADR-025 code changes; AI take-off; supplier integrations; BUILD / MONITOR / LEARN automation; QuickBooks API; contract/warranty implementation; field capture; payroll; cross-org learning; ML training; new Labour Engine features; historical evidence repair; four-output product generation.

---

## 20. Readiness

| Layer | State |
|-------|--------|
| Architecture (this document) | **Approved** (2026-08-29) |
| FG-009 | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| ADR-025 | **Accepted** |
| ADR-030 | **Accepted** (contingency source vs pricing treatment explicit) |
| Product code | Implemented (FG-009 revision `a3b4c5d6e7f8` in Alembic chain; live graph head `b4c5d6e7f8a9`) |

**Next action:** FG-009 remains **CLOSED**. [FG-010](../feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) is **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. Do not reopen FG-009 from this architecture document.

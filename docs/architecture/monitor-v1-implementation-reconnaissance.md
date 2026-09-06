# MONITOR V1 — Implementation reconnaissance

| Attribute | Value |
|-----------|--------|
| Status | **RECONNAISSANCE COMPLETE.** [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **DRAFT FOR JOEL APPROVAL**. MONITOR V1 is **NOT IMPLEMENTED** and **NOT AUTHORIZED FOR CODE**. |
| Date | 2026-09-06 |
| Product | The Estimator / CalibAi |
| Canonical record | This document |
| Roadmap | Item 13 — MONITOR basic estimated-vs-actual |
| Related | [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (architecture/commercial baseline only; does **not** authorize a Feature Gate or implementation) · [CAR-001](CAR-001-calibai-product-architecture-reconciliation.md) · [modules/monitor.md](../modules/monitor.md) · [ADR-020](../adr/ADR-020-build-module-boundary.md) · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) · [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) · [FG-011](../feature-gates/FG-011-project-hub-ux.md) · [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) · [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) · [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) · [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) · [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) |

This reconnaissance freezes the smallest lawful MONITOR V1 implementation design.

```text
MONITOR V1:
RECONNAISSANCE COMPLETE
FEATURE GATE DRAFTED (FG-023)
NOT APPROVED
NOT AUTHORIZED FOR IMPLEMENTATION
NOT IMPLEMENTED
```

Accepting [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) does **not** authorize implementation. [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) is **DRAFT FOR JOEL APPROVAL** and does **not** authorize product code, schema, or migration. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

Readiness: **FEATURE GATE DRAFTED — AWAITING JOEL APPROVAL.**

**Subsequent status (2026-09-06):** FG-023 drafted. Office Direct Cost actuals are **in** the draft gate (BUILD `ProjectDirectCostActual`). No model or migration created.

---

## Landed inventory (do not change here)

No MONITOR product code exists. Project Hub labels MONITOR **Future**.

| Area | Path / evidence |
|------|-----------------|
| Hub label | `app/templates/projects/detail.html` — `MONITOR · Future`; `#hub-monitor` copy: not operational; no estimated-versus-actual |
| Hub assembly | `app/services/project_hub.py` — read-only PLAN / PRICE / CONTRACT / BUILD facts; **no** MONITOR comparison |
| Estimate / lines | `app/models/estimate.py` — `Estimate`, `EstimateVersion`, `EstimateSection`, `EstimateLineItem` (`extended_cost`, `sell_price`, `line_type` including `Allowance`) |
| Pricing snapshot | `app/models/pricing_engine.py` — `EstimatePricingSnapshot` (`direct_cost_basis`, `pre_tax_selling_price`, `tax_amount`, `customer_total`) |
| Labour snapshot | `app/models/labour_engine.py` — `EstimateLabourSnapshot` (**estimated**, not actual). **No** `LabourActualObservation` model |
| Proposal | `app/models/proposal.py` — `Proposal` (`subtotal`, `overhead_amount`, `profit_amount`, `tax_amount`, `total`; statuses include `Accepted`) |
| Change Orders | `app/project_controls/models.py` — `ChangeOrder` / `ChangeOrderItem` (sell-side `quantity × unit_price`; `subtotal`, `markup`, `tax`, `total`) |
| Field evidence | `app/models/build.py` — `FieldCaptureEvent`, `FieldCaptureOriginal`, `FieldCaptureDerivedCandidate` |
| Auth / org | FG-018 membership + FG-019 `/api/v1`; Hub is office HTML |
| Alembic live | current = head `d2e3f4a5b6c7` (FG-021). This recon creates **no** revision |

---

## ADR-021 exact contract

[ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) is **Accepted** as architecture/commercial baseline only.

### Governed term

**PROJECT GROSS MARGIN** is the initial authoritative project profitability metric.

It is **not** NET PROFIT. Net profit would require overhead allocation, payroll burden if outside Direct Cost, G&A, corporate expense, financing, depreciation, and other indirect costs. Those policies are **not governed**. Do **not** introduce NET PROFIT language in MONITOR V1.

ORG-001 optional overhead / profit / contingency treatments remain `UNSPECIFIED`. ADR-021 does not invent them.

### Comparison model

MONITOR compares **ESTIMATED ↔ ACTUAL ↔ FORECAST**.

- Approved estimates / commercial baselines remain **preserved**.
- **Actuals do not rewrite** the approved estimate, Accepted Proposal, or Change Order commercial records.
- **Forecasts** are dated/versioned snapshots, not silently overwritten values. ADR-021: **do not implement forecasting** under that ADR. MONITOR V1 **excludes** forecasts.

### Frozen composed estimated baseline (three layers; do not collapse)

**A. Original estimated commercial baseline**

- Locked `EstimateVersion` that is the source of the customer commitment.
- Authoritative `EstimatePricingSnapshot` **when present**: frozen estimated Direct Cost (`direct_cost_basis`), frozen pre-tax selling price (`pre_tax_selling_price`), frozen tax and customer total.
- When no snapshot exists (legacy `COST_PLUS_MARKUP_STACK`): estimated Direct Cost = Σ `EstimateLineItem.extended_cost`; estimated pre-tax selling price from the **Accepted Proposal**, not a later draft. Do **not** backfill a snapshot.

**B. Customer commitment**

- **Accepted Proposal** (ADR-002) is the immutable customer commercial commitment.
- Tied to its source `EstimateVersion`.
- Must **not** be mutated when a Change Order occurs.

**C. Post-commit commercial amendments**

- **Approved Change Orders** are auditable sell-side deltas **after** the Accepted Proposal.
- Remain separate records. Do not rewrite original baseline or Accepted Proposal.

### Floating-draft prohibition

Must **not** use as committed baseline: current Draft `EstimateVersion`; later revised draft estimate; Draft Proposal; manually restacked Draft Proposal totals.

### Conceptual identities (governance; not implemented)

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

### Taxes

Tax remains **outside** gross-margin arithmetic. Use **pre-tax** values. Do not use tax-collected amounts as revenue or margin.

### Allowances

ADR-021 does not create a separate allowance-draw actual. FG-009 treats allowances that are true/placeholder project costs as Direct Cost inputs to estimated `direct_cost_basis` / `extended_cost`. MONITOR V1 does **not** invent allowance-draw actuals. Allowance lines stay inside estimated Direct Cost when they already are.

### Overhead / profit

Optional overhead/profit/contingency remain `UNSPECIFIED` policy treatments. They are **not** Actual Direct Cost. They are **not** NET PROFIT. Named-method snapshots already fold selling-price method into `pre_tax_selling_price`; MONITOR reads that frozen amount rather than restacking live overhead/profit percents.

### Actual Direct Cost

Future governed sum of **verified ORG-ACTUAL** direct-cost evidence. **Not implemented.** Potential later classes: labour, materials, subcontract, equipment, other approved direct-cost. Corporate overhead / G&A are **not** Direct Cost. Payroll-burden policy is **not** defined.

QuickBooks is **not** required. Current QuickBooks architecture remains customer-estimate **export** only.

### Actuals may not rewrite approved/frozen records

Actuals do not rewrite approved estimate, Accepted Proposal, or Change Orders. MONITOR must not silently rewrite BUILD field evidence.

### QuickBooks

Not a mandatory actuals source. MONITOR must **not** wait on QuickBooks.

### Phase D

Independent. MONITOR must **not** wait on take-off → estimate mapping. Phase D remains **NOT STARTED / NOT AUTHORIZED**.

### BUILD

Field actuals owned by **BUILD** when implemented (ADR-020). MONITOR compares. MONITOR does **not** become the actuals system of record.

### LEARN

MONITOR observes and compares. LEARN may later create review-gated calibration candidates. Neither may silently rewrite pricing/labour standards, historical evidence, accepted proposals, or estimates. ADR-024’s earlier “BUILD/MONITOR” actuals note is **refined**: BUILD owns field-execution capture; MONITOR compares.

### Change Order limitations (do not add schema to invent them)

- CO items are **sell-side** (`quantity × unit_price`). CO total is **not** actual cost and **not** a stored estimated Direct Cost delta.
- `Invoiced` is a lifecycle label, **not** books revenue. Do not drop an authorized CO from authorized-revenue solely because status later became `Invoiced`.
- No governed customer-credit instrument. Negative prices are not a credit policy.
- Do **not** reinterpret `unit_price` as cost. Current Authorized Estimated Cost **cannot** include a CO cost delta until later governance adds that evidence.

### Labour comparability (documented, not corrected)

`EstimateLabourSnapshot` is estimated, not actual. Estimated GM uses Direct Cost that **excludes** Labour Engine snapshot cost by default (FG-009 / FG-012: Direct Cost = Σ `extended_cost`). Actual GM would include verified actual labour when captured. Estimated vs actual GM is **not** labour-apples-to-apples until a later Feature Gate. MONITOR V1 must **not** invent that correction.

### MONITOR ownership

Project-centered **comparison / read layer** on the existing `Project` hub (ADR-019 / FG-011). May later persist dated comparison snapshots and dated forecast snapshots that it owns as comparison artifacts. Those must not mutate source records. V1 recommendation: **no MONITOR-owned snapshot table** (live projection).

---

## MONITOR V1 commercial question

Smallest useful V1 comparison, consistent with ADR-021:

```text
ORIGINAL BASELINE
+ APPROVED CHANGE ORDER REVENUE DELTAS
= CURRENT AUTHORIZED PRE-TAX REVENUE

ORIGINAL ESTIMATED DIRECT COST
(+ CO estimated cost delta only if such evidence exists — it does not today)
= CURRENT AUTHORIZED ESTIMATED COST

versus

ACTUAL DIRECT COST TO DATE  (missing until office actuals exist)

→ VARIANCE where both sides exist
→ PROJECT GROSS MARGIN (estimated from original snapshot pair;
   actual-to-date only when Actual Direct Cost exists)
```

This is **not** “collapse original + COs into one mutated live budget.” Layers remain visible.

Grain for V1: **project total**, with optional **Direct Cost class** rollup (`labour` / `material` / `subcontract` / `other_direct`) once office actuals exist. Not cost code. Not estimate line. Not Field Event. Prefer existing-before-new.

Forecast-final GM is **out of V1**.

---

## Current approved baseline composition

| Layer | V1 source | Notes |
|-------|-----------|--------|
| Original estimated Direct Cost | `EstimatePricingSnapshot.direct_cost_basis` when present on the locked source version; else Σ locked-version `EstimateLineItem.extended_cost` | Do not use Draft versions. Do not add `EstimateLabourSnapshot.direct_labour_cost`. |
| Original authorized pre-tax revenue | Snapshot `pre_tax_selling_price` when the Accepted Proposal’s source version has a snapshot; else Accepted Proposal `subtotal + overhead_amount + profit_amount` | Exclude `tax_amount` / `total`. |
| Approved CO pre-tax revenue delta | Sum of authorized COs: `subtotal + markup` | Authorized set: status `Approved` **or** `Invoiced` (ADR-021). Exclude `tax`. Draft / Pending / Rejected / Cancelled excluded. |
| Credits | None | No governed credit instrument. |
| Current authorized estimated cost | **Equals original estimated Direct Cost** in V1 | CO estimated-cost delta does **not** exist. Do not invent it from `unit_price`. UI must say so. |
| Current authorized pre-tax revenue | Original authorized pre-tax revenue + authorized CO pre-tax revenue deltas | This is Final Authorized Revenue for Actual GM. |
| Estimated GM | `1 − (Original Estimated Direct Cost / Original Estimated Pre-Tax Selling Price)` | Do **not** recompute estimated GM against inflated CO-inclusive revenue (that would fake margin improvement). Keep estimated GM on the original snapshot pair. |
| Actual GM | `1 − (Actual Direct Cost to date / Current Authorized Pre-Tax Revenue)` | Only when actuals exist. Incomplete otherwise. |

Incomplete-state warnings (required, not silent zeros):

- No Accepted Proposal → missing customer commitment; do not invent revenue.
- No locked source version / no snapshot and no Accepted Proposal → missing original baseline.
- No actuals → **MISSING ACTUALS**; do not claim Actual GM.
- Draft-only estimate → not a committed baseline.

---

## Existing baseline records

| Record | Model / table / service | Owner | Frozen / mutable | Grain | Amount fields | Project relationship | MONITOR V1 suitability |
|--------|-------------------------|-------|------------------|-------|---------------|----------------------|------------------------|
| Estimate | `Estimate` / `estimates` | Estimating | Mutable header; versions lock | Project | none (via version) | `project_id` | Pointer only |
| Estimate version | `EstimateVersion` / `estimate_versions` | Estimating | Locked when Issued/Accepted/Rejected/Superseded | Version | `subtotal`, percents, `total` | via Estimate | Use **locked source** version only |
| Line item | `EstimateLineItem` | Estimating | Frozen with locked version | Line | `extended_cost`, `sell_price`; `line_type` incl. Allowance | via section → version | Fallback DC Σ; not V1 UI grain |
| Pricing snapshot | `EstimatePricingSnapshot` / `estimate_pricing_snapshots` | Pricing Engine | Immutable once written | Version (1:1) | `direct_cost_basis`, `pre_tax_selling_price`, `tax_amount`, `customer_total`, method/provenance | via version → estimate → project | **Preferred** original DC + pre-tax revenue |
| Labour snapshot | `EstimateLabourSnapshot` | Labour Engine | Immutable | Task × version | `direct_labour_cost`, hours | via version | **Estimated only.** Not actual. Not in selling-price basis by default. Do not use as Actual Direct Cost |
| Proposal | `Proposal` / `proposals` | Proposals | Accepted is immutable (ADR-002) | Proposal | `subtotal`, `overhead_amount`, `profit_amount`, `tax_amount`, `total` | via `estimate_id` | **Accepted** row is customer-commitment layer |
| Brand snapshot | `ProposalBrandSnapshot` | Brand / Proposals | Frozen at issue | Proposal | none financial | via proposal | Not MONITOR |
| Change Order | `ChangeOrder` / `change_orders` | Project Controls | Mutable until approved; then commercial record | Project | `subtotal`, `markup`, `tax`, `total` | `project_id` | **Sell-side revenue delta only** |
| CO item | `ChangeOrderItem` | Project Controls | with CO | Line | `quantity`, `unit_price`, `total` | via CO | Not cost. Not V1 grain |
| Pricing policy | `OrganizationPricingPolicy` | Pricing Engine | Versioned org standard | Org | rates/methods | not project | Do not live-restack; read snapshot |
| Project Hub facts | `assemble_project_hub` | Projects UX | Projection | Project | presence flags | project | Host surface; not amounts today |
| Commercial context | `ProjectCommercialContext` | Projects | Versioned | Project | qualitative params | project | Not dollar actuals |
| Historical estimates | FG-006 evidence models | Historical ingestion | Evidence | Org historical | ingested costs | not this Project’s actuals | **NOT SUITABLE** as this-project actuals |

Do **not** create a second commercial source of truth. MONITOR **reads** these.

---

## Existing “actual” records

| Candidate | Classification | Why |
|-----------|----------------|-----|
| Field Capture Event / Original / Derived Candidate | **EVIDENCE ONLY** | FG-020 / ADR-042: Project Field Observation. Confirm/reject does not write estimates, proposals, COs, permits, take-off, or MONITOR. Voice/text must not become labour-cost actuals or `LabourActualObservation`. |
| `EstimateLabourSnapshot` | **PLANNED/ESTIMATED** | FG-008 estimated labour evidence |
| Estimate / pricing snapshot / proposal / CO | **PLANNED/ESTIMATED** (CO = sell-side amendment) | Not incurred cost |
| CO `Invoiced` status | **NOT SUITABLE** as actual cost or books revenue | Lifecycle label only |
| Material Catalogue / CostItem | **PLANNED/ESTIMATED** catalog | No usage actual |
| Historical ingestion rows | **NOT SUITABLE** | Other-job evidence; not this Project’s ORG-ACTUAL |
| QuickBooks | **NOT SUITABLE** | Export-only architecture; no API |
| Invoices / bills / POs / time entries / payroll / subcontract actuals / material usage / job-cost ledger | **NOT PRESENT** | No models |
| `LabourActualObservation` | **NOT PRESENT** | Architecture-only name in ADR-021 |

### Are Field Events / Field Observations MONITOR actual-cost inputs?

**No.** They are **EVIDENCE ONLY**. They are not Actual Direct Cost, not Actual Progress for GM, and not a lawful substitute for verified ORG-ACTUAL commercial actuals. Do not convert field evidence into financial actuals merely because it exists.

Progress (percent complete / earned value) is also **not** in Field Events. V1 does not invent schedule progress.

---

## Actuals gap

MONITOR cannot compute Actual Gross Margin from existing records. The gap is **authoritative Actual Direct Cost**.

Smallest pre-QuickBooks V1 actuals capability:

| Item | Freeze |
|------|--------|
| Kind | Office-entered **incurred Direct Cost** observations |
| Owner | **BUILD** (ADR-021: field/actuals SoR is not MONITOR). Distinct from Field Capture Events |
| Source | **Manual office entry.** Not derived from Field Observations. Not imported. Not QuickBooks |
| Classes | `labour`, `material`, `subcontract`, `other_direct` |
| Out of V1 classes | Separate equipment class; allowance draw; payroll burden; committed-but-not-incurred (PO) |
| Grain | Project + class + incremental amount + incurred date |
| UI | Project Hub MONITOR section (office). No Field Web actuals UI |
| If Joel declines actuals in V1 | MONITOR V1 would be **baseline composition + MISSING ACTUALS only** and **must not** claim Actual GM. That would not fully satisfy roadmap “estimated-vs-actual.” **Recommended: include office actuals in the same Feature Gate.** |

This recon does **not** authorize that schema or a Feature Gate.

---

## Recommended MONITOR-owned records

**V1: none.** Live projection in a MONITOR read service (intended `app/services/monitor.py`) consumed by Project Hub.

Dated MONITOR comparison snapshots: **deferred** (ADR-021 permits them when gated; not required for smallest V1).

Dated forecast snapshots: **out of V1**.

---

## Ownership / mutability

| Concept | Owner | Durable vs projection | Mutability | Correction | Provenance | Audit | Deletion | Relation to approved records |
|---------|-------|----------------------|------------|------------|------------|-------|----------|------------------------------|
| Composed baseline | Estimating / Proposals / Project Controls / Pricing | Projection | Read-only | N/A | Cite source ids + statuses | Read existing | N/A | Must not rewrite |
| Estimated / Actual GM, variance | MONITOR comparison layer | Projection | Recalculated | N/A | Formula + source pins | Log reads not required in V1 | N/A | Must not rewrite |
| Direct Cost actual | **BUILD** | **New durable** (if FG includes actuals) | Append-only + supersession | Superseding successor row | Actor, org, project, class, amount, incurred_on, note, `OFFICE_MANUAL` | Actor + timestamps | **Not allowed** | Must not write estimate/proposal/CO/Field Event |
| Field Event | BUILD | Existing durable | Append-only + supersession | Existing FG-020 | Existing | Existing | Not this gate (Observation Delete queued separately) | Unchanged |
| Comparison snapshot | MONITOR | Deferred | — | — | — | — | — | — |

---

## Correction / audit semantics

Follow existing CalibAi Field Event pattern. Do **not** invent a general ledger.

- **No in-place editable amount** on a posted actual.
- Correction = new row with `supersedes_id` pointing at the mistaken row (unique `supersedes_id`, same as `FieldCaptureEvent`).
- Successor restates that observation (replacement amount / class / date / note). Prior row remains visible as superseded.
- Reversal of a mistaken incremental amount = superseding successor with replacement amount (including `0.00` if the observation should not count). Do not delete.
- Provenance: `organization_id`, `project_id`, `user_id` (nullable), `actor_display_name`, `created_at`, `source='OFFICE_MANUAL'`.
- Hub lists current (not-superseded) observations and class totals.

---

## Schema requirement

**Baseline comparison:** no new schema. Projection over existing records.

**Actual Direct Cost (recommended in V1 Feature Gate):** new BUILD-owned durable table. **Do not create it in this pass.**

### Proposed model (design freeze only)

**Name:** `ProjectDirectCostActual`  
**Table:** `project_direct_cost_actuals`

| Field | Type | Notes |
|-------|------|--------|
| `id` | Integer PK | |
| `organization_id` | `String(50)` FK `organizations.id` ON DELETE RESTRICT | required, indexed |
| `project_id` | Integer FK `projects.id` ON DELETE RESTRICT | required, indexed |
| `user_id` | Integer FK `users.id` ON DELETE SET NULL | nullable |
| `actor_display_name` | `String(150)` | required |
| `cost_class` | `String(40)` | `labour` \| `material` \| `subcontract` \| `other_direct` |
| `amount` | `Numeric(14, 2)` | pre-tax Direct Cost; `>= 0` |
| `incurred_on` | Date | required |
| `note` | Text | nullable |
| `source` | `String(40)` | V1: `OFFICE_MANUAL` only |
| `supersedes_id` | Integer FK self ON DELETE RESTRICT | nullable; **UNIQUE** |
| `created_at` | DateTime | required, default utcnow |
| `provenance` | Text | nullable; optional structured note |

**Relationships:** Organization, Project, User, self-supersession.

**Constraints / indexes:**

- `UNIQUE (supersedes_id)` name `uq_project_direct_cost_actuals_supersedes_id` (NULLs allowed; multiple current rows lawful)
- Index `(organization_id, project_id)`
- Org + project scoping: row `organization_id` must match `Project.organization_id` (enforce in service, same pattern as Field Events)

**Actual Direct Cost to date** = sum of `amount` on current (not-superseded) rows for that org+project.

**Migration requirement:** **Yes, if and only if** the later Feature Gate includes office actuals. Additive Alembic only, after explicit prompt approval (Rule 7). **No migration in this pass.**

If the Feature Gate is baseline-only, **no** migration.

---

## Project Gross Margin formula

Tax outside GM. Pre-tax only.

```text
Estimated Gross Margin
  = 1 − (Original Estimated Direct Cost / Original Estimated Pre-Tax Selling Price)

Actual-to-date Gross Margin
  = 1 − (Actual Direct Cost to date / Current Authorized Pre-Tax Revenue)

Gross Margin Variance
  = Actual-to-date Gross Margin − Estimated Gross Margin
```

Display as percentage points when both exist. Do not compute Actual GM when actuals are missing. Do not compute Estimated GM when original DC or original pre-tax selling price is missing.

**Actual-to-date vs forecast-final:** ADR-021 Actual GM uses Final Authorized Pre-Tax Revenue (current authorized commitment), not a forecast remaining-cost. V1 is **actual-to-date GM** against **current authorized revenue**. It is **not** forecast final GM (no cost-to-complete, no forecast snapshot). Remaining-work forecast is out of V1.

### HST / allowances / CO / overhead

| Topic | V1 treatment |
|-------|----------------|
| HST / tax | Outside GM. Do not use `tax_amount`, CO `tax`, or `customer_total` / CO `total` as revenue |
| Allowances | Remain inside estimated DC when already in snapshot / `extended_cost`. No V1 allowance-draw actual class |
| Change Orders | Pre-tax **revenue** delta only (`subtotal + markup`). Not actual cost. Not estimated cost delta |
| Overhead / profit / G&A | Not Direct Cost. Not NET PROFIT. Do not subtract them from Actual GM |
| Committed vs incurred | V1 = **incurred** office-asserted amounts only. No PO/commitment layer |
| Forecast-to-complete | **Out of V1** |

---

## Recommended MONITOR V1 UI

**Office Project Hub** section `#hub-monitor` on `/projects/<id>` (FG-011: evolve the hub; no new module chrome).

**Not** a dedicated `/monitor` app. **Not** Field Web.

V1 presentation:

1. Original estimated Direct Cost
2. Original authorized pre-tax revenue
3. Approved CO pre-tax revenue delta (count of authorized COs)
4. Current authorized pre-tax revenue
5. Current authorized estimated cost (= original DC) + explicit “CO cost delta not stored”
6. Estimated Project Gross Margin (or missing-baseline warning)
7. Actual Direct Cost to date by class + total (or **MISSING ACTUALS**)
8. Actual-to-date Project Gross Margin (only if actuals exist)
9. Variance (only if both GM figures exist)
10. Provenance: source estimate version id, snapshot id, accepted proposal id, CO ids, last actual `created_at`
11. Office form: add Direct Cost actual (class, amount, incurred date, note) if FG includes actuals
12. List current actuals with supersede action (office)

No category traffic-light “health” invented beyond missing-data warnings. No NET PROFIT label. No industry benchmarks.

---

## Project Hub relationship

Projects owns Hub UX. MONITOR comparison is a **read assembly** Hub consumes, analogous to `assemble_project_hub` BUILD/PLAN panels. Actual-entry POST is BUILD-owned service, Hub-routed, not a MONITOR write of commercial baselines.

Hub lifecycle chip `MONITOR · Future` becomes operational only after a closed Feature Gate. This recon does **not** change the template.

---

## Auth / org boundary

Reuse FG-018 / FG-019 / Hub rules:

- Login required (office HTML 302 `/login`)
- Membership-derived org context
- Project must belong to current org (cross-org **404**, not 403 leakage)
- Actor display from session user, same as Field Events
- CSRF on mutating actuals POST
- No new auth architecture
- No session revocation
- **No RBAC expansion.** Any org member who can open the Hub may view MONITOR and enter office actuals in V1 (same as other Hub office writes). If later policy needs estimator-only vs bookkeeper, that is a **separate** auth Feature Gate — do not invent RBAC here.

MONITOR V1 can exist safely under current membership isolation.

---

## Test plan (future; do not run as MONITOR tests in this pass)

Last governed product-changing baseline remains dedicated FG-021 **20** / focused **148** / full **558**. This recon does **not** rerun pytest.

Future Feature Gate tests should cover:

- Unit/service: baseline composition; floating-draft rejection; CO `Approved`+`Invoiced` included; Draft CO excluded; tax excluded; no CO cost invention
- Actual sum of current rows; superseded excluded; `amount >= 0`; class enum
- Org isolation: cross-org project 404; no leak of actuals
- Route auth: anonymous redirect/401 as Hub pattern; CSRF on POST
- Hub UI: Future label gone only when implemented; missing-actuals copy; no “NET PROFIT”
- Baseline immutability: posting actuals does not change estimate/proposal/CO/Field Event rows
- PGM identities; incomplete-state (no Accepted Proposal; no actuals)
- Correction: supersede replaces observation; unique `supersedes_id`
- Field Events remain non-inputs to Actual Direct Cost

---

## Office UAT plan (future; do not perform)

Office-only (not iPhone Field Web):

1. Project with locked version + pricing snapshot + Accepted Proposal + one Approved CO: Hub shows three layers and estimated GM; MISSING ACTUALS; no Actual GM.
2. Enter labour and material actuals: totals and Actual GM appear; variance vs estimated GM.
3. Supersede a mistaken actual: old row retained; totals use successor.
4. Second org cannot see the project/actuals.
5. Confirm estimate, Accepted Proposal, CO, and Field Event rows unchanged.
6. Confirm HST not in GM; CO tax not in revenue; UI never says NET PROFIT.
7. Project with Draft estimate only: committed baseline missing, not a fake number.

---

## Explicit non-goals

MONITOR V1 must **not** absorb:

- LEARN / machine learning / recommendations
- QuickBooks API
- Phase D / external AI
- Observation Delete
- Project Closeout
- Native Signing
- Ontario contract/warranty
- Supplier live pricing
- Session revocation / idle timeout
- PWA / native iOS
- Transcription
- NET PROFIT
- Payroll / burden policy
- Full accounting / general ledger / AR / AP
- Field Web MONITOR UI
- Forecast / cost-to-complete / earned value
- Industry benchmarks as profitability inputs
- CO estimated-cost schema
- Credit/reduction instrument
- `LabourActualObservation` (labour-grain actuals remain later)
- Converting Field Observations into cost
- Rewriting approved estimate / proposal / CO / BUILD evidence
- New RBAC / org-switcher
- Dashboard org-unscoped counts

---

## What a future Feature Gate would need to authorize

Not created in this pass. A bounded MONITOR V1 gate would need the twelve governance answers covering, at minimum:

1. Hub MONITOR comparison projection (read-only over existing commercial records)
2. Whether BUILD office `ProjectDirectCostActual` is in the same gate (recommended **yes**)
3. Additive migration **only if** (2) is yes
4. Office actual entry + supersession on Hub
5. PGM identities exactly as ADR-021
6. Explicit non-goals above
7. No Field Web MONITOR surface
8. Org/auth reuse; no RBAC

---

## Unresolved decisions

The 2026-09-06 recon listed four Joel freezes. [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **drafts** them as:

1. Office Direct Cost actuals **in V1** (same gate).
2. **Incremental** observations + supersession.
3. **No** MONITOR-owned comparison snapshot table in V1.
4. Any org member who can use Hub may enter actuals (**no RBAC**).

Those remain **not approved** until Joel approves FG-023. Labour-apples-to-apples GM remains a documented later issue (ADR-021 §9).

---

## Feature-gate readiness

**FEATURE GATE DRAFTED (FG-023) — AWAITING JOEL APPROVAL.**

Do **not** treat the draft as authorization.

---

## Current-authority repairs recorded in the same docs pass

See the MONITOR V1 recon commit. Three CURRENT-looking stale pins were repaired without rewriting historical snapshots and without authorizing MONITOR code:

1. `docs/platform-roadmap.md` subsection “Current (near-term product governance)” — FG-018-era Alembic/test/gate facts replaced with live current authority.
2. `docs/architecture/fg-021-recent-observation-delete-requirement-capture.md` — header/priority no longer states FG-021 OPEN or photo-put re-UAT as current priority.
3. `docs/modules/README.md` — Labour Engine / Material Catalogue “live head today” pins updated from `a9b0c1d2e3f4` to `d2e3f4a5b6c7`.

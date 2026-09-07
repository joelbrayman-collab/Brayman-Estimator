# Feature Gate FG-023: MONITOR V1 — Estimated versus Actual

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-023` |
| Feature Name | MONITOR V1 — Estimated versus Actual |
| Target Milestone | **None.** FG-023 is the governing identifier. Do not assign a new M0xx number. Roadmap Item 13. |
| Module | **MONITOR** owns the comparison / read projection. **BUILD** owns office Direct Cost actuals (`ProjectDirectCostActual`). **Projects** owns Hub UX at `/projects/<id>`. Estimating, Pricing Engine, Proposals, and Project Controls retain their commercial records. |
| Date | 2026-09-06 |
| Status | **APPROVED / OPEN.** Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED.** Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS.** Hub `#hub-monitor` **LIVE / OFFICE-UAT-VERIFIED.** Gate **NOT CLOSED.** |
| Architecture | [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** · [monitor-v1-implementation-reconnaissance.md](../architecture/monitor-v1-implementation-reconnaissance.md) **COMPLETE** · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** · [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted** · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [modules/monitor.md](../modules/monitor.md) · [FG-011](FG-011-project-hub-ux.md) |
| Related ADRs | [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (commercial baseline; this gate does **not** create a new ADR) · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | Item 12 / [FG-021](FG-021-field-web-v1-today-and-capture.md) **CLOSED** (SESSION-EXPIRY RECOVERY **DEFERRED / NOT YET EXERCISED**). [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) / [FG-019](FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-008](FG-008-labour-engine-phase-b.md) / [FG-009](FG-009-organization-calibrated-pricing-engine.md) / [FG-012](FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. MONITOR V1 recon **COMPLETE**. |
| Approved baseline | Live Alembic current = head **`d2e3f4a5b6c7`**. Dedicated FG-021 **20**. Focused **148**. Full suite **558**. Live **39** Events / **39** Originals. Recon parent `1285ecfe0366e7a946323fbac83a1a829e940cb8`. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **APPROVED / OPEN** (2026-09-06). **NOT CLOSED.** |
| Implementation | **SLICE A IMPLEMENTED / LIVE-MIGRATED.** **SLICE B IMPLEMENTED / LIVE-MIGRATED.** Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS.** Gate **NOT CLOSED.** |
| Schema / Alembic | Revision **`e3f4a5b6c7d8`** (`down_revision = d2e3f4a5b6c7`) **APPLIED LIVE** 2026-09-07 (`d2e3f4a5b6c7` → `e3f4a5b6c7d8`). Live current = heads = **`e3f4a5b6c7d8`**. One graph head. |
| New ADR | **None.** ADR-021 already accepted. |
| MONITOR product code | Slice A service `app/services/monitor.py` `assemble_monitor_v1`. Hub `#hub-monitor` **live / office-UAT-verified**. **No MONITOR snapshot table.** **NOT YET CLOSED.** |
| Office actuals | BUILD model `ProjectDirectCostActual` + `app/services/direct_cost_actuals.py`. BUILD POST create/supersede. Live UAT rows **only** on synthetic project **id 13** `FG023-UAT-MONITOR` (five rows; authorized create + supersession sequence). |
| Field Web MONITOR UI | **Out of scope** |

```text
FG-023:
APPROVED
OPEN
NOT CLOSED
SLICE A: IMPLEMENTED / LIVE-MIGRATED
SLICE B: IMPLEMENTED / LIVE-MIGRATED
SLICE C: MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS
MONITOR V1: IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / NOT YET CLOSED
```

Joel/ChatGPT approved this gate **as written** on **2026-09-06**. Approval includes the correction semantics (`amount >= 0` so a superseding successor may carry `0.00` while the original durable entry remains). Slice A product code was authorized by a later 6 Sep 2026 implementation prompt. Slice B Hub UI was authorized 7 Sep 2026. Slice C live migrate + office UAT was authorized and **PASSED** 7 Sep 2026. **MONITOR V1 is live-migrated and office-UAT-verified. The gate is not closed.** Closure requires a separate ChatGPT authorization. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

### Slice C live migrate + office UAT (2026-09-07)

| Item | Result |
|------|--------|
| Live `flask db upgrade e3f4a5b6c7d8` | **PASS** (`d2e3f4a5b6c7` → `e3f4a5b6c7d8`) |
| Gitignored backup | `instance/brayman_estimator-backup-before-fg023-e3f4a5b6c7d8.db` (`cmp` identical; not committed) |
| Alembic after migrate | current = heads = `e3f4a5b6c7d8`; one graph head |
| Field continuity | **39** Events / **39** Originals |
| UAT project | **id 13** `FG023-UAT-MONITOR` / ORG-001 / client id **8** |
| Estimate / version / snapshot | Estimate **8** `EST-FG023-UAT-MONITOR`; version **8** locked; snapshot **5** `TRUE_GROSS_MARGIN` DC **850.00** / pre-tax selling **1000.00** / tax **130.00** (excluded) |
| Accepted Proposal | **id 5** `PROP-FG023-UAT-MONITOR` (exactly one Accepted) |
| Approved CO | **id 4** `CO-000004` subtotal **100.00** + markup **20.00** = **120.00** (tax 15.60 excluded) |
| Pending CO | **id 5** `CO-000005` subtotal **50.00** + markup **5.00** — **excluded** |
| Rejected CO | **id 6** `CO-000006` subtotal **40.00** + markup **0.00** — **excluded** |
| Hub baseline physical UAT | **PASS** (port **5014**; `#hub-monitor`; MISSING ACTUALS not shown as $0.00; no Inf/NaN/NET PROFIT) |
| Four-class create physical UAT | **PASS** labour **100.00** / material **50.00** / subcontract **25.00** / other_direct **10.00**; to-date **185.00**; actor **Joel Brayman**; source **OFFICE_MANUAL** |
| Supersession / 0.00 physical UAT | **PASS** actual **4** SUPERSEDED preserved; successor **5** ACTIVE **0.00**; to-date **175.00**; other_direct class **0.00**; no DELETE |
| Independent arithmetic | Original GM **15.00%**; authorized revenue **1120.00**; after supersession Actual-to-Date GM **84.38%**; variance **69.38%** — Hub agrees |
| Fail-closed HTTP | **AUTOMATED COVERAGE SUFFICIENT FOR V1** (not physical UAT) |
| Protected projects 1, 2, 9, 11, 12 | **zero** FG-023 UAT actuals |
| Tests this pass | **Not rerun.** Historical dedicated **35** / focused **149** / Slice A focused **126** / pre-Slice-B focused **137** / full **593** |

---

## Purpose

Give office estimators a Project Hub comparison of **frozen composed estimated baseline** versus **office-entered Actual Direct Cost to date**, and compute **Project Gross Margin** only where the identities are complete.

This is the smallest useful Item 13 (estimated-vs-actual). It does **not** wait on QuickBooks or Phase D. It does **not** convert Field Observations into cost.

---

## V1 policy freezes

These were open in the recon. This gate **freezes** them. Joel/ChatGPT approved them as written on 2026-09-06:

| Decision | Freeze |
|----------|--------|
| Include office Direct Cost actuals in V1? | **Yes.** Same gate. Without actuals, Actual GM must not be claimed and Item 13 is incomplete. |
| Incremental vs restated class-to-date? | **Incremental** observations + supersession (Field Event analogue). |
| MONITOR-owned comparison snapshots in V1? | **No.** Live projection only. |
| Who may enter actuals? | Any FG-018 org member who can open the Hub. **No RBAC.** |
| Forecast-final GM | **Out of V1.** Actual-to-date only. |
| Field Events as actuals | **No.** Evidence only. |

If Joel rejects office actuals in this gate, **STOP** and return a baseline-only amendment. Do not silently drop Actual GM while keeping “estimated-vs-actual” language.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | After BUILD Field Capture / Field Web, CalibAi still has no estimated-versus-actual or Project Gross Margin surface. Hub MONITOR is labeled Future. No verified Actual Direct Cost records exist. Office cannot compare the frozen composed baseline to incurred Direct Cost without QuickBooks. |
| 2 | Who is the user? | Office estimator / PM / principal on the **desktop** Project Hub. Not the customer. Not Field Web. Not a public API consumer. |
| 3 | Which module owns it? | **MONITOR** owns the comparison projection (no durable MONITOR table in V1). **BUILD** owns `ProjectDirectCostActual`. **Projects** owns Hub chrome at `/projects/<id>`. Estimating / Pricing Engine / Proposals / Project Controls keep commercial SoR. |
| 4 | What data does it own? | MONITOR: **no new durable records** (live projection; optional dated comparison snapshots deferred). BUILD: `ProjectDirectCostActual` rows (incremental incurred Direct Cost). Hub: no new entity. |
| 5 | What data does it reference? | Locked source `EstimateVersion`; `EstimatePricingSnapshot` when present; `EstimateLineItem.extended_cost` fallback; Accepted `Proposal`; authorized `ChangeOrder` (`Approved` or `Invoiced`) `subtotal + markup`; `Organization` / `Project` / `User`; **not** Field Events as cost; **not** `EstimateLabourSnapshot` as actual or as selling-price basis. |
| 6 | What may implementation change? | Additive BUILD actuals model + service + Hub-routed POST/supersede; MONITOR read service; Hub `#hub-monitor` operational panel; dedicated tests; governed docs; **one** additive Alembic revision **only after** an approved implementation prompt. |
| 7 | What must it not change? | Approved estimate / Accepted Proposal / Change Order commercial values; Field Capture Events / Originals / Derived Candidates; Labour Engine / Pricing Engine standards; LEARN; Field Web UI; QuickBooks; Phase D; Observation Delete; Closeout; Native Signing; session revocation; RBAC; org-switcher; NET PROFIT language; CO estimated-cost schema; forecast snapshots; historical ingestion as this-project actuals. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. **Not met** — implementation not yet authorized. |
| 9 | Tests required? | Dedicated `tests/test_monitor_v1_fg023.py` (name may vary) covering composition, PGM, missing states, actuals sum/supersession, org isolation, Hub copy, immutability; Hub/auth regressions; full suite. Exact count deferred until implementation. |
| 10 | Documentation? | This gate; feature-gate index; `modules/monitor.md`; `modules/build.md`; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones; docs/README; recon subsequent status. |
| 11 | ADR required? | **No new ADR.** ADR-021 already accepted. Stop and return if implementation would invent NET PROFIT, CO cost-from-`unit_price`, Field-Event-as-cost, QuickBooks as required actuals, MONITOR as actuals SoR, or RBAC. |
| 12 | Migration? | **YES — approved as written** (BUILD `project_direct_cost_actuals`). Additive only. `down_revision` must be the then-current head (today `d2e3f4a5b6c7`). **Do not create the revision or choose a revision id in this approval pass.** If a later amendment strips actuals from V1, migration becomes **No**. |

---

## Owner

| Concern | Owner |
|---------|--------|
| Frozen composed baseline projection; Estimated / Actual-to-date GM; variance; missing-data warnings | **MONITOR** (read service) |
| `ProjectDirectCostActual` create / supersede / current-row sum | **BUILD** |
| `/projects/<id>` MONITOR panel and actuals form | **Projects** Hub UX, calling MONITOR reads and BUILD writes |
| `Estimate` / version / lines | Estimating |
| `EstimatePricingSnapshot` | Pricing Engine |
| Accepted Proposal | Proposals |
| Change Orders | Project Controls |
| Field Capture Event / Original | BUILD (unchanged; **not** a cost input) |

MONITOR **must not** become the actuals system of record ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) §10).

---

## Binding commercial identities

Tax remains **outside** GM. Pre-tax only. Do **not** introduce NET PROFIT.

```text
Original Estimated Direct Cost
  = EstimatePricingSnapshot.direct_cost_basis when present on the locked source version
    else Σ locked-version EstimateLineItem.extended_cost
  Do not add EstimateLabourSnapshot.direct_labour_cost.

Original Authorized Pre-Tax Revenue
  = snapshot pre_tax_selling_price when the Accepted Proposal’s source version has a snapshot
    else Accepted Proposal subtotal + overhead_amount + profit_amount

Approved CO Pre-Tax Revenue Delta
  = Σ (subtotal + markup) for Change Orders with status Approved or Invoiced
  Exclude Draft / Pending Approval / Rejected / Cancelled.
  Exclude tax. Do not treat Invoiced as books revenue.
  Do not drop an authorized CO solely because status later became Invoiced.

Current Authorized Estimated Cost
  = Original Estimated Direct Cost
  (CO estimated-cost delta does not exist. Do not invent it from unit_price.)

Current Authorized Pre-Tax Revenue
  = Original Authorized Pre-Tax Revenue + Approved CO Pre-Tax Revenue Delta
  (no governed credit instrument)

Estimated Gross Margin
  = 1 − (Original Estimated Direct Cost / Original Estimated Pre-Tax Selling Price)
  Do not recompute Estimated GM against CO-inflated revenue.

Actual Direct Cost to date
  = Σ amount of current (not-superseded) ProjectDirectCostActual rows for org+project

Actual-to-date Gross Margin
  = 1 − (Actual Direct Cost to date / Current Authorized Pre-Tax Revenue)
  Only when actuals exist and Current Authorized Pre-Tax Revenue is available.

Gross Margin Variance
  = Actual-to-date GM − Estimated GM
  Only when both GM figures exist.
```

Incomplete states must warn, not silent-zero:

- No Accepted Proposal → missing customer commitment
- No locked source version / no snapshot and no Accepted Proposal → missing original baseline
- No actuals → **MISSING ACTUALS**; do not claim Actual GM
- Draft-only estimate → not a committed baseline

Labour-apples-to-apples GM remains a **documented later** issue (ADR-021 §9). Do not “correct” it in this gate.

---

## Proposed BUILD actuals record (do not create until implementation is authorized)

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
| `created_at` | DateTime | required |
| `provenance` | Text | nullable |

Index `(organization_id, project_id)`. Unique `uq_project_direct_cost_actuals_supersedes_id`. Service must require `organization_id` == `Project.organization_id`.

**Correction:** superseding successor row. No in-place amount edit. No deletion. Successor may restated amount including `0.00`.

**Not V1 classes:** equipment as its own class; allowance draw; payroll burden; committed-but-not-incurred (PO); QuickBooks import.

---

## UI (binding)

Evolve existing `/projects/<id>` `#hub-monitor` ([FG-011](FG-011-project-hub-ux.md)).

**Not** a dedicated MONITOR app. **Not** Field Web.

Required Hub presentation after implementation:

1. Original estimated Direct Cost
2. Original authorized pre-tax revenue
3. Approved CO pre-tax revenue delta (and authorized CO count)
4. Current authorized pre-tax revenue
5. Current authorized estimated cost (= original DC) + explicit “CO cost delta not stored”
6. Estimated Project Gross Margin **or** missing-baseline warning
7. Actual Direct Cost to date by class + total **or** **MISSING ACTUALS**
8. Actual-to-date Project Gross Margin only if actuals exist
9. Variance only if both GM figures exist
10. Provenance: source version id, snapshot id, accepted proposal id, authorized CO ids, last actual `created_at`
11. Office form: class, amount, incurred date, note
12. List current actuals with supersede action

No invented health traffic-lights. No NET PROFIT label. No industry benchmarks.

Lifecycle chip `MONITOR · Future` becomes operational only when this gate is implemented and closed — **not** from this approval.

---

## Auth / org

Reuse FG-018 membership and Hub isolation:

- Login required (office HTML 302 `/login`)
- Membership-derived org context
- Cross-org project **404**
- Actor from session user (same as Field Events)
- CSRF on actuals POST
- No new auth architecture
- No session revocation
- No RBAC

---

## Acceptance criteria

Implementation (when separately authorized) is incomplete until all of the following are true:

1. Hub MONITOR panel is operational on `/projects/<id>` and no longer claims MONITOR is not operational **for this V1 scope**.
2. Floating drafts are never used as committed baseline.
3. Authorized CO set is `Approved` or `Invoiced`; tax excluded; `unit_price` not treated as cost.
4. Field Events are not inputs to Actual Direct Cost.
5. Posting/superseding actuals does not mutate estimate, Accepted Proposal, Change Order, or Field Event rows.
6. Missing-actuals and missing-commitment warnings appear instead of fake zeros.
7. Estimated GM uses the original pair; Actual GM uses current authorized pre-tax revenue.
8. UI never says NET PROFIT.
9. Org isolation holds.
10. Dedicated tests + focused Hub/auth/BUILD regressions + full suite pass; exact counts recorded at implementation close.
11. Office UAT (recon plan) performed and recorded under a later close prompt — **not** this approval pass.

---

## Tests (future; do not run as MONITOR tests in this approval pass)

Last governed product-changing baseline remains dedicated FG-021 **20** / focused **148** / full **558**. This approval pass does **not** rerun pytest.

When implemented: composition; floating-draft rejection; CO set; tax exclusion; no CO cost invention; actual sum of current rows; superseded excluded; `amount >= 0`; class enum; org isolation; CSRF; Hub copy; immutability; PGM identities; incomplete states; Field Events not inputs.

---

## Office UAT (future; do not perform)

Office-only:

1. Locked version + snapshot + Accepted Proposal + one Approved CO: three layers + estimated GM; MISSING ACTUALS; no Actual GM.
2. Enter labour and material actuals: totals + Actual GM + variance.
3. Supersede a mistaken actual: prior row retained; totals use successor.
4. Second org cannot see the project/actuals.
5. Estimate / Accepted Proposal / CO / Field Event unchanged.
6. HST not in GM; CO tax not in revenue; no NET PROFIT copy.
7. Draft-only estimate: committed baseline missing, not a fake number.

---

## Explicit non-goals

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
- `LabourActualObservation`
- Converting Field Observations into cost
- MONITOR-owned snapshot table in V1
- New RBAC / org-switcher
- Dashboard org-unscoped counts

---

## Approval

| Role | State |
|------|--------|
| Joel | **Approved as written** 2026-09-06. Correction semantics including `amount >= 0` / `0.00` superseding successor **accepted**. |
| ChatGPT review | **Approved as written** 2026-09-06. |
| Cursor | Slice A implemented 2026-09-06. Slice B implemented 2026-09-07 (Hub `#hub-monitor` + BUILD office actuals create/supersede). Slice C live migrate + office UAT **PASS** 2026-09-07. Gate **not closed**. |

**Next governed action:** FG-023 **CLOSE AUTHORIZATION** — separate ChatGPT prompt. Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**. Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / NOT YET CLOSED**. Do **not** close FG-023 from this Slice C execution record. Do **not** begin FG-024. Do **not** implement [FG-025](FG-025-contractor-facing-ux-language-and-terminology-standardization.md) (FUTURE / RECORDED; waits for this gate to close). Do **not** start LEARN. Do **not** start Observation Delete.

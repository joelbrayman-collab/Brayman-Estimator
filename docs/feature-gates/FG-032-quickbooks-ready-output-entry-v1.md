# Feature Gate FG-032: QuickBooks-Ready Output / Controlled Human-Entry V1

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-032` |
| Feature Name | QuickBooks-Ready Output / Controlled Human-Entry V1 |
| Target Milestone | **V1-05.** This gate is the V1 Feature Gate for four-output **output 3**. It is **not** a 12th major V1 package. Recording **does not** rescore [v1-completion-register.md](../v1-completion-register.md). Preserve **55% / 3 of 11 COMPLETE**. Current scored package remains **V1-04**. |
| Module | **Estimating / output layer** owns the future QuickBooks-ready package, freeze, review, generation, supersession, and human entry-confirmation records. Proposals continue to own the customer Proposal/PDF. Pricing Engine continues to own `EstimatePricingSnapshot`. Estimating continues to own `EstimateCostingSnapshot` and Scope Delivery. QuickBooks Online is **not** an owner in V1. |
| Date | 2026-09-10 |
| Status | **SLICES A+B IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT / SLICE C NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED / OVERALL NOT CLOSED.** [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted** by Joel Brayman, 10 Sep 2026. Joel selected **Option A** on 2026-09-10. Option B remains **POST-V1**. Live current = repository head **`e9f0a1b2c3d4`**. Evidence [testing/fg032-slices-ab-live-migrate-bounded-uat-record.md](../testing/fg032-slices-ab-live-migrate-bounded-uat-record.md). |
| Architecture | [fg-032-quickbooks-option-a-preflight.md](../architecture/fg-032-quickbooks-option-a-preflight.md) · [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted** · [quickbooks-integration.md](../architecture/quickbooks-integration.md) · [project-document-package.md](../architecture/project-document-package.md) · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** · [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** · [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted** · [FG-012](FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-027](FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-031](FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT** |
| Related ADRs | **[ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) Accepted** 10 Sep 2026. Do **not** accept [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md). |
| Prerequisites | FG-012 outputs 1–2 **CLOSED**. FG-027 CURRENT costing snapshot. FG-009 CURRENT (not STALE) pricing snapshot — consume status is **derived** (`pricing_consume_status()`), not a snapshot `status` column. FG-031 frozen routing on costing snapshot lines. FG-022 Family 04 presentation master (external). Issued or Accepted Proposal whose **current** totals match CURRENT pricing. **Accepted** is commercially immutable ([ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)); **Issued remains editable**. This recording does **not** implement any of those. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **SLICES A+B LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT.** **OVERALL NOT CLOSED.** |
| Product implementation | **SLICES A+B IMPLEMENTED.** Slice C **NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED.** |
| Schema / Alembic | Additive **`e9f0a1b2c3d4`** revises **`d8e9f0a1b2c3`**. One graph head. **Applied live 2026-09-11.** Live current **`e9f0a1b2c3d4`**. |
| Live QuickBooks API (Option B) | **POST-V1 / NOT AUTHORIZED** |
| CSV / IIF / Excel / SDK import | **NOT CLAIMED / NOT AUTHORIZED** |
| V1 scoring | **Unchanged.** **55% / 3 of 11 COMPLETE.** V1-04 remains **PARTIAL** and the current scored package. V1-05 remains **PARTIAL**. |

```text
FG-032:
SLICES A+B IMPLEMENTED / TESTED / COMMITTED / PUSHED
LIVE-MIGRATED 11 SEP 2026
BOUNDED OFFICE UAT PASS
OPERATIONAL FOR UAT
SLICE C NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED
OVERALL NOT CLOSED
ADR-049 ACCEPTED 10 SEP 2026
JOEL OPTION A DIRECTION APPROVED 2026-09-10
OPTION B LIVE QUICKBOOKS API = POST-V1 / NOT AUTHORIZED
SCHEMA e9f0a1b2c3d4 APPLIED LIVE
LIVE CURRENT = REPOSITORY HEAD e9f0a1b2c3d4
PRODUCT SHA 70e571140e12377aa5bd009b598530576401113b
PRODUCT PARENT 010f6d641a756ceb2ab67475a284d3b8426c7b20
UAT START PIN 520eeca7410e1a575f46a0bb8ed8126ea0d26445
DO NOT RESCORE V1 (REMAINS 55% / 3 OF 11)
V1-04 REMAINS PARTIAL / CURRENT SCORED PACKAGE
V1-05 REMAINS PARTIAL
FG-027 REMAINS FINAL COSTING AUTHORITY
FG-029 SUPPLIER PRICE REMAINS INFORM ONLY
FG-031 UNCHANGED (CLOSED / OPERATIONAL FOR UAT)
FG-030 UNCHANGED (RECORDED / NOT IMPLEMENTATION-AUTHORIZED)
ADR-008 REMAINS PROPOSED
BMR DEMO READY NO
BRAYMAN REAL-LIFE UAT READY NO
```

Joel selected Option A on **2026-09-10**. Slices A+B are live-migrated with bounded office UAT **PASS**. Slice C remains unauthorized. The gate is **not closed**.

---

## Purpose

Define the minimum credible V1 QuickBooks-ready output and controlled human-entry workflow generated from the authoritative CalibraytAI estimate record, without a live QuickBooks API.

V1 output 3 is a **controlled pair** of **internal office** artifacts:

1. **Sales-estimate entry sheet** (Family 04 presentation) — customer selling lines + tax for manual QuickBooks Estimate entry.
2. **Planned cost-classification companion** — approved direct-cost amounts classified from frozen FG-031 routing.

CalibraytAI remains the commercial source of truth. QuickBooks is the accounting destination.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Brayman can produce approved costing, pricing, and a customer Proposal, but there is no governed QuickBooks-ready office artifact or controlled entry workflow. Manual office entry today is untracked, can float after recost/reprice, can leak internal cost into the customer package, or can be mistaken for a live QuickBooks post. |
| 2 | Who is the user? | Contractor office estimator / accounting clerk on Project Hub PRICE / Estimating. Not the customer. Not a supplier named-user. Not a QuickBooks API. |
| 3 | Which module owns it? | Estimating / output layer owns the QuickBooks-ready package. Proposals own the customer PDF. Pricing Engine owns pricing snapshots. Estimating owns costing snapshots and Scope Delivery. QuickBooks is not an owner. |
| 4 | What data does it own? | `EstimateQuickBooksPackage`, `EstimateQuickBooksSalesLine`, `EstimateQuickBooksCostClassLine`. Slice C entry-confirmation events are **not** owned yet. Not `EstimateLineItem`. Not costing/pricing snapshots. Not Proposal. Not Scope Delivery. Not supplier price. Not PLAN. |
| 5 | What data does it reference? | Organization; Client; Project; Estimate / EstimateVersion; CURRENT `EstimateCostingSnapshot`; CURRENT `EstimatePricingSnapshot`; Issued/Accepted Proposal; frozen FG-031 routing copied onto costing snapshot lines. |
| 6 | What may it change? | Estimating-owned freeze tables, review/issue routes, private HTML/PDF artifacts, Hub PRICE entry. Must **not** mutate costing, pricing, Proposal, Scope Delivery, or catalogues. |
| 7 | What must it not change? | Costing or pricing calculations; Proposal/PDF; Supplier Package; Scope Delivery product behaviour; FG-027 / FG-029 / FG-031 closed product meaning; live DB; live QuickBooks API; CSV/IIF/Excel claims; invoices/bills/POs/payroll/payments; ADR-008 status; V1 55% / 3 of 11; branding; FG-024; FG-030; remaining FG-025; LEARN; Native Signing; Observation Delete. |
| 8 | What are the acceptance criteria? | Slices A+B implemented, tested, live-migrated, and bounded office UAT **PASS**; ADR-049 Accepted; additive **`e9f0a1b2c3d4` applied live**; freeze/non-float, reconciliation, privacy, isolation, download-not-entry, supersession tests PASS; Slice C not implemented; gate not closed. |
| 9 | What tests are required? | Post-migrate dedicated FG-032 **23 passed** (12.96s, 306 warnings). Full suite **`./venv/bin/python -m pytest -q` → 751 passed**, 2479 warnings, 329.14s. Implementation-time focused regression **209 passed** (89.55s) remains historical. |
| 10 | What documentation must be updated? | This gate; ADR-049; Option A preflight; quickbooks-integration.md; project-document-package.md; estimating module; indexes; V1 register **status text only** (do **not** rescore). |
| 11 | Does it require an ADR? | **Yes — ADR-049**, **Accepted** by Joel Brayman, 10 Sep 2026. |
| 12 | Does it require a database migration? | **Yes.** Additive **`e9f0a1b2c3d4`** after **`d8e9f0a1b2c3`**. **Applied live 2026-09-11.** Live current = head **`e9f0a1b2c3d4`**. |
| 13 | UAT plan | Bounded office UAT **PASS** 2026-09-11 on DEMO project **id 26**. Issued WARN + exact reconciliation; Accepted eligibility; review-before-issue `NOT_REVIEWED`; Hub PRICE link; privacy; isolation 404; ISSUED non-float; unissued STALE BLOCK; hybrid amount once; Proposal/Supplier Package unchanged. Slice C ENTERED confirmation remains unauthorized. Evidence [testing/fg032-slices-ab-live-migrate-bounded-uat-record.md](../testing/fg032-slices-ab-live-migrate-bounded-uat-record.md). |
| 14 | Current / intended / future | **Current:** Slices A+B live-migrated / bounded office UAT PASS / operational for UAT. **Intended remaining:** Slice C entry confirmation. **Future / POST-V1:** Option B live QuickBooks Online API; CSV/IIF if a later gate proves a supported import contract; invoices/bills/POs/payroll/actuals. |
| 15 | Privacy boundary | Both V1 artifacts are **internal office / accounting**. Artifact A must not include internal cost, routing, supplier price, subcontract quotes, or margin. Artifact B must not be attached to the customer Proposal/PDF or Supplier Package. Existing customer and supplier privacy remains. |
| 16 | QuickBooks Option A definition | Governed QuickBooks-**ready** HTML preview + PDF (and frozen package record) for **manual** QuickBooks Estimate entry, plus a private planned cost-class companion. No live API. No claimed import file. Download is not entry. |
| 17 | Option B exclusion | Live QuickBooks Online API, OAuth, SDK, auto-post, and any claim that CalibraytAI verified QuickBooks acceptance are **POST-V1 / NOT AUTHORIZED** by this gate. |
| 18 | Implementation slices | **A** persistence + sales-entry HTML/PDF freeze — **IMPLEMENTED**. **B** internal cost-class companion — **IMPLEMENTED**. **C** entered-in-QuickBooks confirmation + duplicate/reversal audit — **NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. |
| 19 | Stop conditions | Missing CURRENT costing or CURRENT (not STALE) pricing; unresolved routing on a non-Allowance line; missing client/project; missing tax; totals mismatch vs Issued/Accepted Proposal; cross-org; mutate ISSUED; generate a second ISSUED package from the same pins without supersession; attempt live API; attempt to invent hybrid amount splits; attempt to use supplier/subcontract quote as cost authority. |
| 20 | Closure conditions | Live migration applied; office UAT PASS; Slice C remains a later authorization. This implementation **does not** close the gate. |

---

## Option A vs Option B

| Option | V1 status |
|--------|-----------|
| **A.** Governed QuickBooks-ready output / controlled human-entry workflow | **JOEL SELECTED 2026-09-10.** Slices A+B **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Slice C **NOT AUTHORIZED**. Gate **NOT CLOSED**. |
| **B.** Live QuickBooks Online API | **POST-V1 / NOT AUTHORIZED** unless Joel separately reverses. |

Distinguish:

| Term | Meaning in this gate |
|------|----------------------|
| QuickBooks-ready | Internal artifacts a human can use to type a QuickBooks Estimate |
| QuickBooks-importable | A file QuickBooks will ingest without typing — **not claimed** |
| Manual QuickBooks entry | Human types from the sheet into QuickBooks |
| Live QuickBooks integration | API/OAuth/post — Option B / POST-V1 |

---

## Output 3 recommendation (locked for this architecture)

**C. Controlled pair** of sales-estimate entry + planned cost-classification companion.

Not A (sales only). Not B (cost/budget only). Not invoices, bills, POs, payroll, deposits, or actuals.

---

## Non-goals

Live QuickBooks API · OAuth · SDK · CSV/IIF/Excel import claims · invoices · vendor bills · purchase orders · payroll · payments · banking · actual-cost sync · mutating costing/pricing/Proposal · accepting ADR-008 · implementing FG-030 · implementing V1-04 product work as a substitute for this gate · implementing V1-06 · rescoring V1

---

## Current vs intended vs future

| Layer | State |
|-------|--------|
| **Current** | Authoritative EstimateVersion; CURRENT costing snapshot; CURRENT pricing snapshot; Issued/Accepted Proposal; FG-031 freeze on costing lines; FG-012 internal breakdown; Family 04 master outside Git. No QB package. No entry confirmation. |
| **Intended (this gate, not implemented)** | Frozen Option A pair; human review; ISSUED bytes that do not float; optional human ENTERED confirmation; supersession for correction. |
| **Future** | Option B API; proven import formats if separately gated; invoices/bills/POs; hybrid amount split if a later gate stores it. |

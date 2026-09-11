# FG-032 QuickBooks Option A — Architecture preflight

| Attribute | Value |
|-----------|--------|
| Status | **RECONCILED WITH IMPLEMENTED SLICES A+B.** Product implemented; migration file **`e9f0a1b2c3d4`** not applied live. [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **OVERALL NOT CLOSED.** |
| Date | 2026-09-10 |
| Gate | [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) |
| ADR | [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted** 10 Sep 2026 |
| Alembic | Live current **`d8e9f0a1b2c3`**. Repository head **`e9f0a1b2c3d4`**. One graph head. **Not applied live.** |
| Product | CalibraytAI (formerly CalibAi) |
| Tenant | Brayman Construction Inc. / ORG-001 |
| Joel decision | **V1-05 Option A approved 2026-09-10.** Option B live QuickBooks Online API remains **POST-V1**. |

```text
FG-032 PREFLIGHT:
RECONCILED WITH SLICES A+B IMPLEMENTATION
ADR-049 ACCEPTED 10 SEP 2026
SLICES A+B IMPLEMENTED / NOT LIVE-MIGRATED
SLICE C NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED
SCHEMA FILE e9f0a1b2c3d4 / LIVE CURRENT d8e9f0a1b2c3
V1 REMAINS 55% / 3 OF 11
V1-04 REMAINS PARTIAL / CURRENT SCORED PACKAGE
V1-05 REMAINS PARTIAL
OPTION A = QUICKBOOKS-READY MANUAL ENTRY (NOT IMPORT, NOT API)
OUTPUT 3 = CONTROLLED PAIR (SALES-ENTRY SHEET + COST-CLASS COMPANION)
```

This document remains the architecture preflight. Slices A+B product code and migration **file** exist. Live database writes and office UAT remain unauthorized.

**Subsequent recon note (2026-09-11):** Git parent of product **`70e571140e12377aa5bd009b598530576401113b`** is **`010f6d641a756ceb2ab67475a284d3b8426c7b20`** (`docs: correct FG-032 Issued vs Accepted freeze`), not FG-031 Slice B **`5e1082af68e0eb145d9da01c0fa26585f6b8b9d1`**. Architecture **`93773820e410e327cd81919172c49a6f661def9e`**. Docs pin **`9c254a38c39ef866cad3c5aca1f01cae4907f376`**. Live current remains **`d8e9f0a1b2c3`**. Repository head remains **`e9f0a1b2c3d4`**.

**Subsequent recon note (2026-09-10):** Late model inventory confirmed: pricing CURRENT/STALE is **derived** (`pricing_consume_status()`), not a snapshot column; Proposal commercial immutability is **Accepted only** (ADR-002); Issued remains editable; `project_number` is on `Project` (not copied onto Proposal); unit selling rate for artifact A is `ProposalLineItem.unit_price`. Architecture recommendation unchanged: copy-at-freeze; WARN if Issued.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | Authoritative `Estimate` / `EstimateVersion`; FG-027 CURRENT `EstimateCostingSnapshot`; FG-009 `EstimatePricingSnapshot` (CURRENT vs `STALE / REQUIRES RE-APPLY`); Issued/Accepted `Proposal` + PDF (output 2); FG-012 internal breakdown (output 1); FG-031 frozen `material_procurement` / `labour_delivery` on costing snapshot lines; Family 04 reusable master **outside Git**. FG-032 Slices A+B package/HTML/PDF **implemented / not live-migrated**. No QuickBooks client, OAuth, IIF, CSV, or “entered in QuickBooks” record in `app/`. |
| **Intended remaining (FG-032)** | Live migrate + office UAT. Slice C ENTERED/REVERSED confirmation remains **not authorized**. |
| **Future / POST-V1** | Option B live QuickBooks Online API; CSV/IIF/Excel only if a later gate proves a supported import contract; invoices, bills, POs, payroll, payments, banking, actual-cost sync; stored hybrid amount split. |

---

## 2. Existing QuickBooks architecture found

[quickbooks-integration.md](quickbooks-integration.md) (pre-this-pass) already required:

- Estimator as authoritative record;
- only approved customer estimate proceeds to a QuickBooks **draft**;
- human review before customer send;
- no auto-send;
- QuickBooks must not become SoR.

It did **not** pin: artifact ownership, freeze identity, sales vs cost-class pair, manual-entry confirmation, or Option A vs B as Joel’s V1 decision.

[project-document-package.md](project-document-package.md) listed output 3 as a “customer-facing QuickBooks-ready representation.” Family 04 classification is **INTERNAL ENTRY REFERENCE / not customer-facing**. This preflight **corrects the audience**: output 3 is an **internal office/accounting** artifact. The **selling values** still match the approved customer estimate. The sheet is not a customer deliverable.

Four-output register: outputs 1–2 complete; 3–4 not implemented. V1-05 owns the QuickBooks handoff; V1-04 tracks whether output 3 exists in the package.

No application code matches QuickBooks, IIF, OAuth, or QBO SDK (repository search this pass).

---

## 3. Existing product capabilities found

| Capability | Evidence | Working / approved / frozen |
|------------|----------|-----------------------------|
| Organization identity | `organizations.id`, `legal_name`, `display_name`, `currency` (CAD), `tax_jurisdiction` label `"Ontario (HST 13%)"` | CURRENT org record; copy at package freeze |
| Brand / legal address | `OrganizationBrandProfile` (FG-017) | CURRENT; copy at generation like Proposal |
| Client | `Client.name`, `company`, `email`, `phone`, single `address` string | Working CRM; Proposal also freezes client_* at issue |
| Project | `Project.name`, `project_number`, `address`; `ProjectLocation` civic fields (FG-015) | Working; copy at freeze |
| Estimate | `estimate_number`; `EstimateVersion.id`, `version_number`, status, lock | Working until locked; ISSUED/ACCEPTED versions lock |
| Line working cost/sell | `EstimateLineItem` qty, unit, description, `unit_cost`, `extended_cost`, `sell_price` | **Working** — can float; **not** the export authority |
| Costing snapshot | `EstimateCostingSnapshot` CURRENT/SUPERSEDED; line `extended_cost`, `line_type`, frozen routing, quote freeze columns | **Approved / frozen** — cost authority |
| Pricing snapshot | unique per version; `pre_tax_selling_price`, `tax_percent`, `tax_amount`, `customer_total`, `costing_snapshot_id`. Consume status **CURRENT** vs **`STALE / REQUIRES RE-APPLY`** is **derived** by `pricing_consume_status()` (costing id match). There is **no** `status` column on `EstimatePricingSnapshot`. | **Approved / frozen** when the EstimateVersion is locked; STALE means re-apply required, not that the row was deleted |
| Scope Delivery | 1:1 `EstimateScopeDelivery`; CONFIRMED required for costing except Allowance | Working until freeze onto costing snapshot |
| Proposal | `proposal_number`, status, copied subtotal/tax/total; `ProposalLineItem.unit_price` / `extended_price`. **Commercial immutability is Accepted only** ([ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)). Issued remains editable. Brand identity freezes at Issued (or Accepted if never Issued). | Copy at create; **Accepted = immutable**. Do **not** cite ADR-002 as an Issued freeze |
| Internal breakdown | `app/services/estimate_output.py`; `GET /estimates/<id>/versions/<version_id>/internal-breakdown` | Derived view; not a QB artifact |
| Rounding | existing `as_money` ROUND_HALF_UP 0.01 | Authoritative money helper |
| ORG-001 commercial policy | 15% true GM (`Selling = Direct / 0.85`); HST 13% | Policy for **new** pricing apply — **not** reapplied at QB export |

---

## 4. Missing capabilities (do not invent)

- QuickBooks Customer / Item / Account / Tax-code IDs
- Structured client city / province / postal (Client has one address string)
- Currency column on EstimateVersion (use Organization.currency = CAD)
- Durable “entered in QuickBooks” record
- Any QB / CSV / IIF / OAuth code in `app/`
- Line-level frozen selling on the costing snapshot (selling lives on pricing/proposal)
- Stored hybrid money split of one `extended_cost`
- Deposits, discounts as first-class estimate fields, payment schedules, invoices, vendor bills, POs, payroll, actual-cost sync

---

## 5. Recommended V1 workflow (minimum)

```text
CURRENT costing snapshot
  + CURRENT (not STALE) pricing snapshot that consumed that costing snapshot
  + Issued or Accepted Proposal whose **current** totals match CURRENT pricing
    (Accepted is commercially immutable per ADR-002; Issued is still editable — copy onto the QB package at freeze)
  + client + project identity
  + tax on pricing snapshot
  + FG-031 routing already frozen on costing lines (UNRESOLVED already blocked costing except Allowance)
→ office user requests QuickBooks review (Hub PRICE / Estimating)
→ pre-generation validation (BLOCK / WARN)
→ preview of both artifacts
→ explicit human approve
→ freeze EstimateQuickBooksPackage (ISSUED) + HTML/PDF bytes
→ download for manual typing into QuickBooks Estimate
→ optional later human POST: entered in QuickBooks (never inferred from download)
→ recost / reprice that changes CURRENT snapshot identity → unissued DRAFT becomes STALE (BLOCK issue)
→ ISSUED historical package remains frozen
→ correction = new package + SUPERSEDE prior; no delete
```

Prerequisite estimate state: a locked or lockable EstimateVersion that already has costing approval and current pricing. Do not generate from Draft costing or STALE pricing.

User action: explicit office request. Not automatic on Proposal issue.

CalibraytAI **cannot** verify QuickBooks accepted the typed estimate. ENTERED is a human record only.

---

## 6. Accounting boundary — what V1 output 3 is

| Concept | In V1 Option A? |
|---------|-----------------|
| Customer Estimate / Sales Estimate (manual QB Estimate entry) | **Yes — artifact A** |
| Project/job identity (name + project_number copied onto the sheet) | **Yes — identifiers only** |
| Revenue / selling-price lines | **Yes — from pricing/Proposal** |
| Sales tax (HST) | **Yes — frozen pricing/Proposal tax** |
| Material / subcontract / internal labour **planned cost class** | **Yes — artifact B only** |
| Allowances | **Yes — labeled; same selling/cost rules as source snapshots** |
| Contingency | **Only if already inside frozen pricing snapshot treatment** — do not recompute |
| Discounts | **NOT REQUIRED** unless already stored on the Proposal snapshot (do not invent) |
| Deposits / payment schedules | **FUTURE** |
| Vendor bills / purchase orders | **Out of V1** |
| Actual costs | **Out of V1** (MONITOR/BUILD remain separate) |
| Invoices | **Out of V1** |

**Recommendation: C — controlled pair.**

Reasons:

- Family 04 is a **QuickBooks Estimate / Entry Sheet** of customer commercial fields (Product/Service, Customer Description, Qty, Amount, Tax).
- FG-031 exists so planned cost class can be consumed without contaminating the customer estimate.
- Collapsing A+B onto one customer-shaped sheet would leak internal classification into an entry artifact that looks like a sales estimate.
- Sales-only (A) would leave V1-05 unable to support job/cost-class setup.
- Cost-only (B) would ignore Family 04 and the four-output “Estimate / Entry” commitment.

Do **not** implement invoices, bills, POs, payroll, payments, banking, or actual-cost synchronization in FG-032.

---

## 7. Cost-classification approach (artifact B)

Use **frozen** FG-031 routing on `EstimateCostingSnapshotLine`, not live `EstimateScopeDelivery`.

| Frozen routing | Planned cost class |
|----------------|--------------------|
| `CONTRACTOR_PURCHASED` | MATERIAL / VENDOR (planned) |
| `SUBCONTRACT` and/or `SUBCONTRACTOR_SUPPLIED` | SUBCONTRACT (planned) |
| `INTERNAL` | INTERNAL LABOUR (planned) |
| `NO_MATERIAL` / `NO_LABOUR` | no corresponding planned class |
| `UNRESOLVED` | **BLOCK** generation (should already be impossible on CURRENT costing except Allowance) |
| Hybrid (`CONTRACTOR_PURCHASED` + `SUBCONTRACT`) | report **one** `extended_cost` once; show **both** dimensions; **do not split money** |

Amounts: approved `extended_cost` from the costing snapshot. Routing classifies; it does not prove the amount.

Supplier price and subcontract `subcontract_quoted_amount` remain **evidence**. They must not become automatic cost authority on artifact B.

Do not put selling price or tax on artifact B as a second selling total.

---

## 8. Source snapshots

| Amount kind | Authority |
|-------------|-----------|
| Direct cost / planned cost class amounts | CURRENT `EstimateCostingSnapshot` (FG-027). Human Costing Approval remains final cost authority. |
| Selling lines, pre-tax, tax, customer total | CURRENT `EstimatePricingSnapshot` **and** Issued/Accepted `Proposal` whose frozen totals **match** that snapshot (tolerance **0.00** after `as_money`). |
| Tax percent / amount | Frozen pricing snapshot (copied onto Proposal at issue). Do **not** reread current org policy. |
| Routing class | Frozen columns on costing snapshot lines (copied at Costing Approval from confirmed Scope Delivery). |
| Scope Delivery live rows | Prerequisite already enforced at costing; QB generation reads the **freeze**, not mutable working routing. |

Do **not** recompute `Direct Cost / 0.85` at export. Do **not** interpret 15% true gross margin as 15% markup.

### Reconciliation equations (ORG-001 / TRUE_GROSS_MARGIN)

At **pricing apply** (already implemented; not changed here):

```text
pre_tax_selling_price = as_money(approved_direct_cost_total / (1 - 0.15))
                      = as_money(approved_direct_cost_total / 0.85)
tax_amount            = as_money(pre_tax_selling_price * tax_percent / 100)
customer_total        = as_money(pre_tax_selling_price + tax_amount)
```

At **QB package freeze** (proposed):

```text
package.pre_tax      == pricing.pre_tax_selling_price == proposal.subtotal     (0.00)
package.tax_percent  == pricing.tax_percent           == proposal.tax_percent  (exact stored)
package.tax_amount   == pricing.tax_amount            == proposal.tax_amount   (0.00)
package.customer_total == pricing.customer_total      == proposal.total        (0.00)
Σ sales-entry line amounts == package.pre_tax                                 (0.00)
Σ cost-class line extended_cost == costing.approved_direct_cost_total         (0.00)
```

Mismatch **BLOCKS**. After ISSUED, do not recompute from current policy.

---

## 9. Field matrix

Status values: **AVAILABLE** · **DERIVED** · **MISSING** · **NOT REQUIRED** · **FUTURE**.

| Field | Source | Module | Working / approved / frozen | Safe to export? | Human confirm? | Status |
|-------|--------|--------|-----------------------------|-----------------|----------------|--------|
| Organization legal name | `organizations.legal_name` / Brand Profile copy | Organization / Brand | CURRENT copied at freeze | Yes (internal) | No beyond review | AVAILABLE |
| Organization identifier | `organizations.id` (ORG-001) | Organization | CURRENT | Yes (internal) | No | AVAILABLE |
| Customer / client name | `Client.name` and/or frozen `Proposal.client_name` | CRM / Proposals | Prefer Proposal freeze when Issued/Accepted | Yes | WARN if Client.name ≠ expected QB customer name | AVAILABLE |
| Customer address | `Client.address` or `Proposal.client_address` (one string) | CRM / Proposals | Unstructured | Yes | WARN if blank | AVAILABLE (unstructured) |
| Customer city / province / postal | none on Client | — | — | — | — | MISSING |
| Project name | `Project.name` / `Proposal.project_name` | Projects | Copy at freeze | Yes | No | AVAILABLE |
| Project number | `Project.project_number` | Projects | Copy at freeze | Yes | No | AVAILABLE |
| Site / project address | `Project.address` and/or `ProjectLocation` civic | Projects / Permit foundation | Copy at freeze | Yes | WARN if blank | AVAILABLE |
| Estimate number | `Estimate.estimate_number` | Estimating | Copy | Yes | No | AVAILABLE |
| EstimateVersion identifier | `EstimateVersion.id` + `version_number` | Estimating | Pin | Yes | No | AVAILABLE |
| Proposal identifier | `Proposal.id` + `proposal_number` | Proposals | Pin Issued/Accepted. Copy commercial values at QB freeze. **Accepted** is immutable; **Issued** is not. | Yes | WARN if Issued | AVAILABLE |
| Output generation date | package `issued_at` | Estimating (future) | Frozen at issue | Yes | No | DERIVED (after impl) |
| Currency | `Organization.currency` (CAD) | Organization | Copy; BLOCK if not CAD in V1 | Yes | No | AVAILABLE |
| Jurisdiction | pricing `tax_jurisdiction` / org label | Pricing / Organization | Frozen on snapshot | Yes | No | AVAILABLE |
| Tax code / QuickBooks tax mapping | none | — | — | — | Human must pick in QuickBooks | MISSING (manual in QB) |
| Tax label | stored jurisdiction / “HST 13%” from frozen percent | Pricing | Frozen | Yes | Review | DERIVED |
| Tax rate | `EstimatePricingSnapshot.tax_percent` | Pricing | Frozen | Yes | No | AVAILABLE |
| Subtotal before tax | `pre_tax_selling_price` / Proposal.subtotal | Pricing / Proposals | Frozen | Yes | Review | AVAILABLE |
| HST amount | `tax_amount` | Pricing / Proposals | Frozen | Yes | Review | AVAILABLE |
| Total including tax | `customer_total` / Proposal.total | Pricing / Proposals | Frozen | Yes | Review | AVAILABLE |
| Line description | Proposal line description (artifact A); costing line description (artifact B) | Proposals / Estimating | Frozen copies | A: customer-safe; B: internal | Review Product/Service label | AVAILABLE |
| Quantity | Proposal / costing snapshot line qty | same | Frozen | Yes | No | AVAILABLE |
| Unit | snapshot / proposal line unit | same | Frozen | Yes | No | AVAILABLE |
| Unit selling rate | `ProposalLineItem.unit_price` | Proposals | Frozen | Artifact A only | No | AVAILABLE |
| Line selling amount | `ProposalLineItem.extended_price` | Proposals | Frozen | Artifact A only | No | AVAILABLE |
| Section | EstimateSection name copied onto freeze | Estimating | Copy | Internal OK; A may omit if Family 04 has no section column | No | AVAILABLE |
| Allowance identity | costing `line_type` / `SOURCE_MANUAL_ALLOWANCE` | Estimating | Frozen | Label on both; no internal cost on A | No | AVAILABLE |
| Cost class | derived from frozen routing | Estimating | Frozen | Artifact B only | Review hybrid WARN | DERIVED |
| Approved direct cost | costing `extended_cost` / snapshot total | Estimating | Frozen | Artifact B only | No | AVAILABLE |
| Approved material cost | **not stored as a split total** | — | hybrid unsplit | B shows class, not invented split | — | MISSING as a money bucket; FUTURE split |
| Approved subcontract cost | same — not a stored split | — | quote amount is evidence only | Do not use quote as cost | — | MISSING as a money bucket; FUTURE split |
| Approved internal labour cost | same — not a stored split; Labour Engine snapshot is **not** selling basis | Labour Engine | display-only elsewhere | Do not use labour snapshot as cost authority | — | MISSING as a money bucket; FUTURE split |
| Actor | package `reviewed_by` / `issued_by` user id | Auth | Frozen | Internal | Explicit review action | AVAILABLE (after impl) |
| Approval time | `reviewed_at` / `issued_at` | Estimating (future) | Frozen | Internal | Explicit | DERIVED (after impl) |
| Source Costing Snapshot | `costing_snapshot_id` | Estimating | Pin CURRENT at issue | Internal | No | AVAILABLE |
| Source Pricing Snapshot | `pricing_snapshot_id` | Pricing | Pin | Internal | No | AVAILABLE |
| Source Scope Delivery state | frozen routing columns (not live row ids required) | Estimating | Frozen | Artifact B | No | AVAILABLE |
| Output version / status | package status machine | Estimating (future) | Frozen | Internal | No | DERIVED (after impl) |
| Manual-entry confirmation | confirmation events | Estimating (future) | Human POST | Internal | **Required to mark ENTERED** | MISSING now; intended |
| QuickBooks Customer Id | none | — | — | — | Human in QB | MISSING / FUTURE |
| QuickBooks Item / Account | none | — | Family 04 Product/Service column | Optional office label; not a catalogue | Human in QB | MISSING mapping; optional copied label |
| Deposits / payment schedule | Proposal payment_terms text only | Proposals | Narrative | Do not treat as QB schedule | — | NOT REQUIRED as structured; FUTURE |
| Invoice / bill / PO | none | — | — | — | — | FUTURE |

**Family 04 columns (verification PDF opened 2026-09-10):** INTERNAL ENTRY REFERENCE; QUICKBOOKS ESTIMATE / ENTRY SHEET; Client, Project, Site, Date, Customer, Project/Billing Address, Estimate date, Tax, Customer message; lines Product/Service, Customer Description, Qty, Amount, Tax; totals. Master stores **no** project amounts. Separately quoted work stays outside unless explicit instruction.

---

## 10. Ownership and source of truth

CalibraytAI remains the authoritative commercial record. QuickBooks is the destination.

The package **references** frozen source ids. It must **not** take ownership of EstimateLineItem, costing snapshot, pricing snapshot, Proposal, Scope Delivery, supplier pricing, subcontract quote evidence, or PLAN.

| Concern | Owner |
|---------|--------|
| QB-ready package + PDFs + confirmation | **Estimating / output layer** |
| Customer Proposal/PDF | Proposals (unchanged) |
| Pricing snapshot | Pricing Engine (consumed) |
| Costing snapshot / Scope Delivery | Estimating (consumed, not rewritten) |
| QuickBooks Online | None in V1 |

Estimating’s prior prohibition on “accounting integrations” is narrowed: it may own the **ready artifact**; it still must not own QuickBooks or become an accounting SoR.

Default candidate in the prompt is adopted **after** reconciling FG-012 (Estimating already owns internal breakdown; Proposals own customer PDF). Same pattern.

---

## 11. Human authority

No AI or deterministic rule may silently:

- approve costing or pricing;
- select a QuickBooks account or tax code;
- mark an output entered;
- overwrite an ISSUED artifact;
- post anything to QuickBooks.

V1 human confirmation:

- explicit review before ISSUED;
- optional Product/Service label on artifact A (Family 04 column; no item catalogue);
- explicit ENTERED confirmation POST;
- QuickBooks tax code / account / customer match remain **in QuickBooks**.

---

## 12. Immutability and versioning

| Rule | Decision |
|------|----------|
| Generated ISSUED output | Frozen snapshot (header + lines + PDF bytes or equivalent stored artifact) |
| Pins | org, project, estimate, EstimateVersion, costing_snapshot_id, pricing_snapshot_id, proposal_id, routing freeze as copied onto costing lines |
| Regeneration | Creates a **new** package; prior ISSUED → SUPERSEDED |
| Edit ISSUED | **Prohibited** |
| Correction | Supersession only; no history delete |
| Recost / reprice while unissued | DRAFT/REVIEWED becomes **STALE**; BLOCK issue until regenerated from new CURRENT pins |
| Recost / reprice after ISSUED | Historical ISSUED remains; new CURRENT pins require a new package if office wants a new handoff |
| Download | Does not mutate status to ENTERED |
| Duplicate QB entry | Discouraged by: one ISSUED package per pin-set unless superseded; WARN if ENTERED already; BLOCK second ENTERED on same package; human must SUPERSEDE/VOID to reverse |
| Reversal | New confirmation event REVERSED / CORRECTED; do not delete ENTERED history |

Historical outputs must not float when source estimates, costing, pricing, tax policy, or customer data later change.

---

## 13. Privacy and audience

Both artifacts are **internal office / accounting**.

| Surface | Must not receive |
|---------|------------------|
| Customer Proposal/PDF | cost class, routing enums, supplier price, subcontract quotes, margin, “entered in QuickBooks” |
| Supplier Package | selling price, margin, subcontract internals, QB package |

Separate artifacts **are required** (pair): sales-entry vs internal cost-class. Do not merge them into one PDF that could be emailed to a customer.

---

## 14. BLOCK vs WARN

**BLOCK (fail closed):**

- no CURRENT costing snapshot;
- no pricing snapshot, or pricing STALE / costing_snapshot_id mismatch;
- Issued/Accepted Proposal missing, or totals ≠ CURRENT pricing (0.00);
- unresolved routing on a non-Allowance costing line;
- missing client identity or project identity;
- missing tax treatment on pricing snapshot;
- currency not CAD (V1 unsupported);
- inconsistent Σ lines vs header totals;
- locked source mismatch (version/proposal/costing/pricing pins disagree);
- cross-organization access;
- mutate ISSUED / VOID package;
- generate a second ISSUED from the same pins without superseding;
- confirm ENTERED twice on the same package;
- non-CAD or missing organization.

**WARN (generate allowed after review):**

- Proposal is Issued but not Accepted (ADR-002 locks Accepted only; copy totals onto the QB package at freeze so later Proposal edits cannot float an ISSUED package);
- hybrid unsplit amount;
- Allowance lines;
- blank unstructured address;
- Client.name vs Proposal.client_name differ;
- no Product/Service mapping;
- OWNER_SUPPLIED / OWNER_THIRD_PARTY present (rare; classify explicitly, do not invent cost).

---

## 15. Duplicate and failure controls

- Unique constraint: at most one ISSUED package per (`estimate_version_id`, `costing_snapshot_id`, `pricing_snapshot_id`, `proposal_id`) unless status SUPERSEDED/VOID.
- Confirmation: at most one active ENTERED per package; subsequent ENTERED **BLOCKS**; REVERSED allows a later ENTERED with new event row.
- Download counter is informational; it is **not** entry.
- Cross-org: same fail-closed 404 pattern as other Estimating routes.

---

## 16. Presentation reference (Family 04 / Allen Jacques)

Repository manifests:

- Classification: **INTERNAL ENTRY REFERENCE**. **Not** customer-facing. **Not** QuickBooks API.
- Reusable master: **JOEL APPROVED**.
- Source Allen Jacques DOCX/PDF live **outside Git**.
- Verification PDF **was opened this pass** at  
  `/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/Reusable Master Template Family V1/VERIFICATION PDF/04_Brayman_QuickBooks_Estimate_Entry_MASTER_V1.pdf`
- It represents **manual entry** presentation, not structured import.
- Master stores no project amounts.

**PRESENTATION CONTENT REVIEW REQUIRED BEFORE IMPLEMENTATION** for pixel/DOCX geometry, fonts, and exact Family 04 layout mapping. That does **not** block this data/architecture preflight.

The Allen Jacques **filled project** PDF is a presentation reference, not a reusable master. Do not change the approved presentation baseline.

---

## 17. Persistence (implemented Slices A+B; not applied live)

Names are proposals. Do not create models or Alembic now.

### `estimate_quickbooks_packages`

| Column | Notes |
|--------|--------|
| id | PK |
| organization_id | FK organizations, RESTRICT, indexed |
| project_id | FK projects, RESTRICT, indexed |
| estimate_id | FK estimates, RESTRICT |
| estimate_version_id | FK estimate_versions, RESTRICT, indexed |
| costing_snapshot_id | FK estimate_costing_snapshots, RESTRICT |
| pricing_snapshot_id | FK estimate_pricing_snapshots, RESTRICT |
| proposal_id | FK proposals, RESTRICT |
| package_number | org-scoped unique display id |
| status | DRAFT / REVIEWED / ISSUED / SUPERSEDED / VOID |
| superseded_by_id | self-FK nullable |
| currency | copy CAD |
| tax_percent, pre_tax, tax_amount, customer_total | copies; Numeric(14,2) |
| approved_direct_cost_total | copy from costing |
| warning_codes / block_codes | JSON |
| reviewed_by_user_id, reviewed_at | |
| issued_by_user_id, issued_at | |
| sales_pdf_sha256 / sales_storage_key | issued artifact |
| cost_class_pdf_sha256 / cost_class_storage_key | issued artifact |
| created_at | |

Check: status enum. Unique partial: one ISSUED per pin-set.

### `estimate_quickbooks_sales_lines`

Frozen artifact A lines: description, qty, unit, unit_price, amount, tax_label, optional product_service_label, source_proposal_line_id, sort_order.

### `estimate_quickbooks_cost_class_lines`

Frozen artifact B lines: description, qty, unit, extended_cost, material_procurement, labour_delivery, planned_class, is_hybrid, is_allowance, source_costing_snapshot_line_id, sort_order. **One amount per commercial line.**

### `estimate_quickbooks_entry_events`

kind: ENTERED / REVERSED / CORRECTED; actor_user_id; occurred_at; note; **not** inferred from download.

Storage: private org path under `instance/` (same custody pattern as Supplier Package / brand logos). Not public.

---

## 18. Status machine

```text
DRAFT → REVIEWED → ISSUED → SUPERSEDED
                              ↘ VOID
```

- DRAFT: preview assembled, not released.
- REVIEWED: human reviewed, not issued.
- ISSUED: frozen downloadable artifacts.
- SUPERSEDED / VOID: terminal for that row; bytes retained.

Unissued + source CURRENT identity change → treat as STALE (implementation may use status STALE or a `stale` flag on DRAFT/REVIEWED).

---

## 19. Routes / templates / services (proposed; not created)

| Surface | Proposal |
|---------|----------|
| Review | `GET /projects/<id>/quickbooks-entry` and/or `GET /estimates/<id>/versions/<vid>/quickbooks-entry` |
| Preview | same GET; render HTML for A and B |
| Issue | `POST .../quickbooks-entry/issue` (CSRF, membership) |
| Download | `GET .../quickbooks-packages/<pkg_id>/sales.pdf` and `.../cost-class.pdf` |
| Confirm entered | `POST .../quickbooks-packages/<pkg_id>/entered` |
| Reverse | `POST .../quickbooks-packages/<pkg_id>/reverse-entry` |

Reuse WeasyPrint/HTML patterns from Supplier Package / Proposal PDF. Family 04 layout mapping is implementation-time.

Authorization: FG-018 contractor membership; org isolation; 404 cross-org.

Services (names): `app/services/estimate_quickbooks.py` assemble/validate/issue/stale-check; do not live in Pricing Engine or Proposals.

---

## 20. Implementation slices (recommended; not authorized)

| Slice | Scope |
|-------|--------|
| **A** | Persistence + validation + sales-entry HTML/PDF freeze + review/issue/download |
| **B** | Internal cost-class companion HTML/PDF + hybrid/Allowance WARN + privacy tests |
| **C** | ENTERED / REVERSED events + duplicate BLOCK + download ≠ entered |

Do not begin Slice A without a separate implementation prompt and Joel authorization. Prefer ADR-049 **Accepted** before schema if Joel requires acceptance first; this recording leaves ADR-049 **Proposed**.

**Subsequent status (2026-09-11):** Slices A+B were later implemented under Joel authorization. ADR-049 is **Accepted**. Slice C remains **NOT IMPLEMENTATION-AUTHORIZED**. Do **not** live-migrate from this preflight.

---

## 21. Migration plan

**Required later: YES.** Additive Alembic after implementation authorization.

**This pass: do not create a revision. Do not `flask db upgrade` or downgrade.**

Rollback later: drop new tables only if never ISSUED in production; otherwise preserve freeze rows.

---

## 22. Tests (later implementation; not run now)

**Focused:** assemble BLOCK/WARN; pin CURRENT costing+pricing+Proposal; total 0.00 reconcile; STALE pricing BLOCK; unresolved routing BLOCK; hybrid not double-counted; privacy (Proposal HTML/PDF unchanged; Supplier Package unchanged); isolation; ISSUED immutable; supersession; ENTERED not from download; second ENTERED BLOCK; CAD-only.

**Regression:** FG-012 output; FG-027 costing; FG-009 pricing; FG-031 routing; FG-029 supplier package; Proposal PDF; clone/lock.

**Office UAT script (later):** pick ORG-001 project with Issued **or Accepted** Proposal matching CURRENT pricing; if Issued, confirm WARN that commercial fields remain editable; open review; confirm BLOCK on STALE; issue; download both PDFs; type into QuickBooks offline (operator); confirm ENTERED; recost a **copy/new version** and prove historical ISSUED totals unchanged.

This recording: **tests not rerun.** HISTORICAL: focused **83 passed** / 454 warnings / 15.24s; full **728 passed** / 2173 warnings / 373.17s.

---

## 23. Documentation close requirements (later implementation)

Update current-state, session-handoff, chat-workflow-log, module estimating, this preflight status, FG-032 closure fields, V1-04 output 3 status **when implemented**. Do **not** rescore V1 from architecture recording. Rescore only when the governing register’s completion rules say output 3 exists **in product**.

---

## 24. Prohibited scope

Application code in this pass · models · routes · services · templates · CSS/JS · migration file · live DB mutation · generate a live QB artifact · connect to QuickBooks · CSV/IIF/Excel · implement confirmation · begin V1-04 product implementation as a substitute · V1-06 · legal content · FG-030 · subcontract RFQ/package · accept ADR-008 · alter supplier pricing · alter costing/pricing calculations · alter Proposal/PDF · branding · rescore V1 · unrelated cleanup

---

## 25. Recommendations (prompt §21)

| Item | Recommendation |
|------|----------------|
| A. Minimum workflow | §5 above |
| B. Artifact pair | Sales-entry sheet + planned cost-class companion |
| C. Format | Office HTML preview + PDF. QuickBooks-**ready**, not importable. No CSV/IIF/Excel/API claim |
| D. Manual entry | Human types QuickBooks Estimate from artifact A; uses B for job/cost-class setup; ENTERED is a later human POST |
| E. Owner | Estimating / output layer |
| F. Source snapshots | CURRENT costing + CURRENT pricing + Issued/Accepted Proposal |
| G. New persistence | Package + sales lines + cost-class lines + entry events |
| H. Schema/migration | **YES later.** **NO file now** |
| I. Slices | A → B → C |
| J. Allen Jacques / Family 04 | Architecture can complete; **presentation content review required before implementation** for layout |
| K. V1 readiness now | **No change — 55%** |
| L. V1-04 status now | **No change — PARTIAL**; output 3 still not implemented |
| M. BMR Demo Ready | **NO** (unchanged) |
| N. Ontario contract blocker | Legal Content Gate **empty**; Family 05 **NOT LEGALLY APPROVED**; unchanged |
| O. FG-030 | Remain **RECORDED / NOT IMPLEMENTATION-AUTHORIZED** |

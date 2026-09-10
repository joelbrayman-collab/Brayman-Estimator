# FG-031 Slice B live migrate + bounded office UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated. Bounded DEMO/SYNTHETIC office UAT **PASS**. Slice B **OPERATIONAL FOR UAT**. FG-031 **OVERALL NOT CLOSED** (ChatGPT Architect confirmation of remaining gate close still required). |
| Date | 2026-09-10 |
| Gate | [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) |
| Product SHA | `5e1082af68e0eb145d9da01c0fa26585f6b8b9d1` |
| Start pin SHA | `314ced5699688a329dbdd7ab2484ef552dd447db` |
| Actor | Joel Brayman — FG031B-UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Authenticated Flask `test_client` against live office PRICE / Scope Delivery Review / costing / pricing / proposal / Supplier Package routes. Session `_user_id` = `"1"` (Joel Brayman). Gitignored runner `instance/fg031b_uat_office.py` (not committed). |

This file records Slice B live-migration and UAT facts only. It does **not** overwrite [fg031-live-migrate-bounded-uat-record.md](fg031-live-migrate-bounded-uat-record.md). It does not implement FG-030, V1-04, or a subcontract RFQ/package.

## Migration

| Field | Value |
|-------|--------|
| Live SQLite | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` (`sqlite:///brayman_estimator.db` → Flask instance path) |
| Pre-migration live current | `c7d8e9f0a1b2` |
| Repository head | `d8e9f0a1b2c3` |
| Backup | `instance/brayman_estimator-backup-before-fg031b-d8e9f0a1b2c3-20260910-083215.db` (gitignored; not committed) |
| Backup size | 1,855,488 bytes (matches live source at backup time) |
| Backup SHA-256 | `b1096083400b6bc840cdb113e157f5795fb3a7c52723ffb70515eb293617bef5` |
| Backup Alembic | `c7d8e9f0a1b2` (Slice B tables absent; 87 sqlite tables) |
| Command | `./venv/bin/flask db upgrade` |
| Post-migration live current | `d8e9f0a1b2c3 (head)` |
| Post-migration repository head | `d8e9f0a1b2c3 (head)` |
| Graph heads | one |
| Added tables | `subcontractors`, `subcontract_quote_evidence` (87 → 89 tables) |
| Added freeze columns | `estimate_costing_snapshot_lines.subcontract_quote_evidence_id`, `subcontract_quote_reference`, `subcontract_quoted_amount`, `subcontract_quote_currency`, `subcontract_quote_date`, `subcontractor_id`, `subcontract_subcontractor_code`, `subcontract_subcontractor_legal_name` |
| Removed tables | none |
| Slice A / FG-029 preservation | Project **19** `FG031-UAT-SCOPE-ROUTING` and project **14** `FG029-UAT-BMR-DEMO` remain |

## Canonical UAT vessel (DEMO / SYNTHETIC)

Authoritative close vessel is the last complete PASS run. Intermediate retry vessels **projects 20–24** / extra estimates from runner false-positive retries are the same labeled DEMO/SYNTHETIC name. They are not genuine Brayman job data. Do not delete them.

| Kind | Id | Identity |
|------|----|----------|
| Client | 20 | FG031B-UAT-SUBCONTRACT-QUOTES DEMO SYNTHETIC Client |
| Project | **25** | `FG031B-UAT-SUBCONTRACT-QUOTES` / `ORG-001` |
| Estimate | 23 | `EST-2026-0014` / FG031B-UAT-SUBCONTRACT-QUOTES DEMO SYNTHETIC |
| Draft version (quotes/costing/pricing) | **28** | Version 1; later **locked** after clone |
| Cloned version | **29** | `FG031B-UAT DEMO SYNTHETIC reconfirm quotes` |
| Issued refusal estimate | 24 | `EST-2026-0015` |
| Issued refusal version | **30** | status **Issued** / locked |
| Section | 26 | FG031B-UAT DEMO SYNTHETIC Scope |
| Line A complete subcontract | 101 | `SUBCONTRACTOR_SUPPLIED` + `SUBCONTRACT` (routing **94**) |
| Line B hybrid | 102 | `CONTRACTOR_PURCHASED` + `SUBCONTRACT` (routing **95**) |
| Line C labour-only | 103 | `NO_MATERIAL` + `SUBCONTRACT` (routing **96**) |
| Line D internal control | 104 | `CONTRACTOR_PURCHASED` + `INTERNAL` (routing **97**) |
| Line E allowance | 105 | `NO_MATERIAL` + `NO_LABOUR` (routing **98**) |
| Line F no-labour | 106 | `CONTRACTOR_PURCHASED` + `NO_LABOUR` (routing **99**) |
| Office user | 1 | Joel Brayman (ORG-001 membership) |
| Costing snapshot (first freeze) | **14** | later **SUPERSEDED** |
| Costing snapshot (recost CURRENT) | **15** | CURRENT after governed recost |
| Pricing snapshot | **10** | consumed snapshot **14**, then **STALE / REQUIRES RE-APPLY** |
| Draft customer Proposal | **10** | synthetic preview only; **not issued** |
| Supplier Package | **6** | DRAFT; cited lines = MR **28** (hybrid) only |
| Complete subcontract MR | 27 | excluded from Supplier Package |
| Hybrid MR | 28 | included under FG-029 CONTRACTOR_PURCHASED |
| DEMO supplier reused | 1 / location 1 | existing FG-029 `BMR-WINCHESTER-DEMO` / WINCHESTER |

### Subcontractors (ORG-001)

| Id | Code | Legal name |
|----|------|------------|
| 1 | FG031B-HVAC | FG031B HVAC DEMO SYNTHETIC Ltd. |
| 2 | FG031B-HVAC-2 | FG031B Alternate HVAC DEMO SYNTHETIC Inc. |
| 3 | FG031B-INSTALL | FG031B Install DEMO SYNTHETIC Ltd. |
| 4 | FG031B-LABOUR | FG031B Labour DEMO SYNTHETIC Ltd. |
| 5 | FG031B-ISSUED | FG031B Issued DEMO SYNTHETIC Ltd. |

Duplicate code `FG031B-HVAC` in the same organization **failed closed**. Subcontractor remains distinct from Supplier (supplier count stayed **1**).

### Quote evidence (canonical vessel)

| Id | Line | Version | Ref | Amount | Status |
|----|------|---------|-----|--------|--------|
| 42 | 101 | 28 | Q-FG031B-100 | 5000.00 CAD | **SUPERSEDED** |
| 43 | 101 | 28 | Q-FG031B-200 | 7000.00 CAD | **SELECTED** |
| 44 | 101 | 28 | Q-FG031B-300 | 8000.00 CAD | **REJECTED** |
| 45 | 102 | 28 | Q-FG031B-HYBRID | 350.00 CAD | **SELECTED** |
| 46 | 103 | 28 | Q-FG031B-LABOUR | 1100.00 CAD | **SELECTED** |
| 47–51 | 107–109 | 29 | copied refs | (same amounts) | **RECEIVED** (clone) |
| 52 | 113 | 30 | Q-ISSUE-1 | 10.00 CAD | **RECEIVED** (issued-refusal vessel) |

Actor on receive/select/reject: user **1** / `Joel Brayman`. No lowest-bid or AI selection.

## Required UAT results

| Case | Route / action | Expected | Actual | Result |
|------|----------------|----------|--------|--------|
| A. Navigation | `GET /projects/25` → PRICE → `GET /projects/25/scope-delivery` | Slice A routing review remains usable; quote panels only on subcontract-labour lines; no new lifecycle stage; CalibraytAI product identity; tenant chrome separate | Lifecycle PLAN/PRICE/CONTRACT/BUILD/MONITOR + LEARN · Future. Quote UI on lines A/B/C only (3 panels). Hub shows CalibraytAI lifecycle. Office chrome remains Brayman Construction Platform | **PASS** |
| Routing cases A–D | Explicit Confirm on Scope Delivery Review | Stored dimensions as specified; no HYBRID enum | Lines 101–104 / routing 94–97 CONFIRMED as specified. `HYBRID` count **0** | **PASS** |
| B. Subcontractor | Slice B create workflow + duplicate code POST | ORG-001; code + legal name stored; duplicate fails closed; not a Supplier | Ids 1–5 ORG-001 ACTIVE. Duplicate `FG031B-HVAC` refused. Supplier count unchanged (1) | **PASS** |
| C. Receive quotes | POST receive on line 101 | Status Received; facts persist; actor/time recorded; no line-cost, Pricing, or costing snapshot from receive | Quotes 42 then 43 received on line 101. `unit_cost` unchanged by receive. Costing count before first freeze remained **13**; pricing count **9** | **PASS** |
| D. Human selection | Select 42 then select 43 | Selected is visually distinct; actor/time recorded; prior SELECTED → SUPERSEDED; no delete; cost/Pricing unchanged | 42 SUPERSEDED (`selected_by=1`); 43 SELECTED (`selected_at` recorded). All three quote rows remain. No lowest-bid/AI | **PASS** |
| E. Rejection | Receive 44 then reject | Rejected stored; cannot select without a governed transition; no cost/Pricing mutation | 44 REJECTED; row retained; reject-to-select without transition refused | **PASS** |
| F. Eligibility | Receive on A/B/C vs D/F | Permit complete/hybrid/labour-only; fail closed INTERNAL and NO_LABOUR | Quotes 43/45/46 succeeded. INTERNAL line 104 and NO_LABOUR line 106 refused | **PASS** |
| G. Costing WARN + Approve All | Working cost ≠ selected 7000; Costing Review; Approve All Costing | `SUBCONTRACT_QUOTE_AMOUNT_DIFFERS` WARN not BLOCK; selected quote does not replace working cost; FG-027 remains authority | WARN present; Approve All Costing enabled/submitted; snapshot **14** created without overwriting working cost to 7000 | **PASS** |
| S. Frozen provenance | Snapshot 14 line 69 | Freeze evidence id/ref/amount/currency/date + subcontractor id/code/legal name | evidence **43** / `Q-FG031B-200` / `7000.00` / CAD / `2026-09-01` / subcontractor **2** / `FG031B-HVAC-2` / `FG031B Alternate HVAC DEMO SYNTHETIC Inc.` | **PASS** |
| T. Historical non-floating | Edit live quote after freeze; do not rewrite snapshot | Copied freeze facts unchanged | Snapshot 14 line 69 freeze facts unchanged after live quote mutation (live quote restored after the check) | **PASS** |
| H. Pricing boundary | Apply existing resolved pricing after costing; then select/quote vs recost | Quote selection never applies Pricing or recosts; pricing consumes approved costing; recost supersedes costing and stales Pricing | Snapshot **10** consumed costing **14**. Quote select after costing did not recost. Direct-cost edit + Approve All Costing superseded 14 → **15** and set Pricing **STALE / REQUIRES RE-APPLY** | **PASS** |
| I. Allowance | Line E NO_MATERIAL + NO_LABOUR, no selected quote | Allowance proceeds; no new selected-quote BLOCK | Line 105 `MANUAL_ALLOWANCE`; costing proceeded without a selected-quote BLOCK | **PASS** |
| J. Clone / reconfirm | Clone editable version | Routing + quotes copy to new line IDs; copied quotes RECEIVED; selection not carried; prior version unchanged | Version **29**; quotes **47–51** RECEIVED on lines **107–109**; prior 42–46 statuses unchanged | **PASS** |
| W. Locked / issued refusal | Receive/select/reject on version 30 Issued/locked | Fail closed; do not unlock historical records | Mutations refused on Issued version **30**. Quote **52** remains RECEIVED | **PASS** |
| X. Customer privacy | Draft Proposal HTML/PDF id **10** | No subcontractor identity/code, quote ref/amount/selection, routing enums, internal cost, margin/markup | HTTP **200**. No subcontractor identity/code, quote refs, routing enums, or quote-UI copy in customer output | **PASS** |
| Y. Supplier Package privacy/filter | Generate package on project 25 | Complete subcontract material excluded; hybrid contractor-purchased may remain; no subcontractor/quote leak | Package **6** DRAFT; lines = MR **28** only. Complete MR **27** excluded. No subcontractor/quote leak in HTML/PDF | **PASS** |
| Z. Tenant isolation / rollback | Cross-org GET/POST + service mismatch | Other org cannot read/mutate ORG-001 subcontractors or quotes; submitted IDs fail closed; rollback | Cross-org project **4** → HTTP **404**. Service mismatch left no CROSS residue | **PASS** |
| AA. PLAN / catalogue preservation | Count + schema check | No subcontract-routing ownership on PLAN/catalogue/`EstimateLineItem` | Takeoff 1/3/16; CostItem 10; Assembly 2; AssemblyItem 1; CanonicalMaterial 27 unchanged. Quote attached to estimating line + scope-delivery only | **PASS** |

## Cost / Pricing non-mutation (quote receive/select/reject)

Receive, select, supersede, and reject on version 28 did **not** create a costing or pricing snapshot. First costing snapshot **14** appeared only after explicit Approve All Costing. Pricing snapshot **10** appeared only after the existing resolved pricing workflow. Quote selection after costing did not recost and did not stale Pricing. Later governed recost (direct-cost edit + Approve All Costing) superseded costing **14** → **15** and set Pricing stale through the existing costing/direct-cost boundary.

Working line A `unit_cost` after recost is **9100** (selected quote remains **7000**). The selected quote did not replace working cost.

## Before / after counts (live DB)

Counts after migrate / before canonical vessel vs after canonical UAT:

| Table | After migrate / before vessel | After UAT |
|-------|-------------------------------|-----------|
| sqlite tables | 89 | 89 |
| projects | 24 | 25 |
| estimates | 22 | 24 |
| estimate_versions | 27 | 30 |
| estimate_line_items | 100 | 113 |
| estimate_scope_deliveries | 93 | 106 |
| estimate_costing_snapshots | 13 | 15 |
| estimate_costing_snapshot_lines | 68 | 80 |
| estimate_pricing_snapshots | 9 | 10 |
| material_requirements | 26 | 28 |
| supplier_packages | 5 | 6 |
| supplier_package_lines | 8 | 9 |
| takeoff_packages | 1 | 1 |
| takeoff_package_items | 3 | 3 |
| takeoff_candidates | 16 | 16 |
| cost_items | 10 | 10 |
| assemblies | 2 | 2 |
| assembly_items | 1 | 1 |
| canonical_materials | 27 | 27 |
| clients | 19 | 20 |
| suppliers | 1 | 1 |
| subcontractors | 5 | 5 |
| subcontract_quote_evidence | 41 | 52 |

New commercial rows are labeled FG031B-UAT / DEMO / SYNTHETIC. Existing FG-029 and FG-031 Slice A UAT evidence is preserved.

## Tests (this UAT session)

Focused:

```text
./venv/bin/python -m pytest -q tests/test_subcontract_quote_fg031.py tests/test_scope_delivery_fg031.py tests/test_estimate_costing_fg027.py tests/test_supplier_workflow_fg029.py
```

**83 passed**, 454 warnings, **15.24s** (21 + 26 + 20 + 16).

Full suite:

```text
./venv/bin/python -m pytest -q
```

**728 passed**, 2173 warnings, **373.17s** (0:06:13).

No product-code correction. Runner-only false positives (approve-button matcher; unscoped quote lookup; UAT project-name `SUBCONTRACT` / line-note `NO_LABOUR` in customer leak list; dashboard CalibraytAI chrome) were not product defects.

## Boundaries not expanded

- Subcontract RFQ/package HTML/PDF: **NOT IMPLEMENTED**
- Subcontractor portal: **NOT IMPLEMENTED**
- FG-030: **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**
- ADR-008: remains **Proposed**
- V1 scoring: remains **55% / 3 of 11**
- BMR DEMO READY: remains **NO**
- BRAYMAN REAL-LIFE UAT READY: remains **NO**
- FG-031 overall: **NOT CLOSED**

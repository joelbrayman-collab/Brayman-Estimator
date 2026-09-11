# FG-032 Slices A+B live migrate + bounded office UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated. Bounded DEMO/SYNTHETIC office UAT **PASS**. Slices A+B **OPERATIONAL FOR UAT**. Slice C **NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **OVERALL NOT CLOSED**. |
| Date | 2026-09-11 |
| Gate | [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) |
| Product SHA | `70e571140e12377aa5bd009b598530576401113b` |
| Start pin SHA | `520eeca7410e1a575f46a0bb8ed8126ea0d26445` |
| Actor | Joel Brayman — FG032-UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Authenticated Flask `test_client` against live office PRICE / QuickBooks-ready entry / Proposal / Supplier Package routes. Session `_user_id` = `"1"` (Joel Brayman). Gitignored runners `instance/fg032_uat_office.py` and `instance/fg032_uat_office_continue.py` (not committed). |

This file records Slices A+B live-migration and UAT facts only. It does **not** implement Slice C, live QuickBooks API, CSV/IIF, FG-030, or V1-04. It does **not** close FG-032.

**Subsequent status (2026-09-11 Slice C atomic ENTERED repair):** Unique occupancy **`f1a2b3c4d5e6`** was added after **`f0a1b2c3d4e5`**. Slice C was **not** live-migrated. Slice C office UAT was **not** run. The A+B evidence in this file remains historical and unchanged. Live current remains **`e9f0a1b2c3d4`**.

**Subsequent status (2026-09-11 Slice C implementation):** Slice C was later **IMPLEMENTED / TESTED / COMMITTED / PUSHED** in the repository (`f0a1b2c3d4e5`). Slice C was **not** live-migrated. Slice C office UAT was **not** run. The A+B evidence in this file remains historical and unchanged. Live current remains **`e9f0a1b2c3d4`**.

## Migration

| Field | Value |
|-------|--------|
| Live SQLite | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` (`sqlite:///brayman_estimator.db` → Flask instance path) |
| Pre-migration live current | `d8e9f0a1b2c3` |
| Repository head | `e9f0a1b2c3d4` |
| Backup | `instance/brayman_estimator-backup-before-fg032-e9f0a1b2c3d4-20260911-063529.db` (gitignored; not committed) |
| Backup size | 1,986,560 bytes (matches live source at backup time) |
| Backup SHA-256 | `a4634e3587c8e5065781cbc9975587a485d94113aa2c8fa0ae750c4ce3d8cd6d` |
| Backup Alembic | `d8e9f0a1b2c3` (QB tables absent; 89 sqlite tables) |
| Command | `./venv/bin/flask db upgrade e9f0a1b2c3d4` |
| Post-migration live current | `e9f0a1b2c3d4 (head)` |
| Post-migration repository head | `e9f0a1b2c3d4 (head)` |
| Graph heads | one |
| Added tables | `estimate_quickbooks_packages`, `estimate_quickbooks_sales_lines`, `estimate_quickbooks_cost_class_lines` (89 → 92 tables) |
| Removed tables | none |
| Slice C table | `estimate_quickbooks_entry_events` **absent** |
| Prior UAT preservation | Project **14** `FG029-UAT-BMR-DEMO`, project **19** `FG031-UAT-SCOPE-ROUTING`, and project **25** `FG031B-UAT-SUBCONTRACT-QUOTES` remain |

## Canonical UAT vessel (DEMO / SYNTHETIC)

| Kind | Id | Identity |
|------|----|----------|
| Client | 21 | FG032-UAT-QB-ENTRY DEMO SYNTHETIC Client |
| Project | **26** | `FG032-UAT-QB-ENTRY` / `ORG-001` / `FG032-UAT-001` |
| Cost item | 11 | `MAT-FG032-UAT` / FG032-UAT DEMO SYNTHETIC Material |
| Issued estimate | 25 | `EST-2026-0016` |
| Issued version | **31** | Version 1 |
| Issued Proposal | **11** | status **Issued** (editable; ADR-002 does not freeze Issued) |
| Issued QB package | **1** | `QB-2026-0001` **ISSUED** |
| Accepted estimate | 26 | `EST-2026-0017` |
| Accepted version | **32** | Version 1 |
| Accepted Proposal | **12** | status **Accepted** |
| Accepted QB package | **2** | `QB-2026-0002` **ISSUED** |
| Stale estimate | 27 | `EST-2026-0018` |
| Stale version | **33** | Version 1; recost after review |
| Stale Proposal | **13** | status **Accepted** |
| Stale QB package | **3** | `QB-2026-0003` **REVIEWED** (issue refused after recost) |
| Office user | 1 | Joel Brayman (ORG-001 membership) |
| Costing snapshot (Issued vessel) | **16** | CURRENT at package freeze |
| Pricing snapshot (Issued vessel) | **11** | consume CURRENT at package freeze |
| Costing snapshot (Accepted vessel) | **17** | |
| Pricing snapshot (Accepted vessel) | **12** | |

New commercial rows are labeled FG032-UAT / DEMO / SYNTHETIC. They are not genuine Brayman job data.

## Required UAT results

| Case | Route / action | Expected | Actual | Result |
|------|----------------|----------|--------|--------|
| Issued eligibility | assemble preview version **31** | Eligible; `PROPOSAL_ISSUED_NOT_ACCEPTED` WARN; CURRENT pricing | eligible True; warnings include Issued/hybrid/Allowance; consume CURRENT | **PASS** |
| Issued reconciliation | package vs pricing vs Proposal | Exact CAD match; project number from Project; unit rate from `ProposalLineItem.unit_price` | pre-tax **235.29** / tax **30.59** / total **265.88**; sales and cost-class sums match | **PASS** |
| Accepted eligibility | assemble preview version **32** | Eligible without Issued WARN | eligible True; warnings `MISSING_PRODUCT_SERVICE_MAPPING` only | **PASS** |
| Review-before-issue | `issue_package` on DRAFT | `NOT_REVIEWED` BLOCK | block `NOT_REVIEWED` | **PASS** |
| Hub PRICE | `GET /projects/26` | QuickBooks-ready entry link | HTTP **200**; link present | **PASS** |
| Review HTML | `GET /projects/26/quickbooks-entry?version_id=31` | INTERNAL ENTRY REFERENCE + cost-class companion; no Entered button | HTTP **200**; both labels; `Entered in QuickBooks` absent | **PASS** |
| Isolation | `GET /projects/4/quickbooks-entry` | Cross-org 404 | HTTP **404** | **PASS** |
| Review POST | `POST .../quickbooks-entry/review` | REVIEWED | package **1** REVIEWED then issued | **PASS** |
| Issue POST | `POST .../quickbooks-entry/issue` | ISSUED + SHA-256 | package **1** ISSUED; sales SHA `9f70a5df…248b1c`; cost SHA `9571797d…948401` | **PASS** |
| Downloads | sales.pdf and cost-class.pdf | Separate private PDFs; download ≠ entry | HTTP **200** both; distinct bytes; status remained ISSUED | **PASS** |
| Artifact A privacy | sales PDF / frozen sales text | No cost-class label; no routing enums | INTERNAL ENTRY REFERENCE present; `PLANNED COST-CLASSIFICATION` absent | **PASS** |
| Artifact B privacy | cost-class PDF / frozen cost text | Companion only; not a second sales sheet | cost-class label present; INTERNAL ENTRY REFERENCE absent | **PASS** |
| Proposal HTML/PDF | `/proposals/11/preview` and `/pdf` | No FG-032 private labels | HTTP **200**; labels absent | **PASS** |
| Supplier Package | `GET /projects/14/supplier-package` | Unchanged; no FG-032 private labels | HTTP **200**; labels absent | **PASS** |
| Non-float | Edit Issued Proposal **11** after issue | Package totals/hashes/PDF unchanged | total remained **265.88**; SHAs unchanged; edited intro absent from frozen PDF | **PASS** |
| Accepted issue | review + issue version **32** | ISSUED without Issued WARN | package **2** `QB-2026-0002` ISSUED | **PASS** |
| Unissued STALE | recost version **33** then issue package **3** | BLOCK | consume `STALE / REQUIRES RE-APPLY`; codes `PRICING_NOT_CURRENT` + `PRICING_COSTING_IDENTITY_MISMATCH` | **PASS** |
| Hybrid once | cost-class lines on Issued preview | One extended cost; both routing dimensions | one hybrid line **100.00** | **PASS** |
| Slice C | schema + UI | No entry-events table; no Entered button | table absent; button absent | **PASS** |

Local PDF copies (gitignored): `instance/fg032-uat-sales.pdf` (3202 bytes), `instance/fg032-uat-cost-class.pdf` (3001 bytes).

## Before / after counts (live DB)

After migrate / before vessel vs after canonical UAT:

| Table | After migrate / before vessel | After UAT |
|-------|-------------------------------|-----------|
| sqlite tables | 92 | 92 |
| projects | 25 | 26 |
| estimates | 24 | 27 |
| proposals | 10 | 13 |
| estimate_quickbooks_packages | 0 | 3 |
| cost_items | 10 | 11 |
| suppliers | 1 | 1 |
| subcontractors | (unchanged) | unchanged |
| canonical_materials | 27 | 27 |
| takeoff_packages | 1 | 1 |

## Tests (this UAT session)

Focused after live migrate:

```text
./venv/bin/python -m pytest -q tests/test_quickbooks_ready_fg032.py
```

**23 passed**, 306 warnings, **12.96s**.

Full suite:

```text
./venv/bin/python -m pytest -q
```

**751 passed**, 2479 warnings, **329.14s** (0:05:29).

No product-code correction.

## Boundaries not expanded

- Slice C ENTERED/REVERSED events: **NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**
- Live QuickBooks API / OAuth / SDK: **POST-V1 / NOT AUTHORIZED**
- CSV / IIF / Excel: **NOT CLAIMED**
- FG-030: **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**
- ADR-008: remains **Proposed**
- V1 scoring: remains **55% / 3 of 11**
- V1-04: remains **PARTIAL / CURRENT SCORED PACKAGE**
- V1-05: remains **PARTIAL**
- BMR DEMO READY: remains **NO**
- BRAYMAN REAL-LIFE UAT READY: remains **NO**
- FG-032 overall: **NOT CLOSED**

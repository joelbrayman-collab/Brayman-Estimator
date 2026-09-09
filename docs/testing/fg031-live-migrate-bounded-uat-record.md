# FG-031 Slice A live migrate + bounded office UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated. Bounded DEMO/SYNTHETIC office UAT **PASS**. Slice A **OPERATIONAL FOR UAT**. FG-031 **OVERALL NOT CLOSED** (Slice B not implemented). |
| Date | 2026-09-09 |
| Gate | [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) |
| Product SHA | `54120608df98432b9be80faf8c2a3a08cdb5679c` |
| Confirmation-gate repair SHA | `ec8dcf35f0da109b75422504e1a104c1623d186c` |
| Start pin SHA | `bbe22f2a10ba9ba827e50c92688774a025b95d34` |
| Actor | Joel Brayman — FG031-UAT |
| Organization | ORG-001 / Brayman Construction Inc. |

This file records live-migration and UAT facts only. It does not implement Slice B, FG-030, or V1-04.

## Migration

| Field | Value |
|-------|--------|
| Pre-migration live current | `b6c7d8e9f0a1` |
| Repository head | `c7d8e9f0a1b2` |
| Backup | `instance/brayman_estimator-backup-before-fg031-c7d8e9f0a1b2.db` (gitignored) |
| Backup size | 1,806,336 bytes |
| Backup SHA-256 | `f2dec3fd0010f67398a908c065a6f273a7c8b3ed7b37280d1113ed16f3b3987b` |
| Backup Alembic | `b6c7d8e9f0a1` (no `estimate_scope_deliveries`) |
| Command | `./venv/bin/flask db upgrade c7d8e9f0a1b2` |
| Post-migration live current | `c7d8e9f0a1b2 (head)` |
| Post-migration repository head | `c7d8e9f0a1b2 (head)` |
| Graph heads | one |
| Added tables | `estimate_scope_deliveries` only (86 → 87 tables) |
| Added columns | `estimate_costing_snapshot_lines.material_procurement`, `labour_delivery` (nullable) |
| Removed tables | none |
| Slice B tables | still absent (`subcontractors`, `subcontract_quote_evidence`) |

## Canonical UAT vessel (DEMO / SYNTHETIC)

Authoritative close vessel is the last complete PASS run.

| Kind | Id | Identity |
|------|----|----------|
| Client | 14 | FG031-UAT-SCOPE-ROUTING DEMO SYNTHETIC Client |
| Project | 19 | `FG031-UAT-SCOPE-ROUTING` / `ORG-001` |
| Estimate | 14 | `EST-2026-0005` / FG031-UAT-SCOPE-ROUTING DEMO SYNTHETIC |
| Draft version (routing/costing) | 15 | Version 1 |
| Cloned version | 16 | `FG031-UAT DEMO SYNTHETIC reconfirm` |
| Section | 13 | FG031-UAT DEMO SYNTHETIC Scope |
| Line A | 38 | contractor-purchased lumber + internal labour |
| Line B | 39 | HVAC-like subcontractor-supplied + subcontract labour |
| Line C | 40 | contractor-purchased + subcontract labour (derived Hybrid) |
| Line D | 41 | legitimate Allowance / NO_MATERIAL + NO_LABOUR |
| Line E | 42 | initially unresolved |
| Line F | 43 | reserved OWNER_SUPPLIED via service setup (hidden first-slice UI) |
| Office user | 1 | Joel Brayman (ORG-001 membership) |
| Costing snapshot | 7 | CURRENT freeze of routing dimensions |
| Supplier Package | 4 | DRAFT; not issued |
| Cited eligible MR | 18 | ESTIMATE_LINE_CITE → line A; CONFIRMED CONTRACTOR_PURCHASED |
| Excluded MRs | 19–24 | subcontractor-supplied, Allowance/NO_MATERIAL, OWNER_SUPPLIED, uncited MANUAL, uncited DEMO, unresolved cite |
| Draft customer Proposal | 6 | `PROP-2026-0001` status **Draft** — synthetic preview only; **not issued** |
| DEMO supplier reused | 1 / location 1 | existing FG-029 `BMR-WINCHESTER-DEMO` / WINCHESTER |

Intermediate retry vessels **projects 15–18** / estimates `EST-2026-0001`–`EST-2026-0004` are the same labeled DEMO/SYNTHETIC name from UAT-runner retries. They are not genuine Brayman job data.

## Required UAT results

| Case | Result |
|------|--------|
| Scope Delivery Review headings / first-slice choices | **PASS** |
| Reserved OWNER_SUPPLIED / OWNER_THIRD_PARTY hidden until stored | **PASS** |
| No raw enum leakage in contractor-facing labels | **PASS** (HTML option values remain internal form posts) |
| No new lifecycle stage | **PASS** (PLAN/PRICE/CONTRACT/BUILD/MONITOR + existing LEARN · Future) |
| No-routing / unconfirmed costing BLOCK | **PASS** (`SCOPE_DELIVERY_UNRESOLVED`; Approve All Costing refused; direct POST fail-closed; no snapshot/pricing) |
| Resolved PROPOSED still BLOCKS costing | **PASS** (human-confirmation gate) |
| Per-row Confirm | **PASS** (`CONFIRMED`, `confirmed_by=1`, `confirmed_at`, actor `Joel Brayman`) |
| Approve All Scope Routing | **PASS** (eligible PROPOSED → CONFIRMED; unresolved E skipped) |
| Unresolved remains fail-closed | **PASS** |
| Allowance exception | **PASS** (no `SCOPE_DELIVERY_UNRESOLVED`; `MANUAL_ALLOWANCE` WARN) |
| FG-027 block cleared after all required CONFIRMED | **PASS**; Approve All Costing created snapshot **id 7** |
| Snapshot routing freeze | **PASS** (historical lines did not float after working Draft edit) |
| INTERNAL labour non-creation | **PASS** (`labour_tasks` 2 unchanged; no labour snapshot; `LABOUR_EVIDENCE_ABSENT` WARN; `include_labour_snapshot_direct_cost=False`) |
| Subcontract Slice A boundary | **PASS** (routing stored/confirmed; no Subcontractor / quote / RFQ / portal tables) |
| Hybrid display | **PASS** (derived `Hybrid` for line C; no stored HYBRID enum) |
| MaterialRequirement not auto-created by routing | **PASS** |
| CONTRACTOR_PURCHASED package inclusion | **PASS** (package 4 lines = MR 18 only) |
| SUBCONTRACTOR_SUPPLIED HVAC-like exclusion | **PASS** |
| Other route exclusions | **PASS** (NO_MATERIAL, OWNER_SUPPLIED, unresolved cite) |
| Uncited MANUAL/DEMO fail-closed | **PASS** |
| Supplier price INFORM ONLY | **PASS** (EstimateLineItem / costing / pricing counts not mutated by package; ADR-008 remains Proposed) |
| Supplier Package issuance | **NOT RUN** — DRAFT filter proved the Slice A boundary; issuing a new package was unnecessary |
| PLAN preservation | **PASS** (TakeoffPackage 1 / items 3 / candidates 16; FG-026 insertions 1 / citations 3 unchanged; no routing columns on PLAN) |
| Catalogue preservation | **PASS** (CostItem 10 / Assembly 2 / CanonicalMaterial 27; no routing columns) |
| Clone / reconfirmation | **PASS** (version 16; copied rows point at new line IDs; resolved status PROPOSED; confirmation cleared; costing blocked until human reconfirm of line 44) |
| Customer-output privacy | **PASS** — Draft proposal preview only; not issued |
| Pricing non-mutation | **PASS** (`estimate_pricing_snapshots` remained **6** through routing confirm / Approve All Scope Routing / costing / package) |
| Tenant isolation | **PASS** (ORG-001 GET/POST `/projects/4/scope-delivery` HTTP **404**) |
| UI QA | **PASS** on authenticated office HTML from live product routes. Interactive browser sessions on ports 5015/5016 were expired (login gate shown; tenant Brayman Construction chrome intact). Viewport meta present. No unrelated PRICE redesign. |

## Before / after counts (live DB)

| Table | Before migrate | After UAT |
|-------|----------------|-----------|
| projects | 14 | 19 |
| estimates | 9 | 14 |
| estimate_versions | 9 | 16 |
| estimate_line_items | 7 | 49 |
| estimate_scope_deliveries | TABLE_ABSENT | 42 |
| estimate_costing_snapshots | 2 | 7 |
| estimate_costing_snapshot_lines | 2 | 32 |
| estimate_pricing_snapshots | 6 | 6 |
| estimate_labour_snapshots | 0 | 0 |
| material_requirements | 3 | 24 |
| supplier_packages | 1 | 4 |
| supplier_package_lines | 3 | 7 |
| labour_tasks | 2 | 2 |
| production_rate_standards | 1 | 1 |
| direct_labour_cost_rate_standards | 1 | 1 |
| takeoff_packages | 1 | 1 |
| takeoff_package_items | 3 | 3 |
| takeoff_candidates | 16 | 16 |
| cost_items | 10 | 10 |
| assemblies | 2 | 2 |
| assembly_items | 1 | 1 |
| canonical_materials | 27 | 27 |
| clients | 9 | 14 |
| proposals | 5 | 6 |
| sqlite tables | 86 | 87 |

New commercial rows are labeled FG031-UAT / DEMO / SYNTHETIC. No unexplained genuine Brayman estimate mutations. Existing FG-029 issued package **id 1** and PLAN/catalogue counts are unchanged except additive FG-031 synthetic rows.

## Tests

**NOT RERUN** this session (UAT revealed no product defect).

Historical FG-031 confirmation-gate repair evidence: dedicated **26 passed**; FG-027 **20 passed**; FG-029 **16 passed**; governed bundle **258 passed**; full suite **707 passed**.

## Boundaries not expanded

- Slice B Subcontractor / quote / RFQ / portal: **NOT IMPLEMENTED**
- FG-030: **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**
- ADR-008: remains **Proposed**
- V1 scoring: remains **55% / 3 of 11**
- BMR DEMO READY: remains **NO** (Ontario/fail-closed contract story still missing)
- BRAYMAN REAL-LIFE UAT READY: remains **NO** (Slice B still required)

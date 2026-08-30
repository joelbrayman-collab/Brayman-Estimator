# Chat Workflow Log — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Continuity log (append-only) |
| Updated | 2026-08-30 |

## Purpose

Memorializes important ChatGPT / Cursor work. This is **not** a verbatim transcript. It is the authoritative decision and implementation summary for recovery without chat history.

**Do not overwrite past entries.** Append new entries at the top of the Entries section (newest first).

## Entry template (copy for each sprint)

```markdown
### YYYY-MM-DD — <short title>

| Field | Content |
|-------|---------|
| Date | |
| Branch | |
| Objective | |
| Business decision | |
| Architectural decision | |
| Prompt template used | |
| Approved Cursor prompt summary | |
| Files expected to change | |
| Files prohibited from changing | |
| Implementation result | |
| Tests | command(s) + exact result |
| Project-state-report update | |
| Milestone entry update | |
| Constitutional issue raised | |
| Unresolved issues | |
| Next approved step | |
| Next approved prompt | |
| Commit hash | (when available) |
```

---

## Entries

### 2026-08-30 — FG-014 catalogue-link flash repair

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `3e671f20a561b4c70bc837486f59f93a150f7fee` (repair start; permit pin `5931696` committed first) |
| Objective | Repair only the FG-014 catalogue-link flash/message defect. Do not broaden Material Catalogue architecture. |
| Business decision | Improper catalogue link must fail closed **and** tell the caller the service reason. Empty select may still say `Select a Material cost item to link.` |
| Architectural decision | `MaterialCatalogueError` subclasses `ValueError`. Catch it before `(TypeError, ValueError)` in `link_cost_item`. Unlink already used the correct order. No schema, identity, CostItem ownership, supplier, Phase D, or Permit Intelligence change. |
| Prompt template used | [cursor-bugfix-template.md](prompts/cursor-bugfix-template.md) |
| Approved Cursor prompt summary | FG-014 CATALOGUE-LINK FLASH REPAIR. Reproduce, smallest root cause, repair flash only, add regression test, run dedicated/regression/full suite, reconcile FG-014 docs, commit and push. Permit pin remains FUTURE. Then STOP. |
| Files expected to change | `app/routes/material_catalogue.py` · `tests/test_material_catalogue_fg014.py` · FG-014 / status docs |
| Files prohibited from changing | migrations · canonical identity model · CostItem ownership · supplier/Phase D/Permit Intelligence · ADR-008 |
| Implementation result | Exception order repaired. Dedicated **35 passed**. Full suite **345 passed**. Live POST on 5006 flashed the Labour service reason. FG-014 not closed (office re-UAT remaining). |
| Tests | `./venv/bin/python -m pytest -q tests/test_material_catalogue_fg014.py` → **35 passed**. Assemblies/estimates/estimate_builder **29 passed**. Full suite **345 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes — architecture record (non-milestone) |
| Constitutional issue raised | None |
| Unresolved issues | Short office re-UAT of catalogue-link error flashes before FG-014 close. |
| Next approved step | **FG-014 office re-UAT of catalogue-link flashes, then close**. |
| Next approved prompt | Office re-UAT / gate-close prompt. Do not implement Permit Intelligence. |
| Commit hash | (this repair commit) |

### 2026-08-30 — FUTURE pin: Project Permit & Approvals Report

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `3e671f20a561b4c70bc837486f59f93a150f7fee` |
| Objective | Architecture requirement pin only. Record a governed advisory PROJECT PERMIT & APPROVALS REPORT as FUTURE / NOT IMPLEMENTED. Do not interrupt FG-014 live-migration/UAT. |
| Business decision | CalibAi must eventually generate an early-lifecycle permit/zoning/servicing preflight from address/jurisdiction + site/property + project type + plans/site plan + current governing municipal/provincial/state requirements, so issues can affect feasibility, scope, pricing, and contracting. The report is advisory. It does not replace the AHJ, building official, planner, surveyor, engineer, septic authority, conservation authority, attorney, or other regulated professionals. FINAL AUTHORITY remains the governing AHJ. |
| Architectural decision | Additional governed project document (not estimate outputs 1–4). Retain with project documents; tie to project, address/jurisdiction, plan version, site-plan version, governing-rule source/version/effective date, generation date, evidence/provenance. Later plan or by-law changes must not silently rewrite an earlier report. Freshness: CURRENT RULE LOOKUP → CITED / VERSIONED PERMIT ANALYSIS → PROJECT REPORT SNAPSHOT → IMMUTABLE HISTORY. Re-check when plans, site plan, scope, address/jurisdiction, or governing requirements change. Status vocabulary (PASS / VERIFY / POTENTIAL NON-CONFORMANCE / ADDITIONAL APPROVAL LIKELY / MISSING INFORMATION / NOT APPLICABLE) is conceptual only — not product enums. Mike Pratt Coach House at 2562 Church Street, North Gower, Ontario is a future architecture/UAT reference; preliminary ChatGPT research is not an authoritative permit determination. Separate repository-first reconnaissance required before implementation. |
| Prompt template used | [cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | ARCHITECTURE REQUIREMENT PIN ONLY. Record Permit & Approvals Report as FUTURE / NOT IMPLEMENTED. Do not authorize Permit Intelligence, legal-library, live regulatory AI, web lookup, automatic approval conclusions, municipal submissions, schema, migration, ADR, or a Feature Gate. Continue FG-014 unchanged. |
| Files expected to change | `docs/` architecture pin + indexes + status/handoff/log/milestones + UAT reference + legal-content distinction. |
| Files prohibited from changing | `app/` · `tests/` · `migrations/` · FG-014 Feature Gate status · any ADR · new Feature Gate |
| Implementation result | Canonical pin created. FG-014 status unchanged (**LIVE-MIGRATED / UAT DEFECT — CLOSURE BLOCKED**). Next coded work remains catalogue-link flash repair + re-UAT. |
| Tests | Docs-only; `git diff --check`. Full suite not re-run this pass. Last recorded full suite **338 passed** (FG-014 live-migrate/UAT). |
| Project-state-report update | Yes — future pin noted; next approved remains FG-014 defect repair. |
| Milestone entry update | Yes — architecture record (non-milestone). |
| Constitutional issue raised | None. Pin does not invent municipal law. |
| Unresolved issues | FG-014 catalogue-link flash defect unrepaired. Permit capability requires later reconnaissance before any Feature Gate. |
| Next approved step | **FG-014 catalogue-link flash repair + re-UAT**. |
| Next approved prompt | FG-014 UAT defect repair (`link_cost_item` exception order). Do not implement Permit Intelligence. |
| Commit hash | (pending docs commit) |

### 2026-08-30 — FG-014 live migration applied; office UAT closure blocked

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `a100caa2c1f5e1c29e79449c8ce5a144ff945f23` (start) |
| Objective | Apply `d6e7f8a9b0c1` to the live development/UAT DB. Bounded office Material Catalogue UAT. Docs only unless a product defect is found. |
| Business decision | Live migrate authorized. Do not repair product defects under this prompt. Do not close FG-014 if UAT finds a product-code defect. |
| Architectural decision | Canonical identity remains platform-shared. CostItem remains org costing. ADR-008 remains Proposed. Supplier onboarding pin unchanged (FUTURE). |
| Prompt template used | Bounded FG-014 live migration + office UAT |
| Approved Cursor prompt summary | Apply only `c5d6e7f8a9b0` → `d6e7f8a9b0c1`. Browser UAT `/material-catalogue/`. Do not modify product code unless a defect is found — if so, STOP and do not repair. |
| Files expected to change | Governed docs only (on success). Product code prohibited unless defect (then stop). |
| Files prohibited from changing | Product repair; new migrations; ADR-008 status; supplier schema |
| Implementation result | Migration **applied**. Live current = head = `d6e7f8a9b0c1`. Seed 27 rows. Catalogue list/search/filter/detail, Material link/unlink, org isolation GET 404, assembly read-through, Cost Library canonical column: **passed**. **UAT DEFECT:** catalogue `POST .../link` for non-Material and cross-org IDs flashes `Select a Material cost item to link.` instead of the service reason. Data remain unlinked. Closure **blocked**. Product code **not** changed. |
| Tests | Dedicated FG-014 **28 passed**. Relevant regressions **278 passed**. Full suite **338 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | FG-014 **not closed**. Catalogue link exception-order flash defect. Seed has no DISCONTINUED rows (filter empty; service tests cover new-link block). |
| Next approved step | **Bounded product-defect repair** for `app/routes/material_catalogue.py` `link_cost_item` exception order, then re-UAT the fail-closed flashes. Do **not** re-run `flask db upgrade`. Do not start supplier onboarding. |
| Next approved prompt | FG-014 UAT defect repair (catalogue link flash). Do not accept ADR-008. Do not start Phase D or supplier ingest. |
| Commit hash | (this commit) |

### 2026-08-30 — FG-014 Material Catalogue V1 implemented

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `273803b75b6bcbe6ae56fbf3274cd4a2dafcec36` (start) |
| Objective | Implement FG-014 identity V1. One additive migration. Do not live-migrate. |
| Business decision | Platform-owned lumber/sheet seed. Optional Material CostItem link. Read-only canonical UX. |
| Architectural decision | `canonical_materials` is platform-shared. CostItem remains org costing. ADR-008 remains Proposed. No supplier schema. |
| Prompt template used | Bounded FG-014 product implementation |
| Approved Cursor prompt summary | IMPLEMENT FG-014. One additive Alembic revision. Do not apply to live development/UAT DB. |
| Files expected to change | models, services, routes, templates, migration, tests, governed docs |
| Files prohibited from changing | TakeoffPackageItem; Assembly schema FK; ADR-008 status; live DB |
| Implementation result | Identity + seed (27 rows) + CostItem FK + `/material-catalogue/`. Graph head `d6e7f8a9b0c1`. Live current `c5d6e7f8a9b0`. |
| Tests | Dedicated FG-014 **28 passed**. Full suite **338 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate and office UAT not done. ADR-008 remains Proposed. |
| Next approved step | **FG-014 live-migrate + office UAT** when Joel authorizes. |
| Next approved prompt | Bounded live-migrate + UAT. Do not start supplier ingest. |
| Commit hash | `976cc4a4942ae346b9843a77126f89969bba2b6e` |

### 2026-08-30 — FG-014 Material Catalogue V1 Feature Gate + future supplier-onboarding pin

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `130b3fd35114014f0635d9a70e7cb3096647d480` (start) |
| Objective | Documentation-only Feature Gate for Material Catalogue V1. Pin future bulk supplier onboarding. Do not implement either. |
| Business decision | Joel: approve FG-014 identity-only lumber/sheets. Suppliers must later onboard by governed bulk ingest (not one-product-at-a-time); INITIAL mapping vs ONGOING sync. That pin is FUTURE ONLY and does not expand V1. |
| Architectural decision | FG-014 **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**. Owner: Material Catalogue (identity); Estimating (CostItem). Seed in the same additive Alembic revision as the table (implementation prompt). Ordinary org users must not mutate platform identity. ADR-008 remains Proposed. No Supplier Feature Gate. |
| Prompt template used | Bounded Material Catalogue V1 Feature Gate governance + future supplier-onboarding pin |
| Approved Cursor prompt summary | FEATURE GATE GOVERNANCE / DOCUMENTATION ONLY. Create FG-014. Do not implement. Do not migrate. Do not accept ADR-008. Record bulk supplier onboarding as FUTURE / NOT IMPLEMENTED without expanding V1. |
| Files expected to change | Feature Gate, indexes, architecture/module/status docs |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; ADR-008 status |
| Implementation result | FG-014 approved, not started. Bulk supplier onboarding pinned in supplier architecture. No product code. |
| Tests | Not rerun (docs-only). Last recorded full suite **310 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | Implementation not started. ADR-008 remains Proposed. Supplier Feature Gate not authorized. |
| Next approved step | **FG-014 implementation prompt** when Joel authorizes. Do not implement after this docs commit. |
| Next approved prompt | Bounded FG-014 implementation (identity + seed + CostItem FK + office UX). Do not start supplier ingest. |
| Commit hash | (this commit) |

### 2026-08-30 — Material Catalogue ADR-034 / ADR-035 / ADR-036 accepted

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `b53d9e7150e43b173bad3c26eee8e829529773e5` (start) |
| Objective | Accept three Material Catalogue ADRs. Do not create a Feature Gate. Do not accept ADR-008. |
| Business decision | Joel: CalibAi-seeded identity; UOM vs pack; living evidence classes; promotions as effective-dated facts; identity V1 before Phase D. |
| Architectural decision | ADR-034 / ADR-035 / ADR-036 **Accepted**. ADR-008 remains **Proposed**. MaterialRequirement and Phase D not authorized. |
| Prompt template used | Bounded Material Catalogue ADR governance |
| Approved Cursor prompt summary | DOCUMENTATION / ADR GOVERNANCE ONLY. Create exactly three ADRs. Do not implement. Do not create a Feature Gate. Do not accept ADR-008. |
| Files expected to change | Three ADRs; indexes; architecture cross-refs; status docs |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; Feature Gates; ADR-008 status |
| Implementation result | ADR-034, ADR-035, ADR-036 Accepted. No Feature Gate. |
| Tests | Not rerun (docs-only). Last recorded full suite **310 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | Feature Gate not opened. ADR-008 remains Proposed. |
| Next approved step | **Material Catalogue Feature Gate** (docs) when Joel authorizes. Do not implement until that gate is approved. |
| Next approved prompt | Material Catalogue V1 Feature Gate (identity-only lumber/sheets). Do not accept ADR-008. |
| Commit hash | (this commit) |

### 2026-08-30 — Material Catalogue architecture governance

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `450cd39dea24c3e41d32defa39e9e74c00ae7c6d` (start) |
| Objective | Document Material Catalogue architecture: CalibAi-seeded identity; CostItem not identity; living supplier evidence distinct from identity; first FG identity-only. No ADR, Feature Gate, or product code. |
| Business decision | Joel: CalibAi-seeded vocabulary; identity-only first gate; Material Catalogue before Phase D; rolled-up commercial Assembly vs exploded fulfillment; Material Cost Standard deferred; ADR-008 deferred; living catalogue (price increases + promotions) with immutable snapshots. |
| Architectural decision | Canonical material ≠ CostItem ≠ supplier SKU. Material Catalogue UX capability ≠ canonical table. Living evidence is effective-dated, not `CURRENT_PRICE` only. |
| Prompt template used | Bounded Material Catalogue architecture governance (documentation) |
| Approved Cursor prompt summary | DOCUMENTATION / ARCHITECTURE GOVERNANCE ONLY. Create material-catalogue-architecture.md. Reconcile supplier docs. No FG, ADR, migration, or product code. Add living material intelligence (Joel decision). |
| Files expected to change | Architecture, module, and status docs |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; Feature Gates; new ADRs |
| Implementation result | Architecture document created; supplier ownership wording reconciled; living intelligence recorded. |
| Tests | Not rerun (docs-only; no product-code change). Last recorded full suite **310 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | ADRs not yet written. Feature Gate not opened. ADR-008 remains Proposed. |
| Next approved step | **Material Catalogue ADRs** when Joel authorizes. Do not implement. Do not open a Feature Gate yet. |
| Next approved prompt | Material Catalogue ADRs (docs). Do not accept ADR-008 unless that prompt authorizes it. |
| Commit hash | (this commit) |

### 2026-08-30 — FG-013 migration reconciliation + UAT closure

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `0c36adb6d98ec2c1af88fa98cf61c00aa14f0eb3` (start) |
| Objective | Verify live DB already at `c5d6e7f8a9b0`; complete bounded FG-013 UAT; close gate. Do not re-run `flask db upgrade`. |
| Business decision | Preserve interrupted-session migration provenance. Folder/OS-drag native pickers not faked as browser PASS. |
| Architectural decision | FG-013 **CLOSED / OPERATIONAL FOR UAT**. Migration **VERIFIED APPLIED** before this pass. No product-code change. |
| Prompt template used | Bounded FG-013 migration-state reconciliation + UAT closure |
| Approved Cursor prompt summary | Independently verify DB; do not upgrade if current=head; UAT + tests; docs; close only if evidence supports. |
| Files expected to change | FG-013 and governed status docs |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; Alembic revisions; Desktop corpus |
| Implementation result | UAT multi-file/mixed/duplicate/review/storage/quarantine/known-family/TIER_A/mutation/org passed. Folder/OS-drag not live-browser verified. Tests 27/11/25/33/310. |
| Tests | `./venv/bin/python -m pytest -q tests/test_historical_upload_fg013.py` → 27 passed. historical 11; labour 25; pricing 33; full suite **310 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | Native folder picker and OS drag/drop not live-browser verified. |
| Next approved step | **Material Catalogue architecture** (docs) when Joel authorizes. Do not `flask db upgrade`. Do not start supplier POC. |
| Next approved prompt | Material Catalogue architecture documentation. |
| Commit hash | (this commit) |

### 2026-08-30 — ADR-033 supplier channel / Winchester launch-partner architecture

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` |
| Objective | Add supplier-channel architecture: Darcy / BMR Winchester as launch/reference partner, not exclusive; dual contractor-procurement vs CalibAi-channel relationships; Darcy originated-value participation categories without terms. |
| Business decision | BMR, BMR Winchester, and Darcy are **not exclusive**. Winchester = design/launch partner, first reference deployment, supplier-channel BD partner. Reward Darcy for value created / business originated; do not surrender CalibAi’s broader supplier market. Channel expansion to other BMR dealers, BMR corporate, other suppliers, and potentially nationals (e.g. Home Depot class) must not assume one integration model. |
| Architectural decision | **ADR-033 Accepted** (docs only). Relationship **A** (contractor ↔ supplier procurement) distinct from **B** (CalibAi ↔ supplier channel). Do not collapse into PreferredSupplier. Anticipate national/enterprise capabilities; do not overbuild Winchester POC. Reference evidence families recorded for later measurement. No channel economics or analytics in a future POC. No Feature Gate. No product code. |
| Prompt template used | Bounded architecture documentation (Joel commercial clarification) |
| Approved Cursor prompt summary | ADD TO SUPPLIER CHANNEL ARCHITECTURE — DARCY / BMR WINCHESTER LAUNCH-PARTNER MODEL. Docs only. No exclusivity. No percentages. Do not implement supplier POC. |
| Files expected to change | Supplier channel architecture; ADR-033; indexes; catalogue/module/roadmap/vision/CAR-001; current-state; session-handoff; chat-workflow-log; milestones; project-state-report |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; Alembic revisions; FG-013 product implementation |
| Implementation result | Architecture recorded. ADR-033 **Accepted**. Winchester/supplier integration **not implemented**. Darcy terms **unset**. |
| Tests | Docs-only pass. No product-code tests required. `git diff --check`. |
| Project-state-report update | Yes (architecture status only) |
| Milestone entry update | Architecture record appended (not a coded milestone) |
| Constitutional issue raised | None |
| Unresolved issues | Darcy commercial terms. Supplier Feature Gate not opened. Heterogeneous adapter designs deferred to later gates. |
| Next approved step | Do **not** start supplier integration. Next **product** action remains FG-013 live-migrate + UAT when separately authorized. |
| Next approved prompt | None for supplier/Winchester POC. FG-013 live-migrate only if Joel authorizes that prompt. |
| Commit hash | (this commit, if/when committed) |

### 2026-08-30 — FG-013 historical upload implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `f52f06c4adbd04055485e49124da59222a8f7768` (start) |
| Objective | Implement FG-013 office UPLOAD PREVIOUS ESTIMATES, ADR-032 custody, one additive migration. |
| Business decision | Multi-file/folder UX; per-file outcomes; quarantine unknown layouts; TIER_A wording; no auto standards. |
| Architectural decision | `HistoricalUploadAttempt` only (no UploadBatch). Storage `instance/historical_uploads/<org>/<sha256>.<ext>`. Revision `c5d6e7f8a9b0`. Live migrate not applied. |
| Prompt template used | Bounded FG-013 implementation |
| Approved Cursor prompt summary | IMPLEMENT FG-013 — CONTRACTOR CALIBRATION ONBOARDING / HISTORICAL ESTIMATE UPLOAD UX. One additive Alembic revision authorized. Do not live-migrate unless established workflow requires a separate prompt — do not apply live. |
| Files expected to change | Models, routes, templates, ingestion/upload services, migration, tests, governed docs |
| Files prohibited from changing | Legacy Desktop corpus; labour/pricing standards writes; Phase D; auth |
| Implementation result | Implemented. Dedicated tests 27 passed. Full suite 310 passed. Live DB current remains `b4c5d6e7f8a9`. |
| Tests | `./venv/bin/python -m pytest -q tests/test_historical_upload_fg013.py` → 27 passed. `./venv/bin/python -m pytest -q` → 310 passed. Temp-DB upgrade/downgrade of `c5d6e7f8a9b0` verified. Live `flask db upgrade` **not** run. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture/implementation record appended |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate + browser UAT pending. Folder-select not exercised in a live browser this pass. |
| Next approved step | Separate live-migrate + UAT smoke prompt. |
| Next approved prompt | Live-migrate `c5d6e7f8a9b0` only when Joel authorizes. |
| Commit hash | (this commit) |

### 2026-08-30 — FG-013 final governance + ADR-032 accepted

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `fc9fed32a7e2f18730a5778c1d09ab5597fe9b74` (start) |
| Objective | Complete FG-013 governance: storage/custody ADR, remaining gate answers, mark APPROVED FOR IMPLEMENTATION. Docs only. |
| Business decision | Productized historical uploads use app-managed private durable storage. Office upload before auth. Self-serve onboarding requires auth. Unknown layouts quarantine. TIER_A = estimate associated with a completed project, not ORG-ACTUAL. No auto standards. |
| Architectural decision | ADR-032 **Accepted**. Two custody regimes. Durable per-file upload attempts. **No** durable UploadBatch. SCHEMA YES additive; MIGRATION YES one bounded revision — **not created this pass**. |
| Prompt template used | Bounded FG-013 complete governance (documentation) |
| Approved Cursor prompt summary | COMPLETE FG-013 GOVERNANCE — HISTORICAL UPLOAD STORAGE / CUSTODY ADR + FINAL GATE APPROVAL. Do not implement. Do not create the migration. |
| Files expected to change | FG-013; ADR-032; ADR/feature-gate indexes; historical-ingestion and organization/calibration architecture; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones; docs indexes |
| Files prohibited from changing | `app/`; `tests/`; `migrations/`; product code; Alembic revisions |
| Implementation result | FG-013 **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**. ADR-032 **Accepted**. Locked multi-file/folder UX preserved. No product code. No migration. |
| Tests | Docs-only pass. Last recorded full suite remains **283 passed**. Not re-run (no product code). `git diff --check`. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record appended |
| Constitutional issue raised | None |
| Unresolved issues | FG-013 **implementation** not started. Migration not created. |
| Next approved step | **STOP PRODUCT CODE.** Wait for a separate FG-013 **implementation** prompt that explicitly authorizes the additive migration. |
| Next approved prompt | None unless Joel issues FG-013 implementation. |
| Commit hash | (this commit) |

### 2026-08-30 — FG-013 multi-file / folder upload UX locked

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `d41c4d92ee009cdc6679b140ecd44789362077f6` (start) |
| Objective | Memorialize Joel’s FG-013 UX rule: one user action may load many historical workbooks (multi-select, multi drop, folder where the client supports it). No durable UploadBatch for UX. Docs only. |
| Business decision | Users must not upload historical estimates one at a time. ~20–25 is guidance, not a quota. One failed/unsupported/duplicate/quarantined file must not block the rest. |
| Architectural decision | NO durable UploadBatch = database architecture only. Does not mean single-file upload. Per-file ingest remains the transaction unit. Combined results summary is request-scoped. Implementation not authorized. |
| Prompt template used | Bounded FG-013 governance clarification (documentation) |
| Approved Cursor prompt summary | ADD TO FG-013 GOVERNANCE — MULTI-FILE / FOLDER UPLOAD CLARIFICATION. Do not implement uploads. Do not create UploadBatch. |
| Files expected to change | FG-013 draft; feature-gates index; current-state; session-handoff; chat-workflow-log; roadmap as needed |
| Files prohibited from changing | `app/**`, `tests/**`, `migrations/**`, database |
| Implementation result | Created FG-013 as DRAFT FOR JOEL REVIEW with locked multi-file/folder section. Implementation not started. |
| Tests | Docs-only. Last recorded full suite **283 passed**. |
| Project-state-report update | Minimal (draft gate; not a coded milestone) |
| Milestone entry update | No (not a completed milestone) |
| Constitutional issue raised | None |
| Unresolved issues | FG-013 remainder (schema, storage ADR, quarantine, auth) not approved. Implementation not authorized. |
| Next approved step | **STOP DEVELOPMENT.** Do not implement FG-013. Joel reviews the draft gate. |
| Next approved prompt | None unless Joel authorizes remaining FG-013 answers or a later implementation prompt. |
| Commit hash | (this documentation commit) |

### 2026-08-30 — ADR-021 MONITOR baseline / Project Gross Margin acceptance

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `0b403d6aa51381d3763cf3dc9d5d96e096d5ab93` (start) |
| Objective | Accept ADR-021: MONITOR composed commercial baseline and Project Gross Margin. Governance / documentation only. |
| Business decision | Authoritative project metric is PROJECT GROSS MARGIN, not net profit. Frozen composed baseline: locked EstimateVersion + EstimatePricingSnapshot when present + Accepted Proposal + approved CO deltas as separate layers. Draft estimates/proposals must not be the committed baseline. |
| Architectural decision | MONITOR is a Project-centered comparison/read layer. Actuals owned by BUILD / later domains. Industry benchmarks not profitability truth. QuickBooks not mandatory. Phase D independent. No schema. No Feature Gate. MONITOR not implemented. |
| Prompt template used | Bounded ADR-021 governance pass (documentation) |
| Approved Cursor prompt summary | ADR-021 MONITOR BASELINE / PROJECT GROSS MARGIN GOVERNANCE PASS. Docs only. Do not implement MONITOR, BUILD actuals, profitability, benchmarking, or historical-upload onboarding. |
| Files expected to change | ADR-021 and supporting governed docs |
| Files prohibited from changing | `app/**`, `tests/**`, `migrations/**`, database, runtime configuration |
| Implementation result | ADR-021 set to Accepted. Module note `docs/modules/monitor.md` (not implemented). Supporting docs reconciled. |
| Tests | Docs-only; `git diff --check`. Product suite not re-run. Last recorded full suite **283 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (architecture record; no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | CO estimated-cost delta not stored; no governed credits; labour-snapshot vs actual labour GM comparability; next product gate not authorized. ADR-010 Proposed. Phase D unauthorized. |
| Next approved step | **STOP DEVELOPMENT.** Do not implement MONITOR. Do not create a Feature Gate. |
| Next approved prompt | None. Joel chooses whether the next product gate is office historical-upload onboarding or authentication/BUILD. |
| Commit hash | (this documentation commit) |

### 2026-08-30 — FG-012 Estimate-Output Consistency implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `17c2951cf586e15321756349ccd05d9133b719f3` (start) |
| Objective | Implement approved FG-012 Internal Detailed Cost Breakdown + Customer Estimate Consistency only. |
| Business decision | Estimating owns the internal breakdown. Existing Proposal remains the customer-facing estimate. Named-method totals copy frozen EstimatePricingSnapshot. Labour snapshots display-only, not in selling-price basis. No TBD/PLACEHOLDER schema. |
| Architectural decision | No new estimate entity, document module, or ADR. Preserve TRUE_GROSS_MARGIN / COST_PLUS_MARKUP / COST_PLUS_MARKUP_STACK / legacy no-snapshot. SCHEMA NO. MIGRATION NO. |
| Prompt template used | Bounded FG-012 implementation prompt (Feature Gate implementation) |
| Approved Cursor prompt summary | IMPLEMENT FG-012 INTERNAL DETAILED COST BREAKDOWN + CUSTOMER ESTIMATE CONSISTENCY. SCHEMA CHANGE NO. MIGRATION NO. No Phase D. No external AI. |
| Files expected to change | Estimating routes/templates/CSS; `app/services/estimate_output.py`; `app/services/proposals.py`; `app/services/proposal_pdf.py`; dedicated tests; governed docs |
| Files prohibited from changing | `migrations/**`, models/schemas, Phase D, auth, Dashboard counts |
| Implementation result | Internal breakdown route; named-method proposal totals; customer PDF OH/Profit leak closed; Estimate Totals method presentation; dedicated 19 tests; full suite 283. |
| Tests | Dedicated `tests/test_estimate_output_consistency.py` **19 passed**; listed regressions **183 passed**; full suite `./venv/bin/python -m pytest -q` **283 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (architecture record; no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | Office proposal create/detail still lists Overhead/Profit amounts (zero for named methods). Live UAT estimates have no Allowance/labour snapshot rows (covered by tests). Phase D unauthorized. ADR-010 Proposed. Office auth not implemented. TBD/PLACEHOLDER durable state deferred. |
| Next approved step | **STOP DEVELOPMENT.** Do not begin another Feature Gate. |
| Next approved prompt | None. Phase D remains unauthorized. |
| Commit hash | (this implementation commit) |

### 2026-08-30 — FG-012 Estimate-Output Consistency governance approval

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `2733e2f3b68b7320f08f093875e272532cd78885` (start) |
| Objective | Memorialize Joel-approved FG-012 Internal Detailed Cost Breakdown + Customer Estimate Consistency. Documentation only. Do not implement. |
| Business decision | Estimating owns the internal breakdown. Existing Proposal remains the customer-facing estimate. Outputs 1 and 2 only. Direct Cost = Σ `extended_cost`. Labour snapshots not in selling-price basis. No TBD/PLACEHOLDER schema. Estimate Totals presentation and customer-PDF Overhead/Profit leak in FG-012 implementation scope. |
| Architectural decision | No new estimate entity, document module, or ADR. Consume FG-009 snapshots read-only. Preserve TRUE_GROSS_MARGIN / COST_PLUS_MARKUP / COST_PLUS_MARKUP_STACK / legacy no-snapshot. Source-contract principle for later outputs 3–4 only. Schema NO. Migration NO. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | FG-012 GOVERNANCE APPROVAL. Docs only. APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED. Do not implement FG-012. |
| Files expected to change | Governed docs listed in the prompt |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, configuration |
| Implementation result | FG-012 created. Indexes and current-state/handoff/roadmap/module/package docs updated. No product code. |
| Tests / validation | `git diff --check`. Product tests not re-run (docs-only). Prior full suite **264 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | No (no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | Implementation not started. Phase D unauthorized. ADR-010 Proposed. Office auth not implemented. TBD/PLACEHOLDER durable state deferred. |
| Next approved step | Separate bounded FG-012 **implementation** Cursor prompt. Do not implement in this pass. |
| Next approved prompt | FG-012 implementation (not this commit) |
| Commit hash | (this docs commit) |

### 2026-08-30 — FG-011 Project Hub UX implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `225731a2208e16fea8558a048e8c34f0f4879549` (start) |
| Objective | Implement approved FG-011 Project Hub UX by evolving `/projects/<id>` only. |
| Business decision | Projects owns the hub UX. Hub reads and links stored facts. No new module, Job entity, schema, or ADR. |
| Architectural decision | PLAN / PRICE / CONTRACT from stored records; BUILD = existing Change Orders; field BUILD / MONITOR / LEARN / QuickBooks / four-output / Ontario contract / real AI labeled Future. Conservative pricing/labour presence only. Phase D unauthorized. Dashboard counts out of scope. |
| Prompt template used | Bounded FG-011 implementation prompt (Feature Gate implementation) |
| Approved Cursor prompt summary | IMPLEMENT FG-011 PROJECT HUB UX. Evolve existing project detail. SCHEMA CHANGE NO. MIGRATION NO. No Phase D. No external AI. |
| Files expected to change | `app/routes/projects.py`, `app/templates/projects/detail.html`, optional CSS/helper, dedicated tests, governed docs |
| Files prohibited from changing | `migrations/**`, models/schemas, take-off/pricing/labour write paths, Dashboard counts, auth |
| Implementation result | Project Hub on `/projects/<id>` with read-only `app/services/project_hub.py`. Dedicated tests added. Browser smoke on labeled FG-009/FG-010 UAT projects. |
| Tests / validation | Dedicated Project Hub **13 passed**. Full suite **264 passed**. `git diff --check` clean. Alembic current/head unchanged `b4c5d6e7f8a9`. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record only (no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | Phase D unauthorized. ADR-010 Proposed. Office auth not implemented. Dashboard org-unscoped counts remain out of scope. FG-010 UAT project still has no commercial context recorded. |
| Next approved step | **STOP.** Do not start Phase D or another Feature Gate. |
| Next approved prompt | None. Next product work requires a new Feature Gate. |
| Commit hash | (this implementation commit) |

### 2026-08-30 — FG-011 Project Hub UX governance approval

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` @ `49c490852fa5b129da7bd32fc7e446539140f30b` (start) |
| Objective | Memorialize Joel-approved FG-011 Project Hub UX. Documentation only. Do not implement. |
| Business decision | Evolve existing `/projects/<id>`. Projects owns the hub UX. No new module, Job entity, schema, or ADR. No M0xx. |
| Architectural decision | ADR-019 remains the hub-entity decision. Hub reads/links only. Conservative pricing/labour presentation. Phase D and external AI remain unauthorized. Dashboard org-unscoped counts out of scope. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | FG-011 GOVERNANCE APPROVAL. Docs only. APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED. |
| Files expected to change | Governed docs listed in the prompt |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, configuration |
| Implementation result | FG-011 created. Indexes and current-state/handoff/roadmap updated. No product code. |
| Tests / validation | `git diff --check`. Product tests not re-run (docs-only). Prior full suite **251 passed**. |
| Project-state-report update | Yes |
| Milestone entry update | No (no new M0xx) |
| Constitutional issue raised | None |
| Unresolved issues | Implementation not started. Phase D unauthorized. ADR-010 Proposed. Office auth not implemented. |
| Next approved step | Separate bounded FG-011 **implementation** Cursor prompt. Do not implement in this pass. |
| Next approved prompt | FG-011 implementation (not this commit) |
| Commit hash | (this docs commit) |

### 2026-08-30 — 29 Aug day-end reconciliation / Review Turnover

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` (start `316cc9f11c141d806737bb7caebdb7c37c5bda9b`) |
| Objective | Full 29 Aug repository / database / documentation / storage / Review Turnover audit. No product features. No Phase D. No external AI. |
| Business decision | Close FG-008 / FG-009 / FG-010 as **CLOSED / OPERATIONAL FOR UAT**. Leave synthetic UAT residue labeled. Next candidate (Project Hub UX) **NOT AUTHORIZED**. |
| Architectural decision | ADR-010 remains **Proposed**. Live Alembic current/head remains `b4c5d6e7f8a9`. No migrations created or altered. |
| Prompt template used | Review Turnover Protocol 22-point package + 29 Aug day-end reconciliation prompt |
| Approved Cursor prompt summary | READ → VERIFY → RECONCILE → TEST → DOCUMENT → COMMIT → PUSH → VERIFY → TURN OVER → STOP. Docs only. |
| Files expected to change | Governed docs only |
| Files prohibited from changing | `app/**` product code; `migrations/**`; tests; historical/commercial source files |
| Implementation result | Pre-flight matched start pins. All listed 29 Aug SHAs are ancestors of `main`. Origin parity. No untracked files. Linear Alembic chain to `b4c5d6e7f8a9`. Live DB snapshot recorded. Stale current-state Alembic/test/next-action language corrected. Complete 22-point `session-handoff.md` including Fresh Chat Startup Prompt. |
| Tests | take-off **18**; Plan Intelligence **56**; Pricing **33**; Labour **25**; Historical **11**; full **251**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Historical 0.13 labour-rate cluster; material-as-labour labels; crew/duration inconsistencies; ORG-001 optional layers unspecified; labour-snapshot cost not in estimate basis by default; Estimate Totals header leftover percents (UI debt); take-off cancel not implemented; ARCH-only eligibility; actor-string identity; ADR-010 Proposed; Phase D not started; office auth not implemented; synthetic UAT residue left labeled. |
| Next approved step | **STOP DEVELOPMENT.** Fresh session uses `docs/session-handoff.md` §22. |
| Next approved prompt | None. Next candidate Project Hub UX requires a new Feature Gate. |
| Commit hash | (this docs reconciliation commit) |

### 2026-08-30 — FG-010 / M012 live migration and synthetic UAT smoke

| Field | Content |
|-------|---------|
| Date | 2026-08-30 |
| Branch | `main` |
| Objective | Apply `b4c5d6e7f8a9` to live development/UAT and perform bounded synthetic browser/UAT smoke. No external AI. No Phase D. No new milestone. |
| Business decision | Live migration authorized. Synthetic UAT only. Leave labeled FG-010 UAT residue. |
| Architectural decision | COUNT remains dimensionless. Dimensional measurement remains scale-governed. ADR-010 remains Proposed. |
| Prompt template used | FG-010 LIVE DEVELOPMENT/UAT MIGRATION + SYNTHETIC SMOKE VERIFICATION |
| Approved Cursor prompt summary | PRE-FLIGHT → TEST GATE → SNAPSHOT → UPGRADE → SCHEMA/INTEGRITY → SYNTHETIC UAT → BROWSER SMOKE → REGRESSION → DOCS RECONCILE → COMMIT/PUSH → STOP. |
| Files expected to change | Governed docs only after live migrate. |
| Files prohibited from changing | Product code; committed migration; historical/commercial records; Labour/Pricing logic. |
| Implementation result | Live current/head `b4c5d6e7f8a9`. Synthetic searchable run produced 4 mock candidates; 3 accepted + 1 duplicate; approved package total 3; immutable; rerun distinct; COUNT without scale succeeded; linear/polyline/area fail-closed; Estimate/Labour/Pricing deltas **ZERO**; external calls **ZERO**. Browser smoke: take-off index, run submit (run 3), candidate review, approved package UI. |
| Tests | Pre and post: take-off **18**; Plan Intelligence **56**; Pricing **33**; Labour **25**; Historical **11**; full **251**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Cancel-run operation missing (accepted). ARCH-only eligibility. Actor-string reviewer identity until auth. Real provider undecided. Phase D mapping future. Synthetic FG-009 and FG-010 residue left labeled. |
| Next approved step | **STOP DEVELOPMENT.** Day-End Reconciliation / Review Turnover audit. |
| Next approved prompt | Single clean-turnover prompt for complete end-of-day audit and tomorrow-start package. |
| Commit hash | (this docs reconciliation commit; implementation `9665295ace673a46a8c645ed0598e5e91d41931c`) |

### 2026-08-29 — FG-010 / M012 implementation commit and push

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Final audit, commit, and push the reviewed FG-010 foundation. No live migrate. No external AI. No Phase D. |
| Business decision | PASS — approved for commit. Live database migration remains unauthorized. |
| Architectural decision | One implementation commit. Graph head `b4c5d6e7f8a9`. Live current remains `a3b4c5d6e7f8`. ADR-010 remains Proposed. |
| Prompt template used | FG-010 FINAL AUDIT + IMPLEMENTATION COMMIT / PUSH AUTHORIZATION |
| Approved Cursor prompt summary | VERIFY → AUDIT → TEST → STAGE → COMMIT → PUSH → STOP. Do not flask db upgrade. |
| Files expected to change | Reviewed FG-010 product + docs + migration `b4c5d6e7f8a9`. |
| Files prohibited from changing | Labour/Pricing commercial logic; historical workbooks; Accepted proposals; live DB schema. |
| Implementation result | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** / **NOT YET LIVE-MIGRATED**. External provider calls: **ZERO**. Estimate/labour/pricing writes: **ZERO**. |
| Tests | Dedicated take-off **18**; Plan Intelligence combined **56**; Pricing **33**; Labour **25**; Historical **11**; full suite **251**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Live DB still `a3b4c5d6e7f8`. Browser/live UAT not yet performed. No cancel-run operation (accepted for synchronous POC). |
| Next approved step | Separate live-migrate + UAT smoke authorization. |
| Next approved prompt | Apply `b4c5d6e7f8a9` to live development/UAT and bounded synthetic browser/UAT smoke. |
| Commit hash | (this commit) |

### 2026-08-29 — FG-010 / M012 foundation implementation (uncommitted)

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Implement FG-010 provider-neutral AI take-off foundation. No live migrate. No commit. No external AI. No Phase D. |
| Business decision | Interior-door COUNT POC via deterministic mock. Package approval is PLAN evidence only. COUNT does not require scale. |
| Architectural decision | First-class `TakeoffExtractionRun` / `TakeoffCandidate` / `TakeoffPackage` / `TakeoffPackageItem`. ADR-027 coordinates only. PlanAuditEvent extended. Org-scoped rows. Mock extractor `calibai-mock`. |
| Prompt template used | FG-010 BOUNDED IMPLEMENTATION AUTHORIZATION |
| Approved Cursor prompt summary | PRESERVE → VERIFY → IMPLEMENT FOUNDATION → TEST → REPORT → STOP. NO COMMIT. NO PUSH. NO LIVE MIGRATION. NO EXTERNAL AI. NO PHASE D. |
| Files expected to change | Plan Intelligence models/services/routes/templates; one additive migration; dedicated tests; governed docs. |
| Files prohibited from changing | Labour Engine / Pricing Engine commercial logic; EstimateVersion writes; historical workbooks; Accepted proposals. |
| Implementation result | **IMPLEMENTED / VERIFIED** / **NOT YET LIVE-MIGRATED**. External provider calls: **ZERO**. Estimate/labour/pricing writes: **ZERO**. |
| Tests | Dedicated take-off **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; Historical **11**; full suite **251**. `git diff --check` clean. Temp migration `a3b4c5d6e7f8` → `b4c5d6e7f8a9` → `a3b4c5d6e7f8`. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None. ADR-006: package approval does not insert estimate lines. |
| Unresolved issues | Uncommitted working tree. Live DB still `a3b4c5d6e7f8`. |
| Next approved step | Joel/ChatGPT governance review. |
| Next approved prompt | Separate commit/push authorization if review PASSes. Do not live-migrate in that prompt unless explicitly authorized. |
| Commit hash | **None** (this pass forbids commit) |

### 2026-08-29 — FG-010 governance approval (documentation commit)

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Approve FG-010 for implementation; Accept ADR-005/006/007/009/011/031; keep ADR-010 Proposed; record COUNT-without-scale and provider-not-authorized conditions; docs-only commit/push. |
| Business decision | M012 POC remains searchable PDF, `INTERIOR_DOOR_OPENING` COUNT. Package approval is not EstimateVersion insertion. |
| Architectural decision | COUNT is dimensionless (narrow authorized M010 count/scale correction in a later implementation prompt). Real external AI provider **not authorized**. Dimensional measurements remain fail-closed. |
| Prompt template used | FG-010 GOVERNANCE APPROVAL + DOCUMENTATION COMMIT |
| Approved Cursor prompt summary | APPROVE → RECONCILE → REGRESS → COMMIT → PUSH → STOP. NO PRODUCT CODE. NO MIGRATION. NO PROVIDER INTEGRATION. |
| Files expected to change | Governed docs only. |
| Files prohibited from changing | `app/`; `migrations/`; `tests/`; historical workbooks; Labour Engine / Pricing Engine product logic. |
| Implementation result | FG-010 **APPROVED FOR IMPLEMENTATION** / **NOT IMPLEMENTED**. Product code **NONE**. |
| Tests | Plan Intelligence combined **51**; Pricing **33**; Labour **25**; Historical **11**; full suite **228**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None. ADR-006 clarification: human take-off approval does not authorize estimate insert in M012. |
| Next approved prompt | Separate bounded FG-010 implementation prompt. Do not implement in this pass. |

### 2026-08-29 — FG-010 / M012 AI Take-off architecture and Feature Gate preparation

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Architecture / ADR reconciliation / Feature Gate preparation for AI Take-off / Quantity Extraction Foundation. No product implementation. |
| Business decision | Next coded candidate after FG-009 closure is M012 interior-door **count** from searchable architectural PDFs, with mandatory human review. Mapping into Estimating is **out of this gate**. |
| Architectural decision | Plan Intelligence owns take-off. First-class extraction run, candidate, and immutable package (ADR-031 **Proposed**). Reuse ADR-027 coordinates. Do not overload `PlanMeasurement`. COUNT V1 must not require scale. New take-off rows carry `organization_id`. |
| Prompt template used | AI TAKE-OFF / QUANTITY EXTRACTION FOUNDATION — ARCHITECTURE / ADR RECONCILIATION / FEATURE GATE PREPARATION |
| Approved Cursor prompt summary | READ → AUDIT → RECONCILE → ARCHITECT → PREPARE → STOP. NO PRODUCT IMPLEMENTATION. NO COMMIT. NO PUSH. |
| Files expected to change | Governed docs only. |
| Files prohibited from changing | `app/`; `migrations/`; historical workbooks; Labour Engine / Pricing Engine product logic; Accepted proposals. |
| Implementation result | Docs package prepared. FG-010 **PREPARED FOR GOVERNANCE APPROVAL**. Product code **NONE**. Migration **NONE**. |
| Tests | Plan Intelligence combined **51**; Pricing **33**; Labour **25**; Historical **11**; full suite **228**. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append architecture-prepared record) |
| Constitutional issue raised | None blocking. Recommend Accept ADR-005/006/007/009/011 with FG-010; do not bulk-accept ADR-010. |
| Next approved prompt | None. Governance review of FG-010 + ADR-031. Do not implement AI take-off. |

### 2026-08-29 — FG-009 live development/UAT migration and UAT smoke

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Final preflight; apply committed FG-009 migration `a3b4c5d6e7f8`; verify seed/schema; bounded Pricing Engine UAT smoke; regression; docs reconciliation. STOP. |
| Business decision | Live migrate authorized for development/UAT only. ORG-001 15% TRUE_GM and 13% HST remain org-scoped. Optional layers remain `UNSPECIFIED`. No second organization created. Synthetic UAT labels only. |
| Architectural decision | No new product code. No new migration. No AI take-off. Labour-snapshot Direct Labour Cost remains excluded from estimate basis by default. |
| Prompt template used | Live development/UAT migration + Pricing Engine smoke verification (this session). |
| Approved Cursor prompt summary | PRESERVE → VERIFY → MIGRATE → SMOKE → REGRESSION → RECONCILE → STOP. `flask db upgrade` explicitly authorized. Do not start AI take-off. |
| Files expected to change | Governed docs only (plus live SQLite schema/seed/UAT rows). |
| Files prohibited from changing | Product code; committed migration file; historical workbooks; Labour Engine production logic; Accepted proposals; customer-facing proposal templates. |
| Implementation result | Migration `f2c3d4e5f6a7` → `a3b4c5d6e7f8` succeeded. UAT smoke passed. Docs reconciled. |
| Tests | Pricing **33**; Labour **25**; Historical **11**; full suite **228**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Synthetic FG-009 UAT residue remains (Draft estimates / WITHDRAWN markup policy / COs). ORG-001 optional layers remain `UNSPECIFIED`. |
| Next approved step | FG-009 closure review, then prepare the next Feature Gate for AI Take-off / Quantity Extraction Foundation. |
| Next approved prompt | None in this pass. Do not start AI take-off. |
| Commit hash | Docs-only reconcile (record after push) |

### 2026-08-29 — FG-009 implementation commit and push

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Commit and push the reviewed FG-009 foundation. Do not apply live migration. |
| Business decision | Governance PASS — approved for commit. ADR-025 **Accepted**. ADR-030 **Accepted**. Live migrate not authorized by this prompt. |
| Architectural decision | One implementation commit. Graph head `a3b4c5d6e7f8`. Live current remains `f2c3d4e5f6a7`. |
| Prompt template used | Commit + push authorization (this session). |
| Approved Cursor prompt summary | PRESERVE → AUDIT → TEST → COMMIT → PUSH → VERIFY → STOP. Do not flask db upgrade. Do not start AI take-off. |
| Files expected to change | Reviewed FG-009 product + docs + migration `a3b4c5d6e7f8`. |
| Files prohibited from changing | Historical workbooks; Labour Engine production logic; live DB. |
| Implementation result | Committed and pushed. Live DB not migrated. |
| Tests | Pricing **33**; Labour **25**; Historical **11**; full suite **228**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Yes (append) |
| Constitutional issue raised | None |
| Unresolved issues | Live migrate not authorized. ORG-001 optional layers remain `UNSPECIFIED`. |
| Next approved step | Separate live-migrate + UAT-smoke authorization. |
| Next approved prompt | Apply `a3b4c5d6e7f8` to live development/UAT only when separately authorized. |
| Commit hash | Recorded after push (`git log -1`) |

### 2026-08-29 — FG-009 final pre-commit implementation review

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Preserve the uncommitted FG-009 tree; reconstruct from code; review against FG-009 / ADR-025 / ADR-030; resolve only remaining genuine FG-009 blockers; re-test; report. No commit, push, or live migrate. |
| Business decision | No new commercial values. ORG-001 15% TRUE_GM and 13% HST remain org-scoped. Optional layers remain `UNSPECIFIED`. |
| Architectural decision | Review found **no remaining FG-009 blockers**. Prior bounded correction already applies inherited CO methods via `price_change_order_from_snapshot` and seeds optional layers as `UNSPECIFIED`. `CALIBAI_BASELINE` is a resolution-source constant only; live fail-closed path is `PROVISIONAL_LEGACY_STACK`. Unlinked COs without snapshot remain legacy. ADR-025 and ADR-030 remain **Accepted**. |
| Prompt template used | Final pre-commit implementation review authorization (this session). |
| Approved Cursor prompt summary | PRESERVE → RECONSTRUCT → CORRECT ONLY FG-009 BLOCKERS → TEST → REPORT → STOP. Do not reimplement. Do not reset/stash. Do not commit/push. Do not apply live migration. |
| Files expected to change | Docs only if needed to record this review. Product code only if a genuine blocker remained. |
| Files prohibited from changing | Historical workbooks; FG-006 facts; Labour Engine production/calibration; Accepted proposals; live DB; new Alembic revision; AI take-off / BUILD / MONITOR / LEARN. |
| Implementation result | **No product-code change this pass.** Existing dirty FG-009 tree preserved. Review complete. Not committed. Live DB not migrated. |
| Tests | `tests/test_pricing_engine.py` **33 passed**; `tests/test_labour_engine.py` **25 passed**; `tests/test_historical_ingestion.py` **11 passed**; full suite **228 passed**. `git diff --check` clean. |
| Project-state-report update | Counts already current; this review confirms them. |
| Milestone entry update | No new milestone. |
| Constitutional issue raised | None |
| Unresolved issues | Commit/push/live-migrate not authorized. ORG-001 overhead/profit/contingency remain `UNSPECIFIED`. Labour-snapshot cost not in estimate basis by default. |
| Next approved step | Joel / ChatGPT governance review of this stopping report. **Do not commit. Do not push. Do not migrate live DB.** |
| Next approved prompt | None until review. Then commit (if approved), then a separate live-migrate prompt. |
| Commit hash | **None** (this pass) |

### 2026-08-29 — FG-009 pre-commit bounded correction (CO method + ORG-001 seed)

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Correct two governance issues in the uncommitted FG-009 tree before commit: (1) FG-009-aware Change Orders must apply inherited pricing METHOD; (2) ORG-001 optional layers must seed as `UNSPECIFIED`, not `NOT_APPLIED`. |
| Business decision | `NOT_APPLIED` is an org-approved commercial decision. Ungoverned overhead/profit/contingency remain `UNSPECIFIED`. TRUE_GM 15% and HST 13% unchanged. FG-009-aware COs apply method identity; legacy COs without snapshot unchanged. |
| Architectural decision | Reuse Pricing Engine `compute_named_method_pre_tax` / `legacy_stack_pre_tax` / `apply_tax_after_pre_tax` from Project Controls via `price_change_order_from_snapshot`. Do not invent a second engine. Copy snapshotted CO lines as direct/extended cost. Correct uncommitted migration `a3b4c5d6e7f8` in place; no new revision. ADR-025 and ADR-030 remain **Accepted**. |
| Prompt template used | Bounded pre-commit correction authorization (this session). |
| Approved Cursor prompt summary | PRE-COMMIT BOUNDED CORRECTION PASS only. Do not reimplement FG-009. Do not reset/stash/discard. Do not commit/push. Do not apply live migration. |
| Files expected to change | Pricing Engine models/services; Project Controls recalculate/copy-lines; uncommitted migration seed; tests; FG-009/module/handoff docs. |
| Files prohibited from changing | Historical workbooks; FG-006 facts; Labour Engine production/calibration; Accepted proposals; live DB; new Alembic revision. |
| Implementation result | **Complete in working tree.** Not committed. Live DB not migrated. Existing FG-009 implementation preserved. |
| Tests | `tests/test_pricing_engine.py` **33 passed**; `tests/test_labour_engine.py` **25 passed**; `tests/test_historical_ingestion.py` **11 passed**; full suite **228 passed**. `git diff --check` clean. Alembic `f2c3d4e5f6a7` → `a3b4c5d6e7f8` → downgrade in dedicated test. |
| Project-state-report update | Yes |
| Milestone entry update | Append-only correction record |
| Constitutional issue raised | None |
| Unresolved issues | Commit/push/live-migrate not authorized. ORG-001 overhead/profit/contingency remain `UNSPECIFIED`. Labour-snapshot cost not included in estimate basis by default. |
| Next approved step | Joel / ChatGPT governance review of the bounded-correction stopping report. **Do not commit. Do not push. Do not migrate live DB.** |
| Next approved prompt | None until review. Then commit (if approved), then a separate live-migrate prompt. |
| Commit hash | **None** (this pass) |

### 2026-08-29 — FG-009 Organization-Calibrated Pricing Engine implementation

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Implement FG-009 only: versioned org pricing policies, named methods, resolution, immutable estimate snapshots, ORG-001 seed, legacy compatibility, Change Order inheritance, tenant isolation, dedicated tests. |
| Business decision | CalibAi owns methods; orgs own rates. ORG-001 15% true GM and 13% HST are org-scoped, not platform defaults. New estimates are not auto-converted. Contingency/overhead for ORG-001 remain `NOT_APPLIED` (not invented). |
| Architectural decision | Route estimate recalc through snapshot if present else legacy stack. Do not delete legacy logic. Labour snapshot Direct Labour Cost is consume-only and not added to the estimate basis by default. Pricing Posture / Execution Risk snapshot-only. |
| Prompt template used | Bounded FG-009 implementation authorization (this session). |
| Approved Cursor prompt summary | Implement FG-009 Organization-Calibrated Pricing Engine foundation only. One additive migration. Do not commit/push. Do not migrate live DB. Do not expand into four-output, QuickBooks, contracts, Labour Engine expansion, historical evidence repair, ML, or BUILD/MONITOR/LEARN. |
| Files expected to change | Pricing Engine models/services/routes/templates; estimate builder routing; CO inheritance; migration `a3b4c5d6e7f8`; `tests/test_pricing_engine.py`; FG-009/docs status. |
| Files prohibited from changing | Historical workbooks; FG-006 facts; accepted proposal immutability rules; Labour Engine production/calibration logic (except read-only consume); live DB. |
| Implementation result | **Complete in working tree.** Not committed. Live DB not migrated. |
| Tests | `tests/test_pricing_engine.py` **26 passed**; `tests/test_labour_engine.py` **25 passed**; `tests/test_historical_ingestion.py` **11 passed**; full suite **221 passed**. `git diff --check` clean. |
| Project-state-report update | Yes |
| Milestone entry update | Architecture record (implementation; not a numbered milestone) |
| Constitutional issue raised | None |
| Unresolved issues | Commit/push/live-migrate not authorized. ORG-001 contingency treatment remains `NOT_APPLIED`. Labour-snapshot cost not included in estimate basis by default. |
| Next approved step | Joel / ChatGPT governance review. **Do not commit. Do not push. Do not migrate live DB.** |
| Next approved prompt | None until review. Then commit (if approved), then a separate live-migrate prompt. |
| Commit hash | **None** (this pass) |

### 2026-08-29 — FG-009 governance approval / documentation commit

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Finalize FG-009 architecture approval, accept ADR-025 and ADR-030, adopt contingency source vs pricing-treatment clarification, commit and push docs only. No product implementation. |
| Business decision | Joel/ChatGPT: FG-009 architecture approved (subject to contingency clarification); Feature Gate **APPROVED FOR IMPLEMENTATION**; ADR-025 **AMEND AND ACCEPT**; ADR-030 **ACCEPT**. Implementation **not authorized**. |
| Architectural decision | Contingency **source/purpose** distinct from **visibility** (`INTERNAL_RESERVE` / `CUSTOMER_PRICED` / `NOT_APPLIED`) and from **pricing treatment** (`INCLUDED_IN_MARGIN_BASIS` / `ADDED_AFTER_BASE_PRICING`). Overhead not equated with GM. TRUE_GROSS_MARGIN must not hide COST_PLUS_MARKUP_STACK. FG-009-aware COs inherit estimate snapshot; historical COs not rewritten. |
| Prompt template used | `docs/prompts/cursor-documentation-template.md` (authorized governance-finalization prompt, this session). |
| Approved Cursor prompt summary | Docs/governance only: accept ADRs, approve FG-009, contingency clarification, tests, commit, push. No product code, no migration, no pricing calculation change. |
| Files expected to change | `docs/**` FG-009 / ADR-025 / ADR-030 / indexes / handoff. |
| Files prohibited from changing | Product code, migrations, tests (except running them). |
| Implementation result | **Docs/governance only.** Live estimate formula unchanged. |
| Tests | `tests/test_labour_engine.py`; `tests/test_historical_ingestion.py`; full suite; `git diff --check` — exact counts in stopping report. |
| Project-state-report update | Yes — FG-009 approved for implementation; not a coded milestone |
| Milestone entry update | Architecture record updated (not a product milestone) |
| Constitutional issue raised | None |
| Unresolved issues | Selling-price code still the legacy stack until a separate implementation prompt. |
| Next approved step | Issue a separately authorized bounded FG-009 **implementation** prompt. |
| Next approved prompt | FG-009 implementation (not this pass). |
| Commit hash | (this commit) |

### 2026-08-29 — Organization-Calibrated Pricing Engine architecture / ADR-025 / FG-009 preparation

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | READ → AUDIT → RECONCILE → ARCHITECT → PREPARE → STOP. No product implementation. Prepare FG-009 Organization-Calibrated Pricing Engine; resolve ADR-025 recommendation; correct stale FG-008 docs. |
| Business decision | CalibAi owns methodology; each org owns commercial intelligence. ORG-001 15% **true gross margin** (`Direct / 0.85`) is not 15% markup and is not a CalibAi universal default. Historical “15% margin” labels are evidence, not auto-policy. |
| Architectural decision | **AMEND AND ACCEPT** ADR-025 recommended: named methods `TRUE_GROSS_MARGIN`, `COST_PLUS_MARKUP`, `COST_PLUS_MARKUP_STACK` (preserve live stack as explicit method; do not globally replace; do not map 15% GM onto 15% markup). ADR-030 Proposed for org policy records + estimate pricing snapshots + CO inheritance. File statuses remain **Proposed**. FG-009 **PREPARED FOR GOVERNANCE APPROVAL**. |
| Prompt template used | `docs/prompts/cursor-documentation-template.md` (authorized architecture / Feature Gate prompt, this session). |
| Approved Cursor prompt summary | Audit pricing code; reconcile vs `pricing-policy.md`; define org-calibrated engine; prepare next FG; amend ADR-025; no product code; no migration; no commit; no push. |
| Files expected to change | `docs/architecture/organization-calibrated-pricing-engine-architecture.md`, `docs/feature-gates/FG-009-*`, `docs/adr/ADR-025-*`, `docs/adr/ADR-030-*`, `docs/modules/pricing-engine.md`, indexes, current-state, session-handoff, roadmap, chat-workflow-log, milestones architecture record. |
| Files prohibited from changing | Product code, migrations, tests (except running them), historical workbooks, selling-price implementation. |
| Implementation result | **Docs/architecture only.** Live estimate formula unchanged. |
| Tests | `tests/test_labour_engine.py`; `tests/test_historical_ingestion.py`; full suite; `git diff --check` — exact counts in stopping report. |
| Project-state-report update | Yes — FG-009 prepared; not a coded milestone |
| Milestone entry update | Architecture record only (not a product milestone) |
| Constitutional issue raised | None new. Article 5 (immutability) and org-owned commercial intelligence constrain implementation. |
| Unresolved issues | FG-009 / ADR-025 / ADR-030 not accepted by Joel. Live CO math still inconsistent with estimates (architecture records the defect; code unchanged). |
| Next approved step | Joel / ChatGPT governance review. **Do not implement. Do not commit unless requested.** |
| Next approved prompt | None for implementation. |
| Commit hash | **None** (this pass) |

### 2026-08-29 — FG-008 post-UAT integrity stabilization

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Close two FG-008 live-UAT integrity issues: accidental ACCEPTED mapping; labour audit for nonexistent ORG-999. Not a new milestone. |
| Business decision | Preserve historical evidence and append-only audit. Revoke (do not silently rewrite) the accidental accept. Do not create Organization ORG-999. |
| Architectural decision | Added `REVOKED` mapping status (String(20), no migration). Rule suggestions join `LabourTask.status == ACTIVE`. `record_labour_audit` refuses unknown orgs. Unknown-org resolution returns fail-closed without persisting audit. Existing ORG-999 audit row preserved; ORG-001 reconciliation event recorded. DRAFT synthetic production standard withdrawn via existing `WITHDRAWN` approval status. |
| Prompt template used | Authorized post-UAT integrity stabilization prompt (this session). |
| Approved Cursor prompt summary | Inspect mapping/audit architecture; add REVOKED if narrowest; exclude archived tasks from rule suggestion; prevent unknown-org audit persist; reconcile live UAT mapping 1; tests; docs; commit/push if clean; STOP. |
| Files expected to change | `app/models/labour_engine.py`, `app/services/labour_engine.py`, `app/routes/labour_engine.py`, `app/templates/labour_engine/*`, `tests/test_labour_engine.py`, `docs/*` |
| Files prohibited from changing | Historical workbooks/facts, pricing-policy, estimate selling-price, ADR-025, Plan Intelligence, Accepted Proposals, migrations |
| Implementation result | Mapping 1 `REVOKED`. HistoricalLabourItem 1 unchanged. Archived-task rule-suggestion blocked. Unknown-org resolution does not persist audit. ORG-999 audit id 16 preserved; reconciliation event 23 under ORG-001. PRS 1 `WITHDRAWN`. |
| Tests | `tests/test_labour_engine.py` → **25 passed**; `tests/test_historical_ingestion.py` → **11 passed**; full suite → **195 passed**, 293 warnings |
| Project-state-report update | Yes — test counts; not a new milestone |
| Milestone entry update | Architecture record only (not a product milestone) |
| Constitutional issue raised | None |
| Unresolved issues | SQLite did not enforce FK on the preserved ORG-999 audit row; documented as historical UAT anomaly. Mapping 4 created then REJECTED during live verification probe. |
| Next approved step | **STOP.** |
| Next approved prompt | None |
| Commit hash | (this commit) |

### 2026-08-29 — FG-008 live development/UAT migration and UAT smoke

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Apply committed FG-008 migration `f2c3d4e5f6a7` to live development/UAT; verify schema/seed/historical integrity; bounded Labour Engine smoke; regression tests; docs-only reconciliation. |
| Business decision | Live migrate authorized. No new schema, no product code, no historical evidence repair, no Pricing Engine. |
| Architectural decision | `flask db upgrade` `e1b2c3d4e5f6` → `f2c3d4e5f6a7`. ORG-001 $65 CAD/man-hour seed confirmed org-specific. Historical counts unchanged (20 workbooks, 20 estimates, 120 labour items). Foundation operational for UAT only. |
| Prompt template used | Authorized live-migration + smoke verification prompt (this session). |
| Approved Cursor prompt summary | Final preflight; apply `f2c3d4e5f6a7`; verify tables/seed/history; UI/service smoke; 22/11/192 tests; docs-only if live-migrated state must be recorded; commit/push docs-only; STOP. |
| Files expected to change | `docs/*` migration-state reconciliation only. No product code. No new migration. |
| Files prohibited from changing | `app/**`, `migrations/**`, `tests/**`, historical evidence, `docs/pricing-policy.md` |
| Implementation result | Upgrade succeeded. Seven FG-008 tables present. Live current/head `f2c3d4e5f6a7`. UAT smoke performed. Leftover synthetic UAT records identified (archived task `UAT-FG008-001`; mapping 1 ACCEPTED to that UAT task; DRAFT 999.000001 production standard; WITHDRAWN candidate). |
| Tests | `./venv/bin/python -m pytest -q tests/test_labour_engine.py` → **22 passed**; `./venv/bin/python -m pytest -q tests/test_historical_ingestion.py` → **11 passed**; `./venv/bin/python -m pytest -q` → **192 passed**, 119 warnings (pre- and post-upgrade). |
| Project-state-report update | Yes — live current/head `f2c3d4e5f6a7` |
| Milestone entry update | Yes — append live-migration record |
| Constitutional issue raised | None |
| Unresolved issues | No live estimate versions for snapshot UAT (0 estimates); snapshot path covered by automated tests. Accidental ACCEPTED mapping of historical item 1 to UAT task during smoke (source row unchanged). One `LabourAuditEvent` with `organization_id=ORG-999` from a nonexistent-org resolution probe (no Organization row created). |
| Next approved step | **STOP.** Do not start the next milestone. |
| Next approved prompt | None |
| Commit hash | Product code `0569f25e7ff496ab637d52437d48cf815522afa1`; docs-only reconciliation this session |

### 2026-08-29 — FG-008 Labour Engine Phase B commit and push

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Final audit, commit, and push of the reviewed FG-008 Labour Engine Phase B implementation. **Do not upgrade the live database.** |
| Business decision | FG-008 implementation stopping report **PASS — ACCEPTED FOR COMMIT**. Labour Engine stops at direct labour cost. ADR-025 remains **Proposed**. |
| Architectural decision | Unchanged from implementation: org-owned LabourTask; human mapping; versioned production vs direct labour cost rates; no silent multipliers; historical rows immutable; calibration candidate lifecycle; tenant fail-closed. |
| Prompt template used | Bounded FG-008 commit/push authorization (this session) |
| Approved Cursor prompt summary | Audit uncommitted FG-008; re-run 22/11/192 tests; commit one implementation+docs commit; push `origin/main`; leave live Alembic at `e1b2c3d4e5f6`. |
| Files expected to change | FG-008 product files, wiring, migration `f2c3d4e5f6a7`, dedicated tests, governed docs |
| Files prohibited from changing | Historical workbooks; HistoricalLabourItem facts; Plan Intelligence; proposals; pricing-policy values; estimate selling-price formula; ADR-025 status; live DB |
| Implementation result | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED.** Live DB **not** migrated. |
| Tests | `tests/test_labour_engine.py` → **22 passed**; `tests/test_historical_ingestion.py` → **11 passed**; full suite → **192 passed**; `git diff --check` clean |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Live Alembic upgrade `f2c3d4e5f6a7` not applied (expected). ORG-001 canonical task catalog remains empty by design. |
| Next approved step | Separate authorization to apply `f2c3d4e5f6a7` to live development/UAT DB and smoke-verify. |
| Next approved prompt | **None.** Do not start another milestone. |
| Commit hash | *(this FG-008 implementation commit)* |

### 2026-08-29 — FG-008 Labour Engine Phase B implementation (not committed)

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Implement FG-008 Labour Engine Phase B foundation only. Return a stopping report. **Do not commit or push.** |
| Business decision | FG-008 **APPROVED FOR IMPLEMENTATION** (ADR-029 **Accepted**). CalibAi owns methodology; each organization owns labour intelligence. Labour Engine stops at direct labour cost. |
| Architectural decision | Org-owned LabourTask; human mapping (no auto-accept); versioned ProductionRateStandard separate from DirectLabourCostRateStandard; Calibration Candidate state machine; explainable resolution; immutable EstimateLabourSnapshot; ORG-001 $65 seeded as org policy only; no silent multipliers. |
| Prompt template used | Bounded FG-008 implementation authorization (this session) |
| Approved Cursor prompt summary | Implement FG-008 only from `820f54afc179279d2435ad3a426b3037548bb45e`. Additive models/migration/services/office UI/tests. No pricing-engine, ADR-025, AI take-off, BUILD/MONITOR, payroll, QuickBooks, contracts, cross-org learning. Do not commit or push. |
| Files expected to change | Labour Engine models/services/routes/templates; one Alembic revision; dedicated tests; governed docs after tests pass |
| Files prohibited from changing | Historical workbooks; HistoricalLabourItem facts; Plan Intelligence; Accepted proposals; M011 versioning; pricing-policy values; estimate selling-price formula; ADR-025 status |
| Implementation result | Implemented in working tree. Stopping report issued. **Not committed.** |
| Tests | `./venv/bin/python -m pytest -q tests/test_labour_engine.py` → **22 passed**, 55 warnings; `./venv/bin/python -m pytest -q tests/test_historical_ingestion.py` → **11 passed**; `./venv/bin/python -m pytest -q` → **192 passed**, 119 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes (FG-008 implementation pending commit) |
| Constitutional issue raised | None |
| Unresolved issues | Commit/push not authorized; live Alembic upgrade not applied; ORG-001 canonical task catalog remains empty by design |
| Next approved step | Governance review of stopping report. Commit/push only if separately authorized. |
| Next approved prompt | **None.** |
| Commit hash | *(uncommitted — prompt forbade commit)* |

### 2026-08-29 — FG-008 architecture approved; ADR-029 Accepted; documentation commit

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Record Joel/ChatGPT approval of FG-008 architecture and ADR-029. Commit documentation only. **No product implementation.** |
| Business decision | FG-008 architecture **APPROVED FOR IMPLEMENTATION**. ADR-029 **Accepted**. Implementation **has not started** and requires a separate execution prompt. |
| Architectural decision | Unchanged from the reviewed stopping report: canonical LabourTask; human mapping; versioned production vs direct labour cost rates; no silent multipliers; historical rows immutable evidence; calibration candidate lifecycle; tenant fail-closed; Labour Engine stops at direct labour cost. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | Finalize FG-008 / ADR-029 governance status; confirm docs consistency; test; **one** docs commit; push `origin/main`. No app/, migrations/, or implementation tests. |
| Files expected to change | `docs/` only |
| Files prohibited from changing | Application code, models, migrations, routes, templates, services, tests, historical workbooks, pricing-policy rate/formula values |
| Implementation result | Governance statuses updated. Labour Engine **not implemented**. |
| Tests | See this session’s stopping report (full suite + historical ingestion). |
| Project-state-report update | Yes |
| Milestone entry update | Yes (FG-008 architecture record status) |
| Constitutional issue raised | None |
| Unresolved issues | Implementation prompt not issued; historical rate-quality defects remain unrepaired by design. |
| Next approved step | Bounded FG-008 implementation prompt (not issued in this pass). |
| Next approved prompt | **None.** |
| Commit hash | *(this approval commit)* |

### 2026-08-29 — FG-008 Labour Engine Phase B architecture / Feature Gate preparation

| Field | Content |
|-------|---------|
| Date | 2026-08-29 |
| Branch | `main` |
| Objective | Prepare FG-008 Labour Engine Phase B / Organization Labour Calibration Foundation: architecture, Feature Gate, ADR-029, stale-doc corrections. **No product implementation.** |
| Business decision | CalibAi owns methodology; each organization owns labour intelligence. ORG-001 $65/hr and 15% true gross margin are Brayman policy, not platform defaults. Historical labour remains evidence. No hidden hour multipliers. Crew catalog and burden modeling deferred. |
| Architectural decision | Canonical org-owned Labour Tasks with human-reviewed mappings; versioned Production Rate Standard separate from Direct Labour Cost Rate Standard; Calibration Candidate state machine; explainable resolution; estimate labour snapshots; actuals architecture defined but persistence deferred; ADR-029 **Proposed**; org architecture §18 automatic condition multiplier **not authorized** for labour. |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | Joel authorized FG-008 **preparation only** (analysis, architecture, Feature Gate, ADR, stale SHA/ADR-028/M009 doc cleanup). Explicitly **not** product code, migration, schema, routes, UI, live engine, pricing change, historical source mutation, commit, or push. |
| Files expected to change | Docs/governance under `docs/` only |
| Files prohibited from changing | Application code, models, migrations, routes, templates, services, tests, historical workbooks, `pricing-policy.md` rate/formula values |
| Implementation result | Documentation prepared. FG-008 **not approved**. Labour Engine **not implemented**. |
| Tests | Before edits: `./venv/bin/python -m pytest -q` → **170 passed**, 64 warnings (27.26s); `./venv/bin/python -m pytest -q tests/test_historical_ingestion.py` → **11 passed** (10.15s). After docs: same commands → **170 passed**, 64 warnings (29.54s); **11 passed** (12.79s). |
| Project-state-report update | Yes |
| Milestone entry update | Yes (architecture record FG-008; CAR-001 M009 subsequent-status correction) |
| Constitutional issue raised | None. Articles 5–6, 9, 11 respected (no schema; no invented policy; historical records not rewritten). |
| Unresolved issues | Joel approval of FG-008/ADR-029; ORG-001 canonical task seed; actuals persistence timing; historical rate-quality defects remain as evidence (not repaired). |
| Next approved step | **None for implementation.** Review FG-008. |
| Next approved prompt | **None.** |
| Commit hash | *(uncommitted documentation pass — Joel has not directed commit)* |

### 2026-08-28 — Post-FG-006 Governance & Turnover State Reconciliation

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Comprehensive documentation-only state reconciliation post-FG-006. Audit repository docs, remove stale references to uncommitted states / obsolete test baselines / old Alembic heads, align current-state, session-handoff, project-state-report, roadmap, milestones, feature gates, and ADRs with authoritative commit `690d755d9901e04eb783198f4b89071fbeaf472a`. |
| Business decision | Documentation is the governing system of record. All operational and roadmap documents must truthfully reflect the completion of M011 and FG-006 and the protected/blocked status of future calibration modules. |
| Architectural decision | Reconciled all documentation across `docs/` to canonical truth: HEAD/origin `690d755d9901e04eb783198f4b89071fbeaf472a`, Alembic head `e1b2c3d4e5f6`, 170 tests passing (11 dedicated historical ingestion tests), 20/20 source workbooks SHA-256 verified, ORG-001 private evidence, commercial evidence anchors (Mike Pratt, Julia Harish, Allen Jacques), and explicit next candidate status (Labour Engine Phase B — NOT STARTED; REQUIRES SEPARATE GOVERNANCE AUTHORIZATION). Zero code, migration, or schema changes. |
| Prompt template used | Approved custom Cursor prompt (Post-FG-006 Governance & Turnover Reconciliation) |
| Approved Cursor prompt summary | Documentation-only state reconciliation: verify repo state (HEAD `690d755`, Alembic `e1b2c3d4e5f6`, 170 tests); audit and correct stale references across docs/; update current-state, session-handoff, project-state-report, roadmap, milestones, FG-006/FG-007, ADR-028, architecture docs; validate docs-only diff; run pytest baseline; output comprehensive stopping report. |
| Files expected to change | `docs/current-state.md`, `docs/session-handoff.md`, `docs/project-state-report.md`, `docs/milestones.md`, `docs/platform-roadmap.md`, `docs/feature-gates/README.md`, `docs/feature-gates/FG-006-historical-estimate-ingestion-phase-b.md`, `docs/feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md`, `docs/adr/ADR-028-organization-foundation-and-project-commercial-context.md`, `docs/architecture/historical-estimate-ingestion-architecture.md`, `docs/architecture/historical-estimates-source-manifest.md`, `docs/architecture/organization-and-calibration-architecture.md`, `docs/README.md`, `docs/chat-workflow-log.md` |
| Files prohibited from changing | `app/*`, `migrations/*`, `tests/*`, dependencies, database records, historical source workbooks |
| Implementation result | Documentation fully reconciled and aligned across the entire repository. Working tree contains only documentation changes. |
| Tests | `./venv/bin/python -m pytest -q` → **170 passed**, 64 legacy warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | None. Repository in clean turnover state. |
| Next approved step | Ready for final turnover commit and handoff. |
| Next approved prompt | None approved (turnover state). Next candidate: Labour Engine Phase B architecture / Feature Gate preparation (NOT STARTED). |
| Commit hash | Reconciled against `690d755d9901e04eb783198f4b89071fbeaf472a` |

### 2026-08-28 — FG-006 Implementation: Historical Estimate Ingestion Engine Phase B

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Implement deterministic, organization-aware ingestion of historical estimate workbooks into CalibAi's governed evidence model (FG-006 Phase B). Ingest the 20 Brayman source workbooks into ORG-001 private intelligence. |
| Business decision | Historical workbooks contain private commercial evidence for future calibration. Ingestion must extract facts deterministically with source-cell provenance without executing macros, altering source files, or converting historical data into approved pricing/labour rates automatically. |
| Architectural decision | (1) Implemented pure Python OpenXML reader (`app/services/historical_ingestion/openxml_reader.py`) reading spreadsheet XML directly without executing macros or VBA; (2) Implemented deterministic template classifier (`template_classifier.py`) categorizing all 20 workbooks into Families A–E (9 Slab, 5 ICF, 1 Multi-trade, 1 Build, 4 Ad-hoc); (3) Implemented versioned family adapters (`family_a.py` through `family_e.py`); (4) Created canonical normalized models (`HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`); (5) Enforced organization isolation on all tables (`ORG-001`); (6) Created additive Alembic migration `e1b2c3d4e5f6`; (7) Implemented evidence review service and UI routes/templates (`/historical-estimates/`); (8) Verified 20/20 SHA-256 source file integrity before and after ingestion; (9) Implemented 10 dedicated tests in `tests/test_historical_ingestion.py`. |
| Prompt template used | Approved custom Cursor prompt (FG-006 Historical Estimate Ingestion Engine Phase B) |
| Approved Cursor prompt summary | Implement deterministic OpenXML reader, template classifier, family adapters, canonical models, additive migration, human review UI, isolation tests, pilot regression anchors, and controlled UAT ingestion of 20 Brayman workbooks into ORG-001. Stop and report. Do not commit. Do not push. |
| Files expected to change | `app/models/historical_estimates.py`, `app/models/__init__.py`, `app/services/historical_ingestion/*`, `app/services/historical_review.py`, `app/routes/historical_estimates.py`, `app/templates/historical_estimates/*`, `app/navigation.py`, `migrations/versions/e1b2c3d4e5f6_add_historical_estimate_ingestion_fg006.py`, `tests/test_historical_ingestion.py`, `docs/*` |
| Files prohibited from changing | Protected Plan Intelligence geometry, accepted proposals, current pricing policy, source historical workbooks (`~/Desktop/CalibAi Historical Estimates`), Labour Engine Phase B (blocked), Pricing Engine (blocked) |
| Implementation result | Completed FG-006 implementation and controlled ingestion. 20 source workbooks ingested into ORG-001 (661 cost items, 120 labour items, 7 subcontract items, 664 source observations, 19 quality flags). 10/10 dedicated tests pass; 169/169 full suite tests pass. 20/20 source SHA-256 hashes verified exact. |
| Tests | `./venv/bin/python -m pytest -q tests/test_historical_ingestion.py` → **11 passed**; `./venv/bin/python -m pytest -q` → **170 passed** |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | None |
| Next approved step | Governance review and commit authorization for FG-006. |
| Next approved prompt | FG-006 Commit Authorization |
| Commit hash | `690d755d9901e04eb783198f4b89071fbeaf472a` |

### 2026-08-28 — M011 Final Implementation Reconciliation: Legacy Commercial Context Correction

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Correct M011 legacy commercial context backfill semantics to prevent fabricating historical commercial decisions. Ensure pre-M011 records explicitly reflect `Legacy / Unknown` across all 7 parameters, reject `Legacy / Unknown` for new projects, display human-readable legacy notices in UI, preserve old estimate version pinning to legacy-unknown context, and verify with dedicated tests and migration validation. |
| Business decision | Pre-M011 commercial decisions were not recorded historically. Assigning arbitrary default values (e.g. Specialty, Fair Market, Self-Perform) would contaminate future CalibAi calibration/analytics. Explicit `Legacy / Unknown` semantics guarantees CalibAi will never falsely infer historical pricing posture, risk, or delivery model from pre-M011 projects. |
| Architectural decision | (1) Updated Alembic migration `d0a1b2c3d4e5` to backfill `project_commercial_contexts` with `Legacy / Unknown` for all 7 decision fields and explicit change summary/provenance; (2) Added `is_legacy_unknown` property on `ProjectCommercialContext`; (3) Enforced that `Legacy / Unknown` is rejected in `validate_commercial_context_data` on new project creation or ordinary editing; (4) Updated project detail and context edit UI templates to render a clean "Legacy project — commercial context not recorded" notice; (5) Preserved immutable reference of historical `EstimateVersion` records to the legacy-unknown v1 context even if the project is subsequently updated to v2; (6) Added dedicated tests in `tests/test_organization_foundation.py`. |
| Prompt template used | Approved custom Cursor prompt (Bounded M011 Correction) |
| Approved Cursor prompt summary | Correct legacy commercial context backfill semantics: update migration d0a1b2c3d4e5 to use explicit `Legacy / Unknown`; enforce option validation rejecting legacy-unknown on new projects; update project templates for legacy notice; add tests proving legacy unknown creation, option rejection, and estimate version pinning; re-run migration validation and pytest suite; update docs; output stopping report. Do not commit. Do not push. |
| Files expected to change | `migrations/versions/d0a1b2c3d4e5_add_organization_foundation_m011.py`, `app/models/project.py`, `app/services/commercial_context.py`, `app/templates/projects/detail.html`, `app/templates/projects/edit_context.html`, `tests/test_organization_foundation.py`, `docs/current-state.md`, `docs/session-handoff.md`, `docs/chat-workflow-log.md` |
| Files prohibited from changing | Protected Plan Intelligence geometry, accepted proposals, pricing formulas, historical workbooks |
| Implementation result | Completed legacy commercial context correction. 19/19 dedicated M011 tests pass; 159/159 full suite tests pass. Upgrade/downgrade migration cycle verified. |
| Tests | `./venv/bin/python -m pytest tests/test_organization_foundation.py -v` → **19 passed**; `./venv/bin/python -m pytest -q` → **159 passed** |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None. Protects future learning/calibration from contaminated historical assumptions. |
| Unresolved issues | None for M011. Ready for governance audit and commit. |
| Next approved step | Submit stopping report for Joel / ChatGPT review prior to governance commit. |
| Next approved prompt | Pending governance commit. |
| Commit hash | Pending governance audit (do not commit / do not push) |

### 2026-08-28 — Milestone 011 Implementation: Organization Foundation & Project Commercial Context (FG-007 / ADR-028)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Bounded product implementation of M011 authorized by FG-007 / ADR-028. Minimum organization-aware foundation, Brayman ORG-001 seed/backfill, direct ownership, tenant query scoping, versioned Project Commercial Context, immutable EstimateVersion references, policy-driven justification, and test suite. |
| Business decision | Establishes the canonical Organization entity (`ORG-001` Brayman Construction Inc.), backfills existing single-tenant data, and requires explicit 7-parameter commercial decision assumptions at project creation. Pricing calculations and multipliers remain completely unaffected in M011. |
| Architectural decision | Implemented per ADR-028: (1) `Organization` model in `app/models/organization.py`, (2) Direct `organization_id` FK on `Client`, `Project`, `CostItem`, `Assembly`, `ProposalTemplate`, (3) Composite uniqueness constraints (`organization_id` + `code`/`name`), (4) Single-tenant context helper `get_current_organization_id()` defaulting to `ORG-001`, (5) Tenant-safe fail-closed query isolation on all root and child entities, (6) Versioned `ProjectCommercialContext` with atomic V1 creation and immutable historical versions, (7) Policy-driven justification engine (`ORGANIZATION_REASON_POLICIES`), (8) Mandatory 7-parameter commercial decision gate in Project form and context update UI, (9) Immutable `EstimateVersion.commercial_context_id` capture, (10) Controlled additive Alembic migration `d0a1b2c3d4e5` with deterministic legacy backfill. |
| Prompt template used | `docs/prompts/cursor-feature-template.md` (Bounded Product Implementation) |
| Approved Cursor prompt summary | Execute M011 implementation: verify repo pins; read governing docs; implement Organization model; add direct ownership FKs; implement context helper and query isolation; implement ProjectCommercialContext model, controlled option sets, policy-driven justification; update Project creation/editing routes/templates; capture EstimateVersion context; create additive Alembic migration `d0a1b2c3d4e5` with ORG-001 seed and deterministic backfill; author `tests/test_organization_foundation.py`; verify full test suite; update governed docs; output stopping report. Do not commit. Do not push. |
| Files expected to change | `app/models/organization.py` (created), `app/models/project.py`, `app/models/client.py`, `app/models/cost_item.py`, `app/models/assembly.py`, `app/models/proposal.py`, `app/models/estimate.py`, `app/models/__init__.py`, `app/services/organizations.py` (created), `app/services/commercial_context.py` (created), `app/services/proposals.py`, `app/services/estimates.py`, `app/routes/projects.py`, `app/routes/clients.py`, `app/routes/cost_library.py`, `app/routes/assemblies.py`, `app/routes/proposal_templates.py`, `app/routes/estimates.py`, `app/routes/proposals.py`, `app/project_controls/repository.py`, `app/project_controls/routes.py`, `app/plan_intelligence/routes.py`, `app/templates/projects/form.html`, `app/templates/projects/detail.html`, `app/templates/projects/edit_context.html` (created), `migrations/versions/d0a1b2c3d4e5_add_organization_foundation_m011.py` (created), `tests/test_organization_foundation.py` (created), docs/ |
| Files prohibited from changing | Protected Plan Intelligence coordinate system/geometry, accepted proposal immutability, existing pricing formulas/gross margins, source historical workbooks |
| Implementation result | Completed full M011 implementation. All models, routes, services, templates, migrations, and test suites delivered cleanly. |
| Tests | `./venv/bin/python -m pytest -q` → **157 passed**, 61 warnings in 11.45s |
| Project-state-report update | Yes |
| Milestone entry update | Yes (M011 added to milestones) |
| Constitutional issue raised | Guaranteed customer commercial data isolation, historical assumption immutability, and policy-driven justification flexibility without modifying core pricing math. |
| Unresolved issues | None for M011. Ready for governance audit. |
| Next approved step | Submit implementation stopping report for Joel / ChatGPT review prior to governance commit. |
| Next approved prompt | FG-006 Historical Ingestion Phase B or Labour Engine Phase B prompt (after commit). |
| Commit hash | Pending governance audit (do not commit / do not push per instructions) |

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Prepare the first implementation Feature Gate (FG-007) and ADR-028 for the minimum organization-aware foundation and Project Creation Commercial Decision Gate required before Phase B Ingestion (FG-006), Labour Engine, and Calibrated Pricing Engine. |
| Business decision | Authorizes conceptual scope for `Organization` entity (`ORG-001` Brayman Construction seed/backfill), direct vs inherited ownership graph, versioned `ProjectCommercialContext` with 7 mandatory commercial decision parameters, decision provenance, and frozen estimate version context references. |
| Architectural decision | Defined ADR-028 and Feature Gate FG-007: (1) Minimal `Organization` entity, (2) Direct FK on root models (`Client`, `Project`, `CostItem`, `Assembly`, `ProposalTemplate`), (3) Inherited ownership through `Project` for child models (`Estimate`, `Proposal`, `ChangeOrder`, `PlanDocument`), (4) Dedicated versioned `ProjectCommercialContext` entity with policy-driven justification requirements, (5) Immutable `commercial_context_id` FK on `EstimateVersion`, (6) Service-level organization query scoping (`get_current_organization_id()`), (7) Controlled additive migration and backfill plan to `ORG-001` with minimal interruption objective. |
| Prompt template used | `docs/prompts/cursor-documentation-template.md` (Feature Gate Preparation) |
| Approved Cursor prompt summary | Execute 25-point Feature Gate Preparation: verify repo state; read governed state; specify M011 scope, Organization entity V1, ownership graph, tenant isolation V1, Brayman backfill strategy, Project Commercial Context V1, option sets, provenance model, estimate frozen context reference, pricing posture and execution risk invariants, estimate stage semantics, app impact audit, migration risks & mitigations, security baseline, test plan, UAT plan, ADR-028, and FG-007; update docs; confirm Phase B ingestion (FG-006), Labour Engine, and Pricing Engine remain blocked; run validation; output stopping report. |
| Files expected to change | `docs/feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md` (created), `docs/adr/ADR-028-organization-foundation-and-project-commercial-context.md` (created), `docs/feature-gates/README.md` (updated), `docs/adr/README.md` (updated), `docs/chat-workflow-log.md` (updated), `docs/current-state.md` (updated), `docs/session-handoff.md` (updated) |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, dependencies, database schema, UI, source workbooks in `~/Desktop/CalibAi Historical Estimates` |
| Implementation result | Prepared comprehensive Feature Gate FG-007, authored ADR-028, updated indexes and governance tracking documents. 0 lines of product code modified. 0 migrations created. |
| Tests | `git diff --check` (clean), `git status --short` (clean docs only) |
| Project-state-report update | Not required (Feature Gate preparation stage) |
| Milestone entry update | Not required |
| Constitutional issue raised | Guaranteed complete historical provenance for all estimate pricing assumptions and isolated customer commercial data. Prevented Brayman-specific rates from becoming CalibAi core platform defaults. |
| Unresolved issues | None for Feature Gate preparation. M011 implementation is NOT authorized and awaits explicit Joel / ChatGPT approval. Phase B Ingestion (FG-006), Labour Engine, and Calibrated Pricing Engine remain BLOCKED. |
| Next approved step | Submit FG-007 and ADR-028 for Joel Brayman / ChatGPT governance review and implementation authorization. |
| Next approved prompt | M011 Implementation Prompt (if approved). |
| Commit hash | Working tree uncommitted (pending governance review per instructions) |

### 2026-08-28 — CalibAi / Brayman Estimator: Organization & Calibration Architecture — Phase A

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Establish organization-aware commercial architecture required before CalibAi can implement organization-specific pricing, labour calibration, historical ingestion, or commercial learning. |
| Business decision | Governing Principle: CalibAi owns the engine and methodology; each customer organization owns its commercial intelligence; Brayman Construction is the first development/UAT organization (Org 001), not the universal CalibAi pricing model. |
| Architectural decision | Defined 3-tier commercial architecture (CalibAi Core vs Baseline Library vs Organization Calibration Model); specified canonical `Organization` entity; built Data Ownership Matrix; established 7-tier Evidence Hierarchy (`ORG-APPROVED`, `CURRENT`, `ORG-ACTUAL`, `ORG-HISTORICAL`, `BASELINE`, `PROVISIONAL`, `MANUAL`) with ORG-APPROVED as active operating standard and ORG-ACTUAL as empirical calibration evidence proposing review candidates; defined 7-phase Calibration Lifecycle and version immutability; specified 7-level Rate Resolution Cascade; defined 7-parameter Project Commercial Decision Gate with provenance and reason requirements; separated Direct Cost Economics from Commercial Pricing Strategy; defined multi-tenant isolation; prohibited cross-organization benchmarking; generalized analytical learning to technology-neutral methods; audited existing application models and routes (zero impact in Phase A; additive migration path for Phase B). |
| Prompt template used | `docs/prompts/cursor-architecture-template.md` (Architecture & Governance Specification) |
| Approved Cursor prompt summary | Execute 28-point Organization & Calibration Architecture Phase A: verify repo state; read governed state; specify CalibAi Core vs Baseline vs Org Model, canonical Organization, Data Ownership Matrix, Evidence Hierarchy, Calibration Lifecycle & Versioning, Rate Resolution Cascade, Commercial Decision Gate, Provenance, Reason Requirements, Pricing Posture, Execution Risk, Historical Learning, Tenant Isolation, Benchmarking Prohibition, Ingestion/Labour/Pricing Reconciliations, Branding, Integrations, UAT Org 001, Read-Only Impact Audit; generate `docs/architecture/organization-and-calibration-architecture.md`; update docs; enforce Phase B blocking condition; run test suite (140 passed); output stopping report. |
| Files expected to change | `docs/architecture/organization-and-calibration-architecture.md` (created), `docs/README.md` (updated), `docs/chat-workflow-log.md` (updated), `docs/current-state.md` (updated), `docs/session-handoff.md` (updated) |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, dependencies, source workbooks in `~/Desktop/CalibAi Historical Estimates` |
| Implementation result | Completed comprehensive 25-section architecture specification (`docs/architecture/organization-and-calibration-architecture.md`), updated README, current-state, session-handoff, and chat-workflow-log. 0 lines of app/migration/test code modified. |
| Tests | `git diff --check` (clean), `./venv/bin/python -m pytest -q` (140 passed) |
| Project-state-report update | Not required (Phase A is architectural specification stage) |
| Milestone entry update | Not required |
| Constitutional issue raised | Confirmed customer commercial data ownership, multi-tenant isolation, and strict prohibition on cross-organization benchmarking without legal governance. Decoupled physical direct cost economics from commercial pricing strategy. |
| Unresolved issues | None for Phase A. Phase B Ingestion (FG-006), Labour Engine (Phase B), and Calibrated Pricing Engine remain BLOCKED pending review and approval of this Phase A architecture. |
| Next approved step | Submit Phase A Organization & Calibration Architecture package for Joel / ChatGPT governance review. |
| Next approved prompt | FG-006 Historical Ingestion Engine (Phase B) Feature Gate prompt. |
| Commit hash | Working tree uncommitted (pending governance review per instructions) |

### 2026-08-28 — Historical Estimate Ingestion — Phase A (Source Audit & Ingestion Architecture)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Perform read-only source data audit, profiling, and ingestion architecture design across 20 historical Brayman estimating workbooks located outside Git repository |
| Business decision | Historical estimates are commercial evidence of past pricing and estimating patterns, not automatic pricing truth or proof of profitability. Raw customer workbooks remain external and immutable. |
| Architectural decision | Categorized 20 workbooks into 5 template families (Family A: 9, Family B: 5, Family C: 1, Family D: 1, Family E: 4). Discovered historical workbooks use Cost-Plus Markup (10-15%) rather than true Gross Margin. Defined organization-neutral cell-level provenance model, 8-tier data quality / contradiction model, 6-tier historical evidence hierarchy, and canonical normalized schema design with Organization ownership. |
| Prompt template used | `docs/prompts/cursor-architecture-template.md` (Read-only audit & architecture) |
| Approved Cursor prompt summary | Read-only inspect `~/Desktop/CalibAi Historical Estimates`; calculate SHA-256 hashes; profile structure & content; detect pricing methods; design cell-level provenance, contradiction model, evidence hierarchy, and normalized schema; run pilot extraction on 5 workbooks; produce manifest and architecture specification; verify source files unchanged; do not commit. |
| Files expected to change | `docs/architecture/historical-estimates-source-manifest.md` (created), `docs/architecture/historical-estimate-ingestion-architecture.md` (created), `docs/chat-workflow-log.md` (updated), `docs/current-state.md` (updated), `docs/session-handoff.md` (updated) |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, dependencies, source workbooks in `~/Desktop/CalibAi Historical Estimates` |
| Implementation result | Completed full 20-workbook forensic audit, generated source provenance manifest, created comprehensive ingestion architecture specification, conducted 5-workbook pilot extraction, verified 100% source byte immutability. No code, migrations, or UI modified. |
| Tests | Python verification scripts for OpenXML zip parsing, SHA-256 integrity, cell extraction; `./venv/bin/python -m pytest -q` (140 passed) |
| Project-state-report update | Not required (Phase A is research / architecture stage) |
| Milestone entry update | Not required |
| Constitutional issue raised | Identified pricing methodology gap between historical cost-plus markup and governing 15% true gross margin policy (`pricing-policy.md` / `ADR-025`). Confirmed CalibAi Core vs Customer Organization separation. |
| Unresolved issues | None for Phase A. Phase B is explicitly blocked pending review and approval of CalibAi Organization & Calibration Architecture — Phase A. |
| Next approved step | Execute Organization & Calibration Architecture Phase A before any Phase B implementation. |
| Next approved prompt | Organization & Calibration Architecture — Phase A prompt. |
| Commit hash | `3461d2eb791d6382eab71e43d15f6b54b62a9192` (`3461d2e`) |

### 2026-08-28 — Implement Milestone 010 (Scale Calibration & Manual Measurement Tools)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Implement M010 Scale Calibration and Manual Measurement Tools strictly per FG-005: durable scale calibration and measurement models, additive migration, service layer, human confirmation workflow, normalized document coordinates, interactive PDF.js viewer, and focused test suite. |
| Business decision | Estimators can calibrate physical scale on reviewed drawing sheets using 2-point reference dimensions or standard architectural/metric presets, define multi-scale viewports, and take manual linear, polyline, polygon area (Shoelace) / perimeter, and count measurements with coordinate stability. |
| Architectural decision | Additive models `PlanScaleCalibration` and `PlanMeasurement` under `PlanSheet` (scoped to `DrawingRevision`). ADR-026 and ADR-027 marked Accepted. Normalized document coordinate system (`[0.0, 1.0]`) rendered via Mozilla PDF.js in Flask templates with interactive SVG/Canvas overlay. Human confirmation required; uncalibrated/NTS fails closed. Additive migration `c9e0f1a2b3d4`. |
| Prompt template used | Approved custom Cursor implementation prompt (FG-005 Approved) |
| Approved Cursor prompt summary | Anti-drift preflight; mark ADR-026/027 Accepted; verify Alembic head `b8d9f0a1c2e3`; implement models, migration `c9e0f1a2b3d4`, services (`scale_measurement.py`), routes, viewer template (`sheet_measure.html`), controller (`sheet-measurement.js`); 19 focused tests in `tests/test_scale_measurement.py`; full test suite; documentation update; commit and push. |
| Files expected to change | `app/plan_intelligence/models.py`, `app/plan_intelligence/routes.py`, `app/plan_intelligence/scale_measurement.py`, `app/templates/plan_intelligence/**`, `app/static/js/**`, `migrations/versions/c9e0f1a2b3d4_add_scale_measurement_m010.py`, `tests/test_scale_measurement.py`, documentation. |
| Files prohibited from changing | Estimating commercial calculations, Proposals, Change Orders, CRM, Auth, Contracts, QuickBooks. |
| Implementation result | Full M010 implementation completed and verified. 19 focused tests pass. Full test suite (140 tests) pass. |
| Tests | `pytest tests/test_scale_measurement.py -v` (19 passed), `pytest -q` (140 passed) |
| Project-state-report update | Yes |
| Milestone entry update | Yes — Milestone 010 |
| Constitutional issue raised | None. Human authority strictly enforced (no auto-confirmation of scale). |
| Unresolved issues | None for M010. Automated quantity take-off deferred to M011+. |
| Next approved step | Feature Gate and architecture for M011 — AI Take-off / Quantity Extraction Foundation. |
| Next approved prompt | M011 Feature Gate prompt |
| Commit hash | `6b969fe` — *feat: implement M010 scale calibration* |

### 2026-08-28 — Prepare and Approve M010 Scale Calibration Feature Gate (FG-005)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Prepare the formal Feature Gate FG-005 and architecture records for M010 — Scale Calibration / Measurement Tools. No product code, schema changes, or migrations. |
| Business decision | Estimators can calibrate physical scale on reviewed drawing sheets using 2-point reference dimensions or standard ratios, define multi-scale viewports, and take manual linear, polyline, area, and count measurements with coordinate stability. |
| Architectural decision | Additive models `PlanScaleCalibration` and `PlanMeasurement` under `PlanSheet` (scoped to `DrawingRevision`). Normalized document coordinate system (`0.0 to 1.0` / 72 DPI PDF points) rendered via Mozilla PDF.js in Flask templates with interactive SVG/Canvas overlay. Human authority required for confirmation; uncalibrated/NTS fails closed. Proposed ADR-026 (Scale Ownership & Multi-Scale Provenance) and ADR-027 (PDF Rendering & Normalized Coordinate System). |
| Prompt template used | Approved custom Cursor prompt (documentation/governance) |
| Approved Cursor prompt summary | Anti-drift preflight; existing-before-new search; create `docs/feature-gates/FG-005-m010-scale-calibration.md`, `docs/adr/ADR-026-scale-ownership-and-calibration-provenance.md`, `docs/adr/ADR-027-pdf-rendering-and-normalized-coordinate-system.md`; update indexes, roadmap, milestones, state, handoff, and log; validate; commit; push. |
| Files expected to change | Documentation and governance files only |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas |
| Implementation result | FG-005 prepared and approved; ADR-026 and ADR-027 proposed; governance indexes and state reports updated. M010 code not begun. |
| Tests | `git diff --check`, `pytest -q` (121 passed) |
| Project-state-report update | Yes |
| Milestone entry update | Yes (`milestones.md` FG-005 added) |
| Constitutional issue raised | None |
| Unresolved issues | None for FG-005 |
| Next approved step | Dedicated M010 implementation Cursor prompt citing FG-005 |
| Next approved prompt | M010 implementation prompt |
| Commit hash | `f8da43c` |

### 2026-08-28 — Review Turnover Reconciliation Repair

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Repair Review Turnover package and governance documents: reconcile accepted ADR list (ADR-002, 017, 018, 019, 020, 022, 023, 024), classify PRICE as PARTIAL (pricing policy calculation migration Proposed in ADR-025), correct LEARN reference to ADR-024, align baseline pins (`5dc4b09` implementation, `39ae8fe` turnover adoption), and remove stale pre-implementation notes. |
| Business decision | Maintain rigorous anti-drift discipline so that repository documents remain 100% authoritative and internally consistent. |
| Architectural decision | No product code or schema changes. ADR statuses, lifecycle classifications, and baseline pins reconciled to exact repository truth. |
| Prompt template used | Approved custom Cursor prompt (documentation/governance repair) |
| Approved Cursor prompt summary | Preflight; audit 22-point turnover package; repair ADR list, lifecycle states, LEARN boundary, and baseline pins across `session-handoff.md`, `review-turnover-protocol.md`, `current-state.md`, `project-state-report.md`, `platform-roadmap.md`, and `milestones.md`; validate; commit; push. |
| Files expected to change | Documentation and governance files only |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas |
| Implementation result | All four known defects and remaining documentation inconsistencies reconciled. Completeness test passed. |
| Tests | `git diff --check`, `pytest -q` (121 passed) |
| Project-state-report update | Yes (Part B fully updated) |
| Milestone entry update | Yes (`milestones.md` FG-004 and M009 updated) |
| Constitutional issue raised | None |
| Unresolved issues | None |
| Next approved step | Prepare Feature Gate for M010 Scale Calibration / Measurement Tools |
| Next approved prompt | M010 Feature Gate |
| Commit hash | `ed3e51f` |

### 2026-08-28 — Adopt Review Turnover Protocol

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Adopt the comprehensive repository-backed Review Turnover Protocol triggered by the exact phrase `Review Turnover` for safe chat rollover and anti-drift reconciliation. |
| Business decision | Enable deterministic, repository-backed session turnover so any long/stale conversation can be discarded and a fresh session started from repository evidence alone. |
| Architectural decision | Review Turnover Protocol (`docs/governance/review-turnover-protocol.md`) adopted as governing. Chat is expendable upon `TURNOVER PASS`. `docs/session-handoff.md` integrated with 22-point standard turnover package. |
| Prompt template used | Approved custom Cursor prompt (governance-only) |
| Approved Cursor prompt summary | Anti-drift preflight; existing-before-new search; create `docs/governance/review-turnover-protocol.md`; integrate governance docs (`AGENTS.md`, `README.md`, `continuity-and-anti-drift.md`, `platform-governance.md`, `development-workflow.md`, `session-handoff.md`, `current-state.md`); validate; commit; push. |
| Files expected to change | Governance and documentation files only |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas |
| Implementation result | Protocol adopted. All governance references updated. 22-point turnover package and startup prompt integrated in session handoff. |
| Tests | `git diff --check`, `pytest -q` (121 passed) |
| Project-state-report update | Yes |
| Milestone entry update | Not required (governance update, not a new coded milestone) |
| Constitutional issue raised | None |
| Unresolved issues | None |
| Next approved step | Prepare Feature Gate for M010 Scale Calibration / Measurement Tools |
| Next approved prompt | M010 Feature Gate |
| Commit hash | `39ae8fe` |

### 2026-08-28 — Implement M009 Sheet Classification / Human Metadata Review

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Implement authorized M009 scope per FG-004: Sheet models, page mappings, suggestions, human review workflow (accept/edit/reject/void), uniqueness validation, migration, and office review UI. |
| Business decision | Estimators can classify PDF pages into logical drawing Sheets, review suggestions with human authority, manage non-1:1 page mappings, and validate/finalize revision sheet indices before downstream scale/take-off. |
| Architectural decision | Additive schema `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions`, and `sheet_id` on audit events. Suggestions never silently set SoR. Uniqueness scoped to `DrawingRevision`. Page ≠ Sheet preserved; source documents and pages immutable. |
| Prompt template used | Approved custom Cursor implementation prompt for M009 (FG-004 approved) |
| Approved Cursor prompt summary | Anti-drift preflight; verify Alembic head; implement authorized models, migration `b8d9f0a1c2e3`, service layer, office UI, tests, and documentation; run test suite; commit and push. |
| Files expected to change | `app/plan_intelligence/*`, `migrations/versions/*`, `tests/test_sheet_intelligence.py`, `app/templates/plan_intelligence/*`, governance/module docs |
| Files prohibited from changing | Estimating, proposals, change orders, CRM, pricing calculation, auth, field/mobile |
| Implementation result | M009 fully implemented. Migration `b8d9f0a1c2e3` applied cleanly. All 15 focused tests and 121 total suite tests pass. |
| Tests | `pytest tests/test_sheet_intelligence.py -q` (15 passed); `pytest -q` (121 passed) |
| Project-state-report update | Yes |
| Milestone entry update | Milestone 009 appended |
| Constitutional issue raised | None |
| Unresolved issues | None for M009 |
| Next approved step | Prepare Feature Gate for M010 Scale Calibration / Measurement Tools |
| Next approved prompt | M010 Feature Gate |
| Commit hash | `5dc4b09` |

### 2026-08-28 — Approve M009 Sheet Feature Gate (FG-004)

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Governance only: accept ADR-017/018 if consistent; create/approve FG-004 for M009. No product code. |
| Business decision | M009 = Sheet classification / human metadata review. FG-004 approved. Implementation awaits a dedicated Cursor prompt. |
| Architectural decision | ADR-017/018 **Accepted** without redesign. Page ≠ Sheet, human SoR, Plan Intelligence ownership, Project hub. ADR-014 document remains Proposed. |
| Prompt template used | Approved custom Cursor prompt (documentation-only) |
| Approved Cursor prompt summary | Preflight; existing-before-new; accept 017/018 or STOP; write FG-004; integrate docs; validate; commit; push; stop. Do not begin M009 code. |
| Files expected to change | Feature Gate, ADRs 017/018 status, indexes, state/handoff/log/roadmap/module docs |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas |
| Implementation result | FG-004 created and approved. ADR-017/018 Accepted. M009 code not begun. |
| Tests | Docs-only: `git diff --check`; link check. No pytest invented. |
| Project-state-report update | Yes |
| Milestone entry update | FG-004 architecture/authorization record appended; M008 not rewritten |
| Constitutional issue raised | None |
| Unresolved issues | ADR-014 formal status; SQLite uniqueness mechanism (either allowed); M009 implementation prompt |
| Next approved step | Dedicated **M009 implementation Cursor prompt** citing FG-004 |
| Next approved prompt | M009 implementation (not this Gate) |
| Commit hash | This adoption commit (see stopping report SHA) |

### 2026-08-28 — CAR-001 CalibAi architecture & product vision adoption

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Documentation/governance only: adopt CAR-001 approved CalibAi vision and architecture. No product code. Do not begin M009. |
| Business decision | CalibAi vision (PLAN→PRICE→CONTRACT→BUILD→MONITOR→LEARN); office+field complementary; V1 direction; sequence recorded as roadmap only. Repository not renamed. |
| Architectural decision | ADR-019/020/022/023/024 **Accepted** (direction). ADR-021 and ADR-025 **Proposed**. Project remains hub. BUILD ≠ Change Orders. API-before-native. Field evidence original vs derived. LEARN cannot mutate pricing/cost library. M009 remains coded Sheets; CAR-001 is not M009. |
| Prompt template used | Approved custom Cursor prompt (documentation-only; equivalent constraints to cursor-documentation-template) |
| Approved Cursor prompt summary | Preflight; existing-before-new; create CAR-001 record; update vision; ADRs; V1/sequence/pricing record; minimum drift fixes; validate; commit; push; stop. |
| Files expected to change | Docs, ADRs, modules, roadmap, state/handoff/log only |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas, product rename |
| Implementation result | CAR-001 recorded. Vision updated. ADRs 019–025 created. M009 code not begun. |
| Tests | Docs-only: `git diff --check`; link check; no pytest invented |
| Project-state-report update | Yes |
| Milestone entry update | CAR-001 architecture record appended; M008/M009 numbers not rewritten |
| Constitutional issue raised | None. Constitution not amended. |
| Unresolved issues | ADR-021, ADR-025, ADR-017/018; M009 Feature Gate |
| Next approved step | Stop. Next coded work is Feature-Gated **M009** when Joel authorizes it. |
| Next approved prompt | None |
| Commit hash | This adoption commit (see stopping report SHA) |

### 2026-08-28 — Adopt CalibAi Continuity & Anti-Drift Protocol

| Field | Content |
|-------|---------|
| Date | 2026-08-28 |
| Branch | `main` |
| Objective | Governance-only: formally adopt the approved CalibAi Continuity & Anti-Drift Protocol before any product/architecture reconciliation |
| Business decision | Joel approved adoption of the protocol; AI memory is never authoritative project state; repository remains the system of record |
| Architectural decision | None. Protocol supplements Constitution Article 1 and existing context-drift stop; Constitution not amended. Product/repository not renamed. |
| Prompt template used | Approved custom Cursor prompt (documentation-only constraints equivalent to [cursor-documentation-template.md](prompts/cursor-documentation-template.md)) |
| Approved Cursor prompt summary | Reconstruct state; existing-before-new search; create `docs/governance/continuity-and-anti-drift.md`; minimum governance integration; validate; commit; push if permitted; stop. No product code, schema, migrations, or M009. |
| Files expected to change | New protocol doc; minimum references in AGENTS.md, docs/README.md, platform-governance, development-workflow, current-state, project-state-report, chat-workflow-log, aiRIA-lessons-adopted, session-handoff |
| Files prohibited from changing | `app/`, `migrations/`, `tests/`, models/schemas, product features; Constitution; product/repository rename |
| Implementation result | Protocol created as APPROVED/GOVERNING. Existing drift rules preserved. Constitution not amended. M009 not begun. |
| Tests | Docs-only: `git diff --check`; link resolution; confirm no application/schema/migration changes. No pytest invented. Exact results in stopping report. |
| Project-state-report update | Yes — protocol adoption recorded |
| Milestone entry update | No — not a product milestone |
| Constitutional issue raised | None. Protocol supplements Article 1; Constitution left unchanged. |
| Unresolved issues | Product/architecture reconciliation not started (separate authorization required) |
| Next approved step | Stop. Do not begin M009. Next: Joel-authorized CalibAi product/architecture reconciliation (separate prompt). |
| Next approved prompt | None |
| Commit hash | This adoption commit (see stopping report SHA) |

### 2026-08-26 — Governance closure after commit 0fdf0d4

| Field | Content |
|-------|---------|
| Date | 2026-08-26 |
| Branch | `main` (tip at or after `ee100ac` = `origin/main`; confirm with `git rev-parse`) |
| Objective | Documentation-only state correction: clear stale transient journal facts after August reconciliation was committed and pushed |
| Business decision | No new product requirements; correct current pins only |
| Architectural decision | Unchanged |
| Approved Cursor prompt summary | Docs-only closure; commit/push allowed if validation passes and only governed docs change |
| Files expected to change | State/journal docs (`current-state`, `session-handoff`, `project-state-report`, `platform-roadmap`, `chat-workflow-log`) |
| Files prohibited from changing | app/, migrations/, tests/, dependencies; architecture/pricing/legal/UAT substance |
| Implementation result | Transient pins cleared; August reconciliation recorded as `0fdf0d4`; state closure tip `ee100ac` (plus any pin-alignment follow-up on `main`) |
| Next approved step | ADR-017/018; Feature Gate before coded Sheets (**not started**) |
| Commit hash | `ee100ac` (initial closure); confirm tip with `git rev-parse` |

### 2026-08-25 — Subsequent commit/push of August governance reconciliation

| Field | Content |
|-------|---------|
| Date | 2026-08-25 |
| Branch | `main` |
| Objective | Record actual outcome after Joel-directed commit-and-push (separate from the original no-commit reconciliation prompt) |
| Historical note | The original August 25 reconciliation prompt instructed **documentation only** and **no commit/push at that stage**. Commit/push occurred **subsequently**, not under that original prompt. |
| Outcome | Local checkpoint `ed36838` pushed; governance reconciliation committed as `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* (18 documentation files); `HEAD` = `origin/main` = `0fdf0d4`; working tree clean after that push |
| Files prohibited from changing | app/, migrations/, tests/ (unchanged) |
| Commit hash | `0fdf0d4` |

### 2026-08-25 — Governance reconciliation (authoritative record, document package, pricing, legal gate)

| Field | Content |
|-------|---------|
| Date | 2026-08-25 |
| Branch | At work time: `main` @ local `ed36838`; `origin/main` then `ee9b4b2` |
| Objective | Documentation-only governance reconciliation; preserve post-M008 state sync; record August 25 product/governance requirements |
| Business decision | One authoritative estimate record; four core outputs; pricing reference rule ($65/hr, 15% gross margin); no silent placeholders; 3415 Roger Stevens UAT reference case |
| Architectural decision | QuickBooks pipeline boundary (no API); Legal Content Gate for Ontario contract/warranty; context drift mandatory stop; PRESERVE → SEARCH → VERIFY → EXECUTE |
| Prompt template used | August 25, 2026 governance reconciliation prompt (documentation-only) |
| Approved Cursor prompt summary | Docs only; preserve six pre-existing state-sync modifications; no app/migrations/tests/deps; **original prompt forbade commit/push at that stage** |
| Files expected to change | `docs/` governance and state files only |
| Files prohibited from changing | app/, migrations/, tests/, dependencies |
| Implementation result | Extended state docs; new pricing policy, document package, QuickBooks architecture, legal template governance, UAT reference case (working tree dirty until subsequent commit) |
| Tests | Not run (documentation-only by design) |
| Project-state-report update | Yes |
| Milestone entry update | No new coded milestone |
| Subsequent outcome | Commit/push was **not** authorized by this prompt; occurred later under a separate Joel-directed commit-and-push → `0fdf0d4` (see entry above) |
| Next approved step | Joel review; then separate commit authorization; ADR-017/018; Feature Gate before coded Sheets |
| Commit hash | None under this prompt (forbade commit); subsequent `0fdf0d4` |

### 2026-07-25 — Repository state sync after M005–M008 merge to main

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `ee9b4b2` (then tip of `origin/main`) |
| Objective | Synchronize state/roadmap/milestone docs with merged Git reality |
| Business decision | Record M005–M008 as merged; do not start coded Sheets |
| Architectural decision | Unchanged — Sheet Intelligence remains architecture/readiness only |
| Files expected to change | `docs/current-state.md`, `project-state-report.md`, `session-handoff.md`, `platform-roadmap.md`, `milestones.md`, `chat-workflow-log.md` |
| Files prohibited from changing | app/, migrations/, tests/ |
| Implementation result | Docs updated to reflect M005–M008 merged on `origin/main`; preserved in local commit `ed36838` |
| Next approved step | Joel ADR-017/018 review; Feature Gate before sheet implementation |
| Commit hash | `ed36838` (local checkpoint; subsequently pushed with `0fdf0d4`) |

### 2026-07-25 — Milestone 008 Sheet Intelligence architecture

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `milestone-008-sheet-intelligence` |
| Objective | Architecture for Sheets from indexed Pages; register docs in indexes/state; **no code** |
| Business decision | Design Sheet Intelligence before any sheet tables/UI |
| Architectural decision | ADR-017 suggestion accept/reject/edit; ADR-018 uniqueness/supersession; first coded sheets require a later Feature Gate; scale/AI POC later |
| Files expected to change | docs only (ADR-017/018, sheet-intelligence.md, M008 readiness, indexes, roadmap, state) |
| Files prohibited from changing | app/, migrations/, tests/ |
| Implementation result | Architecture + readiness docs integrated; Sheets remain unimplemented |
| Tests | Docs validation only (`git diff --check`, link check) |
| Project-state-report update | Yes |
| Milestone entry update | Yes — M008 |
| Next approved step | Merged to `main` via PR #6 |
| Commit hash | `8c74e31` (merged in `ee9b4b2`) |

### 2026-07-25 — Milestone 007 Document Indexing

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `milestone-007-document-indexing` |
| Objective | Implement Document Indexing: pages, deterministic/embedded-text extraction, provenance, archive, audit, relational search |
| Business decision | First coded DI phase after FG-003 CONDITIONAL PASS conditions |
| Architectural decision | Page ≠ Sheet; immutable raw payloads; archive-over-delete; relational search (ADR-016 Stage 1); ADR-015 provenance |
| Files expected to change | `app/plan_intelligence/**`, models, templates, migration `a7c8e9f0b1d2`, `tests/test_plan_indexing.py`, M007 docs/ADRs |
| Files prohibited from changing | Estimating commercial writes; Sheet entity implementation; OCR/CAD/AI take-off |
| Implementation result | Indexing models/services/UI/migration/tests; Estimating untouched |
| Tests | Plan indexing + upload tests; full suite **106 passed** |
| Next approved step | Merged to `main` via PR #5 |
| Commit hash | `cbefe7a` (merged in `eb00123`) |

### 2026-07-25 — Milestone 006 Document Intelligence refinement (CONDITIONAL PASS)

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `milestone-005-plan-intelligence-phase-a` |
| Objective | Expand M006 to full prompt: CONDITIONAL PASS, Page/Sheet edge cases, processing provenance, staged search, revised M007–M010 |
| Business decision | Do not authorize DI code on FG-003 alone; require explicit conditions |
| Architectural decision | FG-003 **CONDITIONAL PASS**; ADR-015 provenance; ADR-016 staged search; M007=indexing/extraction; sheet review / scale / AI POC = later Feature-Gated milestones |
| Prompt template used | Milestone 006 Document Intelligence Architecture and Feature Gate (expanded) |
| Files expected to change | docs only |
| Files prohibited from changing | app/, migrations/, tests/, dependency files |
| Implementation result | Docs refined; no code |
| Tests | Docs validation only (status, diff --check, link check) |
| Project-state-report update | Yes |
| Milestone entry update | Yes |
| Constitutional issue raised | None |
| Unresolved issues | Joel acceptance of conditions + ADR-013–016 |
| Next approved step | M007 Feature Gate when conditions satisfied |
| Next approved prompt | None |
| Commit hash | **None** (prompt forbids commits/pushes) |

### 2026-07-25 — Milestone 006 Document Intelligence architecture

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `milestone-005-plan-intelligence-phase-a` @ `098647c` |
| Objective | Document Intelligence architecture + FG-003; no code |
| Business decision | Insert DI layer between Phase A upload and take-off |
| Architectural decision | FG-003 **PASS**; ADR-013 (DI inside Plan Intelligence); ADR-014 (sheet ≠ page); M005 supports additive DI |
| Prompt template used | Milestone 006 architecture & Feature Gate prompt |
| Approved Cursor prompt summary | Docs only; evaluate M005 compatibility; FG-003; ADRs only if required; no commits |
| Files expected to change | docs only (FG, ADR, architecture, roadmap, milestones, state) |
| Files prohibited from changing | app/, migrations/, tests/ |
| Implementation result | FG-003 PASS; document-intelligence.md; M006 readiness report; ADR-013/014; governance updates |
| Tests | Not run (docs-only milestone by design) |
| Project-state-report update | Yes |
| Milestone entry update | Yes — M006 |
| Constitutional issue raised | None |
| Unresolved issues | Joel acceptance of ADR-013/014; M007 implementation authorization |
| Next approved step | Joel review/commit docs; Feature Gate M007 when ready |
| Next approved prompt | None |
| Commit hash | Pending |

### 2026-07-25 — Milestone 005 FG-002 + Phase A PDF upload

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `c59ec01` (uncommitted M004+M005) |
| Objective | ADR-012; FG-002 pass; Phase A PDF upload/storage only |
| Business decision | Authorize Phase A foundation; defer revision UI |
| Architectural decision | ADR-012 Proposed (drawing set/revision ownership); flat `plan_documents` interim |
| Prompt template used | Milestone 005 implementation prompt |
| Approved Cursor prompt summary | FG-002 + Phase A; no OCR/CAD/AI/estimate insert; no commits |
| Files expected to change | plan_intelligence package; templates; migration; tests; governance docs |
| Files prohibited from changing | Estimating redesign; Proposals immutability; unrelated modules |
| Implementation result | FG-002 Approved; ADR-012 docs; Phase A routes/services/storage/migration/tests |
| Tests | `pytest tests/test_plan_upload.py` — 8 passed; full suite `./venv/bin/python -m pytest -q` → **97 passed**, 68 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes — M005 |
| Constitutional issue raised | None |
| Unresolved issues | Commit pending; ADR-012 acceptance; Phase B gate |
| Next approved step | Joel review/commit; Feature Gate Phase B when ready |
| Next approved prompt | None |
| Commit hash | Pending |

### 2026-07-25 — Milestone 004 Plan Intelligence architecture

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `c59ec01` |
| Objective | Architecture/docs for Plan Intelligence pipeline, model, review, traceability, estimate mapping, ADRs, POC — no code |
| Business decision | Plan Intelligence is the next strategic differentiator (plans → take-off → estimate → proposal) |
| Architectural decision | PDF-first; human approval mandatory; citations first-class; confidence thresholds via ADR-011; feed estimate builder without redesign |
| Prompt template used | Documentation / architecture |
| Approved Cursor prompt summary | Docs only; no app/migrations/tests/deps/commits |
| Files expected to change | `docs/modules/plan-intelligence.md`, `docs/architecture/**`, ADRs, roadmap/milestones/state |
| Files prohibited from changing | `app/**`, `migrations/**`, `tests/**`, `requirements.txt` |
| Implementation result | Architecture expanded; module rewritten; readiness report; ADR-011 added; ADR-005/006 updated |
| Tests | Not re-run (docs-only). Last verified: 89 passed, 53 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes — Milestone 004 |
| Constitutional issue raised | Reinforced no silent AI commercial insert |
| Unresolved issues | ADR acceptance; Phase A Feature Gate; numeric confidence values |
| Next approved step | Joel review; commit M004 docs when directed |
| Next approved prompt | None until Phase A Feature Gate |
| Commit hash | Pending |

### 2026-07-25 — Milestone 003 Accepted Proposal Immutability

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` |
| Objective | Block all mutations when proposal.status == Accepted; preserve view/preview/PDF |
| Business decision | Accepted proposals never reopen/silently rewrite; void/supersede/revision deferred |
| Architectural decision | Central `ensure_proposal_mutable`; recalculate guarded except create-time snapshot flag |
| Prompt template used | Feature (Milestone 003 prompt) |
| Approved Cursor prompt summary | Service guard + UI + tests; no migration; no acceptance workflow; no commit |
| Files expected to change | `app/services/proposals.py`, routes/templates proposals, tests, minimal docs |
| Files prohibited from changing | migrations, estimate builder, unrelated modules |
| Implementation result | Guard implemented; UI read-only for Accepted; tests added |
| Tests | `./venv/bin/python -m pytest -q` → **89 passed**, 53 warnings; focused immutability file 11 passed |
| Project-state-report update | Milestone 003 recorded; full state refresh at commit |
| Milestone entry update | Yes — Milestone 003 |
| Constitutional issue raised | Closed for Accepted silent rewrite (Article 5 / Rule 3) |
| Unresolved issues | Void/supersede workflow not built |
| Next approved step | Joel review; commit when directed |
| Next approved prompt | None until Joel Feature-Gates next milestone |
| Commit hash | Pending |

### 2026-07-25 — Strategic architecture: Plan Intelligence + Supplier pillars

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `71e2754` (+ uncommitted M002 docs) |
| Objective | Update strategic roadmap pillars; create Plan Intelligence and Supplier architecture docs; Phases A–G; narrow POC; ADR-005–010 — documentation only |
| Business decision | Long-term differentiator is plan→take-off→estimate→supplier pricing→proposal/PO with human review and citations; PDF-first |
| Architectural decision | ADR-005–010 Proposed; Plan Intelligence and Supplier Catalogue as Future modules; no claim of existing integrations |
| Prompt template used | Documentation / architecture |
| Approved Cursor prompt summary | Docs only; no app/migrations/deps/commits; distinguish current vs future |
| Files expected to change | `docs/platform-roadmap.md`, `docs/platform-vision.md`, `docs/architecture/**`, `docs/adr/ADR-005`–`010`, module stubs, indexes, milestones/state |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, requirements |
| Implementation result | Architecture docs + ADRs + roadmap pillars created; no application code changed |
| Tests | Full suite not re-run; last verified 78 passed, 43 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Milestone 002 deliverables extended |
| Constitutional issue raised | Reinforced no silent AI commercial overwrite (Articles 5–6) |
| Unresolved issues | Joel ADR acceptance; M003 vs Phase A sequencing |
| Next approved step | Joel review; commit docs when directed |
| Next approved prompt | None for implementation |
| Commit hash | Pending |

### 2026-07-25 — Milestone 002 Product Architecture Review (Proposals FG + ADRs)

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `71e2754` (start) |
| Objective | Feature Gate FG-001 for Proposals; draft ADR-001–004; recommend next implementation milestone — documentation only |
| Business decision | Treat existing Proposal Builder as complete foundation; prioritize Accepted immutability before acceptance workflow / project creation |
| Architectural decision | ADRs Proposed: snapshot ownership (001); Accepted immutability (002); defer CRM FKs (003); acceptance workflow after immutability (004) |
| Prompt template used | Documentation / architecture review (aligned with cursor-documentation-template / cursor-review-template) |
| Approved Cursor prompt summary | Create FG + ADRs; update module/roadmap/milestones/state docs; no app/schema/migration/UI changes; no commit |
| Files expected to change | `docs/feature-gates/**`, `docs/adr/ADR-001`–`004`, proposals module, indexes, milestones, roadmap, state/handoff/log |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, models, routes, templates, services |
| Implementation result | FG-001 + ADR-001–004 created; cross-links updated; no application code changed |
| Tests | Full suite **not re-run**. Last verified remains **78 passed**, 43 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes — Milestone 002 recorded (pending doc commit) |
| Constitutional issue raised | Accepted proposals currently editable — Article 5 / Rule 3 gap (address in Milestone 003) |
| Unresolved issues | Joel approval of ADRs; Milestone 003 prompt not yet written |
| Next approved step | Joel review; commit M002 docs when directed |
| Next approved prompt | **None** — Milestone 003 prompt pending Joel ADR acceptance |
| Commit hash | Pending |

### 2026-07-25 — Record governance baseline milestone (post-commit)

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `29d1ba9` |
| Objective | Update governance records to mark Milestone 001 Completed and refresh project state before push — documentation only |
| Business decision | Memorialise commit `29d1ba9` as completed Governance Baseline before remote publish |
| Architectural decision | None (record-keeping only; no policy change) |
| Prompt template used | Documentation / milestone-record update |
| Approved Cursor prompt summary | Update milestones, project-state-report, current-state, session-handoff, chat-workflow-log, platform-roadmap only; do not commit or push |
| Files expected to change | Listed governance docs only |
| Files prohibited from changing | `app/**`, `migrations/**`, tests, models, routes, templates, services, repositories |
| Implementation result | Milestone 001 marked Completed; roadmap governance sprint moved to Completed; next milestone set to Product Architecture Review |
| Tests | Full suite **not re-run** (docs-only). Last verified remains **78 passed**, 43 warnings |
| Project-state-report update | Yes |
| Milestone entry update | Yes — Milestone 001 → Completed @ `29d1ba9` |
| Constitutional issue raised | None |
| Unresolved issues | Not yet pushed to `origin/main`; live Alembic current still To be verified |
| Next approved step | Push `29d1ba9`; then Product Architecture Review and Feature-Gate one product milestone |
| Next approved prompt | **Not yet created** — pending Product Architecture Review |
| Commit hash | Record update itself uncommitted; baseline commit referenced: `29d1ba9` |

### 2026-07-25 — Governance Baseline Completion (Constitution, milestones, prompts, state report)

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` (base `7b8d5ca`; committed as `29d1ba9`) |
| Objective | Complete governance foundation: Platform Constitution, Milestone History, Prompt Library, Project State Report, and cross-references — documentation only |
| Business decision | Further reduce chat-history dependence; make Joel → ChatGPT → Cursor cycles recoverable and repeatable |
| Architectural decision | Constitution is highest-order law; milestones append-only; project-state-report is milestone-level state; prompts are templates not scope licenses |
| Prompt template used | [prompts/cursor-documentation-template.md](prompts/cursor-documentation-template.md) |
| Approved Cursor prompt summary | Create constitution, milestones, prompts/*, project-state-report; update listed cross-ref docs and Cursor rules; no application/migration/test changes |
| Files expected to change | Governance/documentation paths only |
| Files prohibited from changing | `app/**`, `migrations/**`, models, routes, templates, services, repositories, tests, business logic |
| Implementation result | Governance baseline delivered and committed: **39** files, docs/rules/AGENTS/README only; **no** app/migration/test changes |
| Tests / validation | `./venv/bin/python -m pytest -q` → **78 passed**, 43 warnings; `git diff --check` clean; **171** internal links checked, **0** broken |
| Project-state-report update | Yes |
| Milestone entry update | Yes — later marked Completed at `29d1ba9` |
| Constitutional issue raised | None (established Constitution v1.0) |
| Unresolved issues | Live alembic `current` To be verified; push to origin pending |
| Next approved step | Record milestone completion in docs; then `git push origin main` when Joel directs |
| Next approved prompt | **Not yet created** — pending Product Architecture Review |
| Commit hash | `29d1ba9` — *Complete Estimator governance baseline and prompt library* |

### 2026-07-25 — Platform Governance Foundation

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Branch | `main` @ `7b8d5ca` (start) |
| Objective | Establish documentation/governance foundation only; no application behaviour change |
| Business decision | Adopt AiRIA-derived operating discipline for The Estimator (docs as system of record; Feature Gate; handoffs) |
| Architectural decision | Document current Flask modular architecture as-is; distinguish Current / Intended / Future; encode Rules 1–12 |
| Prompt template used | N/A (predated prompt library) |
| Approved Cursor prompt summary | Create `docs/**`, `.cursor/rules/**`, `AGENTS.md`; inspect repo; do not touch models/migrations/routes/business logic except README links if needed |
| Files expected to change | `docs/**`, `.cursor/rules/**`, `AGENTS.md`, root `README.md` (pointer) |
| Files prohibited from changing | Application code under `app/` (except none intended), `migrations/versions/**`, schemas, tests behaviour |
| Implementation result | Governance document tree created; module docs grounded in code; Cursor rules added; later included in `29d1ba9` |
| Tests | `./venv/bin/python -m pytest -q` → **78 passed**, 43 warnings (2026-07-25) |
| Project-state-report update | Added in follow-on baseline completion task |
| Milestone entry update | Recorded as Milestone 001 |
| Constitutional issue raised | N/A at time of sprint |
| Unresolved issues | Live alembic `current` vs heads needs Flask-Migrate verification; authz depth unverified |
| Next approved step | Completed via baseline commit `29d1ba9` |
| Next approved prompt | Superseded by Product Architecture Review (not yet created) |
| Commit hash | `29d1ba9` (governance baseline commit includes this work) |

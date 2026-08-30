# Milestone History — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative historical record |
| Updated | 2026-08-30 |
| Policy | **Append-only** |

## Purpose

Record completed and in-progress platform milestones so progress is recoverable without chat history.

## Numbering convention

- Format: `Milestone NNN` with zero-padded integers (`001`, `002`, …)
- Title: short human name
- Separate **planned** milestones (roadmap) from **recorded** entries here
- Architecture reconciliations use **CAR-NNN** and are **not** milestone numbers. Do not reuse M009 for CAR-001.

## Required fields (each entry)

Milestone · Status · Branch · Base commit · Objective · Deliverables · Validation · Architectural findings · Open decisions · Next milestone · Commit · Date

## Rules

1. Entries are **append-only** (newest first under Completed / Recorded).
2. Completed entries are **not rewritten** except to correct factual errors (note the correction).
3. Distinguish **Planned** (may live primarily on the roadmap) from **Completed / Recorded** here.
4. “Completed pending baseline commit” means deliverables exist in the working tree awaiting Joel-approved commit.

---

## Architecture records (non-milestone)

### 2026-08-30 — FG-014 catalogue-link flash repair

| Field | Content |
|-------|---------|
| ID | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) |
| Status | **LIVE-MIGRATED / FLASH REPAIR APPLIED — OFFICE RE-UAT REMAINING** |
| Date | 2026-08-30 |
| Objective | Repair misleading catalogue-link flash for non-Material / cross-org POSTs without changing link semantics. |
| Deliverables | `link_cost_item` catches `MaterialCatalogueError` first. Regression tests for Labour/Equipment/Subcontractor/Allowance/Other, cross-org, and empty select. Status docs reconciled. |
| Validation | Dedicated **35 passed**. Assemblies/estimates/estimate_builder **29 passed**. Full suite **345 passed**. Live POST `/material-catalogue/7/link` Labour id 5 flashed the service reason; data remained unlinked. |
| Next | **Office re-UAT of catalogue-link error flashes, then close FG-014**. Do not implement Permit Intelligence. |

### 2026-08-30 — Permit & Approvals Report requirement pin

| Field | Content |
|-------|---------|
| ID | Permit & Approvals Report (not a numbered M0xx; not a Feature Gate; not an ADR) |
| Status | **FUTURE / NOT IMPLEMENTED** — requirement pin only |
| Date | 2026-08-30 |
| Objective | Record a governed advisory project permit-preflight document as future architecture. Identify permit/zoning/servicing/approval issues early enough to affect feasibility, scope, pricing, and contracting. Final authority remains the AHJ. |
| Deliverables | Canonical pin [permit-and-approvals-report.md](architecture/permit-and-approvals-report.md); project-document-package additional-document note; UAT reference case (Mike Pratt Coach House, 2562 Church Street, North Gower, Ontario); indexes and status-doc cross-refs. |
| Validation | Docs-only; `git diff --check`. No `app/` / `tests/` / `migrations/`. No Feature Gate. No ADR. Tests not required this pass. Last recorded full suite **338 passed**. |
| Next | **FG-014 catalogue-link flash repair + re-UAT** (unchanged). Do not implement Permit Intelligence, legal-library, live regulatory lookup, schema, or a Permit Feature Gate in this record. |

### 2026-08-30 — FG-014 live-migrated; office UAT closure blocked

| Field | Content |
|-------|---------|
| ID | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) |
| Status | **LIVE-MIGRATED / UAT DEFECT — CLOSURE BLOCKED** |
| Date | 2026-08-30 |
| Objective | Apply `d6e7f8a9b0c1` and office UAT. Close only if UAT passes. |
| Deliverables | Live current = head = `d6e7f8a9b0c1`. Seed verified. Office UAT mostly passed. Closure blocked by catalogue link flash defect. Product code not repaired. |
| Validation | Dedicated **28**. Regressions **278**. Full suite **338**. Browser UAT on port 5005. |
| Next | Bounded defect repair for `link_cost_item` exception order, then re-UAT. Do not re-migrate. Do not start supplier ingest. |

### 2026-08-30 — FG-014 Material Catalogue V1 implemented (not live-migrated)

| Field | Content |
|-------|---------|
| ID | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) |
| Status | **IMPLEMENTED / VERIFIED / NOT LIVE-MIGRATED** |
| Date | 2026-08-30 |
| Objective | Canonical lumber/sheet identity, platform seed, optional Material CostItem link, office catalogue UX. |
| Deliverables | `canonical_materials`; revision `d6e7f8a9b0c1`; `/material-catalogue/`; dedicated tests. Live DB not upgraded. |
| Validation | Dedicated **28 passed**. Full suite **338 passed**. Throwaway upgrade/downgrade. Live current remains `c5d6e7f8a9b0`. |
| Next | Live-migrate + office UAT when authorized. Do not start Phase D or supplier POC. |

### 2026-08-30 — FG-014 Material Catalogue V1 Feature Gate approved

| Field | Content |
|-------|---------|
| ID | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) (not a numbered M0xx) |
| Status | **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED** |
| Date | 2026-08-30 |
| Objective | Authorize bounded CalibAi Material Catalogue identity V1 (dimensional lumber + sheet goods) + optional Material CostItem link + office catalogue UX. |
| Deliverables | Feature Gate FG-014; module stub; indexes; status docs. **Future pin:** governed bulk supplier onboarding (not implemented; does not expand FG-014; no Supplier Feature Gate). |
| Validation | Docs-only; `git diff --check`. No `app/` / `tests/` / `migrations/`. Tests not required this pass. Last recorded full suite **310 passed**. |
| Next | Separate **FG-014 implementation prompt**. Do not implement in this record. Do not start Phase D, supplier POC, or bulk supplier onboarding. Do not accept ADR-008. |

### 2026-08-30 — Material Catalogue ADR-034 / ADR-035 / ADR-036

| Field | Content |
|-------|---------|
| ID | ADR-034, ADR-035, ADR-036 (not a numbered M0xx; not a Feature Gate) |
| Status | **Accepted** (governance / architecture only; not implemented) |
| Date | 2026-08-30 |
| Objective | Accept canonical identity, quantity/UOM/requirement boundary, and commercial-evidence/mapping ADRs. |
| Deliverables | Three Accepted ADRs. ADR-008 remains Proposed. No Feature Gate. No product code. |
| Validation | Docs-only; `git diff --check`. Tests not required this pass. |
| Next | **Material Catalogue Feature Gate** (identity-only lumber/sheets) when authorized. Do not implement in this record. Do not start Phase D or supplier POC. |

### 2026-08-30 — Material Catalogue architecture (docs)

| Field | Content |
|-------|---------|
| ID | Material Catalogue architecture (not a numbered M0xx; not a Feature Gate) |
| Status | **Intended architecture documented** (not implemented) |
| Date | 2026-08-30 |
| Objective | Lock CalibAi-seeded material identity vs org CostItem vs supplier catalogue vs mapping; living vs identity; first FG identity-only. |
| Deliverables | [material-catalogue-architecture.md](architecture/material-catalogue-architecture.md); supplier-doc ownership reconciliation; living intelligence (price increase + promotion) recorded. No ADR. No Feature Gate. No product code. |
| Validation | Docs-only; `git diff --check`. Tests not required this pass. |
| Next | **Material Catalogue Feature Gate** when authorized. Do not implement. Do not accept ADR-008 in the identity pass. Do not start Phase D or supplier POC. |

### 2026-08-30 — FG-013 live-migration reconciliation + UAT closure

| Field | Content |
|-------|---------|
| ID | FG-013 (not a numbered M0xx) |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Date | 2026-08-30 |
| Objective | Verify already-applied `c5d6e7f8a9b0`, complete bounded browser/UAT, close the gate without re-running `flask db upgrade`. |
| Deliverables | Provenance: migration **VERIFIED APPLIED** before this pass (prior interrupted live-migrate). Multi-file mixed/duplicate/review UAT on port 5004. Folder/OS-drag not live-browser verified. Tests 27/11/25/33/**310**. Docs only. |
| Validation | Dedicated FG-013 **27 passed**; full suite **310 passed**. Live current=head `c5d6e7f8a9b0`. Legacy 20-file corpus SHA match. |
| Next | **Material Catalogue architecture** (docs) when authorized. Do not `flask db upgrade`. Do not start supplier POC, Phase D, MONITOR. |

### 2026-08-30 — ADR-033 supplier neutrality / Winchester launch-partner channel

| Field | Content |
|-------|---------|
| ID | ADR-033 (not a numbered M0xx; not a Feature Gate) |
| Status | **Accepted** (governance / architecture only) |
| Date | 2026-08-30 |
| Objective | Lock supplier-channel rules before any Winchester / supplier-integration POC: neutrality, no exclusivity, dual relationships, launch-partner (not distribution lock-in), Darcy originated-value participation without terms. |
| Deliverables | ADR-033 Accepted; [supplier-channel-and-launch-partner.md](architecture/supplier-channel-and-launch-partner.md). No product code. No Feature Gate. No percentages. |
| Validation | Docs-only; `git diff --check`. No product tests required this pass. |
| Next | **Do not start supplier integration.** FG-013 live-migrate + UAT remains the next **product** action when separately authorized. Darcy commercial terms unset. |

### 2026-08-30 — FG-013 historical-upload implementation

| Field | Content |
|-------|---------|
| ID | FG-013 (not a numbered M0xx) |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED · LIVE MIGRATION PENDING** |
| Date | 2026-08-30 |
| Objective | Productize office UPLOAD PREVIOUS ESTIMATES on FG-006 with ADR-032 custody. |
| Deliverables | Multi-file/folder UX; `HistoricalUploadAttempt`; app-managed storage; unknown-layout quarantine; TIER_A wording; revision `c5d6e7f8a9b0`; dedicated tests. No UploadBatch. Legacy Desktop corpus untouched. |
| Validation | Dedicated FG-013 **27 passed**; full suite **310 passed**. Temp-SQLite upgrade/downgrade verified. Live `flask db current` remains `b4c5d6e7f8a9`. Browser UAT not performed. |
| Next | Separate live-migrate + UAT smoke prompt. Do not upgrade from this commit. |

### 2026-08-30 — FG-013 historical-upload governance + ADR-032 source custody

| Field | Content |
|-------|---------|
| ID | FG-013 + ADR-032 (not a numbered M0xx) |
| Status | FG-013 **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**. ADR-032 **Accepted**. |
| Date | 2026-08-30 |
| Objective | Complete FG-013 gate answers and accept app-managed immutable historical workbook custody without implementing uploads. |
| Deliverables | FG-013 approved; ADR-032 Accepted (legacy Desktop corpus leave-in-place; productized uploads app-managed); durable per-file attempts; no UploadBatch; additive schema/migration authorized for a later implementation prompt only. Docs only. |
| Validation | Docs-only; `git diff --check`. No product tests required this pass. Alembic current/head `b4c5d6e7f8a9`. |
| Next | Separate FG-013 **implementation** prompt (must explicitly authorize the one bounded additive Alembic revision). Do not implement from this governance commit. |

### 2026-08-30 — ADR-021 MONITOR Commercial Baseline / Project Gross Margin

| Field | Content |
|-------|---------|
| ID | ADR-021 (not a numbered M0xx; not a Feature Gate) |
| Status | **Accepted** (governance only) |
| Date | 2026-08-30 |
| Objective | Lock MONITOR estimated baseline and Project Gross Margin semantics before any MONITOR / profitability code. |
| Deliverables | ADR-021 Accepted: composed frozen baseline; Project Gross Margin (not net profit); floating-draft prohibition; MONITOR comparison/read ownership; actuals/BUILD/LEARN/benchmarking not implemented. Docs only. |
| Validation | Docs-only; `git diff --check`. No product tests required. Alembic current/head `b4c5d6e7f8a9`. |
| Next | **STOP DEVELOPMENT.** Do not implement MONITOR. Do not create a MONITOR Feature Gate. Phase D **NOT STARTED / NOT AUTHORIZED**. |

### 2026-08-30 — FG-012 Internal Detailed Cost Breakdown + Customer Estimate Consistency

| Field | Content |
|-------|---------|
| ID | FG-012 (not a numbered M0xx) |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Date | 2026-08-30 |
| Objective | Internal Detailed Cost Breakdown + customer Proposal consistency from the same EstimateVersion / pricing snapshot. |
| Deliverables | Estimating-owned internal breakdown; named-method Proposal totals from frozen snapshot; customer PDF without Overhead/Profit rows; Estimate Totals method presentation; dedicated tests; docs. No schema/migration/ADR. |
| Validation | Dedicated FG-012 **19 passed**; full suite **283 passed**. Browser UAT on labeled FG-009 residue + `PROP-FG012-UAT-GM`. Alembic current/head `b4c5d6e7f8a9`. |
| Next | **STOP DEVELOPMENT.** Phase D **NOT STARTED / NOT AUTHORIZED**. Do not begin another Feature Gate. |

### 2026-08-30 — FG-011 Project Hub UX

| Field | Content |
|-------|---------|
| ID | FG-011 (not a numbered M0xx) |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Date | 2026-08-30 |
| Objective | Evolve `/projects/<id>` into the office-estimator Project Hub. |
| Deliverables | Read-only hub assembly; lifecycle IA PLAN → PRICE → CONTRACT → BUILD with Future MONITOR/LEARN; dedicated tests; docs reconciliation. No schema/migration/ADR. |
| Validation | Dedicated Project Hub **13 passed**; full suite **264 passed**. Browser smoke on labeled FG-009 `/projects/2` and FG-010 `/projects/3`. Alembic current/head `b4c5d6e7f8a9`. |
| Next | **STOP DEVELOPMENT.** Phase D **NOT STARTED / NOT AUTHORIZED**. Estimate-output consistency remains separately gated. |

### 29 Aug 2026 — Day-end reconciliation / Review Turnover

| Field | Content |
|-------|---------|
| ID | Review Turnover (not a product milestone) |
| Status | **COMPLETE / DURABLE / CLEAN TURNOVER** |
| Date | 2026-08-30 |
| Objective | Prove 29 Aug FG-008 / FG-009 / FG-010 work is durable, consistent, pushed, migrated, documented, and reconstructable without chat memory. |
| Deliverables | 22-point `session-handoff.md`; live DB snapshot; residue classification; stale current-state corrections; this journal entry. |
| Validation | Dedicated take-off **18**; Plan Intelligence **56**; Pricing **33**; Labour **25**; Historical **11**; full suite **251**. Alembic current/head `b4c5d6e7f8a9`. |
| Next | **STOP DEVELOPMENT.** Next candidate: Project Hub UX — **NOT STARTED / NOT AUTHORIZED**. Phase D **NOT STARTED / NOT AUTHORIZED**. |

### M012 / FG-010 — Live migration and synthetic UAT smoke

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Date | 2026-08-30 |
| Objective | Apply additive migration `b4c5d6e7f8a9` to live development/UAT and perform bounded synthetic browser/UAT smoke. |
| Deliverables | Live Alembic current/head `b4c5d6e7f8a9`; synthetic FG-010 UAT project/docs/runs/package; COUNT-without-scale and dimensional fail-closed; docs reconciliation. |
| Validation | Dedicated **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **251**. Estimate/Labour/Pricing deltas **ZERO**. External provider calls **ZERO**. Browser smoke on `/projects/3/plans/takeoff`. |
| Next | **STOP DEVELOPMENT.** Day-End Reconciliation / Review Turnover audit. Do not enable a real external AI provider. Do not start Phase D. Do not start another milestone. |

### M012 / FG-010 — Implementation commit and push

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** — **NOT YET LIVE-MIGRATED** |
| Date | 2026-08-29 |
| Objective | Commit and push the reviewed provider-neutral AI take-off foundation. Live migrate not authorized. |
| Deliverables | One implementation commit on `main` including models/services/UI, migration `b4c5d6e7f8a9`, tests, and docs. |
| Validation | Dedicated **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **251**. Live current remains `a3b4c5d6e7f8`. Browser/live UAT **not yet performed**. |
| Next | Separate authorization to apply `b4c5d6e7f8a9` live and perform bounded synthetic browser/UAT smoke. Do not enable a real external AI provider. Do not start Phase D. |

### M012 / FG-010 — Foundation implementation (uncommitted)

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 |
| Status | **IMPLEMENTED / VERIFIED** — **NOT YET LIVE-MIGRATED** — **uncommitted** |
| Date | 2026-08-29 |
| Objective | Implement the provider-neutral AI take-off foundation: extraction runs, candidates, human review, immutable packages, mock extractor, COUNT-without-scale, org isolation, PlanAuditEvent extensions, office UI. |
| Deliverables | Models/services/routes/templates; additive migration `b4c5d6e7f8a9`; `tests/test_takeoff.py`; COUNT regression in `tests/test_scale_measurement.py`; docs reconciliation. |
| Validation | Dedicated **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **251**. Temp DB upgrade/downgrade `a3b4c5d6e7f8` ↔ `b4c5d6e7f8a9`. Live current remains `a3b4c5d6e7f8`. |
| Next | Governance review. **Do not commit, push, or live-migrate** until separately authorized. Do not enable a real external AI provider. Do not start Phase D. |

### M012 / FG-010 — Governance approval (documentation)

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 |
| Status | **APPROVED FOR IMPLEMENTATION** — **NOT IMPLEMENTED** |
| Date | 2026-08-29 |
| Objective | Record Joel/ChatGPT approval of FG-010 and accept ADR-005/006/007/009/011/031. Keep ADR-010 Proposed. COUNT-without-scale clarification. Real external AI provider not authorized. |
| Deliverables | Status reconciliation across FG-010, ADRs, architecture, indexes, handoff. Docs-only commit. |
| Validation | Plan Intelligence combined **51 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **228**. Product/migration files unchanged. |
| Next | Separate bounded FG-010 implementation prompt (provider-neutral). **Do not implement in this pass.** |

### M012 / FG-010 — AI Take-off architecture and Feature Gate preparation

| Field | Content |
|-------|---------|
| ID | M012 / FG-010 (architecture only; not implemented) |
| Status | **PREPARED FOR GOVERNANCE APPROVAL** — **NOT APPROVED** — **NOT IMPLEMENTED** |
| Date | 2026-08-29 |
| Objective | Reconcile Plan Intelligence ADRs; define extraction-run / candidate / package architecture; prepare FG-010. No product code. |
| Deliverables | Take-off architecture; FG-010; ADR-031 **Proposed**; ADR-005–011 reconciliation notes; indexes/handoff. |
| Validation | Plan Intelligence combined **51 passed**; Pricing **33**; Labour **25**; historical **11**; full suite **228**. `git diff --check` expected clean after this pass. Product/migration files unchanged. |
| Next | Joel / ChatGPT review. **Do not implement AI take-off** until FG-010 is approved and a separate implementation prompt is issued. |

### FG-009 — Live development/UAT migration and smoke verification

| Field | Content |
|-------|---------|
| ID | FG-009 (not a numbered product milestone) |
| Status | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Date | 2026-08-29 |
| Objective | Apply committed migration `a3b4c5d6e7f8` to live development/UAT and perform bounded Pricing Engine UAT smoke. No new product features. |
| Deliverables | Live Alembic current/head `a3b4c5d6e7f8`; ORG-001 seed verified (`UNSPECIFIED` optional layers); synthetic UAT TRUE_GM / markup / legacy / CO / override / snapshot immutability; docs reconciliation. |
| Validation | Dedicated **33 passed**; Labour Engine **25 passed**; historical ingestion **11 passed**; full suite **228 passed**. HistoricalLabourItem remained 120. Source workbooks untouched. |
| Next | FG-009 closure review, then prepare the next Feature Gate for AI Take-off / Quantity Extraction Foundation. **Do not start AI take-off.** |

### FG-009 — Implementation commit

| Field | Content |
|-------|---------|
| ID | FG-009 (not a numbered product milestone) |
| Status | **IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED** |
| Date | 2026-08-29 |
| Objective | Commit and push the reviewed Organization-Calibrated Pricing Engine foundation. Live migrate not authorized. |
| Deliverables | Pricing Engine models/services/UI; additive migration `a3b4c5d6e7f8`; CO method inheritance; ORG-001 seed with `UNSPECIFIED` optional layers; dedicated tests. |
| Validation | Dedicated **33 passed**; Labour Engine **25 passed**; historical ingestion **11 passed**; full suite **228 passed**. Live DB remains `f2c3d4e5f6a7`. |
| Next | Separate authorization to apply `a3b4c5d6e7f8` to live development/UAT and UAT-smoke. |

### FG-009 — Pre-commit bounded correction (CO method + ORG-001 seed)

| Field | Content |
|-------|---------|
| ID | FG-009 (not a numbered product milestone) |
| Status | **BOUNDED CORRECTION IN WORKING TREE** — tests passed; **not committed**; live DB **not migrated** |
| Date | 2026-08-29 |
| Objective | Close two pre-commit governance defects: FG-009-aware Change Orders apply inherited pricing METHOD; ORG-001 optional layers seed as `UNSPECIFIED` (distinct from org-approved `NOT_APPLIED`). |
| Deliverables | `price_change_order_from_snapshot`; CO recalculate/copy-lines; in-place correction of uncommitted `a3b4c5d6e7f8` seed; regression tests. No new migration. |
| Validation | Dedicated **33 passed**; Labour Engine **25 passed**; historical ingestion **11 passed**; full suite **228 passed**. Legacy estimate totals not rewritten. Historical Change Orders not rewritten. HistoricalLabourItem facts unchanged. |
| Next | Joel / ChatGPT governance review. **Do not commit / push / live-migrate** until authorized. |

### FG-009 — Organization-Calibrated Pricing Engine implementation

| Field | Content |
|-------|---------|
| ID | FG-009 (not a numbered product milestone) |
| Status | **IMPLEMENTED IN WORKING TREE** — tests passed; **not committed**; live DB **not migrated** |
| Date | 2026-08-29 |
| Objective | Implement organization-owned versioned pricing policies, named methods, deterministic resolution, immutable estimate pricing snapshots, ORG-001 seed, legacy stack compatibility, Change Order snapshot inheritance, tenant isolation. |
| Deliverables | `app/models/pricing_engine.py`; `app/services/pricing_engine.py`; `/pricing-engine/` office UI; additive migration `a3b4c5d6e7f8`; `tests/test_pricing_engine.py` (26 passed) |
| Validation | Dedicated **26 passed**; Labour Engine **25 passed**; historical ingestion **11 passed**; full suite **221 passed**. Legacy estimate totals not rewritten. Historical Change Orders not rewritten. HistoricalLabourItem facts unchanged. |
| Next | Joel / ChatGPT governance review. **Do not commit / push / live-migrate** until authorized. |

### FG-009 — Organization-Calibrated Pricing Engine architecture / Feature Gate preparation

| Field | Content |
|-------|---------|
| ID | FG-009 (not a product milestone; **APPROVED FOR IMPLEMENTATION**; **not implemented**) |
| Status | **ARCHITECTURE AND FEATURE GATE APPROVED** (2026-08-29) |
| Date | 2026-08-29 |
| Objective | Audit live pricing math; reconcile ORG-001 true-GM policy vs markup stack; accept ADR-025/030; approve FG-009; adopt contingency source vs pricing-treatment clarification. |
| Deliverables | Architecture report; FG-009; ADR-025 **Accepted**; ADR-030 **Accepted**; module stub; index/handoff updates. **No product code. No migration.** |
| Validation | Labour Engine tests, historical ingestion tests, full suite, `git diff --check` (see stopping report / chat-workflow-log). |
| Next | Issue a separately authorized bounded FG-009 **implementation** prompt. Do **not** implement from the architecture documents alone. |

### FG-008 — Post-UAT integrity stabilization

| Field | Content |
|-------|---------|
| ID | FG-008 (not a new milestone) |
| Status | **UAT INTEGRITY STABILIZATION COMPLETED** |
| Date | 2026-08-29 |
| Objective | Close two live-UAT integrity gaps: accidental ACCEPTED mapping to archived UAT task; labour audit persisted for nonexistent `ORG-999`. |
| Deliverables | `REVOKED` mapping lifecycle; rule suggestion joins ACTIVE tasks only; `record_labour_audit` / resolution fail-closed for unknown organizations; live mapping 1 `REVOKED`; synthetic PRS 1 `WITHDRAWN`; original ORG-999 audit preserved plus ORG-001 reconciliation event |
| Validation | Dedicated **25 passed**; historical **11 passed**; full suite **195 passed**. HistoricalLabourItem id 1 unchanged. No migration. Alembic `f2c3d4e5f6a7`. |
| Next | **STOP.** Do not start Pricing Engine or another milestone. |

### FG-008 — Live development/UAT migration and smoke verification

| Field | Content |
|-------|---------|
| ID | FG-008 |
| Status | **LIVE DEVELOPMENT/UAT MIGRATION APPLIED / UAT-SMOKE-VERIFIED** |
| Date | 2026-08-29 |
| Objective | Apply committed migration `f2c3d4e5f6a7` to the live development/UAT database and bound-smoke-verify Labour Engine without new schema, product code, or historical evidence repair. |
| Deliverables | Alembic upgrade `e1b2c3d4e5f6` → `f2c3d4e5f6a7`; seven FG-008 tables present; ORG-001 $65 DirectLabourCostRateStandard seed; historical counts unchanged (20/20/120); office `/labour-engine/` smoke; post-upgrade 22/11/192 tests |
| Validation | Live `flask db current` = head = `f2c3d4e5f6a7`. HistoricalLabourItem count 120 unchanged. `hourly_rate=0.13` cluster still 43. Zero historical record mutation. Full suite **192 passed**. |
| Next | **STOP.** Do not start Pricing Engine / ADR-025 or another milestone. |
| Commit | Product code unchanged at `0569f25`. Docs-only reconciliation: *docs: record FG-008 live migration verification* |

### FG-008 — Labour Engine Phase B implementation

| Field | Content |
|-------|---------|
| ID | FG-008 |
| Status | **IMPLEMENTED / VERIFIED** — committed and pushed at `0569f25`; live DB subsequently upgraded (see entry above) |
| Date | 2026-08-29 |
| Objective | Implement organization-owned labour methodology: canonical tasks, human-reviewed mappings, versioned production and direct-labour-cost standards, calibration candidate lifecycle, resolution, estimate snapshots, tenant isolation. |
| Deliverables | Models `app/models/labour_engine.py`; services `app/services/labour_engine.py`; office UI `/labour-engine/`; additive migration `f2c3d4e5f6a7`; `tests/test_labour_engine.py` (22 passed) |
| Validation | Full suite **192 passed**; historical ingestion **11 passed**; dedicated FG-008 **22 passed**. HistoricalLabourItem facts unchanged. Estimate selling-price math unchanged. |
| Next | Live migrate applied 2026-08-29 (see entry above) |

### FG-008 — Labour Engine Phase B Feature Gate preparation

| Field | Content |
|-------|---------|
| ID | FG-008 |
| Status | **FEATURE GATE APPROVED FOR IMPLEMENTATION** — architecture record (implementation is a later entry) |
| Date | 2026-08-29 |
| Objective | Define organization-owned labour methodology: canonical tasks, versioned production and direct-labour-cost standards, calibration candidate lifecycle, resolution, conditions, estimate snapshots, tenant isolation. |
| Deliverables | [FG-008](feature-gates/FG-008-labour-engine-phase-b.md); [labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md); [ADR-029](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted**; [modules/labour-engine.md](modules/labour-engine.md) |
| Implementation | **Not started.** Architecture approved. No product code, schema, or migration in this record. |
| Next | Bounded FG-008 **implementation** Cursor prompt (separately authorized) |

### FG-006 — Historical Estimate Ingestion Engine Phase B Feature Gate

| Field | Content |
|-------|---------|
| ID | FG-006 |
| Status | **FEATURE GATE APPROVED, IMPLEMENTED & VERIFIED** |
| Date | 2026-08-28 |
| Objective | Authorize and implement deterministic, organization-aware ingestion of historical estimate workbooks into CalibAi's governed evidence model. Ingest the 20 Brayman source workbooks into ORG-001 private intelligence. |
| Deliverables | [FG-006](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md); pure Python OpenXML parser (no macro execution), Template classifier (Families A–E), Family adapters, canonical persistence models (`HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`), evidence review service/UI (`/historical-estimates/`), additive migration `e1b2c3d4e5f6`, 11 dedicated tests |
| FG-006 code | Implemented & Verified (170/170 tests passing, 11 dedicated historical ingestion tests; 20/20 source SHA-256 hashes verified exact; committed and pushed on `main` at `690d755d9901e04eb783198f4b89071fbeaf472a`) |

### FG-007 — M011 Organization Foundation & Project Commercial Context Feature Gate

| Field | Content |
|-------|---------|
| ID | FG-007 |
| Status | **FEATURE GATE APPROVED, IMPLEMENTED & VERIFIED** |
| Date | 2026-08-28 |
| Objective | Authorize M011 scope/invariants/tests/migration permission for Organization entity, direct root model ownership, versioned Project Commercial Context, tenant query scoping, and immutable EstimateVersion references. |
| Deliverables | [FG-007](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md); [ADR-028](adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted**; M011 models, services, project form/edit UI, additive migration `d0a1b2c3d4e5`, 19 tests |
| M011 code | Implemented & Verified (159/159 tests passing; committed and pushed on `main` at `cb38d93`) |

### CAR-001 — CalibAi Product & Architecture Reconciliation

| Field | Content |
|-------|---------|
| ID | CAR-001 |
| Status | **APPROVED ARCHITECTURAL DIRECTION** — implementation not authorized by CAR-001 |
| Date | 2026-08-28 |
| Objective | Read-only reconciliation of the existing platform to CalibAi PLAN→PRICE→CONTRACT→BUILD→MONITOR→LEARN; adopt approved vision and core architecture in docs. |
| Deliverables | [CAR-001 record](architecture/CAR-001-calibai-product-architecture-reconciliation.md); vision/roadmap updates; ADR-019–025; BUILD module stub |
| Validation | Docs/governance only; no app/migration/test/schema changes |
| M009 | **Unchanged at CAR-001 time** — M009 remained coded Sheet classification; CAR-001 is not M009. M009 code was **not begun** when CAR-001 was adopted. **Correction (2026-08-29):** M009 was later implemented under FG-004 (`5dc4b09`, migration `b8d9f0a1c2e3`). |
| Next | Feature-Gate M009 when authorized; accept ADR-021/025 when ready |

### FG-005 — M010 Scale Calibration Feature Gate

| Field | Content |
|-------|---------|
| ID | FG-005 |
| Status | **FEATURE GATE APPROVED, IMPLEMENTED & VERIFIED** |
| Date | 2026-08-28 |
| Objective | Authorize M010 scope/invariants/tests/migration permission for drawing scale calibration and manual measurement tools. Implemented in M010 (`6b969fe`, migration `c9e0f1a2b3d4`). |
| Deliverables | [FG-005](feature-gates/FG-005-m010-scale-calibration.md); [ADR-026](adr/ADR-026-scale-ownership-and-calibration-provenance.md) Accepted; [ADR-027](adr/ADR-027-pdf-rendering-and-normalized-coordinate-system.md) Accepted |
| M010 code | Implemented & Verified (`6b969fe`, migration `c9e0f1a2b3d4`) |

### FG-004 — M009 Sheet Classification Feature Gate

| Field | Content |
|-------|---------|
| ID | FG-004 |
| Status | **FEATURE GATE APPROVED, IMPLEMENTED & VERIFIED** |
| Date | 2026-08-28 |
| Objective | Authorize M009 scope/invariants/tests/migration permission. Implemented in M009 (`5dc4b09`, migration `b8d9f0a1c2e3`). |
| Deliverables | [FG-004](feature-gates/FG-004-m009-sheet-classification.md); ADR-017/018 **Accepted**; M009 models, services, review UI, 15 tests |
| M009 code | Implemented & Verified |

---

## Recorded milestones

### Feature Gate 006 — Historical Estimate Ingestion Engine Phase B

| Field | Content |
|-------|---------|
| Milestone | Historical Estimate Ingestion Engine Phase B (FG-006) |
| Status | **Completed & Verified** (implemented, verified, committed, and pushed on `main`) |
| Branch | `main` |
| Base | `cb38d93` |
| Date | 2026-08-28 |
| Objective | Authorize and implement deterministic, organization-aware ingestion of historical estimate workbooks into CalibAi's governed evidence model. Ingest the 20 Brayman source workbooks into ORG-001 private intelligence with full source-cell provenance and human review workflow. |
| Deliverables | [FG-006](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md); pure Python OpenXML parser (no macro execution), Template classifier (Families A–E), Family adapters, canonical persistence models (`HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`), evidence review service/UI (`/historical-estimates/`), additive migration `e1b2c3d4e5f6`, 11 dedicated tests in `tests/test_historical_ingestion.py`. |
| Validation | 170/170 full test suite pass; 11/11 dedicated historical ingestion tests pass; 20/20 source workbook SHA-256 hashes verified exact before and after ingestion; ORG-001 private intelligence isolation verified; zero mutation to active estimating tables. |
| Architectural findings | Pure-Python OpenXML reader executes zero macros; cell provenance preserves exact formula and displayed text; cost-plus markup preserved as historical fact without converting to modern gross margin; contingency separated from markup. |
| Open decisions | None for FG-006. Ingestion is complete and sealed. Pricing Engine remains blocked / not started. |
| Next milestone | **FG-008** Labour Engine Phase B — architecture **APPROVED FOR IMPLEMENTATION** (2026-08-29). Implementation not started. |
| Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |

### Milestone 011 — Organization Foundation & Project Commercial Context

| Field | Content |
|-------|---------|
| Milestone | Organization Foundation & Project Commercial Context |
| Status | **Completed & Verified** (implemented and committed on `main`) |
| Branch | `main` |
| Base | `01b3be4` |
| Date | 2026-08-28 |
| Objective | Implement canonical `Organization` model, Brayman `ORG-001` seed and deterministic backfill, direct ownership FKs on root models (`Client`, `Project`, `CostItem`, `Assembly`, `ProposalTemplate`), tenant-safe query isolation with fail-closed 404s, versioned `ProjectCommercialContext` with 7 mandatory decision parameters, policy-driven justification engine, Commercial Decision Gate in project creation and editing UI, immutable `EstimateVersion.commercial_context_id` references, and controlled additive migration `d0a1b2c3d4e5`. |
| Deliverables | Models (`Organization`, `ProjectCommercialContext`); migration `d0a1b2c3d4e5`; services `app/services/organizations.py`, `app/services/commercial_context.py`; updated routes and templates for projects, clients, cost library, assemblies, proposal templates, estimates, proposals, plan intelligence, project controls; 19 focused tests in `tests/test_organization_foundation.py`. |
| Validation | 159/159 full test suite passes; migration applies cleanly with complete legacy data preservation and deterministic backfill; tenant query isolation verified; policy-driven justification verified; historical estimate version context immutability verified. |
| Architectural findings | Single-tenant context helper `get_current_organization_id()` provides complete query scoping without prematurely implementing auth/RBAC; composite unique constraints preserve cross-tenant code reusability; commercial context captures assumptions without affecting pricing math. |
| Open decisions | None for M011. Organization foundation and Project Commercial Context active. |
| Next milestone | FG-006 — Historical Estimate Ingestion Engine Phase B |
| Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |

### Milestone 010 — Scale Calibration / Measurement Tools

| Field | Content |
|-------|---------|
| Milestone | Scale Calibration / Measurement Tools |
| Status | **Completed & Verified** (implemented on `main`) |
| Branch | `main` |
| Base | `8f7969c` |
| Date | 2026-08-28 |
| Objective | Implement drawing scale calibration (2-point calibration, presets, viewport regions, NTS) and manual measurement tools (linear, polyline, polygon area Shoelace / perimeter, count) with normalized coordinate stability, PDF.js viewer, and fail-closed human authority under Plan Intelligence. |
| Deliverables | Models (`PlanScaleCalibration`, `PlanMeasurement`); migration `c9e0f1a2b3d4`; service layer `app/plan_intelligence/scale_measurement.py`; measurement route and template (`sheet_measure.html`, `sheet-measurement.js`); 19 focused tests in `tests/test_scale_measurement.py`. |
| Validation | 140/140 tests pass; migration applies cleanly; project/revision/sheet isolation verified; source doc/page immutability verified; estimating/proposals unaffected. |
| Architectural findings | Extracted scale strings never auto-confirm; measurements require confirmed calibration; multi-scale viewports scope measurement scales deterministically; geometry persisted in normalized document coordinates `[0.0, 1.0]`. |
| Open decisions | None for M010. Drawing scale calibration and manual measurement tools active. |
| Next milestone | Milestone 011 — Organization Foundation & Project Commercial Context (FG-007) |
| Commit | `6b969fe` — *feat: implement M010 scale calibration* |

### Milestone 009 — Sheet Classification / Human Metadata Review

| Field | Content |
|-------|---------|
| Milestone | Sheet Classification / Human Metadata Review |
| Status | **Completed & Verified** |
| Branch | `main` |
| Base | `da0d38a` |
| Date | 2026-08-28 |
| Objective | Implement durable Sheet entities, non-1:1 Page↔Sheet mapping, first-class suggestions, human review workflow (accept/edit/reject/void), revision uniqueness/finalization validation, and office review UI under Plan Intelligence. |
| Deliverables | Models (`PlanSheet`, `PlanSheetPage`, `PlanSheetSuggestion`, `sheet_id` audit FK); migration `b8d9f0a1c2e3`; service layer `app/plan_intelligence/sheets.py`; office review routes and templates (`sheets_index.html`, `sheet_review.html`, `sheet_create.html`); 15 focused tests in `tests/test_sheet_intelligence.py`. |
| Validation | 121/121 tests pass; migration applies cleanly; project/revision isolation verified; source doc/page immutability verified; estimating/proposals unaffected. |
| Architectural findings | Suggestion presence never auto-accepts SoR; human action required; uniqueness scoped to DrawingRevision; superseded revision sheets remain immutable. |
| Open decisions | None for M009. Scale calibration / measurement tools deferred to M010. |
| Next milestone | M010 — Scale Calibration / Measurement Tools (FG-005 Approved; awaits implementation prompt) |
| Commit | `5dc4b09` — *feat: implement M009 sheet classification* |

### Milestone 008 — Sheet Intelligence Architecture Planning

| Field | Content |
|-------|---------|
| Milestone | Sheet Intelligence Architecture Planning |
| Status | **Completed** (merged to `main`) |
| Branch | `milestone-008-sheet-intelligence` |
| Base | M007 indexing (`cbefe7a`) |
| Date | 2026-07-25 |
| Objective | Design Sheet entity model, page mapping, human review, duplicates/supersession; ADRs only if warranted; **no application code**. |
| Deliverables | [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md); [M008 readiness report](architecture/M008-sheet-intelligence-readiness-report.md); [ADR-017](adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md); [ADR-018](adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md); index/roadmap/state updates. |
| Validation | Docs only; no app/migration/test changes for this milestone. |
| Architectural findings | M007 Pages/Revisions are a sufficient foundation; suggestions ≠ system of record; uniqueness is per Revision; first *coded* sheet work is a later Feature-Gated milestone (recommended M009). |
| Open decisions | Accept ADR-017/018; authorize coded sheet Feature Gate. |
| Next milestone | Feature-Gated Sheet classification and human metadata review (not authorized yet) |
| Commit | `8c74e31` — *Document Sheet Intelligence architecture and suggestion/review ADRs.* Merged via PR #6 → `ee9b4b2`. |

### Milestone 007 — Document Indexing and Deterministic Metadata Extraction

| Field | Content |
|-------|---------|
| Milestone | Document Indexing and Deterministic Metadata Extraction |
| Status | **Completed** (merged to `main`) |
| Branch | `milestone-007-document-indexing` |
| Base | M005 Phase A + M006 architecture |
| Date | 2026-07-25 |
| Objective | First coded Document Intelligence phase: pages, deterministic/embedded-text extraction, provenance, archive, audit, relational search. |
| Deliverables | Models/services for Package/Revision (minimal), Page, ProcessingAttempt/Result, audit; migration `a7c8e9f0b1d2`; UI list/search/reprocess/archive; `tests/test_plan_indexing.py`. |
| Validation | Targeted plan tests + full suite **106 passed**, 110 warnings; `flask db upgrade` to `a7c8e9f0b1d2`; `git diff --check` clean. |
| Architectural findings | Upload ownership unchanged; Estimating untouched; hard-delete blocked once audit/index exist; page ≠ sheet. |
| Open decisions | Sheet Intelligence coded review (next Feature Gate); raw payload retention TTL; auth; project-detail archived filter. |
| Next milestone | Milestone 008 — Sheet Intelligence architecture planning |
| Commit | `cbefe7a` — *Implement Document Intelligence indexing for plan pages, processing, and search.* Merged via PR #5 → `eb00123`. |

### Milestone 006 — Document Intelligence Architecture & Feature Gate

| Field | Content |
|-------|---------|
| Milestone | Document Intelligence Architecture and Feature Gate |
| Status | **Completed** (merged to `main`) |
| Branch | `milestone-005-plan-intelligence-phase-a` |
| Base commit | `098647c` (Phase A); docs tip `35413a1` |
| Date | 2026-07-25 |
| Objective | Design Document Intelligence between PDF upload and take-off; FG-003 readiness with conditions; required ADRs only; no code. |
| Deliverables | FG-003 (**CONDITIONAL PASS**); `architecture/document-intelligence.md`; M006 readiness report; ADR-013–016; roadmap/milestones/state updates. |
| Validation | Docs only; no app/migration/test/dependency changes; link check; `git diff --check`. |
| Architectural findings | M005 supports additive DI; Sheet ≠ Page; extraction provenance required; staged relational search; hard-delete/auth/audit are conditions not FAIL causes. |
| Open decisions | Accept ADR-013–016 (as applicable); coded DI delivered in M007. |
| Next milestone | M007 — Document indexing and deterministic metadata extraction |
| Commit | `35413a1` — *Document Document Intelligence architecture and FG-003 readiness.* Merged via PR #4 → `db1a8da`. |

### Milestone 005 — Plan Intelligence Feature Gate and Phase A PDF Upload

| Field | Content |
|-------|---------|
| Milestone | Plan Intelligence Feature Gate and Phase A PDF Upload |
| Status | **Completed** (merged to `main`) |
| Branch | `milestone-005-plan-intelligence-phase-a` |
| Base commit | `c59ec01` |
| Date | 2026-07-25 |
| Objective | Complete FG-002; document ADR-012 (revision ownership); implement Phase A only — secure searchable PDF upload/storage foundation. |
| Deliverables | ADR-012 (Proposed); FG-002 (Approved); `app/plan_intelligence/` (models/services/storage/routes); templates; migration `f9c1a2b3d4e5`; project detail link; `tests/test_plan_upload.py`; module/docs updates. |
| Validation | Phase A tests 8 passed; full suite **97 passed**, 68 warnings. No OCR/CAD/AI/estimate insert/revision UI. |
| Architectural findings | Flat `plan_documents` is intentionally interim; Drawing Set/Revision lifecycle owned by ADR-012 for later gates. Private storage under instance/`PLAN_UPLOAD_ROOT`. |
| Open decisions | Accept ADR-012; auth for uploads; retention/archival policy when take-offs exist. |
| Next milestone | Milestone 006 — Document Intelligence architecture (then M007+ coded DI) |
| Commit | `098647c` — *Implement Plan Intelligence Phase A PDF upload and storage.* Merged via PR #4 → `db1a8da`. |

### Milestone 004 — Plan Intelligence & Automated Take-Off Architecture

| Field | Content |
|-------|---------|
| Milestone | Plan Intelligence & Automated Take-Off Architecture |
| Status | **Completed pending documentation commit** |
| Branch | `main` |
| Base commit | `c59ec01` |
| Date | 2026-07-25 |
| Objective | Design implementation-ready Plan Intelligence architecture: pipeline, conceptual model, human review, source traceability, estimate mapping, ADRs, narrow POC — documentation only. |
| Deliverables | Expanded `modules/plan-intelligence.md`; full `architecture/plan-intelligence-and-automated-takeoff.md`; readiness report; ADR-005/006 updates; ADR-011 confidence policy; roadmap/milestones/state updates. |
| Validation | Docs only; no app/migration/test/dependency changes; link check after edits. |
| Architectural findings | Differentiator is plan→take-off→estimate→proposal; PDF-first; human approval mandatory; citations first-class; estimate builder not redesigned. |
| Open decisions | POC element confirmation; confidence numeric thresholds; auth for reviewer; Phase A Feature Gate timing; build-vs-buy. |
| Next milestone | Feature Gate + implement Plan Intelligence Phase A (PDF upload/storage) |
| Commit | Pending |

### Milestone 003 — Accepted Proposal Immutability

| Field | Content |
|-------|---------|
| Milestone | Accepted Proposal Immutability |
| Status | **Completed** |
| Branch | `main` |
| Base commit | `71e2754` / docs at `9137052` |
| Date | 2026-07-25 |
| Objective | Enforce service-layer immutability for `Accepted` proposals across all mutation paths; keep detail/preview/PDF read-only available. |
| Deliverables | `ensure_proposal_mutable` / `is_proposal_immutable`; route/UI read-only controls; `tests/test_proposal_immutability.py`. |
| Validation | Full pytest: **89 passed**, 53 warnings (at implementation). No migration. |
| Architectural findings | No section CRUD mutation API; line edit + update_proposal + recalculate + status were mutation surfaces. |
| Open decisions | Void/supersede/revision workflow (ADR-004). |
| Next milestone | Milestone 004 — Plan Intelligence architecture |
| Commit | `c59ec01` — *Enforce immutability for accepted proposals* |

### Milestone 002 — Product Architecture Review and Next-Milestone Selection

| Field | Content |
|-------|---------|
| Milestone | Product Architecture Review and Next-Milestone Selection |
| Status | **Completed pending documentation commit** |
| Branch | `main` |
| Base commit | `71e2754` |
| Date | 2026-07-25 |
| Objective | Review Proposals module against roadmap; produce Feature Gate FG-001 and ADRs 001–004; recommend next implementation milestone without code changes. Extended same day with strategic Plan Intelligence / Supplier architecture, pillars, Phases A–G, ADR-005–010, and POC recommendation. |
| Deliverables | `docs/feature-gates/FG-001-proposals-module.md`; ADR-001–004; `docs/architecture/plan-intelligence-and-automated-takeoff.md`; `docs/architecture/supplier-catalogue-inventory-pricing.md`; ADR-005–010; roadmap pillars; module stubs for Plan Intelligence and Supplier Catalogue; cross-links. |
| Validation | Documentation-only; no application/migration/test file changes; internal doc links checked after edits. Full pytest not re-run (last verified: 78 passed, 43 warnings). |
| Architectural findings | Proposal Builder foundation already exists. Highest Proposals gap: Accepted without immutability. Strategic differentiator: PDF-first Plan Intelligence → reviewed take-off → estimate → supplier pricing → proposal/PO. No plan upload or supplier catalogue in code today. |
| Open decisions | Joel acceptance of ADRs 001–010; Milestone 003 vs Phase A POC sequencing; POC element confirmation. |
| Next milestone | **Milestone 003 — Accepted Proposal Immutability** (near-term) and/or Feature Gate for **Plan Intelligence Phase A** (strategic) — neither implementation-authorized until Joel approves |
| Commit | Pending |

### Milestone 001 — Platform Governance Foundation

| Field | Content |
|-------|---------|
| Milestone | Platform Governance Foundation |
| Status | **Completed** |
| Branch | `main` |
| Base commit | `7b8d5ca` |
| Date | 2026-07-25 |
| Objective | Establish repository-based governance, architecture documentation, development workflow, module ownership, Cursor rules, handoff process, and definition of done. |
| Deliverables | `docs/` governance tree (vision, architecture, principles, governance, workflow, standards, DoD, roadmap, current-state, session-handoff, chat-workflow-log, AiRIA lessons); `docs/modules/*`; `docs/adr` template; `AGENTS.md`; `.cursor/rules/*`; root `README.md` pointer; Constitution; milestone history; prompt library; project state report. Commit **`29d1ba9`** included **39** governance/documentation files only; **no** application, migration, or test files changed. |
| Validation | **78 tests passed**, 43 warnings; `git diff --check` clean; **171** internal links checked, **0** broken; no application, migration, or test files changed. |
| Architectural findings | Modular Flask application; estimate versioning and locking exist; proposal snapshots exist; disabled navigation placeholders for future modules; `project_controls` package exists; hard-coded development `SECRET_KEY` requires later cleanup; accepted-proposal immutability needs targeted product review. |
| Open decisions | Next product milestone (pending Product Architecture Review); authentication model; proposal acceptance → project creation; whether Project Controls needs a dedicated module document. |
| Next milestone | Milestone 002 — Product Architecture Review and Next-Milestone Selection |
| Commit | `29d1ba9` — *Complete Estimator governance baseline and prompt library* (record commit `71e2754` memorialized milestone) |
| Remote at record time | Subsequently pushed; tag `v0.1-governance-baseline` published |

---

## Milestone entry template

```markdown
### Milestone NNN — <Title>

| Field | Content |
|-------|---------|
| Milestone | |
| Status | Planned \| In progress \| Completed pending commit \| Completed |
| Branch | |
| Base commit | |
| Date | |
| Objective | |
| Deliverables | |
| Validation | |
| Architectural findings | |
| Open decisions | |
| Next milestone | |
| Commit | |
```

## Related

- [platform-roadmap.md](platform-roadmap.md) — forward-looking plan
- [project-state-report.md](project-state-report.md) — milestone-level state snapshot
- [session-handoff.md](session-handoff.md) — immediate session continuation

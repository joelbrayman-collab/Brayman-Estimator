# Chat Workflow Log — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Continuity log (append-only) |
| Updated | 2026-08-28 |

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

# Milestone History — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative historical record |
| Updated | 2026-07-25 |
| Policy | **Append-only** |

## Purpose

Record completed and in-progress platform milestones so progress is recoverable without chat history.

## Numbering convention

- Format: `Milestone NNN` with zero-padded integers (`001`, `002`, …)
- Title: short human name
- Separate **planned** milestones (roadmap) from **recorded** entries here

## Required fields (each entry)

Milestone · Status · Branch · Base commit · Objective · Deliverables · Validation · Architectural findings · Open decisions · Next milestone · Commit · Date

## Rules

1. Entries are **append-only** (newest first under Completed / Recorded).
2. Completed entries are **not rewritten** except to correct factual errors (note the correction).
3. Distinguish **Planned** (may live primarily on the roadmap) from **Completed / Recorded** here.
4. “Completed pending baseline commit” means deliverables exist in the working tree awaiting Joel-approved commit.

---

## Recorded milestones

### Milestone 008 — Sheet Intelligence Architecture Planning

| Field | Content |
|-------|---------|
| Milestone | Sheet Intelligence Architecture Planning |
| Status | **Completed pending documentation commit** |
| Branch | `milestone-008-sheet-intelligence` |
| Base | M007 indexing (`cbefe7a`) |
| Date | 2026-07-25 |
| Objective | Design Sheet entity model, page mapping, human review, duplicates/supersession; ADRs only if warranted; **no application code**. |
| Deliverables | [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md); [M008 readiness report](architecture/M008-sheet-intelligence-readiness-report.md); [ADR-017](adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md); [ADR-018](adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md); index/roadmap/state updates. |
| Validation | Docs only; no app/migration/test changes for this milestone. |
| Architectural findings | M007 Pages/Revisions are a sufficient foundation; suggestions ≠ system of record; uniqueness is per Revision; first *coded* sheet work is a later Feature-Gated milestone (recommended M009). |
| Open decisions | Accept ADR-017/018; authorize coded sheet Feature Gate. |
| Next milestone | Feature-Gated Sheet classification and human metadata review (not authorized yet) |
| Commit | Pending |

### Milestone 007 — Document Indexing and Deterministic Metadata Extraction

| Field | Content |
|-------|---------|
| Milestone | Document Indexing and Deterministic Metadata Extraction |
| Status | **Completed** (on feature branch; merge to `main` pending) |
| Branch | `milestone-007-document-indexing` |
| Base | M005 Phase A + M006 architecture |
| Date | 2026-07-25 |
| Objective | First coded Document Intelligence phase: pages, deterministic/embedded-text extraction, provenance, archive, audit, relational search. |
| Deliverables | Models/services for Package/Revision (minimal), Page, ProcessingAttempt/Result, audit; migration `a7c8e9f0b1d2`; UI list/search/reprocess/archive; `tests/test_plan_indexing.py`. |
| Validation | Targeted plan tests + full suite **106 passed**, 110 warnings; `flask db upgrade` to `a7c8e9f0b1d2`; `git diff --check` clean. |
| Architectural findings | Upload ownership unchanged; Estimating untouched; hard-delete blocked once audit/index exist; page ≠ sheet. |
| Open decisions | Sheet Intelligence architecture + coded sheet review (next milestones); raw payload retention TTL; auth; project-detail archived filter. |
| Next milestone | Milestone 008 — Sheet Intelligence architecture planning |
| Commit | `cbefe7a` — *Implement Document Intelligence indexing for plan pages, processing, and search.* |

### Milestone 006 — Document Intelligence Architecture & Feature Gate

| Field | Content |
|-------|---------|
| Milestone | Document Intelligence Architecture and Feature Gate |
| Status | **Completed pending documentation commit** (refinement uncommitted if working tree dirty) |
| Branch | `milestone-005-plan-intelligence-phase-a` |
| Base commit | `098647c` (Phase A); prior M006 pass `35413a1` |
| Date | 2026-07-25 |
| Objective | Design Document Intelligence between PDF upload and take-off; FG-003 readiness with conditions; required ADRs only; no code. |
| Deliverables | FG-003 (**CONDITIONAL PASS**); `architecture/document-intelligence.md`; M006 readiness report; ADR-013–016; roadmap/milestones/state updates. |
| Validation | Docs only; no app/migration/test/dependency changes; link check; `git diff --check`. |
| Architectural findings | M005 supports additive DI; Sheet ≠ Page; extraction provenance required; staged relational search; hard-delete/auth/audit are conditions not FAIL causes. |
| Open decisions | Accept ADR-013–016; authorize M007 implementation gate after FG-003 conditions. |
| Next milestone | M007 — Document indexing and deterministic metadata extraction (not authorized until Feature Gate / prompt) |
| Commit | Prior docs at `35413a1`; refinement pending if uncommitted |

### Milestone 005 — Plan Intelligence Feature Gate and Phase A PDF Upload

| Field | Content |
|-------|---------|
| Milestone | Plan Intelligence Feature Gate and Phase A PDF Upload |
| Status | **Completed** (on feature branch; merge to `main` pending) |
| Branch | `milestone-005-plan-intelligence-phase-a` |
| Base commit | `c59ec01` |
| Date | 2026-07-25 |
| Objective | Complete FG-002; document ADR-012 (revision ownership); implement Phase A only — secure searchable PDF upload/storage foundation. |
| Deliverables | ADR-012 (Proposed); FG-002 (Approved); `app/plan_intelligence/` (models/services/storage/routes); templates; migration `f9c1a2b3d4e5`; project detail link; `tests/test_plan_upload.py`; module/docs updates. |
| Validation | Phase A tests 8 passed; full suite **97 passed**, 68 warnings. No OCR/CAD/AI/estimate insert/revision UI. |
| Architectural findings | Flat `plan_documents` is intentionally interim; Drawing Set/Revision lifecycle owned by ADR-012 for later gates. Private storage under instance/`PLAN_UPLOAD_ROOT`. |
| Open decisions | Accept ADR-012; Document Intelligence M007+ gates; auth for uploads; retention/archival policy when take-offs exist. |
| Next milestone | Milestone 006 — Document Intelligence architecture (then M007+ coded DI) |
| Commit | `098647c` — *Implement Plan Intelligence Phase A PDF upload and storage.* |

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

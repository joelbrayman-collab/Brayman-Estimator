# Feature Gate — Document Intelligence Readiness

| Attribute | Value |
|-----------|--------|
| ID | FG-003 |
| Module | Plan Intelligence (Document Intelligence capability layer) |
| Milestone | Milestone 006 — Document Intelligence Architecture & Feature Gate |
| Status | **PASS** — architecture readiness approved; **implementation not authorized** by this gate |
| Date | 2026-07-25 |
| Base commit / branch | `098647c` on `milestone-005-plan-intelligence-phase-a` (Phase A present) |
| Related ADRs | [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) · [ADR-009](../adr/ADR-009-pdf-first-versus-cad-first.md) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) · [ADR-012](../adr/ADR-012-plan-document-version-ownership.md) · [ADR-013](../adr/ADR-013-document-intelligence-layer-boundary.md) · [ADR-014](../adr/ADR-014-sheet-identity-and-page-mapping.md) |
| Architecture | [architecture/document-intelligence.md](../architecture/document-intelligence.md) |
| Readiness report | [architecture/M006-document-intelligence-readiness-report.md](../architecture/M006-document-intelligence-readiness-report.md) |
| Module | [modules/plan-intelligence.md](../modules/plan-intelligence.md) |

## Purpose

Evaluate whether The Estimator can introduce a **Document Intelligence** layer between Phase A PDF upload (Milestone 005) and future Quantity Take-Off, without rewriting Plan Intelligence ownership or Phase A storage—and whether architecture is ready to sequence Milestones 007–010.

This gate is **readiness / architecture only**. It does **not** authorize application code, migrations, or tests.

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Uploaded PDFs are opaque blobs; estimators need sheet-aware packages, revision metadata, discipline, and search before take-off. |
| 2 | Who is the user? | Estimators and project staff organizing and finding plan content within a project. |
| 3 | Which module owns it? | **Plan Intelligence** — Document Intelligence is a capability layer, not a separate module ([ADR-013](../adr/ADR-013-document-intelligence-layer-boundary.md)). |
| 4 | What data does it own? | Drawing Package, Revision, Sheet, discipline/revision metadata, extraction job results, search index records (future). Continues to own `plan_documents` bytes. |
| 5 | What data does it reference? | `projects`; Phase A `plan_documents`; later take-off citations and estimate versions (reference only). |
| 6 | What may it change? (when later Feature-Gated) | Additive schema under Plan Intelligence; services for indexing/metadata/search; UI for packages/sheets; docs. |
| 7 | What must it not change? | Estimating builder; Proposals; silent estimate mutation; CAD-first strategy; Phase A private storage ownership; hard rewrite of `plan_documents` into a different module. |
| 8 | What are the acceptance criteria? (this gate) | FG-003 PASS/FAIL with scored criteria; architecture doc; required ADRs; M007–M010 order; readiness report; **no code**. |
| 9 | What tests are required? | None in Milestone 006 (docs only). Future implementation milestones define tests. |
| 10 | What documentation must be updated? | FG-003; document-intelligence architecture; ADR-013/014; roadmap; milestones; state/handoff; module; ADR/feature-gate indexes. |
| 11 | Does it require an ADR? | **Yes** — ADR-013 (layer boundary) and ADR-014 (sheet identity). ADR-012 remains authoritative for package/revision lifecycle. |
| 12 | Does it require a database migration? | **Not in M006.** Future coded milestones require additive migrations only. |

## Readiness evaluation

| Criterion | Result | Justification |
|-----------|--------|---------------|
| Document ownership | **PASS** | Plan Intelligence owns plan binaries and future package/revision/sheet records (ADR-007, ADR-012, ADR-013). Estimating does not own files. |
| Metadata model | **PASS** | Phase A register is intentionally thin; target metadata model is defined additively in architecture (no forced redesign of `plan_documents`). |
| Sheet indexing | **PASS** | Feasible as additive `sheets` (and related) tables mapped to PDF pages; identity rules in ADR-014. Not implemented yet — by design. |
| Discipline identification | **PASS** | Controlled vocabulary + optional auto-suggest from filename/title block text; human-confirmable; no architectural blocker. |
| Sheet numbering | **PASS** | Logical sheet number/name is identity; PDF page index is mapping (ADR-014). |
| Revision metadata | **PASS** | ADR-012 lifecycle is compatible with Phase A flat uploads; Drawing Package + Revision tables are additive. |
| Search architecture | **PASS (phased)** | Start with metadata filters + text-layer extraction index; FTS/external search deferred until volume justifies. Compatible with AI citation keys. |
| Future AI compatibility | **PASS** | Stable Sheet / Revision / document ids enable ADR-005 citations without redesign. |
| Scalability | **PASS (POC→scale path)** | Private filesystem adequate for early volume; object-storage migration documented as future ops concern, not a gate failure. |
| Auditability | **PASS with debt** | Architecture requires append-only events; Phase A hard-delete is known debt to retire before take-off/estimate links (ADR-012). |
| Performance | **PASS** | Page-bound indexing and lazy extraction jobs are sufficient for project-scoped POC; no global search required initially. |
| Security | **PASS with open item** | Private non-static storage exists; project scoping exists; **auth/multi-user** remains platform-wide open risk (not unique to DI). |

## Gate decision

| Result | Detail |
|--------|--------|
| **PASS** | Document Intelligence architecture is ready. Milestone 005 Phase A **supports** a Document Intelligence layer **without** architectural rewrite of upload ownership or storage rules. |
| Implementation authorized? | **No** — coded work requires later Feature Gates / milestone prompts (recommended M007+). |
| Conditions | (1) Treat flat `plan_documents` as file register, not final package model. (2) Prefer archive over hard-delete once packages/sheets/take-offs exist. (3) Do not implement OCR/CAD/AI take-off under a “Document Intelligence” label without their own gates. |

## Non-goals (this gate / M006)

- No application code, migrations, or tests  
- No OCR / CAD / AI quantity extraction  
- No estimate insertion  
- No redesign of Estimating or Proposals  
- No Drawing Package UI implementation  

## Approval

| Role | Decision | Date |
|------|----------|------|
| Cursor (architecture evaluation) | **PASS** with conditions above | 2026-07-25 |
| Joel | Pending review | |
| Implementation authorized by FG-003? | **No** | 2026-07-25 |

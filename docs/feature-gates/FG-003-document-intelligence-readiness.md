# Feature Gate — Document Intelligence Readiness

| Attribute | Value |
|-----------|--------|
| ID | FG-003 |
| Module | Plan Intelligence (Document Intelligence capability layer) |
| Milestone | Milestone 006 — Document Intelligence Architecture and Feature Gate |
| Status | **CONDITIONAL PASS** — architecture ready; **implementation not authorized** until listed conditions are met |
| Date | 2026-07-25 |
| Evidence baseline | Branch `milestone-005-plan-intelligence-phase-a` @ `098647c` (Phase A) + prior M006 docs @ `35413a1` |
| Related ADRs | [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) · [ADR-009](../adr/ADR-009-pdf-first-versus-cad-first.md) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) · [ADR-012](../adr/ADR-012-plan-document-version-ownership.md) · [ADR-013](../adr/ADR-013-document-intelligence-layer-boundary.md) · [ADR-014](../adr/ADR-014-sheet-identity-and-page-mapping.md) · [ADR-015](../adr/ADR-015-extracted-metadata-ownership-and-provenance.md) · [ADR-016](../adr/ADR-016-document-intelligence-search-strategy.md) |
| Architecture | [architecture/document-intelligence.md](../architecture/document-intelligence.md) |
| Readiness report | [architecture/M006-document-intelligence-readiness-report.md](../architecture/M006-document-intelligence-readiness-report.md) |
| Module | [modules/plan-intelligence.md](../modules/plan-intelligence.md) |

## Purpose

Determine whether Document Intelligence—sitting between M005 PDF upload/storage and future Quantity Take-Off—can be designed and later implemented **without** rewriting Plan Intelligence ownership or Estimating, and under what **conditions** the first coded milestone may proceed.

This gate is **architecture readiness only**. A technical path existing is **not** sufficient to authorize implementation.

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Uploaded PDFs are opaque; estimators need page/sheet awareness, package/revision context, metadata, and search before take-off. |
| 2 | Who is the user? | Estimators and project staff organizing, reviewing, and finding plan content within a project. |
| 3 | Which module owns it? | **Plan Intelligence** (Document Intelligence is a capability layer — [ADR-013](../adr/ADR-013-document-intelligence-layer-boundary.md)). |
| 4 | What data does it own? | Drawing Package, Revision, Page, Sheet, extraction/processing results (incl. raw), searchable metadata, audit events; continues to own `plan_documents` bytes. |
| 5 | What data does it reference? | `projects`; Phase A `plan_documents`; later take-off candidates and estimate versions (reference / audit only). |
| 6 | What may it change? (later Feature-Gated) | Additive Plan Intelligence schema/services/UI; docs. |
| 7 | What must it not change? | Estimating builder ownership; Proposals; silent estimate mutation; CAD-first strategy; moving plan bytes out of Plan Intelligence. |
| 8 | Acceptance criteria (this gate) | Scored readiness; architecture covering required concepts; ADRs only where needed; M007–M010 sequence; risks/debt; **no code**. |
| 9 | Tests required? | None in M006. |
| 10 | Documentation updates? | FG-003; DI architecture; readiness report; ADR index; roadmap; milestones; state/handoff/log; module. |
| 11 | ADR required? | **Yes** — 013–016 (see ADR section). ADR-012 remains package/revision lifecycle authority. |
| 12 | Migration in M006? | **No.** Future additive migrations only under implementation gates. |

## Readiness evaluation

| Criterion | Result | Justification |
|-----------|--------|---------------|
| Module / data ownership | **PASS** | Plan Intelligence owns files and DI records (ADR-007/012/013). Estimating unchanged. |
| PlanDocument suitability | **PASS** | Thin register + private storage + checksum + page_count + has_text_layer is a viable file SoR for additive Page/Sheet/Package. |
| Drawing package ownership | **PASS** | ADR-012 + product name Drawing Package; additive tables; not in M005 code (by design). |
| Document↔sheet relationships | **PASS** | Via Revision membership + Page mapping (ADR-014); page ≠ sheet. |
| Metadata model | **PASS** | Target model documented; Phase A metadata intentionally minimal. |
| Page / sheet indexing | **PASS** | Page as PDF index unit; Sheet as logical drawing; edge cases documented. |
| Discipline identification | **PASS** | Controlled vocabulary; suggest + human confirm. |
| Sheet numbering / naming | **PASS** | Human-visible identifiers under Revision (ADR-014). |
| Revision metadata / active / superseded | **PASS** | ADR-012 rules; additive schema. |
| Metadata extraction boundaries | **PASS** | Deterministic/text-layer first; proposals not commercial facts (ADR-015). |
| Search architecture | **PASS** | Staged relational → optional FTS → external only with demonstrated need (ADR-016). |
| Citations / auditability | **CONDITIONAL** | Architecture + ADR-005/012 define trail; Phase A lacks audit events and prefers hard-delete — must fix before commercial links. |
| Future OCR / CAD / AI | **PASS** | Hooks documented; separate gates; confidence never auto-authorizes commercial actions (ADR-006/011). |
| Scalability / performance | **PASS** | Project-scoped POC on filesystem + relational indexes; scale path documented. |
| Storage security | **PASS** | Private non-static storage exists in M005. |
| Authorization | **CONDITIONAL** | Project FK scoping exists; **no auth/multi-user** yet — platform debt. |
| Deletion / archival | **CONDITIONAL** | ADR-012 prefers archive; M005 hard-deletes — must retire before Sheet/take-off dependents. |
| Migration requirements | **PASS** | Additive-only path documented; no forced reshape of `plan_documents`. |
| Impact on Estimating | **PASS** | Reference-only; no estimate mutation from DI confidence or metadata. |

## Gate decision

| Result | Detail |
|--------|--------|
| **CONDITIONAL PASS** | Architecture is sound and M005 **supports** an additive Document Intelligence layer **without** ownership rewrite. Implementation remains **blocked** until conditions below are satisfied under a **separate** implementation Feature Gate / approved Cursor prompt. |
| Why not unconditional PASS? | Audit, archival, and authorization gaps are material. Approving code solely because tables *could* be added would violate governance (“path possible ≠ authorized”). |
| Why not FAIL? | No fundamental ownership conflict; Phase A storage abstraction and model are compatible; gaps are remediable additively. |

## Conditions before any Document Intelligence implementation

These conditions must be satisfied (in the M007 Feature Gate / prompt or earlier) before application code, migrations, or tests for Document Intelligence are authorized:

1. **Joel accepts or amends** ADR-013, ADR-014, ADR-015, and ADR-016 (and treats ADR-012 as governing for package/revision lifecycle).
2. **Archive-over-hard-delete** policy is in scope for the first coded DI milestone (or hard-delete is disabled once dependents exist).
3. **Append-only audit events** for upload, process, metadata correction, activate/supersede, and archive are in scope for the first coded DI milestone (or an approved interim equivalent).
4. First coded milestone stays within **M007 scope** (indexing + deterministic extraction); **no OCR engine**, **no CAD**, **no AI quantity extraction**, **no estimate insertion**.
5. **Sheet ≠ Page** (ADR-014) is enforced in schema/UX from the first milestone that creates Sheets.
6. Extracted metadata and confidence values are stored as **proposals / processing results** (ADR-015); they **never** silently mutate estimates.
7. Search uses the **staged relational strategy** (ADR-016); no external search service without a later demonstrated-need gate.
8. **Project-scoped access** remains mandatory on every query; platform auth debt is acknowledged and not papered over.
9. Migrations remain **additive** only; no destructive reshape of `plan_documents`.
10. A dedicated **implementation Feature Gate or approved Cursor prompt** for M007 is issued; FG-003 alone does **not** authorize code.

## Non-goals (M006)

- Application code, migrations, tests, dependency changes
- Commits or pushes
- OCR / CAD / AI quantity extraction
- Estimate mapping or revision comparison products

## Approval

| Role | Decision | Date |
|------|----------|------|
| Cursor (architecture evaluation) | **CONDITIONAL PASS** | 2026-07-25 |
| Joel | Pending review | |
| Implementation authorized by FG-003? | **No** | 2026-07-25 |

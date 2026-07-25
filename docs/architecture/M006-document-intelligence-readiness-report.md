# Milestone 006 — Document Intelligence Readiness Report

| Attribute | Value |
|-----------|--------|
| Milestone | 006 — Document Intelligence Architecture and Feature Gate |
| Date | 2026-07-25 |
| Branch context | `milestone-005-plan-intelligence-phase-a` |
| Scope | Documentation and planning **only** |
| FG-003 | **CONDITIONAL PASS** (implementation not authorized) |
| Code / migrations / tests / dependencies / commits / pushes | **None** for this refinement pass |

---

## 1. Executive readiness summary

**Recommendation: proceed with architecture; do not implement yet.**

M005 Phase A (private PDF storage + `plan_documents`) is a **compatible foundation** for Document Intelligence. No rewrite of upload ownership or Estimating is required. Gaps in audit, archival, and authorization are **material**, so FG-003 is a **CONDITIONAL PASS**, not an unconditional license to code.

Authorize **M007** only after FG-003 conditions are met and a dedicated implementation Feature Gate / Cursor prompt is approved.

---

## 2. FG-003 result and conditions

**Result: CONDITIONAL PASS**

Architecture is sound; M005 supports additive DI. Implementation remains blocked until:

1. Joel accepts/amends ADR-013–016 (and ADR-012 lifecycle).
2. Archive-over-hard-delete is in first coded DI scope.
3. Append-only audit events are in first coded DI scope.
4. First code stays in M007 bounds (no OCR/CAD/AI quantities/estimate insert).
5. Sheet ≠ Page enforced when Sheets appear.
6. Extraction confidence never mutates estimates.
7. Search follows staged relational strategy (ADR-016).
8. Project-scoped queries remain mandatory.
9. Migrations additive only.
10. Separate M007 implementation authorization exists (FG-003 alone insufficient).

Full scorecard: [FG-003](../feature-gates/FG-003-document-intelligence-readiness.md).

---

## 3. M005 compatibility (inspected, not altered)

| Area | Finding |
|------|---------|
| Model | Thin `PlanDocument` suitable as file register |
| Storage | Private project-keyed paths; traversal guards |
| Routes | Upload/list/detail/download/delete — adequate attachment points |
| Ownership | Plan Intelligence package; Estimating untouched |
| Debt | Hard-delete; no audit table; no package/page/sheet |

---

## 4. ADR decisions and numbering

| ADR | Title | Why required |
|-----|-------|----------------|
| **013** (existing) | Document Intelligence layer boundary | Prevents second module / ownership split |
| **014** (existing) | Sheet identity and page mapping | Sheet ≠ PDF page |
| **015** (**new**) | Extracted metadata ownership and provenance | Raw results, attempt versioning, human SoR, confidence limits |
| **016** (**new**) | Document Intelligence search strategy | Relational → FTS → external only with need |

Not created: OCR engine choice, CAD format pick, embedding search, confidence numerics (ADR-011), estimate mapping (ADR-006).

Next free ADR numbers after ADR-016 belong to subsequent architecture milestones (e.g. Sheet Intelligence suggestion/review ADRs) — not required for M007 indexing code.

---

## 5. Recommended M007–M010 sequence

Aligned with repository evidence (ADR-012/014/015) and the milestone prompt’s preferred shape. Estimate mapping and revision-comparison *products* remain **outside** M007–M010.

### M007 — Document indexing and deterministic metadata extraction

| | |
|--|--|
| **Objective** | Make uploaded PDFs page-addressable and extract deterministic/embedded-text metadata with provenance. |
| **Scope** | `Page` records; processing attempts/results + raw payload; text harvest; relational searchable fields; **minimal** Drawing Package + Revision membership (incl. default backfill for existing uploads); archive-over-delete; audit events. |
| **Exclusions** | Sheet classification UX; OCR engine; CAD; AI quantities; scale tools; estimate insert; external search. |
| **Dependencies** | FG-003 conditions; ADR-012/013/015/016; M005. |
| **Migrations** | Additive: packages, revisions, membership, pages, processing tables, audit; soft-archive fields. |
| **Tests** | Page indexing; extraction success/fail leaves file intact; reprocess retains prior raw; project scoping; archive vs delete; no Estimating side effects. |
| **Completion** | Every new upload yields pages + processable metadata trail; orphans backfillable; hard-delete constrained when policy requires. |

### M008 — Sheet classification and human metadata review *(implementation; after architecture docs)*

| | |
|--|--|
| **Objective** | Establish logical Sheets with human-reviewed identifiers, titles, discipline, drawing status. |
| **Scope** | Sheet entities; page↔sheet mapping (incl. non-1:1 cases); suggestion apply/reject; human corrections as SoR; sheet filters. |
| **Exclusions** | Scale calibration; measurement tools; AI quantity extraction; estimate mapping. |
| **Dependencies** | M007; Sheet Intelligence architecture acceptance; dedicated Feature Gate. |
| **Migrations** | Additive sheets / sheet_pages; discipline/status fields. |
| **Tests** | Sheet ≠ page; uniqueness warnings; human correction not clobbered by reprocess; filters. |
| **Completion** | Reviewer can produce a trusted sheet index for an Active Revision. |
| **Note** | A separate docs-only Sheet Intelligence architecture milestone may precede this coded work; numbering on the roadmap may insert architecture before coded sheets. |

### M009 — Scale calibration and manual measurement foundation

| | |
|--|--|
| **Objective** | Enable human scale confirmation and basic manual measure primitives on Sheets. |
| **Scope** | Scale fields; calibration UX; count/length/area foundation (citations-ready regions); no silent estimate write. |
| **Exclusions** | AI extraction; estimate insertion; CAD; full OCR product. |
| **Dependencies** | M008; ADR-005 citation shape readiness. |
| **Migrations** | Additive scale/viewport/measurement draft tables as needed. |
| **Tests** | Scale required before measurement eligibility; measurements cite sheet/page/region; Estimating unchanged. |
| **Completion** | Estimator can manually produce cited measurements on a reviewed sheet. |

### M010 — AI-assisted quantity extraction proof of concept

| | |
|--|--|
| **Objective** | Narrow POC: AI proposes quantities for a single agreed element (e.g. interior doors) with confidence + human review. |
| **Scope** | Candidate generation; confidence display (ADR-011); accept/adjust/reject; take-off package draft; **no** estimate insert. |
| **Exclusions** | Estimate mapping (separate gate); multi-trade expansion; supplier; CAD-first. |
| **Dependencies** | M009; ADR-005/006/011; ADR-010 review as needed. |
| **Migrations** | Additive candidate/review tables. |
| **Tests** | No estimate mutation; citations present; rejected candidates excluded; confidence cannot auto-insert. |
| **Completion** | Joel-agreed POC element reviewed end-to-end without touching Estimating writes. |

---

## 6. Risks and technical debt

### Risks

| Risk | Type | Mitigation |
|------|------|------------|
| Flat uploads treated as final model | Architectural | ADR-012/013; M007 minimal package |
| Hard-delete after dependents | Data integrity | Archive-first condition |
| Page mistaken for Sheet | Data integrity | ADR-014; M008 |
| Confidence → commercial action | Architectural / financial | ADR-006/011/015 |
| Auth gap / cross-project leakage | Security | Project filters; platform auth later |
| Extraction accuracy / bad sheet numbers | Extraction | Human review M008; preserve raw |
| Premature external search / OCR spend | Operational | ADR-016; hooks only |
| Revision sprawl / duplicate sheets | Revision mgmt | Active/superseded rules; uniqueness warnings |
| Large raw payload growth | Performance / ops | Retention policy later |
| Migration ordering mistakes | Migration | Additive-only; Feature Gates per milestone |

### M005 technical debt relevant to DI

Hard-delete · no audit events · no package/revision/page/sheet · text detection only (no harvest) · instance-local filesystem · no auth

### Deferred decisions / assumptions

Exact sheet uniqueness rules · page index 0 vs 1 · retention TTL for raw payloads · object storage timing · POC element confirmation for M010 · numeric confidence thresholds (ADR-011)

---

## 7. Future migration requirements (summary)

Additive only across M007–M010 as listed above. Optional backfill: wrap existing `plan_documents` into default Drawing Package + Revision. **No** destructive reshape of `plan_documents`.

---

## 8. Documentation synchronization

Updated/created: FG-003; document-intelligence.md; this report; ADR-015; ADR-016; indexes; module; roadmap; milestones; current-state; project-state; session-handoff; chat-workflow-log; docs README as needed.

---

## 9. Definition of Done checklist

| Item | Status |
|------|--------|
| FG-003 PASS / CONDITIONAL PASS / FAIL | ✓ CONDITIONAL PASS |
| DI architecture documented | ✓ |
| M005 vs future distinguished | ✓ |
| Package/Document/Page/Sheet/Revision/Discipline ownership | ✓ |
| Metadata/processing boundaries | ✓ |
| Search strategy | ✓ ADR-016 |
| OCR/CAD/AI boundaries | ✓ |
| Genuine ADRs only | ✓ 015, 016 added; 013/014 retained |
| Risks, debt, migrations | ✓ |
| M007–M010 sequence | ✓ |
| State/roadmap synced | ✓ |
| Links validated | ✓ 341 internal links, 0 broken |
| `git diff --check` clean | ✓ |
| No app / migrations / tests / deps / commit / push | ✓ |

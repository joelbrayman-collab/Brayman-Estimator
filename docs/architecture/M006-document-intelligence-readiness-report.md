# Milestone 006 — Document Intelligence Readiness Report

| Attribute | Value |
|-----------|--------|
| Milestone | 006 — Document Intelligence Architecture & Feature Gate |
| Date | 2026-07-25 |
| Branch context | `milestone-005-plan-intelligence-phase-a` @ `098647c` (Phase A present) |
| Scope | Documentation and planning **only** |
| FG-003 | **PASS** (architecture readiness; implementation not authorized) |
| Code / migrations / tests / commits | **None** (this milestone) |

---

## 1. Executive recommendation

**Proceed.** Milestone 005 Phase A is a sufficient foundation for a Document Intelligence layer **without** rewriting upload ownership, private storage, or Estimating.

Authorize **architecture and sequencing now**; authorize **code only** via later Feature-Gated milestones (**M007–M010** below).

Do **not** start OCR, CAD, AI take-off, or estimate insertion under this milestone’s label.

---

## 2. M005 compatibility finding

| Question | Answer |
|----------|--------|
| Does flat `plan_documents` support Document Intelligence? | **Yes**, as the **file register** referenced by additive Package / Revision / Sheet / search tables. |
| Architectural rewrite required? | **No.** |
| Primary gaps? | No package/revision/sheet model yet; Phase A **hard-delete**; thin audit; no search index. |

These gaps are **expected Phase A limitations**, already anticipated by ADR-012. They are implementation debt for M007+, not FG-003 failures.

---

## 3. Deliverables (M006)

| Deliverable | Path | Status |
|-------------|------|--------|
| FG-003 | `docs/feature-gates/FG-003-document-intelligence-readiness.md` | **PASS** |
| Architecture | `docs/architecture/document-intelligence.md` | Done |
| ADR-013 | Layer boundary (Plan Intelligence owns DI) | Proposed |
| ADR-014 | Sheet identity vs PDF page mapping | Proposed |
| This report | `docs/architecture/M006-document-intelligence-readiness-report.md` | Done |
| Roadmap / milestones / state updates | `docs/*` | Done |

ADRs **not** created (already covered or premature): search-engine vendor choice; OCR engine choice; CAD format priority (ADR-009/010); confidence numerics (ADR-011).

---

## 4. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Implementers treat flat uploads as final package model | High | ADR-012/013 + architecture naming; M007 creates Package/Revision before take-off |
| Phase A hard-delete destroys history after sheets/take-offs exist | High | Archive-first policy in M007; restrict delete when dependents exist |
| Sheet identity = page index only | High | ADR-014; M008 indexing UX |
| Document Intelligence becomes a second module / ownership split | Medium | ADR-013 |
| Premature OCR/AI spend | Medium | ADR-009/010; keep M009 text-layer-first; OCR hooks only in M010 |
| Auth missing → cross-project document exposure | Medium | Platform auth milestone; keep project scoping in every query |
| Search scope creep (embeddings / global corpus) | Low–Med | Phased search in architecture; separate gate for AI search |

---

## 5. Technical debt (from Phase A into DI)

| Debt | Impact | Retire in |
|------|--------|-----------|
| Hard-delete of `plan_documents` | Breaks ADR-012 archival preference | M007 |
| No append-only plan audit events | Weak compliance trail | M007 |
| No Drawing Package / Revision | Cannot safely supersede sets | M007 |
| No Sheet records | Citations cannot stabilize | M008 |
| Text-layer detect only (no harvest/index) | Weak findability | M009 |
| Instance-local filesystem only | Scale/ops limit | Later ops milestone (not blocking POC) |

---

## 6. Future migration requirements

All migrations must be **additive** and Feature-Gated:

1. **M007:** `drawing_packages`, `drawing_revisions`, revision↔document membership; optional `archived_at` / soft-delete flags; `plan_audit_events` (or equivalent).
2. **M008:** `plan_sheets` (+ page mapping columns/tables); discipline codes.
3. **M009:** extract job/result tables; FTS/search mirror table or index.
4. **M010:** scale fields on sheets; OCR job/result tables; optional derivative artifact storage **without** overwriting originals.

No destructive reshape of `plan_documents` is required. Optional later backfill: wrap existing orphan PlanDocuments into a default Package/Revision per project.

---

## 7. Implementation order — M007 through M010

| Milestone | Name | Objective | Depends on | Explicit non-goals |
|-----------|------|-----------|------------|-------------------|
| **M007** | Drawing Package & Revision Foundation | Packages, revisions (active/superseded), attach Phase A documents, archive-over-delete, basic audit events | FG for M007; ADR-012/013 | Sheets UI; OCR; take-off; estimate insert |
| **M008** | Sheet Indexing | Create/edit Sheets; discipline; sheet numbers/names; page mapping (ADR-014) | M007 | Full-text search cluster; AI; scale tools |
| **M009** | Metadata Extraction & Search | Text-layer harvest; metadata suggestions; project-scoped search/filter index | M008 | OCR engine (unless tiny gated spike); embeddings; CAD |
| **M010** | Scale Foundation & OCR Hooks | Human scale confirmation fields; OCR job interfaces / storage hooks; readiness for manual measurement milestone | M009; ADR-010 review | Full OCR productization; AI element recognition; estimate mapping |

**After M010:** return to roadmap Phase B remainder / Phase C (manual measurement tools → AI extraction) under new gates — Document Intelligence will then be the stable substrate.

**Mapping to roadmap Phases A–G:**

| Roadmap phase | Milestone coverage |
|---------------|-------------------|
| A Upload | M005 (done) |
| Document Intelligence (new explicit mid-layer) | M006 (docs) → M007–M009 (code) |
| B Sheet/scale/manual measure | M008–M010 (partial) + follow-on coded milestone for measurement tools |
| C AI extraction | After M010 + ADR-011 thresholds |
| D Estimate mapping | Later (ADR-006) |
| E–F Supplier | Separate program |
| G CAD | ADR-009 separate gate |

---

## 8. FG-003 scorecard (summary)

**PASS** on ownership, metadata model, sheet indexing design, discipline, sheet numbering, revision metadata, phased search, AI compatibility, scalability path, performance approach, and security posture—with **known debt** on audit/delete and **open** platform auth.

**Implementation not authorized** by FG-003.

---

## 9. Suggested Joel decisions

1. Accept or amend ADR-013 and ADR-014 (and remaining Proposed Plan Intelligence ADRs as ready).
2. Approve sequencing M007 → M010 as above (or reorder with written rationale).
3. Issue an implementation Feature Gate / Cursor prompt for **M007 only** when ready to write code.
4. Confirm product term **Drawing Package** (vs ADR-012 “Drawing Set”) for UI copy.

---

## 10. Definition of Done checklist

| Item | Done |
|------|------|
| FG-003 completed | ✓ |
| Architecture updated | ✓ |
| Roadmap updated if necessary | ✓ |
| Required ADRs added (013, 014 only) | ✓ |
| No application code | ✓ |
| No migrations | ✓ |
| No tests | ✓ |
| No commits | ✓ (this milestone’s instruction) |

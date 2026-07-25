# Milestone 008 — Sheet Intelligence Readiness Report

| Attribute | Value |
|-----------|--------|
| Milestone | 008 — Sheet Intelligence Architecture Planning |
| Date | 2026-07-25 |
| Scope | Documentation and planning **only** |
| Code / migrations / tests / commits | **None** |
| Depends on | M007 Page indexing (implemented in working tree); ADR-012–018 |

---

## 1. Executive summary

**Recommendation: proceed to design acceptance, then Feature-Gate coded Sheet work as M009.**

M007 provides Pages, minimal Packages/Revisions, text harvest, and provenance — a sufficient foundation for Sheets. Sheet Intelligence should introduce logical **Sheet** entities with human review of suggested metadata, non-1:1 page mapping, and revision-aware uniqueness — **without** OCR, CAD, AI quantities, scale tools, or estimate insertion.

This milestone is **architecture only**. Implementation is **not** authorized here.

**Sequencing correction:** Earlier M006 text treated “M008” as sheet *implementation*. Milestone 008 is now architecture planning; **M009** is the recommended first *coded* Sheet Intelligence milestone. Former scale → **M010**; former AI POC → **M011**.

---

## 2. Architectural recommendations

1. Keep Sheets inside Plan Intelligence (ADR-013); do not create a separate module.  
2. Sheet belongs to a **Revision**; page mapping uses M007 0-based `PlanPage` (ADR-014).  
3. Discipline is a **controlled code attribute**, not a standalone commercial entity.  
4. Suggestions + confidence are proposals; human Accept/Edit/Reject makes SoR (ADR-017).  
5. Uniqueness of sheet numbers is **per Revision**; superseded revisions keep history (ADR-018).  
6. Cover/SPEC/blank pages often have no take-off Sheet; multi-page Sheets use ordered maps; addenda use new package/revision.  
7. Prefer generating **suggestions** over auto-creating reviewed Sheets on day one.  
8. Archive-over-delete remains mandatory once Sheets exist.

---

## 3. Required ADRs

| ADR | Action | Why |
|-----|--------|-----|
| 013–016 | Retain | Layer, sheet≠page basis, provenance, search |
| 014 | Retain | Core Sheet vs Page mapping (implementation note: coded work → M009) |
| 015 | Retain | Human SoR / confidence limits |
| **017** | **Created** | Suggest → accept/reject/edit workflow for sheet metadata |
| **018** | **Created** | Uniqueness, duplicates, supersession, addenda |

**Not created:** separate Discipline-module ADR (attribute + vocabulary is enough); OCR/CAD/AI ADRs already exist or deferred.

Next free number after this milestone: **ADR-019**.

---

## 4. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Auto-accept false sheet numbers | High | ADR-017; no auto-apply |
| Page treated as Sheet in code | High | ADR-014; M009 tests |
| Duplicate numbers in Active Revision | High | ADR-018 warn/block finalize |
| In-place overwrite on new upload | High | ADR-012/018 new Revision |
| Shared-page multi-sheet confusion | Medium | Warn; prefer split PDFs |
| Suggestion noise / UX overload | Medium | Start with simple heuristics; human queue |
| Auth still open | Medium | Project scoping; platform auth later |
| Premature scale/AI in “sheet” milestone | Medium | Hard exclusions on M009 gate |

### Migration risks

Partial unique indexes on SQLite; backfill temptation to auto-create Sheets from every Page — prefer suggestions-only backfill.

### M007 debt relevant to Sheets

Project detail may still list archived docs (pre-commit M007 fix); default package/revision is minimal — sheet UI must not pretend full revision management is done.

---

## 5. Recommended implementation scope for M009

| | |
|--|--|
| **Name** | Sheet Classification and Human Metadata Review |
| **Objective** | Trusted, revision-scoped Sheet index with human-reviewed identifiers and page maps. |
| **In scope** | `plan_sheets`, `plan_sheet_pages`, suggestions + accept/reject/edit; discipline codes; drawing/review status; filters by sheet number/title/discipline; audit events; uniqueness warnings per Active Revision; project-scoped UI. |
| **Out of scope** | Scale calibration; manual measurement tools; OCR engine; CAD; AI quantity extraction; estimate insertion; full revision-comparison product; auto-merge checksum duplicates. |
| **Dependencies** | M007 complete; Joel acceptance of ADR-017/018 (and related); dedicated Feature Gate / Cursor prompt for M009. |
| **Migrations** | Additive sheet/suggestion/map tables only. |
| **Tests** | Sheet ≠ page; mapping cardinalities; accept does not happen from confidence alone; reject/reprocess does not clobber SoR; duplicate number warning; project isolation; Estimating untouched. |
| **Completion** | Reviewer can produce a reviewed sheet index for an Active Revision. |

**Then:** M010 scale/manual measure · M011 AI quantity POC · estimate mapping under separate gate.

---

## 6. Definition of Done checklist

| Item | Status |
|------|--------|
| Sheet Intelligence architecture documented | ✓ |
| Required ADRs only if warranted | ✓ 017, 018 |
| Risks and migration strategy documented | ✓ |
| M009 implementation scope recommended | ✓ |
| No application code | ✓ |
| No migrations | ✓ |
| No tests | ✓ |
| No commits | ✓ |

---

## Appendix — Milestone 008 record (for milestones.md on M008 commit)

| Field | Content |
|-------|---------|
| Milestone | Sheet Intelligence Architecture Planning |
| Status | **Completed pending documentation commit** |
| Branch | `milestone-007-document-indexing` (or successor) |
| Date | 2026-07-25 |
| Objective | Design Sheet entity model, page mapping, human review, duplicates/supersession; ADRs only if warranted; no code. |
| Deliverables | `architecture/sheet-intelligence.md`; this readiness report; ADR-017; ADR-018; roadmap/milestone/state index updates. |
| Validation | Docs only; no app/migration/test changes for this milestone. |
| Architectural findings | M007 Pages/Revisions sufficient foundation; suggestions≠SoR; uniqueness per Revision; M009 is first coded sheet milestone. |
| Open decisions | Accept ADR-017/018; authorize M009 Feature Gate. |
| Next milestone | M009 — Sheet classification and human metadata review (not authorized yet) |
| Commit | Pending |

### Chat workflow summary (preserve for chat-workflow-log on M008 commit)

| Field | Content |
|-------|---------|
| Date | 2026-07-25 |
| Objective | Architecture for Sheets from indexed Pages; no code |
| Architectural decision | ADR-017 review workflow; ADR-018 uniqueness/supersession; M009 = first coded sheets; M010 scale; M011 AI POC |
| Files | docs only — `sheet-intelligence.md`; this report; ADR-017/018; roadmap resequence |
| Next | Joel review; Feature Gate M009 when ready |

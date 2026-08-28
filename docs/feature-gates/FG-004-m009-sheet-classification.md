# Feature Gate — M009 Sheet Classification / Human Metadata Review

| Attribute | Value |
|-----------|--------|
| ID | **FG-004** |
| Milestone | **M009** — Sheet Classification / Human Metadata Review |
| Module | Plan Intelligence |
| Date | 2026-08-28 |
| Approved baseline | `main` @ `9a13655` (CAR-001); intended Alembic head `a7c8e9f0b1d2` (re-verify at implementation) |
| Architecture | [sheet-intelligence.md](../architecture/sheet-intelligence.md) (M008) |
| Module doc | [modules/plan-intelligence.md](../modules/plan-intelligence.md) |
| Related ADRs | [ADR-017](../adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md) **Accepted** · [ADR-018](../adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md) **Accepted** · [ADR-014](../adr/ADR-014-sheet-identity-and-page-mapping.md) (M008 identity model; document status remains Proposed) · [ADR-013](../adr/ADR-013-document-intelligence-layer-boundary.md) · [ADR-015](../adr/ADR-015-extracted-metadata-ownership-and-provenance.md) · [ADR-012](../adr/ADR-012-plan-document-version-ownership.md) |
| CAR | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |

## Status

| Layer | State |
|-------|--------|
| Architecture (M008) | **APPROVED** (Sheet Intelligence architecture on `main`) |
| Feature Gate (this document) | **APPROVED** (2026-08-28, Joel via this prompt) |
| Implementation | **NOT YET STARTED** — not authorized by this governance prompt |

M009 code, migrations, routes, UI, and tests begin **only** after a subsequent **approved Cursor implementation prompt** that cites FG-004.

This Feature Gate does **not** create schema, migrations, or application files.

---

## Objective

Extend existing Plan Intelligence so uploaded plan pages can be represented as construction **Sheets** with structured metadata and a **human review** workflow, while preserving original plan documents, pages, provenance, revisions, and historical state.

M009 implements the architecture already established by M008 and Accepted ADR-017/ADR-018. It does **not** authorize AI take-off, scale measurement, estimating insertion, field/BUILD/MONITOR/LEARN, pricing changes, contracts, QuickBooks, or mobile development.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Indexed PDF pages are not yet construction Sheets. Estimators need revision-scoped sheet identity (number, title, discipline) with human accept/edit/reject before later scale/take-off. |
| 2 | Who is the user? | Estimators and take-off reviewers working in the **office** Plan Intelligence UI on a Project. |
| 3 | Which module owns it? | **Plan Intelligence** (Sheet Intelligence capability layer; ADR-013). Do not create a separate sheet subsystem. |
| 4 | What data does it own? | Additive Sheet records, page↔sheet maps, and sheet-metadata suggestions under a Drawing Revision, plus sheet-related audit events — conceptual tables in [sheet-intelligence.md](../architecture/sheet-intelligence.md) §7: `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions` (names illustrative). Optional `discipline_codes` seed table is **not required** (discipline is a string code on Sheet). |
| 5 | What data does it reference? | `projects` (lifecycle hub, ADR-019); `drawing_packages` / `drawing_revisions`; `plan_documents`; `plan_pages` (0-based `page_index`); `plan_processing_attempts` / results as suggestion source. Must not take ownership of those records. |
| 6 | What may it change? | Additive models/services/routes/templates under `app/plan_intelligence/`; additive Alembic revision(s) for M009 sheet tables only; project-scoped review UI; tests; docs listed in this gate. |
| 7 | What must it not change? | Estimate/proposal/change-order behaviour; cost library; PlanDocument bytes and PlanPage source fields as SoR; existing M007 processing payload immutability; auth implementation; BUILD/field; pricing-policy calculations; unrelated UI redesign. |
| 8 | What are the acceptance criteria? | See **Acceptance criteria** below. |
| 9 | What tests are required? | See **Required implementation tests**. |
| 10 | What documentation must be updated? | This gate; ADR-017/018; ADR index; FG index; plan-intelligence module; sheet-intelligence status; current-state; project-state-report; session-handoff; roadmap; milestones; chat-workflow-log. |
| 11 | Does it require an ADR? | **Yes — existing.** ADR-017/018 **Accepted** by this prompt. M009 implements Page ≠ Sheet per M008 / ADR-014 **without** reopening those decisions. ADR-014 document status remains Proposed (not silently accepted here). No new ADR required for M009 if implementation stays inside M008 field catalog. |
| 12 | Does it require a database migration? | **Yes — future implementation prompt only.** Additive sheet/map/suggestion tables. This governance prompt must **not** create migrations. |

---

## Core invariants (must remain true)

**A. Page ≠ Sheet.** `PlanPage` remains the PDF page record. A Sheet is a construction-domain interpretation associated with page(s) via mapping. Do not collapse the concepts or treat `page_index` as Sheet identity.

**B. Original document preservation.** `PlanDocument` / `PlanPage` remain authoritative source evidence. Sheet metadata must not alter source files or mutate page extraction SoR.

**C. Human authority.** Suggestions may be proposed. A human accepts, edits, or rejects. AI/confidence never silently sets approved authoritative metadata (ADR-017).

**D. Provenance.** Preserve source document, page, processing attempt/result where applicable, suggestion provenance, reviewer action, and timestamps. **Do not fabricate actor identity** before auth exists. Reuse `plan_audit_events` (and optional additive `sheet_id` if required by M008 §7). No fake User rows.

**E. History.** Supersession/versioning/archive per ADR-018: sheets under superseded revisions are immutable historical records; new revised sets get new Sheet rows; prefer `void`/archive over hard-delete.

**F. Module ownership.** Sheets stay in Plan Intelligence.

**G. Project.** Existing `Project` remains the CalibAi lifecycle hub. M009 does not introduce a parallel Job entity.

---

## Authorized M009 schema / behaviour (from M008 — do not invent fields)

Use [sheet-intelligence.md](../architecture/sheet-intelligence.md) and ADR-017/018. Implementation must **not** add commercial or take-off fields.

| Concern | Architected in M008 / ADRs |
|---------|----------------------------|
| Sheet durable model | Sheet under `drawing_revision_id`; human-visible **number**, **title**, **discipline_code**; **drawing_status**; **review_status** |
| Discipline | String codes already listed (`ARCH`, `STR`, `MECH`, `ELEC`, `PLUMB`, `CIVIL`, `FIRE`, `OTHER`, `COVER`, `INDEX`, `SPEC`, `NON_DRAWING`). Not a separate module. Optional lookup table deferred. |
| Page-to-sheet relationship | `SheetPageMap`: `sheet_id`, `plan_document_id`, `page_index` (0-based, M007), `order_index` for multi-page sheets. Cardinality 0..N ↔ 0..N |
| Suggestions | First-class records: proposed fields, optional confidence, `source_attempt_id`, state `open` / `accepted` / `rejected` |
| Review workflow | Human Accept / Edit+Save / Reject / manual create; statuses `draft`, `suggested`, `reviewed`, `void` |
| Uniqueness | Sheet number unique **within a Drawing Revision** (ADR-018); warn on draft; block equivalent of “sheet-index complete” / finalize while unresolved duplicates or empty numbers remain |
| Supersession | Same number allowed across superseded vs active revisions; derive-from-prior creates **new** ids |
| Archive | Archive-over-delete for documents with sheets; prefer void for sheets |
| UI | Project / document / page scoped review UI (office Flask templates under Plan Intelligence) |
| Services/routes | Plan Intelligence package only, alongside existing `/projects/<id>/plans…` |
| Heuristics | Suggestion generation **without** auto-creating reviewed Sheets |

“Sheet type” in product language maps to **discipline_code** / page-class codes above — **not** a new column.

---

## Authorized future code areas (implementation prompt only)

- `app/plan_intelligence/` (models, services, routes, templates)
- `migrations/versions/` — **M009 additive revision(s) only**, after inspecting current Alembic head
- `tests/` — new sheet tests plus existing plan upload/indexing must remain green
- `docs/` as required by definition of done for M009 completion

## Protected areas (do not change in M009)

- Estimating builder and models (`app/models/estimate.py`, `app/services/estimate_builder.py`, estimate routes)
- Proposals, proposal PDF, Accepted immutability
- Change Orders / Project Controls
- CRM/cost library/assemblies behaviour (except incidental Project navigation links)
- PlanDocument stored bytes; PlanPage as source pagination SoR
- Pricing-policy calculation code
- Auth/User implementation
- BUILD / field / MONITOR / LEARN
- Unrelated shell redesign, branding rename, Constitution

---

## Migration authorization boundaries

**This Feature Gate authorizes a future M009 implementation prompt** to create the **minimum required** Alembic migration(s) for additive Sheet / map / suggestion schema (and optional nullable `sheet_id` on plan audit events if needed).

The implementation prompt **must**:

1. Inspect current Alembic head first (documented intent: `a7c8e9f0b1d2` — **do not assume** runtime DB without verification).
2. Create only M009-required schema.
3. Preserve existing data; no destructive changes to `plan_pages` / `plan_documents`.
4. Avoid unrelated model changes.
5. Test upgrade behaviour.
6. Report exact migration head before and after.

**This governance prompt must not create or edit migrations.**

---

## Acceptance criteria (for later implementation)

1. Reviewer can produce a **reviewed sheet index** for an Active Revision (M008 DoD).
2. Eligible pages can receive suggestions; human Accept / Edit / Reject works; confidence cannot auto-accept.
3. Page ≠ Sheet in data and tests; mappings use 0-based `page_index`.
4. Uniqueness warnings / finalize-block per ADR-018.
5. Superseded revisions keep historical sheets; same number allowed on a new active revision.
6. Source PlanDocument/Page not mutated by sheet review.
7. Existing plan upload/indexing, estimates, proposals, and change orders remain intact.
8. Project isolation: no cross-project sheet leakage.
9. Invalid review transitions fail closed.
10. Docs/handoff updated; focused + full tests run and reported.

---

## Required implementation tests

Use existing pytest patterns (`tests/test_plan_upload.py`, `tests/test_plan_indexing.py`).

Later M009 implementation must test:

- Existing Plan upload/indexing remains intact
- Sheet creation/review from eligible Page
- Human accept
- Human edit
- Human reject
- Uniqueness rules (per Revision)
- Supersession/history behaviour
- Project/document/page isolation
- Invalid transitions fail closed
- Source Page/PlanDocument is not mutated
- Existing Estimate / Proposal / Change Order behaviour remains unaffected
- Confidence / heuristics cannot auto-accept SoR
- Reprocess does not clobber accepted Sheet SoR (ADR-017)

Do not invent pass/fail results in this governance document.

---

## Explicitly out of M009

- Automatic estimating insertion
- Quantity take-off
- Scale calculation / manual measure tools
- CAD/DWG processing
- AI pricing
- Supplier catalogue
- BUILD
- Field/mobile workflows
- Photos / voice
- MONITOR / LEARN
- Authentication implementation
- Pricing-policy calculation changes
- Contract / warranty generation
- QuickBooks
- Product/repository rename
- Unrelated UI redesign
- Broad architecture cleanup
- Auto-merge duplicate PDFs by checksum (ADR-018 rejected for M009)
- Full revision-comparison product
- Treating Page as Sheet
- Separate Discipline or Sheet top-level module
- Parallel CalibAi Job entity

---

## Dependencies

- M005–M007 on `main` (upload, pages, packages/revisions, processing, audit)
- M008 Sheet Intelligence architecture
- ADR-017/018 **Accepted**
- Subsequent **implementation Cursor prompt** (not this document)

Auth is **not** a prerequisite for office M009 (CAR-001). Actor identity must not be fabricated.

---

## Stopping conditions (implementation prompt)

Stop and report if: requirements conflict with ADR-017/018 or Page ≠ Sheet; a field not in M008 catalog appears necessary; migration beyond additive sheet schema appears required; Estimating/Proposals would change; auth/User schema appears required; runtime Alembic head is unexpected; two continuity corrections occur.

---

## Open decisions (do not block this Gate)

| Item | Notes |
|------|--------|
| ADR-014 document status | Still **Proposed**; Page ≠ Sheet is **required** by this Gate and M008. Accepting ADR-014 is a separate docs action if Joel wants formal ADR status alignment. |
| SQLite uniqueness | Partial unique index vs application enforcement (ADR-018 allows either). |
| Optional `discipline_codes` table | Deferred; string codes on Sheet are sufficient for M009. |
| Optional `sheet_id` on `plan_audit_events` | M008 permits reuse of event types and/or additive nullable FK. |
| “Sheet-index complete” UX label | ADR-018 requires a finalize-equivalent that blocks on duplicates; exact UI copy is implementation detail inside that rule. |

None of these leave Feature Gate questions 1–12 unanswered.

---

## Gate decision

| Result | Detail |
|--------|--------|
| **FEATURE GATE APPROVED** | M009 scope, invariants, migration permission, tests, and exclusions are authorized for a **later implementation prompt** |
| Implementation started? | **No** |
| Out of scope | Scale, take-off, estimate insert, BUILD/field, auth, pricing code, contracts, QuickBooks, rename |

## Approval

| Role | Decision | Date |
|------|----------|------|
| Joel | Feature Gate approved via M009 Feature Gate prompt | 2026-08-28 |
| Implementation authorized by this prompt? | **No** — await dedicated M009 implementation Cursor prompt | 2026-08-28 |

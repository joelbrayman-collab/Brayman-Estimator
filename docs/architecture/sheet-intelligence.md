# Architecture — Sheet Intelligence

| Attribute | Value |
|-----------|--------|
| Status | **Architecture approved (M008)** · **FG-004 approved** · **not implemented** |
| Updated | 2026-08-28 |
| Module | [../modules/plan-intelligence.md](../modules/plan-intelligence.md) |
| Depends on | M007 Page indexing + Drawing Package/Revision (minimal) |
| Related | [document-intelligence.md](document-intelligence.md) · [FG-004](../feature-gates/FG-004-m009-sheet-classification.md) · ADR-012 · ADR-014 · ADR-015 · ADR-017 · ADR-018 |
| Readiness | [M008-sheet-intelligence-readiness-report.md](M008-sheet-intelligence-readiness-report.md) |

**Honesty rule:** M007 implements Pages, Packages/Revisions (minimal), processing, audit, and relational search. **Sheets are not implemented.** FG-004 authorizes a later M009 implementation prompt; this document remains the field catalog. Do not invent fields beyond this file and Accepted ADR-017/018.

---

## 1. Purpose and position

Sheet Intelligence turns indexed **PDF Pages** into **construction drawing Sheets** that estimators can review, correct, and trust before scale/measurement/take-off.

```text
M007 Document Indexing          Sheet Intelligence              Later
─────────────────────          ──────────────────              ─────
PlanDocument                   Sheet entity                    Scale (M010)
PlanPage (0-based)        →    Discipline / numbers/titles →   Manual measure
Drawing Package/Revision       Page↔Sheet mapping              AI take-off POC
Processing suggestions         Human accept/reject review
```

Owned by **Plan Intelligence** (Document Intelligence / Sheet Intelligence capability layers — ADR-013). Estimating does not own Sheets.

---

## 2. What M007 already provides

| Asset | Role for Sheets |
|-------|-----------------|
| `PlanPage` | Mappable PDF units (0-based `page_index`) |
| `DrawingPackage` / `DrawingRevision` | Revision scope for sheet identity (ADR-012/014) |
| Embedded text + processing results | Source for **suggested** sheet number/title/discipline |
| Audit events | Pattern for sheet review audit |
| Archive-over-delete | Documents with sheets must remain archive-preferring |

---

## 3. Concept catalog

| Concept | Horizon | Definition |
|---------|---------|------------|
| **Sheet** | M009 implementation | Logical construction drawing within a **Revision** |
| **Discipline** | M009 | Controlled **code attribute** on Sheet (not a separate commercial module) |
| **Sheet number** | M009 | Human identifier (e.g. `A-101`) within a Revision |
| **Sheet title** | M009 | Human title (e.g. “Level 1 Floor Plan”) |
| **Page↔Sheet mapping** | M009 | 0..N Pages ↔ 0..N Sheets (not always 1:1) |
| **Sheet suggestion** | M009 | Proposed metadata from heuristics/extractor with optional confidence |
| **Review decision** | M009 | Accept / reject / edit → human SoR fields |
| **Drawing status** | M009 | e.g. unreviewed, reviewed, void, superseded-in-set |
| **Scale / measure** | **Deferred M010** | Not Sheet Intelligence MVP |
| **Take-off candidates** | **Deferred M011+** | Not Sheet Intelligence |

### Discipline (not a standalone entity module)

Initial codes (same as Document Intelligence architecture):  
`ARCH`, `STR`, `MECH`, `ELEC`, `PLUMB`, `CIVIL`, `FIRE`, `OTHER`, plus page-class codes usable on non-drawings: `COVER`, `INDEX`, `SPEC`, `NON_DRAWING`.

Store as string code on Sheet (optional lookup/seed table later). Discipline never prices work or writes estimates.

---

## 4. Relationship model

```text
Project
  └── Drawing Package
        └── Revision (Active | Superseded)
              ├── PlanDocument(s)
              │     └── PlanPage(s)          ← M007
              └── Sheet(s)                  ← Sheet Intelligence
                    └── SheetPageMap
                          └── (plan_document_id, page_index)  [0-based]
                                order_index for multi-page sheets
```

### Cardinality rules

| Case | Mapping |
|------|---------|
| Normal drawing page | 1 Sheet ↔ 1 Page |
| Cover / index / blank | Page may have **no** Sheet, or Sheet typed `COVER` / `INDEX` / `NON_DRAWING` |
| Specification pages | Prefer `SPEC` classification; Sheet optional |
| Multi-page sheet (rare) | 1 Sheet ↔ many Pages (`order_index`) |
| Multi-sheet scan on one page | Discouraged; if forced, multiple Sheets may share a Page with explicit warning (product should prefer split PDFs) |
| Combined package (multi-file) | Sheets across documents under one Revision |

---

## 5. Edge cases (explicit)

| Situation | Architecture handling |
|-----------|------------------------|
| **Cover pages** | Page indexed; default no drawing Sheet, or `COVER` sheet without take-off eligibility |
| **Specification pages** | `SPEC` class; searchable; not measurement-eligible by default |
| **Multi-sheet scans** | Heuristic may suggest multiple numbers from one page text; human must confirm mapping; warn on shared-page Sheets |
| **Multi-page sheets** | One Sheet, multiple Page maps with `order_index` |
| **Addenda** | Prefer new Drawing Package or new Revision; Sheets created under that Revision; do not overwrite prior Revision Sheets |
| **Revised drawing sets** | New Revision; prior Sheets immutable; optional “derive from prior revision” copy with new ids |
| **Duplicate sheets across uploads** | Same number in **same Active Revision** → uniqueness warning / block finalize; same number in **superseded** Revision → allowed (historical) |
| **Duplicate identical PDFs** | Distinct PlanDocuments; Sheets remain revision-scoped; do not auto-merge |

Revision-aware identity: sheet number uniqueness is **per Revision**, not global per Project (ADR-014, ADR-018).

---

## 6. Suggestions, confidence, and human review

Builds on ADR-015; workflow detail in ADR-017.

```text
Page text / filename heuristics
        ↓
SheetSuggestion (number, title, discipline, confidence?, source_attempt_id)
        ↓
Human review
   ├─ Accept  → copy into Sheet SoR fields; mark reviewed
   ├─ Edit    → human values become SoR; mark reviewed
   └─ Reject  → suggestion dismissed; Sheet may remain unmapped or manual
```

Rules:

1. Suggestions never silently overwrite human SoR fields.  
2. Confidence annotates suggestions only — never estimate mutation, never auto-accept.  
3. Re-running heuristics creates new suggestions; does not clobber accepted Sheets unless user explicitly “re-apply suggestions.”  
4. Audit: suggestion_created, suggestion_accepted, suggestion_rejected, sheet_edited, mapping_changed.

### Review workflow states (Sheet)

| Status | Meaning |
|--------|---------|
| `draft` | Created, not human-confirmed |
| `suggested` | Has open suggestions |
| `reviewed` | Human accepted/edited SoR |
| `void` | Excluded from take-off eligibility |

---

## 7. Target schema (conceptual — not a migration)

Additive only (illustrative names):

| Table | Purpose |
|-------|---------|
| `plan_sheets` | Sheet under `drawing_revision_id`; number, title, discipline_code, drawing_status, review_status |
| `plan_sheet_pages` | M2M: sheet_id, plan_document_id, page_index, order_index |
| `plan_sheet_suggestions` | Proposed fields + confidence + source_attempt_id + state (open/accepted/rejected) |
| Optional `discipline_codes` | Seed lookup for UI |

Reuse `plan_audit_events` with sheet-related `event_type` values (or nullable `sheet_id` column in a later additive migration).

**No** destructive changes to `plan_pages` or `plan_documents`.

---

## 8. Migration strategy (for future implementation gate)

1. Additive tables only under Feature-Gated M009.  
2. Backfill optional: create zero Sheets automatically, or one draft Sheet per Page as **suggestions only** — prefer **suggestion generation without auto-creating reviewed Sheets**.  
3. Existing M007 Pages remain SoR for pagination; Sheets reference them.  
4. Downgrade drops new sheet tables only.

---

## 9. Non-goals (Sheet Intelligence)

- Scale calibration / measurement tools  
- OCR / CAD / AI quantity extraction  
- Estimate insertion  
- Full revision comparison product  
- Treating Page as Sheet  
- Separate top-level Discipline module outside Plan Intelligence  

---

## 10. Recommended coded follow-on

See [M008 readiness report](M008-sheet-intelligence-readiness-report.md): **M009** implements Sheet entities + mapping + human review. Scale moves to **M010**; AI quantity POC to **M011**.

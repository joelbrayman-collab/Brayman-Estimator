# Architecture — Document Intelligence

| Attribute | Value |
|-----------|--------|
| Status | **Proposed / Intended** (Milestone 006 — documentation only) |
| Updated | 2026-07-25 |
| Module | [../modules/plan-intelligence.md](../modules/plan-intelligence.md) |
| Feature Gate | [../feature-gates/FG-003-document-intelligence-readiness.md](../feature-gates/FG-003-document-intelligence-readiness.md) (**CONDITIONAL PASS**) |
| Related | [plan-intelligence-and-automated-takeoff.md](plan-intelligence-and-automated-takeoff.md) · ADR-012 … ADR-016 |
| Depends on | Milestone 005 Phase A (`plan_documents` + private PDF storage) |

**Honesty rule:** Only §2 “Current (M005)” describes implemented behaviour. All other sections are **proposed architecture** unless marked otherwise.

---

## 1. Pipeline position

```text
M005 PDF Upload / Storage
        ↓
Document Intelligence   ← this document (packages, pages, sheets, metadata, search)
        ↓
Quantity Take-Off (manual / AI)   ← later milestones
        ↓
Human-approved estimate mapping   ← ADR-006; separate governance
```

Document Intelligence does **not** own estimate lines, proposals, supplier data, or procurement.

**Naming:** *Drawing Package* = ADR-012 *Drawing Set* (prefer Drawing Package in new UI/docs).

---

## 2. Current (M005) — implemented

| Concept | Status | Evidence |
|---------|--------|----------|
| Project-scoped PDF upload | **Current** | `app/plan_intelligence/` routes |
| Private filesystem storage | **Current** | `storage.py`; `PLAN_UPLOAD_ROOT` / `instance/plan_uploads/{project_id}/` |
| `PlanDocument` register | **Current** | `plan_documents`: filename, stored name, content type, byte size, sha256, page_count, has_text_layer, notes, created_at |
| List / detail / download / hard-delete | **Current** | routes + templates |
| Text-layer *detection* (boolean) | **Current** | pypdf sample of early pages |
| Drawing Package / Revision / Page / Sheet | **Not implemented** | — |
| Search index / processing attempts | **Not implemented** | — |
| Soft archive / audit event table | **Not implemented** | hard-delete today |

**M005 support finding:** The Phase A model and storage abstraction **support** an additive Document Intelligence layer **without** changing Estimating ownership or relocating file bytes. Gaps (hard-delete, no package/sheet, thin audit) are debt, not a requirement to redesign upload.

---

## 3. Concept catalog

| Concept | Horizon | Definition |
|---------|---------|------------|
| **Drawing Package** | **Current (M007 minimal)** | Project-scoped container for a logical plan set (bid set, IFC, as-built). |
| **Plan Document** | **Current (M005)** | Uploaded file register + private bytes. |
| **Revision** | **Current (M007 minimal)** | Immutable package snapshot; one **Active**, others **Superseded** (ADR-012). |
| **Page** | **Current (M007)** | One PDF page index within a Plan Document (`page_index`, dimensions optional, text harvest pointer). |
| **Sheet** | Future (Sheet Intelligence) | Logical construction drawing sheet within a Revision (ADR-014). **Not implemented.** |
| **Discipline** | Future (Sheet Intelligence) | Controlled trade/discipline code on a Sheet. **Not implemented.** |
| **Sheet identifier** | Future (Sheet Intelligence) | Human sheet number (e.g. `A-101`) within a Revision. **Not implemented.** |
| **Sheet title** | Future (Sheet Intelligence) | Human title (e.g. “Level 1 Floor Plan”). **Not implemented.** |
| **Drawing status** | Future (Sheet Intelligence) | Lifecycle label on sheet or revision membership. **Not implemented.** |
| **Metadata extraction result** | **Current (M007)** | Normalized fields from a Processing Attempt (ADR-015). |
| **Searchable metadata** | **Current (M007 filters)**; sheet fields later; FTS later | Indexed attributes + optional full-text (ADR-016). |
| **Source region / citation** | Deferred (take-off / ADR-005) | Region on a Sheet/Page used for quantity provenance. |
| **Processing status** | **Current (M007)** | Status of the latest relevant attempt for a target. |
| **Processing attempt** | **Current (M007)** | Versioned run of an extractor (ADR-015). |
| **Human correction** | Future (Sheet Intelligence) | User edit that becomes SoR over suggestions. **Not implemented.** |
| **Audit event** | **Current (M007)** | Append-only who/what/when for DI actions. |
| **Take-off candidate** | Deferred (later POC) | Proposed quantity/element — not an estimate line. |
| **Estimate insertion audit** | Deferred (separate gate) | Explicit human commit into Estimating (ADR-006). |

---

## 4. Intended relationship chain

```text
Project
  └── Drawing Package
        └── Revision  (Active | Superseded)
              ├── Plan Document (1..N)     ← M005 entity, membership added
              │     └── Page (1..N)        ← PDF page index
              └── Sheet (0..N)            ← logical drawing
                    └── maps to Page(s)   ← usually 1:1; not always
                          └── (future) Source region / Take-off candidate
                                └── (future) Estimate insertion audit → EstimateVersion
```

Estimating **references** revision/sheet/citation ids; it does **not** own plan bytes or extraction blobs.

---

## 5. Drawing Package, Revision, Plan Document

### Drawing Package

- Owns: name, description, package type, status, child Revisions.
- Scoped to one Project.
- Does not own estimate lines.

### Revision

- Owns: label, issue/received dates, active/superseded, document membership, sheet set.
- Replacing plans creates a **new** Revision; superseded file bytes are not overwritten.
- Changing Active may later warn stale estimates; never auto-rewrites quantities.

### Plan Document (M005)

- Remains file SoR.
- Joins Revisions via membership (M2M).
- Orphan documents (uploaded before packages exist) should be backfilled into a default package/revision when M007 lands.

---

## 6. Page vs Sheet — not always equivalent

**Decision (ADR-014):** A **Page** is a PDF pagination unit. A **Sheet** is a logical construction drawing. They are **not** always 1:1.

| Situation | Architecture handling |
|-----------|------------------------|
| Cover / title / index pages | Page exists; Sheet optional or typed `COVER` / `INDEX` / `NON_DRAWING` |
| Blank pages | Page exists; mark `blank` / exclude from sheet index by default |
| Multipage sheets (rare large drawings split across PDF pages) | One Sheet ↔ many Pages (`plan_sheet_pages`) |
| Scanned pages | Page + `has_text_layer=false`; OCR hook later; Sheet still creatable manually |
| Combined drawing packages (multi-file) | Multiple Plan Documents under one Revision; Sheets span documents via page maps |
| Specifications mixed with drawings | Pages classified `SPEC` / `DRAWING` / `OTHER`; Sheets primarily for drawings |
| Duplicate sheets in one PDF | Multiple Sheets may map to different pages with same number → human resolve uniqueness per Revision |
| Revised sheets in the same PDF | Prefer new Revision; if single PDF contains clouded revisions, Sheets may carry local revision labels but package Active Revision remains authoritative |
| Addenda / bulletins | Separate Drawing Package or new Revision; never silent overwrite of prior Sheets |

---

## 7. Discipline, identifiers, drawing status

**Discipline (initial vocabulary):** `ARCH`, `STR`, `MECH`, `ELEC`, `PLUMB`, `CIVIL`, `FIRE`, `OTHER`.

**Sheet identifier / title:** Human-editable; uniqueness rules per Revision (warn on duplicates).

**Drawing status (illustrative):** `unreviewed`, `reviewed`, `issued`, `void`, `superseded`. Status does not price work.

---

## 8. Metadata and processing boundaries

| Mode | Allowed in early DI | Notes |
|------|---------------------|-------|
| Deterministic PDF metadata | Yes (M007) | page count, info dict where reliable, checksum |
| Embedded-text extraction | Yes (M007) | per-page text; title-block heuristics as suggestions |
| Manual metadata entry | Future (Sheet Intelligence) | SoR after human edit — **not in M007** |
| Automated classification | Suggest-only early; AI later gated | Never silent commercial effect |
| OCR | Future hook | Derivative artifact; do not overwrite original bytes |
| CAD / CV / LLM / quantity extraction | Future hooks | Separate Feature Gates |

### Processing model (ADR-015)

- **Processing Attempt** — toolchain + version + status + timestamps.
- **Processing Result** — normalized fields + **immutable raw payload** for that attempt.
- **Reprocessing** — new attempt; prior raw retained.
- **Idempotency** — optional skip when `(target, extractor_version, content_checksum)` unchanged.
- **Failed processing** — document/pages remain; status=`failed`; user can retry.
- **Provenance** — every suggestion traces to attempt id.
- **Human correction** — wins over suggestions until explicit re-apply.
- **Confidence** — annotates suggestions only; **never** authorizes estimate mutation.

---

## 9. Search architecture (ADR-016)

### What users should eventually filter / search

project · drawing package · original filename · sheet number · sheet title · discipline · revision · issue date · drawing status · extracted text · processing status

### Staged approach (preferred)

1. **Relational fields + indexes** (simplest; **M007 current**; sheet-field filters later).
2. **DB full-text** over harvested text when needed.
3. **External search** only after demonstrated need + Feature Gate.

No embedding search without a separate AI gate. Search never writes estimates.

---

## 10. Future integration points (hooks only)

| Integration | Boundary |
|-------------|----------|
| **OCR** | Job on Page/Document; raw+text result; optional searchable derivative file; original upload immutable |
| **CAD** | New content types under ADR-009 gate; same Package/Revision/Sheet model |
| **Computer vision** | Consumes sheet images + scale; emits candidates with confidence; no estimate write |
| **LLM classification** | Suggestions into Processing Results; human confirm for SoR fields |
| **Quantity extraction** | Take-off module concern after DI sheets exist; ADR-005 citations |
| **Drawing comparison** | Requires retained Revisions; separate Feature Gate |

---

## 11. Security, audit, performance

| Concern | Rule |
|---------|------|
| Storage security | Private upload root / future object store; no public static plan URLs |
| Authorization | Every query project-scoped; platform auth still open debt |
| Audit | Append-only events for upload, process, correct, activate/supersede, archive, download |
| Performance | Lazy extraction; per-project indexes; avoid full-corpus scans |
| Retention | Archive preferred over hard-delete once dependents exist |

---

## 12. Target schema (conceptual — not a migration)

Illustrative additive tables: `drawing_packages`, `drawing_revisions`, `drawing_revision_documents`, `plan_pages`, `plan_sheets`, `plan_sheet_pages`, `plan_processing_attempts`, `plan_processing_results`, `plan_audit_events`, optional FTS mirror.

`plan_documents` remains file SoR.

---

## 13. Non-goals

Quantity take-off productization beyond gated POC · estimate insertion · supplier/procurement · CAD-first shift · separate top-level module · treating M005 flat uploads as the final ownership model

---

## 14. Recommended coded follow-on

1. **Sheet Intelligence architecture** (docs only) — Sheet entities, suggestion accept/reject, non-1:1 page maps; clearly marked proposed until Feature-Gated.
2. **Coded Sheets + human metadata review** — after architecture acceptance and a dedicated Feature Gate.
3. Later: scale / manual measure → narrow AI quantity POC → estimate mapping under separate gates.

M007 does **not** implement Sheets, discipline metadata, or human sheet-review workflows.

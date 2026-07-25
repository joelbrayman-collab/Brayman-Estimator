# Architecture — Document Intelligence

| Attribute | Value |
|-----------|--------|
| Status | **Future architecture** (Milestone 006 — documentation only) |
| Updated | 2026-07-25 |
| Module | [../modules/plan-intelligence.md](../modules/plan-intelligence.md) |
| Feature Gate | [../feature-gates/FG-003-document-intelligence-readiness.md](../feature-gates/FG-003-document-intelligence-readiness.md) |
| Related | [plan-intelligence-and-automated-takeoff.md](plan-intelligence-and-automated-takeoff.md) · ADR-012 · ADR-013 · ADR-014 |
| Depends on | Milestone 005 Phase A (`plan_documents` + private PDF storage) |

**Current vs future:** Phase A upload/storage exists. Document Intelligence (packages, sheets, search, enrichment) is **not implemented**. This document is intended architecture only.

---

## 1. Position in the pipeline

Document Intelligence sits **between** PDF upload/storage and Quantity Take-Off:

```text
Phase A (M005)                 Document Intelligence              Take-Off (later)
─────────────────              ─────────────────────              ────────────────
Upload PDF                     Drawing Package                    Scale confirm
Private storage                Revision                           Manual / AI measure
plan_documents register   →    Sheet index                   →    Citations (ADR-005)
has_text_layer                 Discipline / metadata              Human review
                               Search index                       Estimate mapping (ADR-006)
```

It does **not** own estimate lines, proposals, supplier data, or procurement.

**Naming:** *Drawing Package* in this document is the product name for ADR-012’s *Drawing Set*. Same concept; prefer **Drawing Package** in new UI/docs going forward; treat “Drawing Set” as synonym in ADR-012 until that ADR is revised on acceptance.

---

## 2. Does M005 support this layer without architectural change?

**Yes.** Phase A provides:

| Asset | Role for Document Intelligence |
|-------|--------------------------------|
| `plan_documents` | Immutable-ish file register (bytes + checksum + page_count + has_text_layer) |
| Private upload root | Secure blob store keyed by project |
| Project FK | Scope boundary |
| SHA-256 | Dedup / integrity for revision membership |

Document Intelligence adds **additive** entities and jobs that **reference** `plan_document_id`. It does not move file ownership out of Plan Intelligence and does not require renaming or splitting the Phase A table as a prerequisite.

Known Phase A gaps (technical debt, not blockers for architecture):

- Hard-delete of files (must become archive-preferring before take-off links)
- No upload/download audit event table yet
- No Drawing Package / Revision / Sheet tables yet

---

## 3. Conceptual model

```text
Project
  └── Drawing Package          (e.g. “IFC Bid Set”, “Issued for Construction”)
        └── Revision           (immutable snapshot; one Active; others Superseded)
              ├── PlanDocument membership  (1..N uploaded PDFs)
              └── Sheet                    (logical drawing sheets)
                    ├── page mapping into PlanDocument(s)
                    ├── discipline
                    ├── sheet number / name
                    └── metadata / extraction results
```

### 3.1 Drawing Package

| | |
|--|--|
| **Definition** | Project-scoped container for a logical plan set (product synonym: Drawing Set / ADR-012). |
| **Owns** | Name, description, package type (bid / IFC / as-built / other), status, child Revisions. |
| **Does not own** | Estimate lines; proposal snapshots. |
| **Rules** | Created under a Project; never cross-project. |

### 3.2 Revision

| | |
|--|--|
| **Definition** | Immutable snapshot of package contents at a point in time (ADR-012). |
| **Owns** | Revision label, issued/received dates, active/superseded flag, membership of PlanDocuments, Sheet set. |
| **Rules** | Exactly one **Active** revision per package for new take-off work; re-upload creates a **new** revision; file bytes of superseded revisions are not overwritten. |
| **Stale estimates** | When take-off→estimate mapping exists, changing Active revision may warn; never auto-rewrites estimate quantities (ADR-006/007/012). |

### 3.3 Sheet

| | |
|--|--|
| **Definition** | Logical drawing sheet within a Revision (ADR-014). |
| **Identity** | Sheet number and/or sheet name within the Revision — **not** solely PDF page index. |
| **Mapping** | One Sheet maps to one primary `(plan_document_id, page_index)` (0- or 1-based convention fixed at implementation). Multi-file packages may place sheets across documents. |
| **Owns** | Discipline, title, sheet number, scale (when known), page mapping, enrichment metadata. |
| **Future** | Viewports, regions, and take-off citations reference Sheet ids (ADR-005). |

### 3.4 Discipline

Controlled vocabulary (initial):

| Code | Label |
|------|-------|
| `ARCH` | Architectural |
| `STR` | Structural |
| `MECH` | Mechanical |
| `ELEC` | Electrical |
| `PLUMB` | Plumbing |
| `CIVIL` | Civil / Site |
| `FIRE` | Fire protection |
| `OTHER` | Other / unspecified |

Assignment may be manual or suggested from filename / title-block text; **human-editable**. Discipline never silently drives estimate pricing.

### 3.5 PlanDocument ↔ Sheet relationship

```text
PlanDocument (Phase A file)
    │
    │  membership (via Revision)
    ▼
Revision
    │
    │  1..N
    ▼
Sheet ──maps──► (plan_document_id, page_index)
```

- A single multi-page PDF commonly yields many Sheets.
- A Revision may include multiple PlanDocuments (e.g. arch + struct PDFs).
- Sheets are versioned by living under a Revision; copying forward on new revision is an explicit product action later (not silent mutation of prior sheets).

---

## 4. Metadata extraction

| Stage | Input | Output | Human role |
|-------|-------|--------|------------|
| Upload-time (exists) | PDF bytes | page_count, has_text_layer, sha256 | None |
| Text-layer harvest | Searchable PDF pages | Per-page / per-sheet text snippets, title candidates | Confirm sheet titles/numbers |
| Title-block heuristics | Cropped header/footer regions (future) | Suggested sheet number, name, discipline | Confirm / edit |
| OCR (future) | Non-searchable pages | Text layer substitute | Confirm quality; never silent estimate use |
| CAD parse (Phase G) | DWG/DXF/IFC | Sheet/model metadata | Separate Feature Gate (ADR-009) |

**Principles**

- Extraction produces **proposals** stored as metadata / job results — not commercial quantities.
- Failed extraction must leave the PlanDocument intact.
- Extraction engines are swappable (ADR-010); Estimator-owned Sheet records remain source of truth for identity.

---

## 5. Search index

### Phase DI-Search-1 (recommended first implementation)

- Filter by project, package, revision (active/superseded), discipline, sheet number, filename.
- Optional SQLite FTS (or equivalent) over harvested text-layer content keyed by `sheet_id` / `plan_document_id` + page.
- No external search cluster required for POC.

### Phase DI-Search-2 (later)

- Asynchronous reindex on new revision.
- Ranked full-text; optional embedding search **only** under a separate Feature Gate (AI policy).
- Object-storage-backed corpora if file volume outgrows instance disk.

Search never writes estimate data. Search hits must deep-link to Sheet / document viewers, not invent quantities.

---

## 6. Integration points (hooks only — not M006 implementation)

### 6.1 Future OCR

| Hook | Description |
|------|-------------|
| `ocr_required` | Derived from `not has_text_layer` or per-page quality score |
| `OcrJob` | Async job on PlanDocument or Sheet page |
| `OcrResult` | Text + confidence; optional searchable PDF derivative stored as **new** artifact (never overwrite original upload bytes) |

OCR is out of Document Intelligence **MVP**; architecture reserves job/result tables and forbids in-place mutation of originals.

### 6.2 Future CAD (Phase G / ADR-009)

| Hook | Description |
|------|-------------|
| Alternate `PlanDocument` content types | DWG/DXF/IFC under separate allowlist Feature Gate |
| Sheet derivation | Model views → Sheet records with stable ids |
| Same Revision membership model | CAD files join Drawing Package Revisions like PDFs |

PDF-first remains the default path through early take-off milestones.

### 6.3 Future AI extraction (Phase C+)

| Hook | Description |
|------|-------------|
| Stable ids | `revision_id`, `sheet_id`, page, bbox → ADR-005 citations |
| Input contract | AI receives sheet images/text + scale (after confirmation) |
| Output contract | Candidate elements/quantities with confidence (ADR-011); **no** estimate write |
| Document Intelligence boundary | Stops at providing indexed sheets + metadata; take-off owns candidates/reviews |

---

## 7. Security, audit, performance

| Concern | Architecture rule |
|---------|-------------------|
| **Security** | Keep blobs under private upload root / future object store; project-scoped authorization; no public static URLs for plans |
| **Audit** | Append-only events: upload, package create, revision activate/supersede, sheet edit, extract job, search export, archive |
| **Performance** | Lazy extraction; index per project; avoid full-corpus scans; page-limited text harvest (as Phase A already samples pages for text detection) |
| **Retention** | Prefer archive (soft-hide) over hard-delete once Sheet/take-off/estimate links exist (ADR-012) |

---

## 8. Target schema (conceptual — not a migration)

Additive tables (names illustrative):

| Table | Purpose |
|-------|---------|
| `drawing_packages` | Package header per project |
| `drawing_revisions` | Revisions; active flag; label; dates |
| `drawing_revision_documents` | M2M Revision ↔ PlanDocument |
| `plan_sheets` | Sheets under a revision |
| `plan_sheet_pages` | Optional explicit page maps if 1:1 insufficient |
| `plan_extract_jobs` / `plan_extract_results` | Metadata / OCR job tracking |
| `plan_search_documents` | FTS mirror or external index pointer |
| `plan_audit_events` | Append-only audit |

Phase A `plan_documents` remains the file SoR. No destructive reshape required.

---

## 9. Non-goals

- Quantity take-off UI or AI element recognition  
- Estimate insertion  
- Supplier / procurement  
- CAD-first platform shift  
- Replacing Phase A upload routes  
- Separate top-level application module outside Plan Intelligence  

---

## 10. Recommended implementation sequence

See [M006 readiness report](M006-document-intelligence-readiness-report.md) for Milestones **007–010**. Summary:

| Milestone | Focus |
|-----------|--------|
| **M007** | Drawing Package + Revision + document membership + archive policy |
| **M008** | Sheet indexing, discipline, sheet numbering |
| **M009** | Metadata extraction + search index (text-layer first) |
| **M010** | Scale confirmation foundation + OCR integration **hooks** (OCR engine optional/gated) |

Each coded milestone needs its own Feature Gate / approved prompt before application changes.

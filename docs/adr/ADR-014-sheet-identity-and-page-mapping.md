# ADR-014 — Sheet Identity and Page Mapping

| Field | Value |
|-------|--------|
| Title | ADR-014: Sheet Identity and Page Mapping |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [ADR-005](ADR-005-ai-takeoff-traceability.md) · [ADR-012](ADR-012-plan-document-version-ownership.md) · [document-intelligence.md](../architecture/document-intelligence.md) · FG-003 |

## Context

Uploaded PDFs are multi-page files. Take-off citations (ADR-005) and human review require stable **sheet** identity. If implementers treat “page 7 of the PDF” as the permanent identity, revision swaps, split/merged PDFs, and multi-file packages will break citations and comparisons.

## Decision

*(Proposed)*

1. A **Sheet** is a logical drawing sheet belonging to a **Revision** (Drawing Package revision).
2. Sheet **identity** is the surrogate key plus human-visible **sheet number** and/or **sheet name** within that Revision. Identity is **not** solely the PDF page index.
3. PDF location is a **mapping**: primary `(plan_document_id, page_index)` (implementation must pick and document 0- vs 1-based indexing once and keep it stable).
4. One PlanDocument may map to many Sheets; one Revision may include many PlanDocuments and therefore many Sheets.
5. When a new Revision is created, prior Revision Sheets remain unchanged (historical). Carrying sheet metadata forward is an explicit copy/derive operation, not an in-place edit of the superseded revision.
6. Metadata corrections (typo in sheet name, discipline change) are allowed on a Sheet with audit; they must not replace underlying PlanDocument bytes.
7. Future citations (ADR-005) must store `sheet_id` (and revision/document/page/region as applicable), not filename+page alone.

## Alternatives Considered

- **Page index as sole identity** — Rejected (brittle across revisions and file splits).
- **Filename + page as identity** — Rejected (renames and replacement uploads break history).
- **One Sheet per PlanDocument** — Rejected (real plan sets are multi-sheet PDFs).

## Consequences

Positive: stable citations and revision comparison; matches how estimators talk about sheets (e.g. A-101).  
Negative: requires indexing UX and possible human confirmation of sheet numbers after upload.

## Module Ownership Impact

Plan Intelligence (Document Intelligence layer) owns Sheet records and mappings.

## Data Ownership Impact

Sheets are historical records under a Revision. Page mappings are Plan Intelligence metadata.

## Migration Impact

Deferred to a Feature-Gated implementation milestone after Document Indexing (M007). Additive `plan_sheets` (name illustrative) only.

## Testing Impact

Future: unique sheet number rules per revision; mapping integrity; citations reference sheet_id.

## Documentation Impact

FG-003; document-intelligence architecture; plan-intelligence module.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Docs only in M006; no sheet tables in this milestone | |

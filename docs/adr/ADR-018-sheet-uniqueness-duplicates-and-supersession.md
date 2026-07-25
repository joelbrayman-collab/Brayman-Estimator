# ADR-018 — Sheet Uniqueness, Duplicates, and Supersession

| Field | Value |
|-------|--------|
| Title | ADR-018: Sheet Uniqueness, Duplicates, and Supersession |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [ADR-012](ADR-012-plan-document-version-ownership.md) · [ADR-014](ADR-014-sheet-identity-and-page-mapping.md) · [sheet-intelligence.md](../architecture/sheet-intelligence.md) |

## Context

Real projects produce duplicate sheet numbers across uploads, addenda, and revised sets. ADR-014 defines Sheet identity within a Revision but does not fully specify uniqueness, duplicate detection, or how addenda relate to supersession. Implementers otherwise invent conflicting rules.

## Decision

*(Proposed)*

1. **Uniqueness scope:** Human-visible sheet number uniqueness is enforced **within a single Drawing Revision** (warn on draft; block “mark revision sheet-index complete” / equivalent finalize if unresolved duplicates remain). Empty sheet numbers are allowed temporarily for drafts but cannot finalize.
2. **Superseded revisions:** Sheets under superseded Revisions are immutable historical records. The same sheet number may exist on Revision A (superseded) and Revision B (active) without conflict.
3. **New revised sets:** Uploading replacement plans creates or attaches to a **new Revision** (ADR-012). Prior Revision Sheets are not overwritten. Optional “derive sheets from prior revision” copies metadata into **new** Sheet rows.
4. **Addenda / bulletins:** Prefer a distinct Drawing Package or a new Revision labeled as addendum; Sheets created there do not mutate prior package Sheets.
5. **Duplicate uploads of the same PDF:** Remain distinct PlanDocuments; do not auto-merge Sheets. Humans may void duplicate Sheets or archive documents.
6. **Multi-page and shared-page mappings:** Multi-page Sheets are allowed via ordered page maps. Multiple Sheets sharing one Page are allowed only with explicit user confirmation and a warning (prefer split files).
7. **Void vs delete:** Prefer `void` / archive semantics for Sheets that should not be take-off eligible; hard-delete Sheets only when no take-off citations exist (future) and policy allows.

## Alternatives Considered

- **Project-global unique sheet numbers** — Rejected (breaks normal revision history).  
- **In-place overwrite of sheet rows on new upload** — Rejected (ADR-012/014).  
- **Auto-merge duplicate PDFs by checksum** — Rejected for M009 (surprising data loss); may revisit under a later Feature Gate.

## Consequences

Positive: predictable identity for citations and comparison.  
Negative: users must resolve duplicates within the Active Revision; addenda need clear package/revision labeling.

## Module Ownership Impact

Plan Intelligence owns uniqueness rules and void/archive of Sheets.

## Data Ownership Impact

Sheet rows are revision-scoped historical records.

## Migration Impact

None in M008. M009 additive constraints/indexes for `(revision_id, sheet_number)` where number non-null (product may use partial unique index or application enforcement on SQLite).

## Testing Impact

Future: duplicate warning/block; superseded revisions allow same number; derive-from-prior creates new ids.

## Documentation Impact

Sheet Intelligence architecture; M008 readiness; roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Docs only in M008 | |

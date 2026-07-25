# ADR-016 — Document Intelligence Search Strategy

| Field | Value |
|-------|--------|
| Title | ADR-016: Document Intelligence Search Strategy |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [ADR-013](ADR-013-document-intelligence-layer-boundary.md) · [document-intelligence.md](../architecture/document-intelligence.md) · FG-003 |

## Context

Users will need to find sheets and documents by project, package, filename, sheet identifiers, discipline, revision, dates, status, extracted text, and processing status. Premature adoption of an external search cluster would add infrastructure without demonstrated scale need.

## Decision

*(Proposed)*

1. **Stage 1 (default for M007; sheet-field filters when Sheets exist):** Ordinary **relational columns + database indexes** for filters: project, drawing package, revision, filename, processing status (and later sheet number, sheet title, discipline, drawing status, issue/received dates).
2. **Stage 2 (when text search is required):** **Database full-text search** (e.g. SQLite FTS5 or the production DB’s FTS) over harvested embedded text / approved OCR text, keyed by `page_id` / `sheet_id`.
3. **Stage 3 (only with demonstrated need + Feature Gate):** External search service — if relational/FTS latency or corpus size fails agreed SLOs.
4. Search is **project-scoped**. No global multi-tenant corpus in early stages.
5. Search **never** writes estimate data and never treats ranking/confidence as commercial approval.
6. Embedding / semantic search is **out of scope** until a separate AI Feature Gate.

## Alternatives Considered

- **External search from day one** — Rejected (no demonstrated need; ops cost).  
- **Filename-only browse forever** — Rejected (insufficient for sheet-centric work).  
- **Embeddings as primary index** — Rejected (premature; policy/ADR-011 implications).

## Consequences

Positive: simplest path; reversible escalation.  
Negative: FTS quality may be weaker than specialized engines until Stage 3 is justified.

## Module Ownership Impact

Plan Intelligence owns searchable metadata and any FTS mirror tables.

## Data Ownership Impact

Indexed text is derived from Plan Intelligence–owned documents/results; not a separate product database.

## Migration Impact

Stage 1: indexed columns on Page/Sheet/Package tables. Stage 2: additive FTS structures. Stage 3: later gate.

## Testing Impact

Future: filter correctness; project isolation; no estimate side effects.

## Documentation Impact

FG-003; document-intelligence architecture; roadmap sequencing.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Docs only in M006 | |

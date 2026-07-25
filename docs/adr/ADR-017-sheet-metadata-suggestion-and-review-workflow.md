# ADR-017 — Sheet Metadata Suggestion and Review Workflow

| Field | Value |
|-------|--------|
| Title | ADR-017: Sheet Metadata Suggestion and Review Workflow |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [ADR-014](ADR-014-sheet-identity-and-page-mapping.md) · [ADR-015](ADR-015-extracted-metadata-ownership-and-provenance.md) · [ADR-011](ADR-011-ai-confidence-threshold-policy.md) · [sheet-intelligence.md](../architecture/sheet-intelligence.md) |

## Context

M007 can harvest embedded text and deterministic PDF metadata. Turning that into sheet numbers, titles, and disciplines will be imperfect. Without an explicit review workflow, implementers may auto-write “Sheet” records from heuristics or treat confidence as approval.

ADR-015 states human SoR and confidence limits generally; Sheet Intelligence needs a durable product rule for **suggest → accept / reject / edit**.

## Decision

*(Proposed)*

1. Sheet metadata suggestions are first-class records (or equivalent) with proposed fields, optional confidence, source processing attempt, and state: `open`, `accepted`, `rejected`.
2. Creating or updating a **reviewed** Sheet’s SoR fields (number, title, discipline, drawing status) requires an explicit human action: Accept, Edit+Save, or manual create — never silent auto-apply from confidence thresholds.
3. Reject dismisses a suggestion without deleting Page or PlanDocument data.
4. Re-generation of suggestions does not overwrite SoR fields or flip `accepted` suggestions; new `open` suggestions may be added.
5. Confidence values never authorize estimate create/update/delete and never auto-accept sheet metadata.
6. Audit events record suggestion lifecycle and sheet SoR edits.

## Alternatives Considered

- **Auto-create reviewed Sheets from text heuristics** — Rejected (false sheet numbers become take-off anchors).  
- **Inline overwrite of Sheet fields on every reprocess** — Rejected (ADR-015).  
- **Confidence threshold auto-accept** — Rejected (ADR-011 spirit; commercial-adjacent identity).

## Consequences

Positive: trusted sheet index; safe improvement of extractors.  
Negative: human review time; suggestion storage growth.

## Module Ownership Impact

Plan Intelligence owns suggestions and Sheet SoR. Estimating unchanged.

## Data Ownership Impact

Suggestions are Plan Intelligence historical/proposal records; Sheet SoR is Plan Intelligence product truth for identity.

## Migration Impact

Deferred to Feature-Gated Sheet implementation (recommended **M009**). Additive suggestion/sheet tables.

## Testing Impact

Future: accept/reject/edit paths; reprocess does not clobber SoR; confidence cannot auto-accept.

## Documentation Impact

Sheet Intelligence architecture; M008 readiness; roadmap sequencing.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Docs only in M008 | |

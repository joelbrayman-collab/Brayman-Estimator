# ADR-013 — Document Intelligence Layer Boundary

| Field | Value |
|-------|--------|
| Title | ADR-013: Document Intelligence Layer Boundary |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [ADR-007](ADR-007-plan-and-estimate-version-ownership.md) · [ADR-012](ADR-012-plan-document-version-ownership.md) · [document-intelligence.md](../architecture/document-intelligence.md) · FG-003 |

## Context

Milestone 006 introduces **Document Intelligence** between Phase A PDF upload and future take-off. Without an explicit boundary, the platform risks either (a) creating a second module that duplicates Plan Intelligence ownership, or (b) letting “Document Intelligence” silently absorb take-off and estimate responsibilities.

## Decision

*(Proposed)*

1. **Document Intelligence is a capability layer inside Plan Intelligence**, not a separate top-level module and not a peer of Estimating or Proposals.
2. The layer **owns** (when implemented): Drawing Packages, Revisions, Sheets, discipline/sheet metadata, extraction jobs/results, and search-index records derived from plan documents.
3. The layer **continues** Plan Intelligence ownership of Phase A `plan_documents` and private plan file storage.
4. The layer **does not own**: estimate versions/lines, proposal snapshots, supplier catalogues, purchase orders, or take-off *quantities* / review packages (those remain later Plan Intelligence take-off concerns under ADR-005/006).
5. Cross-module access remains reference-only: Estimating may later reference `revision_id` / `sheet_id` for provenance; it must not store plan file bytes.
6. Product UI may label the experience “Document Intelligence” while code and module docs remain under Plan Intelligence (`app/plan_intelligence/`, `docs/modules/plan-intelligence.md`).

## Alternatives Considered

- **New top-level Document Intelligence module** — Rejected for now (splits ownership of the same plan files; violates exclusive ownership clarity without a hard boundary need).
- **Fold Document Intelligence into Estimating** — Rejected (Rule 1 / ADR-007; Estimating must not own plan binaries).
- **Skip naming; expand Phase B only** — Rejected as insufficient; package/sheet/search need an explicit mid-layer before take-off tools.

## Consequences

Positive: clear ownership; Phase A storage remains valid; take-off stays a later concern.  
Negative: “Document Intelligence” is a product term that must not be mistaken for a second Flask blueprint package without an ADR amending this decision.

## Module Ownership Impact

Plan Intelligence gains documented sub-capabilities. No ownership transfer. No new module document required unless this ADR is superseded.

## Data Ownership Impact

Package / Revision / Sheet / search records are Plan Intelligence–owned. Phase A files remain Plan Intelligence–owned.

## Migration Impact

None in Milestone 006. Future additive tables under Plan Intelligence only.

## Testing Impact

None in Milestone 006. Future gates define package/sheet/search tests.

## Documentation Impact

FG-003; document-intelligence architecture; plan-intelligence module; roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Docs only in M006 | |

# Current State — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Operational snapshot |
| Updated | 2026-07-25 |
| Evidence | Local repository inspection |

## Baseline

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD | `ee9b4b2` (Merge PR #6 — Milestone 008 Sheet Intelligence) |
| Working tree | Clean |
| Governance | FG-003 CONDITIONAL PASS; M005–M008 merged to `main` |

## Implemented (evidenced in code on `main`)

- CRM, Estimating, Proposals (+ Accepted immutability), Change Orders
- Plan Intelligence Phase A upload/storage (M005; `098647c`)
- **Document Indexing (M007; `cbefe7a`)** — pages, processing attempts/results, immutable raw payloads, audit events, archive-over-delete, relational search, minimal package/revision; migration `a7c8e9f0b1d2`

## Architecture / readiness only (not implemented)

- **Document Intelligence architecture (M006)** — FG-003, `document-intelligence.md`, ADR-013–016
- **Sheet Intelligence (M008; `8c74e31`)** — Sheet entities, discipline, suggestions, accept/reject review, non-1:1 Page↔Sheet mapping — **docs only; no sheet code**
- Scale / manual measure / AI take-off / estimate mapping

## Migrations

- Alembic head intended: `a7c8e9f0b1d2` (M007) — re-verify per environment
- M008 introduced **no** migrations

## Current milestone status

M005–M008 are **merged to `main`**. No coded milestone is in progress. Sheets remain **unimplemented**.

## Recommended next steps

1. Joel reviews/accepts ADR-017/018 and [M008 readiness](architecture/M008-sheet-intelligence-readiness-report.md).
2. Feature-Gate **Sheet classification and human metadata review** before any sheet tables/UI (recommended next coded milestone; not started).
3. Do not begin M009 (or equivalent) until authorized.

## Related

- [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md)
- [architecture/M008-sheet-intelligence-readiness-report.md](architecture/M008-sheet-intelligence-readiness-report.md)
- [ADR-017](adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md) · [ADR-018](adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md)
- [modules/plan-intelligence.md](modules/plan-intelligence.md)
- [architecture/document-intelligence.md](architecture/document-intelligence.md)

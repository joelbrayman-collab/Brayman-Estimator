# Current State — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Operational snapshot |
| Updated | 2026-08-25 |
| Evidence | Local repository inspection |

## Baseline

| Field | Value |
|-------|--------|
| Branch | `main` |
| Remote `origin/main` | `ee9b4b2` (Merge PR #6 — Milestone 008 Sheet Intelligence) |
| Local HEAD | `ed36838` (local docs checkpoint — post-M008 state sync; **not pushed**) |
| Working tree | Documentation-only governance reconciliation in progress; six pre-existing state-sync modifications preserved at `ed36838`; additional August 25 governance docs uncommitted |
| Governance | FG-003 CONDITIONAL PASS; M005–M008 merged to `origin/main`; August 25 product/governance requirements recorded (docs only) |

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

## August 25, 2026 governance (recorded — not implemented)

- **Authoritative estimate record** + **four-output document package** — [architecture/project-document-package.md](architecture/project-document-package.md)
- **Pricing policy** ($65/hr labour direct; 15% gross margin) — [pricing-policy.md](pricing-policy.md)
- **QuickBooks pipeline boundary** (no API) — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- **Ontario contract + warranty / Legal Content Gate** — [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- **UAT reference case** (3415 Roger Stevens Road) — [testing/uat-reference-cases.md](testing/uat-reference-cases.md)
- **Context drift / rollover rule** — [platform-governance.md](platform-governance.md#context-drift-and-handoff-mandatory-stop)

## Recommended next steps

1. Joel reviews/accepts ADR-017/018 and [M008 readiness](architecture/M008-sheet-intelligence-readiness-report.md).
2. Commit preserved post-M008 sync + August 25 governance reconciliation when directed (**not committed in this session**).
3. Feature-Gate **Sheet classification and human metadata review** before any sheet tables/UI (recommended next coded milestone; **not started**).
4. Do not begin coded Sheet work, QuickBooks API, contract generation, or warranty generation until explicitly Feature-Gated.

## Related

- [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md)
- [architecture/M008-sheet-intelligence-readiness-report.md](architecture/M008-sheet-intelligence-readiness-report.md)
- [ADR-017](adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md) · [ADR-018](adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md)
- [modules/plan-intelligence.md](modules/plan-intelligence.md)
- [architecture/document-intelligence.md](architecture/document-intelligence.md)

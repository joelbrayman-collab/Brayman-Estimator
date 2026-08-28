# Current State — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Operational snapshot |
| Updated | 2026-08-28 |
| Evidence | Local repository inspection |

## Baseline

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` | Confirm with `git rev-parse` (expect parity; tip at or after state closure `ee100ac`) |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| Working tree | Clean (confirm `git status`) |
| Governance | FG-003 CONDITIONAL PASS; M005–M008 on `main`; CAR-001 CalibAi architecture adopted 2026-08-28 (docs only); Continuity & Anti-Drift Protocol adopted 2026-08-28; product features not implemented by CAR-001 |

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
- **CalibAi vision + CAR-001 architecture** — [platform-vision.md](platform-vision.md) · [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md) (2026-08-28; implementation not authorized)
- **Context drift / rollover rule** — [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md) (adopted 2026-08-28); summary also in [platform-governance.md](platform-governance.md#context-drift-and-handoff-mandatory-stop)

## Recommended next steps

1. Feature-Gate **M009** Sheet classification and human metadata review before any sheet tables/UI (**not started**; CAR-001 does not authorize code).
2. Joel accepts ADR-021 (MONITOR baseline) and ADR-025 (pricing formula) when ready; ADR-017/018 remain Proposed until separately accepted.
3. Do not begin coded Sheet work, QuickBooks API, contract generation, BUILD capture, or field clients until explicitly Feature-Gated.

## Related

- [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md)
- [architecture/M008-sheet-intelligence-readiness-report.md](architecture/M008-sheet-intelligence-readiness-report.md)
- [ADR-017](adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md) · [ADR-018](adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md)
- [modules/plan-intelligence.md](modules/plan-intelligence.md)
- [architecture/document-intelligence.md](architecture/document-intelligence.md)

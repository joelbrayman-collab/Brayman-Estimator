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
| HEAD / `origin/main` | Confirm with `git rev-parse` |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| Working tree | Clean (confirm `git status`) |
| Governance | FG-004 **approved**; M009 **implemented & verified**; CAR-001 CalibAi architecture adopted 2026-08-28; Review Turnover Protocol adopted 2026-08-28 |

## Implemented (evidenced in code on `main`)

- CRM, Estimating, Proposals (+ Accepted immutability), Change Orders
- Plan Intelligence Phase A upload/storage (M005; `098647c`)
- **Document Indexing (M007; `cbefe7a`)** — pages, processing attempts/results, immutable raw payloads, audit events, archive-over-delete, relational search, minimal package/revision; migration `a7c8e9f0b1d2`
- **Sheet Intelligence / Classification (M009)** — `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions`, `sheet_id` on audit events; service layer for human review (accept, edit, reject, manual create, void); revision sheet index validation & finalization; office review UI; migration `b8d9f0a1c2e3`; 121 total tests passing

## Architecture / readiness only (not implemented)

- **Document Intelligence architecture (M006)** — FG-003, `document-intelligence.md`, ADR-013–016
- Scale / manual measure (M010) / AI take-off (M011+) / estimate mapping
- CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract

## Migrations

- Alembic head: `b8d9f0a1c2e3` (M009 Sheet Intelligence)
- Upgraded cleanly from `a7c8e9f0b1d2` (M007)

## Current milestone status

M005–M009 are **implemented and verified**. Next approved milestone is **M010 — Scale Calibration / Measurement Tools** (requires separate Feature Gate).

## August 25, 2026 governance (recorded — not implemented)

- **Authoritative estimate record** + **four-output document package** — [architecture/project-document-package.md](architecture/project-document-package.md)
- **Pricing policy** ($65/hr labour direct; 15% gross margin) — [pricing-policy.md](pricing-policy.md)
- **QuickBooks pipeline boundary** (no API) — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- **Ontario contract + warranty / Legal Content Gate** — [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- **UAT reference case** (3415 Roger Stevens Road) — [testing/uat-reference-cases.md](testing/uat-reference-cases.md)
- **CalibAi vision + CAR-001 architecture** — [platform-vision.md](platform-vision.md) · [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md) (2026-08-28; implementation not authorized)
- **Context drift / rollover rule** — [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md) (adopted 2026-08-28); summary also in [platform-governance.md](platform-governance.md#context-drift-and-handoff-mandatory-stop)

## Recommended next steps

1. Prepare and approve the **Feature Gate for M010 — Scale Calibration / Measurement Tools**.
2. Joel accepts ADR-021 (MONITOR baseline) and ADR-025 (pricing formula) when ready. ADR-014 remains Proposed as a document; Page ≠ Sheet is implemented and verified.
3. Do not begin QuickBooks API, contract generation, BUILD capture, or field clients until separately Feature-Gated.

## Related

- [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- [FG-004](feature-gates/FG-004-m009-sheet-classification.md)
- [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md)
- [architecture/M008-sheet-intelligence-readiness-report.md](architecture/M008-sheet-intelligence-readiness-report.md)
- [ADR-017](adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md) · [ADR-018](adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md)
- [modules/plan-intelligence.md](modules/plan-intelligence.md)
- [architecture/document-intelligence.md](architecture/document-intelligence.md)

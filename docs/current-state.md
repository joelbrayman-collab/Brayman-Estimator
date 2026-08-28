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
| Governance | FG-004 **approved & implemented**; FG-005 (M010 Scale Calibration) **approved**; CAR-001 CalibAi architecture adopted 2026-08-28; Review Turnover Protocol adopted 2026-08-28 |

## Implemented (evidenced in code on `main`)

- CRM, Estimating, Proposals (+ Accepted immutability), Change Orders
- Plan Intelligence Phase A upload/storage (M005; `098647c`)
- **Document Indexing (M007; `cbefe7a`)** — pages, processing attempts/results, immutable raw payloads, audit events, archive-over-delete, relational search, minimal package/revision; migration `a7c8e9f0b1d2`
- **Sheet Intelligence / Classification (M009)** — `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions`, `sheet_id` on audit events; service layer for human review (accept, edit, reject, manual create, void); revision sheet index validation & finalization; office review UI; migration `b8d9f0a1c2e3`
- **Scale Calibration / Measurement Tools (M010)** — `plan_scale_calibrations`, `plan_measurements`; 2-point calibration, preset ratios, viewport/region calibrations, NTS flagging; manual linear, polyline, area (Shoelace) / perimeter, and count measurements; normalized document coordinate transforms; interactive PDF.js viewer; migration `c9e0f1a2b3d4`; 140 total tests passing

## Architecture / readiness only (not implemented)

- **Document Intelligence architecture (M006)** — FG-003, `document-intelligence.md`, ADR-013–016
- **Historical Estimate Ingestion Architecture (Phase A Complete)** — Read-only audit of 20 historical workbooks, source manifest (`docs/architecture/historical-estimates-source-manifest.md`), ingestion architecture specification (`docs/architecture/historical-estimate-ingestion-architecture.md`), 5-workbook pilot extraction, pricing-method analysis. Implementation/DB deferred to Phase B.
- AI take-off / quantity extraction (M011+) / estimate mapping
- CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract

## Migrations

- Alembic head: `c9e0f1a2b3d4` (M010 Scale Calibration and Measurement)
- Upgraded cleanly from `b8d9f0a1c2e3` (M009)

## Current milestone status

M005–M010 are **implemented and verified**. Next candidate milestone is **M011 — AI Take-off / Quantity Extraction Foundation** (requires dedicated Feature Gate).

## August 25, 2026 governance (recorded — not implemented)

- **Authoritative estimate record** + **four-output document package** — [architecture/project-document-package.md](architecture/project-document-package.md)
- **Pricing policy** ($65/hr labour direct; 15% gross margin) — [pricing-policy.md](pricing-policy.md)
- **QuickBooks pipeline boundary** (no API) — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- **Ontario contract + warranty / Legal Content Gate** — [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- **UAT reference case** (3415 Roger Stevens Road) — [testing/uat-reference-cases.md](testing/uat-reference-cases.md)
- **CalibAi vision + CAR-001 architecture** — [platform-vision.md](platform-vision.md) · [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md) (2026-08-28; implementation not authorized)
- **Context drift / rollover rule** — [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md) (adopted 2026-08-28); summary also in [platform-governance.md](platform-governance.md#context-drift-and-handoff-mandatory-stop)

## Recommended next steps

1. Feature Gate and architecture for **M011 — AI Take-off / Quantity Extraction Foundation**.
2. Joel accepts ADR-021 (MONITOR baseline) and ADR-025 (pricing formula) when ready.
3. Do not begin QuickBooks API, contract generation, BUILD capture, or field clients until separately Feature-Gated.

## Related

- [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- [FG-004](feature-gates/FG-004-m009-sheet-classification.md) · [FG-005](feature-gates/FG-005-m010-scale-calibration.md)
- [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md)
- [architecture/plan-intelligence-and-automated-takeoff.md](architecture/plan-intelligence-and-automated-takeoff.md)
- [ADR-017](adr/ADR-017-sheet-metadata-suggestion-and-review-workflow.md) · [ADR-018](adr/ADR-018-sheet-uniqueness-duplicates-and-supersession.md) · [ADR-026](adr/ADR-026-scale-ownership-and-calibration-provenance.md) · [ADR-027](adr/ADR-027-pdf-rendering-and-normalized-coordinate-system.md)
- [modules/plan-intelligence.md](modules/plan-intelligence.md)
- [architecture/document-intelligence.md](architecture/document-intelligence.md)

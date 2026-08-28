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
| Governance | FG-004, FG-005, FG-006 (Historical Estimate Ingestion Phase B), FG-007 (M011 Organization Foundation) **approved & implemented**; CAR-001 CalibAi architecture adopted 2026-08-28; Review Turnover Protocol adopted 2026-08-28 |

## Implemented (evidenced in code on `main`)

- CRM, Estimating, Proposals (+ Accepted immutability), Change Orders
- Plan Intelligence Phase A upload/storage (M005; `098647c`)
- **Document Indexing (M007; `cbefe7a`)** — pages, processing attempts/results, immutable raw payloads, audit events, archive-over-delete, relational search, minimal package/revision; migration `a7c8e9f0b1d2`
- **Sheet Intelligence / Classification (M009)** — `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions`, `sheet_id` on audit events; service layer for human review (accept, edit, reject, manual create, void); revision sheet index validation & finalization; office review UI; migration `b8d9f0a1c2e3`
- **Scale Calibration / Measurement Tools (M010)** — `plan_scale_calibrations`, `plan_measurements`; 2-point calibration, preset ratios, viewport/region calibrations, NTS flagging; manual linear, polyline, area (Shoelace) / perimeter, and count measurements; normalized document coordinate transforms; interactive PDF.js viewer; migration `c9e0f1a2b3d4`
- **Organization Foundation & Project Commercial Context (M011 / FG-007)** — `Organization` model (`ORG-001` Brayman Construction Inc. seeded/backfilled), direct root entity ownership (`clients`, `projects`, `cost_items`, `assemblies`, `proposal_templates`), inherited graph ownership, tenant query isolation with fail-closed 404s, versioned `ProjectCommercialContext` with 7 mandatory decision parameters, policy-driven justification engine, atomic project creation + commercial decision gate, explicit `Legacy / Unknown` migration semantics for pre-M011 projects (preventing fabricated commercial assumptions), project context versioning UI, immutable `EstimateVersion.commercial_context_id` references; migration `d0a1b2c3d4e5`; 159 total tests passing
- **Historical Estimate Ingestion Engine Phase B (FG-006)** — Deterministic OpenXML parser (pure Python, zero macro execution), template-family classifier (Families A–E), versioned family extraction adapters, canonical normalized persistence models (`HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`), organization isolation (ORG-001 private intelligence), source-cell provenance tracking, idempotent re-ingestion, human review workflow and UI (`/historical-estimates/`), controlled UAT ingestion of 20 Brayman source workbooks (20/20 exact SHA-256 matches); migration `e1b2c3d4e5f6`; 170 total tests passing (11 dedicated historical ingestion tests)

## Architecture / readiness only (not implemented)

- **Labour Engine Phase B & Calibration Model** — Blocked pending separate governance gate.
- **Organization-Calibrated Pricing Engine** — Blocked pending separate governance gate.
- AI take-off / quantity extraction (M012+) / estimate mapping
- CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract

## Migrations

- Alembic head: `e1b2c3d4e5f6` (FG-006 Historical Estimate Ingestion Engine Phase B)
- Upgraded cleanly from `d0a1b2c3d4e5` (M011)

## Current milestone status

M005–M011 and **FG-006 Historical Estimate Ingestion Engine Phase B** are **implemented and verified**. Next candidate milestone is **Labour Engine Phase B** or **Organization-Calibrated Pricing Engine**.

## August 25, 2026 governance (recorded — not implemented)

- **Authoritative estimate record** + **four-output document package** — [architecture/project-document-package.md](architecture/project-document-package.md)
- **Pricing policy** ($65/hr labour direct; 15% gross margin) — [pricing-policy.md](pricing-policy.md)
- **QuickBooks pipeline boundary** (no API) — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- **Ontario contract + warranty / Legal Content Gate** — [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- **UAT reference case** (3415 Roger Stevens Road) — [testing/uat-reference-cases.md](testing/uat-reference-cases.md)
- **CalibAi vision + CAR-001 architecture** — [platform-vision.md](platform-vision.md) · [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md) (2026-08-28; implementation not authorized)
- **Context drift / rollover rule** — [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md) (adopted 2026-08-28); summary also in [platform-governance.md](platform-governance.md#context-drift-and-handoff-mandatory-stop)

## Recommended next steps

1. Review and commit M011 implementation package.
2. Prepare Feature Gate FG-006 for Historical Ingestion Phase B (database ingestion of audited 20 historical workbooks).
3. Prepare Labour Engine Phase B architecture and pricing cascade.

## Related

- [feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md)
- [adr/ADR-028-organization-foundation-and-project-commercial-context.md](adr/ADR-028-organization-foundation-and-project-commercial-context.md)
- [architecture/organization-and-calibration-architecture.md](architecture/organization-and-calibration-architecture.md)
- [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)

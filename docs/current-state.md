# Current State — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Operational snapshot |
| Updated | 2026-08-29 |
| Evidence | Local repository inspection |

## Baseline

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` | FG-008 implementation commit on `main`. Confirm with `git rev-parse HEAD`. Parent of this commit: `820f54afc179279d2435ad3a426b3037548bb45e`. |
| FG-006 implementation | `690d755d9901e04eb783198f4b89071fbeaf472a` |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Working tree at last verified inspect | Clean after FG-008 commit/push (this pass) |
| Governance | FG-004, FG-005, FG-006, FG-007 **approved & implemented**; **FG-008 IMPLEMENTED / VERIFIED** (live DB **not** upgraded); CAR-001 adopted; Review Turnover Protocol adopted; ADR-028 **Accepted**; ADR-029 **Accepted**; ADR-025 **Proposed** |

## Implemented (evidenced in code)

- CRM, Estimating, Proposals (+ Accepted immutability), Change Orders
- Plan Intelligence Phase A upload/storage (M005; `098647c`)
- **Document Indexing (M007; `cbefe7a`)** — pages, processing attempts/results, immutable raw payloads, audit events, archive-over-delete, relational search, minimal package/revision; migration `a7c8e9f0b1d2`
- **Sheet Intelligence / Classification (M009)** — `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions`, `sheet_id` on audit events; human review; migration `b8d9f0a1c2e3`
- **Scale Calibration / Measurement Tools (M010)** — `plan_scale_calibrations`, `plan_measurements`; PDF.js viewer; migration `c9e0f1a2b3d4`
- **Organization Foundation & Project Commercial Context (M011 / FG-007)** — `Organization` (`ORG-001`), tenant isolation, versioned `ProjectCommercialContext`, immutable `EstimateVersion.commercial_context_id`; migration `d0a1b2c3d4e5`
- **Historical Estimate Ingestion Engine Phase B (FG-006)** — OpenXML parser, Families A–E, historical evidence models including `HistoricalLabourItem` (120 ORG-001 rows), review UI `/historical-estimates/`; migration `e1b2c3d4e5f6`
- **Labour Engine Phase B (FG-008)** — org-owned `LabourTask`, human-reviewed mappings, versioned `ProductionRateStandard` and `DirectLabourCostRateStandard`, `LabourCalibrationCandidate` lifecycle, explainable resolution, immutable `EstimateLabourSnapshot`, office UI `/labour-engine/`; additive migration `f2c3d4e5f6a7`. **Implemented & verified. Live DB not upgraded** (`flask db current` remains `e1b2c3d4e5f6`).

## Architecture / readiness only (not implemented)

- **Organization-Calibrated Pricing Engine** — Blocked pending separate governance gate. ADR-025 remains **Proposed**.
- AI take-off / quantity extraction (M012+) / estimate mapping
- CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract
- Crew Template catalog, payroll burden, `LabourActualObservation` persistence

## Migrations

- Alembic **graph** head: `f2c3d4e5f6a7` (FG-008)
- Live `flask db current` at last inspect: `e1b2c3d4e5f6` (upgrade not applied in this pass)

## Current milestone status

M005–M011 and **FG-006** remain **implemented, verified, committed, and pushed** on `main`.

- **Current coded work:** FG-008 Labour Engine Phase B — **IMPLEMENTED / VERIFIED** on `main`. Live DB **not** migrated.
- **Blocked / Not Started (code):** Organization-Calibrated Pricing Engine, cross-org learning, source workbook mutation, pricing formula modifications (ADR-025 still Proposed).

## August 25, 2026 governance (recorded — not implemented)

- **Authoritative estimate record** + **four-output document package** — [architecture/project-document-package.md](architecture/project-document-package.md)
- **Pricing policy** ($65/hr labour direct; 15% gross margin) — [pricing-policy.md](pricing-policy.md) — **ORG-001 values, not CalibAi universal defaults**
- **QuickBooks pipeline boundary** (no API) — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- **Ontario contract + warranty / Legal Content Gate** — [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- **UAT reference case** (3415 Roger Stevens Road) — [testing/uat-reference-cases.md](testing/uat-reference-cases.md)
- **CalibAi vision + CAR-001 architecture** — [platform-vision.md](platform-vision.md) · [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- **Context drift / rollover rule** — [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)

## Recommended next steps

1. Separate governance authorization to apply Alembic upgrade `f2c3d4e5f6a7` to the live development/UAT database and perform post-migration smoke verification.
2. Preserve protected state (20/20 immutable source workbooks outside Git, tenant boundaries, cell provenance, immutable proposal/estimate snapshots, $65 / 15% policy text).
3. Do not repair FG-006 labour quality defects (e.g. stored `hourly_rate = 0.13`) under FG-008.
4. Do not start Pricing Engine / ADR-025 until separately gated.

## Related

- [feature-gates/FG-008-labour-engine-phase-b.md](feature-gates/FG-008-labour-engine-phase-b.md)
- [architecture/labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md)
- [adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md)
- [feature-gates/FG-006-historical-estimate-ingestion-phase-b.md](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md)
- [feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md)
- [architecture/organization-and-calibration-architecture.md](architecture/organization-and-calibration-architecture.md)

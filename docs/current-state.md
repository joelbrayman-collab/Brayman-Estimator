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
| HEAD / `origin/main` | FG-009 implementation commit on `main` (governance parent `41bfb2e`). Live DB **not** migrated. |
| FG-006 implementation | `690d755d9901e04eb783198f4b89071fbeaf472a` |
| FG-008 implementation | `0569f25e7ff496ab637d52437d48cf815522afa1` |
| Working tree at last verified inspect | FG-009 **IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED** |
| Governance | FG-004, FG-005, FG-006, FG-007 **approved & implemented**; **FG-008 CLOSED — OPERATIONAL FOR UAT**; **FG-009 IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED**. CAR-001 adopted; Review Turnover Protocol adopted; ADR-028 **Accepted**; ADR-029 **Accepted**; ADR-025 **Accepted**; ADR-030 **Accepted** |

## Implemented (evidenced in code)

- CRM, Estimating, Proposals (+ Accepted immutability), Change Orders
- Plan Intelligence Phase A upload/storage (M005; `098647c`)
- **Document Indexing (M007; `cbefe7a`)** — pages, processing attempts/results, immutable raw payloads, audit events, archive-over-delete, relational search, minimal package/revision; migration `a7c8e9f0b1d2`
- **Sheet Intelligence / Classification (M009)** — `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions`, `sheet_id` on audit events; human review; migration `b8d9f0a1c2e3`
- **Scale Calibration / Measurement Tools (M010)** — `plan_scale_calibrations`, `plan_measurements`; PDF.js viewer; migration `c9e0f1a2b3d4`
- **Organization Foundation & Project Commercial Context (M011 / FG-007)** — `Organization` (`ORG-001`), tenant isolation, versioned `ProjectCommercialContext`, immutable `EstimateVersion.commercial_context_id`; migration `d0a1b2c3d4e5`
- **Historical Estimate Ingestion Engine Phase B (FG-006)** — OpenXML parser, Families A–E, historical evidence models including `HistoricalLabourItem` (120 ORG-001 rows), review UI `/historical-estimates/`; migration `e1b2c3d4e5f6`
- **Labour Engine Phase B (FG-008)** — org-owned `LabourTask`, human-reviewed mappings (including **REVOKED**), versioned `ProductionRateStandard` and `DirectLabourCostRateStandard`, `LabourCalibrationCandidate` lifecycle, explainable resolution, immutable `EstimateLabourSnapshot`, office UI `/labour-engine/`; additive migration `f2c3d4e5f6a7`. **Implemented, verified, committed, pushed, live-migrated, UAT-smoke-verified.** Foundation **operational for UAT**.
- **Organization-Calibrated Pricing Engine (FG-009)** — **IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED**. Versioned `OrganizationPricingPolicy`, immutable `EstimatePricingSnapshot` (locked versions), named methods `TRUE_GROSS_MARGIN` / `COST_PLUS_MARKUP` / `COST_PLUS_MARKUP_STACK`, policy resolution, pricing audit, ORG-001 seed (org-scoped 15% TRUE_GM, CA-ON 13% HST; not CalibAi defaults; optional overhead/profit/contingency layers `UNSPECIFIED`, distinct from org-approved `NOT_APPLIED`), office UI `/pricing-engine/`, Change Order snapshot inheritance **and method application**. Additive migration `a3b4c5d6e7f8`. Live DB remains `f2c3d4e5f6a7`. Versions without a snapshot still use the legacy stack. New estimates are not auto-converted to true GM.

## Architecture / readiness only (not implemented)

- AI take-off / quantity extraction (M012+) / estimate mapping
- CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract
- Crew Template catalog, payroll burden, `LabourActualObservation` persistence

## Migrations

- Alembic **graph** head: `a3b4c5d6e7f8` (FG-009)
- Live development/UAT `flask db current`: `f2c3d4e5f6a7` (**not** upgraded)

## Current milestone status

M005–M011, **FG-006**, and **FG-008** remain **implemented, verified, committed, and pushed** on `main`.

- **Current coded work:** FG-009 Organization-Calibrated Pricing Engine — **IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED**.
- **Blocked / Not Started:** live DB migration for FG-009; four-output package; QuickBooks; contracts; AI take-off; BUILD/MONITOR/LEARN; historical evidence repair.

## August 25, 2026 governance (recorded — not implemented)

- **Authoritative estimate record** + **four-output document package** — [architecture/project-document-package.md](architecture/project-document-package.md)
- **Pricing policy** ($65/hr labour direct; 15% gross margin) — [pricing-policy.md](pricing-policy.md) — **ORG-001 values, not CalibAi universal defaults**
- **QuickBooks pipeline boundary** (no API) — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- **Ontario contract + warranty / Legal Content Gate** — [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- **UAT reference case** (3415 Roger Stevens Road) — [testing/uat-reference-cases.md](testing/uat-reference-cases.md)
- **CalibAi vision + CAR-001 architecture** — [platform-vision.md](platform-vision.md) · [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- **Context drift / rollover rule** — [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)

## Recommended next steps

1. Separately authorize live development/UAT migration `f2c3d4e5f6a7` → `a3b4c5d6e7f8` and Pricing Engine UAT smoke verification.
2. Preserve protected state (20/20 immutable source workbooks outside Git, tenant boundaries, cell provenance, immutable proposal/estimate snapshots, $65 / 15% ORG-001 policy text).
3. Do not repair FG-006 labour quality defects (e.g. stored `hourly_rate = 0.13`) under Pricing Engine.
4. Do not start AI take-off or another milestone until live migrate is authorized and closed.

## Related

- [feature-gates/FG-009-organization-calibrated-pricing-engine.md](feature-gates/FG-009-organization-calibrated-pricing-engine.md)
- [architecture/organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md)
- [adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md](adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md)
- [adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md](adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md)
- [feature-gates/FG-008-labour-engine-phase-b.md](feature-gates/FG-008-labour-engine-phase-b.md)
- [architecture/labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md)
- [adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md)
- [feature-gates/FG-006-historical-estimate-ingestion-phase-b.md](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md)
- [feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md)
- [architecture/organization-and-calibration-architecture.md](architecture/organization-and-calibration-architecture.md)

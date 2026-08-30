# Current State — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Operational snapshot |
| Updated | 2026-08-30 |
| Evidence | Local repository inspection |

## Baseline

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` | This FG-013 implementation commit (verify `git log -1` after push). Prior governance: `f52f06c4adbd04055485e49124da59222a8f7768`. Product: FG-012 `0b403d6aa51381d3763cf3dc9d5d96e096d5ab93`. Alembic **graph** head `c5d6e7f8a9b0`. Live DB **current** remains `b4c5d6e7f8a9` (**LIVE MIGRATION PENDING**). |
| FG-006 implementation | `690d755d9901e04eb783198f4b89071fbeaf472a` |
| FG-008 implementation | `0569f25e7ff496ab637d52437d48cf815522afa1` |
| Working tree at last verified inspect | **FG-013 IMPLEMENTED / VERIFIED / COMMITTED / PUSHED · LIVE MIGRATION PENDING.** ADR-032 **Accepted** (productized custody coded). **ADR-021 Accepted** (MONITOR not implemented). **FG-012 CLOSED / OPERATIONAL FOR UAT.** FG-011 / FG-008 / FG-009 / FG-010 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Governance | FG-004–FG-012 approved and implemented where noted; **FG-008 / FG-009 / FG-010 / FG-011 / FG-012 CLOSED / OPERATIONAL FOR UAT**. [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **IMPLEMENTED / VERIFIED** with **LIVE MIGRATION PENDING** (revision `c5d6e7f8a9b0`). [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (supplier channel; not implemented). ADR-005/006/007/009/011/031 **Accepted**. ADR-010 **Proposed**. ADR-019 **Accepted**. **ADR-021 Accepted** (MONITOR baseline / Project Gross Margin; MONITOR not implemented). Real external AI provider **not authorized**. CAR-001 adopted; ADR-028 **Accepted**; ADR-029 **Accepted**; ADR-025 **Accepted**; ADR-030 **Accepted** |

## Implemented (evidenced in code)

- CRM, Estimating, Proposals (+ Accepted immutability), Change Orders
- Plan Intelligence Phase A upload/storage (M005; `098647c`)
- **Document Indexing (M007; `cbefe7a`)** — pages, processing attempts/results, immutable raw payloads, audit events, archive-over-delete, relational search, minimal package/revision; migration `a7c8e9f0b1d2`
- **Sheet Intelligence / Classification (M009)** — `plan_sheets`, `plan_sheet_pages`, `plan_sheet_suggestions`, `sheet_id` on audit events; human review; migration `b8d9f0a1c2e3`
- **Scale Calibration / Measurement Tools (M010)** — `plan_scale_calibrations`, `plan_measurements`; PDF.js viewer; migration `c9e0f1a2b3d4`
- **Organization Foundation & Project Commercial Context (M011 / FG-007)** — `Organization` (`ORG-001`), tenant isolation, versioned `ProjectCommercialContext`, immutable `EstimateVersion.commercial_context_id`; migration `d0a1b2c3d4e5`
- **Historical Estimate Ingestion Engine Phase B (FG-006)** — OpenXML parser, Families A–E, historical evidence models including `HistoricalLabourItem` (120 ORG-001 rows), review UI `/historical-estimates/`; migration `e1b2c3d4e5f6`
- **Labour Engine Phase B (FG-008)** — org-owned `LabourTask`, human-reviewed mappings (including **REVOKED**), versioned `ProductionRateStandard` and `DirectLabourCostRateStandard`, `LabourCalibrationCandidate` lifecycle, explainable resolution, immutable `EstimateLabourSnapshot`, office UI `/labour-engine/`; additive migration `f2c3d4e5f6a7`. **Implemented, verified, committed, pushed, live-migrated, UAT-smoke-verified.** Foundation **operational for UAT**.
- **Organization-Calibrated Pricing Engine (FG-009)** — **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. **FG-009 FOUNDATION OPERATIONAL FOR UAT.** Versioned `OrganizationPricingPolicy`, immutable `EstimatePricingSnapshot` (locked versions), named methods `TRUE_GROSS_MARGIN` / `COST_PLUS_MARKUP` / `COST_PLUS_MARKUP_STACK`, policy resolution, pricing audit, ORG-001 seed (org-scoped 15% TRUE_GM, CA-ON 13% HST; not CalibAi defaults; optional overhead/profit/contingency layers `UNSPECIFIED`, distinct from org-approved `NOT_APPLIED`), office UI `/pricing-engine/`, Change Order snapshot inheritance **and method application**. Additive migration `a3b4c5d6e7f8` applied live (`f2c3d4e5f6a7` → `a3b4c5d6e7f8`). Versions without a snapshot still use the legacy stack. New estimates are not auto-converted to true GM. Labour-snapshot Direct Labour Cost is **not** included in the estimate basis by default.
- **AI Take-off / Quantity Extraction Foundation (M012 / FG-010)** — **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. **AI TAKE-OFF FOUNDATION OPERATIONAL FOR UAT.** `TakeoffExtractionRun`, `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem`; provider-neutral mock extractor only; COUNT without scale; PlanAuditEvent extensions; office UI `/projects/<id>/plans/takeoff`. Additive migration `b4c5d6e7f8a9` applied live (`a3b4c5d6e7f8` → `b4c5d6e7f8a9`). Real external AI provider **not authorized**. Phase D estimate mapping **not started**.
- **Project Hub UX (FG-011)** — **IMPLEMENTED / VERIFIED**. `/projects/<id>` is the office-estimator Project Hub: PLAN / PRICE / CONTRACT stored facts and links; BUILD = existing Change Orders; field BUILD / MONITOR / LEARN labeled Future. Read-only `app/services/project_hub.py`. No schema, migration, new module, or ADR. Dedicated tests **13 passed**.
- **Estimate-output consistency (FG-012)** — **IMPLEMENTED / VERIFIED**. Internal Detailed Cost Breakdown at `/estimates/<id>/versions/<version_id>/internal-breakdown`. Named-method Proposal totals copy frozen `EstimatePricingSnapshot` (`TRUE_GROSS_MARGIN` / `COST_PLUS_MARKUP`); no-snapshot versions retain `COST_PLUS_MARKUP_STACK`. Customer PDF omits Overhead/Profit rows. Estimate Totals show the governing method when a snapshot is authoritative. No schema, migration, new module, or ADR. Dedicated tests **19 passed**. Full suite **283 passed** at FG-012 close; **310 passed** after FG-013.
- **Historical upload onboarding (FG-013)** — **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED**. **LIVE MIGRATION PENDING.** Office **UPLOAD PREVIOUS ESTIMATES** at `/historical-estimates/` (multi-file / folder where supported). Per-file `HistoricalUploadAttempt`. App-managed storage `instance/historical_uploads/<org>/<sha256>.<ext>`. Unknown layouts quarantined. Additive revision `c5d6e7f8a9b0`. Dedicated tests **27 passed**. No durable `UploadBatch`. Legacy Desktop corpus untouched. Live `flask db current` still `b4c5d6e7f8a9`.

## Architecture / readiness only (not implemented)

- Real external AI provider / OCR / CAD / multi-trade extraction / estimate mapping (Phase D later)
- CalibAi V1 / BUILD / field / four-output **outputs 3–4** / QuickBooks API / Ontario contract
- Supplier catalogue / Winchester POC / Darcy channel economics ([ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** direction; **not implemented**)
- Crew Template catalog, payroll burden, `LabourActualObservation` persistence
- MONITOR implementation (ADR-021 **Accepted**; not coded)
- Historical-upload onboarding UX ([FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **IMPLEMENTED / VERIFIED**; **LIVE MIGRATION PENDING**; [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**)
- Industry benchmarking

## Migrations

- Alembic **graph** head: `c5d6e7f8a9b0` (FG-013)
- Live development/UAT `flask db current`: `b4c5d6e7f8a9` (**LIVE MIGRATION PENDING**)

## Current milestone status

M005–M011, **FG-006**, **FG-008**, **FG-009**, and **M012 / FG-010** remain **implemented, verified, committed, and pushed** on `main`.

- **Current coded work:** [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **IMPLEMENTED / VERIFIED**; **LIVE MIGRATION PENDING**. ADR-032 **Accepted**. ADR-021 **Accepted** (docs only). FG-012 remains **CLOSED / OPERATIONAL FOR UAT.**
- **Blocked / Not Started (product):** FG-013 **live migrate + UAT smoke**; Phase D estimate mapping; four-output package outputs 3–4; QuickBooks; contracts; BUILD field capture; MONITOR implementation; LEARN; industry benchmarking; historical evidence repair; real external AI provider; office authentication.

## August 25, 2026 governance (recorded — not implemented)

- **Authoritative estimate record** + **four-output document package** — [architecture/project-document-package.md](architecture/project-document-package.md)
- **Pricing policy** ($65/hr labour direct; 15% gross margin) — [pricing-policy.md](pricing-policy.md) — **ORG-001 values, not CalibAi universal defaults**
- **QuickBooks pipeline boundary** (no API) — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- **Ontario contract + warranty / Legal Content Gate** — [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- **UAT reference case** (3415 Roger Stevens Road) — [testing/uat-reference-cases.md](testing/uat-reference-cases.md)
- **CalibAi vision + CAR-001 architecture** — [platform-vision.md](platform-vision.md) · [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- **Context drift / rollover rule** — [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)

## Recommended next steps

1. **STOP before live migrate.** [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) is **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED**. Do **not** run `flask db upgrade` on the development/UAT DB until a separate live-migrate prompt. Do not implement MONITOR. Do not start Phase D.
2. Preserve protected state (20/20 immutable source workbooks outside Git, tenant boundaries, cell provenance, immutable proposal/estimate snapshots, $65 / 15% ORG-001 policy text; optional layers remain `UNSPECIFIED`).
3. Do not repair FG-006 labour quality defects (e.g. stored `hourly_rate = 0.13`) under Estimate-output consistency, Project Hub, AI take-off, or Pricing Engine.
4. Do not enable a real external AI provider. Do not start Phase D estimate mapping. Do not start auth, BUILD/MONITOR/LEARN implementation, QuickBooks, or contract/warranty work. Accepting ADR-021 does **not** authorize a MONITOR Feature Gate. Accepting ADR-033 does **not** authorize a supplier Feature Gate, Winchester POC, or Darcy commercial terms.
5. Dashboard org-unscoped counts remain **out of scope**.
6. Synthetic residue remains in the live development/UAT DB (FG-008 labour UAT artifacts; FG-009 `FG-009 UAT *`; FG-010 client/project/docs/runs/package; FG-012 labeled template `FG-012 UAT Template` and Draft proposal `PROP-FG012-UAT-GM`). Leave labeled; do not invent cleanup. Office proposal create/detail still lists Overhead/Profit amounts (zero when named method governs); customer preview/PDF do not.

## Related

- [adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md)
- [architecture/supplier-channel-and-launch-partner.md](architecture/supplier-channel-and-launch-partner.md)
- [adr/ADR-032-app-managed-historical-workbook-storage.md](adr/ADR-032-app-managed-historical-workbook-storage.md)
- [feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md)
- [feature-gates/FG-012-estimate-output-consistency.md](feature-gates/FG-012-estimate-output-consistency.md)
- [adr/ADR-021-monitor-commercial-baseline.md](adr/ADR-021-monitor-commercial-baseline.md)
- [modules/monitor.md](modules/monitor.md)
- [feature-gates/FG-011-project-hub-ux.md](feature-gates/FG-011-project-hub-ux.md)
- [feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md)
- [architecture/ai-takeoff-quantity-extraction-foundation.md](architecture/ai-takeoff-quantity-extraction-foundation.md)
- [adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md](adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md)
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

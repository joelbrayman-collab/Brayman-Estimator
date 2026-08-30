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
| HEAD / `origin/main` | Starting live-UAT HEAD `f5606a106aaeeb19928d5e1b020c60ba4ef6fcec`. Implementation `e6462a9ee8688b6599ab1a7b0e91232e8d53db3a`. Product: FG-015 **CLOSED / OPERATIONAL FOR UAT**. Alembic live current = head **`e7f8a9b0c1d2`**. |
| FG-006 implementation | `690d755d9901e04eb783198f4b89071fbeaf472a` |
| FG-008 implementation | `0569f25e7ff496ab637d52437d48cf815522afa1` |
| Working tree at last verified inspect | **FG-015 CLOSED / OPERATIONAL FOR UAT.** Live current = head `e7f8a9b0c1d2`. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. Permit Intelligence ADR-037/038/039 **Accepted**. FG-013 **CLOSED / OPERATIONAL FOR UAT.** ADR-034/035/036 **Accepted**. ADR-032 **Accepted**. **ADR-033 Accepted**. **ADR-008 Proposed**. **ADR-021 Accepted** (MONITOR not implemented). Organization Brand Profile is **FUTURE / NOT IMPLEMENTED**. Change Order document family is **FUTURE / NOT IMPLEMENTED**. |
| Governance | FG-004–FG-015 approved and implemented where noted; **FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / FG-013 / FG-014 / FG-015 CLOSED / OPERATIONAL FOR UAT**. [ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-010 **Proposed**. ADR-019 **Accepted**. **ADR-021 Accepted**. Real external AI provider **not authorized**. CAR-001 adopted; ADR-028 **Accepted**; ADR-029 **Accepted**; ADR-025 **Accepted**; ADR-030 **Accepted**; ADR-034/035/036 **Accepted** |

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
- **Historical upload onboarding (FG-013)** — **CLOSED / OPERATIONAL FOR UAT.** Office **UPLOAD PREVIOUS ESTIMATES** at `/historical-estimates/` (multi-file; folder where the browser supports it). Per-file `HistoricalUploadAttempt`. App-managed storage `instance/historical_uploads/<org>/<sha256>.<ext>`. Unknown layouts quarantined. Additive revision `c5d6e7f8a9b0` **verified applied** (provenance: prior interrupted live-migrate work; reconciliation pass did **not** upgrade). Dedicated tests **27 passed**. Full suite **310 passed**. No durable `UploadBatch`. Legacy Desktop corpus untouched.
- **Permit Foundation V1 (FG-015)** — **CLOSED / OPERATIONAL FOR UAT.** `ProjectLocation` 1:1; platform Canada / Ontario / City of Ottawa + aliases; deterministic resolver; versioned preliminary `PermitProfile`; Hub PLAN **PERMIT & APPROVALS** foundation panel; `/projects/<id>/location/edit`. Live current = head `e7f8a9b0c1d2`. Office UAT **PASSED** on port **5008**. Dedicated tests **19 passed**. Full suite **364 passed**. No Permit Rules Library. No Pass 2 analysis.

- **Material Catalogue V1 (FG-014)** — **CLOSED / OPERATIONAL FOR UAT.** Platform `canonical_materials` (27 lumber/sheet seed rows) **applied live**; optional Material `CostItem.canonical_material_id`; office `/material-catalogue/`. Live current = head `d6e7f8a9b0c1`. Catalogue-link flash repaired. Dedicated tests **35 passed**. Full suite **345 passed**. Office re-UAT **PASSED** on port **5007** (valid link/unlink, empty-select, Labour/Equipment fail-closed, cross-org fail-closed, catalogue list/search, identity read-only). No supplier pricing/SKU/inventory.

## Architecture / readiness only (not implemented)

- Real external AI provider / OCR / CAD / multi-trade extraction / estimate mapping (Phase D later)
- **Material Catalogue** — [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT** (`/material-catalogue/`; live current=head `d6e7f8a9b0c1`). [ADR-034](adr/ADR-034-canonical-material-identity-and-ownership.md) / [ADR-035](adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) / [ADR-036](adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted**. Living supplier evidence **not** implemented. ADR-008 remains Proposed.
- CalibAi V1 / BUILD / field / four-output **outputs 3–4** / QuickBooks API / Ontario contract
- Supplier catalogue / Winchester POC / Darcy channel economics ([ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** direction; **not implemented**). **Governed bulk supplier onboarding** is **FUTURE / NOT IMPLEMENTED** (not one-product-at-a-time; not a Supplier Feature Gate; not FG-014).
- **Permit Intelligence** ([architecture/permit-and-approvals-report.md](architecture/permit-and-approvals-report.md) · [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md)) Pass 2 is **FUTURE / NOT IMPLEMENTED**. Architecture **Accepted** (ADR-037/038/039). [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT** (location / jurisdiction / preliminary profile only). No rules library. No live lookup / external AI.
- **Organization Brand Profile** ([architecture/organization-brand-profile.md](architecture/organization-brand-profile.md)) is **FUTURE / NOT IMPLEMENTED**. Single branding source for future generated documents. Not logo storage. Not a Feature Gate. Does not reorder the roadmap.
- **Change Order document family** ([architecture/change-order-document-family.md](architecture/change-order-document-family.md)) is **FUTURE / NOT IMPLEMENTED**. Existing Change Order record remains authoritative. Not a second entity. Not email. Not field UX. Not a numbered core-package output.
- Crew Template catalog, payroll burden, `LabourActualObservation` persistence
- MONITOR implementation (ADR-021 **Accepted**; not coded)
- Industry benchmarking

## Migrations

- Alembic **graph** head: `e7f8a9b0c1d2` (FG-015)
- Live development/UAT `flask db current`: `e7f8a9b0c1d2`

## Current milestone status

M005–M011, **FG-006**, **FG-008**, **FG-009**, and **M012 / FG-010** remain **implemented, verified, committed, and pushed** on `main`.

- **Current coded work:** [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **CLOSED / OPERATIONAL FOR UAT**.
- **Approved, not started:** none at Feature Gate layer. Next: later **Ontario / Ottawa Permit Rules + Mike Pratt POC** Feature Gate (**not created**).
- **Blocked / Not Started (product):** Phase D estimate mapping; four-output package outputs 3–4; QuickBooks; contracts; BUILD field capture; MONITOR implementation; LEARN; industry benchmarking; historical evidence repair; real external AI provider; office authentication; supplier/Winchester POC; bulk supplier onboarding; Permit Rules Library / Pass 2 report; Organization Brand Profile; Change Order document family.

## August 25, 2026 governance (recorded — not implemented)

- **Authoritative estimate record** + **four-output document package** — [architecture/project-document-package.md](architecture/project-document-package.md)
- **Pricing policy** ($65/hr labour direct; 15% gross margin) — [pricing-policy.md](pricing-policy.md) — **ORG-001 values, not CalibAi universal defaults**
- **QuickBooks pipeline boundary** (no API) — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- **Ontario contract + warranty / Legal Content Gate** — [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- **UAT reference case** (3415 Roger Stevens Road) — [testing/uat-reference-cases.md](testing/uat-reference-cases.md)
- **Permit Intelligence architecture** (ADR-037/038/039 **Accepted**; [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**; Mike Pratt Coach House as future Gate 2 UAT reference) — [architecture/permit-and-approvals-report.md](architecture/permit-and-approvals-report.md) · [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md)
- **Organization Brand Profile pin** (FUTURE / NOT IMPLEMENTED) — [architecture/organization-brand-profile.md](architecture/organization-brand-profile.md)
- **Change Order document family pin** (FUTURE / NOT IMPLEMENTED; existing Change Order record remains authoritative) — [architecture/change-order-document-family.md](architecture/change-order-document-family.md)
- **CalibAi vision + CAR-001 architecture** — [platform-vision.md](platform-vision.md) · [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- **Context drift / rollover rule** — [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)

## Recommended next steps

1. Later **Ontario / Ottawa Permit Rules + Mike Pratt POC** Feature Gate (**not created**). Do not populate the Permit Rules Library. Do not implement MONITOR, Phase D, supplier integration, bulk supplier onboarding, Winchester POC, Organization Brand Profile, or the Change Order document family. Do not accept ADR-008. Do not start Pratt POC or Gate 2 until that gate exists.
2. Preserve protected state (20/20 immutable source workbooks outside Git, tenant boundaries, cell provenance, immutable proposal/estimate snapshots, $65 / 15% ORG-001 policy text; optional layers remain `UNSPECIFIED`).
3. Do not repair FG-006 labour quality defects (e.g. stored `hourly_rate = 0.13`) under Estimate-output consistency, Project Hub, AI take-off, or Pricing Engine.
4. Do not enable a real external AI provider. Do not start Phase D estimate mapping. Do not start auth, BUILD/MONITOR/LEARN implementation, QuickBooks, or contract/warranty work. Accepting ADR-021 does **not** authorize a MONITOR Feature Gate. Accepting ADR-033 does **not** authorize a supplier Feature Gate, Winchester POC, or Darcy commercial terms.
5. Dashboard org-unscoped counts remain **out of scope**.
6. Synthetic residue remains in the live development/UAT DB (FG-008 labour UAT artifacts; FG-009 `FG-009 UAT *`; FG-010 client/project/docs/runs/package; FG-012 labeled template `FG-012 UAT Template` and Draft proposal `PROP-FG012-UAT-GM`; **FG-013** labeled `FG-013-UAT-*` workbooks/estimates 21–24 and upload attempts 1–7; **FG-014** CostItems `FG014-UAT-*`, org `ORG-FG014-UAT`, assembly `FG014-UAT-ASM`; **FG-015** labeled `FG015-UAT-*` projects 4–8 plus isolation client id 4). Leave labeled; do not invent cleanup. Office proposal create/detail still lists Overhead/Profit amounts (zero when named method governs); customer preview/PDF do not.

## Related

- [feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md)
- [feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md)
- [architecture/permit-and-approvals-report.md](architecture/permit-and-approvals-report.md)
- [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md)
- [adr/ADR-037-project-location-and-jurisdiction-resolution.md](adr/ADR-037-project-location-and-jurisdiction-resolution.md)
- [adr/ADR-038-permit-intelligence-authority-and-rules-library.md](adr/ADR-038-permit-intelligence-authority-and-rules-library.md)
- [adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)
- [architecture/organization-brand-profile.md](architecture/organization-brand-profile.md)
- [architecture/change-order-document-family.md](architecture/change-order-document-family.md)
- [architecture/supplier-catalogue-inventory-pricing.md](architecture/supplier-catalogue-inventory-pricing.md)
- [adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md](adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md)
- [adr/ADR-035-material-quantity-uom-and-requirement-boundary.md](adr/ADR-035-material-quantity-uom-and-requirement-boundary.md)
- [adr/ADR-034-canonical-material-identity-and-ownership.md](adr/ADR-034-canonical-material-identity-and-ownership.md)
- [architecture/material-catalogue-architecture.md](architecture/material-catalogue-architecture.md)
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

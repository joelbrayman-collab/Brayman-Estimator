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
| HEAD / `origin/main` | FG-017 close `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5`. Docs-reconciliation content `dd30d752190e56ed687e270950df9bf9a06d7a26`. SHA-pin `07cb46c501d968542dff567943044dc1db870f01`. Live `HEAD` / `origin/main`: verify `git rev-parse HEAD` and `git rev-parse origin/main` (do not treat as a circular this-commit reference). Implementation parent `00ca492e28118d75757e9a9c82384978b5decd92`. FG-016 close `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`. Alembic live current = head **`a9b0c1d2e3f4`**. |
| FG-006 implementation | `690d755d9901e04eb783198f4b89071fbeaf472a` |
| FG-008 implementation | `0569f25e7ff496ab637d52437d48cf815522afa1` |
| **Working tree at last verified inspect** | **FG-017 CLOSED / OPERATIONAL FOR UAT.** Live current = head `a9b0c1d2e3f4`. Office UAT **PASSED** on port **5010**. Full suite **423 passed**. [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Proposed**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **DRAFT / NOT APPROVED**. FG-008–FG-016 **CLOSED / OPERATIONAL FOR UAT**. Pratt UAT project **id 9** port **5009**. |
| Governance | FG-004–FG-017 approved and implemented where noted; **FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / FG-013 / FG-014 / FG-015 / FG-016 / FG-017 CLOSED / OPERATIONAL FOR UAT**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **DRAFT / NOT APPROVED**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Proposed**. [ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-010 **Proposed**. ADR-019 **Accepted**. **ADR-021 Accepted**. **ADR-040 Accepted**. Real external AI provider **not authorized**. CAR-001 adopted; ADR-028 **Accepted**; ADR-029 **Accepted**; ADR-025 **Accepted**; ADR-030 **Accepted**; ADR-034/035/036 **Accepted** |

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
- **Permit Foundation V1 (FG-015)** — **CLOSED / OPERATIONAL FOR UAT.** `ProjectLocation` 1:1; platform Canada / Ontario / City of Ottawa + aliases; deterministic resolver; versioned preliminary `PermitProfile`; Hub PLAN **PERMIT & APPROVALS** foundation panel; `/projects/<id>/location/edit`. At FG-015 close, live current was `e7f8a9b0c1d2` (now superseded by FG-016 `f8a9b0c1d2e3`). Office UAT **PASSED** on port **5008**. Dedicated tests **19 passed**. Full suite **364 passed** at FG-015 close. Foundation only; Pass 2 is FG-016.
- **Ontario / Ottawa Permit Intelligence POC (FG-016)** — **CLOSED / OPERATIONAL FOR UAT.** Closure `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`. **Gate-at-close** live current = head `f8a9b0c1d2e3` (applied `e7f8a9b0c1d2` → `f8a9b0c1d2e3`; later superseded by FG-017 `a9b0c1d2e3f4`). 10 APPROVED Ottawa coach-house rules. Pratt live UAT project **id 9** (`FG016-UAT-PRATT`) on port **5009**; analysis **v3** current; 10 findings (PASS 1 / VERIFY 3 / MISSING_INFORMATION 4 / POTENTIAL_NON_CONFORMANCE 1 / ADDITIONAL_APPROVAL_LIKELY 1). HTML/PDF same snapshot. No runtime web. No external AI. Dedicated tests **37 passed**. Full suite **401 passed** at FG-016 close.

- **Organization Brand Profile V1 (FG-017)** — **CLOSED / OPERATIONAL FOR UAT.** Organization-owned CURRENT-on-save Brand Profile, private logo custody `instance/brand_logos/<org>/<sha><ext>`, Proposal freeze at first Issued (Accepted if no Issued snapshot), sticky snapshot, Settings form at `/settings/brand-profile`. Additive revision `a9b0c1d2e3f4` **applied live** (`f8a9b0c1d2e3` → `a9b0c1d2e3f4`). Office UAT **PASSED** on port **5010**. Dedicated tests **22 passed**. Full suite **423 passed**. Change Order / Permit / app chrome (except enabling Settings nav) unchanged.

- **Material Catalogue V1 (FG-014)** — **CLOSED / OPERATIONAL FOR UAT.** Platform `canonical_materials` (27 lumber/sheet seed rows) **applied live**; optional Material `CostItem.canonical_material_id`; office `/material-catalogue/`. At FG-014 close, live current was `d6e7f8a9b0c1` (now superseded by later heads). Catalogue-link flash repaired. Dedicated tests **35 passed**. Full suite **345 passed** at FG-014 close. Office re-UAT **PASSED** on port **5007**. No supplier pricing/SKU/inventory. Living supplier intelligence **FUTURE / NOT IMPLEMENTED**.

## Architecture / readiness only (not implemented)

- Real external AI provider / OCR / CAD / multi-trade extraction / estimate mapping (Phase D later)
- **Material Catalogue** — [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT** (`/material-catalogue/`; **gate-at-close** live current=head `d6e7f8a9b0c1`; live head today is `a9b0c1d2e3f4`). [ADR-034](adr/ADR-034-canonical-material-identity-and-ownership.md) / [ADR-035](adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) / [ADR-036](adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted**. Living supplier evidence **not** implemented. ADR-008 remains Proposed.
- CalibAi V1 / BUILD / field / four-output **outputs 3–4** / QuickBooks API / Ontario contract
- Supplier catalogue / Winchester POC / Darcy channel economics ([ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** direction; **not implemented**). **Governed bulk supplier onboarding** is **FUTURE / NOT IMPLEMENTED** (not one-product-at-a-time; not a Supplier Feature Gate; not FG-014).
- **Permit Intelligence** ([architecture/permit-and-approvals-report.md](architecture/permit-and-approvals-report.md) · [architecture/permit-rules-library.md](architecture/permit-rules-library.md) · [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md)) Pass 2 is **CLOSED / OPERATIONAL FOR UAT** ([FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md)). Architecture **Accepted** (ADR-037/038/039). [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. No live lookup / external AI. National library **not** authorized.
- **Organization Brand Profile** ([architecture/organization-brand-profile.md](architecture/organization-brand-profile.md)) is **CLOSED / OPERATIONAL FOR UAT**. [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md). Live current = head `a9b0c1d2e3f4`. Change Order / Permit consumers remain future.
- **Change Order document family** ([architecture/change-order-document-family.md](architecture/change-order-document-family.md)) is **FUTURE / NOT IMPLEMENTED**. Existing Change Order record remains authoritative. Not a second entity. Not email. Not field UX. Not a numbered core-package output.
- **Authentication / actor identity** ([ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Proposed**; [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **DRAFT / NOT APPROVED**) — office User + membership + login **not implemented**. Shared API **deferred**. BUILD remains blocked behind Item 10 implementation.
- Crew Template catalog, payroll burden, `LabourActualObservation` persistence
- MONITOR implementation (ADR-021 **Accepted**; not coded)
- Industry benchmarking

## Migrations

- Alembic **graph** head: `a9b0c1d2e3f4` (FG-017)
- Live development/UAT `flask db current`: `a9b0c1d2e3f4` (one live current; one graph head)

## Current milestone status

M005–M011, **FG-006**, **FG-008**, **FG-009**, and **M012 / FG-010** remain **implemented, verified, committed, and pushed** on `main`.

- **Current coded work:** [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**.
- **Approved, next:** **STOP product implementation.** [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) is **Proposed**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) is **DRAFT / NOT APPROVED**. Do not implement Authentication, national permit expansion, Phase D, Change Order documents, supplier integration, or external AI / runtime web until Joel issues a later implementation prompt. Shared API remains deferred.
- **Roadmap direction (not authorization):** item 10 office-auth **governance has begun**; **implementation NOT STARTED**. Items 11–12 require Item 10 **implementation**. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**
- **Blocked / Not Started (product):** Authentication implementation; shared API; Phase D estimate mapping; four-output package outputs 3–4; QuickBooks; contracts; BUILD field capture; MONITOR implementation; LEARN; industry benchmarking; historical evidence repair; real external AI provider; supplier/Winchester POC; bulk supplier onboarding; national Permit Rules expansion; Change Order document family; Permit branding.

## August 25, 2026 governance (recorded — not implemented)

- **Authoritative estimate record** + **four-output document package** — [architecture/project-document-package.md](architecture/project-document-package.md)
- **Pricing policy** ($65/hr labour direct; 15% gross margin) — [pricing-policy.md](pricing-policy.md) — **ORG-001 values, not CalibAi universal defaults**
- **QuickBooks pipeline boundary** (no API) — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- **Ontario contract + warranty / Legal Content Gate** — [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md)
- **UAT reference case** (3415 Roger Stevens Road) — [testing/uat-reference-cases.md](testing/uat-reference-cases.md)
- **Permit Intelligence architecture** (ADR-037/038/039 **Accepted**; [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**; [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**; Mike Pratt Coach House live UAT project id 9 port 5009, advisory only) — [architecture/permit-and-approvals-report.md](architecture/permit-and-approvals-report.md) · [architecture/permit-rules-library.md](architecture/permit-rules-library.md) · [architecture/permit-rules-ontario-ottawa-sources.md](architecture/permit-rules-ontario-ottawa-sources.md) · [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md)
- **Organization Brand Profile pin** (**CLOSED / OPERATIONAL FOR UAT**) — [architecture/organization-brand-profile.md](architecture/organization-brand-profile.md); [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md)
- **Change Order document family pin** (FUTURE / NOT IMPLEMENTED; existing Change Order record remains authoritative) — [architecture/change-order-document-family.md](architecture/change-order-document-family.md)
- **CalibAi vision + CAR-001 architecture** — [platform-vision.md](platform-vision.md) · [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- **Context drift / rollover rule** — [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)

## Recommended next steps

1. **STOP product implementation.** [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) is **Proposed**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) is **DRAFT / NOT APPROVED**. Do not implement Authentication until Joel accepts the ADR, approves the gate, completes implementation reconnaissance, and issues a separate implementation prompt. Do not begin national permit expansion, Phase D, Change Order document work, supplier integration, or external AI / runtime web. Do not accept ADR-008.
2. **Roadmap direction:** item 10 office-auth governance has begun; implementation **NOT STARTED**. Shared API deferred. Items 11–12 require Item 10 implementation.
3. Preserve protected state (20/20 immutable source workbooks outside Git, tenant boundaries, cell provenance, immutable proposal/estimate snapshots, $65 / 15% ORG-001 policy text; optional layers remain `UNSPECIFIED`).
4. Do not repair FG-006 labour quality defects (e.g. stored `hourly_rate = 0.13`) under Estimate-output consistency, Project Hub, AI take-off, or Pricing Engine.
5. Do not enable a real external AI provider. Do not start Phase D estimate mapping. Do not start auth, BUILD/MONITOR/LEARN implementation, QuickBooks, or contract/warranty work. Accepting ADR-021 does **not** authorize a MONITOR Feature Gate. Accepting ADR-033 does **not** authorize a supplier Feature Gate, Winchester POC, or Darcy commercial terms.
6. Dashboard org-unscoped counts remain **out of scope**.
7. Synthetic residue remains in the live development/UAT DB (FG-008 labour UAT artifacts; FG-009 `FG-009 UAT *`; FG-010 client/project/docs/runs/package; FG-012 labeled template `FG-012 UAT Template` and Draft proposal `PROP-FG012-UAT-GM`; **FG-013** labeled `FG-013-UAT-*` workbooks/estimates 21–24 and upload attempts 1–7; **FG-014** CostItems `FG014-UAT-*`, org `ORG-FG014-UAT`, assembly `FG014-UAT-ASM`; **FG-015** labeled `FG015-UAT-*` projects 4–8 plus isolation client id 4; **FG-016** Pratt project id 9 / analyses 1–3 / unsupported synthetics 10–11; **FG-017** Brand Profile versions 1–4 on ORG-001, isolation CURRENT, proposals `PROP-FG017-UAT-ISSUE` / `PROP-FG017-UAT-ACCEPT-DIRECT` / `PROP-FG017-UAT-ISO`). Leave labeled; do not invent cleanup. Office proposal create/detail still lists Overhead/Profit amounts (zero when named method governs); customer preview/PDF do not.

## Related

- [adr/ADR-041-user-membership-and-office-authentication.md](adr/ADR-041-user-membership-and-office-authentication.md)
- [feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md)
- [feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md)
- [feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md)
- [feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md)
- [architecture/permit-rules-library.md](architecture/permit-rules-library.md)
- [architecture/permit-rules-ontario-ottawa-sources.md](architecture/permit-rules-ontario-ottawa-sources.md)
- [architecture/permit-and-approvals-report.md](architecture/permit-and-approvals-report.md)
- [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md)
- [adr/ADR-037-project-location-and-jurisdiction-resolution.md](adr/ADR-037-project-location-and-jurisdiction-resolution.md)
- [adr/ADR-038-permit-intelligence-authority-and-rules-library.md](adr/ADR-038-permit-intelligence-authority-and-rules-library.md)
- [adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)
- [architecture/organization-brand-profile.md](architecture/organization-brand-profile.md)
- [adr/ADR-040-organization-brand-profile.md](adr/ADR-040-organization-brand-profile.md)
- [feature-gates/FG-017-organization-brand-profile-v1.md](feature-gates/FG-017-organization-brand-profile-v1.md)
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

# Feature Gates

| Attribute | Value |
|-----------|--------|
| Status | Active |
| Updated | 2026-08-30 |

Feature Gate documents answer the twelve governance questions in [platform-governance.md](../platform-governance.md) for a specific module or milestone **before** Cursor implementation.

## Index

| ID | Title | Status |
|----|-------|--------|
| [FG-001](FG-001-proposals-module.md) | Proposals Module — Product Architecture Review | Draft for Joel approval |
| [FG-002](FG-002-plan-intelligence-phase-a.md) | Plan Intelligence Phase A (PDF Upload & Storage) | **Approved for Phase A** (Milestone 005) |
| [FG-003](FG-003-document-intelligence-readiness.md) | Document Intelligence Readiness | **CONDITIONAL PASS** — architecture only; implementation not authorized (Milestone 006) |
| [FG-004](FG-004-m009-sheet-classification.md) | M009 Sheet Classification / Human Metadata Review | **APPROVED, IMPLEMENTED & VERIFIED** (Milestone 009; `5dc4b09`, migration `b8d9f0a1c2e3`) |
| [FG-005](FG-005-m010-scale-calibration.md) | M010 Scale Calibration / Measurement Tools | **APPROVED, IMPLEMENTED & VERIFIED** (Milestone 010; migration `c9e0f1a2b3d4`) |
| [FG-006](FG-006-historical-estimate-ingestion-phase-b.md) | Historical Estimate Ingestion Engine — Phase B | **APPROVED, IMPLEMENTED & VERIFIED** (FG-006 Phase B; migration `e1b2c3d4e5f6`) |
| [FG-007](FG-007-m011-organization-foundation-and-project-commercial-context.md) | M011 Organization Foundation & Project Commercial Context | **APPROVED, IMPLEMENTED & VERIFIED** (Milestone 011; `cb38d93`, migration `d0a1b2c3d4e5`) |
| [FG-008](FG-008-labour-engine-phase-b.md) | Labour Engine Phase B / Organization Labour Calibration Foundation | **CLOSED / OPERATIONAL FOR UAT** (2026-08-29; revision `f2c3d4e5f6a7` in chain; live head `b4c5d6e7f8a9`) |
| [FG-009](FG-009-organization-calibrated-pricing-engine.md) | Organization-Calibrated Pricing Engine | **CLOSED / OPERATIONAL FOR UAT** (2026-08-29; revision `a3b4c5d6e7f8` in chain; live head `b4c5d6e7f8a9`) |
| [FG-010](FG-010-ai-takeoff-quantity-extraction-foundation.md) | AI Take-off / Quantity Extraction Foundation (M012) | **CLOSED / OPERATIONAL FOR UAT** (2026-08-30; Alembic current/head `b4c5d6e7f8a9`) |
| [FG-011](FG-011-project-hub-ux.md) | Project Hub UX | **CLOSED / OPERATIONAL FOR UAT** (2026-08-30; evolve `/projects/<id>`; no M0xx; no schema) |
| [FG-012](FG-012-estimate-output-consistency.md) | Internal Detailed Cost Breakdown + Customer Estimate Consistency | **CLOSED / OPERATIONAL FOR UAT** (2026-08-30; Estimating owner; existing Proposal is customer-facing estimate; no M0xx; no schema) |
| [FG-013](FG-013-contractor-calibration-onboarding-historical-upload-ux.md) | Contractor Calibration Onboarding / Historical Estimate Upload UX | **CLOSED / OPERATIONAL FOR UAT** (2026-08-30; revision `c5d6e7f8a9b0`; live current=head; no durable UploadBatch) |
| [FG-014](FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) | Material Catalogue V1 — Dimensional Lumber + Sheet Goods | **CLOSED / OPERATIONAL FOR UAT** (2026-08-30; live current=head `d6e7f8a9b0c1`; identity only) |
| [FG-015](FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) | Permit Foundation V1 — Project Location, Jurisdiction & Preliminary Permit Profile | **CLOSED / OPERATIONAL FOR UAT** (2026-08-30; live current=head `e7f8a9b0c1d2`; ADR-037/038/039) |
| [FG-016](FG-016-ontario-ottawa-permit-intelligence-poc.md) | Ontario / Ottawa Permit Intelligence POC — Governed Rules + Mike Pratt Reference | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE MIGRATION PENDING** (2026-08-30; ADR-037/038/039; not CLOSED) |

[FG-015](FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-016](FG-016-ontario-ottawa-permit-intelligence-poc.md) is **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE MIGRATION PENDING** (not CLOSED). Live Pratt office UAT awaits live migration.

Implementation is not authorized by a Feature Gate until Joel approves the gate and the corresponding Cursor prompt.

**CAR-001** aligns strategic CalibAi lifecycle architecture. **FG-004** authorized M009 (implemented & verified). **FG-005** authorized M010 Scale Calibration & Measurement Tools (implemented & verified). **FG-007** authorized M011 Organization Foundation & Project Commercial Context (implemented & verified). **FG-006** authorized Historical Estimate Ingestion Engine Phase B (implemented & verified). **FG-008** Labour Engine Phase B is **CLOSED / OPERATIONAL FOR UAT** (revision `f2c3d4e5f6a7`). **FG-009** Organization-Calibrated Pricing Engine is **CLOSED / OPERATIONAL FOR UAT** (revision `a3b4c5d6e7f8`). **FG-010** AI Take-off / Quantity Extraction Foundation is **CLOSED / OPERATIONAL FOR UAT** (Alembic current/head `b4c5d6e7f8a9`; real external AI provider not authorized). **FG-011** Project Hub UX is **CLOSED / OPERATIONAL FOR UAT** (evolve `/projects/<id>`; no new module; no schema). **FG-012** Internal Detailed Cost Breakdown + Customer Estimate Consistency is **CLOSED / OPERATIONAL FOR UAT** (no schema; no new entity; Proposal remains the customer-facing estimate). [FG-013](FG-013-contractor-calibration-onboarding-historical-upload-ux.md) is **CLOSED / OPERATIONAL FOR UAT** ([ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**; revision `c5d6e7f8a9b0`; live current=head; no durable UploadBatch). [FG-014](FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) is **CLOSED / OPERATIONAL FOR UAT** (Material Catalogue identity V1; live current=head `d6e7f8a9b0c1`; catalogue link flash defect; no supplier integration). [FG-015](FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) is **CLOSED / OPERATIONAL FOR UAT** (Permit Foundation V1; live current=head `e7f8a9b0c1d2`; no rules library; no live lookup). [FG-016](FG-016-ontario-ottawa-permit-intelligence-poc.md) is **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE MIGRATION PENDING** (Ontario / Ottawa Permit Intelligence POC; graph head `f8a9b0c1d2e3`; live current remains `e7f8a9b0c1d2`).

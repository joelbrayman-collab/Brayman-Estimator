# Platform Roadmap — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Planning |
| Updated | 2026-09-09 |

Use repository evidence for **Completed**. Strategic pillars and Phases A–G are **Future** unless marked otherwise. Do not describe unimplemented integrations as existing.

---

## Platform pillars (strategic)

| Pillar | Status today | Architecture / notes |
|--------|--------------|----------------------|
| Core CRM and project records | **Current** (Clients, Projects) | [modules/crm.md](modules/crm.md), [modules/projects.md](modules/projects.md) |
| Estimating and assemblies | **Current** | [modules/estimating.md](modules/estimating.md) |
| Plan Intelligence | **Partial** — Phase A upload (M005); Document Intelligence indexing (M007); Sheet Intelligence & human review (M009); Scale & measurement (M010); take-off **M012 / FG-010 OPERATIONAL FOR UAT** (mock extractor) | [architecture/plan-intelligence-and-automated-takeoff.md](architecture/plan-intelligence-and-automated-takeoff.md) · [architecture/ai-takeoff-quantity-extraction-foundation.md](architecture/ai-takeoff-quantity-extraction-foundation.md) · [architecture/document-intelligence.md](architecture/document-intelligence.md) · [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md) · [modules/plan-intelligence.md](modules/plan-intelligence.md) · [FG-002](feature-gates/FG-002-plan-intelligence-phase-a.md) · [FG-003](feature-gates/FG-003-document-intelligence-readiness.md) · [FG-004](feature-gates/FG-004-m009-sheet-classification.md) · [FG-005](feature-gates/FG-005-m010-scale-calibration.md) · [FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) |
| Automated Quantity Take-Off | **Foundation operational for UAT** — M012 / [FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** | Same Plan Intelligence docs · [architecture/ai-takeoff-quantity-extraction-foundation.md](architecture/ai-takeoff-quantity-extraction-foundation.md) |
| Human Review and Source Traceability | **Partial** — sheet review (M009), measurement citations (M010), and AI candidate review (FG-010 foundation) **Current** (operational for UAT) | ADR-005/006/011 **Accepted**; ADR-031 **Accepted** |
| Supplier Catalogue Management | **Partial Current** — FG-029 supplier workflow **CLOSED / OPERATIONAL FOR UAT**. Supplier named-user isolation [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Live BMR API, EDI, PO, bulk onboarding remain Future. CalibraytAI identity is [material-catalogue-architecture.md](architecture/material-catalogue-architecture.md) (**Partial Current**; [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**). [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Governed **bulk** supplier onboarding is a **FUTURE / NOT IMPLEMENTED** pin. | [architecture/supplier-catalogue-inventory-pricing.md](architecture/supplier-catalogue-inventory-pricing.md) · [architecture/supplier-channel-and-launch-partner.md](architecture/supplier-channel-and-launch-partner.md) · [architecture/fg-030-supplier-identity-and-access-isolation.md](architecture/fg-030-supplier-identity-and-access-isolation.md) · [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** · [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** · [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only) |
| Supplier Inventory and Pricing Integrations | **Future** | Supplier architecture; Phase F; heterogeneous adapters (do not assume one BMR/national model) |
| Procurement and Purchase-Order Preparation | **Future** (nav placeholder only) | Supplier + Projects/Procurement boundary; contractor↔supplier relationship **A** distinct from CalibraytAI channel relationship **B** |
| Proposal and PDF Output | **Current** (snapshot + PDF; Accepted immutability; FG-012 named-method consistency; FG-017 Brand Profile / issued snapshot) | [modules/proposals.md](modules/proposals.md) · [FG-012](feature-gates/FG-012-estimate-output-consistency.md) · [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) |
| Project document package (4 outputs) | **Partial** — outputs 1–2 **CLOSED / OPERATIONAL FOR UAT** ([FG-012](feature-gates/FG-012-estimate-output-consistency.md)); outputs 3–4 Future. **Permit Foundation V1** [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. Pass 2 Permit Intelligence [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. **Organization Brand Profile** is **CLOSED / OPERATIONAL FOR UAT** ([ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md)). **Reusable presentation masters** [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. **Change Order document family** is **FUTURE / NOT IMPLEMENTED**. | [architecture/project-document-package.md](architecture/project-document-package.md) · [architecture/approved-document-presentation-reference-baseline.md](architecture/approved-document-presentation-reference-baseline.md) · [architecture/permit-and-approvals-report.md](architecture/permit-and-approvals-report.md) · [architecture/permit-rules-library.md](architecture/permit-rules-library.md) · [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md) · [architecture/organization-brand-profile.md](architecture/organization-brand-profile.md) · [architecture/change-order-document-family.md](architecture/change-order-document-family.md) · [pricing-policy.md](pricing-policy.md) |
| QuickBooks estimate export | **Future** (pipeline boundary documented; no API) | [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md) |
| Ontario construction contract + warranty | **Future** (Legal Content Gate **empty**; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**). [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) family 05 is an **APPROVED REUSABLE PRESENTATION MASTER** / commercial-draft only and does **not** satisfy this gate. Ontario remains the first expected Canadian package. Do **not** populate jurisdictions from this recording. | [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md) · [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) · [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) |
| Project Controls and Actual-Cost Feedback | **Partial** (Change Orders current; job cost future) | [modules/projects.md](modules/projects.md) |

**Differentiator (long-term):** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project` record ([CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md)). Plan → reviewed take-off → estimate remains the PLAN/PRICE spine, with citations and no silent commercial overwrite.

**Governed position after FG-019 close:**

| Layer | Position |
|-------|----------|
| **CURRENT** | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — CalibraytAI V1 readiness **55%**; **3 / 11** packages COMPLETE (V1-01, V1-02, V1-03); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Live current **`b6c7d8e9f0a1`**. Repository Alembic head **`b6c7d8e9f0a1`**. |
| **NEXT AUTHORIZED ACTION** | **STOP.** Return to ChatGPT Architect. FG-028 is **CLOSED / OPERATIONAL FOR UAT**. Do **not** implement supplier login. Do **not** begin V1-04. Do **not** implement FG-024. Do **not** start another FG-025 slice. Do **not** implement SCOPE DELIVERY / MAKE-BUY routing. Queued ChatGPT architecture: **SCOPE DELIVERY / MAKE-BUY / PROCUREMENT ROUTING**. Website Version 15 identity is published (external). HostPapa migration **QUEUED POST-BETA**. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.** |
| **ROADMAP ITEM 10** | **COMPLETE.** Office Authentication / Actor Identity / Membership: **CLOSED / OPERATIONAL FOR UAT** ([FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md)). Shared API foundation: **CLOSED / OPERATIONAL FOR UAT** ([FG-019](feature-gates/FG-019-shared-api-foundation-v1.md)). |
| **ROADMAP DIRECTION** | Item 11 is **COMPLETE**. Item 12 Field Web is **CLOSED** ([FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md); SESSION-EXPIRY RECOVERY **DEFERRED / NOT YET EXERCISED**). Item 13 [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**; Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**; Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**; MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**. [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.** |
| **SEPARATELY GOVERNED FUTURE PROGRAMS** | [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) supplier login (**RECORDED / NOT IMPLEMENTATION-AUTHORIZED**). **SCOPE DELIVERY / MAKE-BUY / PROCUREMENT ROUTING** (**QUEUED / NOT AUTHORIZED**). [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) remaining surfaces **NOT AUTHORIZED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) North American Contract Intelligence (**FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**). Native Signing production; live BMR API; LEARN; real external AI. |

[FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-008](adr/ADR-008-supplier-price-snapshotting.md) **Proposed**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) Phase D is **CLOSED / OPERATIONAL FOR UAT**. **Change Order document family** remains **FUTURE / NOT IMPLEMENTED**.

**M009 numbering:** A ChatGPT prompt briefly called the 2026-08-28 reconciliation “M009”. That label is withdrawn. The reconciliation is **CAR-001**. Historical milestone numbers are unchanged.


---

## Completed

(Evidenced on `main`)

**Product:**

- Clients and Projects foundation
- Cost Items library (optional free-text supplier field only)
- Assemblies
- Estimates with versioning, sections, and line items
- Proposal templates
- Proposal creation from estimate versions with snapshot independence
- Proposal browser preview
- Proposal PDF generation (branding/logo support)
- Change Orders (Project Controls module)
- App shell branding and navigation structure
- Plan Intelligence Phase A — project-scoped searchable PDF upload/storage (Milestone 005; `098647c`)
- Plan Intelligence Document Indexing — pages, processing provenance, archive, relational search (Milestone 007; `cbefe7a`)
- Plan Intelligence Sheet Classification — sheet entity, page mapping, suggestions, human review workflow, uniqueness validation (Milestone 009; migration `b8d9f0a1c2e3`)
- Plan Intelligence Scale Calibration & Measurement Tools — 2-point calibration, presets, viewports, NTS, linear, polyline, area/perimeter, count measurements, normalized coordinates, PDF.js (Milestone 010; migration `c9e0f1a2b3d4`)
- Organization Foundation & Project Commercial Context — `Organization` model, `ORG-001` seed/backfill, root entity ownership, tenant query scoping, versioned `ProjectCommercialContext` with 7 mandatory parameters, policy-driven justification, immutable `EstimateVersion` references (Milestone 011; migration `d0a1b2c3d4e5`)
- Historical Estimate Ingestion Engine Phase B — Deterministic OpenXML reader, template classifier (Families A–E), versioned family adapters, normalized evidence models, source-cell provenance, quality flags, human review workflow/UI, controlled UAT ingestion of 20 Brayman source workbooks into `ORG-001` (FG-006; migration `e1b2c3d4e5f6`)

**Governance:**

- Platform Governance Foundation (Milestone 001) + baseline tag `v0.1-governance-baseline`
- Milestone 002 Proposals Feature Gate FG-001 + ADR-001–004 (+ strategic ADRs / architecture docs)
- Milestone 003 Accepted Proposal Immutability (`c59ec01`)
- Milestone 004 Plan Intelligence architecture documentation
- Milestone 005 FG-002 Approved + ADR-012 Proposed + Phase A (`098647c`; PR #4 → `db1a8da`)
- Milestone 006 Document Intelligence architecture + FG-003 (`35413a1`; PR #4) + ADR-013/014; ADR-015/016 with M007
- Milestone 007 Document Indexing (`cbefe7a`; PR #5 → `eb00123`)
- Milestone 008 Sheet Intelligence architecture + ADR-017/018 (`8c74e31`; PR #6 → `ee9b4b2`) — **docs only**
- Milestone 009 Sheet Classification / Human Metadata Review (`5dc4b09`, migration `b8d9f0a1c2e3`)
- **CAR-001** CalibAi product & architecture reconciliation (2026-08-28) — **docs/governance only**; not a product milestone number
- **Review Turnover Protocol** adopted (`39ae8fe`) + reconciliation repair (`ed3e51f`)
- **FG-005** M010 Scale Calibration Feature Gate Approved + ADR-026/027 Accepted + M010 Implemented & Verified (migration `c9e0f1a2b3d4`)
- **FG-007** M011 Organization Foundation & Project Commercial Context Approved + ADR-028 Accepted + M011 Implemented & Verified (migration `d0a1b2c3d4e5`)
- **FG-006** Historical Estimate Ingestion Engine Phase B Approved + Implemented & Verified (migration `e1b2c3d4e5f6`)

---

## Current (near-term product governance)

This subsection is **current authority**, not a historical FG-018 snapshot. Gate-at-close Alembic/test facts for closed gates remain in those gate documents.

- **`main` / `origin/main`** — verify `git rev-parse HEAD` and `git rev-parse origin/main`. Live Alembic **current = heads `f4a5b6c7d8e9`**. Last product-changing suite: dedicated FG-026 **20**, full **632**. Live Field Capture **39** Events / **39** Originals.
- **FG-008 through FG-023** **CLOSED** as applicable (FG-021 subject to SESSION-EXPIRY RECOVERY **DEFERRED / NOT YET EXERCISED**). [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**. [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. Roadmap items 10–13 **COMPLETE / CLOSED**. Item 13 [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**; Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**; Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**; MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **FUTURE / RECORDED / IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / SLICE 4 IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**.
- **ADR-021** **Accepted**. Recon: [monitor-v1-implementation-reconnaissance.md](architecture/monitor-v1-implementation-reconnaissance.md) **COMPLETE**. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**.
- **Review Turnover Protocol** adopted (2026-08-28) — `Review Turnover` governing.
- **M010 Scale Calibration & Measurement Tools** implemented and verified (2026-08-28).
- **M011 Organization Foundation & Project Commercial Context** implemented and verified (2026-08-28).
- **FG-006 Historical Estimate Ingestion Engine Phase B** implemented and verified (2026-08-28).
- CalibraytAI V1 direction (not authorized as a single implementation): PLAN → PRICE → CONTRACT baseline → BUILD field capture → basic MONITOR — [CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- Document package outputs 3–4, QuickBooks API, contract/warranty generation — **not started** (governance recorded only). Outputs 1–2: [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**.
- Permit Intelligence — architecture **Accepted** (ADR-037/038/039); Pass 1 [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**; Pass 2 [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT** ([permit-and-approvals-report.md](architecture/permit-and-approvals-report.md)). National permit expansion **not authorized**. Permit branding from Brand Profile **not authorized**.
- Organization Brand Profile — **CLOSED / OPERATIONAL FOR UAT** ([organization-brand-profile.md](architecture/organization-brand-profile.md)); [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md). Proposal is the V1 consumer. Change Order / Permit / chrome consumers remain future.
- Change Order document family — **FUTURE / NOT IMPLEMENTED** pin ([change-order-document-family.md](architecture/change-order-document-family.md)); not a Feature Gate; existing Change Order record remains authoritative.
- Estimate mapping (Phase D) — [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**

---

## CalibAi proposed sequencing (roadmap direction — not implementation authority)

Each item still needs its own Feature Gate / approved Cursor prompt.

0. CAR-001 architecture alignment + Review Turnover Protocol — **Adopted**
1. **M009** Sheet classification / human review — **Completed & Verified** (`5dc4b09`, migration `b8d9f0a1c2e3`)
2. **M010** Scale Calibration / Measurement Tools — **Completed & Verified** (migration `c9e0f1a2b3d4`)
3. **M011** Organization Foundation & Project Commercial Context — **Completed & Verified** (FG-007 / ADR-028; migration `d0a1b2c3d4e5`)
4. **FG-006** Historical Estimate Ingestion Engine Phase B — **Completed & Verified** (migration `e1b2c3d4e5f6`)
5. **FG-008** Labour Engine Phase B — **CLOSED / OPERATIONAL FOR UAT**; ADR-029 **Accepted**. Revision `f2c3d4e5f6a7` in chain. Foundation operational for UAT (not a populated operating catalog; not selling-price integration).
6. Organization-Calibrated Pricing Engine — [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) **CLOSED / OPERATIONAL FOR UAT**. ADR-025 **Accepted**; ADR-030 **Accepted**. Revision `a3b4c5d6e7f8` in chain.
7. AI Take-off / Quantity Extraction Foundation — [FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) **CLOSED / OPERATIONAL FOR UAT** (M012; ADR-031 **Accepted**; real external AI provider **not authorized**; Alembic revision `b4c5d6e7f8a9` in chain)
8. Project Hub UX — [FG-011](feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT** (evolve `/projects/<id>`; no new module; no schema)
9. Internal Detailed Cost Breakdown + Customer Estimate consistency — [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** (depends on Pricing Engine snapshot architecture; outputs 3–4 / four-output **product** remains Future)
10. Authentication / actor identity + shared API foundation — **COMPLETE.** Office Authentication / Actor Identity / Membership: **CLOSED / OPERATIONAL FOR UAT** ([ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md)). Shared API foundation: **CLOSED / OPERATIONAL FOR UAT** ([FG-019](feature-gates/FG-019-shared-api-foundation-v1.md); GET-only `/api/v1`; no FG-019 migration; **gate-at-close** live current was `b0c1d2e3f4a5`; live head today `f4a5b6c7d8e9`).
11. BUILD Field Capture V1 — **COMPLETE.** [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**. Image-only Compatible Renditions **implemented**. Gate-at-close live current = head was `c1d2e3f4a5b6`. Office UAT port **5013**.
12. Field Web / Today + Capture + plan access — **CLOSED** ([FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md)). IMPLEMENTED / LIVE-MIGRATED / REAL-IPHONE UAT COMPLETE SUBJECT TO THE EXPLICIT SESSION-EXPIRY DEFERRED EXCEPTION. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED). **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** Plan access deferred to a later Field slice. Live current = head `d2e3f4a5b6c7`.
13. MONITOR basic estimated-vs-actual — **CLOSED / OPERATIONAL FOR UAT** ([FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted**; [monitor-v1-implementation-reconnaissance.md](architecture/monitor-v1-implementation-reconnaissance.md) **COMPLETE**)
    - **Commercialization hygiene (not a numbered core-package item):** Contractor-facing UX language — [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **FUTURE / RECORDED / IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / SLICE 4 IMPLEMENTED / NOT CLOSED / NOT A PRODUCT-WIDE SWEEP**. Remaining surfaces **NOT AUTHORIZED**. Does **not** displace Item 14 LEARN or Item 15 FG-024.
14. LEARN historical intelligence / review-gated learning (ADR-024)
15. Contract/warranty when Legal Content Gate is satisfied — [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. One linked gate (library / update engine / frozen snapshot / monitoring). Does **not** jump Item 13 / FG-023. FG-025 is **not** a split of this gate.
16. QuickBooks when separately Feature-Gated

**Auth dependency:** Items **11–12 require completed item 10**, which is now **COMPLETE** ([FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) + [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md)). Item 11 is **COMPLETE** ([FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md)). Item 12 Field Web is **CLOSED** ([FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md); SESSION-EXPIRY RECOVERY **DEFERRED / NOT YET EXERCISED**). Pricing Engine (item 6) and AI take-off (item 7) **require item 5** (Labour Engine), which is **implemented**. This sequence is **not** reordered to put auth before M009. Office M009 historically proceeded on the then-unauthenticated app; field capture must not.

**ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.** Item 10 **COMPLETE** does **not** authorize BUILD, Field Web, tokens, RBAC, or org-switcher.

**Explicitly later / separately Feature-Gated:** voice AI, photo AI, advanced forecasting, native iOS, offline-first sync, QuickBooks API, contractor-facing UX language ([FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **RECORDED / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / SLICE 4 IMPLEMENTED / NOT CLOSED**; remaining surfaces **NOT AUTHORIZED**), North American contract/warranty intelligence ([FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**), supplier integrations, POs, CAD-first, multi-tenant productization, ML recommendations, product/repository rename.

---

## Strategic program — Phases A–G

| Phase | Name | Intent | Depends on |
|-------|------|--------|------------|
| **A** | PDF plan upload and storage | Project-scoped upload, secure storage, document register | **Done (M005)** |
| **DI** | Document Intelligence | Pages, packages/revisions, metadata, search | **M006 architecture; M007 code** |
| **SI** | Sheet Intelligence | Sheets, discipline, review workflow, page maps | **Done (M009)** |
| **B** | Scale confirmation, manual measurement | Human-scale confirm; count/length/area; citations | **Done (M010)** |
| **C** | AI-assisted extraction (narrow trade/assembly) | One assembly vocabulary; confidence scores | **FG-010 / M012 CLOSED / OPERATIONAL FOR UAT** (mock extractor; real external AI not authorized) |
| **D** | Reviewed quantities → estimate assemblies | Explicit map + human approve into `EstimateVersion` | Phase C; ADR-006, ADR-007. **[FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) CLOSED / OPERATIONAL FOR UAT** |
| **E** | Supplier catalogue and price-file import | CSV/manual quotes; contractor prices; effective dates; **governed bulk onboarding** (future pin; not one-product-at-a-time) | ADR-008; [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md); Feature Gate; Material Catalogue identity first |
| **F** | Live supplier inventory and pricing | API/EDI adapters; stale handling; PO prep start | Phase E; adapter-per-supplier (Winchester is reference, not exclusive) |
| **G** | CAD ingestion and broader automated take-off | DWG/DXF; expanded trades | Phases D proven; ADR-009/010 |

Phases A–D (Plan Intelligence) and E–F (Supplier) may be sequenced in parallel **programs** after separate Feature Gates—do not casually couple schemas.

---

## Recommended first proof of concept (narrow)

| Field | Recommendation |
|-------|----------------|
| **Name** | Plan Intelligence POC — Interior Door Count from Searchable PDF |
| **Accepted input type** | **Searchable PDF** only (not scanned, not CAD) |
| **Drawing disciplines** | **Architectural** floor plans (one or two sheets max per trial job) |
| **Measurable element** | **Interior door openings — count** (optional stretch: door schedule cross-check if present) |
| **Human-review workflow** | AI or manual count candidates → reviewer accepts/adjusts/rejects per door → approve take-off package → **no** estimate insert until explicit map action (ADR-006) |
| **Source traceability** | Each count cites file, page, sheet id/name, region bbox; method + confidence stored (ADR-005) |
| **Success criteria** | Governed in [FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md): searchable PDF; architectural sheet; extraction run; cited interior-door candidates; human accept/adjust/reject/duplicate; immutable approved package; **no** silent estimate insert (Phase D later) |
| **Explicit non-goals** | Scanned OCR; structural/civil; CAD; supplier APIs; multi-trade extraction; auto-insert to estimates; proposal changes; PO generation; Labour Engine / Pricing Engine writes |

**Historical note:** Phase A (M005) and Phase B (M010) are **implemented**. FG-010 / Phase C foundation is **CLOSED / OPERATIONAL FOR UAT** (mock extractor only). Real external AI provider is **not authorized**. COUNT is dimensionless (must not require scale); dimensional measurements remain fail-closed. Phase D mapping is [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**.

---

## Next recommended milestones

1. **STOP.** [v1-completion-register.md](v1-completion-register.md) is **GOVERNING**. CalibraytAI V1 readiness **55%**. **3 / 11** COMPLETE. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Do **not** reopen FG-029. Do **not** implement FG-030. Do **not** begin another V1 package from this close. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) is **SLICE 1, SLICE 2, SLICE 3, SLICE 4, AND SLICE 5 IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Do **not** start another FG-025 slice. Do **not** begin FG-024. Observation Delete **queued** — do **not** implement yet. Do **not** implement Project Closeout. Do not implement live BMR API, bulk supplier onboarding, national permit expansion, or Change Order documents. Do not accept ADR-008. Do not accept ADR-010. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) remains **CLOSED**. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED.** **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**
2. **Roadmap direction:** Item 12 Field Web is **CLOSED**. Item 13 is **CLOSED / OPERATIONAL FOR UAT**. Native Signing **development** may proceed under separate governance; **production activation** remains blocked pending counsel.
3. Phase D reviewed quantity → estimate mapping is [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. V1-02 / [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. V1-03 / [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) is **CLOSED / OPERATIONAL FOR UAT**.
4. ADR-014 remains Proposed as a document; Page ≠ Sheet is required by FG-004 (M009 implemented).
5. Subsequent CalibAi sequence after item 10: BUILD, field web, MONITOR implementation, LEARN — each separately gated. ADR-021 does not move MONITOR ahead of auth/BUILD.
6. Formal proposal acceptance workflow (ADR-004) remains a Proposals-track candidate. Real external AI provider remains **not authorized**. [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) office historical-upload UX is **CLOSED / OPERATIONAL FOR UAT** (revision `c5d6e7f8a9b0` in chain; no durable UploadBatch). Industry benchmarking remains future, separately gated.

---

## Near-Term (operational)

- Production secrets (`SECRET_KEY`) — local-only gitignored `.env` is in use for this operating environment; production hosting/secrets remain platform debt (not a Feature Gate)
- Remaining multi-user / SaaS questions (RBAC, invitations, SSO, org-switcher) — **not** office authentication; office login is **CLOSED / OPERATIONAL FOR UAT**
- Migration verification runbook
- Change Order audit trail (candidate)

## Future (provisional product)

These remain **not started** unless a later Feature Gate says otherwise. FG-015 / FG-016 / FG-017 / FG-018 office-auth / FG-019 Shared API are **CLOSED / OPERATIONAL FOR UAT** and are **not** future work.

- Formal proposal acceptance workflow; e-signature
- Permit branding from Brand Profile; national Permit Rules expansion (FG-016 Ontario/Ottawa POC is closed; expansion is not authorized)
- Change Order governed document family / client email / field UX — **FUTURE / NOT IMPLEMENTED** pin ([change-order-document-family.md](architecture/change-order-document-family.md)); do not create a second Change Order entity
- Project creation from accepted proposal; budgets
- **Four-output document package** — outputs 1–2: [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**; outputs 3–4 (QuickBooks export, construction contract + warranty) remain Future — [architecture/project-document-package.md](architecture/project-document-package.md); contract/warranty generation is [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**
- Shared API foundation — **CLOSED / OPERATIONAL FOR UAT** ([FG-019](feature-gates/FG-019-shared-api-foundation-v1.md); [ADR-022](adr/ADR-022-field-client-and-shared-api.md)). GET-only `/api/v1`. No tokens. Office authentication remains [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md).
- BUILD Field Observation foundation — **CLOSED / OPERATIONAL FOR UAT** ([FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md)); Field Web (sequence item 12) **CLOSED** ([FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md); SESSION-EXPIRY RECOVERY **DEFERRED / NOT YET EXERCISED**)
- Contract / e-signature / signed Change Order — **ARCHITECTURE RECONNAISSANCE COMPLETE / NOT IMPLEMENTED** ([architecture/contract-esignature-and-signed-change-order.md](architecture/contract-esignature-and-signed-change-order.md)); recommendation **NATIVE V1**; counsel spec **PREPARED** ([legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md)); **development may proceed under separate governance**; **production activation blocked pending counsel**; no Feature Gate in this pass; Change Orders first; Contract later behind Legal Content Gate
- MONITOR remainder (forecast-final GM / Field Web MONITOR / LEARN remain out of V1); LEARN / ML recommendations
- Scheduling, daily reports, timesheets
- Purchasing / POs (beyond prep)
- Job costing, invoicing, QuickBooks — see [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- Historical estimating intelligence; reports; settings
- Plan Intelligence Phase **D–G** (Phase C / FG-010 is **CLOSED / OPERATIONAL FOR UAT**) and Supplier Phases E–F as above
- Real external AI provider (ADR-010 **Proposed**; not authorized)

## Deferred

- Full ERP replacement
- Speculative AI price generation without human approval
- Silent overwrite of historical commercial records
- CAD-first platform strategy (rejected by ADR-009 unless Joel reverses)

## Decisions Required (Joel)

1. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) Slice 1 through Slice 5 are **IMPLEMENTED**. Remaining surfaces **NOT AUTHORIZED**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) is **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Do **not** implement V1-03 from this recording. Do **not** start another FG-025 slice. Do **not** implement FG-024. Do **not** implement Closeout. Do not implement national permit expansion, Change Order document work, live BMR API, or bulk supplier onboarding. Do not accept ADR-008. Do not accept ADR-010. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) remains **CLOSED**. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED.** **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.**
2. Native Signing is a **parallel** track ([legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md)). **Development may proceed under separate governance. Production activation / real customer use is blocked pending Ontario counsel approval of the signing process.** Counsel review is **not** a general development hold. Legal Content Gate for Contract/Warranty templates remains in force. Project Closeout remains **FUTURE**.
3. ADR-010 remains **Proposed** (OCR/CAD/provider). Real external AI provider remains **not authorized**.
4. Confirm POC element remains `INTERIOR_DOOR_OPENING` count.
5. Remaining multi-user / SaaS questions (RBAC, invitations, SSO, org-switcher) and production hosting/secrets. Office authentication is **CLOSED / OPERATIONAL FOR UAT** — not an open auth-model gap.
6. Before a real AI provider: separate governed decision (identity, data sent, retention, training, privacy, credentials, failure, cost).
7. Whether supplier CSV (Phase E) may start before take-off Phase D.
8. FG-017 leftovers (not this pass): Issued→Draft status lock; Internal Detailed Cost Breakdown branding.

# Platform Roadmap — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Planning |
| Updated | 2026-08-31 |

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
| Supplier Catalogue Management | **Future** (only free-text `CostItem.supplier` today). CalibAi identity is [material-catalogue-architecture.md](architecture/material-catalogue-architecture.md) (**Partial Current**; [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**). Governed **bulk** supplier onboarding is a **FUTURE / NOT IMPLEMENTED** pin (not one-product-at-a-time; not authorized by FG-014). | [architecture/supplier-catalogue-inventory-pricing.md](architecture/supplier-catalogue-inventory-pricing.md) · [architecture/supplier-channel-and-launch-partner.md](architecture/supplier-channel-and-launch-partner.md) · [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (supplier-neutral; Winchester launch/reference; **not implemented**) |
| Supplier Inventory and Pricing Integrations | **Future** | Supplier architecture; Phase F; heterogeneous adapters (do not assume one BMR/national model) |
| Procurement and Purchase-Order Preparation | **Future** (nav placeholder only) | Supplier + Projects/Procurement boundary; contractor↔supplier relationship **A** distinct from CalibAi channel relationship **B** |
| Proposal and PDF Output | **Current** (snapshot + PDF; Accepted immutability; FG-012 named-method consistency; FG-017 Brand Profile / issued snapshot) | [modules/proposals.md](modules/proposals.md) · [FG-012](feature-gates/FG-012-estimate-output-consistency.md) · [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) |
| Project document package (4 outputs) | **Partial** — outputs 1–2 **CLOSED / OPERATIONAL FOR UAT** ([FG-012](feature-gates/FG-012-estimate-output-consistency.md)); outputs 3–4 Future. **Permit Foundation V1** [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. Pass 2 Permit Intelligence [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. **Organization Brand Profile** is **CLOSED / OPERATIONAL FOR UAT** ([ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md)). **Change Order document family** is **FUTURE / NOT IMPLEMENTED**. | [architecture/project-document-package.md](architecture/project-document-package.md) · [architecture/permit-and-approvals-report.md](architecture/permit-and-approvals-report.md) · [architecture/permit-rules-library.md](architecture/permit-rules-library.md) · [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md) · [architecture/organization-brand-profile.md](architecture/organization-brand-profile.md) · [architecture/change-order-document-family.md](architecture/change-order-document-family.md) · [pricing-policy.md](pricing-policy.md) |
| QuickBooks estimate export | **Future** (pipeline boundary documented; no API) | [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md) |
| Ontario construction contract + warranty | **Future** (Legal Content Gate; no templates registered) | [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md) |
| Project Controls and Actual-Cost Feedback | **Partial** (Change Orders current; job cost future) | [modules/projects.md](modules/projects.md) |

**Differentiator (long-term):** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project` record ([CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md)). Plan → reviewed take-off → estimate remains the PLAN/PRICE spine, with citations and no silent commercial overwrite.

**Governed position after FG-019 close:**

| Layer | Position |
|-------|----------|
| **CURRENT** | FG-008 through FG-019 **CLOSED / OPERATIONAL FOR UAT** as applicable. Live current = head **`b0c1d2e3f4a5`**. Full suite **494 passed**. API UAT port **5012**. Office auth UAT port **5011**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. |
| **NEXT AUTHORIZED ACTION** | **STOP.** Do not start BUILD, Field Web, tokens, RBAC, or org-switcher. |
| **ROADMAP ITEM 10** | **COMPLETE.** Office Authentication / Actor Identity / Membership: **CLOSED / OPERATIONAL FOR UAT** ([FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md)). Shared API foundation: **CLOSED / OPERATIONAL FOR UAT** ([FG-019](feature-gates/FG-019-shared-api-foundation-v1.md)). |
| **ROADMAP DIRECTION** | Item 11 BUILD is **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.** |
| **SEPARATELY GOVERNED FUTURE PROGRAMS** | BUILD; Field Web; Phase D; supplier integration; Change Order document family; Permit branding / national expansion; QuickBooks; Ontario Contract / Warranty; MONITOR; LEARN; real external AI; other repository-recorded future work. Not reordered here. Not authorized by FG-019 close. |

[FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-008](adr/ADR-008-supplier-price-snapshotting.md) **Proposed**. FG-010 Phase D is **NOT STARTED**. **Change Order document family** remains **FUTURE / NOT IMPLEMENTED**.

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

- **`main` / `origin/main`** — FG-018 close: verify `git rev-parse HEAD` and `git rev-parse origin/main`. Implementation parent `0d7af3e93a9d6c4f27eb2136f915297620be59ed`. Alembic **current = head = `b0c1d2e3f4a5`**. One graph head. Full-suite governed baseline **460 passed**.
- **FG-008 through FG-019** **CLOSED / OPERATIONAL FOR UAT** as applicable. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 is **COMPLETE**.
- **ADR-021** **Accepted** (MONITOR **not implemented**; Feature Gate **not** authorized by the ADR).
- **Review Turnover Protocol** adopted (2026-08-28) — `Review Turnover` governing.
- **M010 Scale Calibration & Measurement Tools** implemented and verified (2026-08-28).
- **M011 Organization Foundation & Project Commercial Context** implemented and verified (2026-08-28).
- **FG-006 Historical Estimate Ingestion Engine Phase B** implemented and verified (2026-08-28).
- CalibAi V1 direction (not authorized as a single implementation): PLAN → PRICE → CONTRACT baseline → BUILD field capture → basic MONITOR — [CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- Document package outputs 3–4, QuickBooks API, contract/warranty generation — **not started** (governance recorded only). Outputs 1–2: [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**.
- Permit Intelligence — architecture **Accepted** (ADR-037/038/039); Pass 1 [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**; Pass 2 [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT** ([permit-and-approvals-report.md](architecture/permit-and-approvals-report.md)). National permit expansion **not authorized**. Permit branding from Brand Profile **not authorized**.
- Organization Brand Profile — **CLOSED / OPERATIONAL FOR UAT** ([organization-brand-profile.md](architecture/organization-brand-profile.md)); [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md). Proposal is the V1 consumer. Change Order / Permit / chrome consumers remain future.
- Change Order document family — **FUTURE / NOT IMPLEMENTED** pin ([change-order-document-family.md](architecture/change-order-document-family.md)); not a Feature Gate; existing Change Order record remains authoritative.
- Estimate mapping (Phase D) remains **NOT STARTED / NOT AUTHORIZED**

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
10. Authentication / actor identity + shared API foundation — **COMPLETE.** Office Authentication / Actor Identity / Membership: **CLOSED / OPERATIONAL FOR UAT** ([ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md)). Shared API foundation: **CLOSED / OPERATIONAL FOR UAT** ([FG-019](feature-gates/FG-019-shared-api-foundation-v1.md); GET-only `/api/v1`; no migration; live current = head `b0c1d2e3f4a5`).
11. BUILD Field Capture V1 — **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED.** Item 10 is complete. Not started. Not authorized.
12. Field Web / Today + Capture + plan access — **BLOCKED.** Requires a separately governed Field Web / BUILD gate. Not started. Not authorized.
13. MONITOR basic estimated-vs-actual ([ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted**; composed frozen baseline; Project Gross Margin; **DOWNSTREAM / NOT IMPLEMENTED**; Feature Gate **not authorized** by ADR-021)
14. LEARN historical intelligence / review-gated learning (ADR-024)
15. Contract/warranty when Legal Content Gate is satisfied
16. QuickBooks when separately Feature-Gated

**Auth dependency:** Items **11–12 require completed item 10**, which is now **COMPLETE** ([FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) + [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md)). BUILD remains **NOT AUTHORIZED** until its own Feature Gate. Pricing Engine (item 6) and AI take-off (item 7) **require item 5** (Labour Engine), which is **implemented**. This sequence is **not** reordered to put auth before M009. Office M009 historically proceeded on the then-unauthenticated app; field capture must not.

**ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.** Item 10 **COMPLETE** does **not** authorize BUILD, Field Web, tokens, RBAC, or org-switcher.

**Explicitly later / separately Feature-Gated:** voice AI, photo AI, advanced forecasting, native iOS, offline-first sync, QuickBooks API, automated Ontario contract/warranty, supplier integrations, POs, CAD-first, multi-tenant productization, ML recommendations, product/repository rename.

---

## Strategic program — Phases A–G

| Phase | Name | Intent | Depends on |
|-------|------|--------|------------|
| **A** | PDF plan upload and storage | Project-scoped upload, secure storage, document register | **Done (M005)** |
| **DI** | Document Intelligence | Pages, packages/revisions, metadata, search | **M006 architecture; M007 code** |
| **SI** | Sheet Intelligence | Sheets, discipline, review workflow, page maps | **Done (M009)** |
| **B** | Scale confirmation, manual measurement | Human-scale confirm; count/length/area; citations | **Done (M010)** |
| **C** | AI-assisted extraction (narrow trade/assembly) | One assembly vocabulary; confidence scores | **FG-010 / M012 CLOSED / OPERATIONAL FOR UAT** (mock extractor; real external AI not authorized) |
| **D** | Reviewed quantities → estimate assemblies | Explicit map + human approve into `EstimateVersion` | Phase C; ADR-006, ADR-007 |
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

**Historical note:** Phase A (M005) and Phase B (M010) are **implemented**. FG-010 / Phase C foundation is **CLOSED / OPERATIONAL FOR UAT** (mock extractor only). Real external AI provider is **not authorized**. COUNT is dimensionless (must not require scale); dimensional measurements remain fail-closed. Phase D mapping is **NOT STARTED**.

---

## Next recommended milestones

1. **STOP.** [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 is **COMPLETE**. Do not start BUILD, Field Web, tokens, RBAC, or org-switcher. Do not implement MONITOR, Phase D, supplier/Winchester POC, bulk supplier onboarding, national permit expansion, or Change Order documents. Do not accept ADR-008.
2. **Roadmap direction:** Item 11 BUILD is **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. Wait for Joel to authorize BUILD architecture / a Feature Gate.
3. Phase D reviewed quantity → estimate mapping remains **NOT STARTED / NOT AUTHORIZED**.
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
- **Four-output document package** — outputs 1–2: [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**; outputs 3–4 (QuickBooks export, Ontario contract + warranty) remain Future — [architecture/project-document-package.md](architecture/project-document-package.md)
- Shared API foundation — **CLOSED / OPERATIONAL FOR UAT** ([FG-019](feature-gates/FG-019-shared-api-foundation-v1.md); [ADR-022](adr/ADR-022-field-client-and-shared-api.md)). GET-only `/api/v1`. No tokens. Office authentication remains [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md).
- BUILD field capture; field web (sequence items 11–12; Item 11 **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**)
- MONITOR implementation; LEARN / ML recommendations
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

1. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 10 is **COMPLETE**. **STOP.** Do not start BUILD, Field Web, tokens, RBAC, or org-switcher. Do not implement national permit expansion, Phase D, Change Order document work, supplier integration, bulk supplier onboarding, or a Winchester POC. Do not accept ADR-008.
2. Whether to authorize BUILD architecture / a BUILD Feature Gate. Item 11 is **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**.
3. ADR-010 remains **Proposed** (OCR/CAD/provider). Real external AI provider remains **not authorized**.
4. Confirm POC element remains `INTERIOR_DOOR_OPENING` count.
5. Remaining multi-user / SaaS questions (RBAC, invitations, SSO, org-switcher) and production hosting/secrets. Office authentication is **CLOSED / OPERATIONAL FOR UAT** — not an open auth-model gap.
6. Before a real AI provider: separate governed decision (identity, data sent, retention, training, privacy, credentials, failure, cost).
7. Whether supplier CSV (Phase E) may start before take-off Phase D.
8. FG-017 leftovers (not this pass): Issued→Draft status lock; Internal Detailed Cost Breakdown branding.

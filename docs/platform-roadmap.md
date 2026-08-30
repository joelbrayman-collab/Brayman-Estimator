# Platform Roadmap — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Planning |
| Updated | 2026-08-30 |

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
| Supplier Catalogue Management | **Future** (only free-text `CostItem.supplier` today) | [architecture/supplier-catalogue-inventory-pricing.md](architecture/supplier-catalogue-inventory-pricing.md) |
| Supplier Inventory and Pricing Integrations | **Future** | Supplier architecture; Phase F |
| Procurement and Purchase-Order Preparation | **Future** (nav placeholder only) | Supplier + Projects/Procurement boundary |
| Proposal and PDF Output | **Current** (snapshot + PDF; Accepted immutability enforced) | [modules/proposals.md](modules/proposals.md) |
| Project document package (4 outputs) | **Future** (governance recorded 2026-08-25) | [architecture/project-document-package.md](architecture/project-document-package.md) · [pricing-policy.md](pricing-policy.md) |
| QuickBooks estimate export | **Future** (pipeline boundary documented; no API) | [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md) |
| Ontario construction contract + warranty | **Future** (Legal Content Gate; no templates registered) | [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md) |
| Project Controls and Actual-Cost Feedback | **Partial** (Change Orders current; job cost future) | [modules/projects.md](modules/projects.md) |

**Differentiator (long-term):** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project` record ([CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md)). Plan → reviewed take-off → estimate remains the PLAN/PRICE spine, with citations and no silent commercial overwrite.

**Next candidate milestone:** [FG-011](feature-gates/FG-011-project-hub-ux.md) **Project Hub UX** — **APPROVED FOR IMPLEMENTATION** — **IMPLEMENTATION NOT STARTED**. Evolve `/projects/<id>` only. No new M0xx. Separately, FG-010 Phase D (reviewed quantity → estimate mapping) is **NOT STARTED**. Real external AI provider **not authorized**. FG-008 / FG-009 / FG-010 remain **CLOSED / OPERATIONAL FOR UAT**.

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

- **`main` / `origin/main`** — FG-010 implementation `9665295`. Alembic current/head `b4c5d6e7f8a9`. FG-008 / FG-009 / FG-010 **CLOSED / OPERATIONAL FOR UAT**.
- **Review Turnover Protocol** adopted (2026-08-28) — `Review Turnover` governing.
- **M010 Scale Calibration & Measurement Tools** implemented and verified (2026-08-28).
- **M011 Organization Foundation & Project Commercial Context** implemented and verified (2026-08-28).
- **FG-006 Historical Estimate Ingestion Engine Phase B** implemented and verified (2026-08-28).
- CalibAi V1 direction (not authorized as a single implementation): PLAN → PRICE → CONTRACT baseline → BUILD field capture → basic MONITOR — [CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- Document package, QuickBooks API, contract/warranty generation — **not started** (governance recorded only)
- Estimate mapping remains outside near-term sheet work

---

## CalibAi proposed sequencing (roadmap direction — not implementation authority)

Each item still needs its own Feature Gate / approved Cursor prompt.

0. CAR-001 architecture alignment + Review Turnover Protocol — **Adopted**
1. **M009** Sheet classification / human review — **Completed & Verified** (`5dc4b09`, migration `b8d9f0a1c2e3`)
2. **M010** Scale Calibration / Measurement Tools — **Completed & Verified** (migration `c9e0f1a2b3d4`)
3. **M011** Organization Foundation & Project Commercial Context — **Completed & Verified** (FG-007 / ADR-028; migration `d0a1b2c3d4e5`)
4. **FG-006** Historical Estimate Ingestion Engine Phase B — **Completed & Verified** (migration `e1b2c3d4e5f6`)
5. **FG-008** Labour Engine Phase B — **CLOSED / OPERATIONAL FOR UAT**; ADR-029 **Accepted**. Revision `f2c3d4e5f6a7` in chain (live head `b4c5d6e7f8a9`). Foundation operational for UAT (not a populated operating catalog; not selling-price integration).
6. Organization-Calibrated Pricing Engine — [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) **CLOSED / OPERATIONAL FOR UAT**. ADR-025 **Accepted**; ADR-030 **Accepted**. Revision `a3b4c5d6e7f8` in chain.
7. AI Take-off / Quantity Extraction Foundation — [FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) **CLOSED / OPERATIONAL FOR UAT** (M012; ADR-031 **Accepted**; real external AI provider **not authorized**; live head `b4c5d6e7f8a9`)
8. Project Hub UX — [FG-011](feature-gates/FG-011-project-hub-ux.md) **APPROVED FOR IMPLEMENTATION** — **IMPLEMENTATION NOT STARTED** (evolve `/projects/<id>`; no new module; no schema)
9. Internal Detailed Cost Breakdown + Customer Estimate consistency (depends on Pricing Engine snapshot architecture; four-output **product** remains Future)
10. Authentication / actor identity + shared API foundation
11. BUILD Field Capture V1
12. Field Web / Today + Capture + plan access
13. MONITOR basic estimated-vs-actual
14. LEARN historical intelligence / review-gated learning (ADR-024)
15. Contract/warranty when Legal Content Gate is satisfied
16. QuickBooks when separately Feature-Gated

**Auth dependency:** Items **11–12 require item 10** (authentication before field capture). Pricing Engine (item 6) and AI take-off (item 7) **require item 5** (Labour Engine), which is **implemented**. This sequence is **not** reordered to put auth before M009. Office M009 may proceed on the current unauthenticated app; field capture must not.

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
| **E** | Supplier catalogue and price-file import | CSV/manual quotes; contractor prices; effective dates | ADR-008; Feature Gate |
| **F** | Live supplier inventory and pricing | API/EDI adapters; stale handling; PO prep start | Phase E |
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

1. **FG-011** Project Hub UX is **APPROVED FOR IMPLEMENTATION**. Product implementation requires a **separate** bounded Cursor prompt. Do not implement from this roadmap entry alone.
2. Phase D reviewed quantity → estimate mapping remains **NOT STARTED / NOT AUTHORIZED**.
3. Joel accepts/amends ADR-021 when that decision is ready. ADR-014 remains Proposed as a document; Page ≠ Sheet is required by FG-004 (M009 implemented).
4. Subsequent CalibAi sequence after FG-011: estimate-output consistency, then auth, each separately gated.
5. Formal proposal acceptance workflow (ADR-004) remains a Proposals-track candidate. Real external AI provider remains **not authorized**.

---

## Near-Term (operational)

- Auth / multi-user model clarification
- Migration verification runbook
- Production secrets (`SECRET_KEY`)
- Change Order audit trail (candidate)

## Future (provisional product)

- Formal proposal acceptance workflow; e-signature
- Project creation from accepted proposal; budgets
- **Four-output document package** (internal breakdown, customer estimate, QuickBooks export, Ontario contract + warranty) — [architecture/project-document-package.md](architecture/project-document-package.md)
- Scheduling, daily reports, timesheets
- Purchasing / POs (beyond prep)
- Job costing, invoicing, QuickBooks — see [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- Historical estimating intelligence; reports; settings
- Full Plan Intelligence Phases C–G (C = FG-010 if approved) and Supplier Phases E–F as above

## Deferred

- Full ERP replacement
- Speculative AI price generation without human approval
- Silent overwrite of historical commercial records
- CAD-first platform strategy (rejected by ADR-009 unless Joel reverses)

## Decisions Required (Joel)

1. Issue a **separate** bounded FG-010 implementation prompt. Real external AI provider remains **not authorized**.
2. ADR-010 remains **Proposed** (OCR/CAD/provider).
3. Confirm POC element remains `INTERIOR_DOOR_OPENING` count.
4. Auth model; production hosting/secrets (unchanged platform debt).
5. Before a real AI provider: separate governed decision (identity, data sent, retention, training, privacy, credentials, failure, cost).
6. Whether supplier CSV (Phase E) may start before take-off Phase D.

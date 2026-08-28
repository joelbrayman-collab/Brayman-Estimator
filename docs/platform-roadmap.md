# Platform Roadmap — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Planning |
| Updated | 2026-08-28 |

Use repository evidence for **Completed**. Strategic pillars and Phases A–G are **Future** unless marked otherwise. Do not describe unimplemented integrations as existing.

---

## Platform pillars (strategic)

| Pillar | Status today | Architecture / notes |
|--------|--------------|----------------------|
| Core CRM and project records | **Current** (Clients, Projects) | [modules/crm.md](modules/crm.md), [modules/projects.md](modules/projects.md) |
| Estimating and assemblies | **Current** | [modules/estimating.md](modules/estimating.md) |
| Plan Intelligence | **Partial** — Phase A upload (M005); Document Intelligence indexing (M007); Sheet Intelligence & human review (M009); Scale (M010) / take-off (M011+) future | [architecture/plan-intelligence-and-automated-takeoff.md](architecture/plan-intelligence-and-automated-takeoff.md) · [architecture/document-intelligence.md](architecture/document-intelligence.md) · [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md) · [modules/plan-intelligence.md](modules/plan-intelligence.md) · [FG-002](feature-gates/FG-002-plan-intelligence-phase-a.md) · [FG-003](feature-gates/FG-003-document-intelligence-readiness.md) · [FG-004](feature-gates/FG-004-m009-sheet-classification.md) |
| Automated Quantity Take-Off | **Future** | Same Plan Intelligence docs |
| Human Review and Source Traceability | **Future** (ADR-005/006/011) | Embedded in Plan Intelligence |
| Supplier Catalogue Management | **Future** (only free-text `CostItem.supplier` today) | [architecture/supplier-catalogue-inventory-pricing.md](architecture/supplier-catalogue-inventory-pricing.md) |
| Supplier Inventory and Pricing Integrations | **Future** | Supplier architecture; Phase F |
| Procurement and Purchase-Order Preparation | **Future** (nav placeholder only) | Supplier + Projects/Procurement boundary |
| Proposal and PDF Output | **Current** (snapshot + PDF; Accepted immutability enforced) | [modules/proposals.md](modules/proposals.md) |
| Project document package (4 outputs) | **Future** (governance recorded 2026-08-25) | [architecture/project-document-package.md](architecture/project-document-package.md) · [pricing-policy.md](pricing-policy.md) |
| QuickBooks estimate export | **Future** (pipeline boundary documented; no API) | [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md) |
| Ontario construction contract + warranty | **Future** (Legal Content Gate; no templates registered) | [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md) |
| Project Controls and Actual-Cost Feedback | **Partial** (Change Orders current; job cost future) | [modules/projects.md](modules/projects.md) |

**Differentiator (long-term):** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project` record ([CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md)). Plan → reviewed take-off → estimate remains the PLAN/PRICE spine, with citations and no silent commercial overwrite.

**Next coded milestone:** **M010** — Scale Calibration / Measurement Tools. Requires dedicated Feature Gate.

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

---

## Current (near-term product governance)

- **`main` / `origin/main`** — confirm with `git rev-parse`. CAR-001 adopted; M005–M010 merged and verified.
- **Review Turnover Protocol** adopted (2026-08-28) — `Review Turnover` governing.
- **M010 Scale Calibration & Measurement Tools** implemented and verified (2026-08-28).
- CalibAi V1 direction (not authorized as a single implementation): PLAN → PRICE → CONTRACT baseline → BUILD field capture → basic MONITOR — [CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md)
- Document package, QuickBooks API, contract/warranty generation — **not started** (governance recorded only)
- Estimate mapping remains outside near-term sheet work

---

## CalibAi proposed sequencing (roadmap direction — not implementation authority)

Each item still needs its own Feature Gate / approved Cursor prompt.

0. CAR-001 architecture alignment + Review Turnover Protocol — **Adopted**
1. **M009** Sheet classification / human review — **Completed & Verified** (`5dc4b09`, migration `b8d9f0a1c2e3`)
2. **M010** Scale Calibration / Measurement Tools — **Completed & Verified** (migration `c9e0f1a2b3d4`)
3. **M011** Organization Foundation & Project Commercial Context — **Feature Gate Prepared (FG-007 / ADR-028)**; awaits approval
4. **M012** Historical Estimate Ingestion Engine Phase B (FG-006) / Labour Engine Phase B
5. **M013** AI Take-off / Quantity Extraction Foundation
6. Project Hub UX
7. Pricing-policy application (requires [ADR-025](adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) acceptance)
6. Internal Detailed Cost Breakdown + Customer Estimate consistency
7. Authentication / actor identity + shared API foundation
8. BUILD Field Capture V1
9. Field Web / Today + Capture + plan access
10. MONITOR basic estimated-vs-actual
11. LEARN historical intelligence / review-gated learning (ADR-024)
12. Contract/warranty when Legal Content Gate is satisfied
13. QuickBooks when separately Feature-Gated

**Auth dependency:** Items **6–7 require item 5**. This sequence is **not** reordered to put auth before M009. Office M009 may proceed on the current unauthenticated app; field capture must not.

**Explicitly later / separately Feature-Gated:** voice AI, photo AI, advanced forecasting, native iOS, offline-first sync, QuickBooks API, automated Ontario contract/warranty, supplier integrations, POs, CAD-first, multi-tenant productization, ML recommendations, product/repository rename.

---

## Strategic program — Phases A–G

| Phase | Name | Intent | Depends on |
|-------|------|--------|------------|
| **A** | PDF plan upload and storage | Project-scoped upload, secure storage, document register | **Done (M005)** |
| **DI** | Document Intelligence | Pages, packages/revisions, metadata, search | **M006 architecture; M007 code** |
| **SI** | Sheet Intelligence | Sheets, discipline, review workflow, page maps | **M008 architecture**; coded sheets Feature-Gated next |
| **B** | Scale confirmation, manual measurement | Human-scale confirm; count/length/area; citations | SI coded sheets first |
| **C** | AI-assisted extraction (narrow trade/assembly) | One assembly vocabulary; confidence scores | Phase B; ADR-005, ADR-010 |
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
| **Success criteria** | (1) Upload/store/retrieve PDF; (2) classify/confirm sheet + scale; (3) produce reviewed door count with citations; (4) optional map into **one** draft estimate assembly/line with human approve; (5) re-upload does not mutate prior take-off version |
| **Explicit non-goals** | Scanned OCR; structural/civil; CAD; supplier APIs; multi-trade extraction; auto-insert to locked estimates; proposal changes; PO generation |

**Safest first slice:** implement **Phase A only** as the first coded milestone after Feature Gate (upload/storage/register), then Phase B manual count for doors **before** enabling AI (Phase C).

---

## Next recommended milestones

1. Dedicated **M009 implementation Cursor prompt** citing [FG-004](feature-gates/FG-004-m009-sheet-classification.md) (**code not started**).
2. Joel accepts/amends ADR-021 / ADR-025 (Proposed) when those decisions are ready. ADR-014 remains Proposed as a document; Page ≠ Sheet is required by FG-004.
3. Subsequent CalibAi sequence items 2–11 on the roadmap, each separately gated.
4. Formal proposal acceptance workflow (ADR-004) remains a Proposals-track candidate.

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
- Full Plan Intelligence Phases C–G and Supplier Phases E–F as above

## Deferred

- Full ERP replacement
- Speculative AI price generation without human approval
- Silent overwrite of historical commercial records
- CAD-first platform strategy (rejected by ADR-009 unless Joel reverses)

## Decisions Required (Joel)

1. Confirm strategic pillars and Phases A–G priority vs Milestone 003 immutability sequencing.
2. Accept/amend ADR-005–010.
3. Confirm POC element (interior door count) or substitute one assembly.
4. Auth model; production hosting/secrets.
5. Build-vs-buy preferences for PDF viewer / OCR (ADR-010).
6. Whether supplier CSV (Phase E) may start before take-off Phase D.

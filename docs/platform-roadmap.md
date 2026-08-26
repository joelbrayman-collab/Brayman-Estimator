# Platform Roadmap — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Planning |
| Updated | 2026-08-26 |

Use repository evidence for **Completed**. Strategic pillars and Phases A–G are **Future** unless marked otherwise. Do not describe unimplemented integrations as existing.

---

## Platform pillars (strategic)

| Pillar | Status today | Architecture / notes |
|--------|--------------|----------------------|
| Core CRM and project records | **Current** (Clients, Projects) | [modules/crm.md](modules/crm.md), [modules/projects.md](modules/projects.md) |
| Estimating and assemblies | **Current** | [modules/estimating.md](modules/estimating.md) |
| Plan Intelligence | **Partial** — Phase A upload (M005); Document Intelligence indexing (M007); Sheet Intelligence architecture (M008 docs); sheet/take-off code future | [architecture/plan-intelligence-and-automated-takeoff.md](architecture/plan-intelligence-and-automated-takeoff.md) · [architecture/document-intelligence.md](architecture/document-intelligence.md) · [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md) · [modules/plan-intelligence.md](modules/plan-intelligence.md) · [FG-002](feature-gates/FG-002-plan-intelligence-phase-a.md) · [FG-003](feature-gates/FG-003-document-intelligence-readiness.md) |
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

**Differentiator (long-term):** Plan → reviewed take-off → estimate → supplier-priced procurement → proposal, with citations and no silent commercial overwrite.

**Next strategic platform capability:** Feature-Gated **Sheet classification and human metadata review** (coded). M008 Sheet Intelligence architecture is on `main` as docs/readiness only — **not implemented**.


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

**Governance:**

- Platform Governance Foundation (Milestone 001) + baseline tag `v0.1-governance-baseline`
- Milestone 002 Proposals Feature Gate FG-001 + ADR-001–004 (+ strategic ADRs / architecture docs)
- Milestone 003 Accepted Proposal Immutability (`c59ec01`)
- Milestone 004 Plan Intelligence architecture documentation
- Milestone 005 FG-002 Approved + ADR-012 Proposed + Phase A (`098647c`; PR #4 → `db1a8da`)
- Milestone 006 Document Intelligence architecture + FG-003 (`35413a1`; PR #4) + ADR-013/014; ADR-015/016 with M007
- Milestone 007 Document Indexing (`cbefe7a`; PR #5 → `eb00123`)
- Milestone 008 Sheet Intelligence architecture + ADR-017/018 (`8c74e31`; PR #6 → `ee9b4b2`) — **docs only**

---

## Current (near-term product governance)

- **`main` / `origin/main`** — confirm with `git rev-parse` (expect parity; tip at or after `ee100ac`). August reconciliation `0fdf0d4`; state closure `ee100ac`; M005–M008 merged; working tree clean
- **No coded milestone in progress**
- Next coded candidate: Sheet classification + human metadata review (Feature Gate / prompt required) — **not started**
- Document package, QuickBooks API, contract/warranty generation — **not started** (governance recorded only)
- Then scale / manual measure → AI quantity POC under later gates
- Estimate mapping remains outside near-term sheet work

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

1. Joel accepts/amends ADR-017/018 and M008 readiness.
2. Feature-Gate and implement Sheet classification + human metadata review (recommended next coded milestone; **not started**).
3. Scale / manual measure, then AI quantity POC under later gates.
4. Estimate mapping / revision comparison under separate gates.
5. Formal proposal acceptance workflow (ADR-004) remains a Proposals-track candidate.

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

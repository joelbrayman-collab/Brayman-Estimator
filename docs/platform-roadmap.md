# Platform Roadmap — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Planning |
| Updated | 2026-07-25 |

Use repository evidence for **Completed**. Strategic pillars and Phases A–G are **Future** unless marked otherwise. Do not describe unimplemented integrations as existing.

---

## Platform pillars (strategic)

| Pillar | Status today | Architecture / notes |
|--------|--------------|----------------------|
| Core CRM and project records | **Current** (Clients, Projects) | [modules/crm.md](modules/crm.md), [modules/projects.md](modules/projects.md) |
| Estimating and assemblies | **Current** | [modules/estimating.md](modules/estimating.md) |
| Plan Intelligence | **Future** | [architecture/plan-intelligence-and-automated-takeoff.md](architecture/plan-intelligence-and-automated-takeoff.md) |
| Automated Quantity Take-Off | **Future** | Same Plan Intelligence doc |
| Human Review and Source Traceability | **Future** (required by ADR-005/006) | Embedded in Plan Intelligence |
| Supplier Catalogue Management | **Future** (only free-text `CostItem.supplier` today) | [architecture/supplier-catalogue-inventory-pricing.md](architecture/supplier-catalogue-inventory-pricing.md) |
| Supplier Inventory and Pricing Integrations | **Future** | Supplier architecture; Phase F |
| Procurement and Purchase-Order Preparation | **Future** (nav placeholder only) | Supplier + Projects/Procurement boundary |
| Proposal and PDF Output | **Current** (engine + snapshot + PDF) | [modules/proposals.md](modules/proposals.md); immutability hardening pending |
| Project Controls and Actual-Cost Feedback | **Partial** (Change Orders current; job cost future) | [modules/projects.md](modules/projects.md) |

**Differentiator (long-term):** Plan → reviewed take-off → estimate → supplier-priced procurement → proposal, with citations and no silent commercial overwrite.

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

**Governance:**

- Platform Governance Foundation (Milestone 001) + baseline tag `v0.1-governance-baseline`
- Milestone 002 Proposals Feature Gate FG-001 + ADR-001–004 (docs; see working tree / commit when directed)
- Strategic architecture docs for Plan Intelligence and Supplier Catalogue (this update; docs only)

---

## Current (near-term product governance)

- Milestone 003 — Accepted Proposal Immutability: **implemented** (service guard + UI + tests; pending commit)
- Milestone 002 / strategic architecture documentation still uncommitted in working tree
- Strategic Plan Intelligence / Supplier programs remain architecture-only until Feature-Gated

---

## Strategic program — Phases A–G

| Phase | Name | Intent | Depends on |
|-------|------|--------|------------|
| **A** | PDF plan upload and storage | Project-scoped upload, secure storage, document register | ADR-007, ADR-009, ADR-010 (light); Feature Gate |
| **B** | Sheet classification, scale confirmation, manual measurement | Human-scale confirm; count/length/area tools; citations | Phase A |
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

1. **Joel:** Accept/amend ADR-001–004 (Proposals) and ADR-005–010 (strategic).
2. **Milestone 003 — Accepted Proposal Immutability** (near-term product hardening).
3. **Feature Gate — Plan Intelligence Phase A POC** (docs + prompt), then implement Phase A only.
4. Later: Phases B→D; separately Feature-Gate Phase E supplier CSV import.

---

## Near-Term (operational)

- Auth / multi-user model clarification
- Migration verification runbook
- Production secrets (`SECRET_KEY`)
- Change Order audit trail (candidate)

## Future (provisional product)

- Formal proposal acceptance workflow; e-signature
- Project creation from accepted proposal; budgets
- Scheduling, daily reports, timesheets
- Purchasing / POs (beyond prep)
- Job costing, invoicing, QuickBooks
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

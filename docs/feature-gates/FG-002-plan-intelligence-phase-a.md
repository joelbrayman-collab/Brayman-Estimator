# Feature Gate — Plan Intelligence Phase A (PDF Upload & Storage)

| Attribute | Value |
|-----------|--------|
| ID | FG-002 |
| Module | Plan Intelligence |
| Milestone | Milestone 005 — Plan Intelligence Feature Gate and Phase A PDF Upload |
| Status | **Approved for Phase A implementation** (this gate) |
| Date | 2026-07-25 |
| Base commit | `c59ec01` (`main`) |
| Related ADRs | [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) · [ADR-009](../adr/ADR-009-pdf-first-versus-cad-first.md) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) · [ADR-012](../adr/ADR-012-plan-document-version-ownership.md) |
| Module doc | [modules/plan-intelligence.md](../modules/plan-intelligence.md) |
| Architecture | [architecture/plan-intelligence-and-automated-takeoff.md](../architecture/plan-intelligence-and-automated-takeoff.md) |

## Purpose

Authorize **only** Phase A: secure, project-scoped **searchable PDF** upload, private storage, metadata register, list/detail/download. Establish an extensible foundation for later drawing-set/revision workflows (ADR-012) without implementing those workflows yet.

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Plans have nowhere to live in the app; Phase A creates the document register and secure storage required before take-off. |
| 2 | Who is the user? | Estimators / project staff uploading PDF plan sets for a project. |
| 3 | Which module owns it? | **Plan Intelligence**. |
| 4 | What data does it own? | `plan_documents` metadata + stored PDF bytes under private upload root. |
| 5 | What data does it reference? | `projects` (required FK). |
| 6 | What may it change? | New Plan Intelligence package (models/services/routes/templates); additive migration; project detail link; docs/milestones/roadmap/state. |
| 7 | What must it not change? | Estimating builder behaviour; Proposals; OCR; CAD; AI extraction; supplier/procurement; estimate insertion; Drawing Set/Revision UI (ADR-012 docs only). |
| 8 | What are the acceptance criteria? | Upload PDF to a project; reject non-PDF; store outside public static; list/view/download; detect text layer (searchable flag); tests pass; no Phase B–G features. |
| 9 | What tests are required? | Upload success; reject non-PDF; searchable flag; list/download; project scoping; existing suite still green. |
| 10 | What documentation must be updated? | FG-002; ADR-012; module plan-intelligence; milestones; roadmap; current-state; project-state; session-handoff; chat-workflow-log; ADR index. |
| 11 | Does it require an ADR? | **Yes** — ADR-012 (Proposed). Related ADR-007/009/010 remain Proposed/governing context. |
| 12 | Does it require a database migration? | **Yes** — additive `plan_documents` table only. |

## Gate decision

| Result | Detail |
|--------|--------|
| **PASS** | Phase A implementation authorized under this Feature Gate |
| Out of scope | OCR, CAD, AI, sheet classification, scale, take-off, estimate mapping, supplier, procurement, revision workflow UI |

## Phase A non-goals (explicit)

- No OCR optimisation  
- No CAD / DWG / DXF / IFC  
- No AI element recognition  
- No supplier integration  
- No procurement  
- No estimate insertion  
- No redesign of Estimating  
- No Drawing Set / Revision management UI (documented in ADR-012 only)  

## Approval

| Role | Decision | Date |
|------|----------|------|
| Joel | Authorized via Milestone 005 implementation prompt | 2026-07-25 |
| Implementation authorized? | **Yes — Phase A only** | 2026-07-25 |

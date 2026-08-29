# The Estimator — Documentation Index

| Attribute | Value |
|-----------|--------|
| Status | Authoritative documentation map |
| Updated | 2026-08-29 |
| Product | The Estimator (Brayman Estimator) |

## Purpose

This folder is the **system of record** for platform vision, architecture, governance, workflow, and session continuity. Chat history is not authoritative.

## Authority layers (do not confuse)

| Layer | Documents | Role |
|-------|-----------|------|
| **Constitutional** | [platform-constitution.md](platform-constitution.md) | Highest-order, rarely changed platform law |
| **Architectural** | [architecture-principles.md](architecture-principles.md), [architecture.md](architecture.md), [adr/](adr/), [modules/](modules/) | Durable rules, structure, decisions, ownership |
| **Operational status** | [project-state-report.md](project-state-report.md), [current-state.md](current-state.md), [session-handoff.md](session-handoff.md) | Milestone state, detailed snapshot, immediate resume |
| **Historical records** | [milestones.md](milestones.md), [chat-workflow-log.md](chat-workflow-log.md) | Append-only milestone and decision history |
| **Reusable templates** | [prompts/](prompts/), [adr/ADR-000-template.md](adr/ADR-000-template.md) | Starting points for Cursor work and ADRs |

## Required reading order (before implementation)

1. [`../AGENTS.md`](../AGENTS.md)
2. [`platform-constitution.md`](platform-constitution.md)
3. [`project-state-report.md`](project-state-report.md)
4. [`current-state.md`](current-state.md)
5. [`platform-vision.md`](platform-vision.md)
6. [`architecture-principles.md`](architecture-principles.md)
7. [`architecture.md`](architecture.md)
8. [`platform-roadmap.md`](platform-roadmap.md)
9. Relevant module document under [`modules/`](modules/)
10. Relevant ADRs under [`adr/`](adr/)
11. Relevant Feature Gate under [`feature-gates/`](feature-gates/)
12. [`session-handoff.md`](session-handoff.md)
13. Relevant prompt template under [`prompts/`](prompts/)

Also read [`platform-governance.md`](platform-governance.md), [`governance/continuity-and-anti-drift.md`](governance/continuity-and-anti-drift.md), [`governance/review-turnover-protocol.md`](governance/review-turnover-protocol.md), and [`definition-of-done.md`](definition-of-done.md) before starting any feature.

## Document catalog

| Document | Purpose | Authority |
|----------|---------|-----------|
| [platform-constitution.md](platform-constitution.md) | Highest-order platform law (Articles 1–12) | **Constitutional** |
| [project-state-report.md](project-state-report.md) | Milestone-level state + template | Operational (mandatory at milestones) |
| [milestones.md](milestones.md) | Append-only milestone history | Historical |
| [prompts/](prompts/) | Reusable Cursor prompt templates | Templates |
| [platform-vision.md](platform-vision.md) | CalibAi vision + current Estimator core | Product intent (Joel-approved CAR-001) |
| [architecture-principles.md](architecture-principles.md) | Numbered durable platform rules | **Architectural** — changes require ADR + Joel |
| [architecture.md](architecture.md) | Current vs intended vs future architecture | Factual for *current*; aspirational elsewhere |
| [architecture/](architecture/) | Domain architecture (Plan Intelligence, Supplier, …) | Future unless marked Current |
| [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md) | CalibAi product/architecture reconciliation | **Approved direction** — not implementation |
| [architecture/M004-plan-intelligence-readiness-report.md](architecture/M004-plan-intelligence-readiness-report.md) | Milestone 004 readiness report | Historical / operational |
| [architecture/document-intelligence.md](architecture/document-intelligence.md) | Document Intelligence (packages, pages, search) | Architecture (M006); partial Current (M007) |
| [architecture/sheet-intelligence.md](architecture/sheet-intelligence.md) | Sheet Intelligence (sheet entities, review) | Architecture (M008); **Implemented (M009)** |
| [architecture/project-document-package.md](architecture/project-document-package.md) | Authoritative record + four core outputs | **Intended** — not implemented |
| [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md) | QuickBooks export pipeline boundary | **Future** — not implemented |
| [architecture/M006-document-intelligence-readiness-report.md](architecture/M006-document-intelligence-readiness-report.md) | Milestone 006 readiness report | Historical / operational |
| [architecture/M008-sheet-intelligence-readiness-report.md](architecture/M008-sheet-intelligence-readiness-report.md) | Milestone 008 readiness report | Historical / operational |
| [architecture/historical-estimates-source-manifest.md](architecture/historical-estimates-source-manifest.md) | Historical estimate source provenance manifest | **Operational / Metadata (Phase A)** |
| [architecture/historical-estimate-ingestion-architecture.md](architecture/historical-estimate-ingestion-architecture.md) | Historical estimate ingestion architecture & audit | **Architecture & Ingestion Specification (Phase A & B Complete)** |
| [architecture/organization-and-calibration-architecture.md](architecture/organization-and-calibration-architecture.md) | Organization & calibration architecture | **Architecture / Governance (Phase A Complete)** |
| [architecture/labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md) | Labour Engine Phase B architecture | **Approved; FG-008 IMPLEMENTED / VERIFIED / LIVE-MIGRATED** (`f2c3d4e5f6a7`) |
| [architecture/organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md) | Organization-Calibrated Pricing Engine architecture | **Approved** — **IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| [feature-gates/FG-008-labour-engine-phase-b.md](feature-gates/FG-008-labour-engine-phase-b.md) | Labour Engine Phase B Feature Gate | **IMPLEMENTED / VERIFIED** |
| [feature-gates/FG-009-organization-calibrated-pricing-engine.md](feature-gates/FG-009-organization-calibrated-pricing-engine.md) | Organization-Calibrated Pricing Engine Feature Gate | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| [adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) | Canonical Labour Task, Production Standard, Calibration Lifecycle | **Accepted** |
| [adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md](adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) | Organization-owned pricing policy and estimate pricing snapshot | **Accepted** |
| [feature-gates/FG-006-historical-estimate-ingestion-phase-b.md](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md) | Historical estimate ingestion Phase B Feature Gate | **Feature Gate (FG-006 Approved & Implemented)** |
| [feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md) | M011 Organization Foundation & Project Commercial Context Feature Gate | **Feature Gate (M011 Approved & Implemented)** |
| [adr/ADR-028-organization-foundation-and-project-commercial-context.md](adr/ADR-028-organization-foundation-and-project-commercial-context.md) | Organization Foundation, Multi-Tenant Boundary, and Project Commercial Context ADR | **Architecture Decision (ADR-028 Accepted)** |
| [platform-governance.md](platform-governance.md) | Decision authority, Feature Gate, ownership, drift stop | **Governing** |
| [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md) | Continuity, anti-drift, preflight, rollover, protected assets | **Governing** |
| [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) | Review Turnover procedure, delta ledger, fresh chat startup | **Governing** |
| [pricing-policy.md](pricing-policy.md) | Labour rate, gross margin, placeholder rules | **Governing** (product policy) |
| [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md) | Ontario contract + warranty template governance; Legal Content Gate | **Governing** |
| [development-workflow.md](development-workflow.md) | Joel → ChatGPT → Cursor lifecycle | **Governing** for AI sessions |
| [documentation-standards.md](documentation-standards.md) | How docs are written and updated | Governing for docs |
| [testing-standards.md](testing-standards.md) | Test expectations | Governing for QA |
| [testing/uat-reference-cases.md](testing/uat-reference-cases.md) | UAT reference projects (e.g. 3415 Roger Stevens) | Governing for UAT |
| [git-workflow.md](git-workflow.md) | Branching, commits, migration safety | Governing for git |
| [definition-of-done.md](definition-of-done.md) | Completion checklist | **Governing** |
| [platform-roadmap.md](platform-roadmap.md) | Completed / current / future / deferred | Planning (keep current) |
| [current-state.md](current-state.md) | Verified snapshot of the repo | Operational (refresh often) |
| [session-handoff.md](session-handoff.md) | Recover after chat/context loss | Continuity (update every session) |
| [chat-workflow-log.md](chat-workflow-log.md) | Memorialized decisions & Cursor outcomes | Continuity (append, do not overwrite) |
| [aiRIA-lessons-adopted.md](aiRIA-lessons-adopted.md) | Transferable process lessons | Reference |
| [adr/](adr/) | Architecture Decision Records | Decisions |
| [feature-gates/](feature-gates/) | Feature Gate documents (pre-implementation) | **Governing** for scope |
| [modules/](modules/) | Per-module ownership & boundaries | Ownership |

## Must update after every feature

At minimum:

- [`current-state.md`](current-state.md)
- [`session-handoff.md`](session-handoff.md)
- [`chat-workflow-log.md`](chat-workflow-log.md) (new entry)
- [`platform-roadmap.md`](platform-roadmap.md) (if status changed)
- [`project-state-report.md`](project-state-report.md) (at milestone completion / major interruption)
- [`milestones.md`](milestones.md) (when a milestone completes)
- Relevant [`modules/*.md`](modules/)
- ADR if a decision changed
- Tests (see definition of done)

## Where to begin

| Role | Start here |
|------|------------|
| New developer / AI agent | Reading order above |
| Resume after a pause | [`session-handoff.md`](session-handoff.md) then [`project-state-report.md`](project-state-report.md) and [`current-state.md`](current-state.md) |
| Propose a feature | [`platform-governance.md`](platform-governance.md) Feature Gate + [`prompts/`](prompts/) |
| Implement in Cursor | [`../AGENTS.md`](../AGENTS.md) + `.cursor/rules/` + filled prompt template |

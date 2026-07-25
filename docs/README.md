# The Estimator — Documentation Index

| Attribute | Value |
|-----------|--------|
| Status | Authoritative documentation map |
| Updated | 2026-07-25 |
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

Also read [`platform-governance.md`](platform-governance.md) and [`definition-of-done.md`](definition-of-done.md) before starting any feature.

## Document catalog

| Document | Purpose | Authority |
|----------|---------|-----------|
| [platform-constitution.md](platform-constitution.md) | Highest-order platform law (Articles 1–12) | **Constitutional** |
| [project-state-report.md](project-state-report.md) | Milestone-level state + template | Operational (mandatory at milestones) |
| [milestones.md](milestones.md) | Append-only milestone history | Historical |
| [prompts/](prompts/) | Reusable Cursor prompt templates | Templates |
| [platform-vision.md](platform-vision.md) | What the product is / is not | Product intent (Joel-approved) |
| [architecture-principles.md](architecture-principles.md) | Numbered durable platform rules | **Architectural** — changes require ADR + Joel |
| [architecture.md](architecture.md) | Current vs intended vs future architecture | Factual for *current*; aspirational elsewhere |
| [architecture/](architecture/) | Domain architecture (Plan Intelligence, Supplier, …) | Future unless marked Current |
| [architecture/M004-plan-intelligence-readiness-report.md](architecture/M004-plan-intelligence-readiness-report.md) | Milestone 004 readiness report | Historical / operational |
| [architecture/document-intelligence.md](architecture/document-intelligence.md) | Document Intelligence (packages, pages, search) | Architecture (M006); partial Current (M007) |
| [architecture/M006-document-intelligence-readiness-report.md](architecture/M006-document-intelligence-readiness-report.md) | Milestone 006 readiness report | Historical / operational |
| [platform-governance.md](platform-governance.md) | Decision authority, Feature Gate, ownership | **Governing** |
| [development-workflow.md](development-workflow.md) | Joel → ChatGPT → Cursor lifecycle | **Governing** for AI sessions |
| [documentation-standards.md](documentation-standards.md) | How docs are written and updated | Governing for docs |
| [testing-standards.md](testing-standards.md) | Test expectations | Governing for QA |
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

# Platform Governance — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **Governing** |
| Updated | 2026-08-25 |

## Highest-order authority

The [Platform Constitution](platform-constitution.md) is the highest-order governance document. Process and Feature Gate rules here implement it; do not repeat the full Constitution.

## Governance operating rule

**PRESERVE → SEARCH → VERIFY → EXECUTE**

- **Existing before new** — search and extend governed documents before creating duplicates.
- **Approved baseline + authorized delta only** — do not implement beyond explicit approval.
- **Preserve** legitimate in-progress documentation and uncommitted state-sync work unless explicitly directed otherwise.

Related mandatory records:

- [milestones.md](milestones.md) — append-only milestone history
- [project-state-report.md](project-state-report.md) — mandatory at milestone completion
- [prompts/](prompts/) — use the prompt library where applicable for Cursor work

## Decision authority

| Role | Authority |
|------|-----------|
| **Joel** | Product vision; construction business rules; priorities; workflow approval; major decisions; milestone completion approval |
| **ChatGPT** | Structured requirements; architectural consistency; module ownership; Cursor prompts; review of Cursor output; roadmap/decision continuity |
| **Cursor** | Repository inspection; scoped implementation; tests; factual handoff reports; no invented requirements |

## Module ownership

- Every feature names an owning module in `docs/modules/`.
- Owned data vs referenced data must be explicit.
- Cross-module changes require documented boundaries and, when material, an ADR.

## Feature approval process

1. Problem and user identified (Joel).
2. ChatGPT drafts requirements + ownership + Feature Gate answers.
3. ADR created when principles, ownership, or schema policy are affected.
4. Bounded Cursor prompt approved.
5. Cursor implements only that scope.
6. Review → corrections → documentation/handoff → Joel milestone approval → commit.

## ADR requirements

Create an ADR when any of the following apply:

- Change to [architecture-principles.md](architecture-principles.md)
- New module or ownership transfer
- Schema / migration strategy change
- Immutability, audit, or financial-control policy change
- External system integration
- Material deviation from roadmap sequence

Template: [adr/ADR-000-template.md](adr/ADR-000-template.md)

## Documentation responsibilities

| Trigger | Update |
|---------|--------|
| Any feature | current-state, session-handoff, chat-workflow-log, definition-of-done items |
| Milestone completion | milestones.md (append), project-state-report.md |
| Cursor implementation | Approved prompt from `docs/prompts/` where applicable; summary in chat-workflow-log |
| Module behaviour/status | `docs/modules/*.md` |
| Roadmap shift | platform-roadmap.md |
| Architecture fact change | architecture.md |
| Principle / Constitution change | architecture-principles.md and/or platform-constitution.md + ADR + Joel approval |

## Architectural review

ChatGPT reviews Cursor reports against principles, module docs, and the approved prompt. Material disagreements stop the merge.

## Scope control

- One objective per Cursor prompt
- No unrelated refactors
- Stop conditions: missing requirements, conflicting docs, unexpected schema need, failing ownership rules

## Change management

- Prefer small feature branches (see [git-workflow.md](git-workflow.md))
- Migrations reviewed before commit
- Historical docs appended (chat-workflow-log), not silently overwritten

## Release readiness

A release is not ready until [definition-of-done.md](definition-of-done.md) is satisfied for in-scope work and Joel approves.

## Prohibited shortcuts

- Implementing before Feature Gate answers exist
- Claiming tests passed without running them
- Generating migrations “just in case”
- Using chat memory as the only record of a decision
- Expanding scope mid-implementation without approval
- Editing application code during a documentation-only task

---

## Context drift and handoff (mandatory stop)

Stop substantive implementation and create or refresh a **verified handoff** when any of the following occur:

- Authoritative baseline cannot be identified
- Approval state is uncertain
- Provenance cannot be established
- Proposed and approved states are being confused
- Previously superseded assumptions reappear
- Existing work is being recreated without verification
- Two substantive user corrections occur because of continuity/context loss
- The system cannot confidently state: baseline, authorized delta, protected state, latest approval, current implementation status, and next action

**No substantive implementation continues until authoritative state is restored.**

Update [session-handoff.md](session-handoff.md), [current-state.md](current-state.md), and [chat-workflow-log.md](chat-workflow-log.md) when stopping for drift.

### Resume procedure (no automatic pull)

```bash
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
```

Then determine whether synchronization is safe. Do **not** automatically `git pull`.

---

## August 2026 product requirements (governance record)

Recorded 2026-08-25 — **documentation only; not implemented**:

| Topic | Document |
|-------|----------|
| Authoritative estimate record + four-output package | [architecture/project-document-package.md](architecture/project-document-package.md) |
| Pricing policy ($65/hr; 15% gross margin) | [pricing-policy.md](pricing-policy.md) |
| QuickBooks pipeline (no API) | [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md) |
| Ontario contract + warranty / Legal Content Gate | [governance/legal-content-and-templates.md](governance/legal-content-and-templates.md) |
| UAT reference case (3415 Roger Stevens Road) | [testing/uat-reference-cases.md](testing/uat-reference-cases.md) |

---

## Feature Gate (required before implementation)

Answer all of the following in the Cursor prompt or an attached Feature Gate document under [`feature-gates/`](feature-gates/):

1. What problem does this solve?
2. Who is the user?
3. Which module owns it?
4. What data does it own?
5. What data does it reference?
6. What may it change?
7. What must it not change?
8. What are the acceptance criteria?
9. What tests are required?
10. What documentation must be updated?
11. Does it require an ADR?
12. Does it require a database migration?

Current Feature Gates: [feature-gates/README.md](feature-gates/README.md).

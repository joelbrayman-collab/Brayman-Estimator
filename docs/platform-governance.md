# Platform Governance — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **Governing** |
| Updated | 2026-09-02 |

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

Detailed governing protocol: [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md) and [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md). The summary rules in this section remain in force and are not superseded.

Stop substantive implementation and create or refresh a **verified handoff** when any of the following occur:

- Authoritative baseline cannot be identified
- Approval state is uncertain
- Provenance cannot be established
- Proposed and approved states are being confused
- Previously superseded assumptions reappear
- Existing work is being recreated without verification
- Two substantive user corrections occur because of continuity/context loss
- The system cannot confidently state: baseline, authorized delta, protected state, latest approval, current implementation status, and next action
- The user invokes the exact phrase `Review Turnover`

**No substantive implementation continues until authoritative state is restored.**

Update [session-handoff.md](session-handoff.md), [current-state.md](current-state.md), and [chat-workflow-log.md](chat-workflow-log.md) when stopping for drift or executing a Review Turnover.

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
| Contract / e-signature / signed Change Order recon | [architecture/contract-esignature-and-signed-change-order.md](architecture/contract-esignature-and-signed-change-order.md) — **COMPLETE / NOT IMPLEMENTED**; recommendation **NATIVE V1**; counsel spec **PREPARED**; **development may proceed under separate governance**; **production activation blocked pending counsel**; no Feature Gate in this pass |
| Field Web / Today + Capture | [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**; [architecture/field-web-today-and-capture.md](architecture/field-web-today-and-capture.md); live current = head `d2e3f4a5b6c7`; gate **NOT CLOSED** |
| Native signing process — counsel review | [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md) — **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL / NOT IMPLEMENTED**; counsel is **not** a general development hold; Change Orders first; Contract later behind Legal Content Gate |
| UAT reference case (3415 Roger Stevens Road) | [testing/uat-reference-cases.md](testing/uat-reference-cases.md) |

**CAR-001** (2026-08-28): CalibAi architectural direction — [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md). Does not authorize product code. M009 is coded Sheets (implemented later under FG-004; not by CAR-001).

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

Current Feature Gates: [feature-gates/README.md](feature-gates/README.md) (FG-004 through FG-013 approved and implemented where noted; **FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / FG-013 CLOSED / OPERATIONAL FOR UAT**; [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**; [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**; [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**; Material Catalogue [ADR-034](adr/ADR-034-canonical-material-identity-and-ownership.md) / [ADR-035](adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) / [ADR-036](adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted**; [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**; [ADR-008](adr/ADR-008-supplier-price-snapshotting.md) **Proposed**; bulk supplier onboarding is a **future pin only** (not a Feature Gate); **Permit Intelligence** architecture is **Accepted** ([ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)); Pass 2 **CLOSED / OPERATIONAL FOR UAT**; not live lookup — [permit-and-approvals-report.md](architecture/permit-and-approvals-report.md) · [permit-rules-library.md](architecture/permit-rules-library.md); **Organization Brand Profile** is **CLOSED / OPERATIONAL FOR UAT** ([organization-brand-profile.md](architecture/organization-brand-profile.md); [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md)); **Change Order document family** is a **future pin only** ([change-order-document-family.md](architecture/change-order-document-family.md); existing Change Order record remains authoritative); real external AI provider **not authorized**; Phase D **not started**).

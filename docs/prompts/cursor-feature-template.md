# Cursor Prompt Template — Feature

Copy this template. Fill every section. Do not authorize scope beyond the Feature Gate.

---

## Title

`<short feature name>`

## Objective

One sentence. Single objective only.

## Business Background

Why this matters for construction estimating / operations.

## User and Workflow

Who uses it and the intended workflow.

## Current Repository State

Branch, HEAD, relevant uncommitted work, pointers to `docs/project-state-report.md` / `docs/current-state.md`.

## Authoritative Documents

List paths that must be read first, including:

- `docs/platform-constitution.md`
- `docs/architecture-principles.md`
- `docs/platform-governance.md` (Feature Gate answers)
- Relevant `docs/modules/*.md`
- Relevant ADRs

## Module Owner

Owning module name and `docs/modules/<file>.md`.

## Data Owned

Records this feature may create/update (owned by the module).

## Data Referenced

Read-only or cross-module references (must not become dual ownership).

## Invariants

Must remain true after the change (locking, snapshots, ownership, etc.).

## Architecture Constraints

Boundaries that must not be crossed.

## Allowed Files or Areas

Explicit paths / packages Cursor may edit.

## Prohibited Files or Areas

Explicit paths Cursor must not edit. Include “do not expand scope” reminder.

## Database and Migration Impact

None | Read-only inspection | Approved migration (link migration template / ADR).  
If none: **do not generate migrations**.

## Security and Authorization Impact

Authn/authz, secrets, multi-user implications. Mark unknowns **To be verified**.

## Acceptance Criteria

Checklist of observable outcomes.

## Required Tests

Focused tests + full suite expectation.

## Required Documentation Updates

e.g. current-state, module doc, roadmap, handoff, chat-workflow-log, project-state-report, milestones if applicable.

## Required Validation Commands

Exact commands (prefer Cursor Terminal).

## Stop Conditions

Stop and report if: missing requirements, ownership conflict, unapproved migration need, incidental behaviour change, failing Constitution/principles.

## Final Report Format

Files changed · assumptions · risks · commands · exact results · docs updated · next step.

## Suggested Commit Message

`<imperative summary>`

## Do Not Commit Automatically

Commit only when Joel explicitly requests it.

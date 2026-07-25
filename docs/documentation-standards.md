# Documentation Standards — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Governing for documentation |
| Updated | 2026-07-25 |

## Required headings / metadata

Every substantive doc should include a status table near the top:

- Status
- Updated (ISO date)
- Optional: Approval / Evidence baseline

## Status labels

Use one of:

| Label | Meaning |
|-------|---------|
| Governing | Binding process/architecture rule |
| Current / Implemented | Exists in code now |
| Proposed / Intended | Approved direction, not built |
| Deferred | Explicitly postponed |
| Deprecated | Superseded; keep for history |
| Continuity | Operational recovery artifact |
| Reference | Guidance, not policy |

## Dates and versioning

- Prefer `YYYY-MM-DD` update stamps.
- Append to logs (`chat-workflow-log.md`); do not silently rewrite history.
- Milestone/commit hashes when recording completed work.

## Naming conventions

- `docs/` kebab-case filenames
- ADRs: `ADR-NNN-short-title.md`
- Modules: `docs/modules/<module>.md`

## Distinguishing material

When a document mixes facts and plans, use explicit section labels:

- **Current**
- **Proposed / Intended**
- **Future**
- **Deferred**

## When to update

| Event | Documents |
|-------|-----------|
| Feature complete | current-state, session-handoff, chat-workflow-log, roadmap, module doc, DoD checklist |
| Architecture decision | ADR + architecture.md / principles if needed |
| Governance change | platform-governance.md + AGENTS.md / Cursor rules if behaviour changes |

## Prohibitions

- No unsupported claims (“fully secure”, “production ready”) without evidence
- When documenting **implemented** architecture, **cite code paths**
- Do not invent AiRIA repository findings; use [aiRIA-lessons-adopted.md](aiRIA-lessons-adopted.md) lessons only unless AiRIA is present in-repo

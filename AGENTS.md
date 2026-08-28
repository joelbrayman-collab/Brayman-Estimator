# AGENTS.md — Operating Guide for AI Development Agents

| Attribute | Value |
|-----------|--------|
| Status | Governing for AI agents (Cursor, etc.) |
| Updated | 2026-08-28 |
| Product | The Estimator |

## Before you edit

1. Read this file.
2. Read `docs/platform-constitution.md` (highest-order rules).
3. Read `docs/project-state-report.md` for current **milestone-level** state.
4. Read `docs/current-state.md` and `docs/session-handoff.md` (handoff is for immediate resume — **not** a substitute for milestone state).
5. Read `docs/architecture-principles.md`, `docs/platform-governance.md`, and `docs/governance/continuity-and-anti-drift.md`.
6. Read `docs/architecture.md` and the relevant `docs/modules/*.md`.
7. Use a template from `docs/prompts/` for the approved Cursor prompt.
8. Inspect the repository (`git status`, relevant code paths) **before** changing files.
9. Confirm the Feature Gate answers exist for the approved objective.

Authoritative index: [`docs/README.md`](docs/README.md).

## Hard rules

- Preserve existing functionality; do not change it incidentally.
- Follow module ownership; do not invent product policy.
- Avoid scope expansion; one objective at a time.
- **Never generate or edit Alembic migrations casually.** Migrations require explicit approval in the prompt.
- Do not modify models/schemas unless the approved scope says so.
- Run tests; report exact commands and results.
- Update documentation: current-state, session-handoff, chat-workflow-log, roadmap/module docs as applicable; update `docs/milestones.md` and `docs/project-state-report.md` when a milestone completes or at major interruption.
- Provide a complete implementation report (files changed, decisions, risks, tests).
- **Stop** when requirements conflict or are missing—do not guess.
- **Never claim** work or test results that were not performed.
- Chat history is not the system of record; repository docs are.
- Follow the [Continuity & Anti-Drift Protocol](docs/governance/continuity-and-anti-drift.md). AI memory is never authoritative project state.

## Workflow

Follow `docs/development-workflow.md` (Joel → ChatGPT → Cursor). Implement only the approved Cursor prompt scope. Record the approved prompt summary in `docs/chat-workflow-log.md`.

## Definition of done

See `docs/definition-of-done.md`. Do not declare complete without it.

## Cursor project rules

See `.cursor/rules/` — concise enforcement; full policy lives in `docs/`.

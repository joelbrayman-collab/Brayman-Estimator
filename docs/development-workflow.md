# Development Workflow — Joel → ChatGPT → Cursor

| Attribute | Value |
|-----------|--------|
| Status | **Governing** |
| Updated | 2026-08-28 |

## Lifecycle

1. **Joel** identifies the business need.
2. **Joel and ChatGPT** clarify workflow and business rules.
3. **ChatGPT** documents architecture and ownership (module docs / ADR / Feature Gate).
4. **Before Cursor implementation:** choose the correct template from [prompts/](prompts/); complete it using the approved Feature Gate; record the **approved prompt summary** in [chat-workflow-log.md](chat-workflow-log.md).
5. **ChatGPT** prepares / finalizes the **bounded** Cursor implementation prompt.
6. **Cursor** inspects the repository before editing.
7. **Cursor** implements **only** the approved scope.
8. **Cursor** runs focused and full tests.
9. **Cursor** reports changes, assumptions, risks, and exact test results.
10. **ChatGPT** reviews the implementation report.
11. Corrections are completed before commit.
12. **After implementation:** update documentation, roadmap, and handoff; update [milestones.md](milestones.md) where appropriate; update [project-state-report.md](project-state-report.md); identify the **next approved prompt** or explicitly state that none is approved.
13. **Joel** approves the milestone.
14. The work is committed with a descriptive message (and pushed when Joel directs).

## Cursor prompt requirements

Start from [prompts/](prompts/). Every implementation prompt should include:

- Objective (one)
- Feature Gate answers (or link)
- Allowed files / areas
- Prohibited files / areas
- Tests required
- Documentation required
- Stop conditions
- Authoritative document references (including [platform-constitution.md](platform-constitution.md) where relevant)

## Stop conditions (Cursor must stop and report)

- Requirements conflict with architecture principles or module ownership
- Approved scope is insufficient to implement safely
- A migration appears necessary but was not approved
- Existing functionality would be broken or changed incidentally
- Tests cannot be run and the reason is unclear
- Ambiguous construction business rule (Joel decision needed)
- **Context drift** — see [platform-governance.md](platform-governance.md#context-drift-and-handoff-mandatory-stop) and [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)

**Do not guess product policy.**

## Resume after pause

Use the governed resume procedure in [session-handoff.md](session-handoff.md). Compare `HEAD` to `origin/main` before any sync; **do not automatically pull**.

## Terminal usage

Prefer **Cursor Terminal** for git, pytest, Flask, and documentation commands inside this repository. Use **Mac Terminal** only for OS-level tasks outside the repo. Always name the terminal explicitly when giving commands.

## Chat conversation naming

To prevent cross-project context confusion (e.g. between Brayman-Estimator and AiRIA), all chat conversation titles in this workspace must start with `BRAYMAN — <Topic>`.

## Related

- [platform-constitution.md](platform-constitution.md)
- [platform-governance.md](platform-governance.md)
- [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)
- [definition-of-done.md](definition-of-done.md)
- [prompts/](prompts/)
- [project-state-report.md](project-state-report.md)
- [milestones.md](milestones.md)
- [chat-workflow-log.md](chat-workflow-log.md)
- [session-handoff.md](session-handoff.md)
- [../AGENTS.md](../AGENTS.md)

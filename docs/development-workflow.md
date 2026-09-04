# Development Workflow — Joel → ChatGPT → Cursor

| Attribute | Value |
|-----------|--------|
| Status | **Governing** |
| Updated | 2026-09-04 |

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

## CalibAi development response continuity

Permanent convention: [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md#chat-title-continuity-convention-permanent).

Every CalibAi development assessment, implementation review, UAT review, stopping-report review, governance response, or turnover response must:

- begin with the exact active ChatGPT development chat title in bold;
- end with `END — <exact active chat title>` **after** any complete ready-to-paste Cursor prompt;
- end with the next complete ready-to-paste Cursor prompt unless Joel explicitly states that no prompt is required.

Do **not** weaken this rule. Cursor/IDE workspace titles remain `BRAYMAN — <Topic>`.

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

## Resume after pause / Review Turnover

Use the governed resume procedure in [session-handoff.md](session-handoff.md) or the formal rollover procedure in [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) (`Review Turnover`). Compare `HEAD` to `origin/main` before any sync; **do not automatically pull**.

## Terminal usage

Prefer **Cursor Terminal** for git, pytest, Flask, and documentation commands inside this repository. Use **Mac Terminal** only for OS-level tasks outside the repo. Always name the terminal explicitly when giving commands.

## Chat conversation naming

Two title systems remain in force and must not be collapsed:

- **Cursor / IDE workspace titles** must start with `BRAYMAN — <Topic>` to prevent cross-project mixing (e.g. AiRIA).
- **ChatGPT development chat titles** are originating-conversation traceability metadata. Use the exact title. See [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md#chat-title-continuity-convention-permanent).

## Related

- [platform-constitution.md](platform-constitution.md)
- [platform-governance.md](platform-governance.md)
- [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)
- [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md)
- [definition-of-done.md](definition-of-done.md)
- [prompts/](prompts/)
- [project-state-report.md](project-state-report.md)
- [milestones.md](milestones.md)
- [chat-workflow-log.md](chat-workflow-log.md)
- [session-handoff.md](session-handoff.md)
- [../AGENTS.md](../AGENTS.md)

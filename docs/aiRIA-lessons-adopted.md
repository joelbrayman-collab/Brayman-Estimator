# Lessons Adopted from the AiRIA Development Process

| Attribute | Value |
|-----------|--------|
| Status | Reference |
| Updated | 2026-07-25 |
| Source | Lessons listed in the Estimator governance foundation prompt (authoritative for this document). This repository does **not** contain the AiRIA codebase; no claim is made that AiRIA was inspected here. |

## Transferable lessons

1. Establish architecture before expansion.
2. Define ownership boundaries.
3. Create immutable architectural rules.
4. Maintain a current roadmap.
5. Document every milestone.
6. Preserve implementation prompts and outcomes.
7. Use small, bounded feature branches.
8. Require tests before completion.
9. Separate planning, implementation, review, and approval.
10. Maintain reliable session handoffs.
11. Do not use chat memory as the sole system of record.
12. Conduct workflow validation before adding large new modules.
13. Distinguish existing functionality from planned functionality.
14. Prevent accidental scope expansion.
15. Document deferred ideas rather than implementing them prematurely.

## Improvements The Estimator adopts from the beginning

| Practice | Location |
|----------|----------|
| Repository-based chat workflow log | [chat-workflow-log.md](chat-workflow-log.md) |
| Standard session handoff | [session-handoff.md](session-handoff.md) |
| Cursor project rules | [../.cursor/rules/](../.cursor/rules/) |
| Mandatory documentation updates | [definition-of-done.md](definition-of-done.md) · [documentation-standards.md](documentation-standards.md) |
| Feature Gate | [platform-governance.md](platform-governance.md) |
| ADR template from the outset | [adr/ADR-000-template.md](adr/ADR-000-template.md) |
| Explicit migration review | [architecture-principles.md](architecture-principles.md) Rule 7 · [git-workflow.md](git-workflow.md) |
| Current-state document | [current-state.md](current-state.md) |
| Agent operating guide | [../AGENTS.md](../AGENTS.md) |

## Related

- [platform-governance.md](platform-governance.md)
- [development-workflow.md](development-workflow.md)

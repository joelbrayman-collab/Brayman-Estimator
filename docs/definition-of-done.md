# Definition of Done — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **Governing** |
| Updated | 2026-07-25 |

A feature is **not complete** until all applicable items are true:

1. Requirements are approved (Feature Gate answered).
2. Ownership is documented (`docs/modules/`).
3. Code is implemented within approved scope.
4. Focused tests pass (actually run).
5. Full tests pass (actually run), or an explicit Joel-approved exception is recorded.
6. Migrations are reviewed where applicable.
7. Documentation is updated.
8. Roadmap is updated.
9. Current-state document is updated.
10. Chat workflow log has a new entry.
11. Session handoff is updated.
12. Diff contains no unrelated changes.
13. Commit message is prepared.
14. Joel approves completion.
15. **Platform Constitution** compliance confirmed ([platform-constitution.md](platform-constitution.md)).
16. **Milestone entry** updated when a milestone is completed ([milestones.md](milestones.md)).
17. **Project State Report** updated ([project-state-report.md](project-state-report.md)).
18. **Approved Cursor prompt summary** recorded in [chat-workflow-log.md](chat-workflow-log.md).
19. **Next approved step** identified (or explicitly: none approved).
20. **Prompt template** used (from [prompts/](prompts/)), or reason documented why not.

Documentation-only sprints still require items 1–2, 7–13, and 15–20 as applicable, and must not change application behaviour.

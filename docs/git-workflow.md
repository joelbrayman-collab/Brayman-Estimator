# Git Workflow — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Governing |
| Updated | 2026-07-25 |

## Requirements

1. Prefer a **clean working tree** before starting a feature (or explicitly document intentional WIP).
2. **One feature per branch.**
3. Recommended branch naming: `cursor/<short-feature-slug>` or `feature/<short-feature-slug>`.
4. **No unrelated changes** in the same commit.
5. **Inspect the diff** before commit (`git diff`, `git status`).
6. **No generated migrations without review** (Rule 7).
7. Descriptive commit messages focused on why.
8. Merge readiness: tests pass, docs updated, Feature Gate satisfied, Joel approval for milestones.

## Commit message standard

- Imperative mood preferred (“Add …”, “Fix …”, “Document …”)
- One primary intent per commit
- Reference module or governance topic when helpful

## Migration safety

- Migrations only for approved schema work
- Review generated SQL / ops before commit
- If local DB revision diverges from repository history: stop, document in session-handoff, recover deliberately (backup DB first). Do not casually `stamp` without understanding.

## Recovery when local migration state differs

1. Backup `instance/*.db`
2. Record `flask db current` / alembic heads in session-handoff
3. Compare to `migrations/versions/`
4. Ask Joel/ChatGPT before stamp/upgrade/downgrade decisions

## Related

- Local branches historically used `cursor/*` naming (see `git branch -vv`)

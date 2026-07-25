# Current State — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Operational snapshot |
| Updated | 2026-07-25 |
| Evidence | Local repository inspection |

Keep short. Refresh often. Mark unverified facts explicitly.

## Baseline

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD (verified) | `29d1ba9` — *Complete Estimator governance baseline and prompt library* |
| Pre-governance base | `7b8d5ca` |
| Remote | Local `main` **ahead of `origin/main` by 1**; commit **committed locally**, **not yet pushed** (verified 2026-07-25) |
| Working tree | Clean immediately after `29d1ba9`; re-check `git status` after any doc updates |
| App | Flask factory `app.create_app` |
| DB default | SQLite `brayman_estimator.db` under instance |
| Governance | **Active** — Constitution, docs, AGENTS.md, Cursor rules, prompt library committed at `29d1ba9` (39 governance/documentation files; no app/migration/test changes in that commit) |

## Implemented capabilities (evidenced)

- Clients CRUD (`app/routes/clients.py`, `Client` model)
- Projects CRUD linked to clients (`app/routes/projects.py`, `Project` model)
- Cost Items library (`app/routes/cost_library.py`)
- Assemblies + assembly items (`app/routes/assemblies.py`)
- Estimates with versions, sections, line items; locking for certain statuses
- Proposal templates; proposals with snapshot sections/lines; browser preview; PDF generation
- Change Orders under Project Controls package
- Dashboard summarizing recent activity
- Branding assets / app shell navigation

## Incomplete / placeholder (nav disabled)

From `app/navigation.py`: Purchase Orders, Job Costing, Reports, AI Assistant, Settings — **not implemented** as live endpoints.

## Local branches visible

| Branch | Note |
|--------|------|
| `main` | Current |
| `cursor/project-controls-change-orders` | Merged via PR #3 |
| `cursor/proposal-templates-pdf-generation` | Historical |
| `cursor/estimate-sections-line-items` | Historical |
| `cursor/sidebar-navigation-refinement` | Historical |
| `cursor/constructos-branding-engine` | Local checkpoint |

## Migrations

- Versions present through change orders (`e8b2c4d15a90` head observed via Alembic ScriptDirectory).
- Live database revision: **To be verified**.

## Tests

- Suite under `tests/`
- Last verified: `./venv/bin/python -m pytest -q` → **78 passed**, 43 warnings (2026-07-25)
- Not re-run for documentation-only milestone-record updates unless required

## Known risks

- Development `SECRET_KEY` hard-coded in `app/__init__.py`
- Change-order audit trail UI marked future in template
- Proposal Accepted status exists; formal acceptance → project creation snapshot flow incomplete as product
- Live Alembic `current` still unverified

## Current milestone

**Milestone 001 — Platform Governance Foundation:** **Completed** at `29d1ba9`.

**Next:** Milestone 002 — Product Architecture Review and Next-Milestone Selection (planning / Feature Gate — **not** implementation yet).

## Recommended next steps

1. Push `29d1ba9` to `origin/main` when Joel directs.
2. Product Architecture Review: compare implemented workflows to product vision; identify risks/gaps.
3. Select and Feature-Gate **one** next product milestone (no specific product feature approved yet).

## Related

- [session-handoff.md](session-handoff.md)
- [project-state-report.md](project-state-report.md)
- [milestones.md](milestones.md)
- [platform-roadmap.md](platform-roadmap.md)
- [architecture.md](architecture.md)

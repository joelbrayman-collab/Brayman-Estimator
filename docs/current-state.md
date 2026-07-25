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
| HEAD (at M002 start) | `71e2754` — governance baseline + milestone record; tag `v0.1-governance-baseline` |
| Pre-governance base | `7b8d5ca` |
| Remote | In sync with `origin/main` at M002 start; M002 docs uncommitted until Joel directs commit |
| Working tree | Dirty with Milestone 002 documentation (confirm `git status`) |
| App | Flask factory `app.create_app` |
| DB default | SQLite `brayman_estimator.db` under instance |
| Governance | **Active** — FG-001 + ADR-001–004 drafted for Proposals |

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
- Live database revision: re-verify per environment (`flask db current`).

## Tests

- Suite under `tests/`
- Last verified: `./venv/bin/python -m pytest -q` → **78 passed**, 43 warnings (2026-07-25)
- Not re-run for Milestone 002 documentation-only work

## Known risks

- Development `SECRET_KEY` hard-coded in `app/__init__.py`
- Change-order audit trail UI marked future in template
- **Accepted proposals remain editable** until Milestone 003 (ADR-002)
- Proposal estimate FK `ON DELETE` model vs migration mismatch
- Formal acceptance → project creation incomplete

## Current milestone

**Milestone 002 — Product Architecture Review:** FG-001 + ADR-001–004 drafted (docs).

**Recommended next implementation:** Milestone 003 — Accepted Proposal Immutability (awaiting Joel approval).

## Recommended next steps

1. Joel reviews [FG-001](feature-gates/FG-001-proposals-module.md) and ADR-001–004.
2. Commit Milestone 002 documentation when directed.
3. Approve and Feature-Gate Milestone 003 (immutability) before any code changes.

## Related

- [session-handoff.md](session-handoff.md)
- [project-state-report.md](project-state-report.md)
- [milestones.md](milestones.md)
- [platform-roadmap.md](platform-roadmap.md)
- [feature-gates/FG-001-proposals-module.md](feature-gates/FG-001-proposals-module.md)
- [architecture.md](architecture.md)

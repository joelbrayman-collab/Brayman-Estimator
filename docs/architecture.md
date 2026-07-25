# Architecture — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Living architecture map |
| Updated | 2026-07-25 |
| Evidence baseline | `main` @ `7b8d5ca` (verified locally) |

**Cite code paths for implemented claims.** Distinctions below are mandatory.

---

## Current Architecture (implemented)

### Application entry

| Piece | Path |
|-------|------|
| WSGI / run entry | [`app.py`](../app.py) — `create_app()`, `app.run(debug=True)` |
| App factory | [`app/__init__.py`](../app/__init__.py) — Flask + SQLAlchemy + Flask-Migrate |
| Default DB URI | SQLite `sqlite:///brayman_estimator.db` (instance path via Flask) |
| Dependencies | [`requirements.txt`](../requirements.txt) |

### Blueprints / packages registered

From [`app/__init__.py`](../app/__init__.py):

| Blueprint | Package / module |
|-----------|------------------|
| `main_bp` | `app/routes/main.py` |
| `clients_bp` | `app/routes/clients.py` |
| `projects_bp` | `app/routes/projects.py` |
| `cost_library_bp` | `app/routes/cost_library.py` |
| `assemblies_bp` | `app/routes/assemblies.py` |
| `estimates_bp` | `app/routes/estimates.py` |
| `proposal_templates_bp` | `app/routes/proposal_templates.py` |
| `proposals_bp` | `app/routes/proposals.py` |
| `project_controls_bp` | `app/project_controls/` |

Shell context: [`app/shell.py`](../app/shell.py). Navigation SSOT: [`app/navigation.py`](../app/navigation.py).

### Models (SQLAlchemy)

Registered in [`app/models/__init__.py`](../app/models/__init__.py):

| Domain | Models | Path |
|--------|--------|------|
| CRM-ish | `Client` | `app/models/client.py` |
| Projects | `Project` | `app/models/project.py` |
| Cost library | `CostItem` | `app/models/cost_item.py` |
| Assemblies | `Assembly`, `AssemblyItem` | `app/models/assembly.py` |
| Estimating | `Estimate`, `EstimateVersion`, `EstimateSection`, `EstimateLineItem` | `app/models/estimate.py` |
| Proposals | `ProposalTemplate`, `Proposal`, `ProposalSection`, `ProposalLineItem` | `app/models/proposal.py` |
| Project controls | `ChangeOrder`, `ChangeOrderItem` | `app/project_controls/models.py` |

Notable behaviours evidenced in code/tests:

- Estimate **versions** with lock statuses (`AUTO_LOCK_VERSION_STATUSES` in `app/models/estimate.py`).
- Proposals built as **snapshots** from estimate versions (`build_proposal_snapshot` exported from `app/services/`); tests in `tests/test_proposal_snapshots.py` assert independence from later estimate edits.
- Proposal statuses include `Accepted` among others (`PROPOSAL_STATUSES` in `app/models/proposal.py`).
- Change Orders package under `app/project_controls/` with its own routes/services/repository/pdf.

### Services / repositories

| Layer | Paths |
|-------|-------|
| Services | `app/services/estimates.py`, `estimate_builder.py`, `proposals.py`, `proposal_pdf.py` |
| Project controls | `app/project_controls/services.py`, `repository.py`, `pdf.py` |
| Generic repositories package | `app/repositories/` (present; inspect before assuming usage) |

### Templates & static assets

- Templates: `app/templates/` (clients, projects, estimates, proposals, proposal_templates, assemblies, cost_library, project_controls, dashboard, base, partials)
- Static: `app/static/` (css, js, branding)

### Migrations

- Flask-Migrate / Alembic under [`migrations/`](../migrations/)
- Config: `migrations/alembic.ini`, `migrations/env.py`
- Version scripts in `migrations/versions/` (clients/projects, cost items, assemblies, estimates/versions, sections/lines, proposals/templates, proposal snapshot sections, change orders)
- ScriptDirectory heads observed locally: **`e8b2c4d15a90`** (change orders). Live DB alembic `current` should be verified with Flask-Migrate in an app context before relying on it.

### Tests

- Location: [`tests/`](../tests/)
- Collected locally: **78 tests** (`pytest --collect-only`, 2026-07-25)
- Coverage areas: assemblies, estimates/builder, proposals, proposal snapshots/preview/pdf, change orders

### Current module relationships (simplified)

```text
Client ──< Project ──< Estimate ──< EstimateVersion ──< Sections/Lines
                         │                │
                         │                └──> Proposal (snapshot) ── Sections/Lines
                         │
                         └── ChangeOrder (optional estimate_version FK)
```

Navigation also shows **disabled** placeholders: Purchase Orders, Job Costing, Reports, AI Assistant, Settings (`app/navigation.py`).

### Known architectural risks / incomplete boundaries

- Root [`README.md`](../README.md) was empty before governance sprint (now pointers added).
- No prior `docs/` governance (this foundation addresses that).
- Change Order detail template notes future audit trail UI (`app/templates/project_controls/change_orders/detail.html`).
- Hard-coded `SECRET_KEY` in `create_app` (development default) — production secret handling is an open operational concern.
- Flask-Login is in requirements; depth of authz usage is **to be verified** before claiming multi-user security.
- Proposal “Accepted” status exists; full acceptance → project budget snapshot workflow is **not** documented as complete product (see Intended).
- CRM is effectively Clients + Projects, not a full CRM suite.

---

## Intended Architecture

Aligns with [platform-vision.md](platform-vision.md) and [architecture-principles.md](architecture-principles.md):

- Explicit module ownership documents (CRM, Estimating, Proposals, Projects, later Project Controls expansions)
- Immutable accepted-proposal snapshots feeding project creation (Rule 3–4)
- Auditable financially significant actions (Rule 6)
- Service boundaries for cross-module access (Rule 11)
- Governance Feature Gate before net-new modules

---

## Future Architecture

Planned only when approved (see [platform-roadmap.md](platform-roadmap.md)):

- Scheduling, Purchasing, Job Costing, Invoicing
- QuickBooks / accounting integration
- Historical estimating intelligence
- Electronic signature / formal proposal acceptance workflows
- Field reporting (daily reports, timesheets)

Do **not** describe these as existing.

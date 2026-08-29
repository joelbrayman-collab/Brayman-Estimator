# Architecture — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Living architecture map |
| Updated | 2026-08-29 |
| Evidence baseline | `main` @ CAR-001 adoption (see git); Plan Intelligence Current claims evidenced in `app/plan_intelligence/` and migration `a7c8e9f0b1d2` |

**Cite code paths for implemented claims.** Distinctions below are mandatory. CalibAi lifecycle architecture: [architecture/CAR-001-calibai-product-architecture-reconciliation.md](architecture/CAR-001-calibai-product-architecture-reconciliation.md).

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
| `plan_intelligence_bp` | `app/plan_intelligence/` |

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
| Plan Intelligence | `DrawingPackage`, `DrawingRevision`, `PlanDocument`, `PlanPage`, `ProcessingAttempt`, `ProcessingResult`, `PlanAuditEvent` | `app/plan_intelligence/models.py` |

Notable behaviours evidenced in code/tests:

- Estimate **versions** with lock statuses (`AUTO_LOCK_VERSION_STATUSES` in `app/models/estimate.py`).
- Proposals built as **snapshots** from estimate versions (`build_proposal_snapshot` exported from `app/services/`); tests in `tests/test_proposal_snapshots.py` assert independence from later estimate edits.
- Proposal statuses include `Accepted` among others (`PROPOSAL_STATUSES` in `app/models/proposal.py`).
- Change Orders package under `app/project_controls/` with its own routes/services/repository/pdf.
- Plan Intelligence Phase A upload/storage (M005) and Document Indexing (M007): pages, processing provenance, archive-over-delete, relational search (`app/plan_intelligence/`; tests `tests/test_plan_upload.py`, `tests/test_plan_indexing.py`). Sheets **implemented** (M009). Scale/measurement **implemented** (M010).

### Services / repositories

| Layer | Paths |
|-------|-------|
| Services | `app/services/estimates.py`, `estimate_builder.py`, `proposals.py`, `proposal_pdf.py` |
| Project controls | `app/project_controls/services.py`, `repository.py`, `pdf.py` |
| Plan Intelligence | `app/plan_intelligence/services.py`, `processing.py`, `extraction.py`, `storage.py`, `packages.py`, `audit.py` |
| Generic repositories package | `app/repositories/` (present; inspect before assuming usage) |

### Templates & static assets

- Templates: `app/templates/` (clients, projects, estimates, proposals, proposal_templates, assemblies, cost_library, project_controls, plan_intelligence, dashboard, base, partials)
- Static: `app/static/` (css, js, branding)

### Migrations

- Flask-Migrate / Alembic under [`migrations/`](../migrations/)
- Config: `migrations/alembic.ini`, `migrations/env.py`
- Version scripts in `migrations/versions/` (clients/projects through change orders, `plan_documents`, Document Intelligence M007)
- Alembic graph head and live development/UAT current: **`f2c3d4e5f6a7`** (FG-008). Verify `flask db current` per environment before relying on it.

### Tests

- Location: [`tests/`](../tests/)
- Collected locally: **78 tests** (`pytest --collect-only`, 2026-07-25)
- Coverage areas: assemblies, estimates/builder, proposals, proposal snapshots/preview/pdf, change orders, plan upload, plan indexing

### Current module relationships (simplified)

```text
Client ──< Project ──< Estimate ──< EstimateVersion ──< Sections/Lines
              │            │                │
              │            │                └──> Proposal (snapshot) ── Sections/Lines
              │            │
              │            └── ChangeOrder (optional estimate_version FK)
              │
              └── PlanDocument / DrawingPackage (Plan Intelligence; M005–M007)
```

Navigation also shows **disabled** placeholders: Purchase Orders, Job Costing, Reports, AI Assistant, Settings (`app/navigation.py`).

### Known architectural risks / incomplete boundaries

- Root [`README.md`](../README.md) was empty before governance sprint (now pointers added).
- No prior `docs/` governance (this foundation addresses that).
- Change Order detail template notes future audit trail UI (`app/templates/project_controls/change_orders/detail.html`).
- Hard-coded `SECRET_KEY` in `create_app` (development default) — production secret handling is an open operational concern.
- Flask-Login is in `requirements.txt` and **unused** in `app/` as of CAR-001 (no User model, no LoginManager). Multi-user security is **not implemented**.
- Proposal “Accepted” status exists; full acceptance → project budget snapshot workflow is **not** documented as complete product (see Intended).
- CRM is effectively Clients + Projects, not a full CRM suite.

---

## Intended Architecture

Aligns with [platform-vision.md](platform-vision.md), [CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md), and [architecture-principles.md](architecture-principles.md):

- `Project` remains the CalibAi lifecycle hub ([ADR-019](adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted**)
- Explicit module ownership documents (CRM, Estimating, Proposals, Projects, Plan Intelligence, proposed BUILD, Supplier Catalogue, Project Controls expansions)
- Immutable accepted-proposal snapshots feeding project creation (Rule 3–4)
- Auditable financially significant actions (Rule 6)
- Service boundaries for cross-module access (Rule 11)
- Governance Feature Gate before net-new modules
- Human-approved, source-traceable take-off before estimate insertion (ADR-005/006 — Proposed)
- Supplier price snapshots on consumption (ADR-008 — Proposed)

---

## Future Architecture

Planned only when approved (see [platform-roadmap.md](platform-roadmap.md)):

### Differentiating pillars (architecture drafted; **not implemented**)

- [Plan Intelligence and Automated Take-Off](architecture/plan-intelligence-and-automated-takeoff.md) — Phases A–G
- [Supplier Catalogue, Inventory and Pricing](architecture/supplier-catalogue-inventory-pricing.md) — Phases E–F
- Procurement / purchase-order preparation (nav placeholder only today)

### Other future capabilities

- **BUILD / MONITOR / LEARN** — [CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md); BUILD boundary [ADR-020](adr/ADR-020-build-module-boundary.md) (**Accepted**, not implemented)
- **Field / shared API** — [ADR-022](adr/ADR-022-field-client-and-shared-api.md) (**Accepted** direction; not implemented)
- **Project document package** (internal breakdown, customer estimate, QuickBooks export, Ontario contract + warranty) — [architecture/project-document-package.md](architecture/project-document-package.md)
- Scheduling, Job Costing, Invoicing
- QuickBooks / accounting integration — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- Historical estimating intelligence (LEARN; [ADR-024](adr/ADR-024-learn-recommendation-boundary.md))
- **Labour Engine Phase B** — [labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md); [FG-008](feature-gates/FG-008-labour-engine-phase-b.md) **IMPLEMENTED / VERIFIED / LIVE-MIGRATED** (foundation operational for UAT). Selling-price application remains out of scope of FG-008.
- **Organization-Calibrated Pricing Engine** — [organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md); [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED**. ADR-025 **Accepted**; ADR-030 **Accepted**.
- Electronic signature / formal proposal acceptance workflows
- CAD ingestion (Phase G; PDF-first per ADR-009)

Do **not** describe these as existing.

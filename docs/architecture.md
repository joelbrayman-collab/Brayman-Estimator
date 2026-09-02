# Architecture — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Living architecture map |
| Updated | 2026-09-02 |
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
| `labour_engine_bp` | `app/routes/labour_engine.py` |
| `pricing_engine_bp` | `app/routes/pricing_engine.py` |
| `api_v1_bp` | `app/routes/api_v1.py` |
| `build_bp` | `app/routes/build.py` |

Shell context: [`app/shell.py`](../app/shell.py). Navigation SSOT: [`app/navigation.py`](../app/navigation.py).

### Models (SQLAlchemy)

Registered in [`app/models/__init__.py`](../app/models/__init__.py):

| Domain | Models | Path |
|--------|--------|------|
| CRM-ish | `Client` | `app/models/client.py` |
| Projects | `Project` | `app/models/project.py` |
| Cost library | `CostItem` | `app/models/cost_item.py` — org costing record; **not** CalibAi material identity ([material-catalogue-architecture.md](architecture/material-catalogue-architecture.md) Intended) |
| Assemblies | `Assembly`, `AssemblyItem` | `app/models/assembly.py` |
| Estimating | `Estimate`, `EstimateVersion`, `EstimateSection`, `EstimateLineItem` | `app/models/estimate.py` |
| Proposals | `ProposalTemplate`, `Proposal`, `ProposalSection`, `ProposalLineItem` | `app/models/proposal.py` |
| Project controls | `ChangeOrder`, `ChangeOrderItem` | `app/project_controls/models.py` |
| Plan Intelligence | `DrawingPackage`, `DrawingRevision`, `PlanDocument`, `PlanPage`, `ProcessingAttempt`, `ProcessingResult`, `PlanAuditEvent`, `PlanSheet`, `PlanSheetPage`, `PlanSheetSuggestion`, `PlanScaleCalibration`, `PlanMeasurement`, `TakeoffExtractionRun`, `TakeoffCandidate`, `TakeoffPackage`, `TakeoffPackageItem` | `app/plan_intelligence/models.py` |
| Labour Engine | `LabourTask`, `LabourTaskMapping`, `ProductionRateStandard`, `DirectLabourCostRateStandard`, `LabourCalibrationCandidate`, `EstimateLabourSnapshot`, `LabourAuditEvent` | `app/models/labour_engine.py` |
| BUILD | `FieldCaptureEvent`, `FieldCaptureOriginal`, `FieldCaptureDerivedCandidate` | `app/models/build.py` — FG-020 **CLOSED / OPERATIONAL FOR UAT** |
| Pricing Engine | `OrganizationPricingPolicy`, `EstimatePricingSnapshot`, `PricingAuditEvent` | `app/models/pricing_engine.py` |

Notable behaviours evidenced in code/tests:

- Estimate **versions** with lock statuses (`AUTO_LOCK_VERSION_STATUSES` in `app/models/estimate.py`).
- Proposals built as **snapshots** from estimate versions (`build_proposal_snapshot` exported from `app/services/`); tests in `tests/test_proposal_snapshots.py` assert independence from later estimate edits.
- Proposal statuses include `Accepted` among others (`PROPOSAL_STATUSES` in `app/models/proposal.py`).
- Change Orders package under `app/project_controls/` with its own routes/services/repository/pdf.
- Plan Intelligence Phase A upload/storage (M005) and Document Indexing (M007): pages, processing provenance, archive-over-delete, relational search (`app/plan_intelligence/`; tests `tests/test_plan_upload.py`, `tests/test_plan_indexing.py`). Sheets **implemented** (M009). Scale/measurement **implemented** (M010). **AI quantity extraction foundation is CLOSED / OPERATIONAL FOR UAT** ([FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md); mock extractor only).

### Services / repositories

| Layer | Paths |
|-------|-------|
| Services | `app/services/estimates.py`, `estimate_builder.py`, `proposals.py`, `proposal_pdf.py`, `build.py`, `build_storage.py` |
| Project controls | `app/project_controls/services.py`, `repository.py`, `pdf.py` |
| Plan Intelligence | `app/plan_intelligence/services.py`, `processing.py`, `extraction.py`, `storage.py`, `packages.py`, `audit.py`, `takeoff.py`, `takeoff_extractors.py` |
| Generic repositories package | `app/repositories/` (present; inspect before assuming usage) |

### Templates & static assets

- Templates: `app/templates/` (clients, projects including Project Hub `projects/detail.html`, estimates, proposals, proposal_templates, assemblies, cost_library, project_controls, plan_intelligence including take-off, labour_engine, pricing_engine, build field observations, dashboard, base, partials)
- Static: `app/static/` (css, js, branding)

### Migrations

- Flask-Migrate / Alembic under [`migrations/`](../migrations/)
- Config: `migrations/alembic.ini`, `migrations/env.py`
- Version scripts in `migrations/versions/` (clients/projects through change orders, `plan_documents`, Document Intelligence M007)
- Alembic **repository** graph head: **`d2e3f4a5b6c7`** (FG-021). Live development/UAT `flask db current`: **`d2e3f4a5b6c7`**. Live current = head. One graph head. Verify `flask db current` per environment before relying on it.

### Tests

- Location: [`tests/`](../tests/)
- Collected locally: last governed full suite **551 passed** (`./venv/bin/python -m pytest -q`, 2026-09-02 FG-021 live migration). Dedicated FG-021 **13**. Focused **141**.
- Coverage areas: assemblies, estimates/builder, proposals, proposal snapshots/preview/pdf, change orders, project hub, plan upload/indexing/sheets/scale/take-off, labour engine, pricing engine, historical ingestion, organization foundation

### Current module relationships (simplified)

```text
Client ──< Project ──< Estimate ──< EstimateVersion ──< Sections/Lines
              │            │                │
              │            │                └──> Proposal (snapshot) ── Sections/Lines
              │            │
              │            └── ChangeOrder (optional estimate_version FK)
              │
              └── PlanDocument / DrawingPackage / sheets / measurements / take-off packages (Plan Intelligence; M005–M010 + M012 foundation; Phase D mapping not started)
```

- Navigation also shows **disabled** placeholders: Purchase Orders, Job Costing, Reports, AI Assistant, Settings (`app/navigation.py`).
- **Project Hub UX (FG-011):** `/projects/<id>` (`app/routes/projects.py` `view_project`, `app/services/project_hub.py`, `app/templates/projects/detail.html`) reads stored facts and links into owning modules. No durable hub entity.
- **Estimate-output consistency (FG-012):** Estimating-owned internal breakdown (`app/services/estimate_output.py`, `GET /estimates/<id>/versions/<version_id>/internal-breakdown`). Named-method Proposal totals copy frozen `EstimatePricingSnapshot`. Customer PDF omits Overhead/Profit rows. No new entity or schema.
- **Permit Foundation (FG-015):** `ProjectLocation`, platform jurisdiction definitions/aliases, versioned preliminary `PermitProfile`, Hub PLAN **PERMIT & APPROVALS** foundation panel (`app/services/jurisdiction.py`, `app/services/permit_foundation.py`). Pass 2 [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT** (**gate-at-close** live current = head `f8a9b0c1d2e3`; live head today is `a9b0c1d2e3f4`).
- **Organization Brand Profile (FG-017):** `OrganizationBrandProfile`, `ProposalBrandSnapshot`, Settings `/settings/brand-profile` (`app/services/brand_profile.py`, `app/services/brand_logo_storage.py`). **CLOSED / OPERATIONAL FOR UAT**. Live current = head `a9b0c1d2e3f4`. Change Order / Permit consumers remain future.

### Known architectural risks / incomplete boundaries

- Root [`README.md`](../README.md) was empty before governance sprint (now pointers added).
- No prior `docs/` governance (this foundation addresses that).
- Change Order detail template notes future audit trail UI (`app/templates/project_controls/change_orders/detail.html`).
- Hard-coded `SECRET_KEY` in `create_app` (development default) — production secret handling is an open operational concern.
- Flask-Login is used for office authentication ([FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**). Shared API Foundation V1 is **operational for UAT** ([FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**) with a **narrow** FG-020 BUILD POST allow-list. RBAC and multi-org switching are **not implemented**.
- Office proposal create/detail still lists Overhead/Profit amounts (zero when named-method snapshot governs). Customer preview/PDF do not. Draft proposal line edits still restack via `recalculate_proposal`.
- Proposal “Accepted” status exists; full acceptance → project budget snapshot workflow is **not** documented as complete product (see Intended).
- CRM is effectively Clients + Projects, not a full CRM suite.

---

## Intended Architecture

Aligns with [platform-vision.md](platform-vision.md), [CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md), and [architecture-principles.md](architecture-principles.md):

- `Project` remains the CalibAi lifecycle hub ([ADR-019](adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted**). `/projects/<id>` is the Project Hub UX ([FG-011](feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**): read/link lifecycle surface owned by Projects; no new module, entity, or schema.
- Internal Detailed Cost Breakdown + customer Proposal consistency ([FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**): existing `EstimateVersion` / pricing snapshot is the source; existing Proposal is the customer-facing estimate; no new document module.
- Explicit module ownership documents (CRM, Estimating, Proposals, Projects, Plan Intelligence, Material Catalogue, proposed BUILD, Supplier Catalogue, Project Controls expansions)
- Immutable accepted-proposal snapshots feeding project creation (Rule 3–4)
- Auditable financially significant actions (Rule 6)
- Service boundaries for cross-module access (Rule 11)
- Governance Feature Gate before net-new modules
- Human-approved, source-traceable take-off before estimate insertion (ADR-005/006 **Accepted**; [FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; mapping deferred to Phase D)
- One project-location / jurisdiction-resolution architecture ([ADR-037](adr/ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted**; [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**)
- Permit Intelligence as a project capability; Permit & Approvals Report as its governed snapshot ([ADR-038](adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted**; Pass 1 [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**; Pass 2 [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**)
- Supplier price snapshots on consumption (ADR-008 — Proposed)

---

## Future Architecture

Planned only when approved (see [platform-roadmap.md](platform-roadmap.md)):

### Differentiating pillars

- [Plan Intelligence and Automated Take-Off](architecture/plan-intelligence-and-automated-takeoff.md) — Phases A–M010 **Current**; Phase **C** AI take-off foundation **operational for UAT** ([FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**); Phases D–G future
- [Material Catalogue](architecture/material-catalogue-architecture.md) — **Partial Current** / [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-034](adr/ADR-034-canonical-material-identity-and-ownership.md) / [ADR-035](adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) / [ADR-036](adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted**. Living supplier evidence is **not** the identity row. `CostItem` is **not** canonical material.
- [Supplier Catalogue, Inventory and Pricing](architecture/supplier-catalogue-inventory-pricing.md) — Phases E–F **Future** (what a supplier sells; maps **to** Material Catalogue; does **not** own CalibAi identity). **Governed bulk onboarding** is a **FUTURE / NOT IMPLEMENTED** pin (not one-product-at-a-time; not authorized by FG-014).
- [Supplier Channel and Launch-Partner Model](architecture/supplier-channel-and-launch-partner.md) — **Future**; [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (Winchester launch/reference, supplier-neutral, dual relationships; **not implemented**)
- Procurement / purchase-order preparation (nav placeholder only today)

### Other future capabilities

- **BUILD / MONITOR / LEARN** — [CAR-001](architecture/CAR-001-calibai-product-architecture-reconciliation.md); BUILD boundary [ADR-020](adr/ADR-020-build-module-boundary.md) (**Accepted**); field evidence / dual-surface architecture [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) (**Accepted**); [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**; MONITOR baseline [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) (**Accepted**, not implemented; Project Gross Margin)
- **Field / shared API** — [ADR-022](adr/ADR-022-field-client-and-shared-api.md) (**Accepted** direction). Shared API Foundation V1 **implemented** ([FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**). Field Web V1 **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING** ([FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md); [architecture/field-web-today-and-capture.md](architecture/field-web-today-and-capture.md)). [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. Live current = head `d2e3f4a5b6c7`.
- **Project document package** — outputs **1–2** [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. Outputs **3–4** remain **Future**. **Permit Intelligence** Pass 1 **CLOSED / OPERATIONAL FOR UAT** ([FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md)); Pass 2 **CLOSED / OPERATIONAL FOR UAT** ([FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md); ADR-037/038/039). Permit & Approvals Report is a **core project document**, not a fifth estimate output and not a Change Order. **Organization Brand Profile** is **CLOSED / OPERATIONAL FOR UAT** ([ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md)). **Change Order document family** remains **FUTURE / NOT IMPLEMENTED**.
- Scheduling, Job Costing, Invoicing
- QuickBooks / accounting integration — [architecture/quickbooks-integration.md](architecture/quickbooks-integration.md)
- Historical estimating intelligence (LEARN; [ADR-024](adr/ADR-024-learn-recommendation-boundary.md))
- **Historical upload onboarding (FG-013)** — [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. Revision `c5d6e7f8a9b0` (**gate-at-close** live current=head; later superseded).
- **Labour Engine Phase B** — [labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md); [FG-008](feature-gates/FG-008-labour-engine-phase-b.md) **IMPLEMENTED / VERIFIED / LIVE-MIGRATED** (foundation operational for UAT). Selling-price application remains out of scope of FG-008.
- **Organization-Calibrated Pricing Engine** — [organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md); [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. ADR-025 **Accepted**; ADR-030 **Accepted**. Foundation operational for UAT. Labour-snapshot Direct Labour Cost is not included in the estimate basis by default. Optional ORG-001 overhead/profit/contingency layers remain `UNSPECIFIED`.

Labour Engine and Pricing Engine foundations are **Current**. AI take-off foundation, Permit Pass 1–2, Material Catalogue identity, historical-upload UX, and Organization Brand Profile V1 (Proposal consumer) are **CLOSED / OPERATIONAL FOR UAT**. Do **not** describe the remaining items in this Future list as existing:

- Electronic signature / formal proposal acceptance workflows
- CAD ingestion (Phase G; PDF-first per ADR-009)
- Estimate mapping from approved take-off packages (Phase D; not FG-010). Material Catalogue identity **precedes** Phase D implementation.
- Living supplier evidence / Winchester POC / bulk supplier onboarding (FG-014 identity is closed; ADR-008 remains Proposed)
- Permit branding from Brand Profile; national Permit Rules expansion (FG-015/FG-016 POC is closed)
- Change Order governed document family / client email / field UX — [change-order-document-family.md](architecture/change-order-document-family.md) **FUTURE / NOT IMPLEMENTED** (do not create a second Change Order entity)
- Authentication / actor identity + shared API (sequence item 10 **COMPLETE** — [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**)
- MONITOR implementation; LEARN / ML; Project Closeout (Item 11 Field Observation foundation is **COMPLETE**; Item 12 Field Web is **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING** — [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md); Closeout **not implemented** — [build-media-storage-lifecycle.md](architecture/build-media-storage-lifecycle.md))
- Contract / e-signature / signed Change Order — **ARCHITECTURE RECONNAISSANCE COMPLETE / NOT IMPLEMENTED** ([architecture/contract-esignature-and-signed-change-order.md](architecture/contract-esignature-and-signed-change-order.md)). Recommendation **NATIVE V1**. Counsel spec **PREPARED** ([legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md)). **Development may proceed under separate governance. Production activation / real customer use is blocked pending Ontario counsel approval of the signing process.** No Feature Gate in this pass.

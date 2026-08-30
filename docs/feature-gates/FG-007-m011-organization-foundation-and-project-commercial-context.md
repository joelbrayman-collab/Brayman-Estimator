# Feature Gate — M011 Organization Foundation & Project Commercial Context

| Attribute | Value |
|---|---|
| ID | **FG-007** |
| Milestone | **M011** — Organization Foundation & Project Commercial Context |
| Module | Organization & Calibration / Projects Core |
| Date | 2026-08-28 |
| Approved baseline | `main` @ `f660b54` (docs: complete organization and calibration architecture Phase A); Alembic head `c9e0f1a2b3d4` (M010) |
| Architecture | [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md) |
| Related ADRs | [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted (governing FG-007 / M011; implemented)** · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) · [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) |
| CAR | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |

---

## Status

| Layer | State |
|---|---|
| Architecture (Phase A) | **APPROVED** (`f660b54`, 2026-08-28) |
| Feature Gate (this document) | **APPROVED** (`01b3be4`, 2026-08-28) |
| Implementation | **IMPLEMENTED & VERIFIED** (159/159 tests passing; committed on `main` at `cb38d93`, migration `d0a1b2c3d4e5`) |

---

## Objective

Prepare and specify the **minimum implementation scope** required to introduce durable Organization ownership and the **Project Creation Commercial Decision Gate** into the application data layer.

This milestone establishes the foundational tenant container and immutable project context provenance needed before CalibAi can safely implement:
1. Historical Estimate Ingestion Engine (Phase B / persistence via FG-006)
2. CalibAi Labour Engine (Phase B / productivity curves & rates)
3. Organization-Calibrated Pricing Engine
4. Organization-scoped QuickBooks Integrations
5. Multi-tenant document package generation

---

## Feature Gate Answers

| # | Question | Answer |
|---|---|---|
| 1 | What problem does this solve? | The platform currently operates single-tenant with globally shared records. Without explicit organization ownership and project-level commercial decision provenance, historical ingestion and labour engine implementations risk hardcoding Brayman-specific rates and assumptions into universal CalibAi core logic, or floating estimate context retroactively when project settings change. |
| 2 | Who is the user? | Estimators, commercial managers, and administrators working in the office web UI creating/configuring projects and producing defensible estimates. |
| 3 | Which module owns it? | **Projects Module** (parenting Commercial Context) & **Organization Subsystem** (parenting tenant identity & ownership). |
| 4 | What data does it own? | Additive `organizations` table; additive `project_commercial_contexts` (and context versions/provenance); additive direct `organization_id` foreign keys on top-level root entities (`clients`, `projects`, `cost_items`, `assemblies`, `proposal_templates`); additive `commercial_context_id` foreign key on `estimate_versions`. |
| 5 | What data does it reference? | `clients`, `projects`, `estimates`, `estimate_versions`, `proposals`, `change_orders`, `plan_documents`, `cost_items`, `assemblies`. |
| 6 | What may implementation change? | Additive `Organization` model and `ProjectCommercialContext` model; nullable `organization_id` columns backfilled to `ORG-001` (Brayman Construction Inc.) and made `nullable=False` where safe; additive Alembic migration; project creation/edit UI for mandatory commercial decision parameters; estimate version reference linking; focused test suite. |
| 7 | What must implementation not change? | Plan Intelligence geometry / coordinate systems; PDF rendering; PlanDocument stored bytes; pricing formula math solvers; CRM core workflows; Proposal snapshot immutability; QuickBooks API writes; full multi-tenant RBAC auth; billing/subscriptions. |
| 8 | What are the acceptance criteria? | See **Acceptance Criteria** below. |
| 9 | What tests are required? | Migration backfill tests; tenant isolation query tests; project commercial context provenance tests; estimate version frozen context reference tests; policy-driven reason enforcement tests; full regression suite (140+ passing). |
| 10 | What documentation must be updated? | This gate; ADR-028; ADR index; FG index; modules/projects.md; current-state; project-state-report; session-handoff; roadmap; chat-workflow-log. |
| 11 | Which ADRs govern it? | [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) (Organization Foundation & Commercial Context); [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) (Project as Hub); [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) (Snapshot Immutability). |
| 12 | Does it require a database migration? | **Yes — future implementation prompt only.** Additive tables (`organizations`, `project_commercial_contexts`) and additive foreign keys (`organization_id`, `commercial_context_id`). This governance prompt must **not** create migrations. |
| 13 | What is the Organization V1 entity scope? | Minimal production container: `id` (String PK, e.g. `ORG-001`), `legal_name`, `display_name`, `primary_address`, `default_region`, `currency` (ISO-4217), `tax_jurisdiction`, `is_active`, `created_at`, `updated_at`. |
| 14 | How is existing data backfilled? | Seed Organization `ORG-001` (Brayman Construction Inc., 411 St. John Street, Merrickville, ON K0G 1N0, CAD, Ontario HST); backfill all existing clients, projects, cost items, assemblies, and proposal templates to `ORG-001`; ensure 100% data integrity with zero orphan records. |
| 15 | How is Project Commercial Context persisted? | 7 mandatory commercial parameters stored in a dedicated `ProjectCommercialContext` entity versioned per project: (1) Project Type, (2) Pricing Posture, (3) Execution Risk, (4) Schedule Condition, (5) Site Condition, (6) Estimate Confidence / Stage, (7) Delivery Model. Includes provenance (`selected_by`, `selected_at`, `justification_reason`, `change_summary`). |
| 16 | How do estimates preserve historical context? | `EstimateVersion` gains an immutable foreign key `commercial_context_id` pointing to the exact context version active when the estimate version was created or repriced. Subsequent project-level context changes do not mutate prior estimate version references. |
| 17 | How is tenant isolation enforced in V1? | Request/service-level organization scoping helper (`get_current_organization_id()`). All repository and service read/write queries must explicitly filter by `organization_id`. Direct PK lookups without organization verification fail closed. |
| 18 | What are the stopping conditions? | Stop if migration threatens existing client/project/estimate data, if circular foreign keys prevent clean backfill, or if multi-tenant isolation requires full RBAC prematurely. |

---

## Core Invariants (Must Remain True)

1. **Pricing Posture Invariant:** Pricing Posture (e.g. Lean, Fair Market, Selective, Premium) is commercial pricing strategy, **not** direct cost economics. It must **never** alter base labour wage rates ($65/hr), true physical crew hours, material quantities, or supplier invoice amounts.
2. **Execution Risk Invariant:** Execution Risk (Low, Normal, Elevated, High) represents delivery uncertainty and site complexity. It remains strictly separate from commercial margin preferences.
3. **Estimate Context Immutability:** Historical estimate versions must forever preserve the exact commercial assumptions under which they were created or approved. Changing project-level settings later creates a new context version and does **not** alter prior estimate records.
4. **Tenant Isolation:** No Organization A route, query, or export may access or infer Organization B data. Single-tenant development mode defaults safely to `ORG-001` without compromising query-scoping architecture.
5. **Policy-Driven Provenance & Reason Requirement:** CalibAi Core supports policy-driven justification requirements. Each Organization determines which Project Commercial Context selections require a justification reason. For Brayman Organization V1, proposed initial policy may require reasons for selections such as Pricing Posture = Premium or Execution Risk = High, but these remain organization-configurable policy, not hardcoded universal platform rules. AI never silently alters project commercial parameters.

---

## Authorized Schema & Model Specifications

### 1. `Organization` (`organizations`)
- `id`: String(50) Primary Key (e.g. `ORG-001`)
- `legal_name`: String(255) Not Null (e.g. "Brayman Construction Inc.")
- `display_name`: String(255) Not Null (e.g. "Brayman Construction")
- `primary_address`: String(255) (e.g. "411 St. John Street, Merrickville, Ontario K0G 1N0")
- `default_region`: String(100) (e.g. "Eastern Ontario / Ottawa Valley")
- `currency`: String(3) Not Null Default "CAD"
- `tax_jurisdiction`: String(100) Default "Ontario (HST 13%)"
- `is_active`: Boolean Not Null Default True
- `created_at`, `updated_at`: DateTime Not Null

### 2. `ProjectCommercialContext` (`project_commercial_contexts`)
- `id`: Integer Primary Key
- `project_id`: Integer Foreign Key -> `projects.id` Not Null (indexed)
- `version_number`: Integer Not Null Default 1
- `is_current`: Boolean Not Null Default True
- `project_type`: String(50) Not Null (e.g. "New Build", "Addition", "Renovation", "Garage", "Foundation", "Commercial", "Specialty")
- `pricing_posture`: String(50) Not Null (e.g. "Lean", "Competitive", "Fair Market", "Selective", "Premium")
- `execution_risk`: String(50) Not Null (e.g. "Low", "Normal", "Elevated", "High")
- `schedule_condition`: String(50) Not Null (e.g. "Flexible", "Normal", "Compressed", "Critical")
- `site_condition`: String(50) Not Null (e.g. "Normal", "Restricted Access", "Remote", "Occupied", "Congested")
- `estimate_stage`: String(50) Not Null (e.g. "Budget", "Preliminary", "Tender", "Contract")
- `delivery_model`: String(50) Not Null (e.g. "Self-Perform", "Mixed", "Primarily Subcontracted")
- `justification_reason`: Text (required when organization policy mandates reason for exceptional posture/risk settings)
- `change_summary`: Text (notes on what changed from prior version)
- `created_by`: String(150) (human actor / "system_backfill")
- `created_at`: DateTime Not Null Default UTC

### 3. Model Ownership Graph (Additive Foreign Keys)
- `clients.organization_id`: String(50) Foreign Key -> `organizations.id` (Indexed, Not Null post-backfill)
- `projects.organization_id`: String(50) Foreign Key -> `organizations.id` (Indexed, Not Null post-backfill)
- `cost_items.organization_id`: String(50) Foreign Key -> `organizations.id` (Indexed, Not Null post-backfill)
- `assemblies.organization_id`: String(50) Foreign Key -> `organizations.id` (Indexed, Not Null post-backfill)
- `proposal_templates.organization_id`: String(50) Foreign Key -> `organizations.id` (Indexed, Not Null post-backfill)
- `estimate_versions.commercial_context_id`: Integer Foreign Key -> `project_commercial_contexts.id` (Nullable for legacy, populated for new/repriced versions)

---

## Acceptance Criteria

1. **Backfill & Data Preservation:** 100% of existing client, project, estimate, proposal, change order, drawing, cost item, and assembly records are successfully associated with `ORG-001` (Brayman Construction Inc.). Zero data loss or corruption.
2. **Project Creation Commercial Gate:** Creating or editing a Project requires valid selections for all 7 commercial context parameters. Selections requiring justification under organization policy prompt for and store human justification reasons.
3. **Estimate Context Freezing:** When an Estimate Version is created, it links directly to the current `ProjectCommercialContext`. If the project's commercial parameters are later modified, a new `ProjectCommercialContext` version is created; existing estimate versions remain frozen to their original context snapshot.
4. **Tenant Query Scoping:** All service-layer list/detail queries for Clients, Projects, Cost Items, and Assemblies automatically enforce organization scoping. Cross-tenant retrieval by guessed ID returns 404 / access denied.
5. **Regression Verification:** All existing 140 pytest unit/integration tests continue to pass with zero regressions across CRM, Estimating, Proposals, Change Orders, and Plan Intelligence.

---

## Required Implementation Tests

1. `test_organization_seed_and_backfill`: Verifies `ORG-001` creation and backfill completeness across all root tables.
2. `test_tenant_isolation_clients_and_projects`: Verifies Organization A cannot query or mutate Organization B clients or projects.
3. `test_project_commercial_context_creation`: Verifies all 7 mandatory parameters are validated upon project creation.
4. `test_project_commercial_context_versioning`: Verifies updating project context creates version N+1 and sets prior versions to `is_current=False`.
5. `test_estimate_version_context_immutability`: Verifies modifying project context does not mutate the `commercial_context_id` or context data attached to historical estimate versions.
6. `test_policy_driven_reason_enforcement`: Verifies organization policy identifies reason-required selections, reason is mandatory when policy requires it, and another organization can configure different reason requirements.
7. `test_full_suite_regression`: Verifies 140 baseline tests pass cleanly in the organization-aware environment.

---

## Migration Safety & Sequencing Plan

The migration is a **controlled additive migration designed to minimize application interruption; implementation must define rollback and verification procedures.**

1. **Phase 1 (Additive Tables):** Create `organizations` and `project_commercial_contexts` tables.
2. **Phase 2 (Seed):** Insert `ORG-001` (Brayman Construction Inc.).
3. **Phase 3 (Nullable Columns):** Add nullable `organization_id` to `clients`, `projects`, `cost_items`, `assemblies`, `proposal_templates`; add nullable `commercial_context_id` to `estimate_versions`.
4. **Phase 4 (Backfill with Explicit Legacy / Unknown Semantics):** Execute SQL `UPDATE ... SET organization_id = 'ORG-001' WHERE organization_id IS NULL`; generate `ProjectCommercialContext` records for existing pre-M011 projects with explicit `Legacy / Unknown` across all 7 parameters (`is_legacy_unknown=True`), and link active estimate versions. Pre-M011 commercial decisions are unrecorded; CalibAi must never infer historical pricing posture, risk, site/schedule conditions, stage, delivery model, or project type from pre-M011 legacy records.
5. **Phase 5 (Constraints & Indexes):** Alter `organization_id` columns to `nullable=False`; add foreign key constraints and performance indexes.

---

## Blocking Conditions

> **Historical Status:** M011 was successfully implemented and verified (`cb38d93`, migration `d0a1b2c3d4e5`), satisfying the prerequisite for FG-006 (Historical Estimate Ingestion Engine — Phase B), which has also been implemented and verified (`690d755`, migration `e1b2c3d4e5f6`).
> **Current Status:** [FG-008](FG-008-labour-engine-phase-b.md) Labour Engine Phase B is **CLOSED / OPERATIONAL FOR UAT** (revision `f2c3d4e5f6a7` in chain). [FG-009](FG-009-organization-calibrated-pricing-engine.md) Organization-Calibrated Pricing Engine is **CLOSED / OPERATIONAL FOR UAT** (revision `a3b4c5d6e7f8` in chain). [FG-010](FG-010-ai-takeoff-quantity-extraction-foundation.md) is **CLOSED / OPERATIONAL FOR UAT** (live Alembic current/head `b4c5d6e7f8a9`).

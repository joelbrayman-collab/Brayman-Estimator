# ADR-028 — Organization Foundation and Project Commercial Context

| Field | Value |
|---|---|
| Title | ADR-028: Organization Foundation, Multi-Tenant Boundary, and Project Commercial Context |
| Status | **Accepted** (governing M011 Feature Gate FG-007; implemented in M011) |
| Date | 2026-08-28 |
| Related | [FG-007](../feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md) · [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md) · [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) · [ADR-002](ADR-002-accepted-proposal-immutability.md) |

---

## Context

The CalibAi / Brayman Estimator platform currently operates as a single-tenant system where `Client`, `Project`, `CostItem`, and `Assembly` models reside in a globally shared namespace. Furthermore, projects lack structured, versioned commercial decision parameters (pricing posture, execution risk, schedule conditions, delivery models).

Implementing the Historical Estimate Ingestion Engine (Phase B) or the CalibAi Labour Engine (Phase B) without an explicit organization container risks embedding Brayman-specific rates ($65/hr direct labor, 15% margin) as universal platform defaults. Additionally, allowing project-level commercial risk and posture assumptions to float without versioning would corrupt the historical context under which past estimates and proposals were priced.

---

## Decision

1. **Organization as Root Commercial Entity:**
   - Introduce an `Organization` model (`organizations` table) representing the customer organization / tenant container.
   - Seed `ORG-001` representing Brayman Construction Inc. (411 St. John Street, Merrickville, Ontario K0G 1N0).
   - Backfill all existing clients, projects, cost items, assemblies, and proposal templates to `ORG-001`.

2. **Direct vs Inherited Ownership Boundaries:**
   - **Direct Foreign Key (`organization_id`):** Added to root entities: `Client`, `Project`, `CostItem`, `Assembly`, and `ProposalTemplate`.
   - **Inherited Ownership:** Child entities (`Estimate`, `EstimateVersion`, `Proposal`, `ChangeOrder`, `PlanDocument`, `PlanSheet`, `PlanScaleCalibration`, `PlanMeasurement`) inherit organization ownership through their parent `Project` (or `Client`), avoiding redundant foreign keys while guaranteeing strict query scoping.

3. **Project Commercial Decision Context Model:**
   - Introduce a versioned `ProjectCommercialContext` model attached to `Project`.
   - Captures the 7 mandatory parameters of the Commercial Decision Gate: (1) Project Type, (2) Pricing Posture, (3) Execution Risk, (4) Schedule Condition, (5) Site Condition, (6) Estimate Confidence / Stage, and (7) Delivery Model.
   - Implements provenance tracking (`created_by`, `created_at`, `justification_reason`, `change_summary`).

4. **Estimate Historical Context Reference:**
   - `EstimateVersion` gains a foreign key `commercial_context_id` referencing the active `ProjectCommercialContext` at the time of creation or repricing.
   - Edits to project-level commercial settings generate a new context version and leave historical estimate version references untouched and immutable.

5. **CostItem & Assembly Scope in V1:**
   - In M011, `CostItem` and `Assembly` receive direct `organization_id` foreign keys and are backfilled to `ORG-001`. This ensures Brayman's private cost items cannot leak as universal defaults when future organizations are onboarded. Full baseline catalog inheritance/override architecture is deferred to a future milestone.

---

## Alternatives Considered

- **Alternative A: Defer Organization Entity until Multi-User Auth / SaaS Launch** — Rejected: Ingesting 20 historical workbooks and calibrating labor rates into a single global namespace would permanently pollute the core data model with Brayman-specific assumptions.
- **Alternative B: Store Commercial Context directly as project columns without versioning** — Rejected: When an estimator modifies a project's pricing posture from Competitive to Premium, all historical estimates under that project would falsely appear to have been priced under the new posture, destroying commercial auditability.
- **Alternative C: Duplicate `organization_id` on every database table** — Rejected: Unnecessary schema bloat. Enforcing ownership on root entities (`Project`, `Client`, `CostItem`, `Assembly`) maintains a clean, normalized relational graph.

---

## Consequences

- **Positive:**
  - Establishes a clean architectural boundary between CalibAi Core methodology and customer-owned commercial intelligence.
  - Guarantees complete historical provenance for all estimate pricing assumptions.
  - Enables zero-risk implementation of Historical Ingestion Phase B and Labour Engine Phase B.
- **Negative:**
  - Requires a 5-step additive database migration and data backfill.
  - Project creation workflow requires 7 mandatory dropdown selections.

---

## Module & Data Ownership Impact

- **Projects Module:** Gains ownership of `ProjectCommercialContext` and manages context versioning lifecycles.
- **Organization Subsystem:** Introduced to manage tenant identity and data isolation scoping.
- **Estimating Module:** `EstimateVersion` records reference to `ProjectCommercialContext`.

---

## Migration Impact

The migration is a **controlled additive migration designed to minimize application interruption; implementation must define rollback and verification procedures.**

Additive migration `_add_organization_and_commercial_context_m011.py`:
1. Create `organizations` table.
2. Insert `ORG-001` seed row.
3. Add nullable `organization_id` and `commercial_context_id` columns.
4. Backfill existing records to `ORG-001` and create initial project commercial context records with explicit `Legacy / Unknown` semantics for all 7 parameters. Pre-M011 commercial decisions are unrecorded; CalibAi must never infer historical pricing posture, risk, site/schedule conditions, stage, delivery model, or project type from pre-M011 legacy records.
5. Set `nullable=False` on `organization_id` root columns and add foreign key constraints and indexes.

---

## Testing Impact

- Focused tests for organization backfill, tenant query scoping, commercial context versioning, policy-driven reason enforcement, and frozen estimate references.
- Full regression verification of 140 existing test baseline.

---

## Approval

| Role | Name | Status | Date |
|---|---|---|---|
| Joel | Joel Brayman | Approved | 2026-08-28 |
| ChatGPT review | Feature Gate FG-007 Approved & Implemented | Approved | 2026-08-28 |
| Implementation note | Implemented & Verified in M011 (`cb38d93`, migration `d0a1b2c3d4e5`) | Complete | 2026-08-28 |

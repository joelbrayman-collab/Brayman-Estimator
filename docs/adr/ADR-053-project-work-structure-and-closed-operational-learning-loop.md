# ADR-053 — Project Work Structure and Closed Operational / Learning Loop

| Field | Value |
|-------|--------|
| Title | ADR-053: Project Work Structure and Closed Operational / Learning Loop |
| Status | **Accepted** (2026-09-15; Joel Brayman / ChatGPT Architect). TAX/WBS product implementation is authorized under [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. SCOPE / TIME / SCH / PERF / CLOSE / LEARN / QB-T remain **NOT AUTHORIZED**. |
| Date | 2026-09-15 |
| Related | [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-020](ADR-020-build-module-boundary.md) **Accepted** · [ADR-021](ADR-021-monitor-commercial-baseline.md) **Accepted** · [ADR-024](ADR-024-learn-recommendation-boundary.md) **Accepted** · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-029](ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** · [ADR-049](ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted** · [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED** (not reopened) · [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED** (not rewritten) · product direction [project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) |

---

## Context

CalibraytAI must support one closed operational / learning loop:

frozen EstimateVersion → Project work structure → Schedule / assignment → field Time → Time approval → approved labour-hours actuals → MONITOR / alerts → Closeout → LEARN → human-accepted calibration.

The 15 Sep 2026 product-direction record is complete and not implementation authorization. A repository-aware preflight was accepted. Existing `ProjectCommercialContext.project_type` is commercial context. Existing `LabourTask` is PRICE estimating authority. Existing `ChangeOrder` is the commercial Change Order SoR. Existing `ProjectDirectCostActual` is office money actuals. None of those may be overloaded to become the work-structure, timesheet, or Schedule engine.

## Decision

**Accepted.**

### A. Project remains the operational home

`Project` remains the lifecycle hub ([ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md)). Work-structure instances belong to a Project.

### B. ProjectCommercialContext is not WBS taxonomy

`ProjectCommercialContext.project_type` and related fields remain commercial / performance drivers. They are **not** replaced by work-structure Project Type.

### C. EstimateVersion + EstimateLabourSnapshot remain WHAT WE THOUGHT

Locked / Accepted estimate labour snapshots are immutable historical evidence. TAX/WBS may **pin** them. It must not mutate them.

### D. Projects owns work-structure identity

Projects owns catalog and Project instances for work-structure Project Type, Element, and Activity. Three layers: CalibraytAI baseline catalog, organization extensions, Project instances. One platform. One codebase. No tenant forks. Tenants cannot promote into baseline.

### E. LabourTask remains PRICE authority

`LabourTask` remains Estimating / Labour Engine authority. Activity **may** reference `labour_task_id`. They are not merged. An Activity may exist with no LabourTask.

### F. Schedule and Time share the same work authority

Future Schedule and Time use the same Project → Element → Activity instances. TAX/WBS does not implement those consumers.

### G. Scheduled time is not actual time

Future Schedule must never fabricate actual labour.

### H. Submitted Time is not approved actual

Future Time Entry distinguishes submitted from approved.

### I. Approved Time is labour-hours actual

Approved Time is the labour-**hours** actual for MONITOR, LEARN, and later payroll readiness.

### J. ProjectDirectCostActual remains money actual

Do not overload `project_direct_cost_actuals` as timesheets. BUILD continues to own office dollar actuals.

### K. ChangeOrder remains the sole commercial Change Order SoR

Do not create a second commercial Change Order entity. Document family remains future pin.

### L. Scope lineage overlays work structure

Future SCOPE slice overlays origin (`ORIGINAL` / `CHANGE_ORDER` / `EXTRA_WORK`) on work structure and **references** `ChangeOrder`. TAX/WBS does not implement origin.

### M. Original scope is immutable historical evidence

Change Orders modify current authorized work. They do not rewrite the original estimate.

### N. MONITOR is a projection / consumer

Do not reopen [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md). Labour-hours performance is a later consumer of approved Time and work structure.

### O–P. Closeout and LEARN eligibility

Closeout establishes learning evidence quality. Project Complete does **not** automatically mean LEARN-eligible.

### Q–S. LEARN recommends; human decides; org-bounded

Reuse the existing `LabourCalibrationCandidate` / review pattern where appropriate. No silent writes to standards, locked estimates, or Schedule. No cross-tenant learning.

### T. QuickBooks Time export is a later sibling

Do not rewrite [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md). Time export is a later QB-T slice.

### U. Field capture remains evidence

`FieldCaptureEvent` is not the Time SoR.

### V. Organization extensions are configuration, not custom code

Organizations may add Types / Elements / Activities as data. They must not create custom executable logic.

## Alternatives Considered

- **Reuse commercial `project_type` as WBS type** — Rejected: commercial context and work taxonomy would collide.
- **Merge Activity into LabourTask** — Rejected: PRICE vs BUILD/Time grain; Extra Work may have no bid-book task.
- **Store field hours on ProjectDirectCostActual** — Rejected: money vs hours; source is OFFICE_MANUAL.
- **Tag timesheets only for Change Order lineage** — Rejected by product direction; lineage belongs on work structure (SCOPE later).

## Consequences

**Positive:** Later slices inherit one work authority. Estimate evidence stays frozen. Existing MONITOR money path and CO commercial SoR remain intact.

**Negative:** TAX/WBS alone does not make Time, Schedule, or LEARN real. Contractors must still seed a work plan from a locked estimate with labour snapshots.

## Module Ownership Impact

**Projects** owns work-structure catalog and Project Element / Activity instances. Estimating continues to own `LabourTask` / `EstimateLabourSnapshot`. Project Controls continues to own `ChangeOrder`. BUILD continues to own field capture and money actuals. MONITOR continues to read. LEARN continues to consume.

## Data Ownership Impact

New TAX/WBS tables are organization-scoped (or baseline with `organization_id` NULL). Seeded Project Activities pin `source_estimate_version_id` and `source_estimate_labour_snapshot_id`. Rows are retired, not hard-deleted.

## Migration Impact

Required for TAX/WBS: one additive Alembic revision parented on `f2a3b4c5d6e7`. No rewrite of existing tables.

## Testing Impact

Dedicated TAX/WBS tests: catalog layers, tenant isolation, seed eligibility/fail-closed/idempotency, pins, Hub/catalog office surfaces, migration upgrade/downgrade.

## Documentation Impact

FG-035; this ADR; module/index/continuity docs. V1 **not rescored**.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Accepted via governed FG-035 TAX/WBS prompt | 2026-09-15 |
| ChatGPT review | Repository-aware preflight accepted; FG-035 / ADR-053 assigned | 2026-09-15 |
| Cursor implementation note | TAX/WBS implemented under this ADR. Later slices not authorized. | 2026-09-15 |

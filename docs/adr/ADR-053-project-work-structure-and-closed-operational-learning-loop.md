# ADR-053 — Project Work Structure and Closed Operational / Learning Loop

| Field | Value |
|-------|--------|
| Title | ADR-053: Project Work Structure and Closed Operational / Learning Loop |
| Status | **Accepted** (2026-09-15; Joel Brayman / ChatGPT Architect). TAX/WBS, SCOPE, TIME, SCH-A, SCH-B, SCH-C, and SCH-D product implementation are authorized under [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / NOT COMMITTED / NOT PUSHED**. SCH overall **OPEN / PARTIAL**. PERF / CLOSE / LEARN / QB-T remain **NOT AUTHORIZED**. |
| Date | 2026-09-15 |
| Related | [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-020](ADR-020-build-module-boundary.md) **Accepted** · [ADR-021](ADR-021-monitor-commercial-baseline.md) **Accepted** · [ADR-024](ADR-024-learn-recommendation-boundary.md) **Accepted** · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-029](ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** · [ADR-049](ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted** · [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED** (not reopened) · [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED** (not rewritten) · product direction [project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) · SCH architecture [fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md) · SCH implementation freeze [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md) |

**Subsequent status (2026-09-19 CORE CLOSE C2 CLIENT FINAL WALKTHROUGH working tree):** C2 Client Final Walkthrough **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NOT PUSHED.** Additive **`e5f6a7b8c9d0`**. Graph head **`e5f6a7b8c9d0`**. Live Alembic remains **`d4e5f6a7b8c9`**. Client input is not the Punch List. Photo **DEFERRED**. Completion Sign-Off remains unimplemented. CORE CLOSE remains **distinct** from Decisions O–P LEARN Closeout below. This ADR is **not rewritten**. No new ADR. This record **does not rescore** V1.

**Subsequent status (2026-09-19 CORE CLOSE C1 CONTRACTOR PUNCH LIST LIVE MIGRATION):** C1 Contractor Punch List **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH MUTATING DATA.** Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Punch List **LIVE / 0 ITEMS**. C2 / Completion Sign-Off remain unimplemented. CORE CLOSE remains **distinct** from Decisions O–P LEARN Closeout below. This ADR is **not rewritten**. No new ADR. LEARN remains unauthorized. This record **does not rescore** V1.

**Subsequent status (2026-09-19 CORE CLOSE C1 CONTRACTOR PUNCH LIST PIN):** C1 Contractor Punch List **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED.** Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Punch List **IMPLEMENTED / NOT LIVE**. C2 / Completion Sign-Off remain unimplemented. CORE CLOSE remains **distinct** from Decisions O–P LEARN Closeout below. This ADR is **not rewritten**. No new ADR. LEARN remains unauthorized. This record **does not rescore** V1.

**Subsequent status (2026-09-18 CORE CLOSE CLOSE/REOPEN OPTION A PIN):** Close/Reopen Option A **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed.** Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. CORE CLOSE remains **distinct** from Decisions O–P LEARN Closeout below. This ADR is **not rewritten**. No new ADR. Punch List / Completion Sign-Off remain unimplemented. LEARN remains unauthorized. This record **does not rescore** V1.

**Subsequent status (2026-09-18 CORE CLOSE CLOSE/REOPEN OPTION A working tree):** Close/Reopen Option A **IMPLEMENTED IN WORKING TREE / TESTED / NO MIGRATION / NOT COMMITTED / NOT PUSHED / NOT LIVE-UATed.** CORE CLOSE remains **distinct** from Decisions O–P LEARN Closeout below. This ADR is **not rewritten**. No new ADR. Punch List / Completion Sign-Off remain unimplemented. LEARN remains unauthorized. This record **does not rescore** V1.

**Subsequent status (2026-09-18 FG-038 PA-A working tree):** [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) **OPEN / PARTIAL / PA-A IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED / NO OWNER ASSIGNED.** Instance Owner authority seam exists. Close/Reopen **NOT IMPLEMENTED**. Live Alembic remains **`b2c3d4e5f6a7`**. Graph head **`c3d4e5f6a7b8`**. CORE CLOSE overall remains **PARTIAL / NOT OPERATIONAL**. This ADR is **not rewritten**. No new ADR. This record **does not rescore** V1.

**Subsequent status (2026-09-18 CORE CLOSE Slice B PIN):** Slice B **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION**. Product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**. Current-operating consumers switched. CLOSED guards on NEW operational work. Close/Reopen **NOT IMPLEMENTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. People & Access **NOT IMPLEMENTED**. PERF-C **SEALED — enumeration seam updated only**. Alembic remains **`b2c3d4e5f6a7`**. CORE CLOSE overall remains **PARTIAL / NOT OPERATIONAL**. This record **does not rescore** V1.

**Subsequent status (2026-09-18 CORE CLOSE Slice B working tree):** Slice B **IMPLEMENTED IN WORKING TREE / TESTED / NO MIGRATION / NOT COMMITTED / NOT PUSHED**. Current-operating consumers switched. CLOSED guards on NEW operational work. Close/Reopen **NOT IMPLEMENTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. People & Access **NOT IMPLEMENTED**. PERF-C **SEALED — enumeration seam updated only**. Alembic remains **`b2c3d4e5f6a7`**. CORE CLOSE overall remains **PARTIAL / NOT OPERATIONAL**. This record **does not rescore** V1.

**Subsequent status (2026-09-18 CORE CLOSE Slice A LIVE MIGRATION):** Slice A **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED**. Product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. Live Alembic **`b2c3d4e5f6a7 (head)`**. All existing Projects **ACTIVE**. Lifecycle event rows **0**. Close/Reopen **NOT IMPLEMENTED**. Consumer switches **NOT IMPLEMENTED**. Punch List **NOT IMPLEMENTED**. Completion Sign-Off **NOT IMPLEMENTED**. This record **does not rescore** V1. CORE CLOSE overall remains **PARTIAL / NOT OPERATIONAL**.

**Subsequent status (2026-09-18 CORE CLOSE Slice A PIN):** Slice A **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-MIGRATED**. Product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. CORE CLOSE (operating `ACTIVE` / `CLOSED`) remains **distinct** from Decisions O–P LEARN Closeout below. This ADR is **not rewritten**. No new ADR. Close/Reopen / Punch List / Completion Sign-Off remain unimplemented. LEARN remains unauthorized.

**Subsequent status (2026-09-18 CORE CLOSE owner freeze):** [architecture/core-close-project-lifecycle-product-direction.md](../architecture/core-close-project-lifecycle-product-direction.md) **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. CORE CLOSE (operating `ACTIVE` / `CLOSED`) is **distinct** from Decisions O–P LEARN Closeout below. This ADR is **not rewritten**. No new ADR. LEARN remains unauthorized.

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

Schedule and Time use the same Project → Element → Activity instances. TAX/WBS does not implement those consumers. SCH-A overlays those instances; it does not copy or replace them.

### G. Scheduled time is not actual time

Schedule must never fabricate actual labour. SCH-A does not create `LabourTimeEntry`. Scheduled windows are not TIME actuals.

**SCH-A implementation (2026-09-15):** Projects owns Schedule overlay records `work_schedule_items` / `work_schedule_history`. One current scheduled window per Element grain and per optional Activity. Project range is derived (`MIN(scheduled_start)` → `MAX(scheduled_end)` of ACTIVE items). Activity windows must stay inside the Element window unless the same service transaction explicitly confirms the Element move/extension. Schedule does not implement PERF. Design freeze: [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md). Do **not** create a new ADR number for Schedule.

**SCH-B implementation (2026-09-16):** Projects owns `WorkScheduleAssignment` (`work_schedule_assignments`; USER XOR Crew). Organization owns optional Crew (`organization_crews` / `organization_crew_members`). Zero assignment rows = Unassigned. History `ASSIGNED` / `UNASSIGNED` uses the existing Integer `assignment_id` placeholder with **no FK**. Retiring an ACTIVE item unassigns then retires in the same transaction. Overlap warnings are a read projection. Subsequent SCH-C implemented separately.

**SCH-C implementation (2026-09-16):** Projects owns `ProjectWorkDependency` (`project_work_dependencies`; Element→Element ACTIVE/INACTIVE). Cycle / self-edge / duplicate ACTIVE edges fail closed. History `DEPENDENCY_ADDED` / `DEPENDENCY_REMOVED` uses Integer `dependency_id` with **no FK**. Sequence / predecessor-unscheduled facts are informational warnings only. Retiring an Element retires ACTIVE incoming and outgoing edges in the same transaction. Additive **`f9b0c1d2e3f4`** applied live 2026-09-16. SCH-D remains **NOT AUTHORIZED**.

### H. Submitted Time is not approved actual

Time Entry distinguishes submitted from approved. Implemented 2026-09-15 under FG-035 TIME (`labour_time_entries.status`). Submitted hours are not `approved_labour_hours()`.

### I. Approved Time is labour-hours actual

Approved Time is the labour-**hours** actual for later MONITOR, LEARN, and payroll readiness. Service: `app/services/time_entry.py` `approved_labour_hours()`. `ProjectDirectCostActual` remains money.

### J. ProjectDirectCostActual remains money actual

Do not overload `project_direct_cost_actuals` as timesheets. BUILD continues to own office dollar actuals.

### K. ChangeOrder remains the sole commercial Change Order SoR

Do not create a second commercial Change Order entity. Document family remains future pin.

### L. Scope lineage overlays work structure

SCOPE overlays origin (`ORIGINAL` / `CHANGE_ORDER` / `EXTRA_WORK`) on work structure and **references** `ChangeOrder`. Implemented 2026-09-15 under FG-035 SCOPE (`f4c5d6e7f8a9`).

### M. Original scope is immutable historical evidence

Change Orders modify current authorized work. They do not rewrite the original estimate. Implemented 2026-09-15: original hours/quantity/pins stay on the seeded Activity; authorized deltas live on `project_work_scope_deltas`.

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

**Projects** owns work-structure catalog and Project Element / Activity instances. Projects owns SCH-A Schedule overlay and SCH-B assignments (`app/models/schedule.py`, `app/services/schedule.py`, `app/routes/schedule.py`). Organization owns optional Crew configuration (`app/models/organization_crew.py`, `app/services/organization_crew.py`, `app/routes/organization_crew.py` under `/settings/crews`). Estimating continues to own `LabourTask` / `EstimateLabourSnapshot`. Project Controls continues to own `ChangeOrder`. BUILD owns field capture, money actuals, and Time Entry. MONITOR continues to read. LEARN continues to consume. Field/iPhone Schedule remains a later presentation of Projects-owned data. Design freeze: [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md).

## Data Ownership Impact

New TAX/WBS tables are organization-scoped (or baseline with `organization_id` NULL). SCOPE adds `scope_origin` / `change_order_id` on Project work plus `project_work_scope_deltas` and append-only `project_work_scope_history`. TIME adds `labour_time_entries` and append-only `labour_time_history`. SCH-A adds `work_schedule_items` and append-only `work_schedule_history`. Seeded Project Activities pin `source_estimate_version_id` and `source_estimate_labour_snapshot_id`. Rows are retired, not hard-deleted. Project start/end dates are not stored; Project range is derived.

## Migration Impact

Required for TAX/WBS: additive Alembic **`f3b4c5d6e7f8`** parented on `f2a3b4c5d6e7`. Required for SCOPE: additive Alembic **`f4c5d6e7f8a9`** parented on `f3b4c5d6e7f8`. Required for TIME: additive Alembic **`f5d6e7f8a9b0`** parented on `f4c5d6e7f8a9`. Required for SCH-A: additive Alembic **`f6e7f8a9b0c1`** parented on **`f5d6e7f8a9b0`**. Required for SCH-B: additive Alembic **`f7f8a9b0c1d2`** parented on **`f6e7f8a9b0c1`** (**live current**; applied 2026-09-16). Required for SCH-C: additive Alembic **`f9b0c1d2e3f4`** parented on **`f7f8a9b0c1d2`** (**live current**; applied 2026-09-16; expected `f8a9b0c1d2e3` collides with FG-016). No rewrite of existing Estimate or ChangeOrder tables.

## Testing Impact

Dedicated TAX/WBS, SCOPE, TIME, SCH-A, SCH-B, SCH-C, and SCH-D tests: catalog layers, tenant isolation, seed eligibility, original immutability, CO deltas, Extra Work, duration Time Entry, approval/return/supersession, approved labour service, Schedule window integrity, assignment/Crew overlap, Element→Element dependencies, cycle rejection, informational sequence warnings, Field worker Today/Week/Month, Company Today, Time suggestion, derived Project range, Hub/Field, migration upgrade/downgrade.

## Documentation Impact

FG-035; this ADR; [fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md); [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md); module/index/continuity docs. V1 **not rescored**.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Accepted via governed FG-035 TAX/WBS prompt | 2026-09-15 |
| ChatGPT review | Repository-aware preflight accepted; FG-035 / ADR-053 assigned | 2026-09-15 |
| Cursor implementation note | TAX/WBS, SCOPE, TIME, SCH-A, SCH-B, SCH-C, and SCH-D implemented under this ADR. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-D **IMPLEMENTED / TESTED / SERVER-SIDE LIVE UAT PASS / PHYSICAL IPHONE UAT PASS / NOT COMMITTED / NOT PUSHED**. Live current = repository head **`f9b0c1d2e3f4`**. PERF / CLOSE / LEARN / QB-T not authorized. | 2026-09-17 |

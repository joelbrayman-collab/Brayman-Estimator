# Feature Gate FG-035: Project Work Structure + Time + Schedule + Performance + LEARN

| Attribute | Value |
|----------|--------|
| Feature Gate ID | `FG-035` |
| Feature Name | Project Work Structure, Time, Schedule, Performance, and LEARN V1 |
| Target Milestone | Operational / learning loop (Time, Schedule, MONITOR labour-hours remainder, Closeout LEARN quality, calibration). Complements V1-08 / V1-11. **Does not rescore V1.** |
| Module | **Projects** owns work-structure catalog and Project Element / Activity instances. Estimating owns `LabourTask` / snapshots (referenced). BUILD owns Time Entry (`labour_time_entries`). Projects will own Schedule overlay when SCH is authorized ([fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md) **RECORDED**; [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md) **DESIGN FROZEN / NOT IMPLEMENTATION-AUTHORIZED**). MONITOR remains a consumer. LEARN remains a consumer. Project Controls owns `ChangeOrder` (referenced by SCOPE). |
| Date | 2026-09-15 |
| Status | **OPEN / PARTIAL.** TAX/WBS **IMPLEMENTED**. SCOPE **IMPLEMENTED**. TIME **IMPLEMENTED**. SCH **ARCHITECTURE RECORDED / IMPLEMENTATION PREFLIGHT COMPLETE / NOT AUTHORIZED**. PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. |
| Architecture | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. SCH architecture [fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md) **RECORDED**. SCH implementation freeze [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md) **DESIGN FROZEN / NOT IMPLEMENTATION-AUTHORIZED**. Product direction [project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) **FUTURE / RECORDED**. [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED** (not reopened). [FG-032](FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED** (not rewritten). [FG-033](FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED**. [FG-034](FG-034-account-recovery-and-transactional-email.md) **CLOSED**. |
| Related ADRs | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md). [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md). [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md). [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md). [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md). |
| Prerequisites | FG-008 labour snapshots. FG-011 Project Hub. FG-018 office auth. ADR-053 Accepted. |

**Subsequent status (2026-09-15):** SCOPE **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. Additive **`f4c5d6e7f8a9`**. Evidence [fg035-scope-live-bounded-uat-record.md](../testing/fg035-scope-live-bounded-uat-record.md). TIME **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. Additive **`f5d6e7f8a9b0`**. Evidence [fg035-time-live-bounded-uat-record.md](../testing/fg035-time-live-bounded-uat-record.md). SCH architecture **PREFLIGHT COMPLETE / RECORDED**. SCH implementation **PREFLIGHT COMPLETE / DESIGN FROZEN / NOT IMPLEMENTATION-AUTHORIZED** ([fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md)). SCH / PERF / CLOSE / LEARN / QB-T remain **NOT AUTHORIZED**. [architecture/interactive-help-voice-and-user-manual-future-record.md](../architecture/interactive-help-voice-and-user-manual-future-record.md) remains **COMPLETE FOR PRODUCT-DIRECTION RECORDING / NOT IMPLEMENTATION-AUTHORIZED**. Do **not** implement Help, Voice, Manual, or Schedule from this gate.

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / PARTIAL** |
| TAX/WBS | **IMPLEMENTED** — baseline + org catalog; Project Element / Activity instances; explicit EstimateLabourSnapshot seed; Hub Project work |
| SCOPE | **IMPLEMENTED** — ORIGINAL / CHANGE_ORDER / EXTRA_WORK lineage on Project work; Change Order deltas; Extra Work; Hub/Field presentation |
| TIME | **IMPLEMENTED** |
| SCH | **NOT AUTHORIZED** — architecture **RECORDED**; implementation **PREFLIGHT COMPLETE / DESIGN FROZEN** ([fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md)) |
| PERF | **NOT AUTHORIZED** |
| CLOSE | **NOT AUTHORIZED** |
| LEARN | **NOT AUTHORIZED** |
| QB-T | **NOT AUTHORIZED** |
| Schema / Alembic | Additive TAX/WBS **`f3b4c5d6e7f8`** revises **`f2a3b4c5d6e7`**. Additive SCOPE **`f4c5d6e7f8a9`** revises **`f3b4c5d6e7f8`**. Additive TIME **`f5d6e7f8a9b0`** revises **`f4c5d6e7f8a9`** |
| V1 scoring | **NOT RESCORED** (**60% / 4 of 11**) |

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH NOT AUTHORIZED (ARCHITECTURE RECORDED; IMPLEMENTATION PREFLIGHT COMPLETE)
PERF NOT AUTHORIZED
CLOSE NOT AUTHORIZED
LEARN NOT AUTHORIZED
QB-T NOT AUTHORIZED
ONE LOOP
ONE PLATFORM / ONE CODEBASE
ORG EXTENSIONS ARE CONFIGURATION
FG-023 NOT REOPENED
FG-032 NOT REWRITTEN
V1 NOT RESCORED
```

---

## Purpose

Provide the complete operational / learning loop recorded in [project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) and bounded by [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md):

FROZEN ESTIMATE VERSION → PROJECT WORK STRUCTURE → SCHEDULE / ASSIGNMENT → FIELD TIME → TIME APPROVAL → APPROVED LABOUR ACTUALS → MONITOR / ALERTS → CLOSEOUT REVIEW → LEARN → HUMAN-ACCEPTED CALIBRATION.

TAX/WBS is the foundation every later slice consumes. Later slices are **not** authorized merely because this Feature Gate exists.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | There is no Project → Element → Activity work authority. Time, Schedule, labour-hours MONITOR, Extra Work, Closeout LEARN quality, and calibration cannot share one structure. |
| 2 | Who is the user? | Office contractor (TAX/WBS configuration and Hub seed). Later slices add field workers (Time / Extra Work) and PM approval. Not customers. |
| 3 | Which module owns it? | Projects owns WBS catalog and instances. Estimating owns LabourTask/snapshots. BUILD will own Time. MONITOR/LEARN consume. Project Controls owns ChangeOrder. |
| 4 | What data does it own (TAX/WBS + SCOPE)? | TAX/WBS tables plus `project_work_scope_deltas`, `project_work_scope_history`, and `scope_origin` / `change_order_id` on Project work. |
| 5 | What data does it reference? | `Organization`, `Project`, `EstimateVersion`, `EstimateLabourSnapshot`, `LabourTask`, `ChangeOrder`. |
| 6 | What may it change? | Additive WBS + SCOPE schema; Hub BUILD Project work panel; Work types office catalog; Field Extra work surface; navigation. |
| 7 | What must it not change? | `ProjectCommercialContext`; `LabourTask` semantics; `ChangeOrder` commercial lifecycle; `ProjectDirectCostActual`; Field capture; FG-023 MONITOR money projection; FG-032 packages; EST-2026-0019; V1 score. |
| 8 | What are the acceptance criteria? | TAX/WBS: three-layer taxonomy; explicit locked/Accepted snapshot seed. SCOPE: original immutable; CO deltas; Extra Work; tenant CO safety; Hub/Field copy; tests + live migrate. Full gate close requires all eight slices. |
| 9 | What tests are required? | Dedicated TAX/WBS and SCOPE tests; Alembic upgrade/downgrade/fresh DB; Hub/catalog/Field office tests; tenant isolation; focused regression; full suite. |
| 10 | What documentation must be updated? | This gate; ADR-053; module/index/continuity docs; UAT records. No V1 rescore. |
| 11 | Does it require an ADR? | **Yes.** ADR-053. |
| 12 | What is explicitly out of scope for this prompt? | TIME, SCH, PERF, CLOSE, LEARN, QB-T, clock-in, Crew Template catalog, CPM, live Postmark, language audit, Time/Schedule UI. |

---

## Complete workstream slices

### TAX/WBS — Work taxonomy and Project work structure

**Status: IMPLEMENTED (this prompt).**

Baseline catalog + organization extensions + Project instances. Work-structure Project Type is **not** commercial `project_type`. Activity may reference LabourTask. Explicit Hub **Build project work** from locked/Accepted `EstimateVersion` with labour snapshots. Pins are immutable. Duplicate seed fail-closed. Evidence [testing/fg035-tax-wbs-live-bounded-uat-record.md](../testing/fg035-tax-wbs-live-bounded-uat-record.md).

**STOP:** no Time; no Schedule.

### SCOPE — Scope origin, Extra Work, Change Order overlay

**Status: IMPLEMENTED (this prompt).**

Original Estimate-seeded work is immutable historical evidence. Eligible Change Orders (Approved / Invoiced) add work or labour/quantity deltas. Draft / unapproved COs cannot become authorized Project scope. Extra Work is operational capture before a CO exists. `ChangeOrder` remains the sole commercial SoR. Evidence [testing/fg035-scope-live-bounded-uat-record.md](../testing/fg035-scope-live-bounded-uat-record.md).

**STOP:** no Schedule.

### TIME — Field duration entry and approval

**Status: IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS.** Duration-based Time Entry (`labour_time_entries` / `labour_time_history`). Worker enters Project → work → hours. SCOPE lineage is inherited via `inherit_scope_lineage()`. Extra Work uses existing `create_extra_work`. No Draft. No clock-in. No offline Time sync. Submitted is not approved actual. Self-approval fail-closed. Approved labour query: `approved_labour_hours()`. Field `/field/.../time` + My time; office `/time`; Hub `#hub-time`. Additive **`f5d6e7f8a9b0`**. Evidence [testing/fg035-time-live-bounded-uat-record.md](../testing/fg035-time-live-bounded-uat-record.md).

**STOP:** no Schedule; no labour-budget alerts; no QB Time export.

### SCH — Dynamic Schedule + assignment + desktop/iPhone calendar

**Status: NOT AUTHORIZED.** Architecture **PREFLIGHT COMPLETE / RECORDED**. Implementation **PREFLIGHT COMPLETE / DESIGN FROZEN** 2026-09-15. Records [architecture/fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md) and [architecture/fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md). First product slice when later authorized: **SCH-A** (items + history + Company/Hub forms). No Crew, assignment, dependencies, iPhone, or Time suggestion in SCH-A. No new ADR. Additive migration **not created**. Do **not** implement Schedule from this slice heading.

### PERF — Labour-hours performance, alerts, Needs Attention, three MONITOR views

**Status: NOT AUTHORIZED.**

### CLOSE — Closeout review and LEARN evidence quality

**Status: NOT AUTHORIZED.**

### LEARN — Comparability, recommendations, calibration provenance

**Status: NOT AUTHORIZED.**

### QB-T — Approved-time export readiness

**Status: NOT AUTHORIZED.**

---

## Production boundary

```text
TAX/WBS: LOCAL OFFICE UAT PROVEN.
SCOPE: LOCAL OFFICE UAT PROVEN.
TIME: LOCAL OFFICE SYNTHETIC UAT PROVEN.
LATER SLICES: NOT AUTHORIZED.
DO NOT IMPLEMENT SCHEDULE FROM THIS GATE ALONE.
V1 NOT RESCORED.
```

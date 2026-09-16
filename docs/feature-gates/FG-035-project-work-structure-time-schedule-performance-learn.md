# Feature Gate FG-035: Project Work Structure + Time + Schedule + Performance + LEARN

| Attribute | Value |
|----------|--------|
| Feature Gate ID | `FG-035` |
| Feature Name | Project Work Structure, Time, Schedule, Performance, and LEARN V1 |
| Target Milestone | Operational / learning loop (Time, Schedule, MONITOR labour-hours remainder, Closeout LEARN quality, calibration). Complements V1-08 / V1-11. **Does not rescore V1.** |
| Module | **Projects** owns work-structure catalog and Project Element / Activity instances. Estimating owns `LabourTask` / snapshots (referenced). BUILD owns Time Entry (`labour_time_entries`). Projects owns Schedule overlay (`work_schedule_items` / `work_schedule_history`) for **SCH-A** and SCH-B assignments (`work_schedule_assignments`). Organization owns optional Crew (`organization_crews` / `organization_crew_members`). SCH architecture [fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md) **RECORDED**. Design freeze [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md). MONITOR remains a consumer. LEARN remains a consumer. Project Controls owns `ChangeOrder` (referenced by SCOPE). |
| Date | 2026-09-15 |
| Status | **OPEN / PARTIAL.** TAX/WBS **IMPLEMENTED**. SCOPE **IMPLEMENTED**. TIME **IMPLEMENTED**. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH overall **OPEN / PARTIAL**. SCH-C / SCH-D **NOT AUTHORIZED**. PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. |
| Architecture | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. SCH architecture [fg-035-sch-dynamic-scheduling-preflight.md](../architecture/fg-035-sch-dynamic-scheduling-preflight.md) **RECORDED**. SCH implementation freeze [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md) remains the design freeze. SCH-A product is **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Live migration is proven/reconciled from durable evidence; the 15 Sep 2026 reconciliation prompt did **not** apply it. Product direction [project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) **FUTURE / RECORDED**. [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED** (not reopened). [FG-032](FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED** (not rewritten). [FG-033](FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED**. [FG-034](FG-034-account-recovery-and-transactional-email.md) **CLOSED**. |
| Related ADRs | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md). [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md). [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md). [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md). [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md). |
| Prerequisites | FG-008 labour snapshots. FG-011 Project Hub. FG-018 office auth. ADR-053 Accepted. |

**Subsequent status (2026-09-16 SCH-B live migrate + bounded synthetic UAT):** SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Additive **`f7f8a9b0c1d2`** applied live (`f6e7f8a9b0c1` → **`f7f8a9b0c1d2 (head)`**). Live current = repository head. Synthetic Project **46**. Project **45** unchanged. EST-2026-0019 unchanged. Evidence [testing/fg035-sch-b-live-bounded-uat-record.md](../testing/fg035-sch-b-live-bounded-uat-record.md). SCH overall **OPEN / PARTIAL**. SCH-C / SCH-D **NOT AUTHORIZED**. No new ADR. V1 **not rescored**.

**Subsequent status (2026-09-16 SCH-B implementation):** SCH-B **IMPLEMENTED / TESTED / NOT LIVE-MIGRATED** at that pass. Additive **`f7f8a9b0c1d2`** parented on **`f6e7f8a9b0c1`**. Live current then remained **`f6e7f8a9b0c1`**. Project **46** was not created in that pass.

**Subsequent status (2026-09-15 SCH-A live-UAT reconciliation):** SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Live current = repository head **`f6e7f8a9b0c1`**. Live migration is proven/reconciled from the pre-SCH-A backup (`f5d6e7f8a9b0`, no schedule tables) versus current live `f6` with schedule tables present. The reconciliation prompt did **not** apply the migration and did **not** create a second UAT project. Existing Project **45** was preserved. Evidence [testing/fg035-sch-a-live-bounded-uat-record.md](../testing/fg035-sch-a-live-bounded-uat-record.md). SCH overall **OPEN / PARTIAL**. SCH-B / SCH-C / SCH-D **NOT AUTHORIZED**. SCOPE **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. Additive **`f4c5d6e7f8a9`**. TIME **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS**. Additive **`f5d6e7f8a9b0`**. SCH architecture **PREFLIGHT COMPLETE / RECORDED**. Design freeze remains [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md). PERF / CLOSE / LEARN / QB-T remain **NOT AUTHORIZED**. [architecture/interactive-help-voice-and-user-manual-future-record.md](../architecture/interactive-help-voice-and-user-manual-future-record.md) remains **COMPLETE FOR PRODUCT-DIRECTION RECORDING / NOT IMPLEMENTATION-AUTHORIZED**. Do **not** implement Help, Voice, Manual, or SCH-B/C/D from this gate.

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / PARTIAL** |
| TAX/WBS | **IMPLEMENTED** — baseline + org catalog; Project Element / Activity instances; explicit EstimateLabourSnapshot seed; Hub Project work |
| SCOPE | **IMPLEMENTED** — ORIGINAL / CHANGE_ORDER / EXTRA_WORK lineage on Project work; Change Order deltas; Extra Work; Hub/Field presentation |
| TIME | **IMPLEMENTED** |
| SCH | **OPEN / PARTIAL** — SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH overall **OPEN / PARTIAL**. SCH-C / SCH-D **NOT AUTHORIZED**. Architecture **RECORDED**; design freeze [fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md) |
| PERF | **NOT AUTHORIZED** |
| CLOSE | **NOT AUTHORIZED** |
| LEARN | **NOT AUTHORIZED** |
| QB-T | **NOT AUTHORIZED** |
| Schema / Alembic | Additive TAX/WBS **`f3b4c5d6e7f8`** revises **`f2a3b4c5d6e7`**. Additive SCOPE **`f4c5d6e7f8a9`** revises **`f3b4c5d6e7f8`**. Additive TIME **`f5d6e7f8a9b0`** revises **`f4c5d6e7f8a9`**. Additive SCH-A **`f6e7f8a9b0c1`** revises **`f5d6e7f8a9b0`**. Additive SCH-B **`f7f8a9b0c1d2`** revises **`f6e7f8a9b0c1`** (**live current = repository head**) |
| V1 scoring | **NOT RESCORED** (**60% / 4 of 11**) |

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH-B IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH OVERALL OPEN / PARTIAL
SCH-C / SCH-D NOT AUTHORIZED
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

**STOP (SCOPE slice, historical):** no Schedule from SCOPE. Subsequent SCH-A is a separate slice.

### TIME — Field duration entry and approval

**Status: IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS.** Duration-based Time Entry (`labour_time_entries` / `labour_time_history`). Worker enters Project → work → hours. SCOPE lineage is inherited via `inherit_scope_lineage()`. Extra Work uses existing `create_extra_work`. No Draft. No clock-in. No offline Time sync. Submitted is not approved actual. Self-approval fail-closed. Approved labour query: `approved_labour_hours()`. Field `/field/.../time` + My time; office `/time`; Hub `#hub-time`. Additive **`f5d6e7f8a9b0`**. Evidence [testing/fg035-time-live-bounded-uat-record.md](../testing/fg035-time-live-bounded-uat-record.md).

**STOP (TIME slice, historical):** no Schedule from TIME; no labour-budget alerts; no QB Time export. Subsequent SCH-A is a separate slice.

### SCH — Dynamic Schedule + assignment + desktop/iPhone calendar

**Status: SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS. SCH-B IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.** SCH overall **OPEN / PARTIAL**. SCH-C / SCH-D **NOT AUTHORIZED**. Architecture **PREFLIGHT COMPLETE / RECORDED**. Design freeze [architecture/fg-035-sch-implementation-preflight.md](../architecture/fg-035-sch-implementation-preflight.md). SCH-A: `WorkScheduleItem` / `work_schedule_items`, `WorkScheduleHistory` / `work_schedule_history`, `app/services/schedule.py`, Company `/schedule`, Hub `#hub-schedule`, form create/edit/retire. Additive **`f6e7f8a9b0c1`** (superseded as live current). SCH-B: `WorkScheduleAssignment` / `work_schedule_assignments`, optional `OrganizationCrew` / `OrganizationCrewMember`, dedicated `/settings/crews`, USER XOR Crew, ASSIGNED/UNASSIGNED history (Integer `assignment_id`, no FK), overlap warnings as read projection. Additive **`f7f8a9b0c1d2`** parented on **`f6e7f8a9b0c1`** (**live current = repository head**). No dependencies, iPhone, or Time suggestion. No new ADR.

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
SCH-A: IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.
SCH-B: IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS.
SCH OVERALL OPEN / PARTIAL.
SCH-C / SCH-D: NOT AUTHORIZED.
DO NOT BEGIN SCH-C FROM THIS GATE ALONE.
V1 NOT RESCORED.
```

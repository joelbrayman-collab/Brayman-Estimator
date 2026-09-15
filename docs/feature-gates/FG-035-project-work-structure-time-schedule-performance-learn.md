# Feature Gate FG-035: Project Work Structure + Time + Schedule + Performance + LEARN

| Attribute | Value |
|----------|--------|
| Feature Gate ID | `FG-035` |
| Feature Name | Project Work Structure, Time, Schedule, Performance, and LEARN V1 |
| Target Milestone | Operational / learning loop (Time, Schedule, MONITOR labour-hours remainder, Closeout LEARN quality, calibration). Complements V1-08 / V1-11. **Does not rescore V1.** |
| Module | **Projects** owns work-structure catalog and Project Element / Activity instances. Estimating owns `LabourTask` / snapshots (referenced). BUILD will own Time later. MONITOR remains a consumer. LEARN remains a consumer. Project Controls owns `ChangeOrder` (referenced later by SCOPE). |
| Date | 2026-09-15 |
| Status | **OPEN / PARTIAL.** TAX/WBS **IMPLEMENTED**. SCOPE / TIME / SCH / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. |
| Architecture | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. Product direction [project-element-authority-future-record.md](../architecture/project-element-authority-future-record.md) **FUTURE / RECORDED**. [FG-023](FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED** (not reopened). [FG-032](FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED** (not rewritten). [FG-033](FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED**. [FG-034](FG-034-account-recovery-and-transactional-email.md) **CLOSED**. |
| Related ADRs | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md). [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md). [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md). [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md). [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md). |
| Prerequisites | FG-008 labour snapshots. FG-011 Project Hub. FG-018 office auth. ADR-053 Accepted. |

**Subsequent status (2026-09-15):** Interactive Help / Voice / professional User Manual are recorded as **mandatory PRE-UAT V1** in [interactive-help-voice-and-user-manual-future-record.md](../architecture/interactive-help-voice-and-user-manual-future-record.md). They **do not interrupt** this gate. Do **not** implement Help, Voice, or the Manual from that record. Later FG-035 slices remain **NOT AUTHORIZED**.

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / PARTIAL** |
| TAX/WBS | **IMPLEMENTED** — baseline + org catalog; Project Element / Activity instances; explicit EstimateLabourSnapshot seed; Hub Project work |
| SCOPE | **NOT AUTHORIZED** |
| TIME | **NOT AUTHORIZED** |
| SCH | **NOT AUTHORIZED** |
| PERF | **NOT AUTHORIZED** |
| CLOSE | **NOT AUTHORIZED** |
| LEARN | **NOT AUTHORIZED** |
| QB-T | **NOT AUTHORIZED** |
| Schema / Alembic | Additive TAX/WBS **`f3b4c5d6e7f8`** revises **`f2a3b4c5d6e7`** |
| V1 scoring | **NOT RESCORED** (**60% / 4 of 11**) |

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE NOT AUTHORIZED
TIME NOT AUTHORIZED
SCH NOT AUTHORIZED
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
| 4 | What data does it own (TAX/WBS)? | `work_types`, `work_element_templates`, `work_activity_templates`, `project_work_elements`, `project_work_activities`, `project_work_structure_seeds`. |
| 5 | What data does it reference? | `Organization`, `Project`, `EstimateVersion`, `EstimateLabourSnapshot`, `LabourTask`. Later: `ChangeOrder` (SCOPE). |
| 6 | What may it change? | Additive WBS schema; Hub BUILD Project work panel; Work types office catalog; navigation. |
| 7 | What must it not change? | `ProjectCommercialContext`; `LabourTask` semantics; `ChangeOrder`; `ProjectDirectCostActual`; Field capture; FG-023 MONITOR money projection; FG-032 packages; EST-2026-0019; V1 score. |
| 8 | What are the acceptance criteria? | TAX/WBS: three-layer taxonomy; explicit locked/Accepted snapshot seed; fail-closed; idempotent; tenant isolation; Hub usable; tests + live migrate. Full gate close requires all eight slices. |
| 9 | What tests are required? | Dedicated TAX/WBS tests; Alembic upgrade/downgrade/fresh DB; Hub/catalog office tests; tenant isolation; focused regression; full suite. |
| 10 | What documentation must be updated? | This gate; ADR-053; module/index/continuity docs; UAT record. No V1 rescore. |
| 11 | Does it require an ADR? | **Yes.** ADR-053. |
| 12 | What is explicitly out of scope for this prompt? | SCOPE, TIME, SCH, PERF, CLOSE, LEARN, QB-T, clock-in, Crew Template catalog, CPM, live Postmark, language audit, Time/Schedule UI. |

---

## Complete workstream slices

### TAX/WBS — Work taxonomy and Project work structure

**Status: IMPLEMENTED (this prompt).**

Baseline catalog + organization extensions + Project instances. Work-structure Project Type is **not** commercial `project_type`. Activity may reference LabourTask. Explicit Hub **Build project work** from locked/Accepted `EstimateVersion` with labour snapshots. Pins are immutable. Duplicate seed fail-closed. Evidence [testing/fg035-tax-wbs-live-bounded-uat-record.md](../testing/fg035-tax-wbs-live-bounded-uat-record.md).

**STOP:** no SCOPE origin; no Time; no Schedule.

### SCOPE — Scope origin, Extra Work, Change Order overlay

**Status: NOT AUTHORIZED.**

### TIME — Field duration entry and approval

**Status: NOT AUTHORIZED.**

### SCH — Dynamic Schedule + assignment + desktop/iPhone calendar

**Status: NOT AUTHORIZED.**

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
LATER SLICES: NOT AUTHORIZED.
DO NOT IMPLEMENT TIME OR SCHEDULE FROM THIS GATE ALONE.
V1 NOT RESCORED.
```

# FG-035 SCH — Dynamic Project / Crew Scheduling — Architecture preflight

| Attribute | Value |
|-----------|--------|
| Status | **PREFLIGHT COMPLETE / ARCHITECTURE RECORDED.** Subsequent SCH-A is **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Subsequent SCH-B is **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Subsequent **2026-09-16:** platform-wide **warning law** **INFORMATIONAL ONLY / NON-BLOCKING**; SCH-C **PREFLIGHT PASS / NOT IMPLEMENTED**. This file remains the architecture SoR and does not authorize SCH-C product or SCH-D. |
| Date | 2026-09-15 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. TAX/WBS **IMPLEMENTED**. SCOPE **IMPLEMENTED**. TIME **IMPLEMENTED**. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. When SCH implementation is later authorized, extend ADR-053. Do **not** invent ADR-054 for Schedule. |
| Alembic | Live current = repository head **`f5d6e7f8a9b0 (head)`**. Expected SCH parent when later authorized: **`f5d6e7f8a9b0`**. **No migration this recording.** |
| Product | CalibraytAI |
| Source | 15 Sep 2026 repository-aware SCH reconnaissance (Cursor), accepted by ChatGPT Architect / Joel with three refinements recorded below. Product-direction input: [project-element-authority-future-record.md](project-element-authority-future-record.md). |

```text
FG-035 SCH:
PREFLIGHT COMPLETE
ARCHITECTURE RECORDED
NOT IMPLEMENTATION-AUTHORIZED
NO SECOND WORK MODEL
SCH OWNS WHEN + WHO
TIME OWNS WHAT ACTUALLY HAPPENED
NO NEW ADR
V1 NOT RESCORED
```

This document records the **complete** accepted SCH architecture: authority / data model **and** contractor-facing product workflow. It is **not** implementation authorization, schema/migration authorization, a Feature Gate close, a V1 rescore, or a UAT claim.

Do **not** implement Schedule from this file.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | Project work structure (`ProjectWorkElement` / `ProjectWorkActivity`) live. SCOPE lineage **IMPLEMENTED**. TIME duration entry **IMPLEMENTED**. `Project` has **no** start/end dates. `ProjectCommercialContext.schedule_condition` is commercial posture, not a calendar. No operational Crew, assignment, dependency, or calendar tables. Company Schedule / Hub Schedule / iPhone Schedule **do not exist**. |
| **Intended (this slice, when later authorized)** | Planning overlay on existing Project work: schedule items, assignments, optional Crew, lightweight dependencies, append-only schedule history, Company / Hub / iPhone projections of one authority, Time suggestion only. |
| **Future (not this slice)** | PERF labour-performance visuals on the calendar; Needs Attention engine; auto-slide; CPM; FG-008 Crew Template catalog; Help / Voice / Manual; QB-T. |

---

## 2. Core SCH law

SCH is a **planning overlay** on the existing Project work authority. It does **not** create a second work model.

```text
WORK AUTHORITY:
ORGANIZATION
→ PROJECT
→ PROJECT WORK ELEMENT
→ PROJECT WORK ACTIVITY

OPERATIONAL CHAIN:
WHAT WE THOUGHT     EstimateVersion + EstimateLabourSnapshot
WHAT IS AUTHORIZED  Project work + SCOPE lineage
WHAT IS SCHEDULED   SCH schedule items + assignments + lightweight dependencies
WHAT WAS WORKED     LabourTimeEntry submitted
WHAT IS ACTUAL      approved_labour_hours()
MONEY ACTUAL        ProjectDirectCostActual
```

Invariants:

- Schedule never creates Time.
- Scheduled time is not actual time.
- Submitted Time is not approved actual.
- Original scope remains immutable historical evidence.
- `ChangeOrder` remains the commercial Change Order SoR.
- `ProjectDirectCostActual` remains money.
- MONITOR remains a consumer. Do not reopen [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md).
- Do not rewrite [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md).
- One platform. One codebase. Organization-specific configuration is **data**, not tenant-specific code.

**SCH V1 owns the current scheduled work window.** There is **not** a second approved-but-unscheduled date authority. History preserves prior scheduled windows. Do not teach a product distinction between separate “planned dates” and “scheduled dates” for SCH V1. Internal column names are settled at implementation preflight.

---

## 3. Ownership

| Owner | Owns |
|-------|--------|
| **Projects** | Schedule items; schedule assignments; work dependencies; schedule material-change history; Company Schedule service/view; Project-filtered Hub Schedule |
| **Organization** | Optional Crew configuration (data) |
| **BUILD** | Time Entry; Time approval; `approved_labour_hours()` |
| **Field / iPhone Schedule** | Presentation of Projects-owned Schedule data. No data fork. |
| **MONITOR / PERF / CLOSE / LEARN / QB-T** | Consumers / later slices |

ADR-020 listed field “schedule/task updates” under BUILD. Company planning bars belong with the work structure (**Projects**). Field progress versus plan waits for PERF.

`User` + active `UserMembership` remains worker identity (TIME already uses `worker_user_id`). Do not invent an employee directory. Do not invent RBAC for SCH.

---

## 4. Conceptual data model

Names remain **provisional** until implementation authorization.

### A. WorkScheduleItem

One **current** scheduled calendar window against existing Project work.

Required: `organization_id`, `project_id`, `project_work_element_id`.  
Optional: `project_work_activity_id` (must belong to that Element).

SCH stores the governing **current scheduled work window**. Prior windows live in history, not as a parallel current date pair.

Do **not** add `Project.start_date` / `Project.end_date`. Do not overload `schedule_condition`.

**Project bar is derived:** minimum ACTIVE scheduled start → maximum active scheduled end for that Project. “Move the Project” is a **confirmed bulk shift** of that Project’s ACTIVE schedule items.

Default Company Schedule grain: **Project + major Element / phase**. Activity scheduling is progressive detail.

The item stores **no hours-worked**. Existing `estimated_hours` remains labour allowance, not calendar duration.

Retire (`INACTIVE`) rather than hard-delete referenced items.

### B. WorkScheduleAssignment

Child of a schedule item. Exactly one target: `worker_user_id` **or** `crew_id`. Not both.

Zero assignment rows = **UNASSIGNED** (valid).

Multiple USER rows on one item = “Ben + Matt” without requiring a Crew.

Worker = existing `User` + **active** organization `UserMembership`. Cross-org assignment fail-closed.

### C. OrganizationCrew + OrganizationCrewMember

Optional thin durable organization configuration.

Crew is **not**: FG-008 Crew Template; `ProductionRateStandard.crew_size_assumption`; historical `crew_size`; a display string; a mandatory contractor feature; `Subcontractor`.

Crew exists so organizations that operate named crews can schedule them and detect conflicts truthfully. Individual-only organizations remain valid.

**Historical truth:** crew conflict detection and later MONITOR / LEARN must not reconstruct a past booking using **only today’s** crew composition. Membership must preserve enough effective-period evidence that a historical schedule window can be interpreted as of the scheduled period. Exact effective-dating belongs to the implementation preflight. Architecture forbids “today’s roster is the past.”

### D. ProjectWorkDependency

Lightweight same-Project directed dependency. V1 default: **Element → Element**. Activity-level edges may be supported where the implementation design justifies them, in the same conceptual identity.

Requirements: same organization; same Project; no self-edge; cycles forbidden; no CPM; no lag/float engine; **no automatic schedule movement**.

Dependencies **WARN**. Sequence / unscheduled-predecessor facts are informational only and never control functionality. Self-edge and cycle remain validation failures. **KEEP / MOVE / REVIEW** are optional contractor actions / navigation affordances, not persisted states and not required to continue. Canonical: [project-element-authority-future-record.md](project-element-authority-future-record.md) **Platform-wide warning behavior**.

Dependencies hang on **work identity**, not on a dated bar, so they survive reschedule.

### E. WorkScheduleHistory

Append-only material planning history. Pattern: `project_work_scope_history` / `labour_time_history`.

Record: `CREATED`, `DATES_CHANGED`, `RETIRED`, `ASSIGNED`, `UNASSIGNED`, `DEPENDENCY_ADDED`, `DEPENDENCY_REMOVED`.

Do **not** record pan, zoom, hover, expand/collapse, filter, or other presentation noise.

---

## 5. Element / Activity window integrity

**Architect refinement (accepted):**

An Activity scheduled beneath an Element **must remain within** the governing Element scheduled window.

If the contractor attempts to move or extend an Activity outside that window, the product must require an explicit contractor decision to:

**A.** extend or move the governing Element window as part of the **same confirmed** scheduling action; **or**  
**B.** cancel / review the Activity move.

Do not silently create contradictory Element/Activity dates. Do not accept the contradiction and merely paint a warning during ordinary editing.

**Parent/child schedule-window integrity is stronger than a dependency warning.** Dependency conflicts remain warnings. Window integrity is a confirmed same-action constraint.

---

## 6. SCH conflicts

SCH owns deterministic scheduling facts and **exposes** them. It does **not** become the later global Needs Attention / performance engine.

1. Worker overlapping ACTIVE scheduled work.
2. Crew overlapping ACTIVE scheduled work.
3. Worker overlap through Crew membership versus another USER/CREW booking, using membership **effective for the scheduled period**.
4. Dependency sequencing conflict (successor starts before predecessor finishes) — **WARNING ONLY**; does not block Save.
5. Predecessor unscheduled while successor is scheduled — **WARNING ONLY**; does not block Save.
6. Authorized ACTIVE work not yet scheduled (awareness).
7. Invalid assignment to retired / inactive / cross-org identity.
8. Parent/child window violation on a **proposed** edit (must be resolved by §5, not left as a standing contradictory schedule).

Crew overlap uses historical membership truth (§4.C), not “who is on the crew today.”

---

## 7. SCH / PERF boundary

**SCH owns:** current scheduled dates; assignments; optional Crews; dependencies; deterministic booking/sequence conflicts; unscheduled authorized-work awareness; schedule material-change history; Schedule → Time suggestion.

**PERF later owns:** estimated vs approved labour; labour allowance consumption; projected labour overrun; progress vs labour; finish-date forecasting from production evidence; schedule performance analysis; broader Needs Attention; project performance forecasting; gross-margin forecasting; MONITOR labour-performance views.

Example: “Forms 43 / 40 hrs” is **PERF presentation**, not SCH V1.

SCH may later supply deterministic conflict facts to one governed performance/alert consumer. Do not implement that consumer in SCH. Do not independently recalculate the same labour-performance condition in Schedule, Hub, MONITOR, and Needs Attention later.

Change Order labour-hour impact on finish date is a **later recommendation** (contractor confirms UPDATE / KEEP / REVIEW). SCH V1 may flag new authorized work as unscheduled. Duration/forecast math waits for PERF.

---

## 8. SCOPE / Change Order / Extra Work

No parallel CO Schedule identity. No parallel Extra Work Schedule identity.

Existing Project work identity remains authoritative.

- Eligible Approved / Invoiced CO work (`scope_origin = CHANGE_ORDER`) is schedulable as ordinary Project work.
- Extra Work via existing SCOPE `create_extra_work` (`scope_origin = EXTRA_WORK`) is schedulable as ordinary Project work.
- New authorized work begins **UNSCHEDULED** until SCH gives it a window.
- Linking Extra Work to a Change Order later must **not** require replacing its schedule identity.
- Schedule never rewrites `ChangeOrder`.
- Draft / unapproved CO cannot create authorized schedulable Project scope.
- `inherit_scope_lineage()` remains SCOPE authority for Time (and for Schedule assignment lineage when implementation needs it). It does not create Time.

---

## 9. Company / Project / iPhone workflow

One assemble service. Filters only. No duplicate store.

### Company Schedule

Primary office planning surface. Default approximately **4–6 week** Month view.

Five-second contractor test, without explanation:

- What is happening now?
- What is next?
- What is coming?
- Where are we busy?
- Where are the conflicts?
- What authorized work is unscheduled?

Default visual level: **Project + major Element / phase**. Do not display every Activity simultaneously. Progressive disclosure.

Compact secondary pulse (ACTIVE JOBS / STARTING SOON / SCHEDULE CONFLICTS / UNSCHEDULED WORK) may exist only as visually secondary. Do not turn Schedule into a KPI dashboard.

### Project Schedule

Project Hub Schedule is a **Project-filtered view of the same records**. No second scheduling engine.

### Desktop

Architecture must support: visual Month planning; move Project (confirmed bulk); move Element; extend/shorten work; assignment; conflicts; expansion to Activity detail.

Direct manipulation is important. **Drag/drop must not be the only editing mechanism.** Accessible form editing remains required.

### iPhone

Same data. Different responsive presentation.

Architecturally support **TODAY / WEEK / MONTH**.

Do **not** shrink the desktop planning board onto the phone.

- **TODAY:** operational — my assignments / active jobs.
- **WEEK:** compact upcoming work.
- **MONTH:** simplified, readable next-month overview. Tap a Project for detail. Read-mostly. Limited adjustment only if a later authorized slice proves useful.

No data fork.

---

## 10. Human confirmation

The contractor confirms:

- initial scheduled dates
- assignment (including Unassigned)
- Project / Element move
- duration extension / shortening
- bulk movement of child schedule items
- whether to extend the Element window when an Activity would exceed it
- dependency response
- optional KEEP / MOVE / REVIEW affordances (not persisted, not required)

The system may warn or suggest. A warning does not require action.

The system does **not** silently move downstream work.  
The system does **not** silently resolve conflicts.  
The system does **not** create Time.

---

## 11. Time connection

Conceptual service boundary (names provisional):

```text
suggest_time_attribution(worker_user_id, work_date, organization_id)
→ zero or more {project_id, element_id, activity_id, schedule_item_id}
```

TIME remains authoritative. The worker confirms Project, Element, Activity, and hours.

If multiple Schedule assignments exist that day: show choices.  
If none: existing Time work-choice behavior (`list_time_work_choices()`) remains available.

`recent_worker_activities()` is **actual Time convenience**, not the Schedule suggestion. Keep them distinct.

Schedule duration never becomes `LabourTimeEntry.hours`.

SCOPE `inherit_scope_lineage()` remains authoritative for Time lineage.

---

## 12. Security / tenant isolation / retirement

- `organization_id` on every SCH durable row. Cross-org access fail-closed (404 / forbidden), consistent with TIME and work-structure.
- Assignment requires active membership in that organization.
- Crew members must be same-org users.
- Retire referenced schedule records. Do not silently rewrite history needed by MONITOR / LEARN.
- No hard delete of referenced Crew / schedule / dependency rows once history exists.

---

## 13. Migration / ADR / tests (later)

SCH will require an **additive** migration when implementation is later authorized.

Expected parent: **`f5d6e7f8a9b0`**.

Conceptual durable identities (provisional): `WorkScheduleItem`, `WorkScheduleAssignment`, `OrganizationCrew`, `OrganizationCrewMember`, `ProjectWorkDependency`, `WorkScheduleHistory`.

Likely indexes: organization + scheduled window; project + element; organization + worker assignment; organization + crew assignment.

Exact constraints, unique keys, and crew effective-dating belong to the **implementation preflight**. **Do not create a migration from this recording.**

**ADR:** Do **not** create another ADR. ADR-053 already governs shared work authority (F) and scheduled time is not actual time (G). When SCH implementation is authorized, **extend ADR-053** (Projects-owned schedule overlay, optional Crew, assignment, window integrity, warn-don’t-slide). Help/Voice recording’s “do not invent ADR-054” remains in force for that record; it is not a SCH ADR number.

Tests (when authorized, not now): tenant isolation; Element/Activity window integrity; unassigned; multi-user assignment without Crew; optional Crew overlap using period membership; DAG cycle rejection; suggestion does not insert Time; SCOPE/CO/Extra Work reuse work ids; Hub and Company views same records.

Product tests were **not** rerun for this docs-only recording. Governed TIME close remains historical: full suite **1083 passed**.

---

## 14. Explicitly not this recording

- Product code, models, routes, templates, CSS/JS, tests
- Alembic revision
- Schedule UI, drag/drop, Crew product, dependency product, conflict UI
- PERF, CLOSE, LEARN, QB-T
- Help / Voice / User Manual
- New Feature Gate or new ADR number
- V1 rescore
- EST-2026-0019 mutation
- Complete-library documentation audit

**STOP.** Return to ChatGPT Architect. Next governed step is a bounded **SCH implementation authorization / implementation preflight**, not another broad reconnaissance, and **not** product implementation from this file.

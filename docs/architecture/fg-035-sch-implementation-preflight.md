# FG-035 SCH — Implementation preflight / design freeze

| Attribute | Value |
|-----------|--------|
| Status | **DESIGN FROZEN.** Subsequent SCH-A product is **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS** (2026-09-15). Subsequent SCH-B product is **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS** (2026-09-16). This freeze remains the design SoR. SCH overall is **OPEN / PARTIAL**. |
| Date | 2026-09-15 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. TAX/WBS **IMPLEMENTED**. SCOPE **IMPLEMENTED**. TIME **IMPLEMENTED**. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. |
| Governing architecture | [fg-035-sch-dynamic-scheduling-preflight.md](fg-035-sch-dynamic-scheduling-preflight.md) **PREFLIGHT COMPLETE / ARCHITECTURE RECORDED**. This file does **not** redesign that record. |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Alembic | SCH-A revision **`f6e7f8a9b0c1`** parented on **`f5d6e7f8a9b0`**. SCH-B revision **`f7f8a9b0c1d2`** parented on **`f6e7f8a9b0c1`**. Live current = repository head **`f7f8a9b0c1d2`**. |
| Baseline | HEAD / origin/main at freeze **`94fc575a720751dadb36f9df70ae85f40b9680d3`** (`docs: freeze FG-035 SCH implementation design`). |

```text
FG-035 SCH (this freeze, historical):
IMPLEMENTATION PREFLIGHT COMPLETE
DESIGN FROZEN

Subsequent 2026-09-15 SCH-A:
IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS

Subsequent 2026-09-16 SCH-B:
IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
NO NEW ADR
V1 NOT RESCORED
NO NEW ADR
V1 NOT RESCORED
```

**Subsequent status (2026-09-16 SCH-B live migrate + bounded synthetic UAT):** SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. Live current = repository head **`f7f8a9b0c1d2`**. Evidence [fg035-sch-b-live-bounded-uat-record.md](../testing/fg035-sch-b-live-bounded-uat-record.md). This freeze remains the design SoR. Do **not** implement SCH-C / SCH-D from this file.

**Subsequent status (2026-09-15 reconciliation):** Live current then = repository head **`f6e7f8a9b0c1`**. Evidence [fg035-sch-a-live-bounded-uat-record.md](../testing/fg035-sch-a-live-bounded-uat-record.md). This freeze remains the design SoR.

This document freezes names, constraints, service boundaries, slice cuts, and the SCH-A test matrix so ChatGPT Architect can issue bounded implementation prompts without reopening architecture.

Do **not** implement SCH-C / SCH-D from this file.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current (at freeze)** | Architecture recorded. No schedule tables. `Project` has no start/end dates. `ProjectCommercialContext.schedule_condition` is commercial posture. TIME uses `work_date` (`Date`) and `worker_user_id`. |
| **Subsequent Current (SCH-A)** | Overlay tables `work_schedule_items` / `work_schedule_history` live at **`f6e7f8a9b0c1`**. `Project` still has no start/end dates. |
| **Intended (SCH-B–D when later authorized)** | Overlay identities and services frozen below, sliced SCH-B → SCH-D. |
| **Future (not SCH)** | PERF, Needs Attention, CPM, FG-008 Crew Template, Help / Voice / Manual, QB-T. |

Repository conventions this freeze follows:

- Table names: plural snake (`labour_time_entries`, `project_work_elements`).
- Status: `ACTIVE` / `INACTIVE` with named `CheckConstraint`.
- Tenant: `organization_id` String(50) FK `organizations.id`, fail-closed 404.
- FKs: `ondelete="RESTRICT"`.
- History: append-only; `actor_user_id` + `actor_display_name`; `event` CHECK.
- Calendar day: `sa.Date` (TIME `work_date`).
- Audit timestamps: naive UTC `datetime.utcnow`.
- Partial unique indexes: already used (`work_types`, snapshot pin).
- XOR / status CHECKs: already used (TIME, SCOPE, Subcontractor). Compatible with SQLite + Alembic.

---

## 2. Frozen durable identities

Conceptual names are **kept**. Repository naming does not require a rename.

| Concept | Model | Table | Owner | First slice |
|---------|--------|--------|--------|-------------|
| WorkScheduleItem | `WorkScheduleItem` | `work_schedule_items` | Projects | SCH-A |
| WorkScheduleHistory | `WorkScheduleHistory` | `work_schedule_history` | Projects | SCH-A |
| WorkScheduleAssignment | `WorkScheduleAssignment` | `work_schedule_assignments` | Projects | SCH-B |
| OrganizationCrew | `OrganizationCrew` | `organization_crews` | Organization | SCH-B |
| OrganizationCrewMember | `OrganizationCrewMember` | `organization_crew_members` | Organization | SCH-B |
| ProjectWorkDependency | `ProjectWorkDependency` | `project_work_dependencies` | Projects | SCH-C |

Files (do not create now):

- `app/models/schedule.py` — item, assignment, dependency, history
- `app/models/organization_crew.py` — crew + member
- `app/services/schedule.py` — assemble, mutate, conflicts, derived Project bar
- `app/services/organization_crew.py` — crew configuration (SCH-B)
- Register imports in `app/models/__init__.py` at implementation

Cross-org access: filter `organization_id`; missing/cross-org → 404, matching TIME `_project_or_404`.

No CASCADE delete of referenced schedule rows. Retire in service.

---

## 3. WorkScheduleItem (SCH-A)

One **current** scheduled calendar window against existing Project work.

### Columns

| Column | Type | Null | Notes |
|--------|------|------|--------|
| `id` | Integer PK | no | |
| `organization_id` | String(50) FK `organizations.id` RESTRICT | no | indexed |
| `project_id` | Integer FK `projects.id` RESTRICT | no | indexed |
| `project_work_element_id` | Integer FK `project_work_elements.id` RESTRICT | no | required grain |
| `project_work_activity_id` | Integer FK `project_work_activities.id` RESTRICT | yes | optional progressive detail |
| `scheduled_start` | Date | no | current window start |
| `scheduled_end` | Date | no | current window end |
| `status` | String(20) | no | `ACTIVE` / `INACTIVE`; default ACTIVE |
| `created_by_user_id` | Integer FK `users.id` RESTRICT | yes | actor |
| `created_by_display_name` | String(150) | no | snapshot |
| `created_at` | DateTime | no | utcnow |
| `updated_at` | DateTime | no | utcnow / onupdate |

Do **not** add `planned_start` / `planned_end`.
Do **not** add `Project.start_date` / `Project.end_date`.
Do **not** store hours-worked. `estimated_hours` remains labour allowance.

### Window field names

Frozen: **`scheduled_start`** and **`scheduled_end`**.

These are the **only** current window columns. They are not a pair competing with a second planned-date authority. Prior windows live in `work_schedule_history`.

### Date semantics

| Rule | Freeze |
|-------|--------|
| Type | `DATE`, not DateTime |
| Timezone | Civil calendar dates, same as TIME `work_date`. No org TZ column in SCH V1. `created_at` remains naive UTC DateTime. |
| Inclusive | **Inclusive–inclusive.** 15–17 Sep is three calendar days. |
| Duration days | `(scheduled_end - scheduled_start).days + 1` |
| Same-day | `scheduled_start == scheduled_end` is valid |
| Multi-day | `scheduled_end > scheduled_start` |
| Validation | `scheduled_end >= scheduled_start` (CHECK + service) |
| Future dates | Allowed (unlike TIME) |
| Past dates | Allowed (catch-up planning) |
| Overlap test | `A.start <= B.end AND B.start <= A.end` |

CHECK:

```text
ck_work_schedule_items_status
  status IN ('ACTIVE', 'INACTIVE')

ck_work_schedule_items_window
  scheduled_end >= scheduled_start
```

### Grain validation (service; SCH-A)

1. Element FK required. Element `organization_id` / `project_id` must match the item.
2. Activity optional. If set: Activity must belong to that Element; same org/project.
3. Element and Activity (if set) must be `ACTIVE` to **create** or keep an ACTIVE item.
4. Retiring work: service retires ACTIVE items on that Element/Activity. Do not hard-delete.

### One current window per work identity

Partial unique indexes (SQLite `sqlite_where`):

- `uq_work_schedule_items_active_element`
  unique (`project_work_element_id`) where `status = 'ACTIVE' AND project_work_activity_id IS NULL`
- `uq_work_schedule_items_active_activity`
  unique (`project_work_activity_id`) where `status = 'ACTIVE' AND project_work_activity_id IS NOT NULL`

Mutate dates on the same ACTIVE row. Do not insert a second ACTIVE window for the same grain.

An Element-level item **and** Activity-level items may coexist. The Element window **governs** child Activity windows.

### Indexes

- `ix_work_schedule_items_org_window` (`organization_id`, `scheduled_start`, `scheduled_end`)
- `ix_work_schedule_items_org_project` (`organization_id`, `project_id`, `status`)
- `ix_work_schedule_items_element` (`project_work_element_id`, `status`)

### Project bar (derived; never stored on Project)

For a Project:

```text
project_scheduled_start = MIN(scheduled_start) of ACTIVE items
project_scheduled_end   = MAX(scheduled_end)   of ACTIVE items
```

Empty → no Project bar. “Move the Project” = confirmed bulk shift of every ACTIVE item on that Project by N days, in **one transaction**, with window-integrity revalidation.

---

## 4. Parent / child window integrity (SCH-A)

**VALIDATION ERROR during mutation. Not a persisted standing conflict.**

An Activity item must satisfy:

```text
element.scheduled_start <= activity.scheduled_start
AND activity.scheduled_end <= element.scheduled_end
```

The governing Element window is the ACTIVE Element-level item (`project_work_activity_id IS NULL`). If the Element has no ACTIVE item, creating an Activity item is a validation error until the Element is scheduled (same transaction may create/extend both).

### Service transaction boundary

Single module: `app/services/schedule.py`.

| Operation | Behavior |
|----------|----------|
| `create_schedule_item` | Persist one item. Activity create must fit Element window or fail. |
| `update_schedule_window` | Resize/move one item. Activity may not leave Element. Shrinking an Element that would exclude children **fails** unless `companion_child_updates` is supplied in the same call. |
| `schedule_activity_with_element_adjustment` | Confirmed same-action path: persist Element window change **and** Activity window change in one commit, or neither. |
| `shift_project_schedule` | Confirmed bulk N-day shift of all ACTIVE items on the Project. |
| `retire_schedule_item` | Set `INACTIVE`. Append `RETIRED`. Do not hard-delete. |

If the contractor attempts an Activity move/extend outside the Element window and does **not** confirm Element adjustment: raise a service error. Do not write. Do not save a warning row.

SQLAlchemy `db.session` commit once at the end of the successful service function. Route/forms collect the confirmation flag; the service enforces atomicity.

Drag/drop is **not** required in SCH-A. Accessible form POST is required. Direct manipulation may be added later without changing this boundary.

---

## 5. WorkScheduleHistory (SCH-A)

Append-only material evidence. Pattern: `LabourTimeHistory` (`event`, `actor_user_id`, `actor_display_name`).

### Columns

| Column | Type | Null |
|--------|------|------|
| `id` | Integer PK | no |
| `organization_id` | String(50) FK RESTRICT | no |
| `work_schedule_item_id` | Integer FK `work_schedule_items.id` RESTRICT | yes for dependency events that hang on work identity; see below |
| `project_id` | Integer FK RESTRICT | no |
| `event` | String(32) | no |
| `actor_user_id` | Integer FK `users.id` RESTRICT | yes |
| `actor_display_name` | String(150) | no |
| `prior_scheduled_start` | Date | yes |
| `prior_scheduled_end` | Date | yes |
| `new_scheduled_start` | Date | yes |
| `new_scheduled_end` | Date | yes |
| `assignment_id` | Integer | yes | set for ASSIGNED / UNASSIGNED (SCH-B) |
| `dependency_id` | Integer | yes | set for DEPENDENCY_* (SCH-C) |
| `reason` | Text | yes |
| `created_at` | DateTime | no |

Dependency events hang on **work identity**, not only a dated bar. For `DEPENDENCY_ADDED` / `DEPENDENCY_REMOVED`, `work_schedule_item_id` may be null; `project_id` + `dependency_id` + reason identify the edge. SCH-A still creates the history table so later slices do not fight SQLite CHECK rewrites.

### Events (full vocabulary frozen at SCH-A table create)

```text
CREATED
DATES_CHANGED
RETIRED
ASSIGNED
UNASSIGNED
DEPENDENCY_ADDED
DEPENDENCY_REMOVED
```

CHECK `ck_work_schedule_history_event` includes the full set from SCH-A so SCH-B/C do not recreate the table. Unused event strings are unused, not a product claim.

Do **not** log pan, zoom, hover, expand/collapse, filter.

Crew membership changes do **not** write Schedule history. Period truth lives on `organization_crew_members` (option A). Schedule history records ASSIGNED/UNASSIGNED of a crew_id to an item, not roster edits.

Index: `ix_work_schedule_history_org_item` (`organization_id`, `work_schedule_item_id`).

---

## 6. WorkScheduleAssignment (SCH-B)

Child of a schedule item. Exactly one target.

### Columns

| Column | Type | Null |
|--------|------|------|
| `id` | Integer PK | no |
| `organization_id` | String(50) FK RESTRICT | no |
| `work_schedule_item_id` | Integer FK `work_schedule_items.id` RESTRICT | no |
| `worker_user_id` | Integer FK `users.id` RESTRICT | yes |
| `crew_id` | Integer FK `organization_crews.id` RESTRICT | yes |
| `created_at` | DateTime | no |

No `UNASSIGNED` row. Zero assignment rows = UNASSIGNED.

### XOR

CHECK `ck_work_schedule_assignments_xor`:

```text
(
  (worker_user_id IS NOT NULL AND crew_id IS NULL)
  OR
  (worker_user_id IS NULL AND crew_id IS NOT NULL)
)
```

SQLite/Alembic already use CHECKs (TIME hours/status; work-structure status).

Partial unique:

- `uq_work_schedule_assignments_item_user` unique (`work_schedule_item_id`, `worker_user_id`) where `worker_user_id IS NOT NULL`
- `uq_work_schedule_assignments_item_crew` unique (`work_schedule_item_id`, `crew_id`) where `crew_id IS NOT NULL`

Multiple USER rows on one item = Ben + Matt without a Crew.

### Write validation (service)

- Item must be ACTIVE, same org.
- USER: `User.is_active` and active `UserMembership` for that org (TIME `_require_membership`).
- CREW: crew `ACTIVE`, same org.
- Inactive user/membership/crew: reject new assignment. Existing rows are retired (`UNASSIGNED` history + delete assignment row is allowed because the item remains; assignment is not historical SoR — history row preserves the event). Prefer **delete the assignment row** after appending `UNASSIGNED`, matching “retire referenced schedule records” for items while treating assignments as current children. Do not hard-delete the parent item.
- Cross-org: fail-closed.

Indexes: `ix_work_schedule_assignments_org_worker` (`organization_id`, `worker_user_id`); `ix_work_schedule_assignments_org_crew` (`organization_id`, `crew_id`).

---

## 7. OrganizationCrew + OrganizationCrewMember (SCH-B)

Optional thin org configuration. **Not** FG-008 Crew Template, `crew_size_assumption`, historical `crew_size`, `Subcontractor`, or a display string.

### OrganizationCrew

| Column | Type | Null |
|--------|------|------|
| `id` | Integer PK | no |
| `organization_id` | String(50) FK RESTRICT | no |
| `name` | String(120) | no |
| `status` | String(20) | no | ACTIVE / INACTIVE |
| `created_at` | DateTime | no |
| `updated_at` | DateTime | no |

CHECK status ACTIVE/INACTIVE.

Unique: `uq_organization_crews_org_name` (`organization_id`, `name`). Retired crews keep the name; creating a new ACTIVE crew with the same name fails unless the old row is renamed. Service may reject duplicate ACTIVE names only via partial unique:

- `uq_organization_crews_org_active_name` unique (`organization_id`, `name`) where `status = 'ACTIVE'`

Retire (`INACTIVE`). No hard delete once a member or assignment history exists.

### OrganizationCrewMember — period truth

| Column | Type | Null |
|--------|------|------|
| `id` | Integer PK | no |
| `organization_id` | String(50) FK RESTRICT | no |
| `crew_id` | Integer FK `organization_crews.id` RESTRICT | no |
| `user_id` | Integer FK `users.id` RESTRICT | no |
| `effective_from` | Date | no |
| `effective_to` | Date | yes | NULL = open-ended |
| `created_at` | DateTime | no |

No `is_current` boolean. Open-ended = `effective_to IS NULL`.

### Effective-period semantics

| Rule | Freeze |
|------|--------|
| Inclusive | `effective_from` and `effective_to` are inclusive calendar dates |
| Open-ended | `effective_to IS NULL` means still a member |
| On a date D | `effective_from <= D AND (effective_to IS NULL OR D <= effective_to)` |
| Overlap with schedule window [S,E] | `effective_from <= E AND (effective_to IS NULL OR effective_to >= S)` |
| Overlapping rows | Forbidden for the same (`crew_id`, `user_id`). Service-enforced (SQLite has no exclusion constraint). |
| Member retirement | Set `effective_to` to the last inclusive day. Do not delete the row. |
| Crew retirement | Crew `INACTIVE`. Existing member rows stay. New assignments rejected. Historical overlap still uses period rows. |
| User loses org membership | New assignments rejected. Historical member rows remain. Do not rewrite `effective_to` silently; office may close the membership period explicitly. |
| Write-time member add | User must have active org membership **today**. Period still records `effective_from`/`effective_to`. |

This is **not** HR employment history. It is only enough to reconstruct who was on a named crew during a scheduled window.

Conflict detection **must** use membership overlapping the **schedule item window**, not “who is on the crew today.”

---

## 8. ProjectWorkDependency (SCH-C)

**SCH-C ships Element → Element only.** Generic Element/Activity edges wait. Two nullable XOR grains now would add complexity without SCH-A/B value. Adding Activity endpoints later is an additive nullable pair + CHECK, not a redesign.

### Columns

| Column | Type | Null |
|--------|------|------|
| `id` | Integer PK | no |
| `organization_id` | String(50) FK RESTRICT | no |
| `project_id` | Integer FK RESTRICT | no |
| `predecessor_element_id` | Integer FK `project_work_elements.id` RESTRICT | no |
| `successor_element_id` | Integer FK `project_work_elements.id` RESTRICT | no |
| `status` | String(20) | no | ACTIVE / INACTIVE |
| `created_at` | DateTime | no |

CHECK: status; `predecessor_element_id != successor_element_id`.

Unique ACTIVE edge: `uq_project_work_dependencies_active_edge` unique (`predecessor_element_id`, `successor_element_id`) where `status = 'ACTIVE'`.

### Service rules

- Same org, same Project, both Elements ACTIVE at create.
- No self-edge (CHECK + service).
- Cycle forbidden: DFS/Kahn on ACTIVE edges in the Project. Reject the write.
- No lag, float, CPM, or automatic successor movement.
- Warn on sequence conflict (successor ACTIVE start < predecessor ACTIVE end, using Element-level schedule items). Contractor KEEP / MOVE / REVIEW.
- Predecessor unscheduled while successor scheduled: WARN, not a validation error.
- Retire (`INACTIVE`) rather than hard-delete. History `DEPENDENCY_REMOVED`.
- Dependencies hang on Element identity, so they survive reschedule of bars.

---

## 9. Deterministic SCH conflict service

One read boundary inside `app/services/schedule.py` (split later only if the file becomes unwieldy; TIME kept one module).

Conceptual:

```text
list_schedule_conflicts(organization_id, *, project_id=None, window_start=None, window_end=None)
```

Returns deterministic facts. **Not** PERF. **Not** Needs Attention.

| Fact | Slice | Persist? |
|------|-------|----------|
| Parent/child window violation | SCH-A | **No.** Validation error on mutate. |
| Unscheduled authorized ACTIVE Element | SCH-A | Read-only awareness |
| Invalid/retired assignment identity | SCH-B | Exposed; writes already fail-closed |
| USER overlapping ACTIVE items | SCH-B | Exposed warning |
| CREW overlapping ACTIVE items | SCH-B | Exposed warning |
| User-through-Crew overlap vs USER/CREW booking using **period** membership | SCH-B | Exposed warning |
| Dependency sequence | SCH-C | Exposed warning |
| Predecessor unscheduled / successor scheduled | SCH-C | Exposed warning |

Contractor resolves warnings. System does not auto-move.

PERF remains forbidden: no labour allowance consumption, overrun, progress vs labour, GM forecast, global Needs Attention.

---

## 10. Assemble service (Company / Hub / later iPhone)

One authority. Filters only.

```text
assemble_schedule(
    organization_id,
    *,
    project_id=None,
    window_start=None,
    window_end=None,
    include_activities=False,
    include_conflicts=False,
)
```

| Concern | Freeze |
|---------|--------|
| Org isolation | Required argument; never infer another org |
| Project filter | `project_id` set → Hub; unset → Company |
| Window | Inclusive dates; default Company view ≈ next 4–6 weeks from today |
| Default grain | Project derived bars + Element-level ACTIVE items |
| Activity | Only when `include_activities=True` (progressive disclosure) |
| Unscheduled | ACTIVE Elements with no ACTIVE Element-level item |
| Assignments | SCH-B projection; SCH-A returns empty assignment lists |
| Conflicts | When `include_conflicts=True`; SCH-A may include unscheduled + would-be window errors only as mutate-time errors |

`assemble_project_hub` later calls `assemble_schedule(..., project_id=project.id)` and exposes `hub["schedule"]`. No second store.

SCH-A does not require `include_conflicts` for worker overlap (no assignments yet). Unscheduled work is in the assemble payload.

---

## 11. Routes / UI ownership (no pixels)

| Surface | Ownership | Freeze |
|---------|----------|--------|
| Company Schedule | Projects | New `app/routes/schedule.py` blueprint `schedule_bp`, prefix `/schedule`. Org-wide planning does not belong stuffed into `projects.py` or `work_structure.py`. |
| Nav | `app/navigation.py` | Enable **Schedule** beside Projects (`schedule.company`). Not under Project Controls. |
| Hub Schedule | Projects | `#hub-schedule` in `app/templates/projects/detail.html`; assemble via `project_hub.py`. |
| Item create/edit/retire | Projects | POST `/schedule/items` and `/schedule/items/<id>` form routes; service in `schedule.py`. Accessible HTML forms **required**. Drag/drop **not** SCH-A. |
| Templates | Projects | `app/templates/schedule/company.html`, `app/templates/schedule/item_form.html` |
| Crew config | Organization | SCH-B: `app/routes/settings.py` or small `app/routes/organization_crew.py` under `/settings/crews`. Prefer dedicated crew routes if settings.py would bloat. |
| Dependencies | Projects | SCH-C POST on schedule blueprint |
| iPhone Today/Week/Month | Field presentation | SCH-D: `field_bp` routes `/field/schedule/today` etc. calling `assemble_schedule`. Templates `app/templates/field/schedule_*.html`. No data fork. |

Register `schedule_bp` in `app/__init__.py` at implementation.

Contractor copy: use `app/presentation/contractor_copy.py` for visible labels. Do not display raw `INACTIVE` / table names.

---

## 12. Time suggestion (SCH-D, not SCH-A)

Schedule never creates Time. TIME remains authoritative for hours and confirmation.

```text
suggest_time_attribution(worker_user_id, work_date, organization_id)
→ list of {project_id, element_id, activity_id, schedule_item_id}
```

Place on `app/services/schedule.py`. TIME calls it; TIME does not own the query.

- Candidate from ACTIVE items whose window includes `work_date` and assignment matches the worker (direct USER or Crew membership **effective that date**).
- Worker still confirms Project / Element / Activity / hours via existing TIME submit.
- Multiple hits → choices. Zero hits → existing `list_time_work_choices()`.
- `recent_worker_activities()` stays TIME convenience, distinct from suggestion.
- Schedule duration never becomes `LabourTimeEntry.hours`.
- `inherit_scope_lineage()` remains SCOPE authority.

**SCH-D**, not SCH-A.

---

## 13. Additive migration sketch (do not create)

Parent: **`f5d6e7f8a9b0`**.

Revision **ids assigned at implementation**. Do not mint Alembic files now. Sequential hex after TIME is likely `f6e7f8a9b0c1` then `f7f8a9b0c1d2` then `f8a9b0c1d2e3` — treat as **expected tokens only**.

Prefer **one migration per independently usable slice** (TAX/WBS, SCOPE, TIME each shipped one revision).

### SCH-A revision

Purpose: schedule items + history + Company/Hub read/write of windows.

Upgrade order:

1. `work_schedule_items` (FKs to org, project, element, activity, user)
2. indexes + CHECKs + partial uniques
3. `work_schedule_history` with **full** event CHECK

Downgrade: drop history, then items.

SQLite: `batch_alter_table` only if altering existing tables (should not be needed). Fresh DB: models + migration graph one head.

Does **not** touch `projects`, TIME, or work-structure tables except FK targets.

### SCH-B revision

Parent: SCH-A.

1. `organization_crews`
2. `organization_crew_members`
3. `work_schedule_assignments` with XOR CHECK

Downgrade reverse.

### SCH-C revision

Parent: SCH-B.

1. `project_work_dependencies`

History events already in SCH-A CHECK.

### SCH-D

No new durable tables expected. Suggestion is a query.

Do not create one giant SCH migration “for completeness.”

---

## 14. Implementation slices

Architect candidate **accepted**, with two refinements:

- SCH-A **does** include Activity-level items and parent/child integrity, because Element-only dates without the invariant would have to be rewritten.
- SCH-A **does not** include Crew, assignment, dependencies, iPhone, or Time suggestion.

### SCH-A — Schedule core

| Field | Content |
|-------|---------|
| Product value | Company + Hub calendar of authorized work; derived Project bars; unscheduled awareness; form create/move/resize/retire |
| Schema | `work_schedule_items`, `work_schedule_history` |
| Services | `app/services/schedule.py`; Hub reads through `assemble_project_hub` |
| Routes/templates | `schedule_bp`; `#hub-schedule`; nav Schedule |
| Tests | §15 |
| Migration | one additive revision parented on `f5d6e7f8a9b0` |
| Live UAT | synthetic office UAT after tests; no EST-2026-0019 |
| Stop | No Crew, assignment, dependencies, iPhone Schedule, Time suggestion, PERF, drag/drop-only editing |

### SCH-B — Assignment + optional Crew

User assignment; optional Crew + period membership; overlap conflicts using period membership. Stop: no DAG, no iPhone, no TIME suggestion.

### SCH-C — Dependencies + SCH conflict presentation

Element→Element DAG; sequence / predecessor-unscheduled warnings; KEEP/MOVE/REVIEW. No auto-slide. No PERF.

### SCH-D — iPhone + Time connection

Today / Week / Month Field presentation of the same rows; `suggest_time_attribution`; worker confirms TIME. No automatic Time.

Do **not** merge SCH-A–D into one implementation prompt.

---

## 15. SCH-A test matrix (do not run now)

Dedicated file (when authorized): `tests/test_work_schedule_fg035.py`.

### Model / service

- Org isolation / cross-org 404
- Project/work ownership match
- Element schedule create
- Activity schedule create
- Activity must belong to Element
- Inactive work cannot receive ACTIVE item
- `scheduled_end >= scheduled_start`
- Same-day window
- Multi-day window
- Reject second ACTIVE item for same Element grain
- Reject second ACTIVE item for same Activity
- Activity outside Element window → error (no persist)
- Element extension + Activity move atomic success
- Same pair without confirmation → error, no partial write
- Retire sets INACTIVE; no hard delete
- History `CREATED` / `DATES_CHANGED` / `RETIRED`
- Presentation events not logged
- Derived Project min/max
- Unscheduled ACTIVE Element listed
- Bulk Project shift keeps child integrity or fails atomically
- No hours-worked column / no TIME insert

### Route / UI

- Company Schedule GET (org-scoped)
- Hub `#hub-schedule` Project-filtered same records
- Create / edit dates / retire POST
- No cross-org access
- Contractor-facing labels (no raw schema names)
- Desktop form usable without drag/drop

### Regression (focused, then full)

- `tests/test_work_structure_tax_wbs_fg035.py`
- `tests/test_work_scope_fg035.py`
- `tests/test_work_time_fg035.py`
- Hub / Field Web / MONITOR existing tests as in TIME close
- Full suite before SCH-A completion

### Migration

- upgrade, downgrade, fresh DB, one graph head

Do **not** run these tests in this docs-only freeze. Historical TIME close remains **1083 passed**.

---

## 16. ADR-053 additions when SCH-A is later authorized

Do **not** create ADR-054. When the first product slice is authorized, extend ADR-053 with:

- Projects owns Schedule overlay records and Company/Hub assemble.
- One current scheduled window (`scheduled_start` / `scheduled_end`); history holds prior windows.
- Project dates are derived; no `Project.start_date` / `end_date`.
- Schedule overlays existing `ProjectWorkElement` / `ProjectWorkActivity`.
- Assignments (later slice) are USER XOR optional Crew; zero rows = Unassigned.
- Crew is optional Organization configuration with period membership; not FG-008 / Subcontractor.
- Dependencies (later slice) warn; no automatic movement.
- Parent/child window integrity is a mutate-time validation error.
- Scheduled ≠ actual. Schedule may later suggest Time only.
- Deterministic SCH conflicts are not PERF.

Do not mark SCH implemented in the ADR until a product slice actually ships.

---

## 17. Explicitly not this freeze

- Product code, models, routes, templates, CSS/JS, tests
- Alembic revision / flask db upgrade
- SCH-B/C/D product
- PERF / CLOSE / LEARN / QB-T
- Help / Voice / Manual
- New Feature Gate or ADR number
- V1 rescore
- EST-2026-0019
- Redesign of [fg-035-sch-dynamic-scheduling-preflight.md](fg-035-sch-dynamic-scheduling-preflight.md)

**STOP.** Return to ChatGPT Architect. Next governed step is a **bounded SCH-A implementation authorization**, not SCH-B–D, and not product code from this file.

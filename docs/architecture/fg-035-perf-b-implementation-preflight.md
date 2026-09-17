# FG-035 PERF-B — Project Needs Attention implementation preflight

| Attribute | Value |
|-----------|--------|
| Status | **IMPLEMENTATION PREFLIGHT COMPLETE / DESIGN FROZEN / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** |
| Date | 2026-09-17 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Parent | PERF-A **SEALED** ([fg-035-perf-a-implementation-preflight.md](fg-035-perf-a-implementation-preflight.md)). Product PERF-A **`7a4b7000e2650eadf68b4ea44d48f75c65830c1f`**. |
| Desktop laws | [v1-desktop-contractor-experience-product-direction.md](v1-desktop-contractor-experience-product-direction.md) |
| Schema | **NONE.** If durable alert state is later found necessary: **STOP**. |
| Baseline | Parent HEAD / `origin/main` **`e809dcdbc3735aa91033f968a9ed562e749e6a0c`**. Alembic **`f9b0c1d2e3f4 (head)`**. |
| V1 | **NOT RESCORED** (**60% / 4 of 11**). PERF-B completion alone is **not** a scoring event. |

```text
FG-035 PERF-B:
IMPLEMENTATION PREFLIGHT COMPLETE
DESIGN FROZEN
OWNER DECISIONS A–G ACCEPTED
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
NO SCHEMA
NO MIGRATION
NO NEW ADR
NO NEW FEATURE GATE
V1 NOT RESCORED
NO PRODUCT
NO PERF-C
NO HOME OFFICE
NO FIELD
NO MONITOR MONEY CHANGE
```

**Subsequent status (2026-09-17 owner decisions / design freeze / seal):** Owner decisions **A–G ACCEPTED**. Design **FROZEN**. This file is the frozen PERF-B contract. Product implementation remains **NOT AUTHORIZED** until a separate implementation prompt.

Do **not** implement PERF-B, PERF-C, Home Office, notifications, progress, Forecast Finish, Print, QuickBooks, or banking from this file.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | PERF-A `assemble_project_performance` on Hub `#hub-labour` after `#hub-time` before MONITOR. Extra Work hours + `needs_review` copy already exist as labour arithmetic, **not** a Needs Attention engine. SCH-B/C `list_schedule_conflicts` already derives overlap + sequence / predecessor-unscheduled facts on `#hub-schedule`. TIME Waiting is already on Time and Labour. Warning law **INFORMATIONAL ONLY / NON-BLOCKING**. |
| **Intended (PERF-B, after separate implementation authorization)** | Project Hub derived **Needs Attention** answering: is there something about this Project I should look at? Design frozen below. |
| **Future (not PERF-B)** | PERF-C / company attention. Context-aware Home Office. Tomorrow readiness. Team notify. Week Ahead. Cash/payroll. Explicit progress. Forecast Finish. Unassigned upcoming work. |

---

## 2. Product question

PERF-A answers **how are we doing on labour?**

PERF-B answers **is there something about this Project I should look at?**

PERF-B must **not** become an AI risk engine, prediction engine, persisted alert system, red/yellow/green health score, progress engine, forecast engine, or blocking workflow.

No opaque score. No severity number. No AI judgment. No persisted alert rows.

Governing laws:

- Warnings inform. Humans decide.
- Validation protects data integrity. Warnings never control functionality.
- CalibraytAI earns the contractor’s attention.
- The interface has a limited attention budget.
- Do not manufacture urgency.
- Positive / ready states are valid information.

Every PERF-B attention fact is **informational only**. It must never block Time, Schedule, Change Orders, Project work, or another workflow. No mandatory acknowledgement. No required resolution.

---

## 3. Frozen owner decisions A–G

| ID | Decision | Freeze |
|----|----------|--------|
| A | 80% threshold | **ACCEPTED.** V1 module/service constant. **Not** organization-configurable. Attention threshold, not a conclusion that Project performance is poor. |
| B | Scheduled finish passed | **ACCEPTED.** ACTIVE current item, `scheduled_end < today`. Factual copy only. `end == today` is quiet. |
| C | Start / no Approved Time | **ACCEPTED.** `scheduled_start < today` and no APPROVED Time on the governed scheduled work. Not `<= today`. |
| D | SCH warning promotion | **ACCEPTED. SEQUENCE only.** Consume existing SCH SEQUENCE fact. Do not recalculate it. |
| E | Unassigned upcoming work | **NOT PERF-B.** Keep on Schedule and future Home Office / Tomorrow readiness. |
| F | Quiet positive state | **ACCEPTED.** Copy: **Nothing needs attention right now.** Do not say everything is on track. |
| G | Hub placement | **ACCEPTED.** Inside `#hub-labour`, Needs Attention **above** the labour summary. |

---

## 4. Reuse — do not duplicate

| Need | Authority to consume |
|------|----------------------|
| Allowed / Used / Remaining / Over / Waiting / Extra Work hours | `app/services/project_performance.py` `assemble_project_performance` |
| Allowed hours | `app/services/work_scope.py` `current_authorized_hours` (already inside PERF-A) |
| Current Extra Work vs authorized | `inherit_scope_lineage(activity)["authorized"]` — **already** how PERF-A buckets Extra Work. Do **not** use frozen `LabourTimeEntry.scope_origin` |
| Approved / Submitted hours | TIME `approved_labour_hours` / `pending_labour_hours` (already inside PERF-A) |
| Schedule window | ACTIVE `WorkScheduleItem.scheduled_start` / `scheduled_end` (`Date`, not time-of-day). “Today” = same `date.today()` convention as SCH-D Field |
| Existing Schedule warnings | `app/services/schedule.py` `list_schedule_conflicts(organization_id, project_id=...)` |
| Hub composition | `app/services/project_hub.py` already calls `assemble_project_performance` |

Do **not** duplicate the SCH conflict engine, PERF-A labour arithmetic, Time approval logic, or SCOPE lineage.

Do **not** use `list_unresolved_extra_work` as the PERF-B hour source. That helper lists unresolved Extra Work rows even with zero Time. PERF-B Extra Work attention requires **Approved Used > 0 or Submitted Waiting > 0** from the PERF-A Extra Work bucket.

---

## 5. Labour attention (frozen)

Grain: **Project authorized totals** from PERF-A `project` (`allowance_known`, `allowed_hours`, `used_hours`, `over_hours`). Element over/close stays visible in the existing Element table. Do **not** emit a second Element labour attention fact.

Waiting hours do **not** count toward Used or the 80%/100% tests.

Threshold: module/service constant in `app/services/project_performance.py` (for example `LABOUR_APPROACHING_RATIO = Decimal("0.80")`). **Not** org configuration.

80% is an **attention threshold**. It is **not** a conclusion that Project performance is poor.

| Candidate | Deterministic test | Title | Detail |
|-----------|--------------------|-------|--------|
| Getting close | `allowance_known` and Allowed > 0 and Used ≥ 80% of Allowed and Used < Allowed | Labour getting close | Used {used} of {allowed} hours |
| Allowance used | `allowance_known` and Allowed > 0 and Used == Allowed | Labour allowance used | Used {used} of {allowed} hours |
| Over allowance | `allowance_known` and Used > Allowed | Labour over allowance | Used {used} of {allowed} hours. Over by {over} hours |
| Unknown allowance | `allowance_known` is false | **No percentage fact** | Do not invent 80/100 without a denominator |
| Known zero, Used == 0 | Allowed known and Allowed == 0 and Used == 0 | **No labour attention** | Zero of zero is not useful |
| Known zero, Used > 0 | Allowed known and Allowed == 0 and Used > 0 | Labour over allowance | Used {used} of 0 hours. Over by {used} hours |

**Collapse:** at most **one** Project-level labour attention fact.

Order of truth: **Over allowance** supersedes **Allowance used** supersedes **Getting close**.

Do not show all three.

Hours format: same TIME `HOURS_QUANTUM` (`0.01`) as PERF-A Hub.

---

## 6. Waiting-for-approval (frozen)

**Do not** create a general Needs Attention item merely because Time is SUBMITTED.

Waiting is already on Time Hub and Labour Hub. SUBMITTED Time does not become Used.

Large/old approval backlog is **later**, not PERF-B, unless a separately governed deterministic contractor need is accepted.

---

## 7. Extra Work attention (frozen)

Unauthorized Extra Work where Approved Used > 0 **or** Submitted Waiting > 0 creates:

**Extra work needs review**

Detail summarizes factual hours, for example: 6 hours used · 2 hours waiting for approval.

Informational only. Does **not** require a Change Order. Does **not** block Time.

Current SCOPE lineage controls. When the work becomes authorized, the Extra Work attention fact **disappears**. Historical frozen Time `scope_origin` must **not** keep the fact alive.

Hub: keep Extra Work **hours** in the labour Extra Work block. The Needs Attention item carries the look-at signal. Do not also render `LABOUR_EXTRA_NEEDS_REVIEW` as a second urgency line.

---

## 8. Scheduled finish passed (frozen)

There is **no** durable completion state.

Do **not** say behind schedule, late, incomplete, or missed deadline.

**Rule:** an ACTIVE `WorkScheduleItem` whose **current** `scheduled_end < today`.

- Use current ACTIVE dates only. History is not a second window.
- `scheduled_end == today` does **not** create this fact.
- Future end does **not** create this fact.
- INACTIVE / retired items do **not** create this fact.

Title: **Scheduled finish passed**

Detail: Scheduled to finish {scheduled_end}

Do **not** infer completion.

---

## 9. Scheduled work has no approved Time (frozen)

Schedule is **date-grain**, not time-of-day.

**Rule:** `scheduled_start < today` on an ACTIVE item **and** that scheduled work still has no APPROVED Time attributable to the governed scheduled work.

Not `scheduled_start <= today`.

Do not create a premature attention item on the scheduled start date.

Time test:

- Activity-grain item: no `approved_labour_hours` on that `project_work_activity_id`
- Element-grain item: no `approved_labour_hours` on any Activity of that Element

Approved Time **suppresses** the fact. Submitted-only Time does **not** suppress it.

Title: **Scheduled work has no approved Time**

Detail: Scheduled to start {scheduled_start}

Do **not** say “work has not started.” Absence of Approved Time does not prove that.

If the same item also qualifies for scheduled finish passed, **both** facts may appear. They are different truths. They are not labour-style redundant 80/100/over.

---

## 10. Existing SCH warnings (frozen)

Consume `list_schedule_conflicts(..., project_id=project.id)`. Do **not** independently recalculate predecessor/successor conflict.

| Existing kind | PERF-B class |
|---------------|--------------|
| `SEQUENCE` | **INCLUDE** — consume the existing fact (`label` / `summary` / `review_url`) |
| `PREDECESSOR_UNSCHEDULED` | **KEEP ONLY IN SCHEDULE** |
| `USER` overlap | **KEEP ONLY IN SCHEDULE** |
| `CREW` overlap | **KEEP ONLY IN SCHEDULE** |
| `USER_THROUGH_CREW` overlap | **KEEP ONLY IN SCHEDULE** |
| Unscheduled authorized Elements | **KEEP ONLY IN SCHEDULE** |

Attention budget controls. Other SCH warning facts stay Schedule-only unless separately authorized later.

---

## 11. Unassigned upcoming work (frozen)

**Not PERF-B.**

Keep in Schedule and future Context-Aware Home Office / Tomorrow readiness.

Assignment urgency is context/time dependent. PERF-B is Project-level operational attention, not an evening briefing.

No automatic assignment. No blocking. Do not implement unassigned attention in PERF-B.

---

## 12. Positive state (frozen)

When zero PERF-B attention facts exist, show a quiet positive state.

Frozen copy: **Nothing needs attention right now.**

Do **not** say “Everything is on track.” That would claim more than current governed evidence proves.

The positive state confirms the attention projection actually checked the Project.

Do not manufacture an attention item.

Do not omit the section entirely.

---

## 13. Display order (frozen)

Deterministic display order:

1. Extra Work needs review
2. one Labour fact
3. Scheduled finish passed
4. Scheduled work has no approved Time
5. existing SEQUENCE fact

This is **display order**. It is **not** severity ranking, importance scoring, risk ranking, or priority scoring.

No numeric severity. No traffic-light score. No AI ranking.

Stable secondary sort: work identity (`element_id` / `activity_id` / `item_id`) then `fact_type`.

---

## 14. Project Hub surface (frozen)

Do **not** create another lifecycle product. Do **not** redesign Project Hub. Do **not** implement Home Office.

Inside existing `#hub-labour`:

1. Labour heading
2. Needs Attention (or quiet positive state)
3. Authorized labour summary
4. Element labour
5. Extra Work / related labour presentation as appropriate

Needs Attention appears **above** the labour summary.

---

## 15. Service / DTO (frozen)

PERF-B lives in the existing `app/services/project_performance.py` service family.

Extend the project-performance assembler or a bounded sibling helper as repository conventions support.

Reuse PERF-A labour facts, SCOPE current lineage, TIME Approved semantics, and the existing SCH warning projection.

No route-owned rules. No template-owned rules. No second Schedule warning engine. SEQUENCE reuse is filter-and-map of existing conflict dicts.

### Attention shape (names may follow repository style; meaning is frozen)

```text
attention:
  items:            # ordered
    fact_type       # stable key, not Hub-only
    title           # contractor-facing
    detail          # contractor-facing why
    project_id
    work:           # optional governed identity
      element_id
      activity_id
      schedule_item_id
      display_name
    destination     # optional existing URL / Hub fragment
  positive          # True when items is empty
  positive_title    # Nothing needs attention right now.
```

Purpose: future PERF-C and Context-Aware Home Office consume the same governed fact rather than scrape Hub HTML or recalculate it.

Include `project_id` on every item so company aggregation is not hard-coded as “organization-wide is the only useful view.”

Do **not** build an event bus, generic notification engine, persisted attention store, or generic rules framework.

Do **not** add a scope selector. Do **not** add Division schema.

---

## 16. Actions (frozen)

Optional links only. No mandatory action. No acknowledgement. No resolution workflow.

| Fact | Sufficient existing destination |
|------|----------------------------------|
| Extra work needs review | `#hub-labour` Extra Work hours + existing CO list |
| Labour over / used / close | `#hub-labour` |
| Scheduled finish passed | `#hub-schedule` |
| No approved Time | `#hub-schedule` and/or Time review |
| SEQUENCE | existing `review_url` / `#hub-schedule` |

---

## 17. Firewalls (frozen)

| Surface | Freeze |
|---------|--------|
| Field / SCH-D | **No PERF-B Field.** No worker Needs Attention panel. Do not modify accepted SCH-D. |
| MONITOR | Money remains MONITOR. Do not import MONITOR financial warnings merely to populate Needs Attention. |
| Cash / payroll / banking / QuickBooks | Desktop later. Not PERF-B. |
| Tomorrow readiness / notify team / Week Ahead | Desktop later. Not PERF-B. The reusable fact seam is sufficient. |
| Operating scope | PERF-B is Project-level. Division not required. Organization remains the hard tenancy / security boundary. Division / Operating Unit remains optional future subordinate scope. Crew is not Division. Do not implement operating-scope schema. Structure the DTO so future PERF-C aggregation is not unnecessarily difficult. |
| Schema | No alert table, attention table, acknowledgement, resolution state, or migration. If implementation later appears to require durable state: **STOP AND RETURN TO ARCHITECT.** |

---

## 18. Contractor copy (implementation-time; not this pass)

Add to `app/presentation/contractor_copy.py` only after implementation is authorized.

| Constant (frozen direction) | Copy |
|-----------------------------|------|
| `LABOUR_NEEDS_ATTENTION_HEADING` | Needs attention |
| `LABOUR_GETTING_CLOSE` | Labour getting close |
| `LABOUR_ALLOWANCE_USED` | Labour allowance used |
| `LABOUR_OVER_ALLOWANCE` | Labour over allowance |
| `LABOUR_EXTRA_WORK_NEEDS_REVIEW` | Extra work needs review |
| `SCHEDULE_FINISH_PASSED` | Scheduled finish passed |
| `SCHEDULE_NO_APPROVED_TIME` | Scheduled work has no approved Time |
| `LABOUR_NOTHING_NEEDS_ATTENTION` | Nothing needs attention right now. |

Reuse existing SEQUENCE copy from `list_schedule_conflicts`. Do not say behind / late / incomplete / missed deadline / work has not started / everything is on track.

---

## 19. Test matrix (do not write tests now)

Dedicated `tests/test_project_needs_attention_fg035.py` (name may follow repository style).

**Labour:** <80 quiet; exactly 80 getting close; 99 getting close; exactly 100 allowance used; >100 over; known zero + Used → over; known zero + Used 0 → none; unknown allowance no percentage fact; one labour fact only.

**Extra Work:** used; waiting; both; authorization removes fact; stale Time origin does not preserve fact.

**Schedule:** end yesterday fact; end today quiet; future end quiet; start yesterday + no Approved Time fact; start today quiet; Approved Time suppresses no-Time fact; no behind/incomplete language.

**SCH:** SEQUENCE reused, not independently recalculated; non-selected warnings remain Schedule-only.

**Positive:** Nothing needs attention right now.

**Warning law:** attention never blocks Time, Schedule, or Change Orders.

**Security:** org / Project isolation.

**UI:** `#hub-labour`; Needs Attention above summary; no Field; MONITOR unchanged.

**Regression:** PERF-A, SCOPE, TIME, SCH, Hub, Field, MONITOR, full suite.

---

## 20. UAT plan (do not execute)

One **new** synthetic Project later. Do **not** use Projects **45–49**.

Scenarios: healthy; labour getting close; labour allowance used / over; Extra Work needs review; scheduled finish passed; scheduled earlier / no Approved Time; SEQUENCE; no false attention.

Keep it understandable. Do not create the vessel in this freeze.

---

## 21. Manual impact plan (do not mutate the log now)

At PERF-B implementation / UAT close, Manual Impact should capture:

- What does Needs Attention mean?
- Does Needs Attention stop me from working? **No.**
- Why does Labour getting close appear?
- What does Labour allowance used mean?
- What does Labour over allowance mean?
- Why does Extra Work need review?
- What does Scheduled finish passed mean?
- Why does CalibraytAI say scheduled work has no approved Time?

Do not write final Manual now. Capture Manual Impact at PERF-B **close**, not this freeze.

---

## 22. V1 effect

Official **60% / 4 of 11**. **NO RESCORE**.

PERF-B is FG-035 work. Completing PERF-B alone is **not** a V1 scoring event.

---

## 23. STOP

```text
DESIGN FROZEN.
OWNER DECISIONS A–G ACCEPTED.
NOT IMPLEMENTATION-AUTHORIZED.
DO NOT IMPLEMENT PERF-B FROM THIS FILE.
DO NOT BEGIN PERF-C.
DO NOT IMPLEMENT HOME OFFICE.
RETURN TO CHATGPT ARCHITECT.
```

# FG-035 PERF-A — Project labour performance implementation preflight

| Attribute | Value |
|-----------|--------|
| Status | **DESIGN FROZEN / NOT IMPLEMENTED.** PERF-A is Project / Element labour Allowed · Used · Remaining on Project Hub. No product code in this pass. |
| Date | 2026-09-17 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Reconciliation | 17 Sep 2026 PERF reconciliation **ACCEPTED**. This freeze implements only PERF-A. |
| Schema | **NONE.** No migration. |
| Baseline | HEAD / `origin/main` **`f1aa486a738a1877d34b16e53fc31d610444ae19`**. SCH-D product **`59d36b8f0b3a86eb41aee03890cb432d0fc58e52`**. Alembic **`f9b0c1d2e3f4 (head)`**. |
| V1 | **NOT RESCORED** (**60% / 4 of 11**) |

```text
FG-035 PERF-A:
IMPLEMENTATION PREFLIGHT COMPLETE
DESIGN FROZEN
NOT IMPLEMENTED
NO SCHEMA
NO MIGRATION
NO NEW ADR
NO NEW FEATURE GATE
V1 NOT RESCORED
PERF-B / PERF-C / CLOSE / LEARN / QB-T NOT AUTHORIZED
```

This file freezes names, authority, aggregation, Hub placement, copy, tests, and UAT so ChatGPT Architect can issue a bounded implementation prompt without reopening architecture.

Do **not** implement PERF-A from this file. Do **not** implement PERF-B, Needs Attention, company attention, explicit progress, Forecast Finish, Print, Shop, Banked Hours, or QB-T from this file.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | TIME Approved hours + Hub Time summary. SCOPE `current_authorized_hours()` / `inherit_scope_lineage()`. Hub BUILD has Project work, Schedule, Time. MONITOR money `#hub-monitor` unchanged. SCH-D Field physically accepted. |
| **Intended (PERF-A)** | Office Hub **Labour** panel: Authorized Allowed / Used / Remaining / Waiting for approval; Extra Work separate. Schema-free read projection. |
| **Future (not PERF-A)** | PERF-B/C Needs Attention (80%/100%, schedule facts). Explicit progress. Forecast Finish. Original / CO / Current three-view. Company attention. Print. Field owner view. |

---

## 2. Frozen owner decisions (PERF-A)

| ID | Decision | PERF-A |
|----|----------|--------|
| A | Used hours | **APPROVED Time only** |
| B | Extra Work | Unauthorized Extra Work is **not** Allowed. Used Extra Work is **separate** |
| C | Needs Attention | **Not in PERF-A** (yes for PERF overall / later PERF-B/C) |
| D | Explicit progress | **Not in PERF-A.** No Not Started / In Progress / Complete schema |
| E | Forecast Finish | **Not V1 PERF.** Do not label scheduled end as forecast |
| F | 80% / 100% | **Not PERF-A business logic** (later PERF-B presentation) |
| G | Labour view | **Current authorized + Extra Work separate.** No original/CO/current three-view |
| H | Company attention | **Not PERF-A.** Project Hub first |

---

## 3. Product question

PERF-A answers **how are we doing on labour for this Project?**

- How many hours are Allowed?
- How many Approved hours have we Used?
- How many hours Remain?
- How many hours are Waiting for approval?
- Is there Extra Work time outside the authorized allowance?

Nothing else.

---

## 4. Authority (consume, do not reimplement)

### Allowed

| Grain | Authority |
|-------|-----------|
| Activity | `app/services/work_scope.py` `current_authorized_hours(activity)` |
| Element | **Sum** `current_authorized_hours` of that Element’s Activities. **Do not** use stored `ProjectWorkElement.estimated_hours` (seed-time rollup; stale after CO `hours_delta`) |
| Project | **Sum** `current_authorized_hours` of the Project’s Activities |

Unauthorized Extra Work: `current_authorized_hours` is **0** (`own_authorized_hours` returns 0 unless a Change Order already authorizes that Extra Work).

Change Order hours: **consume** `current_authorized_hours()` / `authorized_delta_hours()`. Do not independently recalculate CO allowance. Eligible CO = existing `change_order_is_scope_authorizing()` (Approved / Invoiced).

### Used

`app/services/time_entry.py` `approved_labour_hours(...)` with `status=APPROVED` only.

Time grain: every `LabourTimeEntry` has **both** `project_work_activity_id` and `project_work_element_id`. **One aggregation path: Activity.** Never add Project-level Time and Element-level Time.

### Waiting for approval

Same TIME authority as Hub Time `project_time_summary.pending_hours`:

- **INCLUDE:** `SUBMITTED`
- **EXCLUDE:** `APPROVED` (Used), `RETURNED` (worker must correct; visible on Time review, not Labour Used/Waiting), `SUPERSEDED`

Returned is **not** Used and **not** Waiting. Do not invent a fifth Time status.

At implementation, add a TIME sibling `pending_labour_hours(...)` mirroring `approved_labour_hours` filters with `status=SUBMITTED`. PERF must not own a second Time calculator.

Waiting hours **do not** subtract from Remaining.

### Extra Work vs authorized

Classify each Activity with `inherit_scope_lineage(activity)["authorized"]` — **current** work-structure state, **not** frozen `LabourTimeEntry.scope_origin`.

| `authorized` | Allowed contribution | Used / Waiting contribution |
|--------------|----------------------|-----------------------------|
| True | `current_authorized_hours(activity)` | Approved / Submitted Time on that `project_work_activity_id` |
| False | 0 (not in Authorized Allowed) | Extra Work Used / Waiting only |

When Extra Work is linked to an authorizing Change Order, `link_extra_work_to_change_order` may set `scope_origin` to `CHANGE_ORDER`. Lineage `authorized` becomes True. Those hours **move** from Extra Work into Authorized Used. They must not appear in both.

Stale Time `scope_origin=EXTRA_WORK` on a now-authorized Activity still counts as **Authorized Used** (classify by current lineage).

---

## 5. Zero / unknown / over semantics

| Case | Contractor presentation |
|------|-------------------------|
| Allowed known, Used ≤ Allowed | Allowed 120 · Used 86 · Remaining 34 |
| Used > Allowed | Allowed 120 · Used 132 · **Over by** 12. Do **not** show Remaining −12 |
| No governed allowance | Used 8 · **Allowance not available**. Do **not** show Allowed 0 / Remaining −8 |
| Unauthorized Extra Work | Separate block. Allowed is not authorized (0 by Extra Work rule). Show Used Extra Work hours. Do not fold into Authorized Over by |

`allowance_known`: True when the Project has at least one Activity with governed hour evidence (`estimated_hours is not None` or active SCOPE deltas), matching the spirit of `project_scope_totals` `has_hours`. If false, Remaining and Over by are omitted.

Hours quantum: TIME `HOURS_QUANTUM` (`0.01`).

---

## 6. Project aggregation (frozen path)

Walk **all** Project Activities (ACTIVE and INACTIVE) so retired work with Time does not vanish.

For each Activity:

1. `lineage = inherit_scope_lineage(activity)`
2. `allowed_hours += current_authorized_hours(activity)` when `lineage["authorized"]`
3. `used_hours += approved_labour_hours(project_work_activity_id=activity.id)` when authorized
4. `waiting_hours += pending_labour_hours(same)` when authorized
5. Extra Work bucket: same Used/Waiting when **not** authorized

Project Remaining = Allowed − Used **only when** `allowance_known` and Used ≤ Allowed.

Project Over by = Used − Allowed when `allowance_known` and Used > Allowed.

Do not call `approved_labour_hours(project_id=...)` for Authorized Used — that would include Extra Work.

---

## 7. Element aggregation

For each Element with any authorized Allowed, Used, or Waiting:

- Allowed = sum authorized Activity `current_authorized_hours`
- Used / Waiting = sum authorized Activity Time (Activity id), **not** `approved_labour_hours(project_work_element_id=...)` (that would pull Extra Work Time recorded on the same Element)

Extra Work on an existing Element does **not** make that Element’s Authorized row look over.

Do not list Extra-Work-only Elements as Authorized rows with Allowed 0.

---

## 8. Activity presentation

**Not mandatory on the first Hub view.** Project + Element is sufficient for PERF-A acceptance.

No spreadsheet. No progressive disclosure unless a later prompt finds a clean existing Hub expand pattern. Default: **do not** render Activity rows in PERF-A.

---

## 9. Extra Work Hub copy (informational)

```text
Labour

Authorized work
Allowed 120
Used 86
Remaining 34
Waiting for approval 6

Extra work
7 hours used
3 hours waiting for approval
Needs review
```

“Needs review” is **descriptive contractor copy** when Extra Work Used or Waiting > 0. It is **not** the PERF-B Needs Attention engine. Present it as useful attention copy, **not** a red error state suggesting something is broken. No mandatory button. No “resolve before continuing.” No blocker. No persisted alert rows. PERF-B may later decide whether Extra Work contributes to Needs Attention.

If Extra Work Used and Waiting are both 0, omit the Extra Work block (or show a one-line empty state — implementation may omit).

---

## 10. Service contract

**Path:** `app/services/project_performance.py`

**Function:** `assemble_project_performance(organization_id, project_id) -> dict`

Fail-closed: missing / cross-org Project → same 404 pattern as TIME `_project_or_404`.

Do **not** put arithmetic in routes or templates. Do **not** modify `assemble_monitor_v1`. Hub composition may call **both** assemblers independently.

### Return shape (conceptual)

```text
project:
  allowance_known
  allowed_hours
  used_hours
  waiting_hours
  remaining_hours   # None if unknown or over
  over_hours        # None if unknown or not over

elements:           # authorized rows only
  element_id
  display_name
  allowance_known
  allowed_hours
  used_hours
  waiting_hours
  remaining_hours
  over_hours

extra_work:
  used_hours
  waiting_hours
  needs_review      # True if used or waiting > 0; copy only
```

Names may follow repository style; meaning is frozen.

Ownership: **MONITOR consumer / sibling**, not the money assembler. BUILD continues to own Time. Projects continues to own SCOPE hours. File is **not** inside `monitor.py`, `schedule.py`, or a route.

Hub: `project_hub` calls `assemble_project_performance` and passes `hub.labour` (or `hub.performance`) to the template.

---

## 11. Project Hub placement

Existing BUILD order: Project work → Schedule → Time → (MONITOR is the next lifecycle label).

PERF-A adds article **`#hub-labour`** inside BUILD, **after** `#hub-time`, **before** `#hub-monitor`.

| Surface | Freeze |
|---------|--------|
| Lifecycle nav | Unchanged (still PLAN…MONITOR). Do not add a sixth product. |
| Heading | **Labour** |
| Summary | Authorized Allowed / Used / Remaining or Over by / Waiting for approval |
| Rows | Element authorized rows |
| Extra Work | Separate block under the same article |
| Time link | Existing `time_entry.review` (“Review time”) |
| MONITOR | Unchanged |

Do not redesign Hub. Do not alter MONITOR panel copy or `assemble_monitor_v1`.

---

## 12. Contractor copy (Manual Audience Law)

Add to `app/presentation/contractor_copy.py` at implementation (not this pass):

| Constant | Copy |
|----------|------|
| `LABOUR_HUB_HEADING` | Labour |
| `LABOUR_AUTHORIZED_HEADING` | Authorized work |
| `LABOUR_ALLOWED` | Allowed |
| `LABOUR_USED` | Used |
| `LABOUR_REMAINING` | Remaining |
| `LABOUR_WAITING` | Waiting for approval |
| `LABOUR_OVER_BY` | Over by |
| `LABOUR_ALLOWANCE_UNAVAILABLE` | Allowance not available |
| Extra work heading | Reuse `SCOPE_EXTRA_WORK_LABEL` (**Extra work**) |
| `LABOUR_EXTRA_NEEDS_REVIEW` | Needs review |

Avoid: variance engine, authorized denominator, projection, DTO, scope-origin, overlay.

Hours display: existing Hub Time `%.2f` pattern.

---

## 13. Firewalls

| Firewall | Rule |
|----------|------|
| Attention | No 80%/100%, schedule-end, no-Time, sequence, unassigned, or company Needs Attention |
| Warning law | “Over by” and “Needs review” are **INFORMATIONAL**. Must not block Time, Schedule, Change Orders, Project work, or anything else. No alert rows |
| Field | **No PERF-A on Field.** Do not change Today / Week / Month / Company Today / Time / Directions |
| MONITOR | Money only. Independent Hub call OK |
| Shop / Banked Hours / QB / Print | Out of PERF-A |
| Schema | **None.** If implementation discovers a schema need: **STOP** |

---

## 14. Feature Gate answers (PERF-A only)

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Office cannot see Allowed vs Approved Used vs Remaining vs Extra Work on the Project Hub. |
| 2 | Who is the user? | Office contractor / PM on Project Hub. Not Field workers. Not customers. |
| 3 | Which module owns it? | MONITOR consumes. BUILD owns Time. Projects owns SCOPE hours. Hub displays. |
| 4 | What data does it own? | **None.** Read projection only. |
| 5 | What data does it reference? | `ProjectWorkActivity`, `current_authorized_hours`, `inherit_scope_lineage`, `LabourTimeEntry`, `approved_labour_hours`. |
| 6 | What may it change? | New `assemble_project_performance`; Hub `#hub-labour`; contractor_copy; dedicated tests. |
| 7 | What must it not change? | MONITOR money; TIME submit/approve; SCOPE mutations; SCH-D Field; schema; V1 score; EST-2026-0019; Projects 45–48. |
| 8 | Acceptance criteria | Hub Labour matches frozen arithmetic; Extra Work does not make Authorized falsely over; Submitted ≠ Used; no schema; tests pass. |
| 9 | Tests required | Dedicated PERF-A matrix below; TIME/SCOPE/SCH/MONITOR/Field/Hub regression; focused + full suite. |
| 10 | Documentation | This freeze; FG-035 status; indexes; continuity. Manual Impact at **slice close**, not this preflight. |
| 11 | ADR? | **No.** ADR-053 already accepted. |
| 12 | Out of scope | PERF-B/C, progress, Forecast Finish, Field, Print, Shop, Banked Hours, QB-T, three-view, company dashboard. |

---

## 15. Test matrix (dedicated)

File (at implementation): `tests/test_project_labour_performance_fg035.py`

**Project**

- Allowed sums Activity `current_authorized_hours`
- Used = Approved only
- Waiting = Submitted only
- Remaining when Used ≤ Allowed
- Over by when Used > Allowed
- No Time
- No allowance / unknown
- No double-count (Project ≠ sum(Element)+Extra Work incorrectly)

**Element**

- Allowed sums Activities; ignores stale Element `estimated_hours`
- CO `hours_delta` in Allowed
- Used / Waiting authorized only
- Extra Work on same Element excluded from Authorized Used

**Extra Work**

- Unauthorized allowance 0 / separate Used
- Submitted Extra Work is Waiting, not Used
- Does not make Authorized Over by
- After authorizing CO link: hours move to Authorized; no double-count
- Stale Time `scope_origin=EXTRA_WORK` on now-authorized Activity counts as Authorized Used

**TIME states**

- Submitted not Used
- Approved is Used
- Returned neither Used nor Waiting
- Superseded excluded
- No Time mutation in PERF tests beyond fixtures

**Security**

- Organization isolation
- Project isolation / 404

**UI**

- Hub `#hub-labour` Labour copy
- MONITOR panel unchanged
- Field templates unchanged

**Regression (implementation prompt):** TIME, SCOPE, SCH-A/B/C/D, Field, Hub, MONITOR, focused bundle, full suite.

Do **not** write tests in this preflight pass.

---

## 16. UAT plan (plan only)

Do not execute. Do not mutate Projects **45–48** or EST-2026-0019.

Later synthetic vessel (new id) when implementation is authorized.

Contractor scenarios:

- On track: Allowed known, Used well under, no Extra Work
- Labour running high: Used over Allowed → Over by
- Extra Work present: Authorized remaining honest; Extra Work Used separate
- Waiting: Submitted hours visible, Remaining unchanged
- No false over: Extra Work on an existing Element does not Over Authorized work
- No allowance: Used shown; Allowance not available

---

## 17. Manual Impact (plan only)

Do **not** append [manual-impact-log.md](manual-impact-log.md) until PERF-A **slice close**.

Later contractor questions (Manual Audience Law; no Time-state / SCOPE / aggregation vocabulary):

- How many labour hours do we have left?
- What is Used?
- What is Waiting for approval?
- What does Over by mean?
- Why is Extra Work shown separately?
- What does Allowance not available mean?
- Does Over by stop me from entering Time? (**No.**)

---

## 18. Implementation file list (when later authorized)

| Path | Role |
|------|------|
| `app/services/project_performance.py` | **New** assembler |
| `app/services/time_entry.py` | `pending_labour_hours` sibling only |
| `app/services/project_hub.py` | Call assembler |
| `app/templates/projects/detail.html` | `#hub-labour` after Time |
| `app/presentation/contractor_copy.py` | Frozen copy constants |
| `tests/test_project_labour_performance_fg035.py` | **New** dedicated tests |
| Docs | FG-035 / freeze subsequent status at close |

Do **not** create these files in this preflight.

---

## 19. STOP

```text
PERF-A DESIGN FROZEN.
NOT IMPLEMENTED.
NO SCHEMA.
NO PRODUCT.
NO PERF-B.
NO FIELD.
NO MONITOR MONEY CHANGE.
V1 NOT RESCORED.
RETURN TO CHATGPT ARCHITECT.
```

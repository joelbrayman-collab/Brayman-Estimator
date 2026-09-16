# FG-035 SCH-C live bounded UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-16 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | SCH-C **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Alembic | Live current = repository head **`f9b0c1d2e3f4 (head)`**, parent **`f7f8a9b0c1d2`** |

## Scope

Prove LIGHTWEIGHT SEQUENCE on the existing SCH-A WHEN / SCH-B WHO: Element→Element work order, cycle/self/duplicate fail-closed validation, informational SEQUENCE and PREDECESSOR_UNSCHEDULED warnings, KEEP / MOVE / REVIEW as optional affordances, dependency removal, and Element-retirement cleanup of incoming and outgoing ACTIVE work orders. Do **not** implement SCH-D, iPhone Schedule, Schedule → Time suggestion, PERF / CLOSE / LEARN / QB-T, Print, Help / Voice / final Manual, Activity endpoints, lag / float / CPM, automatic movement, or persisted KEEP / MOVE / REVIEW. Do **not** mutate Projects **45** or **46** or EST-2026-0019. V1 **not rescored**.

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH-B IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH-C IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH OVERALL OPEN / PARTIAL
SCH-D NOT AUTHORIZED
PERF NOT AUTHORIZED
CLOSE NOT AUTHORIZED
LEARN NOT AUTHORIZED
QB-T NOT AUTHORIZED
WARNING LAW INFORMATIONAL / NON-BLOCKING
MANUAL FRAMEWORK ACTIVE / SCH-C MANUAL IMPACT CAPTURED
ONE LOOP
ONE PLATFORM / ONE CODEBASE
V1 NOT RESCORED
```

## Git / Alembic

| Field | Value |
|--------|--------|
| Committed HEAD / `origin/main` | **`d59bc716fa6c1ff2e173107500e6178dc0489a5d`** (`docs: record User Guide framework and audience law`) |
| Working tree at UAT | Reviewed SCH-C product + tests + migration FILE + implementation docs + this UAT record (**not committed**) |
| Live current before upgrade | **`f7f8a9b0c1d2`** |
| Repository head before upgrade | **`f9b0c1d2e3f4 (head)`** |
| Upgrade | `f7f8a9b0c1d2` → **`f9b0c1d2e3f4`** **PASS** |
| Live current after | **`f9b0c1d2e3f4 (head)`** |
| Repository head after | **`f9b0c1d2e3f4 (head)`** |
| Table after upgrade | `project_work_dependencies` **present** |
| Token note | `f8a9b0c1d2e3` remains FG-016. SCH-C revision **`f9b0c1d2e3f4`** was preserved, not renamed. |

## Backup

| Field | Value |
|--------|--------|
| Path | `instance/brayman_estimator-backup-before-fg035-sch-c-f9b0c1d2e3f4-20260916-084230.db` (gitignored; not staged) |
| Backup size | **3,112,960** |
| Source DB size at backup | **3,112,960** |
| Backup exists | **yes** |
| Backup Alembic | **`f7f8a9b0c1d2`** |
| `project_work_dependencies` in backup | **absent** |

Earlier backups were not overwritten.

## Protected occupancy — before

| Record | Identity / state |
|--------|------------------|
| Project 45 | `FG035-UAT SCH-A SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating |
| P45 items | **1** Foundation 2026-09-15→2026-09-25 ACTIVE; **2** Structure 2026-09-17→2026-09-21 INACTIVE; **3** Forms 2026-09-15→2026-09-20 ACTIVE; **4** Exterior 2026-09-22→2026-09-24 ACTIVE |
| P45 history | **10**. Assignments **0**. |
| Project 46 | `FG035-UAT SCH-B SYNTHETIC — NOT A CUSTOMER` · ORG-001 |
| P46 items | **6**. History **18**. Assignments **7**. |
| Estimate 28 | EST-2026-0019 Draft · Project **27** |
| Version 34 | version_number **1** · Draft · `is_locked` **0** · subtotal **49872.94** · total **56356.42** |
| Schedule rows on Project 27 | **0** |
| SCH-B assignments on Project 27 | **0** |
| PRODUCTION packages | **0** (`legal_content_jurisdiction_packages.authority_class='PRODUCTION'`) |
| Global LabourTimeEntry | **5** |
| Global ProjectDirectCostActual | **5** |
| Global ProjectWorkScopeDelta | **1** |
| ChangeOrder | **21** |

## Synthetic UAT vessel

Not Joel’s production commercial occupancy. Not EST-2026-0019. Not projects **42**, **43**, **44**, **45**, or **46**.

| Field | Value |
|--------|--------|
| Project | **id 47** `FG035-UAT SCH-C SYNTHETIC — NOT A CUSTOMER` |
| Organization | **ORG-001** |
| Status | Estimating |
| Client | **id 42** `FG035 SCH-C UAT Client — NOT A CUSTOMER` |
| Elements (PROJECT / EXTRA_WORK) | **15** Excavation ACTIVE; **16** Forms (later INACTIVE); **17** Reinforcing ACTIVE; **18** Pour ACTIVE |

Id **47** was assigned by normal SQLite sequencing. It was not forced.

## Dependency chain

Created through `create_work_dependency` (same path as CSRF-protected POST `/schedule/projects/<id>/dependencies`):

| id | Prior work | Must follow | Status after chain |
|----|------------|-------------|--------------------|
| **1** | Excavation **15** | Forms **16** | ACTIVE at create |
| **2** | Forms **16** | Reinforcing **17** | ACTIVE at create |
| **3** | Reinforcing **17** | Pour **18** | ACTIVE at create |

Proof:

- ACTIVE rows **3**
- Same org **ORG-001**, same Project **47**
- `DEPENDENCY_ADDED` history **3**; `dependency_id` **1 / 2 / 3**; `work_schedule_item_id` **NULL**
- Creating the work order did **not** create Schedule items, move dates, create assignments, or create Time

## Cycle validation

Attempt: Pour **18** → Excavation **15**.

| Check | Result |
|--------|--------|
| Rejected | **yes** |
| Contractor-facing message | `That work order would loop back on itself.` |
| Pour→Excavation row | **0** |
| Remaining ACTIVE work orders | **3** (unchanged) |
| Dates | none existed yet; none created |
| Warning used as substitute | **no**. This is **VALIDATION**, not a Schedule warning. |

## Self / duplicate / cross-org validation

| Attempt | Result | Message |
|---------|--------|---------|
| Forms → Forms | **REJECT** | `A work item cannot come after itself.` |
| Duplicate Excavation → Forms | **REJECT** | `That work order already exists.` |
| Same Project through `organization_id=ORG-FG014-UAT` | **REJECT** | `ScheduleNotFoundError: Project not found.` |
| ACTIVE remaining | **3** | |

No second-org UAT vessel was created. Cross-org fail-closed used the existing isolation org.

## Sequence warning

Element-level windows:

| Item | Element | Window |
|------|---------|--------|
| **11** | Forms **16** | 2026-10-01 → 2026-10-10 |
| **12** | Reinforcing **17** | 2026-10-09 → 2026-10-15 |

Required SEQUENCE warning **present**:

`Reinforcing is scheduled before prior work is finished (Forms).`

Label: **Schedule warning**. KEEP: **Leave dates as they are**. MOVE: `/schedule/items/12`. REVIEW: `/projects/47#hub-schedule`.

## Inclusive abut non-warning

Explicit SCH-A MOVE of item **12** to **2026-10-10 → 2026-10-15**.

| Check | Result |
|--------|--------|
| SEQUENCE | **absent** |
| Forms window | unchanged 2026-10-01 → 2026-10-10 |
| PREDECESSOR_UNSCHEDULED | still present (Excavation still unscheduled) |

Then item **12** was restored to 2026-10-09 → 2026-10-15 so Company/Hub could still show SEQUENCE during office HTML proof.

## Predecessor-unscheduled / successor-unscheduled / both-unscheduled

| Case | Result |
|------|--------|
| Both unscheduled (before any dates) | **NO** dependency warning |
| Forms scheduled, Excavation unscheduled | **PREDECESSOR_UNSCHEDULED**: `Forms is scheduled, but the prior work does not have dates yet` |
| Forms scheduled, Reinforcing unscheduled | **NO** dependency warning on Forms→Reinforcing |
| Reinforcing scheduled, Pour unscheduled (before Pour dates) | covered by the successor-unscheduled case above on Forms→Reinforcing |

Informational only. Did not block later SCH-A create of Pour item **13**.

## Warning law — mandatory acceptance

While SEQUENCE and PREDECESSOR_UNSCHEDULED remained on screen:

| A warning did NOT | Proof |
|-------------------|--------|
| block Save | Pour item **13** created 2026-10-20→2026-10-25 |
| disable editing | SCH-A date edit of Reinforcing still succeeded |
| require acknowledgement | no POST, no ack UI |
| require resolution | warnings remained until dates/work-order changed |
| alter dates | Forms/Reinforcing windows unchanged by the Pour create |
| move work | no automatic movement |
| alter assignments | assignment **9** Worker A on Forms remained |
| create Time | Project 47 `labour_time_entries` **0** |
| trigger another workflow | no CO / SCOPE / actuals writes |
| persist warning state | no `schedule_warnings` / `schedule_warning_resolutions` tables |

Validation **did** fail closed for cycle / self / duplicate / cross-org.

WARNINGS INFORM. HUMANS DECIDE.

## KEEP / MOVE / REVIEW / no-action

| Affordance | Live proof |
|-----------|------------|
| KEEP / Leave dates as they are | Display only. No POST merely to acknowledge. Warning remained. |
| MOVE / Change dates | Normal SCH-A `update_schedule_window` on item **12** (inclusive-abut test). Warning itself did not move dates. |
| REVIEW / Review this project | `review_url` `/projects/47#hub-schedule`. No REVIEW state stored. |
| TAKE NO ACTION | After warnings appeared, UAT continued: assigned Worker A, created Pour dates, later removed a work order. |

## Dependency removal

Removed ACTIVE work order **3** (Reinforcing → Pour) through `retire_work_dependency` (same path as CSRF-protected POST `/schedule/dependencies/<id>/retire`).

| Check | Result |
|--------|--------|
| Status | **INACTIVE** |
| Row retained | **yes** |
| `DEPENDENCY_REMOVED` history | **1** with `dependency_id=3` and `work_schedule_item_id` NULL |
| Dates | unchanged on items **11 / 12 / 13** |
| Assignment **9** | unchanged |

No hard-delete.

## Element retirement

Retired Forms **16** through `deactivate_project_work_row` (normal governed work-retirement). At that moment Forms still had ACTIVE incoming **1** and outgoing **2**.

| Check | Result |
|--------|--------|
| Forms status | **INACTIVE** |
| Incoming **1** | **INACTIVE** |
| Outgoing **2** | **INACTIVE** |
| Rows retained | **2** |
| `DEPENDENCY_REMOVED` for that pair | **2** |
| Forms Schedule item **11** | **INACTIVE** (existing Schedule retirement continued) |
| Assignment rows on item **11** | **0** (SCH-B unassign-then-retire in the same transaction) |
| Reinforcing / Pour dates | unchanged |
| Active warnings pointing at Forms | **none** |

## Company Schedule

Restarted local office app onto current SCH-C code at **https://127.0.0.1:5456** (`--no-reload`). Cursor browser MCP was unavailable (`cursor-ide-browser` server not found). Office HTML was proven twice:

1. Authenticated Flask `test_client` against live DB **before** Element retirement, while SEQUENCE and PREDECESSOR_UNSCHEDULED were present.
2. Live TLS process **https://127.0.0.1:5456** as user **1** after restart, Project **47** still usable after retirement.

| Surface | Result |
|---------|--------|
| `test_client` `/schedule?project_id=47&from=2026-10-01&to=2026-10-31` | **200**. Work order. Comes after. Must follow. Schedule warning. Before prior work is finished. Prior work does not have dates yet. Leave dates as they are. Change dates. Review this project. Information only. CSRF token. Worker A. No DAG / ProjectWorkDependency. |
| Live TLS same URL after restart | **200**. Project 47. Work order. Must follow. Add work order. Reinforcing. Pour. Edit dates. CSRF. No DAG. |
| Live TLS `/schedule?project_id=46` | **200**. SCH-B name, Worker A, Schedule conflict, Work order heading remain intact. |

No Print implementation. No dependency-line graph.

## Project Hub

| Surface | Result |
|---------|--------|
| `test_client` `/projects/47` `#hub-schedule` | **200**. Same Work order / Comes after / Add work order / Schedule warning / KEEP / MOVE / REVIEW / information-only copy. Same `assemble_schedule` store. |
| Live TLS `/projects/47` | **200**. `#hub-schedule`. Work order. Add work order. CSRF. |

## CSRF / auth

| POST | Without CSRF token |
|------|--------------------|
| `/schedule/projects/47/dependencies` | **400** (`test_client` and live TLS) |
| `/schedule/dependencies/<id>/retire` | **400** (`test_client` and live TLS) |

Cross-org create **REJECT** as above. No unauthenticated write succeeded.

## Authority protection

| Record | Project 47 | Global after UAT |
|--------|-----------|------------------|
| LabourTimeEntry | **0** | **5** (unchanged) |
| ProjectDirectCostActual | **0** | **5** (unchanged) |
| ProjectWorkScopeDelta | **0** | **1** (unchanged) |
| ChangeOrder | **0** | **21** (unchanged) |

Dependency operations did not rewrite `scheduled_start` / `scheduled_end` except the explicit SCH-A MOVE used for inclusive abut. No Project start/end authority.

## Protected occupancy — after

| Record | Result |
|--------|--------|
| Project 45 items/windows | Unchanged (1–4 as before) |
| Project 45 history | **10** (unchanged) |
| Project 45 assignments | **0** |
| Project 46 items / history / assignments | **6 / 18 / 7** (unchanged) |
| Estimate 28 / Version 34 | EST-2026-0019 Draft · subtotal **49872.94** · total **56356.42** · `is_locked` **0** |
| Project 27 Schedule rows | **0** |
| SCH-B assignments on Project 27 | **0** |
| PRODUCTION packages | **0** |

## Fresh post-UAT tests (authoritative)

Cursor Terminal.

Dedicated SCH-C:

```bash
./venv/bin/python -m pytest -q tests/test_work_schedule_dependency_fg035.py
```

**14 passed**, 0 failed, 32 warnings, **4.34s**, exit **0**.

SCH-A + SCH-B:

```bash
./venv/bin/python -m pytest -q \
tests/test_work_schedule_fg035.py \
tests/test_work_schedule_assignment_fg035.py
```

**22 passed**, 0 failed, 57 warnings, **11.13s**, exit **0**.

Focused:

```bash
./venv/bin/python -m pytest -q \
tests/test_work_structure_tax_wbs_fg035.py \
tests/test_work_scope_fg035.py \
tests/test_work_time_fg035.py \
tests/test_work_schedule_fg035.py \
tests/test_work_schedule_assignment_fg035.py \
tests/test_work_schedule_dependency_fg035.py \
tests/test_project_hub.py \
tests/test_field_web_fg021.py \
tests/test_monitor_v1_fg023.py
```

**135 passed**, 0 failed, 540 warnings, **63.04s**, exit **0**.

Full:

```bash
./venv/bin/python -m pytest -q
```

**1119 passed**, 0 failed, 3705 warnings, **507.32s**, exit **0**.

Do not substitute the pre-migration **1119 / 453.73s** result. This file’s full-suite line is the post-live-UAT evidence.

## Known deferrals

SCH-D / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. No iPhone Schedule. No Schedule → Time suggestion. No Print implementation. No Help / Voice / final Manual. No Activity dependency endpoints. No lag / float / CPM. No automatic schedule movement. V1 **not rescored** (**60% / 4 of 11**).

# FG-035 SCH-A live bounded UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-15 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted** |
| Alembic | Live current = repository head **`f6e7f8a9b0c1 (head)`**, parent **`f5d6e7f8a9b0`** |
| Chronology | **Interrupted.** This record reconciles existing live/UAT residue. It does **not** claim that this reconciliation applied the migration. |

## Scope

Prove SCH-A Schedule overlay on existing Project work: Company `/schedule`, Hub `#hub-schedule`, window integrity, history, authority protection. Do **not** implement SCH-B / SCH-C / SCH-D, assignment, Crew, dependencies, iPhone Schedule, Schedule → Time suggestion, PERF / CLOSE / LEARN / QB-T. Do **not** mutate EST-2026-0019. V1 **not rescored**.

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH OVERALL OPEN / PARTIAL
SCH-B NOT AUTHORIZED
SCH-C NOT AUTHORIZED
SCH-D NOT AUTHORIZED
PERF NOT AUTHORIZED
CLOSE NOT AUTHORIZED
LEARN NOT AUTHORIZED
QB-T NOT AUTHORIZED
ONE LOOP
ONE PLATFORM / ONE CODEBASE
V1 NOT RESCORED
```

## Interrupted chronology (do not invent a neat sequence)

This is **not** a clean first-pass live-migrate performed by the reconciliation prompt.

1. SCH-A product, tests, and migration **file** `migrations/versions/f6e7f8a9b0c1_fg035_sch_a_work_schedule.py` were implemented in the working tree (not committed).
2. A prior live-migrate + bounded synthetic UAT prompt expected live current **`f5d6e7f8a9b0`**. It **STOPPED** because live current was already **`f6e7f8a9b0c1`**.
3. Joel / ChatGPT Architect then authorized **preserve and reconcile** the existing live/UAT state: do **not** restore the backup, do **not** run `flask db upgrade` / `downgrade` / stamp, do **not** create Project 46 or another SCH-A UAT project, do **not** delete Project 45.
4. This reconciliation reconstructed durable evidence, re-exercised only unprovable / transient criteria, ran **fresh** post-UAT tests, and recorded this file.

Do **not** pretend the reconciliation prompt applied `f6e7f8a9b0c1`.

## Git / Alembic

| Field | Value |
|--------|--------|
| HEAD / `origin/main` | **`94fc575a720751dadb36f9df70ae85f40b9680d3`** (`docs: freeze FG-035 SCH implementation design`) |
| Working tree | SCH-A implementation + tests + migration file + this UAT/governance reconciliation (**not committed**) |
| Live current at reconciliation start | **`f6e7f8a9b0c1 (head)`** |
| Repository head | **`f6e7f8a9b0c1 (head)`** |
| Live current after reconciliation | **`f6e7f8a9b0c1 (head)`** |

## Backup provenance (read-only; not restored)

| Field | Value |
|--------|--------|
| Path | `instance/brayman_estimator-backup-before-fg035-sch-a-f6e7f8a9b0c1-20260915-163451.db` (gitignored; not committed) |
| Byte size | **2,957,312** |
| Backup Alembic | **`f5d6e7f8a9b0`** |
| `work_schedule_items` in backup | **absent** |
| `work_schedule_history` in backup | **absent** |

This is durable **pre-SCH-A** provenance. This reconciliation did **not** modify or restore it.

## Migration reconstruction

**OBSERVED / RECONSTRUCTED FROM DURABLE EVIDENCE:**

| State | Alembic | Schedule tables |
|-------|---------|-----------------|
| Pre-SCH-A live (backup) | `f5d6e7f8a9b0` | absent |
| Current live | `f6e7f8a9b0c1` | present |
| Repository head | `f6e7f8a9b0c1` | file in working tree |

**SCH-A LIVE MIGRATION IS DURABLY PROVEN.** This reconciliation did **not** apply it.

## Protected occupancy (before reconstruction and after re-exercise)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft · Project **27** |
| Version 34 | version_number **1** · Draft · `is_locked` **0** · subtotal **49872.94** · total **56356.42** |
| Schedule rows on Project 27 | **0** |
| PRODUCTION packages | **0** |

UNCHANGED from the previously recorded protected state.

## Synthetic UAT vessel (preserved; no second project)

Not Joel’s production commercial occupancy. Not EST-2026-0019. Not projects **42**, **43**, or **44**.

| Field | Value |
|--------|--------|
| Project | **id 45** `FG035-UAT SCH-A SYNTHETIC — NOT A CUSTOMER` |
| Organization | **ORG-001** |
| Status | Estimating |
| Elements | **6** Foundation ACTIVE EXTRA_WORK; **7** Structure ACTIVE EXTRA_WORK; **8** Exterior ACTIVE EXTRA_WORK |
| Activities | **7** Forms (Element 6) ACTIVE; **8** Frame (Element 7) ACTIVE |

No Project **46**. Project **45** was not deleted.

## Project 45 residue at reconstruction (before this prompt’s mutations)

**OBSERVED / RECONSTRUCTED FROM DURABLE EVIDENCE.** 4 `work_schedule_items`. 8 `work_schedule_history` rows. All on Project 45.

| Item | Grain | Window | Status | Created-by |
|------|-------|--------|--------|------------|
| 1 | Element 6 Foundation | 2026-09-15 → 2026-09-18 | ACTIVE | Office |
| 2 | Element 7 Structure | 2026-09-17 → 2026-09-21 | INACTIVE | Office |
| 3 | Activity 7 Forms (Element 6) | 2026-09-15 → 2026-09-17 | ACTIVE | Office |
| 4 | Element 8 Exterior | 2026-09-22 → 2026-09-24 | ACTIVE | Joel Brayman |

History 1–8: CREATED on items 1/2/3/4; DATES_CHANGED on items 3, 1, 2; RETIRED on item 2. Item 4 CREATED actor **Joel Brayman** (`actor_user_id` **1**). Derived ACTIVE range at reconstruction: **2026-09-15 → 2026-09-24**. Unscheduled authorized Element: **Structure (7)**.

## Evidence classification

A = proven from durable existing evidence. B = not provable from residue; re-exercised this reconciliation. C = failed / contradictory (none).

| # | Criterion | Class | Support |
|---|----------|-------|---------|
| 1 | Company Schedule loads | B | HTTPS GET `/schedule?project_id=45` **200** on Flask TLS **5456** |
| 2 | Project 45 appears | A+B | Project row + Company HTML contains the synthetic name |
| 3 | Unscheduled authorized work appears | A+B | Structure (7) unscheduled; Company/Hub show Structure |
| 4 | Element can be scheduled | A | Items 1, 2, 4 CREATED |
| 5 | Scheduled Element leaves unscheduled | A | Foundation and Exterior have ACTIVE element-grain items |
| 6 | Dates display correctly | B | Company/Hub ISO dates 2026-09-15 / 2026-09-22 / 2026-09-24 / later 2026-09-25 |
| 7 | Same-day scheduling | A | Item 1 CREATED 2026-09-15 → 2026-09-15 |
| 8 | Multi-day scheduling | A | Items 1/2/4 multi-day windows |
| 9 | Derived Project range | A+B | Reconstruction MIN/MAX 15→24; after atomic 15→25 |
| 10 | Hub uses same Schedule authority | B | `/projects/45` `#hub-schedule`; same items; `assemble_schedule(..., include_activities=True)` |
| 11 | Activity inside Element accepted | A | Item 3 15–17 inside Element 1 15–18 |
| 12 | Activity outside Element rejected | B | POST `/schedule/items/3` 15→25 without confirm: **FAIL CLOSED** |
| 13 | Rejected contradiction did not persist | B | After failed POST, items unchanged; history still **8** |
| 14 | Atomic Element+Activity extension succeeds | B | Confirmed same-action POST **302**; item 1 → 15–25, item 3 → 15–20 |
| 15 | Unrelated Activities not silently moved | B | Item 4 remained 22–24; Frame activity 8 still unscheduled |
| 16 | CREATED history | A | History 1, 2, 3, 8 |
| 17 | DATES_CHANGED history | A+B | History 4, 5, 6 plus this-prompt 9, 10 |
| 18 | RETIRED history | A | History 7 on item 2 |
| 19 | Retirement retains row | A | Item 2 still present |
| 20 | Retired item no longer active | A | Item 2 INACTIVE; assemble returns only ACTIVE |
| 21 | Work unscheduled again where applicable | A | Structure remains unscheduled |
| 22 | Schedule creates no Time | A | Project 45 `labour_time_entries` **0** |
| 23 | Schedule creates no money actual | A | Project 45 `project_direct_cost_actuals` **0** |
| 24 | Schedule does not mutate SCOPE | A | Project 45 `project_work_scope_deltas` **0**; Change Orders **0** |
| 25 | Schedule does not mutate EST-2026-0019 | A | Occupancy re-read unchanged |

Completeness: every required criterion is supported by **A** durable reconstructed evidence and/or **B** fresh bounded verification this reconciliation. **YES.**

## Window-integrity recheck (this prompt)

**EXERCISED / VERIFIED THIS PROMPT** via product route `POST /schedule/items/3` against live Project 45 (Flask test client, user id 1).

| Step | Result |
|------|--------|
| Before | Item 1 ACTIVE 2026-09-15→2026-09-18; item 3 ACTIVE 2026-09-15→2026-09-17; item 4 ACTIVE 2026-09-22→2026-09-24; item 2 INACTIVE 2026-09-17→2026-09-21; history **8** |
| Attempt Activity 15→25 without `confirm_element_adjustment` | HTTP **200**; flash *Activity dates must stay inside the work item dates unless you confirm extending the work item in the same action.* |
| After failed attempt | Windows unchanged; history still **8** |
| Confirmed same-action Element 15→25 + Activity 15→20 | HTTP **302** `/schedule?project_id=45` |
| After pass | Item 1 ACTIVE 15→25; item 3 ACTIVE 15→20; item 4 **unchanged** 22→24; Frame still unscheduled; Structure still unscheduled |
| New history | **9** DATES_CHANGED item 3 (Joel Brayman); **10** DATES_CHANGED item 1 (Joel Brayman) |
| Derived range after | **2026-09-15 → 2026-09-25** |

## Company Schedule / Project Hub (this prompt)

Flask `--no-reload` TLS **5456** was restarted onto current SCH-A code (authorized restart). Authenticated HTTPS GET against the live office process:

| Path | Result |
|------|--------|
| `GET /schedule?project_id=45&from=2026-09-15&to=2026-09-30` | **200**. Project 45 visible. Range `2026-09-15 → 2026-09-25`. Foundation and Exterior scheduled. Structure *Not scheduled yet*. **Set dates** / **Edit dates**. No assignment / Crew / dependency / labour-analytics SCH-A chrome. |
| `GET /projects/45` | **200**. `#hub-schedule` present. Same Project 45 records. Forms visible (Hub `include_activities=True`). Same derived range. Owning Schedule links. |
| `GET /schedule/items/3` | **200**. Confirm-element checkbox present. |
| `GET /schedule/items/new?project_id=45` | **200**. Form actions available. |

Cursor IDE browser MCP was **unavailable** (`Server not found: cursor-ide-browser`). Live office verification used the running local Flask TLS process above, not a second schedule store.

## Authority protection (after completion)

| Check | Result |
|-------|--------|
| Project 45 `LabourTimeEntry` | **0** |
| Project 45 `ProjectWorkScopeDelta` | **0** (no SCH-added delta) |
| Project 45 `ProjectDirectCostActual` | **0** |
| Project 45 Change Orders | **0** |
| Element `estimated_hours` | Foundation / Structure / Exterior remain **NULL** |
| `projects` start/end date columns | **absent** (range remains derived) |
| Project 27 schedule rows | **0** |

SCH-A did not create Time, change approved labour actuals, create money actuals, rewrite ChangeOrder, rewrite original estimated hours, or add Project start/end date authority.

## Tests (authoritative POST-LIVE-UAT; do not substitute earlier 1096 / 413.66s)

| Command | Result |
|---------|--------|
| Dedicated | `./venv/bin/python -m pytest -q tests/test_work_schedule_fg035.py` **13 passed**, 31 warnings, **4.12s**, exit **0** |
| Focused TAX/WBS + SCOPE + TIME + SCH-A + Hub + Field Web + MONITOR | `./venv/bin/python -m pytest -q tests/test_work_structure_tax_wbs_fg035.py tests/test_work_scope_fg035.py tests/test_work_time_fg035.py tests/test_work_schedule_fg035.py tests/test_project_hub.py tests/test_field_web_fg021.py tests/test_monitor_v1_fg023.py` **112 passed**, 482 warnings, **51.94s**, exit **0** |
| Full | `./venv/bin/python -m pytest -q` **1096 passed**, 3647 warnings, **514.43s**, exit **0** |

## Result

**SCH-A LIVE BOUNDED SYNTHETIC UAT PASS.** Gate remains **OPEN / PARTIAL**. SCH overall **OPEN / PARTIAL**. SCH-B / SCH-C / SCH-D **NOT AUTHORIZED**. V1 **60% / 4 of 11** **NOT RESCORED**. Working tree **not committed**.

# FG-035 SCH-B live bounded UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-16 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | SCH-B **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Alembic | Live current = repository head **`f7f8a9b0c1d2 (head)`**, parent **`f6e7f8a9b0c1`** |

## Scope

Prove WHO on the existing SCH-A WHEN: USER XOR Crew assignment, optional Organization Crew, inclusive period membership, Unassigned, unassignment, overlap warnings as a read projection, and item retirement that unassigns then retires in the same transaction. Do **not** implement SCH-C / SCH-D, dependencies, KEEP / MOVE / REVIEW, iPhone Schedule, Schedule → Time suggestion, PERF / CLOSE / LEARN / QB-T. Do **not** mutate Project 45 or EST-2026-0019. V1 **not rescored**.

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH-B IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS
SCH OVERALL OPEN / PARTIAL
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

## Git / Alembic

| Field | Value |
|--------|--------|
| Committed HEAD / `origin/main` | **`d3352509b708482ac9bbacce8cea0860b2d8cfcf`** (`docs: pin FG-035 SCH-A SHA`) at UAT start |
| Product SCH-B SHA | **`374798d7338a4c00d90a9c7a2b2efa310bc7e355`** (`feat: implement FG-035 SCH-B assignment and crews`) |
| Product SCH-A SHA | **`fd8a66990df8286e54151b80b6f3cd5be5dd3ad1`** |
| Working tree at UAT | SCH-B product + tests + docs + this UAT record (committed in the product SHA) |
| Live current before upgrade | **`f6e7f8a9b0c1`** |
| Repository head before upgrade | **`f7f8a9b0c1d2 (head)`** |
| Upgrade | `f6e7f8a9b0c1` → **`f7f8a9b0c1d2`** **PASS** |
| Live current after | **`f7f8a9b0c1d2 (head)`** |
| Repository head after | **`f7f8a9b0c1d2 (head)`** |
| Tables after upgrade | `work_schedule_assignments`, `organization_crews`, `organization_crew_members` **present** |

## Backup

| Field | Value |
|--------|--------|
| Path | `instance/brayman_estimator-backup-before-fg035-sch-b-f7f8a9b0c1d2-20260916-062918.db` (gitignored; not committed) |
| Backup size | **3,035,136** |
| Source DB size at backup | **3,035,136** |
| Backup exists | **yes** |
| Backup Alembic | **`f6e7f8a9b0c1`** |
| SCH-B tables in backup | **absent** (`work_schedule_items` present from SCH-A) |

Earlier backups were not overwritten.

## Protected occupancy — before

| Record | Identity / state |
|--------|------------------|
| Project 45 | `FG035-UAT SCH-A SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating |
| P45 items | **1** Foundation 2026-09-15→2026-09-25 ACTIVE; **2** Structure 2026-09-17→2026-09-21 INACTIVE; **3** Forms 2026-09-15→2026-09-20 ACTIVE; **4** Exterior 2026-09-22→2026-09-24 ACTIVE |
| P45 history | **10** rows (CREATED/DATES_CHANGED/RETIRED). No ASSIGNED/UNASSIGNED. |
| Estimate 28 | EST-2026-0019 Draft · Project **27** |
| Version 34 | version_number **1** · Draft · `is_locked` **0** · subtotal **49872.94** · total **56356.42** |
| Schedule rows on Project 27 | **0** |
| PRODUCTION packages | **0** |

## Synthetic UAT vessel

Not Joel’s production commercial occupancy. Not EST-2026-0019. Not projects **42**, **43**, **44**, or **45**.

| Field | Value |
|--------|--------|
| Project | **id 46** `FG035-UAT SCH-B SYNTHETIC — NOT A CUSTOMER` |
| Organization | **ORG-001** |
| Status | Estimating |
| Client | `FG035 SCH-B UAT Client — NOT A CUSTOMER` |
| Elements (EXTRA_WORK) | **9** Foundation; **10** Structure; **11** Exterior; **12** Interior; **13** Sitework; **14** Roofing |

Id **46** was assigned by normal SQLite sequencing. It was not forced.

## Synthetic users

| id | Display name | Org membership | Active |
|----|--------------|----------------|--------|
| **12** | FG035 SCH-B Worker A | ORG-001 active | yes |
| **13** | FG035 SCH-B Worker B | ORG-001 active | yes |
| **14** | FG035 SCH-B Inactive Worker | ORG-001 membership present | **no** (`is_active=0`) |

Cross-org rejection used existing user **5** (ORG-FG014-UAT only).

## Crews

| id | Name | Status |
|----|------|--------|
| **1** | FG035-UAT Concrete Crew | ACTIVE |
| **2** | FG035-UAT Retire Proof Crew | INACTIVE (retired; row retained) |

Membership:

| id | Crew | User | effective_from | effective_to |
|----|------|------|----------------|--------------|
| **1** | Concrete **1** | Worker A **12** | **2026-09-20** inclusive | **NULL** (open-ended) |
| **2** | Retire Proof **2** | Worker B **13** | **2026-07-01** | **2026-07-15** inclusive |

Overlapping period for Worker A on Concrete Crew was **rejected**. Closing/retaining the bounded Retire Proof period did **not** write Schedule history. Roster change did **not** change Schedule dates.

## Schedule windows (Project 46)

| Item | Element | Window | Status | Role |
|------|--------|--------|--------|------|
| **5** | Foundation | 2026-09-20 → 2026-09-25 | ACTIVE | Overlap pair A |
| **6** | Structure | 2026-09-22 → 2026-09-28 | ACTIVE | Overlap pair A |
| **7** | Exterior | 2026-10-10 → 2026-10-14 | ACTIVE | **Unassigned** |
| **8** | Interior | 2026-08-01 → 2026-08-05 | ACTIVE | Historical pair B (Crew) |
| **9** | Sitework | 2026-08-03 → 2026-08-08 | ACTIVE | Historical pair B (USER A) |
| **10** | Roofing | 2026-09-01 → 2026-09-03 | **INACTIVE** | Retirement transaction |

Assigning did **not** change `scheduled_start` / `scheduled_end`.

## Assignment / unassign / retire results

| Step | Result |
|------|--------|
| USER assign | Worker A → item **6**; Worker B → items **5** and **6**. ASSIGNED history `assignment_id` set. |
| Crew assign | Concrete Crew → items **5**, **6**, and **8**. ASSIGNED history set. |
| Duplicate USER | **REJECTED** |
| Inactive USER (14) | **REJECTED** |
| Cross-org USER (5) | **REJECTED** / fail closed |
| Duplicate Crew | **REJECTED** |
| INACTIVE Crew (2) | **REJECTED** |
| Cross-org Crew | **REJECTED** / fail closed |
| Unassigned | Item **7** zero rows. Company and Hub show contractor-facing **Unassigned**. No Unassigned user/Crew row. |
| Unassign | Assignment **2** (Worker B on item **5**) removed via service equivalent of POST `/schedule/items/<id>/assignments/<assignment_id>/remove`. UNASSIGNED history **25** has `assignment_id=2` after row delete. Item **5** remained ACTIVE. Dates unchanged. |
| Restore for display | Worker B re-assigned to item **5** as assignment **8** so Company/Hub still show USER overlap after the unassign proof. |
| Retire item **10** | Assignment **8** (then-current Worker B on item **10**) UNASSIGNED history **26**, row deleted, item INACTIVE, RETIRED history **27**. No current assignments remain. Dates unchanged. Crew membership rows retained. No Time created. |
| INACTIVE item assign | Assigning to item **10** after retire **REJECTED** |

SQLite reused INTEGER PK **8** for the later restored assignment on item **5**. History for retired item **10** still records `assignment_id=8`. This is why `work_schedule_history.assignment_id` remains a non-FK Integer placeholder.

## Overlap warnings (read projection)

No `work_schedule_conflicts` table. Windows were not moved.

| Kind | Name | Result |
|------|------|--------|
| USER | FG035 SCH-B Worker B | **WARNING** on overlapping items **5** and **6** |
| CREW | FG035-UAT Concrete Crew | **WARNING** on overlapping items **5** and **6** |
| USER_THROUGH_CREW | FG035 SCH-B Worker A | **WARNING**: membership **2026-09-20 → NULL** overlaps both Sep windows; Crew on item **5**; USER on item **6** |
| False historical through-Crew | Worker A USER on item **9** (2026-08-03→08-08) + Crew on item **8** (2026-08-01→08-05) | **NO conflict**. Membership begins **2026-09-20**, after those windows. Engine used scheduled-window membership, not today’s roster. |

Contractor-facing copy: **Schedule conflict** / **is already scheduled elsewhere**.

## Company Schedule / Project Hub

Restarted local Flask onto SCH-B code at **https://127.0.0.1:5456** (`--no-reload`). Cursor browser MCP was unavailable in this session (`cursor-ide-browser` server not found). Office HTML was proven against the live app + live DB as user **1** via Flask `test_client` session:

| Surface | Result |
|---------|--------|
| `/schedule?project_id=46` | **200**. Project 46 visible. Worker A/B names. Concrete Crew. Unassigned. Schedule conflict copy. SCH-A date editor links present. No KEEP/MOVE/REVIEW. No iPhone Schedule. No PERF. |
| `/projects/46` Hub `#hub-schedule` | **200**. Same names, Unassigned, and conflict facts from `assemble_schedule`. No second assignment store. |
| `/settings/crews` | **200**. Concrete Crew ACTIVE. Retire Proof Crew **Retired**. Create form CSRF token present. |
| `/schedule/items/5` | Assignment POST + remove POST forms include `csrf_token`. |

CSRF: unauthenticated POST to Crew create, assignment create, and unassign **400** without token.

## Authority protection

| Record | Project 46 | Global after UAT |
|--------|-----------|------------------|
| LabourTimeEntry | **0** | **5** (unchanged) |
| ProjectDirectCostActual | **0** | **5** (unchanged) |
| ProjectWorkScopeDelta | **0** | **1** (unchanged) |
| ChangeOrder | **0** | **21** (unchanged) |

## Protected occupancy — after

| Record | Result |
|--------|--------|
| Project 45 items/windows | Unchanged (1–4 as before) |
| Project 45 history | **10** (unchanged) |
| Project 45 assignments | **0** |
| Estimate 28 / Version 34 | EST-2026-0019 Draft · subtotal **49872.94** · total **56356.42** · `is_locked` **0** |
| Project 27 Schedule rows | **0** |
| PRODUCTION packages | **0** |

## Fresh post-UAT tests (authoritative)

Cursor Terminal.

Dedicated SCH-B:

```bash
./venv/bin/python -m pytest -q tests/test_work_schedule_assignment_fg035.py
```

**9 passed**, 26 warnings, **6.28s**, exit **0**.

Dedicated SCH-A:

```bash
./venv/bin/python -m pytest -q tests/test_work_schedule_fg035.py
```

**13 passed**, 31 warnings, **3.85s**, exit **0**.

Focused:

```bash
./venv/bin/python -m pytest -q \
tests/test_work_structure_tax_wbs_fg035.py \
tests/test_work_scope_fg035.py \
tests/test_work_time_fg035.py \
tests/test_work_schedule_fg035.py \
tests/test_work_schedule_assignment_fg035.py \
tests/test_project_hub.py \
tests/test_field_web_fg021.py \
tests/test_monitor_v1_fg023.py
```

**121 passed**, 508 warnings, **54.70s**, exit **0**.

Full:

```bash
./venv/bin/python -m pytest -q
```

**1105 passed**, 3673 warnings, **450.77s**, exit **0**.

Do not substitute the pre-migration 1105 result. This is the post-live-UAT full suite.

## Known deferrals

SCH-C / SCH-D / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. No dependency UI. No KEEP/MOVE/REVIEW. No iPhone Schedule. No Schedule → Time suggestion. V1 **not rescored** (**60% / 4 of 11**).

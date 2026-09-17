# FG-035 PERF-A live bounded UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-17 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | PERF-A **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS / COMMITTED / SHA-PINNED / PUSHED** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Alembic | Live current = repository head **`f9b0c1d2e3f4 (head)`**. **No PERF-A migration.** |
| Freeze | [architecture/fg-035-perf-a-implementation-preflight.md](../architecture/fg-035-perf-a-implementation-preflight.md) |

## Scope

Prove Project Hub Labour Allowed · Used · Remaining · Waiting for approval · Extra Work on one new synthetic Project using existing SCOPE and TIME authority. Do **not** implement PERF-B, Needs Attention, 80%/100% alerts, Field PERF, MONITOR money changes, Print, Shop, Banked Hours, QB-T, CLOSE, or LEARN. Do **not** mutate Projects **45 / 46 / 47 / 48** or EST-2026-0019. V1 **not rescored**.

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH-A/B/C/D IMPLEMENTED
PERF-A IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS
COMMITTED / SHA-PINNED / PUSHED
PERF-B / PERF-C NOT AUTHORIZED
CLOSE NOT AUTHORIZED
LEARN NOT AUTHORIZED
QB-T NOT AUTHORIZED
NO SCHEMA
V1 NOT RESCORED
```

## Git / Alembic

| Field | Value |
|-------|--------|
| HEAD / `origin/main` at UAT inspect | **`8187d88d9a7695d009b4e8610ab2468831ec4fe3`** (`docs: freeze FG-035 PERF-A implementation design`) |
| Product PERF-A SHA | **`7a4b7000e2650eadf68b4ea44d48f75c65830c1f`** (`feat: implement FG-035 PERF-A labour performance`) |
| Divergence at UAT inspect | **0 0** |
| Working tree at UAT inspect | DIRTY — reviewed PERF-A product + tests + docs + this UAT record. Later **COMMITTED / SHA-PINNED / PUSHED**. |
| Live current | **`f9b0c1d2e3f4 (head)`** unchanged |
| PERF alert tables | **none** |

## Protected occupancy — before

| Record | Identity / state |
|--------|------------------|
| Project 45 | `FG035-UAT SCH-A SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · elements **3** · activities **2** · time **0** |
| Project 46 | `FG035-UAT SCH-B SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · elements **6** · activities **0** · time **0** |
| Project 47 | `FG035-UAT SCH-C SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · elements **4** · activities **0** · time **0** |
| Project 48 | `FG035-UAT SCH-D SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · elements **9** · activities **2** · time **1** |
| Project 27 | `40x80 Thickened-Edge Concrete Slab` · elements **0** · time **0** |
| Estimate 28 | EST-2026-0019 Draft · Project **27** |
| Version 34 | version_number **1** · Draft · `is_locked` **False** · subtotal **49872.94** · total **56356.42** |
| PRODUCTION packages | **0** |
| Global LabourTimeEntry | **6** |
| Max project id | **48** |

## Synthetic PERF-A vessel

Not Joel’s production commercial occupancy. Not EST-2026-0019. Not projects **45–48**.

| Field | Value |
|-------|--------|
| Project | **id 49** `FG035-UAT PERF-A SYNTHETIC — NOT A CUSTOMER` |
| Organization | **ORG-001** |
| Status | Estimating |
| Client | `FG035 PERF-A UAT Client — NOT A CUSTOMER` |
| Estimate | `EST-2026-FG035-PERF-UAT` · labour snapshot **2000 sqft × 0.05 = 100.00** hours · Issued / locked · seed from that version |
| Authorized Element **28** | Foundation · stored `estimated_hours` **100.000000** |
| Authorized Activity **11** | Concrete · ORIGINAL · `estimated_hours` **100.000000** |
| Extra Work Element **29** | Extra work (created later) |
| Extra Work Activity **12** | Additional concrete work |
| Known-zero Activity **13** | Standby labour · `estimated_hours` **0** · `current_authorized_hours` **0** · no Time |
| Change Order | **CO-000022** Approved `Authorize additional concrete work` · `hours_delta` **+20.00** on Activity **12** |
| Time worker | user **10** TIME UAT Worker |
| Time reviewer | user **11** TIME UAT Reviewer |
| Office Hub | `http://127.0.0.1:5460/projects/49#hub-labour` on current PERF-A code |

Id **49** was assigned by normal SQLite sequencing. It was not forced.

## Step results

### Initial allowance

`current_authorized_hours(Concrete)` = **100.00**. Service:

| | Allowed | Used | Waiting | Remaining | Over by |
|--|---------|------|---------|-----------|---------|
| Project | 100.00 | 0.00 | 0.00 | 100.00 | none |
| Foundation | 100.00 | 0.00 | 0.00 | 100.00 | none |
| Extra work | — | 0.00 | 0.00 | — | needs review **false** |

### Approved / Submitted / Returned

Normal `submit_time` / `approve_time` / `return_time`:

- **60.00** APPROVED (six × 10.00, 2026-08-01…08-06)
- **10.00** SUBMITTED (2026-08-07) · entry **13** remains SUBMITTED
- **8.00** RETURNED (2026-08-08) · entry **14**

| | Allowed | Used | Waiting | Remaining |
|--|---------|------|---------|-----------|
| Project | 100.00 | 60.00 | 10.00 | **40.00** |

Waiting **10** did **not** reduce Remaining to 30. Returned **8** is neither Used nor Waiting.

### Over by

Five more APPROVED 10.00 entries (2026-08-09…08-13). Used **110.00**. Waiting still **10.00**.

| | Allowed | Used | Remaining | Over by | Waiting |
|--|---------|------|-----------|---------|---------|
| Project / Foundation | 100.00 | 110.00 | **none** (not −10) | **10.00** | 10.00 |

### Extra Work before authorization

`create_extra_work` → Element **Extra work** / Activity **Additional concrete work**. APPROVED **6.00** (entry **20**) + SUBMITTED **2.00** (entry **21**). Frozen Time `scope_origin` **EXTRA_WORK**. Lineage `authorized` **False**.

Authorized remained Allowed **100.00** · Used **110.00** · Over by **10.00**. Extra **6** did **not** make Authorized Used 116 or Over by 16.

Extra work: **6 hours used · 2 hours waiting for approval · Needs review**. Informational only. Hub / Time / Schedule GETs **200**. Creating **CO-000022** succeeded. No PERF alert table. No acknowledgement.

### Extra Work after SCOPE authorization

`link_extra_work_to_change_order` then `apply_change_order_delta(hours_delta="20")` on Activity **12**. Activity origin became **CHANGE_ORDER**. `current_authorized_hours` = **20.00**.

Arithmetic:

- Concrete Allowed **100** + Extra Allowed **20** = Project Allowed **120**
- Concrete Used **110** + Extra Used **6** = Project Used **116**
- Concrete Waiting **10** + Extra Waiting **2** = Project Waiting **12**
- Remaining = 120 − 116 = **4.00**
- Extra Work bucket Used **0** / Waiting **0** / needs review **false** (not double-counted)

Live Activity-grain sum matched the service exactly.

### Current-lineage / stale Time proof

Entries **20** and **21** still store `scope_origin=EXTRA_WORK` after authorization. PERF classifies them as Authorized Used **6.00** / Waiting **2.00**. Hub Time still reports Extra work hours **6.00** from TIME’s frozen-origin summary. Labour Extra Work block is omitted. Historical Time was **not** rewritten.

### Element / Project rollup

| Element | Stored `estimated_hours` | PERF Allowed | Used | Waiting | Remaining / Over by |
|---------|--------------------------|--------------|------|---------|---------------------|
| Foundation **28** | **100.000000** | 100.00 (sum of Concrete **100** + Standby **0**) | 110.00 | 10.00 | Over by 10.00 |
| Extra work **29** | **None** (ignored) | **20.00** from `current_authorized_hours` / CO `hours_delta` | 6.00 | 2.00 | Remaining 14.00 |

Project totals equal one Activity-grain rollup. No Project+Element+Activity double-count.

### Hub Labour UX

Office Hub `#hub-labour` after `#hub-time` before `#hub-monitor`. Contractor copy only.

**Authorized work:** Allowed **120.00** · Used **116.00** · Remaining **4.00**. Waiting for approval **12.00**. Foundation Over by **10.00**. Extra work row Allowed **20.00** Used **6.00** Remaining **14.00**. No architecture language. Lifecycle nav unchanged (no sixth product).

**Could Ben understand whether this project is okay on labour in about five seconds?** **YES.** Project remaining **4** hours with Foundation over and Extra work still having room is readable immediately.

### MONITOR firewall

`#hub-monitor` still **Estimated versus actual** / Project Gross Margin / Direct Cost actuals. No labour-hours math. No forecast final GM. `assemble_monitor_v1` unchanged.

### Field firewall

Authenticated Field Today / Company Today / Week / Month / Time for Project 49: **no** `#hub-labour`. No physical iPhone retest.

### Unknown / zero

Unknown allowance was **not** manufactured live (would require bypassing governed seed hours on this vessel). Dedicated automated tests cover it.

Known zero: Activity **13** Standby labour `estimated_hours=0` / `current_authorized_hours=0`. Not confused with unknown. It rolls into Foundation Allowed **100** and does not create a separate Hub row.

### Security

ORG-001 only. `assemble_project_performance("ORG-002", 49)` → `TimeEntryNotFoundError` “Project not found.” Project 45 labour Used **0** (isolation; not mutated).

## Protected occupancy — after

| Record | State |
|--------|--------|
| Projects 45 / 46 / 47 / 48 | **unchanged** (names, element/activity/time counts) |
| Project 27 / Estimate 28 / Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| PRODUCTION packages | **0** |
| Project 49 time | **15** entries (global time **21** = prior **6** + **15**) |
| Alembic | **`f9b0c1d2e3f4`** |

## Fresh post-UAT tests

| Command | Result |
|---------|--------|
| Dedicated | `./venv/bin/python -m pytest -q tests/test_project_labour_performance_fg035.py` **14 passed**, 124 warnings, **10.69s**, exit **0** |
| Focused | `./venv/bin/python -m pytest -q tests/test_work_structure_tax_wbs_fg035.py tests/test_work_scope_fg035.py tests/test_work_time_fg035.py tests/test_work_schedule_fg035.py tests/test_work_schedule_assignment_fg035.py tests/test_work_schedule_dependency_fg035.py tests/test_work_schedule_field_fg035.py tests/test_project_labour_performance_fg035.py tests/test_project_hub.py tests/test_field_web_fg021.py tests/test_monitor_v1_fg023.py` **170 passed**, 708 warnings, **110.65s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1154 passed**, 0 failed, 3873 warnings, **633.10s**, exit **0** |

## Completeness

Every required PERF-A engineering + bounded live-UAT acceptance criterion is supported by durable evidence. **YES.** Unknown-allowance live case uses dedicated automated evidence, as authorized when a truthful unknown would require bypassing SCOPE seed hours.

## STOP

```text
PERF-A IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS.
COMMITTED / SHA-PINNED / PUSHED.
NO SCHEMA.
NO PERF-B.
V1 NOT RESCORED.
RETURN TO CHATGPT ARCHITECT.
```

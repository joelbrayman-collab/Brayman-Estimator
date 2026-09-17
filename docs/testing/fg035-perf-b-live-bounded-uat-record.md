# FG-035 PERF-B live bounded UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-17 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | PERF-B **IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. No new ADR. |
| Alembic | Live current = repository head **`f9b0c1d2e3f4 (head)`**. **No PERF-B migration.** |
| Freeze | [architecture/fg-035-perf-b-implementation-preflight.md](../architecture/fg-035-perf-b-implementation-preflight.md) |

## Scope

Prove Project Hub `#hub-labour` Needs Attention on **one** new synthetic Project using existing SCOPE, TIME, Schedule, and Change Order authority. Do **not** persist attention rows. Do **not** implement PERF-C, Home Office, Field PERF, MONITOR money changes, Print, Shop, Banked Hours, QB-T, CLOSE, or LEARN. Do **not** mutate Projects **45 / 46 / 47 / 48 / 49** or EST-2026-0019. V1 **not rescored**. **No commit. No push.**

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH-A/B/C/D IMPLEMENTED
PERF-A IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS
PERF-B IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS
NOT COMMITTED
NOT PUSHED
PERF-C / CLOSE / LEARN / QB-T NOT AUTHORIZED
NO SCHEMA
V1 NOT RESCORED
```

## Git / Alembic

| Field | Value |
|-------|--------|
| HEAD / `origin/main` at UAT inspect | **`11a11cb33e8bc7c185557980a1852af66d53b367`** (`docs: freeze FG-035 PERF-B implementation design`) |
| Divergence | **0 0** |
| Working tree | DIRTY — reviewed PERF-B product + tests + docs + this UAT record. **Not committed.** |
| Live current | **`f9b0c1d2e3f4 (head)`** unchanged |
| PERF alert tables | **none** (131 SQLite tables; no attention/alert persistence) |

## Protected occupancy — before

| Record | Identity / state |
|--------|------------------|
| Project 45 | `FG035-UAT SCH-A SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · elements **3** · activities **2** · time **0** |
| Project 46 | `FG035-UAT SCH-B SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · elements **6** · activities **0** · time **0** |
| Project 47 | `FG035-UAT SCH-C SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · elements **4** · activities **0** · time **0** |
| Project 48 | `FG035-UAT SCH-D SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · elements **9** · activities **2** · time **1** |
| Project 49 | `FG035-UAT PERF-A SYNTHETIC — NOT A CUSTOMER` · ORG-001 · Estimating · elements **2** · activities **3** · time **15** |
| Project 27 | `40x80 Thickened-Edge Concrete Slab` · elements **0** · time **0** |
| Estimate 28 | EST-2026-0019 Draft · Project **27** |
| Version 34 | version_number **1** · Draft · `is_locked` **False** · subtotal **49872.94** · total **56356.42** |
| PRODUCTION packages | **0** |
| Global LabourTimeEntry | **21** |
| Max project id | **49** |

## Synthetic PERF-B vessel

Not Joel’s production commercial occupancy. Not EST-2026-0019. Not projects **45–49**.

| Field | Value |
|-------|--------|
| Project | **id 50** `FG035-UAT PERF-B SYNTHETIC — NOT A CUSTOMER` |
| Organization | **ORG-001** |
| Status | Estimating |
| Client | `FG035 PERF-B UAT Client — NOT A CUSTOMER` |
| Estimate | `EST-2026-FG035-PERFB-UAT` · labour snapshot **2000 sqft × 0.05 = 100.00** hours · Issued / locked · seed from that version |
| Authorized Element **30** | Foundation · stored `estimated_hours` **100.000000** |
| Authorized Activity **14** | Concrete · ORIGINAL · `estimated_hours` **100.000000** |
| Extra Work Element **31** | Extra work (created later; now CHANGE_ORDER after authorization) |
| Extra Work Activity **15** | Additional forming |
| Framing Element **32** | Framing · EXTRA_WORK origin · **no Time** · SEQUENCE successor |
| Interior Element **33** | Interior · scheduled **today–today** |
| Roof Element **34** / Activity **16** | Roof / Roofing · ORIGINAL after reclassify · no-approved-Time proofs |
| Site cleanup Element **35** | Warning Law schedule POST (tomorrow) |
| Change Order | **CO-000023** Approved `Authorize additional forming` · **CO-000024** Draft `Keep working while attention shows` |
| Time worker | user **10** TIME UAT Worker |
| Time reviewer | user **11** TIME UAT Reviewer |
| Office Hub | `http://127.0.0.1:5461/projects/50#hub-labour` on current PERF-B code (port **5460** remains the earlier PERF-A process) |

Id **50** was assigned by normal SQLite sequencing. It was not forced.

## Step results

### Healthy positive state

Immediately after seed, before Time or Schedule: `attention.items = []`, `positive = true`, `positive_title = "Nothing needs attention right now."` No fake attention fact. No warning row. Copy does **not** say “Everything is on track.”

**Does the positive state make it clear that CalibraytAI checked the Project and found nothing requiring attention?** **YES.**

That empty state cannot be re-shown on this vessel after Time/Schedule exist without de-authorizing governed work. Durable proof: no Time existed until entries **22+**; dedicated `test_positive_state_when_empty`; labour-only reconstruction with Used **0** produces zero labour facts.

### Labour getting close / below threshold / allowance used / over

Allowed remains **100.00** on Foundation / Concrete. Used is Approved only.

Durable Concrete Time (activity **14**):

| Entries | Hours | Status | Running Approved Used |
|---------|-------|--------|------------------------|
| 22–26 (2026-01-01…01-05) | 16+16+16+16+15 | APPROVED | **79.00** |
| 27–28 (2026-06-01…06-02) | 16+14 | RETURNED (were SUBMITTED for the waiting proof) | still **79.00** |
| 29 (2026-01-06) | 1 | APPROVED | **80.00** |
| 30–31 (2026-01-07…01-08) | 16+4 | APPROVED | **100.00** |
| 32 (2026-01-09) | 10 | APPROVED | **110.00** |

PERF-B labour law on those durable hours (same `_labour_attention_items` used live):

| Used | Waiting | Labour fact | Detail |
|------|---------|-------------|---------|
| 79.00 | 0 | **none** | 80% is informational only; 79 is quiet |
| 79.00 | 30 | **none** | Waiting does **not** drive the threshold |
| 80.00 | 0 | **Labour getting close** only | Used 80 of 100 hours |
| 100.00 | 0 | **Labour allowance used** only | Used 100 of 100 hours |
| 110.00 | 0 | **Labour over allowance** only | Used 110 of 100 hours. Over by 10 hours. Remaining is **none**, not negative |

No “Allowance used” while getting close. No “Getting close” at 100 or 110. No “Over allowance” at 80 or 100.

### Waiting does not drive threshold

Entries **27–28** were SUBMITTED (**30.00** waiting) while Approved Used was **79.00**. No Labour getting close fact. Those entries were then returned through normal `return_time` so later labour steps stay easy to audit. Dedicated tests corroborate.

### Extra Work needs review

`create_extra_work` → Element **Extra work** / Activity **Additional forming**. APPROVED **6.00** (entry **33**) + SUBMITTED **2.00** (entry **34**). Frozen Time `scope_origin` **EXTRA_WORK**. Lineage unauthorized before CO.

Needs Attention: **Extra work needs review** · `6 hours used · 2 hours waiting for approval`. Destination `/project-controls/change-orders?project_id=50`.

Authorized labour at that step remained Allowed **100.00** · Used **110.00** · Over by **10.00**. Extra **6** did **not** make Authorized Used 116.

Display order **before** Extra Work authorization (labour snapshot Used **110** / Extra **6+2** plus the live Schedule on this vessel):

1. Extra work needs review
2. Labour over allowance
3. Scheduled finish passed
4. Scheduled work has no approved Time
5. SEQUENCE

That order is **display order only**. No severity / rank / priority / score fields. Extra Work was **not** de-authorized later merely to recreate this list on the Hub.

### Extra Work authorization removes the fact

**CO-000023** Approved `Authorize additional forming` + `link_extra_work_to_change_order`.

| | Before | After |
|--|--------|--------|
| Extra work needs review | present | **gone** |
| Activity **15** lineage | EXTRA_WORK / unauthorized | CHANGE_ORDER / **authorized True** |
| Entry **33** `scope_origin` | EXTRA_WORK | **EXTRA_WORK** (stale Time origin unchanged) |
| Extra Used / Waiting on PERF-A extra bucket | 6 / 2 | **0 / 0** (`needs_review` **false**) |

Stale Time origin does **not** keep the attention fact alive. No double-count of Extra as both extra and a second labour getting-close fact. Authorized Used later includes the extra **6.00** plus Roof hours (see final Hub).

### Scheduled finish passed / finish-today false-alert

ACTIVE Foundation item **23**: `2026-09-01` → **`2026-09-10`**. Fact: **Scheduled finish passed** · `Scheduled to finish September 10, 2026`. Copy does **not** contain behind / late / incomplete / missed deadline. No completion inference.

ACTIVE Interior item **25**: start **=** end **= 2026-09-17** (today). **No** Scheduled finish passed for Interior. **No** no-approved-Time fact for Interior (start-today quiet).

### Scheduled work has no approved Time

ACTIVE Framing item **24**: start **2026-09-09** (< today), **no Approved Time** on Framing. Fact: **Scheduled work has no approved Time** · `Scheduled to start September 9, 2026`. Does **not** say “work has not started.”

### Start-today false-alert

Interior start **= today**. No no-approved-Time fact. Mandatory date-grain anti-nag. Live.

### Submitted does not suppress / Approved suppresses / unrelated Time

Roof item **26** start **2026-09-16**. Roofing activity **16** is ORIGINAL. SUBMITTED **2.00** (entry **35**, later approved) did **not** count as Approved. After APPROVED entries **35–36** (**4.00**), Roof’s no-approved-Time fact **disappears**.

**Live now:** Framing item **24** still has **Scheduled work has no approved Time** while Foundation has **110.00** Approved hours and Roof has **4.00** Approved hours. Unrelated Project Time does **not** suppress Framing. Dedicated tests corroborate the SUBMITTED-only moment on Roof.

No separate general Waiting attention fact.

### SEQUENCE reuse

`list_schedule_conflicts(ORG-001, project_id=50)` returns exactly kind **SEQUENCE**:

- label: `Schedule warning`
- summary: `Framing is scheduled before prior work is finished (Foundation).`
- review_url: `/projects/50#hub-schedule`

PERF-B surfaces the **same** label and summary. PERF-B does **not** compute a second sequence. Hub Schedule already shows the same SCH warning independently.

### Excluded SCH facts

Live `list_schedule_conflicts` kinds on this vessel: **SEQUENCE** only. Live Needs Attention types: labour over, scheduled finish passed, no approved Time, SEQUENCE. No assignment overlap, Crew overlap, USER, USER_THROUGH_CREW, PREDECESSOR_UNSCHEDULED, or unassigned-upcoming promotion. Dedicated tests cover the excluded kinds without overpopulating this vessel.

### Warning Law — live

With Needs Attention facts present:

- `submit_time` succeeded (entries **37** and **38**, then returned through normal review). Controls were not disabled.
- GET `/projects/50` **200**. GET `/time?project_id=50` **200** (browser Time review still shows Filter / Approve selected). GET `/project-controls/change-orders?project_id=50` **200** (New Change Order still present). GET `/work-structure/projects/50` **200**.
- Hub Schedule still offers Edit dates / Add work order / Change dates.
- No acknowledgement. No required resolution. No automatic mutation from attention. **No attention persistence tables.**

### Project Hub contractor UX

Live office Flask **5461** on current PERF-B code. Browser: `http://127.0.0.1:5461/projects/50#hub-labour`.

`#hub-labour` **Needs attention** is **above** Authorized work Allowed / Used / Over by / Waiting for approval.

Live list (after Extra Work authorization; Extra fact correctly gone):

1. Labour over allowance — Used 120 of 100 hours. Over by 20 hours → Labour
2. Scheduled finish passed — Scheduled to finish September 10, 2026 → Schedule
3. Scheduled work has no approved Time — Scheduled to start September 9, 2026 → Schedule
4. Schedule warning — Framing is scheduled before prior work is finished (Foundation). → Schedule

Short. Readable. No technical fact-type tokens. No severity scores. No traffic lights. No analytics overload.

**Could Ben look at Needs Attention and understand in a few seconds why CalibraytAI is asking him to look at this Project?** **YES.**

Final labour math on the Hub: Allowed **100.00** · Used **120.00** · Over by **20.00** · Waiting **2.00**. Foundation Used **110.00**. Extra work (now authorized) Used **6.00** Waiting **2.00** with Allowance not available. Roof Used **4.00**. Remaining is **none**, not negative.

### Action links

Implemented destinations point only to existing surfaces:

- Extra Work (when present) → `/project-controls/change-orders?project_id=50` (Change orders)
- Labour → `/projects/50#hub-labour`
- Schedule / SEQUENCE → `/projects/50#hub-schedule`

No mandatory action. No new workflow. No invented route.

### MONITOR firewall — live

`#hub-monitor` remains Estimated versus actual / Project Gross Margin / Direct Cost actuals. **No** Needs Attention heading inside MONITOR. `assemble_monitor_v1` does **not** import `assemble_project_performance` or `assemble_project_attention`. No financial formula change. Authorized change orders count **1** (CO-000023); CO revenue delta **$0.00**.

### Field firewall — live

Authenticated Field Today / Week / Month / Company Today / Project 50 / Time: **no** `#hub-labour`, **no** `Needs attention` heading. Server/HTML check. No physical iPhone retest.

### Operating-scope firewall

PERF-B is Project-level on Project **50**. No Division / Operating Unit / scope selector / new RBAC / organization-wide attention aggregation. `assemble_project_performance("ORG-002", 50)` → `TimeEntryNotFoundError` “Project not found.” Current Organization isolation intact. PERF-C **not** implemented.

## Protected occupancy — after

| Record | State |
|--------|--------|
| Projects 45 / 46 / 47 / 48 / 49 | **unchanged** (names, element/activity/time counts) |
| Project 27 / Estimate 28 / Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| PRODUCTION packages | **0** |
| Project 50 time | **17** entries (global time **38** = prior **21** + **17**) |
| Alembic | **`f9b0c1d2e3f4`** |

## Fresh post-UAT tests

| Command | Result |
|---------|--------|
| Dedicated | `./venv/bin/python -m pytest -q tests/test_project_needs_attention_fg035.py` **36 passed**, 339 warnings, **18.78s**, exit **0** |
| PERF-A + PERF-B | `./venv/bin/python -m pytest -q tests/test_project_labour_performance_fg035.py tests/test_project_needs_attention_fg035.py` **50 passed**, 463 warnings, **26.40s**, exit **0** |
| Focused | `./venv/bin/python -m pytest -q tests/test_work_structure_tax_wbs_fg035.py tests/test_work_scope_fg035.py tests/test_work_time_fg035.py tests/test_work_schedule_fg035.py tests/test_work_schedule_assignment_fg035.py tests/test_work_schedule_dependency_fg035.py tests/test_work_schedule_field_fg035.py tests/test_project_labour_performance_fg035.py tests/test_project_needs_attention_fg035.py tests/test_project_hub.py tests/test_field_web_fg021.py tests/test_monitor_v1_fg023.py` **206 passed**, 1047 warnings, **116.29s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1190 passed**, 0 failed, 4212 warnings, **746.12s**, exit **0** |

## Completeness

Every required PERF-B bounded live-UAT acceptance criterion is supported by durable live evidence and/or dedicated automated evidence as authorized when an earlier vessel state cannot be re-shown without de-authorizing governed work. **YES.**

## STOP

```text
PERF-B IMPLEMENTED / TESTED / BOUNDED SYNTHETIC LIVE UAT PASS.
NOT COMMITTED.
NOT PUSHED.
NO SCHEMA.
NO PERF-C.
V1 NOT RESCORED.
RETURN TO CHATGPT ARCHITECT.
```

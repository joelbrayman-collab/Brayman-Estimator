# FG-035 TIME live bounded UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-15 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | TIME **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted** |
| Alembic | **`f5d6e7f8a9b0 (head)`** revises **`f4c5d6e7f8a9`** |

## Scope

Prove duration-based field Time Entry, SCOPE inheritance, Extra Work from Time, submit / return / resubmit / approve, post-approval supersession, and the approved-labour-hours service. Do **not** implement SCH, PERF, CLOSE, LEARN, or QB-T. Do **not** mutate EST-2026-0019. V1 **not rescored**.

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME IMPLEMENTED
SCH NOT AUTHORIZED
PERF NOT AUTHORIZED
CLOSE NOT AUTHORIZED
LEARN NOT AUTHORIZED
QB-T NOT AUTHORIZED
ONE LOOP
ONE PLATFORM / ONE CODEBASE
V1 NOT RESCORED
```

## Decisions recorded

| Decision | Choice |
|----------|--------|
| Draft Time | **Not implemented.** Field Extra Work and Capture already submit in one action. Time is duration + work + hours; worker confirms by sending. Returned entries are the correction path before approval. |
| Offline Time | **V1 Time is online-session only.** Field IndexedDB remains capture-original retry. TIME does not invent a second sync engine and does **not** claim offline Time Entry. |
| Self-approval | **Fail closed.** Membership has no role exception. Worker cannot approve or return their own Time. |
| Hours bounds | Hours > 0; max **16.00** per entry; max **24.00** submitted+approved hours per worker per day; two decimal places. No future work dates. Historical dates allowed. |
| QB-T export flag | **Not stored.** QB-T later owns any EXPORTED lifecycle. |

## Git / Alembic

| Field | Value |
|--------|--------|
| Live current before upgrade | `f4c5d6e7f8a9` |
| Upgrade | `f4c5d6e7f8a9` → **`f5d6e7f8a9b0`** **PASS** |
| Product SHA | **`03c074fb1eb2bbca77ba86e495726c0e042c1979`** |
| Backup | `instance/brayman_estimator-backup-before-fg035-f5d6e7f8a9b0-20260915.db` (gitignored; not committed) |
| Backup size | 2,875,392 bytes (matches live source at backup time) |

## Protected occupancy (before and after)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft |
| Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| PRODUCTION packages | **0** |

## Synthetic UAT (ORG-001)

Not Joel’s production commercial occupancy. Not EST-2026-0019. Not project **42** or **43**.

| Step | Result |
|------|--------|
| Project | **id 44** `FG035-UAT TIME SYNTHETIC — NOT A CUSTOMER` |
| Estimate | `EST-2026-FG035-TIME-UAT` Issued / locked |
| Seed | Original Forms activity **ORIGINAL** |
| A. ORIGINAL | Worker **10** recorded **4.50** hours → submit → reviewer **11** approved → approved service **ORIGINAL 4.50** then **6.00** after the return-path correction on the same original activity |
| B. CHANGE ORDER | CO-linked activity Additional Forms layout inherited **CHANGE_ORDER** without the worker selecting the CO → submit → approve → **14.00** CHANGE_ORDER hours |
| Extra Work | `Move garage drain` via existing SCOPE `create_extra_work` → **3.50** EXTRA_WORK approved hours |
| Return / resubmit | **2.00** returned with reason, resubmitted **1.75**, approved, then superseded to **1.50** |
| Approved total | **23.50** approved / **0.00** pending · **5** entries · **12** history rows |
| EST-2026-0019 | Unchanged |
| PRODUCTION packages | **0** |

Office `/time` review, Field `/field/.../time`, My time, Hub `#hub-time`, and Extra Work highlighting were proven in dedicated tests (`tests/test_work_time_fg035.py`). Live UAT used the same services against the migrated development/UAT SQLite.

Browser verification 2026-09-15 (Flask `--no-reload` TLS **5445**, after restart onto TIME code):

- Office `/time` Time review: filters, TIME UAT Worker, Extra Work highlighted, Original 4.50 + 1.50, Change Order 14.00, Extra Work 3.50.
- Hub `/projects/44#hub-time`: approved **23.50**, waiting **0.00**, Extra work hours **3.50**.
- Field Confirm and Time → `/field/projects/44/time`: iPhone stacked Date → work item → work → hours → **+ Extra work** with the Extra Work rule; hierarchical Foundation filters work to Forms / Additional Forms layout.
- Field `/field/time` as the office user: empty (TIME UAT Worker owns the synthetic entries).
- Landscape Field Time Extra Work clipping found and CSS-fixed (`field-panel-time` full-width Extra Work / note / send). Desktop landscape screenshot after that CSS fix was blocked when the browser session disconnected; iPhone Extra Work panel was verified after the fix.

Physical iPhone Time UAT: **DEFERRED / NOT CLAIMED AS PASS**.

## Tests

| Command | Result |
|---------|--------|
| Dedicated TIME | `./venv/bin/python -m pytest -q tests/test_work_time_fg035.py` **7 passed** (included in focused TIME+SCOPE+TAX/WBS **31 passed**, 278 warnings, **16.29s**, exit **0**) |
| Hub / Field / MONITOR + TIME | `tests/test_project_hub.py tests/test_field_web_fg021.py tests/test_monitor_v1_fg023.py tests/test_work_time_fg035.py` **76 passed**, 258 warnings, **35.03s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1083 passed**, 3616 warnings, **466.85s**, exit **0** |

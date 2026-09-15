# FG-035 SCOPE live bounded UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-15 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | SCOPE **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted** |
| Alembic | **`f4c5d6e7f8a9 (head)`** revises **`f3b4c5d6e7f8`** |

## Scope

Prove ORIGINAL / CHANGE_ORDER / EXTRA_WORK lineage on Project work structure, Change Order deltas without rewriting original estimate evidence, Extra Work capture, and contractor Hub/Field copy. Do **not** implement TIME, SCH, PERF, CLOSE, LEARN, or QB-T. Do **not** mutate EST-2026-0019. V1 **not rescored**.

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
SCOPE IMPLEMENTED
TIME NOT AUTHORIZED
SCH NOT AUTHORIZED
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
|-------|--------|
| Live current before upgrade | `f3b4c5d6e7f8` |
| Upgrade | `f3b4c5d6e7f8` → **`f4c5d6e7f8a9`** **PASS** |
| Backup | `instance/brayman_estimator-backup-before-fg035-f4c5d6e7f8a9-20260915.db` (gitignored; not committed) |
| Backup size | 2,793,472 bytes (matches live source at backup time) |

## Protected occupancy (before and after)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft |
| Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| PRODUCTION packages | **0** |

## Existing TAX/WBS backfill (project **42**)

| Row | Result |
|------|--------|
| Activity **1** FG035 UAT Forms | **ORIGINAL** · ESTIMATE_SEED · snapshot pin **1** · hours **5.000000** |
| Element **1** Foundation | **ORIGINAL** · ESTIMATE_SEED |
| Element **2** FG035 project-only access | **EXTRA_WORK** fail-closed (PROJECT source; not original estimate evidence) |

## Synthetic UAT (ORG-001)

Not Joel’s production commercial occupancy. Not EST-2026-0019. Not project **42**.

| Step | Result |
|-------|--------|
| Project | **id 43** `FG035-UAT SCOPE SYNTHETIC — NOT A CUSTOMER` |
| Estimate | `EST-2026-FG035-SCOPE-UAT` Issued / locked · snapshot hours **40.000000** |
| Seed | seed id **2**; Activity **2** **ORIGINAL**; pin retained |
| Approved CO delta | +12 hours; stored original remains **40**; current authorized **52** |
| Extra work | Activity **3** `Move/add garage drain` under Foundation · **EXTRA_WORK**; unresolved query returns it |
| History | **2** append-only rows |
| EST-2026-0019 | Unchanged |
| PRODUCTION packages | **0** |

Office Hub / Field Extra work / CSRF were proven in dedicated tests (`tests/test_work_scope_fg035.py`). Live UAT used the same services against the migrated development/UAT SQLite.

## Tests

| Command | Result |
|---------|--------|
| Dedicated SCOPE | `./venv/bin/python -m pytest -q tests/test_work_scope_fg035.py` **10 passed** |
| Focused | `tests/test_work_scope_fg035.py tests/test_work_structure_tax_wbs_fg035.py` **23 passed**, 193 warnings, **12.80s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1075 passed**, 3531 warnings, **437.62s**, exit **0** |

## Non-claims

TIME / SCH / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. Full field timesheets **not implemented**. Visual Schedule **not implemented**. MONITOR labour-hours **not implemented**. FG-023 **not reopened**. FG-032 **not rewritten**. Help / Voice / User Manual **not implemented**. V1 **not rescored** (**60% / 4 of 11**). Physical iPhone Extra work UAT **DEFERRED / NOT CLAIMED AS PASS**.

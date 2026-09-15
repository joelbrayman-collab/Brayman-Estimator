# FG-035 TAX/WBS live bounded UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-15 |
| Gate | [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL** |
| Slice | TAX/WBS **IMPLEMENTED / LIVE-MIGRATED / SYNTHETIC UAT PASS** |
| ADR | [ADR-053](../adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted** |
| Alembic | **`f3b4c5d6e7f8 (head)`** revises **`f2a3b4c5d6e7`** |

## Scope

Prove the three-layer work taxonomy and explicit EstimateLabourSnapshot seed. Do **not** implement SCOPE, TIME, SCH, PERF, CLOSE, LEARN, or QB-T. Do **not** mutate EST-2026-0019. V1 **not rescored**.

```text
FG-035:
OPEN / PARTIAL
TAX/WBS IMPLEMENTED
LATER SLICES NOT AUTHORIZED
ONE LOOP
ONE PLATFORM / ONE CODEBASE
V1 NOT RESCORED
```

## Git / Alembic

| Field | Value |
|-------|--------|
| Live current before upgrade | `f2a3b4c5d6e7` |
| Upgrade | `f2a3b4c5d6e7` → **`f3b4c5d6e7f8`** **PASS** |
| Backup | `instance/brayman_estimator-backup-before-fg035-f3b4c5d6e7f8-20260915.db` (gitignored; not committed) |
| Backup size | 2,658,304 bytes (matches live source at backup time) |

## Protected occupancy (before and after)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft |
| Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| PRODUCTION packages | **0** |

## Synthetic UAT (ORG-001)

Not Joel’s production commercial occupancy. Not EST-2026-0019.

| Step | Result |
|-------|--------|
| Baseline catalog | `GEN` / General construction **ACTIVE** |
| Organization extension | Work type id **2** `FG035-UAT-TES-EXTRA` / FG035-UAT TES extra |
| Project | **id 42** `FG035-UAT TAX/WBS SYNTHETIC — NOT A CUSTOMER` |
| Estimate | `EST-2026-FG035-UAT` version **39** Issued / locked |
| Seed | `project_work_structure_seeds` id **1**; Element **Foundation**; Activity **FG035 UAT Forms**; hours **5.000000**; quantity **100 sqft**; snapshot pin retained |
| Duplicate seed | Fail-closed: `This project's work plan is already built.` |
| Project-specific add | `FG035 project-only access`; source **PROJECT**; not added to catalog |
| Retire | Row kept **INACTIVE** |
| EST-2026-0019 | Unchanged |
| PRODUCTION packages | **0** |

Office HTTP catalog / Hub / CSRF were proven in dedicated tests (`tests/test_work_structure_tax_wbs_fg035.py`). Live UAT used the same services against the migrated development/UAT SQLite.

## Tests

| Command | Result |
|---------|--------|
| Dedicated | `./venv/bin/python -m pytest -q tests/test_work_structure_tax_wbs_fg035.py` **13 passed** (included in focused/full) |
| Focused | `tests/test_work_structure_tax_wbs_fg035.py tests/test_labour_engine.py tests/test_project_hub.py tests/test_estimates.py tests/test_auth_fg018.py` **98 passed**, 400 warnings, **39.20s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1065 passed**, 3403 warnings, **456.75s**, exit **0** |

## Non-claims

SCOPE / TIME / SCH / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. Clock-in **not implemented**. Visual Schedule **not implemented**. FG-023 **not reopened**. FG-032 **not rewritten**. V1 **not rescored** (**60% / 4 of 11**).

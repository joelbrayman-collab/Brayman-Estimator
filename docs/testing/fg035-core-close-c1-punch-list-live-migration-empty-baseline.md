# FG-035 CORE CLOSE C1 Punch List live migration — empty baseline

| Attribute | Value |
|-----------|--------|
| Status | **PASS.** **LIVE-MIGRATED.** **EMPTY LIVE BASELINE VERIFIED.** **NOT LIVE-UATed WITH MUTATING DATA.** [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) remains **OPEN / PARTIAL**. CORE CLOSE remains **PARTIAL**. |
| Date | 2026-09-19 |
| Gate | FG-035 CORE CLOSE C1 Contractor Punch List only |
| Product SHA | **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`** |
| Pin SHA | **`7bdbf191fe062f43550a9ccb81abf6eb21db8691`** |
| Alembic | **`c3d4e5f6a7b8` → `d4e5f6a7b8c9 (head)`** |
| V1 | **NOT RESCORED** (**65% / 4 of 11**; secondary **79% / 22 of 28**) |

```text
C1:
IMPLEMENTED /
TESTED /
COMMITTED /
PUSHED /
SHA-PINNED /
LIVE-MIGRATED /
EMPTY LIVE BASELINE VERIFIED /
NOT LIVE-UATed WITH MUTATING DATA

PUNCH LIST:
LIVE /
0 ITEMS

C2 CLIENT FINAL WALKTHROUGH:
NOT IMPLEMENTED

COMPLETION SIGN-OFF:
NOT IMPLEMENTED

CLOSE/REOPEN:
SEALED

CORE CLOSE:
PARTIAL

FG-035:
OPEN / PARTIAL

V1 NOT RESCORED
```

This file records live migration and empty Punch List baseline only. It does **not** create Punch List items. It does **not** implement C2 Client Final Walkthrough or Completion Sign-Off. Close/Reopen remains sealed and was **not** live-executed.

---

## Git / Alembic

| Field | Value |
|-------|--------|
| Branch | `main` |
| Pre-migration HEAD = origin/main | `7bdbf191fe062f43550a9ccb81abf6eb21db8691` |
| Divergence | `0 0` |
| Working tree before migrate | **CLEAN** |
| Live current before | `c3d4e5f6a7b8` |
| Graph head before | `d4e5f6a7b8c9 (head)` |
| Command | `FLASK_DEBUG=1 ./venv/bin/flask --app app db upgrade d4e5f6a7b8c9` |
| Exit | **0** |
| Applied | `c3d4e5f6a7b8` → **`d4e5f6a7b8c9`** |
| Live current after | **`d4e5f6a7b8c9 (head)`** |
| Graph heads after | **`d4e5f6a7b8c9 (head)`** |
| Downgrade / stamp | **not performed** |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg035-punch-list-d4e5f6a7b8c9-20260919-073221.db` |
| Source bytes | 3,248,128 |
| Backup bytes | 3,248,128 |
| Source SHA-256 | `7384ecb862d87c7e251a162dceffdd1a18417783f3ed8b082d83d63f1731e199` |
| Backup SHA-256 | `7384ecb862d87c7e251a162dceffdd1a18417783f3ed8b082d83d63f1731e199` |
| Backup Alembic | `c3d4e5f6a7b8` |
| Copy method | Idle filesystem `cp` after stopping office Flask holders on ports 5460/5461. No WAL. Recovery stash **not** altered. Restarted after upgrade. |

## Punch List schema (after)

`project_punch_list_items` and `project_punch_list_item_events` exist. Status **OPEN / COMPLETE**. Origin schema recognizes **CONTRACTOR** and future **CLIENT_WALKTHROUGH**. C1 creates **CONTRACTOR** only. No C2 foreign keys. No seed. No fake “No deficiencies” row.

## Empty live baseline

| Assertion | Result |
|-----------|--------|
| Punch List item count | **0** |
| OPEN | **0** |
| COMPLETE | **0** |
| CONTRACTOR origin | **0** |
| CLIENT_WALKTHROUGH origin | **0** |
| Punch List events | **0** |
| Migration seed | **none** |
| Automatic Project items | **none** |

## Occupancy non-regression

| Counter | After |
|---------|--------|
| Projects | **50** |
| ACTIVE / CLOSED | **50 / 0** |
| Project lifecycle events | **0** |
| ORG-001 Owner | Membership **1** / User **1** / Joel Brayman |
| Owner SET events | **1** |
| `COMPANY_MANAGEMENT` grants | **1** (id **1** / membership **1**) |
| EST-2026-0019 | Estimate **28** Draft / Project **27** Estimating+ACTIVE / Version **34** Draft |
| PRODUCTION packages | **0** |
| Live Close | **NO** |
| Live Reopen | **NO** |
| Live Punch List item created | **NO** |

## Office process restart / empty Hub smoke

Office Flask on ports **5460** / **5461** was stopped before backup, then restarted **after** `current=heads=d4e5f6a7b8c9` with `--no-reload`. Login **200**. Unauthenticated Hub **302** login (not 500). Authenticated Project **27** Hub render contains `#hub-punch-list`, heading **Punch List**, empty copy **Nothing is on the Punch List**, and **Add Punch List Item**. No Client Final Walkthrough. No Completion Sign-Off. No Punch List POST. No Close. No Reopen.

## Tests

| Command | Result |
|---------|--------|
| Dedicated | `./venv/bin/python -m pytest -q tests/test_core_close_punch_list_c1_fg035.py` **26 passed**, 56 warnings, **14.51s**, exit **0** |
| Focused | CORE CLOSE + Project Work + authority **228 passed**, 862 warnings, **110.42s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1364 passed**, 4786 warnings, **808.82s**, exit **0** |

Live occupancy rechecked after tests: Alembic **`d4e5f6a7b8c9 (head)`**, Punch List items **0**, grants **1**, Projects **50 / 50 / 0 / 0**.

## Firewalls

No live Punch List item. No C2 invitation/form/photo/review queue. No Completion Sign-Off. No Native Signing change. No Field Punch List. No live Close/Reopen. Recovery stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved.

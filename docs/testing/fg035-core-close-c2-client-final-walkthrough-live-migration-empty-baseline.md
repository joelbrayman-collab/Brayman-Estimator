# FG-035 CORE CLOSE C2 Client Final Walkthrough live migration — empty baseline

| Attribute | Value |
|-----------|--------|
| Status | **PASS.** **LIVE-MIGRATED.** **EMPTY LIVE BASELINE VERIFIED.** **NOT LIVE-UATed WITH CLIENT DATA.** [FG-035](../feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) remains **OPEN / PARTIAL**. CORE CLOSE remains **PARTIAL**. |
| Date | 2026-09-19 |
| Gate | FG-035 CORE CLOSE C2 Client Final Walkthrough only |
| Product SHA | **`ec4ef9956025fd8e281c12c17d84493b121f8337`** |
| Pin SHA | **`14bd00b88c3a25ea7576be1d3dd2bbe288d272de`** |
| Alembic | **`d4e5f6a7b8c9` → `e5f6a7b8c9d0 (head)`** |
| V1 | **NOT RESCORED** (**65% / 4 of 11**; secondary **79% / 22 of 28**) |

```text
C2:
IMPLEMENTED /
TESTED /
COMMITTED /
PUSHED /
SHA-PINNED /
LIVE-MIGRATED /
EMPTY LIVE BASELINE VERIFIED /
NOT LIVE-UATed WITH CLIENT DATA

C1 PUNCH LIST:
LIVE /
UNCHANGED /
0 ITEMS

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

This file records live migration and empty Client Final Walkthrough baseline only. It does **not** create invitations, tokens, client responses, or Punch List items. It does **not** implement Completion Sign-Off. Close/Reopen remains sealed and was **not** live-executed.

---

## Git / Alembic

| Field | Value |
|-------|--------|
| Branch | `main` |
| Pre-migration HEAD = origin/main | `14bd00b88c3a25ea7576be1d3dd2bbe288d272de` |
| Divergence | `0 0` |
| Working tree before migrate | **CLEAN** |
| Live current before | `d4e5f6a7b8c9` |
| Graph head before | `e5f6a7b8c9d0 (head)` |
| Command | `FLASK_DEBUG=1 ./venv/bin/flask --app app db upgrade e5f6a7b8c9d0` |
| Exit | **0** |
| Applied | `d4e5f6a7b8c9` → **`e5f6a7b8c9d0`** |
| Live current after | **`e5f6a7b8c9d0 (head)`** |
| Graph heads after | **`e5f6a7b8c9d0 (head)`** |
| Downgrade / stamp | **not performed** |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg035-c2-e5f6a7b8c9d0-20260919-084414.db` |
| Source bytes | 3,313,664 |
| Backup bytes | 3,313,664 |
| Source SHA-256 | `00fad237fc77e48163763371fe33fb2d5e8075dbe615eae17443d5525b7719cb` |
| Backup SHA-256 | `00fad237fc77e48163763371fe33fb2d5e8075dbe615eae17443d5525b7719cb` |
| Backup Alembic | `d4e5f6a7b8c9` |
| Copy method | Idle filesystem `cp` after stopping office Flask holders on ports 5460/5461. No WAL. Recovery stash **not** altered. Restarted after upgrade. |

## C2 schema (after)

`project_final_walkthrough_invitations`, `project_final_walkthrough_items`, and `project_final_walkthrough_access_attempts` exist. Invitation status **OPEN / RESPONDED / EXPIRED / REVOKED**. Response mode **ITEMS / NOTHING_TO_ADD**. Item review **PENDING_REVIEW / ACCEPTED_TO_PUNCH_LIST / ALREADY_ADDRESSED / DISCUSS_OR_OUT_OF_SCOPE**. Token stored as lookup_key + SHA-256 hash. No seed. No automatic invitation.

## Empty live baseline

| Assertion | Result |
|-----------|--------|
| Final Walkthrough invitations | **0** |
| Client responses | **0** |
| Client submitted items | **0** |
| Pending reviews | **0** |
| Accepted-to-Punch-List C2 items | **0** |
| Nothing-to-add responses | **0** |
| Access attempts | **0** |
| Migration seed | **none** |
| Automatic invitation | **none** |
| Automatic Punch List item | **none** |

## C1 non-regression

| Assertion | Result |
|-----------|--------|
| Punch List item count | **0** |
| OPEN | **0** |
| COMPLETE | **0** |
| CLIENT_WALKTHROUGH origin | **0** |
| Punch List events | **0** |

## Occupancy non-regression

| Counter | After |
|---------|--------|
| Projects | **50** |
| ACTIVE / CLOSED | **50 / 0** |
| Project lifecycle events | **0** |
| ORG-001 Owner | Membership **1** / User **1** / Joel Brayman |
| Owner SET events | **1** |
| `COMPANY_MANAGEMENT` grants | **1** (membership **1**) |
| EST-2026-0019 | Estimate **28** Draft / Project **27** ACTIVE / Version **34** Draft |
| PRODUCTION packages | **0** |
| Live Close | **NO** |
| Live Reopen | **NO** |
| Live invitation created | **NO** |
| Live client response created | **NO** |
| Live Punch List item created | **NO** |

## Office process restart / empty Hub smoke

Office Flask on ports **5460** / **5461** was stopped before backup, then restarted **after** `current=heads=e5f6a7b8c9d0` with `--no-reload`. Login **200**. Unauthenticated Hub **302** login (not 500). Authenticated GET-only Project **27** Hub render contains `#hub-final-walkthrough`, heading **Final Walkthrough**, empty copy **Final Walkthrough not sent**, and **Invite Client to Final Walkthrough**. Punch List empty copy remains **Nothing is on the Punch List**. No Completion Sign-Off. No invitation POST. No Punch List POST. No Close. No Reopen.

## Tests

| Command | Result |
|---------|--------|
| Dedicated | `./venv/bin/python -m pytest -q tests/test_core_close_client_final_walkthrough_c2_fg035.py` **34 passed**, 74 warnings, **18.70s**, exit **0** |
| Focused | CORE CLOSE + Hub + CO/work + auth + Field + MONITOR + PERF **352 passed**, 1303 warnings, **198.21s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1398 passed**, 4860 warnings, **779.71s**, exit **0** |

Live occupancy rechecked after tests: Alembic **`e5f6a7b8c9d0 (head)`**, C2 invitations **0**, Punch List items **0**, grants **1**, Projects **50 / 50 / 0 / 0**.

## Firewalls

No live client invitation. No live client token issued. No live client response. No live C2 item. No live Punch List item. No Completion Sign-Off. No Native Signing change. No live Close/Reopen. Recovery stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved.

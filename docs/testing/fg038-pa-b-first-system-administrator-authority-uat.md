# FG-038 PA-B Stage 2 — first System Administrator bounded live UAT

| Attribute | Value |
|-----------|--------|
| Status | **PASS.** **LIVE APPOINT UAT PASS.** **LIVE REMOVE UAT PASS.** **ZERO CURRENT SYS ADMINS.** [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) remains **OPEN / PARTIAL**. |
| Date | 2026-09-20 |
| Gate | FG-038 PA-B Stage 2 only |
| Product SHA | **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`** |
| Pin SHA | **`3a4735b40ee4580ad3ae419569cafb7bdec32352`** |
| Stage 1 governance SHA | **`162bcb60d09bb32bd231ed0753c020e5c0720a81`** |
| Alembic | **`f6a7b8c9d0e1 (head)`** unchanged |
| V1 | **NOT RESCORED** (**65% / 4 of 11**; secondary **79% / 22 of 28**) |

```text
FG-038 PA-B STAGE 2:
LIVE APPOINT UAT PASS
LIVE REMOVE UAT PASS
ZERO CURRENT SYS ADMINS
ORG-001 MEMBERSHIP 5 / USER 6 / AUTH-B UAT USER
ACTOR USER 1 / JOEL BRAYMAN
APPOINT EVENTS 1
REMOVE EVENTS 1
OWNER UNCHANGED / MEMBERSHIP 1
COMPANY_MANAGEMENT UNCHANGED / 1
NO PEOPLE UI
NO PERSON FOUNDATION
NO LIVE CLOSE / REOPEN
V1 NOT RESCORED
```

This file records the authorized temporary first live Sys Admin appointment and removal. Current authority is **0**. Append-only APPOINT then REMOVE history is **permanent** and must **not** be cleaned up. It does **not** implement People & Access UI or Person / Worker identity.

Stage 1: [fg038-pa-b-live-migration-zero-sys-admin-checkpoint.md](fg038-pa-b-live-migration-zero-sys-admin-checkpoint.md).

---

## Git / Alembic (pre-appoint)

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD = origin/main | `162bcb60d09bb32bd231ed0753c020e5c0720a81` |
| Divergence | `0 0` |
| Working tree | **CLEAN** |
| Live current / heads | **`f6a7b8c9d0e1 (head)`** |

## Pre-UAT occupancy

| Counter | Before |
|---------|--------|
| Current Sys Admin rows | **0** |
| APPOINT events | **0** |
| REMOVE events | **0** |
| ORG-001 Owner | Membership **1** / User **1** / Joel Brayman |
| Owner SET events | **1** |
| Membership 5 | ORG-001 / User **6** / AUTH-B UAT User / membership ACTIVE / user ACTIVE |
| Membership 5 stored domains | **none** (not Domain B; AUTH-B is a UAT name) |
| `COMPANY_MANAGEMENT` grants | **1** (membership **1** only) |
| Sensitive Financial / C | **0** |
| C2 invitations / items / attempts | **0 / 0 / 0** |
| Punch List items | **0** |
| Projects / ACTIVE / CLOSED / events | **50 / 50 / 0 / 0** |
| Users / memberships | **14 / 13** |
| EST-2026-0019 | Estimate **28** Draft / Project **27** ACTIVE |

## Live APPOINT

```text
FLASK_DEBUG=1 ./venv/bin/flask --app app auth appoint-system-administrator \
  --organization-id ORG-001 \
  --membership-id 5 \
  --actor-user-id 1
```

CLI output: `System Administrator membership 5 is appointed for organization ORG-001.`  
Exit **0**. No other organization/membership/actor.

## Post-APPOINT

| Assertion | Result |
|-----------|--------|
| Current Sys Admin rows | **1** (`id` 1, org ORG-001, membership **5**, appointed_by User **1**) |
| Membership 5 / User 6 `is_system_administrator` | **TRUE** |
| Membership 5 `is_instance_owner` | **FALSE** |
| User 6 owner-or-sys-admin | **TRUE because SYS ADMIN** |
| Joel `is_system_administrator` | **FALSE** |
| Joel owner-or-sys-admin | **TRUE because OWNER** |
| APPOINT events | **1** (org ORG-001, membership **5**, actor User **1**, identifier Joel Brayman, timestamp populated) |
| REMOVE events | **0** |
| Owner pointer / SET | Membership **1** / **1** |
| B / C | **1** (membership **1**) / **0** |
| Membership 5 stored domains | still **none** |
| `actor_can_close_or_reopen(User 6, ORG-001)` | **TRUE** (GET/POST Close **not** executed) |
| Sys Admin appoint Membership 6 | **DENIED** `Only the Instance Owner may appoint a System Administrator.` CLI exit **1**. Current rows remain **1** |
| Sys Admin remove Owner Membership 1 | **DENIED** Owner-remove blocked. Owner unchanged |
| Sys Admin deactivate Owner membership / user | **DENIED**. Membership 1 ACTIVE. User 1 ACTIVE |
| Same-current APPOINT Membership 5 by Owner | CLI exit **0**; current rows **1**; APPOINT events **1**; no duplicate event |

## Live REMOVE

```text
FLASK_DEBUG=1 ./venv/bin/flask --app app auth remove-system-administrator \
  --organization-id ORG-001 \
  --membership-id 5 \
  --actor-user-id 1
```

CLI output: `System Administrator membership 5 is removed for organization ORG-001.`  
Exit **0**.

## Post-REMOVE / final

| Assertion | Result |
|-----------|--------|
| Current Sys Admin rows | **0** |
| Membership 5 / User 6 `is_system_administrator` | **FALSE** |
| User 6 owner-or-sys-admin | **FALSE** |
| `actor_can_close_or_reopen(User 6)` | **FALSE** |
| APPOINT events | **1** preserved |
| REMOVE events | **1** (org ORG-001, membership **5**, actor User **1**, identifier Joel Brayman, timestamp populated) |
| Owner | Membership **1** / User **1** / Joel Brayman / SET **1** / effective **TRUE** |
| B / C | **1** / **0** |
| Membership 5 ordinary access | unchanged (no stored grant; membership ACTIVE; user ACTIVE) |
| C2 / Punch / Projects / lifecycle | **0 / 0 / 0** · **0** · **50 ACTIVE / 0 CLOSED** · **0** |
| Users / memberships | **14 / 13** unchanged |
| Ben | still **ABSENT** |

## Tests

| Command | Result |
|---------|--------|
| Focused | `tests/test_system_administrator_authority_fg038.py tests/test_instance_owner_authority_fg038.py tests/test_core_close_close_reopen_fg035.py tests/test_auth_fg018.py tests/test_access_domains.py` **155 passed**, 462 warnings, **88.17s**, exit **0** (PA-B **38**; PA-A **35**; Close/Reopen **22**; FG-018 **37**; FG-037 **23**) |
| Full suite | **not run** (no product/code change) |

Live occupancy rechecked after tests: current Sys Admin **0**, APPOINT **1**, REMOVE **1**, Owner Membership **1**, B **1**, C **0**, C2 **0 / 0 / 0**, Punch **0**.

## Firewalls

No leftover live Sys Admin. No second Sys Admin. Membership **1** was not appointed. No B/C grant created. No Owner mutation. No live Close/Reopen. No Person/User/Membership/Ben creation. No People UI. Recovery stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved. APPOINT/REMOVE history **not** deleted.

## Next block (not this UAT)

People UI cannot yet implement frozen Person law. Next product block is **PA-C Person / Worker identity foundation** (Person ≠ Platform User; no automatic login or Domain A). Not implemented here.

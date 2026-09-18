# FG-038 PA-A Stage 2 — first ORG-001 Instance Owner authority UAT

| Attribute | Value |
|-----------|--------|
| Status | **PASS.** **FIRST OWNER ASSIGNED / LIVE AUTHORITY UAT PASS.** Instance Owner foundation **LIVE / OPERATIONAL**. [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) remains **OPEN / PARTIAL**. |
| Date | 2026-09-18 |
| Gate | FG-038 PA-A Stage 2 only |
| Product SHA | **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`** |
| Stage 1 governance SHA | **`b434b041b4c873d62a2f2e8926c16e563e786e6d`** |
| Alembic | **`c3d4e5f6a7b8 (head)`** unchanged |
| V1 | **NOT RESCORED** (**65% / 4 of 11**; secondary **79% / 22 of 28**) |

```text
FG-038 PA-A STAGE 2:
FIRST OWNER ASSIGNED
LIVE AUTHORITY UAT PASS
ORG-001 MEMBERSHIP 1 / USER 1 / JOEL BRAYMAN
OWNER SET EVENTS 1
ISOLATION ORGS OWNERLESS
COMPANY_MANAGEMENT UNCHANGED / 1
OWNER IS NOT DOMAIN B
SYS ADMIN NOT IMPLEMENTED
NO PEOPLE UI
NO CLOSE / REOPEN
CORE CLOSE OWNER AUTHORITY BLOCKER CLEARED FOR ORG-001
V1 NOT RESCORED
```

This file records the authorized first live SET and bounded authority UAT. It does **not** implement Close/Reopen, Sys Admin, or People & Access UI.

Stage 1: [fg038-pa-a-live-migration-ownerless-checkpoint.md](fg038-pa-a-live-migration-ownerless-checkpoint.md).

---

## Git / Alembic (pre-SET)

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD = origin/main | `b434b041b4c873d62a2f2e8926c16e563e786e6d` |
| Divergence | `0 0` |
| Working tree | **CLEAN** |
| Live current / heads | **`c3d4e5f6a7b8 (head)`** |

## Pre-SET occupancy

| Counter | Before |
|---------|--------|
| Organizations | **3** all **OWNERLESS** |
| Instance Owners | **0** |
| SET events | **0** |
| `COMPANY_MANAGEMENT` grants | **1** |
| Projects / ACTIVE / CLOSED / events | **50 / 50 / 0 / 0** |

## Target / actor (read-only, then SET)

| Fact | Result |
|------|--------|
| Organization | `ORG-001` exists |
| Membership 1 | `organization_id=ORG-001`, `user_id=1`, `is_active=TRUE` |
| User 1 | `display_name=Joel Brayman`, `is_active=TRUE` |
| Actor User 1 | same active User |
| Independent B fact | Membership 1 has `COMPANY_MANAGEMENT` — **not** the reason SET was allowed |

## Live SET

```text
FLASK_DEBUG=1 ./venv/bin/flask --app app auth set-instance-owner \
  --organization-id ORG-001 \
  --membership-id 1 \
  --actor-user-id 1
```

CLI output: `Instance Owner membership 1 is set for organization ORG-001.`  
Exit **0**. No other organization/membership/actor.

## Post-SET pointer / event

| Assertion | Result |
|-----------|--------|
| ORG-001 `instance_owner_membership_id` | **1** |
| `instance_owner_set_at` | `2026-09-18 13:45:37.850447` |
| `instance_owner_set_by_user_id` | **1** |
| ORG-FG014-UAT / ORG-002 pointers | **NULL** |
| Effective Owners | **1** |
| SET events | **1** |
| Event org / type / previous / new / actor | `ORG-001` / `SET` / **NULL** / **1** / **1** |
| `actor_identifier` | `Joel Brayman` |
| `created_at` | populated (same timestamp as set_at) |

## Authority UAT

| Check | Result |
|-------|--------|
| `get_instance_owner_membership('ORG-001')` | Membership **1** |
| `is_instance_owner(User 1, 'ORG-001')` | **True** |
| `require_instance_owner` User 1 | **AUTHORIZED** (returns None) |
| combined helper User 1 | **AUTHORIZED** |
| `is_system_administrator(User 1, ORG-001)` | **False** |
| AUTH-B User 6 `is_instance_owner` | **False** |
| User 6 require / combined | **403** |
| Unauthenticated probe | **302** `/login?next=...` |
| Isolation owner helpers | **None / False** |
| User 1 Owner of isolation orgs | **False** |
| Grants after SET | still **1** on membership **1**; no create/remove |
| `deactivate_membership(Membership 1)` | **refused** before commit; membership remains active |
| `deactivate_user(User 1)` | **refused** before commit; user remains active |
| Same-current `set_instance_owner(ORG-001, 1, 1)` | pointer stays **1**; event count stays **1** |

Deactivation used the live service raise-before-commit path. Membership 1 and User 1 were **not** left inactive.

## Occupancy after SET / UAT / tests

Projects **50 / 50 ACTIVE / 0 CLOSED / 0 lifecycle events**. EST-2026-0019 Estimate **28** Draft / Project **27** Estimating+ACTIVE / Version **34** Draft. PRODUCTION packages **0**. Grants **1**. Isolation orgs ownerless.

## Tests

| Command | Result |
|---------|--------|
| Dedicated | `./venv/bin/python -m pytest -q tests/test_instance_owner_authority_fg038.py` **35 passed**, 88 warnings, **16.83s**, exit **0** |
| Focused | four-file set **113 passed**, 306 warnings, **45.72s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1316 passed**, 4597 warnings, **683.84s**, exit **0** |

## CORE CLOSE readiness

`require_instance_owner_or_system_administrator` now **ALLOW** for User 1 / ORG-001 and **DENY** for ordinary ORG-001 non-Owner, isolation orgs, and Sys Admin (False). **CORE CLOSE OWNER AUTHORITY BLOCKER: CLEARED FOR ORG-001.** Close/Reopen **NOT IMPLEMENTED**.

## Firewalls

No other Owner. No Sys Admin. No People UI. No Close/Reopen. No `COMPANY_MANAGEMENT` mutation. Recovery stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved.

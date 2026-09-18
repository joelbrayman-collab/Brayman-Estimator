# FG-038 PA-A Stage 1 live migration — ownerless checkpoint

| Attribute | Value |
|-----------|--------|
| Status | **PASS.** **LIVE-MIGRATED.** Subsequent Stage 2 **FIRST OWNER ASSIGNED** ([fg038-pa-a-first-instance-owner-authority-uat.md](fg038-pa-a-first-instance-owner-authority-uat.md)). [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) remains **OPEN / PARTIAL**. |
| Date | 2026-09-18 |
| Gate | FG-038 PA-A Stage 1 only |
| Product SHA | **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`** |
| Preflight commit | **`a42ffe59005f8e282d4dbbfcbcbc0b5bbb86db8d`** (`docs: freeze FG-038 PA-A live migration owner preflight`) |
| Alembic | **`b2c3d4e5f6a7` → `c3d4e5f6a7b8 (head)`** |
| V1 | **NOT RESCORED** (**65% / 4 of 11**; secondary **79% / 22 of 28**) |

```text
FG-038 PA-A STAGE 1:
LIVE-MIGRATED
NO OWNER ASSIGNED
3 ORGANIZATIONS OWNERLESS
0 INSTANCE OWNERS
0 OWNER SET EVENTS
COMPANY_MANAGEMENT UNCHANGED / 1
OWNERLESS FAIL CLOSED
NO SET CLI
NO SYS ADMIN
NO PEOPLE UI
NO CLOSE / REOPEN
V1 NOT RESCORED
```

This file records Stage 1 live migration and ownerless proof only. Subsequent Stage 2 assigned the first Owner. This file does **not** implement Close/Reopen, Sys Admin, or People & Access UI.

Canonical preflight: [fg-038-pa-a-live-migration-owner-preflight.md](../architecture/fg-038-pa-a-live-migration-owner-preflight.md).

---

## Git / Alembic

| Field | Value |
|-------|--------|
| Branch | `main` |
| Pre-migration HEAD = origin/main | `a42ffe59005f8e282d4dbbfcbcbc0b5bbb86db8d` |
| Divergence | `0 0` |
| Working tree before migrate | **CLEAN** |
| Live current before | `b2c3d4e5f6a7` |
| Graph head before | `c3d4e5f6a7b8 (head)` |
| Command | `FLASK_DEBUG=1 ./venv/bin/flask --app app db upgrade c3d4e5f6a7b8` |
| Exit | **0** |
| Applied | `b2c3d4e5f6a7` → **`c3d4e5f6a7b8`** |
| Live current after | **`c3d4e5f6a7b8 (head)`** |
| Graph heads after | **`c3d4e5f6a7b8 (head)`** |
| Downgrade / stamp | **not performed** |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg038-paa-c3d4e5f6a7b8-20260918-091029.db` |
| Source bytes | 3,219,456 |
| Backup bytes | 3,219,456 |
| Source SHA-256 | `5da37af27fc0b20d649290ce64a9022f43eb856fd718cb383e4edf2b69bc5aa4` |
| Backup SHA-256 | `5da37af27fc0b20d649290ce64a9022f43eb856fd718cb383e4edf2b69bc5aa4` |
| Backup Alembic | `b2c3d4e5f6a7` |
| Copy method | Idle filesystem `cp` after stopping office Flask holders on ports 5460/5461. No WAL. Restarted after upgrade. |

## Pre-migration occupancy

| Counter | Before |
|---------|--------|
| Organizations | **3** (`ORG-001`, `ORG-FG014-UAT`, `ORG-002`) |
| Users | **14** |
| Memberships | **13** |
| `COMPANY_MANAGEMENT` grants | **1** (id **1** / membership **1**) |
| Projects | **50** |
| ACTIVE / CLOSED | **50 / 0** |
| Project CRM status | Active **12** · Estimating **25** · Lead **13** |
| Lifecycle events | **0** |
| Owner schema / events table | **ABSENT** |
| Instance Owners | **0** |
| EST-2026-0019 | Estimate **28** Draft / Project **27** Estimating+ACTIVE / Version **34** Draft |
| PRODUCTION packages | **0** |

## Owner schema (after)

`organizations` columns present and nullable: `instance_owner_membership_id`, `instance_owner_set_at`, `instance_owner_set_by_user_id`. FKs **ON DELETE RESTRICT** to `user_memberships.id` and `users.id`. Indexes `ix_organizations_instance_owner_membership_id`, `ix_organizations_instance_owner_set_by_user_id`.

`organization_instance_owner_events` exists. CheckConstraint `event IN ('SET')`. FKs **ON DELETE RESTRICT**. Indexes on organization / previous / new / actor. sqlite tables **133 → 134**. No `COMPANY_MANAGEMENT` / `SYSTEM_ADMIN` / Sensitive Financial coupling on the owner schema.

## Ownerless checkpoint

| Assertion | Result |
|-----------|--------|
| ORG-001 pointer / set_at / set_by | **NULL / NULL / NULL** |
| ORG-FG014-UAT | **NULL / NULL / NULL** |
| ORG-002 | **NULL / NULL / NULL** |
| Effective Instance Owner count | **0** |
| SET event count | **0** |
| `COMPANY_MANAGEMENT` grants | **1** unchanged |
| Access-domain rows created/removed | **none** |
| Projects / ACTIVE / CLOSED / events | **50 / 50 / 0 / 0** |
| Users / memberships | **14 / 13** |
| EST-2026-0019 / Project 27 / Version 34 | unchanged |
| PRODUCTION packages | **0** |
| `flask auth set-instance-owner` | **NOT RUN** |

## Ownerless authority helpers (live)

Ephemeral app-context proof against the live ownerless DB. No SET. Probe routes were not shipped.

| Check | Result |
|-------|--------|
| `get_instance_owner_membership('ORG-001')` | **None** |
| `is_instance_owner(User 1 Joel Brayman, 'ORG-001')` | **False** (B grant does not imply Owner) |
| `is_instance_owner(User 6 AUTH-B UAT User, 'ORG-001')` | **False** |
| `is_system_administrator(...)` | **False** |
| `require_instance_owner` unauthenticated | **302** login |
| `require_instance_owner` User 1 | **403** |
| `require_instance_owner` User 6 | **403** |
| combined helper User 1 / User 6 | **403** |

## Tests

| Command | Result |
|---------|--------|
| Dedicated | `./venv/bin/python -m pytest -q tests/test_instance_owner_authority_fg038.py` **35 passed**, 88 warnings, **16.09s**, exit **0** |
| Focused | `tests/test_instance_owner_authority_fg038.py tests/test_access_domains.py tests/test_core_close_slice_a_fg035.py tests/test_core_close_slice_b_fg035.py` **113 passed**, 306 warnings, **46.06s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1316 passed**, 4597 warnings, **574.01s**, exit **0** |

Live occupancy rechecked after tests: Alembic **`c3d4e5f6a7b8`**, Owners **0**, events **0**, grants **1**, Projects **50 / 50 / 0 / 0**.

## Stage 2 note (not authorized)

Architect has substantively identified the intended future ORG-001 Instance Owner as Joel Brayman (membership **1**, user **1**, intended actor **1**). Those ids are **not** executable from this record. A later prompt must explicitly authorize the SET command.

## Firewalls

No Owner SET. No Sys Admin. No People & Access UI. No Close/Reopen. No Punch List. No Completion Sign-Off. No `COMPANY_MANAGEMENT` mutation. Recovery stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved.

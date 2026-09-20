# FG-038 PA-B Stage 1 live migration — zero-Sys-Admin checkpoint

| Attribute | Value |
|-----------|--------|
| Status | **PASS.** **LIVE-MIGRATED.** **ZERO-SYS-ADMIN CHECKPOINT PASS.** **NO LIVE SYS ADMIN.** [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) remains **OPEN / PARTIAL**. |
| Date | 2026-09-20 |
| Gate | FG-038 PA-B Stage 1 only |
| Product SHA | **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`** |
| Pin SHA | **`3a4735b40ee4580ad3ae419569cafb7bdec32352`** |
| Alembic | **`e5f6a7b8c9d0` → `f6a7b8c9d0e1 (head)`** |
| V1 | **NOT RESCORED** (**65% / 4 of 11**; secondary **79% / 22 of 28**) |

```text
FG-038 PA-B STAGE 1:
LIVE-MIGRATED
ZERO-SYS-ADMIN CHECKPOINT PASS
NO LIVE SYS ADMIN
0 CURRENT SYS ADMIN ROWS
0 APPOINT EVENTS
0 REMOVE EVENTS
INSTANCE OWNER UNCHANGED
MEMBERSHIP 1 / USER 1 / JOEL BRAYMAN
OWNER SET EVENTS 1
COMPANY_MANAGEMENT UNCHANGED / 1
SENSITIVE FINANCIAL 0
NO APPOINT CLI
NO PEOPLE UI
V1 NOT RESCORED
```

This file records Stage 1 live migration and zero-Sys-Admin proof only. It does **not** appoint a System Administrator. It does **not** implement People & Access UI. Instance Owner remains distinct from System Administrator.

---

## Git / Alembic

| Field | Value |
|-------|--------|
| Branch | `main` |
| Pre-migration HEAD = origin/main | `3a4735b40ee4580ad3ae419569cafb7bdec32352` |
| Divergence | `0 0` |
| Working tree before migrate | **CLEAN** |
| Live current before | `e5f6a7b8c9d0` |
| Graph head before | `f6a7b8c9d0e1 (head)` |
| Command | `FLASK_DEBUG=1 ./venv/bin/flask --app app db upgrade f6a7b8c9d0e1` |
| Exit | **0** |
| Applied | `e5f6a7b8c9d0` → **`f6a7b8c9d0e1`** |
| Live current after | **`f6a7b8c9d0e1 (head)`** |
| Graph heads after | **`f6a7b8c9d0e1 (head)`** |
| Downgrade / stamp | **not performed** |
| `flask auth appoint-system-administrator` | **NOT RUN** against live ORG-001 |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg038-pab-f6a7b8c9d0e1-20260920-074506.db` |
| Source bytes (pre-migrate) | 3,399,680 |
| Backup bytes | 3,399,680 |
| Source SHA-256 | `dc8f3b767a215a80c63deab1b75e51df9942d82f09b884c65413178a3ee47659` |
| Backup SHA-256 | `dc8f3b767a215a80c63deab1b75e51df9942d82f09b884c65413178a3ee47659` |
| Backup Alembic | `e5f6a7b8c9d0` |
| Backup Sys Admin tables | **ABSENT** |
| Copy method | Idle filesystem `cp` after stopping office Flask holders on ports 5460/5461/5462. No WAL. Recovery stash **not** altered. |

## Sys Admin schema (after)

`organization_system_administrator_memberships` exists. Columns: `id`, `organization_id`, `membership_id`, `appointed_at`, `appointed_by_user_id`. Unique `(organization_id, membership_id)`. FKs **ON DELETE RESTRICT** to `organizations.id`, `user_memberships.id`, `users.id`.

`organization_system_administrator_events` exists. Append-only. CheckConstraint `event IN ('APPOINT', 'REMOVE')`. Columns: `id`, `organization_id`, `membership_id`, `event`, `actor_user_id`, `actor_identifier`, `created_at`. FKs **ON DELETE RESTRICT**. No seed. No job-title inference. No Domain A/B/C representation.

## Zero-Sys-Admin checkpoint

| Assertion | Result |
|-----------|--------|
| Current Sys Admin rows | **0** |
| APPOINT events | **0** |
| REMOVE events | **0** |
| All Sys Admin events | **0** |
| Owner auto-converted to Sys Admin | **NO** |
| Inferred Sys Admin | **NO** |
| ORG-001 Owner pointer | Membership **1** |
| Owner user | User **1** / Joel Brayman / active |
| Owner SET events | **1** |
| Isolation orgs | ORG-002 / ORG-FG014-UAT **OWNERLESS** |
| `COMPANY_MANAGEMENT` grants | **1** unchanged (membership **1**) |
| Sensitive Financial / C grants | **0** |
| Access-domain mutation | **none** |
| Projects / ACTIVE / CLOSED / events | **50 / 50 / 0 / 0** |
| C2 invitations / items / attempts | **0 / 0 / 0** |
| Punch List items | **0** |
| `flask auth appoint-system-administrator` | **NOT RUN** |

## Live helpers (read-only; no appoint)

Ephemeral `FLASK_DEBUG=1` app-context proof against the live migrated DB. No authority created.

| Check | Result |
|-------|--------|
| `is_system_administrator(User 1 Joel Brayman, 'ORG-001')` | **False** |
| `is_instance_owner(User 1 Joel Brayman, 'ORG-001')` | **True** |
| Owner-or-Sys-Admin for User 1 | **True because Instance Owner, not because Sys Admin** |
| `is_system_administrator(User 6 AUTH-B UAT User, 'ORG-001')` | **False** |
| Owner-or-Sys-Admin for User 6 | **False** |
| unknown identity `999999` | **False** |
| cross-org `ORG-002` / missing org | **False** |

## Tests

| Command | Result |
|---------|--------|
| Dedicated PA-B | `./venv/bin/python -m pytest -q tests/test_system_administrator_authority_fg038.py` **38 passed**, 108 warnings, **29.18s**, exit **0** |
| Authority / CORE CLOSE | PA-B + PA-A + FG-037 + FG-018 + Close/Reopen + Slice A + Slice B **210 passed**, 605 warnings, **159.36s**, exit **0** (PA-A **35**; FG-037 **23**; FG-018 **37**; Close/Reopen **22**; Slice A **18**; Slice B **37**) |
| Help + C1/C2 | D1/D3/D4/D5 + C1 + C2 **95 passed**, 208 warnings, **176.07s**, exit **0** (Help **35**; C1 **26**; C2 **34**) |
| Full suite | `./venv/bin/python -m pytest -q` **1477 passed**, 5062 warnings, **969.59s**, exit **0** |

Live occupancy rechecked after tests: Alembic **`f6a7b8c9d0e1 (head)`**, Sys Admin **0**, APPOINT **0**, REMOVE **0**, Owner Membership **1** / User **1** / Joel Brayman, SET events **1**, grants **1**, C **0**, C2 **0 / 0 / 0**, Punch List **0**, Projects **50 / 50 / 0 / 0**.

## First appointment note (not authorized)

Do **not** infer that Joel Brayman should also be a System Administrator. Instance Owner and System Administrator are distinct. A later prompt must specify organization id, membership id, actor user id, and UAT expectations before any live appoint.

## Firewalls

No live Sys Admin appointment. No People & Access UI. No Sensitive Financial. No extra B/C grants. No Owner mutation. No Close/Reopen. No Help mutation. No Completion Sign-Off. Recovery stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved.

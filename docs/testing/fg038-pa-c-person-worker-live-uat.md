# FG-038 PA-C — bounded live Person UAT

| Attribute | Value |
|-----------|--------|
| Status | **PASS.** **LIVE PERSON UAT PASS.** **1 INACTIVE SYNTHETIC UAT PERSON RETAINED.** [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) remains **OPEN / PARTIAL**. |
| Date | 2026-09-20 |
| Gate | FG-038 PA-C bounded live Person UAT only |
| Product SHA | **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`** |
| Pin SHA | **`bc0ce7f541728262df0573a6096b5948d7abe6ed`** |
| Stage 1 governance SHA | **`433c46f2ae08dfe5513ee2ad86ad72347b8c47e3`** |
| Alembic | **`g7b8c9d0e1f2 (head)`** unchanged |
| V1 | **NOT RESCORED** (**65% / 4 of 11**; secondary **79% / 22 of 28**) |

```text
FG-038 PA-C LIVE PERSON UAT:
LIVE PERSON UAT PASS
PERSON ≠ USER LIVE PASS
WAGE PROTECTION LIVE PASS
CREATE / UPDATE / DEACTIVATE / REACTIVATE / DEACTIVATE PASS
1 INACTIVE SYNTHETIC UAT PERSON RETAINED
PERSON 1 / ORG-001 / FG038 PA-C UAT WORKER
ACTOR USER 1 / JOEL BRAYMAN
NO LOGIN
NO PERSON↔USER LINK
NO PA-D
NO PEOPLE UI
NO SENSITIVE FINANCIAL
OWNER UNCHANGED / MEMBERSHIP 1
CURRENT SYS ADMINS 0
APPOINT 1 / REMOVE 1
COMPANY_MANAGEMENT UNCHANGED / 1
V1 NOT RESCORED
```

This file records the authorized one synthetic live Person UAT. The Person remains **INACTIVE** and must **not** be deleted. It does **not** implement PA-D, People & Access UI, or Sensitive Financial.

Stage 1: [fg038-pa-c-live-migration-empty-person-checkpoint.md](fg038-pa-c-live-migration-empty-person-checkpoint.md).

---

## Git / Alembic (pre-create)

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD = origin/main | `433c46f2ae08dfe5513ee2ad86ad72347b8c47e3` |
| Divergence | `0 0` |
| Working tree | **CLEAN** |
| Live current | `g7b8c9d0e1f2 (head)` |
| Person rows before | **0** |
| Users / Memberships before | **14 / 13** |
| Owner | Membership **1** / User **1** / Joel Brayman |
| Current Sys Admins | **0** |
| APPOINT / REMOVE | **1 / 1** |
| B / C | **1 / 0** |

## Synthetic identity

| Field | Value |
|-------|--------|
| Full name | FG038 PA-C UAT Worker |
| Address | 123 UAT Test Street, Ottawa, ON K1A 0A1 |
| Mobile (created) | 613-555-0198 |
| Mobile (final) | 613-555-0199 |
| Email | fg038-pac-uat-worker@example.invalid |
| Hourly wage | 37.50 |
| Actor | User **1** / Joel Brayman |
| Organization | ORG-001 |

Deliberately synthetic. Not Joel, Ben, Nicole, Darcy, an existing employee, or an existing User email.

## Create

| Field | Value |
|-------|--------|
| Command | `FLASK_DEBUG=1 ./venv/bin/flask --app app auth create-person --organization-id ORG-001 --actor-user-id 1 --full-name "FG038 PA-C UAT Worker" --address "123 UAT Test Street, Ottawa, ON K1A 0A1" --mobile-number "613-555-0198" --email-address "fg038-pac-uat-worker@example.invalid" --hourly-wage "37.50"` |
| Exit | **0** |
| Output | `Person 1 is created for organization ORG-001.` |
| Person id | **1** |
| After create | rows **1** / ACTIVE **1** / INACTIVE **0** |

## Access separation (immediately after create)

| Assertion | Result |
|-----------|--------|
| Person count | **1** |
| Users | **14** unchanged |
| Memberships | **13** unchanged |
| A grants | **0** unchanged |
| B grants | **1** unchanged |
| C grants | **0** |
| Owner | Membership **1** / User **1** / Joel Brayman |
| Current Sys Admins | **0** |
| APPOINT / REMOVE | **1 / 1** |
| User with UAT email | **none** |
| Person `user_id` identity column | **ABSENT** |
| Login / invitation / password | **none created** |

## Identity payload

`get_person(ORG-001, 1, actor=User 1)` returned:

`id=1`, `organization_id=ORG-001`, `full_name=FG038 PA-C UAT Worker`, `address=123 UAT Test Street, Ottawa, ON K1A 0A1`, `mobile_number=613-555-0198`, `email_address=fg038-pac-uat-worker@example.invalid`, `is_active=True`.

`PersonIdentity` fields: `id`, `organization_id`, `full_name`, `address`, `mobile_number`, `email_address`, `is_active`. **No** `hourly_wage`. **No** password. **No** access grants.

## Wage protection

| Check | Result |
|-------|--------|
| Owner CLI `show-person-wage` User 1 | **ALLOW** `hourly_wage: 37.50` exit **0** |
| Ordinary / AUTH-B User 6 CLI | **DENY** exit **1**: Only the Instance Owner or a System Administrator may read hourly wage. User 6 is not Owner, not Sys Admin, and `membership_has_access_domain(..., COMPANY_MANAGEMENT)` is **False** |
| B-only live identity | **Not available without creating a B grant.** The only live `COMPANY_MANAGEMENT` row is Membership **1** (the Owner). No new B grant / User created. Service law: `get_person_hourly_wage()` allows only `is_instance_owner` or `is_system_administrator`. Dedicated `test_wage_b_only_user_denied` **PASS** |
| Cross-org User 5 FG018 Foreign vs ORG-001 Person 1 | **DENY** same wage-read message. User 5 is not Owner of ORG-001 |
| Owner vs `organization_id=ORG-002` Person 1 | **DENY** fail-closed (Owner is not Owner of ORG-002) |

## Lifecycle

| Step | Command | Exit | Result |
|------|---------|------|--------|
| Update mobile 613-555-0198 → 613-555-0199 | `flask auth update-person --organization-id ORG-001 --person-id 1 --actor-user-id 1 --mobile-number "613-555-0199"` | **0** | same id **1**; wage **37.50**; no User/access mutation |
| First deactivate | `flask auth deactivate-person ... --person-id 1 --actor-user-id 1` | **0** | same row; not deleted |
| Reactivate | `flask auth reactivate-person ... --person-id 1 --actor-user-id 1` | **0** | same id **1** |
| Final deactivate | `flask auth deactivate-person ... --person-id 1 --actor-user-id 1` | **0** | INACTIVE retained |

## Final occupancy

| Assertion | Result |
|-----------|--------|
| Person rows | **1** |
| ACTIVE | **0** |
| INACTIVE | **1** |
| Person 1 | FG038 PA-C UAT Worker / ORG-001 / mobile **613-555-0199** / wage **37.50** / `is_active=False` |
| Final identity payload | same fields; `is_active=False`; wage omitted |
| Final Owner wage read | **37.50** |
| Users / Memberships | **14 / 13** |
| Owner | Membership **1** / User **1** / Joel Brayman |
| Current Sys Admins | **0** |
| APPOINT / REMOVE | **1 / 1** |
| B / C | **1 / 0** |
| Alembic | `g7b8c9d0e1f2 (head)` |
| Time / Crew / Field / Schedule | remain User-based; Person **1** not assigned |
| Person↔User link | **ABSENT** |
| Platform access | **NONE** — no User, Membership, login, invitation, or password for the UAT email |
| Sensitive Financial | **NOT IMPLEMENTED**; C grants **0**; no wage UI |

## Tests

Bounded live occupancy test updated from empty-table to accept either **0** Persons or the retained inactive synthetic UAT Person. No product service/model/CLI/schema change.

| Command | Result |
|---------|--------|
| Dedicated PA-C | **37 passed**, 101 warnings, **17.00s**, exit **0** |
| PA-B | **38 passed**, 108 warnings, **25.75s**, exit **0** |
| PA-A | **35 passed**, 88 warnings, **16.57s**, exit **0** |
| Focused identity/authority | PA-C + PA-B + PA-A + Close/Reopen + FG-018 + FG-037 **192 passed**, 563 warnings, **107.20s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1514 passed**, 5163 warnings, **691.64s**, exit **0** (run because occupancy test changed) |

## Explicitly not done

- No second Person
- No PA-D / Person↔User linkage
- No People UI
- No Sensitive Financial / Domain C
- No Owner / Sys Admin mutation
- No Time / Crew / Field / Schedule assignment
- No delete of the synthetic Person
- No rescore
- Recovery stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved

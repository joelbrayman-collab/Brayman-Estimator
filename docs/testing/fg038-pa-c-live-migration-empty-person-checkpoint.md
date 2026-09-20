# FG-038 PA-C Stage 1 live migration — empty-Person checkpoint

| Attribute | Value |
|-----------|--------|
| Status | **PASS.** **LIVE-MIGRATED.** **EMPTY-PERSON CHECKPOINT PASS.** **NO LIVE PERSON DATA.** [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) remains **OPEN / PARTIAL**. |
| Date | 2026-09-20 |
| Gate | FG-038 PA-C Stage 1 only |
| Product SHA | **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`** |
| Pin SHA | **`bc0ce7f541728262df0573a6096b5948d7abe6ed`** |
| Alembic | **`f6a7b8c9d0e1` → `g7b8c9d0e1f2 (head)`** |
| V1 | **NOT RESCORED** (**65% / 4 of 11**; secondary **79% / 22 of 28**) |

```text
FG-038 PA-C STAGE 1:
LIVE-MIGRATED
EMPTY-PERSON CHECKPOINT PASS
NO LIVE PERSON DATA
0 PERSON ROWS
0 ACTIVE PERSONS
0 INACTIVE PERSONS
NO PERSON CLI
INSTANCE OWNER UNCHANGED
MEMBERSHIP 1 / USER 1 / JOEL BRAYMAN
OWNER SET EVENTS 1
CURRENT SYS ADMINS 0
APPOINT 1
REMOVE 1
COMPANY_MANAGEMENT UNCHANGED / 1
SENSITIVE FINANCIAL 0
NO PEOPLE UI
NO PA-D
V1 NOT RESCORED
```

This file records Stage 1 live migration and empty-Person proof only. It does **not** create a Person. It does **not** implement People & Access UI. Person remains distinct from User.

---

## Git / Alembic

| Field | Value |
|-------|--------|
| Branch | `main` |
| Pre-migration HEAD = origin/main | `bc0ce7f541728262df0573a6096b5948d7abe6ed` |
| Divergence | `0 0` |
| Working tree before migrate | **CLEAN** |
| Live current before | `f6a7b8c9d0e1` |
| Graph head before | `g7b8c9d0e1f2 (head)` |
| Live Person table before | **ABSENT** |
| Command | `FLASK_DEBUG=1 ./venv/bin/flask --app app db upgrade g7b8c9d0e1f2` |
| Exit | **0** |
| Applied | `f6a7b8c9d0e1` → **`g7b8c9d0e1f2`** |
| Live current after | **`g7b8c9d0e1f2 (head)`** |
| Graph heads after | **`g7b8c9d0e1f2 (head)`** |
| Downgrade / stamp | **not performed** |
| Person CLI | **NOT RUN** against live ORG-001 |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg038-pac-g7b8c9d0e1f2-20260920-150849.db` |
| Source bytes (pre-migrate) | 3,436,544 |
| Backup bytes | 3,436,544 |
| Source SHA-256 | `51e2a64096de46154ae99d80a431acf4209557a932a9dc779eeb95682758ad4a` |
| Backup SHA-256 | `51e2a64096de46154ae99d80a431acf4209557a932a9dc779eeb95682758ad4a` |
| Backup Alembic | `f6a7b8c9d0e1` |
| Backup Person table | **ABSENT** |
| Copy method | Idle filesystem `cp` after stopping office Flask on port **5020** (PIDs **61387** / **61393**). Recovery stash **not** altered. |

## Person schema (after)

`organization_people` exists. Mandatory columns: `organization_id`, `full_name`, `address`, `mobile_number`, `email_address`, `hourly_wage NUMERIC(10, 2)`, `is_active`, `created_at`, `created_by_user_id`. Optional actor metadata: `updated_at`, `updated_by_user_id`. CheckConstraint `hourly_wage >= 0`. FKs **ON DELETE RESTRICT** to `organizations.id` and `users.id` (actor metadata only). **No** identity `user_id`. **No** membership FK. **No** unique email index.

## Empty-Person checkpoint

| Assertion | Result |
|-----------|--------|
| `organization_people` table | **EXISTS** |
| Person rows | **0** |
| ACTIVE Persons | **0** |
| INACTIVE Persons | **0** |
| Seed / User backfill / Membership backfill | **NO** |
| Joel Person | **NO** |
| Time / Crew / Field conversion | **NO** |
| Person↔User identity FK | **ABSENT** |
| Time worker identity | `LabourTimeEntry.worker_user_id` remains User-based |
| Crew identity | `OrganizationCrewMember.user_id` remains User-based |
| Field actor identity | `field_capture_events.user_id` remains User-based |
| Schedule identity | `work_schedule_assignments.worker_user_id` remains User-based |
| ORG-001 Owner pointer | Membership **1** |
| Owner user | User **1** / Joel Brayman / active |
| Owner SET events | **1** |
| Current Sys Admin rows | **0** |
| APPOINT events | **1** |
| REMOVE events | **1** |
| `COMPANY_MANAGEMENT` grants | **1** unchanged (membership **1**) |
| Sensitive Financial / C grants | **0** |
| Access-domain mutation | **none** |
| Users / Memberships | **14 / 13** unchanged |
| `flask auth create-person` | **NOT RUN** |

## Empty live service check (read-only; no create)

Ephemeral `FLASK_DEBUG=1` app-context proof against the live migrated DB. No Person created.

| Check | Result |
|-------|--------|
| `list_organization_people(organization_id='ORG-001', actor=User 1)` | **0** |
| Person wage to read | **none exists** |

## Tests

First dedicated PA-C run after migrate failed **1** (`test_live_db_has_no_person_table_yet`) because the live table now exists. Bounded correction renamed/replaced that assertion with `test_live_db_person_table_exists_empty` (table exists; **0** rows). That correction does **not** expand PA-C product.

| Command | Result |
|---------|--------|
| Dedicated PA-C after correction | `./venv/bin/python -m pytest -q tests/test_person_identity_fg038.py` **37 passed**, 101 warnings, **16.66s**, exit **0** |
| PA-B | **38 passed**, 108 warnings, **25.58s**, exit **0** |
| PA-A | **35 passed**, 88 warnings, **16.03s**, exit **0** |
| FG-037 | **23 passed**, 75 warnings, **12.44s**, exit **0** |
| FG-018 | **37 passed**, 58 warnings, **18.60s**, exit **0** |
| Time | **8 passed**, 85 warnings, **7.20s**, exit **0** |
| Schedule | **57 passed**, 133 warnings, **28.40s**, exit **0** |
| Field | **53 passed**, 213 warnings, **32.35s**, exit **0** |
| Labour/costing | **59 passed**, 502 warnings, **18.31s**, exit **0** |
| Close/Reopen | **22 passed**, 133 warnings, **16.54s**, exit **0** |
| Help D1/D3/D4/D5 | **35 passed**, 78 warnings, **14.79s**, exit **0** |
| C1/C2 | **60 passed**, 130 warnings, **32.72s**, exit **0** |
| Focused identity/authority | PA-C + PA-B + PA-A + Close/Reopen + FG-018 + FG-037 **192 passed**, 563 warnings, **103.59s**, exit **0** |
| Full suite | `./venv/bin/python -m pytest -q` **1514 passed**, 5163 warnings, **680.24s**, exit **0** |

## Explicitly not done

- No live Person created
- No Person CLI
- No PA-D / Person↔User linkage
- No People UI
- No Sensitive Financial / Domain C
- No Owner / Sys Admin mutation
- No rescore
- Recovery stash **`840dba8320b59ff9464410fec390d755a31a56aa`** preserved

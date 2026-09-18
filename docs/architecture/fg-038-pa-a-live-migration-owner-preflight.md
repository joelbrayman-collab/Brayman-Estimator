# FG-038 PA-A — Live migration + first Instance Owner implementation preflight

| Attribute | Value |
|-----------|--------|
| Status | **PREFLIGHT COMPLETE / LIVE MIGRATION NOT AUTHORIZED / OWNER ASSIGNMENT NOT AUTHORIZED** |
| Date | 2026-09-18 |
| Gate | [FG-038](../feature-gates/FG-038-instance-owner-authority-foundation.md) **OPEN / PARTIAL** |
| Product SHA | **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`** |
| Pin SHA | **`bc084f96a868692b46c39ddaffcbf992ddedca03`** |
| Alembic | Live current **`b2c3d4e5f6a7`**. Graph head **`c3d4e5f6a7b8`**. Mismatch **intentional**. |
| V1 | **NOT RESCORED** (**65% / 4 of 11**; secondary **79% / 22 of 28**) |

```text
FG-038 PA-A LIVE MIGRATION + FIRST OWNER PREFLIGHT:
PREFLIGHT COMPLETE
LIVE MIGRATION NOT AUTHORIZED
OWNER ASSIGNMENT NOT AUTHORIZED
TWO-STAGE: MIGRATE THEN STOP THEN EXPLICIT SET
NO SYS ADMIN
NO PEOPLE UI
NO CLOSE / REOPEN
OWNER IS NOT DOMAIN B
V1 NOT RESCORED
```

This file freezes the **future operational sequence** only. It does **not** authorize `flask db upgrade`. It does **not** authorize `flask auth set-instance-owner` against live data. It does **not** choose the first Instance Owner.

---

## 1. Verified baseline (this preflight)

Inspected 2026-09-18. Read-only. No backup copy created.

| Field | Value |
|-------|--------|
| Path | `/Users/joelbrayman/Desktop/Brayman-Estimator` |
| Branch | `main` |
| HEAD = origin/main | `bc084f96a868692b46c39ddaffcbf992ddedca03` |
| Product SHA | `01e7463082b84b2fcd9d61ff7125a5012b7f8043` |
| Divergence | `0 0` |
| Working tree | **CLEAN** at inspect |
| Live Alembic | `b2c3d4e5f6a7` |
| Graph head | `c3d4e5f6a7b8` |
| Live owner schema | **absent** (`instance_owner_membership_id` not on `organizations`; `organization_instance_owner_events` not present) |
| Live Instance Owners | **0** |
| Recovery stash | `840dba8320b59ff9464410fec390d755a31a56aa` **preserved** |

### Protected occupancy (before counters)

| Counter | Before |
|---------|--------|
| Projects | **50** |
| ACTIVE | **50** |
| CLOSED | **0** |
| `project_operating_state_events` | **0** |
| Organizations | **3** (`ORG-001`, `ORG-FG014-UAT`, `ORG-002`) |
| Users | **14** |
| Memberships | **13** |
| `COMPANY_MANAGEMENT` grants | **1** (grant id **1** / membership **1**) |
| PRODUCTION jurisdiction packages | **0** |
| EST-2026-0019 | Estimate **28** / Project **27** / Version **34** / Draft / Project `operating_state` **ACTIVE** |
| sqlite tables | **133** |
| Live DB bytes (inspect) | **3,219,456** |
| Live DB SHA-256 (inspect) | `5da37af27fc0b20d649290ce64a9022f43eb856fd718cb383e4edf2b69bc5aa4` |

That SHA-256 is **inspect evidence**, not a backup. Recalculate immediately before Stage 1 backup; do not reuse this hash as the backup proof if the file changes.

---

## 2. Two-stage law (frozen)

Do **not** combine migration and Owner SET into one opaque action.

### STAGE 1 — migrate, remain ownerless, STOP

1. Pre-migration backup (gitignored file copy).
2. Pre-migration live evidence (Alembic, occupancy, grant count, owner schema absent).
3. `./venv/bin/flask db upgrade c3d4e5f6a7b8`
4. Verify schema exists.
5. Verify **zero** Instance Owners.
6. Verify **zero** Owner SET events.
7. Verify `COMPANY_MANAGEMENT` grant count **unchanged (1)**.
8. Verify Projects / lifecycle / EST-2026-0019 / PRODUCTION **unchanged**.
9. **STOP / CHECKPOINT.** Return to ChatGPT Architect. Do **not** SET.

If any Stage 1 assertion fails: **STOP before SET.** Restore from backup. Do not continue.

### STAGE 2 — only after separate Architect ACCEPT with explicit ids

1. Explicit SET via CLI using Architect-chosen `--organization-id`, `--membership-id`, `--actor-user-id`.
2. Verify pointer / timestamp / set-by.
3. Verify exactly **one** SET event with correct previous/new/actor fields.
4. Verify effective Owner helpers.
5. Verify `COMPANY_MANAGEMENT` unchanged.
6. Verify ordinary Owner deactivation refused.
7. Bounded live UAT (service/CLI; no People UI; no Close/Reopen).
8. Post-UAT tests.

Stage 2 is **not** authorized by this preflight.

---

## 3. Backup / restore

Follow existing live-migrate governance (`instance/` is gitignored). **Do not** create the backup during this preflight.

| Item | Frozen method |
|------|----------------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup naming | `instance/brayman_estimator-backup-before-fg038-paa-c3d4e5f6a7b8-YYYYMMDD-HHMMSS.db` |
| Copy | `cp` of the live sqlite file while Flask is idle / not writing |
| Proof | backup bytes **equal** source bytes; SHA-256 of source and backup **match**; backup `alembic_version` still **`b2c3d4e5f6a7`** |
| Restore trigger | Stage 1 schema/seed/occupancy mismatch; failed upgrade; accidental SET; any unexpected Project/lifecycle/grant mutation |
| Restore | Stop the office app. Replace live DB with the backup file. Confirm `flask db current` = `b2c3d4e5f6a7` and occupancy counters restored. |
| Downgrade | **Not** the primary restore. Do **not** run `flask db downgrade` / `stamp` unless a later Architect prompt explicitly authorizes it. File restore is the bounded SQLite recovery. |
| Recovery stash | `840dba8320b59ff9464410fec390d755a31a56aa` is **unrelated**. Do **not** pop/apply/drop it. |

---

## 4. Stage 1 post-migration ownerless assertions

After `flask db upgrade c3d4e5f6a7b8`, **before** any SET:

| Assertion | Expected |
|-----------|----------|
| `flask db current` | `c3d4e5f6a7b8` |
| `flask db heads` | `c3d4e5f6a7b8` |
| `organizations.instance_owner_membership_id` | column exists, **NULL** on every org including ORG-001 |
| `instance_owner_set_at` / `instance_owner_set_by_user_id` | columns exist, **NULL** on every org |
| `organization_instance_owner_events` | table exists |
| Instance Owner count | **0** |
| Owner SET event count | **0** |
| `COMPANY_MANAGEMENT` grants | **1** (membership **1**) |
| Projects / ACTIVE / CLOSED / lifecycle events | **50 / 50 / 0 / 0** |
| EST-2026-0019 | Estimate 28 / Project 27 / Version 34 / Draft / ACTIVE |
| PRODUCTION packages | **0** |
| Sys Admin table/column/`SYSTEM_ADMIN` | **absent** |
| Access-domain rows | **unchanged** |

No automatic Owner seed. Isolation orgs remain ownerless. ORG-002 has **zero** memberships and cannot receive a SET until a later governed membership exists.

---

## 5. ORG-001 membership facts (read-only; no choice)

These are live facts for Joel / ChatGPT Architect. This preflight **does not infer** the Owner from first membership, lowest id, User 1, Membership 1, name, email, or `COMPANY_MANAGEMENT`.

| membership id | user id | display name | membership active | user active | stored grants |
|---------------|---------|--------------|-------------------|-------------|---------------|
| 1 | 1 | Joel Brayman | TRUE | TRUE | `COMPANY_MANAGEMENT` |
| 2 | 4 | FG018 Multi | TRUE | TRUE | (none) |
| 5 | 6 | AUTH-B UAT User | TRUE | TRUE | (none) |
| 6 | 7 | AUTH-C UAT User | TRUE | TRUE | (none) |
| 7 | 8 | MAIL-B UAT User | TRUE | TRUE | (none) |
| 8 | 9 | AUTH-D UAT User | TRUE | TRUE | (none) |
| 9 | 10 | TIME UAT Worker | TRUE | TRUE | (none) |
| 10 | 11 | TIME UAT Reviewer | TRUE | TRUE | (none) |
| 11 | 12 | FG035 SCH-B Worker A | TRUE | TRUE | (none) |
| 12 | 13 | FG035 SCH-B Worker B | TRUE | TRUE | (none) |
| 13 | 14 | FG035 SCH-B Inactive Worker | TRUE | **FALSE** | (none) |

SET of membership **13** must be **rejected** (inactive User). Ben genuine ORG-001 membership remains **ABSENT**.

**Product-direction note (not Stage 2 authorization):** [people-and-access-product-direction.md](people-and-access-product-direction.md) §19 records Joel Brayman as intended Instance Owner **YES**. That freeze is access-policy direction. It is **not** a live SET command, not a membership-id fill, and not this preflight’s choice. Stage 2 still requires an explicit Architect/Joel prompt stating `--membership-id` and `--actor-user-id`.

---

## 6. SET actor semantics (PA-A)

`flask auth set-instance-owner` requires `--actor-user-id` because `OrganizationInstanceOwnerEvent.actor_user_id` is **NOT NULL**.

`set_instance_owner(...)` validates the actor as an existing **active User**. It does **not** require:

- current Instance Owner (none exists yet)
- System Administrator (PA-B does not exist; helper returns False)
- `COMPANY_MANAGEMENT`
- matching the target membership’s user

PA-A therefore **intentionally permits the governed operator CLI to SET the first Owner without pre-existing Owner authority**. The CLI is bootstrap infrastructure, not contractor People & Access UI.

Actor evidence to record on the future live SET:

- `--actor-user-id` as stated in the Stage 2 prompt
- resulting `instance_owner_set_by_user_id`
- event `actor_user_id`
- event `actor_identifier` (display_name, else `user-<id>`)

Do **not** invent Sys Admin authority to act. Do **not** treat Domain B as Owner. Do **not** fill actor id in this preflight.

---

## 7. Exact CLI template (ids unfilled)

```text
./venv/bin/flask auth set-instance-owner \
  --organization-id ORG-001 \
  --membership-id <MEMBERSHIP_ID> \
  --actor-user-id <ACTOR_USER_ID>
```

`<MEMBERSHIP_ID>` and `<ACTOR_USER_ID>` remain blank until a later Architect prompt states both explicitly. Do **not** infer them. Do **not** run this command now.

Expected success print shape (from current CLI):

```text
Instance Owner membership <id> is set for organization ORG-001.
```

---

## 8. Stage 2 post-SET assertions

After a valid first SET of membership **M** by actor **A**:

| Assertion | Expected |
|-----------|----------|
| ORG-001 `instance_owner_membership_id` | **M** |
| `instance_owner_set_at` | populated |
| `instance_owner_set_by_user_id` | **A** |
| SET event count | **exactly 1** |
| event `organization_id` | `ORG-001` |
| event `event` | `SET` |
| event `previous_membership_id` | **NULL** (first SET) |
| event `new_membership_id` | **M** |
| event `actor_user_id` | **A** |
| event `actor_identifier` | non-empty |
| event `created_at` | populated |
| `get_instance_owner_membership('ORG-001').id` | **M** |
| `is_instance_owner(target_user, 'ORG-001')` | **True** |
| `is_system_administrator(...)` | **False** |
| same-current SET | **idempotent** (no second event) |
| `COMPANY_MANAGEMENT` grants | still **1** on membership **1**; SET must not create or revoke B |
| isolation orgs | still ownerless |
| Projects / lifecycle / EST-2026-0019 / PRODUCTION | **unchanged** |

A later Owner change (not this first SET) must append a second SET with `previous_membership_id` = prior M. Do **not** implement transfer UI here.

---

## 9. Bounded authority UAT (future; no People UI)

There is **no** contractor Owner HTTP product surface in PA-A. Tests register `/__test__/instance-owner-gate` only. Do **not** create People & Access UI, Sys Admin UI, or Close/Reopen merely to UAT.

Prefer a **gitignored** live runner calling `app/services/instance_authority.py` and the operator CLI.

| Case | Proof |
|------|--------|
| Effective Owner | `is_instance_owner(chosen_user, 'ORG-001')` is True; `get_instance_owner_membership` returns membership M |
| Ordinary non-Owner active ORG-001 member | `is_instance_owner` False; `require_instance_owner` / combined helper **403** if exercised via the same test probe pattern used in `tests/test_instance_owner_authority_fg038.py` (gitignored live probe only; do not ship a product Close route) |
| Unauthenticated | existing login redirect (probe or any `@login_required` office route). No new public Owner UI. |
| Inactive membership pointer | fail closed (helpers return none / False) |
| Inactive user | fail closed; membership **13** already has inactive User and must not become Owner |
| Cross-org | SET of a non-ORG-001 membership must fail; isolation orgs remain ownerless |
| Deactivate current Owner membership/user | `deactivate_membership` / `deactivate_user` raise `InstanceAuthorityError` (raises **before** commit; safe to call as a refused proof) |
| COMPANY_MANAGEMENT | grant row still 1; Owner SET did not grant/revoke B; B holder is Owner **only if** Architect chose that membership explicitly |

Do **not** Close or Reopen a live Project during this UAT.

---

## 10. Protected occupancy (after counters)

Stage 1 and Stage 2 must leave these **identical** to before:

| Counter | Must remain |
|---------|-------------|
| Projects | 50 |
| ACTIVE | 50 |
| CLOSED | 0 |
| lifecycle events | 0 |
| `COMPANY_MANAGEMENT` grants | 1 |
| EST-2026-0019 / Project 27 / Version 34 | Draft / ACTIVE; no commercial mutation |
| PRODUCTION packages | 0 |
| Schedule / Time / SCOPE / actuals | unchanged |

Allowed live mutation:

- Stage 1: Alembic current `b2c3d4e5f6a7` → `c3d4e5f6a7b8`; additive owner columns + empty events table.
- Stage 2: ORG-001 owner pointer + **one** SET event. No other org pointers.

---

## 11. Future test commands

Do **not** represent historical PA-A tests as post-live-UAT evidence.

After Stage 1 and/or Stage 2 (code unchanged; data/schema live):

```text
./venv/bin/python -m pytest -q tests/test_instance_owner_authority_fg038.py
./venv/bin/python -m pytest -q tests/test_instance_owner_authority_fg038.py tests/test_access_domains.py tests/test_core_close_slice_a_fg035.py tests/test_core_close_slice_b_fg035.py
./venv/bin/python -m pytest -q
```

Historical accepted evidence (product close, **not** post-live): dedicated **35 passed** / 15.49s; focused **150 passed** / 60.60s; full **1316 passed**, 4597 warnings, **561.70s**, exit **0**.

---

## 12. Commit / push implications (future)

| Step | Product commit? |
|------|-----------------|
| This preflight | docs-only; **not** a live mutation. Commit only if a later Architect ACCEPT COMMIT covers these docs. |
| Stage 1 live migrate | **No product code commit.** Record a live-migrate evidence file. Docs commit of that record is separately governed. |
| Stage 2 SET | **No product code commit** unless a defect requires a code fix. Record SET/UAT evidence. |
| Defect found | STOP. Return to Architect. Do not expand into PA-B, People UI, or Close/Reopen. |

---

## 13. Firewalls

Do **not**:

- live-migrate from this file
- SET a live Owner from this file
- infer Owner
- create Sys Admin / `SYSTEM_ADMIN`
- modify `COMPANY_MANAGEMENT`
- implement People & Access UI / Person fields
- implement Close / Reopen / Punch List / Sign-Off
- rescore V1
- pop/drop the recovery stash

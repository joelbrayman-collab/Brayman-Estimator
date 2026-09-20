# Feature Gate FG-038: Instance Owner Authority Foundation (PA-A)

**Subsequent status (2026-09-19 PA-B System Administrator authority foundation):** PA-B **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NO LIVE SYS ADMIN / NOT COMMITTED / NOT PUSHED.** Additive **`f6a7b8c9d0e1`** revises **`e5f6a7b8c9d0`**. Graph head **`f6a7b8c9d0e1`**. Live Alembic remains **`e5f6a7b8c9d0`**. Live Sys Admin rows **0**. ORG-001 Instance Owner **UNCHANGED** (Membership **1** / User **1** / Joel Brayman). People & Access UI **NOT IMPLEMENTED**. Sensitive Financial **NOT IMPLEMENTED**. D5 remains **SEALED**. This gate is **not closed**.

**Subsequent status (2026-09-18 Stage 2 first Owner SET):** [testing/fg038-pa-a-first-instance-owner-authority-uat.md](../testing/fg038-pa-a-first-instance-owner-authority-uat.md) **PASS / FIRST OWNER ASSIGNED / LIVE AUTHORITY UAT PASS.** ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. SET events **1**. Isolation orgs ownerless. This gate is **not closed**.

**Subsequent status (2026-09-18 Stage 1 live migration):** [testing/fg038-pa-a-live-migration-ownerless-checkpoint.md](../testing/fg038-pa-a-live-migration-ownerless-checkpoint.md) **PASS / LIVE-MIGRATED.** Subsequent Stage 2 assigned the first Owner. This gate is **not closed**.

**Subsequent status (2026-09-18 live-migration + first-Owner preflight):** [fg-038-pa-a-live-migration-owner-preflight.md](../architecture/fg-038-pa-a-live-migration-owner-preflight.md) **PREFLIGHT COMPLETE.** Subsequent Stage 1 migrated. Subsequent Stage 2 assigned the first Owner. This gate is **not closed**.

| Attribute | Value |
|----------|--------|
| Feature Gate ID | `FG-038` |
| Feature Name | Instance Owner Authority Foundation (People & Access PA-A) |
| Target Milestone | Organization / office identity. Prerequisite for CORE CLOSE Close/Reopen authorization. Not a 12th major V1 package. Does **not** rescore V1. |
| Module | **Organization subsystem** owns `Organization.instance_owner_membership_id` and `OrganizationInstanceOwnerEvent`. Office / platform later consumes `require_instance_owner_or_system_administrator`. No People & Access UI module. |
| Date | 2026-09-18 |
| Status | **OPEN / PARTIAL / PA-A IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / FIRST OWNER ASSIGNED / LIVE AUTHORITY UAT PASS.** Product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Live Alembic **`c3d4e5f6a7b8 (head)`**. ORG-001 Instance Owner = Membership **1** / User **1** / Joel Brayman. Owner SET events **1**. Isolation organizations **OWNERLESS**. System Administrator **DEFERRED TO PA-B**. People & Access UI **NOT IMPLEMENTED**. Close/Reopen **NOT IMPLEMENTED**. CORE CLOSE owner-authority blocker **CLEARED FOR ORG-001**. Official V1 **65% / 4 of 11** (not rescored). Secondary Functional V1 Build **79% / 22 of 28** (not rescored). |
| Architecture | [people-and-access-product-direction.md](../architecture/people-and-access-product-direction.md) owner freeze. [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. **No new ADR.** [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED** (not reopened). [FG-037](FG-037-company-management-access-domain-authorization.md) **CLOSED** (not reopened). [FG-035](FG-035-project-work-structure-time-schedule-performance-learn.md) CORE CLOSE remains **PARTIAL / NOT OPERATIONAL**. |
| Related ADRs | [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. No new ADR. |
| Prerequisites | FG-018 office Users / membership **CLOSED**. People & Access freeze **RECORDED**. Authority-foundation preflight **PASS**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / PARTIAL** — PA-A foundation only |
| Instance Owner pointer | **IMPLEMENTED / LIVE / OPERATIONAL** — ORG-001 `instance_owner_membership_id` = **1** |
| SET events | **IMPLEMENTED / LIVE** — append-only count **1** (`SET`, previous NULL, new **1**, actor **1**) |
| Authority service | **IMPLEMENTED / LIVE / OPERATIONAL** — `app/services/instance_authority.py` |
| CLI | **IMPLEMENTED / RUN LIVE ONCE** — ORG-001 / membership 1 / actor 1 |
| Live Owner assignment | **ASSIGNED** — ORG-001 Membership 1 / User 1 / Joel Brayman. Isolation orgs **OWNERLESS**. |
| System Administrator | **IMPLEMENTED IN WORKING TREE / NOT LIVE** — explicit org-scoped membership rows + APPOINT/REMOVE events; `is_system_administrator` fail-closed; live rows **0** |
| People & Access UI | **NOT IMPLEMENTED** |
| Close/Reopen | **NOT IMPLEMENTED** |
| Schema / Alembic | PA-A additive **`c3d4e5f6a7b8` applied live**. PA-B additive **`f6a7b8c9d0e1` FILE ONLY**. Graph head **`f6a7b8c9d0e1`**. Live current **`e5f6a7b8c9d0`**. |
| V1 scoring | **NOT RESCORED** |

```text
FG-038 PA-A:
INSTANCE OWNER AUTHORITY FOUNDATION
IMPLEMENTED
TESTED
COMMITTED
PUSHED
SHA-PINNED
LIVE-MIGRATED
FIRST OWNER ASSIGNED
LIVE AUTHORITY UAT PASS
PRODUCT SHA 01e7463082b84b2fcd9d61ff7125a5012b7f8043
OWNERLESS FAIL CLOSED
SYS ADMIN DEFERRED TO PA-B
NO PEOPLE & ACCESS UI
NO CLOSE / REOPEN
OWNER IS NOT DOMAIN B
A DOES NOT IMPLY B
B DOES NOT IMPLY C
V1 NOT RESCORED
```

---

## Feature Gate answers

1. **What problem does this solve?** Persist one Contractor Instance Owner per organization as protected administrative root, with SET audit, ownerless fail-closed behaviour, and a governed operator CLI, so later Close/Reopen can require Owner (or later Sys Admin) without inferring authority from Domain B, names, emails, or membership order.

2. **Who is the user?** PA-A has no contractor-facing user. The operator CLI is bootstrap infrastructure. The later contractor user is the Instance Owner.

3. **Which module owns it?** Organization subsystem (`Organization` / `UserMembership`). No new product module.

4. **What data does it own?** `organizations.instance_owner_membership_id`, `instance_owner_set_at`, `instance_owner_set_by_user_id`; append-only `organization_instance_owner_events`.

5. **What data does it reference?** `user_memberships.id`, `users.id`, FG-018 organization/membership request context.

6. **What may it change?** Organization owner pointer + SET events; `app/services/instance_authority.py`; `flask auth set-instance-owner`; ordinary deactivation guards for the current Owner; one additive Alembic file; Alembic graph-head test assertions; minimum governance.

7. **What must it not change?** Live Owner assignment. Sys Admin persistence. People & Access UI. Close/Reopen. Punch List. Completion Sign-Off. A/B/C grant schema. `membership_has_access_domain` / `require_access_domain` / `RECOGNIZED_STORED_DOMAINS`. COMPANY_MANAGEMENT grants. Person/Worker fields. Recovery stash. V1 scores. Live `flask db upgrade`.

8. **What are the acceptance criteria?** Organizations may exist ownerless. Valid same-org active membership may be SET. Cross-org / inactive membership / inactive User rejected. Exactly one SET event per valid SET. Second SET appends history. Owner SET does not create or revoke Domain B. Ownerless helpers fail closed / HTTP 403. `is_system_administrator` is False. CLI requires explicit organization-id + membership-id. Migration file does not seed an Owner. Dedicated tests pass. Live DB remains ownerless and unmigrated.

9. **What tests are required?** Dedicated `tests/test_instance_owner_authority_fg038.py` covering persistence A–O, helpers, CLI, deactivation, A/B/C firewall, no Close/Reopen, Alembic upgrade/downgrade on a temporary database. Dedicated **35 passed**, 88 warnings, **15.49s**, exit **0**. Focused **150 passed**, 364 warnings, **60.60s**, exit **0**. Full suite **1316 passed**, 4597 warnings, **561.70s**, exit **0**.

10. **What documentation must be updated?** This gate; people-and-access subsequent status; FG-037 subsequent (not reopened); current-state; session-handoff; chat-workflow-log; platform-governance; platform-roadmap; architecture.md; architecture/README; docs/README; feature-gates/README; v1-completion-register subsequent; project-state-report; milestones.

11. **Does it require an ADR?** **No.** Architect: no new ADR. ADR-041 remains Accepted.

12. **Does it require a database migration?** **Yes — one additive Alembic file only.** Revision **`c3d4e5f6a7b8`**, down_revision **`b2c3d4e5f6a7`**. **Do not run** `flask db upgrade` / `downgrade` / `stamp` from this gate. No Owner seed. Zero SET events at migration.

---

## Persistence

- `Organization.instance_owner_membership_id` nullable FK `user_memberships.id` **ON DELETE RESTRICT**
- `instance_owner_set_at` nullable DateTime
- `instance_owner_set_by_user_id` nullable FK `users.id` **ON DELETE RESTRICT**
- Index on `instance_owner_membership_id`
- `OrganizationInstanceOwnerEvent`: append-only; event **SET** only; previous/new membership nullable in schema; SET requires a real target membership; actor_user_id / actor_identifier / created_at NOT NULL; FKs **RESTRICT**

Effective Owner requires: pointer exists, membership exists, same organization, membership active, user active. Otherwise **NONE**. Protected actions fail closed. No fallback to COMPANY_MANAGEMENT, first member, lowest ID, email, or name.

---

## Service / CLI

Canonical: `app/services/instance_authority.py`.

| Helper | PA-A behaviour |
|--------|----------------|
| `get_instance_owner_membership` | Effective membership or None |
| `is_instance_owner` | True only for effective Owner user |
| `is_system_administrator` | Always False |
| `require_instance_owner` | 403 unless effective Owner; unauthenticated uses existing login redirect |
| `require_instance_owner_or_system_administrator` | Owner only in PA-A; later PA-B may OR Sys Admin |
| `set_instance_owner` | Validates org/membership/actor; SET pointer + timestamp + actor; one SET event; commit |
| `deactivate_membership` / `deactivate_user` | Ordinary deactivation refuses current/effective Owner |

CLI:

```text
./venv/bin/flask auth set-instance-owner \
  --organization-id <ORG> \
  --membership-id <ID> \
  --actor-user-id <ID>
```

`--actor-user-id` is required because SET events store `actor_user_id` NOT NULL. No HTTP set-owner. This gate does **not** authorize running the CLI against live ORG-001.

---

## Firewalls / explicit exclusions

Do **not** implement:

- live Owner assignment / seed
- System Administrator table, column, or `SYSTEM_ADMIN` domain
- People & Access UI
- Close / Reopen
- Punch List / Completion Sign-Off
- Person / Worker profile fields
- automatic Domain B grant or revoke on Owner SET
- Owner/Sys Admin B/C information-access inheritance (deferred)

**OWNER / SYS ADMIN IS NOT DOMAIN B.**

---

## Related

- [people-and-access-product-direction.md](../architecture/people-and-access-product-direction.md)
- [core-close-project-lifecycle-product-direction.md](../architecture/core-close-project-lifecycle-product-direction.md)
- [FG-037-company-management-access-domain-authorization.md](FG-037-company-management-access-domain-authorization.md)
- [FG-018-organization-authentication-actor-identity-and-membership-v1.md](FG-018-organization-authentication-actor-identity-and-membership-v1.md)
- [adr/ADR-041-user-membership-and-office-authentication.md](../adr/ADR-041-user-membership-and-office-authentication.md)

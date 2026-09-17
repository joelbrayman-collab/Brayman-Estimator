# Feature Gate FG-037: Company / Management Access-Domain Authorization

| Attribute | Value |
|----------|--------|
| Feature Gate ID | `FG-037` |
| Feature Name | Company / Management Access-Domain Authorization |
| Target Milestone | Organization / office identity. Prerequisite for FG-035 PERF-C Company Attention. Not a 12th major V1 package. Does **not** rescore V1. |
| Module | **Organization subsystem** owns `UserMembershipAccessDomainGrant` on `UserMembership`. Office / platform consumes `require_access_domain`. No new product module. |
| Date | 2026-09-17 |
| Status | **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION** (2026-09-17). Product SHA **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`**. Live Alembic **`a0b1c2d3e4f5 (head)`**. First live grant: ORG-001 Membership **1** / User **1** / Joel Brayman / `COMPANY_MANAGEMENT`. Live grant rows **1**. PERF-C **NOT IMPLEMENTED**. Company Attention **NOT IMPLEMENTED**. Sensitive Financial **NOT IMPLEMENTED**. Official V1 **65% / 4 of 11** (not rescored). Secondary Functional V1 Build **79% / 22 of 28** (not rescored). |
| Architecture | [company-management-access-domain-seam.md](../architecture/company-management-access-domain-seam.md) owner freeze. [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; Decision 4 **narrowly amended** (job-title RBAC still rejected). [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED** (not reopened). [FG-035](FG-035-project-work-structure-time-schedule-performance-learn.md) PERF-C remains **DEFINED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Related ADRs | [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. No new ADR. |
| Prerequisites | FG-018 office Users / membership **CLOSED**. Company/Management seam freeze **DEFINED**. |

**Subsequent status (2026-09-17 PERF-C Slice A COMMIT / PUSH / SHA-PIN):** FG-035 PERF-C **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NOT LIVE-UATed**. Product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. Office `/company-attention` consumes `require_access_domain(ACCESS_DOMAIN_COMPANY_MANAGEMENT)`. This gate remains **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION**. Sensitive Financial remains **NOT IMPLEMENTED**. People & Access remains **NOT IMPLEMENTED**. Official V1 **65% / 4 of 11** (not rescored).

**Subsequent status (2026-09-17 PERF-C Slice A working tree):** FG-035 PERF-C **IMPLEMENTED IN WORKING TREE / TESTED / NOT COMMITTED / NOT PUSHED / NOT LIVE-UATed**. Office `/company-attention` consumes `require_access_domain(ACCESS_DOMAIN_COMPANY_MANAGEMENT)`. This gate remains **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION**. Sensitive Financial remains **NOT IMPLEMENTED**. People & Access remains **NOT IMPLEMENTED**. Official V1 **65% / 4 of 11** (not rescored).

**Subsequent status (2026-09-17 People & Access freeze):** [people-and-access-product-direction.md](../architecture/people-and-access-product-direction.md) **RECORDED MANDATORY PRODUCT DIRECTION / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Future Settings → People & Access. This gate is **not reopened**. Operator CLI remains bootstrap infrastructure. Do **not** add People & Access product to this gate.

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION** |
| Owner law A/B/C | **RECORDED** |
| Initial owner access policy | **RECORDED** (Joel A+B now, future C; Ben A+B when genuine membership exists, future C; others A default, B/C explicit later) |
| Model | **IMPLEMENTED** — `UserMembershipAccessDomainGrant` / `user_membership_access_domain_grants` |
| Domain service | **IMPLEMENTED** — `app/services/access_domains.py` |
| Server-side helper | **IMPLEMENTED** — `require_access_domain(...)` (not wired into global `protect_office_routes`) |
| CLI | **IMPLEMENTED** — `flask auth grant-access-domain` / `revoke-access-domain` / `show-access-domains` |
| Schema / Alembic | Additive **`a0b1c2d3e4f5`** revises **`f9b0c1d2e3f4`**. Live current = graph head **`a0b1c2d3e4f5 (head)`**. Applied live 2026-09-17 (`f9b0c1d2e3f4` → `a0b1c2d3e4f5`). |
| Product SHA | **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`** (`feat: implement FG-037 company-management access-domain grants`) |
| Live grant | **YES.** ORG-001 Membership **1** / User **1** / Joel Brayman / `COMPANY_MANAGEMENT` only. Live grant rows **1**. |
| Live migration / UAT | **LIVE-MIGRATED.** First explicit grant **PASS**. Bounded seam UAT **PASS**. |
| V1 scoring | **NOT RESCORED** (official **65% / 4 of 11**; secondary Functional V1 Build remains **79% / 22 of 28**). Eligible as a completed functional capability; Architect decides scorecard separately. |

```text
FG-037:
CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION
LIVE-MIGRATED PASS
FIRST EXPLICIT GRANT PASS
DEFAULT DENY PASS
GRANTED USER ALLOW PASS
UNGRANTED USER DENY PASS
PROJECT/OPERATIONAL NON-REGRESSION PASS
FIELD FIREWALL PASS
SENSITIVE FINANCIAL FIREWALL PASS
PRODUCT SHA 1649b6fab6d362c19088290a6f3cb52f2a0b3d92
LIVE ALEMBIC a0b1c2d3e4f5 (head)
LIVE GRANT ROWS 1
LIVE DOMAIN VALUES COMPANY_MANAGEMENT ONLY
JOEL MEMBERSHIP 1 EFFECTIVE B YES
BEN GENUINE ORG-001 MEMBERSHIP ABSENT / NOT GRANTED
A = ACTIVE USERMEMBERSHIP (NOT STORED)
B = EXPLICIT COMPANY_MANAGEMENT GRANT / DEFAULT DENY
C = SENSITIVE_FINANCIAL FUTURE / NOT IMPLEMENTED
A DOES NOT IMPLY B
B DOES NOT IMPLY C
NO JOB-TITLE RBAC
NO GRANT-ALL
NO AUTOMATIC BOOTSTRAP GRANT
NO COMPANY ATTENTION
NO FIELD CHANGE
NO PERF-C
UNKNOWN DOMAIN FAIL CLOSED
INACTIVE MEMBERSHIP DENIES DESPITE STALE GRANT
V1 NOT RESCORED
```

---

## Purpose

Answer only: **Can this authenticated organization user access Company / Management information?**

Active membership continues to authorize Project / Operational work. Company / Management requires an explicit stored grant. Sensitive Financial remains future.

---

## Owner law

| Domain | Key | How authority is established | Status |
|--------|-----|------------------------------|--------|
| **A. PROJECT / OPERATIONAL** | *(not stored)* | Active `UserMembership` | **Current / unchanged** |
| **B. COMPANY / MANAGEMENT** | `COMPANY_MANAGEMENT` | Explicit membership grant | **OPERATIONAL.** Live grant: Joel Membership 1 only. Default deny for all others. |
| **C. SENSITIVE FINANCIAL** | *(future)* | Later explicit grant | **FUTURE / NOT IMPLEMENTED** |

A does not imply B. B does not imply C.

Joel and Ben both receiving B now (and C later when implemented) is an **owner access policy**, not an architectural coupling between B and C. `COMPANY_MANAGEMENT` must never automatically imply `SENSITIVE_FINANCIAL`.

---

## Initial owner access policy (2026-09-17)

| Person / class | A Project / Operational | B Company / Management | C Sensitive Financial |
|----------------|-------------------------|------------------------|------------------------|
| **Joel Brayman** (ORG-001 Membership 1 / User 1) | **YES** (active membership) | **YES** (explicit live grant this close) | **YES WHEN LATER IMPLEMENTED** (policy only; not granted; not implemented) |
| **Ben Brayman** | **YES when a genuine governed ORG-001 user/membership exists** | **YES when that membership exists and is later explicitly granted** | **YES WHEN LATER IMPLEMENTED** (policy only) |
| **All other users** | **YES** through existing governed membership | **NO** unless later explicitly granted | **NO** unless later explicitly granted |

**Ben membership requirement:** the 2026-09-17 read-only live inventory did **not** identify a genuine Ben Brayman ORG-001 membership. Do **not** repurpose, rename, or infer a synthetic UAT user. Create Ben’s genuine governed ORG-001 user/membership in a later bounded action **before** his `COMPANY_MANAGEMENT` grant and before Ben real-world UAT.

---

## First live grant (2026-09-17)

Command:

```text
./venv/bin/flask auth grant-access-domain --membership-id 1 --domain COMPANY_MANAGEMENT
```

Result: `Access domain COMPANY_MANAGEMENT is present on membership 1.`

| Check | Result |
|-------|--------|
| Membership 1 stored `COMPANY_MANAGEMENT` | **YES** |
| Membership 1 effective `COMPANY_MANAGEMENT` | **YES** |
| Total live grant rows | **1** |
| Live domain values | `COMPANY_MANAGEMENT` only |
| Other memberships | no `COMPANY_MANAGEMENT` grant |
| `SENSITIVE_FINANCIAL` rows | **0** / grant rejected as unknown domain |
| `PROJECT_OPERATIONAL` rows | **0** (not stored) |

---

## Bounded live seam UAT (2026-09-17)

In-process live Flask against `instance/brayman_estimator.db`. No Company Attention product. No occupancy mutation. EST-2026-0019 remained Draft id **28**. Ungranted deny used ORG-001 Membership **5** / User **6** / AUTH-B UAT User (single active membership). Membership **2** / FG018 Multi remains a valid stored-grant deny (`stored_domains: (none)` / `effective_COMPANY_MANAGEMENT: no`) but is **not** used for HTTP Domain A because that user has two active memberships.

| ID | Proof | Result |
|----|-------|--------|
| A | Joel Membership 1 effective `COMPANY_MANAGEMENT` | **PASS** (`flask auth show-access-domains --membership-id 1` → stored YES / effective yes; helper True; HTTP probe **200**) |
| B | Ungranted active ORG-001 membership denied B | **PASS** (Membership 2 CLI effective no; Membership 5 helper False / HTTP probe **403**) |
| C | Joel retains Project / Operational | **PASS** (`/projects/` **200**; org context `ORG-001`) |
| D | Other users retain Project / Operational | **PASS** (AUTH-B `/projects/` **200**; org context `ORG-001`) |
| E | Field unchanged | **PASS** (`GET /field` **302** → `/field/today`; `/field/today` **200**) |
| F | No Field Company Attention | **PASS** (no Company Attention / `company_attention` / `COMPANY_MANAGEMENT` in Field Today; `app/services/company_attention.py` absent) |
| G | `SENSITIVE_FINANCIAL` remains ineffective | **PASS** (Joel helper False; HTTP probe **403**; CLI grant of C rejected `Unknown access domain.`; zero C rows) |
| H | Server-side B helper allow Joel / deny ungranted | **PASS** (`require_access_domain(COMPANY_MANAGEMENT)` Joel **200** / AUTH-B **403**) |

Focused Domain A / Field regression: `./venv/bin/python -m pytest -q tests/test_access_domains.py tests/test_auth_fg018.py tests/test_organization_foundation.py tests/test_project_hub.py tests/test_work_time_fg035.py tests/test_work_schedule_fg035.py tests/test_work_schedule_field_fg035.py tests/test_field_web_fg021.py` → **154 passed**, 435 warnings, **82.70s**, exit **0**.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Every active office member currently has the same organization authority. Company / Management information must default-deny until an explicit grant exists. PERF-C cannot ship without this seam. |
| 2 | Who is the user? | Authenticated office User with exactly one active organization membership. Operator CLI for grant/revoke. Not Field. Not a Settings Members UI. |
| 3 | Which module owns it? | Organization subsystem owns grant rows on `UserMembership`. Application owns recognized domain vocabulary. |
| 4 | What data does it own? | `user_membership_access_domain_grants` (`id`, `user_membership_id`, `domain_key`, `created_at`). |
| 5 | What data does it reference? | `user_memberships.id` (FK, ON DELETE CASCADE). Does **not** duplicate `organization_id`. |
| 6 | What may it change? | Membership grant model; access-domain service; `flask auth` grant/revoke/show; additive Alembic file. |
| 7 | What must it not change? | Field product; Schedule WHO; TIME rules; Project/Hub membership authority; global `protect_office_routes`; PERF-C / Company Attention; Sensitive Financial; live memberships. |
| 8 | What are the acceptance criteria? | Dedicated tests A–U pass. Default deny without B. Grant/revoke idempotent. Unknown domain fail closed. Inactive membership denies despite stale grant. Cross-org fail closed. Field unchanged. No live migrate. No live grant. |
| 9 | What tests are required? | Dedicated `tests/test_access_domains.py`. Focused auth/organization and Project/Schedule/Time/Field regressions. Full suite before claim-done. |
| 10 | What documentation must be updated? | This gate; freeze subsequent status; FG-018 subsequent; indexes; current-state; session-handoff; chat-workflow-log. No V1 rescore. |
| 11 | Does it require an ADR? | **No.** ADR-041 Decision 4 already narrowly amended. No new ADR. |
| 12 | Does it require a database migration? | **Yes.** One additive revision **`a0b1c2d3e4f5`**. File created. **Do not apply live in Slice A.** |

---

## Access-domain model

`UserMembership.access_domain_grants` → `UserMembershipAccessDomainGrant`.

Unique `(user_membership_id, domain_key)`.

No role enum. No permission booleans. No financial columns.

The only **effective stored** domain in this slice is `COMPANY_MANAGEMENT`. `PROJECT_OPERATIONAL` is **not stored**. `SENSITIVE_FINANCIAL` is **not recognized** and is **not effective**.

Unknown domains fail closed.

---

## Server-side enforcement

`membership_has_access_domain(...)` is default-deny.

`require_access_domain(...)`:

- unauthenticated → existing login behaviour
- invalid / missing / multiple active membership → existing fail-closed behaviour
- active membership without `COMPANY_MANAGEMENT` → **403**
- active membership with `COMPANY_MANAGEMENT` → authorized

Navigation is UX only. Direct URL must not bypass the helper.

`protect_office_routes` is **not** modified to require domain B. Project / Hub / Schedule / Time / Field remain membership authority A.

No Company Attention route is created merely to consume the helper. Tests register a test-only probe.

---

## CLI

Canonical target: `--membership-id`.

| Command | Behaviour |
|---------|-----------|
| `flask auth grant-access-domain` | Recognized domain only; active user; active membership; idempotent |
| `flask auth revoke-access-domain` | Recognized domain; missing grant is a no-op; inactive membership allowed |
| `flask auth show-access-domains` | Stored recognized domains + `effective_COMPANY_MANAGEMENT` yes/no |

No `--grant-all`. No name heuristics. No creation-order inference. No automatic bootstrap grant. First live grant is Membership 1 only (this close).

---

## Migration

Revision **`a0b1c2d3e4f5`** / down_revision **`f9b0c1d2e3f4`**.

Upgrade creates `user_membership_access_domain_grants`. Downgrade drops it. No membership mutation. No seed.

**Live upgrade applied 2026-09-17:** `f9b0c1d2e3f4` → `a0b1c2d3e4f5`. Live current **`a0b1c2d3e4f5 (head)`**. Subsequent first live grant (same date): grant row count **1** (`COMPANY_MANAGEMENT` on Membership 1 only). Do **not** downgrade or stamp from this record.

---

## Firewalls / explicit exclusions

Do **not** implement:

- PERF-C / `company_attention.py` / Company Attention route, template, or nav
- Field Company Attention
- Settings → Members
- Sensitive Financial / bank / cash / payroll permissions
- job-title RBAC
- grant-all / identity allowlists
- additional live grants beyond Joel Membership 1
- Ben account creation / synthetic-user rename
- first live `SENSITIVE_FINANCIAL` grant

**NO COMPANY ATTENTION IN THE FIELD APP.**

---

## Slice A implementation / test state

| Item | State |
|------|--------|
| Model + relationship | **IMPLEMENTED** |
| Domain service | **IMPLEMENTED** |
| Server-side helper | **IMPLEMENTED** |
| CLI | **IMPLEMENTED** |
| Additive migration file | **CREATED / APPLIED LIVE** (`f9b0c1d2e3f4` → `a0b1c2d3e4f5`) |
| Dedicated tests | `tests/test_access_domains.py` included in focused **154 passed**, 435 warnings, **82.70s**, exit **0** (this close). HISTORICAL Slice A dedicated **23 passed**. |
| Product SHA | **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`** |
| Live migration | **APPLIED** 2026-09-17. Live current **`a0b1c2d3e4f5 (head)`**. |
| Live grant | **PASS** — Membership 1 `COMPANY_MANAGEMENT` only. Grant rows **1**. |
| Bounded seam UAT | **PASS** (A–H) |
| Gate close | **CLOSED / OPERATIONAL FOR COMPANY_MANAGEMENT AUTHORIZATION** |

---

## Related

- [company-management-access-domain-seam.md](../architecture/company-management-access-domain-seam.md)
- [FG-018-organization-authentication-actor-identity-and-membership-v1.md](FG-018-organization-authentication-actor-identity-and-membership-v1.md)
- [FG-035-project-work-structure-time-schedule-performance-learn.md](FG-035-project-work-structure-time-schedule-performance-learn.md)
- [adr/ADR-041-user-membership-and-office-authentication.md](../adr/ADR-041-user-membership-and-office-authentication.md)

# Feature Gate FG-037: Company / Management Access-Domain Authorization

| Attribute | Value |
|----------|--------|
| Feature Gate ID | `FG-037` |
| Feature Name | Company / Management Access-Domain Authorization |
| Target Milestone | Organization / office identity. Prerequisite for FG-035 PERF-C Company Attention. Not a 12th major V1 package. Does **not** rescore V1. |
| Module | **Organization subsystem** owns `UserMembershipAccessDomainGrant` on `UserMembership`. Office / platform consumes `require_access_domain`. No new product module. |
| Date | 2026-09-17 |
| Status | **OPEN / SLICE A IMPLEMENTED / TESTED / NOT LIVE-MIGRATED / NO LIVE GRANT.** PERF-C **NOT IMPLEMENTED**. Company Attention **NOT IMPLEMENTED**. Sensitive Financial **NOT IMPLEMENTED**. |
| Architecture | [company-management-access-domain-seam.md](../architecture/company-management-access-domain-seam.md) owner freeze. [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; Decision 4 **narrowly amended** (job-title RBAC still rejected). [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED** (not reopened). [FG-035](FG-035-project-work-structure-time-schedule-performance-learn.md) PERF-C remains **DEFINED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Related ADRs | [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. No new ADR. |
| Prerequisites | FG-018 office Users / membership **CLOSED**. Company/Management seam freeze **DEFINED**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / SLICE A IMPLEMENTED / TESTED** |
| Owner law A/B/C | **RECORDED** |
| Model | **IMPLEMENTED** — `UserMembershipAccessDomainGrant` / `user_membership_access_domain_grants` |
| Domain service | **IMPLEMENTED** — `app/services/access_domains.py` |
| Server-side helper | **IMPLEMENTED** — `require_access_domain(...)` (not wired into global `protect_office_routes`) |
| CLI | **IMPLEMENTED** — `flask auth grant-access-domain` / `revoke-access-domain` / `show-access-domains` |
| Schema / Alembic | Additive file **`a0b1c2d3e4f5`** revises **`f9b0c1d2e3f4`**. **NOT APPLIED LIVE** |
| Live grant | **NONE.** First `COMPANY_MANAGEMENT` recipient remains **UNRESOLVED** |
| Live migration / UAT | **SEPARATELY AUTHORIZED** |
| V1 scoring | **NOT RESCORED** (official **65% / 4 of 11**; secondary Functional V1 Build remains **79% / 22 of 28**) |

```text
FG-037:
OPEN / SLICE A IMPLEMENTED / TESTED
NOT LIVE-MIGRATED
NO LIVE GRANT
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
| **B. COMPANY / MANAGEMENT** | `COMPANY_MANAGEMENT` | Explicit membership grant | **Slice A implemented / not live-migrated** |
| **C. SENSITIVE FINANCIAL** | *(future)* | Later explicit grant | **FUTURE / NOT IMPLEMENTED** |

A does not imply B. B does not imply C.

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

No `--grant-all`. No name heuristics. No creation-order inference. No automatic bootstrap grant. No live grant in this slice.

---

## Migration

Revision **`a0b1c2d3e4f5`** / down_revision **`f9b0c1d2e3f4`**.

Upgrade creates `user_membership_access_domain_grants`. Downgrade drops it. No membership mutation. No seed.

**Live `flask db upgrade` / `downgrade` / `stamp` is not authorized by this slice.**

---

## Firewalls / explicit exclusions

Do **not** implement:

- PERF-C / `company_attention.py` / Company Attention route, template, or nav
- Field Company Attention
- Settings → Members
- Sensitive Financial / bank / cash / payroll permissions
- job-title RBAC
- grant-all / identity allowlists
- first live `COMPANY_MANAGEMENT` recipient

**NO COMPANY ATTENTION IN THE FIELD APP.**

---

## Slice A implementation / test state

| Item | State |
|------|--------|
| Model + relationship | **IMPLEMENTED** |
| Domain service | **IMPLEMENTED** |
| Server-side helper | **IMPLEMENTED** |
| CLI | **IMPLEMENTED** |
| Additive migration file | **CREATED / NOT APPLIED LIVE** |
| Dedicated tests | `tests/test_access_domains.py` — **23 passed**, 75 warnings, **18.72s**, exit **0** |
| Live migration | **NOT RUN** |
| Live grant | **NONE** |
| Live UAT | **NOT AUTHORIZED** |

---

## Related

- [company-management-access-domain-seam.md](../architecture/company-management-access-domain-seam.md)
- [FG-018-organization-authentication-actor-identity-and-membership-v1.md](FG-018-organization-authentication-actor-identity-and-membership-v1.md)
- [FG-035-project-work-structure-time-schedule-performance-learn.md](FG-035-project-work-structure-time-schedule-performance-learn.md)
- [adr/ADR-041-user-membership-and-office-authentication.md](../adr/ADR-041-user-membership-and-office-authentication.md)

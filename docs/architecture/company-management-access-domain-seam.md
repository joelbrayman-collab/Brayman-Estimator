# Company / Management access-domain seam — owner-decision freeze

| Attribute | Value |
|-----------|--------|
| Status | **DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED** |
| Date | 2026-09-17 |
| Owner | Organization subsystem (`User` / `UserMembership`). Office / platform consumes the later grant helper. No new product module. |
| ADR | [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. Decision 4 is **narrowly amended** (2026-09-17): job-title RBAC remains rejected; named information/access domains associated with membership are permitted. Decision 4 is **not rewritten**. No new ADR. |
| Parent auth | [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. This freeze does **not** reopen FG-018. |
| First consumer | FG-035 PERF-C Company Attention ([fg-035-perf-c-product-definition.md](fg-035-perf-c-product-definition.md)) **DEFINED / NOT IMPLEMENTATION-AUTHORIZED**. PERF-C must **not** ship until this seam is separately implemented and proven. |
| Schema | **NONE in this freeze.** Expected later implementation direction: membership access-domain grant rows. Additive migration requires a later **explicitly approved** implementation prompt. Do **not** create a migration from this file. |
| Baseline | HEAD / `origin/main` **`c9c4f2f83e30a35e6cff1d38a91ee9b61aae41bf`**. Alembic **`f9b0c1d2e3f4 (head)`**. |
| V1 | **NOT RESCORED** (**60% / 4 of 11**). This freeze is **not** a scoring event. |

```text
COMPANY / MANAGEMENT ACCESS-DOMAIN SEAM:
DEFINED
NOT IMPLEMENTATION-AUTHORIZED
NOT IMPLEMENTED
NO SCHEMA
NO MIGRATION
NO NEW ADR
NO NEW FEATURE GATE
NO SETTINGS MEMBERS UI
NO JOB-TITLE RBAC
NO SENSITIVE FINANCIAL
NO LIVE GRANTS
NO PERF-C PRODUCT
V1 NOT RESCORED
PERF-A SEALED
PERF-B SEALED
PERF-C REMAINS DEFINED / NOT IMPLEMENTATION-AUTHORIZED
```

This file is the frozen **owner-decision** contract for the minimum Company / Management authorization seam. It is **not** an implementation prompt. Do **not** implement access domains, grants, CLI, Company Attention, Settings Members, Sensitive Financial, Field changes, PERF-C product, or a generic RBAC platform from this file.

---

## 1. Current vs Intended vs Future

| Layer | State |
|-------|--------|
| **Current** | Active `User` + exactly one active `UserMembership` authorizes the organization. No role column. No capability column. No people-admin UI. Settings is Brand Profile only. Office vs Field is a **client surface**. Any active office member can currently open every Project in that organization. |
| **Intended (this freeze)** | Owner decisions in §§2–16 **ACCEPTED**. Authorization distinguishes **information / access domains**, not job titles. Domain A remains implied by active membership. Domain B requires an explicit `COMPANY_MANAGEMENT` grant. Domain C remains future. Seam **not implementation-authorized.** |
| **Future (not this freeze)** | Bounded implementation slice (separate prompt, including migration approval if schema is chosen). Governed operator CLI grant/revoke. Later Settings → Members / Permissions. `SENSITIVE_FINANCIAL`. PERF-C Company Attention as first consumer **after** the seam is proven. |

---

## 2. Frozen owner decisions

| ID | Decision | Freeze |
|----|----------|--------|
| 1 | Access model | **ACCEPTED.** Information / access domains, not job-title roles. Do **not** create admin / manager / supervisor / employee / estimator / field worker / reviewer roles. |
| 2 | Domain A | **ACCEPTED.** Active `UserMembership` continues to provide **PROJECT / OPERATIONAL** organization access. Do **not** store a duplicate `PROJECT_OPERATIONAL` grant merely for symmetry. Existing Project, Schedule, Time, Field, and other currently governed membership-based access remains unchanged unless separately governed later. |
| 3 | Domain B | **ACCEPTED.** **COMPANY / MANAGEMENT** requires an **explicit** access-domain grant on the user’s organization membership. Stored key: `COMPANY_MANAGEMENT`. Missing grant = **DENY**. A membership by itself does **not** imply B. |
| 4 | Domain C | **ACCEPTED as FUTURE PRODUCT DIRECTION ONLY.** **SENSITIVE FINANCIAL** is separately governed. A does not imply B. B does not imply C. Do **not** implement `SENSITIVE_FINANCIAL`. Do **not** create live grants, placeholders, bank/cash/payroll permissions, or symmetry rows. The grant model must remain capable of supporting C later. |
| 5 | Data shape | **ACCEPTED as architectural direction.** Membership access-domain **grant rows**, not boolean soup on `UserMembership`, not job-title roles, not email allowlists, not hard-coded identities. Do **not** implement the model now. |
| 6 | Recognized keys | **ACCEPTED.** The application owns the access-domain vocabulary. Arbitrary ungoverned strings must **not** become effective merely because a row exists. First implementation slice: the only new **effective stored** domain is `COMPANY_MANAGEMENT`. Unknown / unrecognized domains **fail closed**. |
| 7 | Existing members | **ACCEPTED.** `COMPANY_MANAGEMENT` is **DEFAULT DENY**. Existing active memberships keep Project / Operational access. Existing users do **not** automatically receive B. Do **not** grant all existing members. Do **not** infer grants from display name, email, creation order, job title, or test fixture names. Initial live grant recipient(s) must be **explicitly identified** in a later governed migration/UAT step. |
| 8 | Grant / revoke V1 | **ACCEPTED.** Minimum initial mechanism may be a **governed operator CLI** against an explicitly identified organization membership/user. No name heuristics. No silent bootstrap assumption. Do **not** build Settings → Members merely to unblock PERF-C. Later contractor-facing Members / Permissions remains separately governed future product work. |
| 9 | Contractor control | **ACCEPTED.** The contractor / company owner controls who may access company and sensitive business information. The V1 CLI is an implementation mechanism. It does **not** transfer product authority away from the contractor. Future UX must preserve that law. |
| 10 | Server-side enforcement | **ACCEPTED.** `COMPANY_MANAGEMENT` **must** be enforced server-side. Navigation visibility is UX only. Hiding a nav item is **not** authorization. Direct URL must not bypass the grant. |
| 11 | Field / identity / surface | **ACCEPTED.** Permissions follow the authenticated user and the contractor’s explicit authorization — **not** the device. Application surfaces remain intentionally bounded. `COMPANY_MANAGEMENT` does **not** cause Company Attention to appear in the Field App. Authorized office/management access from a mobile browser remains office access, not Field. Do **not** alter Field from this file. |
| 12 | First consumer | **ACCEPTED.** Company Attention / PERF-C will be the **first** product consumer of `COMPANY_MANAGEMENT`. Do **not** retroactively gate Project Hub, Projects list, Schedule, Time, or Field with domain B. Those remain under existing Project / Operational membership authority. |
| 13 | Sequencing | **ACCEPTED.** This seam is a **separate governed implementation slice** and must be implemented and proven **before** PERF-C Company Attention product implementation. Do **not** hide permission code inside the PERF-C assembler or route work. |
| 14 | ADR-041 | **ACCEPTED.** Narrow amendment / clarification of Decision 4 only. Job-title RBAC remains rejected. Named access domains associated with membership are permitted. Do **not** rewrite ADR-041 history. |
| 15 | Scope of first implementation (when later authorized) | **ACCEPTED.** Answers only: **Can this authenticated organization user access Company / Management information?** Does **not** implement Sensitive Financial, bank/payroll/cash, per-Project ACL, Division, Operating Unit, job hierarchy, generic enterprise RBAC, custom permission builder, Settings Members UI, or PERF-C itself. |
| 16 | Firewalls | **ACCEPTED.** Do **not** from this file implement grants, CLI, schema, Field Company Attention, Home Office, PERF-C product, Sensitive Financial, or reopen PERF-A / PERF-B. |

---

## 3. Conceptual domains (keep separate)

| Domain | Key | How authority is established | Status |
|--------|-----|------------------------------|--------|
| **A. PROJECT / OPERATIONAL** | *(not stored)* | Active `UserMembership` | **Current** (unchanged) |
| **B. COMPANY / MANAGEMENT** | `COMPANY_MANAGEMENT` | Explicit membership grant | **DEFINED / NOT IMPLEMENTED** |
| **C. SENSITIVE FINANCIAL** | *(future)* | Later explicit grant | **FUTURE / NOT THIS SLICE** |

These are **information-access domains**, not job titles.

```text
A DOES NOT IMPLY B.
B DOES NOT IMPLY C.
```

---

## 4. Recognized-domain rule

The application owns the recognized vocabulary.

For the first implementation slice:

- Effective stored domain: **`COMPANY_MANAGEMENT` only**
- `PROJECT_OPERATIONAL` is **not** stored
- `SENSITIVE_FINANCIAL` is **not** an active domain and is **not** created as a placeholder row

Unknown / unrecognized domain keys or requests: **DENY / FAIL CLOSED**.

Do **not** permit a stringly-typed permission free-for-all.

---

## 5. Default deny / existing members

```text
COMPANY_MANAGEMENT IS DEFAULT DENY.
```

Existing active `UserMembership` rows retain current Project / Operational access. Field behaviour is unchanged.

Do **not**:

- grant all existing members
- infer grants from name, email, creation order, job title, or fixture names
- assume the bootstrap / first ORG-001 user automatically receives B

Somebody must later receive the first live grant. That recipient must be **explicitly identified** during a later governed migration/UAT step. This freeze does **not** enumerate live users or emails.

---

## 6. Expected later data shape (direction only)

```text
UserMembership (active)                 → PROJECT / OPERATIONAL (A)
    |
    +-- access-domain grant row(s)
            COMPANY_MANAGEMENT          → COMPANY / MANAGEMENT (B)
            SENSITIVE_FINANCIAL         → later (C) — not this slice
```

Do **not** implement tables, models, or migrations from this file.

Exact table/column names are implementation reconnaissance. Ownership: Organization subsystem.

---

## 7. Server-side enforcement (direction only)

Expected later behaviour:

| State | Behaviour |
|-------|-----------|
| Unauthenticated | Existing login behaviour |
| Invalid / no active membership | Existing fail-closed behaviour |
| Active membership **without** `COMPANY_MANAGEMENT` | **403** — authenticated, not authorized |
| Active membership **with** `COMPANY_MANAGEMENT` | May access governed Company / Management surfaces |
| Direct URL | Must not bypass the grant |
| Nav hidden | UX only — **not** authorization |

Do **not** implement now.

---

## 8. Field / identity / surface

```text
PERMISSIONS FOLLOW THE AUTHENTICATED USER AND THE CONTRACTOR'S
EXPLICIT AUTHORIZATION — NOT THE DEVICE.

APPLICATION SURFACES REMAIN INTENTIONALLY BOUNDED.

NO COMPANY ATTENTION IN THE FIELD APP.
```

A user granted domain B may later open office/management Company Attention from a mobile browser. That remains office/management access. It does **not** add Company Attention to Field.

---

## 9. Contractor control and V1 CLI

```text
THE CONTRACTOR / COMPANY OWNER CONTROLS WHO MAY ACCESS COMPANY AND
SENSITIVE BUSINESS INFORMATION.
```

V1 grant/revoke may be a governed operator CLI. The CLI must operate against an **explicitly identified** organization membership/user. No name heuristics. No silent bootstrap assumption.

Settings today is Brand Profile only. There is **no** people-admin surface. Do **not** invent Settings → Members in this slice. A later contractor-facing grant/revoke UX remains separately governed and must preserve contractor control.

---

## 10. Sequencing vs PERF-C

```text
PERMISSION SEAM  →  separately implemented and proven
THEN
PERF-C / COMPANY ATTENTION  →  first product consumer of COMPANY_MANAGEMENT
```

PERF-C remains:

```text
DEFINED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED
```

Do **not** hide permission implementation inside the PERF-C assembler or route work.

Do **not** retroactively gate Hub / Projects list / Schedule / Time / Field with `COMPANY_MANAGEMENT`.

---

## 11. ADR-041 relationship

[ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) Decision 4 historically rejected V1 RBAC (administrator / estimator / field / reviewer) and treated tenant authorization as active membership.

**2026-09-17 narrow amendment:** that rejection of **job-title RBAC** stands. This freeze permits **explicitly governed information/access domains** on membership.

FG-018 remains **CLOSED**. This freeze does **not** reopen it. Implementation of the seam requires a later governed prompt (and Feature Gate answers before code).

---

## 12. Explicit exclusions

| Item | Freeze |
|------|--------|
| Job-title RBAC | **Forbidden** |
| Boolean `company_management_access` on `UserMembership` | **Rejected** as the governing model |
| Email / identity allowlists | **Rejected** |
| `SENSITIVE_FINANCIAL` live grants / placeholder rows | **Forbidden now** |
| Bank / payroll / cash permissions | **Not this work** |
| Per-Project ACL / Division / Operating Unit | **Not this work** |
| Generic enterprise policy engine | **Not this work** |
| Settings Members / invitation product | **Not this work** |
| PERF-C / Company Attention product | **Not this freeze** |
| Home Office | **Not this freeze** |
| Field changes | **Forbidden** |
| PERF-A / PERF-B | **SEALED** |
| Live user grants / live DB mutation | **Forbidden from this file** |
| V1 rescore | **Forbidden** |

---

## 13. What this freeze does not authorize

Do **not** from this file:

- implement access domains, models, helpers, decorators, CLI, or tests
- create or run a migration
- mutate the database or grant any live user
- enumerate live user emails
- implement Settings Members
- implement Sensitive Financial or financial permissions
- alter Project / Schedule / Time / Field access
- implement PERF-C or Company Attention
- reopen PERF-A or PERF-B
- rescore V1
- write an implementation prompt as if this file authorized code

A later **implementation** prompt is separately governed. This file is not that prompt.

---

## 14. Stop

```text
OWNER DECISIONS 1–16 ACCEPTED.
ACCESS DOMAINS, NOT JOB TITLES.
A = ACTIVE MEMBERSHIP.
B = EXPLICIT COMPANY_MANAGEMENT GRANT / DEFAULT DENY.
C = FUTURE / NOT IMPLEMENTED.
SEAM DEFINED / NOT IMPLEMENTATION-AUTHORIZED.
DO NOT IMPLEMENT PERMISSIONS FROM THIS FILE.
DO NOT IMPLEMENT PERF-C FROM THIS FILE.
RETURN TO CHATGPT ARCHITECT.
```

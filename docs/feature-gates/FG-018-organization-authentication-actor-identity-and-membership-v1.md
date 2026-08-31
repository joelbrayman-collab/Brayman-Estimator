# Feature Gate FG-018: Organization Authentication, Actor Identity, and Membership V1

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-018` |
| Feature Name | Organization Authentication, Actor Identity, and Membership V1 |
| Target Milestone | **None.** FG-018 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Organization subsystem** owns `User` and `UserMembership` ([ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md); [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Proposed**). **Office / platform** owns login, logout, session, CSRF, and SECRET_KEY/config fail-closed behaviour. Existing modules consume authenticated actor identity on **new** writes within bounded implementation scope. |
| Date | 2026-08-30 |
| Status | **DRAFT FOR JOEL REVIEW / NOT APPROVED.** Implementation **NOT STARTED**. Not authorized. |
| Architecture | [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Proposed** · [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** (shared API **deferred**) · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [platform-roadmap.md](../platform-roadmap.md) item 10 |
| Related ADRs | [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Proposed** (do **not** treat as Accepted) · [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | FG-017 **CLOSED / OPERATIONAL FOR UAT**. Item-10 reconnaissance reviewed by Joel/ChatGPT. **ADR-041 must be Accepted** and this gate **Approved** before any implementation prompt. |
| Approved baseline | N/A — this gate is **not approved**. Live Alembic current/head remains **`a9b0c1d2e3f4`**. Full suite governed baseline **423 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **DRAFT / NOT APPROVED** |
| ADR-041 | **Proposed / FOR JOEL REVIEW** |
| Implementation | **NOT STARTED** |
| Schema / Alembic | **Unchanged.** Live current = head `a9b0c1d2e3f4`. One head. **No migration in this pass.** |
| Shared API | **OUT OF THIS GATE** |
| BUILD / Field Web | **BLOCKED** until Item 10 authentication is implemented under a later authorized prompt |

A commit of this draft does **not** constitute Feature Gate approval or ADR acceptance.

This gate is the first bounded product slice of roadmap **item 10**. It covers **office authentication, durable User, and Organization membership**. It does **not** cover shared API (deferred to a later separately governed gate before BUILD/Field requires it, per [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) and [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md)).

---

## Purpose

Give the office application a durable authenticated User and Organization membership so actor attribution is no longer an anonymous free-text default, and so BUILD field capture is not later built on an unauthenticated office app.

```text
USER (email + hashed password + display name + active)
→ USER MEMBERSHIP (active link to Organization)
→ AUTHENTICATED OFFICE SESSION
→ MEMBERSHIP-DERIVED ORGANIZATION CONTEXT
→ NEW GOVERNED WRITES SNAPSHOT ACTOR IDENTITY
```

Office success (only after later **acceptance, approval, implementation reconnaissance, and a separate implementation prompt**): a seeded ORG-001 office user can log in; unauthenticated office access fails closed after activation; Organization context comes from membership; historical actor strings are unchanged.

Success is **OFFICE AUTHENTICATION + ACTOR IDENTITY + MEMBERSHIP V1**, not a shared API, not BUILD, and not RBAC.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | The office app is unauthenticated; actor fields are provenance strings; org context silently defaults to `ORG-001`. Field capture ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md)) cannot start on that foundation. |
| 2 | Who is the user? | Office operator on the **future authenticated** office app (seeded ORG-001 member). Not field. Not the customer. Not self-service SaaS. **Today** the app remains unauthenticated until this gate is implemented. |
| 3 | Which module owns it? | **Organization subsystem** owns User + UserMembership. **Office / platform** owns session/login/CSRF/SECRET_KEY. Existing modules consume actor identity on new writes; they do not become identity owners. |
| 4 | What data does it own? | User; UserMembership; session of the logged-in User. Not Organization commercial records. Not BUILD actuals. Not API tokens. |
| 5 | What data does it reference? | `organizations` (tenant). Existing actor-string columns as **historical snapshots**. Optional nullable `user_id` on bounded **new** writes only. |
| 6 | What may implementation change? | Only after a separate implementation prompt: User/membership models; login/logout; CSRF; SECRET_KEY fail-closed; bootstrap without Git credentials; office `login_required` after bootstrap; bounded new-write actor snapshot; **one** additive migration; tests; docs. |
| 7 | What must it not change? | BUILD; Field Web; shared API; historical actor strings; Proposal immutability; Brand Profile freeze rules; Permit analysis; Labour/Pricing commercial rules; take-off approval rules; Material Catalogue identity; Change Order records; RBAC; ADR-008/010 status. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. Not claimed complete by this draft. |
| 9 | Tests required? | See **Dedicated tests** and **Regression**. None written in this pass. |
| 10 | Documentation? | This gate; ADR-041; indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones. |
| 11 | ADR required? | **Yes — ADR-041, now Proposed.** Implementation must not start until ADR-041 is **Accepted**. If implementation exposes an uncovered conflict: **STOP**. |
| 12 | Migration? | **YES — one bounded additive revision** in the **implementation** prompt only. Identifier deferred. Do **not** create it now. Do **not** run `flask db upgrade` now. |

---

## Owner

| Concern | Owner |
|---------|--------|
| User record (email, display name, password hash, active) | **Organization subsystem** ([ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md)) |
| UserMembership | **Organization subsystem** |
| Login / logout / Flask-Login session | **Office / platform** |
| CSRF on login and mutating browser POSTs | **Office / platform** |
| SECRET_KEY / non-development fail-closed | **Office / platform** |
| Bootstrap of first ORG-001 user (non-Git secrets) | **Office / platform** (operator-supplied values) |
| Historical actor-string columns | **Owning modules unchanged** — snapshots; no rewrite |
| Optional nullable `user_id` on bounded new writes | Owning module of that table; FG-018 may add only where the implementation prompt justifies |
| Shared API / field tokens | **Out of this gate** ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md)) |
| BUILD field capture | **Out of this gate** ([ADR-020](../adr/ADR-020-build-module-boundary.md)) |

Do **not** create a new product module named Auth/IAM.

---

## Exact proposed scope

If later Approved, implementation may include **only**:

1. Durable **User** (one concept; not a separate Actor entity).
2. Durable **UserMembership** (User ↔ Organization; schema may allow multiple memberships).
3. **Email/password** authentication.
4. Secure **password hashing**. Never store plaintext.
5. **Login / logout**.
6. **Active/inactive** User (inactive fail closed).
7. **Membership-derived Organization context** for authenticated requests (not silent `DEFAULT_ORGANIZATION_ID`).
8. **Initial ORG-001 User bootstrap** without committed credentials.
9. **Login protection of all operating office routes** after safe bootstrap and activation. No permanent anonymous operating mode.
10. **CSRF protection** for login and mutating browser POSTs.
11. **Non-development SECRET_KEY/config** requirement; production-like startup must not silently use the committed development secret.
12. **Authenticated actor provenance** on new governed writes within the bounded implementation scope (display-name snapshot).
13. **Optional nullable `user_id`** only where justified by the implementation prompt — **not** a repository-wide conversion.
14. **Tests.**
15. **Documentation.**
16. **Minimum additive schema** required by [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md).

V1 operating seed: **one** active membership in **ORG-001** only. **No** organization-switcher UX. If a User has zero active memberships: fail closed. If a User has more than one active membership: **do not invent** selection UX or silent `ORG-001` fallback; that is a later governed decision.

---

## Non-goals

**DO NOT** include in this gate (draft or later implementation):

- BUILD Field Capture
- Field Web
- shared API
- `/api/v1/me`
- public API
- API tokens
- field authentication
- MONITOR
- LEARN
- Phase D
- supplier integration
- Change Order document family
- Permit branding
- national Permit expansion
- QuickBooks
- Ontario Contract / Warranty
- external AI
- runtime web lookup
- SaaS billing
- self-registration
- invitations
- SSO / external IdP
- broad RBAC
- administrator / estimator / field / reviewer roles
- organization switching UX
- historical actor-string migration
- repository-wide `user_id` FK conversion
- password-reset email
- mail infrastructure
- production-security certification
- accepting ADR-008 or ADR-010

---

## Acceptance criteria

Apply only after ADR-041 is **Accepted**, this gate is **Approved**, implementation reconnaissance is complete, and a **separate implementation prompt** is issued. Not claimed complete by this draft.

1. Unauthenticated office access **fails closed after activation**.
2. Seeded **active ORG-001 member can log in**.
3. **Correct password required**.
4. **Inactive user cannot authenticate**.
5. **Logout terminates** the authenticated session.
6. **Membership controls Organization context**.
7. **No silent authenticated fallback to ORG-001**.
8. **Cross-org access without membership fails closed**.
9. Existing **organization-isolation protections remain intact**.
10. Existing **office workflows remain operational** for the authenticated ORG-001 user.
11. Login and mutating browser POSTs have **CSRF protection**.
12. Production-like configuration does **not silently use** the committed development `SECRET_KEY`.
13. Password stored **only as a secure hash**.
14. **No credential committed to Git**.
15. New bounded governed actions use **authenticated actor identity** (display-name snapshot; optional `user_id` only where in scope).
16. **Historical actor strings remain unchanged**.
17. **No BUILD / shared API / RBAC** product surface appears.
18. Full regression suite passes with **no unexplained loss**.

---

## Dedicated tests (proposed; not written)

When implementation is authorized, dedicated tests must cover at least:

- login success / wrong password / missing CSRF
- logout
- inactive user
- unauthenticated access to operating office routes after activation
- membership-derived org context
- no silent authenticated ORG-001 fallback
- cross-org fail-closed without membership
- password stored hashed
- SECRET_KEY production-like fail-closed (committed development secret rejected)
- bootstrap does not require credentials in the repository
- new bounded writes snapshot authenticated display name
- historical actor-string fixtures unchanged

Exact filenames are implementation reconnaissance.

## Regression suite (proposed)

Existing organization-isolation suites (foundation, labour, pricing, take-off, permit, brand, hub, historical upload, catalogue, estimate-output) must continue to pass, with an **authenticated test fixture** after activation. Full suite `./venv/bin/python -m pytest -q` at or above the then-current governed baseline. Do not claim the current **423** count after implementation without running it.

---

## Proposed schema concepts (not created)

| Concept | Justification |
|---------|----------------|
| `users` | Durable authenticated actor ([ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md)) |
| `user_memberships` | Phase A / ADR-041 User ↔ Organization |
| Credential columns **on User** (password hash) | Email/password V1; no separate credential table required |

Exact table/column names are **implementation reconnaissance**. Do **not** create roles, permissions, API token, or session tables in FG-018 unless a later prompt proves Flask cookie session insufficient.

**Migration:** one additive revision after `a9b0c1d2e3f4` when implementation is authorized. Identifier deferred. No historical actor backfill. Downgrade drops new tables; commercial records remain.

---

## Security requirements (this gate)

| Item | Class |
|------|--------|
| Hashed passwords | Required |
| Login / logout / inactive fail-closed | Required |
| CSRF on login and mutating POSTs | Required |
| Membership tenant context | Required |
| Login-gated operating office routes after activation | Required |
| Non-development SECRET_KEY fail-closed | Required |
| No credentials in Git | Required |
| Login throttling / enumeration hardening | Deferred; must remain recorded |
| Password-reset email | Deferred (CLI reset in V1) |
| API tokens | Not applicable (API out of gate) |
| SSO | Not applicable to V1 |
| Production-security certification | Not this gate |

---

## Bootstrap / credential design boundary

- Support creating the first **active ORG-001 office User and membership**.
- **Do not** commit email, password, hash, or secrets.
- Values come from a **governed non-repository mechanism** at deployment/UAT time.
- Exact CLI/command/env shape is **implementation reconnaissance**.

---

## Implementation reconnaissance (later; not this pass)

Flag for a **separate post-approval** implementation reconnaissance. Do **not** implement now:

- table/column names
- password-hash implementation
- CSRF library/config
- login route/template placement
- bootstrap CLI or command mechanism
- exact environment/config mechanism for SECRET_KEY
- exact office-route protection strategy
- which bounded new-write paths gain optional `user_id` in FG-018
- test fixture / login migration strategy
- migration revision identifier

---

## Documentation consistency note

Roadmap item 10 remains **not implemented**. Shared API remains **deferred**. BUILD remains **blocked** behind Item 10 authentication. This draft does **not** approve implementation.

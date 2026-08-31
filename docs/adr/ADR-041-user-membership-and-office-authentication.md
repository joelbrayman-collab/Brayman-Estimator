# ADR-041 — User, Organization Membership, and Office Authentication

| Field | Value |
|-------|--------|
| Title | ADR-041: Durable User, Organization Membership, Office Authentication, Session, and Historical Actor Provenance |
| Status | **Accepted** (2026-08-30; governing [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **IMPLEMENTED / LIVE MIGRATION PENDING**). Live `flask db upgrade` of `b0c1d2e3f4a5` is **not** authorized by the implementation commit. |
| Date | 2026-08-30 |
| Related | [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **IMPLEMENTED / LIVE MIGRATION PENDING** · [ADR-022](ADR-022-field-client-and-shared-api.md) **Accepted** (field/API direction; no API in this ADR) · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [platform-roadmap.md](../platform-roadmap.md) item 10 · [ADR-020](ADR-020-build-module-boundary.md) **Accepted** · [modules/build.md](../modules/build.md) · Constitution Articles 1, 4, 5, 6 |

---

## Problem

The office application is unauthenticated. Anyone who can reach the Flask process can use every operating HTML route. Actor attribution is free-text `String(150)` (and similar) with defaults such as `"Joel Brayman"` / `"Estimator"` / `HISTORICAL_UPLOAD_ACTOR`. Those strings are **provenance snapshots**, not identities.

Organization isolation exists (`organization_id` query scoping; default `ORG-001` via `get_current_organization_id()`). There is **no User**, **no membership**, **no login**, and **no session org**. `Flask-Login` is declared in `requirements.txt` and unused.

Roadmap item 10 (Authentication / actor identity + shared API foundation) is the first unfinished numbered CalibAi sequence item. Items 11–12 (BUILD Field Capture; Field Web) **require** authentication before field capture ([ADR-022](ADR-022-field-client-and-shared-api.md)). Building field capture on anonymous office access would make audit attribution fictional.

## Context

Joel/ChatGPT reviewed the Item-10 architecture reconnaissance (2026-08-30) and locked the decisions in this ADR’s Decision section.

[ADR-022](ADR-022-field-client-and-shared-api.md) remains the field/API sequence: **Flask services → shared API when field is authorized → field web → native later.** This ADR does **not** implement a shared API.

[ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) remains the tenant/legal-commercial root. Phase A architecture already names `UserMembership` as organization-owned. M011 implemented `Organization` **without** users. This ADR supplies the missing identity layer. It does **not** implement the Phase A phrase “with RBAC roles.”

This ADR does **not** create a migration. Product implementation still requires a **separate** implementation prompt after the FG-018 reconnaissance recorded in the Feature Gate.

---

## Decision

**Accepted.** Do **not** treat acceptance as product implementation. Shared API remains deferred.

### 1. Durable User is the authenticated actor

- V1 uses **one** durable **User** concept.
- Do **not** create a separate Actor entity.
- User is the durable authenticated actor for office actions after FG-018 is implemented, migrated, bootstrapped, and activated.
- User is **not** the tenant. `Organization` remains the only tenant / legal-commercial root ([ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md)).
- Do **not** invent employee/HR records.

### 2. Login identifier

- V1 login identifier is **email address**.
- Email is **login identifier** and **contact identifier**.
- Email is **not** immutable legal identity.
- **Display name** is the human-readable actor identity snapshotted onto new governed actions where applicable.

### 3. UserMembership

- Durable **UserMembership** binds User ↔ Organization.
- Schema **must permit** a User to have memberships in more than one Organization (Phase A 1:N).
- FG-018 V1 does **not** implement organization-switching UX, SaaS tenant administration, self-registration, or invitations.
- The initial operating user receives **active membership in ORG-001 only**.
- Authenticated request Organization context **must** derive from an **active membership**, not silently from `DEFAULT_ORGANIZATION_ID`.
- V1 operating assumption: the seeded office user has **exactly one** active membership (ORG-001). If a User has **zero** active memberships, authentication/authorization **fails closed**. If a User has **more than one** active membership, FG-018 **must not invent** a switcher or silent default; that selection behaviour is a **later governed decision**. Do not silently fall back to `ORG-001`.

### 4. Authorization (no RBAC in V1)

Keep these concepts separate:

| Concept | V1 rule |
|---------|---------|
| **Authentication** | Active logged-in User |
| **Tenant authorization** | Active Organization membership |
| **Audit provenance** | Logged-in User identity + preserved human-readable snapshot where applicable |

Do **not** create RBAC, administrator / estimator / field-user / reviewer roles, or a permissions matrix. The initial ORG-001 user is **not** an “administrator” schema role. Office vs field is a **client surface** (HTML office now; field web later), not two role tables.

### 5. Authentication technology and session

- V1: **email + password**.
- Use the existing declared **Flask-Login** dependency if implementation is later authorized.
- Passwords **must be securely hashed**. Never store plaintext passwords.
- Office session: **Flask session / Flask-Login** — login, logout, inactive-user fail closed, authenticated session.
- Future field-client cookie-versus-token architecture is **deferred** to the shared API gate.
- Inactive User **cannot authenticate** and cannot act. Historical rows keep stored snapshots / optional FKs.

### 6. Initial-user bootstrap

- FG-018 must support creation of the **first active ORG-001 office User and membership**.
- Do **not** hardcode or invent Joel’s login email, password, password hash, or any credential secret.
- **No real credential may be committed to Git.**
- Bootstrap values must be supplied at deployment/UAT time through a **governed non-repository mechanism** (exact CLI/command/env shape is implementation reconnaissance).

### 7. Password recovery

- V1: **CLI / governed operator reset only**.
- No password-reset email flow. No mail infrastructure.
- Password-reset email is a **future capability**, not a V1 requirement.

### 8. CSRF

- CSRF protection is **required** for login and mutating browser POST routes.
- Exact library/config is implementation reconnaissance. Do not invent exemptions casually.

### 9. SECRET_KEY

- Production / non-development operation **must not** rely on the committed `"development-secret-key"` in `create_app`.
- `SECRET_KEY` must come from **environment/config or another governed non-repository secret mechanism**.
- Do **not** invent an external secrets platform.
- Tests/development may use explicit test/development configuration.
- Production-like startup **must fail safely** rather than silently using the committed development secret.
- Exact env/config names are implementation reconnaissance.

### 10. Historical actor provenance

- Existing human-readable actor/provenance strings remain **historical snapshots**.
- **Do not rewrite** `created_by`, `reviewed_by`, `approved_by`, `frozen_by`, `generated_by`, `requested_by`, `pricing_override_by`, audit `actor`, or other existing provenance strings.
- **Do not backfill** historical actor strings into new User FKs.
- After FG-018 activation, **new governed writes** use authenticated User identity.
- Where a durable FK is justified, use an **optional nullable `user_id`** while **preserving** the human-readable actor snapshot.
- Do **not** launch a repository-wide FK conversion campaign in FG-018.

### 11. Shared API and field deferred

- Shared API is **out of FG-018**.
- Do **not** include `/api/v1/me`, public API, field API, BUILD endpoints, API tokens, or token revocation.
- [ADR-022](ADR-022-field-client-and-shared-api.md) remains: services → shared API **when field is authorized** → field client.
- A **later separately governed gate** addresses shared API before BUILD/Field requires it.
- Existing Flask **service layer remains authoritative**. Login must not duplicate business rules.

### 12. Office routes after activation

- Once FG-018 is implemented, migrated, bootstrapped, **and activated**: **all operating office routes must require authentication**.
- Do **not** preserve a permanent anonymous operating mode.
- Transition must be sequenced so a **bootstrap User exists before** anonymous office access is removed.

### 13. Security limitations

This ADR does **not** certify production security. Login throttling, credential-enumeration hardening, and password-reset email remain recorded deferred items. SSO / external IdP is not V1.

---

## Alternatives Considered

- **Separate Actor entity besides User** — Rejected for V1: one durable authenticated actor is enough; a second identity table would split provenance.
- **Defer User until SaaS / multi-tenant productization** — Rejected: ADR-022 requires auth before field; anonymous office cannot be the field foundation.
- **Magic link / email-only login** — Rejected: no mail infrastructure in this repository.
- **External identity provider / SSO in V1** — Rejected: not required by architecture; separately gated later if Joel authorizes.
- **Shared API / `/api/v1/me` inside FG-018** — Rejected: ADR-022 places JSON API when field is authorized; field is items 11–12.
- **RBAC (admin / estimator / field / reviewer)** — Rejected for V1: Phase A conceptual RBAC is not Feature-Gated; FG-008 forbade pretending RBAC exists; Item-10 reconnaissance found no V1 requirement.
- **Permanent unauthenticated office mode after activation** — Rejected: would defeat Item 10.
- **Rewrite historical actor strings onto User FKs** — Rejected: invents identity; violates historical snapshot preservation (Constitution Article 5).
- **Hardcode ORG-001 bootstrap credentials in Git** — Rejected: credential leakage; forbidden by this ADR.

---

## Consequences

**Positive:** Durable who-are-you and which-organization before BUILD; historical strings preserved; Organization remains the tenant; Flask-Login already declared; field/API stay on ADR-022 sequence.

**Negative:** Office UAT workflows must gain a login fixture; `SECRET_KEY` / CSRF become blocking for activation; bootstrap is an operator step; multi-membership selection is unresolved beyond fail-closed.

## Explicit non-goals

BUILD Field Capture; Field Web; shared API; MONITOR; LEARN; Phase D; supplier integration; Change Order document family; Permit branding; national Permit expansion; QuickBooks; Ontario Contract / Warranty; external AI; runtime web lookup; SaaS billing; self-registration; invitations; SSO; broad RBAC; organization-switching UX; historical actor-string migration; repository-wide `user_id` FK conversion; password-reset email; mail infrastructure; production-security certification; accepting ADR-008 or ADR-010.

## Module Ownership Impact

- **Organization subsystem** owns `User` and `UserMembership` (identity and tenant membership). No new product module.
- **Office / platform** owns login, logout, session, CSRF, and SECRET_KEY/config fail-closed behaviour when FG-018 is implemented.
- Existing owning modules keep their records. They **consume** authenticated actor identity on **new** writes within the later implementation’s bounded scope. They do **not** become identity owners.

## Data Ownership Impact

- User and membership rows are organization-scoped via membership, not a second tenant root.
- Historical actor strings remain owned by their current tables as snapshots.
- Optional nullable `user_id` on selected new writes is **reference**, not a campaign to re-own those tables.

## Migration Impact

**Deferred.** One bounded **additive** Alembic revision is expected under a later **implementation** prompt after this ADR is Accepted and FG-018 is Approved. Exact revision identifier is implementation reconnaissance. Do **not** create a migration in this pass. Do **not** run `flask db upgrade` for this ADR.

## Testing Impact

When implementation is authorized: dedicated login/membership/CSRF/SECRET_KEY fail-closed tests plus regression of existing organization-isolation suites with an authenticated fixture. See [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md). [testing-standards.md](../testing-standards.md) already requires Flask-Login tests when authz exists.

## Documentation Impact

This ADR; FG-018; adr/feature-gate indexes; current-state; session-handoff; project-state-report; platform-roadmap; chat-workflow-log; milestones.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Accepted via governed prompt | 2026-08-30 |
| ChatGPT review | Item-10 architecture + FG-018 draft reviewed; acceptance authorized | 2026-08-30 |
| Cursor implementation note | Docs/governance only this pass. Implementation reconnaissance recorded on FG-018. No product code. | 2026-08-30 |

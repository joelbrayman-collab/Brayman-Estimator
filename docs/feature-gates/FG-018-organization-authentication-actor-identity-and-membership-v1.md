# Feature Gate FG-018: Organization Authentication, Actor Identity, and Membership V1

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-018` |
| Feature Name | Organization Authentication, Actor Identity, and Membership V1 |
| Target Milestone | **None.** FG-018 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Organization subsystem** owns `User` and `UserMembership` ([ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md); [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**). **Office / platform** owns login, logout, session, CSRF, and SECRET_KEY/config fail-closed behaviour. Existing modules consume authenticated actor identity on **new** writes within bounded implementation scope. |
| Date | 2026-08-30 |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Live `flask db current` = repository head **`b0c1d2e3f4a5`**. Office UAT **PASSED** on port **5011**. Shared API **out of this gate**. This is **not** production-security certification. |
| Architecture | [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** · [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** (shared API **deferred**) · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [platform-roadmap.md](../platform-roadmap.md) item 10 |
| Related ADRs | [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** · [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | FG-017 **CLOSED / OPERATIONAL FOR UAT**. Item-10 architecture reconnaissance reviewed. **ADR-041 Accepted.** Gate **Approved**, **implemented**, live-migrated, bootstrapped, and office-UAT closed. |
| Approved baseline | Live Alembic current = head **`b0c1d2e3f4a5`**. Full suite **460 passed**. Dedicated FG-018 **37 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **CLOSED / OPERATIONAL FOR UAT** |
| ADR-041 | **Accepted** |
| Implementation | **IMPLEMENTED** and **live-migrated**. First ORG-001 user bootstrapped via CLI. Office UAT **PASSED** on port **5011**. |
| Schema / Alembic | Revision **`b0c1d2e3f4a5`** applied live (`a9b0c1d2e3f4` → `b0c1d2e3f4a5`). Live current = head **`b0c1d2e3f4a5`**. One graph head. |
| Shared API | **OUT OF THIS GATE** |
| BUILD / Field Web | **BLOCKED.** ADR-022 still requires a separately governed Shared API step before field implementation. Do not create that gate from a documentation pass. |

This gate is **CLOSED / OPERATIONAL FOR UAT**. It is **not** production-security certification, SaaS readiness, or BUILD readiness beyond the authenticated office prerequisite.

### Implementation evidence (2026-08-31)

| Item | Result |
|------|--------|
| Product implementation | Login/logout, Flask-Login, CSRFProtect, membership-derived org context, CLI bootstrap/reset, bounded actor snapshots, shell Estimate/Proposal org isolation |
| Migration | `b0c1d2e3f4a5` additive; `users` + `user_memberships`; schema-only; no credentials |
| Password hashing | `pbkdf2:sha256` (Werkzeug scrypt unavailable on this Python 3.9) |
| Dedicated tests | `tests/test_auth_fg018.py` **37 passed** |
| Focused regression | Listed FG-018 suites + dedicated file **460 passed** |
| Full suite | `./venv/bin/python -m pytest -q` **460 passed** (pre-FG-018 baseline 423) |
| Live Alembic current | **`b0c1d2e3f4a5`** (applied 2026-08-31) |
| Repository Alembic head | **`b0c1d2e3f4a5`** |
| Remaining live action | **None for this gate.** Shared API remains a later gate. |

### Live migration / bootstrap / office UAT evidence (2026-08-31)

| Item | Result |
|------|--------|
| Live upgrade | `a9b0c1d2e3f4` → `b0c1d2e3f4a5` (`add users and user memberships fg018`) |
| Graph heads | One (`b0c1d2e3f4a5`) |
| Local-only `SECRET_KEY` | Gitignored `.env`; not `development-secret-key`; value not recorded in docs |
| Bootstrap | `flask auth bootstrap-org-001-user --display-name "Joel Brayman"`; email stored after governed `strip().lower()`; password via `AUTH_BOOTSTRAP_PASSWORD`; hash `pbkdf2:sha256`; plaintext absent; one active ORG-001 membership; duplicate bootstrap failed closed |
| Office UAT port | **5011** (CSRF enabled; debug off) |
| Login / logout | Unauthenticated `/` → `/login`; correct credentials → dashboard; wrong password generic failure; `GET /logout` 405; `POST /logout` clears session |
| Fail-closed membership | Inactive login generic failure; zero-membership dashboard 403; multi-membership dashboard 403; disposable UAT users only |
| Org context | Authenticated ORG-001 shell/lists scoped to ORG-001; no org-switcher; `ORG-FG014-UAT` project 4 / `EST-FG017-UAT-ISO` / `PROP-FG017-UAT-ISO` absent from ORG-001 shell; foreign-only member sees isolation estimate and cannot open ORG-001 project 3 |
| Route / file protection | Representative families 200 when authenticated; `/settings/` authenticated 302 to Brand Profile (existing alias); unauthenticated downloads 302 to login; authenticated downloads 200; static CSS public |
| CSRF | Login POST without token 400; form POST without token 400; valid tokens succeed; JSON calibration without `X-CSRFToken` 400; with header CSRF accepted |
| SECRET_KEY | Production-like missing/dev-secret fail-closed; TESTING fallback allowed; `FLASK_DEBUG=1` may use development secret |
| Actor provenance | New labeled writes snapshot `Joel Brayman` (labour `UAT-FG018-001`, pricing `UAT-FG018-ACTOR`, project commercial/permit, permit analysis, apply-org-pricing snapshot, historical review decision, take-off run). Brand Profile CURRENT was not rewritten; existing `created_by` remains `Joel Brayman`. |
| Historical integrity | `labour_tasks.UAT-FG008-001` and `historical_upload_attempts.id=1` actor strings unchanged. No `user_id` columns added. |
| Dedicated / focused / full | `tests/test_auth_fg018.py` **37 passed**; focused FG-018 list **460 passed**; `./venv/bin/python -m pytest -q` **460 passed** |

A commit of the earlier implementation did **not** constitute live migration. This close records the authorized live-migrate / bootstrap / UAT pass.

Success is **OFFICE AUTHENTICATION + ACTOR IDENTITY + MEMBERSHIP V1** operational for UAT, not a shared API, not BUILD, and not RBAC.

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

Office success (after live migration + CLI bootstrap + UAT close): a seeded ORG-001 office user can log in; unauthenticated office access fails closed; Organization context comes from membership; historical actor strings are unchanged. **This pass is CLOSED / OPERATIONAL FOR UAT.**

Success is **OFFICE AUTHENTICATION + ACTOR IDENTITY + MEMBERSHIP V1**, not a shared API, not BUILD, and not RBAC.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | The office app is unauthenticated; actor fields are provenance strings; org context silently defaults to `ORG-001`. Field capture ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md)) cannot start on that foundation. |
| 2 | Who is the user? | Office operator on the authenticated office app (seeded ORG-001 member). Not field. Not the customer. Not self-service SaaS. Live UAT still requires migration + bootstrap. |
| 3 | Which module owns it? | **Organization subsystem** owns User + UserMembership. **Office / platform** owns session/login/CSRF/SECRET_KEY. Existing modules consume actor identity on new writes; they do not become identity owners. |
| 4 | What data does it own? | User; UserMembership; session of the logged-in User. Not Organization commercial records. Not BUILD actuals. Not API tokens. |
| 5 | What data does it reference? | `organizations` (tenant). Existing actor-string columns as **historical snapshots**. Optional nullable `user_id` on bounded **new** writes only. |
| 6 | What may implementation change? | Only after a separate implementation prompt: User/membership models; login/logout; CSRF; SECRET_KEY fail-closed; bootstrap without Git credentials; office `login_required` after bootstrap; bounded new-write actor snapshot; **one** additive migration; tests; docs. |
| 7 | What must it not change? | BUILD; Field Web; shared API; historical actor strings; Proposal immutability; Brand Profile freeze rules; Permit analysis; Labour/Pricing commercial rules; take-off approval rules; Material Catalogue identity; Change Order records; RBAC; ADR-008/010 status. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. Not claimed complete by this draft. |
| 9 | Tests required? | See **Dedicated tests** and **Regression**. None written in this pass. |
| 10 | Documentation? | This gate; ADR-041; indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones. |
| 11 | ADR required? | **Yes — ADR-041 Accepted.** If implementation exposes an uncovered conflict: **STOP**. |
| 12 | Migration? | **YES — one bounded additive revision** in the **implementation** prompt only. Identifier deferred. Do **not** create it now. Do **not** run `flask db upgrade` now. |

---

## Owner

| Concern | Owner |
|---------|--------|
| User record (email, display name, password hash, active) | **Organization subsystem** ([ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**) |
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

Apply only after a **separate implementation prompt** is issued. Not claimed complete by this approval.

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
- Exact CLI/command/env shape is recorded in **Implementation reconnaissance** below. **Not implemented.**

---

## Implementation reconnaissance (2026-08-30)

**Status:** Recorded 2026-08-30. **Implemented 2026-08-31** per this gate. Recon below remains the historical design record.

Verified live: Flask 3.1.3; Flask-Login 0.6.3 **declared unused**; Flask-WTF **not installed**; Werkzeug 3.1.8; Python 3.9 `hashlib.scrypt` **missing** (default `generate_password_hash()` raises). `python-dotenv` declared unused. `.env` gitignored. No Flask CLI auth commands. No `conftest.py`. No `/api/` blueprint. `SECRET_KEY` hardcoded `"development-secret-key"` in [`app/__init__.py`](../../app/__init__.py). `get_current_organization_id()` falls back to `ORG-001`. `HISTORICAL_UPLOAD_ACTOR` default `"Joel Brayman"`.

### A. Office-route inventory

Live `url_map` (TESTING create_app): **151 rules**. **150 operating rules require login after activation** except future `auth.login` / `auth.logout` and Flask `static`. Duplicate slash aliases (`/proposals` and `/proposals/`) are the same endpoints.

**Public / auth candidates (to be added; not present today):**

| Methods | Path | Class |
|---------|------|--------|
| GET, POST | `/login` | public auth |
| POST | `/logout` | auth (CSRF); not GET |

**Static asset (remains public):** `GET /static/<path:filename>` — CSS/JS/committed branding PNG only. **Not** org-custody logos or PDFs.

**Download / file (login required):**

| Methods | Path | Endpoint |
|---------|------|----------|
| GET | `/projects/<id>/permit-report.pdf` | `projects.download_permit_report_pdf` |
| GET | `/projects/<project_id>/plans/<document_id>/download` | `plan_intelligence.download_plan` |
| GET | `/project-controls/change-orders/<id>/pdf` | `project_controls.download_change_order_pdf` |
| GET | `/proposals/<id>/pdf` | `proposals.download_proposal_pdf` |
| GET | `/proposals/<id>/brand-logo` | `proposals.proposal_brand_logo` |
| GET | `/settings/brand-logo` | `settings.current_brand_logo` |

**Browser JSON helper (login required; not a public API):**

| Methods | Path | Endpoint |
|---------|------|----------|
| GET | `/projects/<project_id>/plans/sheets/<sheet_id>/measurements/data` | `plan_intelligence.sheet_measurement_data` |

JSON **mutating** measurement/calibration POSTs on the same sheet (also login + CSRF; `request.is_json` accepted today): `.../calibrations/two-point`, `.../calibrations/preset`, `.../calibrations/<id>/confirm`, `.../calibrations/<id>/void`, `.../calibrations/nts`, `.../measurements`, `.../measurements/<id>/void`.

**Internal / dev-only:** none found.

**Authenticated office routes (login required after activation):** all remaining registered HTML GET/POST rules under `/`, `/clients/`, `/projects/`, `/estimates/`, `/proposals`, `/proposal-templates`, `/labour-engine/`, `/pricing-engine/`, `/historical-estimates/`, `/material-catalogue/`, `/cost-library/`, `/assemblies/`, `/settings`, `/project-controls/change-orders`, and plan/take-off/permit paths listed in the live `url_map`. Dashboard `GET /` is included.

No permanent anonymous operating mode after activation.

### B. Proposed User schema (`users`) — do not create now

| Column | Type | Notes |
|--------|------|--------|
| `id` | Integer PK | Matches Brand Profile / LabourTask integer identity. Not a tenant code. |
| `email` | String(255) NOT NULL | Login + contact identifier. Unique on **normalized** value. |
| `display_name` | String(150) NOT NULL | Human-readable actor snapshot source. Length matches existing actor columns. |
| `password_hash` | String(255) NOT NULL | Werkzeug `pbkdf2:sha256` hash only. Never plaintext. |
| `is_active` | Boolean NOT NULL default True | Inactive cannot authenticate. |
| `created_at` | DateTime NOT NULL | UTC, same pattern as `Organization`. |
| `updated_at` | DateTime NOT NULL | UTC, `onupdate`. |

**Normalization:** `email.strip().lower()`. Reject empty. Unique index on `email`.

**Do not add:** `last_login` (no repository evidence); HR/personnel fields; roles.

**Flask-Login:** `UserMixin`. `get_id()` → `str(id)`. Column `is_active` satisfies Flask-Login. `user_loader`: load by integer id; **return `None` if missing or `is_active` is false** (stale session fail-closed).

### C. Proposed UserMembership schema (`user_memberships`) — do not create now

| Column | Type | Notes |
|--------|------|--------|
| `id` | Integer PK | |
| `user_id` | Integer NOT NULL FK `users.id` | indexed |
| `organization_id` | String(50) NOT NULL FK `organizations.id` | indexed |
| `is_active` | Boolean NOT NULL default True | |
| `created_at` | DateTime NOT NULL | |

**Constraints:** UNIQUE (`user_id`, `organization_id`). **No roles column.** Phase A “with RBAC roles” remains future architecture.

**V1 org resolution (authenticated request):** count **active** memberships for `current_user`.

| Active memberships | Behaviour |
|--------------------|-----------|
| 0 | Fail closed |
| 1 | Use that `organization_id` |
| >1 | Fail closed. Do **not** pick ORG-001, first row, or most recent. |

V1 bootstrap: one active ORG-001 user, one active ORG-001 membership.

### D. Password / auth design

| Concern | Design |
|---------|--------|
| Hash | `werkzeug.security.generate_password_hash(..., method="pbkdf2:sha256")` — **must pin method**. Default scrypt **fails** on this Python 3.9 (`hashlib.scrypt` missing). |
| Verify | `check_password_hash` |
| Login form | `GET/POST /login` — email + password. No Flask-WTF `FlaskForm` required if CSRFProtect + manual fields (repository has no WTForms today). |
| Logout | `POST /logout` only (CSRF). |
| Inactive | Cannot log in; `user_loader` returns None. |
| Session | Flask signed cookie + Flask-Login. `login_manager.login_view = "auth.login"`. |
| Remember-me | **Omit** (not in ADR; do not invent). |
| Safe next | Allow only relative same-host paths; reject `//`, `http:`, empty → dashboard. |
| Login failure | Generic “Invalid email or password.” Re-render login. Do not reveal whether the email exists. Malformed email = same generic failure. |
| Throttling | **Deferred** (ADR-041). Record only. |

### E. CSRF design

Flask-WTF is **not** in `requirements.txt`. Several tests already set `WTF_CSRF_ENABLED: False` (leftover-compatible). **Add `Flask-WTF`** and `CSRFProtect(app)`.

- Enable CSRF for login POST and all mutating browser POSTs (HTML form and JSON measurement POSTs).
- Templates: `csrf_token()` hidden field; JSON helpers: `X-CSRFToken` header from cookie (`flask-wtf` default).
- **TESTING:** default `WTF_CSRF_ENABLED = False` in `create_app` when `TESTING` so existing POST suites do not all gain tokens. Dedicated CSRF tests set `WTF_CSRF_ENABLED True`.
- **No exemption** for mutating measurement JSON POSTs. GET `measurements/data` is not CSRF-relevant.
- Static GET is not CSRF-relevant.

### F. SECRET_KEY / config

Location: [`app/__init__.py`](../../app/__init__.py) `create_app`. Env var name: **`SECRET_KEY`** (already used by tests as config key). `python-dotenv` may load gitignored `.env` at startup if present — do not commit `.env`.

| Mode | Behaviour |
|------|-----------|
| `TESTING` | Explicit config `SECRET_KEY` (existing tests already pass one). If omitted under TESTING only: `"test-secret-key"`. Never require production env in pytest. |
| Development | Allow committed `"development-secret-key"` **only** when `FLASK_DEBUG=1` (or Flask debug true). |
| Non-development | `SECRET_KEY` **must** come from environment/config, **must be present**, **must not equal** `"development-secret-key"`. Else **raise** at startup (fail safely). |

Local UAT after implementation: export a local-only `SECRET_KEY`, or run with `FLASK_DEBUG=1`. Do not add an external secrets platform.

### G. Bootstrap / password reset

**Recommend:** Flask CLI group `auth` (no CLI exists today; Flask-Migrate already uses Flask CLI).

```text
flask auth bootstrap-org-001-user --email EMAIL --display-name NAME
flask auth reset-password --email EMAIL
```

Password: `getpass` prompt, or env `AUTH_BOOTSTRAP_PASSWORD` / `AUTH_RESET_PASSWORD` at **runtime only**. Never argv. Never Git. Never Alembic.

- Hash with pinned pbkdf2.
- `ensure_default_organization()` then insert User + active membership ORG-001.
- Duplicate bootstrap (email exists): **fail closed**; do not overwrite hash.
- Reset: existing user only; replace hash; do not change membership; unknown email fail closed (generic operator error).
- Idempotent membership: if user exists with ORG-001 membership, bootstrap fails; use reset for password.

### H. Organization-context transition

[`app/services/organizations.py`](../../app/services/organizations.py) today: `g.organization_id` else `DEFAULT_ORGANIZATION_ID` (`ORG-001`).

**Authenticated request:** ignore silent `DEFAULT_ORGANIZATION_ID`. Resolve from active memberships as in C. Set `g.organization_id` to that value for existing service callers.

**Unauthenticated HTTP:** must not reach operating services after activation (`login_required`). If they do: fail closed.

**No request context (CLI / seed):** keep `DEFAULT_ORGANIZATION_ID` so `ensure_default_organization()` and model `default=get_current_organization_id` callables still work.

**TESTING isolation:** replace `set_current_organization_id("ORG-002")` HTTP simulations with an authenticated ORG-002 member fixture. Do not keep a silent ORG-001 fallback for authenticated users. `set_current_organization_id` may remain as a non-HTTP test helper only where no login is involved.

**Shell leak:** [`app/shell.py`](../../app/shell.py) `register_shell_context` queries `Estimate` / `Proposal` **without org filter**. Login page must not run that query. After auth: **MAY** scope those queries to membership org (bounded; isolation-related). Do not copy Dashboard unscoped counts as a product expansion.

### I. Route-activation sequence (one deployment; no permanent bypass)

1. Apply additive migration `b0c1d2e3f4a5`.
2. CLI `flask auth bootstrap-org-001-user` (CLI is not HTTP; not locked out).
3. Verify `flask auth` / login with those credentials.
4. HTTP `before_request`: require login for every endpoint except `static`, `auth.login`, `auth.logout`.
5. Authenticated `get_current_organization_id()` uses membership only.

No `OFFICE_AUTH_ENFORCED` flag (would be a permanent bypass if left false). Operator order: migrate → bootstrap → open browser. If code is deployed before bootstrap, the browser is locked until CLI bootstrap — that is intended.

### J. Actor-provenance touchpoints

**Do not** add `user_id` columns in FG-018. Snapshot `current_user.display_name` into existing String(150) actor fields on **new** writes. Historical rows unchanged. No backfill.

| Class | Path | Current default | FG-018 |
|-------|------|-----------------|--------|
| **MUST** | `labour_engine._actor` | form or `"Joel Brayman"` | authenticated display_name |
| **MUST** | `pricing_engine._actor` | form or `"Joel Brayman"` | authenticated display_name |
| **MUST** | `brand_profile._actor_name` | `HISTORICAL_UPLOAD_ACTOR` / `"Joel Brayman"` | authenticated display_name |
| **MUST** | `historical_ingestion._office_actor` | config `"Joel Brayman"` | authenticated display_name |
| **MUST** | `historical_estimates.post_review` | form or `"Joel Brayman"` | authenticated display_name |
| **MUST** | `estimates.apply_org_pricing` | form or `"Joel Brayman"` | authenticated display_name |
| **MUST** | `projects.create_project` `created_by` / `generated_by` | form or `"Estimator"` | authenticated display_name |
| **MUST** | `projects` permit run / facts `generated_by` / `reviewed_by` | `"Estimator"` | authenticated display_name |
| **MUST** | take-off routes empty `created_by` / `reviewed_by` / `approved_by` | form blanks | authenticated display_name (keep human-actor rules; still reject AI/system strings) |
| **MAY** | Change Order `requested_by` empty form | empty / operator typed | default display_name if blank |
| **MAY** | `record_plan_audit` `detail` | often includes actor already | include display_name on **new** events; **no** new column |
| **DEFER** | `PlanAuditEvent` actor column | **none** | do not add in FG-018 |
| **DEFER** | repository-wide `user_id` FKs | n/a | later gate |
| **C — leave** | historical `created_by` / `reviewed_by` / `approved_by` / `frozen_by` / `generated_by` / `requested_by` / `pricing_override_by` / audit `actor` **existing rows** | as stored | **untouched** |

### K. Migration design (do not create)

- File: `migrations/versions/b0c1d2e3f4a5_add_users_and_user_memberships_fg018.py`
- `revision = "b0c1d2e3f4a5"`
- `down_revision = "a9b0c1d2e3f4"`
- Tables: `users`, `user_memberships` only
- Schema **only**. **No** User/password/membership seed in SQL.
- Downgrade: drop the two tables.
- Post-upgrade: CLI bootstrap (not Alembic).

### L. Implementation files (later prompt)

**NEW:** `app/models/user.py`; `app/services/auth.py`; `app/routes/auth.py`; `app/templates/auth/login.html`; `app/cli/auth.py` (or `app/commands/auth.py`); `migrations/versions/b0c1d2e3f4a5_add_users_and_user_memberships_fg018.py`; `tests/test_auth_fg018.py`; `tests/auth_fixtures.py` (or helpers in dedicated test module).

**CHANGED:** `app/__init__.py` (LoginManager, CSRFProtect, SECRET_KEY fail-closed, register auth blueprint, `before_request`); `app/models/__init__.py`; `requirements.txt` (add Flask-WTF); `app/services/organizations.py`; `app/shell.py` (skip commercial queries when anonymous); `app/templates/base.html` (csrf meta, logout POST, user label); actor helpers listed in J; all HTTP test modules (authenticated client); docs on close (not this pass).

**Do not change:** `migrations/` except the one new revision when implementation is authorized.

### M. Dedicated tests (proposed file `tests/test_auth_fg018.py`)

Login success; wrong password; inactive user; logout; session cookie; unauthenticated operating route → login; membership-derived org; zero memberships fail closed; multiple active memberships fail closed; cross-org URL 404/fail closed; password hashed not plaintext; bootstrap CLI; duplicate bootstrap fail; password-reset CLI; CSRF login; CSRF mutating POST; production-like SECRET_KEY reject committed default; TESTING/dev SECRET_KEY allowed; authenticated actor snapshot on one MUST path; historical actor fixture strings unchanged; file/download login protection (`/settings/brand-logo`, plan download, proposal PDF).

### N. Regression suites

| Area | File |
|------|------|
| Organization isolation | `tests/test_organization_foundation.py` |
| CRM / projects / hub | `tests/test_project_hub.py` (+ project routes in foundation) |
| Estimates | `tests/test_estimates.py`, `tests/test_estimate_builder.py` |
| Estimate output | `tests/test_estimate_output_consistency.py` |
| Proposals / immutability / PDF / preview / snapshots | `tests/test_proposals.py`, `tests/test_proposal_immutability.py`, `tests/test_proposal_pdf.py`, `tests/test_proposal_preview.py`, `tests/test_proposal_snapshots.py` |
| Brand Profile | `tests/test_brand_profile_fg017.py` |
| Change Orders | `tests/test_change_orders.py` |
| Labour | `tests/test_labour_engine.py` |
| Pricing | `tests/test_pricing_engine.py` |
| Take-off | `tests/test_takeoff.py` |
| Plans / sheets / scale | `tests/test_plan_upload.py`, `tests/test_plan_indexing.py`, `tests/test_sheet_intelligence.py`, `tests/test_scale_measurement.py` |
| Permit | `tests/test_permit_foundation_fg015.py`, `tests/test_permit_intelligence_fg016.py` |
| Historical | `tests/test_historical_ingestion.py`, `tests/test_historical_upload_fg013.py` |
| Material catalogue | `tests/test_material_catalogue_fg014.py` |
| Assemblies / cost library POSTs | `tests/test_assemblies.py` |
| Settings / brand | `tests/test_brand_profile_fg017.py` |

Then `./venv/bin/python -m pytest -q`. Governed baseline today: **423 passed**. Do not claim a new count until run after implementation.

**Fixture strategy:** shared helper `login_office_user(client, email, password)` after seeding User + ORG-001 membership in each app fixture (or one extracted helper copied into tests — no `conftest.py` exists; adding `tests/conftest.py` is acceptable if it only provides auth helpers and does not change test collection semantics). CSRF off under TESTING.

### O. Shared API / BUILD boundary

FG-018 does **not** implement `/api/`, `/api/v1/me`, tokens, field endpoints, or public API. Approving FG-018 does **not** unblock BUILD. BUILD remains blocked until FG-018 is **implemented and closed**, and a later shared-API gate is separately governed if ADR-022 still requires it before field implementation. **Do not create that gate now.**

### P. Security / failure behaviour

| Case | Behaviour |
|------|-----------|
| Wrong password | Generic failure; no session |
| Inactive user | Cannot authenticate; stale session dropped via `user_loader` |
| No membership | Fail closed (403/redirect+flash; no org) |
| Multiple active memberships | Fail closed; do not select |
| Cross-org URL | Existing org-scoped `first_or_404` remains; membership org is the only query org |
| Missing SECRET_KEY (non-dev) | Startup raise |
| Committed dev secret in production-like mode | Startup raise |
| Missing CSRF | 400 from CSRFProtect |
| Deactivated membership | Fail closed even if User active |
| Direct file/download | Same login_required as HTML |
| Login redirect loop | Exempt only login/logout/static |
| Bootstrap rerun | Fail; do not overwrite |
| Duplicate / malformed email | Unique constraint / generic login failure |

**Joel policy still required:** none of the above invents org-switching. Login throttling remains deferred. Credential-enumeration is generic-message only (not a new product feature).

### Q. Conflicts discovered (do not repair in this pass)

- Phase A architecture still says UserMembership “with RBAC roles” — V1 has **no** roles.
- `register_shell_context` unscoped Estimate/Proposal queries.
- Default Werkzeug hash (scrypt) **broken** on current Python 3.9 — pin pbkdf2.
- `WTF_CSRF_ENABLED` already false in some tests though Flask-WTF is absent.
- Historical chat/milestone rows saying “do not create FG-018” remain historical snapshots.

---

## Documentation consistency note

Roadmap item 10 office-auth is **CLOSED / OPERATIONAL FOR UAT**. Item 10 as a whole is **PARTIALLY COMPLETE**. Shared API remains **deferred / not implemented**. BUILD remains **BLOCKED** until a later shared-API gate is separately governed ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md)). Do not create FG-019 from a documentation pass.

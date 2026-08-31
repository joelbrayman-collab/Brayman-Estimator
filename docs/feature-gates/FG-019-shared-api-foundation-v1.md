# Feature Gate FG-019: Shared API Foundation V1

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-019` |
| Feature Name | Shared API Foundation V1 — Authenticated JSON Transport |
| Target Milestone | **None.** FG-019 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Office / platform** owns the `/api/v1` transport adapter. It does **not** take ownership of User, Organization, Project, or Client records. |
| Date | 2026-08-31 |
| Status | **DRAFT FOR JOEL REVIEW / NOT APPROVED.** Implementation **NOT STARTED.** A draft is **not** authorization. |
| Architecture | [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** (field/API sequence; no API code in CAR-001) · [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** (office User / membership / session; cookie-versus-token deferred to this gate) · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** (BUILD **out of this gate**) · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [platform-roadmap.md](../platform-roadmap.md) item 10 |
| Related ADRs | [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** · [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted** · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Shared API architecture reconnaissance reviewed 2026-08-31. **ADR-022 Accepted. ADR-041 Accepted.** |
| Approved baseline | Live Alembic current = head **`b0c1d2e3f4a5`**. Full suite **460 passed**. Dedicated FG-018 **37 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **DRAFT FOR JOEL REVIEW / NOT APPROVED** |
| Implementation | **NOT STARTED** |
| Schema / Alembic | **NO MIGRATION.** Live current = head **`b0c1d2e3f4a5`**. One graph head. |
| Shared API product code | **NOT STARTED** |
| BUILD / Field Web | **BLOCKED.** FG-019 closure would complete Item 10 and make Item 11 eligible for its own governance. FG-019 does **not** authorize BUILD implementation. |

This draft does **not** approve FG-019. It does **not** authorize `/api/` implementation, BUILD, Field Web, tokens, or a new ADR.

---

## Purpose

Give future CalibAi clients an **authenticated JSON transport adapter** over the existing Flask service/query layer so BUILD field capture is not later invented as a second business-logic stack or as anonymous JSON.

```text
FG-018 SESSION (Flask-Login cookie)
→ /api/v1 JSON TRANSPORT
→ EXISTING SERVICES / ORG-SCOPED QUERIES
→ ALLOW-LISTED IDENTITY + PROJECT IDENTITY
```

Office HTML continues to call Flask routes/services directly. FG-019 is an **additional** adapter, not an office rewrite.

Success (if later Approved, implemented, and closed): a session-authenticated User with exactly one active membership can `GET /api/v1/me` and tenant-scoped project identity reads; unauthenticated and fail-closed membership cases return JSON errors; no mutation; no BUILD surface; no migration.

Success is **SHARED API FOUNDATION V1**, not BUILD, not Field Web, not tokens, and not a public API.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Item 10 is only **PARTIALLY COMPLETE**. FG-018 closed office login. ADR-022 still requires a shared JSON API before field/BUILD. No `/api/` blueprint exists. |
| 2 | Who is the user? | Future CalibAi clients (same-origin Field Web later). Not the customer. Not a public developer. Not native iOS in this gate. Office operators keep using HTML. |
| 3 | Which module owns it? | **Office / platform** owns the `/api/v1` blueprint and JSON error/auth transport. Organization subsystem remains owner of User / UserMembership. Projects remains owner of `projects`. CRM remains owner of `clients`. |
| 4 | What data does it own? | **None.** No new tables. Session remains the FG-018 Flask-Login session. |
| 5 | What data does it reference? | `users`, `user_memberships`, `organizations`, `projects`, `clients` (client name only). |
| 6 | What may implementation change? | Only after Joel Approves this gate **and** a separate implementation prompt: `/api/v1` blueprint; session-authenticated GET handlers; 401 JSON instead of HTML login redirect for `/api/` paths; optional thin org-scoped project-read helper that does **not** duplicate commercial rules; tests; docs. |
| 7 | What must it not change? | BUILD; Field Web UI; tokens; office HTML rewrite; historical actor strings; Proposal immutability; Brand Profile freeze; Permit analysis; Labour/Pricing commercial rules; take-off approval; Material Catalogue identity; Change Order records; RBAC; org-switcher; ADR-008/010 status; Alembic history. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. Not claimed complete by this draft. |
| 9 | Tests required? | See **Dedicated tests** and **Regression**. None written in this pass. |
| 10 | Documentation? | This gate; feature-gate index; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log; milestones; docs/README. |
| 11 | ADR required? | **No new ADR.** ADR-022 + ADR-041 are sufficient for cookie/session, read-only `/api/v1`, no tokens, no migration. If implementation wants tokens or a public API: **STOP**. |
| 12 | Migration? | **NO.** No new tables. No token schema. No API credential storage. Do **not** run `flask db upgrade` for this gate. |

---

## Owner

| Concern | Owner |
|---------|--------|
| `/api/v1` blueprint, JSON 401/403/404/400, GET-only surface | **Office / platform** |
| Flask-Login session / login / logout / CSRF on browser POSTs | **Office / platform** (FG-018; unchanged) |
| User / UserMembership | **Organization subsystem** |
| Organization tenant | **Organization subsystem** |
| Project identity rows | **Projects** |
| Client name (referenced) | **CRM** |
| BUILD field-execution records | **Out of this gate** ([ADR-020](../adr/ADR-020-build-module-boundary.md)) |

Do **not** create a new product module named API/IAM.

---

## Authentication model

V1 **reuses FG-018**:

- Flask-Login authenticated `User`
- existing Flask cookie/session
- `is_active` User (`user_loader` already returns `None` when inactive)
- exactly one active `UserMembership`
- organization context from membership only (`resolve_membership_organization_id` / `get_current_organization_id`)

**Do not** introduce bearer tokens, API tokens, refresh tokens, token tables, OAuth, SSO, native-mobile auth, organization switching, or RBAC.

Same-origin future Field Web may use this cookie/session. Future native iOS may need a **separately governed** token mechanism. **Do not** solve native authentication in FG-019.

---

## Exact endpoint surface

Blueprint `url_prefix=/api/v1`. **GET only.** FG-019 **HAS NO MUTATING API ENDPOINT.**

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/me` | Authenticated actor + membership-derived Organization identity |
| `GET` | `/api/v1/projects` | Current-org project identity list |
| `GET` | `/api/v1/projects/<id>` | Current-org project identity read; cross-org/missing → 404 |

`POST` / `PUT` / `PATCH` / `DELETE` on `/api/v1/*` must **not** exist (405 if hit).

Office `POST /login` and `POST /logout` remain HTML (FG-018). They are **not** API endpoints.

Existing office JSON under `plan_intelligence_bp` (calibration/measurement) is **not** part of `/api/v1` and must not be migrated in this gate.

### `GET /api/v1/me` — allow-list

| Field | Source |
|-------|--------|
| `user_id` | `User.id` |
| `email` | `User.email` (normalized identity; justified so a client knows who is logged in) |
| `display_name` | `User.display_name` |
| `is_active` | `User.is_active` |
| `organization_id` | sole active `UserMembership.organization_id` |
| `organization_display_name` | `Organization.display_name` |

**Exclude:** `password_hash`; roles; membership rows beyond the current org; commercial records.

### `GET /api/v1/projects` and `GET /api/v1/projects/<id>` — allow-list

| Field | Source |
|-------|--------|
| `id` | `Project.id` |
| `name` | `Project.name` |
| `project_number` | `Project.project_number` |
| `status` | `Project.status` |
| `client_id` | `Project.client_id` |
| `client_name` | `Client.name` (same-org client) |

**Exclude:** address, description, commercial context, estimates, proposals, Change Orders, plans, take-off, permit profiles/analyses, labour/pricing snapshots, Brand Profile, historical ingestion, costs, margin.

List is membership-org `Project.query.filter_by(organization_id=...)`. Detail is the same filter then `first_or_404`. Do **not** return `assemble_project_hub`.

A later implementation prompt may add a **thin** org-scoped project-read helper in `app/services/` so the blueprint does not become a second query SoR. That helper must not invent commercial rules. **Do not create it in this draft pass.**

---

## Mutation / CSRF

**FG-019 HAS NO MUTATING API ENDPOINT.**

Read-only GET does not need a new mutation-CSRF design. Existing mutating **browser** routes remain under FG-018 CSRF (`csrf_token` / `X-CSRFToken`). Do **not** create CSRF exemptions.

If a later gate adds cookie-authenticated JSON POST, it must send `X-CSRFToken`. That is **out of FG-019**.

---

## Tenant isolation

Every `/api/v1` request:

- requires an authenticated active User
- derives org from **exactly one** active membership
- **ignores** caller-supplied `organization_id` as authority
- scopes Project/Client reads to that org
- cross-org project id → **404** (do not leak existence)

Zero active memberships → **403**. More than one active membership → **403**.

---

## Error contract

Plain JSON `{"error": "<message>"}`. HTTP status is the contract. No error-code taxonomy.

| Case | Status |
|------|--------|
| Unauthenticated `/api/v1/*` | **401** JSON (not 302 `/login`) |
| Inactive / stale User (`user_loader` None) | **401** |
| Zero active memberships | **403** |
| Multiple active memberships | **403** |
| Missing project (same org) | **404** |
| Cross-org project | **404** |
| Malformed path/id | **400** or **404** without leaking foreign existence |
| Method not allowed on `/api/v1/*` | **405** |

Do not return `password_hash` or stack traces.

Unauthenticated **office HTML** remains 302 to `/login` (FG-018). Only `/api/` paths use 401 JSON.

---

## Office application

The office HTML application **continues to call Flask services directly**.

**DO NOT** migrate office pages to `/api/v1/`.

---

## Schema / migration

**NO MIGRATION.**

- no new database tables
- no token schema
- no API credential storage
- reuse `users`, `user_memberships`, `organizations`, `projects`, `clients`

If a later implementation prompt wants tokens: **STOP.** That contradicts this gate.

---

## Native / token deferral

- Same-origin Field Web (later gate) may use FG-018 cookie/session.
- Future native iOS (separately Feature-Gated; CAR-001 later list) may require tokens.
- **Do not** add token infrastructure in FG-019.

---

## Item-10 completion rule

Roadmap item 10 (**Authentication / actor identity + shared API foundation**) becomes **COMPLETE** only when:

1. [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) is **CLOSED / OPERATIONAL FOR UAT** (already true), **and**
2. FG-019 Shared API Foundation is **CLOSED / OPERATIONAL FOR UAT**.

Nothing more (not Field Web, not BUILD, not tokens, not RBAC).

After Item 10 is complete, **Item 11 BUILD Field Capture** becomes eligible for its **own** architecture / Feature-Gate governance. FG-019 closure **must not** authorize BUILD implementation. Item 12 Field Web remains a later gate. MONITOR remains downstream.

---

## Exact proposed scope

If later Approved **and** a separate implementation prompt is authorized, implementation may include **only**:

1. Flask blueprint `/api/v1`.
2. Session authentication reuse (FG-018 Flask-Login cookie).
3. `GET /api/v1/me` with the allow-list above.
4. `GET /api/v1/projects` and `GET /api/v1/projects/<id>` with the allow-list above.
5. JSON 401 for unauthenticated `/api/` (not HTML login redirect).
6. Membership fail-closed 403; cross-org/missing 404.
7. Optional thin org-scoped project-read helper (no commercial duplication).
8. Dedicated tests + office regression + full suite.
9. Documentation.

---

## Non-goals

**DO NOT** include:

- BUILD models, routes, or UI
- Field Web UI / Today screen
- native iOS
- tokens / API keys / OAuth / SSO
- public developer API / integration marketplace API
- mutation endpoints
- photos, notes, field evidence, labour actuals, time capture, issue/event capture
- MONITOR / LEARN
- Phase D
- supplier integration
- Change Order document family
- Permit branding
- QuickBooks
- Ontario Contract / Warranty
- external AI / runtime web lookup
- RBAC / organization switching
- SaaS billing / invitations / self-registration
- office HTML rewrite
- database migration
- accepting ADR-008 or ADR-010

---

## Acceptance criteria

Not claimed by this draft. If later implemented:

1. Unauthenticated `GET /api/v1/me` and `GET /api/v1/projects` → **401** JSON.
2. Authenticated active User with exactly one active membership → **200** on `/me` and org-scoped project reads.
3. `/me` returns **only** the allow-listed fields; no `password_hash`.
4. Project list returns **only** current-org projects; allow-listed fields only.
5. Current-org project detail → **200** allow-list.
6. Cross-org project id → **404**.
7. Missing same-org project → **404**.
8. Zero membership → **403**.
9. Multiple active memberships → **403**.
10. Inactive/stale User → **401**.
11. Caller-supplied `organization_id` does not change scope.
12. Handlers call existing membership org resolution and org-scoped Project/Client reads (no second SoR).
13. **No** mutating `/api/v1` endpoint.
14. **No** BUILD surface.
15. **No** token/auth schema; **no** migration.
16. Office HTML login/logout and operating routes remain operational.
17. Full suite passes with no unexplained loss versus **460 passed**.

---

## Dedicated tests (future implementation prompt)

Proposed file: `tests/test_shared_api_fg019.py` — **do not create until implementation is authorized.**

- `/api/v1/me` authenticated 200 + allow-list
- `/api/v1/me` unauthenticated 401 JSON
- inactive User 401
- zero membership 403
- multiple memberships 403
- `organization_id` equals sole active membership
- project list current-org only
- project detail current-org 200
- cross-org project 404
- missing project 404
- response allow-list (no extra commercial keys; no `password_hash`)
- JSON error shape
- `POST /api/v1/me` (and other writes) 405 / not registered
- no BUILD routes under `/api/v1`

CSRF: GET-only; no new CSRF exemption tests beyond proving GET succeeds without a mutation token.

---

## Regression (future implementation prompt)

| Suite | Path |
|-------|------|
| Auth / membership | `tests/test_auth_fg018.py` |
| Organization / tenant | `tests/test_organization_foundation.py` |
| Project Hub | `tests/test_project_hub.py` |
| Estimates / proposals | `tests/test_estimates.py`, `tests/test_proposals.py`, `tests/test_proposal_immutability.py` |
| Brand / permit / plans | `tests/test_brand_profile_fg017.py`, `tests/test_permit_foundation_fg015.py`, `tests/test_permit_intelligence_fg016.py`, `tests/test_plan_upload.py`, `tests/test_takeoff.py` |
| Labour / pricing | `tests/test_labour_engine.py`, `tests/test_pricing_engine.py` |

Then `./venv/bin/python -m pytest -q`. Governed baseline today: **460 passed**. Do not claim a new count until that future run.

---

## Protected implementation rule

**ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

Drafting FG-019 does **not** authorize Cursor to implement `/api/`. Joel must Approve this gate **and** issue a separate implementation prompt.

---

## Documentation consistency note

Roadmap item 10 remains **PARTIALLY COMPLETE** until FG-019 is later **CLOSED / OPERATIONAL FOR UAT**. Shared API product code remains **NOT STARTED**. BUILD remains **BLOCKED**.

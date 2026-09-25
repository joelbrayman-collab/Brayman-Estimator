# Feature Gate FG-040: Hosted Office Production Configuration

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-040` |
| Feature Name | Hosted office production configuration |
| Target Milestone | **None.** FG-040 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Application factory / startup configuration** (`app/__init__.py`). No business module owns new records. |
| Date | 2026-09-25 |
| Status | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED** |
| Architecture | Hosted SQLite for V1. One Gunicorn worker is a later host command. This gate does not deploy. |
| Related ADRs | **None.** |
| Prerequisites | Whole-system Rule 16 **SEALED**. S16 **APPLIED LIVE** at `h8c9d0e1f2a3`. Production architecture accepted: hosted SQLite, one worker, persistent disk, HTTPS, environment secrets. |
| Approved baseline | `main` @ `52e46cc4fef0d2f3a6dca25fa0f7d60b676584a7` |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED** |
| Implementation | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED** |
| Schema / Alembic | **NO** change. Repository head remains **`h8c9d0e1f2a3`**. Live remains **`h8c9d0e1f2a3`**. |
| New ADR | **None** |
| Hosted deployment | **NOT PERFORMED.** Hosted application **DOES NOT EXIST**. |
| Hosted validation | **NOT PERFORMED** |
| Production E2E | **NOT PERFORMED** |
| V1 rescore | **NOT PERFORMED.** Official V1 remains **65% / 4 of 11**. Secondary Functional V1 Build remains **79% / 22 of 28**. |
| FG-039 | **PARKED / NOT PUBLISHED** |

This gate makes the sealed application configurable for a later hosted environment. It does not choose a host, copy data, or put the office online.

---

## Configuration law

**Local office mode** is the default. `CALIBRAYTAI_HOSTED` is absent. The database URI stays `sqlite:///brayman_estimator.db` unless a test passes another `SQLALCHEMY_DATABASE_URI`. `CALIBRAYTAI_DATABASE_URI` is ignored. `SESSION_COOKIE_SECURE` stays false so `http://127.0.0.1:5460` still works. Family 05 keeps the Mac absolute default. Local mail behaviour is unchanged.

**Hosted production mode** is only `CALIBRAYTAI_HOSTED=1`, or the same flag in the application config dict used by tests. Debug off is not this signal.

In hosted mode, `CALIBRAYTAI_DATABASE_URI` is required. A missing, blank, or whitespace value raises `HostedDatabaseConfigError` before SQLAlchemy is initialized. That startup does not create `instance/brayman_estimator.db`. An explicit SQLite URI is valid. PostgreSQL is not added.

In hosted mode, `SECRET_KEY` must exist and must not be `development-secret-key`, including when `FLASK_DEBUG=1`. Existing non-debug and test secret checks stay in place for local mode.

In hosted mode the session cookie is `Secure`, `HttpOnly`, and `SameSite=Lax`. There is no remember-me cookie. Login remains `remember=False`.

`PUBLIC_BASE_URL` is not required to start. `public_base_url()` is unchanged. Postmark is not activated.

In hosted mode, contract generation does not fall back to the Mac Family 05 path. A missing `FAMILY_05_MASTER_PATH` raises the existing `Family05MasterError` (`MISSING_PRESENTATION_MASTER`) when the master is loaded. Startup does not require the file. The governed SHA-256 check is unchanged.

Persistent storage stays the normal Flask instance directory. This gate does not add another storage root. Gunicorn still uses `app:app`. No Procfile, service file, or container is added. One worker is a host command after a host exists.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | A hosted process must not silently open or create the implicit local SQLite database, must use HTTPS session cookies, and must not fall back to the Mac Family 05 path. The Mac office must keep today's behaviour. |
| 2 | Who is the user? | Joel, later, on the hosted office. This package does not put the office online. |
| 3 | Which module owns it? | Application factory / startup configuration (`app/__init__.py`). Family 05 path choice in hosted mode is `app/services/family_05_master.py`. |
| 4 | What data does it own? | **None.** |
| 5 | What data does it reference? | The existing database only when an explicit hosted URI is configured. |
| 6 | What may it change? | Startup configuration and the hosted Family 05 path choice. |
| 7 | What must it not change? | Mac data, h8 revision, local HTTP, local mail, passwords, reset-token rules, CSRF, generic login failure, upload limits, models, migrations, routes. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. |
| 9 | Tests required? | `tests/test_hosted_production_config.py`, plus auth and Family 05 regression, then the full suite. |
| 10 | Documentation? | This gate, the feature-gate index, current-state, session-handoff, chat-workflow-log, and the roadmap next-action. Do not rescore V1. Do not write the User Guide. |
| 11 | ADR required? | **No.** |
| 12 | Migration? | **No.** |

---

## Acceptance criteria

1. Local mode with no hosted flag resolves `sqlite:///brayman_estimator.db`.
2. Local mode ignores `CALIBRAYTAI_DATABASE_URI`.
3. Local mode leaves `SESSION_COOKIE_SECURE` false.
4. Hosted mode uses the explicit `CALIBRAYTAI_DATABASE_URI`.
5. Hosted mode with a missing, blank, or whitespace URI raises `HostedDatabaseConfigError` and does not create `brayman_estimator.db` on a temporary instance path.
6. Hosted mode fails when `SECRET_KEY` is missing or is the development secret, including when `FLASK_DEBUG=1`.
7. Hosted mode starts when `SECRET_KEY` is some other value and the database URI is explicit.
8. Hosted mode sets `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, and `SESSION_COOKIE_SAMESITE=Lax`.
9. Hosted mode starts with `PUBLIC_BASE_URL` empty while the local mail provider remains active. A set value is what `public_base_url()` returns.
10. Hosted contract load without `FAMILY_05_MASTER_PATH` raises `Family05MasterError` and does not use the Mac path.
11. Local Family 05 still resolves the Mac default path.
12. The live Mac database and Flask PID `62523` are unchanged by this package.

---

## Out of scope

Hosting vendor, hostname, DNS, certificates, remote host creation, remote installs, Procfile, systemd, Passenger, Dockerfile, database copy, file copy, production secret values, Postmark, LibreOffice, hosted validation, production E2E, Mac write freeze, cutover, PostgreSQL, more than one worker, synchronization, V1 rescore, FG-039 publication, and the website HostPapa migration.

---

## Mac non-regression

The Mac office stays in local mode. It does not adopt hosted settings. Local Flask on `127.0.0.1:5460` stays on HTTP-compatible cookies. The live database path, data, and revision `h8c9d0e1f2a3` stay in place.

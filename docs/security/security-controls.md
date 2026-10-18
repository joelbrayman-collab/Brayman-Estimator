# Security Controls — CalibraytAI

| Attribute | Value |
|-----------|--------|
| Status | Current (18 Oct 2026). Items marked **unreleased** are on branch `security/closure-2026-10-18`, tested, not deployed. |
| Enforced by | the tests named in each row |

## Sign-in and sessions

| Control | Behaviour | Tests | Status |
|---|---|---|---|
| Office sign-in wall | Every office route sends a signed-out request to `/login` (API: 401 JSON). The public endpoint list is frozen in a test. | `test_security_route_sweep.py` (all 406 routes), `test_auth_fg018.py` | Live |
| Supplier sign-in | Supplier pages send a signed-out request to `/supplier/login`; an office user gets 403 there and a supplier is sent to the Supplier Hub from office pages. | `test_supplier_hub.py`, `test_security_route_sweep.py` | Live |
| Inactivity sign-out | Office and supplier accounts are signed out after **30 minutes without activity**, measured from the last request or keep-alive, never from sign-in. A warning appears 2 minutes before ("Still there?", countdown, Stay signed in); typing or tapping counts as activity; what was typed in a form is put back after signing in again (same person, same browser tab only). | `test_session_idle_timeout.py` (13), `test_session_idle_timeout_browser.py` (desktop + 390 px) | **Unreleased** |
| Session cookies (hosted) | Secure, HttpOnly, SameSite=Lax; the session ends when the browser closes. | `test_hosted_production_config.py` | Live |
| Password recovery | Single-use, expiring reset links; the same reply for known and unknown emails; resetting ends other sessions. | `test_account_recovery_*` | Live |
| Owner recovery | `flask auth reset-password --email joel@braymanconstruction.ca` in the Render shell. | `test_auth_fg018.py` | Live |
| UAT sign-in bypass | Switched off 15 Oct 2026. **Code removed** on the security branch: setting the old variable does nothing; change-password always asks for the current password. No replacement. | `test_auth_bypass_removed.py` | Off live; code removal **unreleased** |

## Data separation

| Control | Tests | Status |
|---|---|---|
| Organization isolation (projects, estimates, proposals, contracts, documents, drawings) | `test_auth_fg018.py`, `test_organization_foundation.py`, `test_security_contract_download.py`, … | Live |
| Contractor-to-contractor and supplier-to-supplier isolation; supplier write isolation (25 actions) | `test_supplier_hub.py`, `test_security_supplier_write_isolation.py` | Live |
| Supplier quote privacy; no contractor prices or margins on supplier pages | `test_supplier_hub.py`, `test_security_supplier_write_isolation.py` | Live |
| Delivery notices go only to that order's people; `TRANSACTIONAL_UAT_ALLOWLIST` limits outgoing mail | `test_supplier_hub.py`, `test_account_recovery_auth_d_fg034.py` | Live |
| Cal is read-only and organization-scoped | `test_cal_find_it.py` | Live |

## Stored documents

| Control | Behaviour | Tests | Status |
|---|---|---|---|
| Signed-file integrity | Every read of a stored signing file is checked against its recorded SHA-256; an altered file is never served or repaired. | `test_native_signing_sign_a_fg033.py`, `test_security_signing_artifacts_missing.py` | Live |
| Missing or altered stored file | The customer sees "This document is not available." (nothing shown, nothing signed or changed); the office sees a plain message on the request or Contract page. Before the correction this was the generic error page; no bytes were ever served. | `test_security_signing_artifacts_missing.py`, `test_security_contract_download.py` | **Unreleased** |
| September signing files | 19 synthetic records on the live database have no file on the live disk; see [../operations/signing-artifact-inventory.md](../operations/signing-artifact-inventory.md). | `test_restore_september_signing_files.py` | Plan prepared, not run |

## Build and release

| Control | Status |
|---|---|
| Production packages pinned to the verified set (`requirements.txt` + `requirements-lock.txt`, Python 3.9.6) — `test_dependency_pins.py` | **Unreleased** |
| Release gate stops at READY_FOR_PUSH; separate authorization; no skipped test allowed — `test_release_tools.py`, [../operations/release-procedure.md](../operations/release-procedure.md) | In the repository (cleanup branch) |

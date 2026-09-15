# FG-034 AUTH-B responsive Forgot Password / Reset UX record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-15 |
| Gate | [FG-034](../feature-gates/FG-034-account-recovery-and-transactional-email.md) **OPEN / PARTIAL** |
| Slice | AUTH-B **IMPLEMENTED / PASS** |
| Alembic | **None.** Live current remains **`f2a3b4c5d6e7 (head)`** |

## Scope

Responsive office Account Recovery browser UX on the AUTH-A / MAIL-A foundation. Local/fake `PASSWORD_RESET` capture only. No live Postmark HTTP. No Native Signing mail. Physical iPhone Account Recovery UAT **DEFERRED** — **NOT CLAIMED AS PASS**.

## Product surfaces

| Route | Result |
|--------|--------|
| `GET /login` | Forgot Password? on the login card |
| `GET/POST /forgot-password` | Email-only request; CSRF; AUTH-A `request_password_reset` |
| `GET /forgot-password/sent` | Generic non-enumerating confirmation |
| `GET/POST /reset-password/<lookup>.<secret>` | AUTH-A validate/complete; 8-character floor; CSRF |
| `GET /reset-password/complete` | Password Updated; Return to Sign In; no auto-login |

One HTML/CSS system. Desktop card max-width **420px**. Mobile CSS **44px / 48px** touch targets. No device-specific routes or templates.

## Public route boundary

Office login-wall exemptions are limited to `auth.forgot_password`, `auth.forgot_password_sent`, `auth.reset_password`, and `auth.reset_password_complete`. They are **not** merged with `/sign/*`. Unauthenticated `/clients` still redirects to `/login`. Fake `/sign/...` remains **404** (not office login).

## Local / synthetic UAT

Dedicated synthetic user **`authb-uat@example.invalid`** (user id **6**). Not Joel’s protected production identity. EST-2026-0019 **not** used.

| Step | Result |
|------|--------|
| Forgot request | Generic confirmation for known email |
| MAIL-A capture | `instance/mail_capture/*PASSWORD_RESET.txt`; `PUBLIC_BASE_URL` reset path |
| Reset form | Set New Password; new + confirm |
| Success | Password Updated; no auto-login |
| Old password | Fails |
| New password | Authenticates; office home loads |
| `credentials_epoch` | **2** after service UAT then browser UAT |
| Second pre-reset session | Invalidated after epoch bump (service UAT) |
| EST-2026-0019 | Draft / unchanged |
| PRODUCTION packages | **0** |

Password for the retained synthetic user was rotated during AUTH-B UAT. Operators may CLI-reset that account; the password is not published here.

## Automated product validation

Dedicated `tests/test_account_recovery_auth_b_fg034.py`: **12 passed**. Focused AUTH-B + MAIL-A/AUTH-A + FG-018 + SIGN-A–E + FG-028 identity **167 passed**, 325 warnings, **92.58s**. Full suite **1021 passed**, 3300 warnings, **394.93s**, exit **0**.

## Explicitly not claimed

- Physical iPhone Account Recovery UAT PASS
- Postmark production delivery
- AUTH-C complete delivery E2E close
- Native Signing invitation email (MAIL-B)
- V1 rescore

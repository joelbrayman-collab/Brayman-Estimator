# FG-034 AUTH-C complete Account Recovery E2E record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-15 |
| Gate | [FG-034](../feature-gates/FG-034-account-recovery-and-transactional-email.md) **OPEN / PARTIAL** |
| Slice | AUTH-C **IMPLEMENTED / PASS** |
| Alembic | **None.** Live current remains **`f2a3b4c5d6e7 (head)`** |

## Scope

Prove MAIL-A + AUTH-A + AUTH-B as one Account Recovery product through local/fake transactional delivery. No live Postmark HTTP. No Native Signing mail. Physical iPhone Account Recovery UAT **DEFERRED** — **NOT CLAIMED AS PASS**.

## Bounded product correction

`app/services/transactional_email.py` records `FAILED` / `TRANSPORT_ERROR` when an injected transport raises, so a known-account Forgot Password request still returns the generic public confirmation and durable mail evidence.

## Positive E2E (synthetic)

Dedicated user **`authc-uat@example.invalid`** (user id **7**). Not Joel’s production identity. AUTH-B user `authb-uat@example.invalid` retained. EST-2026-0019 **not** used.

| Step | Result |
|------|--------|
| Login with current password | Two independent sessions authenticated |
| Forgot Password | Generic confirmation |
| MAIL-A capture | `PASSWORD_RESET` / `LOCAL_CAPTURED`; 60-minute copy; `PUBLIC_BASE_URL` |
| Reset | Token consumed; `credentials_epoch` **1** |
| Prior sessions | 302 after epoch bump |
| Old password | Fails |
| New password | Office home loads |
| EST-2026-0019 | Estimate 28 Draft; version 34 Draft; 49872.94 / 56356.42 |
| Proposal 14 | Draft |
| PRODUCTION packages | **0** |

Password is not published. Live 127.0.0.1 was already in the AUTH-B rate-limit window; AUTH-C UAT used a distinct test client IP.

## Automated product validation

Dedicated `tests/test_account_recovery_auth_c_fg034.py`: **10 passed**. Focused AUTH-C + AUTH-B + MAIL-A/AUTH-A + FG-018 + SIGN-A–E **164 passed**, 318 warnings, **96.83s**. Full suite **1031 passed**, 3300 warnings, **395.54s**, exit **0**.

## Explicitly not claimed

- Physical iPhone Account Recovery UAT PASS
- Postmark production delivery
- MAIL-B Native Signing mail
- AUTH-D close
- V1 rescore

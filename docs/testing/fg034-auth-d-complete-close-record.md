# FG-034 AUTH-D complete Account Recovery + transactional email close record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-15 |
| Gate | [FG-034](../feature-gates/FG-034-account-recovery-and-transactional-email.md) **CLOSED / OPERATIONAL FOR UAT** |
| Slice | AUTH-D **IMPLEMENTED / PASS** |
| Alembic | **None.** Live current remains **`f2a3b4c5d6e7 (head)`** |

## Scope

Prove MAIL-A + AUTH-A + AUTH-B + AUTH-C + MAIL-B as one Account Recovery + transactional-email product. Activate the Postmark HTTP adapter contract. No live Postmark credentials were present. Physical iPhone Account Recovery UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT** — **NOT CLAIMED AS PASS**. Native Signing physical iPhone UAT remains **DEFERRED** — **NOT CLAIMED AS PASS**. FG-033 remains **CLOSED**. V1 **not rescored**.

## Bounded product

`PostmarkTransport` now calls `postmark_http_send` when `POSTMARK_SERVER_TOKEN` and sender exist. Tests inject `POSTMARK_URLOPEN` or `POSTMARK_HTTP_SEND`. Missing token remains `FAILED_CONFIG` / `POSTMARK_CONFIG`. Status is never `DELIVERED`. Secrets are not stored on `transactional_messages` rows.

## Postmark configuration inspected (no secrets printed)

| Setting | Result |
|---------|--------|
| `TRANSACTIONAL_EMAIL_PROVIDER` | unset / default **local** |
| `POSTMARK_SERVER_TOKEN` | **UNSET** |
| `TRANSACTIONAL_FROM_EMAIL` | default only (`noreply@localhost`) — not a production sender |
| `TRANSACTIONAL_UAT_ALLOWLIST` | **UNSET** |
| `.env` | `SECRET_KEY` only; no Postmark keys |

**LIVE POSTMARK DELIVERY: DEFERRED — PROVIDER CONFIGURATION REQUIRED. NOT CLAIMED AS PASS.**

## Positive E2E (synthetic live, local/fake)

Dedicated user **`authd-uat@example.invalid`** (user id **9**). Change Order **id 19** `FG034-UAT AUTH-D SYNTHETIC CO`. Request **`SIGN-2026-0014`** **EXECUTED**. Not Joel’s production identity. EST-2026-0019 **not** used.

| Step | Result |
|------|--------|
| Login with current password | Authenticated |
| Forgot Password | Generic confirmation |
| MAIL-A capture | `PASSWORD_RESET` / `LOCAL_CAPTURED` |
| Reset | Token consumed; `credentials_epoch` **1** |
| Prior session | 302 after epoch bump |
| Old password | Fails |
| New password | Office home loads |
| CO invitation | SENT; `SIGNING_INVITATION` / `LOCAL_CAPTURED` |
| Resend | Old token invalid; `SIGNING_RESEND` / `LOCAL_CAPTURED` |
| Complete | EXECUTED; `SIGNING_COMPLETE` / `LOCAL_CAPTURED` |
| EST-2026-0019 | Estimate 28 Draft; version 34 Draft; 49872.94 / 56356.42 |
| Proposal 14 | Draft |
| PRODUCTION packages | **0** |
| `instance/` | gitignored; capture files private |

Password and raw secrets are not published.

## Automated product validation

Dedicated `tests/test_account_recovery_auth_d_fg034.py`: **12 passed**. Focused AUTH-D + MAIL-A/AUTH-A + AUTH-B + AUTH-C + MAIL-B + FG-018 + SIGN-A–E **185 passed**, 356 warnings, **117.94s**, exit **0**. Full suite **1052 passed**, 3338 warnings, **434.60s**, exit **0**.

## Explicitly not claimed

- Physical iPhone Account Recovery UAT PASS
- Physical Native Signing iPhone UAT PASS
- Live Postmark / production sender-domain delivery
- V1 rescore
- Time / Schedule / MONITOR / LEARN / Extra Work / Closeout / language audit

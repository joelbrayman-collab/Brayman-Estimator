# FG-034 MAIL-B Native Signing transactional delivery record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-15 |
| Gate | [FG-034](../feature-gates/FG-034-account-recovery-and-transactional-email.md) **OPEN / PARTIAL** |
| Slice | MAIL-B **IMPLEMENTED / PASS** |
| Alembic | **None.** Live current remains **`f2a3b4c5d6e7 (head)`** |

## Scope

Connect Native Signing invitation / resend / complete to the existing MAIL-A engine. Same `/sign` credential. Copyable URL retained. SENT remains invitation-issued, not mail delivered. No live Postmark HTTP. No new Alembic. FG-033 remains **CLOSED**. Physical iPhone UAT **DEFERRED** — **NOT CLAIMED AS PASS**.

## Bounded product

`app/services/signing_mail.py` is the Signing consumer of MAIL-A. Invitation mail uses `PUBLIC_BASE_URL` + existing `/sign/<lookup>.<secret>`. `TransactionalMessage` is delivery authority. Signing events are unchanged (CHECK constraint cannot add `INVITATION_EMAIL_*` without a migration). Mail failure after commit does not roll back SENT / EXECUTED.

Office contractor copy: **Email captured for testing** / **Email accepted for delivery** / **Email not sent** / **Email configuration missing**. Never **Delivered**.

## Positive E2E (synthetic live)

Dedicated user **`mailb-uat@example.invalid`** (user id **8**). Change Order **id 18** `FG034-UAT MAIL-B SYNTHETIC CO`. Request **`SIGN-2026-0013`** **EXECUTED**. Not Joel’s production identity. EST-2026-0019 **not** used.

| Step | Result |
|------|--------|
| Issue invitation | SENT; `SIGNING_INVITATION` / `LOCAL_CAPTURED`; capture URL uses `PUBLIC_BASE_URL` + same `/sign` credential |
| Office CO detail | `data-signing-email-delivery` = Email captured for testing. No Delivered |
| Resend | New credential; old URL `TOKEN_INVALID`; `SIGNING_RESEND` / `LOCAL_CAPTURED` |
| Customer sign (no countersign) | EXECUTED; `SIGNING_COMPLETE` / `LOCAL_CAPTURED`; no new signing URL; no PDF attachment |
| Forgot Password / `/sign` | Public Forgot Password 200; login still has Forgot Password; `/sign` remains public |
| EST-2026-0019 | Estimate 28 Draft; version 34 Draft; 49872.94 / 56356.42 |
| Proposal 14 | Draft |
| PRODUCTION packages | **0** |
| `instance/` | gitignored; capture files private |

Live contract invitation on an existing generated contract was **not** issued: LibreOffice converter **UNAVAILABLE** on this machine (`CONVERTER_UNAVAILABLE`). Dedicated MAIL-B tests prove contract invitation uses the same MAIL-A engine and `/sign` credential. Existing live `SIGN-2026-0002` remains `APPROVED_FOR_SIGNATURE` (historical SIGN-A).

## Automated product validation

Dedicated `tests/test_signing_mail_b_fg034.py`: **9 passed**. Focused MAIL-B + MAIL-A/AUTH-A + AUTH-B + AUTH-C + FG-018 + SIGN-A–E **173 passed**, 338 warnings, **107.18s**, exit **0**. Full suite **1040 passed**, 3320 warnings, **376.12s**, exit **0**.

## Explicitly not claimed

- Physical iPhone UAT PASS
- Postmark production delivery
- AUTH-D close
- FG-034 gate close
- V1 rescore
- Live contract invitation on this machine (converter unavailable; automated contract path PASS)

# FG-034 MAIL-A / AUTH-A live bounded UAT record

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-15 |
| Gate | [FG-034](../feature-gates/FG-034-account-recovery-and-transactional-email.md) **OPEN / PARTIAL** |
| Slices | MAIL-A **IMPLEMENTED**. AUTH-A **IMPLEMENTED**. AUTH-B/C, MAIL-B, AUTH-D **not** this record |
| Alembic | **`f2a3b4c5d6e7`** (parent `e0f1a2b3c4d5`) applied live |

## Scope

Service-layer transactional email (local/fake; no live Postmark HTTP) and Account Recovery security foundation. No Forgot Password pages. No Native Signing mail integration.

## Git / Alembic

| Field | Value |
|--------|--------|
| Parent HEAD | SIGN-E **`3062c67ce3706b4341394d05c3eddb4df9b54c22`** |
| Live current after migrate | **`f2a3b4c5d6e7 (head)`** |
| Upgrade | `e0f1a2b3c4d5` → **`f2a3b4c5d6e7`** |
| Backup | `instance/brayman_estimator-backup-before-fg034-mail-a-auth-a-20260915.db` |

## Protected occupancy (before and after)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft |
| Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |
| PRODUCTION packages | **0** |
| Signing requests | SIGN-2026-0001 through SIGN-2026-0012 unchanged |
| Live users `credentials_epoch` | **0** (all existing users) |

Unchanged. EST-2026-0019 was not used for reset, mail, or identity mutation. PRODUCTION Ontario packages remain **0**. New tables `password_reset_tokens`, `password_reset_access_attempts`, and `transactional_messages` are empty on the live DB after migrate.

## Session identity after migrate

Legacy Flask-Login identities storing only `"<user_id>"` are accepted as `credentials_epoch` **0**. Existing live office sessions remain valid until a password reset bumps the epoch. After epoch ≥ 1, a legacy bare id fails closed.

## Automated product validation

Dedicated `tests/test_account_recovery_mail_a_auth_a_fg034.py`: **28 passed**. Focused MAIL-A/AUTH-A + FG-018 + SIGN-A–E **142 passed**, 308 warnings, **77.71s**. Full suite **1009 passed**, 3290 warnings, **344.09s**, exit **0**.

## Explicitly not claimed

- Physical iPhone Account Recovery UAT PASS
- Postmark production delivery
- Complete Forgot Password web flow (AUTH-B/C)
- Native Signing invitation email (MAIL-B)

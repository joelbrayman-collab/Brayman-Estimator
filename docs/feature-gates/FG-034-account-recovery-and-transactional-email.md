# Feature Gate FG-034: Account Recovery and Transactional Email V1

| Attribute | Value |
|----------|--------|
| Feature Gate ID | `FG-034` |
| Feature Name | Account Recovery and Transactional Email V1 |
| Target Milestone | **V1-10** (account recovery / mail secrets) and **V1-07** (transactional delivery for Native Signing). Not a 12th major V1 package. Does **not** rescore V1. |
| Module | **Organization / office identity** owns User password reset tokens, `credentials_epoch`, and reset access attempts. **Platform** owns the shared transactional-email service and `transactional_messages`. Signing **consumes** mail later (MAIL-B); it does **not** own mail. |
| Date | 2026-09-15 |
| Status | **OPEN / PARTIAL.** MAIL-A **IMPLEMENTED**. AUTH-A **IMPLEMENTED**. AUTH-B **IMPLEMENTED / PASS**. AUTH-C **NOT STARTED**. MAIL-B **NOT STARTED**. AUTH-D **NOT STARTED**. |
| Architecture | [ADR-052](../adr/ADR-052-account-recovery-and-transactional-email.md) **Accepted**. Supersedes [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) Decision 7’s CLI-only / no-mail V1 boundary **without rewriting ADR-041 historically**. [FG-018](FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED** (not reopened). [FG-033](FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED** (not reopened). [FG-021](FG-021-field-web-v1-today-and-capture.md) SESSION-EXPIRY RECOVERY remains **DEFERRED** and is a different problem. |
| Related ADRs | [ADR-052](../adr/ADR-052-account-recovery-and-transactional-email.md) **Accepted**. [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [ADR-045](../adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted** (CalibraytAI mail identity). |
| Prerequisites | FG-018 office Users / membership **CLOSED**. FG-033 Native Signing **CLOSED / OPERATIONAL FOR UAT**. Production sender domain / Postmark token **not** required for MAIL-A / AUTH-A. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / PARTIAL** |
| MAIL-A | **IMPLEMENTED** — transactional message record, local/fake transport, Postmark adapter boundary, no live network send |
| AUTH-A | **IMPLEMENTED** — `credentials_epoch`, reset tokens hash-at-rest, rate limits, 8-character new-password floor, CLI epoch bump |
| AUTH-B | **IMPLEMENTED / PASS** — responsive Forgot Password / Reset UX |
| AUTH-C | **NOT STARTED** — complete password-reset delivery E2E via public routes |
| MAIL-B | **NOT STARTED** — Native Signing invitation/resend/complete through this engine |
| AUTH-D | **NOT STARTED** — desktop/mobile automated close + Postmark UAT |
| Schema / Alembic | Additive MAIL-A/AUTH-A **`f2a3b4c5d6e7`** revises **`e0f1a2b3c4d5`** |
| V1 scoring | **NOT RESCORED** (**60% / 4 of 11**) |

```text
FG-034:
OPEN / PARTIAL
MAIL-A IMPLEMENTED
AUTH-A IMPLEMENTED
AUTH-B IMPLEMENTED / PASS
AUTH-C NOT STARTED
MAIL-B NOT STARTED
AUTH-D NOT STARTED
ONE TRANSACTIONAL EMAIL ENGINE
DEFAULT PROVIDER POSTMARK (NOT ACTIVATED THIS SLICE)
LOCAL / FAKE TRANSPORT ONLY IN MAIL-A
PASSWORD RESET TTL 60 MINUTES
CREDENTIALS_EPOCH SESSION INVALIDATION
CLI RESET RETAINED
8-CHARACTER MINIMUM FOR NEWLY SET / RESET PASSWORDS
DESKTOP + IPHONE / MOBILE (AUTH-B/D)
PHYSICAL IPHONE UAT DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT
NOT CLAIMED AS PASS
FG-033 NOT REOPENED
FG-021 NOT REOPENED
V1 NOT RESCORED
```

---

## Purpose

Provide **complete** office Account Recovery:

LOGIN → Forgot Password → email request → transactional reset message → secure link → responsive reset page → new password + confirm → password changed → token consumed → sessions invalidated → login with new password.

Provide **one** transactional-email engine for:

- `PASSWORD_RESET`
- `SIGNING_INVITATION`
- `SIGNING_RESEND`
- `SIGNING_COMPLETE`

Do not build a second mail system. Do not treat a token service as the complete product. The gate does **not** close until the complete flow works, including later AUTH-B/C/D and MAIL-B.

---

## Feature Gate answers

| # | Question | Answer |
|---|---------|--------|
| 1 | What problem does this solve? | Operators cannot recover a forgotten office password except via CLI. Native Signing still depends on a copyable URL for real-customer send. There is no outbound transactional mail. |
| 2 | Who is the user? | Office User (email login). Customer signing recipients for MAIL-B (no CalibraytAI account). Not marketing subscribers. |
| 3 | Which module owns it? | Organization/identity owns reset tokens and `credentials_epoch`. Platform owns `app/services/transactional_email.py`. Signing consumes mail in MAIL-B only. |
| 4 | What data does it own? | `users.credentials_epoch`; `password_reset_tokens`; `password_reset_access_attempts`; `transactional_messages`; gitignored `instance/mail_capture/`. |
| 5 | What data does it reference? | `User`, `UserMembership`, later Signing request identity as `related_type`/`related_id` only. |
| 6 | What may it change? | Auth password-setting paths (8-character floor for **new** passwords); Flask-Login identity format; CLI reset epoch bump; mail config. |
| 7 | What must it not change? | FG-033 `/sign` ceremony; EST-2026-0019; PRODUCTION legal packages; FG-021 SESSION-EXPIRY; Time / MONITOR / LEARN; inventing RBAC or SSO. |
| 8 | What are the acceptance criteria? | Complete workstream in §Complete workstream slices. MAIL-A/AUTH-A close when service tests pass and live migrate is applied. Full gate close requires AUTH-B through AUTH-D. |
| 9 | What tests are required? | Dedicated MAIL-A/AUTH-A tests this slice; later public UX/E2E/responsive/Postmark tests; FG-018 and SIGN-A–E regression; full suite. |
| 10 | What documentation must be updated? | This gate; ADR-052; ADR-041 subsequent status; indexes; current-state; session-handoff; chat-workflow-log; milestones; project-state-report; v1-completion-register (no rescore). |
| 11 | Does it require an ADR? | **Yes.** ADR-052. External mail provider + supersession of ADR-041 Decision 7. |
| 12 | Does it require a database migration? | **Yes.** One additive revision **`f2a3b4c5d6e7`** (MAIL-A/AUTH-A). |

---

## Product decisions (Joel / Architect, 15 Sep 2026)

| Decision | V1 rule |
|----------|--------|
| Feature Gate | FG-034 covers Account Recovery **and** transactional email as one workstream |
| Provider | **Postmark** default. MAIL-A does not send live HTTP |
| Reset TTL | **60 minutes** (`PASSWORD_RESET_TOKEN_TTL_SECONDS=3600`) |
| Session invalidation | `users.credentials_epoch`; Flask-Login identity `id:epoch` |
| Legacy sessions | Bare `"<user_id>"` is accepted as **epoch 0** so migrate does not log everyone out |
| CLI reset | **Retained**; uses 8-character validator; bumps epoch |
| New password floor | **8 characters**. No composition alphabet. Historical shorter hashes still authenticate until changed |
| Templates | `PASSWORD_RESET`, `SIGNING_INVITATION`, `SIGNING_RESEND`, `SIGNING_COMPLETE` |
| Physical iPhone UAT | **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT**. Not PASS. Automated responsive tests remain required in AUTH-B/D |
| Sender domain | Not required to begin MAIL-A / AUTH-A |

---

## Complete workstream slices

Later slices are **not** authorized merely because this Feature Gate exists.

### MAIL-A — Transactional message foundation

**Status: IMPLEMENTED (this prompt).**

Typed templates. Local capture + injected fake provider. Postmark adapter boundary (`FAILED_CONFIG` without token; HTTP hook not activated). No network. Statuses include `LOCAL_CAPTURED` / `ACCEPTED` / `FAILED` / `SKIPPED_ALLOWLIST` / `FAILED_CONFIG`. Never claim `DELIVERED`. Secrets not stored on message rows.

**STOP:** no Forgot Password pages; no Postmark account; no Signing office delivery UX.

### AUTH-A — Token / session / password-policy foundation

**Status: IMPLEMENTED (this prompt).**

`credentials_epoch`; hash-at-rest reset tokens; request and presentation rate limits; generic `request_password_reset`; `validate_password_reset_credential`; `complete_password_reset`; CLI epoch bump; 8-character `validate_new_password`. No browser routes.

**STOP:** no AUTH-B templates/CSS/routes.

### AUTH-B — Responsive Forgot Password / Reset UX

**Status: IMPLEMENTED / PASS (this prompt).**

One responsive implementation. Desktop + iPhone. No device-specific forks. Forgot Password on login; generic confirmation; reset form; 8-character floor; CSRF; AUTH-A integration; local/fake MAIL-A only. Physical iPhone Account Recovery UAT **DEFERRED** — **NOT CLAIMED AS PASS**. Evidence [testing/fg034-auth-b-responsive-forgot-reset-ux-record.md](../testing/fg034-auth-b-responsive-forgot-reset-ux-record.md).

**STOP:** no AUTH-C delivery-E2E close; no Postmark; no MAIL-B.

### AUTH-C — Complete password-reset delivery E2E

**Status: NOT STARTED.**

Public generic confirmation; token consume; login with new password.

### MAIL-B — Native Signing transactional integration

**Status: NOT STARTED.**

Same engine. Existing `/sign` ceremony unchanged. Copyable URL retained. Do not mark SENT as delivered merely because a token exists.

### AUTH-D — Complete desktop/mobile/UAT close

**Status: NOT STARTED.**

Automated viewport assertions. One real allowlisted Postmark send. Physical iPhone **DEFERRED**, not PASS. Gate close only when complete functionality works.

---

## Security (this slice)

- Reset secret: `secrets.token_urlsafe(32)`; SHA-256 at rest; lookup `token_urlsafe(16)`
- Unknown / inactive emails: no token, no message; same public result object
- Rate limits: 5/3600s per IP; 3/3600s per email-hash; 8 fails / 900s per IP on token presentation
- Raw unknown email not stored on attempt rows (hash only)
- Never log/store password or raw secret
- `PUBLIC_BASE_URL` for future email links; local/TESTING may use `http://localhost`

---

## Production boundary

```text
MAIL-A / AUTH-A / AUTH-B: LOCAL / FAKE ONLY.
POSTMARK HTTP: NOT ACTIVATED.
ACCOUNT RECOVERY WEB UX: AUTH-B IMPLEMENTED / PASS.
PHYSICAL IPHONE ACCOUNT RECOVERY UAT: DEFERRED / NOT PASS.
NATIVE SIGNING EMAIL: NOT THIS SLICE.
```

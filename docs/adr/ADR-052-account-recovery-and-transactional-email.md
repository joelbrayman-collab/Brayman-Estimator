# ADR-052 — Account Recovery and Transactional Email

| Field | Value |
|-------|--------|
| Title | ADR-052: Web Account Recovery, Shared Transactional Email, and Supersession of ADR-041 Decision 7’s CLI-only V1 Boundary |
| Status | **Accepted** (2026-09-15; Joel Brayman / ChatGPT Architect). MAIL-A / AUTH-A / AUTH-B / AUTH-C product implementation is authorized under [FG-034](../feature-gates/FG-034-account-recovery-and-transactional-email.md). MAIL-B / AUTH-D remain unauthorized until later bounded prompts. |
| Date | 2026-09-15 |
| Related | [ADR-041](ADR-041-user-membership-and-office-authentication.md) **Accepted** (Decision 7 historically CLI-only; **superseded for V1 product scope by this ADR**, not rewritten) · [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED** (SESSION-EXPIRY RECOVERY **DEFERRED**; not this ADR) · [ADR-045](ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted** |

---

## Context

ADR-041 Decision 7 recorded V1 password recovery as **CLI / operator reset only**, with **no password-reset email and no mail infrastructure**. That was correct when FG-018 closed: the repository had no outbound mail and Native Signing had not shipped.

Joel identified Forgot Password as a Production V1 capability during UAT. Native Signing (FG-033) remains **CLOSED / OPERATIONAL FOR UAT** but still uses a copyable invitation URL for technical UAT. Real-customer send needs transactional delivery. Building a second mail system for signing would violate complete-functionality design.

Constitution Article 8 requires an ADR: external system integration (Postmark), session-invalidation schema, and a material supersession of an Accepted ADR’s V1 boundary.

This ADR does **not** rewrite ADR-041’s historical Decision 7 text.

---

## Decision

**Accepted.**

### 1. Production V1 includes web Account Recovery

The intended user flow is complete:

LOGIN → Forgot Password → enter email → generic confirmation → transactional reset message → secure reset link → responsive reset page → new password + confirm → password updated → token consumed → confirmation → login with new password.

CLI `flask auth reset-password` is **retained** as operator break-glass. It is not the public product.

### 2. One shared transactional-email service

One engine owns delivery. Typed V1 templates:

- `PASSWORD_RESET`
- `SIGNING_INVITATION`
- `SIGNING_RESEND`
- `SIGNING_COMPLETE`

Password-reset logic does not live inside the mail service. Signing lifecycle logic does not live inside the mail service. There is **no** marketing/list/subscriber product.

### 3. Default production provider is Postmark

Do not build SMTP. Development/TESTING uses local capture or an injected fake transport. Live Postmark HTTP is activated in AUTH-D after credentials exist. MAIL-A persists `FAILED_CONFIG` when `provider=postmark` but the token/from-address is missing, without crashing the application.

### 4. Password-reset tokens are not Signing domain records

Reuse SIGN-B **security patterns** (lookup + high-entropy secret, SHA-256 hash-at-rest, single-use, expiry, IP rate limits). Do **not** store reset tokens on `SigningParticipant` / `SigningRequest`.

TTL: **60 minutes** (`PASSWORD_RESET_TOKEN_TTL_SECONDS`, default 3600).

### 5. Session invalidation via `credentials_epoch`

`users.credentials_epoch` Integer NOT NULL default 0. Flask-Login `get_id()` is `user_id:epoch`. `user_loader` requires an active user and matching epoch.

Legacy sessions that store only `"<user_id>"` are accepted as **epoch 0** so live migrate does not force an authentication outage. After a password reset, epoch ≥ 1 and a legacy id fails closed.

Successful web reset and CLI reset bump the epoch. No session-store table. This does **not** implement FG-021 Field Web SESSION-EXPIRY recovery.

### 6. Password policy for newly set / reset passwords

One `validate_new_password` path. Minimum **8 characters**. No required uppercase/lowercase/number/symbol alphabet. Existing shorter hashes remain valid for **login** until the user sets a new password through a governed path (web reset, CLI reset, bootstrap).

### 7. Enumeration resistance

Public reset request does not disclose whether an email belongs to an account, nor active/inactive, membership, or organization. Unknown and inactive are treated as no-token / no-message. Rate limits apply to known and unknown the same way. Operator CLI may still say User not found.

### 8. Desktop + iPhone / mobile

One responsive auth experience. No device-specific forks. Physical iPhone Account Recovery UAT is **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT** and is **not** claimed as PASS. Automated viewport assertions remain required before FG-034 close.

---

## Alternatives Considered

- **Keep CLI-only recovery** — Rejected: Joel’s Production V1 complete-functionality direction.
- **Magic-link login instead of password reset** — Rejected: V1 remains email + password (ADR-041 Decision 5).
- **Amazon SES or SendGrid as default** — Rejected as default: more ops (SES) or marketing-platform residue (SendGrid). Postmark is transactional-first.
- **Store reset tokens on SigningParticipant** — Rejected: couples unrelated domains.
- **Idle-timeout / session table** — Rejected for this ADR: smallest mechanism is `credentials_epoch`.
- **Reopen FG-018 or FG-033** — Rejected: new gate FG-034.

---

## Consequences

**Positive:** Operators can recover passwords; Native Signing can later send through the same engine; session theft after reset is mitigated; ADR-041 history preserved.

**Negative:** Live Postmark, sender domain, MAIL-B Native Signing mail, and AUTH-D remain required before the gate closes. AUTH-C local E2E is implemented; MAIL-B Native Signing mail is not.

## Module Ownership Impact

- Organization / identity: `User.credentials_epoch`, `password_reset_tokens`, `password_reset_access_attempts`.
- Platform: transactional email service and `transactional_messages`.
- Signing: consumer in MAIL-B only; ceremony ownership unchanged.

## Data Ownership Impact

Reset tokens bound to `user_id`. Message rows may reference `related_type` / `related_id` without owning Signing records. Capture files under gitignored `instance/mail_capture/`.

## Migration Impact

**Required** for MAIL-A/AUTH-A: additive Alembic **`f2a3b4c5d6e7`** (parent `e0f1a2b3c4d5`). Existing users receive `credentials_epoch = 0`.

## Testing Impact

Dedicated MAIL-A/AUTH-A tests; FG-018 login regression; SIGN-A–E regression; migration upgrade/downgrade; full suite before close of later slices.

## Documentation Impact

FG-034; this ADR; ADR-041 subsequent status; indexes; current-state; session-handoff; chat-workflow-log; milestones; project-state-report; v1-completion-register (no rescore).

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Accepted via governed MAIL-A / AUTH-A prompt | 2026-09-15 |
| ChatGPT review | Account Recovery + Transactional Email preflight accepted | 2026-09-15 |
| Cursor implementation note | MAIL-A / AUTH-A implemented this pass. AUTH-B/C/MAIL-B/AUTH-D not authorized. | 2026-09-15 |

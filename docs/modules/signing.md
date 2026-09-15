# Module — Signing Service

| Attribute | Value |
|-----------|--------|
| Status | **Current.** [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED / OPERATIONAL FOR UAT**. SIGN-A **IMPLEMENTED**. SIGN-B **IMPLEMENTED**. SIGN-C **IMPLEMENTED**. SIGN-D **IMPLEMENTED** (automated). SIGN-E **IMPLEMENTED**. Native Signing functional target: **desktop + iPhone / mobile** on one responsive ceremony. Real iPhone UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT** — **NOT CLAIMED AS PASS**. Production / real-customer Native Signing **NOT COMPLETE**. No external-review dependency in the development workflow. |
| Updated | 2026-09-15 |
| Code | `app/models/signing.py`, `app/services/signing.py`, `app/services/signing_artifact_storage.py`, `app/services/signing_executed_pdf.py`, `app/services/signing_docx_pdf.py`, `app/cli/signing.py`, `app/routes/sign.py`, `app/routes/signing.py`, `app/templates/signing/`, `app/static/css/signing.css` |
| Feature Gate | [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) |
| Architecture | [contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md) |

## Purpose

Native Signing is an **overlay**. It freezes a signable artifact and records a governed signing request. It does **not** own Change Order commercial records or generated-contract commercial identity.

## SIGN-A

- Request identity `SIGN-YYYY-NNNN`
- Change Order: freeze current governed ReportLab PDF once into private `instance/signing_artifacts/<org>/<sha>.pdf`
- Generated contract: bind retained TECH-C DOCX + SHA-256 + Family 05 provenance; convert-once PDF is SIGN-E
- Participants: `CUSTOMER` plus optional `ORGANIZATION_COUNTERSIGN` foundation
- Consent version pin (`CONSENT-SYNTHETIC-UAT-001` seeded for SYNTHETIC_UAT)
- HUMAN office create + APPROVED_FOR_SIGNATURE
- AI / AUTOMATION **BLOCK**
- Append-only `REQUEST_CREATED` / `APPROVED_FOR_SIGNATURE`
- Authority `SYNTHETIC_UAT` / `PRODUCTION`

## SIGN-B

- Secure invitation: `secrets.token_urlsafe` lookup + secret; SHA-256 hash-at-rest; raw secret shown once
- URL `/sign/<lookup_key>.<secret>`
- No customer User / password / login
- Narrow public `/sign/*` login exemption; office login wall otherwise unchanged
- Expiry enforced from the request pin; completed token cannot sign again
- Presentation rate limit (`signing_token_access_attempts`; default 8 fails / 900s)
- Frozen Change Order PDF review/download; live CO mutation does not change reviewed bytes
- Contract customer PDF is SIGN-E convert-once; historical DOCX freeze remains `CONTRACT_PDF_NOT_AVAILABLE`
- Pinned consent version; explicit accept; typed-name SIGN & ACCEPT
- CSRF on public SIGN & ACCEPT
- Evidence: confirmed name, UTC `signed_at`, completion IP, basic user-agent, artifact SHA
- Status `APPROVED_FOR_SIGNATURE` → `SENT` → `SIGNED`
- Events `SENT` / `VIEWED` / `CONSENT_ACCEPTED` / `SIGNED` (VIEWED is an event, not a status)
- If `countersign_required`: customer confirmation is SIGNED, awaiting organization countersignature
- iPhone-first standalone ceremony CSS; desktop `@media (min-width: 768px)` on the same sheet; no office chrome
- Office CLI `flask signing invite` returns one copyable URL
- RESEND is SIGN-C
- Additive Alembic **`c8d9e0f1a2b3`** (parent `b7c8d9e0f1a2`)

## SIGN-C (current)

- SIGNED + `countersign_required=true`: active org HUMAN countersigns; COUNTERSIGNED event; executed PDF assembled; EXECUTED
- SIGNED + `countersign_required=false`: executed PDF assembled without a second signature ceremony
- Executed PDF = immutable pre-sign PDF + completion/audit page (`pypdf`); commercial pages are not re-rendered
- Distinct private artifact `instance/signing_artifacts/<org>/<sha>.pdf`; SHA-256 of exact retained bytes
- Request becomes EXECUTED only after custody succeeds; custody failure leaves SIGNED
- RESEND rotates SENT token; old secret fail-closed; same frozen artifact and consent
- VOID (CREATED / APPROVED_FOR_SIGNATURE / SENT / SIGNED) requires reason; terminal; token invalid; EXECUTED cannot be voided in place
- EXPIRE when `expires_at` passed and not yet SIGNED/EXECUTED; EXPIRED once
- Customer DECLINE from SENT; no signature evidence; no executed artifact
- Customer completed-link can download executed PDF; office GET `/signing-requests/<id>/executed`
- Events COUNTERSIGNED / EXECUTED / RESENT / VOIDED / EXPIRED / DECLINED
- Additive Alembic **`d9e0f1a2b3c4`** (parent `c8d9e0f1a2b3`)

## Owned data

- `signing_consent_versions`
- `signing_frozen_artifacts` (SIGN-E converter provenance nullable)
- `signing_requests`
- `signing_participants` (token hash-at-rest + SIGN-B evidence columns)
- `signing_events`
- `signing_token_access_attempts` (never stores raw secrets)
- `signing_executed_artifacts`

Private bytes: `instance/signing_artifacts/` (gitignored).

## Prohibited

- Transactional email
- ReportLab / HTML Family 05 substitute
- Customer account registration
- Mutating `CHANGE_ORDER_STATUSES` or generated-contract `GENERATED`
- EST-2026-0019
- Inventing RBAC
- Legal-review approval states / fields
- Overwriting the pre-sign freeze
- Device-specific signing forks

## SIGN-D

- Office Send for Signature on Approved Change Orders
- Hub labels UNSIGNED / AWAITING SIGNATURE / SIGNED / EXECUTED
- Customer `/sign` name-first copy; responsive CSS; no office chrome
- Complete synthetic E2E: freeze → invite → SENT → customer sign → countersign → EXECUTED
- No-countersign auto-EXECUTED path
- VOID / RESEND / EXPIRE / DECLINE / replay / invalid token fail-closed
- Tenant isolation; public `/sign` exemption does not weaken office login
- Automated mobile markup/CSS/copy/state assertions
- Real iPhone UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT** — **NOT CLAIMED AS PASS**

## SIGN-E (current)

- Family 05 retained DOCX → LibreOffice/soffice **once** → retain PDF + converter provenance
- Missing converter **BLOCK**; failed conversion does not retain a PDF
- Same signing engine, request lifecycle, `/sign` routes, token, signature evidence, and audit for CONTRACT and CHANGE_ORDER
- Desktop + iPhone / mobile functional parity; one responsive ceremony; no device-specific forks
- PRODUCTION contract send **BLOCK** without ACTIVE PRODUCTION package
- Additive Alembic **`e0f1a2b3c4d5`** (parent `d9e0f1a2b3c4`)
- MAIL-B / AUTH-D Native Signing invitation/resend/complete through the FG-034 engine **IMPLEMENTED / PASS** (local/fake; SENT ≠ delivered; copyable URL retained; Postmark HTTP adapter activated; live Postmark **DEFERRED**)

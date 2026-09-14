# Module — Signing Service

| Attribute | Value |
|-----------|--------|
| Status | **Partial Current.** [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **OPEN / PARTIAL**. SIGN-A **IMPLEMENTED**. SIGN-B **IMPLEMENTED**. SIGN-C/D/E **NOT STARTED**. Production / real-customer Native Signing **NOT COMPLETE**. No external-review dependency in the development workflow. |
| Updated | 2026-09-14 |
| Code | `app/models/signing.py`, `app/services/signing.py`, `app/services/signing_artifact_storage.py`, `app/cli/signing.py`, `app/routes/sign.py`, `app/templates/signing/`, `app/static/css/signing.css` |
| Feature Gate | [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) |
| Architecture | [contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md) |

## Purpose

Native Signing is an **overlay**. It freezes a signable artifact and records a governed signing request. It does **not** own Change Order commercial records or generated-contract commercial identity.

## SIGN-A

- Request identity `SIGN-YYYY-NNNN`
- Change Order: freeze current governed ReportLab PDF once into private `instance/signing_artifacts/<org>/<sha>.pdf`
- Generated contract: bind retained TECH-C DOCX + SHA-256 + Family 05 provenance; **no** DOCX→PDF in SIGN-A
- Participants: `CUSTOMER` plus optional `ORGANIZATION_COUNTERSIGN` foundation
- Consent version pin (`CONSENT-SYNTHETIC-UAT-001` seeded for SYNTHETIC_UAT)
- HUMAN office create + APPROVED_FOR_SIGNATURE
- AI / AUTOMATION **BLOCK**
- Append-only `REQUEST_CREATED` / `APPROVED_FOR_SIGNATURE`
- Authority `SYNTHETIC_UAT` / `PRODUCTION`

## SIGN-B (current)

- Secure invitation: `secrets.token_urlsafe` lookup + secret; SHA-256 hash-at-rest; raw secret shown once
- URL `/sign/<lookup_key>.<secret>`
- No customer User / password / login
- Narrow public `/sign/*` login exemption; office login wall otherwise unchanged
- Expiry enforced from the request pin; completed token cannot sign again
- Presentation rate limit (`signing_token_access_attempts`; default 8 fails / 900s)
- Frozen Change Order PDF review/download; live CO mutation does not change reviewed bytes
- Contract customer PDF **BLOCK** (`CONTRACT_PDF_NOT_AVAILABLE`; SIGN-E)
- Pinned consent version; explicit accept; typed-name SIGN & ACCEPT
- CSRF on public SIGN & ACCEPT
- Evidence: confirmed name, UTC `signed_at`, completion IP, basic user-agent, artifact SHA
- Status `APPROVED_FOR_SIGNATURE` → `SENT` → `SIGNED`
- Events `SENT` / `VIEWED` / `CONSENT_ACCEPTED` / `SIGNED` (VIEWED is an event, not a status)
- If `countersign_required`: customer confirmation is SIGNED, awaiting organization countersignature
- iPhone-first standalone ceremony CSS; no office chrome
- Office CLI `flask signing invite` returns one copyable URL
- RESEND is SIGN-C
- Additive Alembic **`c8d9e0f1a2b3`** (parent `b7c8d9e0f1a2`)

## Owned data

- `signing_consent_versions`
- `signing_frozen_artifacts`
- `signing_requests`
- `signing_participants` (token hash-at-rest + SIGN-B evidence columns)
- `signing_events`
- `signing_token_access_attempts` (never stores raw secrets)

Private bytes: `instance/signing_artifacts/` (gitignored).

## Prohibited (SIGN-B)

- Countersignature action
- Executed PDF
- Transactional email
- LibreOffice conversion (SIGN-E)
- Customer account registration
- Mutating `CHANGE_ORDER_STATUSES` or generated-contract `GENERATED`
- EST-2026-0019
- Inventing RBAC
- Legal-review approval states / fields

## Later slices (not started)

SIGN-C countersign + executed PDF. SIGN-D CO E2E + real iPhone UAT. SIGN-E Family 05 DOCX→PDF.

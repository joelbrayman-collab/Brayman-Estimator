# Module — Signing Service

| Attribute | Value |
|-----------|--------|
| Status | **Partial Current.** [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **OPEN / PARTIAL**. SIGN-A **IMPLEMENTED**. SIGN-B/C/D/E **NOT STARTED**. Production / real-customer signing **BLOCKED** pending Ontario counsel process approval. |
| Updated | 2026-09-14 |
| Code | `app/models/signing.py`, `app/services/signing.py`, `app/services/signing_artifact_storage.py`, `app/cli/signing.py` |
| Feature Gate | [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) |
| Architecture | [contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md) |

## Purpose

Native Signing is an **overlay**. It freezes a signable artifact and records a governed signing request. It does **not** own Change Order commercial records or generated-contract commercial identity.

## SIGN-A (current)

- Request identity `SIGN-YYYY-NNNN`
- Change Order: freeze current governed ReportLab PDF once into private `instance/signing_artifacts/<org>/<sha>.pdf`
- Generated contract: bind retained TECH-C DOCX + SHA-256 + Family 05 provenance; **no** DOCX→PDF in SIGN-A
- Participants: `CUSTOMER` plus optional `ORGANIZATION_COUNTERSIGN` foundation (no tokens)
- Consent version pin (`CONSENT-SYNTHETIC-UAT-001` seeded for SYNTHETIC_UAT)
- HUMAN office create + APPROVED_FOR_SIGNATURE
- AI / AUTOMATION **BLOCK**
- Append-only `REQUEST_CREATED` / `APPROVED_FOR_SIGNATURE`
- Authority `SYNTHETIC_UAT` / `PRODUCTION`
- Office CLI `flask signing create-change-order|create-contract|approve|show`

## Owned data

- `signing_consent_versions`
- `signing_frozen_artifacts`
- `signing_requests`
- `signing_participants`
- `signing_events`

Private bytes: `instance/signing_artifacts/` (gitignored). Additive Alembic **`b7c8d9e0f1a2`**.

## Prohibited (SIGN-A)

- Public `/sign` route
- Invitation tokens / raw secrets
- Customer ceremony / consent UI
- Countersignature action
- Executed PDF
- Transactional email
- LibreOffice conversion (SIGN-E)
- Mutating `CHANGE_ORDER_STATUSES` or generated-contract `GENERATED`
- EST-2026-0019
- Inventing RBAC

## Later slices (not started)

SIGN-B invitation + iPhone ceremony. SIGN-C countersign + executed PDF. SIGN-D CO E2E + iPhone UAT. SIGN-E Family 05 DOCX→PDF.

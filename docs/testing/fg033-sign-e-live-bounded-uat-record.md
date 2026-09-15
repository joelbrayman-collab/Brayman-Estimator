# FG-033 SIGN-E generated-contract Native Signing + convert-once + responsive parity

| Attribute | Value |
|-----------|--------|
| Status | **SIGN-E PASS — AUTOMATED PRODUCT / E2E VALIDATION COMPLETE.** Real iPhone UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT.** **NOT CLAIMED AS PASS.** [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED / OPERATIONAL FOR UAT**. Production / real-customer Native Signing **NOT COMPLETE**. PRODUCTION packages remain **0**. |
| Date | 2026-09-15 |
| Gate | [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) SIGN-E (final workstream slice) |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor SIGN-E implementation + automated close |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Additive Alembic **`e0f1a2b3c4d5`**. Convert-once Family 05 DOCX → PDF via LibreOffice/soffice (injected/fake soffice in tests). Same `/sign` ceremony for CHANGE_ORDER and CONTRACT. Desktop + iPhone viewport assertions. Dedicated pytest (in-memory). Full governed suite. |

This file records SIGN-E **automated** product proof. It is **not** a real customer send, not a production executed contract, not legal approval, not a V1 rescore, and **not** real-device iPhone UAT PASS.

```text
SIGN-E:
PASS — AUTOMATED PRODUCT / E2E VALIDATION COMPLETE

NATIVE SIGNING FUNCTIONAL TARGET:
DESKTOP + IPHONE / MOBILE
ONE RESPONSIVE SIGNING SYSTEM.
NO DEVICE-SPECIFIC SIGNING FORKS.

REAL IPHONE UAT:
DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT.
NOT CLAIMED AS PASS.

NO EXTERNAL-REVIEW DEPENDENCY IN THE DEVELOPMENT WORKFLOW.
NOT A LEGAL APPROVAL.
NOT EXTERNALLY REVIEWED.
NATIVE SIGNING PRODUCTION: NOT COMPLETE
SYNTHETIC EXECUTED != PRODUCTION EXECUTION.
TRANSACTIONAL EMAIL: NOT IMPLEMENTED (not a SIGN-E close blocker).
```

## Git / Alembic

| Field | Value |
|-------|--------|
| Parent HEAD | SIGN-D product commit on `origin/main` (`46798858f8743a7fae486c6c0e1b0766b0df61f5`) |
| Live current after migrate | **`e0f1a2b3c4d5 (head)`** |
| Upgrade | `d9e0f1a2b3c4` → **`e0f1a2b3c4d5`** |
| Backup | `instance/brayman_estimator-backup-before-fg033-sign-e-20260915.db` |

## Protected occupancy (before and after)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft |
| Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |
| PRODUCTION packages | **0** |
| SIGN-2026-0001 | CHANGE_ORDER **APPROVED_FOR_SIGNATURE** (SIGN-A retained) |
| SIGN-2026-0002 | CONTRACT **APPROVED_FOR_SIGNATURE** / CTR-2026-0005 (historical DOCX freeze; customer PDF remains BLOCK until a new convert-once request) |
| SIGN-2026-0003 | CHANGE_ORDER **SIGNED** (SIGN-B retained; not countersigned) |
| SIGN-2026-0004 | CHANGE_ORDER **EXECUTED** (SIGN-C countersign retained) |
| SIGN-2026-0005 | CHANGE_ORDER **EXECUTED** (SIGN-C no-countersign retained) |
| SIGN-2026-0006 | SENT |
| SIGN-2026-0007 | VOIDED |
| SIGN-2026-0008 | EXPIRED |
| SIGN-2026-0009 | DECLINED |
| SIGN-2026-0010 | CHANGE_ORDER **EXECUTED** (synthetic iPhone-session residue; **not** real iPhone UAT PASS) |
| SIGN-2026-0011 | VOIDED |
| SIGN-2026-0012 | VOIDED |

Unchanged. EST-2026-0019 was not used for convert, send, sign, execute, request, or token. PRODUCTION Ontario packages remain **0**. No live SIGN-E contract request was created on this Mac because LibreOffice/soffice is not installed; missing converter **BLOCK** is the product path. Automated tests cover injected converter and a fake soffice subprocess.

## Automated product proof (pytest)

Dedicated `tests/test_native_signing_sign_e_fg033.py` exercises product routes/services (in-memory; no live-customer data; no EST-2026-0019):

| Path | Result |
|-------|--------|
| Convert-once DOCX → PDF at request create; retrieve does not reconvert | **PASS** |
| Converter provenance (`converter_identity` / `converter_version` / `converted_at`) | **PASS** |
| Frozen SHA is PDF SHA; `source_docx_sha256` remains DOCX SHA | **PASS** |
| Missing converter BLOCK; no PDF stored | **PASS** |
| Failed conversion BLOCK; no invented PDF | **PASS** |
| Fake soffice subprocess convert | **PASS** |
| Non-PDF converter output BLOCK | **PASS** |
| No ReportLab / HTML fallback imports | **PASS** |
| Historical DOCX freeze still fail-closed for customer PDF | **PASS** |
| PRODUCTION contract send BLOCK without ACTIVE PRODUCTION package | **PASS** |
| Synthetic CONTRACT E2E: invite → review PDF → consent → Sign & Accept → countersign → EXECUTED | **PASS** |
| No-countersign CONTRACT auto-EXECUTED | **PASS** |
| Invalid / expired / void / consumed fail-closed | **PASS** |
| Cross-org isolation | **PASS** |
| EST-2026-0019 protected | **PASS** |
| Same `/sign` routes for CHANGE_ORDER and CONTRACT | **PASS** |
| Desktop + iPhone User-Agent: review, consent, signer name, Sign & Accept, complete, executed retrieval | **PASS** |
| CSS: desktop `@media (min-width: 768px)` and mobile `@media (max-width: 767px)`; overflow-x hidden | **PASS** |
| Additive Alembic `e0f1a2b3c4d5` upgrade/downgrade | **PASS** |

Physical iPhone / Safari device validation remains **DEFERRED**. Automated viewport assertions do **not** mean mobile functionality is incomplete.

## Conversion rule

LibreOffice/soffice only. Convert once at Family 05 bind. Retain PDF + provenance. Retrieve the frozen PDF; never reconvert. Missing converter **BLOCK**. Failed conversion does not retain a PDF. Tests may inject a converter or a fake soffice binary. ReportLab / HTML is not a product fallback.

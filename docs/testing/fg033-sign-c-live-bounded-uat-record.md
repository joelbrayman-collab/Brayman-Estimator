# FG-033 SIGN-C live bounded Native Signing UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** SIGN-C countersign + executed PDF custody + VOID/EXPIRE/DECLINE/RESEND proven on labeled SYNTHETIC_UAT Change Orders. Live current **`d9e0f1a2b3c4 (head)`**. [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **OPEN / PARTIAL**. SIGN-D/E **NOT STARTED**. PRODUCTION packages remain **0**. |
| Date | 2026-09-14 |
| Gate | [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) SIGN-C only |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor SIGN-C implementation + live UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Additive migration `d9e0f1a2b3c4`. Office HUMAN countersign. pypdf executed assembly from frozen pre-sign PDF + audit page. Private signing-artifact custody. No transactional email. No LibreOffice. |

This file records SIGN-C technical proof only. It is **not** a real customer send, not a production executed contract, not legal approval, and not a V1 rescore.

```text
NO EXTERNAL-REVIEW DEPENDENCY IN THE DEVELOPMENT WORKFLOW.
NOT A LEGAL APPROVAL.
NOT EXTERNALLY REVIEWED.
NATIVE SIGNING PRODUCTION: NOT COMPLETE.
SYNTHETIC EXECUTED != PRODUCTION EXECUTION.
SIGN-C STOPS BEFORE SIGN-D HUB / REAL IPHONE CLOSE.
```

## Git / Alembic

| Field | Value |
|-------|--------|
| Parent HEAD | `daf254c1a0f7e1125dbad4620c29bf8d40625254` |
| Live current before upgrade | `c8d9e0f1a2b3` |
| Upgrade | `c8d9e0f1a2b3` → **`d9e0f1a2b3c4`** **PASS** |
| Backup | `instance/brayman_estimator-backup-before-fg033-sign-c-20260914.db` |

## Protected occupancy (before and after)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft |
| Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |
| PRODUCTION packages | **0** |
| SIGN-2026-0001 | CHANGE_ORDER **APPROVED_FOR_SIGNATURE** (SIGN-A retained) |
| SIGN-2026-0002 | CONTRACT **APPROVED_FOR_SIGNATURE** / CTR-2026-0005 |
| SIGN-2026-0003 | CHANGE_ORDER **SIGNED** (SIGN-B retained; not countersigned) |

Unchanged. EST-2026-0019 was not used. SIGN-2026-0003 was not mutated.

## Synthetic SIGN-C identities (retained)

| Record | Identity |
|--------|----------|
| Client | FG033C-UAT Client — SYNTHETIC NATIVE SIGNING — NOT A CUSTOMER |
| Countersign project | FG033C-UAT SYNTHETIC COUNTERSIGN — NOT FOR EXECUTION |
| Request | **SIGN-2026-0004** CHANGE_ORDER **EXECUTED** (`countersign_required=true`) |
| Frozen PDF SHA-256 | `a5237de69d368d426b95ea4de48b36a5eca597040bea4457f85f440e9d21f5cb` |
| Executed PDF SHA-256 | `5988b261e262b3cb7c72a8ba00a82c35e866c6a51a3f5ff6daaf6740d41e2adb` |
| Executed bytes | 60253 |
| Events | REQUEST_CREATED · APPROVED_FOR_SIGNATURE · SENT · VIEWED · CONSENT_ACCEPTED · SIGNED · COUNTERSIGNED · EXECUTED |
| Confirmed signer name | FG033C UAT Signer |
| Completion IP | 203.0.113.210 |
| User-agent | SIGN-C-Live-UAT |
| Actor | HUMAN `uat@example.invalid` |
| Replay after EXECUTED | POST sign → **409/404 TOKEN_CONSUMED / unavailable** |
| Customer executed download | exact retained bytes |
| No-countersign request | **SIGN-2026-0005** CHANGE_ORDER **EXECUTED** (`countersign_required=false`; no COUNTERSIGNED event) |
| RESEND | **SIGN-2026-0006** SENT (token rotated; old secret TOKEN_INVALID) |
| VOID | **SIGN-2026-0007** VOIDED |
| EXPIRE | **SIGN-2026-0008** EXPIRED |
| DECLINE | **SIGN-2026-0009** DECLINED (no signature evidence; no executed artifact) |
| Consent | CONSENT-SYNTHETIC-UAT-001 |

Pre-sign artifact bytes for SIGN-2026-0004 remained unchanged after executed assembly. TECH-D CTR-2026-0003 / CTR-2026-0004 intact. SIGN-A/B evidence retained.

## Tests

Dedicated SIGN-C **19 passed**. Dedicated SIGN-A **11 passed**. Dedicated SIGN-B **18 passed**. Focused SIGN-A/B + CONTRACT + Change Order **174 passed**. Full suite **951 passed**, 3151 warnings, **529.43s**, exit **0**.

## Governance

- FG-033 remains **OPEN / PARTIAL**
- SIGN-A **PASS**
- SIGN-B **PASS**
- SIGN-C **PASS**
- SIGN-D/E **NOT STARTED**
- Native Signing production **NOT COMPLETE**
- V1 **not rescored**

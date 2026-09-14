# FG-033 SIGN-A live bounded Native Signing UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** SIGN-A freeze + CREATED → APPROVED_FOR_SIGNATURE proven on labeled SYNTHETIC_UAT Change Order and generated-contract overlay. Live current **`b7c8d9e0f1a2 (head)`**. [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **OPEN / PARTIAL**. SIGN-B/C/D/E **NOT STARTED**. PRODUCTION packages remain **0**. |
| Date | 2026-09-14 |
| Gate | [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) SIGN-A only |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor SIGN-A implementation + live UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Additive migration `b7c8d9e0f1a2`. Office CLI/service only. No public `/sign` route. No tokens. No executed PDF. |

This file records SIGN-A technical proof only. It is **not** customer signing, not counsel approval, and not a V1 rescore.

```text
COUNSEL REVIEW: DEFERRED FOR V1 TECHNICAL DEVELOPMENT.
MANDATORY PRE-PRODUCTION GATE.
NOT A LEGAL APPROVAL.
NOT A COUNSEL PASS.
NATIVE SIGNING PRODUCTION: NOT COMPLETE.
GENERATED != EXECUTED.
SIGN-A STOPS AT APPROVED_FOR_SIGNATURE.
```

## Git / Alembic

| Field | Value |
|-------|--------|
| Parent HEAD | `de4c2e194c71d66aaf9b81463d8d36eafe52c844` |
| Live current before upgrade | `a6b7c8d9e0f1` |
| Upgrade | `a6b7c8d9e0f1` → **`b7c8d9e0f1a2`** **PASS** |
| Backup | `instance/brayman_estimator-backup-before-fg033-sign-a-20260914.db` |

## Protected occupancy (before and after)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft |
| Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |
| PRODUCTION packages | **0** |

Unchanged. Not used for UAT.

## Synthetic SIGN-A identities (retained)

| Record | Identity |
|--------|----------|
| Client | FG033A-UAT Client — SYNTHETIC NATIVE SIGNING — NOT A CUSTOMER |
| Project | FG033A-UAT SYNTHETIC NATIVE SIGNING — NOT FOR EXECUTION |
| Change Order | FG033A-UAT SYNTHETIC CHANGE ORDER — NOT FOR EXECUTION · Approved |
| Request | **SIGN-2026-0001** CHANGE_ORDER **APPROVED_FOR_SIGNATURE** |
| Frozen PDF SHA-256 | `be95556e1727587e315677c9437081e1f9b6a0dfb22bcfa5d89f94c4edd026ed` |
| Bytes | 59122 |
| Events | REQUEST_CREATED · APPROVED_FOR_SIGNATURE |
| Estimate | EST-FG033A-UAT-0001 Issued / locked |
| Proposal | PROP-FG033A-UAT-0001 Issued |
| Contract | **CTR-2026-0005** GENERATED (new; does not mutate TECH-D CTR-2026-0003 / CTR-2026-0004) |
| Request | **SIGN-2026-0002** CONTRACT **APPROVED_FOR_SIGNATURE** SYNTHETIC_UAT |
| Bound DOCX SHA-256 | `5d6189554a7287c4f65fdd93164f17789d23da5cffa523b625a6fcaef5675be2` |
| Consent | CONSENT-SYNTHETIC-UAT-001 |
| Actor | HUMAN `uat@example.invalid` |

TECH-D evidence retained: CTR-2026-0003 / CTR-2026-0004 unchanged. Slice C CTR-2026-0001 / CTR-2026-0002 retained.

## Tests

Dedicated SIGN-A **11 passed**. Focused SIGN-A + CONTRACT + Change Order **103 passed**. Full suite **915 passed**, 3068 warnings, **341.52s**, exit **0**.

## Governance

- FG-033 remains **OPEN / PARTIAL**
- SIGN-B/C/D/E **NOT STARTED**
- Native Signing production **NOT COMPLETE**
- V1 **not rescored**

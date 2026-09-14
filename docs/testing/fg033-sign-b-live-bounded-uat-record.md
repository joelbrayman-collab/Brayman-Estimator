# FG-033 SIGN-B live bounded Native Signing UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** SIGN-B invitation + public customer ceremony proven on a labeled SYNTHETIC_UAT Change Order. Live current **`c8d9e0f1a2b3 (head)`**. [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **OPEN / PARTIAL**. SIGN-C/D/E **NOT STARTED**. PRODUCTION packages remain **0**. |
| Date | 2026-09-14 |
| Gate | [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) SIGN-B only |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor SIGN-B implementation + live UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Additive migration `c8d9e0f1a2b3`. Office HUMAN invite. Public `/sign/*` customer ceremony. No customer account. No transactional email. No executed PDF. |

This file records SIGN-B technical proof only. It is **not** a real customer send, not an executed contract, not legal approval, and not a V1 rescore.

```text
NO EXTERNAL-REVIEW DEPENDENCY IN THE DEVELOPMENT WORKFLOW.
NOT A LEGAL APPROVAL.
NOT EXTERNALLY REVIEWED.
NATIVE SIGNING PRODUCTION: NOT COMPLETE.
SIGNED != EXECUTED.
SIGN-B STOPS AT SIGNED.
```

## Git / Alembic

| Field | Value |
|-------|--------|
| Parent HEAD | `df383e234f30e67597b31a543c10c858eca4f16c` |
| Live current before upgrade | `b7c8d9e0f1a2` |
| Upgrade | `b7c8d9e0f1a2` → **`c8d9e0f1a2b3`** **PASS** |
| Backup | `instance/brayman_estimator-backup-before-fg033-sign-b-20260914.db` |

## Protected occupancy (before and after)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft |
| Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |
| PRODUCTION packages | **0** |
| SIGN-2026-0001 | CHANGE_ORDER **APPROVED_FOR_SIGNATURE** (SIGN-A evidence retained) |
| SIGN-2026-0002 | CONTRACT **APPROVED_FOR_SIGNATURE** / CTR-2026-0005 |

Unchanged. EST-2026-0019 was not used.

## Synthetic SIGN-B identities (retained)

| Record | Identity |
|--------|----------|
| Client | FG033B-UAT Client — SYNTHETIC NATIVE SIGNING — NOT A CUSTOMER |
| Project | FG033B-UAT SYNTHETIC CUSTOMER CEREMONY — NOT FOR EXECUTION |
| Change Order | FG033B-UAT SYNTHETIC CHANGE ORDER — NOT FOR EXECUTION · Approved |
| Request | **SIGN-2026-0003** CHANGE_ORDER **SIGNED** |
| Frozen PDF SHA-256 | `db3d03a2cc12f81e33408cdf533d61881a679244deb9d436823fa4ac98831b81` |
| Bytes | 59151 |
| Consent | CONSENT-SYNTHETIC-UAT-001 |
| Events | REQUEST_CREATED · APPROVED_FOR_SIGNATURE · SENT · VIEWED · CONSENT_ACCEPTED · SIGNED |
| Confirmed signer name | FG033B UAT Signer |
| Completion IP | 203.0.113.200 |
| User-agent | SIGN-B-Live-UAT |
| Countersign required | true (confirmation: Signed successfully. Awaiting organization countersignature.) |
| Replay | POST after SIGNED → **409 TOKEN_CONSUMED** |
| Actor | HUMAN `uat@example.invalid` |
| Invitation | copyable `/sign/<lookup>.<secret>` issued once; raw secret not stored |

Later live Change Order mutation produced a different PDF SHA; customer download remained the frozen SHA. No EXECUTED artifact. No countersign. TECH-D CTR-2026-0003 / CTR-2026-0004 intact. SIGN-A requests retained as APPROVED_FOR_SIGNATURE.

## Tests

Dedicated SIGN-B **18 passed**. Dedicated SIGN-A **11 passed**. Focused SIGN + CONTRACT + Change Order **137 passed**. Full suite **933 passed**, 3110 warnings, **342.95s**, exit **0**.

## Governance

- FG-033 remains **OPEN / PARTIAL**
- SIGN-A **PASS**
- SIGN-B **PASS**
- SIGN-C/D/E **NOT STARTED**
- Native Signing production **NOT COMPLETE**
- V1 **not rescored**

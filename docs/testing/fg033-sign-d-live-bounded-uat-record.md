# FG-033 SIGN-D automated Change Order Native Signing product validation record

| Attribute | Value |
|-----------|--------|
| Status | **SIGN-D PASS — AUTOMATED PRODUCT / E2E VALIDATION COMPLETE.** Real iPhone UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT.** **NOT CLAIMED AS PASS.** [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) remains **OPEN / PARTIAL**. SIGN-E **NOT STARTED**. PRODUCTION packages remain **0**. |
| Date | 2026-09-15 |
| Gate | [FG-033](../feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) SIGN-D only |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor SIGN-D implementation + automated close |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | No new Alembic. Office Send for Signature on labeled SYNTHETIC_UAT Change Orders. Public `/sign` ceremony. Organization countersign. Dedicated pytest product routes (in-memory). Full governed suite. |

This file records SIGN-D **automated** product proof only. It is **not** a real customer send, not a production executed contract, not legal approval, not a V1 rescore, and **not** real-device iPhone UAT PASS.

```text
SIGN-D:
PASS — AUTOMATED PRODUCT / E2E VALIDATION COMPLETE

REAL IPHONE UAT:
DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT.
NOT CLAIMED AS PASS.

NO EXTERNAL-REVIEW DEPENDENCY IN THE DEVELOPMENT WORKFLOW.
NOT A LEGAL APPROVAL.
NOT EXTERNALLY REVIEWED.
NATIVE SIGNING PRODUCTION: NOT COMPLETE.
SYNTHETIC EXECUTED != PRODUCTION EXECUTION.
SIGN-D STOPS BEFORE SIGN-E.
```

## Git / Alembic

| Field | Value |
|-------|--------|
| Parent HEAD | `e48b074c27543bc300322362b9e174508e745d4c` |
| Live current | **`d9e0f1a2b3c4 (head)`** (unchanged; SIGN-C executed artifacts) |
| Upgrade | none |
| Backup | `instance/brayman_estimator-backup-before-fg033-sign-d-20260914.db` |

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
| SIGN-2026-0004 | CHANGE_ORDER **EXECUTED** (SIGN-C countersign retained) |
| SIGN-2026-0005 | CHANGE_ORDER **EXECUTED** (SIGN-C no-countersign retained) |
| SIGN-2026-0006 | SENT (SIGN-C RESEND retained) |
| SIGN-2026-0007 | VOIDED |
| SIGN-2026-0008 | EXPIRED |
| SIGN-2026-0009 | DECLINED |

Unchanged. EST-2026-0019 was not used for send, sign, execute, request, or token. PRODUCTION Ontario packages remain **0**.

## Live synthetic residue (not real-device PASS)

Live development/UAT also retains SIGN-D office/synthetic residue:

| Record | Identity / state |
|--------|------------------|
| SIGN-2026-0010 | CHANGE_ORDER **EXECUTED** (synthetic iPhone-session residue; **not** real iPhone UAT PASS) |
| SIGN-2026-0011 | VOIDED |
| SIGN-2026-0012 | VOIDED |

These rows are labeled SYNTHETIC_UAT evidence only. They do **not** constitute real-device UAT PASS.

## Automated product proof (pytest)

Dedicated `tests/test_native_signing_sign_d_fg033.py` exercises product routes/services (in-memory; no live-customer data; no EST-2026-0019):

| Path | Result |
|-------|--------|
| Approved CO → office Send for Signature → invitation → SENT | **PASS** |
| Public customer GET + frozen PDF review | **PASS** |
| Consent + confirmed typed name → Sign & Accept → SIGNED | **PASS** |
| Organization countersign → EXECUTED | **PASS** |
| Executed PDF retained; SHA of exact bytes; frozen pre-sign bytes unchanged | **PASS** |
| Customer completed-state retrieval + office executed GET | **PASS** |
| Replay blocked | **PASS** |
| No-countersign path auto-EXECUTED; no second ceremony | **PASS** |
| VOID: token unusable; no Sign & Accept | **PASS** |
| RESEND: token rotates; old unusable; new valid | **PASS** |
| EXPIRE fail-closed | **PASS** |
| DECLINE terminal; no signature; no executed artifact | **PASS** |
| Wrong org cannot countersign / download executed | **PASS** |
| Customer token cannot open another request | **PASS** |
| Invalid token fail-closed | **PASS** |
| Public `/favicon.ico` does not redirect to office login | **PASS** |
| Customer mobile markup/CSS/copy/state assertions | **PASS** |

### Customer mobile UX (automated)

- Mobile viewport + `viewport-fit=cover` / safe-area CSS
- No office chrome / Dashboard / Project Controls / office navigation
- Standalone customer signing surface
- Organization identity + project/document identity rendered
- Practical control sizing (`min-height` 44 / 56), `overflow-x: hidden`
- Sign & Accept primary
- Consent, signer-name, document-review accessible
- No desktop-table dependency
- Name-first copy: identify document/project → name → Review the document → consent → Sign & Accept
- SHA / request-number / enum jargon not shown to the customer
- States: SENT; SIGNED awaiting countersignature; EXECUTED complete; invalid token fail-closed

## Tests

Prior SIGN-D engineering focused matrix (before final mobile assertions): **187 passed**, 446 warnings, **84.41s**, exit **0**.

Prior customer-copy focused: **46 passed**, 113 warnings, **29.74s**, exit **0**.

Final focused SIGN-A/B/C/D + Change Order + Project Hub + TECH-A/B/C/D contract regression: **206 passed**, 486 warnings, **69.82s**, exit **0**.

Full governed suite: **962 passed**, 3184 warnings, **317.78s**, exit **0**.

`git diff --check` **PASS**. Alembic current = heads `d9e0f1a2b3c4`.

## Real iPhone UAT (deferred)

```text
REAL IPHONE UAT:
DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT.
NOT CLAIMED AS PASS.
```

Deferred later checklist (does **not** reopen SIGN-D unless a defect is actually found):

BRAYMAN / BEN REAL-WORLD MOBILE UAT — on an actual iPhone later verify:

- ceremony opens
- PDF review
- consent
- typed name
- Sign & Accept
- confirmation
- executed retrieval
- void/expired fail-closed
- practical touch usability

A later defect becomes normal governed corrective work. It does **not** reopen SIGN-D by default.

## Governance

- FG-033 remains **OPEN / PARTIAL**
- SIGN-A **PASS**
- SIGN-B **PASS**
- SIGN-C **PASS**
- SIGN-D **PASS** (automated product / E2E only)
- SIGN-E **NOT STARTED**
- Native Signing production **NOT COMPLETE**
- V1 **not rescored**

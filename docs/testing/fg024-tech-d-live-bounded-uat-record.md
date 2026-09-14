# FG-024 TECH-D live bounded synthetic Ontario UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** End-to-end technical Ontario CONTRACT chain proven using **SYNTHETIC_UAT** only. Live current remains **`a6b7c8d9e0f1 (head)`**. No new migration. [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **OVERALL OPEN / PARTIAL**. PRODUCTION packages remain **0**. |
| Date | 2026-09-14 |
| Gate | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) TECH-D only (production-shaped synthetic Ontario UAT) |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor tests + live UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | No schema change. Dedicated pytest chain. Live services against `instance/brayman_estimator.db`. Explicit SYNTHETIC_UAT generation path. Family 05 copy-only merge. Private DOCX custody. Ordinary production selector unused for synthetic content. |

This file records TECH-D technical proof only. It is **not** an Ontario production contract, not counsel approval, not Native Signing, and not a V1 rescore.

```text
COUNSEL REVIEW: DEFERRED FOR V1 TECHNICAL DEVELOPMENT.
MANDATORY PRE-PRODUCTION GATE.
NOT A LEGAL APPROVAL.
NOT A COUNSEL PASS.
ONTARIO PRODUCTION LEGAL CONTENT: NOT APPROVED / NOT ACTIVE.
FAMILY 05: COMMERCIAL_DRAFT / NOT LEGALLY APPROVED.
PRODUCTION CONTRACT EXECUTION: BLOCKED PENDING COUNSEL REVIEW.
GENERATED != EXECUTED.
TECH-D: TECHNICAL PROOF ONLY.
```

## Starting Git / Alembic state

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` (start) | `af00fca3e3c1d34ed3bdd890ef71826b1b97d5a8` |
| Subject | `docs: record mobile-first field time UX` |
| TECH-C product | `9a6c86fb8e66234a10ac19f15118d8caea200af6` |
| Divergence | `0 0` |
| Working tree | clean |
| Live Alembic current | `a6b7c8d9e0f1 (head)` |
| Repository Alembic head | `a6b7c8d9e0f1` |
| Graph heads | one |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg024-techd-20260914.db` |

## Family 05 master

| Field | Value |
|-------|--------|
| Path | `/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/Reusable Master Template Family V1/MASTER DOCX/05_Brayman_Ontario_Construction_Contract_COMMERCIAL_DRAFT_MASTER_V1.docx` |
| SHA-256 before | `24bb319a10a8d386136fffdff8737dac5a30b80ec3104808c13033c9f5000fb5` |
| SHA-256 after | `24bb319a10a8d386136fffdff8737dac5a30b80ec3104808c13033c9f5000fb5` |
| Unchanged | **YES.** Renderer worked from a copy only. Never wrote the master path. |

## Protected occupancy (before and after)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft |
| Version 34 | Draft unlocked · subtotal **49872.94** · total **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |
| PRODUCTION packages | **0** |

Unchanged. Not used for UAT.

## Synthetic UAT identities (retained)

| Record | Identity |
|--------|----------|
| Client 24 | FG024D-UAT Client — SYNTHETIC ONTARIO CONTRACT UAT — NOT A CUSTOMER |
| Project 29 | FG024D-UAT SYNTHETIC ONTARIO CONTRACT UAT — NOT FOR EXECUTION |
| Estimate | EST-FG024D-UAT-0001 Issued / locked |
| Issued Proposal | PROP-FG024D-UAT-0001 Issued |
| Draft Proposal | PROP-FG024D-UAT-DRAFT Draft (negative C1 control) |
| Package | FG024D-UAT-ON-001 · **SYNTHETIC_UAT** · **ACTIVE** |
| Source | FG024D-UAT-SRC-001 |
| Candidate | PROPOSED / non-authoritative |
| Contracts | CTR-2026-0003 (ALLOW) · CTR-2026-0004 (WARN) · status **GENERATED** |
| Artifact SHA-256 | `f44a154d8c3cd6b7d615de05a30bb93b6f6fa922f239825fe22cbf4276c867f7` |
| Storage key | `ORG-001/f44a154d8c3cd6b7d615de05a30bb93b6f6fa922f239825fe22cbf4276c867f7.docx` |
| Bytes | 124760 |
| Activation | HUMAN `fg024d-tech-d-human` · append-only ACTIVATE event |

Slice C evidence retained: CTR-2026-0001 / CTR-2026-0002 (`artifact_storage_key` NULL).

TECH-D records **retained** as unmistakably synthetic evidence. They are **not** production legal content.

## Proof results

| Requirement | Result |
|-----------|--------|
| C1 Issued locked EstimateVersion + Issued Proposal | **PASS** CTR-2026-0003 |
| C1 Draft Proposal BLOCK | **PASS** `PROPOSAL_NOT_ELIGIBLE` |
| TECH-A HUMAN activation of APPROVED SYNTHETIC_UAT | **PASS** |
| Ordinary PRODUCTION selector ignores synthetic ACTIVE | **PASS** `JURISDICTION_NOT_SUPPORTED` |
| C2 pending candidate WARN | **PASS** `PENDING_CANDIDATE` |
| WARN uses current ACTIVE bodies | **PASS** |
| Candidate body absent from artifact | **PASS** |
| C3 missing warranty BLOCK | **PASS** `MISSING_REQUIRED_LEGAL_OBJECT` |
| C3 provision + warranty eligible | **PASS** |
| Exact legal objects frozen | **PASS** |
| Family 05 master SHA verified | **PASS** |
| Master unchanged after generation | **PASS** |
| Commercial tokens from frozen snapshot | **PASS** |
| Contract + warranty merged | **PASS** |
| Safety banners retained | **PASS** (`GOVERNED COMMERCIAL DRAFT` · `COMMERCIAL DRAFT — NOT FOR EXECUTION` · `NOT FOR SIGNATURE`) |
| DOCX retained / SHA / retrieval | **PASS** |
| Later source mutation does not alter artifact | **PASS** |
| PRODUCTION package count remains 0 | **PASS** |
| Ordinary Ontario production selection BLOCK | **PASS** |
| Hub production CONTRACT unavailable | **PASS** (UAT project and EST-2026-0019 project) |
| EST-2026-0019 unchanged | **PASS** |
| GENERATED != EXECUTED | **PASS** |
| No Native Signing / Slice D / Ontario PRODUCTION | **PASS** |

After the immutability mutation, live project/client/legal-object display values were restored to the labeled FG024D-UAT names so leftover records remain unmistakably synthetic. Frozen snapshot + retained DOCX SHA were unchanged.

## Tests

| Suite | Result |
|-------|--------|
| Dedicated TECH-D | **5 passed**, 18 warnings, **0.94s** |
| Focused TECH-A/B/C/D + FG-024 CONTRACT | **124 passed**, 295 warnings, **25.62s** |
| Full suite | **904 passed**, 3040 warnings, **350.10s**, exit **0** |

## Governance

- FG-024 remains **OPEN / PARTIAL**
- Slice D **NOT AUTHORIZED**
- Native Signing **not started**
- V1 **not rescored** (**60% / 4 of 11**)
- Family 05 remains **COMMERCIAL_DRAFT**
- Independent fail-closed BMR contract-story remains **PASS**
- TECH-D adds a truthful **synthetic** end-to-end technical demonstration
- **BMR DEMO READY remains NO**
- GENERATED != EXECUTED

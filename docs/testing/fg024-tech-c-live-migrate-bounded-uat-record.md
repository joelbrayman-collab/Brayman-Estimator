# FG-024 TECH-C live migrate + bounded synthetic UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated through **`a6b7c8d9e0f1 (head)`**. Bounded synthetic TECH-C UAT **PASS**. [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **OVERALL OPEN / PARTIAL**. Legal Content Gate production packages remain **0**. |
| Date | 2026-09-14 |
| Gate | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) TECH-C only (Family 05 DOCX merge + generated-contract artifact custody) |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor implementation + live migrate + UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Live `flask db upgrade`. Synthetic Issued locked EstimateVersion + explicit Issued Proposal. Explicit SYNTHETIC_UAT generation path. Family 05 copy-only merge. Private DOCX custody + SHA-256. Ordinary production selector unused for synthetic content. No Ontario PRODUCTION package. No EST-2026-0019 mutation. No Word→PDF conversion. |

This file records TECH-C live-migration and bounded synthetic UAT facts only. It does **not** implement TECH-D, Slice D, Ontario production legal content, Native Signing, or a V1 rescore.

```text
COUNSEL REVIEW: DEFERRED FOR V1 TECHNICAL DEVELOPMENT.
MANDATORY PRE-PRODUCTION GATE.
NOT A LEGAL APPROVAL.
NOT A COUNSEL PASS.
ONTARIO PRODUCTION LEGAL CONTENT: NOT APPROVED / NOT ACTIVE.
FAMILY 05: COMMERCIAL_DRAFT / NOT LEGALLY APPROVED.
PRODUCTION CONTRACT EXECUTION: BLOCKED PENDING COUNSEL REVIEW.
GENERATED != EXECUTED.
```

## Starting Git / Alembic state

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` (start) | `689262818b172aa4e317648a9a0ae72639f1f070` |
| Subject | `feat: govern Ontario contract generation policy` |
| Divergence | `0 0` |
| Working tree | clean at preflight; TECH-C files added before migrate |
| Live Alembic current (pre-migrate) | `f5a6b7c8d9e0 (head)` |
| Repository Alembic head (pre-commit) | `a6b7c8d9e0f1` after TECH-C revision added |
| Graph heads | one |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg024-techc-a6b7c8d9e0f1-20260914.db` |

## Family 05 master

| Field | Value |
|-------|--------|
| Path | `/Users/joelbrayman/Documents/CalibAi/Approved Document Templates/Reusable Master Template Family V1/MASTER DOCX/05_Brayman_Ontario_Construction_Contract_COMMERCIAL_DRAFT_MASTER_V1.docx` |
| SHA-256 before | `24bb319a10a8d386136fffdff8737dac5a30b80ec3104808c13033c9f5000fb5` |
| SHA-256 after | `24bb319a10a8d386136fffdff8737dac5a30b80ec3104808c13033c9f5000fb5` |
| Bytes | 124592 |
| Unchanged | **YES.** Renderer worked from a copy only. Never wrote the master path. |

## Pre-migration inspection

Revision `migrations/versions/a6b7c8d9e0f1_add_fg024_tech_c_artifact_custody.py`:

- `down_revision` = `f5a6b7c8d9e0`
- Additive only (`artifact_storage_key`, `artifact_media_type` on generated contracts and snapshots)
- Historical generated contracts remain valid with nullable storage keys
- No Ontario / U.S. seed
- No PRODUCTION package created
- No Native Signing / PDF custody schema

**PASS.** Migration authorized.

## Pre-migration commercial identity (bounded)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft · Version **34** Draft unlocked · subtotal **49872.94** · total **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |
| Jurisdiction packages | **0** |
| Legal-content objects | **0** |
| Historical contracts | CTR-2026-0001 / CTR-2026-0002 (`proposal_id` NULL; storage keys not yet present) |

## Live migration

| Field | Value |
|-------|--------|
| Command | `./venv/bin/flask --app app db upgrade` |
| Applied | `f5a6b7c8d9e0` → `a6b7c8d9e0f1` |
| Post-migration live current | `a6b7c8d9e0f1 (head)` |
| Post-migration repository head | `a6b7c8d9e0f1 (head)` |
| Historical contracts after migrate | CTR-2026-0001 / CTR-2026-0002 `proposal_id` **NULL**, `artifact_storage_key` **NULL**, status **GENERATED** |
| PRODUCTION packages | **0** |
| EST-2026-0019 | unchanged Draft **28** / Version **34** |

**PASS.**

## Bounded TECH-C synthetic UAT

Live services against `instance/brayman_estimator.db`. Synthetic identities only. Explicit SYNTHETIC_UAT path. EST-2026-0019 unused. Family 05 master used as a **copy only**.

| Step | Result |
|-------|--------|
| Ordinary production selector | **BLOCK** (`JURISDICTION_NOT_SUPPORTED` / empty PRODUCTION library) |
| ACTIVE SYNTHETIC_UAT package + synthetic `contract_provision` + synthetic `warranty` | **PASS** via HUMAN `activate_legal_content` |
| Issued locked EstimateVersion + explicit Issued Proposal | **PASS** `EST-FG024C-UAT-001` / `PROP-FG024C-UAT-001` |
| Generate + Family 05 copy merge | **PASS** CTR-2026-0003 / snapshot 3 / status **GENERATED** |
| Commercial tokens | CLIENT / PROJECT / SITE / DATE mapped from frozen snapshot |
| Legal bodies | exact frozen provision + warranty inserted; candidate path unused |
| Safety labels retained | `GOVERNED COMMERCIAL DRAFT` · `COMMERCIAL DRAFT — NOT FOR EXECUTION` · `NOT FOR SIGNATURE` |
| Artifact SHA-256 | `e2b5f22b90a899cf5dcc18a1539ba07fd9393e631358853f02f210489462229b` |
| Storage key | `ORG-001/e2b5f22b90a899cf5dcc18a1539ba07fd9393e631358853f02f210489462229b.docx` |
| Retrieval | exact retained bytes; SHA matches retained bytes |
| Master provenance | Family 05 SHA `24bb319a10a8d386136fffdff8737dac5a30b80ec3104808c13033c9f5000fb5` |
| Later live mutation | project/client/legal bodies mutated; retained DOCX unchanged |
| Cleanup | synthetic UAT package/objects/events/CTR-2026-0003/estimate 31/proposal 15/project 29/client 24 removed |
| Slice C evidence | `CTR-2026-0001` / `CTR-2026-0002` retained (`proposal_id` NULL; `artifact_storage_key` NULL) |
| Slice C commercial host | Client **23** / Project **28** / EST-FG024C-UAT-0001 / EST-FG024C-UAT-DRAFT retained |
| Slice B source evidence | `FG024B-UAT-SRC-001` retained |
| PRODUCTION packages after cleanup | **0** |
| EST-2026-0019 | Draft **28** / Version **34** unchanged |
| Private artifact | gitignored `instance/generated_contracts/ORG-001/e2b5f22b90a899cf5dcc18a1539ba07fd9393e631358853f02f210489462229b.docx` (124656 bytes; SHA matches) |

**PASS.**

## Tests

| Suite | Result |
|-------|--------|
| Focused TECH-C + FG-024 related + Hub/customer/proposal (pre-migrate) | **175 passed**, 395 warnings, **42.44s** |
| Full suite (post-migrate / post-UAT) | **899 passed**, 3022 warnings, **290.85s**, exit **0** |

## Governance

- FG-024 remains **OPEN / PARTIAL**
- Slice D **NOT AUTHORIZED**
- TECH-D **not started**
- Native Signing **not started**
- V1 **not rescored** (**60% / 4 of 11**)
- Family 05 remains **COMMERCIAL_DRAFT**
- GENERATED != EXECUTED

# FG-024 TECH-B live migrate + bounded synthetic UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated through **`f5a6b7c8d9e0 (head)`**. Bounded synthetic TECH-B UAT **PASS**. [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **OVERALL OPEN / PARTIAL**. Legal Content Gate production packages remain **0**. |
| Date | 2026-09-14 |
| Gate | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) TECH-B only (C1/C2/C3 generation policy) |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor implementation + live migrate + UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Live `flask db upgrade`. Synthetic Issued locked EstimateVersion + explicit Issued Proposal. Explicit SYNTHETIC_UAT generation path. Ordinary production selector unused for synthetic content. No Ontario PRODUCTION package. No EST-2026-0019 mutation. |

This file records TECH-B live-migration and bounded synthetic UAT facts only. It does **not** implement TECH-C, TECH-D, Slice D, Ontario production legal content, Native Signing, Family 05 merge, or a V1 rescore.

```text
COUNSEL REVIEW: DEFERRED FOR V1 TECHNICAL DEVELOPMENT.
MANDATORY PRE-PRODUCTION GATE.
NOT A LEGAL APPROVAL.
NOT A COUNSEL PASS.
ONTARIO PRODUCTION LEGAL CONTENT: NOT APPROVED / NOT ACTIVE.
FAMILY 05: COMMERCIAL_DRAFT / NOT LEGALLY APPROVED.
PRODUCTION CONTRACT EXECUTION: BLOCKED PENDING COUNSEL REVIEW.
```

## Starting Git / Alembic state

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` | `bb4ddb1db07e020c02f829400e40db7e6287b718` |
| Subject | `feat: add governed legal content activation` |
| Divergence | `0 0` |
| Working tree | clean at preflight; TECH-B files added before migrate |
| Live Alembic current (pre-migrate) | `e4f5a6b7c8d9 (head)` |
| Repository Alembic head (pre-commit) | `f5a6b7c8d9e0` after TECH-B revision added |
| Graph heads | one |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg024-techb-f5a6b7c8d9e0-20260914.db` |

## Pre-migration inspection

Revision `migrations/versions/f5a6b7c8d9e0_add_fg024_tech_b_generation_policy.py`:

- `down_revision` = `e4f5a6b7c8d9`
- Additive only (`proposal_id` pin; snapshot proposal/WARN provenance columns)
- Historical generated contracts remain valid with nullable `proposal_id`
- No Ontario / U.S. seed
- No PRODUCTION package created

**PASS.** Migration authorized.

## Pre-migration commercial identity (bounded)

| Record | Identity / state |
|--------|------------------|
| Estimate 28 | EST-2026-0019 Draft · subtotal **49872.94** |
| Proposal 14 | PROP-2026-0006 Draft |
| Jurisdiction packages | **0** |
| Legal-content objects | **0** |
| Historical contracts | CTR-2026-0001 / CTR-2026-0002 (no proposal_id column yet) |

## Live migration

| Field | Value |
|-------|--------|
| Command | `./venv/bin/flask --app app db upgrade` |
| Applied | `e4f5a6b7c8d9` → `f5a6b7c8d9e0` |
| Post-migration live current | `f5a6b7c8d9e0 (head)` |
| Post-migration repository head | `f5a6b7c8d9e0 (head)` |
| Historical contracts after migrate | CTR-2026-0001 / CTR-2026-0002 `proposal_id` **NULL** |
| PRODUCTION packages | **0** |
| EST-2026-0019 | unchanged Draft **28** |

**PASS.**

## Bounded TECH-B synthetic UAT

Live services against `instance/brayman_estimator.db`. Synthetic identities only. Explicit SYNTHETIC_UAT path. EST-2026-0019 unused. Project **9** reused as Ontario location host only.

| Step | Result |
|-------|--------|
| Ordinary production selector | **BLOCK** (empty PRODUCTION library) |
| C3 provision only | **BLOCK** `MISSING_REQUIRED_LEGAL_OBJECT` |
| Issued locked EstimateVersion + explicit Issued Proposal + provision + warranty | **PASS** CTR-2026-0003; proposal pin **15** / `PROP-FG024B-UAT-001` / Issued; both legal objects frozen |
| Draft Proposal | **BLOCK** `PROPOSAL_NOT_ELIGIBLE` |
| Valid ACTIVE + pending candidate | selector **WARN** `PENDING_CANDIDATE` |
| Generation under WARN | **PASS** CTR-2026-0004; current ACTIVE bodies used; candidate body not used; `pending_candidate_used_as_authority=false`; package remained ACTIVE; candidate remained PROPOSED |
| Cleanup | synthetic UAT packages/objects/events/contracts/estimate/proposals removed |
| Slice C evidence | `CTR-2026-0001` / `CTR-2026-0002` retained (`proposal_id` NULL) |
| Slice B source evidence | `FG024B-UAT-SRC-001` retained |
| PRODUCTION packages after cleanup | **0** |
| EST-2026-0019 | Draft **28** unchanged |

**PASS.**

## Tests

| Suite | Result |
|-------|--------|
| Focused TECH-B + FG-024 related (pre-migrate) | **150 passed**, 362 warnings, **31.37s** |
| Full suite (post-migrate / post-UAT) | **886 passed**, 2989 warnings, **292.71s**, exit **0** |

## Governance

- FG-024 remains **OPEN / PARTIAL**
- Slice D **NOT AUTHORIZED**
- TECH-C / TECH-D **not started**
- Native Signing **not started**
- V1 **not rescored** (**60% / 4 of 11**)

# FG-024 Slice C live migrate + bounded office UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated through **`d3e4f5a6b7c8 (head)`**. Bounded office UAT **PASS**. Slice C **CLOSED / OPERATIONAL FOR UAT**. [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **OVERALL OPEN / PARTIAL**. Legal Content Gate remains **empty**. |
| Date | 2026-09-13 |
| Gate | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) Slice C only |
| Start product SHA | `1a2553932da1b750e2cbe0e32fd90e54d569a685` (`feat: add FG-024 contract generation foundation`) |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor live-migrate + UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Live `flask db upgrade`. Empty Slice-C counts via SQLite. Generation UAT via live `app/services/contract_generation.py` against `instance/brayman_estimator.db` using **synthetic/test legal authority only**. Slice A fail-closed re-proven via `select_legal_content_package_for_project` on labeled UAT projects **13** and **9**. Slice B AI/activation boundaries re-proven via `app/services/legal_content_update.py`. No UI. No Ontario/U.S. legal-content seed. No real customer contract. No Native Signing. |

This file records Slice C live-migration and bounded office UAT facts only. It does **not** implement Slice D, Ontario/U.S. population, real customer contract generation, Native Signing, warranty schedule, C1/C2/C3 production policy, or live monitoring.

## Starting Git / Alembic state

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` | `1a2553932da1b750e2cbe0e32fd90e54d569a685` |
| Subject | `feat: add FG-024 contract generation foundation` |
| Divergence | `0 0` |
| Working tree | clean |
| Staging | empty |
| Live Alembic current (pre-migrate) | `c2d3e4f5a6b7` |
| Repository Alembic head | `d3e4f5a6b7c8 (head)` |
| Graph heads | one |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg024c-d3e4f5a6b7c8-20260913-143836.db` |
| Bytes | 2,277,376 (source and backup matched at backup time) |
| SHA-256 | `f6e3db6840e5574fd0e928ea5f039881c0d7e1786378375a0ec6c67f1411c98c` |
| Backup Alembic | `c2d3e4f5a6b7` |
| Pre-migration sqlite tables | **101** |
| Slice C tables before migrate | **absent** |

## Pre-migration inspection

Revision `migrations/versions/d3e4f5a6b7c8_add_fg024_contract_generation_foundation.py`:

- `down_revision` = `c2d3e4f5a6b7`
- Additive only (`project_generated_contracts`, `project_contract_snapshots`, `project_contract_snapshot_objects`)
- No destructive operations
- No Slice A/B redesign
- No Permit Rules mutation
- No legal-content seed rows
- No Ontario / U.S. content
- No real customer contract rows
- No signing schema

**PASS.** Migration authorized.

## Pre-migration commercial identity (bounded)

Unrelated to FG-024. Recorded only to prove survival. **Not** used as a Slice C generation fixture.

| Record | Identity / state |
|--------|------------------|
| Client 22 | Marc Bouliion |
| Project 27 | 40x80 Thickened-Edge Concrete Slab / Estimating |
| Estimate 28 | EST-2026-0019 Draft |
| EstimateVersion 34 | Draft · subtotal **49872.94** · total **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |

Bounded counts before migrate: clients **22** · projects **27** · estimates **28** · versions **34** · proposals **14** · project_locations **10** · permit_rules **10** · legal-content packages **0** · objects **0**. Slice B retained evidence: source `FG024B-UAT-SRC-001` (id **1**), snapshots **2**, candidate **1**.

## Live migration

| Field | Value |
|-------|--------|
| Command | `./venv/bin/flask db upgrade` |
| Applied | `c2d3e4f5a6b7` → `d3e4f5a6b7c8` (Slice C contract-generation / immutable-snapshot foundation) |
| Post-migration live current | `d3e4f5a6b7c8 (head)` |
| Post-migration repository head | `d3e4f5a6b7c8 (head)` |
| Graph heads | one |
| sqlite tables | 101 → **104** |
| Seed rows | **none** |
| Downgrade | **not performed** |

### Tables confirmed

`project_generated_contracts`, `project_contract_snapshots`, `project_contract_snapshot_objects` created. `permit_rules` count remained **10**. Slice A library tables unchanged and empty. Slice B source/snapshot/candidate evidence unchanged. No unrelated table drop.

## Empty live table counts (immediately after migrate)

| Object | Count |
|--------|-------|
| project_generated_contracts | **0** |
| project_contract_snapshots | **0** |
| project_contract_snapshot_objects | **0** |
| Jurisdiction packages | **0** |
| Legal-content objects | **0** |

Legal Content Gate remained **empty**.

## Commercial-data continuity

Post-migrate and post-UAT identity/state for Client 22 / Project 27 / Estimate 28 / Version 34 / Proposal 14 matched the pre-migrate bounded values. EST-2026-0019 was **not** used as a generation fixture. Draft / not issued preserved.

**PASS.**

## Bounded Slice C office UAT

Live service: `app/services/contract_generation.py` in Flask app context against `instance/brayman_estimator.db`. Synthetic UAT authority only. No Ontario/U.S. clause bodies. No real customer contract.

### Fail-closed live UAT

| Case | Result |
|------|--------|
| A unresolved jurisdiction (project **13**) | `BLOCK` / `JURISDICTION_UNRESOLVED` |
| B empty library (project **9**, CA-ON) | `BLOCK` / `JURISDICTION_NOT_SUPPORTED` |
| B empty library generation (synthetic project **28**, no package) | `BLOCK` / `JURISDICTION_NOT_SUPPORTED` |
| C package not ACTIVE | `BLOCK` / `PACKAGE_NOT_ACTIVE` |
| D package outside effective date | `BLOCK` / `PACKAGE_NOT_EFFECTIVE` |
| E missing required legal object | `BLOCK` / `MISSING_REQUIRED_LEGAL_OBJECT` |
| F non-authoritative legal object (`PROPOSED`) | `BLOCK` / `LEGAL_OBJECT_NOT_AUTHORITATIVE` |
| G missing presentation master | `BLOCK` / `MISSING_PRESENTATION_MASTER` |
| H Draft EstimateVersion | `BLOCK` / `DRAFT_ESTIMATE_VERSION` |
| I missing required commercial facts | `BLOCK` / `MISSING_COMMERCIAL_FACTS` |
| J pending-candidate / `UPDATE_PENDING_REVIEW` | `BLOCK` / `PENDING_REVIEW_UNSUPPORTED` |

ADR-051 §6 remains **unsupported / fail-closed**. No ALLOW / WARN / production BLOCK policy was implemented.

**PASS.**

### No-fallback proof

Generation source does not fall back to generic North America, generic Canada, generic USA, another jurisdiction, Family 05 as legal authority, Permit Rules, or AI-created legal content. Family 05 master present with empty library still **BLOCK**. `permit_rules` remained **10**.

**PASS.**

### Successful synthetic generation

Isolated UAT fixture:

| Role | Identity |
|------|----------|
| Client | **23** `FG024C-UAT Client` |
| Project | **28** `FG024C-UAT Contract Generation` (Ottawa / CA-ON) |
| Estimate | **29** `EST-FG024C-UAT-0001` |
| EstimateVersion | **35** Issued |
| Draft control | Estimate **30** `EST-FG024C-UAT-DRAFT` |
| Package (temporary) | `FG024C-UAT-ON-001` / ACTIVE / effective / synthetic `contract_provision` |
| Presentation master | Family **05** / `V1-UAT-SYNTHETIC` / `FG024C_UAT_SYNTHETIC_FAMILY_05_PRESENTATION_SHELL.docx` / SHA-256 `e4b54a02d3d553dbae930061829e2fc507a29e04091922146a23ed53dbfa193e` / `COMMERCIAL_DRAFT` |

Generated:

| Record | Identity |
|--------|----------|
| Contract **1** | `CTR-2026-0001` / status **GENERATED** |
| Snapshot **1** | pins package `FG024C-UAT-ON-001`, object body snapshot, EstimateVersion **35**, Family 05 presentation shell |
| Artifact SHA-256 | `2a317355987f936e0fcf1ff8a4b8f1cef7cd4044511c6161c9fd6fd2158b6f46` |
| Legal-content SHA-256 | `1f56688b304e24e14bac5920d350daed739d4b2420b069da4b22c2d8ab19f393` |
| Commercial SHA-256 | `a944dd8e6e59f457665d441c762332d8e528d0199af1aeeb6698d8a011f5b7a3` |

Artifact text includes `NOT AN EXECUTED CONTRACT` and `NOT FOR SIGNATURE`. This is **SYNTHETIC UAT ONLY**.

**PASS.**

### Immutability UAT

After generation, live UAT mutated the synthetic package code, legal-object body, and EstimateVersion total. Snapshot **1** artifact text, artifact hash, legal-content hash, commercial hash, package code `FG024C-UAT-ON-001`, object body, and commercial total remained unchanged.

A later generation created **new** contract **2** `CTR-2026-0002` / snapshot **2** (artifact SHA-256 `65ea5d29c1f0778c3ca1bf1cfe7eb626294accda2dac1d9b2f05f385a15dc115`). Snapshot **1** survived unchanged.

**PASS.**

### EstimateVersion pinning

Draft EstimateVersion **BLOCK**. Eligible Issued version **35** generated. Snapshot **1** pins `estimate_version_id=35`, `EST-FG024C-UAT-0001`, status `Issued`. Later live total mutation did not change snapshot **1**.

C1 production UX policy remains **unresolved**.

**PASS.**

### Presentation-master pinning

Snapshot **1** pins Family code **05**, version `V1-UAT-SYNTHETIC`, filename `FG024C_UAT_SYNTHETIC_FAMILY_05_PRESENTATION_SHELL.docx`, SHA-256 `e4b54a02d3d553dbae930061829e2fc507a29e04091922146a23ed53dbfa193e`, legal status **COMMERCIAL_DRAFT**. Family 05 remains presentation shell only and did **not** create legal authority.

**PASS.**

### Legal-content pinning

Snapshot **1** preserves package id **1** / code `FG024C-UAT-ON-001` / object id **1** / version **1** / synthetic body / object SHA-256 `bc005c4f01dcb453eff29972b686d0fe169f401d746884006c5cb36ade1bbb5b`. Later live-object mutation did not alter snapshot **1**. The live package/object were then **deleted**; snapshot **1** still holds the frozen copies.

**PASS.**

### Artifact hash / provenance

Contract **1** and snapshot **1** share artifact SHA-256 `2a317355987f936e0fcf1ff8a4b8f1cef7cd4044511c6161c9fd6fd2158b6f46`. Legal-content and commercial SHA-256 are 64-character hex. Generation process `fg024_slice_c`. Actor `fg024c-uat`. Provenance is labeled UAT / not legal authority.

**PASS.**

### Native Signing boundary

No signer, signature, signing audit, signed artifact, `SENT FOR SIGNATURE`, or `SIGNED`. Generated status remains the Slice C terminal boundary.

**PASS.**

## Slice A fail-closed regression

Live `select_legal_content_package_for_project` after synthetic-library cleanup:

| Case | Project | Result |
|------|---------|--------|
| unresolved jurisdiction | **id 13** `FG-023 UAT MONITOR` | `BLOCK` / `JURISDICTION_UNRESOLVED` / `package_id=None` |
| resolved Ontario + empty library | **id 9** Pratt coach-house UAT | `BLOCK` / `JURISDICTION_NOT_SUPPORTED` / `CA-ON` / `package_id=None` |

No generic fallback. Selector source does not consult Permit Rules or Family 05. `permit_rules` remained **10**.

**PASS.**

## Slice B regression

Live service rejections after Slice C generation:

| Call | Actor | Code |
|------|-------|------|
| `approve_content_version` | AI | `AI_CANNOT_APPROVE` |
| `activate_legal_content` | AI | `AI_CANNOT_ACTIVATE` |
| `activate_legal_content` | HUMAN | `ACTIVATION_NOT_SLICE_B` |
| `supersede_active_from_candidate` | — | `ACTIVE_MUTATION_FORBIDDEN` |
| `deactivate_active_from_candidate` | — | `ACTIVE_MUTATION_FORBIDDEN` |

No APScheduler / live-monitor helpers on the Slice B service. Candidate **2** created for §6 proof was **deleted**. Slice B retained evidence (source **1**, snapshots **1–2**, candidate **1**) was not mutated as legal authority.

**PASS.**

## UAT data disposition

Labeled synthetic Slice C commercial + generated-contract evidence **retained** (not legal authority, not a real customer contract):

| Row | Identity |
|-----|----------|
| Client **23** | `FG024C-UAT Client` |
| Project **28** | `FG024C-UAT Contract Generation` |
| Estimate **29** | `EST-FG024C-UAT-0001` |
| EstimateVersion **35** | Issued (live total later mutated to **9999.00** after snapshot **1**; snapshot **1** frozen at original commercial hash) |
| Estimate **30** | `EST-FG024C-UAT-DRAFT` |
| Contract **1** | `CTR-2026-0001` GENERATED |
| Snapshot **1** | frozen first generation |
| Contract **2** | `CTR-2026-0002` GENERATED |
| Snapshot **2** | later generation after live mutation |

Temporary synthetic Slice A package/object used for generation proof was **deleted**. Live library packages **0** / objects **0**. Legal Content Gate remains **empty**. Legitimate commercial records were **not** deleted.

## Tests after live migration

| Suite | Command | Result |
|-------|---------|--------|
| Slice C focused | `./venv/bin/python -m pytest -q tests/test_contract_generation_fg024.py` | **16 passed**, 33 warnings, **2.71s** |
| Slice A focused | `./venv/bin/python -m pytest -q tests/test_legal_content_library_fg024.py` | **17 passed**, 35 warnings, **2.32s** |
| Slice B focused | `./venv/bin/python -m pytest -q tests/test_legal_content_update_fg024.py` | **16 passed**, 22 warnings, **2.10s** |
| Full | `./venv/bin/python -m pytest -q` | **825 passed**, 2771 warnings, **266.33s**, exit **0** |

Prior repository baseline: Slice C **16** / Slice A **17** / Slice B **16** / full **825**.

## Acceptance

All Slice C closure criteria in the 13 Sep 2026 live-migrate prompt are **PASS**. Slice C is **CLOSED / OPERATIONAL FOR UAT**. Slice A remains **CLOSED / OPERATIONAL FOR UAT**. Slice B remains **CLOSED / OPERATIONAL FOR UAT**. FG-024 overall remains **OPEN / PARTIAL**. V1 score **unchanged** (**60% / 4 of 11**). Output 4 **not** complete. V1-06 **PARTIAL**. Slice D **NOT AUTHORIZED**.

## Out of this UAT

Slice D; Ontario or U.S. legal language; counsel drafting of production content; real customer contract; contract issuance; Native Signing; warranty schedule; live monitoring; Family 05 legal approval; Permit Rules mutation; C1 production UX; C2 §6 production policy; C3 warranty increment; V1 rescore; EST-2026-0019 mutation.

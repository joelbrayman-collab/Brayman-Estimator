# FG-024 Slice A live migrate + bounded office UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated through **`b1c2d3e4f5a6 (head)`**. Bounded office UAT **PASS**. Slice A **CLOSED / OPERATIONAL FOR UAT**. [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **OVERALL OPEN / PARTIAL**. Legal Content Gate remains **empty**. |
| Date | 2026-09-13 |
| Gate | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) Slice A only |
| Start product SHA | `868f8f2c7c46b36c4e121204fa2c12b2250c00ce` (`feat: add FG-024 legal-content library foundation`) |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor live-migrate + UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Live `flask db upgrade`. Empty-library counts via SQLite / Flask app context. Fail-closed UAT via live `select_legal_content_package_for_project` against existing labeled UAT projects. No UI. No legal-content seed. |

This file records Slice A live-migration and bounded office UAT facts only. It does **not** implement Slices B–D, Ontario/U.S. population, contract generation, or Native Signing.

## Starting Git / Alembic state

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` | `868f8f2c7c46b36c4e121204fa2c12b2250c00ce` |
| Subject | `feat: add FG-024 legal-content library foundation` |
| Divergence | `0 0` |
| Working tree | clean |
| Staging | empty |
| Live Alembic current (pre-migrate) | `f1a2b3c4d5e6` |
| Repository Alembic head | `b1c2d3e4f5a6` |
| Graph heads | one |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg024a-b1c2d3e4f5a6-20260913-091555.db` |
| Bytes | 2,121,728 (source and backup matched at backup time) |
| SHA-256 | `fc276ef01b0cf43320d48b13cf69228beaf96c5a62dd97dd1026286a05da9068` |
| Backup Alembic | `f1a2b3c4d5e6` |
| Pre-migration sqlite tables | 94 |
| Slice A tables before migrate | `legal_content_jurisdiction_packages` **absent**; `legal_content_objects` **absent** |

## Pre-migration commercial identity (bounded)

Unrelated to FG-024. Recorded only to prove survival. Not used as a UAT mutation fixture.

| Record | Identity / state |
|--------|------------------|
| Client 22 | Marc Bouliion |
| Project 27 | 40x80 Thickened-Edge Concrete Slab / Estimating |
| Estimate 28 | EST-2026-0019 |
| EstimateVersion 34 | Draft · subtotal **49872.94** · total **56356.42** |
| Pricing snapshot 14 | direct **42392.00** · sell **49872.94** · HST **6483.48** · customer **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |

Bounded counts before migrate: clients **22** · projects **27** · estimates **28** · versions **34** · proposals **14** · project_locations **10** · permit_rules **10**.

## Live migration

| Field | Value |
|-------|--------|
| Command | `./venv/bin/flask db upgrade` |
| Applied | `f1a2b3c4d5e6` → `b1c2d3e4f5a6` (empty legal-content library) |
| Post-migration live current | `b1c2d3e4f5a6 (head)` |
| Post-migration repository head | `b1c2d3e4f5a6 (head)` |
| Graph heads | one |
| sqlite tables | 94 → **96** |
| Seed rows | **none** |
| Downgrade | **not performed** |

### Tables confirmed

`legal_content_jurisdiction_packages` and `legal_content_objects` created. `permit_rules` count remained **10**. No unrelated table drop. No legal-content seed.

## Empty-library counts (live)

| Object | Count |
|--------|-------|
| Jurisdiction packages | **0** |
| Legal-content objects | **0** |
| Ontario packages | **0** |
| U.S. packages | **0** |
| Generic CA / USA / NA packages | **0** |

Empty live library is the intended Slice A state.

## Commercial-data continuity

Post-migrate identity/state for Client 22 / Project 27 / Estimate 28 / Version 34 / Proposal 14 / snapshot 14 matched the pre-migrate bounded values. Project 27 was **not** mutated for UAT. Draft / not issued preserved.

## Canonical UAT vessels (existing labeled / non-destructive)

No new legal-content rows. No new commercial recost. No Marc mutation.

| Case | Project | Why safe |
|------|---------|----------|
| A unresolved jurisdiction | **id 13** `FG-023 UAT MONITOR` | Existing labeled MONITOR UAT vessel; **no** `ProjectLocation` row |
| B resolved Ontario + empty library | **id 9** `FG-016 UAT — Mike Pratt Coach House` | Existing labeled permit UAT vessel; civic Canada / Ontario / North Gower |

## Fail-closed office UAT

Live service: `select_legal_content_package_for_project` in Flask app context against `instance/brayman_estimator.db`.

### A. Unresolved jurisdiction

Project **13** location = none.

Result: `BLOCK` / `JURISDICTION_UNRESOLVED` / `package_id=None`.

**PASS.**

### B. Resolved Ontario + empty library

Project **9** location Canada / Ontario / North Gower.

ADR-037 `resolve_jurisdiction(..., tax_jurisdiction=None)` returned municipality `CA-ON-OTTAWA` (City of Ottawa), parent `CA-ON` (Ontario).

Selector result: `BLOCK` / `JURISDICTION_NOT_SUPPORTED` / `jurisdiction_code='CA-ON'` / `package_id=None`.

**PASS.** Implemented empty-library contract is `JURISDICTION_NOT_SUPPORTED`, not `NO_ACTIVE_PACKAGE`.

### C. No fallback

- Selector returned no package id.
- Live package/object counts remained **0**.
- `app/services/legal_content.py` source contains `resolve_jurisdiction` and does **not** contain `PermitRule`, `permit_rules`, `Family 05`, or `family_05`.
- No generic Canada / USA / North America package exists to return.

**PASS.**

## Tests after live migration

| Suite | Command | Result |
|-------|---------|--------|
| Focused | `./venv/bin/python -m pytest -q tests/test_legal_content_library_fg024.py` | **17 passed**, 35 warnings, **2.28s** |
| Full | `./venv/bin/python -m pytest -q` | **782 passed**, 2704 warnings, **269.18s** (0:04:29) |

Prior repository baseline: focused **17** / full **782**.

## Acceptance

All Slice A closure criteria in the 13 Sep 2026 live-migrate prompt are **PASS**. Slice A is **CLOSED / OPERATIONAL FOR UAT**. FG-024 overall remains **OPEN / PARTIAL**. V1 score **unchanged** (**60% / 4 of 11**). Output 4 **not** complete. V1-06 **not** complete.

## Out of this UAT

Slice B/C/D; Ontario or U.S. legal language; counsel drafting; contract generation; Native Signing; UI; Family 05 changes; Permit Rules changes; V1 rescore; EST-2026-0019 mutation.

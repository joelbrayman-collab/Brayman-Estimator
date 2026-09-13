# FG-024 Slice B live migrate + bounded office UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated through **`c2d3e4f5a6b7 (head)`**. Bounded office UAT **PASS**. Slice B **CLOSED / OPERATIONAL FOR UAT**. [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **OVERALL OPEN / PARTIAL**. Legal Content Gate remains **empty**. |
| Date | 2026-09-13 |
| Gate | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) Slice B only |
| Start product SHA | `e36397778d282e14801bfb00c896ec7a3c36057f` (`feat: add FG-024 legal-content update foundation`) |
| Actor | Joel Brayman / ChatGPT Architect authorization; Cursor live-migrate + UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Live `flask db upgrade`. Empty Slice-B counts via SQLite. Lifecycle UAT via live `app/services/legal_content_update.py` against `instance/brayman_estimator.db`. Slice A fail-closed re-proven via `select_legal_content_package_for_project` on labeled UAT projects **13** and **9**. No UI. No Ontario/U.S. legal-content seed. No contract generation. |

This file records Slice B live-migration and bounded office UAT facts only. It does **not** implement Slice C or Slice D, Ontario/U.S. population, contract generation, Native Signing, or live monitoring.

## Starting Git / Alembic state

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` | `e36397778d282e14801bfb00c896ec7a3c36057f` |
| Subject | `feat: add FG-024 legal-content update foundation` |
| Divergence | `0 0` |
| Working tree | clean |
| Staging | empty |
| Live Alembic current (pre-migrate) | `b1c2d3e4f5a6` |
| Repository Alembic head | `c2d3e4f5a6b7 (head)` |
| Graph heads | one |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg024b-c2d3e4f5a6b7-20260913-125346.db` |
| Bytes | 2,174,976 (source and backup matched at backup time) |
| SHA-256 | `de1bfb6481b5354ccb7221e7be728167f3f1ae430b53285a83796c998304b76e` |
| Backup Alembic | `b1c2d3e4f5a6` |
| Pre-migration sqlite tables | 96 |
| Slice B tables before migrate | **absent** |

## Pre-migration commercial identity (bounded)

Unrelated to FG-024. Recorded only to prove survival. Not used as a UAT mutation fixture.

| Record | Identity / state |
|--------|------------------|
| Client 22 | Marc Bouliion |
| Project 27 | 40x80 Thickened-Edge Concrete Slab / Estimating |
| Estimate 28 | EST-2026-0019 |
| EstimateVersion 34 | Draft · subtotal **49872.94** · total **56356.42** |
| Proposal 14 | PROP-2026-0006 Draft |

Bounded counts before migrate: clients **22** · projects **27** · estimates **28** · versions **34** · proposals **14** · project_locations **10** · permit_rules **10** · legal-content packages **0** · objects **0**.

## Live migration

| Field | Value |
|-------|--------|
| Command | `./venv/bin/flask db upgrade` |
| Applied | `b1c2d3e4f5a6` → `c2d3e4f5a6b7` (Slice B source/update foundation) |
| Post-migration live current | `c2d3e4f5a6b7 (head)` |
| Post-migration repository head | `c2d3e4f5a6b7 (head)` |
| Graph heads | one |
| sqlite tables | 96 → **101** |
| Seed rows | **none** |
| Downgrade | **not performed** |

### Tables confirmed

`legal_content_sources`, `legal_content_source_snapshots`, `legal_content_candidate_changes`, `legal_content_candidate_impacts`, `legal_content_review_events` created. `permit_rules` count remained **10**. Slice A library tables unchanged and empty. No unrelated table drop.

## Empty live table counts (immediately after migrate)

| Object | Count |
|--------|-------|
| legal_content_sources | **0** |
| legal_content_source_snapshots | **0** |
| legal_content_candidate_changes | **0** |
| legal_content_candidate_impacts | **0** |
| legal_content_review_events | **0** |
| Jurisdiction packages | **0** |
| Legal-content objects | **0** |

Legal Content Gate remained **empty**.

## Commercial-data continuity

Post-migrate and post-UAT identity/state for Client 22 / Project 27 / Estimate 28 / Version 34 / Proposal 14 matched the pre-migrate bounded values. Project 27 was **not** mutated. Draft / not issued preserved.

## Bounded Slice B office UAT

Live service: `app/services/legal_content_update.py` in Flask app context against `instance/brayman_estimator.db`. Synthetic source only. No Ontario/U.S. clause bodies.

### Source registration

Registered `FG024B-UAT-SRC-001` / class `OFFICIAL_PRIMARY` / identity `FG-024 Slice B UAT Source` / ADR-037 node `CA-ON`. Provenance marked UAT / not legal authority. Classification did **not** confer APPROVED or ACTIVE.

**PASS.**

### Snapshot fingerprinting

Payload A created snapshot 1 with SHA-256 persisted. Identical payload A reused snapshot 1 with `unchanged=True`. Candidate count remained **0**.

**PASS.** Unchanged source did **not** create a false candidate.

### Changed snapshot

Payload B created snapshot 2 with a different SHA-256. Slice A package/object counts remained **0**.

**PASS.**

### Candidate / provenance

Candidate 1 created from snapshot 2: state `PROPOSED`, `source_id=1`, `snapshot_id=2`, jurisdiction `CA-ON`. Candidate is not legal authority.

**PASS.**

### AI / automation authority

Live service rejections:

| Call | Actor | Code |
|------|-------|------|
| `approve_content_version` | AI | `AI_CANNOT_APPROVE` |
| `approve_content_version` | AUTOMATION | `AI_CANNOT_APPROVE` |
| `activate_legal_content` | AI | `AI_CANNOT_ACTIVATE` |
| `activate_legal_content` | AUTOMATION | `AI_CANNOT_ACTIVATE` |
| `activate_legal_content` | HUMAN | `ACTIVATION_NOT_SLICE_B` |
| `route_candidate_to_counsel_review` | AI | `AI_CANNOT_ROUTE` |

**PASS.**

### Human / counsel review boundary

Human routed candidate 1 to `COUNSEL_REVIEW`. Isolated synthetic package/object used only to prove `approve_content_version` → object `APPROVED` while package remained **not** `ACTIVE`. Counsel `activate_legal_content` remained `ACTIVATION_NOT_SLICE_B`. Isolated package/object then **removed**.

`APPROVED` ≠ `ACTIVE`. **PASS.**

### Deferred policy / no auto-SUPERSEDE

`supersede_active_from_candidate` / `deactivate_active_from_candidate` raised `ACTIVE_MUTATION_FORBIDDEN`. Isolated package `support_status` was **not** set to `UPDATE_PENDING_REVIEW`. Slice A selector unchanged.

**PASS.** ADR-051 §6 remains **deferred**.

### No live monitoring

No watcher/cron/APScheduler helpers on the Slice B service.

**PASS.**

## Slice A fail-closed regression

Live `select_legal_content_package_for_project`:

| Case | Project | Result |
|------|---------|--------|
| A unresolved jurisdiction | **id 13** `FG-023 UAT MONITOR` | `BLOCK` / `JURISDICTION_UNRESOLVED` / `package_id=None` |
| B resolved Ontario + empty library | **id 9** Pratt coach-house UAT | `BLOCK` / `JURISDICTION_NOT_SUPPORTED` / `CA-ON` / `package_id=None` |

No generic fallback. Selector source does not consult Permit Rules or Family 05. `permit_rules` remained **10**.

**PASS.**

## UAT data disposition

Labeled synthetic Slice B lifecycle evidence **retained** (not legal authority):

| Row | Identity |
|-----|----------|
| Source **1** | `FG024B-UAT-SRC-001` / `OFFICIAL_PRIMARY` / `FG-024 Slice B UAT Source` |
| Snapshots **2** | payload A and payload B; UAT-only text |
| Candidate **1** | `COUNSEL_REVIEW`; provenance to source 1 / snapshot 2 |
| Review event **1** | HUMAN `ROUTED` |

Isolated synthetic Slice A package/object used for APPROVED≠ACTIVE proof was **deleted**. Live library packages **0** / objects **0**. Legal Content Gate remains **empty**.

## Tests after live migration

| Suite | Command | Result |
|-------|---------|--------|
| Slice B focused | `./venv/bin/python -m pytest -q tests/test_legal_content_update_fg024.py` | **16 passed**, 22 warnings, **2.21s** |
| Slice A focused | `./venv/bin/python -m pytest -q tests/test_legal_content_library_fg024.py` | **17 passed**, 35 warnings, **2.25s** |
| Full | `./venv/bin/python -m pytest -q` | **809 passed**, 2738 warnings, **278.30s**, exit **0** |

Prior repository baseline: Slice B **16** / Slice A **17** / full **809**.

## Acceptance

All Slice B closure criteria in the 13 Sep 2026 live-migrate prompt are **PASS**. Slice B is **CLOSED / OPERATIONAL FOR UAT**. Slice A remains **CLOSED / OPERATIONAL FOR UAT**. FG-024 overall remains **OPEN / PARTIAL**. V1 score **unchanged** (**60% / 4 of 11**). Output 4 **not** complete. V1-06 **not** complete.

## Out of this UAT

Slice C/D; Ontario or U.S. legal language; counsel drafting of production content; contract generation; Native Signing; UI; live monitoring; Family 05 changes; Permit Rules changes; V1 rescore; EST-2026-0019 mutation; ADR-051 §6 generation-while-pending policy.

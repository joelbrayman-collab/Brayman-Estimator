# FG-032 Slice C live migrate + bounded office UAT record

| Attribute | Value |
|-----------|--------|
| Status | **UAT PASS.** Live-migrated through **`f1a2b3c4d5e6 (head)`**. Bounded DEMO/SYNTHETIC office UAT **PASS**. Slice C **OPERATIONAL FOR UAT**. Slices A+B remain **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **OVERALL NOT CLOSED**. |
| Date | 2026-09-11 |
| Gate | [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) |
| Start product SHA | `00de0517b994635dec0be04a6e581167f690f7fe` (`fix: enforce atomic FG-032 entry confirmation`) |
| Actor | Joel Brayman — FG032C-UAT |
| Organization | ORG-001 / Brayman Construction Inc. |
| Method | Authenticated Flask `test_client` against live office PRICE / QuickBooks-ready entry / Proposal / Supplier Package / Field Web routes. Session `_user_id` = `"1"` (Joel Brayman). Gitignored runners `instance/fg032c_uat_office.py` and `instance/fg032c_uat_office_continue.py` (not committed). |

This file records Slice C live-migration and bounded office UAT facts only. It does **not** implement live QuickBooks API, OAuth, CSV, or IIF. Slices A+B evidence remains in [fg032-slices-ab-live-migrate-bounded-uat-record.md](fg032-slices-ab-live-migrate-bounded-uat-record.md) and is historical for A+B facts.

**Subsequent status (2026-09-11 FG-032 close + V1-05 rescore):** [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**. Readiness **60% / 4 of 11**. V1-04 remains **PARTIAL**. The UAT evidence in this file remains historical and unchanged.

Historical repair-time tests (focused **37** / regression **256** / full **765** at occupancy-repair commit) are **not** this session’s results.

## Starting Git / Alembic state

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD / `origin/main` | `00de0517b994635dec0be04a6e581167f690f7fe` |
| Subject | `fix: enforce atomic FG-032 entry confirmation` |
| Divergence | `0 0` |
| Working tree | clean |
| Staging | empty |
| Live Alembic current (pre-migrate) | `e9f0a1b2c3d4` |
| Repository Alembic head | `f1a2b3c4d5e6` |
| Graph heads | one |
| Pending chain | `e9f0a1b2c3d4` → `f0a1b2c3d4e5` → `f1a2b3c4d5e6` |

## Backup (gitignored; not committed)

| Field | Value |
|-------|--------|
| Source | `/Users/joelbrayman/Desktop/Brayman-Estimator/instance/brayman_estimator.db` |
| Backup | `instance/brayman_estimator-backup-before-fg032c-f1a2b3c4d5e6-20260911-115130.db` |
| Bytes | 2,064,384 (source and backup matched at backup time) |
| SHA-256 | `e4f30e6b1dbe303a4c9bf9cecf3fedc353d9c3b39dc60ace1740539c77fd367f` |
| Backup Alembic | `e9f0a1b2c3d4` |
| Pre-migration sqlite tables | 92 |
| Slice C tables before migrate | `estimate_quickbooks_entry_events` **absent**; `estimate_quickbooks_entry_occupancies` **absent** |

## Live migration

| Field | Value |
|-------|--------|
| Command | `./venv/bin/flask db upgrade f1a2b3c4d5e6` |
| Applied in order | `e9f0a1b2c3d4` → `f0a1b2c3d4e5` (entry events) → `f1a2b3c4d5e6` (occupancy) |
| Post-migration live current | `f1a2b3c4d5e6 (head)` |
| Post-migration repository head | `f1a2b3c4d5e6 (head)` |
| Graph heads | one |
| sqlite tables | 92 → **94** |
| Occupancy backfill | 0 rows (no pre-existing events) |
| Downgrade | **not performed** |

### Tables and constraints confirmed

`estimate_quickbooks_entry_events`

- Kind check `ENTERED` / `REVERSED` / `CORRECTED`
- FKs: package / project / organization **RESTRICT**; actor **SET NULL**
- Indexes: org, project, package, org+package+id

`estimate_quickbooks_entry_occupancies`

- PRIMARY KEY `estimate_quickbooks_package_id` (database uniqueness by package)
- UNIQUE `entered_event_id` named `uq_estimate_quickbooks_entry_occupancies_event` (SQLite autoindex `sqlite_autoindex_estimate_quickbooks_entry_occupancies_1`)
- FKs: package / organization / entered event **RESTRICT**
- Index: `ix_estimate_quickbooks_entry_occupancies_organization_id`

No unrelated table or migration change. Live current remained `f1a2b3c4d5e6` after UAT.

## Canonical UAT vessels (DEMO / SYNTHETIC)

Existing FG-032 project **26** was inspected before mutation. A+B packages were **not** re-seeded.

| Kind | Id | Identity |
|------|----|----------|
| Client | 21 | FG032-UAT-QB-ENTRY DEMO SYNTHETIC Client |
| Project | **26** | `FG032-UAT-QB-ENTRY` / `ORG-001` / `FG032-UAT-001` |
| Working ISSUED package | **1** | `QB-2026-0001` version **31** — Slice C working package |
| Control ISSUED package | **2** | `QB-2026-0002` version **32** — untouched sibling control |
| REVIEWED package | **3** | `QB-2026-0003` version **33** — unissued ENTERED fail-closed |
| New DRAFT (this UAT only) | **4** | `QB-2026-0004` version **32** — DRAFT ENTERED fail-closed |
| Issued Proposal | **11** | status Issued (A+B vessel; post-issue edit remains) |
| Accepted Proposal | **12** | status Accepted |
| Office user | 1 | Joel Brayman |
| Costing / pricing (Issued vessel) | 16 / 11 | CURRENT at A+B freeze |
| Supplier Package (privacy) | project **14** package **1** | FG029-UAT-BMR-DEMO; read-only |

Version **31** regenerate is blocked (`PROPOSAL_PRICING_MISMATCH`) because A+B UAT edited Issued Proposal **11** after issue (non-float). The DRAFT vessel was therefore generated from eligible version **32**. Package **1** ISSUED freeze was not mutated.

New commercial row: package **4** `QB-2026-0004` DRAFT, labeled continuation of FG032-UAT / DEMO / SYNTHETIC. Not genuine Brayman job data.

## Required UAT results

| Case | Action | Expected | Actual | Result |
|------|--------|----------|--------|--------|
| Download ≠ entry | GET sales.pdf + cost-class.pdf + preview | 0 events / 0 occupancy | HTTP **200**; sales 3202 B SHA `9f70a5df…248b1c`; cost 3001 B SHA `9571797d…948401`; events 0 occupancy 0 | **PASS** |
| Issue ≠ entry | ISSUED package **2** after migrate | 0 events / 0 occupancy | ISSUED; events 0; occupancy none | **PASS** |
| ENTERED | POST `/entered` package **1** | 1 ENTERED + 1 occupancy + derived ENTERED + actor/time + disclaimer | event **1** ENTERED; occupancy package 1 → event 1; actor user **1** `Joel Brayman — FG032C-UAT` at `2026-09-11 16:22:51.674363`; flash “did not post / did not verify” | **PASS** |
| Duplicate HTTP | second POST `/entered` | fail closed; no second event/occupancy | “already has an active Entered”; events remain 1; occupancy 1 | **PASS** |
| Duplicate service | `confirm_entered` while active | `DUPLICATE_ACTIVE_ENTERED` | block `DUPLICATE_ACTIVE_ENTERED` | **PASS** |
| DB uniqueness | INSERT second occupancy for package 1 | IntegrityError PK | `UNIQUE constraint failed: …estimate_quickbooks_package_id`; rolled back; occupancy 1 | **PASS** |
| DB uniqueness event | INSERT occupancy package 2 with event 1 | IntegrityError UNIQUE event | UNIQUE `entered_event_id`; rolled back; package 2 occupancy none | **PASS** |
| CORRECTED | POST `/correct-entry` with note | append CORRECTED; occupancy remains; state ENTERED; original ENTERED unchanged | event **2** CORRECTED; occupancy still event 1; event 1 note/time unchanged | **PASS** |
| REVERSED | POST `/reverse-entry` with reason | append REVERSED; occupancy removed; state NOT ENTERED; history retained | event **3** REVERSED; occupancy none; derived NOT ENTERED; event 1 retained | **PASS** |
| Re-entry | POST `/entered` after reverse | new ENTERED + occupancy reclaimed; history unchanged | event **4** ENTERED; occupancy package 1 → event **4**; event 1 timestamp/note unchanged | **PASS** |
| ENTERED on DRAFT | POST package **4** | refuse + no residue | ISSUED-only refusal; no event/occupancy on package 4 | **PASS** |
| ENTERED on REVIEWED | POST package **3** | refuse + no residue | ISSUED-only refusal; package 3 remains REVIEWED with 0 events | **PASS** |
| REVERSE/CORRECT without active | POST package **2** | refuse + no residue | refused; package 2 still 0 events / 0 occupancy | **PASS** |
| Blank reason/note | reverse/correct package **1** while ENTERED | refuse; state remains ENTERED | refused; 1 event remained | **PASS** |
| Missing actor | service `actor=""` | `ENTRY_ACTOR_REQUIRED` + rollback | block `ENTRY_ACTOR_REQUIRED` | **PASS** |
| AI actor | HTTP `AI` / `CALIBAI-AI` + service `AI` | `ENTRY_AI_ACTOR` + no residue | refused; package 2 unchanged | **PASS** |
| Cross-org HTTP | GET `/projects/4/quickbooks-entry`; POST entered on project 4 package 1 | **404** | both **404**; no residue | **PASS** |
| Cross-org service | `organization_id="ORG-002"` | `CROSS_ORG` | block `CROSS_ORG` | **PASS** |
| Event immutability | update kind/actor/time; reassign package; delete | `ENTRY_EVENT_IMMUTABLE` + rollback | all five attempts raised `ENTRY_EVENT_IMMUTABLE`; event 1 intact | **PASS** |
| Commercial non-mutation | package 1/2/3 fields, lines, PDFs, estimate lines, costing/pricing, Proposal, Scope Delivery, Supplier Packages, PLAN/catalogue | unchanged by ENTERED/CORRECTED/REVERSED/re-entry | package fingerprints match; PDF SHA unchanged vs pre-ENTERED; universe unchanged after entry ops (package count +1 only for DRAFT **4**) | **PASS** |
| Privacy | Proposal 11 HTML/PDF; Supplier Package 14 HTML/PDF; Field Web; QB PDFs | no Slice C state/controls | markers absent; Hub PRICE `/projects/26/quickbooks-entry` retains controls | **PASS** |
| No external QuickBooks | no API/OAuth/CSV/IIF/posting | none | no `*.csv`/`*.iif`; no oauth/token tables; UI states CalibraytAI did not post or verify | **PASS** |

Two-session race: **not** run against the live database. Genuine concurrency remains the focused test `test_concurrent_entered_exactly_one_succeeds` (this session focused suite **37 passed**). Live UAT used bounded duplicate HTTP + UNIQUE constraint checks.

Final live Slice C state on package **1**: events **1 ENTERED, 2 CORRECTED, 3 REVERSED, 4 ENTERED**; occupancy **package 1 → event 4**; derived **ENTERED**.

Local PDF copies (gitignored): `instance/fg032c-uat-sales.pdf` (3202 bytes), `instance/fg032c-uat-cost-class.pdf` (3001 bytes).

## Tests (this live-migrate / UAT session)

Focused after live migrate:

```text
./venv/bin/python -m pytest -q tests/test_quickbooks_ready_fg032.py
```

**37 passed**, 496 warnings, **16.61s**.

Affected regression (auth/org isolation, Estimates, Hub PRICE, Proposal, Supplier Package, FG-009, FG-012, FG-027, FG-029, FG-031):

```text
./venv/bin/python -m pytest -q tests/test_pricing_engine.py tests/test_estimate_output_consistency.py tests/test_estimate_costing_fg027.py tests/test_supplier_workflow_fg029.py tests/test_scope_delivery_fg031.py tests/test_subcontract_quote_fg031.py tests/test_proposals.py tests/test_proposal_pdf.py tests/test_proposal_preview.py tests/test_proposal_immutability.py tests/test_proposal_snapshots.py tests/test_auth_fg018.py tests/test_project_hub.py tests/test_estimate_builder.py tests/test_estimates.py
```

**256 passed**, 1147 warnings, **88.48s**.

Full suite:

```text
./venv/bin/python -m pytest -q
```

**765 passed**, 2669 warnings, **299.75s** (0:04:59).

Bounded office UAT: **97** recorded cases **PASS**. No product-code correction.

Historical occupancy-repair tests (focused 37 / 15.98s; regression 256 / 134.28s; full 765 / 422.30s) remain historical.

## Assumptions and remaining risks

- HTTP empty `actor_display_name` falls back to the authenticated display name. Missing-actor fail-closed is proven at the service boundary.
- Version 31 cannot regenerate a DRAFT because Proposal **11** no longer reconciles with frozen pricing (A+B non-float edit). DRAFT **4** used eligible version **32**.
- Live UAT did not perform an unsafe two-writer race against the office database.
- Package **4** DRAFT remains as labeled UAT residue.
- FG-032 is **not closed**. V1 remains **55% / 3 of 11**. V1-04 **PARTIAL**. V1-05 **PARTIAL**. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**.

**Subsequent status (2026-09-11 FG-032 close + V1-05 rescore):** those remaining-risk pins above are historical to this UAT. Gate is now **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**. Readiness **60% / 4 of 11**. V1-04 remains **PARTIAL**.
- Live QuickBooks API / OAuth / CSV / IIF remain **not authorized**.

## Boundaries not expanded

- FG-032 overall: **CLOSED / OPERATIONAL FOR UAT** (subsequent 2026-09-11 documentation close; this file’s UAT evidence is unchanged)
- V1 scoring: **subsequent V1-05 COMPLETE**; published readiness **60% / 4 of 11** (this UAT file did not itself rescore)
- V1-04: **PARTIAL / CURRENT SCORED PACKAGE**
- V1-05: **COMPLETE** (subsequent close-time rescore; this UAT file did not itself rescore)
- Live QuickBooks API / OAuth / SDK: **POST-V1 / NOT AUTHORIZED**
- CSV / IIF / Excel: **NOT CLAIMED**
- FG-030: **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**
- ADR-008: remains **Proposed**
- BMR DEMO READY: **NO**
- BRAYMAN REAL-LIFE UAT READY: **NO**

## Final Git / Alembic state (after this documentation commit)

| Field | Value |
|-------|--------|
| Branch | `main` |
| Parent | `00de0517b994635dec0be04a6e581167f690f7fe` |
| This commit subject | `docs: record FG-032 Slice C live migration and UAT` |
| Live Alembic current | `f1a2b3c4d5e6 (head)` |
| Repository Alembic head | `f1a2b3c4d5e6` |
| Graph heads | one |
| Product correction | none |
| Application / template / CSS / migration files changed during UAT | none |


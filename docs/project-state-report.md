# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-08-29 |

Update this report at every **completed milestone** and major interruption point.
Distinguish from:

- [session-handoff.md](session-handoff.md) — immediate session continuation
- [milestones.md](milestones.md) — historical milestone record
- [current-state.md](current-state.md) — detailed verified product/repo snapshot

---

# PART A — Standard Project State Report Template

| Field | Content |
|-------|---------|
| Report date | |
| Repository | |
| Current branch | |
| Base commit | |
| Latest completed milestone | |
| Current milestone | |
| Product status | |
| Architecture status | |
| Implemented capabilities | |
| Incomplete work | |
| Database and migration status | |
| Test status | |
| Documentation status | |
| Security or technical risks | |
| Decisions made | |
| Decisions pending | |
| Uncommitted work | |
| Next approved milestone | |
| Exact resume commands | |
| Documents to read first | |
| Approved next Cursor prompt location or summary | |
| Commit status | |

---

# PART B — Current Baseline Report

| Field | Content |
|-------|---------|
| Report date | 2026-08-29 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | FG-008 architecture approval commit on `main` (parent `e2bf33c9377c3990052ae4a3c5f695c8df5d041c`). Confirm with `git rev-parse HEAD`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone | **FG-008** — Labour Engine Phase B foundation (migration `f2c3d4e5f6a7`; live DB still `e1b2c3d4e5f6`) |
| Current milestone | FG-008 **IMPLEMENTED / VERIFIED**; next coded work not authorized |
| Product status | Operational on `main`: CRM, Estimating, Proposals, Change Orders, Plan M005–M010, M011, FG-006 historical ingestion, Labour Engine Phase B foundation. CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract / Pricing Engine **not implemented**. |
| Architecture status | CAR-001 approved. M011 / FG-007 / ADR-028 + FG-006 implemented. FG-008 **IMPLEMENTED / VERIFIED**. ADR-029 **Accepted**. ADR-025 **Proposed**. Review Turnover Protocol governing. |
| Implemented capabilities | Prior coded baseline plus FG-008 Labour Engine (tasks, mappings, standards, candidates, resolution, snapshots, `/labour-engine/` UI). Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001, 73 distinct task strings — **unchanged**. |
| Incomplete work | Live Alembic upgrade `f2c3d4e5f6a7`; Organization-Calibrated Pricing Engine; AI take-off (M012+); four-output package; QuickBooks; Ontario contract/warranty; BUILD field capture. |
| Database and migration status | Migration graph head `f2c3d4e5f6a7`. Live `flask db current` **not** upgraded (`e1b2c3d4e5f6`) — expected until a separate upgrade authorization. |
| Test status | **192 passed**, 119 warnings (`./venv/bin/python -m pytest -q`); **11 passed** (`tests/test_historical_ingestion.py`); **22 passed** (`tests/test_labour_engine.py`) |
| Documentation status | FG-008 **IMPLEMENTED / VERIFIED**; live DB not migrated; ADR-025 unchanged (**Proposed**) |
| Decisions made | FG-008 implementation committed; ORG-001 $65 seeded as org policy only; no silent labour multipliers; snapshots not wired into selling-price |
| Decisions pending | Live Alembic upgrade authorization; ORG-001 canonical task seed contents |
| Uncommitted work | None after this commit |
| Next approved milestone | **NONE** |
| Next candidate milestone | Apply `f2c3d4e5f6a7` to live DB (separate authorization); then Organization-Calibrated Pricing Engine (separate gate) |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-008-labour-engine-phase-b.md](feature-gates/FG-008-labour-engine-phase-b.md) → [architecture/labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md) → [adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) |
| Approved next Cursor prompt location or summary | **None** — live migrate requires a separate prompt |
| Commit status | FG-008 implementation commit on `main`. Confirm with `git log -1`. Parent `820f54afc179279d2435ad3a426b3037548bb45e`. |
| Governance baseline | FG-006 verified on `main`; FG-008 implemented & verified; live DB not yet migrated |

### Resume commands (Cursor Terminal)

```bash
cd /Users/joelbrayman/Desktop/Brayman-Estimator
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
./venv/bin/flask db current
./venv/bin/python -m pytest -q
```

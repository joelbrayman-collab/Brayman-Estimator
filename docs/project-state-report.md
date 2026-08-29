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
| Latest completed **coded** milestone | **FG-006** — Historical Estimate Ingestion Engine Phase B (migration `e1b2c3d4e5f6`) |
| Current milestone | **FG-008 Labour Engine Phase B** — architecture **APPROVED FOR IMPLEMENTATION**; **not implemented** |
| Product status | Operational on `main`: CRM, Estimating, Proposals (+ Accepted immutability), Change Orders, Plan upload (M005), Document Indexing (M007), Sheet Classification / Review (M009), Scale Calibration & Manual Measurement Tools (M010), Organization Foundation & Project Commercial Context (M011), Historical Estimate Ingestion Engine Phase B (FG-006). CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract / Labour Engine **code** / Pricing Engine **not implemented**. |
| Architecture status | CAR-001 approved. M011 / FG-007 / ADR-028 + FG-006 implemented. FG-008 architecture **approved**. ADR-029 **Accepted**. Implementation **not started**. Review Turnover Protocol governing. |
| Implemented capabilities | Unchanged from FG-006/M011 coded baseline (see [current-state.md](current-state.md)). Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001, 73 distinct task strings. |
| Incomplete work | FG-008 **implementation** (not started); Organization-Calibrated Pricing Engine; AI take-off (M012+); four-output package; QuickBooks; Ontario contract/warranty; BUILD field capture. |
| Database and migration status | Current Alembic head `e1b2c3d4e5f6` (unchanged; no migration in FG-008 approval) |
| Test status | **170 passed**, 64 warnings (`./venv/bin/python -m pytest -q`); **11 passed** (`tests/test_historical_ingestion.py`). Exact post-approval run in stopping report. |
| Documentation status | FG-008 **APPROVED FOR IMPLEMENTATION**; ADR-029 **Accepted**; SHA parent pin `e2bf33c`; stale “M009 not started” notes annotated |
| Decisions made | FG-008 architecture **approved**; ADR-029 **Accepted**; Labour Engine **implementation not started**; $65 / 15% remain ORG-001 policy; crew catalog and burden model deferred; no silent labour multipliers |
| Decisions pending | Bounded implementation prompt; ORG-001 canonical task seed contents; actuals persistence timing (recommended defer) |
| Uncommitted work | None after this approval commit |
| Next approved milestone | **NONE** (implementation prompt not yet issued) |
| Next candidate milestone | **FG-008 implementation** after a bounded Cursor prompt |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-008-labour-engine-phase-b.md](feature-gates/FG-008-labour-engine-phase-b.md) → [architecture/labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md) → [adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) |
| Approved next Cursor prompt location or summary | **None yet** — implementation prompt not issued |
| Commit status | Parent `e2bf33c9377c3990052ae4a3c5f695c8df5d041c`. This approval commit SHA: see `git log -1` / stopping report. |
| Governance baseline | FG-006 verified in code; FG-008 architecture approved; no product code in this commit |

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

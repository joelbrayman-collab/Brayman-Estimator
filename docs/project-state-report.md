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
| Current commit / `origin/main` | Implementation `8e11179fb5abb42a68805fe011e84c15e866ea04`; docs reconcile is the live-migrate verification commit |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **FG-009** — Organization-Calibrated Pricing Engine foundation (migration `a3b4c5d6e7f8`; live development/UAT current `a3b4c5d6e7f8`). FG-008 remains **CLOSED — OPERATIONAL FOR UAT**. |
| Current milestone | FG-009 **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. FG-008 remains **CLOSED — OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: CRM, Estimating, Proposals, Change Orders, Plan M005–M010, M011, FG-006 historical ingestion, Labour Engine Phase B foundation, FG-009 Pricing Engine foundation (**OPERATIONAL FOR UAT**). CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. M011 / FG-007 / ADR-028 + FG-006 implemented. FG-008 **IMPLEMENTED / VERIFIED / LIVE-MIGRATED**. ADR-029 **Accepted**. FG-009 **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. ADR-025 **Accepted**; ADR-030 **Accepted**. Review Turnover Protocol governing. |
| Implemented capabilities | Prior coded baseline plus FG-008 Labour Engine plus FG-009 Pricing Engine (policies, snapshots, named methods, resolution, CO method inheritance, `/pricing-engine/` UI). Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | AI take-off (M012+); four-output package; QuickBooks; Ontario contract/warranty; BUILD field capture; Project Hub. |
| Database and migration status | Graph head and live development/UAT `flask db current`: `a3b4c5d6e7f8` (one head). |
| Test status | **228 passed** (`./venv/bin/python -m pytest -q`); **11 passed** (`tests/test_historical_ingestion.py`); **25 passed** (`tests/test_labour_engine.py`); **33 passed** (`tests/test_pricing_engine.py`) |
| Documentation status | FG-009 **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; ADR-025 **Accepted**; ADR-030 **Accepted**; FG-008 **IMPLEMENTED / VERIFIED / LIVE-MIGRATED**. |
| Decisions made | Named methods explicit; 15% GM ≠ 15% markup; ORG-001 seed org-scoped; optional overhead/profit/contingency layers `UNSPECIFIED` until separately governed (distinct from org-approved `NOT_APPLIED`); FG-009-aware COs apply inherited pricing method; new estimates not auto-converted; labour snapshot cost not added to estimate basis by default; Pricing Posture / Execution Risk snapshot-only. |
| Decisions pending | ORG-001 overhead/profit/contingency treatments beyond `UNSPECIFIED`; labour-snapshot inclusion in Direct Cost basis without double-count. |
| Uncommitted work | None expected after the docs-only live-migrate verification commit. |
| Next approved milestone | **NONE.** Next governed action is FG-009 closure review, then prepare the next Feature Gate for AI Take-off / Quantity Extraction Foundation. |
| Next candidate milestone | AI Take-off / Quantity Extraction Foundation — **not started**. Requires its own Feature Gate. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-009-organization-calibrated-pricing-engine.md](feature-gates/FG-009-organization-calibrated-pricing-engine.md) → [architecture/organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md) |
| Approved next Cursor prompt location or summary | **STOP.** FG-009 closure review, then prepare AI Take-off Feature Gate. Do not start AI take-off. |
| Commit status | FG-009 implementation `8e11179` on `main`; live DB migrated; docs reconcile records UAT smoke. |
| Governance baseline | FG-006 verified on `main`; FG-008 implemented, verified, live-migrated; FG-009 implemented, verified, committed, pushed, live-migrated, UAT-smoke-verified |

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

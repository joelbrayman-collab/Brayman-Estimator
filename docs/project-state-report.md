# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-08-30 |

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
| Report date | 2026-08-30 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | 29 Aug cycle closed. FG-010 live-migrate docs `316cc9f11c141d806737bb7caebdb7c37c5bda9b`. This day-end turnover docs commit is current after push. Implementation pins: FG-008 `0569f25`; FG-009 `8e11179`; FG-010 `9665295`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT** (current/head `b4c5d6e7f8a9`). FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | **NONE in progress.** M012 / FG-010 **CLOSED / OPERATIONAL FOR UAT**. 29 Aug day-end reconciliation **COMPLETE**. |
| Product status | Operational on `main`: CRM, Estimating, Proposals, Change Orders, Plan M005–M010, M011, FG-006 historical ingestion, Labour Engine Phase B foundation, FG-009 Pricing Engine foundation (**OPERATIONAL FOR UAT**), FG-010 take-off foundation (mock extractor; **OPERATIONAL FOR UAT**). CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 / FG-009 / FG-010 **CLOSED / OPERATIONAL FOR UAT**. ADR-005/006/007/009/011/031 **Accepted**. ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. |
| Implemented capabilities | Prior coded baseline plus FG-008 Labour Engine plus FG-009 Pricing Engine plus FG-010 take-off foundation: extraction runs, candidates, packages, mock extractor, COUNT-without-scale. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | Phase D estimate mapping; four-output package; QuickBooks; Ontario contract/warranty; BUILD field capture; Project Hub UX; office authentication. |
| Database and migration status | Graph head and live development/UAT `flask db current`: `b4c5d6e7f8a9` (one head). |
| Test status | Dedicated take-off **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical ingestion **11**; full suite **251 passed** |
| Documentation status | 29 Aug day-end Review Turnover package complete (22-point `session-handoff.md`). FG-008/009/010 **CLOSED / OPERATIONAL FOR UAT**. ADR-010 **Proposed**. |
| Decisions made (this turnover) | Docs-only reconciliation of 29 Aug cycle. No product-code changes. No Phase D. No external AI. Next candidate recorded as unauthorized. |
| Decisions pending | Real AI provider; Phase D mapping gate. FG-009 carry-forward: ORG-001 optional layers `UNSPECIFIED`; labour-snapshot Direct Labour Cost not in estimate basis by default. |
| Uncommitted work | None expected after this docs reconciliation commit/push. |
| Next approved milestone | **NONE.** **STOP DEVELOPMENT.** |
| Next candidate milestone | Roadmap item 8 **Project Hub UX** — **NOT STARTED / NOT AUTHORIZED**. Phase D mapping separately **NOT STARTED / NOT AUTHORIZED**. Do not enable a real external AI provider. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [project-state-report.md](project-state-report.md) → [platform-roadmap.md](platform-roadmap.md) |
| Approved next Cursor prompt location or summary | **NONE.** Fresh session must run the startup prompt in `session-handoff.md` §22. Do not start development without a new Feature Gate. |
| Commit status | 29 Aug product commits **COMMITTED / PUSHED**. Live DB **migrated** to `b4c5d6e7f8a9`. Day-end turnover docs **this commit**. |
| Governance baseline | FG-008 / FG-009 / FG-010 closed/operational for UAT; M012 operational for UAT; turnover complete |

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

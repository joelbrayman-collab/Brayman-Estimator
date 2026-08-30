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
| Current commit / `origin/main` | FG-011 implementation on `main` (verify `git log -1` after push). Governance pin `225731a2208e16fea8558a048e8c34f0f4879549`. Implementation pins: FG-008 `0569f25`; FG-009 `8e11179`; FG-010 `9665295`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT** (current/head `b4c5d6e7f8a9`). FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | **NONE in product code.** [FG-011](feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**. M012 / FG-010 **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: CRM, Estimating, Proposals, Change Orders, Plan M005–M010, M011, FG-006 historical ingestion, Labour Engine Phase B foundation, FG-009 Pricing Engine foundation (**OPERATIONAL FOR UAT**), FG-010 take-off foundation (mock extractor; **OPERATIONAL FOR UAT**), FG-011 Project Hub UX (**OPERATIONAL FOR UAT**). CalibAi V1 / BUILD field / four-output package / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 / FG-009 / FG-010 / FG-011 **CLOSED / OPERATIONAL FOR UAT**. ADR-019 **Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. |
| Implemented capabilities | Prior coded baseline plus FG-008 / FG-009 / FG-010 plus FG-011 Project Hub: `/projects/<id>` lifecycle read/link UX. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | Phase D estimate mapping; four-output package; QuickBooks; Ontario contract/warranty; BUILD field capture; office authentication. |
| Database and migration status | Graph head and live development/UAT `flask db current`: `b4c5d6e7f8a9` (one head). FG-011 made **no** schema change. |
| Test status | Dedicated Project Hub **13 passed**; take-off **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical ingestion **11**; full suite **264 passed** |
| Documentation status | FG-011 **CLOSED / OPERATIONAL FOR UAT**. FG-008/009/010 remain closed. ADR-010 **Proposed**. |
| Decisions made (this implementation pass) | Evolve `/projects/<id>` only; Projects owns hub UX; read/link stored facts; conservative pricing/labour presentation; Future labels for MONITOR/LEARN/field BUILD/QB/contracts/four-output/real AI. No schema/ADR/Phase D. |
| Decisions pending | Real AI provider; Phase D mapping gate. FG-009 carry-forward: ORG-001 optional layers `UNSPECIFIED`; labour-snapshot Direct Labour Cost not in estimate basis by default. |
| Uncommitted work | None expected after this implementation commit/push. |
| Next approved milestone | **NONE.** STOP. Do not start Phase D or another Feature Gate. |
| Next candidate milestone | Estimate-output consistency (roadmap item 9), separately gated. Phase D mapping remains **NOT STARTED / NOT AUTHORIZED**. Do not enable a real external AI provider. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-011-project-hub-ux.md](feature-gates/FG-011-project-hub-ux.md) → [modules/projects.md](modules/projects.md) |
| Approved next Cursor prompt location or summary | **STOP.** Do not start Phase D. Do not enable external AI. Next product work requires a new Feature Gate. |
| Commit status | FG-011 implementation **this commit**. Live DB remains `b4c5d6e7f8a9`. |
| Governance baseline | FG-008 / FG-009 / FG-010 / FG-011 closed/operational for UAT; M012 operational for UAT; Phase D not started |

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

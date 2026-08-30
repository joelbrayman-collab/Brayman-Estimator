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
| Current commit / `origin/main` | FG-010 implementation `9665295ace673a46a8c645ed0598e5e91d41931c`. Docs reconciliation follows live-migrate/UAT. FG-009 implementation `8e11179fb5abb42a68805fe011e84c15e866ea04`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **M012 / FG-010** AI Take-off foundation **LIVE-MIGRATED / UAT-SMOKE-VERIFIED** (current/head `b4c5d6e7f8a9`). FG-009 remains **CLOSED / OPERATIONAL FOR UAT**. FG-008 remains **CLOSED — OPERATIONAL FOR UAT**. |
| Current milestone | **M012 / FG-010 IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. **AI TAKE-OFF FOUNDATION OPERATIONAL FOR UAT**. FG-009 remains **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: CRM, Estimating, Proposals, Change Orders, Plan M005–M010, M011, FG-006 historical ingestion, Labour Engine Phase B foundation, FG-009 Pricing Engine foundation (**OPERATIONAL FOR UAT**), FG-010 take-off foundation (mock extractor; **OPERATIONAL FOR UAT**). CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 **IMPLEMENTED / VERIFIED / LIVE-MIGRATED**. FG-009 **CLOSED / OPERATIONAL FOR UAT**. FG-010 **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. ADR-005/006/007/009/011/031 **Accepted**. ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. |
| Implemented capabilities | Prior coded baseline plus FG-008 Labour Engine plus FG-009 Pricing Engine plus FG-010 take-off foundation: extraction runs, candidates, packages, mock extractor, COUNT-without-scale. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | Phase D estimate mapping; four-output package; QuickBooks; Ontario contract/warranty; BUILD field capture; Project Hub. |
| Database and migration status | Graph head and live development/UAT `flask db current`: `b4c5d6e7f8a9` (one head). |
| Test status | Dedicated take-off **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical ingestion **11**; full suite **251 passed** |
| Documentation status | FG-010 **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; ADR-005/006/007/009/011/031 **Accepted**; ADR-010 **Proposed**. |
| Decisions made (this implementation pass) | Apply `b4c5d6e7f8a9` live; synthetic FG-010 UAT + browser smoke. Provider-neutral mock only; COUNT without scale; no estimate/labour/pricing writes. |
| Decisions pending | Real AI provider; Phase D mapping gate. FG-009 carry-forward: ORG-001 optional layers `UNSPECIFIED`; labour-snapshot Direct Labour Cost not in estimate basis by default. |
| Uncommitted work | None expected after this docs reconciliation commit/push. |
| Next approved milestone | **NONE.** **STOP DEVELOPMENT.** Day-End Reconciliation / Review Turnover audit before any further development. |
| Next candidate milestone | After day-end turnover: Project Hub / Phase D, separately gated. Do not enable a real external AI provider. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) → [architecture/ai-takeoff-quantity-extraction-foundation.md](architecture/ai-takeoff-quantity-extraction-foundation.md) → [adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md](adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) |
| Approved next Cursor prompt location or summary | **STOP DEVELOPMENT.** Full Day-End Reconciliation / Repository / Documentation / Storage / Review Turnover audit. Do not enable a real external AI provider. Do not start Phase D. Do not start another milestone. |
| Commit status | FG-010 implementation **COMMITTED / PUSHED**. Live DB **migrated** to `b4c5d6e7f8a9`. Docs reconciliation **this commit**. |
| Governance baseline | FG-008 and FG-009 closed/operational for UAT; FG-010 foundation operational for UAT |

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

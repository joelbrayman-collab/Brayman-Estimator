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
| Current commit / `origin/main` | FG-010 implementation commit on `main` (parent `5bd6c772a093e9ca3ad506e17f0629eabe86f53c`). FG-009 implementation `8e11179fb5abb42a68805fe011e84c15e866ea04`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **M012 / FG-010** AI Take-off foundation **COMMITTED / PUSHED** / **NOT YET LIVE-MIGRATED** (graph head `b4c5d6e7f8a9`; live current `a3b4c5d6e7f8`). FG-009 remains **CLOSED / OPERATIONAL FOR UAT**. FG-008 remains **CLOSED — OPERATIONAL FOR UAT**. |
| Current milestone | **M012 / FG-010 IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** — **NOT YET LIVE-MIGRATED**. FG-009 remains **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: CRM, Estimating, Proposals, Change Orders, Plan M005–M010, M011, FG-006 historical ingestion, Labour Engine Phase B foundation, FG-009 Pricing Engine foundation (**OPERATIONAL FOR UAT**), FG-010 take-off foundation (mock extractor; **not live-migrated**; browser UAT **not yet performed**). CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 **IMPLEMENTED / VERIFIED / LIVE-MIGRATED**. FG-009 **CLOSED / OPERATIONAL FOR UAT**. FG-010 **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** / **NOT YET LIVE-MIGRATED**. ADR-005/006/007/009/011/031 **Accepted**. ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. |
| Implemented capabilities | Prior coded baseline plus FG-008 Labour Engine plus FG-009 Pricing Engine plus FG-010 take-off foundation: extraction runs, candidates, packages, mock extractor, COUNT-without-scale. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | FG-010 live-migrate and browser/UAT smoke; Phase D estimate mapping; four-output package; QuickBooks; Ontario contract/warranty; BUILD field capture; Project Hub. |
| Database and migration status | Graph head `b4c5d6e7f8a9`. Live development/UAT `flask db current`: `a3b4c5d6e7f8`. **Do not apply live migration.** |
| Test status | Dedicated take-off **18 passed**; Plan Intelligence combined **56 passed**; Pricing **33**; Labour **25**; historical ingestion **11**; full suite **251 passed** |
| Documentation status | FG-010 **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** / **NOT YET LIVE-MIGRATED**; ADR-005/006/007/009/011/031 **Accepted**; ADR-010 **Proposed**. Browser/live UAT **not yet performed**. |
| Decisions made (this implementation pass) | Commit and push the reviewed FG-010 foundation. Provider-neutral mock only; COUNT without scale; no estimate/labour/pricing writes; no live migrate. |
| Decisions pending | Live-migrate authorization; real AI provider; Phase D mapping gate. FG-009 carry-forward: ORG-001 optional layers `UNSPECIFIED`; labour-snapshot Direct Labour Cost not in estimate basis by default. |
| Uncommitted work | None expected after this commit/push. |
| Next approved milestone | **NONE.** Next governed action is a **separate live-migrate + UAT smoke** prompt. |
| Next candidate milestone | Apply `b4c5d6e7f8a9` to live development/UAT (separate authorization). Then Project Hub / Phase D, separately gated. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) → [architecture/ai-takeoff-quantity-extraction-foundation.md](architecture/ai-takeoff-quantity-extraction-foundation.md) → [adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md](adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) |
| Approved next Cursor prompt location or summary | **STOP.** Separate authorization to apply `b4c5d6e7f8a9` live and perform bounded synthetic browser/UAT smoke. Do not enable a real external AI provider. Do not start Phase D. |
| Commit status | FG-010 implementation **COMMITTED / PUSHED**. Live DB **not** migrated. |
| Governance baseline | FG-008 and FG-009 closed/operational for UAT; FG-010 foundation committed/pushed, not live-migrated |

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

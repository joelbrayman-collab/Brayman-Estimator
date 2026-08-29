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
| Current commit / `origin/main` | `bc37463a15dbb3a97e6250686ba5b0a4d78f1955` (docs: FG-009 live-migrate verification). FG-009 implementation `8e11179fb5abb42a68805fe011e84c15e866ea04`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **FG-009** — Organization-Calibrated Pricing Engine foundation (migration `a3b4c5d6e7f8`; live development/UAT current `a3b4c5d6e7f8`). FG-008 remains **CLOSED — OPERATIONAL FOR UAT**. |
| Current milestone | **M012 / FG-010 APPROVED FOR IMPLEMENTATION** — **NOT IMPLEMENTED**. FG-009 remains **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: CRM, Estimating, Proposals, Change Orders, Plan M005–M010, M011, FG-006 historical ingestion, Labour Engine Phase B foundation, FG-009 Pricing Engine foundation (**OPERATIONAL FOR UAT**). AI take-off **not implemented**. CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 **IMPLEMENTED / VERIFIED / LIVE-MIGRATED**. FG-009 **CLOSED / OPERATIONAL FOR UAT**. FG-010 **APPROVED FOR IMPLEMENTATION**. ADR-005/006/007/009/011/031 **Accepted**. ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | Prior coded baseline plus FG-008 Labour Engine plus FG-009 Pricing Engine. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. No AI take-off tables. |
| Incomplete work | AI take-off **implementation** (M012 / FG-010); Phase D estimate mapping; four-output package; QuickBooks; Ontario contract/warranty; BUILD field capture; Project Hub. |
| Database and migration status | Graph head and live development/UAT `flask db current`: `a3b4c5d6e7f8` (one head). **No new migration in this pass.** |
| Test status | Plan Intelligence combined **51 passed**; Pricing **33**; Labour **25**; historical ingestion **11**; full suite **228** |
| Documentation status | FG-010 **APPROVED FOR IMPLEMENTATION** / **NOT IMPLEMENTED**; ADR-005/006/007/009/011/031 **Accepted**; ADR-010 **Proposed**. |
| Decisions made (this governance pass) | FG-010 approved; COUNT is dimensionless; mapping out of M012; real external AI provider not authorized. |
| Decisions pending | FG-010 implementation prompt; real AI provider; confidence UI cut-points; Phase D mapping gate. FG-009 carry-forward: ORG-001 optional layers `UNSPECIFIED`; labour-snapshot Direct Labour Cost not in estimate basis by default. |
| Uncommitted work | None expected after the FG-010 approval docs commit. |
| Next approved milestone | **NONE coded.** Next governed action is a **separate bounded FG-010 implementation prompt**. |
| Next candidate milestone | **M012 / FG-010** implementation (provider-neutral). |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) → [architecture/ai-takeoff-quantity-extraction-foundation.md](architecture/ai-takeoff-quantity-extraction-foundation.md) → [adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md](adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) |
| Approved next Cursor prompt location or summary | **STOP.** Issue a separate bounded FG-010 implementation prompt. Do not implement in this pass. Do not enable a real external AI provider. |
| Commit status | Parent `bc37463`. This pass is the FG-010 approval documentation commit. |
| Governance baseline | FG-008 and FG-009 closed/operational for UAT; FG-010 approved for implementation only |

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

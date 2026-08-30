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
| Current commit / `origin/main` | This FG-013 draft documentation commit (verify `git log -1` after push). Prior: ADR-021 `d41c4d92ee009cdc6679b140ecd44789362077f6`. Product: FG-012 `0b403d6aa51381d3763cf3dc9d5d96e096d5ab93`. Implementation pins: FG-008 `0569f25`; FG-009 `8e11179`; FG-010 `9665295`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT** (current/head `b4c5d6e7f8a9`). FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | **NONE in product code.** [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **DRAFT FOR JOEL REVIEW** (implementation not authorized). [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (docs only; MONITOR not implemented). [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: CRM, Estimating, Proposals, Change Orders, Plan M005–M010, M011, FG-006 historical ingestion, Labour Engine Phase B foundation, FG-009 Pricing Engine foundation (**OPERATIONAL FOR UAT**), FG-010 take-off foundation (mock extractor; **OPERATIONAL FOR UAT**), FG-011 Project Hub UX (**OPERATIONAL FOR UAT**), FG-012 estimate-output consistency (**OPERATIONAL FOR UAT**). CalibAi V1 / BUILD field / four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 / FG-009 / FG-010 / FG-011 / FG-012 **CLOSED / OPERATIONAL FOR UAT**. ADR-019 **Accepted**. **ADR-021 Accepted** (MONITOR baseline / Project Gross Margin; not implemented). ADR-005/006/007/009/011/031 **Accepted**. ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. |
| Implemented capabilities | Prior coded baseline plus FG-008 / FG-009 / FG-010 / FG-011 plus FG-012: internal cost breakdown; named-method Proposal totals from frozen snapshot; customer PDF without Overhead/Profit rows. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty; BUILD field capture; MONITOR implementation; office authentication; FG-013 historical-upload **implementation**; industry benchmarking. |
| Database and migration status | Graph head and live development/UAT `flask db current`: `b4c5d6e7f8a9` (one head). FG-011 and FG-012 made **no** schema change. |
| Test status | Dedicated FG-012 **19 passed**; Project Hub **13**; take-off **18**; Plan Intelligence combined **56**; Pricing **33**; Labour **25**; historical ingestion **11**; full suite **283 passed** |
| Documentation status | FG-013 **DRAFT FOR JOEL REVIEW** (multi-file/folder UX locked; implementation not authorized). ADR-021 **Accepted** (docs only). FG-012 **CLOSED / OPERATIONAL FOR UAT**. FG-011 **CLOSED / OPERATIONAL FOR UAT**. FG-008/009/010 remain closed. ADR-010 **Proposed**. |
| Decisions made (this governance pass) | ADR-021 Accepted: Project Gross Margin (not net profit); frozen composed baseline (locked EstimateVersion + pricing snapshot when present + Accepted Proposal + approved CO deltas as separate layers); floating drafts prohibited; MONITOR is a comparison/read layer; actuals/BUILD/LEARN/benchmarking not implemented. No schema. No Feature Gate. |
| Decisions pending | Real AI provider; Phase D mapping gate; next product gate (historical-upload onboarding vs auth/BUILD — not authorized here). FG-009 carry-forward: ORG-001 optional layers `UNSPECIFIED`; labour-snapshot Direct Labour Cost not in estimate basis by default (ADR-021 comparability note). |
| Uncommitted work | None expected after this implementation commit/push. |
| Next approved milestone | **NONE.** **STOP DEVELOPMENT.** Do not implement FG-013. Do not implement MONITOR. Do not start Phase D. |
| Next candidate milestone | Phase D mapping remains **NOT STARTED / NOT AUTHORIZED**. MONITOR implementation remains **not authorized**. Do not enable a real external AI provider. Authentication remains later/separately gated. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [adr/ADR-021-monitor-commercial-baseline.md](adr/ADR-021-monitor-commercial-baseline.md) → [feature-gates/FG-012-estimate-output-consistency.md](feature-gates/FG-012-estimate-output-consistency.md) |
| Approved next Cursor prompt location or summary | **None.** Stop. Do not implement MONITOR. Do not start Phase D. Do not enable external AI. |
| Commit status | FG-013 **draft checkpoint** **this commit**. Live DB remains `b4c5d6e7f8a9`. No schema. No product code. Implementation not authorized. |
| Governance baseline | ADR-021 Accepted; FG-008 / FG-009 / FG-010 / FG-011 / FG-012 closed/operational for UAT; M012 operational for UAT; Phase D not started; MONITOR not implemented |

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

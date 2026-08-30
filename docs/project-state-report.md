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
| Current commit / `origin/main` | This FG-014 governance commit (verify `git log -1` after push). Started from `130b3fd35114014f0635d9a70e7cb3096647d480`. FG-013 product: `974136bb2ac7d2f61acf71b53f81a2ae55f132b1`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT**. **FG-013 CLOSED / OPERATIONAL FOR UAT** (`c5d6e7f8a9b0` live current=head). FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**. Material Catalogue [ADR-034](adr/ADR-034-canonical-material-identity-and-ownership.md) / [ADR-035](adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) / [ADR-036](adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** (not implemented). [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (docs only; MONITOR not implemented). [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: prior baseline plus FG-013 office historical upload **CLOSED / OPERATIONAL FOR UAT**. CalibAi V1 / BUILD field / four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / **FG-013 CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted** (not implemented). ADR-019 **Accepted**. **ADR-021 Accepted**. **ADR-032 Accepted**. **ADR-033 Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Supplier integration **not started**. Bulk supplier onboarding **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-013: multi-file UPLOAD PREVIOUS ESTIMATES; `HistoricalUploadAttempt`; ADR-032 app-managed custody; unknown-layout quarantine; TIER_A wording. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | FG-014 **implementation**; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty; BUILD field capture; MONITOR implementation; office authentication; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding. |
| Database and migration status | Graph head: `c5d6e7f8a9b0`. Live development/UAT `flask db current`: `c5d6e7f8a9b0` (**VERIFIED APPLIED** before reconciliation; this pass did **not** upgrade). One graph head. |
| Test status | Dedicated FG-013 **27 passed**; historical **11**; labour **25**; pricing **33**; FG-012 **19**; Project Hub **13**; take-off **18**; Plan Intelligence combined **56**; full suite **310 passed** |
| Documentation status | FG-013 **CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted** (not implemented). ADR-032 **Accepted**. **ADR-033 Accepted**. ADR-021 **Accepted** (docs only). FG-012 **CLOSED / OPERATIONAL FOR UAT**. ADR-008 / ADR-010 **Proposed**. Bulk supplier onboarding pinned FUTURE only. |
| Decisions made (this implementation pass) | Approved FG-014 Material Catalogue V1 (identity + CostItem link + office UX; implementation not started). Seed via same additive Alembic revision as table. Ordinary org users must not mutate platform identity. Pinned governed **bulk supplier onboarding** as FUTURE / NOT IMPLEMENTED (does not expand FG-014; no Supplier Feature Gate). ADR-008 remains Proposed. |
| Decisions pending | FG-014 **implementation prompt**. Real AI provider; Phase D mapping gate. FG-009 carry-forward unchanged. Darcy commercial terms unset. Supplier Feature Gate **not authorized**. Bulk supplier onboarding remains future. |
| Uncommitted work | None expected after this docs commit/push. |
| Next approved milestone | **FG-014 implementation** when separately authorized. Do not implement in this governance pass. Do not `flask db upgrade`. Do not implement MONITOR. Do not start Phase D. Do not start supplier/Winchester POC or bulk supplier onboarding. Do not accept ADR-008. |
| Next candidate milestone | FG-014 implementation (lumber/sheets identity). Phase D mapping remains **NOT STARTED / NOT AUTHORIZED**. MONITOR implementation remains **not authorized**. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) → [architecture/material-catalogue-architecture.md](architecture/material-catalogue-architecture.md) |
| Approved next Cursor prompt location or summary | **FG-014 implementation** (bounded; identity-only lumber/sheets; one additive migration if that prompt authorizes). Do not accept ADR-008. Do not start Phase D, supplier POC, or bulk supplier onboarding. Do not `flask db upgrade` until a live-migrate prompt. |
| Commit status | FG-014 **Feature Gate + future supplier-onboarding pin** this commit. Graph head / live current `c5d6e7f8a9b0`. |
| Governance baseline | FG-013 CLOSED / OPERATIONAL FOR UAT; FG-014 APPROVED FOR IMPLEMENTATION / IMPLEMENTATION NOT STARTED; ADR-034/035/036 Accepted (not implemented); ADR-032 Accepted; ADR-033 Accepted; ADR-008 Proposed; ADR-021 Accepted; FG-008–FG-012 closed/operational for UAT; Phase D not started; MONITOR not implemented; bulk supplier onboarding FUTURE only |

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

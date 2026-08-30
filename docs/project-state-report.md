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
| Current commit / `origin/main` | This Material Catalogue ADR-docs commit (verify `git log -1` after push). Started from `b53d9e7150e43b173bad3c26eee8e829529773e5`. FG-013 product: `974136bb2ac7d2f61acf71b53f81a2ae55f132b1`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT**. **FG-013 CLOSED / OPERATIONAL FOR UAT** (`c5d6e7f8a9b0` live current=head). FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue [ADR-034](adr/ADR-034-canonical-material-identity-and-ownership.md) / [ADR-035](adr/ADR-035-material-quantity-uom-and-requirement-boundary.md) / [ADR-036](adr/ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** (not implemented; no Feature Gate). [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (docs only; MONITOR not implemented). [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: prior baseline plus FG-013 office historical upload **CLOSED / OPERATIONAL FOR UAT**. CalibAi V1 / BUILD field / four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / **FG-013 CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted** (not implemented). ADR-019 **Accepted**. **ADR-021 Accepted**. **ADR-032 Accepted**. **ADR-033 Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Supplier integration **not started**. |
| Implemented capabilities | Prior coded baseline plus FG-013: multi-file UPLOAD PREVIOUS ESTIMATES; `HistoricalUploadAttempt`; ADR-032 app-managed custody; unknown-layout quarantine; TIER_A wording. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | Material Catalogue Feature Gate then identity implementation; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty; BUILD field capture; MONITOR implementation; office authentication; industry benchmarking; supplier/Winchester POC. |
| Database and migration status | Graph head: `c5d6e7f8a9b0`. Live development/UAT `flask db current`: `c5d6e7f8a9b0` (**VERIFIED APPLIED** before reconciliation; this pass did **not** upgrade). One graph head. |
| Test status | Dedicated FG-013 **27 passed**; historical **11**; labour **25**; pricing **33**; FG-012 **19**; Project Hub **13**; take-off **18**; Plan Intelligence combined **56**; full suite **310 passed** |
| Documentation status | FG-013 **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted** (not implemented; no Feature Gate). ADR-032 **Accepted**. **ADR-033 Accepted**. ADR-021 **Accepted** (docs only). FG-012 **CLOSED / OPERATIONAL FOR UAT**. ADR-008 / ADR-010 **Proposed**. |
| Decisions made (this implementation pass) | Accepted ADR-034 (CalibAi identity; CostItem remains costing), ADR-035 (UOM/waste/exploded fulfillment; MaterialRequirement not authorized), ADR-036 (evidence classes; living intelligence; promotions; mapping). ADR-008 remains Proposed. No Feature Gate. |
| Decisions pending | Material Catalogue **Feature Gate** (identity-only lumber/sheets). Real AI provider; Phase D mapping gate. FG-009 carry-forward unchanged. Darcy commercial terms unset. Supplier Feature Gate **not authorized**. |
| Uncommitted work | None expected after this docs commit/push. |
| Next approved milestone | **Material Catalogue Feature Gate** (docs) when separately authorized. Do not implement until that gate is approved. Do not `flask db upgrade`. Do not implement MONITOR. Do not start Phase D. Do not start supplier/Winchester POC. Do not accept ADR-008 in the identity gate. |
| Next candidate milestone | Material Catalogue Feature Gate (lumber/sheets identity). Phase D mapping remains **NOT STARTED / NOT AUTHORIZED**. MONITOR implementation remains **not authorized**. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [architecture/material-catalogue-architecture.md](architecture/material-catalogue-architecture.md) → [adr/ADR-034-canonical-material-identity-and-ownership.md](adr/ADR-034-canonical-material-identity-and-ownership.md) |
| Approved next Cursor prompt location or summary | **Material Catalogue Feature Gate** (docs only; do not implement). Identity-only lumber/sheets. Do not accept ADR-008. Do not start Phase D or supplier POC. Do not `flask db upgrade`. |
| Commit status | Material Catalogue **ADR docs** this commit. Graph head / live current `c5d6e7f8a9b0`. |
| Governance baseline | FG-013 CLOSED / OPERATIONAL FOR UAT; ADR-034/035/036 Accepted (not implemented); ADR-032 Accepted; ADR-033 Accepted; ADR-008 Proposed; ADR-021 Accepted; FG-008–FG-012 closed/operational for UAT; Phase D not started; MONITOR not implemented |

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

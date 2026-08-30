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
| Current commit / `origin/main` | This docs commit after live-migrate/UAT. Started from `a100caa2c1f5e1c29e79449c8ce5a144ff945f23`. Implementation `976cc4a4942ae346b9843a77126f89969bba2b6e`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **FG-014 CLOSED / OPERATIONAL FOR UAT** (`d6e7f8a9b0c1` live current=head; flash repair `1a2e34c`; office re-UAT port **5007**). **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT**. **FG-013 CLOSED / OPERATIONAL FOR UAT**. FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue ADR-034/035/036 **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (docs only; MONITOR not implemented). [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: FG-014 Material Catalogue V1 **CLOSED / OPERATIONAL FOR UAT**. CalibAi V1 / BUILD field / four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / **FG-013 CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. ADR-019 **Accepted**. **ADR-021 Accepted**. **ADR-032 Accepted**. **ADR-033 Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Supplier integration **not started**. Bulk supplier onboarding **FUTURE / NOT IMPLEMENTED**. Permit & Approvals Report **FUTURE / NOT IMPLEMENTED**. Organization Brand Profile **FUTURE / NOT IMPLEMENTED**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-014 live: platform canonical materials (27 lumber/sheet seed rows); optional Material CostItem link; office `/material-catalogue/`. Catalogue-link flash repaired; office re-UAT **PASSED** on port **5007**. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty; BUILD field capture; MONITOR implementation; office authentication; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; Permit & Approvals Report; Organization Brand Profile; Change Order document family. |
| Database and migration status | Graph head: `d6e7f8a9b0c1`. Live development/UAT `flask db current`: `d6e7f8a9b0c1` (**verified applied** 2026-08-30). One graph head. |
| Test status | Dedicated FG-014 **35 passed**; FG-013 **27**; historical **11**; labour **25**; pricing **33**; FG-012 **19**; Project Hub **13**; take-off **18**; Plan Intelligence combined **56**; full suite **345 passed** |
| Documentation status | [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. FG-013 **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. ADR-032 **Accepted**. **ADR-033 Accepted**. ADR-021 **Accepted** (docs only). FG-012 **CLOSED / OPERATIONAL FOR UAT**. ADR-008 / ADR-010 **Proposed**. Bulk supplier onboarding pinned FUTURE only. Permit & Approvals Report pinned FUTURE only ([permit-and-approvals-report.md](architecture/permit-and-approvals-report.md)). Organization Brand Profile pinned FUTURE only ([organization-brand-profile.md](architecture/organization-brand-profile.md)). Change Order document family pinned FUTURE only ([change-order-document-family.md](architecture/change-order-document-family.md)). |
| Decisions made (this branding / Change Order document pin) | Recorded Organization Brand Profile and Change Order document family as **FUTURE / NOT IMPLEMENTED** pins. No product-code change. No Feature Gate. No ADR. Did not reorder next action. FG-014 remains **CLOSED / OPERATIONAL FOR UAT**. |
| Decisions pending | Real AI provider; Phase D mapping gate. FG-009 carry-forward unchanged. Darcy commercial terms unset. Supplier Feature Gate **not authorized**. Bulk supplier onboarding remains future. Permit Intelligence architecture reconnaissance not started. Whether Organization Branding becomes a small platform prerequisite Feature Gate — later. How Change Order document snapshot / email / acceptance evidence is gated — later. |
| Uncommitted work | None expected after this docs commit/push. |
| Next approved milestone | **Permit Intelligence Engine architecture reconnaissance** (repository-first; not implementation). Do not `flask db upgrade` again. Do not implement MONITOR. Do not start Phase D. Do not start supplier/Winchester POC or bulk supplier onboarding. Do not accept ADR-008. Do not implement the Permit & Approvals Report. Do not implement Organization Brand Profile or the Change Order document family. |
| Next candidate milestone | Permit Intelligence reconnaissance. Supplier Catalogue onboarding/mapping remains **not authorized**. Phase D mapping remains **NOT STARTED / NOT AUTHORIZED**. MONITOR implementation remains **not authorized**. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) → [architecture/material-catalogue-architecture.md](architecture/material-catalogue-architecture.md) |
| Approved next Cursor prompt location or summary | **Permit Intelligence Engine architecture reconnaissance** only. Do not implement. Do not accept ADR-008. Do not start Phase D, supplier POC, or bulk supplier onboarding. Do not implement Organization Brand Profile or the Change Order document family. |
| Commit status | Organization Brand Profile + Change Order document family **docs pin** this commit. Live current=head `d6e7f8a9b0c1`. FG-014 remains closed. |
| Governance baseline | FG-014 CLOSED / OPERATIONAL FOR UAT; live current=head d6e7f8a9b0c1; FG-013 CLOSED / OPERATIONAL FOR UAT; ADR-034/035/036 Accepted; ADR-032 Accepted; ADR-033 Accepted; ADR-008 Proposed; ADR-021 Accepted; FG-008–FG-012 closed/operational for UAT; Phase D not started; MONITOR not implemented; bulk supplier onboarding FUTURE only; Permit & Approvals Report FUTURE only; Organization Brand Profile FUTURE only; Change Order document family FUTURE only |

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

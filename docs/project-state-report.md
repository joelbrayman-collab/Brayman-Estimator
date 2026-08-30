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
| Current commit / `origin/main` | FG-016 close (this docs commit). Implementation `a709829d32d94ab2baf36f142ad0095254ba3d3a`. FG-015 implementation `e6462a9ee8688b6599ab1a7b0e91232e8d53db3a`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **FG-016 CLOSED / OPERATIONAL FOR UAT** (live current=head `f8a9b0c1d2e3`; Pratt UAT project 9 port 5009). **FG-015 CLOSED / OPERATIONAL FOR UAT**. **FG-014 CLOSED / OPERATIONAL FOR UAT**. **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT**. **FG-013 CLOSED / OPERATIONAL FOR UAT**. FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. Permit Intelligence ADR-037/038/039 **Accepted**. [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue ADR-034/035/036 **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (docs only; MONITOR not implemented). [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: FG-016 Ontario / Ottawa Permit Intelligence POC **CLOSED / OPERATIONAL FOR UAT**. FG-015 Permit Foundation V1 **CLOSED / OPERATIONAL FOR UAT**. FG-014 Material Catalogue V1 **CLOSED / OPERATIONAL FOR UAT**. CalibAi V1 / BUILD field / four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / **FG-013 CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-019 **Accepted**. **ADR-021 Accepted**. **ADR-032 Accepted**. **ADR-033 Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Supplier integration **not started**. Organization Brand Profile **FUTURE / NOT IMPLEMENTED**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-016: platform `permit_rules` (10 APPROVED Ottawa coach-house rows); `project_permit_facts`; immutable `permit_analyses` / `permit_findings`; Hub PLAN report state; office HTML + neutral CalibAi PDF. FG-015 location/jurisdiction/preliminary profile unchanged. |
| Incomplete work | Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty; BUILD field capture; MONITOR implementation; office authentication; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Organization Brand Profile; Change Order document family. |
| Database and migration status | Graph head `f8a9b0c1d2e3`. Live current `f8a9b0c1d2e3`. One graph head. Applied `e7f8a9b0c1d2` → `f8a9b0c1d2e3`. |
| Test status | Dedicated FG-016 **37 passed**; FG-015 **19**; FG-014 **35**; FG-013 **27**; historical **11**; labour **25**; pricing **33**; FG-012 **19**; Project Hub **13**; take-off **18**; Plan Intelligence combined **56**; full suite **401 passed** |
| Documentation status | [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. FG-013 **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-032 **Accepted**. **ADR-033 Accepted**. ADR-021 **Accepted** (docs only). FG-012 **CLOSED / OPERATIONAL FOR UAT**. ADR-008 / ADR-010 **Proposed**. Organization Brand Profile pinned FUTURE only. Change Order document family pinned FUTURE only. |
| Decisions made (this FG-016 live-migrate/UAT pass) | Applied `e7f8a9b0c1d2` → `f8a9b0c1d2e3`. Pratt UAT project 9 on port 5009 from signed Precision Home Design set dated April 1 2026. Findings from APPROVED rules + reviewed facts only. HTML/PDF same snapshot. Immutability verified (v1 pinned; v3 current). No product-code change. No AHJ approval claimed. |
| Decisions pending | Next Feature Gate not authorized. Real AI provider; Phase D mapping gate. FG-009 carry-forward unchanged. Darcy commercial terms unset. Supplier Feature Gate **not authorized**. |
| Uncommitted work | None expected after this implementation commit/push. |
| Next approved milestone | **STOP.** Do not begin national permit expansion, Phase D, Organization Branding, Change Order documents, supplier integration, or external AI / runtime web. |
| Next candidate milestone | Not authorized. Supplier Catalogue onboarding/mapping remains **not authorized**. Phase D mapping remains **NOT STARTED / NOT AUTHORIZED**. MONITOR implementation remains **not authorized**. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) → [architecture/permit-rules-ontario-ottawa-sources.md](architecture/permit-rules-ontario-ottawa-sources.md) |
| Approved next Cursor prompt location or summary | **STOP.** Do not begin national permit expansion. Do not accept ADR-008. Do not start Phase D, supplier POC, branding, or Change Order documents. |
| Commit status | FG-016 close (this docs commit) on `main`. Live current = head `f8a9b0c1d2e3`. FG-016 **CLOSED / OPERATIONAL FOR UAT**. Implementation ancestor `a709829d32d94ab2baf36f142ad0095254ba3d3a`. |
| Governance baseline | FG-016 CLOSED / OPERATIONAL FOR UAT; FG-015 CLOSED / OPERATIONAL FOR UAT; FG-014 CLOSED / OPERATIONAL FOR UAT; live current=head f8a9b0c1d2e3; FG-013 CLOSED / OPERATIONAL FOR UAT; ADR-034/035/036 Accepted; ADR-037/038/039 Accepted; ADR-032 Accepted; ADR-033 Accepted; ADR-008 Proposed; ADR-021 Accepted; FG-008–FG-012 closed/operational for UAT; Phase D not started; MONITOR not implemented; Organization Brand Profile FUTURE only; Change Order document family FUTURE only |

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

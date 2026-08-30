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
| Current commit / `origin/main` | FG-015 Feature Gate governance docs commit after this pass. Prior architecture commit `5474c47189f67645cc6a636cdfa054cf3c6660f9`. Product unchanged. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **FG-014 CLOSED / OPERATIONAL FOR UAT** (`d6e7f8a9b0c1` live current=head; flash repair `1a2e34c`; office re-UAT port **5007**). **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT**. **FG-013 CLOSED / OPERATIONAL FOR UAT**. FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. Permit Intelligence ADR-037/038/039 **Accepted**. [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue ADR-034/035/036 **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (docs only; MONITOR not implemented). [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: FG-014 Material Catalogue V1 **CLOSED / OPERATIONAL FOR UAT**. CalibAi V1 / BUILD field / four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / **FG-013 CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **APPROVED FOR IMPLEMENTATION** / **NOT STARTED**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-019 **Accepted**. **ADR-021 Accepted**. **ADR-032 Accepted**. **ADR-033 Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Supplier integration **not started**. Organization Brand Profile **FUTURE / NOT IMPLEMENTED**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-014 live: platform canonical materials (27 lumber/sheet seed rows); optional Material CostItem link; office `/material-catalogue/`. Catalogue-link flash repaired; office re-UAT **PASSED** on port **5007**. Historical labour evidence: 120 `HistoricalLabourItem` rows, ORG-001 — **unchanged**. |
| Incomplete work | FG-015 Permit Foundation V1 **not started**; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty; BUILD field capture; MONITOR implementation; office authentication; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; Permit Rules Library / Pass 2; Organization Brand Profile; Change Order document family. |
| Database and migration status | Graph head: `d6e7f8a9b0c1`. Live development/UAT `flask db current`: `d6e7f8a9b0c1` (**verified applied** 2026-08-30). One graph head. |
| Test status | Dedicated FG-014 **35 passed**; FG-013 **27**; historical **11**; labour **25**; pricing **33**; FG-012 **19**; Project Hub **13**; take-off **18**; Plan Intelligence combined **56**; full suite **345 passed** |
| Documentation status | [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **APPROVED FOR IMPLEMENTATION** / **NOT STARTED**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. FG-013 **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-032 **Accepted**. **ADR-033 Accepted**. ADR-021 **Accepted** (docs only). FG-012 **CLOSED / OPERATIONAL FOR UAT**. ADR-008 / ADR-010 **Proposed**. Organization Brand Profile pinned FUTURE only. Change Order document family pinned FUTURE only. |
| Decisions made (this FG-015 governance pass) | Created FG-015. Status **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED**. Projects owns ProjectLocation (1:1, parented to `projects`); preserve `Project.address`; no ambiguous backfill. Permit context class is separate from commercial `PROJECT_TYPES` (no auto-map; not a zoning ontology). Preliminary profile is versioned snapshot foundation (ADR-039); no Pass 2 findings. No new ADR. No product code. |
| Decisions pending | Real AI provider; Phase D mapping gate. FG-009 carry-forward unchanged. Darcy commercial terms unset. Supplier Feature Gate **not authorized**. Bulk supplier onboarding remains future. Whether Organization Branding becomes a small platform prerequisite Feature Gate — later. How Change Order document snapshot / email / acceptance evidence is gated — later. Finding-severity product enums remain deferred until Gate 2. Ontario / Ottawa + Mike Pratt Feature Gate **not created**. |
| Uncommitted work | None expected after this docs commit/push. |
| Next approved milestone | **FG-015 implementation** under a later approved Cursor prompt. This governance pass **STOPS** without implementing. Do not `flask db upgrade` again until a live-migrate prompt. Do not populate the Permit Rules Library. Do not start Phase D, supplier/Winchester POC, branding, or Change Order documents. Do not accept ADR-008. |
| Next candidate milestone | After FG-015 closes: later **Ontario / Ottawa Permit Rules + Mike Pratt POC** (not created). Supplier Catalogue onboarding/mapping remains **not authorized**. Phase D mapping remains **NOT STARTED / NOT AUTHORIZED**. MONITOR implementation remains **not authorized**. |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) → [architecture/jurisdiction-resolution.md](architecture/jurisdiction-resolution.md) |
| Approved next Cursor prompt location or summary | **FG-015 implementation** (later prompt). Do **not** implement in this governance chat. Do not populate rules. Do not accept ADR-008. Do not start Phase D, supplier POC, branding, or Change Order documents. |
| Commit status | FG-015 **docs-only** this commit. Live current=head `d6e7f8a9b0c1`. Implementation **not started**. |
| Governance baseline | FG-015 APPROVED FOR IMPLEMENTATION / NOT STARTED; FG-014 CLOSED / OPERATIONAL FOR UAT; live current=head d6e7f8a9b0c1; FG-013 CLOSED / OPERATIONAL FOR UAT; ADR-034/035/036 Accepted; ADR-037/038/039 Accepted; ADR-032 Accepted; ADR-033 Accepted; ADR-008 Proposed; ADR-021 Accepted; FG-008–FG-012 closed/operational for UAT; Phase D not started; MONITOR not implemented; Organization Brand Profile FUTURE only; Change Order document family FUTURE only |

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

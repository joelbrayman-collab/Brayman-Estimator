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
| Current commit / `origin/main` | FG-017 live-migrate / office UAT close `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5`. Implementation parent `00ca492e28118d75757e9a9c82384978b5decd92`. FG-016 close `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`. Post-FG-017 docs reconciliation is a later docs-only commit — verify `git rev-parse HEAD`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **FG-017 CLOSED / OPERATIONAL FOR UAT** (live current=head `a9b0c1d2e3f4`; office UAT port **5010**). **FG-016 CLOSED / OPERATIONAL FOR UAT** (Pratt UAT project 9 port 5009). **FG-015 CLOSED / OPERATIONAL FOR UAT**. **FG-014 CLOSED / OPERATIONAL FOR UAT**. **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT**. **FG-013 CLOSED / OPERATIONAL FOR UAT**. FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. Permit Intelligence ADR-037/038/039 **Accepted**. [FG-013](feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue ADR-034/035/036 **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (docs only; MONITOR not implemented). [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: FG-017 Organization Brand Profile V1 **CLOSED / OPERATIONAL FOR UAT**. FG-016 Ontario / Ottawa Permit Intelligence POC **CLOSED / OPERATIONAL FOR UAT**. FG-015 Permit Foundation V1 **CLOSED / OPERATIONAL FOR UAT**. FG-014 Material Catalogue V1 **CLOSED / OPERATIONAL FOR UAT**. CalibAi V1 / BUILD field / four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 / FG-009 / FG-010 / FG-011 / FG-012 / **FG-013 CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-019 **Accepted**. **ADR-021 Accepted**. **ADR-032 Accepted**. **ADR-033 Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-008 / ADR-010 **Proposed**. **ADR-040 Accepted**. Real external AI provider **not authorized**. Phase D **not started**. Supplier integration **not started**. Organization Brand Profile **operational for office UAT**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-017: versioned Organization Brand Profile, private logo custody, Proposal brand snapshots, Settings `/settings/brand-profile`. FG-016 permit rules/facts/analyses remain. |
| Incomplete work | Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty; BUILD field capture; MONITOR implementation; office authentication; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family. |
| Database and migration status | Graph head `a9b0c1d2e3f4`. Live current `a9b0c1d2e3f4`. Applied `f8a9b0c1d2e3` → `a9b0c1d2e3f4`. One head. |
| Test status | Dedicated FG-017 **22 passed**; FG-016 **37**; FG-015 **19**; FG-014 **35**; FG-013 **27**; historical **11**; labour **25**; pricing **33**; FG-012 **19**; Project Hub **13**; take-off **18**; Plan Intelligence combined **56**; full suite **423 passed** |
| Documentation status | [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-014](feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT**. FG-013 **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-032 **Accepted**. **ADR-033 Accepted**. ADR-021 **Accepted** (docs only). FG-012 **CLOSED / OPERATIONAL FOR UAT**. ADR-008 / ADR-010 **Proposed**. [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**. Change Order document family pinned FUTURE only. |
| Decisions made (this docs reconciliation pass) | Repaired stale CURRENT/FUTURE/NEXT language after FG-017 close. Preserved numbered CalibAi sequence. Item 10 remains first unfinished sequence item and is **NOT AUTHORIZED**. No Feature Gate created. No ADR created or accepted. |
| Decisions pending | Internal breakdown branding later. Real AI provider; Phase D mapping gate. FG-009 carry-forward unchanged. Darcy commercial terms unset. Supplier Feature Gate **not authorized**. Issued→Draft status lock still not decided. |
| Uncommitted work | None after post-FG-017 docs reconciliation (this pass). |
| Next approved milestone | **STOP.** [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. Do not start the next Feature Gate. Do not start Authentication. No product implementation authorized. |
| Next candidate milestone | **Roadmap direction only (not authorization):** first unfinished numbered sequence item is **item 10 Authentication / actor identity + shared API foundation** — **NOT STARTED / NOT AUTHORIZED**; no Feature Gate. Items 11–12 require item 10. Phase D, supplier onboarding, Change Order documents, Permit branding / national expansion, MONITOR, and LEARN remain separately governed and unauthorized. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [current-state.md](current-state.md) → [project-state-report.md](project-state-report.md) → [platform-roadmap.md](platform-roadmap.md) → [feature-gates/FG-017-organization-brand-profile-v1.md](feature-gates/FG-017-organization-brand-profile-v1.md) |
| Approved next Cursor prompt location or summary | **STOP.** Fresh-chat prompt in [session-handoff.md](session-handoff.md) §22. Expected next *substantive* step, only after Joel/ChatGPT review: separately authorized Authentication architecture and Feature-Gate **reconnaissance** — not implementation. |
| Commit status | FG-017 live-migrate / office UAT close `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5` on `main`. Implementation parent `00ca492e28118d75757e9a9c82384978b5decd92`. Live current = head `a9b0c1d2e3f4`. FG-016 **CLOSED / OPERATIONAL FOR UAT**. ADR-040 **Accepted**. FG-017 **CLOSED / OPERATIONAL FOR UAT**. |
| Governance baseline | FG-017 CLOSED / OPERATIONAL FOR UAT; live current=head a9b0c1d2e3f4; full suite 423 passed; FG-016 CLOSED / OPERATIONAL FOR UAT; ADR-040 Accepted; ADR-008 Proposed; Phase D not started; MONITOR not implemented; Change Order document family FUTURE only |

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

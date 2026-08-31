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
| Current commit / `origin/main` | FG-017 close `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5`. Docs-reconciliation content `dd30d752190e56ed687e270950df9bf9a06d7a26`. SHA-pin `07cb46c501d968542dff567943044dc1db870f01`. Live `HEAD` / `origin/main`: verify `git rev-parse HEAD` and `git rev-parse origin/main` (do not treat as a circular this-commit reference). Implementation parent `00ca492e28118d75757e9a9c82384978b5decd92`. FG-016 close `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **FG-017 CLOSED / OPERATIONAL FOR UAT** (live current=head `a9b0c1d2e3f4`; office UAT port **5010**). **FG-016 CLOSED / OPERATIONAL FOR UAT** (Pratt UAT project 9 port 5009). **FG-015 CLOSED / OPERATIONAL FOR UAT**. **FG-014 CLOSED / OPERATIONAL FOR UAT**. **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT**. **FG-013 CLOSED / OPERATIONAL FOR UAT**. FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **IMPLEMENTED / LIVE MIGRATION PENDING**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. Permit Intelligence ADR-037/038/039 **Accepted**. Material Catalogue ADR-034/035/036 **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (docs only; MONITOR not implemented). [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: FG-017 Organization Brand Profile V1 **CLOSED / OPERATIONAL FOR UAT**. FG-016 Ontario / Ottawa Permit Intelligence POC **CLOSED / OPERATIONAL FOR UAT**. FG-015 Permit Foundation V1 **CLOSED / OPERATIONAL FOR UAT**. FG-014 Material Catalogue V1 **CLOSED / OPERATIONAL FOR UAT**. CalibAi V1 / BUILD field / four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-017 **CLOSED / OPERATIONAL FOR UAT**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **IMPLEMENTED / LIVE MIGRATION PENDING**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-019 **Accepted**. **ADR-021 Accepted**. **ADR-032 Accepted**. **ADR-033 Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-008 / ADR-010 **Proposed**. **ADR-040 Accepted**. Real external AI provider **not authorized**. Phase D **not started**. Shared API **deferred**. Supplier integration **not started**. Organization Brand Profile **operational for office UAT**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-018: User/UserMembership, office login/logout, CSRF, membership org context, CLI bootstrap/reset, bounded actor snapshots. Live DB still on FG-017 schema. FG-017 Brand Profile and FG-016 permit remain. |
| Incomplete work | FG-018 live migration/bootstrap/UAT; shared API; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty; BUILD field capture; MONITOR implementation; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family. |
| Database and migration status | Repository graph head `b0c1d2e3f4a5`. Live current `a9b0c1d2e3f4`. Live upgrade **not run**. Expected split. |
| Test status | Dedicated FG-018 **37 passed**; full suite **460 passed**. Pre-FG-018 baseline **423**. Dedicated FG-017 **22**; FG-016 **37**; FG-015 **19**; FG-014 **35**; FG-013 **27**; historical **11**; labour **25**; pricing **33**; FG-012 **19**; Project Hub **13**; take-off **18**; Plan Intelligence combined **56**. |
| Documentation status | [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **IMPLEMENTED / LIVE MIGRATION PENDING**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-032 **Accepted**. **ADR-033 Accepted**. ADR-021 **Accepted** (docs only). FG-012 **CLOSED / OPERATIONAL FOR UAT**. ADR-008 / ADR-010 **Proposed**. [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**. Change Order document family pinned FUTURE only. |
| Decisions made (this governance pass) | Implemented FG-018 in repository. Live migration **not run**. Shared API deferred. No RBAC. No org-switcher. |
| Decisions pending | Whether to authorize live `flask db upgrade` to `b0c1d2e3f4a5`, CLI bootstrap, SECRET_KEY, and office UAT. Multi-membership selection remains fail-closed. |
| Uncommitted work | None after this implementation commit. |
| Next approved milestone | **STOP. Do not live-migrate.** Wait for Joel/ChatGPT live-migration/bootstrap/UAT authorization. Do not mark FG-018 CLOSED. |
| Next candidate milestone | Live-migrate FG-018, bootstrap ORG-001 user, office UAT, then a separate close prompt. Items 11–12 require Item 10 **close**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [current-state.md](current-state.md) → [project-state-report.md](project-state-report.md) → [adr/ADR-041-user-membership-and-office-authentication.md](adr/ADR-041-user-membership-and-office-authentication.md) → [feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) |
| Approved next Cursor prompt location or summary | **STOP. Do not live-migrate.** Fresh-chat prompt in [session-handoff.md](session-handoff.md) §22 should wait for a separate live-migration/bootstrap/UAT authorization. |
| Commit status | FG-018 implementation: verify `git rev-parse HEAD`. Parent `b7b1bb59d3826ced14459e35d307628672344b5f`. Live current `a9b0c1d2e3f4`. Repository head `b0c1d2e3f4a5`. ADR-041 **Accepted**. FG-018 **IMPLEMENTED / LIVE MIGRATION PENDING**. |
| Governance baseline | FG-018 IMPLEMENTED / LIVE MIGRATION PENDING; live current a9b0c1d2e3f4; repo head b0c1d2e3f4a5; full suite 460 passed; dedicated 37; ADR-041 Accepted; ADR-008 Proposed; Phase D not started; MONITOR not implemented; shared API deferred; Change Order document family FUTURE only |

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

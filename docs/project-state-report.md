# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-08-31 |

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
| Report date | 2026-08-31 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | FG-020 Compatible Rendition increment: verify `git rev-parse HEAD` and `git rev-parse origin/main` after this commit. Starting parent `77d496367f9e6f003eb69949adb3bd82c6cadfd7`. FG-020 foundation `77d496367f9e6f003eb69949adb3bd82c6cadfd7`. FG-018 close: implementation parent `0d7af3e93a9d6c4f27eb2136f915297620be59ed`. FG-017 close `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5`. FG-016 close `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **FG-020 IMPLEMENTED / LIVE MIGRATION PENDING** (revision `c1d2e3f4a5b6` not applied live; image-only Compatible Renditions **implemented**; dedicated **44**; focused **128**; full suite **538**). **FG-019 CLOSED / OPERATIONAL FOR UAT** (no migration; API UAT port **5012**; full suite **494** at close). **FG-018 CLOSED / OPERATIONAL FOR UAT** (live current `b0c1d2e3f4a5`; office UAT port **5011**). **FG-017 CLOSED / OPERATIONAL FOR UAT** (office UAT port **5010**). **FG-016 CLOSED / OPERATIONAL FOR UAT** (Pratt UAT project 9 port 5009). **FG-015 CLOSED / OPERATIONAL FOR UAT**. **FG-014 CLOSED / OPERATIONAL FOR UAT**. **M012 / FG-010** AI Take-off foundation **CLOSED / OPERATIONAL FOR UAT**. **FG-013 CLOSED / OPERATIONAL FOR UAT**. FG-008 and FG-009 **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **IMPLEMENTED / LIVE MIGRATION PENDING**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. Roadmap item 10 **COMPLETE**. Item 11 **implemented / live migration pending**. Item 12 **BLOCKED / NOT AUTHORIZED**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. Permit Intelligence ADR-037/038/039 **Accepted**. Material Catalogue ADR-034/035/036 **Accepted**. [ADR-032](adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. [ADR-033](adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted**. [ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (docs only; MONITOR not implemented). [FG-012](feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: FG-020 BUILD Field Observation foundation **IMPLEMENTED / LIVE MIGRATION PENDING**. FG-019 Shared API Foundation V1 **CLOSED / OPERATIONAL FOR UAT**. FG-018 office authentication **CLOSED / OPERATIONAL FOR UAT**. FG-017 Organization Brand Profile V1 **CLOSED / OPERATIONAL FOR UAT**. FG-016 Ontario / Ottawa Permit Intelligence POC **CLOSED / OPERATIONAL FOR UAT**. Field Web / four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-019 **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **IMPLEMENTED / LIVE MIGRATION PENDING**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-019 **Accepted**. **ADR-021 Accepted**. **ADR-032 Accepted**. **ADR-033 Accepted**. ADR-005/006/007/009/011/031 **Accepted**. ADR-008 / ADR-010 **Proposed**. **ADR-040 Accepted**. Real external AI provider **not authorized**. Phase D **not started**. Shared API Foundation V1 **operational for UAT**. Supplier integration **not started**. Organization Brand Profile **operational for office UAT**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-020 Field Capture Events / Originals / Derived Candidates; office Field Observations; bounded `/api/v1` BUILD POSTs; `flask build propose-derived-candidate`; automatic HEIC/HEIF → JPEG Compatible Renditions. FG-019 GET `/api/v1` over FG-018 session. FG-018 live: User/UserMembership, office login/logout, CSRF, membership org context, CLI bootstrap/reset. First ORG-001 user bootstrapped. FG-017 Brand Profile and FG-016 permit remain. |
| Incomplete work | FG-020 live migration and office UAT; Field Web; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty; MONITOR implementation; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family; RBAC; org-switcher. |
| Database and migration status | Repository graph head `c1d2e3f4a5b6`. Live current `b0c1d2e3f4a5`. FG-020 upgrade **pending**. One graph head. **No new migration** in the Compatible Rendition increment. |
| Test status | Dedicated FG-020 **44 passed** (33 field observation + 11 media compatibility); focused (Hub + FG-018 + FG-019 + both FG-020) **128 passed**; full suite **538 passed**. Dedicated FG-019 **34**; dedicated FG-018 **37**. Pre-increment baseline **527**. Pre-FG-020 baseline **494**. Dedicated FG-017 **22**; FG-016 **37**; FG-015 **19**; FG-014 **35**; FG-013 **27**; historical **11**; labour **25**; pricing **33**; FG-012 **19**; take-off **18**; Plan Intelligence combined **56**. |
| Documentation status | [ADR-042](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**. [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **IMPLEMENTED / LIVE MIGRATION PENDING**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. [FG-017](feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**. Material Catalogue **ADR-034 / ADR-035 / ADR-036 Accepted**. **ADR-037 / ADR-038 / ADR-039 Accepted**. ADR-032 **Accepted**. **ADR-033 Accepted**. ADR-021 **Accepted** (docs only). FG-012 **CLOSED / OPERATIONAL FOR UAT**. ADR-008 / ADR-010 **Proposed**. [ADR-040](adr/ADR-040-organization-brand-profile.md) **Accepted**. Change Order document family pinned FUTURE only. |
| Decisions made (this governance pass) | Authorized FG-020 Media Compatibility increment implemented. HEIC/HEIF → JPEG Compatible Renditions land automatically after Original Source preservation. Storage-lifecycle pin preserved. Project Closeout remains **FUTURE**. FG-020 was **not** rewound. Live `flask db upgrade` **not** run. No new Alembic revision. |
| Decisions pending | Live-migration / office UAT of FG-020. Archive package format. Project Closeout Feature Gate not created. Multi-membership selection remains fail-closed. Native/token auth remains deferred. |
| Uncommitted work | None after this increment commit. |
| Next approved milestone | **STOP.** Separate live-migration / office UAT prompt (`b0c1d2e3f4a5` → `c1d2e3f4a5b6`). Do **not** implement Closeout. Do **not** start Field Web. |
| Next candidate milestone | Item 12 Field Web — **BLOCKED / NOT AUTHORIZED** until FG-020 close. Project Closeout — **FUTURE / NOT AUTHORIZED**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [architecture/build-media-storage-lifecycle.md](architecture/build-media-storage-lifecycle.md) → [feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) → [adr/ADR-042-build-field-evidence-and-iphone-first-capture.md](adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) → [current-state.md](current-state.md) → [project-state-report.md](project-state-report.md) |
| Approved next Cursor prompt location or summary | **STOP.** Wait for a separate live-migration / office UAT prompt. Do **not** start Field Web. Do **not** implement Closeout. |
| Commit status | FG-020 Compatible Rendition increment: verify `git rev-parse HEAD`. Live current `b0c1d2e3f4a5`. Repository head `c1d2e3f4a5b6`. ADR-042 **Accepted**. FG-020 **IMPLEMENTED / LIVE MIGRATION PENDING**. Item 10 **COMPLETE**. |
| Governance baseline | FG-020 IMPLEMENTED / LIVE MIGRATION PENDING; image-only Compatible Renditions implemented; FG-019 CLOSED / OPERATIONAL FOR UAT; FG-018 CLOSED / OPERATIONAL FOR UAT; item 10 COMPLETE; live current b0c1d2e3f4a5; repository head c1d2e3f4a5b6; full suite 538 passed; dedicated FG-020 44; focused 128; dedicated FG-019 34; dedicated FG-018 37; API UAT port 5012; office UAT port 5011; ADR-041 Accepted; ADR-042 Accepted; ADR-008 Proposed; Phase D not started; MONITOR not implemented; Item 12 BLOCKED; Change Order document family FUTURE only |

### Resume commands (Cursor Terminal)

```bash
cd /Users/joelbrayman/Desktop/Brayman-Estimator
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
./venv/bin/flask db current
./venv/bin/flask db heads
./venv/bin/python -m pytest -q
```

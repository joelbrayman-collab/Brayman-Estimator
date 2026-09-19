# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-19 |

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
| Report date | 2026-09-19 |
| Repository | Brayman-Estimator (The Estimator / CalibraytAI) |
| Current branch | `main` |
| Current commit / `origin/main` | C2 Client Final Walkthrough product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. C2 pin SHA **`14bd00b88c3a25ea7576be1d3dd2bbe288d272de`**. C1 Punch List product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. C1 pin SHA **`7bdbf191fe062f43550a9ccb81abf6eb21db8691`**. C1 live-migration governance SHA **`2fdc89b47230d1389309a415373c2742610efcd2`**. This C2 live-migration governance record follows. Close/Reopen Option A product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. FG-038 PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Slice B product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**. Slice A product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. PERF-C product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. FG-037 product SHA **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`**. Live current **`e5f6a7b8c9d0 (head)`**. Repository graph head **`e5f6a7b8c9d0`**. |
| Latest completed **coded** milestone on `main` | **FG-035 CORE CLOSE C2 Client Final Walkthrough** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH CLIENT DATA**). Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Prior coded: **C1 Contractor Punch List**. Prior coded: **Close/Reopen Option A**. Prior coded: **FG-038 PA-A**. Prior coded: **CORE CLOSE Slice B**. Prior coded: **CORE CLOSE Slice A**. Prior coded: **FG-035 PERF-C**. Prior coded: **FG-037**. |
| Current milestone | [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) CORE CLOSE C2 Client Final Walkthrough **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH CLIENT DATA**. Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Additive **`e5f6a7b8c9d0`**. C1 Contractor Punch List remains **LIVE / 0 ITEMS**. Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Close/Reopen Option A remains **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed**. Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md) **OPEN / PARTIAL / PA-A IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / FIRST OWNER ASSIGNED / LIVE AUTHORITY UAT PASS**. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — Governed V1 Readiness **65%**; **4 / 11** COMPLETE. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE Slice A **LIVE-MIGRATED**. CORE CLOSE Slice B **SHA-PINNED / NO MIGRATION**. CORE CLOSE overall **PARTIAL**. [FG-037](feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**. [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. |
| Incomplete work | C2 Client Final Walkthrough **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 INVITATIONS**. C1 Punch List **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 ITEMS**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Completion Sign-Off **NOT IMPLEMENTED**. Sys Admin **DEFERRED TO PA-B**. People & Access UI **NOT IMPLEMENTED**. [FG-037](feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**. Ben genuine ORG-001 membership **ABSENT**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN Closeout / LEARN / QB-T **NOT AUTHORIZED**. |
| Database and migration status | Live current **`e5f6a7b8c9d0 (head)`**. Repository graph head **`e5f6a7b8c9d0`**. C2 additive **applied live** 2026-09-19. C2 invitations **0**. C1 Punch List additive **applied live** 2026-09-19. Punch List items **0**. FG-038 PA-A additive **applied live** 2026-09-18. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Isolation orgs **OWNERLESS**. Owner SET events **1**. All existing Projects **ACTIVE**. Event rows **0**. Grant row count **1** (Membership 1 / Joel Brayman / `COMPANY_MANAGEMENT`). PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | Post-migration dedicated C2 **34 passed**, 74 warnings, **18.70s**, exit **0**. Focused **352 passed**, 1303 warnings, **198.21s**, exit **0**. Full suite **1398 passed**, 4860 warnings, **779.71s**, exit **0**. |
| Documentation status | **2026-09-19 CORE CLOSE C2 CLIENT FINAL WALKTHROUGH live migration.** C2 **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH CLIENT DATA**. Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Additive **`e5f6a7b8c9d0` applied live**. Close/Reopen Option A remains **SHA-PINNED / NOT LIVE-UATed**. PA-A remains **LIVE / OPERATIONAL**. People & Access UI remains **NOT IMPLEMENTED**. FG-037 remains **CLOSED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-19 C2 live migrate `d4e5f6a7b8c9` → `e5f6a7b8c9d0`. Empty live baseline 0 invitations / 0 items. No live client invitation. No rescore. |
| Decisions pending | Completion Sign-Off. Labeled live Close/Reopen UAT. PA-B Sys Admin. Scorecard. Ben membership. Recovery stash drop. People & Access UI. Home Office. |
| Uncommitted work | **This live-migration governance record.** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. Live occupancy unchanged except C2 schema. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect. Recommended next: **D — PROJECT COMPLETION SIGN-OFF**. Do **not** send a live client invitation. Do **not** Close a live Project. Do **not** drop the recovery stash. |
| Next candidate milestone | **D — PROJECT COMPLETION SIGN-OFF**. |
| Approved next Cursor prompt location or summary | **STOP.** Return to ChatGPT Architect. C2 is **LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH CLIENT DATA**. Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Live Alembic **`e5f6a7b8c9d0 (head)`**. Recommended next: **D — PROJECT COMPLETION SIGN-OFF**. Do **not** create live C2 data. Do **not** drop the recovery stash. |
| Documents to read first | [architecture/core-close-project-lifecycle-product-direction.md](architecture/core-close-project-lifecycle-product-direction.md) → [feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) → [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Architecture status | CAR-001 approved. CORE CLOSE C2 Client Final Walkthrough **LIVE-MIGRATED / EMPTY LIVE BASELINE**. Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Additive **`e5f6a7b8c9d0`**. C1 Punch List **LIVE-MIGRATED / EMPTY LIVE BASELINE**. Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md) PA-A **LIVE / OPERATIONAL**. People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE Slice A **LIVE-MIGRATED**. CORE CLOSE Slice B **SHA-PINNED**. CORE CLOSE overall **PARTIAL**. |
| Implemented capabilities | C2 Client Final Walkthrough live / 0 invitations (product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**). C1 Punch List live / 0 items (product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**). Close/Reopen Option A (product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**). FG-038 PA-A Instance Owner pointer + SET events + authority helpers + operator CLI (**live / ORG-001 Owner assigned**). PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. FG-037 COMPANY_MANAGEMENT grants **operational**. CORE CLOSE Slice A/B **operational for current-work guards**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. C2 Client Final Walkthrough is **committed / SHA-pinned / live-migrated / empty baseline / not live-UATed with client data**. C1 Punch List is **committed / SHA-pinned / live-migrated / empty baseline**. Close/Reopen Option A is **committed / SHA-pinned / not live-UATed**. FG-038 PA-A Instance Owner foundation is **committed / SHA-pinned / live-migrated / first Owner assigned**. FG-034 MAIL-A / AUTH-A / AUTH-B / AUTH-C / MAIL-B / AUTH-D is **IMPLEMENTED / PASS**. FG-033 SIGN-E through SIGN-A **IMPLEMENTED**. Real iPhone UAT **DEFERRED**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Native Signing production **NOT COMPLETE**. |
| Commit status | Working tree **DIRTY with this live-migration governance record**. C2 product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Pin SHA **`14bd00b88c3a25ea7576be1d3dd2bbe288d272de`**. C1 product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Close/Reopen product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. FG-038 PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Live Alembic current **`e5f6a7b8c9d0 (head)`**. Graph head **`e5f6a7b8c9d0`**. |
| Governance baseline | V1 register GOVERNING / 65% / 4 of 11 COMPLETE; secondary Functional V1 Build 79% / 22 of 28; C2 Client Final Walkthrough LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 INVITATIONS; product SHA ec4ef9956025fd8e281c12c17d84493b121f8337; C1 Punch List LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 ITEMS; Close/Reopen Option A SHA-PINNED / NOT LIVE-UATed; FG-038 PA-A LIVE / OPERATIONAL; live current e5f6a7b8c9d0; graph head e5f6a7b8c9d0; live grant rows 1; ORG-001 Owner membership 1 |

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

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
| Current commit / `origin/main` | C1 Punch List product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Pin SHA **`7bdbf191fe062f43550a9ccb81abf6eb21db8691`**. Live-migration governance SHA **`2fdc89b47230d1389309a415373c2742610efcd2`**. Close/Reopen Option A product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. FG-038 PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Slice B product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**. Slice A product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. PERF-C product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. FG-037 product SHA **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`**. Live current **`d4e5f6a7b8c9`**. Repository graph head **`e5f6a7b8c9d0`** (working tree; not applied live). |
| Latest completed **coded** milestone on `main` | **FG-035 CORE CLOSE C1 Contractor Punch List** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / EMPTY LIVE BASELINE VERIFIED / NOT LIVE-UATed WITH MUTATING DATA**). Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Prior coded: **Close/Reopen Option A**. Prior coded: **FG-038 PA-A**. Prior coded: **CORE CLOSE Slice B**. Prior coded: **CORE CLOSE Slice A**. Prior coded: **FG-035 PERF-C**. Prior coded: **FG-037**. |
| Current milestone | [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) CORE CLOSE C2 Client Final Walkthrough **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NOT PUSHED**. Additive **`e5f6a7b8c9d0`**. C1 Contractor Punch List remains **LIVE / 0 ITEMS**. Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Close/Reopen Option A remains **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed**. Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md) **OPEN / PARTIAL / PA-A IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / FIRST OWNER ASSIGNED / LIVE AUTHORITY UAT PASS**. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — Governed V1 Readiness **65%**; **4 / 11** COMPLETE. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE Slice A **LIVE-MIGRATED**. CORE CLOSE Slice B **SHA-PINNED / NO MIGRATION**. CORE CLOSE overall **PARTIAL**. [FG-037](feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**. [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. |
| Incomplete work | C2 Client Final Walkthrough **IMPLEMENTED IN WORKING TREE / NOT LIVE-MIGRATED / NOT COMMITTED**. C1 Punch List **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 ITEMS**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Completion Sign-Off **NOT IMPLEMENTED**. Sys Admin **DEFERRED TO PA-B**. People & Access UI **NOT IMPLEMENTED**. [FG-037](feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**. Ben genuine ORG-001 membership **ABSENT**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN Closeout / LEARN / QB-T **NOT AUTHORIZED**. |
| Database and migration status | Live current **`d4e5f6a7b8c9`**. Repository graph head **`e5f6a7b8c9d0`** (working tree). C2 additive **not applied live**. C1 Punch List additive **applied live** 2026-09-19. Punch List items **0**. Live C2 tables **ABSENT**. FG-038 PA-A additive **applied live** 2026-09-18. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Isolation orgs **OWNERLESS**. Owner SET events **1**. All existing Projects **ACTIVE**. Event rows **0**. Grant row count **1** (Membership 1 / Joel Brayman / `COMPANY_MANAGEMENT`). PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | Dedicated C2 **34 passed**, 74 warnings, **19.71s**, exit **0**. C1 regression **26 passed**, 56 warnings, **14.65s**, exit **0**. Focused CORE CLOSE/Hub/CO/work/auth/Field/MONITOR/PERF **352 passed**, 1303 warnings, **197.04s**, exit **0**. Full suite **1398 passed**, 4860 warnings, **767.57s**, exit **0**. |
| Documentation status | **2026-09-19 CORE CLOSE C2 CLIENT FINAL WALKTHROUGH working tree.** C2 **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NOT PUSHED**. Additive **`e5f6a7b8c9d0`**. Graph head **`e5f6a7b8c9d0`**. Live Alembic remains **`d4e5f6a7b8c9`**. C1 Punch List remains **LIVE / 0 ITEMS**. Completion Sign-Off **NOT IMPLEMENTED**. Close/Reopen Option A remains **SHA-PINNED / NOT LIVE-UATed**. PA-A remains **LIVE / OPERATIONAL**. People & Access UI remains **NOT IMPLEMENTED**. FG-037 remains **CLOSED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-19 C2 hashed no-login invitation; client input XOR nothing-to-add; contractor review; accept-to-Punch-List requires work source; origin CLIENT_WALKTHROUGH; photos DEFERRED; email copyable-link pending configuration; one additive migration FILE; TEST DB only; no live C2 data; no commit. |
| Decisions pending | Architect ACCEPT COMMIT C2. Live migrate `e5f6a7b8c9d0` separately. Completion Sign-Off. Labeled live Close/Reopen UAT. PA-B Sys Admin. Scorecard. Ben membership. Recovery stash drop. People & Access UI. Home Office. |
| Uncommitted work | **This C2 working-tree product + tests + one additive migration FILE + governance.** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. Live occupancy unchanged. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect. Recommended next: **ACCEPT COMMIT C2**. After C2 close: **D — COMPLETION SIGN-OFF**. Do **not** live-migrate. Do **not** commit from this record. Do **not** send a live client invitation. Do **not** Close a live Project. Do **not** drop the recovery stash. |
| Next candidate milestone | **D — COMPLETION SIGN-OFF** (after Architect ACCEPT COMMIT C2). |
| Approved next Cursor prompt location or summary | **STOP.** Return to ChatGPT Architect. C2 is **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NOT PUSHED**. Additive **`e5f6a7b8c9d0`**. Live Alembic **`d4e5f6a7b8c9`**. Recommended next: **ACCEPT COMMIT C2**. Do **not** create live C2 data. Do **not** drop the recovery stash. |
| Documents to read first | [architecture/core-close-project-lifecycle-product-direction.md](architecture/core-close-project-lifecycle-product-direction.md) → [feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) → [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Architecture status | CAR-001 approved. CORE CLOSE C2 Client Final Walkthrough **IMPLEMENTED IN WORKING TREE / TESTED / NOT LIVE-MIGRATED / NOT COMMITTED**. Additive **`e5f6a7b8c9d0`**. C1 Punch List **LIVE-MIGRATED / EMPTY LIVE BASELINE**. Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md) PA-A **LIVE / OPERATIONAL**. People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE Slice A **LIVE-MIGRATED**. CORE CLOSE Slice B **SHA-PINNED**. CORE CLOSE overall **PARTIAL**. |
| Implemented capabilities | C2 Client Final Walkthrough working tree (no-login invitation + contractor review). C1 Punch List live / 0 items (product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**). Close/Reopen Option A (product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**). FG-038 PA-A Instance Owner pointer + SET events + authority helpers + operator CLI (**live / ORG-001 Owner assigned**). PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. FG-037 COMPANY_MANAGEMENT grants **operational**. CORE CLOSE Slice A/B **operational for current-work guards**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. C2 Client Final Walkthrough is **implemented in working tree / tested / not live-migrated / not committed**. C1 Punch List is **committed / SHA-pinned / live-migrated / empty baseline**. Close/Reopen Option A is **committed / SHA-pinned / not live-UATed**. FG-038 PA-A Instance Owner foundation is **committed / SHA-pinned / live-migrated / first Owner assigned**. FG-034 MAIL-A / AUTH-A / AUTH-B / AUTH-C / MAIL-B / AUTH-D is **IMPLEMENTED / PASS**. FG-033 SIGN-E through SIGN-A **IMPLEMENTED**. Real iPhone UAT **DEFERRED**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Native Signing production **NOT COMPLETE**. |
| Commit status | Working tree **DIRTY with C2 product + tests + additive migration FILE + governance**. HEAD / origin/main **`2fdc89b47230d1389309a415373c2742610efcd2`**. C1 product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Pin SHA **`7bdbf191fe062f43550a9ccb81abf6eb21db8691`**. Close/Reopen product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. FG-038 PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Live Alembic current **`d4e5f6a7b8c9`**. Graph head **`e5f6a7b8c9d0`**. |
| Governance baseline | V1 register GOVERNING / 65% / 4 of 11 COMPLETE; secondary Functional V1 Build 79% / 22 of 28; C2 Client Final Walkthrough working tree / not live; C1 Punch List LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 ITEMS; product SHA 81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c; Close/Reopen Option A SHA-PINNED / NOT LIVE-UATed; FG-038 PA-A LIVE / OPERATIONAL; live current d4e5f6a7b8c9; graph head e5f6a7b8c9d0; live grant rows 1; ORG-001 Owner membership 1 |

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

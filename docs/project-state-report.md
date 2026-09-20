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
| Latest completed **coded** milestone on `main` | **D5 Voice with Help** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED**). Product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. Prior coded: **D4 Field Help**. Prior coded: **D3 office Help**. Prior coded: **D2 bounded contractor-language residuals**. Prior coded: **D1 Project Hub contextual Help**. Prior coded: **FG-035 CORE CLOSE C2 Client Final Walkthrough**. |
| Current milestone | **D5 Voice with Help IMPLEMENTED / TESTED / COMMITTED / PUSHED.** D4 remains **COMMITTED / PUSHED**. D3 remains **COMMITTED**. D1 Hub Help remains **IMPLEMENTED**. D2 remains **IMPLEMENTED**. Contextual Help coverage complete for Hub / Office / Field. Voice is an interface to Help. Voice actions **NOT IMPLEMENTED / NOT V1**. User Guide remains outstanding. C2 remains **SEALED**. Live Alembic **`e5f6a7b8c9d0`**. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — **65%**; **4 / 11** COMPLETE. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE overall **PARTIAL**. LEARN **Future**. |
| Incomplete work | User Guide remains outstanding. C2 **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 INVITATIONS**. C1 Punch List **0 ITEMS**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Completion Sign-Off **NOT IMPLEMENTED / BLOCKED UNTIL WHOLE-PRODUCT UAT**. People & Access UI **NOT IMPLEMENTED**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN **Future**. |
| Database and migration status | Live current **`e5f6a7b8c9d0 (head)`**. Repository graph head **`e5f6a7b8c9d0`**. C2 additive **applied live** 2026-09-19. C2 invitations **0**. C1 Punch List additive **applied live** 2026-09-19. Punch List items **0**. FG-038 PA-A additive **applied live** 2026-09-18. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Isolation orgs **OWNERLESS**. Owner SET events **1**. All existing Projects **ACTIVE**. Event rows **0**. Grant row count **1** (Membership 1 / Joel Brayman / `COMPANY_MANAGEMENT`). PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | Dedicated D5 **9 passed**, 9 warnings, **2.91s**, exit **0**. D1 Help **9 passed**. D3 Help **8 passed**. D4 Help **9 passed**. D2 **6 passed**. Combined Help **41 passed**, 94 warnings, **19.71s**. Focused Help/Field/auth/C1/C2 **246 passed**, 743 warnings, **148.85s**, exit **0**. Full suite **1439 passed**, 4954 warnings, **650.95s**, exit **0**. |
| Documentation status | **2026-09-19 D5 VOICE WITH HELP PIN.** D5 **IMPLEMENTED / TESTED / COMMITTED / PUSHED**. Product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. D4 remains **COMMITTED / PUSHED**. Product SHA **`e7c3fb35a1b1c4519c387a71eb8f7e81a6cc1169`**. D3 remains **COMMITTED / PUSHED**. D1 Help remains **IMPLEMENTED**. D2 remains **IMPLEMENTED**. Contextual Help coverage complete for Hub / Office / Field. Voice is an interface to Help. User Guide remains outstanding. C2 remains **SEALED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-19 D5 Voice consumes the D1–D4 Help authority. Browser Web Speech only. Bounded question matching. No provider. No schema. Voice does not mutate. No rescore. |
| Decisions pending | FG-038 PA-B System Administrator. People & Access UI. Whole-product UAT. Completion Sign-Off after UAT. Labeled live Close/Reopen UAT. Scorecard. Ben membership. Recovery stash drop. Home Office. |
| Uncommitted work | **None for D5.** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. |
| Next approved milestone | **FG-038 PA-B — System Administrator authority foundation.** |
| Next candidate milestone | **People & Access UI** after PA-B is sealed. |
| Approved next Cursor prompt location or summary | **FG-038 PA-B** after this D5 pin. D5 is **SEALED**. C2 remains **SEALED**. Do **not** implement People & Access UI from this pin record. |
| Documents to read first | [architecture/core-close-project-lifecycle-product-direction.md](architecture/core-close-project-lifecycle-product-direction.md) → [feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) → [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Architecture status | CAR-001 approved. CORE CLOSE C2 Client Final Walkthrough **LIVE-MIGRATED / EMPTY LIVE BASELINE**. Product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Additive **`e5f6a7b8c9d0`**. C1 Punch List **LIVE-MIGRATED / EMPTY LIVE BASELINE**. Product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md) PA-A **LIVE / OPERATIONAL**. People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE Slice A **LIVE-MIGRATED**. CORE CLOSE Slice B **SHA-PINNED**. CORE CLOSE overall **PARTIAL**. |
| Implemented capabilities | C2 Client Final Walkthrough live / 0 invitations (product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**). C1 Punch List live / 0 items (product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**). Close/Reopen Option A (product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**). FG-038 PA-A Instance Owner pointer + SET events + authority helpers + operator CLI (**live / ORG-001 Owner assigned**). PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. FG-037 COMPANY_MANAGEMENT grants **operational**. CORE CLOSE Slice A/B **operational for current-work guards**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. C2 Client Final Walkthrough is **committed / SHA-pinned / live-migrated / empty baseline / not live-UATed with client data**. C1 Punch List is **committed / SHA-pinned / live-migrated / empty baseline**. Close/Reopen Option A is **committed / SHA-pinned / not live-UATed**. FG-038 PA-A Instance Owner foundation is **committed / SHA-pinned / live-migrated / first Owner assigned**. FG-034 MAIL-A / AUTH-A / AUTH-B / AUTH-C / MAIL-B / AUTH-D is **IMPLEMENTED / PASS**. FG-033 SIGN-E through SIGN-A **IMPLEMENTED**. Real iPhone UAT **DEFERRED**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Native Signing production **NOT COMPLETE**. |
| Commit status | D5 product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. This pin commit follows. D4 product SHA **`e7c3fb35a1b1c4519c387a71eb8f7e81a6cc1169`**. D4 pin SHA **`adcc78a0d15ee17971878c848038e035b12b9fca`**. D3 product SHA **`61f86789ae4e755fb39b3d65cbfee6a481ab15e8`**. D3 pin SHA **`1ab6cf09328e84915b306dd91a601dd4eb5a0c71`**. C2 product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Pin SHA **`14bd00b88c3a25ea7576be1d3dd2bbe288d272de`**. C1 product SHA **`81b6d802ccf15c10b01a1f63337ef4d0d5a26d6c`**. Close/Reopen product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. FG-038 PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Live Alembic current **`e5f6a7b8c9d0 (head)`**. Graph head **`e5f6a7b8c9d0`**. |
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

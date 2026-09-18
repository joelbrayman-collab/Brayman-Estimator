# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-18 |

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
| Report date | 2026-09-18 |
| Repository | Brayman-Estimator (The Estimator / CalibraytAI) |
| Current branch | `main` |
| Current commit / `origin/main` | Close/Reopen Option A product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. This pin follows. FG-038 PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Slice B product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**. Slice A product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. PERF-C product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. FG-037 product SHA **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`**. Live current **`c3d4e5f6a7b8 (head)`**. Repository graph head **`c3d4e5f6a7b8`**. |
| Latest completed **coded** milestone on `main` | **FG-035 CORE CLOSE Close/Reopen Option A** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed**). Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. Prior coded: **FG-038 PA-A**. Prior coded: **CORE CLOSE Slice B**. Prior coded: **CORE CLOSE Slice A**. Prior coded: **FG-035 PERF-C**. Prior coded: **FG-037**. |
| Current milestone | [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) CORE CLOSE Close/Reopen Option A **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed**. Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md) **OPEN / PARTIAL / PA-A IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / FIRST OWNER ASSIGNED / LIVE AUTHORITY UAT PASS**. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — Governed V1 Readiness **65%**; **4 / 11** COMPLETE. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE Slice A **LIVE-MIGRATED**. CORE CLOSE Slice B **SHA-PINNED / NO MIGRATION**. CORE CLOSE overall **PARTIAL / NOT YET SEALED**. [FG-037](feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**. [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. |
| Incomplete work | Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Punch List / Completion Sign-Off **NOT IMPLEMENTED**. Sys Admin **DEFERRED TO PA-B**. People & Access UI **NOT IMPLEMENTED**. [FG-037](feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**. Ben genuine ORG-001 membership **ABSENT**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN Closeout / LEARN / QB-T **NOT AUTHORIZED**. |
| Database and migration status | Live current **`c3d4e5f6a7b8 (head)`**. Repository graph head **`c3d4e5f6a7b8`**. FG-038 PA-A additive **applied live** 2026-09-18. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Isolation orgs **OWNERLESS**. Owner SET events **1**. All existing Projects **ACTIVE**. Event rows **0**. Grant row count **1** (Membership 1 / Joel Brayman / `COMPANY_MANAGEMENT`). PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | Close/Reopen dedicated **22 passed**, 133 warnings, **18.23s**, exit **0**. Slice A+B **55 passed**, 143 warnings, **18.54s**. FG-038 **35 passed**, 88 warnings, **18.61s**. Full suite **1338 passed**, 4730 warnings, **966.45s**, exit **0**. |
| Documentation status | **2026-09-18 CORE CLOSE Close/Reopen Option A SHA pin.** Option A **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed**. Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. PA-A remains **LIVE / OPERATIONAL**. People & Access UI remains **NOT IMPLEMENTED**. FG-037 remains **CLOSED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-18 Option A: Owner/Sys Admin Close/Reopen; Domain B denied; fail-and-flash invalid repeats; no migration; no live Close. |
| Decisions pending | Labeled live Close/Reopen UAT. Punch List. Completion Sign-Off. PA-B Sys Admin. Scorecard. Ben membership. Recovery stash drop. People & Access UI. Home Office. |
| Uncommitted work | **None for Option A.** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. Live occupancy unchanged. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect. Recommended next governed product slice: **FG-035 CORE CLOSE PUNCH LIST**. Do **not** Close a live Project from this pin. Do **not** drop the recovery stash. |
| Next candidate milestone | FG-035 CORE CLOSE Punch List implementation-readiness / implementation prompt. Labeled live Close/Reopen UAT remains separately authorized. |
| Documents to read first | [architecture/core-close-project-lifecycle-product-direction.md](architecture/core-close-project-lifecycle-product-direction.md) → [feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) → [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Approved next Cursor prompt location or summary | **STOP.** Return to ChatGPT Architect. Close/Reopen Option A is **IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed**. Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. Recommended next: **FG-035 CORE CLOSE PUNCH LIST**. Live Alembic **`c3d4e5f6a7b8 (head)`**. Do **not** Close a live Project. Do **not** drop the recovery stash. |
| Architecture status | CAR-001 approved. CORE CLOSE Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md) PA-A **LIVE / OPERATIONAL**. People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE Slice A **LIVE-MIGRATED**. CORE CLOSE Slice B **SHA-PINNED**. CORE CLOSE overall **PARTIAL / NOT YET SEALED**. |
| Implemented capabilities | Close/Reopen Option A (product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**). FG-038 PA-A Instance Owner pointer + SET events + authority helpers + operator CLI (**live / ORG-001 Owner assigned**). PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. FG-037 COMPANY_MANAGEMENT grants **operational**. CORE CLOSE Slice A/B **operational for current-work guards**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. Close/Reopen Option A is **committed / SHA-pinned / not live-UATed**. FG-038 PA-A Instance Owner foundation is **committed / SHA-pinned / live-migrated / first Owner assigned**. FG-034 MAIL-A / AUTH-A / AUTH-B / AUTH-C / MAIL-B / AUTH-D is **IMPLEMENTED / PASS**. FG-033 SIGN-E through SIGN-A **IMPLEMENTED**. Real iPhone UAT **DEFERRED**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Native Signing production **NOT COMPLETE**. |
| Commit status | Working tree **CLEAN after this pin**. Close/Reopen product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. FG-038 PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Live Alembic current **`c3d4e5f6a7b8 (head)`**. Graph head **`c3d4e5f6a7b8`**. |
| Governance baseline | V1 register GOVERNING / 65% / 4 of 11 COMPLETE; secondary Functional V1 Build 79% / 22 of 28; Close/Reopen Option A IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION / NOT LIVE-UATed; product SHA 172f0786aaa9e668f30be28c3cee30ac4fce5b1f; FG-038 PA-A LIVE / OPERATIONAL; live current c3d4e5f6a7b8; live grant rows 1; ORG-001 Owner membership 1 |

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

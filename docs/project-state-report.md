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
| Current commit / `origin/main` | Sealed HEAD remains CORE CLOSE Slice B pin **`46939919a83f6952680eff80d990521937ba4f21`**. PA-A is **uncommitted working tree**. Slice B product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**. Slice A product SHA **`f4b7515664c51850f3d87ed79f4a7e1226886fbd`**. PERF-C product SHA **`22fd30cd774fcf155ae69d7dcf99a44123d91409`**. FG-037 product SHA **`1649b6fab6d362c19088290a6f3cb52f2a0b3d92`**. Live current **`b2c3d4e5f6a7`**. Repository graph head **`c3d4e5f6a7b8`**. |
| Latest completed **coded** milestone on `main` | **FG-035 CORE CLOSE Slice B** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / NO MIGRATION**). Product SHA **`9360b706ab66f2588306b201ca0c4c45645fcb9a`**. Current working-tree coded: **FG-038 PA-A**. Prior coded: **CORE CLOSE Slice A**. Prior coded: **FG-035 PERF-C**. Prior coded: **FG-037**. |
| Current milestone | [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md) **OPEN / PARTIAL / PA-A IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NO OWNER ASSIGNED**. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — Governed V1 Readiness **65%**; **4 / 11** COMPLETE. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). [architecture/people-and-access-product-direction.md](architecture/people-and-access-product-direction.md) People & Access UI **NOT IMPLEMENTED**. CORE CLOSE Slice A **LIVE-MIGRATED**. CORE CLOSE Slice B **SHA-PINNED / NO MIGRATION**. Close/Reopen **NOT IMPLEMENTED**. [FG-037](feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**. [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. |
| Incomplete work | FG-038 PA-A **IMPLEMENTED IN WORKING TREE / NOT LIVE-MIGRATED / NO OWNER ASSIGNED**. Close / Reopen / Punch List / Completion Sign-Off **NOT IMPLEMENTED**. Sys Admin **DEFERRED TO PA-B**. People & Access UI **NOT IMPLEMENTED**. [FG-037](feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**. Ben genuine ORG-001 membership **ABSENT**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN Closeout / LEARN / QB-T **NOT AUTHORIZED**. |
| Database and migration status | Live current **`b2c3d4e5f6a7`**. Repository graph head **`c3d4e5f6a7b8`** (FG-038 file; **not applied live**). CORE CLOSE Slice A additive **applied live** 2026-09-18. All existing Projects **ACTIVE**. Event rows **0**. All organizations **OWNERLESS**. Grant row count **1** (Membership 1 / Joel Brayman / `COMPANY_MANAGEMENT`). PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | FG-038 dedicated **35 passed**, 88 warnings, **15.49s**, exit **0**. Focused FG-038+FG-037+FG-018+CORE CLOSE A/B **150 passed**, 364 warnings, **60.60s**, exit **0**. Full suite **1316 passed**, 4597 warnings, **561.70s**, exit **0**. HISTORICAL Slice B full suite **1281 passed**. |
| Documentation status | **2026-09-18 FG-038 PA-A working tree.** PA-A **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NO OWNER ASSIGNED**. Additive **`c3d4e5f6a7b8`**. [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md). People & Access UI remains **NOT IMPLEMENTED**. FG-037 remains **CLOSED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-18 PA-A: persist `instance_owner_membership_id` + SET events; no seed; CLI requires explicit organization-id + membership-id + actor-user-id; ownerless 403; `is_system_administrator` False; Owner is not Domain B; no new ADR; B/C inheritance deferred. |
| Decisions pending | Live migrate `c3d4e5f6a7b8`. Explicit Owner assignment. PA-B Sys Admin. Close/Reopen. Punch List. Completion Sign-Off. Scorecard. Ben membership. Recovery stash drop. People & Access UI. Home Office. |
| Uncommitted work | **FG-038 PA-A working tree.** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. Live grant Membership 1 unchanged. Live DB not mutated by PA-A. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate. Do **not** assign Owner. Do **not** implement Close, Reopen, Punch List, Completion Sign-Off, Sys Admin, People & Access UI, Home Office, LEARN, or QB-T. Do **not** drop the recovery stash. |
| Next candidate milestone | Architect-governed live migrate and/or explicit Owner assignment — **NOT THIS WORKING TREE**. |
| Documents to read first | [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [architecture/people-and-access-product-direction.md](architecture/people-and-access-product-direction.md) → [architecture/core-close-project-lifecycle-product-direction.md](architecture/core-close-project-lifecycle-product-direction.md) → [architecture/company-management-access-domain-seam.md](architecture/company-management-access-domain-seam.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Approved next Cursor prompt location or summary | **STOP.** Return to ChatGPT Architect. FG-038 PA-A is **IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NOT COMMITTED / NO OWNER ASSIGNED**. Live Alembic **`b2c3d4e5f6a7`**. Graph head **`c3d4e5f6a7b8`**. Do **not** run `flask db upgrade`. Do **not** assign a live Instance Owner. Do **not** implement Close/Reopen/Punch List/Sign-Off, Sys Admin, or People & Access UI. Do **not** drop the recovery stash. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. FG-038 PA-A Instance Owner foundation is **in the working tree / not live-migrated / no Owner assigned**. FG-034 MAIL-A / AUTH-A / AUTH-B / AUTH-C / MAIL-B / AUTH-D is **IMPLEMENTED / PASS**. FG-033 SIGN-E through SIGN-A **IMPLEMENTED**. Real iPhone UAT **DEFERRED**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Native Signing production **NOT COMPLETE**. |
| Architecture status | CAR-001 approved. [FG-038](feature-gates/FG-038-instance-owner-authority-foundation.md) PA-A **IMPLEMENTED IN WORKING TREE / NOT LIVE-MIGRATED / NO OWNER ASSIGNED**. [architecture/people-and-access-product-direction.md](architecture/people-and-access-product-direction.md) People & Access UI **NOT IMPLEMENTED**. [architecture/company-management-access-domain-seam.md](architecture/company-management-access-domain-seam.md) **DEFINED**. [FG-037](feature-gates/FG-037-company-management-access-domain-authorization.md) **CLOSED**. CORE CLOSE Slice A **LIVE-MIGRATED**. CORE CLOSE Slice B **SHA-PINNED**. Close/Reopen **NOT IMPLEMENTED**. |
| Implemented capabilities | FG-038 PA-A Instance Owner pointer + SET events + authority helpers + operator CLI (**working tree / not live**). FG-037 COMPANY_MANAGEMENT grants **operational**. CORE CLOSE Slice A/B **operational for current-work guards** (Close/Reopen not implemented). |
| Commit status | Sealed HEAD **`46939919a83f6952680eff80d990521937ba4f21`**. FG-038 PA-A **uncommitted**. Live Alembic current **`b2c3d4e5f6a7`**. Graph head **`c3d4e5f6a7b8`**. |
| Governance baseline | V1 register GOVERNING / 65% / 4 of 11 COMPLETE; secondary Functional V1 Build 79% / 22 of 28; FG-038 PA-A IMPLEMENTED IN WORKING TREE / NOT LIVE-MIGRATED / NO OWNER ASSIGNED; live current b2c3d4e5f6a7; graph head c3d4e5f6a7b8; live grant rows 1; all organizations ownerless |

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

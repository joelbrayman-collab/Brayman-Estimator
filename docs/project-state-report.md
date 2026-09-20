# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-20 |

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
| Report date | 2026-09-20 |
| Repository | Brayman-Estimator (The Estimator / CalibraytAI) |
| Current branch | `main` |
| Current commit / `origin/main` | PA-B product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Pin SHA **`3a4735b40ee4580ad3ae419569cafb7bdec32352`**. Stage 1 governance SHA **`162bcb60d09bb32bd231ed0753c020e5c0720a81`**. This Stage 2 UAT governance commit follows. D5 product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. D5 pin SHA **`c670dc2e35178ad18f02f53683098ee330c4dd7b`**. Live current **`f6a7b8c9d0e1 (head)`**. Repository graph head **`f6a7b8c9d0e1`**. |
| Latest completed **coded** milestone on `main` | **FG-038 PA-B System Administrator authority** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / LIVE APPOINT UAT PASS / LIVE REMOVE UAT PASS / ZERO CURRENT SYS ADMINS**). Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Prior coded: **D5 Voice with Help**. |
| Current milestone | **FG-038 PA-B LIVE APPOINT UAT PASS / LIVE REMOVE UAT PASS / ZERO CURRENT SYS ADMINS.** Additive **`f6a7b8c9d0e1` applied live**. D5 remains **SEALED**. People & Access **PARTIAL / NOT OPERATIONAL**. People UI **NOT IMPLEMENTED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). CORE CLOSE overall **PARTIAL**. LEARN **Future**. |
| Incomplete work | Current Sys Admin **0** with permanent APPOINT **1** / REMOVE **1**. Person / Worker identity **NOT IMPLEMENTED**. User Guide remains outstanding. C2 **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 INVITATIONS**. C1 Punch List **0 ITEMS**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Completion Sign-Off **NOT IMPLEMENTED / BLOCKED UNTIL WHOLE-PRODUCT UAT**. People & Access UI **NOT IMPLEMENTED**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN **Future**. |
| Database and migration status | Live current **`f6a7b8c9d0e1 (head)`**. Repository graph head **`f6a7b8c9d0e1`**. PA-B additive **applied live**. Sys Admin tables **present**. Current Sys Admin rows **0**. APPOINT **1**. REMOVE **1**. C2 invitations **0**. Punch List items **0**. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Owner SET events **1**. Grant row count **1**. PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | Focused PA-B/PA-A/Close/Reopen/FG-018/FG-037 **155 passed**, 462 warnings, **88.17s**, exit **0**. Full suite **not run** (no product/code change). |
| Documentation status | **2026-09-20 FG-038 PA-B STAGE 2 FIRST SYS ADMIN UAT.** Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-20 PA-B Stage 2 Option A: Membership **5** / User **6** temporarily appointed then removed. Live APPOINT UAT **PASS**. Live REMOVE UAT **PASS**. Current Sys Admins **0**. |
| Decisions pending | Architect: PA-C Person / Worker identity foundation. Whole-product UAT. Completion Sign-Off after UAT. Scorecard. Ben membership. Recovery stash drop. Home Office. |
| Uncommitted work | **None for PA-B product.** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. |
| Next approved milestone | **PA-C Person / Worker identity foundation.** |
| Next candidate milestone | **People & Access UI** after PA-C. |
| Approved next Cursor prompt location or summary | STOP. Architect PA-C implementation-readiness / implementation authorization. Do **not** implement People UI from this record. D5 is **SEALED**. |
| Documents to read first | [testing/fg038-pa-b-first-system-administrator-authority-uat.md](testing/fg038-pa-b-first-system-administrator-authority-uat.md) → [architecture/people-and-access-product-direction.md](architecture/people-and-access-product-direction.md) → [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Architecture status | CAR-001 approved. FG-038 PA-B **LIVE / OPERATIONAL / ZERO CURRENT SYS ADMINS**. PA-A **LIVE / OPERATIONAL**. People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE overall **PARTIAL**. |
| Implemented capabilities | PA-B Sys Admin foundation live / current 0 / APPOINT 1 / REMOVE 1. C2 live / 0 invitations. C1 Punch List live / 0 items. Close/Reopen Option A. FG-038 PA-A Instance Owner live / ORG-001 Owner assigned. FG-037 COMPANY_MANAGEMENT grants **operational**. |
| Product status | Current product **CalibraytAI**. PA-B Sys Admin foundation is **live-migrated / live appoint UAT pass / live remove UAT pass / zero current Sys Admins**. FG-038 PA-A Instance Owner foundation is **live / first Owner assigned**. D5 Voice-with-Help is **sealed**. |
| Commit status | PA-B product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Pin SHA **`3a4735b40ee4580ad3ae419569cafb7bdec32352`**. This Stage 2 UAT governance commit follows. Live Alembic current **`f6a7b8c9d0e1 (head)`**. Graph head **`f6a7b8c9d0e1`**. |
| Governance baseline | V1 register GOVERNING / 65% / 4 of 11 COMPLETE; secondary Functional V1 Build 79% / 22 of 28; PA-B live UAT pass / current 0 / APPOINT 1 / REMOVE 1; live current f6a7b8c9d0e1; graph head f6a7b8c9d0e1; live grant rows 1; ORG-001 Owner membership 1 |

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

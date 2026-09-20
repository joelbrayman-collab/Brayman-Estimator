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
| Current commit / `origin/main` | PA-B product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Pin SHA **`3a4735b40ee4580ad3ae419569cafb7bdec32352`**. Stage 2 UAT governance SHA **`6ad1410db5dbbccb6a4728b7c7b7ae442b935227`**. PA-C is **in working tree / not committed**. D5 product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. Live current **`f6a7b8c9d0e1`**. Repository graph head **`g7b8c9d0e1f2`**. |
| Latest completed **coded** milestone on `main` | **FG-038 PA-B System Administrator authority** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / LIVE APPOINT UAT PASS / LIVE REMOVE UAT PASS / ZERO CURRENT SYS ADMINS**). Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Prior coded: **D5 Voice with Help**. |
| Current milestone | **FG-038 PA-C IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NO LIVE PERSON / NOT COMMITTED / NOT PUSHED.** Additive **`g7b8c9d0e1f2`**. D5 remains **SEALED**. People & Access **PARTIAL / NOT OPERATIONAL**. People UI **NOT IMPLEMENTED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). CORE CLOSE overall **PARTIAL**. LEARN **Future**. |
| Incomplete work | PA-C not committed / not live-migrated. Person↔User linkage **DEFERRED TO PA-D**. People UI **NOT IMPLEMENTED**. Current Sys Admin **0** with permanent APPOINT **1** / REMOVE **1**. User Guide remains outstanding. C2 **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 INVITATIONS**. C1 Punch List **0 ITEMS**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Completion Sign-Off **NOT IMPLEMENTED / BLOCKED UNTIL WHOLE-PRODUCT UAT**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN **Future**. |
| Database and migration status | Live current **`f6a7b8c9d0e1`**. Repository graph head **`g7b8c9d0e1f2`**. PA-B additive **applied live**. PA-C additive **file only / not applied live**. Live Person table **absent**. Current Sys Admin rows **0**. APPOINT **1**. REMOVE **1**. C2 invitations **0**. Punch List items **0**. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Owner SET events **1**. Grant row count **1**. PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | Dedicated PA-C **37 passed**, 101 warnings, **27.61s**. Focused PA-C/PA-B/PA-A/Close/Reopen/FG-018/FG-037 **192 passed**, 563 warnings, **107.11s**, exit **0**. Full suite **1514 passed**, 5163 warnings, **723.80s**, exit **0**. |
| Documentation status | **2026-09-20 FG-038 PA-C PERSON / WORKER IDENTITY.** Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-20 PA-C additive Person authority. No User FK retarget. Wage Owner/Sys-Admin protected; not Domain C. No Person↔User linkage. |
| Decisions pending | Architect ACCEPT COMMIT / PUSH / SHA-PIN PA-C. Live empty-Person checkpoint. Bounded Person UAT. PA-D. Whole-product UAT. Completion Sign-Off after UAT. Scorecard. Ben membership. Recovery stash drop. Home Office. |
| Uncommitted work | **PA-C product and docs in working tree.** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. |
| Next approved milestone | **Architect ACCEPT COMMIT / PUSH / SHA-PIN PA-C.** |
| Next candidate milestone | **PA-C live migration / empty-Person checkpoint** then bounded Person UAT then **PA-D**. |
| Approved next Cursor prompt location or summary | STOP. Architect ACCEPT COMMIT / PUSH / SHA-PIN PA-C. Do **not** live-migrate. Do **not** implement People UI or PA-D from this record. D5 is **SEALED**. |
| Documents to read first | [architecture/people-and-access-product-direction.md](architecture/people-and-access-product-direction.md) → [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Architecture status | CAR-001 approved. FG-038 PA-C **IMPLEMENTED IN WORKING TREE / NOT LIVE**. PA-B **LIVE / OPERATIONAL / ZERO CURRENT SYS ADMINS**. PA-A **LIVE / OPERATIONAL**. People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE overall **PARTIAL**. |
| Implemented capabilities | PA-C Person foundation in working tree. PA-B Sys Admin foundation live / current 0 / APPOINT 1 / REMOVE 1. C2 live / 0 invitations. C1 Punch List live / 0 items. Close/Reopen Option A. FG-038 PA-A Instance Owner live / ORG-001 Owner assigned. FG-037 COMPANY_MANAGEMENT grants **operational**. |
| Product status | Current product **CalibraytAI**. PA-C Person / Worker identity is **implemented in working tree / not live-migrated**. PA-B Sys Admin foundation is **live-migrated / live appoint UAT pass / live remove UAT pass / zero current Sys Admins**. FG-038 PA-A Instance Owner foundation is **live / first Owner assigned**. D5 Voice-with-Help is **sealed**. |
| Commit status | PA-C **NOT COMMITTED**. HEAD remains Stage 2 UAT governance **`6ad1410db5dbbccb6a4728b7c7b7ae442b935227`**. Live Alembic current **`f6a7b8c9d0e1`**. Graph head **`g7b8c9d0e1f2`**. |
| Governance baseline | V1 register GOVERNING / 65% / 4 of 11 COMPLETE; secondary Functional V1 Build 79% / 22 of 28; PA-C working tree; PA-B live UAT pass / current 0 / APPOINT 1 / REMOVE 1; live current f6a7b8c9d0e1; graph head g7b8c9d0e1f2; live grant rows 1; ORG-001 Owner membership 1 |

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

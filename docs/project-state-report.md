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
| Current commit / `origin/main` | PA-C product SHA **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`**. Pin SHA **`bc0ce7f541728262df0573a6096b5948d7abe6ed`**. Stage 1 governance SHA **`433c46f2ae08dfe5513ee2ad86ad72347b8c47e3`**. This UAT governance commit follows. PA-B product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. D5 product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. Live current **`g7b8c9d0e1f2 (head)`**. |
| Latest completed **coded** milestone on `main` | **FG-038 PA-C Person / Worker identity** (**LIVE / OPERATIONAL / LIVE PERSON UAT PASS**). Product SHA **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`**. Prior coded: **PA-B System Administrator authority**. |
| Current milestone | **FG-038 PA-C LIVE PERSON UAT PASS / 1 INACTIVE SYNTHETIC UAT PERSON RETAINED.** Additive **`g7b8c9d0e1f2` applied live**. D5 remains **SEALED**. People & Access **PARTIAL / NOT OPERATIONAL**. People UI **NOT IMPLEMENTED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). CORE CLOSE overall **PARTIAL**. LEARN **Future**. |
| Incomplete work | Person↔User linkage **DEFERRED TO PA-D**. People UI **NOT IMPLEMENTED**. Current Sys Admin **0** with permanent APPOINT **1** / REMOVE **1**. User Guide remains outstanding. C2 **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 INVITATIONS**. C1 Punch List **0 ITEMS**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Completion Sign-Off **NOT IMPLEMENTED / BLOCKED UNTIL WHOLE-PRODUCT UAT**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN **Future**. |
| Database and migration status | Live current **`g7b8c9d0e1f2 (head)`**. Repository graph head **`g7b8c9d0e1f2`**. PA-C additive **applied live**. Live Person table **exists**. Live Person rows **1** INACTIVE. Current Sys Admin rows **0**. APPOINT **1**. REMOVE **1**. C2 invitations **0**. Punch List items **0**. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Owner SET events **1**. Grant row count **1**. PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | Dedicated PA-C **37 passed**, 101 warnings, **17.00s**. Focused identity **192 passed**, 563 warnings, **107.20s**, exit **0**. Full suite **1514 passed**, 5163 warnings, **691.64s**, exit **0**. |
| Documentation status | **2026-09-20 FG-038 PA-C BOUNDED LIVE PERSON UAT.** Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-20 one synthetic live Person UAT. Person ≠ User live. Wage Owner-protected live. Lifecycle pass. Person retained INACTIVE. |
| Decisions pending | PA-D. Whole-product UAT. Completion Sign-Off after UAT. Scorecard. Ben membership. Recovery stash drop. Home Office. |
| Uncommitted work | **This UAT governance commit follows.** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. |
| Next approved milestone | **PA-D Platform Access / Person-User linkage.** |
| Next candidate milestone | **PA-E contractor-facing People & Access UI.** |
| Approved next Cursor prompt location or summary | STOP. Architect PA-D architecture / implementation. Do **not** implement People UI from this record. D5 is **SEALED**. |
| Documents to read first | [architecture/people-and-access-product-direction.md](architecture/people-and-access-product-direction.md) → [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Architecture status | CAR-001 approved. FG-038 PA-C **LIVE / OPERATIONAL / LIVE PERSON UAT PASS**. PA-B **LIVE / OPERATIONAL / ZERO CURRENT SYS ADMINS**. PA-A **LIVE / OPERATIONAL**. People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE overall **PARTIAL**. |
| Implemented capabilities | PA-C Person foundation live / 1 INACTIVE synthetic UAT Person retained. PA-B Sys Admin foundation live / current 0 / APPOINT 1 / REMOVE 1. C2 live / 0 invitations. C1 Punch List live / 0 items. Close/Reopen Option A. FG-038 PA-A Instance Owner live / ORG-001 Owner assigned. FG-037 COMPANY_MANAGEMENT grants **operational**. |
| Product status | Current product **CalibraytAI**. PA-C Person / Worker identity is **live / operational / live Person UAT pass**. PA-B Sys Admin foundation is **live-migrated / live appoint UAT pass / live remove UAT pass / zero current Sys Admins**. FG-038 PA-A Instance Owner foundation is **live / first Owner assigned**. D5 Voice-with-Help is **sealed**. |
| Commit status | PA-C product SHA **`0698f9d2a4ccabcef53ebcef9cb1415bfcd470f7`**. Pin SHA **`bc0ce7f541728262df0573a6096b5948d7abe6ed`**. Stage 1 governance SHA **`433c46f2ae08dfe5513ee2ad86ad72347b8c47e3`**. This UAT governance commit follows. Live Alembic current **`g7b8c9d0e1f2 (head)`**. |
| Governance baseline | V1 register GOVERNING / 65% / 4 of 11 COMPLETE; secondary Functional V1 Build 79% / 22 of 28; PA-C live Person UAT pass / 1 inactive retained; PA-B live UAT pass / current 0 / APPOINT 1 / REMOVE 1; live current g7b8c9d0e1f2; live grant rows 1; ORG-001 Owner membership 1 |

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

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
| Current commit / `origin/main` | PA-B product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Pin SHA **`3a4735b40ee4580ad3ae419569cafb7bdec32352`**. This Stage 1 governance commit follows. D5 product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. D5 pin SHA **`c670dc2e35178ad18f02f53683098ee330c4dd7b`**. Live current **`f6a7b8c9d0e1 (head)`**. Repository graph head **`f6a7b8c9d0e1`**. |
| Latest completed **coded** milestone on `main` | **FG-038 PA-B System Administrator authority** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED / SHA-PINNED / LIVE-MIGRATED / ZERO-SYS-ADMIN CHECKPOINT PASS / NO LIVE SYS ADMIN**). Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Prior coded: **D5 Voice with Help**. |
| Current milestone | **FG-038 PA-B LIVE-MIGRATED / ZERO-SYS-ADMIN CHECKPOINT PASS / NO LIVE SYS ADMIN.** Additive **`f6a7b8c9d0e1` applied live**. D5 remains **SEALED**. People & Access **PARTIAL / NOT OPERATIONAL**. People UI **NOT IMPLEMENTED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). CORE CLOSE overall **PARTIAL**. LEARN **Future**. |
| Incomplete work | Live Sys Admin **0**. User Guide remains outstanding. C2 **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 INVITATIONS**. C1 Punch List **0 ITEMS**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Completion Sign-Off **NOT IMPLEMENTED / BLOCKED UNTIL WHOLE-PRODUCT UAT**. People & Access UI **NOT IMPLEMENTED**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN **Future**. |
| Database and migration status | Live current **`f6a7b8c9d0e1 (head)`**. Repository graph head **`f6a7b8c9d0e1`**. PA-B additive **applied live**. Sys Admin tables **present**. Live Sys Admin rows **0**. APPOINT **0**. REMOVE **0**. C2 invitations **0**. Punch List items **0**. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Owner SET events **1**. Grant row count **1**. PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | Dedicated PA-B **38 passed**, 108 warnings, **29.18s**, exit **0**. Full suite **1477 passed**, 5062 warnings, **969.59s**, exit **0**. |
| Documentation status | **2026-09-20 FG-038 PA-B STAGE 1 LIVE MIGRATION.** Product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-20 PA-B accepted, SHA-pinned, and live-migrated. Zero-Sys-Admin checkpoint **PASS**. No live Sys Admin appointed. |
| Decisions pending | Architect: bounded first Sys Admin UAT **or** People & Access UI. Whole-product UAT. Completion Sign-Off after UAT. Scorecard. Ben membership. Recovery stash drop. Home Office. |
| Uncommitted work | **None for PA-B product.** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. |
| Next approved milestone | **Architect decision — bounded first Sys Admin authority UAT or proceed directly to People & Access.** |
| Next candidate milestone | **People & Access UI** after any separately authorized first Sys Admin UAT, or directly if Architect so decides. |
| Approved next Cursor prompt location or summary | STOP. Architect decides first live Sys Admin UAT vs People & Access UI. Do **not** appoint a live Sys Admin from this record. D5 is **SEALED**. |
| Documents to read first | [testing/fg038-pa-b-live-migration-zero-sys-admin-checkpoint.md](testing/fg038-pa-b-live-migration-zero-sys-admin-checkpoint.md) → [architecture/people-and-access-product-direction.md](architecture/people-and-access-product-direction.md) → [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Architecture status | CAR-001 approved. FG-038 PA-B **LIVE / OPERATIONAL / NO ADMIN APPOINTED**. PA-A **LIVE / OPERATIONAL**. People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE overall **PARTIAL**. |
| Implemented capabilities | PA-B Sys Admin foundation live / no admin appointed. C2 live / 0 invitations. C1 Punch List live / 0 items. Close/Reopen Option A. FG-038 PA-A Instance Owner live / ORG-001 Owner assigned. FG-037 COMPANY_MANAGEMENT grants **operational**. |
| Product status | Current product **CalibraytAI**. PA-B Sys Admin foundation is **live-migrated / zero-Sys-Admin checkpoint pass / no live Sys Admin**. FG-038 PA-A Instance Owner foundation is **live / first Owner assigned**. D5 Voice-with-Help is **sealed**. |
| Commit status | PA-B product SHA **`2b25ec99b010c0c66d58d6aa08fdbab55b077e08`**. Pin SHA **`3a4735b40ee4580ad3ae419569cafb7bdec32352`**. This Stage 1 governance commit follows. Live Alembic current **`f6a7b8c9d0e1 (head)`**. Graph head **`f6a7b8c9d0e1`**. |
| Governance baseline | V1 register GOVERNING / 65% / 4 of 11 COMPLETE; secondary Functional V1 Build 79% / 22 of 28; PA-B live-migrated / zero Sys Admin; live current f6a7b8c9d0e1; graph head f6a7b8c9d0e1; live grant rows 1; ORG-001 Owner membership 1; live Sys Admin 0 |

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

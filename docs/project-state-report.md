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
| Current commit / `origin/main` | D5 Voice-with-Help product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. D5 pin SHA **`c670dc2e35178ad18f02f53683098ee330c4dd7b`**. PA-B is **uncommitted working tree**. C2 Client Final Walkthrough product SHA **`ec4ef9956025fd8e281c12c17d84493b121f8337`**. Close/Reopen Option A product SHA **`172f0786aaa9e668f30be28c3cee30ac4fce5b1f`**. FG-038 PA-A product SHA **`01e7463082b84b2fcd9d61ff7125a5012b7f8043`**. Live current **`e5f6a7b8c9d0`**. Repository graph head **`f6a7b8c9d0e1`**. |
| Latest completed **coded** milestone on `main` | **D5 Voice with Help** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED**). Product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. Prior coded: **D4 Field Help**. Prior coded: **D3 office Help**. Prior coded: **D2 bounded contractor-language residuals**. Prior coded: **D1 Project Hub contextual Help**. Prior coded: **FG-035 CORE CLOSE C2 Client Final Walkthrough**. |
| Current milestone | **FG-038 PA-B SYSTEM ADMINISTRATOR AUTHORITY FOUNDATION IMPLEMENTED IN WORKING TREE / TESTED / MIGRATION FILE CREATED / NOT LIVE-MIGRATED / NO LIVE SYS ADMIN / NOT COMMITTED / NOT PUSHED.** Additive **`f6a7b8c9d0e1`**. D5 remains **SEALED**. People & Access **PARTIAL / NOT OPERATIONAL**. People UI **NOT IMPLEMENTED**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). CORE CLOSE overall **PARTIAL**. LEARN **Future**. |
| Incomplete work | PA-B not committed. Live Sys Admin **0**. User Guide remains outstanding. C2 **LIVE-MIGRATED / EMPTY LIVE BASELINE / 0 INVITATIONS**. C1 Punch List **0 ITEMS**. Close/Reopen Option A **SHA-PINNED / NOT LIVE-UATed**. Completion Sign-Off **NOT IMPLEMENTED / BLOCKED UNTIL WHOLE-PRODUCT UAT**. People & Access UI **NOT IMPLEMENTED**. Home Office **RECORDED / NOT IMPLEMENTED**. LEARN **Future**. |
| Database and migration status | Live current **`e5f6a7b8c9d0`**. Repository graph head **`f6a7b8c9d0e1`**. PA-B additive **FILE ONLY**. Live Sys Admin tables **absent**. Live Sys Admin rows **0**. C2 additive **applied live** 2026-09-19. C2 invitations **0**. C1 Punch List additive **applied live** 2026-09-19. Punch List items **0**. FG-038 PA-A additive **applied live** 2026-09-18. ORG-001 Owner = Membership **1** / User **1** / Joel Brayman. Isolation orgs **OWNERLESS**. Owner SET events **1**. All existing Projects **ACTIVE**. Event rows **0**. Grant row count **1** (Membership 1 / Joel Brayman / `COMPANY_MANAGEMENT`). PRODUCTION packages **0**. No EST-2026-0019 mutation. |
| Test status | Dedicated PA-B **38 passed**, 108 warnings, **26.16s**, exit **0**. PA-A **35 passed**. FG-037 **23 passed**. FG-018 **37 passed**. Close/Reopen **22 passed**. Slice A **18 passed**. Slice B **37 passed**. Combined PA-A/FG-037/FG-018/Close/A/B **172 passed**, 497 warnings, **81.75s**. Help D1/D3/D4/D5 **35 passed**. C1 **26 passed**. C2 **34 passed**. Combined Help+C1/C2 **95 passed**, 208 warnings, **48.99s**. Full suite **1477 passed**, 5062 warnings, **676.28s**, exit **0**. |
| Documentation status | **2026-09-19 FG-038 PA-B WORKING TREE.** PA-B **IMPLEMENTED / TESTED / NOT COMMITTED / NOT PUSHED**. D5 remains **SEALED**. Product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. Official V1 **65% / 4 of 11**. Secondary Functional V1 Build **79% / 22 of 28** (not rescored). Recovery stash still present / not dropped. |
| Decisions made (this implementation) | 2026-09-19 Sys Admin is explicit org-scoped membership authority plus append-only APPOINT/REMOVE. Owner-only appoint. Owner/Sys Admin remove. Owner hard-protected. Not A/B/C. Close/Reopen existing seam now effective for Sys Admin in TEST DB. No live mutation. |
| Decisions pending | Architect ACCEPT COMMIT / PUSH / SHA-PIN PA-B. Live migration / ownerless-Sys-Admin checkpoint. First Sys Admin UAT. People & Access UI. Whole-product UAT. Completion Sign-Off after UAT. Scorecard. Ben membership. Recovery stash drop. Home Office. |
| Uncommitted work | **PA-B working tree (not committed).** Recovery stash `stash@{0}` **`840dba8320b59ff9464410fec390d755a31a56aa`** remains as recovery evidence and was **not dropped**. |
| Next approved milestone | **Architect ACCEPT COMMIT PA-B**, then live migration / ownerless-Sys-Admin checkpoint if separately authorized. |
| Next candidate milestone | **People & Access UI** after PA-B is sealed and live-migrated. |
| Approved next Cursor prompt location or summary | **STOP.** Return to Architect. Do **not** commit PA-B from this working tree until Architect ACCEPT COMMIT. D5 is **SEALED**. |
| Documents to read first | [architecture/people-and-access-product-direction.md](architecture/people-and-access-product-direction.md) → [feature-gates/FG-038-instance-owner-authority-foundation.md](feature-gates/FG-038-instance-owner-authority-foundation.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Architecture status | CAR-001 approved. FG-038 PA-B **WORKING TREE / NOT LIVE**. PA-A **LIVE / OPERATIONAL**. CORE CLOSE C2 Client Final Walkthrough **LIVE-MIGRATED / EMPTY LIVE BASELINE**. People & Access **PARTIAL / NOT OPERATIONAL**. CORE CLOSE overall **PARTIAL**. |
| Implemented capabilities | PA-B Sys Admin foundation in working tree (not live). C2 Client Final Walkthrough live / 0 invitations. C1 Punch List live / 0 items. Close/Reopen Option A. FG-038 PA-A Instance Owner live / ORG-001 Owner assigned. FG-037 COMPANY_MANAGEMENT grants **operational**. |
| Product status | Current product **CalibraytAI**. PA-B Sys Admin foundation is **in the working tree / not live-migrated / no live Sys Admin**. FG-038 PA-A Instance Owner foundation is **live / first Owner assigned**. D5 Voice-with-Help is **sealed**. |
| Commit status | HEAD / `origin/main` **`c670dc2e35178ad18f02f53683098ee330c4dd7b`**. D5 product SHA **`021a893104260baa543e1f791b24d671562f40dd`**. PA-B **NOT COMMITTED**. Live Alembic current **`e5f6a7b8c9d0`**. Graph head **`f6a7b8c9d0e1`**. |
| Governance baseline | V1 register GOVERNING / 65% / 4 of 11 COMPLETE; secondary Functional V1 Build 79% / 22 of 28; PA-B working tree / not live; live current e5f6a7b8c9d0; graph head f6a7b8c9d0e1; live grant rows 1; ORG-001 Owner membership 1; live Sys Admin 0 |

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

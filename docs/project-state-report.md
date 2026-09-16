# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-15 |

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
| Report date | 2026-09-15 |
| Repository | Brayman-Estimator (The Estimator / CalibraytAI) |
| Current branch | `main` |
| Current commit / `origin/main` | Product SCH-A **`fd8a66990df8286e54151b80b6f3cd5be5dd3ad1`** (`feat: implement FG-035 SCH-A schedule core`). Product TIME **`03c074fb1eb2bbca77ba86e495726c0e042c1979`**. Live current **`f6e7f8a9b0c1 (head)`**. Repository Alembic head **`f6e7f8a9b0c1`**. Live SCH-A migration proven/reconciled (the reconciliation prompt did **not** apply it). Prior product SCOPE **`21bf0eba47acdb19eb292c2319d675a1748c1dff`**. |
| Latest completed **coded** milestone on `main` | **FG-035 SCH-A** (**IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS / COMMITTED**). Gate **OPEN / PARTIAL**. Prior coded: **FG-035 TIME**. Prior coded: **FG-035 SCOPE**. Prior coded: **FG-035 TAX/WBS**. Prior close: **FG-034 AUTH-D**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **60%**; **4 / 11** COMPLETE. [FG-035](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) **OPEN / PARTIAL**. TAX/WBS **IMPLEMENTED**. SCOPE **IMPLEMENTED**. TIME **IMPLEMENTED**. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH overall **OPEN / PARTIAL**. [ADR-053](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) **Accepted**. [FG-034](feature-gates/FG-034-account-recovery-and-transactional-email.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-033](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. FG-034 MAIL-A / AUTH-A / AUTH-B / AUTH-C / MAIL-B / AUTH-D is **IMPLEMENTED / PASS** (local/fake mail; Postmark HTTP adapter activated; live Postmark **DEFERRED**; responsive Forgot Password / Reset UX; complete local E2E; Native Signing invitation/resend/complete). FG-033 SIGN-E convert-once + generated-contract ceremony is **IMPLEMENTED**. Real iPhone UAT **DEFERRED**. FG-033 SIGN-D Change Order E2E + office/Hub + automated mobile UX is **IMPLEMENTED**. FG-033 SIGN-C countersign + executed PDF custody is **IMPLEMENTED**. FG-033 SIGN-B secure invitation + public customer ceremony is **IMPLEMENTED**. FG-033 SIGN-A Native Signing freeze + request + audit is **IMPLEMENTED**. FG-024 Slice A empty-library engine is **CLOSED / OPERATIONAL FOR UAT** (live / empty of PRODUCTION). FG-024 Slice B update foundation is **CLOSED / OPERATIONAL FOR UAT** (live). FG-024 Slice C generation is **CLOSED / OPERATIONAL FOR UAT** (live / synthetic-UAT proven / no real jurisdictional content). TECH-A activation + authority class **IMPLEMENTED**. TECH-B generation policy **IMPLEMENTED**. TECH-C Family 05 merge + artifact custody **IMPLEMENTED**. TECH-D synthetic Ontario UAT **IMPLEMENTED**. Hub CONTRACT fail-closed UX **IMPLEMENTED** (ALLOW/WARN/BLOCK). Independent BMR contract-story **PASS**. BMR DEMO READY **NO**. FG-032 QuickBooks Option A is **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**. FG-029 supplier workflow is **CLOSED / OPERATIONAL FOR UAT**. FG-027 costing approval is **CLOSED / OPERATIONAL FOR UAT**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output output 4 / live QuickBooks API / Ontario contract **not complete**. Native Signing production **NOT COMPLETE**. |
| Architecture status | CAR-001 approved. SCH-A **IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. [architecture/fg-035-sch-implementation-preflight.md](architecture/fg-035-sch-implementation-preflight.md) remains the design freeze. [architecture/fg-035-sch-dynamic-scheduling-preflight.md](architecture/fg-035-sch-dynamic-scheduling-preflight.md) **PREFLIGHT COMPLETE / ARCHITECTURE RECORDED**. [architecture/interactive-help-voice-and-user-manual-future-record.md](architecture/interactive-help-voice-and-user-manual-future-record.md) **FUTURE / RECORDED / MANDATORY PRE-UAT V1 / NOT IMPLEMENTATION-AUTHORIZED**. [FG-034](feature-gates/FG-034-account-recovery-and-transactional-email.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-052](adr/ADR-052-account-recovery-and-transactional-email.md) **Accepted** (supersedes ADR-041 Decision 7 V1 CLI-only/no-mail without rewriting ADR-041). [FG-033](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED / OPERATIONAL FOR UAT**. No new ADR for SIGN-E. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. [architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md](architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md) **PREFLIGHT COMPLETE**; subsequent product **CLOSED / OPERATIONAL FOR UAT**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / TECH-A IMPLEMENTED / TECH-B IMPLEMENTED / TECH-C IMPLEMENTED / TECH-D IMPLEMENTED / OVERALL OPEN / PARTIAL**. [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md) **FUTURE / RECORDED / COMPLETE FOR PRODUCT-DIRECTION RECORDING / NOT IMPLEMENTATION-AUTHORIZED** (15 Sep 2026 recording closed through §105 step 13). ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-034 AUTH-D complete E2E close + Postmark HTTP adapter (**mocked success/failure/missing-config; live Postmark DEFERRED**). FG-034 MAIL-B Native Signing invitation/resend/complete through MAIL-A (**local/fake; SENT ≠ delivered; copyable URL retained**). FG-034 AUTH-C complete Account Recovery E2E through local transactional delivery (**enumeration; token failure; CSRF; rate limits; `credentials_epoch` session invalidation; CLI break-glass; desktop/mobile automated parity**). FG-034 AUTH-B responsive Forgot Password / Reset UX (**CSRF; generic confirmation; 8-character floor; desktop/iPhone CSS parity; local/fake MAIL-A only**). FG-034 MAIL-A local/fake transactional engine + AUTH-A credentials_epoch / reset tokens / rate limits / 8-char new-password floor (**live-migrated**; no live Postmark HTTP). FG-033 SIGN-E convert-once Family 05 PDF + generated-contract ceremony + desktop/iPhone parity (**live-migrated / automated product validation PASS**; real iPhone UAT **DEFERRED**). FG-033 SIGN-D Change Order E2E + office/Hub + automated mobile UX (**automated product validation PASS**; real iPhone UAT **DEFERRED**). FG-033 SIGN-C countersign + executed PDF custody (**live-migrated / synthetic UAT PASS**; COUNTERSIGNED/EXECUTED; VOID/EXPIRE/DECLINE/RESEND). FG-033 SIGN-B invitation + public `/sign` ceremony (**live-migrated / synthetic customer UAT PASS**; hash-at-rest token; no customer account; SENT → SIGNED). FG-033 SIGN-A freeze + request engine + audit (**live-migrated / office synthetic UAT PASS**). FG-024 TECH-C Family 05 DOCX merge + private artifact custody (**live-migrated / synthetic UAT PASS**; no PRODUCTION Ontario package). FG-024 TECH-B C1/C2/C3 generation policy (**live-migrated / synthetic UAT PASS**; no PRODUCTION Ontario package). FG-024 TECH-A HUMAN/COUNSEL activation + SYNTHETIC_UAT / PRODUCTION authority class (**live-migrated / synthetic UAT PASS**). FG-024 fail-closed CONTRACT Hub UX (**implemented**; selector remains authority; WARN distinguished from BLOCK; no generation control). FG-024 Slice C generation + immutable snapshot (**live-migrated / synthetic office UAT PASS / operational for UAT**; labeled synthetic contracts only). FG-024 Slice B source / snapshot / candidate / review foundation (**live-migrated / bounded office UAT PASS / operational for UAT**; labeled synthetic source evidence only). FG-024 Slice A empty legal-content library + ADR-037-backed selection + coded fail-closed (**live-migrated / bounded office UAT PASS / operational for UAT**; library **empty of PRODUCTION**). FG-032 Slice C append-only ENTERED/REVERSED/CORRECTED confirmation with unique occupancy lock (**live-migrated / bounded office UAT PASS / operational for UAT**). |
| Incomplete work | Help / Voice / User Manual **RECORDED / NOT IMPLEMENTED**. SCH-B / SCH-C / SCH-D / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. Live Postmark **DEFERRED**. Physical iPhone Account Recovery UAT **DEFERRED**. FG-024 Slice D **not authorized**. |
| Database and migration status | Live current **`f6e7f8a9b0c1 (head)`**. Repository head **`f6e7f8a9b0c1`**. Live SCH-A migration proven/reconciled from durable evidence; this reconciliation did **not** apply it. FG-035 TIME **applied live** 2026-09-15 (superseded as live current). FG-035 SCOPE **applied live** 2026-09-15. FG-035 TAX/WBS **applied live** 2026-09-15. FG-034 MAIL-A/AUTH-A **applied live** 2026-09-15. PRODUCTION packages **0**. No EST-2026-0019 mutation. Labeled FG-035 TAX/WBS UAT project **id 42**. Labeled FG-035 SCOPE UAT project **id 43**. Labeled FG-035 TIME UAT project **id 44**. Labeled FG-035 SCH-A UAT project **id 45**. Remaining applied-live chain through FG-033 / FG-024 / FG-032 is unchanged. |
| Test status | Dedicated SCH-A **13 passed**, 31 warnings, **4.12s**, exit **0**. Focused TAX/WBS+SCOPE+TIME+SCH-A+Hub/Field/MONITOR **112 passed**, 482 warnings, **51.94s**, exit **0**. Full suite **1096 passed**, 3647 warnings, **514.43s**, exit **0**. HISTORICAL SCH-A engineering full suite **1096 passed**, 3647 warnings, **413.66s**. HISTORICAL TIME full suite **1083 passed**, 3616 warnings, **466.85s**. HISTORICAL SCOPE full suite **1075 passed**, 3531 warnings, **437.62s**. HISTORICAL TAX/WBS full suite **1065 passed**, 3403 warnings, **456.75s**. |
| Documentation status | **2026-09-16 FG-035 SCH-A committed / SHA pinned.** FG-035 remains **OPEN / PARTIAL**. SCH-A **LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS**. SCH overall **OPEN / PARTIAL**. SCH-B / SCH-C / SCH-D / PERF / CLOSE / LEARN / QB-T **NOT AUTHORIZED**. V1 **unchanged** (**60% / 4 of 11**). |
| Decisions made (this implementation) | 2026-09-15 preserved existing live f6 / Project 45. Reconstructed durable evidence. Re-exercised FAIL CLOSED window integrity, Company/Hub, and atomic Element+Activity. Fresh post-UAT tests PASS. |
| Decisions pending | SCH-B authorization. PERF authorization. Help/Voice/Manual preflight. Live Postmark. Physical iPhone UAT. Slice D. FG-030. V1-04. |
| Uncommitted work | None after SCH-A implementation commit. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin SCH-B / PERF / CLOSE / LEARN / QB-T. Do **not** rescore V1. |
| Next candidate milestone | FG-035 SCH-B — **NOT AUTHORIZED FROM THIS RECORD**. |
| Documents to read first | [feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md](feature-gates/FG-035-project-work-structure-time-schedule-performance-learn.md) → [testing/fg035-sch-a-live-bounded-uat-record.md](testing/fg035-sch-a-live-bounded-uat-record.md) → [adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md](adr/ADR-053-project-work-structure-and-closed-operational-learning-loop.md) → [architecture/fg-035-sch-implementation-preflight.md](architecture/fg-035-sch-implementation-preflight.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Approved next Cursor prompt location or summary | **STOP.** Return to ChatGPT Architect. No SCH-B implementation authorization. |
| Commit status | Product SCH-A **`fd8a66990df8286e54151b80b6f3cd5be5dd3ad1`**. Product TIME **`03c074fb1eb2bbca77ba86e495726c0e042c1979`**. Live current `f6e7f8a9b0c1`. Repo Alembic head `f6e7f8a9b0c1`. |
| Governance baseline | V1 register GOVERNING / 60% / 4 of 11 COMPLETE; FG-035 OPEN / PARTIAL; TAX/WBS IMPLEMENTED; SCOPE IMPLEMENTED; TIME IMPLEMENTED; SCH-A IMPLEMENTED / TESTED / LIVE-MIGRATED / BOUNDED SYNTHETIC UAT PASS; ADR-053 Accepted; FG-034 CLOSED / OPERATIONAL FOR UAT; FG-033 CLOSED / OPERATIONAL FOR UAT; live current f6e7f8a9b0c1; repo Alembic head f6e7f8a9b0c1 |

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

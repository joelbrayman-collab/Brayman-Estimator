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
| Current commit / `origin/main` | This 15 Sep 2026 FG-033 SIGN-E convert-once + generated-contract Native Signing. Parent SIGN-D **`46798858f8743a7fae486c6c0e1b0766b0df61f5`**. Opening V1 product remains **`d6fa984b1e84be4a1b21ff8f7358fc1d43fa74dc`**. Live current **`e0f1a2b3c4d5 (head)`**. Repository Alembic head **`e0f1a2b3c4d5`**. |
| Latest completed **coded** milestone on `main` | **FG-033 SIGN-E convert-once + generated-contract Native Signing + desktop/iPhone parity** (**IMPLEMENTED / TESTED / LIVE-MIGRATED / AUTOMATED PASS / REAL IPHONE UAT DEFERRED / GATE CLOSED / OPERATIONAL FOR UAT**). Prior: **FG-033 SIGN-D Change Order E2E**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **60%**; **4 / 11** COMPLETE (V1-01, V1-02, V1-03, V1-05); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. Current scored package **V1-04** (**PARTIAL**). [FG-033](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED / OPERATIONAL FOR UAT**. SIGN-A through SIGN-E **IMPLEMENTED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / TECH-A IMPLEMENTED / TECH-B IMPLEMENTED / TECH-C IMPLEMENTED / TECH-D IMPLEMENTED / OVERALL OPEN / PARTIAL**. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–6 IMPLEMENTED / NOT CLOSED**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. FG-033 SIGN-E convert-once + generated-contract ceremony is **IMPLEMENTED**. Real iPhone UAT **DEFERRED**. FG-033 SIGN-D Change Order E2E + office/Hub + automated mobile UX is **IMPLEMENTED**. FG-033 SIGN-C countersign + executed PDF custody is **IMPLEMENTED**. FG-033 SIGN-B secure invitation + public customer ceremony is **IMPLEMENTED**. FG-033 SIGN-A Native Signing freeze + request + audit is **IMPLEMENTED**. FG-024 Slice A empty-library engine is **CLOSED / OPERATIONAL FOR UAT** (live / empty of PRODUCTION). FG-024 Slice B update foundation is **CLOSED / OPERATIONAL FOR UAT** (live). FG-024 Slice C generation is **CLOSED / OPERATIONAL FOR UAT** (live / synthetic-UAT proven / no real jurisdictional content). TECH-A activation + authority class **IMPLEMENTED**. TECH-B generation policy **IMPLEMENTED**. TECH-C Family 05 merge + artifact custody **IMPLEMENTED**. TECH-D synthetic Ontario UAT **IMPLEMENTED**. Hub CONTRACT fail-closed UX **IMPLEMENTED** (ALLOW/WARN/BLOCK). Independent BMR contract-story **PASS**. BMR DEMO READY **NO**. FG-032 QuickBooks Option A is **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**. FG-029 supplier workflow is **CLOSED / OPERATIONAL FOR UAT**. FG-027 costing approval is **CLOSED / OPERATIONAL FOR UAT**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output output 4 / live QuickBooks API / Ontario contract **not complete**. Native Signing production **NOT COMPLETE**. |
| Architecture status | CAR-001 approved. [FG-033](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) **CLOSED / OPERATIONAL FOR UAT**. No new ADR for SIGN-E. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. [architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md](architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md) **PREFLIGHT COMPLETE**; subsequent product **CLOSED / OPERATIONAL FOR UAT**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C CLOSED / OPERATIONAL FOR UAT / TECH-A IMPLEMENTED / TECH-B IMPLEMENTED / TECH-C IMPLEMENTED / TECH-D IMPLEMENTED / OVERALL OPEN / PARTIAL**. [architecture/project-element-authority-future-record.md](architecture/project-element-authority-future-record.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-033 SIGN-E convert-once Family 05 PDF + generated-contract ceremony + desktop/iPhone parity (**live-migrated / automated product validation PASS**; real iPhone UAT **DEFERRED**). FG-033 SIGN-D Change Order E2E + office/Hub + automated mobile UX (**automated product validation PASS**; real iPhone UAT **DEFERRED**). FG-033 SIGN-C countersign + executed PDF custody (**live-migrated / synthetic UAT PASS**; COUNTERSIGNED/EXECUTED; VOID/EXPIRE/DECLINE/RESEND). FG-033 SIGN-B invitation + public `/sign` ceremony (**live-migrated / synthetic customer UAT PASS**; hash-at-rest token; no customer account; SENT → SIGNED). FG-033 SIGN-A freeze + request engine + audit (**live-migrated / office synthetic UAT PASS**). FG-024 TECH-C Family 05 DOCX merge + private artifact custody (**live-migrated / synthetic UAT PASS**; no PRODUCTION Ontario package). FG-024 TECH-B C1/C2/C3 generation policy (**live-migrated / synthetic UAT PASS**; no PRODUCTION Ontario package). FG-024 TECH-A HUMAN/COUNSEL activation + SYNTHETIC_UAT / PRODUCTION authority class (**live-migrated / synthetic UAT PASS**). FG-024 fail-closed CONTRACT Hub UX (**implemented**; selector remains authority; WARN distinguished from BLOCK; no generation control). FG-024 Slice C generation + immutable snapshot (**live-migrated / synthetic office UAT PASS / operational for UAT**; labeled synthetic contracts only). FG-024 Slice B source / snapshot / candidate / review foundation (**live-migrated / bounded office UAT PASS / operational for UAT**; labeled synthetic source evidence only). FG-024 Slice A empty legal-content library + ADR-037-backed selection + coded fail-closed (**live-migrated / bounded office UAT PASS / operational for UAT**; library **empty of PRODUCTION**). FG-032 Slice C append-only ENTERED/REVERSED/CORRECTED confirmation with unique occupancy lock (**live-migrated / bounded office UAT PASS / operational for UAT**). |
| Incomplete work | Real iPhone UAT **DEFERRED**. FG-024 Slice D **not authorized**. Subcontract RFQ/package remains **maturation during UAT / not implemented**. FG-030 supplier login **not implemented**. Field favicon remains tenant PNG (no supplied square favicon). Website Version 15 identity published (external). HostPapa migration **QUEUED POST-BETA**. FG-025 remaining surfaces **NOT AUTHORIZED** (customer Proposal/PDF terminology **done**). Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production completeness**; Project Closeout; four-output output 4; live QuickBooks API; Ontario contract/warranty templates. Project Element / Time / LEARN **recorded only / not implemented**. |
| Database and migration status | Live current **`e0f1a2b3c4d5 (head)`**. Repository head **`e0f1a2b3c4d5`**. One graph head. Live current **equals** repository head. FG-033 SIGN-E **applied live** 2026-09-15. FG-033 SIGN-C **applied live** 2026-09-14. FG-033 SIGN-B **applied live** 2026-09-14. FG-033 SIGN-A **applied live** 2026-09-14. FG-024 TECH-C **applied live** 2026-09-14. FG-024 TECH-B **applied live** 2026-09-14. FG-024 TECH-A **applied live** 2026-09-14. FG-024 Slice C **applied live** 2026-09-13. FG-024 Slice B **applied live** 2026-09-13. FG-024 Slice A **applied live** 2026-09-13. Library tables **empty of PRODUCTION**. PRODUCTION packages **0**. Labeled Slice B UAT source `FG024B-UAT-SRC-001` retained. Labeled Slice C UAT client **23** / project **28** / contracts `CTR-2026-0001` and `CTR-2026-0002` retained. TECH-D `CTR-2026-0003` / `CTR-2026-0004` retained. SIGN-A `SIGN-2026-0001` / `SIGN-2026-0002` / `CTR-2026-0005` retained. SIGN-B `SIGN-2026-0003` retained SIGNED. SIGN-C `SIGN-2026-0004` / `SIGN-2026-0005` EXECUTED. SIGN-D live residue `SIGN-2026-0010` EXECUTED / `0011` VOIDED / `0012` VOIDED. FG-032 A+B **`e9f0a1b2c3d4` applied live** 2026-09-11. Slice C events **`f0a1b2c3d4e5`** and occupancy **`f1a2b3c4d5e6` applied live** 2026-09-11. Labeled DEMO UAT projects **id 14** (FG-029), **id 19** (FG-031 Slice A canonical), **id 25** (FG-031 Slice B canonical), **id 26** (FG-032 canonical), **id 9** (FG-016 Pratt), **id 13** (FG-023 MONITOR), and **id 28** (FG-024 Slice C). No live BMR account. No EST-2026-0019 mutation. |
| Test status | Full suite this SIGN-E slice **981 passed**, 3262 warnings, **371.67s**, exit **0**. Dedicated SIGN-E **19 passed**. Dedicated SIGN-D **11 passed**. Dedicated SIGN-C **18 passed**. Dedicated SIGN-A **11 passed**. Dedicated SIGN-B **18 passed**. Focused SIGN-A/B/C/D/E + CO + Hub + TECH **208 passed**. HISTORICAL SIGN-D **962 passed**, 3184 warnings, **317.78s**. |
| Documentation status | **2026-09-15 FG-033 SIGN-E** memorialized. Real iPhone UAT **DEFERRED TO BRAYMAN / BEN REAL-WORLD UAT** — **NOT CLAIMED AS PASS**. Ontario Legal Content Gate production remains **EMPTY**. Family 05 remains **COMMERCIAL_DRAFT**. No external-review dependency. Independent BMR contract-story **PASS**. BMR DEMO READY remains **NO**. FG-033 **CLOSED / OPERATIONAL FOR UAT**. FG-024 overall **NOT CLOSED**. V1 **unchanged** (**60% / 4 of 11**). |
| Decisions made (this implementation) | 2026-09-15 Joel / ChatGPT Architect authorized SIGN-E convert-once + contract ceremony + desktop/iPhone parity and FG-033 close on automated product validation. Real iPhone UAT remains **DEFERRED**, not PASS. One additive migration. No new ADR. No V1 rescore. |
| Decisions pending | Slice D authorization. FG-030 implementation authorization. V1-04 start. Architect review of overall BMR DEMO READY. Later Project Element architecture preflight. Remaining Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 except #1 (selected), #2, and #4 (implemented). FG-025 remaining-surface authorization. Observation Delete. HostPapa hosting migration (post-beta). Subcontract RFQ/package remains maturation. EST-2026-0019 Joel review marks (commercial; not this product). |
| Uncommitted work | None after this SIGN-E commit. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect. Do **not** begin Slice D. Do **not** populate Ontario legal content. Do **not** implement FG-030. Do **not** begin V1-04 product work. Do **not** close FG-024 or FG-025. |
| Next candidate milestone | FG-024 Slice D / Ontario PRODUCTION legal population / transactional email — **NOT AUTHORIZED FROM THIS SLICE**. |
| Documents to read first | [feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md](feature-gates/FG-033-native-signing-document-approval-signature-and-executed-artifact.md) → [testing/fg033-sign-e-live-bounded-uat-record.md](testing/fg033-sign-e-live-bounded-uat-record.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Approved next Cursor prompt location or summary | **STOP.** Return to ChatGPT Architect. |
| Commit status | This 15 Sep 2026 FG-033 SIGN-E product commit on `origin/main`. Parent SIGN-D **`46798858f8743a7fae486c6c0e1b0766b0df61f5`**. Live current `e0f1a2b3c4d5 (head)`. Repo head `e0f1a2b3c4d5`. |
| Governance baseline | V1 register GOVERNING / 60% / 4 of 11 COMPLETE; FG-033 CLOSED / OPERATIONAL FOR UAT; SIGN-A IMPLEMENTED; SIGN-B IMPLEMENTED; SIGN-C IMPLEMENTED; SIGN-D IMPLEMENTED; SIGN-E IMPLEMENTED; REAL IPHONE UAT DEFERRED; FG-024 Slice A CLOSED / OPERATIONAL FOR UAT; FG-024 Slice B CLOSED / OPERATIONAL FOR UAT; FG-024 Slice C CLOSED / OPERATIONAL FOR UAT; TECH-A IMPLEMENTED; TECH-B IMPLEMENTED; TECH-C IMPLEMENTED; TECH-D IMPLEMENTED; FG-024 OVERALL OPEN / PARTIAL; ADR-050 Accepted; ADR-051 Accepted; FG-032 CLOSED / OPERATIONAL FOR UAT; V1-05 COMPLETE; V1-04 PARTIAL / CURRENT SCORED PACKAGE; live current e0f1a2b3c4d5 (head); repo Alembic head e0f1a2b3c4d5 |

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

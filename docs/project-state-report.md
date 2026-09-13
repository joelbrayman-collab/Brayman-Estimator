# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-13 |

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
| Report date | 2026-09-13 |
| Repository | Brayman-Estimator (The Estimator / CalibraytAI) |
| Current branch | `main` |
| Current commit / `origin/main` | This FG-024 Slice C preflight commit. Parent **`a176db36034af17309fd3f3e7e8c9a58043d6f56`**. Opening V1 product remains **`d6fa984b1e84be4a1b21ff8f7358fc1d43fa74dc`**. Live current **`c2d3e4f5a6b7 (head)`**. Repository Alembic head **`c2d3e4f5a6b7`**. |
| Latest completed **coded** milestone on `main` | **FG-024 Slice B live migrate + bounded office UAT** (**CLOSED / OPERATIONAL FOR UAT**). Prior: **FG-024 Slice B product foundation**. Prior: **CalibraytAI Opening V1** (**DEPLOYED / OPERATIONAL**). Prior: **FG-024 Slice A live migrate + bounded office UAT** (**CLOSED / OPERATIONAL FOR UAT**). |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **60%**; **4 / 11** COMPLETE (V1-01, V1-02, V1-03, V1-05); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. Current scored package **V1-04** (**PARTIAL**). [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C PREFLIGHT COMPLETE / PRODUCT NOT AUTHORIZED / OVERALL OPEN / PARTIAL**. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. FG-024 Slice A empty-library engine is **CLOSED / OPERATIONAL FOR UAT** (live / empty). FG-024 Slice B update foundation is **CLOSED / OPERATIONAL FOR UAT** (live). FG-024 Slice C generation is **PREFLIGHT COMPLETE / PRODUCT NOT AUTHORIZED / NOT IMPLEMENTED**. FG-032 QuickBooks Option A is **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**. FG-029 supplier workflow is **CLOSED / OPERATIONAL FOR UAT**. FG-027 costing approval is **CLOSED / OPERATIONAL FOR UAT**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output output 4 / live QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. [architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md](architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md) **PREFLIGHT COMPLETE**. [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A CLOSED / OPERATIONAL FOR UAT / SLICE B CLOSED / OPERATIONAL FOR UAT / SLICE C PREFLIGHT COMPLETE / PRODUCT NOT AUTHORIZED / OVERALL OPEN / PARTIAL**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-024 Slice B source / snapshot / candidate / review foundation (**live-migrated / bounded office UAT PASS / operational for UAT**; labeled synthetic source evidence only). FG-024 Slice A empty legal-content library + ADR-037-backed selection + coded fail-closed (**live-migrated / bounded office UAT PASS / operational for UAT**; library **empty**). FG-032 Slice C append-only ENTERED/REVERSED/CORRECTED confirmation with unique occupancy lock (**live-migrated / bounded office UAT PASS / operational for UAT**). FG-032 Slices A+B governed QuickBooks-ready sales-entry sheet + planned cost-class companion (private HTML/PDF; review/issue; **live-migrated / bounded office UAT PASS**). FG-031 Slice B thin `Subcontractor` + `SubcontractQuoteEvidence` + selected-quote freeze onto costing snapshot + Scope Delivery Review quote UI (**live-migrated / office UAT PASS**). Slice A `EstimateScopeDelivery` + Hub PRICE Scope Delivery Review + FG-027 `SCOPE_DELIVERY_UNRESOLVED` BLOCK requiring **CONFIRMED** routing + Supplier Package `CONTRACTOR_PURCHASED` filter (**live-migrated / office UAT PASS**). FG-028 Slice 3 approved CalibraytAI V2 runtime logo on Field header. FG-029 MaterialRequirement + Supplier Catalogue mapping review + frozen Supplier Package HTML/PDF (inform-only price) **live-migrated and DEMO UAT-verified**. FG-027 costing approval + Pricing consume/stale **live-migrated and office-UAT-verified**. |
| Incomplete work | FG-024 Slice C product **not authorized**. Slice D **not authorized**. Subcontract RFQ/package remains **maturation during UAT / not implemented**. FG-030 supplier login **not implemented**. Field favicon remains tenant PNG (no supplied square favicon). Website Version 15 identity published (external). HostPapa migration **QUEUED POST-BETA**. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; four-output output 4; live QuickBooks API; Ontario contract/warranty templates. |
| Database and migration status | Live current **`c2d3e4f5a6b7 (head)`**. Repository head **`c2d3e4f5a6b7`**. One graph head. Live current **equals** repository head. FG-024 Slice B **applied live** 2026-09-13. FG-024 Slice A **applied live** 2026-09-13. Library tables **empty**. Labeled Slice B UAT source `FG024B-UAT-SRC-001` retained. FG-032 A+B **`e9f0a1b2c3d4` applied live** 2026-09-11. Slice C events **`f0a1b2c3d4e5`** and occupancy **`f1a2b3c4d5e6` applied live** 2026-09-11. FG-031 Slice A **applied live**. Slice B **`d8e9f0a1b2c3` applied live**. FG-029 migration **applied live**. Labeled DEMO UAT projects **id 14** (FG-029), **id 19** (FG-031 Slice A canonical), **id 25** (FG-031 Slice B canonical), **id 26** (FG-032 canonical), **id 9** (FG-016 Pratt; reused for FG-024 Ontario empty-library UAT), and **id 13** (FG-023 MONITOR; reused for FG-024 unresolved-jurisdiction UAT). No live BMR account. |
| Test status | Full suite this Slice C preflight **809 passed**, 2738 warnings, **545.74s**, exit **0**. HISTORICAL Slice B dedicated **16 passed** / 2.21s. HISTORICAL Slice A dedicated **17 passed** / 2.25s. HISTORICAL Slice B live-UAT full **809 passed** / 278.30s. |
| Documentation status | [architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md](architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md) **PREFLIGHT COMPLETE**. Product **NOT AUTHORIZED**. [architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md](architecture/fg-024-slice-b-legal-content-source-lifecycle-preflight.md) **PREFLIGHT COMPLETE** with subsequent Slice B **CLOSED / OPERATIONAL FOR UAT**. [ADR-051](adr/ADR-051-legal-content-source-and-update-lifecycle.md) **Accepted**. Slice B **CLOSED / OPERATIONAL FOR UAT**. Slice A **CLOSED / OPERATIONAL FOR UAT**. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [testing/fg024-slice-a-live-migrate-bounded-uat-record.md](testing/fg024-slice-a-live-migrate-bounded-uat-record.md) **UAT PASS**. [testing/fg024-slice-b-live-migrate-bounded-uat-record.md](testing/fg024-slice-b-live-migrate-bounded-uat-record.md) **UAT PASS**. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **60%**. |
| Decisions made (this implementation) | 2026-09-13 Joel / ChatGPT Architect authorized Slice C **preflight only**. Generation + immutable snapshot architecture frozen. New ADR **not** required. Schema **required later** (not created). ADR-051 §6 remains deferred / fail-closed on that branch. Family 05 remains COMMERCIAL_DRAFT / presentation shell only. Native Signing remains separate. Empty library remains FAIL CLOSED. No product code. No migration. No live DB mutation. No Ontario/U.S. legal seed. No V1 rescore. |
| Decisions pending | FG-024 Slice C product authorization. C1 EstimateVersion/Proposal “APPROVED estimate” mapping for production UX. C2 ADR-051 §6 ALLOW/BLOCK/WARN. C3 warranty schedule in smallest engine vs later increment. Slice D authorization. FG-030 implementation authorization. V1-04 start. Remaining Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 except #1 (selected) and #2. FG-025 remaining-surface authorization. Observation Delete. Ontario counsel answers. HostPapa hosting migration (post-beta). Subcontract RFQ/package remains maturation. EST-2026-0019 Joel review marks (commercial; not this preflight). |
| Uncommitted work | None after this Slice C preflight commit. |
| Next approved milestone | **STOP.** Slice A and Slice B are **CLOSED / OPERATIONAL FOR UAT**. Slice C is **PREFLIGHT COMPLETE / PRODUCT NOT AUTHORIZED / NOT IMPLEMENTED**. Do **not** begin Slice C product or Slice D. Do **not** polish Opening V1. Do **not** integrate the public website. Do **not** implement FG-030. Do **not** begin V1-04 product work. |
| Next candidate milestone | FG-024 Slice C product — **NOT AUTHORIZED**. Slice D — **NOT AUTHORIZED**. V1-04 — **NOT AUTHORIZED**. FG-030 — **NOT AUTHORIZED**. |
| Documents to read first | [architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md](architecture/fg-024-slice-c-contract-generation-snapshot-preflight.md) → [feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) → [adr/ADR-051-legal-content-source-and-update-lifecycle.md](adr/ADR-051-legal-content-source-and-update-lifecycle.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Approved next Cursor prompt location or summary | **STOP.** Do **not** begin Slice C product or Slice D. Return to ChatGPT Architect. |
| Commit status | This FG-024 Slice C preflight commit on `origin/main`. Parent **`a176db36034af17309fd3f3e7e8c9a58043d6f56`**. Live current `c2d3e4f5a6b7 (head)`. Repo head `c2d3e4f5a6b7`. |
| Governance baseline | V1 register GOVERNING / 60% / 4 of 11 COMPLETE; FG-024 Slice A CLOSED / OPERATIONAL FOR UAT; FG-024 Slice B CLOSED / OPERATIONAL FOR UAT; FG-024 Slice C PREFLIGHT COMPLETE / PRODUCT NOT AUTHORIZED; FG-024 OVERALL OPEN / PARTIAL; ADR-050 Accepted; ADR-051 Accepted; FG-032 CLOSED / OPERATIONAL FOR UAT; V1-05 COMPLETE; V1-04 PARTIAL / CURRENT SCORED PACKAGE; live current c2d3e4f5a6b7 (head); repo Alembic head c2d3e4f5a6b7 |

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

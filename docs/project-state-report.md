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
| Current commit / `origin/main` | FG-024 Slice A product (this commit). Parent ADR-050 acceptance **`a4516b5a82ae6210751d42270e3250ca470cc139`**. Parent FG-024 Slice A preflight **`20c62d43ee12a679d39fbd44e2232a87754964ed`**. Parent catch-up **`3200112d627d6c6d8173daf72194f8409ac84b11`**. A+B product SHA **`70e571140e12377aa5bd009b598530576401113b`**. FG-032 product parent **`010f6d641a756ceb2ab67475a284d3b8426c7b20`**. Architecture **`93773820e410e327cd81919172c49a6f661def9e`**. Live current **`f1a2b3c4d5e6`**. Repository Alembic head **`b1c2d3e4f5a6`**. |
| Latest completed **coded** milestone on `main` | **FG-024 Slice A empty legal-content library** (**PRODUCT IMPLEMENTED IN REPOSITORY / NOT LIVE-MIGRATED / NOT OFFICE-UAT / NOT CLOSED**). Prior: **ADR-050 Accepted** (architecture only). Prior: **FG-032 documentation-only close + V1-05 rescore** (**CLOSED / OPERATIONAL FOR UAT**; V1-05 **COMPLETE**). Prior coded: **FG-032 Slice C live migrate + bounded office UAT**. Prior: **FG-032 Slice C atomic ENTERED occupancy repair**. Prior: **FG-032 Slice C** product. Prior: **FG-032 Slices A+B**. Prior: **FG-031 Slice B** (**LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT**). Prior: **FG-029 V1-03 BMR / supplier workflow** (**CLOSED / OPERATIONAL FOR UAT**). **FG-028 SLICES 1–3 COMPLETE / CLOSED**. **FG-027 CLOSED / OPERATIONAL FOR UAT.** V1-02 **COMPLETE**. V1-03 **COMPLETE**. V1-05 **COMPLETE**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **60%**; **4 / 11** COMPLETE (V1-01, V1-02, V1-03, V1-05); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. Current scored package **V1-04** (**PARTIAL**). [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A PRODUCT IMPLEMENTED IN REPOSITORY / NOT LIVE-MIGRATED / NOT OFFICE-UAT / NOT CLOSED**. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. FG-024 Slice A empty-library engine is **in the repository / not live-migrated**. FG-032 QuickBooks Option A is **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**. FG-029 supplier workflow is **CLOSED / OPERATIONAL FOR UAT**. FG-027 costing approval is **CLOSED / OPERATIONAL FOR UAT**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output output 4 / live QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / SLICE A PRODUCT IMPLEMENTED IN REPOSITORY / NOT LIVE-MIGRATED / NOT CLOSED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-024 Slice A empty legal-content library + ADR-037-backed selection + coded fail-closed (**in repository / not live-migrated**). FG-032 Slice C append-only ENTERED/REVERSED/CORRECTED confirmation with unique occupancy lock (**live-migrated / bounded office UAT PASS / operational for UAT**). FG-032 Slices A+B governed QuickBooks-ready sales-entry sheet + planned cost-class companion (private HTML/PDF; review/issue; **live-migrated / bounded office UAT PASS**). FG-031 Slice B thin `Subcontractor` + `SubcontractQuoteEvidence` + selected-quote freeze onto costing snapshot + Scope Delivery Review quote UI (**live-migrated / office UAT PASS**). Slice A `EstimateScopeDelivery` + Hub PRICE Scope Delivery Review + FG-027 `SCOPE_DELIVERY_UNRESOLVED` BLOCK requiring **CONFIRMED** routing + Supplier Package `CONTRACTOR_PURCHASED` filter (**live-migrated / office UAT PASS**). FG-028 Slice 3 approved CalibraytAI V2 runtime logo on Field header. FG-029 MaterialRequirement + Supplier Catalogue mapping review + frozen Supplier Package HTML/PDF (inform-only price) **live-migrated and DEMO UAT-verified**. FG-027 costing approval + Pricing consume/stale **live-migrated and office-UAT-verified**. |
| Incomplete work | FG-024 live migrate + office UAT + Slices B–D **not authorized**. Subcontract RFQ/package remains **maturation during UAT / not implemented**. FG-030 supplier login **not implemented**. Field favicon remains tenant PNG (no supplied square favicon). Website Version 15 identity published (external). HostPapa migration **QUEUED POST-BETA**. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; four-output output 4; live QuickBooks API; Ontario contract/warranty templates. |
| Database and migration status | Live current **`f1a2b3c4d5e6`**. Repository head **`b1c2d3e4f5a6`**. One graph head. Live current **does not equal** repository head (FG-024 Slice A **not applied live**). FG-032 A+B **`e9f0a1b2c3d4` applied live** 2026-09-11. Slice C events **`f0a1b2c3d4e5`** and occupancy **`f1a2b3c4d5e6` applied live** 2026-09-11. FG-031 Slice A **applied live**. Slice B **`d8e9f0a1b2c3` applied live**. FG-029 migration **applied live**. Labeled DEMO UAT projects **id 14** (FG-029), **id 19** (FG-031 Slice A canonical), **id 25** (FG-031 Slice B canonical), and **id 26** (FG-032 canonical; Slice C working package **1**, DRAFT residue **4**). No live BMR account. |
| Test status | 2026-09-13 FG-024 Slice A product dedicated **17 passed**, 35 warnings, 2.29s (`./venv/bin/python -m pytest -q tests/test_legal_content_library_fg024.py`). Full suite **782 passed**, 2704 warnings, **267.61s**. HISTORICAL ADR-050 acceptance full suite **765 passed**, 2669 warnings, **301.88s**. HISTORICAL FG-024 Slice A preflight full suite **765 passed**, 2669 warnings, **268.08s**. HISTORICAL catch-up full suite **765 passed**, 2669 warnings, **297.20s**. HISTORICAL Slice C live-migrate/UAT session remains dedicated FG-032 **37 passed** / 16.61s; affected regressions **256 passed** / 88.48s; full **765 passed** / 299.75s. Bounded office UAT **97 cases PASS**. |
| Documentation status | [architecture/fg-024-slice-a-legal-content-library-preflight.md](architecture/fg-024-slice-a-legal-content-library-preflight.md) **PREFLIGHT COMPLETE**. Slice A product **IN REPOSITORY / NOT LIVE-MIGRATED**. [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) **Accepted**. [governance/product-identity.md](governance/product-identity.md) **GOVERNING** for current vs former name. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **60%**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **CLOSED / OPERATIONAL FOR UAT**. V1-05 **COMPLETE**. [testing/fg032-slice-c-live-migrate-bounded-uat-record.md](testing/fg032-slice-c-live-migrate-bounded-uat-record.md). [testing/fg032-slices-ab-live-migrate-bounded-uat-record.md](testing/fg032-slices-ab-live-migrate-bounded-uat-record.md). [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Decisions made (this implementation) | 2026-09-13 Joel / ChatGPT Architect authorized FG-024 Slice A empty-library product. Persistence + selection + fail-closed **implemented in repository**. Live migrate **not** run. No UI. No Ontario/U.S. seed. V1 score **unchanged**. EST-2026-0019 commercial occupancy preserved. Prior: 2026-09-13 Joel / ChatGPT Architect **Accepted** [ADR-050](adr/ADR-050-north-american-legal-content-library-ownership.md) (architecture / fail-closed ownership only). |
| Decisions pending | FG-024 Slice A **live migrate + bounded office UAT**. Slices B–D. FG-030 implementation authorization. V1-04 start. Remaining Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 except #1 (selected) and #2. FG-025 remaining-surface authorization. Observation Delete. Ontario counsel answers. HostPapa hosting migration (post-beta). Subcontract RFQ/package remains maturation. EST-2026-0019 Joel review marks (commercial; not this product). |
| Uncommitted work | None after this documentation commit. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate FG-024. Do **not** begin Slice B/C/D. Do **not** implement FG-030. Do **not** begin V1-04 product work. Do **not** implement subcontract RFQ/package. Do **not** implement live QuickBooks API. Website source is **not** this repository. |
| Next candidate milestone | FG-024 Slice A live migrate + bounded office UAT — **NOT AUTHORIZED**. Slice B — **NOT AUTHORIZED**. V1-04 — **NOT AUTHORIZED**. FG-030 — **NOT AUTHORIZED**. |
| Documents to read first | [feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) → [architecture/fg-024-slice-a-legal-content-library-preflight.md](architecture/fg-024-slice-a-legal-content-library-preflight.md) → [adr/ADR-050-north-american-legal-content-library-ownership.md](adr/ADR-050-north-american-legal-content-library-ownership.md) → [v1-completion-register.md](v1-completion-register.md) → [session-handoff.md](session-handoff.md) |
| Approved next Cursor prompt location or summary | **STOP.** No live migrate. No Slice B. Return to ChatGPT Architect. |
| Commit status | FG-024 Slice A product is this commit. Parent ADR-050 acceptance **`a4516b5a82ae6210751d42270e3250ca470cc139`**. Live current `f1a2b3c4d5e6`. Repo head `b1c2d3e4f5a6`. |
| Governance baseline | V1 register GOVERNING / 60% / 4 of 11 COMPLETE; FG-024 Slice A PRODUCT IN REPOSITORY / NOT LIVE-MIGRATED / NOT CLOSED; ADR-050 Accepted; FG-032 CLOSED / OPERATIONAL FOR UAT; V1-05 COMPLETE; V1-04 PARTIAL / CURRENT SCORED PACKAGE; ADR-049 Accepted; FG-031 CLOSED / OPERATIONAL FOR UAT; ADR-048 Accepted; FG-030 RECORDED / NOT IMPLEMENTATION-AUTHORIZED; FG-029 CLOSED / OPERATIONAL FOR UAT; ADR-046 Accepted; ADR-008 Proposed; FG-028 SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT; FG-027 CLOSED / OPERATIONAL FOR UAT; live current f1a2b3c4d5e6; repo Alembic head b1c2d3e4f5a6 |

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

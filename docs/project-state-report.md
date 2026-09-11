# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-11 |

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
| Report date | 2026-09-11 |
| Repository | Brayman-Estimator (The Estimator / CalibraytAI) |
| Current branch | `main` |
| Current commit / `origin/main` | Docs pin **`9c254a38c39ef866cad3c5aca1f01cae4907f376`** (`docs: pin FG-032 Slices A+B SHA`) until this reconciliation. Product SHA **`70e571140e12377aa5bd009b598530576401113b`** (`feat: implement FG-032 QuickBooks-ready artifacts`). FG-032 product parent **`010f6d641a756ceb2ab67475a284d3b8426c7b20`** (`docs: correct FG-032 Issued vs Accepted freeze`). Architecture **`93773820e410e327cd81919172c49a6f661def9e`** (`docs: define V1-05 QuickBooks Option A`). Live current **`d8e9f0a1b2c3`**. Repository Alembic head **`e9f0a1b2c3d4`**. |
| Latest completed **coded** milestone on `main` | **FG-032 Slices A+B** product (**IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / OFFICE UAT NOT RUN / OVERALL NOT CLOSED**). Prior coded: **FG-031 Slice B** (**LIVE-MIGRATED / OFFICE UAT PASS / OPERATIONAL FOR UAT**). Prior: **FG-029 V1-03 BMR / supplier workflow** (**CLOSED / OPERATIONAL FOR UAT**). **FG-028 Slices 1–3 COMPLETE / CLOSED**. **FG-027 CLOSED / OPERATIONAL FOR UAT.** V1-02 **COMPLETE**. V1-03 **COMPLETE**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **55%**; **3 / 11** COMPLETE (V1-01, V1-02, V1-03); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. Current scored package **V1-04** (**PARTIAL**). [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slices A+B **IMPLEMENTED / NOT LIVE-MIGRATED / OVERALL NOT CLOSED**. [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. FG-032 QuickBooks Option A Slices A+B are **IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED**. FG-029 supplier workflow is **CLOSED / OPERATIONAL FOR UAT**. FG-027 costing approval is **CLOSED / OPERATIONAL FOR UAT**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output output 4 / live QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. [ADR-049](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slices A+B **IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED**. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-032 Slices A+B governed QuickBooks-ready sales-entry sheet + planned cost-class companion (private HTML/PDF; review/issue; not live-migrated). FG-031 Slice B thin `Subcontractor` + `SubcontractQuoteEvidence` + selected-quote freeze onto costing snapshot + Scope Delivery Review quote UI (**live-migrated / office UAT PASS**). Slice A `EstimateScopeDelivery` + Hub PRICE Scope Delivery Review + FG-027 `SCOPE_DELIVERY_UNRESOLVED` BLOCK requiring **CONFIRMED** routing + Supplier Package `CONTRACTOR_PURCHASED` filter (**live-migrated / office UAT PASS**). FG-028 Slice 3 approved CalibraytAI V2 runtime logo on Field header. FG-029 MaterialRequirement + Supplier Catalogue mapping review + frozen Supplier Package HTML/PDF (inform-only price) **live-migrated and DEMO UAT-verified**. FG-027 costing approval + Pricing consume/stale **live-migrated and office-UAT-verified**. |
| Incomplete work | FG-032 live migration, office UAT, and Slice C **not authorized**. Subcontract RFQ/package remains **maturation during UAT / not implemented**. FG-030 supplier login **not implemented**. Field favicon remains tenant PNG (no supplied square favicon). Website Version 15 identity published (external). HostPapa migration **QUEUED POST-BETA**. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); four-output output 4; live QuickBooks API; Ontario contract/warranty templates. |
| Database and migration status | Live current **`d8e9f0a1b2c3`**. Repository head **`e9f0a1b2c3d4`**. FG-032 **`e9f0a1b2c3d4` file only / not applied live**. FG-031 Slice A **applied live**. Slice B **`d8e9f0a1b2c3` applied live**. FG-029 migration **applied live**. Labeled DEMO UAT projects **id 14** (FG-029), **id 19** (FG-031 Slice A canonical), and **id 25** (FG-031 Slice B canonical). No live BMR account. |
| Test status | **HISTORICAL / NOT RERUN** this documentation correction. Dedicated FG-032 **23 passed**, 306 warnings, 9.50s. Focused regression **209 passed**, 1279 warnings, 89.55s. Full **`./venv/bin/python -m pytest -q` → 751 passed**, 2479 warnings, 350.35s. Live migration **NOT RUN**. |
| Documentation status | [governance/product-identity.md](governance/product-identity.md) **GOVERNING** for current vs former name. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **55%**. [FG-032](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slices A+B **IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Decisions made (this implementation) | 2026-09-10 Joel accepted ADR-049 and authorized FG-032 Slices A+B. Product implemented. Migration file created. Tests passed. Live DB **not** mutated. Office UAT **not** run. Slice C **not** implemented. No V1 rescore. V1 remains **55% / 3 of 11**. Current scored package **V1-04 / PARTIAL**. V1-05 **PARTIAL**. BMR DEMO READY remains **NO**. BRAYMAN REAL-LIFE UAT READY remains **NO**. Independent remaining blocker: Ontario/fail-closed contract story. |
| Decisions pending | FG-032 live migration and office UAT authorization. Slice C authorization. FG-030 implementation authorization. V1-04 start. Remaining Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 except #1 (selected) and #2. FG-025 remaining-surface authorization. FG-024. Observation Delete. Ontario counsel answers. HostPapa hosting migration (post-beta). Subcontract RFQ/package remains maturation. |
| Uncommitted work | None after this documentation reconciliation. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate. Do **not** office-UAT. Do **not** implement Slice C. Do **not** implement FG-030. Do **not** begin V1-04 product work. Do **not** implement subcontract RFQ/package. Website source is **not** this repository. |
| Next candidate milestone | FG-032 live migrate / UAT — **NOT AUTHORIZED**. Slice C — **NOT AUTHORIZED**. FG-030 — **NOT AUTHORIZED**. V1-04 — **NOT AUTHORIZED**. Subcontract RFQ/package — **NOT AUTHORIZED**. |
| Documents to read first | [feature-gates/FG-032-quickbooks-ready-output-entry-v1.md](feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) → [architecture/fg-032-quickbooks-option-a-preflight.md](architecture/fg-032-quickbooks-option-a-preflight.md) → [adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md](adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) → [session-handoff.md](session-handoff.md) → [v1-completion-register.md](v1-completion-register.md) |
| Approved next Cursor prompt location or summary | **STOP.** No live-migration/UAT prompt from this implementation. |
| Commit status | Product SHA **`70e571140e12377aa5bd009b598530576401113b`** (`feat: implement FG-032 QuickBooks-ready artifacts`). Live current `d8e9f0a1b2c3`. Repo head `e9f0a1b2c3d4`. |
| Governance baseline | V1 register GOVERNING / 55% / 3 of 11 COMPLETE; FG-032 SLICES A+B IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED; ADR-049 Accepted; FG-031 CLOSED / OPERATIONAL FOR UAT; ADR-048 Accepted; FG-030 RECORDED / NOT IMPLEMENTATION-AUTHORIZED; FG-029 CLOSED / OPERATIONAL FOR UAT; ADR-046 Accepted; ADR-008 Proposed; FG-028 SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT; FG-027 CLOSED / OPERATIONAL FOR UAT; live current d8e9f0a1b2c3; repo Alembic head e9f0a1b2c3d4 |

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

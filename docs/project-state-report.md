# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-09 |

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
| Report date | 2026-09-09 |
| Repository | Brayman-Estimator (The Estimator / CalibraytAI) |
| Current branch | `main` |
| Current commit / `origin/main` | FG-031 Slice A product SHA **`54120608df98432b9be80faf8c2a3a08cdb5679c`**. Parent pin **`9c3eeddb0ae8e4c0daaba119ee6eb590a25c6a18`**. Architecture SHA **`1c6c8c492b92f11cc80ad1b6e8689f0e42523bcd`**. FG-028 Slice 3 product SHA **`502035fa70ced1d0ff042db3077cc66f50e68de4`**. FG-029 close SHA **`880697a246de7e901a81f89584168a9a9fb1dd67`**. FG-029 product SHA **`ee578dcb5a688842ebedaff0682131826e6c7188`**. Live current **`b6c7d8e9f0a1`**. Repository Alembic head **`c7d8e9f0a1b2`**. |
| Latest completed **coded** milestone on `main` | **FG-031 Slice A** (**IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / NOT CLOSED**). Prior: **FG-029 V1-03 BMR / supplier workflow** (**CLOSED / OPERATIONAL FOR UAT**). **FG-028 Slices 1–3 COMPLETE / CLOSED**. **FG-027 CLOSED / OPERATIONAL FOR UAT.** V1-02 **COMPLETE**. V1-03 **COMPLETE**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **55%**; **3 / 11** COMPLETE (V1-01, V1-02, V1-03); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **SLICE A IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. FG-029 supplier workflow is **CLOSED / OPERATIONAL FOR UAT**. FG-027 costing approval is **CLOSED / OPERATIONAL FOR UAT**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. [ADR-048](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [ADR-047](adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **SLICE A IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-031 Slice A `EstimateScopeDelivery` + Hub PRICE Scope Delivery Review + FG-027 `SCOPE_DELIVERY_UNRESOLVED` BLOCK requiring **CONFIRMED** routing (`PROPOSED` is not costing authority) + Supplier Package `CONTRACTOR_PURCHASED` filter (**not live-migrated**). FG-028 Slice 3 approved CalibraytAI V2 runtime logo on Field header. FG-029 MaterialRequirement + Supplier Catalogue mapping review + frozen Supplier Package HTML/PDF (inform-only price) **live-migrated and DEMO UAT-verified**. FG-027 costing approval + Pricing consume/stale **live-migrated and office-UAT-verified**. |
| Incomplete work | FG-031 live migrate / UAT / Slice B **not authorized**. FG-030 supplier login **not implemented**. Field favicon remains tenant PNG (no supplied square favicon). Website Version 15 identity published (external). HostPapa migration **QUEUED POST-BETA**. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates. |
| Database and migration status | Live current **`b6c7d8e9f0a1`**. Repository head **`c7d8e9f0a1b2`**. FG-031 Slice A file **not applied live**. FG-029 migration **applied live**. Labeled DEMO UAT project **id 14**. No live BMR account. |
| Test status | Dedicated FG-031 **26 passed**. Governed bundle **258 passed**. Full suite **707 passed**. Historical Slice A implementation full **704**. |
| Documentation status | [governance/product-identity.md](governance/product-identity.md) **GOVERNING** for current vs former name. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **55%**. [FG-031](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **SLICE A IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED**. [FG-030](feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Decisions made (this implementation) | 2026-09-09 Joel/ChatGPT authorized FG-031 Slice A human-confirmation costing gate repair. Costing requires CONFIRMED routing. PROPOSED is not costing authority. Reused `SCOPE_DELIVERY_UNRESOLVED`. V1 remains **55% / 3 of 11**. |
| Decisions pending | FG-031 live migrate / UAT / Slice B authorization. FG-030 implementation authorization. Remaining Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 except #2. FG-025 remaining-surface authorization. FG-024. Observation Delete. Ontario counsel answers. HostPapa hosting migration (post-beta). |
| Uncommitted work | None after this Slice A commit. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect. Do **not** live-migrate FG-031. Do **not** implement Slice B. Do **not** implement FG-030. Do **not** begin V1-04. Website source is **not** this repository. |
| Next candidate milestone | FG-031 live migrate / UAT — **NOT AUTHORIZED**. Slice B — **NOT AUTHORIZED**. FG-030 implementation — **NOT AUTHORIZED**. V1-04 — **NOT AUTHORIZED**. |
| Documents to read first | [adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md](adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) → [feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md](feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) → [architecture/fg-031-scope-delivery-make-buy-procurement-routing-preflight.md](architecture/fg-031-scope-delivery-make-buy-procurement-routing-preflight.md) → [session-handoff.md](session-handoff.md) |
| Approved next Cursor prompt location or summary | **STOP.** No Cursor prompt from this implementation. Live migrate / Slice B / FG-030 / V1-04 require separate authorization. |
| Commit status | FG-031 Slice A product SHA **`54120608df98432b9be80faf8c2a3a08cdb5679c`**. Live current `b6c7d8e9f0a1`. Repository head `c7d8e9f0a1b2`. FG-031 **SLICE A IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED**. FG-028 **CLOSED / OPERATIONAL FOR UAT**. FG-029 **LIVE-MIGRATED / UAT PASS / CLOSED**. |
| Governance baseline | V1 register GOVERNING / 55% / 3 of 11 COMPLETE; FG-031 SLICE A IMPLEMENTED / NOT LIVE-MIGRATED / NOT CLOSED; ADR-048 Accepted; FG-030 RECORDED / NOT IMPLEMENTATION-AUTHORIZED; FG-029 CLOSED / OPERATIONAL FOR UAT; ADR-046 Accepted; ADR-008 Proposed; FG-028 SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT; FG-027 CLOSED / OPERATIONAL FOR UAT; live current b6c7d8e9f0a1; repo Alembic head c7d8e9f0a1b2 |

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

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
| Current commit / `origin/main` | FG-029 product SHA pending pin after this commit. Parent architecture pin **`a077ba9f30c5925542fdf2663081f60a10241066`**. Architecture recording **`07039c8dabfeba7b6ef4714d2cee50abf648bc4f`**. FG-028 Slices 1–2 SHA **`e06fa92c4543ae641ba5067b1d277af048d97139`**. Live current **`a5b6c7d8e9f0`**. Repository Alembic head **`b6c7d8e9f0a1`**. |
| Latest completed **coded** milestone on `main` | **FG-029 V1-03 BMR / supplier workflow** (**IMPLEMENTED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / NOT CLOSED**). Prior: **FG-028 Slices 1–2**. **FG-027 CLOSED / OPERATIONAL FOR UAT.** V1-02 **COMPLETE**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **45%**; **2 / 11** COMPLETE (V1-01, V1-02); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **IMPLEMENTED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / NOT CLOSED**. [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–2 IMPLEMENTED / SLICE 3 HELD / NOT CLOSED**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. FG-029 supplier workflow is **in repository, not live-migrated**. FG-027 costing approval is **CLOSED / OPERATIONAL FOR UAT**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. [ADR-046](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **NOT CLOSED** (Slice 3 held). [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **IMPLEMENTED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / NOT CLOSED**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-029 MaterialRequirement + Supplier Catalogue mapping review + frozen Supplier Package HTML/PDF (inform-only price). FG-028 Slices 1–2 visible product identity. FG-027 costing approval + Pricing consume/stale **live-migrated and office-UAT-verified**. |
| Incomplete work | FG-029 live-migrate / UAT / close. FG-028 Slice 3 logo asset. Website identity **EXTERNAL**. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates. |
| Database and migration status | Live current **`a5b6c7d8e9f0`**. Repository head **`b6c7d8e9f0a1`**. FG-029 migration **file not applied live**. No live DB mutation. No live DEMO BMR seed. |
| Test status | Dedicated FG-029 **16 passed**. Material Catalogue **35 passed**. Estimating+FG-026+FG-027 **62 passed**. Output/PDF **41 passed**. Tenancy **56 passed**. Governed bundle **210 passed**. Full suite **677 passed**. |
| Documentation status | [governance/product-identity.md](governance/product-identity.md) **GOVERNING** for current vs former name. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **45%**. [FG-029](feature-gates/FG-029-bmr-supplier-workflow-v1.md) **NOT CLOSED**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **NOT CLOSED**. |
| Decisions made (this implementation) | 2026-09-09 Joel authorized FG-029 product implementation. Inform-only supplier price. ADR-008 stays Proposed. V1 percentages unchanged. Live migrate/UAT not authorized. |
| Decisions pending | FG-029 live-migrate / UAT / close. Slice 3 Joel-approved lettering asset. Website external pass. Remaining Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 except #2. FG-025 remaining-surface authorization. FG-024. Observation Delete. Ontario counsel answers. |
| Uncommitted work | None after this product commit (SHA in pin). |
| Next approved milestone | **STOP.** Do **not** live-migrate. Do **not** populate live DEMO BMR data. Do **not** begin another V1 package. FG-028 Slice 3 waits on Joel asset. Website is external. |
| Next candidate milestone | FG-029 live-migrate / UAT — **NOT AUTHORIZED until a separate prompt**. |
| Documents to read first | [adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md](adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) → [feature-gates/FG-029-bmr-supplier-workflow-v1.md](feature-gates/FG-029-bmr-supplier-workflow-v1.md) → [architecture/fg-029-bmr-supplier-workflow-v1-preflight.md](architecture/fg-029-bmr-supplier-workflow-v1-preflight.md) → [session-handoff.md](session-handoff.md) |
| Approved next Cursor prompt location or summary | **STOP.** Live-migrate / UAT / Slice 3 / website require separate authorization. |
| Commit status | Product SHA pending pin. Live current `a5b6c7d8e9f0`. Repository head `b6c7d8e9f0a1`. FG-029 **NOT LIVE-MIGRATED / NOT CLOSED**. FG-028 **NOT CLOSED**. |
| Governance baseline | V1 register GOVERNING / 45% / 2 of 11 COMPLETE; FG-029 implemented / not live-migrated / not closed; ADR-046 Accepted; ADR-008 Proposed; FG-028 Slices 1–2 implemented / Slice 3 held / NOT CLOSED; FG-027 CLOSED / OPERATIONAL FOR UAT; live current a5b6c7d8e9f0; repository head b6c7d8e9f0a1 |

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

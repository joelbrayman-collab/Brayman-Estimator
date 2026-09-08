# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-08 |

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
| Report date | 2026-09-08 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | FG-027 implementation SHA **pending this commit / follow-up pin**. Start pin **`28fb5c0445fafabb2924d5d43bce46bf5fca3d0e`**. Architecture recording **`076e12f022fa5248a34e7baf7d05ae51e9e0ac4b`**. Product parent FG-026 **`aa4c71800586e0b8e2a63931bcdc8bc44d87a489`**. Alembic graph head **`a5b6c7d8e9f0`**. Live current **`f4a5b6c7d8e9`**. |
| Latest completed **coded** milestone on `main` | **FG-027 IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED.** Dedicated **15** / bundle **176** / full **647**. **FG-026 CLOSED / OPERATIONAL FOR UAT** remains last live-migrated PRICE mapping close. Product SHA **`aa4c71800586e0b8e2a63931bcdc8bc44d87a489`**. **FG-023 CLOSED / OPERATIONAL FOR UAT** remains the last MONITOR close. **FG-021 CLOSED** remains the last Field Web product close. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **39%**; **1 / 11** COMPLETE (V1-01); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main` for prior closed gates. FG-027 costing approval is in repository only until live migrate. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-027 costing approval + Pricing consume/stale **in repository** (not live-migrated). FG-026 takeoff-to-estimate mapping **live-migrated and office-UAT-verified**. Prior coded baseline plus FG-025 Slice 1–5, FG-023 MONITOR, FG-021 Field Web, FG-020 Field Capture, FG-019 API, FG-018 auth. |
| Incomplete work | FG-027 live migrate + UAT. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; supplier/Winchester POC. |
| Database and migration status | Repository head **`a5b6c7d8e9f0`**. Live current **`f4a5b6c7d8e9`**. FG-027 migration **file only**. FG-026 tables **applied live**. One graph head. Live UAT line 7 / Assembly id 2 **not mutated**. |
| Test status | Dedicated FG-027 **15 passed**. Estimating focused **29**. Pricing focused **52**. Labour/material **60**. FG-026 **20**. Governed bundle **176**. Full suite **647 passed**. |
| Documentation status | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **39%**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Decisions made (this implementation) | 2026-09-08 Joel authorized FG-027 product implementation. Approve All = costing only. Live migrate / UAT not authorized. V1 readiness **unchanged 39%**. |
| Decisions pending | FG-027 live migrate + UAT authorization. Remaining Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 except #2. FG-025 remaining-surface authorization. FG-024. Observation Delete. Ontario counsel answers. |
| Uncommitted work | FG-027 product + docs pending the implementation commit. |
| Next approved milestone | **STOP.** Do **not** live-migrate FG-027. Do **not** UAT. Do **not** begin V1-03. Do **not** implement FG-024 or another FG-025 slice. |
| Next candidate milestone | FG-027 live migrate + bounded UAT — **NOT AUTHORIZED until a separate prompt**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [v1-completion-register.md](v1-completion-register.md) → [feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) → [adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) → [architecture/fg-027-costing-approval-preflight.md](architecture/fg-027-costing-approval-preflight.md) |
| Approved next Cursor prompt location or summary | **STOP.** Do **not** live-migrate FG-027. Do **not** begin FG-024. Do **not** begin another FG-025 slice. Do **not** begin LEARN. |
| Commit status | Implementation SHA pending this commit. Live current `f4a5b6c7d8e9`. Graph head `a5b6c7d8e9f0`. FG-027 **IMPLEMENTED / NOT LIVE-MIGRATED**. FG-026 **CLOSED**. FG-025 **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. FG-024 **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Governance baseline | V1 register GOVERNING / 39% / 1 of 11 COMPLETE; FG-027 IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED; ADR-044 Accepted; FG-026 CLOSED / OPERATIONAL FOR UAT; live current f4a5b6c7d8e9; repo head a5b6c7d8e9f0 |

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

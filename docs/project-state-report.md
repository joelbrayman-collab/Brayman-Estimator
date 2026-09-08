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
| Current commit / `origin/main` | FG-027 close SHA **`c348bcfb41daead674aaf75050fc0a6847a8c0c0`**. Parent pin **`cf282bc6ea5cb8c917b9bae052c84a31cae65445`**. Product repair SHA **`72949f99da2b56ec06e95e16e29fa194a6730bbd`**. Implementation SHA **`c751d72b32f1ed415375719df2fd69936ace64d7`**. Live current = heads **`a5b6c7d8e9f0`**. |
| Latest completed **coded** milestone on `main` | **FG-027 CLOSED / OPERATIONAL FOR UAT.** Remaining office UAT **PASS**. V1-02 **COMPLETE**. Product tests last verified dedicated **20** / A–D bundle **121** / full **652**. **FG-026 CLOSED / OPERATIONAL FOR UAT** remains last live-migrated PRICE mapping close. Product SHA **`aa4c71800586e0b8e2a63931bcdc8bc44d87a489`**. **FG-023 CLOSED / OPERATIONAL FOR UAT** remains the last MONITOR close. **FG-021 CLOSED** remains the last Field Web product close. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **45%**; **2 / 11** COMPLETE (V1-01, V1-02); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main` for prior closed gates. FG-027 costing approval is **CLOSED / OPERATIONAL FOR UAT**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-027 costing approval + Pricing consume/stale **live-migrated and office-UAT-verified**. FG-026 takeoff-to-estimate mapping **live-migrated and office-UAT-verified**. Prior coded baseline plus FG-025 Slice 1–5, FG-023 MONITOR, FG-021 Field Web, FG-020 Field Capture, FG-019 API, FG-018 auth. |
| Incomplete work | V1-03 / BMR supplier workflow **NOT AUTHORIZED**. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; supplier/Winchester POC. |
| Database and migration status | Repository head = live current **`a5b6c7d8e9f0`**. FG-027 migration **applied live**. No new revision in UAT continuation / close. FG-026 tables **applied live**. One graph head. Live UAT line 7 working unit_cost **260**, `library_unit_cost_reference` **0.0000**, `MANUAL_OVERRIDE`. Costing snapshots **1 SUPERSEDED 750.00** / **2 CURRENT 780.00**. Pricing snapshot **id 6** consume CURRENT. Assembly id 2 **unchanged**. |
| Test status | Dedicated FG-027 **20 passed**. Estimating focused **29**. Pricing focused **52**. FG-026 **20**. Governed A–D bundle **121**. Full suite **652 passed**. Historical dedicated **15** / full **647** remain the pre-repair baseline. Product tests **not** rerun under the UAT/close prompt. |
| Documentation status | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **45%**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Decisions made (this implementation) | 2026-09-08 Joel authorized bounded FG-027 office UAT continuation after the legacy override-provenance repair. Remaining UAT **PASS**. Gate **CLOSED**. V1-02 **COMPLETE**. Readiness **45%**. |
| Decisions pending | V1-03 authorization. Remaining Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 except #2. FG-025 remaining-surface authorization. FG-024. Observation Delete. Ontario counsel answers. |
| Uncommitted work | None after the FG-027 close commit **`c348bcfb41daead674aaf75050fc0a6847a8c0c0`**. |
| Next approved milestone | **STOP.** Return to ChatGPT Architect for **V1-03 authorization**. Do **not** begin V1-03 from this report. Do **not** implement FG-024 or another FG-025 slice. |
| Next candidate milestone | V1-03 / BMR supplier workflow — **NOT AUTHORIZED until a separate prompt**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [v1-completion-register.md](v1-completion-register.md) → [feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) → [adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) → [architecture/fg-027-costing-approval-preflight.md](architecture/fg-027-costing-approval-preflight.md) |
| Approved next Cursor prompt location or summary | **STOP.** Return for V1-03 authorization. Do **not** begin FG-024. Do **not** begin another FG-025 slice. Do **not** begin LEARN. |
| Commit status | Close SHA **`c348bcfb41daead674aaf75050fc0a6847a8c0c0`**. Live current = heads `a5b6c7d8e9f0`. FG-027 **CLOSED / OPERATIONAL FOR UAT**. FG-026 **CLOSED**. FG-025 **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. FG-024 **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Governance baseline | V1 register GOVERNING / 45% / 2 of 11 COMPLETE; FG-027 CLOSED / OPERATIONAL FOR UAT; ADR-044 Accepted; FG-026 CLOSED / OPERATIONAL FOR UAT; live current = heads a5b6c7d8e9f0 |

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

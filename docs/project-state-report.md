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
| Current commit / `origin/main` | FG-026 product SHA **`aa4c71800586e0b8e2a63931bcdc8bc44d87a489`**. Parent V1 register SHA **`73253c46b5fcb54a96345107ac49fe1162063369`**. Docs pin parent **`1a855cc7e020f1f712c6710b30c8e7faca2c4713`**. Slice 5 product SHA remains **`5b497905086554214e85f69afd8101d88f89161c`**. Alembic graph head **`f4a5b6c7d8e9`**. Live current **`f4a5b6c7d8e9`**. |
| Latest completed **coded** milestone on `main` | **FG-026 CLOSED / OPERATIONAL FOR UAT** (live `f4a5b6c7d8e9`; office UAT port **5015**; TakeoffPackage **id 1** / Estimate **id 9**). Product SHA **`aa4c71800586e0b8e2a63931bcdc8bc44d87a489`**. Dedicated **20** / full **632** remain implementation evidence (not rerun this close). **FG-023 CLOSED / OPERATIONAL FOR UAT** remains the last MONITOR close (live `e3f4a5b6c7d8` at that close; office UAT port **5014**; project **id 13** `FG023-UAT-MONITOR`). Close-time: dedicated **35** / focused **149** / full **593**. Historical Slice A close: dedicated **23** / focused **126** / full **581**. Pre-Slice-B focused **137** remains historical. **FG-021 CLOSED** remains the last Field Web product close (gate-at-close live current `d2e3f4a5b6c7`; dedicated FG-021 **20**; focused **148**; full **558**). **FG-020 CLOSED / OPERATIONAL FOR UAT**. **FG-019 CLOSED / OPERATIONAL FOR UAT**. **FG-018 CLOSED / OPERATIONAL FOR UAT**. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **39%**; **1 / 11** COMPLETE (V1-01); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: FG-021 Field Web V1 **CLOSED**. Text / screenshot PNG / Take Photo JPEG / voice Save / network retain-retry / browser-close IndexedDB recovery / HEIC Files/Browse real-device / mixed capture / background-foreground persistence / CSRF recovery / portrait / one-handed / outdoor readability **PASS**. **LANDSCAPE TOLERANCE PASS.** **ORIENTATION / PORTRAIT PASS.** **CURRENT-IPHONE FIELD-USABILITY PASS.** Primary UAT device iPhone 14 / iOS 26.6.1 / Safari. **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED). Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-026 takeoff-to-estimate mapping **live-migrated and office-UAT-verified** (`TakeoffEstimateInsertion` / citations; map UI; atomic insert). Prior coded baseline plus FG-025 Slice 1–5, FG-023 MONITOR, FG-021 Field Web, FG-020 Field Capture, FG-019 API, FG-018 auth. |
| Incomplete work | V1-02 costing **NOT AUTHORIZED**. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; supplier/Winchester POC. |
| Database and migration status | Repository head **`f4a5b6c7d8e9`**. Live current **`f4a5b6c7d8e9`**. FG-026 tables **applied live**. One graph head. Live `project_direct_cost_actuals` exists. Five UAT rows on project **id 13** only. Field **39 / 39**. Package 1 unchanged. Insertion **id 1** / line **id 7** / citations **3**. |
| Test status | Dedicated FG-026 `./venv/bin/python -m pytest -q tests/test_takeoff_estimate_mapping_fg026.py` → **20 passed** (implementation). PLAN takeoff **18 passed**. Estimating/builder **22 passed**. Pricing/labour/material **93 passed**. Governed bundle **172 passed**. Full `./venv/bin/python -m pytest -q` → **632 passed**. Historical full **612** remains the pre-FG-026 baseline. This live-migrate/UAT pass did **not** rerun pytest. |
| Documentation status | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **39%**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Decisions made (this implementation) | 2026-09-08 FG-026 live migrate + bounded office UAT **PASS**. V1-01 scored **COMPLETE** factor **1.00** / contribution **10.0**. Overall readiness **38.85 → 39%**. Gate **CLOSED / OPERATIONAL FOR UAT**. |
| Decisions pending | V1-02 authorization. Seven Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13. FG-025 remaining-surface authorization. FG-024. Observation Delete. Ontario counsel answers. |
| Uncommitted work | None after this FG-026 live-migrate/UAT docs commit. |
| Next approved milestone | **STOP.** Do **not** begin V1-02. Do **not** implement FG-024 or another FG-025 slice. |
| Next candidate milestone | V1-02 — **NOT AUTHORIZED until a separate prompt**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [v1-completion-register.md](v1-completion-register.md) → [current-state.md](current-state.md) → [feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) |
| Approved next Cursor prompt location or summary | **STOP.** Do **not** begin V1-02. Do **not** begin FG-024. Do **not** begin another FG-025 slice. Do **not** begin LEARN. |
| Commit status | FG-026 product SHA **`aa4c71800586e0b8e2a63931bcdc8bc44d87a489`**. Parent V1 register SHA **`73253c46b5fcb54a96345107ac49fe1162063369`**. Live current `f4a5b6c7d8e9`. Graph head `f4a5b6c7d8e9`. FG-026 **CLOSED / OPERATIONAL FOR UAT**. FG-023 **CLOSED**. FG-025 **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. FG-024 **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Governance baseline | V1 register GOVERNING / 39% / 1 of 11 COMPLETE; FG-026 CLOSED / OPERATIONAL FOR UAT; FG-023 CLOSED; FG-025 SLICE 1–5 IMPLEMENTED / NOT CLOSED; FG-024 FUTURE / NOT IMPLEMENTATION-AUTHORIZED; live current = heads f4a5b6c7d8e9 |

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

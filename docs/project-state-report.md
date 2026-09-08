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
| Current commit / `origin/main` | FG-026 implementation (this commit). Parent V1 register SHA **`73253c46b5fcb54a96345107ac49fe1162063369`**. Slice 5 product SHA remains **`5b497905086554214e85f69afd8101d88f89161c`**. Alembic graph head **`f4a5b6c7d8e9`**. Live current **`e3f4a5b6c7d8`**. |
| Latest completed **coded** milestone on `main` | **FG-023 CLOSED / OPERATIONAL FOR UAT** (live `e3f4a5b6c7d8`; office UAT port **5014**; project **id 13** `FG023-UAT-MONITOR`). Close-time: dedicated **35** / focused **149** / full **593**. Historical Slice A close: dedicated **23** / focused **126** / full **581**. Pre-Slice-B focused **137** remains historical. **FG-021 CLOSED** remains the last Field Web product close (gate-at-close live current `d2e3f4a5b6c7`; dedicated FG-021 **20**; focused **148**; full **558**). **FG-020 CLOSED / OPERATIONAL FOR UAT**. **FG-019 CLOSED / OPERATIONAL FOR UAT**. **FG-018 CLOSED / OPERATIONAL FOR UAT**. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **34%**; **0 / 11** COMPLETE; BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT RUN / NOT CLOSED**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: FG-021 Field Web V1 **CLOSED**. Text / screenshot PNG / Take Photo JPEG / voice Save / network retain-retry / browser-close IndexedDB recovery / HEIC Files/Browse real-device / mixed capture / background-foreground persistence / CSRF recovery / portrait / one-handed / outdoor readability **PASS**. **LANDSCAPE TOLERANCE PASS.** **ORIENTATION / PORTRAIT PASS.** **CURRENT-IPHONE FIELD-USABILITY PASS.** Primary UAT device iPhone 14 / iOS 26.6.1 / Safari. **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED). Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT RUN**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-026 takeoff-to-estimate mapping in Git (`TakeoffEstimateInsertion` / citations; map UI; atomic insert). Prior coded baseline plus FG-025 Slice 1–5, FG-023 MONITOR, FG-021 Field Web, FG-020 Field Capture, FG-019 API, FG-018 auth. |
| Incomplete work | FG-026 live migrate + UAT **NOT RUN**. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; supplier/Winchester POC. |
| Database and migration status | Repository head **`f4a5b6c7d8e9`**. Live current **`e3f4a5b6c7d8`**. FG-026 tables **not** applied live. One graph head. Live `project_direct_cost_actuals` exists. Five UAT rows on project **id 13** only. Field **39 / 39**. This package wrote **no** live DB rows. |
| Test status | Dedicated FG-026 `./venv/bin/python -m pytest -q tests/test_takeoff_estimate_mapping_fg026.py` → **20 passed**. PLAN takeoff **18 passed**. Estimating/builder **22 passed**. Pricing/labour/material **93 passed**. Governed bundle **172 passed**. Full `./venv/bin/python -m pytest -q` → **632 passed**. Historical full **612** remains the pre-FG-026 baseline. |
| Documentation status | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **34%**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT RUN / NOT CLOSED**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Decisions made (this implementation) | 2026-09-08 FG-026 product implementation in Git. V1-01 scored PARTIAL factor **0.55** (not COMPLETE: live migrate/UAT remain). Overall readiness **34%**. No live DB writes. UAT **NOT RUN**. |
| Decisions pending | FG-026 live migrate + bounded UAT authorization. Seven Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13. FG-025 remaining-surface authorization. FG-024. Observation Delete. Ontario counsel answers. |
| Uncommitted work | None after this FG-026 implementation commit. |
| Next approved milestone | **STOP.** Separate prompt required for live `flask db upgrade` to `f4a5b6c7d8e9` and bounded project-3 UAT. Do **not** implement FG-024 or another FG-025 slice. |
| Next candidate milestone | FG-026 live migrate + UAT — **NOT AUTHORIZED until a separate prompt**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [v1-completion-register.md](v1-completion-register.md) → [current-state.md](current-state.md) → [feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) |
| Approved next Cursor prompt location or summary | **STOP.** Do **not** live-migrate FG-026. Do **not** create project-3 UAT Draft/Assembly until a separate prompt. Do **not** begin FG-024. Do **not** begin another FG-025 slice. Do **not** begin LEARN. |
| Commit status | FG-026 implementation (this commit). Parent V1 register SHA **`73253c46b5fcb54a96345107ac49fe1162063369`**. Live current `e3f4a5b6c7d8`. Graph head `f4a5b6c7d8e9`. FG-026 **IMPLEMENTED / NOT LIVE-MIGRATED / UAT NOT RUN**. FG-023 **CLOSED**. FG-025 **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. FG-024 **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Governance baseline | V1 register GOVERNING / 34% / 0 of 11 COMPLETE; FG-026 IMPLEMENTED IN GIT / NOT LIVE-MIGRATED; FG-023 CLOSED; FG-025 SLICE 1–5 IMPLEMENTED / NOT CLOSED; FG-024 FUTURE / NOT IMPLEMENTATION-AUTHORIZED; live current e3f4a5b6c7d8; repo head f4a5b6c7d8e9 |

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

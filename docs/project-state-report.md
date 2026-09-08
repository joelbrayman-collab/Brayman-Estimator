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
| Current commit / `origin/main` | Slice 3 product SHA **`071f5f923515c6405298bf96b0af249a20f81358`** (`feat: continue FG-025 contractor-facing PRICE language`). At Slice 3 close, `HEAD` = `origin/main` = that product SHA. Parent Slice 2 **`1aa54f51dcd2447ce6934dddbf5305c81016a824`**. A later **docs-only** post-close reconciliation commit (this update) is **not** the Slice 3 product SHA. |
| Latest completed **coded** milestone on `main` | **FG-023 CLOSED / OPERATIONAL FOR UAT** (live `e3f4a5b6c7d8`; office UAT port **5014**; project **id 13** `FG023-UAT-MONITOR`). Close-time: dedicated **35** / focused **149** / full **593**. Historical Slice A close: dedicated **23** / focused **126** / full **581**. Pre-Slice-B focused **137** remains historical. **FG-021 CLOSED** remains the last Field Web product close (gate-at-close live current `d2e3f4a5b6c7`; dedicated FG-021 **20**; focused **148**; full **558**). **FG-020 CLOSED / OPERATIONAL FOR UAT**. **FG-019 CLOSED / OPERATIONAL FOR UAT**. **FG-018 CLOSED / OPERATIONAL FOR UAT**. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**. Item 13 **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**. Parallel: [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Future recorded: [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Item 11 **COMPLETE**. Item 10 **COMPLETE**. |
| Product status | Operational on `main`: FG-021 Field Web V1 **CLOSED**. Text / screenshot PNG / Take Photo JPEG / voice Save / network retain-retry / browser-close IndexedDB recovery / HEIC Files/Browse real-device / mixed capture / background-foreground persistence / CSRF recovery / portrait / one-handed / outdoor readability **PASS**. **LANDSCAPE TOLERANCE PASS.** **ORIENTATION / PORTRAIT PASS.** **CURRENT-IPHONE FIELD-USABILITY PASS.** Primary UAT device iPhone 14 / iOS 26.6.1 / Safari. **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED). Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1, SLICE 2, AND SLICE 3 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-025 Slice 1 Hub MONITOR mapping, Slice 2 Project Hub PLAN/commercial/history copy, and Slice 3 office PRICE specialist mapping (`app/presentation/contractor_copy.py`). FG-023 Slice A BUILD `ProjectDirectCostActual` + MONITOR `assemble_monitor_v1` + Slice B Hub `#hub-monitor` and BUILD actuals POSTs, live-migrated and office-UAT-verified on synthetic `FG023-UAT-MONITOR`. FG-021 `/field` Today + Project confirm + Capture; IndexedDB pending queue; idempotent Event/Original POST; Field display GET. FG-020 Field Capture Events / Originals / Derived Candidates; office Field Observations; bounded `/api/v1` BUILD POSTs; HEIC/HEIF → JPEG Compatible Renditions. FG-019 GET `/api/v1` over FG-018 session. |
| Incomplete work | FG-025 remaining surfaces (nav/auth/Settings, Field Web, customer PDF); Observation Delete (**QUEUED / NOT AUTHORIZED**); server-side per-login session revocation / idle timeout (**FUTURE AUTHENTICATION HARDENING / NOT FG-021**); Native Signing **production activation**; Project Closeout; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family; RBAC; org-switcher. |
| Database and migration status | Repository head = live current `e3f4a5b6c7d8`. Applied `d2e3f4a5b6c7` → `e3f4a5b6c7d8` (2026-09-07 Slice C). One graph head. Live `project_direct_cost_actuals` exists. Five UAT rows on project **id 13** only. Field **39 / 39**. Close wrote **no** further actuals. |
| Test status | Slice 3 dedicated FG-025 **13 passed**. PRICE-focused **167 passed**. Governed **303 passed**. Full suite **606 passed**. Close-time dedicated FG-023 **35 passed**. Focused **149 passed**. Historical Slice A close focused **126 passed**. Pre-Slice-B focused **137 passed**. Full suite at FG-023 close **593 passed**. Dedicated FG-021 **20 passed**; prior FG-021 focused bundle **148 passed**; full **558** remains historical at FG-021 close. Dedicated FG-020 **44**. Dedicated FG-019 **34**; dedicated FG-018 **37**. |
| Documentation status | [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / NOT CLOSED / NOT YET PRODUCT-WIDE COMPLETE**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED.** Observation Delete **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Legal Content Gate **empty**. ADR-008 / ADR-010 **Proposed**. |
| Decisions made (this governance pass) | 2026-09-07 FG-025 **Slice 3 AUTHORIZED AND IMPLEMENTED**. Presentation-layer mapping only. Labour office title **Labour rates**. Pricing office title **Pricing**. Internal `TRUE_GROSS_MARGIN` unchanged; display **Gross Margin Pricing**. Internal domain keys unchanged. Frozen Hub metric identities unchanged except Hub PRICE specialist link labels. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. Remaining FG-025 surfaces **NOT AUTHORIZED**. |
| Decisions pending | FG-025 remaining-surface authorization (Slice 4+). “Contract value” vs Current Authorized Pre-Tax Revenue still **G** and frozen. Observation Delete remains **QUEUED / NOT AUTHORIZED**. Ontario counsel answers to [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md). |
| Uncommitted work | None after this FG-025 Slice 3 commit. |
| Next approved milestone | **STOP after Slice 3.** Do **not** start Slice 4. Do **not** implement FG-024. Do **not** implement Observation Delete. Native Signing **production** remains blocked pending counsel. |
| Next candidate milestone | FG-025 Slice 4 nav/auth/Settings copy — **NOT AUTHORIZED until a separate prompt**. Native Signing — **development may proceed under separate governance**; production blocked pending counsel. Observation Delete — **QUEUED / NOT AUTHORIZED**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [current-state.md](current-state.md) → [feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) → [feature-gates/FG-023-monitor-v1-estimated-versus-actual.md](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) |
| Approved next Cursor prompt location or summary | **STOP.** Do **not** begin Slice 4. Do **not** begin FG-024. Do **not** begin LEARN. |
| Commit status | Slice 3 product SHA **`071f5f923515c6405298bf96b0af249a20f81358`**. At Slice 3 close, `HEAD` = `origin/main` = that product SHA. A later **docs-only** post-close reconciliation commit is **not** the Slice 3 product SHA. Live current = heads `e3f4a5b6c7d8`. FG-023 **CLOSED / OPERATIONAL FOR UAT**. FG-025 **SLICE 1, SLICE 2, AND SLICE 3 IMPLEMENTED / NOT CLOSED**. FG-024 **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. FG-021 **CLOSED**. FG-022 **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. |
| Governance baseline | FG-023 CLOSED / OPERATIONAL FOR UAT; MONITOR V1 IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED; FG-025 SLICE 1, SLICE 2, AND SLICE 3 IMPLEMENTED / NOT CLOSED; remaining surfaces NOT AUTHORIZED; live current = heads e3f4a5b6c7d8; dedicated FG-025 13; PRICE-focused 167; governed 303; full 606; FG-021 CLOSED; SESSION-EXPIRY RECOVERY DEFERRED / NOT YET EXERCISED; Observation Delete QUEUED / NON-BLOCKING; FG-022 CLOSED / APPROVED REUSABLE MASTER FAMILY V1; FG-024 FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED |

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

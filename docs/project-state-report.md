# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-06 |

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
| Report date | 2026-09-06 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | Verify `git rev-parse HEAD` and `git rev-parse origin/main` after this FG-023 draft docs commit. |
| Latest completed **coded** milestone on `main` | **FG-021 CLOSED** (IMPLEMENTED / LIVE-MIGRATED / REAL-IPHONE UAT COMPLETE SUBJECT TO THE EXPLICIT SESSION-EXPIRY DEFERRED EXCEPTION; live current = head `d2e3f4a5b6c7`; dedicated FG-021 **20**; focused **148**; full **558**). **FG-020 CLOSED / OPERATIONAL FOR UAT**. **FG-019 CLOSED / OPERATIONAL FOR UAT**. **FG-018 CLOSED / OPERATIONAL FOR UAT**. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **DRAFT FOR JOEL APPROVAL / NOT APPROVED / NOT AUTHORIZED FOR IMPLEMENTATION**. MONITOR V1 recon **COMPLETE**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**. Roadmap item 12 **CLOSED** subject to the explicit SESSION-EXPIRY deferred exception. Parallel: [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Item 11 **COMPLETE**. Item 10 **COMPLETE**. |
| Product status | Operational on `main`: FG-021 Field Web V1 **CLOSED**. Text / screenshot PNG / Take Photo JPEG / voice Save / network retain-retry / browser-close IndexedDB recovery / HEIC Files/Browse real-device / mixed capture / background-foreground persistence / CSRF recovery / portrait / one-handed / outdoor readability **PASS**. **LANDSCAPE TOLERANCE PASS.** **ORIENTATION / PORTRAIT PASS.** **CURRENT-IPHONE FIELD-USABILITY PASS.** Primary UAT device iPhone 14 / iOS 26.6.1 / Safari. **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED). Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-021 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. Approved presentation source custody **CLOSED**. [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-021 `/field` Today + Project confirm + Capture; IndexedDB pending queue; idempotent Event/Original POST; Field display GET. FG-020 Field Capture Events / Originals / Derived Candidates; office Field Observations; bounded `/api/v1` BUILD POSTs; HEIC/HEIF → JPEG Compatible Renditions. FG-019 GET `/api/v1` over FG-018 session. |
| Incomplete work | MONITOR implementation (**NOT AUTHORIZED**; FG-023 draft only); Observation Delete (**QUEUED / NOT AUTHORIZED**); server-side per-login session revocation / idle timeout (**FUTURE AUTHENTICATION HARDENING / NOT FG-021**); Native Signing **production activation**; Project Closeout; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family; RBAC; org-switcher. |
| Database and migration status | Live current = head `d2e3f4a5b6c7`. Applied `c1d2e3f4a5b6` → `d2e3f4a5b6c7`. One graph head. No FG-023 migration. |
| Test status | Dedicated FG-021 **20 passed**; focused (Hub + FG-018 + FG-019 + both FG-020 + FG-021) **148 passed**; full suite **558 passed**. Dedicated FG-020 **44**. Dedicated FG-019 **34**; dedicated FG-018 **37**. Product pytest not re-run for this docs-only governance record. |
| Documentation status | [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **DRAFT FOR JOEL APPROVAL / NOT APPROVED / NOT AUTHORIZED FOR IMPLEMENTATION**. MONITOR V1 recon **COMPLETE**. [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED.** Observation Delete **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Legal Content Gate **empty**. ADR-008 / ADR-010 **Proposed**. |
| Decisions made (this governance pass) | FG-023 drafted. Office Direct Cost actuals **included** in the same gate (BUILD `ProjectDirectCostActual`; incremental; no MONITOR snapshot table; Hub membership may enter actuals). No new ADR. No product code. Residual roadmap “Do not start Item 13” current-authority leftover repaired. Current ChatGPT development chat title recorded as **BRAYMAN - CalibAi 5 Sep 2026**. |
| Decisions pending | Joel approval of FG-023. Observation Delete remains **QUEUED / NOT AUTHORIZED**. Server-side per-login session revocation / idle timeout remains **FUTURE AUTHENTICATION HARDENING**. Ontario counsel answers to [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md). |
| Uncommitted work | None after this FG-023 draft docs commit. |
| Next approved milestone | Joel review of FG-023. Do **not** implement MONITOR. Do **not** implement Observation Delete. Do **not** implement session revocation / idle timeout. Native Signing **production** remains blocked pending counsel. Do **not** implement Closeout. |
| Next candidate milestone | FG-023 approval then a separate implementation prompt — **not this pass**. Native Signing — **development may proceed under separate governance**; production blocked pending counsel. Observation Delete — **QUEUED / NOT AUTHORIZED**. Project Closeout — **FUTURE / NOT AUTHORIZED**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [current-state.md](current-state.md) → [feature-gates/FG-023-monitor-v1-estimated-versus-actual.md](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) → [architecture/monitor-v1-implementation-reconnaissance.md](architecture/monitor-v1-implementation-reconnaissance.md) → [adr/ADR-021-monitor-commercial-baseline.md](adr/ADR-021-monitor-commercial-baseline.md) |
| Approved next Cursor prompt location or summary | **STOP for Joel review of FG-023.** Do **not** implement MONITOR. Do **not** implement Observation Delete. Do **not** implement session revocation / idle timeout. |
| Commit status | Verify `git rev-parse HEAD` after this FG-023 draft docs commit. Live current = head `d2e3f4a5b6c7`. FG-023 **DRAFT FOR JOEL APPROVAL**. FG-021 **CLOSED**. FG-022 **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. |
| Governance baseline | FG-023 DRAFT FOR JOEL APPROVAL / NOT APPROVED / NOT AUTHORIZED FOR IMPLEMENTATION; office actuals in draft gate; no migration; MONITOR V1 recon COMPLETE; FG-021 CLOSED; SESSION-EXPIRY RECOVERY DEFERRED / NOT YET EXERCISED; OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL; Observation Delete QUEUED / NON-BLOCKING; FG-022 CLOSED / APPROVED REUSABLE MASTER FAMILY V1; live current = head d2e3f4a5b6c7; full suite 558; dedicated FG-021 20; focused 148 |

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

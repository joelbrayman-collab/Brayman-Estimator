# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-07 |

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
| Report date | 2026-09-07 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | Confirm `HEAD` = `origin/main` after this Slice C docs commit. Last product-changing **`7dd4d82c927ec2c38a0562e7e1cdedbccabb6662`**. |
| Latest completed **coded** milestone on `main` | **FG-023 Slice C MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS** (live `e3f4a5b6c7d8`; office UAT port **5014**; project **id 13** `FG023-UAT-MONITOR`). Historical Slice B close: dedicated **35** / focused **149** / full **593** (not rerun this pass). Historical Slice A close: dedicated **23** / focused **126** / full **581**. Pre-Slice-B focused **137** remains historical. **FG-021 CLOSED** remains the last Field Web product close (gate-at-close live current `d2e3f4a5b6c7`; dedicated FG-021 **20**; focused **148**; full **558**). **FG-020 CLOSED / OPERATIONAL FOR UAT**. **FG-019 CLOSED / OPERATIONAL FOR UAT**. **FG-018 CLOSED / OPERATIONAL FOR UAT**. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **APPROVED / OPEN / NOT CLOSED**. Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**. Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / NOT YET CLOSED**. Preflight [architecture/fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md) **COMPLETE**. MONITOR V1 recon **COMPLETE**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**. Roadmap item 12 **CLOSED** subject to the explicit SESSION-EXPIRY deferred exception. Item 13 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / NOT CLOSED**. Parallel: [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Future recorded: [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Item 11 **COMPLETE**. Item 10 **COMPLETE**. |
| Product status | Operational on `main`: FG-021 Field Web V1 **CLOSED**. Text / screenshot PNG / Take Photo JPEG / voice Save / network retain-retry / browser-close IndexedDB recovery / HEIC Files/Browse real-device / mixed capture / background-foreground persistence / CSRF recovery / portrait / one-handed / outdoor readability **PASS**. **LANDSCAPE TOLERANCE PASS.** **ORIENTATION / PORTRAIT PASS.** **CURRENT-IPHONE FIELD-USABILITY PASS.** Primary UAT device iPhone 14 / iOS 26.6.1 / Safari. **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED). Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-021 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. Approved presentation source custody **CLOSED**. [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-023 Slice A BUILD `ProjectDirectCostActual` + MONITOR `assemble_monitor_v1` + Slice B Hub `#hub-monitor` and BUILD actuals POSTs, live-migrated and office-UAT-verified on synthetic `FG023-UAT-MONITOR`. FG-021 `/field` Today + Project confirm + Capture; IndexedDB pending queue; idempotent Event/Original POST; Field display GET. FG-020 Field Capture Events / Originals / Derived Candidates; office Field Observations; bounded `/api/v1` BUILD POSTs; HEIC/HEIF → JPEG Compatible Renditions. FG-019 GET `/api/v1` over FG-018 session. |
| Incomplete work | FG-023 **close** (migrate + UAT complete; close not authorized); Observation Delete (**QUEUED / NOT AUTHORIZED**); server-side per-login session revocation / idle timeout (**FUTURE AUTHENTICATION HARDENING / NOT FG-021**); Native Signing **production activation**; Project Closeout; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family; RBAC; org-switcher. |
| Database and migration status | Repository head = live current `e3f4a5b6c7d8`. Applied `d2e3f4a5b6c7` → `e3f4a5b6c7d8` (2026-09-07 Slice C). One graph head. Live `project_direct_cost_actuals` exists. Five UAT rows on project **id 13** only. Field **39 / 39**. |
| Test status | Dedicated FG-023 **35 passed**. Focused **149 passed**. Historical Slice A close focused **126 passed**. Pre-Slice-B focused **137 passed**. Full suite **593 passed**. Tests **not rerun** this Slice C pass. Dedicated FG-021 **20 passed**; prior FG-021 focused bundle **148 passed**; full **558** remains historical at FG-021 close. Dedicated FG-020 **44**. Dedicated FG-019 **34**; dedicated FG-018 **37**. |
| Documentation status | [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **APPROVED / OPEN / NOT CLOSED**. Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**. Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / NOT YET CLOSED**. Preflight [architecture/fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md) **COMPLETE**. MONITOR V1 recon **COMPLETE**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED.** Observation Delete **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Legal Content Gate **empty**. ADR-008 / ADR-010 **Proposed**. |
| Decisions made (this governance pass) | 2026-09-07 FG-023 Slice C executed: live migrate `e3f4a5b6c7d8` **PASS**; office Hub UAT **PASS** on `FG023-UAT-MONITOR` (project 13, port 5014); four-class create **PASS**; `0.00` supersession **PASS**; independent arithmetic **PASS**. FG-023 remains **OPEN**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. No product-code change. No new migration. |
| Decisions pending | FG-023 **close authorization**. Observation Delete remains **QUEUED / NOT AUTHORIZED**. Server-side per-login session revocation / idle timeout remains **FUTURE AUTHENTICATION HARDENING**. Ontario counsel answers to [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md). |
| Uncommitted work | None after this Slice C docs commit. |
| Next approved milestone | FG-023 **CLOSE AUTHORIZATION** (separate ChatGPT prompt). Do **not** close FG-023 from this Slice C record. Do **not** implement FG-024. Do **not** implement Observation Delete. Do **not** implement session revocation / idle timeout. Native Signing **production** remains blocked pending counsel. Do **not** implement Closeout. |
| Next candidate milestone | FG-023 close — **not this pass**. Native Signing — **development may proceed under separate governance**; production blocked pending counsel. Observation Delete — **QUEUED / NOT AUTHORIZED**. Project Closeout — **FUTURE / NOT AUTHORIZED**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [current-state.md](current-state.md) → [feature-gates/FG-023-monitor-v1-estimated-versus-actual.md](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) → [architecture/fg-023-monitor-v1-implementation-preflight.md](architecture/fg-023-monitor-v1-implementation-preflight.md) → [architecture/monitor-v1-implementation-reconnaissance.md](architecture/monitor-v1-implementation-reconnaissance.md) → [adr/ADR-021-monitor-commercial-baseline.md](adr/ADR-021-monitor-commercial-baseline.md) |
| Approved next Cursor prompt location or summary | **FG-023 CLOSE AUTHORIZATION** — separate ChatGPT prompt after this Slice C PASS report. Do **not** begin FG-024. |
| Commit status | Confirm `HEAD` = `origin/main` after this Slice C docs commit. Last product-changing `7dd4d82c927ec2c38a0562e7e1cdedbccabb6662`. Live current = heads `e3f4a5b6c7d8`. FG-023 **APPROVED / OPEN / NOT CLOSED**. Slice A + Slice B **IMPLEMENTED / LIVE-MIGRATED**. Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**. FG-024 **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. FG-021 **CLOSED**. FG-022 **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. |
| Governance baseline | FG-023 APPROVED / OPEN / NOT CLOSED; Slice A + Slice B IMPLEMENTED / LIVE-MIGRATED; Slice C MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS; MONITOR V1 IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / NOT YET CLOSED; live current = heads e3f4a5b6c7d8; dedicated FG-023 35; focused 149; historical Slice A focused 126; pre-Slice-B focused 137; full 593 (not rerun this pass); FG-021 CLOSED; SESSION-EXPIRY RECOVERY DEFERRED / NOT YET EXERCISED; Observation Delete QUEUED / NON-BLOCKING; FG-022 CLOSED / APPROVED REUSABLE MASTER FAMILY V1; FG-024 FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED |

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

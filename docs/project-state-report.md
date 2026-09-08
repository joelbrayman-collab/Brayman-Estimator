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
| Current commit / `origin/main` | Slice 5 product SHA remains **`5b497905086554214e85f69afd8101d88f89161c`**. FG-026 docs SHA **`95b396602eb578f0399e7785d7e066b6dd0056f8`**. This V1 register docs commit is **not** a product SHA. Live Alembic current = repository head **`e3f4a5b6c7d8`**. |
| Latest completed **coded** milestone on `main` | **FG-023 CLOSED / OPERATIONAL FOR UAT** (live `e3f4a5b6c7d8`; office UAT port **5014**; project **id 13** `FG023-UAT-MONITOR`). Close-time: dedicated **35** / focused **149** / full **593**. Historical Slice A close: dedicated **23** / focused **126** / full **581**. Pre-Slice-B focused **137** remains historical. **FG-021 CLOSED** remains the last Field Web product close (gate-at-close live current `d2e3f4a5b6c7`; dedicated FG-021 **20**; focused **148**; full **558**). **FG-020 CLOSED / OPERATIONAL FOR UAT**. **FG-019 CLOSED / OPERATIONAL FOR UAT**. **FG-018 CLOSED / OPERATIONAL FOR UAT**. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **30%**; **0 / 11** COMPLETE; BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**. Item 13 **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / SLICE 4 IMPLEMENTED / SLICE 5 IMPLEMENTED / NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **FUTURE / RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**. Parallel: [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Future recorded: [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Item 11 **COMPLETE**. Item 10 **COMPLETE**. |
| Product status | Operational on `main`: FG-021 Field Web V1 **CLOSED**. Text / screenshot PNG / Take Photo JPEG / voice Save / network retain-retry / browser-close IndexedDB recovery / HEIC Files/Browse real-device / mixed capture / background-foreground persistence / CSRF recovery / portrait / one-handed / outdoor readability **PASS**. **LANDSCAPE TOLERANCE PASS.** **ORIENTATION / PORTRAIT PASS.** **CURRENT-IPHONE FIELD-USABILITY PASS.** Primary UAT device iPhone 14 / iOS 26.6.1 / Safari. **OLDER SUPPORTED IPHONE / SAFARI WAIVED AS NOT PRACTICAL.** **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED** (NOT PASS / NOT FAIL / NOT N/A / NOT WAIVED). Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1, SLICE 2, SLICE 3, SLICE 4, AND SLICE 5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **FUTURE / RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-025 Slice 1 Hub MONITOR mapping, Slice 2 Project Hub PLAN/commercial/history copy, Slice 3 office PRICE specialist mapping, Slice 4 shared office shell mapping, and Slice 5 Field Web mapping (`app/presentation/contractor_copy.py`). FG-023 Slice A BUILD `ProjectDirectCostActual` + MONITOR `assemble_monitor_v1` + Slice B Hub `#hub-monitor` and BUILD actuals POSTs, live-migrated and office-UAT-verified on synthetic `FG023-UAT-MONITOR`. FG-021 `/field` Today + Project confirm + Capture; IndexedDB pending queue; idempotent Event/Original POST; Field display GET. FG-020 Field Capture Events / Originals / Derived Candidates; office Field Observations; bounded `/api/v1` BUILD POSTs; HEIC/HEIF → JPEG Compatible Renditions. FG-019 GET `/api/v1` over FG-018 session. |
| Incomplete work | FG-025 remaining surfaces **NOT AUTHORIZED** (not a must-rewrite list). Unauthorized candidate surfaces: customer Proposal/PDF terminology; Historical Evidence nav and historical specialist screens; standalone Permit screens; Hub PRICE table leftover `TRUE_GROSS_MARGIN`; final product-wide terminology sweep. **REVIEW / DECISION REQUIRED** (not implied must-change): Cost Items nav label; “Contract value” terminology; Dashboard `page_title` still Dashboard; Office sign in / Brayman Construction Platform titles retained; `GENERIC_LOGIN_FAILURE` retained for security; Brand Profile saved. flash retained; disabled Settings (coming soon) frozen by FG-017. Observation Delete (**QUEUED / NOT AUTHORIZED**); server-side per-login session revocation / idle timeout (**FUTURE AUTHENTICATION HARDENING / NOT FG-021**); Native Signing **production activation**; Project Closeout; [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) (**RECORDED / NOT IMPLEMENTATION-AUTHORIZED**); four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family; RBAC; org-switcher. |
| Database and migration status | Repository head = live current `e3f4a5b6c7d8`. Applied `d2e3f4a5b6c7` → `e3f4a5b6c7d8` (2026-09-07 Slice C). One graph head. Live `project_direct_cost_actuals` exists. Five UAT rows on project **id 13** only. Field **39 / 39**. Close wrote **no** further actuals. |
| Test status | **PRODUCT TESTS NOT RERUN — V1 GOVERNANCE / GAP RECONCILIATION ONLY.** Historical Slice 5 evidence remains dedicated FG-025 **19 passed**. Field-focused **83 passed**. Prompt governed list **190 passed**. Full suite **612 passed**. |
| Documentation status | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **30%**. [FG-023](feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **IMPLEMENTATION PREFLIGHT COMPLETE / SLICE 1 IMPLEMENTED / SLICE 2 IMPLEMENTED / SLICE 3 IMPLEMENTED / SLICE 4 IMPLEMENTED / SLICE 5 IMPLEMENTED / NOT CLOSED / NOT YET PRODUCT-WIDE COMPLETE**. [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **FUTURE / RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **CLOSED**. **SESSION-EXPIRY RECOVERY: DEFERRED / NOT YET EXERCISED.** Observation Delete **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Legal Content Gate **empty**. ADR-008 / ADR-010 **Proposed**. |
| Decisions made (this governance pass) | 2026-09-08 CalibAi V1 completion register **RECORDED**. Initial readiness **30%**. FG-026 remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. Remaining FG-025 surfaces **NOT AUTHORIZED**. FG-023 remains **CLOSED**. FG-024 remains **FUTURE / NOT IMPLEMENTATION-AUTHORIZED**. |
| Decisions pending | Seven Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 (QuickBooks A vs B; exception-based costing; FG-024 Slice D; customer PDF language; Closeout; extra jurisdictions; Native Signing development timing). FG-026 implementation authorization. FG-025 remaining-surface authorization. Observation Delete remains **QUEUED**. Ontario counsel answers. |
| Uncommitted work | None after this 2026-09-08 V1 register docs commit. |
| Next approved milestone | **STOP.** Do **not** implement FG-026, FG-024, or another FG-025 slice from this recording. Native Signing **production** remains blocked pending counsel. |
| Next candidate milestone | V1-01 (FG-026 implementation) and V1-06 (FG-024) — **NOT AUTHORIZED until separate prompts**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [v1-completion-register.md](v1-completion-register.md) → [current-state.md](current-state.md) → [feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) |
| Approved next Cursor prompt location or summary | **STOP.** Do **not** implement FG-026. Do **not** begin FG-024. Do **not** begin another FG-025 slice. Do **not** begin LEARN. |
| Commit status | Slice 5 product SHA remains **`5b497905086554214e85f69afd8101d88f89161c`**. FG-026 docs SHA **`95b396602eb578f0399e7785d7e066b6dd0056f8`**. This V1 register docs commit is **not** a product SHA. Live current = heads `e3f4a5b6c7d8`. FG-023 **CLOSED**. FG-025 **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. FG-026 **RECORDED / PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED**. FG-024 **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Governance baseline | V1 register GOVERNING / 30% / 0 of 11 COMPLETE; FG-023 CLOSED; FG-025 SLICE 1–5 IMPLEMENTED / NOT CLOSED; FG-026 RECORDED / NOT IMPLEMENTATION-AUTHORIZED; FG-024 FUTURE / NOT IMPLEMENTATION-AUTHORIZED; live current = heads e3f4a5b6c7d8 |

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

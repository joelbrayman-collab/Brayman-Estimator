# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-05 |

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
| Report date | 2026-09-05 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | Verify `git rev-parse HEAD` and `git rev-parse origin/main` after this FG-021 mixed-capture PASS docs commit. |
| Latest completed **coded** milestone on `main` | **FG-021 IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** (gate **NOT CLOSED**; live current = head `d2e3f4a5b6c7`; dedicated FG-021 **19**; focused **147**; full **557**). **FG-020 CLOSED / OPERATIONAL FOR UAT**. **FG-019 CLOSED / OPERATIONAL FOR UAT**. **FG-018 CLOSED / OPERATIONAL FOR UAT**. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** (gate **NOT CLOSED**). Roadmap item 12 **IMPLEMENTED / LIVE-MIGRATED / UAT OPEN** (first unfinished numbered item). Parallel: [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. Item 11 **COMPLETE**. Item 10 **COMPLETE**. |
| Product status | Operational on `main`: FG-021 Field Web V1 **OPEN**. Text / screenshot PNG / Take Photo JPEG / voice Save / network retain-retry / browser-close IndexedDB recovery / HEIC Files/Browse real-device / mixed capture / desktop continuity **PASS**. Observation Delete remains **OPEN**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-020 **CLOSED / OPERATIONAL FOR UAT**. [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. Approved presentation source custody **CLOSED**. [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Family 05 remains **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-021 `/field` Today + Project confirm + Capture; IndexedDB pending queue; idempotent Event/Original POST; Field display GET. FG-020 Field Capture Events / Originals / Derived Candidates; office Field Observations; bounded `/api/v1` BUILD POSTs; HEIC/HEIF → JPEG Compatible Renditions. FG-019 GET `/api/v1` over FG-018 session. |
| Incomplete work | Remaining FG-021 real iPhone UAT (background/foreground, session-expiry, CSRF recovery, older iPhone smoke, orientation/readability); Native Signing **production activation**; Project Closeout; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; MONITOR implementation; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family; RBAC; org-switcher. |
| Database and migration status | Live current = head `d2e3f4a5b6c7`. Applied `c1d2e3f4a5b6` → `d2e3f4a5b6c7`. One graph head. |
| Test status | Dedicated FG-021 **19 passed**; focused (Hub + FG-018 + FG-019 + both FG-020 + FG-021) **147 passed**; full suite **557 passed**. Dedicated FG-020 **44**. Dedicated FG-019 **34**; dedicated FG-018 **37**. Product pytest not re-run for this docs-only UAT record. |
| Documentation status | [FG-022](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. **MIXED CAPTURE PASS** (Event **35**). **HEIC REAL-DEVICE PASS** (Event **34** / Original **32**). Browser-close IndexedDB recovery **PASS** (Event **32** / Original **30**). Approved presentation source custody **CLOSED**. Native Signing recon **COMPLETE**; counsel spec **PREPARED** — **NOT LEGAL APPROVAL**. Development may proceed under separate governance; production activation blocked pending counsel. Legal Content Gate **empty**. ADR-008 / ADR-010 **Proposed**. |
| Decisions made (this governance pass) | FG-021 mixed-capture real-iPhone UAT **PASS**. Event **35**, Project **11**, Originals **33** text / **34** audio / **35** JPEG. Kind set `{text, image, audio}`. Live **35** / **35**. Field Today and desktop Hub **PASS**. Gate **NOT CLOSED**. No product/test/schema/migration/ADR/FG-022 change. iPhone test not repeated. |
| Decisions pending | Remaining FG-021 real-iPhone UAT (background/foreground next). Observation Delete remains **QUEUED / NOT AUTHORIZED**. Ontario counsel answers to [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md). Archive package format. Project Closeout Feature Gate not created. |
| Uncommitted work | None after this FG-021 mixed-capture PASS docs commit. |
| Next approved milestone | **STOP.** Do **not** close FG-021. Do **not** repeat mixed capture. Mixed capture is **PASS**. Native Signing **production** remains blocked pending counsel. Do **not** implement Closeout or Observation Delete. |
| Next candidate milestone | Remaining FG-021 real-iPhone UAT (background/foreground persistence). Native Signing — **development may proceed under separate governance**; production blocked pending counsel. Project Closeout — **FUTURE / NOT AUTHORIZED**. Item 13 MONITOR — **FUTURE / NOT AUTHORIZED**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [current-state.md](current-state.md) → [feature-gates/FG-021-field-web-v1-today-and-capture.md](feature-gates/FG-021-field-web-v1-today-and-capture.md) → [feature-gates/FG-022-reusable-approved-document-template-family-v1.md](feature-gates/FG-022-reusable-approved-document-template-family-v1.md) |
| Approved next Cursor prompt location or summary | **STOP.** Do **not** close FG-021. Do **not** repeat mixed capture. Mixed capture is **PASS**. Do **not** implement Closeout or Observation Delete. |
| Commit status | Verify `git rev-parse HEAD` after this FG-021 mixed-capture PASS docs commit. Live current = head `d2e3f4a5b6c7`. FG-021 **OPEN**. FG-022 **CLOSED / APPROVED REUSABLE MASTER FAMILY V1**. Approved presentation source custody **CLOSED**. |
| Governance baseline | FG-021 IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN; MIXED CAPTURE PASS (Event 35); HEIC REAL-DEVICE PASS (Event 34 / Original 32); browser-close IndexedDB recovery PASS (Event 32 / Original 30); Observation Delete remains OPEN; FG-022 CLOSED / APPROVED REUSABLE MASTER FAMILY V1; Family 05 COMMERCIAL_DRAFT / NOT LEGALLY APPROVED; Legal Content Gate empty; live current = head d2e3f4a5b6c7; full suite 557; dedicated FG-021 19; focused 147; presentation source custody CLOSED; Native Signing development may proceed separately / production blocked pending counsel; ADR-043 Accepted; Closeout FUTURE |

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

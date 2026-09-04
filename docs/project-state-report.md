# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-04 |

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
| Report date | 2026-09-04 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | Verify `git rev-parse HEAD` and `git rev-parse origin/main` after this reconciliation commit. Parent at start of this pass: `97f35fe757f0be99af9140693d2e12924659ec46` (*docs: close approved document template custody gap*). |
| Latest completed **coded** milestone on `main` | **FG-021 IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** (gate **NOT CLOSED**; live current = head `d2e3f4a5b6c7`; dedicated FG-021 **19**; focused **147**; full **557**). **FG-020 CLOSED / OPERATIONAL FOR UAT**. **FG-019 CLOSED / OPERATIONAL FOR UAT**. **FG-018 CLOSED / OPERATIONAL FOR UAT**. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** (gate **NOT CLOSED**). Roadmap item 12 **IMPLEMENTED / LIVE-MIGRATED / UAT OPEN** (first unfinished numbered item). [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. Item 11 **COMPLETE**. Item 10 **COMPLETE**. |
| Product status | Operational on `main`: FG-021 Field Web V1 **OPEN**. Text / screenshot PNG / Take Photo JPEG / voice Save / network retain-retry / desktop continuity **PASS**. HEIC real-device, mixed capture, IndexedDB browser-close recovery, and Observation Delete remain **OPEN**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-020 **CLOSED / OPERATIONAL FOR UAT**. [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. Approved presentation source custody **CLOSED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-021 `/field` Today + Project confirm + Capture; IndexedDB pending queue; idempotent Event/Original POST; Field display GET. FG-020 Field Capture Events / Originals / Derived Candidates; office Field Observations; bounded `/api/v1` BUILD POSTs; HEIC/HEIF → JPEG Compatible Renditions. FG-019 GET `/api/v1` over FG-018 session. |
| Incomplete work | Remaining FG-021 real iPhone UAT; Native Signing **production activation**; Project Closeout; reusable presentation-template extraction; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; MONITOR implementation; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family; RBAC; org-switcher. |
| Database and migration status | Live current = head `d2e3f4a5b6c7`. Applied `c1d2e3f4a5b6` → `d2e3f4a5b6c7`. One graph head. |
| Test status | Dedicated FG-021 **19 passed**; focused (Hub + FG-018 + FG-019 + both FG-020 + FG-021) **147 passed**; full suite **557 passed**. Dedicated FG-020 **44**. Dedicated FG-019 **34**; dedicated FG-018 **37**. |
| Documentation status | [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. Approved presentation source custody **CLOSED**. Native Signing recon **COMPLETE**; counsel spec **PREPARED** — **NOT LEGAL APPROVAL**. Development may proceed under separate governance; production activation blocked pending counsel. Legal Content Gate **empty**. ADR-008 / ADR-010 **Proposed**. |
| Decisions made (this governance pass) | Current-state documentation reconciliation only. No product code. Custody closure already committed at `97f35fe`. Gate **NOT CLOSED**. |
| Decisions pending | Joel/ChatGPT chooses remaining FG-021 real-iPhone closure UAT **or** separately governed reusable-template extraction. Ontario counsel answers to [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md). Archive package format. Project Closeout Feature Gate not created. |
| Uncommitted work | None after this documentation reconciliation commit. |
| Next approved milestone | **STOP** for Joel/ChatGPT review. Do **not** close FG-021. Native Signing **production** remains blocked pending counsel. Do **not** implement Closeout, Observation Delete, or template extraction from this pass. |
| Next candidate milestone | Remaining FG-021 real-iPhone UAT **or** reusable-template extraction — **not chosen here**. Native Signing — **development may proceed under separate governance**; production blocked pending counsel. Project Closeout — **FUTURE / NOT AUTHORIZED**. Item 13 MONITOR — **FUTURE / NOT AUTHORIZED**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [current-state.md](current-state.md) → [feature-gates/FG-021-field-web-v1-today-and-capture.md](feature-gates/FG-021-field-web-v1-today-and-capture.md) → [architecture/approved-document-presentation-reference-baseline.md](architecture/approved-document-presentation-reference-baseline.md) → [adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) |
| Approved next Cursor prompt location or summary | Joel/ChatGPT review before either remaining FG-021 UAT or reusable-template extraction. Do **not** implement Closeout or Contract templates. |
| Commit status | Verify `git rev-parse HEAD` after this reconciliation commit. Live current = head `d2e3f4a5b6c7`. FG-021 **OPEN**. Approved presentation source custody **CLOSED**. |
| Governance baseline | FG-021 IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN; gate NOT CLOSED; live current = head d2e3f4a5b6c7; full suite 557; dedicated FG-021 19; focused 147; presentation source custody CLOSED; Legal Content Gate empty; Native Signing development may proceed separately / production blocked pending counsel; ADR-043 Accepted; Closeout FUTURE |

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

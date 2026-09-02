# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-02 |

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
| Report date | 2026-09-02 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | FG-020 Compatible Rendition increment: verify `git rev-parse HEAD` and `git rev-parse origin/main` after this commit. Starting parent `77d496367f9e6f003eb69949adb3bd82c6cadfd7`. FG-020 foundation `77d496367f9e6f003eb69949adb3bd82c6cadfd7`. FG-018 close: implementation parent `0d7af3e93a9d6c4f27eb2136f915297620be59ed`. FG-017 close `620dec1a9612e87a1ede20cfa6aa46c6d72a8dd5`. FG-016 close `fa591f14b2eb99db75c4e3720fdeb30d14a8f77a`. |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Docs reconcile after FG-006 | `e2bf33c` — *docs: reconcile post-FG-006 governance turnover state* |
| Latest completed **coded** milestone on `main` | **FG-021 IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING** (not closed; live current = head `d2e3f4a5b6c7`; dedicated FG-021 **13**; focused **141**). **FG-020 CLOSED / OPERATIONAL FOR UAT**. **FG-019 CLOSED / OPERATIONAL FOR UAT**. **FG-018 CLOSED / OPERATIONAL FOR UAT**. FG-008 through FG-017 remain **CLOSED / OPERATIONAL FOR UAT**. |
| Current milestone | [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING** (gate **NOT CLOSED**). [FG-020](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**. Item 11 **COMPLETE**. Item 12 Field Web **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**. [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. [FG-019](feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-018](feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**. |
| Product status | Operational on `main`: FG-021 Field Web V1 **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**. FG-020 BUILD Field Observation foundation **CLOSED / OPERATIONAL FOR UAT**. FG-019 Shared API Foundation V1 **CLOSED / OPERATIONAL FOR UAT**. FG-018 office authentication **CLOSED / OPERATIONAL FOR UAT**. Real iPhone UAT **not complete**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. FG-008 through FG-020 **CLOSED / OPERATIONAL FOR UAT**. [ADR-043](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) **Accepted**. [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. Phase D **not started**. Change Order document family **FUTURE / NOT IMPLEMENTED**. |
| Implemented capabilities | Prior coded baseline plus FG-021 `/field` Today + Project confirm + Capture; IndexedDB pending queue; idempotent Event/Original POST; Field display GET. FG-020 Field Capture Events / Originals / Derived Candidates; office Field Observations; bounded `/api/v1` BUILD POSTs; HEIC/HEIF → JPEG Compatible Renditions. FG-019 GET `/api/v1` over FG-018 session. |
| Incomplete work | FG-021 real iPhone UAT; Native Signing **production activation**; Project Closeout; Phase D estimate mapping; four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; MONITOR implementation; industry benchmarking; supplier/Winchester POC; bulk supplier onboarding; national permit library; Change Order document family; RBAC; org-switcher. |
| Database and migration status | Live current = head `d2e3f4a5b6c7`. Applied `c1d2e3f4a5b6` → `d2e3f4a5b6c7`. One graph head. |
| Test status | Dedicated FG-021 **13 passed**; focused (Hub + FG-018 + FG-019 + both FG-020 + FG-021) **141 passed**; full suite **551 passed**. Dedicated FG-020 **44**. Dedicated FG-019 **34**; dedicated FG-018 **37**. |
| Documentation status | [FG-021](feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**. Native Signing recon **COMPLETE**; counsel spec **PREPARED** — **NOT LEGAL APPROVAL**. Development may proceed under separate governance; production activation blocked pending counsel. Legal Content Gate **unchanged**. ADR-008 / ADR-010 **Proposed**. |
| Decisions made (this governance pass) | FG-021 live `flask db upgrade` applied. Pre-migration gitignored SQLite copy recorded. Gate **NOT CLOSED**. Native Signing **development may proceed under separate governance**; **production activation blocked pending counsel**. FG-020 remains **CLOSED / OPERATIONAL FOR UAT**. |
| Decisions pending | Real iPhone Safari UAT / FG-021 close. Whether to authorize a separate Native Signing development gate (production still blocked pending counsel). Ontario counsel answers to [legal/native-signing-process-counsel-review.md](legal/native-signing-process-counsel-review.md). Archive package format. Project Closeout Feature Gate not created. |
| Uncommitted work | None after this FG-021 live-migration docs commit. |
| Next approved milestone | Real iPhone Safari UAT. Do **not** close FG-021 until UAT. Native Signing **production** remains blocked pending counsel. Do **not** implement Closeout or Contract templates. |
| Next candidate milestone | FG-021 close after real iPhone UAT. Native Signing — **development may proceed under separate governance**; production blocked pending counsel. Project Closeout — **FUTURE / NOT AUTHORIZED**. |
| Documents to read first | [session-handoff.md](session-handoff.md) → [architecture/fg-021-field-web-v1-implementation-reconnaissance.md](architecture/fg-021-field-web-v1-implementation-reconnaissance.md) → [feature-gates/FG-021-field-web-v1-today-and-capture.md](feature-gates/FG-021-field-web-v1-today-and-capture.md) → [adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md](adr/ADR-043-field-web-capture-reliability-local-pending-and-idempotent-replay.md) → [architecture/field-web-today-and-capture.md](architecture/field-web-today-and-capture.md) → [feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md](feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) → [current-state.md](current-state.md) |
| Approved next Cursor prompt location or summary | Real iPhone Safari UAT / FG-021 close prompt, **or** a Native Signing development gate (production still counsel-blocked). Do **not** implement Closeout or Contract templates. |
| Commit status | Verify `git rev-parse HEAD` after this live-migration docs commit. Live current = head `d2e3f4a5b6c7`. FG-021 **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**. FG-020 **CLOSED / OPERATIONAL FOR UAT**. |
| Governance baseline | FG-021 IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING; gate NOT CLOSED; live current = head d2e3f4a5b6c7; full suite 551; dedicated FG-021 13; focused 141; Native Signing development may proceed separately / production blocked pending counsel; ADR-043 Accepted; Closeout FUTURE |

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

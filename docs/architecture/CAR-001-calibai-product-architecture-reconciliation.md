# CAR-001 — CalibAi Product & Architecture Reconciliation

| Attribute | Value |
|-----------|--------|
| ID | **CAR-001** |
| Title | CalibAi Product & Architecture Reconciliation |
| Status | **APPROVED ARCHITECTURAL DIRECTION** — implementation **not** authorized by CAR-001 |
| Date | 2026-08-28 |
| Approved by | Joel Brayman |
| Baseline | `main` @ `b7ec3ba` (anti-drift protocol); reconciliation was read-only |
| Product rename | **Not authorized** — repository product name remains The Estimator |

## Designation

The 2026-08-28 read-only reconciliation was mistakenly labeled M009 in a ChatGPT prompt. That label is **withdrawn**.

| Record | Meaning |
|--------|---------|
| **CAR-001** | This architecture/product reconciliation (docs/governance) |
| **M009** | Remains **coded Sheet classification / Sheet Intelligence implementation**, per the existing roadmap. At CAR-001 adoption this code was **not begun**. |

Do not renumber historical milestones.

**Subsequent status (2026-08-28, after CAR-001 — not authorized by CAR-001):** M009 was implemented and verified under [FG-004](../feature-gates/FG-004-m009-sheet-classification.md) (`5dc4b09`, migration `b8d9f0a1c2e3`). M010, M011, FG-006, FG-008, and FG-009 followed under their own gates. CAR-001 itself remains docs/governance direction only.

**Subsequent status (2026-08-29 — not authorized by CAR-001):** [FG-010](../feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) / M012 was implemented, committed, and pushed (`9665295`). Real external AI provider **not authorized**. PLAN remained partial; PRICE remained FG-008/FG-009 operational for UAT.

**Subsequent status (2026-08-30 — not authorized by CAR-001):** FG-010 / M012 is **LIVE-MIGRATED / UAT-SMOKE-VERIFIED** (`b4c5d6e7f8a9` **gate-at-close** head). **AI TAKE-OFF FOUNDATION OPERATIONAL FOR UAT.** Real external AI provider **not authorized**. Phase D **not started**. [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (MONITOR composed baseline and Project Gross Margin; MONITOR **not implemented**). [ADR-033](../adr/ADR-033-supplier-neutrality-and-launch-partner-channel.md) **Accepted** (supplier-neutral Winchester launch/reference channel; supplier integration **not implemented**; no Feature Gate).

**Subsequent status (2026-08-30 post-FG-017 — not authorized by CAR-001):** FG-011 through FG-017 are **CLOSED / OPERATIONAL FOR UAT**. Live Alembic current/head is **`a9b0c1d2e3f4`**. [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted**. Full-suite governed baseline **423 passed**.

**Subsequent status (2026-08-30 Item 10 governance — not authorized by CAR-001):** [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) is **Accepted**. [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) was then **APPROVED / IMPLEMENTATION NOT STARTED**. Office authentication **implementation NOT STARTED** on that date. Shared API **deferred**. BUILD remained blocked until Item 10 was implemented. CAR-001 still does **not** authorize implementation. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

**Subsequent status (2026-08-31 post-FG-018 — not authorized by CAR-001):** [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**. Live Alembic current = head **`b0c1d2e3f4a5`**. Full suite **460 passed**. Roadmap item 10 is **PARTIALLY COMPLETE**: office Authentication / Actor Identity / Membership is closed; Shared API foundation remains **NOT STARTED / DEFERRED / NOT AUTHORIZED**. Items 11–12 (BUILD / Field Web) remain blocked. MONITOR remains downstream / not implemented. CAR-001 still does **not** authorize implementation. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.** Next authorized action: **STOP.**

**Subsequent status (2026-08-31 FG-019 close — not authorized by CAR-001):** [FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md) is **CLOSED / OPERATIONAL FOR UAT**. GET-only `/api/v1`. No migration. Live Alembic current = head **`b0c1d2e3f4a5`**. Full suite **494 passed**. Roadmap item 10 is **COMPLETE**. Item 11 BUILD is **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. CAR-001 still does **not** authorize BUILD implementation. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

**Subsequent status (2026-08-31 ADR-042 Proposed — not authorized by CAR-001):** [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) was then **Proposed / FOR JOEL REVIEW**. It did **not** accept BUILD architecture in that pass. FG-020 was **not created**. BUILD / Field Web / transcription / external AI remained **not implemented**. Item 11 remained **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**. Live Alembic current = head **`b0c1d2e3f4a5`**. Full suite baseline **494 passed**. CAR-001 still does **not** authorize implementation.

**Subsequent status (2026-08-31 FG-020 Compatible Rendition increment — not authorized by CAR-001):** Image-only HEIC/HEIF → JPEG Compatible Renditions are **implemented**. FG-020 remains **IMPLEMENTED / LIVE MIGRATION PENDING**. Live current remains **`b0c1d2e3f4a5`**. Repository head remains **`c1d2e3f4a5b6`**. Full suite **538 passed**. No new migration. Item 12 Field Web remains **BLOCKED / NOT AUTHORIZED**. CAR-001 still does **not** authorize Field Web, MONITOR, Project Closeout, or live `flask db upgrade`. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

**Subsequent status (2026-08-31 FG-020 implemented / live migration pending — not authorized by CAR-001):** [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) is **IMPLEMENTED / LIVE MIGRATION PENDING**. Repository Alembic head **`c1d2e3f4a5b6`**. Live current remains **`b0c1d2e3f4a5`**. Full suite **527 passed**. Item 12 Field Web remains **BLOCKED / NOT AUTHORIZED**. CAR-001 still does **not** authorize Field Web, MONITOR, or live `flask db upgrade`. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

**Subsequent status (2026-08-31 FG-020 approved / recon recorded — not authorized by CAR-001):** [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) is **APPROVED / IMPLEMENTATION NOT STARTED**. Implementation reconnaissance is recorded. BUILD product code **NOT STARTED**. Item 11 is **approved / not started**. Item 12 Field Web remains **BLOCKED / NOT AUTHORIZED**. Live Alembic current = head **`b0c1d2e3f4a5`**. Full suite baseline **494 passed**. CAR-001 still does **not** authorize implementation.

**Subsequent status (2026-08-31 ADR-042 Accepted / FG-020 draft — not authorized by CAR-001):** [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) is **Accepted**. [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) is **DRAFT FOR JOEL REVIEW / NOT APPROVED**. BUILD implementation **NOT STARTED**. Item 11 is **governance in progress / NOT AUTHORIZED**. Item 12 Field Web remains **BLOCKED / NOT AUTHORIZED**. Live Alembic current = head **`b0c1d2e3f4a5`**. Full suite baseline **494 passed**. CAR-001 still does **not** authorize implementation.

**Subsequent status (2026-09-02 FG-021 live migration — not authorized by CAR-001):** [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) is **CLOSED / OPERATIONAL FOR UAT**. [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) is **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT PENDING**. Live Alembic current = head **`d2e3f4a5b6c7`**. Full suite **551 passed**. Gate **NOT CLOSED**. Real iPhone UAT **not complete**. CAR-001 still does **not** authorize Native Signing production, MONITOR, Project Closeout, or closing FG-021. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

**Subsequent status (2026-09-04 current-state reconciliation — not authorized by CAR-001):** [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) is **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN**. Latest product-changing suite **557 passed** (dedicated FG-021 **19**; focused **147**). Approved presentation source custody **CLOSED**. Legal Content Gate **empty**. CAR-001 still does **not** authorize Native Signing production, MONITOR, Project Closeout, reusable-template extraction, or closing FG-021.

**Subsequent status (2026-09-06 FG-021 OPTION 2 close — not authorized by CAR-001):** [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) is **CLOSED**. SESSION-EXPIRY RECOVERY **DEFERRED / NOT YET EXERCISED**. Live current = head **`d2e3f4a5b6c7`**. Full suite **558**. CAR-001 still does **not** authorize MONITOR implementation.

**Subsequent status (2026-09-06 MONITOR V1 recon — not authorized by CAR-001):** MONITOR V1 implementation reconnaissance is **COMPLETE** ([monitor-v1-implementation-reconnaissance.md](monitor-v1-implementation-reconnaissance.md)). MONITOR remains **NOT IMPLEMENTED**. CAR-001 still does **not** authorize MONITOR product code. **ROADMAP SEQUENCE ≠ IMPLEMENTATION AUTHORIZATION.**

**Subsequent status (2026-09-06 FG-023 draft — not authorized by CAR-001):** [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) is **DRAFT FOR JOEL APPROVAL / NOT APPROVED / NOT AUTHORIZED FOR IMPLEMENTATION**. CAR-001 still does **not** authorize MONITOR product code.

**Subsequent status (2026-09-06 FG-023 approval — not authorized by CAR-001):** [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) is **APPROVED / IMPLEMENTATION NOT STARTED / IMPLEMENTATION NOT YET AUTHORIZED**. CAR-001 still does **not** authorize MONITOR product code.

**Subsequent status (2026-09-06 FG-023 preflight — not authorized by CAR-001):** [fg-023-monitor-v1-implementation-preflight.md](fg-023-monitor-v1-implementation-preflight.md) is **COMPLETE**. Readiness **B**. CAR-001 still does **not** authorize MONITOR product code.

**Subsequent status (2026-09-06 FG-023 Slice A — not authorized by CAR-001):** [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) Slice A is **IMPLEMENTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED** (`2553cf09bdd6b8018112d7eb4b682f87aa103b01`; revision `e3f4a5b6c7d8` not applied live). MONITOR V1 is **PARTIALLY IMPLEMENTED**. Hub UI **NOT IMPLEMENTED**. Live current remains **`d2e3f4a5b6c7`**. Full suite **581**. CAR-001 still does **not** authorize Slice B, live migrate, or office UAT.

**Subsequent status (2026-09-07 Review Turnover — not authorized by CAR-001):** Current-authority pins and session-handoff §22 reconciled to Slice A. Next governed action at that time was FG-023 Slice B **implementation preflight / authorization**.

**Subsequent status (2026-09-07 Slice B preflight — not authorized by CAR-001):** Slice B **PREFLIGHT COMPLETE**. Hub UI **NOT IMPLEMENTED**. Next governed action is FG-023 Slice B **implementation** (separate authorization). CAR-001 still does **not** authorize Slice B product code, live migrate, or office UAT.

**Subsequent status (2026-09-07 Slice B implementation — not authorized by CAR-001):** Slice B **IMPLEMENTED / NOT LIVE-MIGRATED**. Hub `#hub-monitor` **in product code**. Dedicated **35**. Focused **149**. Full **593**. Live current remains **`d2e3f4a5b6c7`**. CAR-001 still does **not** authorize live migrate or office UAT.

**Subsequent status (2026-09-07 Slice C preflight — not authorized by CAR-001):** Slice C **PREFLIGHT COMPLETE / NOT PERFORMED**. Next governed action is FG-023 Slice C **execution**. CAR-001 still does **not** authorize live migrate or office UAT.

**Subsequent status (2026-09-07 Slice C execution — not authorized by CAR-001):** Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**. Live current = heads **`e3f4a5b6c7d8`**. Gate remains **OPEN**. CAR-001 still does **not** authorize FG-023 close or FG-024.

**Subsequent status (2026-09-07 FG-024 recorded — not authorized by CAR-001):** [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) is **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. CONTRACT legal-content intelligence is recorded, not implemented. Next governed implementation action remains FG-023 Slice C **execution**. CAR-001 still does **not** authorize FG-024 product code, legal-content population, live migrate, or office UAT.

**Subsequent status (2026-09-07 FG-025 recorded — not authorized by CAR-001):** [FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) is **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Contractor-facing UX language is recorded, not implemented. Slice C is already **PASS**. Next governed action remains FG-023 **close**. CAR-001 still does **not** authorize FG-025 UI rewrite, FG-023 close, or FG-024 product code.

**Subsequent status (2026-09-07 FG-023 close — not authorized by CAR-001):** [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) is **CLOSED / OPERATIONAL FOR UAT**. MONITOR V1 **IMPLEMENTED / LIVE-MIGRATED / OFFICE-UAT-VERIFIED / CLOSED**. Item 13 **CLOSED / OPERATIONAL FOR UAT**. Close-time tests dedicated **35** / focused **149** / full **593**. CAR-001 still does **not** authorize FG-024, FG-025, or LEARN.

**Subsequent status (2026-09-07 FG-025 implementation preflight — not authorized by CAR-001):** [FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) is **IMPLEMENTATION PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED / NOT CLOSED**. CAR-001 still does **not** authorize FG-025 UI rewrite, FG-024, or LEARN.

**Subsequent status (2026-09-07 FG-025 Slice 1 — not authorized by CAR-001):** [FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1 IMPLEMENTED / NOT CLOSED**. Remaining slices **NOT AUTHORIZED**. CAR-001 still does **not** authorize Slice 2, FG-024, or LEARN.

**Subsequent status (2026-09-07 FG-025 Slice 2 — not authorized by CAR-001):** [FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1 AND SLICE 2 IMPLEMENTED / NOT CLOSED**. Remaining slices **NOT AUTHORIZED**. CAR-001 still does **not** authorize Slice 3, FG-024, or LEARN.

**Subsequent status (2026-09-07 FG-025 Slice 3 — not authorized by CAR-001):** [FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 3 IMPLEMENTED / TESTED / COMMITTED / PUSHED**. Product SHA **`071f5f923515c6405298bf96b0af249a20f81358`**. FG-025 overall **NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. No schema / migration / DB / calculation change. CAR-001 still does **not** authorize Slice 4, FG-024, or LEARN.

**Subsequent status (2026-09-08 FG-025 Slice 4 — not authorized by CAR-001):** [FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 4 IMPLEMENTED / TESTED / COMMITTED / PUSHED**. Product SHA **`56e16f03446f982d577d2a3f0d3375ef865e1dc9`**. Parent **`ab6219827f33a59f4d6528bbfffbd4551b9d1411`**. FG-025 overall **NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. No schema / migration / DB / calculation change. CAR-001 still does **not** authorize Slice 5, FG-024, or LEARN.

**Subsequent status (2026-09-08 FG-025 Slice 5 — not authorized by CAR-001):** [FG-025](../feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 5 IMPLEMENTED / TESTED / COMMITTED / PUSHED**. Product SHA **`5b497905086554214e85f69afd8101d88f89161c`**. Parent **`0ed4d67282551d75b4204e33d367f3f3baba023a`**. FG-025 overall **NOT CLOSED**. Remaining surfaces **NOT AUTHORIZED**. No schema / migration / DB / Field workflow / media pipeline change. CAR-001 still does **not** authorize another FG-025 slice, FG-024, or LEARN.

**Subsequent status (2026-09-08 FG-026 implementation — live migrate/UAT not authorized by CAR-001):** [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT RUN / NOT CLOSED**. Additive `f4a5b6c7d8e9` in Git only. CAR-001 still does **not** authorize live migrate, FG-024, remaining FG-025 surfaces, or LEARN.

**Subsequent status (2026-09-08 V1 completion register after FG-026 implementation):** [v1-completion-register.md](../v1-completion-register.md) remains governing. Readiness **34%**. **0 / 11** major packages COMPLETE. V1-01 PARTIAL factor 0.55. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. This does **not** authorize live migrate, FG-024, another FG-025 slice, or LEARN.

**Subsequent status (2026-09-08 FG-027 implemented — live migrate not authorized by CAR-001):** [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) is **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED**. [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. Live current remains **`f4a5b6c7d8e9`**. Repository graph head **`a5b6c7d8e9f0`**. Readiness remains **39%**. CAR-001 still does **not** authorize FG-027 live migrate, FG-024, remaining FG-025 surfaces, or LEARN.

**Subsequent status (2026-09-08 FG-027 office UAT continuation + close — not authorized by CAR-001):** [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. V1-02 **COMPLETE**. Readiness **45%**. Live current = heads **`a5b6c7d8e9f0`**. CAR-001 still does **not** authorize V1-03, FG-024, remaining FG-025 surfaces, or LEARN.

**Subsequent status (2026-09-09 FG-028 product identity — not authorized by CAR-001):** Current product name is **CalibraytAI** (formerly CalibAi). [ADR-045](../adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. [FG-028](../feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) Slices 1–2 **IMPLEMENTED**; Slice 3 logo asset **HELD**. Repository name remains The Estimator / Brayman-Estimator. CAR-001 still does **not** authorize V1-03, FG-024 implementation, remaining FG-025 surfaces, LEARN, or a repository rename.

**Subsequent status (2026-09-09 FG-028 Slice 3 asset received — installation not authorized by CAR-001):** [FG-028](../feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) Slice 3 package `CalibraytAI_090926_Final.zip` is **ASSET RECEIVED / JOEL APPROVED / INSTALLATION PENDING**. Do **not** install during FG-029 live migration / UAT. Gate remains **NOT CLOSED**. CAR-001 still does **not** authorize logo installation, website publish, FG-024 implementation, remaining FG-025 surfaces, LEARN, or a repository rename.

**Subsequent status (2026-09-09 FG-030 supplier identity — not authorized by CAR-001):** [ADR-047](../adr/ADR-047-supplier-identity-authentication-and-access-isolation.md) **Accepted** (architecture only). [FG-030](../feature-gates/FG-030-supplier-identity-authentication-and-access-isolation.md) **RECORDED / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. Named supplier login, membership, package sharing, and fail-closed isolation. Not a 12th V1 major package. V1 remains **45% / 2 of 11**. CAR-001 still does **not** authorize FG-030 implementation, website publish, FG-024 implementation, remaining FG-025 surfaces, LEARN, or a repository rename.

**Subsequent status (2026-09-09 FG-029 V1-03 architecture recording — not authorized by CAR-001):** [ADR-046](../adr/ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted**. [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **RECORDED / ARCHITECTURE PREFLIGHT COMPLETE / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**. ADR-008 remains **Proposed**. V1 remains **45% / 2 of 11**. CAR-001 still does **not** authorize V1-03 product code, live BMR integration, FG-024 implementation, remaining FG-025 surfaces, or LEARN.

**Subsequent status (2026-09-09 FG-029 product implementation — live migrate not authorized by CAR-001):** [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **IMPLEMENTED / TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / NOT CLOSED** at that commit. Product SHA **`ee578dcb5a688842ebedaff0682131826e6c7188`**. Dedicated **16**. Full suite **677**. Live current remained **`a5b6c7d8e9f0`**. CAR-001 still does **not** authorize live migrate from that recording.

**Subsequent status (2026-09-09 FG-029 live migrate + bounded UAT close — not authorized by CAR-001):** [FG-029](../feature-gates/FG-029-bmr-supplier-workflow-v1.md) **CLOSED / OPERATIONAL FOR UAT**. Live current = head **`b6c7d8e9f0a1`**. V1-03 **COMPLETE**. Readiness **55%**. **3 / 11** COMPLETE. BMR DEMO READY **NO**. BRAYMAN REAL-LIFE UAT READY **NO**. Bounded DEMO project **id 14**. Issued package **id 1**. FG-030 remains **RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. FG-028 Slice 3 remains **APPLICATION INSTALLATION / TEST / ACCEPTANCE PENDING**. CAR-001 still does **not** authorize FG-030 implementation, Slice 3 installation, V1-04, FG-024, remaining FG-025 surfaces, LEARN, SCOPE DELIVERY / MAKE-BUY routing, or a repository rename.

**Subsequent status (2026-09-09 FG-028 Slice 3 installed — not authorized by CAR-001):** [FG-028](../feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–3 COMPLETE / CLOSED / OPERATIONAL FOR UAT**. Runtime `calibraytai-logo-v2.png` on Field header. Tenant office/login/Brand Profile logos unchanged. Field favicon unchanged (no supplied square favicon). CAR-001 still does **not** authorize FG-030 implementation, V1-04, FG-024, remaining FG-025 surfaces, LEARN, SCOPE DELIVERY / MAKE-BUY routing, or a repository rename.

**Subsequent status (2026-09-09 FG-031 Slice A product — not authorized by CAR-001):** [ADR-048](../adr/ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted**. [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **SLICE A IMPLEMENTED / NOT LIVE-MIGRATED / UAT NOT AUTHORIZED / SLICE B NOT AUTHORIZED / NOT CLOSED**. Two stored dimensions; 1:1 `EstimateScopeDelivery` per `EstimateLineItem`; no HYBRID enum. Supporting V1 gate; **not** a 12th major package. V1 remains **55% / 3 of 11**. CAR-001 still does **not** authorize live migrate, Slice B, FG-030 implementation, V1-04, FG-024, remaining FG-025 surfaces, LEARN, or a repository rename.

## What CAR-001 was

A repository-grounded, **read-only** mapping of the existing Brayman-Estimator / The Estimator platform onto the CalibAi lifecycle:

**PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN**

through one authoritative project record.

**No product code, schemas, or migrations were changed during CAR-001 analysis.**

Detailed capability inventory lived in the review session. This file is the durable decision record. Provenance: Joel review of that reconciliation; adoption prompt 2026-08-28.

## Approved product vision

See [platform-vision.md](../platform-vision.md).

CalibAi is a construction intelligence platform connecting PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN through one authoritative project record.

**Positioning:** Construction intelligence. Calibrated.

**Learning principle:** Every project makes the next project smarter.

CalibAi provides complementary **office** and **field** experiences over the same authoritative project record.

## Approved core architecture

| Decision | Record |
|----------|--------|
| `Project` remains the lifecycle hub; no parallel CalibAi Job entity | [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** |
| Preserve and extend the existing Flask platform (CRM, Projects, Estimating, Proposals, COs, Plan/Document/Sheet Intelligence architecture) | ADR-019 |
| BUILD is a new owning module; Change Orders stay with Project Controls | [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** |
| MONITOR compares estimated ↔ actual ↔ forecast; frozen composed baseline; Project Gross Margin | [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (Slice A projection + Slice B Hub **implemented / live-migrated / office-UAT-verified**; [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **CLOSED / OPERATIONAL FOR UAT**) |
| LEARN is review-gated and must not mutate pricing policy / cost library / approved estimates / historical actuals | [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** |
| Field is first-class; Flask services → API → field web → native later if warranted | [ADR-022](../adr/ADR-022-field-client-and-shared-api.md) **Accepted** |
| Original field evidence separate from derived structured records | [ADR-023](../adr/ADR-023-field-evidence-provenance.md) **Accepted** |
| Dual first-class BUILD surfaces; original audio/photo/text custody; capture-first; desktop review | [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Accepted**; [FG-020](../feature-gates/FG-020-build-field-capture-v1-project-field-observation-foundation.md) **CLOSED / OPERATIONAL FOR UAT**; [FG-021](../feature-gates/FG-021-field-web-v1-today-and-capture.md) **IMPLEMENTED / LIVE-MIGRATED / IPHONE UAT OPEN** |
| Pricing markup stack vs 15% gross-margin policy — named methods **CLOSED / OPERATIONAL FOR UAT** | [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **CLOSED / OPERATIONAL FOR UAT** |

Replacement of existing modules or schemas requires **separate explicit approval**.

## Approved V1 direction

V1 should demonstrate a thin but genuine connected construction lifecycle:

PLAN → PRICE → CONTRACT BASELINE → BUILD field capture → BASIC MONITOR (estimate vs actual)

LEARN in early V1 may begin as historical capture / structured project results. Sophisticated recommendation/ML is later.

**Explicitly later / separately Feature-Gated (not V1 implementation):** voice AI, photo AI, advanced forecasting, native iOS, offline-first sync, QuickBooks API, automated Ontario contract/warranty generation, supplier integrations, purchase orders, CAD-first, multi-tenant productization, ML recommendations, product/repository rename.

CAR-001 does **not** implement any of the above.

## Proposed development sequence (roadmap direction only)

Each coded slice still requires its own Feature Gate and approved Cursor prompt.

0. CAR-001 architecture alignment (this record)
1. **M009** Sheet classification / human review
2. Project Hub UX
3. Pricing-policy application (after ADR-025) — **now tracked as [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md)** (approved for implementation 2026-08-29; **not implemented**). This CAR-001 list is historical sequence direction, not implementation authority.
4. Internal Detailed Cost Breakdown + Customer Estimate consistency
5. Authentication / actor identity + shared API foundation
6. BUILD Field Capture V1
7. Field Web / Today + Capture + plan access
8. MONITOR basic estimated-vs-actual
9. LEARN historical intelligence / review-gated learning
10. Contract/warranty when Legal Content Gate is satisfied
11. QuickBooks when separately Feature-Gated

**Auth dependency (not a silent reorder):** Items 6–7 (BUILD capture and field web) **require** item 5 (authentication / actor identity). M009 office sheet work may proceed on the current unauthenticated office app; that risk is known and is not used to move auth ahead of M009 in this sequence.

## Related

- [platform-vision.md](../platform-vision.md)
- [platform-roadmap.md](../platform-roadmap.md)
- [architecture.md](../architecture.md)
- [modules/build.md](../modules/build.md)
- [modules/monitor.md](../modules/monitor.md)
- [continuity-and-anti-drift.md](../governance/continuity-and-anti-drift.md)

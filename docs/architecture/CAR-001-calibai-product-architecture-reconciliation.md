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
| MONITOR compares estimated ↔ actual ↔ forecast; frozen composed baseline; Project Gross Margin | [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (2026-08-30; MONITOR **not implemented**) |
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

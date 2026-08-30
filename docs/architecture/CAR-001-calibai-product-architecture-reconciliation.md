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

**Subsequent status (2026-08-30 — not authorized by CAR-001):** FG-010 / M012 is **LIVE-MIGRATED / UAT-SMOKE-VERIFIED** (`b4c5d6e7f8a9`). **AI TAKE-OFF FOUNDATION OPERATIONAL FOR UAT.** Real external AI provider **not authorized**. Phase D **not started**. [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (MONITOR composed baseline and Project Gross Margin; MONITOR **not implemented**).

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
| Pricing markup stack vs 15% gross-margin policy — named methods accepted; not implemented | [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **APPROVED FOR IMPLEMENTATION** |

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

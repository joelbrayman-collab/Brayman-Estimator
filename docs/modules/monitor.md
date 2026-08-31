# Module — MONITOR

| Attribute | Value |
|-----------|--------|
| Status | **Proposed / Intended** — **not implemented** |
| Updated | 2026-08-30 |
| Code | None |
| ADR | [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (baseline and Project Gross Margin governance; implementation not authorized) |
| CAR | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |

## Purpose

Provide a **Project-centered comparison / read layer** for estimated vs actual vs forecast, including **Project Gross Margin**, without becoming the system of record for estimates, proposals, Change Orders, field actuals, accounting, or calibration standards.

## Intended owned records (when Feature-Gated)

Dated MONITOR **comparison snapshots** and dated **forecast snapshots** only. Source evidence remains owned by other modules.

## Referenced data (intended)

- Locked `EstimateVersion` and `EstimatePricingSnapshot` (when present)
- Accepted Proposal (immutable customer commitment)
- Approved Change Orders (auditable commercial deltas)
- BUILD / later actual-cost observations (ORG-ACTUAL)
- Project hub (`Project` — [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md))

## Prohibited responsibilities

- Owning or mutating estimates, proposals, Change Orders, field actuals, or ORG-APPROVED standards
- Using Draft estimates or Draft Proposal restacks as the committed baseline
- Treating industry benchmarks as profitability truth
- Treating QuickBooks, invoiced status, or cash received as Final Authorized Revenue unless later accounting governance says so
- Silent LEARN writes ([ADR-024](../adr/ADR-024-learn-recommendation-boundary.md))

## Current implementation

**None.** [FG-011](../feature-gates/FG-011-project-hub-ux.md) Project Hub labels MONITOR **Future**. No MONITOR models, routes, or UI.

## Dependencies

- ADR-021 (this baseline) — **Accepted**
- Verified actuals (BUILD / later actual-cost gates) before Actual Gross Margin can be computed
- Authentication before field capture ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md); [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **IMPLEMENTED / LIVE MIGRATION PENDING**)
- Feature Gate + approved Cursor prompt before any code

## Related

- [modules/projects.md](projects.md)
- [modules/build.md](build.md)
- [modules/estimating.md](estimating.md)
- [modules/proposals.md](proposals.md)
- [pricing-policy.md](../pricing-policy.md)

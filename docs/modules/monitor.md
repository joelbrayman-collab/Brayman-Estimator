# Module — MONITOR

| Attribute | Value |
|-----------|--------|
| Status | **Partial Current** — Slice A comparison service **implemented** (not operational Hub). V1 recon **COMPLETE**. [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **APPROVED / OPEN / NOT CLOSED**. Hub UI **NOT IMPLEMENTED**. Live migration **NOT PERFORMED**. |
| Updated | 2026-09-06 |
| Code | `app/services/monitor.py` (`assemble_monitor_v1`). BUILD actuals: `app/models/direct_cost_actual.py`, `app/services/direct_cost_actuals.py`. No Hub `#hub-monitor` UI. |
| ADR | [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (baseline and Project Gross Margin governance; implementation not authorized) |
| Recon | [monitor-v1-implementation-reconnaissance.md](../architecture/monitor-v1-implementation-reconnaissance.md) **COMPLETE** |
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

**Slice A (2026-09-06):** live projection `assemble_monitor_v1(project, organization_id)` in `app/services/monitor.py`. BUILD-owned `ProjectDirectCostActual` / `project_direct_cost_actuals` via `app/services/direct_cost_actuals.py`. Additive revision `e3f4a5b6c7d8` **created, not applied live**. Dedicated tests `tests/test_monitor_v1_fg023.py` **23 passed**. Full suite **581 passed**.

**Not implemented:** Project Hub `#hub-monitor` UI / office write routes; live `flask db upgrade`; office UAT; MONITOR snapshot table; forecast-final GM; NET PROFIT; Field Event conversion; QuickBooks. [FG-011](../feature-gates/FG-011-project-hub-ux.md) Hub still labels MONITOR **Future** until Slice B. Preflight: [fg-023-monitor-v1-implementation-preflight.md](../architecture/fg-023-monitor-v1-implementation-preflight.md) **COMPLETE**. Feature Gate: [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **APPROVED / OPEN / NOT CLOSED**.

## Dependencies

- ADR-021 (this baseline) — **Accepted**
- Verified actuals (BUILD / later actual-cost gates) before Actual Gross Margin can be computed
- Authentication before field capture ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md); [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**)
- Feature Gate + approved Cursor prompt before remaining slices. [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) is **APPROVED / OPEN**. Slice A is **implemented / not live-migrated**. Slice B Hub UI and Slice C live-migrate/UAT remain separately authorized.

## Related

- [modules/projects.md](projects.md)
- [modules/build.md](build.md)
- [modules/estimating.md](estimating.md)
- [modules/proposals.md](proposals.md)
- [pricing-policy.md](../pricing-policy.md)

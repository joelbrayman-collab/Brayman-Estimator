# Module — MONITOR

| Attribute | Value |
|-----------|--------|
| Status | **Partial Current** — Slice A comparison service **implemented**. Slice B Hub `#hub-monitor` + office actuals writes **implemented**. Slice C **MIGRATION COMPLETE / OFFICE UAT COMPLETE / PASS**. **LIVE-MIGRATED**. **OFFICE-UAT-VERIFIED**. V1 recon **COMPLETE**. [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **APPROVED / OPEN / NOT CLOSED**. Gate close **NOT PERFORMED**. |
| Updated | 2026-09-07 |
| Code | `app/services/monitor.py` (`assemble_monitor_v1`). BUILD actuals: `app/models/direct_cost_actual.py`, `app/services/direct_cost_actuals.py`, `app/routes/build.py` create/supersede. Hub: `app/services/project_hub.py`, `app/templates/projects/detail.html` `#hub-monitor`. |
| ADR | [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (baseline and Project Gross Margin; Slice A projection + Slice B Hub display implemented; live-migrated; office-UAT-verified) |
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

**Slice A (2026-09-06):** live projection `assemble_monitor_v1(project, organization_id)` in `app/services/monitor.py`. BUILD-owned `ProjectDirectCostActual` / `project_direct_cost_actuals` via `app/services/direct_cost_actuals.py`. Additive revision `e3f4a5b6c7d8` **applied live** 2026-09-07.

**Slice B (2026-09-07):** Project Hub `#hub-monitor` displays MONITOR V1 identities and office actual-cost create/supersede POSTs in `app/routes/build.py`. Dedicated tests `tests/test_monitor_v1_fg023.py` **35 passed**. Focused **149 passed**. Full suite **593 passed**. Historical Slice A focused **126** and pre-Slice-B focused **137** remain historical.

**Slice C (2026-09-07):** Live `flask db upgrade e3f4a5b6c7d8` **PASS**. Office UAT **PASS** on port **5014** against synthetic project **id 13** `FG023-UAT-MONITOR`. Tests **not rerun**.

**Not implemented:** MONITOR snapshot table; forecast-final GM; NET PROFIT; Field Event conversion; QuickBooks; Field Web MONITOR; FG-023 **close**. LEARN remains Future on the Hub. Preflight: [fg-023-monitor-v1-implementation-preflight.md](../architecture/fg-023-monitor-v1-implementation-preflight.md) **COMPLETE**. Feature Gate: [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) **APPROVED / OPEN / NOT CLOSED**.

## Dependencies

- ADR-021 (this baseline) — **Accepted**
- Verified actuals (BUILD / later actual-cost gates) before Actual Gross Margin can be computed
- Authentication before field capture ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md); [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**)
- Feature Gate + approved Cursor prompt before remaining slices. [FG-023](../feature-gates/FG-023-monitor-v1-estimated-versus-actual.md) is **APPROVED / OPEN**. Slice A and Slice B are **implemented / live-migrated**. Slice C migrate/UAT **PASS**. Gate close remains separately authorized.

## Related

- [modules/projects.md](projects.md)
- [modules/build.md](build.md)
- [modules/estimating.md](estimating.md)
- [modules/proposals.md](proposals.md)
- [pricing-policy.md](../pricing-policy.md)

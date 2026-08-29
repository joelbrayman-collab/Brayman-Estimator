# ADR-029 — Canonical Labour Task, Versioned Production Standard, and Evidence-to-Approval Calibration Lifecycle

| Field | Value |
|-------|--------|
| Title | ADR-029: Canonical Labour Task, Versioned Production Standard, and Evidence-to-Approval Calibration Lifecycle |
| Status | **Accepted** (architectural direction; FG-008 implementation **not started**) |
| Date | 2026-08-29 |
| Related | [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) · [labour-engine-phase-b-architecture.md](../architecture/labour-engine-phase-b-architecture.md) · [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md) · [ADR-024](ADR-024-learn-recommendation-boundary.md) · [ADR-025](ADR-025-pricing-policy-versus-estimate-markup-stack.md) · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) · [ADR-002](ADR-002-accepted-proposal-immutability.md) · [ADR-017](ADR-017-sheet-metadata-suggestion-and-review-workflow.md) |

## Context

FG-006 persisted 120 `HistoricalLabourItem` rows for ORG-001 as ORG-HISTORICAL evidence. Those rows use free-text `task_description` values (73 distinct strings), optional crew/duration/hours, and an `hourly_rate` that is not always a true dollars-per-man-hour. Active estimating still prices labour as lump `CostItem.unit_cost` / `EstimateLineItem` markup lines.

Without a governed labour methodology, implementation would risk:

- treating Brayman strings, $65/hr, and historical hours as universal CalibAi defaults
- silently equating unlike task labels
- collapsing production rate, wage rate, margin, and posture into one factor
- auto-promoting historical or actual evidence into operating standards
- retroactively repricing locked estimates when standards change

Org architecture §18 illustrated a silent commercial-profile productivity multiplier. That conflicts with §12 and FG-007: Pricing Posture must not alter true labour hours.

## Decision

*(Accepted 2026-08-29 — architecture approved. Product code, schema, and migrations still require a **separate FG-008 implementation prompt**.)*

1. **Canonical Labour Task** is organization-owned. Historical source strings remain distinct until a human accepts a mapping. AI may suggest; AI may not merge.

2. **Production Rate Standard** and **Direct Labour Cost Rate Standard** are separate, versioned, organization-owned records.  
   `QUANTITY × PRODUCTION RATE = MAN-HOURS`  
   `MAN-HOURS × DIRECT LABOUR COST RATE = DIRECT LABOUR COST`  
   Crew × hours/day × duration may express the same man-hours; it must not hide the economics.

3. **ORG-001** `$65 CAD / man-hour` and 15% true gross margin remain Brayman policy ([pricing-policy.md](../pricing-policy.md)), not platform defaults. FG-008 must not change that policy. Selling-price formula migration remains [ADR-025](ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Proposed**.

4. **Evidence classes** stay as already adopted (ORG-ACTUAL, ORG-APPROVED, CURRENT, ORG-HISTORICAL, BASELINE, PROVISIONAL, MANUAL). ORG-ACTUAL and ORG-HISTORICAL must not silently become ORG-APPROVED. AI cannot set ORG-APPROVED.

5. **Calibration Candidate** is a dedicated entity with an explicit state machine: evidence → analysis → candidate → human review → new ORG-APPROVED version (or reject). Candidates stay distinguishable from raw evidence, approved standards, manual overrides, and baseline.

6. **Labour-standard resolution** is deterministic and explainable, in this order: approved project-specific override; active matching ORG-APPROVED standard; other reviewed org evidence only if expressly authorized for that estimate; CalibAi baseline; provisional/manual. Each resolution stores organization, class, source, version, effective date, provenance, and reason.

7. **Project conditions** select a matching approved standard or require an **explicit documented** adjustment with reason. No hidden labour multipliers from Pricing Posture, Execution Risk, or commercial profile. Org architecture §18’s automatic `+15%` hours example is **not** authorized for the Labour Engine.

8. **Crew Template catalog is deferred.** Phase B stores crew assumptions on the production standard and snapshot only.

9. **Payroll burden breakdown is deferred.** Phase B uses a blended internal direct labour cost rate.

10. **EstimateVersion** (when using the engine) pins an immutable labour-assumption snapshot. Later standard changes spawn new versions; they do not rewrite locked estimates, accepted proposal snapshots, or FG-006 historical rows.

11. **Tenant isolation:** every labour intelligence record is organization-owned; cross-org lookup fail-closed; no pooled learning.

12. **Actual labour persistence and field capture are out of FG-008 coded scope.** Estimated-vs-actual architecture is defined for later BUILD/MONITOR gates.

## Alternatives Considered

- **Treat CostItem Labour category as the production engine** — Rejected: lump `unit_cost` cannot represent quantity × production rate × wage rate with provenance.
- **Auto-cluster historical strings into canonical tasks** — Rejected: silent merge of unlike work.
- **Single “labour factor” combining productivity, wage, risk, and posture** — Rejected: violates FG-007 / org architecture §12.
- **Implement Crew Template and burden model in Phase B** — Rejected: scope expansion not required for the economic identity.
- **Silent condition multipliers on hours** — Rejected: unauditable; conflicts with no-hidden-multiplier rule.
- **Promote FG-006 rows to ORG-APPROVED on ingest** — Rejected: evidence is not an operating standard; quality defects (e.g. stored rate `0.13`) prove the risk.

## Consequences

**Positive:** Methodology is reusable across organizations; commercial intelligence stays tenant-private; historical evidence can inform calibration without corrupting the bid book; locked estimates remain reproducible.

**Negative:** First implementation needs mapping UX and will not automatically produce production rates where historical rows lack quantity. Estimators must approve standards. Wiring Labour Engine output into estimate line selling prices is a later, separately gated step.

## Module Ownership Impact

A **Labour Engine** module owns canonical tasks, mappings, production/rate standards, calibration candidates, and estimate labour snapshots. Estimating continues to own cost library and estimate line selling-price math. Historical ingestion continues to own `HistoricalLabourItem`. BUILD/MONITOR will own actuals write path when gated.

## Data Ownership Impact

New organization-owned records (intended). Historical labour rows remain ingestion-owned evidence. No silent rewrite of proposals, commercial context versions, or historical workbooks.

## Migration Impact

**Deferred** until a separate FG-008 **implementation** prompt. Additive tables only. No casual Alembic in this approval pass.

## Testing Impact

**Deferred** to implementation. Must include org isolation, mapping review, production-rate math, resolution audit, candidate promotion, estimate snapshot immutability, and non-regression of pricing math and historical ingestion.

## Documentation Impact

[labour-engine-phase-b-architecture.md](../architecture/labour-engine-phase-b-architecture.md); [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) **APPROVED FOR IMPLEMENTATION** (not implemented); [modules/labour-engine.md](../modules/labour-engine.md); ADR index; Feature Gate index; current-state / handoff / roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-29 |
| ChatGPT review | Stopping report reviewed; architecture accepted | 2026-08-29 |
| Cursor implementation note | Docs/governance only; FG-008 **not implemented**; no product code | 2026-08-29 |

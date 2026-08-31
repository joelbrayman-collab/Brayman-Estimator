# Module — Labour Engine

| Attribute | Value |
|-----------|--------|
| Status | **Current** — FG-008 Phase B foundation **CLOSED / OPERATIONAL FOR UAT** (revision `f2c3d4e5f6a7` in chain; **gate-at-close** live head `b4c5d6e7f8a9`; live head today `a9b0c1d2e3f4`) |
| Updated | 2026-08-30 |
| Feature Gate | [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) **CLOSED / OPERATIONAL FOR UAT** |
| Architecture | [../architecture/labour-engine-phase-b-architecture.md](../architecture/labour-engine-phase-b-architecture.md) |
| ADR | [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** |
| Code | `app/models/labour_engine.py`, `app/services/labour_engine.py`, `app/routes/labour_engine.py`, `app/templates/labour_engine/`, migration `f2c3d4e5f6a7` |

## Purpose

Own CalibAi labour **methodology** for an organization: canonical tasks, versioned production rates, versioned direct labour cost rates, calibration candidates, and frozen estimate labour assumptions.

CalibAi owns the engine. Each organization owns its labour intelligence. ORG-001 (Brayman) is not the universal model.

## Responsibilities

- Canonical Labour Task catalog (org-owned)
- Human-reviewed source-string mappings (`ACCEPTED` may be **REVOKED** by a human with a reason; `ARCHIVED` tasks cannot drive rule suggestions)
- Versioned production-rate standards
- Versioned direct labour cost rate standards (not selling price)
- Calibration candidate review
- Explainable rate resolution
- Estimate labour-assumption snapshots
- Append-only `LabourAuditEvent`

## Owned data

`LabourTask`, `LabourTaskMapping`, `ProductionRateStandard`, `DirectLabourCostRateStandard`, `LabourCalibrationCandidate`, `EstimateLabourSnapshot`, `LabourAuditEvent`.

## Referenced data

- `organizations`
- `historical_labour_items` and related FG-006 evidence (owned by historical ingestion)
- `projects` / `project_commercial_contexts` (conditions as context, not silent hour multipliers)
- `estimate_versions` (snapshot pin)

## Prohibited responsibilities

- Owning historical source workbooks or rewriting `HistoricalLabourItem` facts
- Owning cost library masters (`cost_items`) or proposal snapshots
- Changing [pricing-policy.md](../pricing-policy.md) or implementing ADR-025 selling-price migration
- Field time capture (BUILD). MONITOR compares estimated vs actual and does not own actuals ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted**; `LabourActualObservation` remains unimplemented)
- Cross-organization labour pooling

## Current implementation

Office UI at `/labour-engine/`. ORG-001 $65 CAD/man-hour Direct Labour Cost Rate Standard v1 is seeded as organization policy (`docs/pricing-policy.md` provenance); other organizations do not inherit it. Unknown organizations receive fail-closed resolution and cannot persist `LabourAuditEvent`. Historical labour remains FG-006 evidence. Estimating `CostItem` category `Labour` lump unit costs remain valid for legacy estimates. Snapshots are opt-in and are **not** wired into selling-price calculation.

## Invariants

- Quantity × production rate = man-hours; man-hours × direct labour cost rate = direct labour cost
- Production rate ≠ direct labour cost rate ≠ pricing posture ≠ execution risk
- ORG-ACTUAL / ORG-HISTORICAL never silently become ORG-APPROVED
- AI never sets ORG-APPROVED
- Tenant queries fail closed
- Locked estimate snapshots do not float with later standards

## Open decisions

- ORG-001 canonical task catalog contents (empty catalog shipped; office create/mapping)
- Actuals persistence deferred
- Crew Template catalog deferred
- Burden modeling deferred
- ADR-025 remains **Accepted**; [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) is approved for implementation, **not implemented**. Labour Engine must not “fix” selling price.

## Relevant tests

`tests/test_labour_engine.py` (25 passed as of 2026-08-29 post-UAT integrity stabilization).

## Relevant ADRs

- ADR-029 **Accepted**
- ADR-024 **Accepted** (LEARN boundary)
- ADR-028 **Accepted** (organization isolation)
- ADR-025 **Accepted** (do not change estimate selling-price math in the Labour Engine)

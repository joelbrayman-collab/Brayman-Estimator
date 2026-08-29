# Module — Labour Engine

| Attribute | Value |
|-----------|--------|
| Status | **Current** — FG-008 Phase B foundation **IMPLEMENTED / VERIFIED** (live DB not yet migrated) |
| Updated | 2026-08-29 |
| Feature Gate | [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) **IMPLEMENTED / VERIFIED** |
| Architecture | [../architecture/labour-engine-phase-b-architecture.md](../architecture/labour-engine-phase-b-architecture.md) |
| ADR | [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** |
| Code | `app/models/labour_engine.py`, `app/services/labour_engine.py`, `app/routes/labour_engine.py`, `app/templates/labour_engine/`, migration `f2c3d4e5f6a7` |

## Purpose

Own CalibAi labour **methodology** for an organization: canonical tasks, versioned production rates, versioned direct labour cost rates, calibration candidates, and frozen estimate labour assumptions.

CalibAi owns the engine. Each organization owns its labour intelligence. ORG-001 (Brayman) is not the universal model.

## Responsibilities

- Canonical Labour Task catalog (org-owned)
- Human-reviewed source-string mappings
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
- Field time capture (BUILD) or MONITOR actuals persistence (until those gates)
- Cross-organization labour pooling

## Current implementation

Office UI at `/labour-engine/`. ORG-001 $65 CAD/man-hour Direct Labour Cost Rate Standard v1 is seeded as organization policy (`docs/pricing-policy.md` provenance); other organizations do not inherit it. Historical labour remains FG-006 evidence. Estimating `CostItem` category `Labour` lump unit costs remain valid for legacy estimates. Snapshots are opt-in and are **not** wired into selling-price calculation.

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
- ADR-025 remains **Proposed**

## Relevant tests

`tests/test_labour_engine.py` (22 passed as of 2026-08-29 implementation pass).

## Relevant ADRs

- ADR-029 **Accepted**
- ADR-024 **Accepted** (LEARN boundary)
- ADR-028 **Accepted** (organization isolation)
- ADR-025 **Proposed** (do not change estimate selling-price math here)

# Module — Labour Engine

| Attribute | Value |
|-----------|--------|
| Status | **Intended** — architecture **approved**; **not implemented** |
| Updated | 2026-08-29 |
| Feature Gate | [FG-008](../feature-gates/FG-008-labour-engine-phase-b.md) **APPROVED FOR IMPLEMENTATION** (implementation has **not** started) |
| Architecture | [../architecture/labour-engine-phase-b-architecture.md](../architecture/labour-engine-phase-b-architecture.md) |
| ADR | [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** |
| Code | **None** |

## Purpose

Own CalibAi labour **methodology** for an organization: canonical tasks, versioned production rates, versioned direct labour cost rates, calibration candidates, and frozen estimate labour assumptions.

CalibAi owns the engine. Each organization owns its labour intelligence. ORG-001 (Brayman) is not the universal model.

## Responsibilities (intended)

- Canonical Labour Task catalog (org-owned)
- Human-reviewed source-string mappings
- Versioned production-rate standards
- Versioned direct labour cost rate standards (not selling price)
- Calibration candidate review
- Explainable rate resolution
- Estimate labour-assumption snapshots

## Owned data (intended; not in schema yet)

Conceptual: `LabourTask`, `LabourTaskMapping`, `ProductionRateStandard`, `DirectLabourCostRateStandard`, `LabourCalibrationCandidate`, estimate labour snapshots.

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

**None.** Labour in production today is: (1) FG-006 historical evidence rows; (2) Estimating `CostItem` category `Labour` lump unit costs.

## Invariants

- Quantity × production rate = man-hours; man-hours × direct labour cost rate = direct labour cost
- Production rate ≠ direct labour cost rate ≠ pricing posture ≠ execution risk
- ORG-ACTUAL / ORG-HISTORICAL never silently become ORG-APPROVED
- AI never sets ORG-APPROVED
- Tenant queries fail closed
- Locked estimate snapshots do not float with later standards

## Open decisions

- FG-008 and ADR-029: architecture **approved**; implementation **not started** (separate execution prompt required)
- Actuals persistence deferred (recommended)
- Crew Template catalog deferred
- Burden modeling deferred

## Relevant tests

None yet. Future tests are listed in FG-008.

## Relevant ADRs

- ADR-029 **Accepted**
- ADR-024 **Accepted** (LEARN boundary)
- ADR-028 **Accepted** (organization isolation)
- ADR-025 **Proposed** (do not change estimate selling-price math here)

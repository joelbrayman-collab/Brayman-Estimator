# Module — Pricing Engine

| Attribute | Value |
|-----------|--------|
| Status | **FG-009 FOUNDATION OPERATIONAL FOR UAT** |
| Updated | 2026-08-29 |
| Feature Gate | [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Architecture | [../architecture/organization-calibrated-pricing-engine-architecture.md](../architecture/organization-calibrated-pricing-engine-architecture.md) |
| ADRs | [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** |
| Code | `app/models/pricing_engine.py`, `app/services/pricing_engine.py`, `app/routes/pricing_engine.py`, `/pricing-engine/` office UI. Migration `a3b4c5d6e7f8`. |

## Purpose

Own CalibAi pricing **methodology**: named methods, organization-owned policy versioning, deterministic resolution, and immutable estimate pricing snapshots.

CalibAi owns the engine. Each organization owns its commercial intelligence. ORG-001 (Brayman) is not the universal model.

## Responsibilities

- Versioned organization pricing policies
- Named methods (`TRUE_GROSS_MARGIN`, `COST_PLUS_MARKUP`, `COST_PLUS_MARKUP_STACK`)
- Policy resolution and provenance
- Estimate pricing snapshots
- Change Order inheritance of the estimate snapshot contract
- Pricing audit events
- Minimal office UI for policy review/approval and snapshot inspection

## Owned data

- `OrganizationPricingPolicy`
- `EstimatePricingSnapshot`
- `PricingAuditEvent`

## Referenced data

- `organizations`
- `project_commercial_contexts` (posture/risk as snapshot context, not silent multipliers; optional `pricing_policy_id`)
- `estimate_versions` / line `extended_cost`
- Labour Engine **direct labour cost** (read-only consume; default apply path does not add labour-snapshot cost into the estimate basis)
- FG-006 historical commercial facts (read-only evidence)

## Prohibited responsibilities

- Owning historical source workbooks or rewriting ingestion facts
- Changing production rates, man-hours, or direct labour cost rates
- Implementing four-output documents, QuickBooks API, or contracts
- Setting ORG-APPROVED policy via AI
- Cross-organization pooling of private economics
- Recalculating locked/accepted commercial records or backfilling legacy totals

## Current implementation

- Versions **without** an `EstimatePricingSnapshot` continue to use live `COST_PLUS_MARKUP_STACK` in `app/services/estimate_builder.py`.
- Versions **with** a snapshot recalculate via the frozen named method (`refresh_version_from_snapshot`). Later org policy changes do not re-resolve locked snapshots.
- New estimates are **not** auto-converted to `TRUE_GROSS_MARGIN`. A human must apply org pricing on a draft version.
- ORG-001 seed (migration, if `ORG-001` exists): `TRUE_GROSS_MARGIN` 15%, Ontario HST 13% (`CA-ON`). Overhead, profit, and contingency treatments are **`UNSPECIFIED`** (not yet governed; not inferred from historical workbooks). `UNSPECIFIED` is distinct from an org-approved `NOT_APPLIED` decision. Not a CalibAi default.
- Pricing Posture and Execution Risk are recorded on the snapshot only.
- FG-009-aware Change Orders inherit the linked snapshot **and apply its pricing METHOD** (`TRUE_GROSS_MARGIN`, `COST_PLUS_MARKUP`, or `COST_PLUS_MARKUP_STACK`). Historical Change Orders without a snapshot retain legacy markup-on-subtotal behavior.
- Live development/UAT `flask db current` / graph head: `a3b4c5d6e7f8`.

## Invariants (architecture)

- 15% true gross margin ≠ 15% markup
- Direct Cost, contingency source/visibility/pricing treatment, margin, markup, overhead, profit, tax, allowance, discount, Pricing Posture, and Execution Risk remain distinct
- Snapshots do not float when org policy later changes
- Tax is downstream of pre-tax selling price unless a future org/legal policy proves otherwise

## Open decisions

- ORG-001 overhead, profit, and contingency treatments remain `UNSPECIFIED` until a human-approved org policy change (not hard-coded from historical examples; not silently recorded as `NOT_APPLIED`)
- When (if) labour-snapshot Direct Labour Cost should be included in the estimate basis without double-counting CostItem labour lines

## Relevant tests

`tests/test_pricing_engine.py` (33 passed after pre-commit bounded correction). Also `tests/test_estimate_builder.py`, `tests/test_historical_ingestion.py`, `tests/test_labour_engine.py`, full suite (228 passed).

## Relevant ADRs

- [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**
- [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted**

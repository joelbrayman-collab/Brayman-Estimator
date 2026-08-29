# Module — Pricing Engine

| Attribute | Value |
|-----------|--------|
| Status | **Architecture approved** — **not implemented** |
| Updated | 2026-08-29 |
| Feature Gate | [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **APPROVED FOR IMPLEMENTATION** (not implemented) |
| Architecture | [../architecture/organization-calibrated-pricing-engine-architecture.md](../architecture/organization-calibrated-pricing-engine-architecture.md) |
| ADRs | [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** |
| Code | **None.** Live selling-price math remains `app/services/estimate_builder.py` (markup/overhead/profit stack). |

## Purpose

Own CalibAi pricing **methodology**: named methods, organization-owned policy versioning, deterministic resolution, and immutable estimate pricing snapshots.

CalibAi owns the engine. Each organization owns its commercial intelligence. ORG-001 (Brayman) is not the universal model.

## Responsibilities (intended)

- Versioned organization pricing policies
- Named methods (`TRUE_GROSS_MARGIN`, `COST_PLUS_MARKUP`, `COST_PLUS_MARKUP_STACK`; `TIERED` later)
- Policy resolution and provenance
- Estimate pricing snapshots
- Change Order inheritance of the estimate snapshot contract
- Explainable calculation (including future AI explanation — not approval)

## Owned data (intended)

Conceptual: `OrganizationPricingPolicy`, `EstimatePricingSnapshot`, pricing-application audit. **Not in schema today.**

## Referenced data

- `organizations`
- `project_commercial_contexts` (posture/risk as context, not silent multipliers)
- `estimate_versions` / line extended costs
- Labour Engine **direct labour cost** (consume only, when wired)
- FG-006 historical commercial facts (read-only evidence)

## Prohibited responsibilities

- Owning historical source workbooks or rewriting ingestion facts
- Changing production rates, man-hours, or direct labour cost rates
- Implementing four-output documents, QuickBooks API, or contracts
- Setting ORG-APPROVED policy via AI
- Cross-organization pooling of private economics
- Recalculating locked/accepted commercial records

## Current implementation

**None.** Estimating still computes sell price via line markup + overhead + compounding profit + tax. Pricing Posture and Execution Risk do not enter that math. Labour snapshots are not wired into sell price.

## Invariants (architecture)

- 15% true gross margin ≠ 15% markup
- Direct Cost, contingency source/visibility/pricing treatment, margin, markup, overhead, profit, tax, allowance, discount, Pricing Posture, and Execution Risk remain distinct
- Snapshots do not float when org policy later changes
- Tax is downstream of pre-tax selling price unless a future org/legal policy proves otherwise

## Open decisions

- Exact additive schema (minimum durable set at implementation)
- Whether V1 seeds ORG-001 true-GM policy as data (still org-scoped)
- ORG-001 contingency visibility and pricing treatment (human-approved org policy; not hard-coded from historical examples)

## Relevant tests

None yet. Future: dedicated pricing-engine suite plus `tests/test_estimate_builder.py`, `tests/test_historical_ingestion.py`, `tests/test_labour_engine.py`, full suite.

## Relevant ADRs

- [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**
- [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted**

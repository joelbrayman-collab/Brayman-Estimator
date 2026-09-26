# ADR-054 — Calculation Result Review and Estimate Mapping

| Field | Value |
|-----------|--------|
| Title | ADR-054: Calculation Result Review and Estimate Mapping |
| Status | **Accepted** |
| Date | 2026-09-26 |
| Related | [calculation-engine-result-contract-v1.md](../architecture/calculation-engine-result-contract-v1.md) · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) |

**Subsequent status (2026-09-26 entry experience):** The decision is unchanged. The ordinary estimate page explains Add from calculation and does not ask for a calculation file. Test ingestion stays on a separate page. Hosted validation Alembic is `j0e1f2a3b4c5`. The Mac primary remains `h8c9d0e1f2a3`. No calculator formula was added.

## Context

Contract V1 is pinned. A calculated quantity must not become an estimate line by itself. Takeoff insertion is the closest confirmation pattern, and it cannot hold an unreviewed quantity: it requires a takeoff package and an estimate line.

## Decision

Estimating owns a separate review record for a valid Contract V1 result.

1. An invalid result is rejected. Nothing from it is stored.
2. A valid result is frozen with its fingerprint. Company ids and prices stay on the Platform record, not inside that frozen result.
3. Each final quantity stays visible until a person confirms a compatible Cost Item or Assembly, or leaves it unresolved.
4. Confirmation uses the existing cost-item and assembly line insertion. The estimate line waste percent is set to zero because the contract quantity is already final.
5. A labour quantity, or a Labour-category cost item, is not turned into an estimate line. Labour mapping stays deferred.
6. A later result is a new review. It does not rewrite an accepted line. A locked estimate version is not edited.
7. There is no Website call, no public API, and no calculator formula in this decision.

## Alternatives Considered

- Extend `TakeoffEstimateInsertion` — rejected. That row requires a takeoff package and a line, so an unresolved quantity cannot wait there.
- Auto-insert on exact code match — rejected. A suggestion may be shown. It is not accepted until the person confirms.

## Consequences

The contractor can add a reviewed quantity to an estimate. Unmapped quantities remain visible. Labour and unit conversion stay out of this step. Hosted and Mac databases do not receive the tables until a later authorized migration.

## Module Ownership Impact

Estimating owns the intake, the quantity review, and the acceptance history. Costs and pricing stay the company cost source. The pricing engine is not changed. Labour is not started.

## Data Ownership Impact

`calculation_result_intakes` freezes the result. `calculation_quantity_reviews` holds the open, confirmed, or labour-deferred quantity. `calculation_mapping_acceptances` is append-only. Estimate lines remain estimate lines.

## Migration Impact

Required. Additive revision `j0e1f2a3b4c5`. Not live-migrated from the implementation that added it.

## Testing Impact

`tests/test_calculation_estimate_mapping.py` and the existing Contract V1 fixture tests.

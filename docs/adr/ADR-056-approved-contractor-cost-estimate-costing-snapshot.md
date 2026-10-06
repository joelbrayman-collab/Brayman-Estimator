# ADR-056 — Approved Contractor Cost into the Estimate Costing Snapshot

| Field | Value |
|-------|--------|
| Title | ADR-056: Approved Contractor Cost Consumption into the Existing Estimate Costing Snapshot |
| Status | **Accepted** |
| Date | 2026-10-06 |
| Related | [ADR-008](ADR-008-supplier-price-snapshotting.md) **Proposed** · [ADR-036](ADR-036-material-commercial-evidence-and-supplier-mapping.md) **Accepted** · [ADR-044](ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** · [ADR-046](ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) **Accepted** |

## Context

[ADR-008](ADR-008-supplier-price-snapshotting.md) remains **Proposed**. It describes a general price snapshot when an estimate or purchase-order line adopts a supplier price. [ADR-036](ADR-036-material-commercial-evidence-and-supplier-mapping.md) Decision 8 and [ADR-046](ADR-046-supplier-neutral-material-requirement-and-supplier-mapping-boundary.md) Decision L require an accepted successor before supplier price becomes estimate working cost.

The repository now has four separate records: supplier price evidence, effective contractor cost, contractor cost approval, and the estimate costing snapshot. [ADR-044](ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) already owns that snapshot. A second costing system would bypass it.

## Decision

This ADR is the successor for one path only. It does **not** accept ADR-008 and does **not** change ADR-008's proposed wording.

1. An existing `EstimateLineItem` may consume one `ContractorCostApproval` whose status is `APPROVED`.
2. Consumption freezes that cost through the existing `EstimateCostingSnapshot` / `EstimateCostingSnapshotLine`. Estimating still owns the snapshot. Pricing still consumes the snapshot and does not select the cost.
3. The snapshot line cites `contractor_cost_approval_id`. That citation is the provenance chain to supplier price evidence, supplier product, supplier, and canonical material. The supplier catalogue is not copied onto the snapshot.
4. The frozen `unit_cost` is the approved amount. A later supplier price or a later contractor approval does not rewrite that snapshot line.
5. The same approval may be cited by more than one estimate. Each estimate freezes the amount it used.
6. `PENDING` and `REJECTED` approvals are refused. A missing approval is refused. Consumption does not create or approve a contractor cost.
7. The estimate line must already exist. Consumption does not create an `EstimateLineItem`.
8. The line matches the approval only through `CostItem.canonical_material_id`. Description, SKU, and free text are not a match. No governed material link means refuse.
9. The approval unit token must be the same unit token as the estimate line. This ADR authorizes no unit conversion.
10. The approval currency must match the organization currency.
11. Only `CONTRACTOR_CONFIRMED_PRICE` can be cited, because a public list price cannot be an approved contractor cost.
12. The caller names the approval. The operation does not choose a supplier and does not choose the lowest amount.
13. Supplier price evidence and the contractor approval row stay unchanged.
14. This ADR does not authorize a pricing-policy engine, a discount hierarchy, a purchase order, or automatic estimate-line creation.

[ADR-044](ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) Decision M remains: ordinary costing approval still does not require supplier evidence. This path is an additional citation when an approved contractor cost is explicitly consumed.

## Alternatives Considered

- **Accept ADR-008 as written** — Rejected. ADR-008 also covers purchase orders and a general catalogue snapshot. This slice is narrower.
- **Store the supplier catalogue on the snapshot line** — Rejected. The approval citation is enough provenance.
- **A second costing snapshot model** — Rejected. ADR-044 already owns the freeze.
- **Match the line by description or SKU** — Rejected. Canonical material on the cost item is the governed identity.

## Consequences

Positive: an October estimate can stay at an approved $100 after a November approval of $95. Negative: a line with no canonical material cannot use this path until that link exists.

## Module Ownership Impact

Estimating owns the consumption and the snapshot. Supplier Catalogue still owns price evidence. The contractor cost approval remains Estimating-owned and reusable.

## Data Ownership Impact

Additive nullable `contractor_cost_approval_id` on `estimate_line_items` and `estimate_costing_snapshot_lines`. Existing snapshot rows stay valid with a null citation.

## Migration Impact

Revision `q7d8e9f0a1b2` revises `p6c7d8e9f0a1`. It is not applied to the Mac primary or the hosted database by this slice.

## Testing Impact

`tests/test_approved_contractor_cost_snapshot.py`.

## Documentation Impact

Existing supplier, costing, checklist, roadmap, and module authorities. ADR-008 stays Proposed.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Authorized by the 6 Oct 2026 architect prompt for this bridge | 2026-10-06 |
| ChatGPT review | ADR-008 successor limited to approved contractor cost into the existing snapshot | 2026-10-06 |
| Cursor implementation note | Accepted with the product bridge in the same slice. ADR-008 remains Proposed. | 2026-10-06 |

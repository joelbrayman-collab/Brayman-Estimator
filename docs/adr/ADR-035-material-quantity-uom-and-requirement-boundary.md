# ADR-035 — Material Quantity, UOM, and Requirement Boundary

| Field | Value |
|-------|--------|
| Title | ADR-035: Material Quantity, UOM, and Requirement Boundary |
| Status | **Accepted** (governance / architecture only; **not implemented**) |
| Date | 2026-08-30 |
| Related | [material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md) · [ADR-034](ADR-034-canonical-material-identity-and-ownership.md) · [ADR-036](ADR-036-material-commercial-evidence-and-supplier-mapping.md) · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) · [ADR-007](ADR-007-plan-and-estimate-version-ownership.md) · [ADR-031](ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) · [FG-010](../feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) |

## Context

Today:

- `TakeoffPackageItem` stores quantity, citation, and `element_type` — not CostItem or SKU (`app/plan_intelligence/models.py`).
- `AssemblyItem` has `quantity` and `waste_percent`; adding an Assembly to an estimate creates **one** rolled-up `EstimateLineItem`.
- `CostItem.unit` is a free-text string, not a controlled requirement UOM.
- Phase D (approved take-off → `EstimateVersion`) is **not started / not authorized**. ADR-006 forbids auto-insert; ADR-007 forbids plans and estimates overwriting each other’s history.

Without a quantity/UOM boundary, supplier pack conversion would be confused with waste, and fulfillment would be forced to reverse-engineer components from a rolled-up commercial line.

This ADR does **not** authorize MaterialRequirement implementation, Phase D, schema, or product code.

## Decision

### 1. Canonical requirement UOM ≠ supplier sales/pack UOM

Canonical **requirement** quantity and UOM stay distinct from **supplier sales / pack** UOM.

Example:

```text
450 LF required
→ supplier mapping
→ 12-ft pieces
→ governed conversion / rounding
→ supplier quantity
```

Conversion and pack rounding belong to the future **material ↔ supplier-product mapping** ([ADR-036](ADR-036-material-commercial-evidence-and-supplier-mapping.md)). They do **not** belong on Canonical Material.

Do not treat current free-text `CostItem.unit` as the final canonical UOM system.

### 2. Pack rounding is not waste

Pack rounding is a fulfillment conversion. It is **not** waste.

Waste remains, in conceptual precedence:

1. estimate-specific override (`EstimateLineItem.waste_percent`)
2. Assembly component (`AssemblyItem.waste_percent`)
3. future organization material-waste standard
4. none

**No universal waste factor belongs on Canonical Material.** Actual waste is future ORG-ACTUAL evidence, not identity.

### 3. Rolled-up commercial line vs exploded fulfillment

**Commercial estimate presentation** may remain one rolled-up Assembly line.

**Supplier / fulfillment** must be capable of using **exploded** material quantities (studs, plates, sheathing, insulation, and so on).

Do **not** require fulfillment to reconstruct components from a single rolled-up `EstimateLineItem`.

### 4. TakeoffPackageItem stays quantity/citation/element

`TakeoffPackageItem` remains quantity, citation, and `element_type`.

It does **not** own supplier SKU, CostItem, or supplier price. Plan Intelligence stays supplier-neutral. AI does not choose the commercial product ([ADR-006](ADR-006-human-approval-before-estimate-insertion.md), [FG-010](../feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md)).

### 5. MaterialRequirement is anticipated, not authorized

A future **MaterialRequirement** is architecturally anticipated as:

- project-scoped
- reviewed
- supplier-neutral
- canonical material + quantity + UOM
- specification / substitution context
- source / citation / provenance

**Accepting this ADR does not authorize implementing MaterialRequirement.** It requires separate Phase D / governance review.

### 6. Phase D remains separately governed

Phase D remains **NOT AUTHORIZED**.

**Material Catalogue identity ([ADR-034](ADR-034-canonical-material-identity-and-ownership.md)) must precede Phase D implementation.**

When separately gated, Phase D should map approved take-off through explicit human review toward Assembly, canonical material / future MaterialRequirement, and/or structured estimate lines — without automatically selecting a supplier SKU ([ADR-006](ADR-006-human-approval-before-estimate-insertion.md), [ADR-007](ADR-007-plan-and-estimate-version-ownership.md)).

## Alternatives Considered

- **Store pack UOM on Canonical Material** — Rejected: pack is supplier-specific.
- **Treat pack rounding as waste** — Rejected: different authority and purpose.
- **Put waste on Canonical Material** — Rejected: waste is org/project/assembly context.
- **Explode every Assembly onto the customer estimate** — Rejected as a *requirement*; commercial presentation may stay rolled up. Fulfillment still needs explosion.
- **Implement MaterialRequirement in the identity Feature Gate** — Rejected: premature; Phase D still unauthorized.
- **Implement Phase D before identity** — Rejected: would trap supplier-useful quantities in estimate-only structures.

## Consequences

Positive: fulfillment and estimating can share a requirement quantity without sharing a pack or a waste factor.

Negative: mapping conversion tables are future work; Assemblies will need a later explosion path without changing today’s commercial UX.

## Module Ownership Impact

| Concern | Owner |
|---------|--------|
| Canonical requirement UOM vocabulary | Material Catalogue identity ([ADR-034](ADR-034-canonical-material-identity-and-ownership.md)) |
| Assembly formulas and component waste | Estimating |
| Take-off quantity / citation | Plan Intelligence |
| Pack conversion | Future mapping / Supplier Catalogue |
| MaterialRequirement | **Not owned yet** — future, separately gated |

## Data Ownership Impact

Take-off packages remain Plan Intelligence. Estimate lines remain Estimating snapshots. Canonical UOM is platform vocabulary. Conversion factors are mapping data, not identity.

## Migration Impact

**Deferred.** No schema in this pass. Future additive conversion/mapping tables only after a Feature Gate that includes mapping (not identity V1).

## Testing Impact

None this pass. Future tests must prove pack rounding ≠ waste, and that take-off items still have no CostItem/SKU FK.

## Documentation Impact

[material-catalogue-architecture.md](../architecture/material-catalogue-architecture.md); Plan Intelligence / Estimating module notes; ADR index.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Approved via Material Catalogue ADR governance prompt | 2026-08-30 |
| ChatGPT review | Architecture report + locked decisions | 2026-08-30 |
| Cursor implementation note | Docs/ADR only. MaterialRequirement and Phase D **not** authorized. | 2026-08-30 |

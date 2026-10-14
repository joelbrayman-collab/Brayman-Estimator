# ADR-057 — Takeoff catalogue categories and takeoff-derived canonical identities

| Field | Value |
|-------|--------|
| Title | ADR-057: Takeoff catalogue categories and takeoff-derived canonical identities |
| Status | **Proposed** — needs Joel's approval before revision `u1b2c3d4e5f6` is applied to any office database |
| Date | 2026-10-13 |
| Amends | ADR-034 (canonical material identity), FG-014 category scope |
| Migration | `migrations/versions/u1b2c3d4e5f6_takeoff_material_catalogue_categories.py` |

## Context

The pool-deck takeoff prices pressure-treated lumber, PVC/composite decking and fascia, black aluminum guards and stair rails, a pool gate, helical piers, structural connectors, and fasteners. The canonical catalogue accepted only `DIMENSIONAL_LUMBER`, `SHEET_GOODS`, and `CONCRETE`, and its lumber identities are SPF. A supplier price for any of these materials could not reach contractor cost approval.

## Decision

1. Seven categories join the catalogue: `DECKING`, `FASCIA`, `RAILING`, `GATE`, `FOUNDATION`, `CONNECTOR`, `FASTENER`. The package unit `PKG` joins the canonical and requirement units. Pressure-treated lumber stays in `DIMENSIONAL_LUMBER` as its own identities (`CAL-PT-<size>-<length>`), never mapped onto the SPF seeds.
2. No identity is seeded by the migration. Takeoff identities are derived deterministically from a takeoff line (`app/services/deck_takeoff/catalogue.py`) and created one at a time, only when a person records supplier evidence for that line. An existing identity is reused unchanged.
3. An identity states only what the takeoff already states: category, unit, stock length, product type (cellular PVC or capped composite), retained structural size and material, gate clear opening, package count. It holds no manufacturer specification, SKU, or price.
4. A line whose identity needs a missing fact (for example a deck board with no product type) gets no identity. Its supplier price stays on the supplier response record.

## Alternatives Considered

- Seed a fixed list of finish identities — rejected: stock lengths and package sizes are manufacturer facts that are not known yet.
- Map pressure-treated lumber onto the SPF seeds — rejected: a different material.
- Keep finish prices outside the catalogue — rejected: they could never reach the cost approval gate.

## Consequences

Positive: every takeoff material can reach supplier evidence, contractor cost review, approval, and estimate costing through the existing gates. Negative: the catalogue grows from recorded evidence rather than a reviewed seed list; each created identity is visible in the Material Catalogue and attributable to the person who recorded it.

## Module Ownership Impact

Material Catalogue keeps ownership of identities. Deck Takeoff proposes identities; it does not edit existing ones.

## Data Ownership Impact

Canonical identities stay platform-shared and supplier-neutral. Supplier products, evidence, maps, and approvals keep their FG-029 / ADR-046 / ADR-056 owners.

## Rollback

See [../operations/takeoff-catalogue-migration-rollback.md](../operations/takeoff-catalogue-migration-rollback.md). Downgrade refuses while any takeoff identity or `PKG` requirement exists; the rollback for such a database is the pre-migration backup.

## Approval

| Role | Name | Decision | Date |
|------|------|----------|------|
| Product owner | Joel | Pending | |

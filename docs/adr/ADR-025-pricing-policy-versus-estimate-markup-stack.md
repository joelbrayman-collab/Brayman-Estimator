# ADR-025 — Pricing Policy versus Estimate Markup Stack

| Field | Value |
|-------|--------|
| Title | ADR-025: Gross-Margin Policy versus Existing Estimate Markup Stack |
| Status | **Proposed** |
| Date | 2026-08-28 |
| Related | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [pricing-policy.md](../pricing-policy.md) · [modules/estimating.md](../modules/estimating.md) |

## Context

CAR-001 verified a discrepancy. **Do not treat this ADR as choosing a migration.**

**Current estimate code** (`app/services/estimate_builder.py` and related models):

- Line sell price uses **markup percent** on extended cost: `extended_cost * (1 + markup_percent/100)`
- Version totals then apply **overhead percent** and **profit percent** (and tax percent)

**Governing pricing policy** (`docs/pricing-policy.md`, 2026-08-25):

- Labour direct cost reference: **$65 CAD / man-hour**
- Target gross margin: **15%**
- `Selling Price = Direct Cost / (1 - Gross Margin)` = **Direct Cost / 0.85**
- 15% gross margin is **not** a 15% markup

These are **not mathematically equivalent**. The estimate builder is **preserved** until this ADR is accepted and a Feature Gate authorizes calculation changes.

## Decision

*(Proposed — no calculation change authorized.)*

1. **Record** the discrepancy as a governed open decision.
2. **Do not** change estimate calculation code in CAR-001.
3. **Do not** silently choose: replace markup stack, dual-mode, or “treat overhead+profit as margin.”
4. Preserve the existing estimate builder until Joel accepts a migration method **and** a Feature Gate / Cursor prompt authorizes implementation.
5. `$65/hr` and 15% gross-margin **policy text** remains authoritative for governed outputs when those outputs exist; code application remains Future until this ADR is accepted.

## Alternatives Considered (not selected)

- **Replace markup/overhead/profit with gross-margin formula only** — Not selected.
- **Keep markup stack; document policy as aspirational** — Not selected (policy is already governing).
- **Dual-mode / translation layer** — Not selected.
- **Map 15% margin onto existing percent fields** — Not selected (would be incorrect if done as 15% markup).

## Consequences

Until accepted, internal totals may not match the governing selling-price formula. UAT reference case (3415 Roger Stevens) must not be treated as implemented in-app pricing.

## Module Ownership Impact

Estimating continues to own calculation code. Pricing policy remains a governing document, not a module.

## Data Ownership Impact

None until a migration is approved. Historical estimate versions must not be silently recalculated.

## Migration Impact

**Deferred.** Any future change needs review (Rule 7 if schema; Feature Gate either way). None in CAR-001.

## Testing Impact

None in CAR-001. A future Feature Gate must require tests that the chosen formula matches `pricing-policy.md` and does not mutate locked versions unexpectedly.

## Documentation Impact

CAR-001; pricing-policy.md cross-link; estimating module planned-capabilities note.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | Discrepancy recorded from CAR-001 | 2026-08-28 |
| Cursor implementation note | Proposed only; no code changes | 2026-08-28 |

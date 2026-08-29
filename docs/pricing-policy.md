# Pricing Policy — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **Governing** (current reference rule) |
| Updated | 2026-08-29 |
| Authority | Joel-approved product policy — not invented by implementation |

## Purpose

Record Brayman's **current** pricing terminology and formulas so estimates, internal breakdowns, customer-facing outputs, and QuickBooks exports reconcile consistently. Future changes to rates, margin methodology, category rules, contingency, or tax treatment are **governed pricing-policy changes** requiring explicit approval — not silent code or spreadsheet drift.

## Current reference rule (2026-08-25)

| Parameter | Value |
|-----------|--------|
| Labour direct cost reference | **$65 CAD per man-hour** |
| Current target gross margin | **15%** |

### Gross margin formula (not markup)

```text
Selling Price = Direct Cost / (1 - Gross Margin)
```

At 15% gross margin:

```text
Selling Price = Direct Cost / 0.85
```

**Important:** 15% gross margin is **distinct from** a 15% markup on cost.

**CAR-001 / FG-009 discrepancy (recorded; architecture approved, not implemented):** Current estimate builder code uses line **markup percent** plus version **overhead percent** and **profit percent**. That stack is **not mathematically equivalent** to this gross-margin formula. See [ADR-025](adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) (**Accepted** — named methods; do not map 15% GM onto 15% markup). [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) is **APPROVED FOR IMPLEMENTATION** — not implemented. Do not change calculation code until a separate FG-009 implementation prompt is issued. LEARN must not silently rewrite this policy ([ADR-024](adr/ADR-024-learn-recommendation-boundary.md)).

This document records **ORG-001** (Brayman Construction) policy. It is not the universal CalibAi pricing model.

### Tax (HST)

HST is **separate** from the pre-tax selling price. Apply HST after pre-tax selling price according to the applicable tax treatment for the output (internal vs customer-facing vs QuickBooks).

## Placeholder and pending pricing

Missing supplier or subcontract pricing must remain explicitly labeled as one of:

- **TBD**
- **ALLOWANCE**
- **PLACEHOLDER**

A placeholder may **never** silently become final pricing. Implementation and UAT must treat unresolved placeholders as non-final.

## Governance

| Change type | Requirement |
|-------------|-------------|
| Labour rate change | Joel approval; update this document; regenerate affected outputs from authoritative estimate record |
| Margin / markup methodology change | Joel approval; update this document |
| Category-specific margin rules | Feature Gate + Joel approval |
| Contingency rules | Feature Gate + Joel approval |
| Tax treatment change | Joel approval; may require legal/commercial review |

## Related outputs

All governed project outputs derive from one [authoritative project/estimate record](architecture/project-document-package.md#authoritative-estimate-record). Pricing policy applies when translating direct costs into selling prices across:

1. Internal Detailed Cost Breakdown
2. Customer-Facing Estimate
3. QuickBooks Estimate Output
4. Ontario Construction Contract (approved price only)

## Related documents

- [architecture/project-document-package.md](architecture/project-document-package.md)
- [architecture/organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md)
- [feature-gates/FG-009-organization-calibrated-pricing-engine.md](feature-gates/FG-009-organization-calibrated-pricing-engine.md)
- [modules/estimating.md](modules/estimating.md)
- [modules/pricing-engine.md](modules/pricing-engine.md)
- [testing/uat-reference-cases.md](testing/uat-reference-cases.md)

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

**CAR-001 / FG-009 (implementation state):** Named methods are implemented and live-migrated. Versions **without** an `EstimatePricingSnapshot` still use the live markup/overhead/profit stack (`COST_PLUS_MARKUP_STACK`). Versions **with** a snapshot use the frozen named method. FG-009-aware Change Orders apply the inherited method. ORG-001 optional overhead/profit/contingency layers seed as `UNSPECIFIED` until separately governed (not recorded as org-approved `NOT_APPLIED`). 15% true GM is not mapped onto 15% markup. See [ADR-025](adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) (**Accepted**) and [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) (**IMPLEMENTED / VERIFIED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**). LEARN must not silently rewrite this policy ([ADR-024](adr/ADR-024-learn-recommendation-boundary.md)).

This document records **ORG-001** (Brayman Construction) policy. It is not the universal CalibAi pricing model.

### Project Gross Margin (MONITOR — governed, not implemented)

The initial authoritative CalibAi **project** profitability metric is **PROJECT GROSS MARGIN** ([ADR-021](adr/ADR-021-monitor-commercial-baseline.md) **Accepted**). **NET PROFIT** is not the official project metric until overhead / burden / G&A allocation is separately governed.

Tax remains **outside** gross-margin arithmetic. MONITOR (not implemented) must compare **pre-tax** estimated Direct Cost and pre-tax selling price / authorized revenue. Do not use tax-collected amounts as revenue or margin.

This is distinct from the live-estimate method above: estimate selling price uses the named pricing method on Direct Cost. Project Gross Margin later compares a **frozen composed baseline** (locked `EstimateVersion` + `EstimatePricingSnapshot` when present + Accepted Proposal + approved Change Order deltas) to verified actual Direct Cost. Draft estimates and Draft Proposal restacks are not the committed baseline.

QuickBooks is not required for Project Gross Margin. Industry benchmarks are not inputs to it.

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
- [adr/ADR-021-monitor-commercial-baseline.md](adr/ADR-021-monitor-commercial-baseline.md)
- [testing/uat-reference-cases.md](testing/uat-reference-cases.md)

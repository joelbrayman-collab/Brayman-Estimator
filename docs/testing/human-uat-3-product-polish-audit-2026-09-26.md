# Human UAT 3 — product and polish reconciliation

| Attribute | Value |
|-----------|--------|
| Date | 2026-09-26 |
| Status | **AUDIT / DESIGN ONLY / NOT IMPLEMENTED** |
| Baseline | `003469f852d363d59c9459dd985abe0dd3f63f97` live as `dep-darsccfpn0mc73drlubg` |
| Waves C–F | **PAUSED.** Wave C was not started. |

No product code in this record.

## Joel’s input

The office is cleaner, and still looks unfinished. Seven workflow documents should appear from a register, not from hand-written cards. Every estimate that can become a proposal needs estimate-specific commercial control, at least margin and labour, where current law allows it. Brand should leave the daily menu. The company needs My Subcontractors. A job should say which work is self-performed and which is subcontracted, and subcontracted work should be able to request a price.

## The seven documents

Repository authority is FG-022, register `docs/testing/reusable-approved-document-template-family-v1-register.md`. Exactly seven masters. They live outside Git. There is no runtime document registry. The project page does not list them.

| # | Name | Audience | Wired in the app |
|---|------|----------|------------------|
| 01 | Labour Calculation Detail | Internal | No |
| 02 | Internal Detailed Cost Breakdown | Internal | HTML internal breakdown exists. It is not this master. |
| 03 | Customer Facing Estimate | Customer | Proposal/estimate PDF renderers exist. They are not this master. |
| 04 | QuickBooks Estimate Entry | Internal reference | QuickBooks-ready pages exist. They are not this master. |
| 05 | Ontario Construction Contract | Draft only. Not for signature. | Yes. `app/services/contract_generation.py` merges this master. |
| 06 | Door / Window / Skylight Schedule | Customer | No |
| 07 | Client Construction Proposal | Customer | Proposal PDF exists. It is not this master. |

A documents page should loop a small in-code family register. Adding a family adds a row. It should not add a hand-written card. Family 05 must keep its not-for-signature labels.

## Pricing and labour

Company pricing is an approved policy (`OrganizationPricingPolicy`) with `TRUE_GROSS_MARGIN` and a target margin. Applying it writes `EstimatePricingSnapshot` on that estimate version, including the margin and the customer total. A proposal copies that snapshot. A later company-policy change does not rewrite the snapshot or the proposal.

An estimate can already point at a different approved company policy (`pricing_policy_override_id`) with a reason. The version screen calls that an optional override and lists policy codes. It does not let the estimator type a margin for one job. A typed margin is not current law.

Labour snapshots (`EstimateLabourSnapshot`) store the resolved hourly rate and production speed for a version. The service can take an override with a reason. The estimate screen does not offer that. Creating a snapshot is not part of the ordinary estimate form. Existing snapshots do not change when the company rate later changes.

## Brand, subcontractors, scope, RFQ

The header gear already opens Brand profile and is labeled Settings. Brand is also in the Company menu. Daily navigation does not need both. Keep the header control. Remove the menu item.

`Subcontractor` already exists, organization-owned, with code, legal name, and active/inactive. It is created inside Scope Delivery, not as a company directory. It has no email, phone, or trade. `Supplier` is a building-supply dealer, not this directory. Do not merge them.

Self-performed versus subcontracted is stored per estimate line (`EstimateScopeDelivery.labour_delivery`: INTERNAL or SUBCONTRACT). New Project does not ask. Quote evidence can be typed onto a subcontract line and one quote selected. That selection does not by itself change the price. There is no outbound RFQ, no plan attachment on the request, and no subcontractor email.

Smallest later RFQ: email a request, then record the reply as the quote evidence that already exists. Do not build a portal in V1. Markup still runs through the estimate pricing snapshot.

## Polish

Home is the strongest office page. Past jobs, plan measurement, and the project record are the weakest. The repeated failure is one-off layout: inline styles, raw tables, and equal buttons. The existing classes (`page-heading`, `form-panel`, `data-table`, `empty-state`, `home-counts`, `projects-row`) are enough to become the system. Do not invent a second design language.

## Paused waves

Waves C–F stay paused. The next product change is not authorized by this audit.

# Project Document Package — Architecture

| Attribute | Value |
|-----------|--------|
| Status | **Intended / governing product architecture** (not fully implemented) |
| Updated | 2026-08-25 |
| Implementation | **None authorized** in August 2026 governance reconciliation |

## Purpose

Define the governed **core document package** for Brayman project workflows: one authoritative estimate record and four derived outputs that must stay consistent when governed inputs change.

## Authoritative estimate record

The Brayman Estimator must maintain **one authoritative project/estimate record** per governed project workflow.

| Requirement | Rule |
|-------------|------|
| Single source | All project outputs derive from the same authoritative record |
| Propagation | A governed input change must propagate consistently to affected outputs |
| Versioning | Approved commercial states use explicit versioning/supersession — no silent overwrite ([Constitution Article 5](platform-constitution.md)) |
| Placeholders | TBD / ALLOWANCE / PLACEHOLDER remain explicit until resolved ([pricing policy](../pricing-policy.md)) |

**Current implementation note:** Estimate versions, proposal snapshots, and PDF output exist today. The full four-output package, Ontario contract generation, warranty attachment, and QuickBooks export pipeline are **Future / not implemented**.

## Core document package (four outputs)

Every governed project workflow must support these four outputs:

### 1. Internal Detailed Cost Breakdown

**Audience:** Brayman internal only — **must not** be customer-facing.

**Contains (when implemented):**

- Direct materials
- Supplier quotations
- Subcontract / package direct costs
- Labour hours by task
- Direct labour cost
- Allowances / placeholders
- Waste / cleanup / disposal
- Gross-margin calculations
- Internal reconciliation
- Internal estimating notes

### 2. Customer-Facing Estimate

**Audience:** Customer.

**Contains (when implemented):**

- Detailed scope
- Customer-facing line items
- Price
- Appropriate allowances
- Exclusions
- Tax treatment
- Commercial notes

**Must NOT expose** (unless explicitly authorized):

- Supplier costs
- Internal labour cost
- Gross margin

### 3. QuickBooks Estimate Output

**Audience:** QuickBooks workflow (customer-facing estimate representation).

A customer-facing QuickBooks-ready representation of the **approved** estimate.

See [quickbooks-integration.md](quickbooks-integration.md) for the governed pipeline boundary. **Do not implement QuickBooks API** without Feature Gate and Joel approval.

### 4. Ontario Construction Contract

**Audience:** Customer signature package.

Generated **only from an APPROVED estimate**.

**Must preserve:**

- Project identity
- Exact approved estimate / version provenance
- Approved scope
- Price
- Allowances
- Exclusions
- Payment / commercial terms
- Approved change-order treatment

**Warranty:** The Ontario construction contract must be accompanied by the applicable governed **warranty document** as an attachment or schedule. See [legal-content-and-templates.md](../governance/legal-content-and-templates.md).

**Contract / warranty progression states** (governed lifecycle — not implemented):

| State | Meaning |
|-------|---------|
| PROPOSED | Draft under internal review |
| APPROVED | Authorized for generation from approved estimate |
| GENERATED | Document produced from approved source |
| VERIFIED | Human verified against approved estimate/version |
| SENT FOR SIGNATURE | Released to signature workflow |
| SIGNED | Executed |
| SUPERSEDED | Replaced by a later approved version |

**No contract is final merely because it was generated.**

## Input change propagation

When a governed field changes in the authoritative record (scope, price, allowance, exclusion, tax treatment, commercial term):

1. Identify affected outputs
2. Mark downstream outputs stale or require regeneration
3. Do not leave customer-facing, QuickBooks, or contract outputs inconsistent with the authoritative record

## Module ownership (intended)

| Concern | Owning module / doc |
|---------|---------------------|
| Authoritative estimate structure | [Estimating](../modules/estimating.md) |
| Customer-facing estimate presentation | Proposals (today: proposal snapshot/PDF; future: governed customer estimate output) |
| Internal detailed breakdown | Estimating / future reporting boundary — Feature Gate required |
| QuickBooks export | Future integration boundary — [quickbooks-integration.md](quickbooks-integration.md) |
| Ontario contract + warranty package | Governed templates — [legal-content-and-templates.md](../governance/legal-content-and-templates.md) |

## Related

- [pricing-policy.md](../pricing-policy.md)
- [quickbooks-integration.md](quickbooks-integration.md)
- [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md)
- [testing/uat-reference-cases.md](../testing/uat-reference-cases.md)
- [platform-vision.md](../platform-vision.md)

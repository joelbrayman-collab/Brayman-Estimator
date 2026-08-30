# Project Document Package — Architecture

| Attribute | Value |
|-----------|--------|
| Status | **Intended / governing product architecture** (not fully implemented) |
| Updated | 2026-08-30 |
| Implementation | **FG-012** authorizes outputs **1 and 2 only**. **CLOSED / OPERATIONAL FOR UAT** (2026-08-30). Outputs 3 and 4 remain Future. |

## Purpose

Define the governed **core document package** for Brayman project workflows: one authoritative estimate record and four derived outputs that must stay consistent when governed inputs change.

## Authoritative estimate record

The Brayman Estimator must maintain **one authoritative project/estimate record** per governed project workflow.

| Requirement | Rule |
|-------------|------|
| Single source | All project outputs derive from the same authoritative record |
| Propagation | A governed input change must propagate consistently to affected outputs |
| Versioning | Approved commercial states use explicit versioning/supersession — no silent overwrite ([Constitution Article 5](../platform-constitution.md)) |
| Placeholders | TBD / ALLOWANCE / PLACEHOLDER remain explicit until resolved ([pricing policy](../pricing-policy.md)) |

**Current implementation note:** Estimate versions, proposal snapshots, and PDF output exist today. [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) (**CLOSED / OPERATIONAL FOR UAT**) governs consistency of outputs **1 and 2** from the existing `Estimate` / `EstimateVersion` / lines / `EstimatePricingSnapshot` (when present). Internal breakdown: `GET /estimates/<id>/versions/<version_id>/internal-breakdown`. The existing **Proposal** preview/PDF **is** the customer-facing estimate. Ontario contract generation, warranty attachment, and QuickBooks export remain **Future / not implemented**. Do not build a four-output renderer under a later gate without authorization.

**Source-contract principle:** every governed output must identify and derive from the authoritative `EstimateVersion` and, when present, its `EstimatePricingSnapshot`. Historical customer documents must not silently float with later estimate edits. Later MONITOR / Project Gross Margin uses that same frozen pin plus the Accepted Proposal and approved Change Order deltas ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted**); MONITOR is **not implemented**.

## Core document package (four outputs)

Every governed project workflow must support these four outputs:

### 1. Internal Detailed Cost Breakdown

**Audience:** Brayman internal only — **must not** be customer-facing.

**FG-012 (CLOSED / OPERATIONAL FOR UAT):** Estimating-owned office view/document of one `EstimateVersion` from stored facts. Direct Cost = Σ line `extended_cost`. Labour Engine snapshots, if shown, are labeled **not included in selling-price basis**. Do not invent missing supplier/subcontract prices. Machine-enforced TBD/PLACEHOLDER state is **not** in FG-012.

**Contains (implemented under FG-012, from stored facts only):**

- Estimate / version / snapshot identity
- Sections and lines (quantity, unit, unit cost, waste, extended/direct cost)
- Allowance identification
- CostItem category where available
- Direct Cost reconciliation
- Authoritative pricing method and stored GM/markup treatment
- Pre-tax selling price, tax, customer total
- Optional labour snapshot evidence (separate; not in basis)

Full four-output “catalogue” items such as supplier quotations remain **Future** unless already stored.

### 2. Customer-Facing Estimate

**Audience:** Customer.

**Joel / FG-012:** the existing Proposal snapshot + preview + PDF **is** this output. Do not create a separate Customer Estimate entity.

**Contains (FG-012 implemented):**

- Detailed scope / customer-facing line items (selling prices)
- Price reconciling to the source version/snapshot customer total
- Appropriate allowances (labeled)
- Exclusions / commercial notes as already snapshotted
- Tax treatment from stored snapshot/version (no new tax engine)

**Must NOT expose** (unless explicitly authorized):

- Supplier costs / unit cost / extended (direct) cost
- Internal labour cost / Labour Engine snapshot cost
- Gross margin / internal markup
- Internal Overhead / Profit rows on the customer PDF

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

## Additional governed project document (Permit & Approvals Report)

**Status:** Pass 2 report **CLOSED / OPERATIONAL FOR UAT** ([FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md)). Architecture **Accepted** (ADR-037/038/039). [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT** (preliminary profile foundation). Canonical: [permit-and-approvals-report.md](permit-and-approvals-report.md) · [permit-rules-library.md](permit-rules-library.md).

The **Permit & Approvals Report** is a **core project document** (advisory preflight). It is **not** a fifth estimate-derived commercial output, **not** a Change Order, and **not** a substitute for the AHJ.

Issued reports are immutable snapshots. Recheck produces a new version ([ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)).

This section does **not** authorize live lookup or external AI. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) implemented the bounded POC. It does **not** change FG-012 outputs 1–2 or authorize outputs 3–4.

## Core package vs transaction-document families (FUTURE / NOT IMPLEMENTED)

**Status:** **FUTURE / NOT IMPLEMENTED.** Requirement pins only.

| Kind | Canonical record |
|------|------------------|
| Core project document / package outputs | This document (outputs 1–4) plus additional pinned documents such as the Permit & Approvals Report |
| Project transaction document families | Repeating per-project documents. Change Orders belong here because a project may have many. Canonical: [change-order-document-family.md](change-order-document-family.md) |

Do **not** force Change Order into a numbered “Document #7”. Do **not** create a second Change Order entity. The existing Change Order business record remains authoritative.

Organization branding for all generated documents (core and transaction families) is pinned on [organization-brand-profile.md](organization-brand-profile.md). Do not create independent logo/header settings per module.

These pins do **not** authorize Brand Profile implementation by themselves. [ADR-040](../adr/ADR-040-organization-brand-profile.md) is **Accepted**. [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) is **APPROVED / IMPLEMENTATION NOT STARTED** and still needs a separate implementation prompt. They do **not** authorize Change Order PDF rewrite or email. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) authorizes a **neutral CalibAi** Permit Report layout without Brand Profile; do **not** add a second Permit-logo system. They do **not** reopen FG-012, FG-014, or FG-015.

## Input change propagation

When a governed field changes in the authoritative record (scope, price, allowance, exclusion, tax treatment, commercial term):

1. Identify affected outputs
2. Mark downstream outputs stale or require regeneration
3. Do not leave customer-facing, QuickBooks, or contract outputs inconsistent with the authoritative record

## Module ownership (intended)

| Concern | Owning module / doc |
|---------|---------------------|
| Authoritative estimate structure | [Estimating](../modules/estimating.md) |
| Customer-facing estimate presentation | **Proposals** — existing proposal snapshot/PDF **is** the customer-facing estimate ([FG-012](../feature-gates/FG-012-estimate-output-consistency.md)) |
| Internal detailed breakdown | **Estimating** — [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** |
| QuickBooks export | Future integration boundary — [quickbooks-integration.md](quickbooks-integration.md) |
| Ontario contract + warranty package | Governed templates — [legal-content-and-templates.md](../governance/legal-content-and-templates.md) |
| Permit & Approvals Report | **CLOSED / OPERATIONAL FOR UAT** ([FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md); [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)) — [permit-and-approvals-report.md](permit-and-approvals-report.md). Bounded Ontario / Ottawa coach-house POC. Not a national library. |
| Organization Brand Profile | **FUTURE / NOT IMPLEMENTED** — [organization-brand-profile.md](organization-brand-profile.md); [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted**; [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) **APPROVED / IMPLEMENTATION NOT STARTED** (single branding source; not implemented; not authorized for product work) |
| Change Order document family | **FUTURE / NOT IMPLEMENTED** pin — [change-order-document-family.md](change-order-document-family.md). Existing Change Order record remains authoritative. Project Controls / Projects. |

## Related

- [feature-gates/FG-012-estimate-output-consistency.md](../feature-gates/FG-012-estimate-output-consistency.md)
- [pricing-policy.md](../pricing-policy.md)
- [quickbooks-integration.md](quickbooks-integration.md)
- [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md)
- [testing/uat-reference-cases.md](../testing/uat-reference-cases.md)
- [permit-and-approvals-report.md](permit-and-approvals-report.md) — **FUTURE / NOT IMPLEMENTED** additional project document (advisory preflight; not outputs 1–4)
- [organization-brand-profile.md](organization-brand-profile.md) — **FUTURE / NOT IMPLEMENTED** Organization Brand Profile
- [change-order-document-family.md](change-order-document-family.md) — **FUTURE / NOT IMPLEMENTED** Change Order transaction-document family (not a numbered core output)
- [platform-vision.md](../platform-vision.md)

# Governed document and drawing output standard

| Attribute | Value |
|-----------|--------|
| Status | Architecture constraint. Recorded 1 Oct 2026. Not a new renderer. |
| Product | CalibraytAI / Brayman |
| Applies to | Every governed issued document and drawing |

## Rule

Every governed CalibraytAI or Brayman document and drawing uses the current organization and document branding system.

That includes construction drawings, drawing sets, material take-offs, internal cost breakdowns, customer estimates, proposals, supplier requests for quotation, procurement packages, contracts when implemented, change orders, purchase documents, project reports, field reports, completion documents, actuals reports, learning reports, analytics outputs, generated PDFs, and any other governed issued document.

No case script, Markdown-to-PDF conversion, spreadsheet export, drawing generator, or one-off document may set its own branding. A case may produce a document before a general platform workflow exists. That document still uses the governed identity, states its status, and remains replaceable by the platform renderer when that renderer exists.

## Content stays separate from branding

The visual identity is one system. The information in each document stays inside that document’s boundary.

| Document | What it may contain |
|----------|---------------------|
| Customer | Customer-safe commercial information |
| Internal | Authorized cost, margin, and operational information |
| Supplier | Supplier procurement and transaction information |
| Field | Field-operational information |
| Learning and actuals | Authorized internal evidence and history |

Internal use controls content and access. It does not allow an unbranded layout.

A supplier document may list quantities, SKUs, price fields, availability, and delivery. It does not expose margin or private contractor negotiation.

Customer estimates and proposals stay on the existing customer-output path. This rule does not create a second customer-estimate PDF generator.

## Authorities already in force

| Authority | What it governs |
|-----------|-----------------|
| [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) | Internal detailed cost and customer-estimate consistency |
| [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) | Organization Brand Profile |
| [ADR-040](../adr/ADR-040-organization-brand-profile.md) | Brand profile, logo custody, issued-document snapshots |
| `app/templates/proposals/preview.html` | Current customer estimate and proposal preview |
| `app/services/proposal_pdf.py` | Current customer proposal PDF |
| `app/templates/estimates/internal_breakdown.html` | Current internal detailed cost |
| Organization Brand Profile logo | Issued-document mark. Static `app/static/branding/brayman-construction-logo.png` is the fallback already named by `proposal_pdf.py` |

Do not add a competing logo, colour set, or document architecture.

When the current ORG-001 profile leaves colour blank, the proposal PDF fallbacks apply: primary `#1f3a5f`, accent `#c79a2b`.

## Drawings

Construction drawings use the same identity: organization name, approved logo, document colours, title block, project identification, revision, date, sheet number, document status, and the header and footer treatment.

Technical drawing standards stay separate. Branding a sheet does not move geometry.

## Quality gate

A governed document is not complete until the organization identity, logo, colours, document type, title, project identity, revision or date, status, and information boundary are correct. It must not leak internal information, use a generic unbranded layout, carry obsolete product branding, or introduce an ad-hoc logo or colour. Generated PDFs and drawing sets are inspected visually.

## Build-out

This is a cross-cutting constraint on the [Platform Build-Out Register](PLATFORM_BUILD_OUT_REGISTER.md). It is not a separate customer-facing feature. A future document generator is not closed until it meets this standard.

## Linda Bushel

The 1 Oct 2026 generic Markdown-to-PDF package is superseded. The case records underneath it stay. The replacement J1 delivery uses this identity and does not become a second platform renderer.

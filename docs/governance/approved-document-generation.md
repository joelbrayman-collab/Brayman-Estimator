# Approved document generation — permanent requirement

| Attribute | Value |
|---|---|
| Status | **Governing** |
| Date | 2026-10-27 |
| Authority | Joel, 27 Oct 2026: "DATA CHANGES BY PROJECT. THE APPROVED DOCUMENT FORMAT DOES NOT." |
| Masters | [FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) Reusable Master Template Family V1; identity in the [register](../testing/reusable-approved-document-template-family-v1-register.md) |
| Code | `app/services/approved_masters.py`; contract test `tests/test_approved_master_governance.py` |

## Rule

The approved masters are the templates for their document types, not visual references:

| Family | Document type | Constant |
|---|---|---|
| 01 | Labour Calculation Detail | `LABOUR_CALCULATION_DETAIL` |
| 02 | Internal Detailed Cost Breakdown | `INTERNAL_DETAILED_COST_BREAKDOWN` |
| 03 | Customer Facing Estimate | `CUSTOMER_FACING_ESTIMATE` |
| 04 | QuickBooks Estimate Entry | `QUICKBOOKS_ESTIMATE_ENTRY` |
| 05 | Ontario Construction Contract | `ONTARIO_CONSTRUCTION_CONTRACT` |
| 06 | Door / Window / Skylight Schedule | `DOOR_WINDOW_SKYLIGHT_SCHEDULE` |
| 07 | Client Construction Proposal | `CLIENT_CONSTRUCTION_PROPOSAL` |
| 08 | Customer Detailed Cost Estimate (added 27 Oct 2026) | `CUSTOMER_DETAILED_COST_ESTIMATE` |

Master 02 shows the contractor's actual costs and project economics. Master 08 shows detailed customer
selling prices and, where wanted, labour tasks and hours; it never shows acquisition cost, the internal
labour rate, gross profit, margin or markup.

A document of one of these types is produced only by populating a byte copy of its master with
`approved_masters.populate`:

- the master must match its approved SHA-256, or nothing is produced;
- only designated content changes: the CLIENT / PROJECT / SITE / DATE / AMOUNT / PRICE tokens, the rows of
  the master's data tables (filled; extra rows are copies of the master's own row; unused placeholder rows
  removed) and the master's bullet list;
- headings, typography (`word/styles.xml` byte for byte), spacing, margins, header, logo, footer and page
  structure stay the master's;
- no new layout, no approximation, no project-specific writer, no silent fallback
  (`assert_governed_route` refuses any other writer);
- if a document cannot be produced correctly from its master, generation stops with the reason. A change
  to a master needs Joel's explicit approval before it becomes the governed master.

PDF route: the register's approved route is Microsoft Word for Mac "Save as PDF". The populated DOCX is
the governed artifact.

## Why the Linda Bushel documents were wrong (27 Oct 2026)

The 27 Oct Linda documents were written by `branded_issue_pdf.py`, an interim writer created for the J1
case narrative sheets on 1 Oct. Nothing told case scripts that FG-022's masters exist, and no code or test
mapped document types to masters, so the interim writer was reused for an internal cost sheet and a
customer estimate. Fixed by this module, the contract test, and a guard in the case writer that refuses
governed document types (the writer stays only to reproduce the historical J1 sheets).

## Office renderers still to be re-routed

These live application renderers produce documents that correspond to governed types and are not yet
generated from the masters. They are listed so that none is added silently; re-routing them is a
separate release that changes live Production documents.

| Renderer | Produces | Governed type |
|---|---|---|
| `app/services/proposal_pdf.py` | Client proposal PDF | 07 Client Construction Proposal (03 for the price page) |
| `app/services/guided_internal_cost_pdf.py` | Guided Estimating internal cost estimate | 02 Internal Detailed Cost Breakdown |
| `app/services/estimate_quickbooks_pdf.py` | QuickBooks-ready estimate PDF | 04 QuickBooks Estimate Entry |
| `app/services/brayman_v1_contract_presentation.py` | Brayman V1 contract presentation | 05 Ontario Construction Contract |

## Additions, 30 Oct 2026 (estimate-to-project release)

- `app/services/contractor_estimate_package.py`: the **Contractor Estimate Package** (decision 2). Internal to the
  contractor, legal landscape on every page, plain PDF (no form fields or scripts). No approved master family exists
  for it yet; its layout follows the accepted Paulusse REV2 package. Classified as not governed by a master until Joel
  approves one.
- `app/services/subcontract_signing.py`: a subcontract commitment frozen as a PDF for CaliSIGN (Gate 3), like the
  supplier purchase order. Not a customer document.
- Masters 07 and 08 are now V2, with the Excluded / By Others section (see the template family register).

# Formal Estimate Approval Gate and the Three Human Commercial Gates

**Status: RECORDED / BINDING REQUIREMENT / NOT IMPLEMENTATION-AUTHORIZED / NOT IMPLEMENTED**

Recorded 2026-10-30 on Joel Brayman's instruction. This clarifies the earlier Estimate Approval → Procurement → CaliSIGN workflow. It is held for the formal Calibrayt stage-definition exercise, which follows Ben's review of the Paulusse estimate. Do not build it before then.

## The approval does not happen in the PDF

The Estimate Builder PDF is a worksheet for review and adjustment. It is never the contractor's formal approval and never a source of truth. The formal approval happens **inside Calibrayt**.

## Governed sequence

1. Estimate Builder PDF
2. Contractor review / adjustment
3. Changes reconciled into Calibrayt
4. Final Calibrayt estimate review
5. **FORMAL CONTRACTOR APPROVAL IN CALIBRAYT** (Gate 1)
6. Estimate version locked
7. Customer proposal generated
8. Draft procurement / subcontract documents prepared
9. **Customer accepts** (Gate 2)
10. Accepted Project Commercial Baseline
11. Procurement documents released to the contractor approval queue
12. **Contractor approves external commitments** (Gate 3)
13. CaliSIGN sends and tracks them

## Formal approval screen

Calibrayt must give the contractor one clear place to make the formal approval. For Brayman Construction, Ben sees a concise final commercial summary with these items:

- project
- Brayman Project #
- Client Project #
- scope / work packages
- direct materials
- labour hours
- labour rate
- direct labour
- subcontract costs
- equipment
- allowances / other
- Total Direct Cost
- Target Gross Margin
- Gross Profit
- Selling Price
- HST
- Customer Total
- material / supplier exceptions
- important assumptions / exclusions

The action button reads **APPROVE ESTIMATE**, or an equivalent wording. The screen must make clear that Ben is approving the estimate for issue to the customer.

The approval records:

- the approving user
- the date and time
- the estimate version
- the commercial values listed above
- the scope and version identity

After approval, that estimate version is locked. Any later change requires a new governed version.

## Three human commercial gates (distinct controls)

| Gate | Who | Where | Meaning |
|---|---|---|---|
| **1 — Contractor estimate approval** | Ben (contractor) | Inside Calibrayt | Brayman approves this scope and pricing for issue to the customer. |
| **2 — Customer acceptance** | Customer | The proposal generated from that exact approved estimate version | The project is commercially authorized. The accepted estimate becomes the Project Commercial Baseline. |
| **3 — External commitment approval** | Ben (contractor) | Contractor approval queue, before CaliSIGN sends | Brayman authorizes this specific external financial commitment. Ben approves each supplier PO and each subcontract commitment separately. |

Everything between these human gates should be generated automatically from governed project information. Information must not have to be entered twice.

## Relationship to existing work (for the stage-definition exercise)

- **Gate 1:** Calibrayt already has estimate versions, costing approval (FG-027), pricing snapshots and a version lock on sign-off. Gate 1 is expected to extend these. It is not a replacement. The summary screen and the explicit APPROVE ESTIMATE record are the parts that do not exist yet.
- **Gate 2:** The proposal is generated from a locked version, and MONITOR's baseline comes from the accepted proposal → version → pricing snapshot (ADR-021). Both already exist.
- **Gate 3:** Supplier POs and CaliSIGN supplier signing already exist. The contractor approval queue between the accepted baseline and CaliSIGN sending does not exist yet. Subcontract commitments also do not exist yet; see the Dynamic Estimate Builder architecture audit, 2026-10-30.
- The PDF import / reconciliation path (step 3) is the one proposed in that audit: upload, read the fields, show the differences, apply through the normal services.

---

# Customer-facing scope clarity (addendum, recorded 2026-10-30)

**Status:** RECORDED / BINDING REQUIREMENT. The Paulusse PDF part applies to the Paulusse scope include/exclude work. The platform part is NOT IMPLEMENTATION-AUTHORIZED and is held for the Dynamic Estimate Builder architecture work.

## Governing rule

**DESELECTING SCOPE CHANGES RESPONSIBILITY — IT DOES NOT ERASE THE SCOPE.**

Deselecting a scope item from Brayman's price must never make it silently disappear from the customer documents. Every governed scope item resolves to a clear commercial status, either **INCLUDED** or **EXCLUDED**. When responsibility is known, the item also names the party: **BY LOCKWOOD**, **BY OWNER / CLIENT**, **BY OTHERS**, or another governed party.

## When an item is excluded (internal Estimate Builder)

- Preserve the construction quantity.
- Mark the item as excluded from Brayman.
- Name the responsible party only where the project record confirms it.
- Remove the associated Brayman costs from the estimate.
- Recalculate the project price.

## Responsibility

Never assume that an excluded item is "By Lockwood". Show "By Lockwood" only when the project information establishes it. Otherwise show "Excluded from Brayman Construction scope / By Others" until responsibility is confirmed.

## Customer documents

- **Customer Detailed Estimate:** two sections.
  - **INCLUDED IN BRAYMAN CONSTRUCTION PRICE** lists all included scope packages.
  - **EXCLUDED / BY OTHERS** lists all identified project scope not in Brayman's price, with the responsible party where it is known.
  - Example wording: "Existing siding removal and substrate preparation — Excluded from Brayman Construction scope; by Lockwood."
- **Customer Proposal:** the Included and Excluded sections derive from the SAME scope selections. The proposal must not keep independent scope wording that can drift away from the estimate.
- **Chain:** Ben's scope selection → internal cost inclusion/exclusion → selling-price calculation → Customer Detailed Estimate → Customer Proposal.

## Paulusse acceptance test (removal / preparation)

1. Start from the accepted baseline.
2. Exclude the applicable preparation/removal scope.
3. Its Brayman costs disappear.
4. Unrelated costs remain.
5. The customer price recalculates.
6. The Customer Detailed Estimate shows the work as excluded.
7. The Proposal shows the work as excluded.
8. Responsibility shows "By Lockwood" only if the project record supports it.
9. Re-include the scope.
10. Costs and customer wording return to Included.
11. Restore the accepted baseline.

## Future platform rule (Dynamic Estimate Builder)

Every governed project work package keeps two separate concepts:

- **Commercial Status:** Included or Excluded.
- **Responsible Party / Delivery Method.**

Examples:

- Roofing: Included; Subcontracted; Brayman Construction / approved roofing subcontractor.
- Site preparation: Excluded; Client.

This extends the work-package design in the 2026-10-30 architecture audit. Delivery method is read from the existing scope-delivery routing (ADR-048). Commercial status and responsible party are new fields.

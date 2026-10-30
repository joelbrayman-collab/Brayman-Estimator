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

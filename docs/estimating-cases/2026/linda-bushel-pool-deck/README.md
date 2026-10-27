# Linda Bushel pool deck — case index

| Field | Value |
|-------|--------|
| Status | 27 Oct 2026 costing issue is current: written BMR, Vista and Pro Post prices are in the case. Labour hours, Vista's payable price and the foundation quantity are open. Selling price not issued. Issue J1 (1 Oct) is historical. |
| Date preserved | 2026-09-29 |
| Client spelling on the located documents | **Linda Bushel** |
| Location | 12 D'Arcy's Way, Kemptville, Ontario, K0G 1J0 |
| This case is | One project record. It is not a platform estimating default. |

The preservation instruction also used the spelling “Buschel.” That spelling does not appear on the located files. Those files say **Bushel**. Nothing was renamed.

## What is in this folder

| Path | What it is |
|------|------------|
| `source/2026-09-29-linda-bushel-pool-deck-design.md` | Unaltered copy of the 29 Sep 2026 design brief. |
| `drawings/framing-and-pier-layout-comparison.png` | Unaltered framing comparison. Option A is marked Recommended on the sheet. |
| `learning/project-record.md` | Structured record of facts, decisions, and gaps. |
| `case-record.json` | Machine-readable status. Missing stages are recorded as absent. |

## What was not in this folder on 29 Sep 2026, before issue P1

No client sketch, construction drawing, 11×17 PDF, material take-off, internal estimate, customer estimate, or BMR supplier request was found on this Mac. Those missing source files were not invented. Issue P1, below, is a later preliminary package. It is not a recovered original.

The drawing, if later issued, is a construction and pricing basis. It is not a North Grenville permit approval and it is not an engineering seal.

## Issue P1 — 29 Sep 2026

Preliminary only. Not sent to Darcy. Not an estimate. The source brief and the framing comparison above are unchanged.

| Path | What it is |
|------|------------|
| `drawings/2026-09-29-p1-preliminary-11x17.pdf` | Eight-sheet 11×17 basis. Title: Preliminary Construction and Supplier Pricing Basis - Subject to Permit Review and Field Verification. |
| `takeoff/2026-09-29-p1-material-takeoff.md` | Quantities reconciled to that drawing. |
| `takeoff/p1_calculation.py` | The arithmetic that writes the sheet, the take-off, and the supplier request. |
| `supplier/bmr-winchester/2026-09-29-p1-darcy-supplier-request.md` | Request for Darcy. Prices, availability, substitution, and delivery timing are blank. |

## Capability test — 29 Sep 2026

Not final. Not sent. Does not replace issue P1 and does not change the take-off.

| Path | What it is |
|------|------------|
| `drawings/2026-09-29-capability-test-foundation-framing-11x17.pdf` | Foundation and framing plan, CT-1. |
| `drawings/2026-09-29-capability-test-stair-detail-11x17.pdf` | First stair proof, CT-2. Kept for comparison. |
| `drawings/2026-09-29-capability-test-stair-detail-r2-11x17.pdf` | Refined stair sheet, CT-2 R2. Imperial labels. Tread runs under the riser. |
| `drawings/capability_test_plan.py` | Vector generator for CT-1. |
| `drawings/stair_detail.py` | Generator for the first CT-2 proof. |
| `drawings/stair_detail_r2.py` | Generator for CT-2 R2. Project proving geometry. Not the Stair Engine. |
| `takeoff/2026-09-29-drawing-vs-p1-differences.md` | Difference report. P1 quantities were not changed. |
| `geometry/2026-09-29-governed-geometry-reconciliation.md` | Layout trace. Piers, joists, stringers, and throat stay unresolved. No quantity was changed. |
| `costing/2026-09-29-ben-internal-cost.md` | Internal cost sheet for Ben. Every line is PRICE REQUIRED. Not sent. |
| `supplier/bmr-winchester/2026-09-29-darcy-quantity-differences.md` | Differences from the unsent Darcy request. Not sent. |

## Case package — 1 Oct 2026

Does not replace issue P1. Does not choose the open pier, joist, or stringer counts. Does not add a price. Not sent to Darcy. Not a permit approval and not an engineering seal.

| Path | What it is |
|------|------------|
| `drawings/2026-10-01-issue-status.md` | Names the P1 PDF as the 11×17 package and records the visual check. |
| `takeoff/2026-10-01-quantity-reconciliation.md` | Arithmetic check and the lines that stay unresolved. |
| `supplier/bmr-winchester/2026-10-01-supplier-package-status.md` | Current unsent supplier package. Prices stay blank. |
| `estimates/internal/2026-10-01-ben-internal-cost.md` | Internal sheet for Ben. Every dollar is PRICE REQUIRED. |
| `estimates/customer/2026-10-01-preliminary-customer-estimate.md` | Customer scope. Selling price is not issued. |

## Issue J1 — 1 Oct 2026

Current preliminary issue. Joel's decisions of 1 Oct 2026: 15 piers from the CT-1 layout, 16 joist lines from P1, 10 stringers, a 5.00 in working throat, a 12 in lower-deck walking surface, and street number 12. The client selected helical piers. Sonotubes and concrete are not in this issue. The throat is not a structural certification. Issue P1, CT-1, CT-2, and CT-2 R2 stay as historical evidence. The Darcy request is ready to send and has not been sent. No supplier price was invented.

| Path | What it is |
|------|------------|
| `drawings/2026-10-01-j1-preliminary-11x17.pdf` | Eight-sheet 11×17 basis. Produced by `takeoff/issue_j1.py`. |
| `takeoff/2026-10-01-j1-material-takeoff.md` | Quantities reconciled to that drawing. |
| `takeoff/issue_j1.py` | Generator for the J1 drawing, take-off, and supplier request. It does not write the 29 Sep files. |
| `supplier/bmr-winchester/2026-10-01-j1-darcy-request-for-quotation.md` | Request for quotation for Darcy at BMR Winchester. Not a quotation received. |
| `estimates/internal/2026-10-01-j1-ben-internal-cost.md` | Internal sheet for Ben. Supplier-dependent dollars are PRICE REQUIRED. |
| `estimates/customer/2026-10-01-j1-preliminary-customer-estimate.md` | Customer preliminary estimate. Selling price is not issued. |
| `drawings/review/2026-10-01-j1/J1-VISUAL-REVIEW.md` | Visual review of all eight sheets. Two presentation defects were corrected. Final result is pass. |
| `delivery/LINDA_BUSHEL_POOL_DECK_J1_BEN_PACKAGE.zip` | Package for Ben. Drawing, take-off, internal cost, supplier request, and customer draft. |
| `takeoff/branded_issue_pdf.py` | Interim PDF writer for the J1 narrative sheets. It uses the ORG-001 logo and the proposal colour fallbacks. It is not a second platform renderer. |

The generic Markdown-to-PDF package written earlier on 1 Oct 2026 is superseded. The replacement PDFs use the governed Brayman identity. Historical 29 Sep records stay.

The current J1 sheets, take-off, cost sheet, customer estimate, and supplier request were rewritten into job language. Words such as approved geometry, Option A, and the names of earlier trials are not on those sheets. The 29 Sep records still use the words they were written with.

## 6 Oct 2026 — cost request for Ben

Fillable PDF of every line that still needs a cost. The walking surface and the stair treads are Trex composite. Fascia is 44.184 ft on the exposed rim: upper sides 10.092 ft each, upper front returns 4 ft each, lower sides 3 ft each, and the lower front 10 ft. The open pool edge and the stair stringer faces have no fascia. Colour, product line, fascia width, and fascia stock length are not chosen. Framing stays pressure-treated. The boxes are empty. No price was added. Ben types the unit price, the line price, and a note, saves the PDF, and sends it back. The customer estimate and the internal cost stay unpriced until that return is in the case. The 1 Oct drawing still shows 5/4×6 boards and was not reissued.

| Path | What it is |
|------|------------|
| `estimates/internal/2026-10-06-ben-items-that-need-a-cost.pdf` | Fillable request. Same file on the Desktop as `Linda-Bushel-items-that-need-a-cost.pdf`. |

## 27 Oct 2026 — written supplier prices, Ben's internal cost, Linda's estimate

Current issue. Issue J1 is not rewritten. Supplier originals are kept unchanged; the Markdown records transcribe them and the originals govern.

| Path | What it is |
|------|------------|
| `supplier/bmr-winchester/2026-10-26-darcy-bmr-estimate-237147-1.pdf` | BMR Winchester estimate 237147/1, Darcy, 26 Oct 2026. $8,676.09 before HST. Expires 28 Oct. |
| `supplier/bmr-winchester/2026-10-26-darcy-bmr-estimate-237147-1.md` | Line record and arithmetic check. |
| `supplier/bmr-winchester/2026-10-26-vista-rail-quote-87915-165209.pdf` | Vista railing quote through BMR, 26 Oct 2026. $3,851.49 **MSRP**. |
| `supplier/bmr-winchester/2026-10-26-vista-rail-quote-87915-165209.md` | Bill of materials record. Additional to BMR; payable price to confirm with Darcy. |
| `supplier/pro-post-foundations/2026-10-06-pro-post-OT-2236-estimate.pdf` | Pro Post Foundations OT-2236, 6 Oct 2026: 11 helical piles, $3,750.00 before HST incl. $400 conditional engineer report. Validity lapsed 21 Oct. |
| `supplier/pro-post-foundations/2026-10-06-pro-post-OT-2236-pile-locations.png` | Pro Post pile locations on Brayman's A-01 plan. |
| `supplier/pro-post-foundations/2026-10-06-pro-post-pile-head-options.png` | Pro Post pile-head options sheet. |
| `supplier/pro-post-foundations/2026-10-05-a01-screenshot-attached-to-OT-2236-email.png` | Brayman A-01 general arrangement, as attached in the email thread. |
| `supplier/pro-post-foundations/2026-10-27-forwarded-OT-2236-estimate.eml` | Ben's forward of the Pro Post email, 27 Oct 2026, with all attachments. |
| `supplier/pro-post-foundations/2026-10-06-pro-post-OT-2236.md` | Record and arithmetic check. |
| `takeoff/2026-10-27-supplier-quote-reconciliation.md` / `.pdf` | Every requirement: J1 quantity, supplier quantity, price, status. 15 piers (J1) against 11 piles (Pro Post). |
| `estimates/internal/2026-10-27-ben-internal-cost.md` / `.pdf` | Internal cost for Ben. INTERNAL — NOT FOR CUSTOMER. Direct cost incomplete (labour, delivery, equipment, permit). |
| `estimates/customer/2026-10-27-linda-bushel-estimate.md` / `.pdf` | Linda's estimate: scope, assumptions, exclusions. Price to be confirmed. No internal figures. |
| `takeoff/issue_2026_10_27.py` | Writes the three PDFs and the package with the J1 interim writer (`branded_issue_pdf.build`; `**bold**` now rendered). |
| `delivery/LINDA_BUSHEL_POOL_DECK_2026-10-27_BEN_PACKAGE.zip` | Ben's package: the three PDFs, the three supplier originals, the pile locations and the J1 drawing. |

Open: **FOUNDATION QUANTITY CONFIRMATION REQUIRED — J1 = 15; Pro Post engineered quotation = 11.** **CONFIRM WITH DARCY — Vista payable cost.** **LABOUR HOURS REQUIRED** ($65 per man-hour, governed). Delivery, carrying, equipment, permit fee, lower-deck skirt and gate hardware not priced. Pricing rule: 15% true gross margin, selling price = direct cost ÷ 0.85.

# J1 visual review — 1 Oct 2026

Drawing: `drawings/2026-10-01-j1-preliminary-11x17.pdf`

Rendered at 120 dpi to `sheet-01.png` through `sheet-08.png` in this folder. Each sheet was inspected as an image. Text extraction was not the review.

Page size 17 × 11 in, landscape, eight sheets. Title block on every sheet: Preliminary Construction and Supplier Pricing Basis - Subject to Permit Review and Field Verification. Address on every sheet: 12 D'Arcy's Way, Kemptville, ON K0G 1J0. Sheet numbers 1 of 8 through 8 of 8.

Generator: `takeoff/issue_j1.py`. The correction below does not change pier, joist, or stringer geometry, and it does not change the take-off quantities.

## First inspection

| Sheet | Result | What was seen |
|---|---|---|
| 1 | ISSUE | Sheet-index line 4, “Decking, stair, guard, gate, and skirting,” sat in the footer. The descenders were cut off. |
| 2 | ISSUE | The left edge of the lower deck ran through the “1” in P10 and P13, so those labels read as P0 and P3. |
| 3 | ISSUE | Same edge-line collision on P10, P12, P13, and P15. Joist lines, 16 of them, were otherwise readable. |
| 4 | ISSUE | Same pier-label collision. Guard, gate, and “POOL EDGE OPEN” were readable. |
| 5 | PASS | 12 in walking surface, 37 in guards, 42 in gate, 50 in upper deck, 38 in rise. No clipping. |
| 6 | PASS | Profile is five risers and four treads. The upper deck is the top landing, so the fifth riser has no tread after it. Throat text is 5.00 in, calculated 4.997 in, and is not a certification. Two 5/4 × 6 boards per tread. |
| 7 | PASS | 15 saddles, 15 post connectors, 16 header connectors, 10 stringer connectors, 76 stitch bolts. Lower deck called out at 12 in. |
| 8 | PASS | Field, permit, and supplier notes are clear of the footer. The request is not sent. The 5.00 in throat is not certified. |

## Correction

Presentation only. No member was moved and no quantity changed.

- Cover sheet index and the rows above it were tightened so line 4 and line 8 sit above the footer.
- P10, P12, P13, and P15 labels were moved off the vertical edge line. Other pier labels sit on a white patch so a joist or beam does not cut the name.

The PDF, take-off, and supplier request were regenerated from `takeoff/issue_j1.py`. The take-off and the supplier request did not change. Counts after regeneration: 15 piers, 16 joists, 10 stringers, 76 bolts, 1.212 cu yd, 798 deck screws.

## Second inspection

| Sheet | Result |
|---|---|
| 1 Cover, general notes, and geometry | PASS |
| 2 Pier and foundation plan | PASS |
| 3 Framing plan | PASS |
| 4 Decking, guards, gate, and skirt | PASS |
| 5 Front and side elevations | PASS |
| 6 Stair detail | PASS |
| 7 Typical details | PASS |
| 8 Field verification and supplier notes | PASS |

Checked on the corrected sheets: 15 piers with readable names P1–P15, 16 joist lines, 10 stringers in the note, 5.00 in throat labelled as a working basis and not a certification, 12 in lower-deck walking surface, two 5/4×6 tread boards, 37 in Veranda kit, 42 in clear gate, and the same address and preliminary status on every title block.

No remaining drawing defect from that inspection.

## Helical piers — same day revision

Joel relayed the client's decision to use helical piers instead of sonotubes and concrete. The 15 locations did not move. Shaft, helix, length, torque, and capacity were not specified and were not drawn as a certified product.

Sheets 1, 2, 7, and 8 were rendered again and inspected.

| Sheet | Result | What was seen |
|---|---|---|
| 1 | PASS | Cover states helical piers, no sonotubes, and no concrete. The sheet index is clear of the footer. |
| 2 | PASS | Notes call each pier a helical pier and say capacity is not certified. P1–P15 remain readable. |
| 7 | PASS | The typical detail is a schematic shaft and helix, labelled product not specified. The note says no concrete. |
| 8 | PASS | Field note 3 asks for product, depth, torque, and bearing, and says the 48 in sonotube depth is not this issue. |

Sheets 3, 4, 5, and 6 were not given a new foundation note. Their geometry is unchanged. The review images in this folder were rendered again from the revised PDF.

## Governed identity — same day

The title block now uses the ORG-001 logo, Brayman Construction, Brayman Construction Inc., 411 St. John Street, Merrickville, Ontario K0G 1N0, and the proposal colour fallbacks. Geometry and quantities were not changed. Sheet 1 was inspected as an image. The logo, names, address, sheet number, gold rule, sheet index, and footer are clear of one another. Line 4 of the index remains above the footer. The review images were rendered again from that PDF.

# Linda Bushel — supplier quotation reconciliation

Date: 2026-10-27

Compares the three written supplier documents with the 1 Oct 2026 issue J1 take-off. J1 is not changed. Prices are pre-HST.

| Source | Document | Amount |
|---|---|---|
| BMR Winchester | Estimate 237147/1, 26 Oct 2026, expires 28 Oct 2026 | $8,676.09 |
| Vista (through BMR) | Quote 87915-165209, 26 Oct 2026, **MSRP** | $3,851.49 |
| Pro Post Foundations | Estimate OT-2236, 6 Oct 2026, valid 15 days (lapsed 21 Oct) | $3,750.00 (incl. $400 conditional engineer report) |

Status words: **priced** (written price, quantity matches J1), **variance** (written price, quantity or product differs from J1), **substitution** (a different product does the same job), **conditional**, **optional**, **not priced** (no written price), **superseded**.

## Framing

| Requirement | J1 qty | Supplier qty | Supplier | SKU / product | Unit | Extension | Status / explanation |
|---|---|---|---|---|---|---|---|
| Upper joists, 2×8 | 11 × 12 ft (132 ft; net 112.766 ft for 16 joists) | 4 × 12 ft, 2 × 10 ft, 6 × 8 ft (116 ft) | BMR | 0749011 / 0749002 / 0748997 | 23.924 / 19.911 / 15.916 | 231.00 | **Variance.** Different stock lengths. J1's two outer joists are 10.092 ft and do not fit a 10 ft stick; the four 12 ft sticks are needed by J1's four paired sticks. Confirm the joist stock with Darcy against the cut list. |
| Curved header, 2×8 | 2 × 12 ft (8 pieces × 2.695 ft) | 3 × 8 ft | BMR | 0748997 | 15.916 | 47.75 | **Variance.** An 8 ft stick gives two 2.695 ft pieces, so 3 sticks give 6 of the 8 pieces. Confirm. |
| Beams, 2-ply 2×10 | 7 × 12 ft + 4 × 10 ft | 7 × 12 ft + 4 × 10 ft | BMR | 0749066 / 0749057 | 39.576 / 32.751 | 408.03 | **Priced.** Matches J1. Beam layout depends on the foundation decision below. |
| Lower-deck joists, 2×8 | 3 × 12 ft | 3 × 12 ft | BMR | 0749011 | 23.924 | 71.77 | **Priced.** Matches J1. |
| Stair stringers, 2×12 | 10 × 8 ft (10 stringers) | 4 × 10 ft | BMR | 0749109 | 44.126 | 176.50 | **Variance.** A J1 stringer is about 61 in plus a 3 in end cut, so one 10 ft stick gives one stringer: 4 stringers, not 10. Confirm with Darcy and Ben. |
| Posts, 6×6 | 11 × 8 ft (15 posts) | 7 × 8 ft | BMR | 0749190 | 38.338 | 268.37 | **Variance.** 7 sticks match an 11-post layout (two upper posts per stick), not J1's 15. See Foundation. |
| Blocking | 4 × 2×8 × 12 ft | 6 × 2×10 × 8 ft | BMR | 0749048 | 26.381 | 158.29 | **Substitution.** 2×10 blocking in place of 2×8. Confirm. |
| Post-to-beam connector | 15 | 30 deck post ties | BMR | SDJT14-TZ | 2.291 | 68.73 | **Variance.** 30 ties (two per post would be 22 for 11 posts, 30 for 15). Confirm. |
| Joist-to-header connector | 16 | 14 skewed hangers (7 L + 7 R) | BMR | SKH26L-TZ / SKH26R-TZ, printed "2×6" | 6.247 | 87.46 | **Variance.** Count 14 against 16, and the hanger is printed for 2×6 where the joists are 2×8. Confirm size and count. |
| Joist hangers | not in J1 | 11 | BMR | JUS28-TZ (2×8 slant-nail) | 1.187 | 13.06 | **Variance.** Not in J1. Purpose not stated. |
| Stringer connectors | 10 | 10 | BMR | CSH-TZ concealed stringer hanger | 2.291 | 22.91 | **Priced.** Count matches J1's 10 stringers; see the stringer variance. |
| Stitch bolts / nuts / washers | 76 / 76 / 152 (diameter open) | 100 / 75 / 150, 3/8 in × 4 in carriage | BMR | 2094562 / 2093387 / 2680633 | packages | 136.51 | **Variance.** Diameter now 3/8 in. 75 nuts and 150 washers are one nut and two washers short of J1's 76 bolts. |
| Structural screws | 100 | 100 (2 × 50) | BMR | 0017968 T40 3 in | 30.342 / pk | 60.68 | **Priced.** |

## Deck finish

| Requirement | J1 qty | Supplier qty | Supplier | SKU / product | Unit | Extension | Status / explanation |
|---|---|---|---|---|---|---|---|
| Upper deck boards | 11 × 20 ft + side pieces (part of 17 × 10 ft and 7 × 8 ft) | 11 × 20 ft + 11 × 12 ft | BMR | Trex Select Island Mist 1×6 | 188.48 / 113.28 | 3,319.36 | **Priced, stock re-planned.** Colour now chosen: Island Mist. |
| Lower deck boards | in the 10 ft pack | 4 × 20 ft | BMR | Trex Select Island Mist 1×6×20 | 188.48 | 753.92 | **Priced, stock re-planned.** |
| Stair treads (4 treads × 2 boards × 10 ft) | in the 10 ft pack | 4 × 20 ft | BMR | Trex Select Island Mist 1×6×20 | 188.48 | 753.92 | **Priced.** 4 × 20 ft = 8 × 10 ft = the 8 tread boards. |
| All Trex boards, lineal | 446 ft (11×20 + 17×10 + 7×8) | 512 ft (19×20 + 11×12) | | | | 4,827.20 | Supplier lineal is 66 ft more than J1. |
| Stair risers (by group on the estimate) | not in J1 | 5 × 1×8 × 12 ft fascia | BMR | Trex fascia Island Mist 1×8×12 | 124.379 | 621.90 | **Variance.** Grouped under "Stairs": five pieces match the five 10 ft risers. J1 did not list riser boards. Confirm. |
| Rim fascia | 44.184 ft, width open | 5 × 1×12 × 12 ft (60 ft) | BMR | Trex fascia Island Mist 1×12×12 | 208.98 | 1,044.90 | **Variance.** Grouped under "Other", no use stated. 60 ft covers the 44.184 ft rim. Confirm the use and the 12 in width. |
| Deck fasteners | 798 (two per crossing) | 6 boxes, 50 sq ft each (300 sq ft) | BMR | Trex deck fasteners 0022924 | 56.22 | 337.32 | **Priced.** About 184 sq ft of walking surface (116.8 upper + 30 lower + about 37 treads). |
| Fascia screws and caps | not counted | 1 kit | BMR | 0022490 | 93.712 | 93.71 | **Priced.** |
| Lower-deck skirt, PT 1×6 × 8 ft | 5 | — | — | — | — | — | **Not priced.** Not on the BMR estimate. |

## Railing

| Requirement | J1 qty | Supplier qty | Supplier | SKU / product | Unit | Extension (MSRP) | Status / explanation |
|---|---|---|---|---|---|---|---|
| Level guard | 10 Veranda 37 in × 6 ft kits | 7 rails (5 × 5 ft, 2 × 7 ft), 4 end, 4 corner, 2 mid posts, 2 + 5 picket packages, 4 level brackets | Vista via BMR | PB7453/7455/5468/5469/5470/7777/7779/7477 | MSRP | 2,560.72 | **Substitution.** Vista 42 in aluminium replaces the 37 in Veranda kit. Runs follow the J1 layout (sections 1–2, 4–8, 10–11). |
| Stair guard | 2 custom | 1 × 8 ft stair rail (cut to two 40.91 in), 2 top + 2 bottom stair posts, 2 stair picket packages | Vista via BMR | PB5484/5733/5735/7773 | MSRP | 655.93 | **Substitution.** Sections 3 and 9. |
| Gate | 1, 42 in clear | 1 × 42 in high, 48 in gate | Vista via BMR | PB7517XB | 423.99 | 423.99 | **Substitution.** 48 in gate where J1 asked 42 in clear. Hinges and latch not listed separately: confirm included. |
| Gate hinges and latch | latch 1, hinges open | — | — | — | — | — | **Not priced** unless the Vista gate includes them. |
| Guard posts, PT 4×4 × 8 ft | 14 | — | — | — | — | — | **Superseded** by Vista aluminium posts on base plates. Blocking under each post is still needed (not counted in J1 either). |
| Accessories | — | base-plate covers 10 + 4, paint pen 1 | Vista via BMR | PB7744/7746/6766 | MSRP | 210.85 | **Priced (MSRP).** |
| **Vista total** | | | | | | **3,851.49** | **Additional to BMR's $8,676.09** (the BMR estimate shows "Vista Rail Package — See separate quote" with no amount). **MSRP, not Brayman's cost. CONFIRM WITH DARCY — Vista payable cost / relationship to BMR estimate.** |

## Foundation

| Requirement | J1 qty | Supplier qty | Supplier | Product | Unit | Extension | Status / explanation |
|---|---|---|---|---|---|---|---|
| Helical piers / piles | **15** | **11** (10 + 1) | Pro Post | 2-3/8 in × 7 ft galvanized, 8 in blade (10) and 10 in blade (1) | 295.00 / 315.00 | 3,265.00 | **Variance — see below.** |
| Pier brackets | 15, unless included | included | Pro Post | standard adjustable flat bracket 5 × 5 × 3/16 in | — | 0.00 | **Priced (included).** |
| Travel | — | 1 | Pro Post | | 85.00 | 85.00 | **Priced.** |
| Engineer report and compliance letter | — | 1 | Pro Post | | 400.00 | 400.00 | **Conditional.** Required if the town asks for it with the permit application. |
| U-brackets | — | — | Pro Post | | 35.00 each | — | **Optional.** |
| Pile extensions | — | as needed for torque | Pro Post | 2-3/8 in × 7 ft | 240.00 each | — | **Conditional.** |
| Excavation / welder / winter / waiting | — | as needed | Pro Post | | 105 / 145 / 95 / 95 per hour | — | **Conditional.** |

### 15 piers in J1 against 11 piles from Pro Post

- **J1 (1 Oct 2026):** 15 piers from Brayman's own CT-1 layout: 9 under the upper deck (front beam with piers 6 ft apart, a 12 ft main beam 13 ft out, two wing piers) and 6 under the lower deck. The J1 sheets say the pier product, capacity and beam spans were not checked or certified.
- **Pro Post (6 Oct 2026):** 11 piles "based on our engineer's recommendation", marked on Brayman's A-01 general arrangement plan (29 Sep 2026, the same deck: 18 ft wide, 5 ft clear at centre, 10 ft stairs, 10 × 3 ft lower deck). 7 under the upper deck: two at the pool-side corners, two on a short beam near the pool, three along the front edge (corners and centre; the centre pile is the 10 in blade). 4 under the lower deck, one at each corner.
- **Same deck, different framing.** The deck outline matches. The beam arrangement does not: Pro Post's front beam has 3 piles about 9 ft apart where J1 has 4 piers 6 ft apart, and Pro Post has no 12 ft main beam 13 ft out. The lower deck is carried on 4 piles where J1 has 6.
- **The BMR list was not drawn for J1's 15.** BMR's 7 post sticks fit 11 posts, not 15.

**FOUNDATION QUANTITY CONFIRMATION REQUIRED — J1 = 15; Pro Post engineered quotation = 11.**

The 11-pile quotation is the only written, engineer-based foundation price in the case, and it is used for the current cost. Before construction, Joel and Ben choose one of two things:

1. **Adopt Pro Post's 11 piles** and re-draw the J1 framing to Pro Post's beam lines. The 9 ft front-beam spans and the lower-deck spans must be accepted by Pro Post's engineer or the town's span table, and the BMR beam, post and connector list confirmed against that framing.
2. **Keep J1's 15 piers** and ask Pro Post for a revised quotation. No price for 15 is calculated here.

The earlier working figure of **$350 per helical pier** (Joel, before any written quotation) is **superseded** by OT-2236. It is not used. It was never written into the case.

## Other

| Requirement | J1 | Supplier | Status / explanation |
|---|---|---|---|
| Delivery to 12 D'Arcy's Way | not priced | BMR: "Delivery extra" | **Not priced.** |
| Carrying | — | BMR: "Carrying extra" | **Not priced.** |
| Vista delivery | — | not stated | **Not priced.** Confirm with Darcy whether it ships with the BMR order. |
| Town permit fees | excluded in the J1 customer estimate | — | **Not priced.** Decision: in Linda's price or excluded. |
| Equipment (Brayman) | none listed | — | **Not priced.** Pro Post brings its own machine. |
| Disposal | not priced | — | **Not priced.** |
| Brayman labour | no hours on file | — | **Not supplier pricing.** See the internal cost sheet. |

## Is written supplier pricing now complete?

**Nearly, not fully.** The three documents give written prices for every principal purchased part: framing lumber and hardware, Trex decking and fascia (BMR); railing and gate (Vista); helical piles with brackets (Pro Post). What still has no usable written price:

1. **Vista's payable price.** The $3,851.49 is MSRP. Brayman's BMR price for it is not written anywhere.
2. **Delivery and carrying** (BMR says extra), and Vista delivery.
3. **Lower-deck skirt** (5 × PT 1×6 × 8 ft): not on the BMR estimate.
4. **Gate hinges and latch**, unless the Vista gate includes them.
5. **Pro Post's price for the final pile count**, if J1's 15 is kept; and OT-2236's validity has lapsed.

The BMR quantities also differ from J1 in several places (stringers, upper joist stock, header stock, post count, hangers). Darcy's estimate says the customer verifies quantities and prices may vary with the final design; those lines are confirmed before ordering.

BMR's prices are held only if the award is confirmed **by 28 Oct 2026**.

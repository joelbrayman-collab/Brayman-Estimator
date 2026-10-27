# Linda Bushel — Internal Cost for Ben

Date: 2026-10-27

**INTERNAL — NOT FOR CUSTOMER**

12 D'Arcy's Way, Kemptville, ON K0G 1J0. Pool deck: upper deck, stairs and lower deck on helical piles.

All amounts are before HST. HST is shown only for cash flow: it is outside direct cost and gross margin (Brayman pricing policy). A blank is not zero. Nothing on this sheet was estimated without a written source.

Sources: BMR estimate 237147/1 (26 Oct, expires **28 Oct**), Vista quote 87915-165209 (26 Oct, MSRP), Pro Post estimate OT-2236 (6 Oct, valid 15 days — **lapsed 21 Oct**). Line-by-line comparison with issue J1: `takeoff/2026-10-27-supplier-quote-reconciliation.md`. The 1 Oct J1 cost sheet stays as it was.

## A. BMR Winchester — materials

| Group | Amount |
|---|---|
| Framing lumber (joists, header, beams, lower joists, stringers, posts, blocking) | $1,361.71 |
| Structural hardware (post ties, hangers, stringer hangers, 3/8 in bolts, nuts, washers, structural screws) | $389.35 |
| Trex Select Island Mist deck boards (upper, lower, stair treads) | $4,827.20 |
| Trex Island Mist fascia (5 × 1×8 × 12 ft under Stairs, 5 × 1×12 × 12 ft under Other) | $1,666.80 |
| Trex fasteners and fascia screw kit | $431.03 |
| **BMR quoted materials** | **$8,676.09** |
| HST (cash flow only) | $1,127.89 |

Confirm with Darcy before ordering (the estimate says the customer verifies quantities):

- Stringers: 4 × 2×12 × 10 ft gives 4 stringers; J1 has 10.
- Upper joist stock: cut to J1's lengths, the quoted sticks give at most 14 of the 16 joists (J1 needs 7 × 12 ft; 4 are quoted).
- Header: 3 × 2×8 × 8 ft gives 6 of the 8 header pieces.
- Posts: 7 sticks quoted. By J1's cutting rules, 15 posts need 11 sticks and an 11-pile layout needs 8 (see the foundation decision).
- Hangers: 14 skewed hangers printed "2×6" for 16 2×8 joists; 11 extra 2×8 hangers with no stated use.
- Fascia: what the 1×8 (stairs) and 1×12 (other) pieces are for. J1 had 44.184 ft of rim fascia and no riser boards.
- Nuts and washers: 75 / 150 against 100 bolts.
- Lower-deck skirt, 5 × PT 1×6 × 8 ft: not on the estimate.

## B. Vista railing (through BMR)

| Item | Amount |
|---|---|
| Vista quotation, total **MSRP** | $3,851.49 |
| Relationship to BMR | **Additional.** BMR's priced lines add to $8,676.09 on their own; the Vista package is "See separate quote" with no amount. |
| Brayman's payable price | **Not established.** MSRP is a list price, not Brayman's cost. |
| Used on this sheet | **$3,851.49 (MSRP) as Brayman's cost** until Darcy gives the price BMR will invoice. A lower BMR price only increases Brayman's margin; Linda's price is unaffected. |

**CONFIRM WITH DARCY — Vista payable cost / relationship to BMR estimate.** Also confirm: gate hinges and latch included, post-base fasteners, delivery.

Vista 42 in aluminium replaces J1's 37 in Veranda kits, the 14 PT 4×4 guard posts and the custom stair guards. Its gate is 48 in. Each post needs solid blocking under the base plate (not counted).

## C. Pro Post Foundations — helical piles

| Item | Qty | Amount |
|---|---|---|
| Helical pile 2-3/8 in × 8 in blade × 7 ft, flat bracket included | 10 × $295 | $2,950.00 |
| Helical pile 2-3/8 in × 10 in blade × 7 ft, flat bracket included | 1 × $315 | $315.00 |
| Travel fee | 1 | $85.00 |
| Piles and travel (11 piles) | | $3,350.00 |
| Engineer report and compliance letter — conditional on the town; **included in the cost used** | 1 | $400.00 |
| **Foundation cost used** | | **$3,750.00** |
| HST (cash flow only) | | $487.50 |
| Deposit to book (50% of $4,237.50) | | $2,118.75 |

Not included, if needed: pile extensions $240 each, U-brackets $35 each, excavation $105/h, welder $145/h, winter installation $95/h, waiting or unmarked piles $95/h, revisions to the engineer report $100.

**FOUNDATION QUANTITY CONFIRMATION REQUIRED — J1 = 15; Pro Post engineered quotation = 11.** Pro Post's 11 piles sit on the same deck outline but a different beam layout. Choose: adopt the 11 piles and re-draw the framing to Pro Post's beam lines, or keep 15 and get a revised Pro Post price. This sheet uses the written 11-pile price ($3,750 including the engineer report).

OT-2236 was valid to 21 Oct. Reconfirm the price with Pro Post before the deposit.

The earlier working figure of $350 per pier is superseded by OT-2236 and is not used.

## D. Labour

Searched 27 Oct 2026 for anything that can calculate Linda's labour:

| Source | What it has for this deck |
|---|---|
| This case (P1, CT, J1, 6 Oct cost request) | Quantities only. No hours. |
| `app/services/deck_framing_quantity.py` and the deck take-off engine | Member counts only; by design "does not invent a labour production rate". |
| Production labour tasks and production-rate standards (27 Oct copy of the Production database) | 7 tasks, all UAT or concrete; 1 production rate, synthetic and withdrawn. No deck, framing, decking or railing rate. |
| Production historical estimates (24) and their labour lines (120) | Slabs, ICF, a garage, a renovation, a concrete gate. No deck, stair or railing labour. |
| Direct labour cost rate | Platform policy and the Production rate standard: $65.00 per man-hour (29 Aug 2026). |

**Rate used: $75.00 per hour — Ben's labour rate, set by Joel on 27 Oct 2026.** The platform pricing policy (docs/pricing-policy.md) and the Production rate standard still say $65 and are updated separately; this case does not change them.

**Hours: no governed method exists, so the hours are built up task by task from the take-off below** and proposed for Joel's approval. Change any line and the price follows.

## E. Delivery and carrying

BMR: "Delivery extra. Carrying extra." No amount on any document. Treated as $0.00 (absorbed) unless Joel gives an amount.

## F. Equipment

$0.00. Pro Post brings its own installation machine; Brayman's work needs hand and power tools only.

## G. Permit and engineering

| Item | Treatment |
|---|---|
| Pro Post engineer report and compliance letter | $400.00, **included** in the $3,750 foundation cost (the conservative case). |
| Town building-permit fee | Excluded from Linda's price, as in J1; billed at cost if Brayman applies. |

<!-- PRICE:BEGIN -->
## Labour build-up (proposed for Joel's approval)

Built from the J1 take-off and the supplier quantities. No governed deck production rate exists, so each line is a proposed allowance for a two-person crew: approve it or change any line.

| Task | Quantity basis | Man-hours |
|---|---|---|
| Layout, mark the pile locations, meet Pro Post on site | 11 pile locations; deck and stair lines | 8 |
| Posts and beams | 11 posts cut on brackets; built-up 2×10 beams (7 × 12 ft + 4 × 10 ft), 3/8 in carriage bolts | 16 |
| Upper-deck framing | 16 joists cut to the pool curve, 8-piece curved header with 14 skewed hangers, blocking | 24 |
| Lower-deck framing | 9 joists 3 ft, lower beam, blocking, lower posts cut on site | 8 |
| Stairs | 10 ft wide, 4 treads, 5 risers; stringers cut and hung | 16 |
| Trex decking | about 147 sq ft (upper 116.8 + lower 30), every board scribed to the pool curve on the upper deck | 16 |
| Stair treads and risers (Trex) | 8 tread boards, 5 riser boards 10 ft | 8 |
| Trex fascia | about 44 ft of exposed rim, colour-matched screws | 6 |
| Railing blocking | solid blocking under each Vista post base | 4 |
| Vista railing and gate | 11 sections, 14 posts on base plates, pickets, 48 in gate | 16 |
| Unload and carry materials | BMR delivery to the back yard (carrying is extra from BMR) | 4 |
| Clean-up and final walk-through | debris, offcuts, punch list | 4 |
| **Total** | Two-person crew, about 8.1 working days | **130** |

## Direct cost and selling price

| Cost component | Cost (pre-HST) | Evidence / status |
|---|---|---|
| BMR materials | $8,676.09 | Written: estimate 237147/1, 26 Oct 2026 |
| Vista railing and gate | $3,851.49 | Written: quote 87915-165209 at **MSRP**; additional to BMR. Used as Brayman's cost until Darcy gives BMR's price. Any discount lowers cost and raises margin; the price to Linda does not change. |
| Pro Post helical foundation (11 piles, travel, engineer report) | $3,750.00 | Written: OT-2236. Includes the $400 report in full (conditional on the town). Pile count to confirm; reconfirm the lapsed quote. |
| Brayman labour | $9,750.00 | 130 man-hours × $75 (Ben's rate). Build-up below; Joel approves or changes it. |
| Delivery / carrying | $0.00 | BMR: delivery and carrying extra; no amount on any document. $0 (absorbed) until Darcy gives one |
| Equipment | $0.00 | None: Pro Post brings its own machine; hand tools only |
| Permit fee | $0.00 | Excluded from Linda's price (as in J1); billed at cost if Brayman pulls the permit |
| **TOTAL DIRECT COST** | **$26,027.58** | |

Governed pricing: ORG-001-TRUE-GM-15, **true gross margin 15%** (not markup). Selling price = direct cost ÷ 0.85.

| | Amount |
|---|---|
| Total direct cost | $26,027.58 |
| Gross profit | $4,593.10 |
| **Selling price before HST** | **$30,620.68** |
| HST 13% | $3,980.69 |
| **Linda estimate total** | **$34,601.37** |
| Resulting true gross margin | 15.00% |

Every 10 man-hours more or less changes the price before HST by $882.35.
<!-- PRICE:END -->

## Dates

- **28 Oct 2026** — BMR prices held only if the award is confirmed by then.
- OT-2236 lapsed 21 Oct — reconfirm with Pro Post.

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
| Direct labour cost rate | **$65.00 per man-hour**, APPROVED (ORG-001, 29 Aug 2026; docs/pricing-policy.md). |

**Result: no governed method gives Linda's labour hours.** The rate is governed; the hours are a decision for Joel. The table below prices the job at 80, 100, 120 and 140 man-hours so that one number finishes it.

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
## Direct cost and selling price

| Cost component | Cost (pre-HST) | Evidence / status |
|---|---|---|
| BMR materials | $8,676.09 | Written: estimate 237147/1, 26 Oct 2026 |
| Vista railing and gate | $3,851.49 | Written: quote 87915-165209 at **MSRP**; additional to BMR. Used as Brayman's cost until Darcy gives BMR's price. Any discount lowers cost and raises margin; the price to Linda does not change. |
| Pro Post helical foundation (11 piles, travel, engineer report) | $3,750.00 | Written: OT-2236. Includes the $400 report in full (conditional on the town). Pile count to confirm; reconfirm the lapsed quote. |
| Brayman labour | **NOT SET** | **Need Joel to approve the total man-hours** (rate $65, governed). No governed deck production rate, Linda labour estimate or Brayman deck history exists. |
| Delivery / carrying | $0.00 unless Joel gives an amount | BMR: "delivery extra, carrying extra"; no amount on any document |
| Equipment | $0.00 | None: Pro Post brings its own machine |
| Permit fee | $0.00 | Excluded from Linda's price (as in J1) |
| **Total direct cost before labour** | **$16,277.58** | All three written supplier amounts |

Governed pricing: ORG-001-TRUE-GM-15, **true gross margin 15%** (not markup). Selling price = direct cost ÷ 0.85.

Choose the man-hours (2-person crew; 8 h days: 80 h = 5 days, 100 h = 6¼ days, 120 h = 7½ days, 140 h = 8¾ days):

| Man-hours | Labour | Total direct cost | Gross profit | Selling price before HST | HST 13% | Linda total |
|---|---|---|---|---|---|---|
| 80 | $5,200.00 | $21,477.58 | $3,790.16 | $25,267.74 | $3,284.81 | $28,552.55 |
| 100 | $6,500.00 | $22,777.58 | $4,019.57 | $26,797.15 | $3,483.63 | $30,280.78 |
| 120 | $7,800.00 | $24,077.58 | $4,248.98 | $28,326.56 | $3,682.45 | $32,009.01 |
| 140 | $9,100.00 | $25,377.58 | $4,478.40 | $29,855.98 | $3,881.28 | $33,737.26 |

Each man-hour adds $65.00 of cost and $76.47 to the price before HST ($86.41 with HST).
<!-- PRICE:END -->

## Dates

- **28 Oct 2026** — BMR prices held only if the award is confirmed by then.
- OT-2236 lapsed 21 Oct — reconfirm with Pro Post.

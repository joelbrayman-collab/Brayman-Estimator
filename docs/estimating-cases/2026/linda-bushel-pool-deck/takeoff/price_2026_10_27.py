"""Linda Bushel pool deck — direct cost and selling price, 27 Oct 2026.

One calculation for Ben's internal sheet and Linda's estimate. Written supplier amounts are constants
copied from the originals in supplier/ (see the .md records beside them). Brayman labour has no governed
production rate: no governed deck production rate, Linda labour estimate or
historical Brayman deck labour exists (searched 27 Oct 2026; see the internal sheet). Joel supplies the
man-hours; the rate and the margin are governed (docs/pricing-policy.md, ORG-001 records).

    python price_2026_10_27.py                      # priced at the proposed labour build-up
    python price_2026_10_27.py --man-hours 100      # priced at a man-hour total Joel chooses instead
    python price_2026_10_27.py --man-hours 100 --delivery 325   # with a delivery/carrying amount
"""

from __future__ import annotations

import argparse
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
INTERNAL = CASE / "estimates/internal/2026-10-27-ben-internal-cost.md"
CUSTOMER = CASE / "estimates/customer/2026-10-27-linda-bushel-estimate.md"
BEGIN, END = "<!-- PRICE:BEGIN -->", "<!-- PRICE:END -->"

BMR = Decimal("8676.09")            # BMR Winchester estimate 237147/1, pre-HST
VISTA = Decimal("3851.49")          # Vista 87915-165209, MSRP: used as cost until Darcy gives BMR's price
PRO_POST = Decimal("3750.00")       # OT-2236 subtotal: 11 piles 3,265 + travel 85 + engineer report 400
LABOUR_RATE = Decimal("75")         # Ben's labour rate, $ per hour (Joel, 27 Oct 2026). The platform policy and
                                    # the Production rate standard still say $65 until they are updated.

# Labour build-up from the J1 take-off and the supplier quantities (27 Oct 2026). Proposed, not a governed
# production rate: Joel approves or changes each line. Two-person crew, 8-hour days.
LABOUR_TASKS = (
    ("Layout, mark the pile locations, meet Pro Post on site", "11 pile locations; deck and stair lines", 8),
    ("Posts and beams", "11 posts cut on brackets; built-up 2×10 beams (7 × 12 ft + 4 × 10 ft), 3/8 in carriage bolts", 16),
    ("Upper-deck framing", "16 joists cut to the pool curve, 8-piece curved header with 14 skewed hangers, blocking", 24),
    ("Lower-deck framing", "9 joists 3 ft, lower beam, blocking, lower posts cut on site", 8),
    ("Stairs", "10 ft wide, 4 treads, 5 risers; stringers cut and hung", 16),
    ("Trex decking", "about 147 sq ft (upper 116.8 + lower 30), every board scribed to the pool curve on the upper deck", 16),
    ("Stair treads and risers (Trex)", "8 tread boards, 5 riser boards 10 ft", 8),
    ("Trex fascia", "about 44 ft of exposed rim, colour-matched screws", 6),
    ("Railing blocking", "solid blocking under each Vista post base", 4),
    ("Vista railing and gate", "11 sections, 14 posts on base plates, pickets, 48 in gate", 16),
    ("Unload and carry materials", "BMR delivery to the back yard (carrying is extra from BMR)", 4),
    ("Clean-up and final walk-through", "debris, offcuts, punch list", 4),
)
PROPOSED_HOURS = sum(hours for _task, _basis, hours in LABOUR_TASKS)
MARGIN = Decimal("0.15")            # ORG-001-TRUE-GM-15: selling price = direct cost / (1 - 0.15)
HST = Decimal("0.13")               # Ontario HST, applied after the pre-tax selling price


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt(value: Decimal) -> str:
    return f"${money(value):,.2f}"


def price(man_hours, delivery=Decimal("0")) -> dict:
    labour = money(LABOUR_RATE * Decimal(man_hours))
    direct = BMR + VISTA + PRO_POST + labour + delivery
    selling = money(direct / (Decimal(1) - MARGIN))
    profit = selling - direct
    tax = money(selling * HST)
    return {"man_hours": man_hours, "labour": labour, "delivery": delivery, "direct": direct, "selling": selling,
            "profit": profit, "margin": (profit / selling * 100).quantize(Decimal("0.01")), "hst": tax,
            "total": selling + tax}


def labour_block() -> list:
    rows = ["## Labour build-up (proposed for Joel's approval)", "",
            "Built from the J1 take-off and the supplier quantities. No governed deck production rate exists, so each line is a proposed allowance for a two-person crew: approve it or change any line.", "",
            "| Task | Quantity basis | Man-hours |", "|---|---|---|"]
    rows += [f"| {task} | {basis} | {hours} |" for task, basis, hours in LABOUR_TASKS]
    days = Decimal(PROPOSED_HOURS) / 16
    rows += [f"| **Total** | Two-person crew, about {days.quantize(Decimal('0.1'))} working days | **{PROPOSED_HOURS}** |", ""]
    return rows


def internal_block(chosen) -> str:
    known = BMR + VISTA + PRO_POST
    rows = labour_block() + [
        "## Direct cost and selling price",
        "",
        "| Cost component | Cost (pre-HST) | Evidence / status |",
        "|---|---|---|",
        f"| BMR materials | {fmt(BMR)} | Written: estimate 237147/1, 26 Oct 2026 |",
        f"| Vista railing and gate | {fmt(VISTA)} | Written: quote 87915-165209 at **MSRP**; additional to BMR. Used as Brayman's cost until Darcy gives BMR's price. Any discount lowers cost and raises margin; the price to Linda does not change. |",
        f"| Pro Post helical foundation (11 piles, travel, engineer report) | {fmt(PRO_POST)} | Written: OT-2236. Includes the $400 report in full (conditional on the town). Pile count to confirm; reconfirm the lapsed quote. |",
    ]
    if chosen:
        rows += [
            f"| Brayman labour | {fmt(chosen['labour'])} | {chosen['man_hours']} man-hours × $75 (Ben's rate). Build-up below; Joel approves or changes it. |",
            f"| Delivery / carrying | {fmt(chosen['delivery'])} | {'Joel' if chosen['delivery'] else 'BMR: delivery and carrying extra; no amount on any document. $0 (absorbed) until Darcy gives one'} |",
            "| Equipment | $0.00 | None: Pro Post brings its own machine; hand tools only |",
            "| Permit fee | $0.00 | Excluded from Linda's price (as in J1); billed at cost if Brayman pulls the permit |",
            f"| **TOTAL DIRECT COST** | **{fmt(chosen['direct'])}** | |",
            "",
            "Governed pricing: ORG-001-TRUE-GM-15, **true gross margin 15%** (not markup). Selling price = direct cost ÷ 0.85.",
            "",
            "| | Amount |",
            "|---|---|",
            f"| Total direct cost | {fmt(chosen['direct'])} |",
            f"| Gross profit | {fmt(chosen['profit'])} |",
            f"| **Selling price before HST** | **{fmt(chosen['selling'])}** |",
            f"| HST 13% | {fmt(chosen['hst'])} |",
            f"| **Linda estimate total** | **{fmt(chosen['total'])}** |",
            f"| Resulting true gross margin | {chosen['margin']}% |",
            "",
            f"Every 10 man-hours more or less changes the price before HST by {fmt(LABOUR_RATE * 10 / (Decimal(1) - MARGIN))}.",
        ]
    return "\n".join(rows)


CUSTOMER_TEMPLATE = """# Linda Bushel — Pool Deck Estimate

Date: 2026-10-27

Prepared for: Linda Bushel, 12 D'Arcy's Way, Kemptville, ON K0G 1J0

Prepared by: Brayman Construction Inc., 411 St. John Street, Merrickville, ON K0G 1N0

## Project

A new freestanding deck beside your above-ground pool: an upper deck at the pool, a full-width stair, and a small lower deck with a gate. Supply and installation.

## Scope of work

**Foundation**

- Galvanized steel helical piles with adjustable steel brackets, installed by a specialist foundation contractor. No concrete footings.
- Engineer's report and compliance letter for the piles, if the town asks for it with the permit.

**Structure**

- Pressure-treated structural framing: built-up 2×10 beams, 2×8 joists, 6×6 posts and 2×12 stair stringers.
- Galvanized structural connectors, hangers, bolts and structural screws.
- The upper deck edge follows the curve of the pool. The deck stands on its own and is not attached to the pool.

**Decking and finish**

- Trex Select composite decking in Island Mist on the upper deck, the lower deck and the stair treads.
- Trex Island Mist fascia on the exposed edges, with colour-matched screws.
- Trex deck fasteners.

**Upper deck, stairs and lower deck**

- Upper deck about 18 ft wide, with about 5 ft of clear deck at the centre of the pool.
- 10 ft wide stairs from the upper deck down to the lower deck.
- Lower deck 10 ft wide by 3 ft deep.

**Railing and gate**

- Vista 42 in aluminium railing, textured black, standard pickets: upper deck sides and front, both sides of the stairs, and the lower deck.
- Matching Vista gate, 42 in high and 48 in wide, centred on the lower deck.

**Installation**

- Complete installation by Brayman Construction, and clean-up of construction debris.

## Price

| | |
|---|---|
| Estimate subtotal | {selling} |
| HST 13% | {hst} |
| **TOTAL ESTIMATE** | **{total}** |

## Assumptions

- Pool about 21 ft in diameter and about 50 in high; all sizes are checked on site before materials are ordered.
- Access to the back yard for the pile machine (about 46 in wide; a gate or fence panel may need to be removed and replaced).
- Underground services are located before the piles go in; private buried lines (pool, power, irrigation) are pointed out by the owner.
- Normal soil. If the piles must go deeper than planned, extensions are extra and agreed with you first.
- Installation outside freezing winter conditions.
- Island Mist colour and the layout shown on our plan, confirmed with you before ordering.

## Not included

- Town building-permit fee (Brayman can apply for the permit; the town's fee is billed at cost).
- Changes to the pool, its equipment or its fence, other than reinstalling a removed panel.
- A guard along the open pool edge, skirting under either deck, electrical work, lighting, landscaping or grading.
- Removal of an existing deck or structure.

## Validity

Material and foundation prices come from our suppliers' current quotations and are held for a short time. This estimate is valid for 7 days. A signed agreement and deposit confirm the order.
"""


def write(chosen) -> None:
    text = INTERNAL.read_text(encoding="utf-8")
    start, end = text.index(BEGIN) + len(BEGIN), text.index(END)
    INTERNAL.write_text(text[:start] + "\n" + internal_block(chosen) + "\n" + text[end:], encoding="utf-8")
    if chosen:
        CUSTOMER.write_text(CUSTOMER_TEMPLATE.format(selling=fmt(chosen["selling"]), hst=fmt(chosen["hst"]),
                                                     total=fmt(chosen["total"])), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--man-hours", type=int, default=PROPOSED_HOURS)
    parser.add_argument("--delivery", type=Decimal, default=Decimal("0"))
    args = parser.parse_args()
    chosen = price(args.man_hours, args.delivery)
    write(chosen)
    print("internal sheet updated", "with" if chosen else "without", "a chosen labour figure")
    if chosen:
        import issue_2026_10_27

        issue_2026_10_27.main()
        print({k: str(v) for k, v in chosen.items()})


if __name__ == "__main__":
    main()

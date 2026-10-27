"""Linda Bushel pool deck — direct cost and selling price, 27 Oct 2026.

One calculation for Ben's internal sheet and Linda's estimate. Written supplier amounts are constants
copied from the originals in supplier/ (see the .md records beside them). Brayman labour is the only
input this repository cannot supply: no governed deck production rate, Linda labour estimate or
historical Brayman deck labour exists (searched 27 Oct 2026; see the internal sheet). Joel supplies the
man-hours; the rate and the margin are governed (docs/pricing-policy.md, ORG-001 records).

    python price_2026_10_27.py                      # internal sheet with the labour table; no customer price
    python price_2026_10_27.py --man-hours 100      # internal sheet, Linda's priced estimate, PDFs, package
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
LABOUR_RATE = Decimal("65")         # ORG-001 direct labour cost, $ per man-hour (APPROVED, 29 Aug 2026)
MARGIN = Decimal("0.15")            # ORG-001-TRUE-GM-15: selling price = direct cost / (1 - 0.15)
HST = Decimal("0.13")               # Ontario HST, applied after the pre-tax selling price
SCENARIOS = (80, 100, 120, 140)


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


def internal_block(chosen) -> str:
    known = BMR + VISTA + PRO_POST
    rows = [
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
            f"| Brayman labour | {fmt(chosen['labour'])} | {chosen['man_hours']} man-hours approved by Joel × $65 (governed rate) |",
            f"| Delivery / carrying | {fmt(chosen['delivery'])} | {'Joel' if chosen['delivery'] else 'Not charged separately — absorbed (Joel)'} |",
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
        ]
    else:
        rows += [
            f"| Brayman labour | **NOT SET** | **Need Joel to approve the total man-hours** (rate $65, governed). No governed deck production rate, Linda labour estimate or Brayman deck history exists. |",
            "| Delivery / carrying | $0.00 unless Joel gives an amount | BMR: \"delivery extra, carrying extra\"; no amount on any document |",
            "| Equipment | $0.00 | None: Pro Post brings its own machine |",
            "| Permit fee | $0.00 | Excluded from Linda's price (as in J1) |",
            f"| **Total direct cost before labour** | **{fmt(known)}** | All three written supplier amounts |",
            "",
            "Governed pricing: ORG-001-TRUE-GM-15, **true gross margin 15%** (not markup). Selling price = direct cost ÷ 0.85.",
            "",
            "Choose the man-hours (2-person crew; 8 h days: 80 h = 5 days, 100 h = 6¼ days, 120 h = 7½ days, 140 h = 8¾ days):",
            "",
            "| Man-hours | Labour | Total direct cost | Gross profit | Selling price before HST | HST 13% | Linda total |",
            "|---|---|---|---|---|---|---|",
        ]
        for hours in SCENARIOS:
            p = price(hours)
            rows.append(f"| {hours} | {fmt(p['labour'])} | {fmt(p['direct'])} | {fmt(p['profit'])} | {fmt(p['selling'])} | {fmt(p['hst'])} | {fmt(p['total'])} |")
        rows += ["", "Each man-hour adds $65.00 of cost and $76.47 to the price before HST ($86.41 with HST)."]
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
- A guard along the open pool edge, skirting, electrical work, lighting, landscaping or grading.
- Removal of an existing deck or structure.

## Validity

Material and foundation prices come from our suppliers' current quotations and are held for a short time. This estimate is valid for 14 days. A signed agreement and deposit confirm the order.
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
    parser.add_argument("--man-hours", type=int)
    parser.add_argument("--delivery", type=Decimal, default=Decimal("0"))
    args = parser.parse_args()
    chosen = price(args.man_hours, args.delivery) if args.man_hours else None
    write(chosen)
    print("internal sheet updated", "with" if chosen else "without", "a chosen labour figure")
    if chosen:
        import issue_2026_10_27

        issue_2026_10_27.main()
        print({k: str(v) for k, v in chosen.items()})


if __name__ == "__main__":
    main()

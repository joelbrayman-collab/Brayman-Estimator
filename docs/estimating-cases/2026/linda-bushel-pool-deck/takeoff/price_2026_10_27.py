"""Linda Bushel pool deck — direct cost and selling price, 27 Oct 2026.

One calculation for Masters 01, 02 and 03 (issue_masters_2026_10_27.py writes the documents). Written supplier amounts are constants
copied from the originals in supplier/ (see the .md records beside them). Brayman labour has no governed
production rate: no governed deck production rate, Linda labour estimate or
historical Brayman deck labour exists (searched 27 Oct 2026; see the internal sheet). Joel supplies the
man-hours; the rate and the margin are governed (docs/pricing-policy.md, ORG-001 records).

    python price_2026_10_27.py                      # figures at the proposed labour build-up
    python price_2026_10_27.py --man-hours 100      # figures at a man-hour total Joel chooses instead (prints only)
"""

from __future__ import annotations

import argparse
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]

BMR = Decimal("8676.09")            # BMR Winchester estimate 237147/1, pre-HST
VISTA = Decimal("3851.49")          # Vista 87915-165209: ADDITIONAL to BMR; quoted price is Brayman's cost (Joel, 27 Oct)
PRO_POST = Decimal("3750.00")       # OT-2236 subtotal: 11 piles 3,265 + travel 85 + engineer report 400
LABOUR_RATE = Decimal("75")         # Governed Brayman direct labour rate from 27 Oct 2026 (docs/pricing-policy.md).

# Labour build-up from the J1 take-off and the supplier quantities (27 Oct 2026): Joel's 125 man-hour estimating
# allowance for Ben's review (Ben may adjust any line). Not a governed production rate. Two-person crew, 8-hour days.
LABOUR_TASKS = (
    ("Layout and mark the pile locations", "deck and stair lines; 11 pile locations marked for Pro Post (Pro Post supplies AND installs the piles: no pile labour here)", 4),
    ("Posts and beams", "11 posts cut on brackets; built-up 2×10 beams (7 × 12 ft + 4 × 10 ft), 3/8 in carriage bolts", 16),
    ("Upper-deck framing", "16 joists cut to the pool curve, 8-piece curved header with 14 skewed hangers, blocking", 24),
    ("Lower-deck framing", "9 joists 3 ft, lower beam, blocking, lower posts cut on site", 8),
    ("Stairs", "10 ft wide, 4 treads, 5 risers; stringers cut and hung", 16),
    ("Trex decking", "about 147 sq ft (upper 116.8 + lower 30), every board scribed to the pool curve on the upper deck", 16),
    ("Stair treads and risers (Trex)", "8 tread boards, 5 riser boards 10 ft", 8),
    ("Trex fascia", "about 44 ft of exposed rim, colour-matched screws", 5),
    ("Railing blocking", "solid blocking under each Vista post base", 4),
    ("Vista railing and gate", "11 sections, 14 posts on base plates, pickets, 48 in gate", 16),
    ("Unload and carry materials", "BMR delivery to the back yard (carrying is extra from BMR)", 4),
    ("Clean-up and final walk-through", "debris, offcuts, punch list", 4),
)
PROPOSED_HOURS = sum(hours for _task, _basis, hours in LABOUR_TASKS)
MARGIN = Decimal("0.125")           # Linda Bushel project decision (Ben, 27 Oct 2026): 12.5% TRUE gross margin,
                                    # selling price = direct cost / (1 - 0.125). Project-specific; the organization
                                    # standard ORG-001-TRUE-GM-15 (15%) is unchanged.
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


# Direct-cost components that make up BMR estimate 237147/1 (sum = BMR) and the Pro Post subtotal.
BMR_LINES = (("framing", Decimal("1361.71")), ("hardware", Decimal("389.35")), ("decking", Decimal("4827.20")),
             ("fascia", Decimal("1666.80")), ("fasteners", Decimal("431.03")))
assert sum(v for _k, v in BMR_LINES) == BMR


def customer_lines() -> dict:
    """Linda's selling prices by component (Master 08). Every direct-cost line is divided by (1 - MARGIN) and
    rounded to the cent; the rounding residual, if any, goes on the last labour line so the components add up
    to the selling price exactly. The residual is recorded in the internal case record only."""
    keep = Decimal(1) - MARGIN
    materials = [(k, money(v / keep)) for k, v in BMR_LINES]
    materials += [("vista", money(VISTA / keep)), ("helical", money(PRO_POST / keep))]
    labour = [(task, hours, money(LABOUR_RATE * hours / keep)) for task, _basis, hours in LABOUR_TASKS]
    selling = price(PROPOSED_HOURS)["selling"]
    residual = selling - sum(v for _k, v in materials) - sum(v for _t, _h, v in labour)
    task, hours, value = labour[-1]
    labour[-1] = (task, hours, value + residual)
    out = {"materials": materials, "labour": labour, "residual": residual, "selling": selling,
           "materials_total": sum(v for _k, v in materials), "labour_total": sum(v for _t, _h, v in labour)}
    assert out["materials_total"] + out["labour_total"] == selling
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--man-hours", type=int, default=PROPOSED_HOURS)
    parser.add_argument("--delivery", type=Decimal, default=Decimal("0"))
    args = parser.parse_args()
    print({k: str(v) for k, v in price(args.man_hours, args.delivery).items()})


if __name__ == "__main__":
    main()

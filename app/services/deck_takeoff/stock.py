"""Stock-length allocation. Governed rule pool_deck_takeoff v1.

Cuts are placed on purchasable stock lengths. A stick holds its cuts plus
one kerf between neighbouring cuts. The last cut on a stick needs no kerf
because the offcut takes it.

Several packing passes run and the one that buys the least total length is
kept. Fewer sticks breaks a tie. Offcuts are reported as waste. They are
not reused to reduce another material's purchase.

A cut longer than every stock length is refused. A splice is a design
decision, not a packing decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

TOL = 1e-6


class StockRefusal(ValueError):
    """A cut cannot be placed on any listed stock length."""


@dataclass
class Stick:
    stock_in: float
    cuts: List[Tuple[float, str]] = field(default_factory=list)

    def used_in(self, kerf_in: float) -> float:
        if not self.cuts:
            return 0.0
        return sum(c for c, _ in self.cuts) + kerf_in * (len(self.cuts) - 1)

    def fits(self, cut_in: float, kerf_in: float, stock_in: Optional[float] = None) -> bool:
        stock = self.stock_in if stock_in is None else stock_in
        extra = cut_in + (kerf_in if self.cuts else 0.0)
        return self.used_in(kerf_in) + extra <= stock + TOL

    def offcut_in(self, kerf_in: float) -> float:
        return self.stock_in - self.used_in(kerf_in)


@dataclass(frozen=True)
class Allocation:
    sticks: Tuple[Tuple[float, Tuple[Tuple[float, str], ...], float], ...]
    kerf_in: float
    stock_lengths_in: Tuple[float, ...]
    policy: str

    @property
    def stick_count(self) -> int:
        return len(self.sticks)

    @property
    def purchased_in(self) -> float:
        return sum(s for s, _, _ in self.sticks)

    @property
    def net_in(self) -> float:
        return sum(c for _, cuts, _ in self.sticks for c, _ in cuts)

    @property
    def kerf_loss_in(self) -> float:
        return sum(self.kerf_in * max(0, len(cuts) - 1) for _, cuts, _ in self.sticks)

    @property
    def offcut_in(self) -> float:
        return sum(o for _, _, o in self.sticks)

    @property
    def waste_in(self) -> float:
        return self.purchased_in - self.net_in

    def count_by_stock(self) -> Dict[float, int]:
        out: Dict[float, int] = {}
        for stock, _, _ in self.sticks:
            out[stock] = out.get(stock, 0) + 1
        return dict(sorted(out.items()))

    def as_dict(self) -> dict:
        return {
            "policy": self.policy,
            "kerf_in": self.kerf_in,
            "stock_lengths_in": list(self.stock_lengths_in),
            "stick_count": self.stick_count,
            "count_by_stock_in": {str(_r(k)): v for k, v in self.count_by_stock().items()},
            "purchased_in": _r(self.purchased_in),
            "net_in": _r(self.net_in),
            "kerf_loss_in": _r(self.kerf_loss_in),
            "offcut_in": _r(self.offcut_in),
            "waste_in": _r(self.waste_in),
            "waste_percent": _r(100.0 * self.waste_in / self.purchased_in) if self.purchased_in else 0.0,
            "sticks": [
                {
                    "stock_in": _r(stock),
                    "cuts": [{"length_in": _r(c), "label": label} for c, label in cuts],
                    "offcut_in": _r(off),
                }
                for stock, cuts, off in self.sticks
            ],
        }


def _r(value: float) -> float:
    return round(float(value), 4)


def _validate(pieces, stock_lengths_in, kerf_in):
    if kerf_in is None or not isinstance(kerf_in, (int, float)) or kerf_in < 0:
        raise StockRefusal("A saw kerf (zero or more inches) is required.")
    stocks = sorted({float(s) for s in stock_lengths_in if s and float(s) > 0})
    if not stocks:
        raise StockRefusal("At least one stock length is required.")
    longest = stocks[-1]
    clean = []
    for length, label in pieces:
        length = float(length)
        if length <= 0:
            raise StockRefusal(f"Cut {label} has no length.")
        if length > longest + TOL:
            raise StockRefusal(
                f"Cut {label} is {length:.3f} in. The longest stock is {longest:.0f} in. "
                "A splice location is a design decision."
            )
        clean.append((length, str(label)))
    return clean, stocks


def _best_fit(pieces, stocks, kerf_in, opening):
    sticks: List[Stick] = []
    for length, label in sorted(pieces, key=lambda p: (-p[0], p[1])):
        best = None
        best_left = None
        for stick in sticks:
            if stick.fits(length, kerf_in):
                left = stick.stock_in - stick.used_in(kerf_in) - length - (kerf_in if stick.cuts else 0)
                if best is None or left < best_left - TOL:
                    best, best_left = stick, left
        if best is None:
            size = opening(length)
            best = Stick(stock_in=size)
            sticks.append(best)
        best.cuts.append((length, label))
    for stick in sticks:
        need = stick.used_in(kerf_in)
        stick.stock_in = next(s for s in stocks if s + TOL >= need)
    return sticks


def allocate(
    pieces: Sequence[Tuple[float, str]],
    stock_lengths_in: Sequence[float],
    kerf_in: float,
) -> Allocation:
    """Place every cut on stock. Return the cheapest of several passes."""
    clean, stocks = _validate(pieces, stock_lengths_in, kerf_in)
    if not clean:
        return Allocation(sticks=(), kerf_in=kerf_in, stock_lengths_in=tuple(stocks), policy="empty")
    candidates = []
    for size in stocks:
        def opening(length, size=size):
            if length <= size + TOL:
                return size
            return next(s for s in stocks if s + TOL >= length)

        candidates.append((f"open {size:.0f} in, best fit, shrink", _best_fit(clean, stocks, kerf_in, opening)))

    def smallest(length):
        return next(s for s in stocks if s + TOL >= length)

    candidates.append(("open smallest fitting stock, best fit, shrink", _best_fit(clean, stocks, kerf_in, smallest)))

    def score(item):
        _, sticks = item
        return (round(sum(s.stock_in for s in sticks), 6), len(sticks))

    policy, chosen = min(candidates, key=score)
    frozen = tuple(
        (
            stick.stock_in,
            tuple(stick.cuts),
            stick.offcut_in(kerf_in),
        )
        for stick in sorted(chosen, key=lambda s: (-s.stock_in, -s.used_in(kerf_in)))
    )
    return Allocation(sticks=frozen, kerf_in=float(kerf_in), stock_lengths_in=tuple(stocks), policy=policy)


def recorded_allocation(groups: Sequence[Sequence[Tuple[float, str]]], stock_in: float, kerf_in: float) -> Allocation:
    """An allocation written down in a governing issue. Each group is one stick."""
    sticks = []
    for cuts in groups:
        stick = Stick(stock_in=float(stock_in), cuts=[(float(c), str(l)) for c, l in cuts])
        if stick.used_in(kerf_in) > stick.stock_in + TOL:
            raise StockRefusal("A recorded stick holds more than its stock length.")
        sticks.append((stick.stock_in, tuple(stick.cuts), stick.offcut_in(kerf_in)))
    return Allocation(sticks=tuple(sticks), kerf_in=float(kerf_in), stock_lengths_in=(float(stock_in),), policy="recorded")


def allocate_by_use(groups, stock_lengths_in: Sequence[float], kerf_in: float, reuse_across_uses: bool) -> Allocation:
    """Allocate cuts that belong to named uses.

    When offcuts may not be reused across uses, each use is packed on its
    own sticks, as the J1 issue did ("offcuts are not reused to reduce the
    purchase"). Otherwise every cut is packed together.
    """
    groups = {use: list(cuts) for use, cuts in groups.items() if cuts}
    if reuse_across_uses:
        merged = [cut for use in sorted(groups) for cut in groups[use]]
        allocation = allocate(merged, stock_lengths_in, kerf_in)
        return Allocation(
            sticks=allocation.sticks,
            kerf_in=allocation.kerf_in,
            stock_lengths_in=allocation.stock_lengths_in,
            policy=f"offcuts reused across uses; {allocation.policy}",
        )
    sticks = []
    stocks = None
    policies = []
    for use in sorted(groups):
        part = allocate(groups[use], stock_lengths_in, kerf_in)
        sticks.extend(part.sticks)
        stocks = part.stock_lengths_in
        policies.append(f"{use}: {part.policy}")
    if stocks is None:
        _clean, stocks = _validate([], stock_lengths_in, kerf_in)
        stocks = tuple(stocks)
    return Allocation(
        sticks=tuple(sorted(sticks, key=lambda s: (-s[0], -(s[0] - s[2])))),
        kerf_in=float(kerf_in),
        stock_lengths_in=tuple(stocks),
        policy="each use on its own sticks (" + "; ".join(policies) + ")",
    )

"""Guard, stair-rail, and fascia runs for a centred stair and lower deck.

The runs and their junctions come from the plan. Panel and post counts
need the railing product's panel lengths and post spacing. Those stay
unresolved until the product facts are supplied.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from app.services.deck_takeoff.geometry import CurvedDeck, GeometryRefusal


@dataclass(frozen=True)
class Run:
    key: str
    label: str
    length_ft: float
    kind: str  # level | stair
    horizontal_ft: float


@dataclass(frozen=True)
class Chain:
    side: str
    runs: Tuple[Run, ...]
    junctions: Tuple[str, ...]  # between consecutive runs
    start: str
    end: str


def guard_chains(deck: CurvedDeck, *, stair_width_ft, lower_width_ft, lower_depth_ft, gate_clear_in, stair_run_ft, rise_in) -> Tuple[Chain, ...]:
    """Two mirrored guard chains, from the pool edge to the gate."""
    if abs(lower_width_ft - stair_width_ft) > 1e-6:
        raise GeometryRefusal(
            "This rule needs the lower deck as wide as the stair. Another layout needs its own run rule."
        )
    if stair_width_ft >= deck.width_ft:
        raise GeometryRefusal("The stair must be narrower than the upper deck.")
    gate_ft = gate_clear_in / 12.0
    if gate_ft >= lower_width_ft:
        raise GeometryRefusal("The gate opening is wider than the lower deck front.")
    side = deck.side_length_ft
    front_return = (deck.width_ft - stair_width_ft) / 2.0
    slope = math.hypot(stair_run_ft * 12.0, rise_in) / 12.0
    lower_return = (lower_width_ft - gate_ft) / 2.0
    chains = []
    for name in ("left", "right"):
        runs = (
            Run(f"upper-side-{name}", f"Upper {name} side", side, "level", side),
            Run(f"upper-front-{name}", f"Upper front {name} of stair", front_return, "level", front_return),
            Run(f"stair-{name}", f"Stair {name}", slope, "stair", stair_run_ft),
            Run(f"lower-side-{name}", f"Lower {name} side", lower_depth_ft, "level", lower_depth_ft),
            Run(f"lower-front-{name}", f"Lower front {name} of gate", lower_return, "level", lower_return),
        )
        chains.append(
            Chain(
                side=name,
                runs=runs,
                junctions=("level corner", "stair top", "stair bottom", "level corner"),
                start="free end at the pool edge",
                end="gate post",
            )
        )
    return tuple(chains)


def topology_counts(chains: Sequence[Chain]) -> Dict[str, int]:
    counts = {"level corner": 0, "stair top": 0, "stair bottom": 0, "free end at the pool edge": 0, "gate post": 0}
    for chain in chains:
        for junction in chain.junctions:
            counts[junction] += 1
        counts[chain.start] += 1
        counts[chain.end] += 1
    return counts


def fascia_runs(deck: CurvedDeck, *, stair_width_ft, lower_width_ft, lower_depth_ft) -> Tuple[Tuple[str, float], ...]:
    """Exposed straight rims. The open pool edge, the stair opening on the
    upper front, and the lower-deck back edge under the stair are left open."""
    side = deck.side_length_ft
    front_return = (deck.width_ft - stair_width_ft) / 2.0
    return (
        ("Upper left side", side),
        ("Upper right side", side),
        ("Upper front left of stair", front_return),
        ("Upper front right of stair", front_return),
        ("Lower left side", lower_depth_ft),
        ("Lower right side", lower_depth_ft),
        ("Lower front", lower_width_ft),
    )


def panel_plan(run: Run, *, panel_lengths_ft: Sequence[float], max_post_spacing_in: float, cut_to_length: bool, span_basis: str) -> Dict:
    """Bays and panels for one run. Bays are equal. A panel is cut to the bay."""
    measured = run.horizontal_ft if (run.kind == "level" or span_basis == "horizontal") else run.length_ft
    longest = max(panel_lengths_ft)
    by_panel = math.ceil(measured / longest - 1e-9)
    by_post = math.ceil(measured * 12.0 / max_post_spacing_in - 1e-9)
    bays = max(1, by_panel, by_post)
    bay_ft = measured / bays
    fitting = [p for p in sorted(panel_lengths_ft) if p + 1e-9 >= bay_ft]
    exact = [p for p in panel_lengths_ft if abs(p - bay_ft) < 1e-6]
    if exact:
        panel = exact[0]
    elif cut_to_length and fitting:
        panel = fitting[0]
    else:
        return {"run": run.key, "measured_ft": measured, "bays": bays, "bay_ft": bay_ft, "panel_ft": None, "refused": "No listed panel fits this bay without cutting, and cutting is not allowed."}
    return {"run": run.key, "measured_ft": measured, "bays": bays, "bay_ft": bay_ft, "panel_ft": panel, "refused": None}


def chain_posts(plans_by_run: Dict[str, Dict], chain: Chain) -> int:
    """Posts shared at junctions: one more post than bays along a chain."""
    return 1 + sum(plans_by_run[run.key]["bays"] for run in chain.runs)

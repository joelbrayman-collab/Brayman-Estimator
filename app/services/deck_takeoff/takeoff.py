"""Complete pool-deck material takeoff. Governed rule pool_deck_takeoff v1.

Brayman calculates. The supplier prices. This module calculates every
quantity the stored project facts support, places cuts on stock, and keeps
each open fact visible on the line that needs it. It writes nothing.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from app.services.deck_takeoff import product_facts as pf
from app.services.deck_takeoff.basis import DeckBasis
from app.services.deck_takeoff.geometry import (
    CurvedDeck,
    GeometryRefusal,
    bays_in,
    boards_per_tread,
    crossings_upper,
    max_spacing_in,
    rectangle_courses,
    split_at,
    upper_courses,
)
from app.services.deck_takeoff.railing import (
    chain_posts,
    fascia_runs,
    guard_chains,
    panel_plan,
    topology_counts,
)
from app.services.deck_takeoff.records import (
    CALCULATED,
    ENGINEERING_REQUIRED,
    FIELD_VERIFICATION_REQUIRED,
    PRODUCT_DEPENDENT,
    RULE_ID,
    RULE_VERSION,
    fingerprint,
    flag,
    line,
    r3,
    worst,
)
from app.services.deck_takeoff.catalogue import identity_for_line, lumber_identity
from app.services.deck_takeoff.stock import StockRefusal, allocate, allocate_by_use

BRAYMAN = "Brayman"
SUPPLIER = "Supplier / manufacturer"
ENGINEER = "Engineer or municipal review"
FIELD = "Field measurement"


def _product_flags(facts, category, names):
    return [
        flag(PRODUCT_DEPENDENT, pf.label(q), SUPPLIER if not q.startswith("cutting.") else BRAYMAN)
        for q in pf.missing(facts, category, names)
    ]


def _ft_in(feet: float) -> str:
    whole = int(math.floor(feet + 1e-9))
    sixteenths = int(round((feet - whole) * 192))
    if sixteenths >= 192:
        whole += 1
        sixteenths -= 192
    inches, rem = divmod(sixteenths, 16)
    if rem == 0:
        return f"{whole}'-{inches}\""
    g = math.gcd(rem, 16)
    return f"{whole}'-{inches} {rem // g}/{16 // g}\""


class _Collector:
    def __init__(self):
        self.lines: List[dict] = []

    def add(self, item: dict) -> dict:
        self.lines.append(item)
        return item


def calculate_pool_deck_takeoff(basis: DeckBasis, product_facts: Optional[Mapping] = None) -> dict:
    facts = pf.clean_product_facts(product_facts)
    out = _Collector()
    deck = CurvedDeck(
        pool_radius_ft=basis.pool_radius_ft,
        width_ft=basis.upper_width_ft,
        clear_depth_ft=basis.upper_clear_depth_ft,
    )
    kerf = facts["cutting"].get("kerf_in")
    kerf_flags = _product_flags(facts, "cutting", ["kerf_in"])
    deck_facts = facts["decking"]

    geometry = {
        "pool_radius_ft": r3(deck.pool_radius_ft),
        "front_edge_out_ft": r3(deck.front_y_ft),
        "side_meets_pool_out_ft": r3(deck.side_y_ft),
        "side_length_ft": r3(deck.side_length_ft),
        "upper_area_sqft": r3(deck.area_sqft),
        "rectangle_area_sqft": r3(deck.rectangle_area_sqft),
        "pool_bite_area_sqft": r3(deck.pool_bite_area_sqft),
        "open_pool_edge_ft": r3(deck.pool_edge_arc_ft),
        "lower_area_sqft": r3(basis.lower_width_ft * basis.lower_depth_ft),
        "stair_run_ft": r3(basis.stair_run_ft),
        "riser_count": basis.riser_count,
        "riser_height_in": r3(basis.rise_in / basis.riser_count) if basis.riser_count else None,
        "upper_joist_max_spacing_in": r3(max_spacing_in(basis.upper_joists_ft)),
        "lower_joist_max_spacing_in": r3(max_spacing_in(basis.lower_joists_ft)),
        "stringer_max_spacing_in": r3(max_spacing_in(basis.stringers_ft)),
    }

    _boards(out, basis, deck, facts, kerf, kerf_flags, geometry)
    _fascia(out, basis, deck, facts, kerf, kerf_flags)
    _railing(out, basis, deck, facts)
    _gate(out, basis, facts)
    _structure(out, basis, deck, kerf, kerf_flags, facts)
    _piers_and_connectors(out, basis, deck, facts)
    _skirting(out, basis)

    engineering = [
        flag(ENGINEERING_REQUIRED, "Structural adequacy of the retained framing (spans, beams, posts, connections) is not certified.", ENGINEER),
        flag(ENGINEERING_REQUIRED, "Pool-enclosure compliance (1.2 m barrier, self-closing and self-latching gate) is not confirmed.", ENGINEER),
    ]
    field_items = [
        flag(FIELD_VERIFICATION_REQUIRED, note, FIELD) for note in basis.field_notes
    ]
    open_items: List[dict] = []
    seen = set()
    for item in out.lines:
        for f in item["flags"]:
            key = (f["status"], f["fact"], f["needed_from"])
            if key not in seen:
                seen.add(key)
                open_items.append({**f, "lines": [item["key"]]})
            else:
                for existing in open_items:
                    if (existing["status"], existing["fact"], existing["needed_from"]) == key:
                        existing["lines"].append(item["key"])
    for item in out.lines:
        if item["canonical_material_code"] or not item["request"]:
            continue
        seed = item.get("canonical_identity") or identity_for_line(item, facts)
        if seed is not None:
            item["canonical_identity"] = seed
            item["canonical_material_code"] = seed["code"]
    requested = [item for item in out.lines if item["request"]]
    result = {
        "rule": {"id": RULE_ID, "version": RULE_VERSION},
        "source": dict(basis.source),
        "inputs": {
            "basis": basis.input_record(),
            "product_facts": facts,
            "structural_specification": basis.structural,
            "finish_specification": basis.finish,
        },
        "geometry": geometry,
        "lines": out.lines,
        "open_items": open_items,
        "project_items": engineering + field_items,
        # Every line that buys something must be final, whether or not it is sent to the supplier.
        "purchasing_complete": all(item["purchasing"]["complete"] for item in out.lines if item["purchasing"]["unit"]),
        "status_counts": _status_counts(requested),
    }
    result["fingerprint"] = fingerprint({k: v for k, v in result.items() if k != "fingerprint"})
    return result


def _status_counts(lines):
    counts = {CALCULATED: 0, FIELD_VERIFICATION_REQUIRED: 0, PRODUCT_DEPENDENT: 0, ENGINEERING_REQUIRED: 0}
    for item in lines:
        counts[item["status"]] += 1
    return counts


# ---------------------------------------------------------------- boards


def _boards(out, basis, deck, facts, kerf, kerf_flags, geometry):
    d = facts["decking"]
    spec = basis.finish.get("decking") or "PVC/composite deck boards. Straight boards parallel to the front edge. Pool ends cut to the curve. Boards are not bent."
    type_flags = _product_flags(facts, "decking", ["product_type", "product_name"])
    width = d.get("actual_width_in")
    gap = d.get("gap_in")
    layout_flags = _product_flags(facts, "decking", ["actual_width_in", "gap_in"])
    overhang = d.get("end_overhang_in")
    overhang_flags = _product_flags(facts, "decking", ["end_overhang_in"])
    oh_ft = (overhang or 0.0) / 12.0

    pieces: List[Tuple[float, str]] = []
    crossings = {}
    support_flags = []
    # Support spacing against the manufacturer limit. A shortfall is a framing change.
    limit = d.get("max_joist_spacing_in")
    if limit is None:
        support_flags += _product_flags(facts, "decking", ["max_joist_spacing_in"])
    else:
        for label_, stations in (("upper joists", basis.upper_joists_ft), ("lower joists", basis.lower_joists_ft)):
            spacing = max_spacing_in(stations)
            if spacing is not None and spacing > limit + 1e-6:
                support_flags.append(
                    flag(
                        ENGINEERING_REQUIRED,
                        f"The {label_} are up to {spacing:.2f} in apart. The board allows {limit:.2f} in. Added framing is a structural change that is not authorized.",
                        BRAYMAN,
                    )
                )

    # Upper deck.
    if width is not None and gap is not None:
        layout = upper_courses(deck, width, gap)
        cut_rows = []
        rip_flags = []
        skipped_rows = 0
        for c in layout.courses:
            if c.kind == "ripped":
                keep, extra = _rip_decision(c.board_width_in, d, "Upper deck front band")
                rip_flags += extra
                if not keep:
                    skipped_rows += 1
                    continue
            if c.band == "A":
                length = c.piece_length_ft + 2 * oh_ft
                label_ = f"Upper row A{c.index}" + (f" ripped to {c.board_width_in:.2f} in" if c.kind == "ripped" else "")
                pieces.append((length * 12.0, label_))
                cut_rows.append({"row": f"A{c.index}", "kind": c.kind, "board_width_in": r3(c.board_width_in), "pieces": 1, "length_ft": r3(length), "length": _ft_in(length)})
            else:
                length = c.piece_length_ft + oh_ft
                for side in ("left", "right"):
                    pieces.append((length * 12.0, f"Upper row B{c.index} {side}, pool end cut to the curve"))
                cut_rows.append({"row": f"B{c.index}", "kind": "curve", "board_width_in": r3(c.board_width_in), "pieces": 2, "length_ft": r3(length), "length": _ft_in(length), "pool_end_starts_ft_from_centre": r3(c.inner_x_ft)})
        crossings["upper"] = crossings_upper(layout, basis.upper_joists_ft) - skipped_rows * len(basis.upper_joists_ft)
        remainder = layout.corner_remainder_in
        rem_flags = list(rip_flags)
        min_rip = d.get("min_rip_width_in")
        if remainder > 1e-6:
            if min_rip is None:
                rem_flags.append(flag(PRODUCT_DEPENDENT, pf.label("decking.min_rip_width_in"), SUPPLIER))
                rem_flags.append(flag(FIELD_VERIFICATION_REQUIRED, f"Corner remainder of {remainder:.2f} in beside the pool at each side. Whether a ripped board is bought waits for the narrowest allowed rip.", FIELD))
            elif remainder + 1e-6 >= min_rip:
                inner = deck.side_y_ft + remainder / 12.0
                from app.services.deck_takeoff.geometry import pool_wall_x

                rem_len = deck.half_width_ft - pool_wall_x(deck.pool_radius_ft, inner) + oh_ft
                for side in ("left", "right"):
                    pieces.append((rem_len * 12.0, f"Upper corner rip {side}, {remainder:.2f} in wide"))
                reach = pool_wall_x(deck.pool_radius_ft, inner)
                crossings["upper"] += sum(1 for x in basis.upper_joists_ft if abs(x) >= reach - 1e-6)
                cut_rows.append({"row": "B-corner", "kind": "corner rip", "board_width_in": r3(remainder), "pieces": 2, "length_ft": r3(rem_len), "length": _ft_in(rem_len)})
            else:
                rem_flags.append(flag(FIELD_VERIFICATION_REQUIRED, f"Corner remainder of {remainder:.2f} in is narrower than the allowed rip. It is a field fit, not a board.", FIELD))
        geometry["upper_courses"] = {"full_width_rows": layout.full_rows, "ripped_rows": sum(1 for c in layout.courses if c.kind == "ripped"), "curve_rows_each_side": layout.curve_rows, "corner_remainder_in": r3(remainder), "coverage_in": r3(layout.coverage_in)}
        out.add(
            line(
                key="decking.upper",
                group="Decking",
                description="Upper deck boards, straight courses parallel to the front edge, pool ends cut to the curve.",
                specification=spec,
                construction_quantity=r3(deck.area_sqft),
                construction_unit="sq ft",
                cuts=cut_rows,
                inputs={"actual_width_in": width, "gap_in": gap, "end_overhang_in": overhang},
                flags=type_flags + overhang_flags + rem_flags + support_flags,
                request=False,
            )
        )
    else:
        out.add(
            line(
                key="decking.upper",
                group="Decking",
                description="Upper deck boards. Courses wait for the board width and gap.",
                specification=spec,
                construction_quantity=r3(deck.area_sqft),
                construction_unit="sq ft",
                flags=type_flags + layout_flags + support_flags,
                request=False,
            )
        )

    # Lower deck.
    if width is not None and gap is not None:
        lower = rectangle_courses(basis.lower_depth_ft, basis.lower_width_ft, width, gap, "L")
        rows = []
        lower_flags = []
        bought = 0
        for c in lower.courses:
            if c.kind == "ripped":
                keep, extra = _rip_decision(c.board_width_in, d, "Lower deck")
                lower_flags += extra
                if not keep:
                    continue
            bought += 1
            length = c.piece_length_ft + 2 * oh_ft
            pieces.append((length * 12.0, f"Lower row L{c.index}" + (f" ripped to {c.board_width_in:.2f} in" if c.kind == "ripped" else "")))
            rows.append({"row": f"L{c.index}", "kind": c.kind, "board_width_in": r3(c.board_width_in), "pieces": 1, "length_ft": r3(length), "length": _ft_in(length)})
        crossings["lower"] = bought * len(basis.lower_joists_ft)
        out.add(
            line(
                key="decking.lower",
                group="Decking",
                description="Lower deck boards, straight courses parallel to the lower front.",
                specification=spec,
                construction_quantity=r3(basis.lower_width_ft * basis.lower_depth_ft),
                construction_unit="sq ft",
                cuts=rows,
                inputs={"actual_width_in": width, "gap_in": gap},
                flags=type_flags + overhang_flags + lower_flags,
                request=False,
            )
        )
    else:
        out.add(
            line(
                key="decking.lower",
                group="Decking",
                description="Lower deck boards. Courses wait for the board width and gap.",
                specification=spec,
                construction_quantity=r3(basis.lower_width_ft * basis.lower_depth_ft),
                construction_unit="sq ft",
                flags=type_flags + layout_flags,
                request=False,
            )
        )

    # Treads.
    tread_flags = list(type_flags)
    nosing = d.get("tread_nosing_overhang_in")
    tread_flags += _product_flags(facts, "decking", ["tread_nosing_overhang_in"])
    stair_limit = d.get("max_stair_stringer_spacing_in")
    stringer_spacing = max_spacing_in(basis.stringers_ft)
    if stair_limit is None:
        tread_flags += _product_flags(facts, "decking", ["max_stair_stringer_spacing_in"])
    elif stringer_spacing is not None and stringer_spacing > stair_limit + 1e-6:
        tread_flags.append(
            flag(
                ENGINEERING_REQUIRED,
                f"The stringers are up to {stringer_spacing:.2f} in apart. Treads of this board allow {stair_limit:.2f} in. More stringers is a structural change that is not authorized.",
                BRAYMAN,
            )
        )
    if width is not None and gap is not None and nosing is not None and basis.tread_count:
        surface = basis.tread_depth_in + nosing
        full, rip, _ = boards_per_tread(surface, width, gap)
        keep, extra = _rip_decision(rip, d, "Each tread")
        tread_flags += extra
        if not keep:
            rip = None
        per = full + (1 if rip is not None else 0)
        length = basis.stair_width_ft + 2 * oh_ft
        rows = []
        for t in range(1, basis.tread_count + 1):
            for b in range(1, per + 1):
                ripped = rip is not None and b == per
                pieces.append((length * 12.0, f"Tread {t} board {b}" + (f" ripped to {rip:.2f} in" if ripped else "")))
        rows.append({"row": "each tread", "boards": per, "ripped_last_board_in": r3(rip), "length_ft": r3(length), "length": _ft_in(length), "treads": basis.tread_count})
        crossings["treads"] = basis.tread_count * per * len(basis.stringers_ft)
        out.add(
            line(
                key="decking.treads",
                group="Stairs",
                description=f"Stair tread boards, {basis.tread_count} treads.",
                specification=spec,
                construction_quantity=basis.tread_count * per,
                construction_unit="boards",
                cuts=rows,
                inputs={"tread_depth_in": basis.tread_depth_in, "nosing_overhang_in": nosing, "actual_width_in": width, "gap_in": gap},
                flags=tread_flags + overhang_flags,
                request=False,
            )
        )
    else:
        out.add(
            line(
                key="decking.treads",
                group="Stairs",
                description=f"Stair tread boards, {basis.tread_count} treads, {basis.stair_width_ft:g} ft wide. Boards per tread wait for the board facts.",
                specification=spec,
                construction_quantity=basis.tread_count,
                construction_unit="treads",
                flags=tread_flags + layout_flags,
                request=False,
            )
        )

    # Risers.
    closure = d.get("riser_closure")
    riser_h = basis.rise_in / basis.riser_count if basis.riser_count else None
    if closure == "required":
        rb = d.get("riser_board_width_in")
        if rb is None:
            out.add(line(key="decking.risers", group="Stairs", description="Riser boards.", construction_quantity=basis.riser_count, construction_unit="risers", flags=_product_flags(facts, "decking", ["riser_board_width_in"]), request=False))
        else:
            per = math.ceil(riser_h / rb - 1e-9)
            length = basis.stair_width_ft
            for i in range(1, basis.riser_count + 1):
                for b in range(per):
                    pieces.append((length * 12.0, f"Riser {i} board {b + 1}"))
            out.add(line(key="decking.risers", group="Stairs", description=f"Riser boards, {basis.riser_count} risers at {riser_h:.2f} in.", construction_quantity=basis.riser_count * per, construction_unit="boards", cuts=[{"row": "each riser", "boards": per, "length_ft": r3(length)}], inputs={"riser_height_in": r3(riser_h), "riser_board_width_in": rb}, flags=list(type_flags), request=False))
    elif closure is None:
        out.add(line(key="decking.risers", group="Stairs", description=f"Riser closure for {basis.riser_count} risers at {riser_h:.2f} in." if riser_h else "Riser closure.", construction_quantity=basis.riser_count, construction_unit="risers", flags=_product_flags(facts, "decking", ["riser_closure"]), request=False))

    nosing_choice = d.get("nosing")
    if nosing_choice != "not_used":
        nosing_flags = _product_flags(facts, "decking", ["nosing"])
        nosing_qty = None
        nosing_len = d.get("nosing_stock_length_ft")
        if nosing_choice == "required":
            if nosing_len is None:
                nosing_flags += _product_flags(facts, "decking", ["nosing_stock_length_ft"])
            else:
                nosing_qty = basis.tread_count * math.ceil(basis.stair_width_ft / nosing_len - 1e-9)
        out.add(
            line(
                key="stairs.nosing",
                group="Stairs",
                description="Compatible stair nosing or tread edge profile.",
                specification="Manufacturer to state whether a separate nosing or edge profile is required for these treads.",
                construction_quantity=basis.tread_count,
                construction_unit="tread edges",
                purchasing_quantity=nosing_qty,
                purchasing_unit="EA",
                stock_length_ft=nosing_len,
                stock_rule="Pieces of the nosing stock to cover the stair width at each tread.",
                flags=nosing_flags,
            )
        )

    # One purchasing line per board stock length. The board is one material.
    stock = d.get("stock_lengths_ft")
    board_flags = list(type_flags) + list(layout_flags) + list(overhang_flags) + list(kerf_flags)
    board_flags += _product_flags(facts, "decking", ["stock_lengths_ft"])
    for item in out.lines:
        if item["key"] in ("decking.upper", "decking.lower", "decking.treads", "decking.risers"):
            board_flags += [f for f in item["flags"] if f["status"] in (PRODUCT_DEPENDENT, ENGINEERING_REQUIRED)]
    allocation = None
    refusal = None
    reuse, reuse_flags = _offcut_policy(facts)
    board_flags += reuse_flags
    if pieces and stock and kerf is not None:
        try:
            by_use = {}
            for cut in pieces:
                by_use.setdefault(_use_of(cut[1]), []).append(cut)
            allocation = allocate_by_use(by_use, [s * 12.0 for s in stock], kerf, reuse)
        except StockRefusal as exc:
            refusal = str(exc)
            board_flags.append(flag(PRODUCT_DEPENDENT, refusal, SUPPLIER))
    board_flags = _dedupe(board_flags)
    fasteners = _deck_fasteners(crossings, d)
    if allocation is not None:
        for stock_in, count in allocation.count_by_stock().items():
            sticks = [s for s in allocation.sticks if s[0] == stock_in]
            net = sum(c for _, cuts, _ in sticks for c, _ in cuts)
            out.add(
                line(
                    key=f"decking.boards.{stock_in / 12.0:g}ft",
                    group="Decking",
                    description=f"PVC/composite deck boards, {stock_in / 12.0:g} ft.",
                    specification=spec + (f" Product: {d.get('product_name')}." if d.get("product_name") else ""),
                    construction_quantity=r3(net / 12.0),
                    construction_unit="lin ft of cuts",
                    purchasing_quantity=count,
                    purchasing_unit="EA",
                    stock_length_ft=stock_in / 12.0,
                    stock_rule=f"Upper, lower, tread{', riser' if closure == 'required' else ''} cuts placed together on the listed stock lengths. {allocation.policy}.",
                    waste={"rule": "Offcut on purchased stock plus kerf. Offcuts are not reused.", "waste_in": r3(sum(o for _, _, o in sticks) + kerf * sum(max(0, len(c) - 1) for _, c, _ in sticks)), "purchased_in": r3(stock_in * count)},
                    allocation={"overall": allocation.as_dict()} if stock_in == min(allocation.count_by_stock()) else None,
                    inputs={"stock_lengths_ft": stock, "kerf_in": kerf},
                    flags=board_flags,
                )
            )
    else:
        out.add(
            line(
                key="decking.boards",
                group="Decking",
                description="PVC/composite deck boards for the upper deck, lower deck, and stair treads.",
                specification=spec,
                construction_quantity=r3(deck.area_sqft + basis.lower_width_ft * basis.lower_depth_ft),
                construction_unit="sq ft of walking surface, plus treads",
                purchasing_unit="EA",
                stock_rule="Board count waits for the product facts listed on this line.",
                flags=board_flags,
            )
        )
    out.add(fasteners)


def _offcut_policy(facts):
    """(reuse_across_uses, flags). Undecided: pack each use alone, and say so."""
    choice = facts["cutting"].get("offcut_reuse")
    if choice is None:
        return False, [flag(PRODUCT_DEPENDENT, pf.label("cutting.offcut_reuse"), BRAYMAN)]
    return choice == "across_uses", []


def _use_of(label: str) -> str:
    return label.split(" ", 1)[0].lower()


def _rip_decision(rip_in, d, where):
    """Whether a ripped board is bought. A sliver below the allowed rip is a field fit."""
    if rip_in is None:
        return True, []
    minimum = d.get("min_rip_width_in")
    if minimum is None:
        return True, [flag(PRODUCT_DEPENDENT, pf.label("decking.min_rip_width_in"), SUPPLIER)]
    if rip_in + 1e-6 >= minimum:
        return True, []
    return False, [
        flag(
            FIELD_VERIFICATION_REQUIRED,
            f"{where}: a {rip_in:.2f} in strip is narrower than the allowed {minimum:g} in rip. No board is bought for it; the gap or overhang is adjusted on site.",
            FIELD,
        )
    ]


def _deck_fasteners(crossings, d):
    total = sum(crossings.values()) if crossings else None
    flags_ = []
    per = d.get("fasteners_per_crossing")
    pack = d.get("fasteners_per_package")
    for name, value in (("fasteners_per_crossing", per), ("fasteners_per_package", pack)):
        if value is None:
            flags_.append(flag(PRODUCT_DEPENDENT, pf.label(f"decking.{name}"), SUPPLIER))
    if total is None:
        flags_.append(flag(PRODUCT_DEPENDENT, "Board courses, which need the board width and gap", SUPPLIER))
    qty = None
    packages = None
    if total is not None and per is not None:
        qty = total * per
        if pack is not None:
            packages = math.ceil(qty / pack)
    return line(
        key="fasteners.deck",
        group="Fasteners",
        description="Deck board fasteners or hidden clips at each board-to-joist and board-to-stringer crossing.",
        construction_quantity=total,
        construction_unit="crossings",
        purchasing_quantity=packages,
        purchasing_unit="PKG",
        stock_rule=f"{qty} fasteners at {per} per crossing." if qty is not None else "Fasteners per crossing and package size from the manufacturer.",
        inputs={"crossings": crossings},
        flags=flags_,
    )


# ---------------------------------------------------------------- fascia


def _fascia(out, basis, deck, facts, kerf, kerf_flags):
    f = facts["fascia"]
    runs = fascia_runs(deck, stair_width_ft=basis.stair_width_ft, lower_width_ft=basis.lower_width_ft, lower_depth_ft=basis.lower_depth_ft)
    total = sum(length for _, length in runs)
    open_edges = basis.finish.get("fascia_open_edges") or [
        "Open pool edge",
        "Upper front between the stair stringers",
        "Lower-deck back edge under the stair",
    ]
    flags_ = _product_flags(facts, "fascia", ["product_name", "actual_height_in", "thickness_in", "stock_lengths_ft"]) + kerf_flags
    stock = f.get("stock_lengths_ft")
    cuts = []
    pieces = []
    if stock:
        longest = max(stock)
        for name, length in runs:
            n = math.ceil(length / longest - 1e-9)
            piece = length / n
            for i in range(n):
                pieces.append((piece * 12.0, f"{name}" + (f" piece {i + 1} of {n}" if n > 1 else "")))
            cuts.append({"run": name, "run_ft": r3(length), "pieces": n, "piece_ft": r3(piece), "piece": _ft_in(piece)})
        if any(c["pieces"] > 1 for c in cuts):
            flags_.append(flag(FIELD_VERIFICATION_REQUIRED, "A fascia run is longer than the stock. Splice over a joist or blocking, located on site.", FIELD))
    else:
        cuts = [{"run": name, "run_ft": r3(length), "run": name} for name, length in runs]
    allocation = None
    if pieces and kerf is not None:
        allocation = allocate(pieces, [s * 12.0 for s in stock], kerf)
    flags_ = _dedupe(flags_)
    if allocation is not None:
        for stock_in, count in allocation.count_by_stock().items():
            sticks = [s for s in allocation.sticks if s[0] == stock_in]
            net_here = sum(c for _, cs, _ in sticks for c, _ in cs)
            out.add(
                line(
                    key=f"fascia.{stock_in / 12.0:g}ft",
                    group="Fascia",
                    description=f"Matching PVC/composite fascia, {stock_in / 12.0:g} ft.",
                    specification=(basis.finish.get("fascia") or "Matching PVC/composite fascia on the exposed straight rims.") + " Open: " + "; ".join(open_edges) + ".",
                    construction_quantity=r3(net_here / 12.0),
                    construction_unit="lin ft of fascia cuts",
                    purchasing_quantity=count,
                    purchasing_unit="EA",
                    stock_length_ft=stock_in / 12.0,
                    stock_rule=f"Each run is one piece when it fits the longest stock, otherwise equal pieces. {allocation.policy}.",
                    waste={"rule": "Offcut plus kerf. No percentage added.", "waste_in": r3(stock_in * count - net_here)},
                    allocation={"overall": allocation.as_dict()} if stock_in == min(allocation.count_by_stock()) else None,
                    cuts=cuts if stock_in == min(allocation.count_by_stock()) else [],
                    inputs={"runs": [[n, r3(l)] for n, l in runs], "kerf_in": kerf},
                    flags=flags_,
                )
            )
    else:
        out.add(
            line(
                key="fascia",
                group="Fascia",
                description="Matching PVC/composite fascia on the exposed straight rims.",
                specification="Open: " + "; ".join(open_edges) + ".",
                construction_quantity=r3(total),
                construction_unit="lin ft of exposed rim",
                purchasing_unit="EA",
                stock_rule="Piece count waits for the fascia stock length.",
                cuts=cuts,
                inputs={"runs": [[n, r3(l)] for n, l in runs]},
                flags=flags_,
            )
        )
    # Fascia fasteners.
    spacing = f.get("fastener_spacing_in")
    per = f.get("fasteners_per_station")
    pack = f.get("fasteners_per_package")
    ff = _product_flags(facts, "fascia", ["fastener_spacing_in", "fasteners_per_station", "fasteners_per_package"])
    qty = None
    packages = None
    if spacing is not None and per is not None:
        stations = sum(math.ceil(length * 12.0 / spacing - 1e-9) + 1 for _, length in runs)
        qty = stations * per
        if pack is not None:
            packages = math.ceil(qty / pack)
    out.add(
        line(
            key="fasteners.fascia",
            group="Fasteners",
            description="Fascia fasteners.",
            construction_quantity=r3(total),
            construction_unit="lin ft of fascia",
            purchasing_quantity=packages,
            purchasing_unit="PKG",
            stock_rule=f"{qty} fasteners, one station at each run end and at the spacing between." if qty is not None else "Spacing and fasteners per station from the manufacturer.",
            flags=ff,
        )
    )


# ---------------------------------------------------------------- railing


def _railing(out, basis, deck, facts):
    rf = facts["railing"]
    chains = guard_chains(
        deck,
        stair_width_ft=basis.stair_width_ft,
        lower_width_ft=basis.lower_width_ft,
        lower_depth_ft=basis.lower_depth_ft,
        gate_clear_in=basis.gate_clear_in,
        stair_run_ft=basis.stair_run_ft,
        rise_in=basis.rise_in,
    )
    runs = [run for chain in chains for run in chain.runs]
    level = [r for r in runs if r.kind == "level"]
    stair = [r for r in runs if r.kind == "stair"]
    topo = topology_counts(chains)
    out.add(
        line(
            key="railing.runs",
            group="Railing",
            description="Guard and stair-rail runs.",
            construction_quantity=r3(sum(r.length_ft for r in level)),
            construction_unit="lin ft of level guard",
            cuts=[{"run": r.label, "length_ft": r3(r.length_ft), "kind": r.kind, "horizontal_ft": r3(r.horizontal_ft)} for r in runs],
            inputs={"stair_rail_ft_each": r3(stair[0].length_ft), "junctions": topo},
            request=False,
        )
    )
    attach = flag(ENGINEERING_REQUIRED, "Guard post attachment and blocking for the guard load.", ENGINEER)
    height = flag(ENGINEERING_REQUIRED, "Guard height against the pool-enclosure requirement.", ENGINEER)
    need = ["system_name", "level_panel_lengths_ft", "stair_panel_lengths_ft", "stair_panel_span_basis", "panels_cut_to_length", "max_post_spacing_in"]
    missing_flags = _product_flags(facts, "railing", need)
    if not missing_flags:
        plans = {}
        refused = []
        for run in runs:
            lengths = rf["level_panel_lengths_ft"] if run.kind == "level" else rf["stair_panel_lengths_ft"]
            plan = panel_plan(run, panel_lengths_ft=lengths, max_post_spacing_in=rf["max_post_spacing_in"], cut_to_length=rf["panels_cut_to_length"], span_basis=rf["stair_panel_span_basis"])
            plans[run.key] = plan
            if plan["refused"]:
                refused.append(flag(PRODUCT_DEPENDENT, f"{run.label}: {plan['refused']}", SUPPLIER))
        if refused:
            missing_flags = refused
        else:
            counts: Dict[Tuple[str, float], int] = {}
            for run in runs:
                plan = plans[run.key]
                counts[(run.kind, plan["panel_ft"])] = counts.get((run.kind, plan["panel_ft"]), 0) + plan["bays"]
            for (kind, length), count in sorted(counts.items()):
                out.add(
                    line(
                        key=f"railing.{kind}-panel.{length:g}ft",
                        group="Railing",
                        description=f"Black aluminum {'stair' if kind == 'stair' else 'level'} rail panel, {length:g} ft.",
                        specification=rf.get("system_name") or "",
                        construction_quantity=count,
                        construction_unit="bays",
                        purchasing_quantity=count,
                        purchasing_unit="EA",
                        stock_length_ft=length,
                        stock_rule="Equal bays on each run, no wider than the post spacing. A panel longer than its bay is cut to the bay.",
                        cuts=[{"run": r.label, "bays": plans[r.key]["bays"], "bay_ft": r3(plans[r.key]["bay_ft"])} for r in runs if r.kind == kind and plans[r.key]["panel_ft"] == length],
                        flags=[height] if kind == "level" else [],
                    )
                )
            posts = sum(chain_posts(plans, chain) for chain in chains)
            out.add(
                line(
                    key="railing.posts",
                    group="Railing",
                    description="Black aluminum rail posts, including corner, stair-transition, end, and gate posts.",
                    specification=rf.get("system_name") or "",
                    construction_quantity=posts,
                    construction_unit="posts",
                    purchasing_quantity=posts,
                    purchasing_unit="EA",
                    stock_rule="One post at each end and junction of a chain, and one at each bay line. Junction posts are shared.",
                    inputs={"chains": [[run.key for run in chain.runs] for chain in chains]},
                    flags=[attach],
                )
            )
    if missing_flags:
        out.add(
            line(
                key="railing.panels-and-posts",
                group="Railing",
                description="Black aluminum guard and stair-rail panels and posts.",
                specification=rf.get("system_name") or "Black aluminum guard, stair rail, and compatible gate.",
                construction_quantity=r3(sum(r.length_ft for r in runs)),
                construction_unit="lin ft of guard and stair rail",
                purchasing_unit="EA",
                stock_rule="Panels and posts wait for the railing system's panel lengths and post spacing.",
                cuts=[{"run": r.label, "length_ft": r3(r.length_ft)} for r in runs],
                flags=_dedupe(missing_flags + [attach, height]),
            )
        )
    out.add(
        line(
            key="railing.fittings",
            group="Railing",
            description=(
                f"Rail fittings: {topo['level corner']} level corners, {topo['stair top']} stair-top and "
                f"{topo['stair bottom']} stair-bottom transitions, {topo['free end at the pool edge']} free ends at the pool edge."
            ),
            specification=rf.get("system_name") or "",
            construction_quantity=topo["level corner"] + topo["stair top"] + topo["stair bottom"] + topo["free end at the pool edge"],
            construction_unit="junctions",
            purchasing_quantity=(topo["level corner"] + topo["stair top"] + topo["stair bottom"] + topo["free end at the pool edge"]) * rf["fittings_per_junction"] if rf.get("fittings_per_junction") else None,
            purchasing_unit="EA",
            stock_rule="Junction counts are calculated. Fitting kits per junction come from the railing system.",
            inputs={"junctions": topo},
            flags=_product_flags(facts, "railing", ["fittings_per_junction"]),
        )
    )


def _gate(out, basis, facts):
    g = facts["gate"]
    flags_ = _product_flags(facts, "gate", ["product_name", "clear_opening_in", "hinges_per_gate", "latches_per_gate"])
    clear = g.get("clear_opening_in")
    if clear is not None and abs(clear - basis.gate_clear_in) > 0.25:
        flags_.append(flag(PRODUCT_DEPENDENT, f"The gate gives {clear:g} in clear. The drawing needs {basis.gate_clear_in:g} in.", SUPPLIER))
    flags_.append(flag(ENGINEERING_REQUIRED, "Self-closing and self-latching hardware acceptable for the pool enclosure.", ENGINEER))
    out.add(
        line(
            key="gate",
            group="Railing",
            description=f"Compatible black aluminum pool gate, {basis.gate_clear_in:g} in clear, outward swinging, self-closing and self-latching.",
            specification=g.get("product_name") or "",
            construction_quantity=1,
            construction_unit="gate",
            purchasing_quantity=1,
            purchasing_unit="EA",
            stock_rule=(f"{g.get('hinges_per_gate')} self-closing hinges and {g.get('latches_per_gate')} self-latching latch." if g.get("hinges_per_gate") and g.get("latches_per_gate") else "Hinge and latch counts from the gate product."),
            flags=flags_,
        )
    )


# ---------------------------------------------------------------- structure


def _family(basis, name):
    spec = basis.structural.get(name)
    if not isinstance(spec, Mapping):
        return None
    if not spec.get("size") or not spec.get("stock_lengths_ft"):
        return None
    return spec


def _identity(spec):
    return (str(spec.get("size")), str(spec.get("material") or ""), tuple(sorted(float(s) for s in spec["stock_lengths_ft"])), spec.get("canonical_material_code"))


def _structure(out, basis, deck, kerf, kerf_flags, facts):
    groups: Dict[tuple, List[Tuple[float, str]]] = {}
    families: Dict[tuple, List[str]] = {}
    notes: List[dict] = []
    missing_spec = []

    def add(name, cuts):
        spec = _family(basis, name)
        if spec is None:
            missing_spec.append(name)
            return
        key = _identity(spec)
        groups.setdefault(key, []).extend((c, l, name) for c, l in cuts)
        families.setdefault(key, []).append(name)

    joists = [(deck.joist_length_ft(x) * 12.0, f"Upper joist at {x:+.3f} ft") for x in basis.upper_joists_ft]
    add("joist", joists)
    notes.append({"family": "joist", "count": len(joists), "net_ft": r3(sum(c for c, _ in joists) / 12.0), "cuts": [{"station_ft": r3(x), "length_ft": r3(deck.joist_length_ft(x))} for x in basis.upper_joists_ft]})
    if basis.header_segment_count:
        chords = deck.header_chords(basis.header_segment_count)
        add("header", [(c * 12.0, f"Header segment {i + 1}") for i, c in enumerate(chords)])
        notes.append({"family": "header", "count": len(chords), "piece_ft": r3(chords[0]), "sagitta_in": r3(deck.header_sagitta_in(basis.header_segment_count))})
    problems: Dict[str, List[dict]] = {}

    def problem(family, text):
        problems.setdefault(family, []).append(flag(ENGINEERING_REQUIRED, text, BRAYMAN))

    thickness = basis.structural.get("joist_thickness_in")
    blocks = []
    blocking_ids = basis.structural.get("blocking_beam_ids") or []
    if blocking_ids and thickness is None:
        problem("blocking", "The joist thickness used for block lengths is not recorded.")
    for beam_id in blocking_ids:
        beam = next((b for b in basis.beams if b["id"] == beam_id), None)
        if beam is None:
            problem("blocking", f"Blocking names beam {beam_id}, which is not stored.")
            continue
        if thickness is None:
            continue
        xs = [p[0] for p in beam["points"]]
        for index, bay in enumerate(bays_in(basis.upper_joists_ft, min(xs), max(xs)), start=1):
            blocks.append((bay - thickness, f"Block {index} on {beam_id}, {bay:.1f} in bay"))
    if blocks:
        add("blocking", blocks)
        notes.append({"family": "blocking", "count": len(blocks), "lengths_in": sorted({r3(b) for b, _ in blocks})})
    if basis.lower_joists_ft:
        lower = [(basis.lower_depth_ft * 12.0, f"Lower joist at {x:+.3f} ft") for x in basis.lower_joists_ft]
        add("lower_joist", lower)
        notes.append({"family": "lower_joist", "count": len(lower), "length_ft": r3(basis.lower_depth_ft)})
    supports = {pid: (x, y) for pid, x, y in basis.piers}
    beam_cuts = []
    for beam in basis.beams:
        try:
            splices = [supports[s] for s in beam["splice_support_ids"]]
            segments = split_at(beam["points"], splices) if splices else [math.hypot(beam["points"][1][0] - beam["points"][0][0], beam["points"][1][1] - beam["points"][0][1])]
        except (KeyError, GeometryRefusal) as exc:
            problem("beam", f"Beam {beam['id']} was not cut: {exc}")
            continue
        for ply in range(beam["plies"]):
            for i, seg in enumerate(segments):
                beam_cuts.append((seg * 12.0, f"{beam['id']} ply {ply + 1} piece {i + 1}"))
    if beam_cuts:
        add("beam", beam_cuts)
        notes.append({"family": "beam", "count": len(beam_cuts), "net_ft": r3(sum(c for c, _ in beam_cuts) / 12.0)})
    if basis.stringer_count and basis.rise_in is not None and basis.stair_run_ft is not None:
        allowance = basis.structural.get("stringer_end_allowance_in")
        slope = math.hypot(basis.stair_run_ft * 12.0, basis.rise_in)
        if allowance is not None:
            add("stringer", [(slope + allowance, f"Stringer {i + 1}") for i in range(basis.stringer_count)])
        else:
            problem("stringer", "The stringer end-cut allowance is not recorded, so the stringer stock length is not set.")
        notes.append({"family": "stringer", "count": basis.stringer_count, "slope_in": r3(slope), "end_allowance_in": allowance})
    uncut_posts = []
    for post in basis.posts:
        if post["cut_length_in"] is not None:
            add("post", [(post["cut_length_in"], f"Post {post['id']} at {post['support_id']}")])
        else:
            uncut_posts.append(post)

    if missing_spec:
        for name in sorted(set(missing_spec)):
            problem(name, f"No recorded structural specification for {name.replace('_', ' ')}.")

    for key, cuts in sorted(groups.items(), key=lambda kv: kv[0]):
        size, material, stock, code = key
        fam = families[key]
        line_flags = list(kerf_flags)
        for name, found in problems.items():
            spec = _family(basis, name)
            if name in fam or (spec is not None and _identity(spec) == key):
                line_flags += found
        if "post" in fam:
            line_flags.append(flag(FIELD_VERIFICATION_REQUIRED, "Post cut lengths assume the recorded bracket height and pier-head elevation. Confirm on site before cutting.", FIELD))
        if "header" in fam:
            line_flags.append(flag(FIELD_VERIFICATION_REQUIRED, "Header segments are field-cut to the verified pool wall.", FIELD))
        if "stringer" in fam:
            line_flags.append(flag(FIELD_VERIFICATION_REQUIRED, "Stringer layout and plumb cuts are set out on site.", FIELD))
        if kerf is None:
            out.add(
                line(
                    key=f"lumber.{size}.{'+'.join(fam)}",
                    group="Structure",
                    description=f"{material} {size}".strip() + f" — {', '.join(fam)}.",
                    construction_quantity=r3(sum(c for c, _, _ in cuts) / 12.0),
                    construction_unit="lin ft of cuts",
                    purchasing_unit="EA",
                    stock_rule="Stick count waits for the saw kerf.",
                    flags=line_flags,
                    canonical_material_code=code,
                )
            )
            continue
        reuse, reuse_flags = _offcut_policy(facts)
        line_flags += reuse_flags
        by_family = {}
        for c, l, name in cuts:
            by_family.setdefault(name, []).append((c, l))
        try:
            allocation = allocate_by_use(by_family, [s * 12.0 for s in stock], kerf, reuse)
        except StockRefusal as exc:
            out.add(line(key=f"lumber.{size}.{'+'.join(fam)}", group="Structure", description=f"{material} {size}", construction_quantity=r3(sum(c for c, _, _ in cuts) / 12.0), construction_unit="lin ft of cuts", purchasing_unit="EA", flags=line_flags + [flag(ENGINEERING_REQUIRED, str(exc), BRAYMAN)], canonical_material_code=code))
            continue
        for stock_in, count in allocation.count_by_stock().items():
            sticks = [s for s in allocation.sticks if s[0] == stock_in]
            net_here = sum(c for _, cs, _ in sticks for c, _ in cs)
            waste_here = stock_in * count - net_here
            out.add(
                line(
                    key=f"lumber.{size}.{material}.{stock_in / 12.0:g}ft".replace(" ", "-").lower(),
                    group="Structure",
                    description=f"{material} {size} × {stock_in / 12.0:g} ft".strip() + f" — {', '.join(fam)}.",
                    specification=f"Retained structural specification. {size}, {material}.",
                    construction_quantity=r3(net_here / 12.0),
                    construction_unit="lin ft of cuts",
                    purchasing_quantity=count,
                    purchasing_unit="EA",
                    stock_length_ft=stock_in / 12.0,
                    stock_rule=f"{allocation.policy}.",
                    waste={"rule": "Offcut plus kerf on the purchased sticks. No percentage added.", "waste_in": r3(waste_here), "waste_percent": r3(100.0 * waste_here / (stock_in * count))},
                    allocation={"overall": allocation.as_dict()} if stock_in == min(allocation.count_by_stock()) else None,
                    inputs={"families": fam, "kerf_in": kerf},
                    flags=line_flags,
                    canonical_material_code=code,
                    canonical_identity=None if code else lumber_identity(size, material, stock_in / 12.0),
                )
            )
    post_spec = _family(basis, "post")
    if uncut_posts:
        if post_spec is None:
            problem("post", "Uncut posts have no recorded post specification.")
        else:
            longest = max(post_spec["stock_lengths_ft"])
            out.add(
                line(
                    key=f"lumber.{post_spec['size']}.uncut-posts.{longest:g}ft".lower(),
                    group="Structure",
                    description=f"{post_spec.get('material', '')} {post_spec['size']} × {longest:g} ft posts, ordered uncut.".strip(),
                    specification=f"Retained structural specification. {post_spec['size']}, {post_spec.get('material', '')}.",
                    construction_quantity=len(uncut_posts),
                    construction_unit="posts",
                    purchasing_quantity=len(uncut_posts),
                    purchasing_unit="EA",
                    stock_length_ft=longest,
                    stock_rule="One uncut piece of the longest recorded post stock for each post that is cut on site.",
                    flags=[flag(FIELD_VERIFICATION_REQUIRED, f"{len(uncut_posts)} posts are ordered uncut and cut on site.", FIELD)],
                    canonical_material_code=post_spec.get("canonical_material_code"),
                    canonical_identity=None if post_spec.get("canonical_material_code") else lumber_identity(post_spec["size"], post_spec.get("material", ""), longest),
                )
            )
    def _grouped(name):
        spec = _family(basis, name)
        return any(name in fams for fams in families.values()) or (spec is not None and _identity(spec) in groups)

    open_families = sorted(name for name in problems if not _grouped(name))
    if open_families:
        out.add(
            line(
                key="structure.open",
                group="Structure",
                description="Structural members that cannot be counted yet: " + ", ".join(n.replace("_", " ") for n in open_families) + ".",
                construction_quantity=None,
                construction_unit="",
                purchasing_unit="EA",
                stock_rule="Not counted until the recorded specification is complete.",
                flags=[f for name in open_families for f in problems[name]],
                request=False,
            )
        )
    wing = basis.structural.get("wing_blocking")
    if isinstance(wing, Mapping) and wing.get("count"):
        out.add(
            line(
                key="lumber.wing-blocking",
                group="Structure",
                description=f"Wing blocking, {wing['count']} blocks, field-cut. {wing.get('note', '')}".strip(),
                construction_quantity=wing["count"],
                construction_unit="blocks",
                purchasing_quantity=wing.get("sticks"),
                purchasing_unit="EA",
                stock_length_ft=wing.get("stock_length_ft"),
                stock_rule="Recorded in the governing issue. Block lengths are cut on site.",
                flags=[flag(FIELD_VERIFICATION_REQUIRED, "Wing block lengths are cut on site.", FIELD)],
                canonical_material_code=(_family(basis, "blocking") or {}).get("canonical_material_code"),
                canonical_identity=(
                    None
                    if (_family(basis, "blocking") or {}).get("canonical_material_code") or not _family(basis, "blocking") or not wing.get("stock_length_ft")
                    else lumber_identity(_family(basis, "blocking")["size"], _family(basis, "blocking").get("material", ""), float(wing["stock_length_ft"]))
                ),
            )
        )
    out.add(
        line(
            key="structure.schedule",
            group="Structure",
            description="Structural cut schedule.",
            construction_quantity=None,
            construction_unit="",
            cuts=notes,
            request=False,
        )
    )


def _beam_spans(basis):
    """Each beam split at every pier on it."""
    spans = []
    for beam in basis.beams:
        on = []
        (x0, y0), (x1, y1) = beam["points"][0], beam["points"][-1]
        total = math.hypot(x1 - x0, y1 - y0)
        for pid, x, y in basis.piers:
            t = ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / (total * total)
            off = abs((x1 - x0) * (y0 - y) - (x0 - x) * (y1 - y0)) / total
            if off < 0.05 and -1e-6 <= t <= 1 + 1e-6:
                on.append(t * total)
        edges = sorted(set([0.0, total] + [round(v, 6) for v in on]))
        spans.append((beam["id"], [b - a for a, b in zip(edges, edges[1:])]))
    return spans


def _bearings(basis, deck):
    """Joist bearings on beams: one per distinct crossing point."""
    count = 0
    for x in basis.upper_joists_ft:
        y_lo = deck.front_y_ft - deck.joist_length_ft(x)
        points = set()
        for beam in basis.beams:
            (x0, y0), (x1, y1) = beam["points"][0], beam["points"][-1]
            if min(x0, x1) - 1e-6 <= x <= max(x0, x1) + 1e-6 and abs(x1 - x0) > 1e-9:
                y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
                if y_lo - 1e-6 <= y <= deck.front_y_ft + 1e-6:
                    points.add((round(x, 4), round(y, 4)))
        count += len(points)
    lower = 0
    if basis.lower_back_y_ft is not None:
        for x in basis.lower_joists_ft:
            points = set()
            for beam in basis.beams:
                (x0, y0), (x1, y1) = beam["points"][0], beam["points"][-1]
                if abs(y1 - y0) < 1e-9 and min(x0, x1) - 1e-6 <= x <= max(x0, x1) + 1e-6:
                    if basis.lower_back_y_ft - 1e-6 <= y0 <= basis.lower_back_y_ft + basis.lower_depth_ft + 1e-6:
                        points.add((round(x, 4), round(y0, 4)))
            lower += len(points)
    return count, lower


def _between(length_in: float) -> int:
    """J1 stitch allowance: stations at 16 in, kept 8 in clear of each end."""
    count = 0
    station = 16.0
    while station <= length_in - 8.0 + 1e-6:
        count += 1
        station += 16.0
    return count


def _piers_and_connectors(out, basis, deck, facts):
    eng = flag(ENGINEERING_REQUIRED, "Helical pier shaft, helix, length, torque, and capacity.", ENGINEER)
    out.add(
        line(
            key="piers.helical",
            group="Foundations",
            description=f"Helical piers, one at each of {len(basis.piers)} drawn locations. No sonotubes. No concrete.",
            construction_quantity=len(basis.piers),
            construction_unit="locations",
            purchasing_quantity=len(basis.piers),
            purchasing_unit="EA",
            cuts=[{"pier": pid, "x_ft": r3(x), "y_ft": r3(y)} for pid, x, y in basis.piers],
            flags=[eng],
        )
    )
    posts = len(basis.posts) or len(basis.piers)
    includes = facts["foundations"].get("pier_includes_bracket")
    if includes is not True:
        out.add(
            line(
                key="connectors.pier-bracket",
                group="Connectors",
                description="Helical-pier post bracket, one per pier unless the pier includes it.",
                construction_quantity=len(basis.piers),
                construction_unit="piers",
                purchasing_quantity=len(basis.piers),
                purchasing_unit="EA",
                flags=(_product_flags(facts, "foundations", ["pier_includes_bracket"]) if includes is None else []) + [eng],
            )
        )
    conn = flag(ENGINEERING_REQUIRED, "Connector product and capacity are not specified.", ENGINEER)
    out.add(line(key="connectors.post-to-beam", group="Connectors", description="Post-to-beam connectors, one per post.", construction_quantity=posts, construction_unit="posts", purchasing_quantity=posts, purchasing_unit="EA", flags=[conn]))
    out.add(line(key="connectors.header", group="Connectors", description="Joist-to-header connectors, one per upper joist.", construction_quantity=len(basis.upper_joists_ft), construction_unit="joists", purchasing_quantity=len(basis.upper_joists_ft), purchasing_unit="EA", flags=[conn]))
    if basis.stringer_count:
        out.add(line(key="connectors.stringer", group="Connectors", description="Stringer connectors, one per stringer.", construction_quantity=basis.stringer_count, construction_unit="stringers", purchasing_quantity=basis.stringer_count, purchasing_unit="EA", flags=[conn]))
    spans = _beam_spans(basis)
    bolts = sum(_between(s * 12.0) * 2 for _, segs in spans for s in segs)
    bolt = flag(ENGINEERING_REQUIRED, "Beam stitch bolt diameter and spacing. The count is a pricing allowance, not an engineered schedule.", ENGINEER)
    detail = [{"beam": bid, "spans_ft": [r3(s) for s in segs]} for bid, segs in spans]
    out.add(line(key="fasteners.stitch-bolts", group="Fasteners", description="Beam stitch bolts, two rows at 16 in between piers.", construction_quantity=bolts, construction_unit="bolts", purchasing_quantity=bolts, purchasing_unit="EA", cuts=detail, flags=[bolt]))
    out.add(line(key="fasteners.stitch-nuts", group="Fasteners", description="Nuts for the stitch bolts.", construction_quantity=bolts, construction_unit="nuts", purchasing_quantity=bolts, purchasing_unit="EA", flags=[bolt]))
    out.add(line(key="fasteners.stitch-washers", group="Fasteners", description="Washers for the stitch bolts, two per bolt.", construction_quantity=bolts * 2, construction_unit="washers", purchasing_quantity=bolts * 2, purchasing_unit="EA", flags=[bolt]))
    upper_b, lower_b = _bearings(basis, deck)
    screws = (upper_b + lower_b) * 2
    out.add(
        line(
            key="fasteners.structural-screws",
            group="Fasteners",
            description="Structural screws, two at each joist bearing on a beam.",
            construction_quantity=upper_b + lower_b,
            construction_unit="bearings",
            purchasing_quantity=screws,
            purchasing_unit="EA",
            inputs={"upper_bearings": upper_b, "lower_bearings": lower_b},
            flags=[conn],
        )
    )


def _skirting(out, basis):
    text = basis.finish.get("skirting")
    perimeter = basis.lower_width_ft + 2 * basis.lower_depth_ft
    out.add(
        line(
            key="skirting.lower",
            group="Skirting",
            description="Lower-deck skirting on the two sides and the front, including under the gate.",
            specification=text or "The finish change does not restate the skirting material.",
            construction_quantity=r3(perimeter),
            construction_unit="lin ft of lower perimeter",
            purchasing_unit="EA",
            flags=[flag(PRODUCT_DEPENDENT, "Skirting material after the finish change (the earlier issue used pressure-treated 1×6)", BRAYMAN)]
            if not text
            else [flag(PRODUCT_DEPENDENT, "Skirting board width and stock length", SUPPLIER)],
            # Not sent to the supplier until Brayman chooses the material.
            request=bool(text),
        )
    )


def _dedupe(flags_):
    seen = set()
    out = []
    for f in flags_:
        key = (f["status"], f["fact"])
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out

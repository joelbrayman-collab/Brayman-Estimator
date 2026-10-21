"""Straight-wall framing quantities.

One stud-position function is the authority for the count and the drawing.
The contractor supplies every measurement. This module does not size members,
add waste, choose a stock length, or write an estimate.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from html import escape

from app.services.construction_measurement import rectangular_area_square_feet


class WallFramingInputError(ValueError):
    """A required wall measurement is missing or cannot be used."""


# Joel, 21 Oct 2026: a stud runs between the plates, so its length is the wall height less
# the plates. The calculator models the plate counts (entered) but not a plate thickness, so
# the actual dressed thickness of 2x plate stock, 1-1/2 in, is used: the same value the
# drawings use for 2x lumber (app/services/drawings/deck.py, DRESSED_IN). 1.5 in = 0.125 ft
# exactly, so the stud length in feet stays an exact decimal.
PLATE_THICKNESS_IN = Decimal("1.5")


def stud_positions_inches(length_ft, spacing_in):
    """Place one stud at the left end, at each spacing, and at the right end.

    Positions are inches from the left end. A position is stored once.
    The final space may be shorter than the entered spacing.
    """
    length_in = Decimal(str(length_ft)) * Decimal(12)
    spacing = Decimal(str(spacing_in))
    positions = [Decimal(0)]
    cursor = spacing
    while cursor < length_in:
        positions.append(cursor)
        cursor += spacing
    if positions[-1] != length_in:
        positions.append(length_in)
    return tuple(positions)


def _plain(value):
    text = format(Decimal(value), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _positive_measure(text, label):
    cleaned = (text or "").strip()
    if cleaned == "":
        raise WallFramingInputError("Enter the {0}.".format(label))
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise WallFramingInputError(
            "Enter the {0} as a number greater than zero.".format(label)
        ) from exc
    if value <= 0:
        raise WallFramingInputError(
            "Enter the {0} as a number greater than zero.".format(label)
        )
    return value


def _positive_count(text, label):
    cleaned = (text or "").strip()
    if cleaned == "" or not cleaned.isdigit() or int(cleaned) <= 0:
        raise WallFramingInputError(
            "Enter the {0} as a whole number greater than zero.".format(label)
        )
    return int(cleaned)


def _row_is_blank(row, keys):
    return all(not str(row.get(key) or "").strip() for key in keys)


def _signed_measure(text, label, allow_zero):
    cleaned = (text or "").strip()
    if cleaned == "":
        raise WallFramingInputError("Enter the {0}.".format(label))
    bound = "zero or greater" if allow_zero else "greater than zero"
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise WallFramingInputError(
            "Enter the {0} as a number {1}.".format(label, bound)
        ) from exc
    if (allow_zero and value < 0) or (not allow_zero and value <= 0):
        raise WallFramingInputError(
            "Enter the {0} as a number {1}.".format(label, bound)
        )
    return value


_MEMBER_LABELS = {
    "king": "King studs",
    "jack": "Jack studs",
    "cripple": "Cripples",
    "header": "Headers",
}


def _one_opening(row, length_in, wall_height):
    opening_type = str(row.get("opening_type") or "").strip()
    if opening_type not in ("door", "window"):
        raise WallFramingInputError("Enter the opening type.")
    width = _signed_measure(row.get("width_in"), "opening width in inches", False)
    height = _signed_measure(row.get("height_ft"), "opening height in feet", False)
    position = _signed_measure(row.get("position_in"), "opening position in inches", True)
    if position + width > length_in:
        raise WallFramingInputError("Keep the opening inside the wall length.")
    sill_text = str(row.get("sill_ft") or "").strip()
    if opening_type == "door":
        if sill_text != "":
            raise WallFramingInputError(
                "A door starts at the wall base. Leave the sill height empty."
            )
        if height > wall_height:
            raise WallFramingInputError("Keep the opening inside the wall height.")
        sill = Decimal(0)
        label = "Door"
        display = "Door · {0} in from the left · {1} in wide · {2} ft high".format(
            _plain(position),
            _plain(width),
            _plain(height),
        )
    else:
        if sill_text == "":
            raise WallFramingInputError("Enter the window sill height in feet.")
        sill = _signed_measure(sill_text, "window sill height in feet", True)
        if sill + height > wall_height:
            raise WallFramingInputError("Keep the opening inside the wall height.")
        label = "Window"
        display = (
            "Window · {0} in from the left · {1} in wide · {2} ft high · sill {3} ft"
        ).format(_plain(position), _plain(width), _plain(height), _plain(sill))
    return {
        "opening_type": opening_type,
        "label": label,
        "width_in": width,
        "height_ft": height,
        "position_in": position,
        "sill_ft": sill,
        "display": display,
    }


def _validated_openings(rows, length_in, wall_height):
    openings = []
    for row in rows or ():
        if _row_is_blank(row, ("opening_type", "width_in", "height_ft", "position_in", "sill_ft")):
            continue
        openings.append(_one_opening(row, length_in, wall_height))
    for index, opening in enumerate(openings):
        left = opening["position_in"]
        right = left + opening["width_in"]
        for other in openings[index + 1 :]:
            other_left = other["position_in"]
            other_right = other_left + other["width_in"]
            if left < other_right and other_left < right:
                raise WallFramingInputError("Openings overlap. Touching edges are allowed.")
    return tuple(openings)


def _validated_corners(rows):
    corners = []
    for row in rows or ():
        if _row_is_blank(row, ("end", "count", "stud_size", "length_ft")):
            continue
        end = str(row.get("end") or "").strip()
        if end not in ("left", "right"):
            raise WallFramingInputError("Enter the corner end.")
        count = _positive_count(row.get("count"), "additional stud count")
        size = str(row.get("stud_size") or "").strip()
        if size == "":
            raise WallFramingInputError("Enter the corner stud size.")
        length = _signed_measure(row.get("length_ft"), "corner member length in feet", False)
        lineal = Decimal(count) * length
        corners.append(
            {
                "end": end,
                "count": count,
                "stud_size": size,
                "length_ft": length,
                "lineal_ft": lineal,
                "display": "{0} corner · {1} studs · {2} · {3} ft".format(
                    end.capitalize(),
                    count,
                    size,
                    _plain(lineal),
                ),
            }
        )
    return tuple(corners)


def _validated_members(rows):
    members = []
    for row in rows or ():
        if _row_is_blank(row, ("kind", "name", "count", "length_ft")):
            continue
        kind = str(row.get("kind") or "").strip()
        if kind not in _MEMBER_LABELS and kind != "other":
            raise WallFramingInputError("Enter the member name.")
        if kind == "other":
            label = str(row.get("name") or "").strip()
            if label == "":
                raise WallFramingInputError("Enter the other member name.")
        else:
            label = _MEMBER_LABELS[kind]
        count = _positive_count(row.get("count"), "member count")
        length = _signed_measure(row.get("length_ft"), "member length in feet", False)
        lineal = Decimal(count) * length
        members.append(
            {
                "kind": kind,
                "label": label,
                "count": count,
                "length_ft": length,
                "lineal_ft": lineal,
                "display": "{0} · {1} · {2} ft".format(label, count, _plain(lineal)),
            }
        )
    return tuple(members)


def calculate_straight_wall(
    *,
    length_ft,
    height_ft,
    spacing_in,
    stud_size,
    top_plate_count,
    bottom_plate_count,
    openings=None,
    corners=None,
    extra_members=None,
):
    """Return the straight-wall count from the contractor's entries."""
    length = _positive_measure(length_ft, "wall length in feet")
    height = _positive_measure(height_ft, "wall height in feet")
    spacing = _positive_measure(spacing_in, "stud spacing in inches")
    size = (stud_size or "").strip()
    if size == "":
        raise WallFramingInputError("Enter the stud size.")
    top_count = _positive_count(top_plate_count, "number of top plates")
    bottom_count = _positive_count(bottom_plate_count, "number of bottom plates")

    positions = stud_positions_inches(length, spacing)
    stud_count = len(positions)
    last_gap = positions[-1] - positions[-2]
    short_final = last_gap if last_gap < spacing else None
    area = rectangular_area_square_feet(length, height)
    plate_depth_in = Decimal(top_count + bottom_count) * PLATE_THICKNESS_IN
    stud_length_in = height * Decimal(12) - plate_depth_in
    if stud_length_in <= 0:
        raise WallFramingInputError(
            "The wall height must be taller than its plates ({0} in).".format(_plain(plate_depth_in))
        )
    stud_length_ft = stud_length_in / Decimal(12)
    stud_lineal = Decimal(stud_count) * stud_length_ft
    top_lineal = length * Decimal(top_count)
    bottom_lineal = length * Decimal(bottom_count)
    opening_rows = _validated_openings(openings, positions[-1], height)
    corner_rows = _validated_corners(corners)
    member_rows = _validated_members(extra_members)
    intersecting = tuple(
        position
        for position in positions
        if any(
            opening["position_in"] < position < opening["position_in"] + opening["width_in"]
            for opening in opening_rows
        )
    )
    remaining = tuple(position for position in positions if position not in intersecting)
    remaining_lineal = Decimal(len(remaining)) * stud_length_ft
    corner_lineal = sum((row["lineal_ft"] for row in corner_rows), Decimal(0))
    extra_lineal = sum((row["lineal_ft"] for row in member_rows), Decimal(0))
    accounted = remaining_lineal + top_lineal + bottom_lineal + corner_lineal + extra_lineal
    return {
        "length_ft": length,
        "height_ft": height,
        "spacing_in": spacing,
        "stud_size": size,
        "top_plate_count": top_count,
        "bottom_plate_count": bottom_count,
        "plate_thickness_in": PLATE_THICKNESS_IN,
        "stud_length_in": stud_length_in,
        "stud_length_ft": stud_length_ft,
        "positions_in": positions,
        "stud_count": stud_count,
        "short_final_spacing_in": short_final,
        "stud_lineal_ft": stud_lineal,
        "top_plate_lineal_ft": top_lineal,
        "bottom_plate_lineal_ft": bottom_lineal,
        "total_lineal_ft": accounted,
        "gross_wall_area_sqft": area,
        "openings": opening_rows,
        "corners": corner_rows,
        "extra_members": member_rows,
        "intersecting_positions_in": intersecting,
        "remaining_positions_in": remaining,
        "remaining_stud_count": len(remaining),
        "remaining_stud_lineal_ft": remaining_lineal,
        "displays": {
            "length_ft": _plain(length),
            "height_ft": _plain(height),
            "stud_length_in": _plain(stud_length_in),
            "stud_length_note": "{0} ft wall less {1} plates at {2} in".format(
                _plain(height), top_count + bottom_count, _plain(PLATE_THICKNESS_IN)
            ),
            "spacing_in": _plain(spacing),
            "stud_count": str(stud_count),
            "short_final_spacing_in": None if short_final is None else _plain(short_final),
            "stud_lineal_ft": _plain(stud_lineal),
            "top_plate_lineal_ft": _plain(top_lineal),
            "bottom_plate_lineal_ft": _plain(bottom_lineal),
            "total_lineal_ft": _plain(accounted),
            "gross_wall_area_sqft": _plain(area),
            "remaining_stud_count": str(len(remaining)),
            "remaining_stud_lineal_ft": _plain(remaining_lineal),
            "intersecting_positions": ", ".join(
                "{0} in".format(_plain(position)) for position in intersecting
            ),
        },
    }


def elevation_drawing(result):
    """Draw the elevation from positions this module already counted."""
    if result.get("openings") or result.get("corners") or result.get("extra_members"):
        return _layout_elevation(result)
    displays = result["displays"]
    positions = result["positions_in"]
    length_in = positions[-1]
    left = 56
    right = 344
    top = 214
    bottom = 392
    span = right - left

    def x_at(position):
        return left + float(position / length_in) * span

    studs = []
    for position in positions:
        x = x_at(position)
        studs.append(
            '<line class="stud" data-position="{0}" x1="{1:.2f}" y1="{2}" x2="{1:.2f}" y2="{3}" stroke="#1c1f24" stroke-width="1.6"/>'.format(
                _plain(position),
                x,
                top + 6,
                bottom - 6,
            )
        )
    short_text = displays["short_final_spacing_in"]
    only_short_gap = short_text is not None and len(positions) == 2
    spacing_mark = ""
    if not only_short_gap:
        gap_end = x_at(positions[1])
        spacing_mark = (
            '<line x1="{0}" y1="198" x2="{1:.2f}" y2="198" stroke="#6b5420" stroke-width="1"/>'
            '<text x="{2:.2f}" y="192" text-anchor="middle" font-size="12" fill="#6b5420">{3} in</text>'
        ).format(left, gap_end, (left + gap_end) / 2, displays["spacing_in"])
    short_mark = ""
    if short_text is not None:
        gap_start = x_at(positions[-2])
        short_mark = (
            '<line x1="{0:.2f}" y1="198" x2="{1}" y2="198" stroke="#6b5420" stroke-width="1"/>'
            '<text x="{2:.2f}" y="192" text-anchor="end" font-size="12" fill="#6b5420">{3} in short</text>'
        ).format(gap_start, right, right, short_text)
    lines = [
        "Stud size {0}".format(escape(result["stud_size"])),
        "Selected spacing {0} in".format(displays["spacing_in"]),
    ]
    if short_text is not None:
        lines.append("Short final spacing {0} in".format(short_text))
    lines.extend(
        (
            "{0} studs".format(displays["stud_count"]),
            "Studs {0} ft".format(displays["stud_lineal_ft"]),
            "Top plates {0} \u00b7 {1} ft".format(
                result["top_plate_count"],
                displays["top_plate_lineal_ft"],
            ),
            "Bottom plates {0} \u00b7 {1} ft".format(
                result["bottom_plate_count"],
                displays["bottom_plate_lineal_ft"],
            ),
            "Total framing {0} ft".format(displays["total_lineal_ft"]),
            "Gross wall area {0} sq ft".format(displays["gross_wall_area_sqft"]),
        )
    )
    titles = "".join(
        '<text x="8" y="{0}" font-size="13" fill="#1c1f24">{1}</text>'.format(36 + index * 16, line)
        for index, line in enumerate(lines)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 460" width="100%" role="img" '
        'aria-label="Dimensioned wall elevation" data-stud-positions="{positions}">'
        '<rect width="360" height="460" fill="#ffffff"/>'
        '<text x="8" y="20" font-size="15" font-weight="600" fill="#1c1f24">Wall elevation</text>'
        "{titles}"
        '<rect x="{left}" y="{top}" width="{span}" height="6" fill="#1c1f24"/>'
        '<rect x="{left}" y="{plate_bottom}" width="{span}" height="6" fill="#1c1f24"/>'
        "{studs}"
        "{spacing_mark}"
        "{short_mark}"
        '<line x1="{left}" y1="418" x2="{right}" y2="418" stroke="#6b5420" stroke-width="1"/>'
        '<text x="{length_mid:.2f}" y="436" text-anchor="middle" font-size="13" fill="#6b5420">{length_label} ft</text>'
        '<line x1="36" y1="{top}" x2="36" y2="{bottom}" stroke="#6b5420" stroke-width="1"/>'
        '<text x="22" y="{height_mid:.2f}" font-size="13" fill="#6b5420" transform="rotate(-90 22 {height_mid:.2f})">{height_label} ft</text>'
        "</svg>"
    ).format(
        positions=",".join(_plain(position) for position in positions),
        titles=titles,
        left=left,
        right=right,
        top=top,
        bottom=bottom,
        span=span,
        plate_bottom=bottom - 6,
        studs="".join(studs),
        spacing_mark=spacing_mark,
        short_mark=short_mark,
        length_mid=(left + right) / 2,
        length_label=displays["length_ft"],
        height_mid=(top + bottom) / 2,
        height_label=displays["height_ft"],
    )


def _layout_elevation(result):
    """Draw openings and entered members from the result already calculated."""
    displays = result["displays"]
    positions = result["positions_in"]
    intersecting = set(result["intersecting_positions_in"])
    length_in = positions[-1]
    left = 56
    right = 344
    top = 214
    bottom = 392
    span = right - left
    wall_height = result["height_ft"]

    def x_at(position):
        return left + float(position / length_in) * span

    def y_from_base(feet):
        return bottom - float(feet / wall_height) * (bottom - top)

    openings = []
    for opening in result["openings"]:
        x = x_at(opening["position_in"])
        width = x_at(opening["position_in"] + opening["width_in"]) - x
        head = y_from_base(opening["sill_ft"] + opening["height_ft"])
        sill = y_from_base(opening["sill_ft"])
        openings.append(
            (
                '<rect class="opening" data-opening-type="{0}" data-position="{1}" data-width="{2}" '
                'data-height="{3}" data-sill="{4}" x="{5:.2f}" y="{6:.2f}" width="{7:.2f}" height="{8:.2f}" '
                'fill="#f4e7c8" fill-opacity="0.55" stroke="#6b5420" stroke-width="1.2"/>'
            ).format(
                opening["opening_type"],
                _plain(opening["position_in"]),
                _plain(opening["width_in"]),
                _plain(opening["height_ft"]),
                _plain(opening["sill_ft"]),
                x,
                head,
                width,
                sill - head,
            )
        )
    studs = []
    for position in positions:
        meets_opening = position in intersecting
        studs.append(
            (
                '<line class="{0}" data-position="{1}" data-station="{2}" x1="{3:.2f}" y1="{4}" '
                'x2="{3:.2f}" y2="{5}" stroke="#1c1f24" stroke-width="1.6"{6}/>'
            ).format(
                "stud opening-station" if meets_opening else "stud",
                _plain(position),
                "opening" if meets_opening else "full-height",
                x_at(position),
                top + 6,
                bottom - 6,
                ' stroke-dasharray="4 3"' if meets_opening else "",
            )
        )
    short_text = displays["short_final_spacing_in"]
    only_short_gap = short_text is not None and len(positions) == 2
    spacing_mark = ""
    if not only_short_gap:
        gap_end = x_at(positions[1])
        spacing_mark = (
            '<line x1="{0}" y1="198" x2="{1:.2f}" y2="198" stroke="#6b5420" stroke-width="1"/>'
            '<text x="{2:.2f}" y="192" text-anchor="middle" font-size="12" fill="#6b5420">{3} in</text>'
        ).format(left, gap_end, (left + gap_end) / 2, displays["spacing_in"])
    short_mark = ""
    if short_text is not None:
        gap_start = x_at(positions[-2])
        short_mark = (
            '<line x1="{0:.2f}" y1="198" x2="{1}" y2="198" stroke="#6b5420" stroke-width="1"/>'
            '<text x="{2:.2f}" y="192" text-anchor="end" font-size="12" fill="#6b5420">{3} in short</text>'
        ).format(gap_start, right, right, short_text)
    lines = [
        "Stud size {0}".format(escape(result["stud_size"])),
        "Selected spacing {0} in".format(displays["spacing_in"]),
    ]
    if short_text is not None:
        lines.append("Short final spacing {0} in".format(short_text))
    lines.extend(
        (
            "{0} original layout studs".format(displays["stud_count"]),
            "{0} full-height studs".format(displays["remaining_stud_count"]),
            "Full-height studs {0} ft".format(displays["remaining_stud_lineal_ft"]),
            "Top plates {0} · {1} ft".format(result["top_plate_count"], displays["top_plate_lineal_ft"]),
            "Bottom plates {0} · {1} ft".format(
                result["bottom_plate_count"],
                displays["bottom_plate_lineal_ft"],
            ),
            "Accounted framing {0} ft".format(displays["total_lineal_ft"]),
            "Gross wall area {0} sq ft".format(displays["gross_wall_area_sqft"]),
        )
    )
    titles = "".join(
        '<text x="8" y="{0}" font-size="13" fill="#1c1f24">{1}</text>'.format(36 + index * 16, line)
        for index, line in enumerate(lines)
    )
    schedule = []
    if intersecting:
        schedule.append("Dashed studs meet an opening.")
        schedule.append("Opening stations {0}".format(displays["intersecting_positions"]))
    for opening in result["openings"]:
        if opening["opening_type"] == "door":
            schedule.append(
                "Door {0} in, {1} in wide, {2} ft high".format(
                    _plain(opening["position_in"]),
                    _plain(opening["width_in"]),
                    _plain(opening["height_ft"]),
                )
            )
        else:
            schedule.append(
                "Window {0} in, {1} by {2} ft, sill {3} ft".format(
                    _plain(opening["position_in"]),
                    _plain(opening["width_in"]),
                    _plain(opening["height_ft"]),
                    _plain(opening["sill_ft"]),
                )
            )
    for corner in result["corners"]:
        schedule.append(corner["display"])
    for member in result["extra_members"]:
        schedule.append(member["display"])
    schedule.append("Quantity layout. Not a purchasing takeoff.")
    schedule_top = 464
    schedule_markup = "".join(
        '<text x="8" y="{0}" font-size="12" fill="#1c1f24">{1}</text>'.format(
            schedule_top + index * 16,
            escape(line),
        )
        for index, line in enumerate(schedule)
    )
    view_height = schedule_top + max(len(schedule) - 1, 0) * 16 + 20
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 {view_height}" width="100%" role="img" '
        'aria-label="Dimensioned wall elevation" data-stud-positions="{positions}" '
        'data-opening-positions="{opening_positions}" data-full-height-positions="{full_height}">'
        '<rect width="360" height="{view_height}" fill="#ffffff"/>'
        '<text x="8" y="20" font-size="15" font-weight="600" fill="#1c1f24">Wall elevation</text>'
        "{titles}"
        '<rect x="{left}" y="{top}" width="{span}" height="6" fill="#1c1f24"/>'
        '<rect x="{left}" y="{plate_bottom}" width="{span}" height="6" fill="#1c1f24"/>'
        "{openings}"
        "{studs}"
        "{spacing_mark}"
        "{short_mark}"
        '<line x1="{left}" y1="418" x2="{right}" y2="418" stroke="#6b5420" stroke-width="1"/>'
        '<text x="{length_mid:.2f}" y="436" text-anchor="middle" font-size="13" fill="#6b5420">{length_label} ft</text>'
        '<line x1="36" y1="{top}" x2="36" y2="{bottom}" stroke="#6b5420" stroke-width="1"/>'
        '<text x="22" y="{height_mid:.2f}" font-size="13" fill="#6b5420" transform="rotate(-90 22 {height_mid:.2f})">{height_label} ft</text>'
        "{schedule}"
        "</svg>"
    ).format(
        view_height=view_height,
        positions=",".join(_plain(position) for position in positions),
        opening_positions=",".join(_plain(position) for position in result["intersecting_positions_in"]),
        full_height=",".join(_plain(position) for position in result["remaining_positions_in"]),
        titles=titles,
        left=left,
        right=right,
        top=top,
        bottom=bottom,
        span=span,
        plate_bottom=bottom - 6,
        openings="".join(openings),
        studs="".join(studs),
        spacing_mark=spacing_mark,
        short_mark=short_mark,
        length_mid=(left + right) / 2,
        length_label=displays["length_ft"],
        height_mid=(top + bottom) / 2,
        height_label=displays["height_ft"],
        schedule=schedule_markup,
    )

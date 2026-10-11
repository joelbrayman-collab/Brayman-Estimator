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


def calculate_straight_wall(
    *,
    length_ft,
    height_ft,
    spacing_in,
    stud_size,
    top_plate_count,
    bottom_plate_count,
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
    stud_lineal = Decimal(stud_count) * height
    top_lineal = length * Decimal(top_count)
    bottom_lineal = length * Decimal(bottom_count)
    return {
        "length_ft": length,
        "height_ft": height,
        "spacing_in": spacing,
        "stud_size": size,
        "top_plate_count": top_count,
        "bottom_plate_count": bottom_count,
        "positions_in": positions,
        "stud_count": stud_count,
        "short_final_spacing_in": short_final,
        "stud_lineal_ft": stud_lineal,
        "top_plate_lineal_ft": top_lineal,
        "bottom_plate_lineal_ft": bottom_lineal,
        "total_lineal_ft": stud_lineal + top_lineal + bottom_lineal,
        "gross_wall_area_sqft": area,
        "displays": {
            "length_ft": _plain(length),
            "height_ft": _plain(height),
            "spacing_in": _plain(spacing),
            "stud_count": str(stud_count),
            "short_final_spacing_in": None if short_final is None else _plain(short_final),
            "stud_lineal_ft": _plain(stud_lineal),
            "top_plate_lineal_ft": _plain(top_lineal),
            "bottom_plate_lineal_ft": _plain(bottom_lineal),
            "total_lineal_ft": _plain(stud_lineal + top_lineal + bottom_lineal),
            "gross_wall_area_sqft": _plain(area),
        },
    }


def elevation_drawing(result):
    """Draw the elevation from positions this module already counted."""
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

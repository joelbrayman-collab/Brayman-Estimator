"""Paper-space callouts.

A callout names elements in the Construction Model. Moving it changes
only the sheet. It does not change a coordinate.
"""

from __future__ import annotations

import re

PROXIMITY_POINTS = 36.0
CODE_CALLOUT_CANNOT_BE_PLACED = "CALLOUT_CANNOT_BE_PLACED"

_ID_NUMBER = re.compile(r"^(.*?)(\d+)$")
_REFUSAL = re.compile(
    r"^You need to provide this information\. The (?P<fact>.+) of "
    r"(?P<noun>member|support) (?P<identifier>\S+) for (?:the )?(?P<view>.+)\.$"
)
_YOU_NEED = "You need to provide this information."


def build_station_callouts(elements, origin_u, origin_v, points_per_unit, place_x, place_y) -> list:
    """Group elements that land on the same or a nearby paper point."""
    located = []
    for element in elements:
        coordinates = element["projected_geometry"]["coordinates"]
        if not coordinates:
            continue
        point = coordinates[0]
        located.append(
            {
                "element": element,
                "u": point["u"],
                "v": point["v"],
                "px": place_x + (point["u"] - origin_u) * points_per_unit,
                "py": place_y + (point["v"] - origin_v) * points_per_unit,
            }
        )
    callouts = []
    for index, cluster in enumerate(_clusters(located)):
        if len(cluster) < 2:
            continue
        grouped = [item["element"] for item in cluster]
        anchor_u = sum(item["u"] for item in cluster) / len(cluster)
        anchor_v = sum(item["v"] for item in cluster) / len(cluster)
        callouts.append(
            {
                "id": f"group-{index + 1}",
                "element_ids": tuple(sorted((item["id"] for item in grouped), key=_id_key)),
                "text": describe_group(grouped),
                "geometry_reference": {"u": anchor_u, "v": anchor_v},
                "anchor_x": sum(item["px"] for item in cluster) / len(cluster),
                "anchor_y": sum(item["py"] for item in cluster) / len(cluster),
                "kind": "group",
                "justification": "left",
                "provenance": _provenance(grouped),
                "uncertainty": _uncertainty(grouped),
            }
        )
    return callouts


def build_attribute_callouts(
    elements, origin_u, origin_v, points_per_unit, place_x, place_y, model=None
) -> list:
    """One paper callout per construction class. The ids stay on the callout."""
    buckets = {}
    order = []
    for element in elements:
        coordinates = (element.get("projected_geometry") or {}).get("coordinates") or []
        if not coordinates or not element.get("id"):
            continue
        key = _callout_class(element, model)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(element)
    callouts = []
    for index, key in enumerate(order):
        grouped = buckets[key]
        points = []
        for element in grouped:
            for point in element["projected_geometry"]["coordinates"]:
                points.append(point)
        anchor_u = sum(point["u"] for point in points) / len(points)
        anchor_v = sum(point["v"] for point in points) / len(points)
        text = describe_group(grouped)
        size = grouped[0].get("member_size")
        if size and size not in text:
            text = f"{text}\n{size}"
        material_name = grouped[0].get("material_name")
        if material_name and material_name not in text:
            text = f"{text}\n{material_name}"
        callouts.append(
            {
                "id": f"class-{index + 1}",
                "element_ids": tuple(sorted((item["id"] for item in grouped), key=_id_key)),
                "text": text,
                "geometry_reference": {"u": anchor_u, "v": anchor_v},
                "anchor_x": place_x + (anchor_u - origin_u) * points_per_unit,
                "anchor_y": place_y + (anchor_v - origin_v) * points_per_unit,
                "kind": "group" if len(grouped) > 1 else "member",
                "justification": "left",
                "provenance": _provenance(grouped),
                "uncertainty": _uncertainty(grouped),
                "leader": True,
                "member_points": tuple(
                    (
                        place_x + (point["u"] - origin_u) * points_per_unit,
                        place_y + (point["v"] - origin_v) * points_per_unit,
                    )
                    for point in points
                ),
            }
        )
    return callouts


def build_member_callouts(elements, roles, origin_u, origin_v, points_per_unit, place_x, place_y, grouped_ids) -> list:
    """Name an isolated member. Grouped stations keep their group note."""
    wanted = set(roles or ())
    callouts = []
    for element in elements:
        role = element.get("role") or element.get("kind")
        if role not in wanted or element["id"] in grouped_ids:
            continue
        coordinates = element["projected_geometry"]["coordinates"]
        if not coordinates:
            continue
        point = coordinates[0]
        size = element.get("member_size")
        text = role.replace("_", " ").upper() + " " + element["id"]
        if size:
            text = f"{text}\n{size}"
        if element.get("annotate_material") and element.get("material_name"):
            text = f"{text}\n{element['material_name']}"
        callouts.append(
            {
                "id": f"member-{element['id']}",
                "element_ids": (element["id"],),
                "text": text,
                "geometry_reference": {"u": point["u"], "v": point["v"]},
                "anchor_x": place_x + (point["u"] - origin_u) * points_per_unit,
                "anchor_y": place_y + (point["v"] - origin_v) * points_per_unit,
                "kind": "member",
                "justification": "left",
                "provenance": element.get("provenance"),
                "uncertainty": element.get("uncertainty") or (),
            }
        )
    return callouts


def build_refusal_callouts(issues) -> list:
    """One readable note for each missing fact, keeping every element id."""
    groups = {}
    other = []
    for issue in issues:
        match = _REFUSAL.match(issue.message)
        if match is None:
            other.append(issue)
            continue
        key = (match.group("fact"), match.group("noun"), match.group("view"))
        groups.setdefault(key, []).append(match.group("identifier"))
    callouts = []
    for index, (fact, noun, view) in enumerate(sorted(groups)):
        identifiers = sorted(set(groups[(fact, noun, view)]), key=_id_key)
        callouts.append(
            {
                "id": f"refusal-{index + 1}",
                "element_ids": tuple(identifiers),
                "text": wrap_text(
                    f"{_YOU_NEED} The {fact} of {noun} {_spans(identifiers)} for the {view}."
                ),
                "geometry_reference": None,
                "anchor_x": None,
                "anchor_y": None,
                "kind": "refusal",
                "justification": "left",
                "provenance": None,
                "uncertainty": (),
            }
        )
    for index, issue in enumerate(other):
        callouts.append(
            {
                "id": f"note-{index + 1}",
                "element_ids": (),
                "text": wrap_text(issue.message),
                "geometry_reference": None,
                "anchor_x": None,
                "anchor_y": None,
                "kind": "refusal",
                "justification": "left",
                "provenance": None,
                "uncertainty": (),
            }
        )
    return callouts


def describe_group(elements) -> str:
    buckets = {}
    for element in elements:
        role = element.get("role") or element.get("kind") or "element"
        buckets.setdefault(role, []).append(element["id"])
    lines = []
    notes = []
    for role in sorted(buckets):
        identifiers = sorted(set(buckets[role]), key=_id_key)
        lines.append(f"{len(identifiers)} {_plural(role, len(identifiers))}")
        lines.append(_span(identifiers))
    for element in elements:
        for note in element.get("uncertainty") or []:
            text = note.get("note")
            if text and text not in notes:
                notes.append(text)
    lines.extend(notes)
    return "\n".join(lines)


def place_callouts(callouts, obstacles, frame) -> tuple:
    """Deterministic paper positions that avoid occupied rectangles.

    A callout that cannot be placed is returned unplaced. It is not given
    a position that overlaps another annotation.
    """
    occupied = [tuple(item) for item in obstacles]
    placed = []
    refused = []
    for callout in callouts:
        width, height = text_size(callout["text"])
        slot = _slot(
            width,
            height,
            frame,
            occupied,
            (callout.get("anchor_x"), callout.get("anchor_y")),
        )
        if slot is None:
            refused.append(dict(callout))
            continue
        record = dict(callout)
        record["paper_x"] = slot[0]
        record["paper_y"] = slot[1]
        record["width"] = width
        record["height"] = height
        record["justification"] = callout.get("justification") or "left"
        placed.append(record)
        occupied.append((slot[0], slot[1], slot[0] + width, slot[1] + height))
    return placed, refused


def wrap_text(text: str, limit: int = 42) -> str:
    """Keep an annotation narrow enough to sit beside the drawing."""
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            trial = word if not current else f"{current} {word}"
            if current and len(trial) > limit:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
    return "\n".join(lines)


def text_size(text: str) -> tuple:
    lines = text.split("\n") or [""]
    width = max(len(line) for line in lines) * 3.6 + 4
    height = len(lines) * 8 + 2
    return width, height


def rectangles_overlap(left, right) -> bool:
    return not (
        left[2] <= right[0]
        or right[2] <= left[0]
        or left[3] <= right[1]
        or right[3] <= left[1]
    )


def _callout_class(element, model=None):
    connections = []
    if isinstance(model, dict) or hasattr(model, "get"):
        for item in (model.get("connections") or []) if model is not None else []:
            if element.get("id") in (item.get("participant_ids") or []):
                connections.append(item.get("connection_type") or "")
    length = element.get("length_display") or element.get("length") or ""
    return (
        element.get("role") or element.get("kind") or "",
        element.get("member_size") or "",
        element.get("material_id") or element.get("material_name") or "",
        "" if length == "" else str(length),
        tuple(sorted(connections)),
    )


def _clusters(located) -> list:
    ordered = sorted(located, key=lambda item: (round(item["py"], 2), round(item["px"], 2), item["element"]["id"]))
    clusters = []
    for item in ordered:
        merged = False
        item_class = _callout_class(item["element"])
        for cluster in clusters:
            if item_class != _callout_class(cluster[0]["element"]):
                continue
            if any(_near(item, other) for other in cluster):
                cluster.append(item)
                merged = True
                break
        if not merged:
            clusters.append([item])
    changed = True
    while changed:
        changed = False
        merged_clusters = []
        for cluster in clusters:
            target = None
            for existing in merged_clusters:
                if any(_near(left, right) for left in cluster for right in existing):
                    target = existing
                    break
            if target is None:
                merged_clusters.append(list(cluster))
            else:
                target.extend(cluster)
                changed = True
        clusters = merged_clusters
    clusters.sort(key=lambda cluster: (min(item["py"] for item in cluster), min(item["px"] for item in cluster)))
    return clusters


def _near(left, right) -> bool:
    return abs(left["px"] - right["px"]) <= PROXIMITY_POINTS and abs(left["py"] - right["py"]) <= PROXIMITY_POINTS


def _slot(width, height, frame, occupied, anchor):
    """Place a label at the nearest clear paper position to its member."""
    x0, y0, x1, y1 = frame
    ax = anchor[0] if anchor[0] is not None else (x0 + x1) / 2.0
    ay = anchor[1] if anchor[1] is not None else (y0 + y1) / 2.0
    best = None
    best_key = None

    def consider(px, py):
        nonlocal best, best_key
        if not _fits(px, py, width, height, frame, occupied):
            return
        dx = (px + width / 2.0) - ax
        dy = (py + height / 2.0) - ay
        key = ((dx * dx) + (dy * dy), -py, px)
        if best_key is None or key < best_key:
            best = (px, py)
            best_key = key

    if anchor[0] is not None and anchor[1] is not None:
        for radius in (16, 36, 64, 96, 140, 200, 260, 320):
            consider(ax + radius, ay + radius)
            consider(ax + radius, ay - height - radius)
            consider(ax - width - radius, ay + radius)
            consider(ax - width - radius, ay - height - radius)
            consider(ax + radius, ay - height / 2.0)
            consider(ax - width - radius, ay - height / 2.0)
            consider(ax - width / 2.0, ay + radius)
            consider(ax - width / 2.0, ay - height - radius)
    y = y1 - height - 4
    while y >= y0 + 2:
        x = x0 + 4
        while x + width <= x1 - 2:
            consider(x, y)
            x += 24
        y -= 18
    return best


def _fits(px, py, width, height, frame, occupied) -> bool:
    x0, y0, x1, y1 = frame
    rect = (px, py, px + width, py + height)
    if rect[0] < x0 + 2 or rect[1] < y0 + 2 or rect[2] > x1 - 2 or rect[3] > y1 - 2:
        return False
    return not any(rectangles_overlap(rect, other) for other in occupied)


def _plural(role: str, count: int) -> str:
    word = role.replace("_", " ").upper()
    if count == 1 or word.endswith("S"):
        return word
    return f"{word}S"


def _spans(identifiers) -> str:
    buckets = {}
    order = []
    for item in identifiers:
        parsed = _split_id(item)
        key = parsed[0] if parsed else item
        if key not in buckets:
            order.append(key)
            buckets[key] = []
        buckets[key].append(item)
    return ", ".join(_span(buckets[key]) for key in order)


def _span(identifiers) -> str:
    if len(identifiers) == 1:
        return identifiers[0]
    parsed = [_split_id(item) for item in identifiers]
    if parsed and all(item is not None for item in parsed):
        prefixes = {item[0] for item in parsed}
        numbers = [item[1] for item in parsed]
        if len(prefixes) == 1 and numbers == list(range(numbers[0], numbers[0] + len(numbers))):
            return f"{identifiers[0]} to {identifiers[-1]}"
    if len(identifiers) > 6:
        return f"{identifiers[0]} to {identifiers[-1]}"
    return ", ".join(identifiers)


def _split_id(value: str):
    match = _ID_NUMBER.match(value)
    if match is None or not match.group(1):
        return None
    return match.group(1), int(match.group(2))


def _id_key(value: str):
    parsed = _split_id(value)
    if parsed is None:
        return (value, 0)
    return parsed


def _provenance(elements) -> tuple:
    found = []
    for element in elements:
        provenance = element.get("provenance")
        if provenance and provenance not in found:
            found.append(dict(provenance))
    return tuple(found)


def _uncertainty(elements) -> tuple:
    found = []
    for element in elements:
        for note in element.get("uncertainty") or []:
            if note not in found:
                found.append(dict(note))
    return tuple(found)

"""Paper-space callouts.

A callout names elements in the Construction Model. Moving it changes
only the sheet. It does not change a coordinate.
"""

from __future__ import annotations

import re

# Helvetica at 7pt, measured once. This module does not import a PDF writer.
_HELVETICA_7 = {
    " ": 1.946, "!": 1.946, '"': 2.485, "#": 3.892,
    "$": 3.892, "%": 6.223, "&": 4.669, "'": 1.337,
    "(": 2.331, ")": 2.331, "*": 2.723, "+": 4.088,
    ",": 1.946, "-": 2.331, ".": 1.946, "/": 1.946,
    "0": 3.892, "1": 3.892, "2": 3.892, "3": 3.892,
    "4": 3.892, "5": 3.892, "6": 3.892, "7": 3.892,
    "8": 3.892, "9": 3.892, ":": 1.946, ";": 1.946,
    "<": 4.088, "=": 4.088, ">": 4.088, "?": 3.892,
    "@": 7.105, "A": 4.669, "B": 4.669, "C": 5.054,
    "D": 5.054, "E": 4.669, "F": 4.277, "G": 5.446,
    "H": 5.054, "I": 1.946, "J": 3.500, "K": 4.669,
    "L": 3.892, "M": 5.831, "N": 5.054, "O": 5.446,
    "P": 4.669, "Q": 5.446, "R": 5.054, "S": 4.669,
    "T": 4.277, "U": 5.054, "V": 4.669, "W": 6.608,
    "X": 4.669, "Y": 4.669, "Z": 4.277, "[": 1.946,
    "\\": 1.946, "]": 1.946, "^": 3.283, "_": 3.892,
    "`": 2.331, "a": 3.892, "b": 3.892, "c": 3.500,
    "d": 3.892, "e": 3.892, "f": 1.946, "g": 3.892,
    "h": 3.892, "i": 1.554, "j": 1.554, "k": 3.500,
    "l": 1.554, "m": 5.831, "n": 3.892, "o": 3.892,
    "p": 3.892, "q": 3.892, "r": 2.331, "s": 3.500,
    "t": 1.946, "u": 3.892, "v": 3.500, "w": 5.054,
    "x": 3.500, "y": 3.500, "z": 3.500, "{": 2.338,
    "|": 1.820, "}": 2.338, "~": 4.088,
}

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


def bearing_annotation(note, paper_points):
    """A paper note for one supplied bearing. The contact line stays put."""
    if not isinstance(note, dict):
        return None
    label = note.get("label")
    relationship_id = note.get("relationship_id")
    source = note.get("from_id")
    target = note.get("to_id")
    if not label or not relationship_id or not source or not target:
        return None
    if len(paper_points) < 2:
        return None
    kind = str(note.get("kind") or "bears_on").replace("_", " ")
    text = f"BEARING {label}\n{source} {kind} {target}\n{relationship_id}"
    midpoint = (
        sum(point[0] for point in paper_points) / len(paper_points),
        sum(point[1] for point in paper_points) / len(paper_points),
    )
    return {
        "id": f"bearing-{relationship_id}",
        "element_ids": (source, target),
        "text": text,
        "geometry_reference": None,
        "anchor_x": midpoint[0],
        "anchor_y": midpoint[1],
        "kind": "note",
        "justification": "left",
        "provenance": None,
        "uncertainty": (),
        "leader": True,
        "member_points": tuple(paper_points),
    }


def group_bearing_annotations(callouts) -> list:
    """One paper note when the contact and the member kinds match.

    A single bearing keeps its leader. A group names every relationship
    and does not point at one seat.
    """
    order = []
    buckets = {}
    for item in callouts:
        key = _bearing_key(item)
        if key is None:
            key = ("solo", item.get("id"))
        if key not in buckets:
            order.append(key)
            buckets[key] = []
        buckets[key].append(item)
    grouped = []
    for key in order:
        items = buckets[key]
        grouped.append(items[0] if len(items) == 1 else _merge_bearing_notes(items))
    return grouped


def _bearing_key(item):
    lines = (item.get("text") or "").split("\n")
    if len(lines) < 3 or not lines[0].startswith("BEARING "):
        return None
    parts = lines[1].split()
    if len(parts) < 3:
        return None
    source, target = parts[0], parts[-1]
    kind = " ".join(parts[1:-1])
    return (lines[0], kind, _id_prefix(source), _id_prefix(target))


def _id_prefix(value: str) -> str:
    parsed = _split_id(value)
    return parsed[0] if parsed else value


def _merge_bearing_notes(items) -> dict:
    first = items[0]
    lines = first["text"].split("\n")
    parts = lines[1].split()
    kind = " ".join(parts[1:-1])
    sources = []
    targets = []
    relationships = []
    for item in items:
        row = item["text"].split("\n")
        bits = row[1].split()
        if bits[0] not in sources:
            sources.append(bits[0])
        if bits[-1] not in targets:
            targets.append(bits[-1])
        relationships.append(row[2])
    merged = dict(first)
    merged["id"] = f"bearing-{relationships[0]}"
    merged["element_ids"] = tuple(dict.fromkeys([*sources, *targets]))
    merged["text"] = f"{lines[0]}\n{_spans(sources)} {kind} {_spans(targets)}\n{_spans(relationships)}"
    merged["leader"] = False
    merged["member_points"] = ()
    return merged


def route_leader(origin, target, blocked, existing, frame, arrival=()) -> tuple:
    """A paper polyline from a note to the member it names.

    A route that crosses another member is refused even when it is shorter.
    The last short stub may enter the member it names. When every route
    crosses, the note stays and no leader is drawn.
    """
    if origin is None or target is None:
        return ()
    if abs(origin[0] - target[0]) < 0.5 and abs(origin[1] - target[1]) < 0.5:
        return ()
    x0, y0, x1, y1 = frame
    through = [
        (origin, target),
        (origin, (target[0], origin[1]), target),
        (origin, (origin[0], target[1]), target),
        (origin, (x0 + 8, origin[1]), (x0 + 8, target[1]), target),
        (origin, (x1 - 8, origin[1]), (x1 - 8, target[1]), target),
        (origin, (origin[0], y1 - 8), (target[0], y1 - 8), target),
        (origin, (origin[0], y0 + 8), (target[0], y0 + 8), target),
    ]
    for rect in arrival:
        if not _point_in_rect(target, rect):
            continue
        through.extend(
            (
                (origin, (rect[0] - 8, origin[1]), (rect[0] - 8, target[1]), target),
                (origin, (rect[2] + 8, origin[1]), (rect[2] + 8, target[1]), target),
                (origin, (origin[0], rect[3] + 8), (target[0], rect[3] + 8), target),
                (origin, (origin[0], rect[1] - 8), (target[0], rect[1] - 8), target),
            )
        )
    best = None
    for index, points in enumerate(through):
        if any(point[0] < x0 or point[0] > x1 or point[1] < y0 or point[1] > y1 for point in points):
            continue
        segments = list(zip(points, points[1:]))
        if any(
            not _segment_clear(
                segment,
                blocked,
                existing,
                arrival,
                target,
                last=(offset == len(segments) - 1),
            )
            for offset, segment in enumerate(segments)
        ):
            continue
        length = sum(_segment_length(segment) for segment in segments)
        key = (length, index)
        if best is None or key < best[0]:
            best = (key, tuple(points))
    return () if best is None else best[1]


def place_margin_callouts(callouts, obstacles, frame, content) -> tuple:
    """Stack secondary notes in the open margin, outside the construction.

    A note that fits nowhere in the margin falls back to any clear paper
    slot. It is not dropped while a clear slot exists.
    """
    if content is None:
        return place_callouts(callouts, obstacles, frame)
    occupied = [tuple(item) for item in obstacles]
    placed = []
    refused = []
    bands = _margin_bands(frame, content)
    for callout in callouts:
        width, height = text_size(callout["text"])
        anchor = (callout.get("anchor_x"), callout.get("anchor_y"))
        slot = _margin_slot(width, height, bands, occupied, anchor)
        if slot is None:
            slot = _slot(width, height, frame, occupied, anchor)
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


def group_connector_notes(notes) -> tuple:
    """Group connector notes that carry the same supplied metadata.

    Different connectors stay apart. Every member id stays on the group.
    """
    groups = {}
    order = []
    for note in notes:
        key = note["key"]
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(note)
    grouped = []
    for key in order:
        items = groups[key]
        identifiers = []
        points = []
        for item in items:
            for identifier in item["element_ids"]:
                if identifier not in identifiers:
                    identifiers.append(identifier)
            points.extend(item["points"])
        first = items[0]
        grouped.append(
            {
                "key": key,
                "element_ids": tuple(identifiers),
                "lines": first["lines"],
                "points": tuple(points),
                "anchor": first["anchor"],
            }
        )
    return tuple(grouped)


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
    """Paper size of a Helvetica 7 note. The box matches the ink."""
    lines = text.split("\n") or [""]
    width = max((_line_width(line) for line in lines), default=0) + 6
    height = len(lines) * 8 + 4
    return width, height


def _line_width(line: str) -> float:
    return sum(_HELVETICA_7.get(char, 4.0) for char in line)


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


def _margin_bands(frame, content):
    x0, y0, x1, y1 = frame
    cx0, cy0, cx1, cy1 = content
    gap = 8
    bands = []
    if cx0 - x0 > 56:
        bands.append(("left", (x0 + 4, y0 + 4, cx0 - gap, y1 - 4)))
    if x1 - cx1 > 56:
        bands.append(("right", (cx1 + gap, y0 + 4, x1 - 4, y1 - 4)))
    if y1 - cy1 > 40:
        bands.append(("top", (x0 + 4, cy1 + gap, x1 - 4, y1 - 4)))
    if cy0 - y0 > 40:
        bands.append(("bottom", (x0 + 4, y0 + 4, x1 - 4, cy0 - gap)))
    return bands


def _margin_slot(width, height, bands, occupied, anchor):
    ax = anchor[0] if anchor and anchor[0] is not None else None

    def order(item):
        name, box = item
        if ax is None or name in {"top", "bottom"}:
            side = 2
        elif name == "left":
            side = 0 if ax <= (box[0] + box[2]) / 2.0 else 1
        else:
            side = 0 if ax >= (box[0] + box[2]) / 2.0 else 1
        area = (box[2] - box[0]) * (box[3] - box[1])
        return (side, -area, name)

    for name, box in sorted(bands, key=order):
        if box[2] - box[0] < width + 4 or box[3] - box[1] < height + 4:
            continue
        if name == "right":
            x = box[2] - width - 2
        else:
            x = box[0] + 2
        y = box[3] - height - 2
        while y >= box[1] + 2:
            if _fits(x, y, width, height, (box[0], box[1], box[2], box[3]), occupied):
                return (x, y)
            y -= 6
    return None


def _segment_clear(segment, blocked, existing, arrival=(), target=None, last=False) -> bool:
    start, end = segment
    if _segment_length(segment) < 0.5:
        return True
    for rect in blocked:
        if _segment_hits_rect(start, end, rect):
            return False
    for rect in arrival:
        if last:
            if _arrival_blocked(start, end, rect, target):
                return False
        elif _segment_hits_rect(start, end, rect):
            return False
    for other in existing:
        if _segments_cross(start, end, other[0], other[1]):
            return False
    return True


def _arrival_blocked(start, end, rect, target) -> bool:
    """The last stub may enter its own member. It may not run along that member."""
    if target is None or not _segment_hits_rect(start, end, rect):
        return False
    if _segment_length((end, target)) > 4:
        return True
    if not _point_in_rect(end, rect):
        return True
    length = _segment_length((start, end))
    if length <= 18:
        return False
    scale = (length - 18.0) / length
    probe = (
        start[0] + (end[0] - start[0]) * scale,
        start[1] + (end[1] - start[1]) * scale,
    )
    return _point_in_rect(probe, rect)


def _segment_length(segment) -> float:
    start, end = segment
    return ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5


def _segment_hits_rect(start, end, rect) -> bool:
    if _point_in_rect(start, rect) or _point_in_rect(end, rect):
        return True
    left, bottom, right, top = rect
    edges = (
        ((left, bottom), (right, bottom)),
        ((right, bottom), (right, top)),
        ((right, top), (left, top)),
        ((left, top), (left, bottom)),
    )
    return any(_segments_cross(start, end, edge[0], edge[1]) for edge in edges)


def _point_in_rect(point, rect) -> bool:
    return rect[0] <= point[0] <= rect[2] and rect[1] <= point[1] <= rect[3]


def _segments_cross(a, b, c, d) -> bool:
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    left = orient(a, b, c)
    right = orient(a, b, d)
    across = orient(c, d, a)
    back = orient(c, d, b)
    return left * right < 0 and across * back < 0


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

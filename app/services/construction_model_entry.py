"""Turn contractor-entered deck facts into one construction-model revision.

The page collects the fields the existing model already requires.
It does not invent a length, a size, or a second model store.
"""

from __future__ import annotations

from app.services.construction_model.completeness import assess_construction_model
from app.services.construction_model.model import (
    DOCUMENT_STATUS_ISSUED_FOR_PERMIT,
    DOCUMENT_STATUS_PRELIMINARY,
    DOCUMENT_STATUS_TEXT,
    IMPERIAL_UNITS,
    MEMBER_ROLES,
    METRIC_UNITS,
    SOURCE_PROJECT_INPUT,
    STRUCTURE_CLASS_DECK,
    SUPPORT_KINDS,
)
from app.services.project_construction_model import (
    ProjectConstructionModelError,
    load_current_revision,
    save_construction_model_revision,
)

MEMBER_ROW_COUNT = 8
SUPPORT_ROW_COUNT = 4
MAX_GROUP_COUNT = 200
OFFICE_REFERENCE = "Office construction information"

DOCUMENT_STATUS_CHOICES = (
    (DOCUMENT_STATUS_PRELIMINARY, "Preliminary construction drawing"),
    (DOCUMENT_STATUS_ISSUED_FOR_PERMIT, "Issued for permit"),
)
MEASUREMENT_CHOICES = (
    ("imperial", "Imperial"),
    ("metric", "Metric"),
)
ROLE_CHOICES = tuple(sorted(MEMBER_ROLES))
SUPPORT_CHOICES = tuple(sorted(SUPPORT_KINDS))

_MEMBER_KEYS = frozenset({"id", "role", "member_size", "length", "provenance"})
_SUPPORT_KEYS = frozenset({"id", "kind", "provenance"})
_LEVEL_KEYS = frozenset({"id", "name", "elevation", "provenance"})
_LENGTH_KEYS = frozenset({"value", "unit", "derived", "provenance"})


def empty_entry():
    return {
        "project_document_status": "",
        "measurement_system": "",
        "level_id": "level-1",
        "level_name": "",
        "level_elevation": "",
        "members": [_blank_member() for _ in range(MEMBER_ROW_COUNT)],
        "supports": [_blank_support() for _ in range(SUPPORT_ROW_COUNT)],
    }


def current_revision_for_project(*, organization_id, project_id):
    try:
        return load_current_revision(
            organization_id=organization_id,
            project_id=project_id,
        )
    except ProjectConstructionModelError:
        return None


def entry_from_model(content):
    """Return form values when this page can show the model without dropping facts."""
    if not isinstance(content, dict) or not _office_shape(content):
        return None
    form = empty_entry()
    form["project_document_status"] = content.get("project_document_status") or ""
    form["measurement_system"] = content.get("measurement_system") or ""
    level = content["levels"][0]
    form["level_id"] = level["id"]
    form["level_name"] = level["name"]
    form["level_elevation"] = _show_number(level.get("elevation"))
    for index, group in enumerate(_member_groups(content.get("members") or [])):
        if index >= MEMBER_ROW_COUNT:
            return None
        form["members"][index] = group
    for index, group in enumerate(_support_groups(content.get("supports") or [])):
        if index >= SUPPORT_ROW_COUNT:
            return None
        form["supports"][index] = group
    return form


def model_from_entry(form):
    """Build a model from the posted fields, or return contractor-facing errors."""
    errors = []
    status = _text(form.get("project_document_status"))
    if status not in DOCUMENT_STATUS_TEXT:
        errors.append("Choose the drawing status.")
    system = _text(form.get("measurement_system"))
    if system not in ("imperial", "metric"):
        errors.append("Choose imperial or metric.")
        system = None
    level_name = _text(form.get("level_name"))
    if not level_name:
        errors.append("Enter the level name.")
    elevation, elevation_error = _required_number(
        form.get("level_elevation"),
        "Enter the level elevation.",
    )
    if elevation_error:
        errors.append(elevation_error)
    level_id = _text(form.get("level_id")) or "level-1"
    provenance = {
        "source": SOURCE_PROJECT_INPUT,
        "reference": OFFICE_REFERENCE,
    }
    members, member_errors = _members(form.get("members") or [], system, provenance)
    errors.extend(member_errors)
    supports, support_errors = _supports(form.get("supports") or [], provenance)
    errors.extend(support_errors)
    if errors:
        return None, errors
    if not members:
        errors.append("Enter at least one member.")
    if not supports:
        errors.append("Enter at least one support.")
    if errors:
        return None, errors
    model = {
        "structure_class": STRUCTURE_CLASS_DECK,
        "project_document_status": status,
        "measurement_system": system,
        "levels": [
            {
                "id": level_id,
                "name": level_name,
                "elevation": elevation,
                "provenance": dict(provenance),
            }
        ],
        "members": members,
        "supports": supports,
    }
    assessment = assess_construction_model(model)
    if not assessment.generation_permitted or assessment.accepted is None:
        messages = [issue.message for issue in assessment.issues] or [
            "That construction model cannot be stored."
        ]
        return None, messages
    return model, []


def save_office_revision(*, organization_id, project_id, form, actor_display_name):
    """Insert the next revision from the office form. Return the revision or errors."""
    model, errors = model_from_entry(form)
    if errors:
        return None, errors
    try:
        revision = save_construction_model_revision(
            organization_id=organization_id,
            project_id=project_id,
            content=model,
            source_kind=SOURCE_PROJECT_INPUT,
            source_reference=OFFICE_REFERENCE,
            actor_display_name=actor_display_name,
        )
    except ProjectConstructionModelError as exc:
        return None, [str(exc)]
    return revision, []


def _office_shape(content):
    if content.get("structure_class") != STRUCTURE_CLASS_DECK:
        return False
    levels = content.get("levels") or []
    members = content.get("members") or []
    supports = content.get("supports") or []
    if len(levels) != 1 or not members or not supports:
        return False
    if not _only_keys(levels[0], _LEVEL_KEYS):
        return False
    if not _provenance_is_office(levels[0].get("provenance")):
        return False
    for member in members:
        if not _only_keys(member, _MEMBER_KEYS):
            return False
        if member.get("geometry"):
            return False
        if not _provenance_is_office(member.get("provenance")):
            return False
        length = member.get("length")
        if length is not None:
            if not isinstance(length, dict) or not _only_keys(length, _LENGTH_KEYS):
                return False
            if length.get("derived") is True:
                return False
            if not _provenance_is_office(length.get("provenance")):
                return False
    for support in supports:
        if not _only_keys(support, _SUPPORT_KEYS):
            return False
        if support.get("geometry"):
            return False
        if not _provenance_is_office(support.get("provenance")):
            return False
    for name in (
        "relationships",
        "connections",
        "openings",
        "materials",
        "dimensions",
        "constraints",
        "assumptions",
        "stair_results",
        "dimension_chains",
        "uncertainty",
    ):
        if content.get(name):
            return False
    return True


def _only_keys(item, allowed):
    return isinstance(item, dict) and set(item).issubset(allowed)


def _provenance_is_office(value):
    return (
        isinstance(value, dict)
        and value.get("source") == SOURCE_PROJECT_INPUT
        and value.get("reference") == OFFICE_REFERENCE
        and set(value).issubset({"source", "reference"})
    )


def _member_groups(members):
    groups = []
    index = {}
    for member in members:
        length = member.get("length") or {}
        key = (
            member.get("role") or "",
            member.get("member_size") or "",
            length.get("value"),
            length.get("unit") or "",
        )
        if key in index:
            groups[index[key]]["count"] = str(int(groups[index[key]]["count"]) + 1)
            continue
        index[key] = len(groups)
        groups.append(
            {
                "role": key[0],
                "member_size": key[1],
                "length": "" if length.get("value") is None else _show_number(length.get("value")),
                "length_unit": key[3],
                "count": "1",
            }
        )
    return groups


def _support_groups(supports):
    groups = []
    index = {}
    for support in supports:
        kind = support.get("kind") or ""
        if kind in index:
            groups[index[kind]]["count"] = str(int(groups[index[kind]]["count"]) + 1)
            continue
        index[kind] = len(groups)
        groups.append({"kind": kind, "count": "1"})
    return groups


def _members(rows, system, provenance):
    built = []
    errors = []
    sequence = 0
    allowed_units = IMPERIAL_UNITS if system == "imperial" else METRIC_UNITS
    for row in rows:
        if not _member_row_used(row):
            continue
        role = _text(row.get("role"))
        if role not in MEMBER_ROLES:
            errors.append("Choose a member role.")
            continue
        count, count_error = _count(row.get("count"), "Enter the member count.")
        if count_error:
            errors.append(count_error)
            continue
        size = _text(row.get("member_size"))
        length_text = _text(row.get("length"))
        unit = _text(row.get("length_unit"))
        length = None
        if length_text:
            number, number_error = _required_number(length_text, "Enter a numeric length.")
            if number_error:
                errors.append(number_error)
                continue
            if system is None or unit not in allowed_units:
                errors.append("Choose a length unit for the measurement system.")
                continue
            length = {
                "value": number,
                "unit": unit,
                "derived": False,
                "provenance": dict(provenance),
            }
        elif unit:
            errors.append("Enter the length, or clear the length unit.")
            continue
        for _ in range(count):
            sequence += 1
            item = {
                "id": f"member-{role}-{sequence}",
                "role": role,
                "provenance": dict(provenance),
            }
            if size:
                item["member_size"] = size
            if length is not None:
                item["length"] = {
                    "value": length["value"],
                    "unit": length["unit"],
                    "derived": False,
                    "provenance": dict(provenance),
                }
            built.append(item)
    return built, errors


def _supports(rows, provenance):
    built = []
    errors = []
    sequence = 0
    for row in rows:
        if not _support_row_used(row):
            continue
        kind = _text(row.get("kind"))
        if kind not in SUPPORT_KINDS:
            errors.append("Choose a pier or a footing.")
            continue
        count, count_error = _count(row.get("count"), "Enter the support count.")
        if count_error:
            errors.append(count_error)
            continue
        for _ in range(count):
            sequence += 1
            built.append(
                {
                    "id": f"support-{kind}-{sequence}",
                    "kind": kind,
                    "provenance": dict(provenance),
                }
            )
    return built, errors


def _member_row_used(row):
    return any(
        _text(row.get(key))
        for key in ("role", "member_size", "length", "length_unit", "count")
    )


def _support_row_used(row):
    return any(_text(row.get(key)) for key in ("kind", "count"))


def _count(value, message):
    text = _text(value)
    if not text:
        return None, message
    if not text.isdigit() or text.startswith("0"):
        return None, message
    number = int(text)
    if number < 1 or number > MAX_GROUP_COUNT:
        return None, message
    return number, None


def _required_number(value, message):
    text = _text(value)
    if not text:
        return None, message
    try:
        number = float(text) if "." in text else int(text)
    except ValueError:
        return None, message
    return number, None


def _show_number(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _blank_member():
    return {
        "role": "",
        "member_size": "",
        "length": "",
        "length_unit": "",
        "count": "",
    }


def _blank_support():
    return {"kind": "", "count": ""}

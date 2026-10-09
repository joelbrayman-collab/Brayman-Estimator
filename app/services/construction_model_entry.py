"""Turn contractor-entered deck facts into one construction-model revision.

The page collects the fields the existing model already requires.
It does not invent a length, a size, an elevation, or a second model store.
A member is not assigned to a level. The model has no field for that.
"""

from __future__ import annotations

import re
import secrets

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

SUPPORT_ROW_COUNT = 4
MAX_GROUP_COUNT = 200
REQUEST_ROW_GUARD = 200
OFFICE_REFERENCE = "Office construction information"
_LEVEL_ID = re.compile(r"^level-[a-z0-9]{1,40}$")
_TOKEN = re.compile(r"^[a-f0-9]{8}$")
_GROUP_ID = re.compile(r"^g([a-f0-9]{8})-([1-9][0-9]*)$")

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
        "levels": [_blank_level()],
        "members": [_blank_member()],
        "supports": [_blank_support() for _ in range(SUPPORT_ROW_COUNT)],
    }


def new_level_row():
    return _blank_level()


def new_member_row():
    return _blank_member()


def elevation_unit_label(measurement_system):
    """The unit already implied by the model measurement system.

    A level stores the elevation number. It does not store a second unit.
    """
    if measurement_system == "imperial":
        return "ft"
    if measurement_system == "metric":
        return "m"
    return ""


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
    levels = [_level_row(level) for level in content["levels"]]
    members = _member_groups(content.get("members") or [])
    if len(levels) > REQUEST_ROW_GUARD or len(members) > REQUEST_ROW_GUARD:
        return None
    form["levels"] = levels
    form["members"] = members
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
    provenance = {
        "source": SOURCE_PROJECT_INPUT,
        "reference": OFFICE_REFERENCE,
    }
    levels, level_errors = _levels(form.get("levels") or [], provenance)
    errors.extend(level_errors)
    members, member_errors = _members(form.get("members") or [], system, provenance)
    errors.extend(member_errors)
    supports, support_errors = _supports(form.get("supports") or [], provenance)
    errors.extend(support_errors)
    if errors:
        return None, errors
    if not levels:
        errors.append("Enter at least one level.")
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
        "levels": levels,
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
    if not levels or not members or not supports:
        return False
    for level in levels:
        if not _only_keys(level, _LEVEL_KEYS):
            return False
        if not _provenance_is_office(level.get("provenance")):
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


def _level_row(level):
    elevation = level.get("elevation") if "elevation" in level else None
    return {
        "id": level.get("id") or "",
        "name": level.get("name") or "",
        "elevation": "" if elevation is None else _show_number(elevation),
    }


def _member_groups(members):
    """Restore one row per saved group.

    A group id keeps that row separate from another row with the same
    role, size, and length. Older office ids have no group id. Those
    rows stay grouped by role, size, and length, which is how they
    were saved.
    """
    groups = []
    index = {}
    for member in members:
        length = member.get("length") or {}
        match = _GROUP_ID.match(str(member.get("id") or ""))
        if match:
            key = ("group", match.group(1))
            token = match.group(1)
        else:
            key = (
                "legacy",
                member.get("role") or "",
                member.get("member_size") or "",
                length.get("value"),
                length.get("unit") or "",
            )
            token = ""
        if key in index:
            groups[index[key]]["count"] = str(int(groups[index[key]]["count"]) + 1)
            continue
        index[key] = len(groups)
        groups.append(
            {
                "token": token,
                "role": member.get("role") or "",
                "member_size": member.get("member_size") or "",
                "length": "" if length.get("value") is None else _show_number(length.get("value")),
                "length_unit": length.get("unit") or "",
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


def _levels(rows, provenance):
    built = []
    errors = []
    seen = set()
    for row in rows:
        if not _level_row_used(row):
            continue
        name = _text(row.get("name"))
        if not name:
            errors.append("Enter the level name.")
            continue
        elevation_text = _text(row.get("elevation"))
        elevation = None
        if elevation_text:
            elevation, elevation_error = _required_number(
                elevation_text,
                f"Enter a numeric elevation for {name}.",
            )
            if elevation_error:
                errors.append(elevation_error)
                continue
        level_id = _text(row.get("id"))
        if not _LEVEL_ID.match(level_id):
            level_id = "level-" + secrets.token_hex(4)
        if level_id in seen:
            errors.append("Each level needs its own identity.")
            continue
        seen.add(level_id)
        recorded = {
            "id": level_id,
            "name": name,
            "provenance": dict(provenance),
        }
        if elevation is not None:
            recorded["elevation"] = elevation
        built.append(recorded)
    return built, errors


def _members(rows, system, provenance):
    built = []
    errors = []
    seen_tokens = set()
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
        token = _text(row.get("token"))
        if not _TOKEN.match(token) or token in seen_tokens:
            if token and token in seen_tokens:
                errors.append("Each member group needs its own identity.")
                continue
            token = secrets.token_hex(4)
        seen_tokens.add(token)
        for number in range(1, count + 1):
            item = {
                "id": f"g{token}-{number}",
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


def _level_row_used(row):
    return any(_text(row.get(key)) for key in ("id", "name", "elevation"))


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


def _blank_level():
    return {"id": "", "name": "", "elevation": ""}


def _blank_member():
    return {
        "token": "",
        "role": "",
        "member_size": "",
        "length": "",
        "length_unit": "",
        "count": "",
    }


def _blank_support():
    return {"kind": "", "count": ""}

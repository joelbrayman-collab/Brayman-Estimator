"""Plans-page request for a dimensioned plan.

This page builds one drawing type. It does not calculate members, and it does
not turn a candidate into a project drawing.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional

from app.models.plan_generation_candidate import PlanGenerationCandidate
from app.services.plan_generation.validation import DRAWING_TYPE_DIMENSIONED_PLAN

MEMBER_ROW_COUNT = 4
UNSUPPORTED_DRAWING_MESSAGE = "This drawing type cannot be built here."


def empty_member() -> dict:
    return {
        "id": "",
        "role": "",
        "kind": "",
        "x": "",
        "y": "",
        "x1": "",
        "y1": "",
        "x2": "",
        "y2": "",
    }


def empty_build_form(project_name: str) -> dict:
    return {
        "measurement_system": "",
        "paper_width": "",
        "paper_height": "",
        "paper_unit": "",
        "scale_statement": "",
        "scale_unit": "",
        "origin": "",
        "title": project_name or "",
        "members": [empty_member() for _ in range(MEMBER_ROW_COUNT)],
    }


def build_form_from_post(form: Mapping, project_name: str) -> dict:
    """Keep what the contractor typed. Blank geometry stays blank."""
    values = empty_build_form("")
    values["measurement_system"] = _text(form.get("measurement_system"))
    values["paper_width"] = _text(form.get("paper_width"))
    values["paper_height"] = _text(form.get("paper_height"))
    values["paper_unit"] = _text(form.get("paper_unit"))
    values["scale_statement"] = _text(form.get("scale_statement"))
    values["scale_unit"] = _text(form.get("scale_unit"))
    values["origin"] = _text(form.get("origin"))
    posted_title = form.get("title")
    values["title"] = project_name or "" if posted_title is None else _text(posted_title)
    members = []
    for index in range(MEMBER_ROW_COUNT):
        member = empty_member()
        for key in member:
            member[key] = _text(form.get(f"member_{key}_{index}"))
        members.append(member)
    values["members"] = members
    return values


def dimensioned_plan_request_from_form(form: Mapping) -> tuple[bool, Optional[dict]]:
    """Return whether this page may build the posted type, and the request.

    A type other than dimensioned_plan is refused here. No request is returned,
    so nothing is rendered or stored.
    """
    posted_type = _text(form.get("drawing_type"))
    if posted_type and posted_type != DRAWING_TYPE_DIMENSIONED_PLAN:
        return False, None
    payload: dict[str, Any] = {
        "drawing_type": DRAWING_TYPE_DIMENSIONED_PLAN,
        "assumptions": [],
        "uncertainty_flags": [],
        "exclusions": [],
    }
    system = _text(form.get("measurement_system"))
    if system:
        payload["measurement_system"] = system
    paper = _paper(form)
    if paper is not None:
        payload["paper"] = paper
    scale = _scale(form)
    if scale is not None:
        payload["scale"] = scale
    origin = _text(form.get("origin"))
    if origin:
        payload["origin"] = origin
    title = _text(form.get("title"))
    if title:
        payload["title"] = title
    payload["members"] = _members(form)
    return True, payload


def candidates_for_project(organization_id: str, project_id: int):
    return (
        PlanGenerationCandidate.query.filter_by(
            organization_id=organization_id,
            project_id=project_id,
        )
        .order_by(PlanGenerationCandidate.id.asc())
        .all()
    )


def _members(form: Mapping) -> list:
    members = []
    for index in range(MEMBER_ROW_COUNT):
        member = {
            "id": _text(form.get(f"member_id_{index}")),
            "role": _text(form.get(f"member_role_{index}")),
            "kind": _text(form.get(f"member_kind_{index}")),
            "x": _text(form.get(f"member_x_{index}")),
            "y": _text(form.get(f"member_y_{index}")),
            "x1": _text(form.get(f"member_x1_{index}")),
            "y1": _text(form.get(f"member_y1_{index}")),
            "x2": _text(form.get(f"member_x2_{index}")),
            "y2": _text(form.get(f"member_y2_{index}")),
        }
        if not any(member.values()):
            continue
        item: dict[str, Any] = {}
        if member["id"]:
            item["id"] = member["id"]
        if member["role"]:
            item["role"] = member["role"]
        geometry = _geometry(member)
        if geometry is not None:
            item["geometry"] = geometry
        members.append(item)
    return members


def _geometry(member: Mapping) -> Optional[dict]:
    kind = member["kind"]
    if kind == "point":
        return {
            "kind": "point",
            "x": _posted_number(member["x"]),
            "y": _posted_number(member["y"]),
        }
    if kind == "segment":
        return {
            "kind": "segment",
            "x1": _posted_number(member["x1"]),
            "y1": _posted_number(member["y1"]),
            "x2": _posted_number(member["x2"]),
            "y2": _posted_number(member["y2"]),
        }
    if kind:
        return {"kind": kind}
    return None


def _paper(form: Mapping) -> Optional[dict]:
    width = _text(form.get("paper_width"))
    height = _text(form.get("paper_height"))
    unit = _text(form.get("paper_unit"))
    if not width and not height and not unit:
        return None
    return {
        "width": _posted_number(width),
        "height": _posted_number(height),
        "unit": unit,
    }


def _scale(form: Mapping) -> Optional[dict]:
    statement = _text(form.get("scale_statement"))
    unit = _text(form.get("scale_unit"))
    if not statement and not unit:
        return None
    payload = {}
    if statement:
        payload["statement"] = statement
    if unit:
        payload["unit"] = unit
    return payload


def _posted_number(value: str):
    if value == "":
        return None
    try:
        number = float(value)
    except ValueError:
        return value
    if not math.isfinite(number):
        return value
    return number


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()

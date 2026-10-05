"""PROOF ONLY. Drawing specification for the QCAD crew-sheet proof.

This is not a Construction Model and it is not wired into the application.
It reads the generic complete-deck fixture and names the profiles, cuts,
relationships, dimensions, and sheet fields that fixture already stores.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tests/fixtures/construction_model/complete_deck_fixture.py"
MODEL_PATH = ROOT / "app/services/construction_model/model.py"

MEMBER_IDS = ("post-1", "beam-front", "joist-1")
POST_BEAM_BEARING_ID = "rel-bear-post-1-beam-front"
REFUSAL = "You need to provide this information."
FEET_TO_INCHES = 12.0


def _load(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture():
    return _load("complete_deck_fixture_qcad_proof", FIXTURE_PATH)


def _model_module():
    return _load("construction_model_model_qcad_proof", MODEL_PATH)


def _inches(feet: float) -> float:
    return round(float(feet) * FEET_TO_INCHES, 6)


def _member(model: dict, identifier: str) -> dict:
    found = [item for item in model["members"] if item["id"] == identifier]
    if len(found) != 1:
        raise KeyError(identifier)
    return found[0]


def _relationship(model: dict, *, kind: str, source: str, target: str):
    found = [
        item
        for item in model["relationships"]
        if item.get("kind") == kind and item.get("from_id") == source and item.get("to_id") == target
    ]
    if not found:
        return None
    return found[0]


def _span_inches(coordinates) -> float:
    start, end = coordinates[0], coordinates[-1]
    dx = float(end["x"]) - float(start["x"])
    dy = float(end["y"]) - float(start["y"])
    dz = float(end["z"]) - float(start["z"])
    return _inches((dx * dx + dy * dy + dz * dz) ** 0.5)


def _polygon(profile: dict) -> list:
    points = [[_inches(point["u"]), _inches(point["v"])] for point in profile["coordinates"]]
    if len(points) > 1 and points[0] == points[-1]:
        points = points[:-1]
    return points


def _profile(view_profile, member: dict, horizontal: str, vertical: str) -> list:
    profile = view_profile(member, horizontal, vertical)
    if profile is None:
        raise ValueError(f"{member['id']} has no {horizontal}/{vertical} profile")
    return _polygon(profile)


def drawing_specification(model=None, omit_relationship_ids=()):
    """Governed render packet for post-1, beam-front, and joist-1 only."""
    fixture = _fixture()
    model_module = _model_module()
    source = fixture.deck_model() if model is None else model
    omitted = set(omit_relationship_ids)
    relationships = [item for item in source["relationships"] if item.get("id") not in omitted]
    working = dict(source)
    working["relationships"] = relationships
    view_profile = model_module.view_profile
    status = source.get("project_document_status")
    sheet = fixture.sheet_definition()
    section = fixture.section_requests()[0]
    detail_request = next(item for item in fixture.detail_requests() if item["id"] == "post-beam")

    members = {identifier: _member(working, identifier) for identifier in MEMBER_IDS}
    post = members["post-1"]
    beam = members["beam-front"]
    joist = members["joist-1"]

    bearing = next((item for item in relationships if item.get("id") == POST_BEAM_BEARING_ID), None)
    if detail_request["relationship_id"] != POST_BEAM_BEARING_ID:
        raise ValueError("The fixture detail request no longer names the post/beam bearing.")
    post_supports_beam = _relationship(working, kind="supports", source="post-1", target="beam-front")
    beam_supports_joist = _relationship(working, kind="supports", source="beam-front", target="joist-1")

    plan = {
        identifier: {
            "id": member["id"],
            "role": member["role"],
            "member_size": member["member_size"],
            "polygon": _profile(view_profile, member, "x", "y"),
        }
        for identifier, member in members.items()
    }
    elevation = {
        identifier: {
            "id": member["id"],
            "role": member["role"],
            "member_size": member["member_size"],
            "polygon": _profile(view_profile, member, "x", "z"),
        }
        for identifier, member in members.items()
    }

    post_height = _span_inches(post["geometry"]["coordinates"])
    beam_length = _span_inches(beam["geometry"]["coordinates"])
    joist_length = _span_inches(joist["geometry"]["coordinates"])

    dimensions = {
        "post_height": {
            "member_id": "post-1",
            "p1": [elevation["post-1"]["polygon"][0][0], min(point[1] for point in elevation["post-1"]["polygon"])],
            "p2": [elevation["post-1"]["polygon"][0][0], max(point[1] for point in elevation["post-1"]["polygon"])],
            "inches": post_height,
        },
        "beam_length": {
            "member_id": "beam-front",
            "p1": [min(point[0] for point in plan["beam-front"]["polygon"]), plan["beam-front"]["polygon"][0][1]],
            "p2": [max(point[0] for point in plan["beam-front"]["polygon"]), plan["beam-front"]["polygon"][0][1]],
            "inches": beam_length,
        },
        "joist_length": {
            "member_id": "joist-1",
            "p1": [plan["joist-1"]["polygon"][0][0], min(point[1] for point in plan["joist-1"]["polygon"])],
            "p2": [plan["joist-1"]["polygon"][0][0], max(point[1] for point in plan["joist-1"]["polygon"])],
            "inches": joist_length,
        },
    }

    connector = None
    for connection in source.get("connections") or []:
        geometry = connection.get("connector_geometry") or {}
        if geometry.get("relationship_id") == POST_BEAM_BEARING_ID:
            connector = connection
            break

    if bearing is None:
        detail = {"refused": True, "message": REFUSAL, "block_name": None}
    else:
        surface = bearing["bearing_surface"]["coordinates"]
        bearing_inches = _span_inches(surface)
        dimensions["bearing"] = {
            "relationship_id": bearing["id"],
            "p1": [_inches(surface[0]["x"]), _inches(surface[0]["z"])],
            "p2": [_inches(surface[-1]["x"]), _inches(surface[-1]["z"])],
            "inches": bearing_inches,
        }
        plate = None
        if connector and connector.get("connector_geometry"):
            geometry = connector["connector_geometry"]
            plate_points = [
                [_inches(point["x"]), _inches(point["z"])]
                for point in geometry["geometry"]["coordinates"]
            ]
            if plate_points and plate_points[0] == plate_points[-1]:
                plate_points = plate_points[:-1]
            bolts = [
                {
                    "center": [_inches(point["x"]), _inches(point["z"])],
                    "diameter_in": _inches(geometry["bolt_diameter"]),
                }
                for point in geometry["fastener_locations"]["coordinates"]
            ]
            plate = {
                "connection_id": connector["id"],
                "connector": connector.get("connector"),
                "fastener": connector.get("fastener"),
                "quantity": connector.get("quantity"),
                "width_in": _inches(geometry["width"]),
                "thickness_in": _inches(geometry["thickness"]),
                "polygon": plate_points,
                "bolts": bolts,
                "uncertainty": geometry.get("uncertainty"),
            }
        detail = {
            "refused": False,
            "message": None,
            "block_name": "POST_BEAM_DETAIL",
            "relationship_id": bearing["id"],
            "kind": bearing["kind"],
            "from_id": bearing["from_id"],
            "to_id": bearing["to_id"],
            "connector_geometry_supplied": plate is not None,
            "plate": plate,
            "post": elevation["post-1"],
            "beam": elevation["beam-front"],
        }

    joist_connection = next(
        (
            item
            for item in source.get("connections") or []
            if item.get("id") == "connection-beam-joist"
        ),
        None,
    )
    joist_geometry = (joist_connection or {}).get("connector_geometry")

    return {
        "proof": "qcad-professional-crew-drawing",
        "authority": "construction-model",
        "member_ids": list(MEMBER_IDS),
        "sheet": {
            "paper": sheet["paper"],
            "width_in": 17.0,
            "height_in": 11.0,
            "project_name": sheet["project_name"],
            "drawing_title": "Post, beam, and joist",
            "sheet_number": sheet["sheet_number"],
            "revision": sheet["revision"],
            "date": sheet["date"],
            "organization_name": sheet["organization_name"],
            "address": sheet["address"],
            "document_status": model_module.DOCUMENT_STATUS_TEXT[status],
            "scale_note": "AS NOTED",
        },
        "section": {
            "id": section["id"],
            "direction": section["section_direction"],
            "location_ft": float(section["section_location"]),
            "location_in": _inches(section["section_location"]),
            "cut_depth_ft": float(section["cut_depth"]),
            "horizontal": "x",
            "vertical": "z",
        },
        "plan": plan,
        "elevation": elevation,
        "dimensions": dimensions,
        "detail": detail,
        "relationships": {
            "post_beam_bearing_id": None if bearing is None else bearing["id"],
            "post_supports_beam_id": None if post_supports_beam is None else post_supports_beam["id"],
            "beam_supports_joist_id": None if beam_supports_joist is None else beam_supports_joist["id"],
            "joist_connector_geometry_supplied": bool(joist_geometry),
            "joist_connector_name": None if joist_connection is None else joist_connection.get("connector"),
            "joist_callout": (
                None
                if beam_supports_joist is None
                else f"{beam_supports_joist['from_id']} supports {beam_supports_joist['to_id']}"
            ),
        },
        "labels": {
            "post-1": f"{post['id']}  {post['member_size']}",
            "beam-front": f"{beam['id']}  {beam['member_size']}",
            "joist-1": f"{joist['id']}  {joist['member_size']}",
        },
    }

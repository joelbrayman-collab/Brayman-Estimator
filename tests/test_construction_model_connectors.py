"""Slice 14: connector geometry is drawn only when the model supplies it."""

from __future__ import annotations

import copy
from io import BytesIO

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model.completeness import assess_construction_model
from app.services.construction_model.sheet import compose_construction_wave
from app.services.construction_model.views import (
    _connection_has_geometry,
    group_connection_rows,
    project_connector_geometry,
    project_construction_wave,
)
from app.services.organizations import ensure_default_organization
from tests.fixtures.construction_model.complete_deck_fixture import (
    deck_model,
    detail_requests,
    section_requests,
    sheet_definition,
    sheet_program,
)


def _accepted(model=None):
    return assess_construction_model(model or deck_model()).accepted


def _wave(model=None):
    payload = deck_model() if model is None else model
    return project_construction_wave(payload, sections=section_requests(), details=detail_requests())


def test_metadata_only_connector_has_no_shape():
    connection = next(item for item in _accepted()["connections"] if item["id"] == "connection-stringer-tread")
    assert connection["connector"] == "fixture tread clip"
    assert connection["quantity"] == 2
    assert not _connection_has_geometry(connection)
    detail = next(item for item in _wave().details if item.view_id == "stringer-tread")
    overlays = project_connector_geometry(
        _accepted(),
        [element["id"] for element in detail.elements],
        detail.horizontal_axis,
        detail.vertical_axis,
    )
    assert overlays == ()


def test_supplied_geometry_projects_on_the_relationship():
    accepted = _accepted()
    connection = next(item for item in accepted["connections"] if item["id"] == "connection-post-beam")
    block = connection["connector_geometry"]
    assert block["relationship_id"] == "rel-bear-post-1-beam-front"
    assert block["reference_ids"] == ["post-1", "beam-front"]
    assert block["connector"] == "fixture post cap"
    assert block["uncertainty"] == "Fixture plate thickness is nominal."
    assert _connection_has_geometry(connection)
    detail = next(item for item in _wave().details if item.view_id == "post-beam")
    section = _wave().sections[0]
    detail_overlay = project_connector_geometry(
        accepted,
        [element["id"] for element in detail.elements],
        detail.horizontal_axis,
        detail.vertical_axis,
    )
    section_overlay = project_connector_geometry(
        accepted,
        [element["id"] for element in section.elements],
        section.horizontal_axis,
        section.vertical_axis,
    )
    assert len(detail_overlay) == 1
    assert detail_overlay[0]["relationship_id"] == "rel-bear-post-1-beam-front"
    assert detail_overlay[0]["line"] == section_overlay[0]["line"]
    assert len(detail_overlay[0]["fasteners"]) == 2
    assert detail_overlay[0]["dimensions"]["width"] == block["width"]
    assert detail_overlay[0]["dimensions"]["thickness"] == block["thickness"]
    assert detail_overlay[0]["dimensions"]["bolt_diameter"] == block["bolt_diameter"]
    assert detail_overlay[0]["uncertainty"] == "Fixture plate thickness is nominal."


def test_connector_geometry_without_its_relationship_is_refused():
    payload = deck_model()
    payload["relationships"] = [
        item for item in payload["relationships"] if item["id"] != "rel-bear-post-1-beam-front"
    ]
    before = copy.deepcopy(payload["members"])
    assessment = assess_construction_model(payload)
    assert assessment.complete is False
    assert any("relationship" in issue.fact.lower() for issue in assessment.issues)
    assert payload["members"] == before


def test_product_name_and_quantity_do_not_invent_geometry_or_fastener_locations():
    payload = deck_model()
    clip = next(item for item in payload["connections"] if item["id"] == "connection-stringer-tread")
    clip["connector"] = "Typical joist hanger"
    clip["quantity"] = 8
    accepted = assess_construction_model(payload).accepted
    stored = next(item for item in accepted["connections"] if item["id"] == "connection-stringer-tread")
    assert not _connection_has_geometry(stored)
    overlays = project_connector_geometry(accepted, stored["participant_ids"], "y", "z")
    assert overlays == ()
    assert "fastener_locations" not in stored


def test_schedule_distinguishes_metadata_from_supplied_geometry():
    accepted = _accepted()
    members = {item["id"]: item for item in accepted["members"]}
    rows = group_connection_rows(accepted["connections"], members)
    by_connector = {row["connector"]: row["geometry"] for row in rows}
    assert by_connector["fixture post cap"] == "geometry supplied"
    assert by_connector["fixture tread clip"] == "metadata only"


def test_connector_drawing_does_not_move_members_or_write_records():
    model = deck_model()
    before = copy.deepcopy(model["members"])
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        counts = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
        result = compose_construction_wave(
            model,
            sheet_definition(),
            sections=section_requests(),
            details=detail_requests(),
            sheet_program=sheet_program(),
        )
        after = (Project.query.count(), PlanDocument.query.count(), Estimate.query.count())
    assert model["members"] == before
    assert counts == after == (0, 0, 0)
    assert result.composed is True
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(result.pdf_bytes)).pages)
    assert "GEOMETRY SUPPLIED" in text
    assert "GEOMETRY NOT SUPPLIED" in text
    assert "WIDTH 0'-3\"" in text
    assert "THICKNESS 1/4\"" in text
    assert "BOLT 1/2\"" in text
    assert "$" not in text

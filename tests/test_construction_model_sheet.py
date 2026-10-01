"""Slice 3: governed 11×17 sheet from one Construction Model."""

from __future__ import annotations

import copy
from io import BytesIO

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import (
    DOCUMENT_STATUS_ISSUED_FOR_PERMIT,
    DOCUMENT_STATUS_PRELIMINARY,
    compose_construction_sheet,
)
from app.services.construction_model.completeness import CODE_MISSING_SUPPORT
from app.services.construction_model.sheet import (
    CODE_GEOMETRY_DOES_NOT_FIT_SHEET,
    PAGE_HEIGHT,
    PAGE_WIDTH,
)
from app.services.organizations import ensure_default_organization


def _provenance(source="project_input"):
    return {"source": source}


def _point(x, y, z):
    return {"kind": "point", "coordinates": [{"x": x, "y": y, "z": z}]}


def _segment(start, end):
    return {
        "kind": "segment",
        "coordinates": [
            {"x": start[0], "y": start[1], "z": start[2]},
            {"x": end[0], "y": end[1], "z": end[2]},
        ],
    }


def _model(**overrides):
    payload = {
        "structure_class": "deck",
        "project_document_status": DOCUMENT_STATUS_PRELIMINARY,
        "measurement_system": "imperial",
        "levels": [
            {
                "id": "walk",
                "name": "Walking surface",
                "elevation": 3,
                "provenance": _provenance(),
            }
        ],
        "members": [
            {
                "id": "beam-a",
                "role": "beam",
                "geometry": _segment((0, 1, 2), (8, 1, 2)),
                "provenance": _provenance("governed_calculation_result"),
            },
            {
                "id": "joist-a",
                "role": "joist",
                "geometry": _segment((1, 0, 3), (1, 5, 3)),
                "provenance": _provenance(),
            },
        ],
        "supports": [
            {
                "id": "support-a",
                "kind": "pier",
                "geometry": _point(0, 1, 0),
                "provenance": _provenance("source_document"),
            }
        ],
        "uncertainty": [
            {
                "code": "FIELD_VERIFICATION_REQUIRED",
                "subject_id": "support-a",
                "note": "Support length is not confirmed.",
            }
        ],
    }
    payload.update(overrides)
    return payload


def _sheet(**overrides):
    payload = {
        "paper": "11x17",
        "scale": "1/4 in = 1 ft",
        "organization_name": "Brayman Construction",
        "project_name": "Sample deck",
        "address": "12 Example Road",
        "drawing_title": "Construction drawing",
        "sheet_number": "1",
        "revision": "A",
        "date": "2026-10-01",
    }
    payload.update(overrides)
    return payload


def _text(pdf_bytes: bytes) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf_bytes)).pages)


def _page(pdf_bytes: bytes):
    box = PdfReader(BytesIO(pdf_bytes)).pages[0].mediabox
    return float(box.width), float(box.height)


def test_complete_model_produces_an_11x17_sheet():
    result = compose_construction_sheet(_model(), _sheet())
    assert result.composed is True
    assert result.pdf_bytes
    assert result.manifest["paper"] == "11x17"
    width, height = _page(result.pdf_bytes)
    assert abs(width - PAGE_WIDTH) < 0.1
    assert abs(height - PAGE_HEIGHT) < 0.1
    assert width > height


def test_incomplete_model_produces_no_sheet():
    payload = _model()
    payload["supports"] = []
    result = compose_construction_sheet(payload, _sheet())
    assert result.composed is False
    assert result.pdf_bytes is None
    assert result.manifest is None
    assert result.issues[0].code == CODE_MISSING_SUPPORT
    assert result.issues[0].message.startswith("You need to provide this information.")


def test_sheet_text_names_each_view_status_scale_and_uncertainty():
    result = compose_construction_sheet(_model(), _sheet())
    text = _text(result.pdf_bytes)
    assert "PLAN" in text
    assert "FRONT ELEVATION" in text
    assert "SIDE ELEVATION" in text
    assert "Brayman Construction" in text
    assert "Sample deck" in text
    assert "12 Example Road" in text
    assert "Construction drawing" in text
    assert "Sheet 1" in text
    assert "Revision A" in text
    assert "2026-10-01" in text
    assert "PRELIMINARY CONSTRUCTION DRAWING" in text
    assert "FIELD VERIFICATION" in text
    assert "Scale 1/4 in = 1 ft" in text
    assert "Support length is not confirmed." in text
    assert "Not a permit" not in text
    assert "Not a seal" not in text


def test_issued_status_is_the_model_status():
    result = compose_construction_sheet(
        _model(project_document_status=DOCUMENT_STATUS_ISSUED_FOR_PERMIT),
        _sheet(),
    )
    text = _text(result.pdf_bytes)
    assert "CONSTRUCTION DRAWING" in text
    assert "ISSUED FOR PERMIT" in text
    assert "Not a permit" not in text


def test_sheet_element_ids_match_the_model_and_the_model_is_unchanged():
    model = _model()
    snapshot = copy.deepcopy(model)
    result = compose_construction_sheet(model, _sheet())
    assert model == snapshot
    for view_ids in result.manifest["element_ids"].values():
        assert view_ids == ["beam-a", "joist-a", "support-a"]
    assert result.manifest["uncertainty"][0]["note"] == "Support length is not confirmed."


def test_geometry_that_does_not_fit_is_refused():
    result = compose_construction_sheet(_model(), _sheet(scale="4/1 in = 1 ft"))
    assert result.composed is False
    assert result.pdf_bytes is None
    assert result.issues[0].code == CODE_GEOMETRY_DOES_NOT_FIT_SHEET
    assert result.issues[0].message.startswith("You need to provide this information.")


def test_same_input_produces_the_same_pdf_bytes():
    first = compose_construction_sheet(_model(), _sheet())
    second = compose_construction_sheet(_model(), _sheet())
    assert first.pdf_bytes == second.pdf_bytes
    assert first.manifest["pdf_sha256"] == second.manifest["pdf_sha256"]


def test_sheet_definition_cannot_carry_geometry():
    definition = _sheet()
    definition["members"] = [{"id": "extra"}]
    result = compose_construction_sheet(_model(), definition)
    assert result.composed is False
    assert result.pdf_bytes is None
    assert "without its own geometry" in result.issues[0].fact


def test_composition_does_not_write_project_plan_or_estimate():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-construction-sheet",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        projects_before = Project.query.count()
        plans_before = PlanDocument.query.count()
        estimates_before = Estimate.query.count()
        compose_construction_sheet(_model(), _sheet())
        compose_construction_sheet(_model(supports=[]), _sheet())
        assert Project.query.count() == projects_before
        assert PlanDocument.query.count() == plans_before
        assert Estimate.query.count() == estimates_before
        db.session.remove()
        db.drop_all()

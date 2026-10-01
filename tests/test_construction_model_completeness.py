"""Construction Model slice 1: representation and completeness refusal.

No views, no PDF, and no project writes.
"""

from __future__ import annotations

from pathlib import Path

from app import create_app, db
from app.models import Estimate, Project
from app.plan_intelligence.models import PlanDocument
from app.services.construction_model import (
    DOCUMENT_STATUS_ISSUED_FOR_PERMIT,
    DOCUMENT_STATUS_PRELIMINARY,
    assess_construction_model,
    element_store,
)
from app.services.construction_model.completeness import (
    CODE_INVALID_DOCUMENT_STATUS,
    CODE_MISSING_DOCUMENT_STATUS,
    CODE_MISSING_MEASUREMENT_SYSTEM,
    CODE_MISSING_SUPPORT,
)
from app.services.organizations import ensure_default_organization

PACKAGE = Path(__file__).resolve().parents[1] / "app" / "services" / "construction_model"
FORBIDDEN_SOURCE = (
    "bushel",
    "Bushel",
    "linda",
    "Linda",
    "10.5",
    "PlanDocument",
    "Estimate",
    "reportlab",
    "freecad",
    "FreeCAD",
    "cadquery",
    "build123d",
    "render_dimensioned_plan",
    "db.session",
    "helical",
)


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


def _deck(**overrides):
    payload = {
        "structure_class": "deck",
        "project_document_status": DOCUMENT_STATUS_PRELIMINARY,
        "measurement_system": "imperial",
        "levels": [
            {
                "id": "walk",
                "name": "Walking surface",
                "elevation": 3,
                "provenance": _provenance("project_input"),
            }
        ],
        "members": [
            {
                "id": "beam-a",
                "role": "beam",
                "geometry": _segment((0, 0, 2), (4, 0, 2)),
                "provenance": _provenance("governed_calculation_result"),
            },
            {
                "id": "joist-a",
                "role": "joist",
                "geometry": _segment((0, 0, 3), (0, 6, 3)),
                "provenance": _provenance("project_input"),
            },
        ],
        "supports": [
            {
                "id": "support-a",
                "kind": "pier",
                "geometry": _point(0, 0, 0),
                "provenance": _provenance("source_document"),
            },
            {
                "id": "support-b",
                "kind": "pier",
                "geometry": _point(4, 0, 0),
                "provenance": _provenance("instance_configuration"),
            },
        ],
    }
    payload.update(overrides)
    return payload


def test_valid_deck_class_model_is_one_store():
    result = assess_construction_model(_deck())
    assert result.complete is True
    assert result.generation_permitted is True
    assert result.drawing_artifact is None
    assert result.accepted["structure_class"] == "deck"
    assert result.accepted["measurement_system"] == "imperial"
    assert len(result.accepted["members"]) == 2
    assert len(result.accepted["supports"]) == 2
    store = element_store(result.accepted)
    assert store["members"] == result.accepted["members"]
    assert store["supports"] == result.accepted["supports"]
    assert "plan" not in store
    assert "elevation" not in store
    assert "section" not in store


def test_required_facts_are_identified_when_the_model_is_empty():
    result = assess_construction_model({"structure_class": "deck"})
    fields = {issue.field for issue in result.issues}
    assert "project_document_status" in fields
    assert "measurement_system" in fields
    assert "levels" in fields
    assert "members" in fields
    assert "supports" in fields
    assert result.complete is False
    assert result.generation_permitted is False
    assert result.accepted is None
    assert result.drawing_artifact is None


def test_complete_model_passes():
    result = assess_construction_model(
        _deck(project_document_status=DOCUMENT_STATUS_ISSUED_FOR_PERMIT)
    )
    assert result.complete is True
    assert result.generation_permitted is True
    assert result.accepted["project_document_status"] == DOCUMENT_STATUS_ISSUED_FOR_PERMIT
    assert result.accepted["project_document_status_text"] == (
        "CONSTRUCTION DRAWING — ISSUED FOR PERMIT"
    )


def test_incomplete_model_fails_and_names_the_missing_fact():
    payload = _deck()
    payload["supports"] = []
    result = assess_construction_model(payload)
    assert result.complete is False
    assert result.generation_permitted is False
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.code == CODE_MISSING_SUPPORT
    assert issue.field == "supports"
    assert issue.fact == "At least one support"
    assert issue.message == "You need to provide this information. At least one support."


def test_missing_member_geometry_names_that_member():
    payload = _deck()
    del payload["members"][0]["geometry"]
    result = assess_construction_model(payload)
    assert result.generation_permitted is False
    issue = result.issues[0]
    assert issue.field == "members[beam-a].geometry"
    assert issue.message.startswith("You need to provide this information.")
    assert "beam-a" in issue.fact


def test_uncertainty_stays_on_a_complete_model():
    note = {
        "code": "FIELD_VERIFICATION_REQUIRED",
        "subject_id": "support-a",
        "note": "Support length is not confirmed.",
    }
    payload = _deck(uncertainty=[note])
    first = assess_construction_model(payload)
    second = assess_construction_model(first.accepted)
    assert first.complete is True
    assert first.uncertainty == (note,)
    assert first.accepted["uncertainty"] == [note]
    assert second.complete is True
    assert second.accepted["uncertainty"] == [note]
    assert second.uncertainty == (note,)


def test_optional_information_does_not_block_completeness():
    result = assess_construction_model(_deck())
    assert result.complete is True
    for name in (
        "relationships",
        "connections",
        "openings",
        "materials",
        "dimensions",
        "constraints",
        "assumptions",
    ):
        assert result.accepted[name] == []


def test_generic_engine_disclaimer_is_not_a_project_status():
    result = assess_construction_model(
        _deck(project_document_status="Not a permit. Not a seal.")
    )
    assert result.complete is False
    assert result.issues[0].code == CODE_INVALID_DOCUMENT_STATUS
    assert "professional seal" in result.issues[0].fact
    assert result.issues[0].message.startswith("You need to provide this information.")


def test_missing_status_is_its_own_fact():
    payload = _deck()
    del payload["project_document_status"]
    result = assess_construction_model(payload)
    assert result.issues[0].code == CODE_MISSING_DOCUMENT_STATUS
    assert result.issues[0].message == (
        "You need to provide this information. The project drawing status."
    )


def test_missing_measurement_system_is_named():
    payload = _deck()
    payload["measurement_system"] = ""
    result = assess_construction_model(payload)
    assert result.issues[0].code == CODE_MISSING_MEASUREMENT_SYSTEM
    assert "measurement system" in result.issues[0].fact.lower()


def test_source_has_no_job_defaults_and_no_drawing_side_effects():
    for path in PACKAGE.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_SOURCE:
            assert token not in source, path.name


def test_a_different_support_count_is_still_complete():
    payload = _deck()
    payload["supports"] = payload["supports"][:1]
    result = assess_construction_model(payload)
    assert result.complete is True
    assert len(result.accepted["supports"]) == 1


def test_assessment_does_not_write_project_plan_or_estimate():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-construction-model",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        projects_before = Project.query.count()
        plans_before = PlanDocument.query.count()
        estimates_before = Estimate.query.count()
        assess_construction_model(_deck())
        assess_construction_model({"structure_class": "deck"})
        assert Project.query.count() == projects_before
        assert PlanDocument.query.count() == plans_before
        assert Estimate.query.count() == estimates_before
        db.session.remove()
        db.drop_all()

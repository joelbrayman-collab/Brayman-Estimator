"""PGE-3: draw a supplied stair result. No stair calculation and no project write."""

from __future__ import annotations

import json
import math
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app import create_app, db
from app.models import Estimate, Project
from app.models.project_work_package import ProjectWorkPackage
from app.plan_intelligence.models import PlanDocument
from app.services.organizations import ensure_default_organization
from app.services.plan_generation import render_plan_generation, validate_plan_generation_request
from app.services.plan_generation.render import DISCLAIMER
from app.services.plan_generation.validation import CODE_MISSING_STAIR_GEOMETRY

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "plan_generation"
PACKAGE = REPO_ROOT / "app" / "services" / "plan_generation"
METRES_PER_INCH = 0.0254


def _load(name: str) -> dict:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    payload.pop("fixture_role", None)
    return payload


def _text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _slope(points: list) -> float:
    start, end = points[0], points[-1]
    return (end[1] - start[1]) / (end[0] - start[0])


def _metric_twin(payload: dict) -> dict:
    twin = json.loads(json.dumps(payload))
    twin["measurement_system"] = "metric"
    twin["scale"]["unit"] = "m"
    geometry = twin["stair_geometry"]
    geometry["unit"] = "m"
    for key in ("total_rise", "total_run", "rise", "going"):
        geometry[key] = geometry[key] * METRES_PER_INCH
    for point in geometry["profile"]:
        point["x"] *= METRES_PER_INCH
        point["y"] *= METRES_PER_INCH
    for point in geometry["stringer"]:
        point["x"] *= METRES_PER_INCH
        point["y"] *= METRES_PER_INCH
    throat = geometry["throat"]
    throat["value"] *= METRES_PER_INCH
    throat["unit"] = "m"
    segment = throat["segment"]
    for key in ("x1", "y1", "x2", "y2"):
        segment[key] *= METRES_PER_INCH
    geometry["nosing"]["value"] *= METRES_PER_INCH
    geometry["nosing"]["unit"] = "m"
    return twin


def test_recorded_stair_renders_supplied_content():
    payload = _load("stair_detail_recorded.json")
    result = render_plan_generation(payload)
    assert result.rendered is True
    text = _text(result.pdf_bytes)
    assert payload["title"] in text
    assert payload["scale"]["statement"] in text
    assert payload["origin"] in text
    assert "imperial" in text
    assert DISCLAIMER in text
    assert "Total rise 38 in" in text
    assert "Total run 44 in" in text
    assert "Risers 5" in text
    assert "Treads 4" in text
    assert "Rise 7.6 in" in text
    assert "Going 11 in" in text
    assert "Angle 40.82 deg" in text
    assert "Throat 4.997 in" in text
    assert "Nosing 0.75 in" in text
    assert "STRUCTURAL_VERIFICATION_REQUIRED" in text
    assert "stringer" in text
    geometry = payload["stair_geometry"]
    assert result.manifest["riser_count"] == geometry["riser_count"]
    assert result.manifest["tread_count"] == geometry["tread_count"]
    assert result.manifest["angle_degrees"] == geometry["angle_degrees"]
    assert result.manifest["total_rise"] == geometry["total_rise"]
    assert result.manifest["total_run"] == geometry["total_run"]
    assert result.manifest["engine_version"] == "pge-3"
    assert result.manifest["validation_engine_version"] == "pge-1"
    assert result.manifest["calculation_provenance"]["result_id"] == "fixture-recorded-stair"
    assert result.manifest["calculation_provenance"]["engine_id"] == "stair"
    assert result.manifest["calculation_fingerprint"] is None


def test_alternate_stair_renders_differently_and_omits_throat():
    recorded = render_plan_generation(_load("stair_detail_recorded.json"))
    alternate = render_plan_generation(_load("stair_detail_alternate.json"))
    assert alternate.rendered is True
    text = _text(alternate.pdf_bytes)
    assert "Alternate stair profile" in text
    assert "1:5" in text
    assert "metric" in text
    assert "Risers 3" in text
    assert "Treads 2" in text
    assert "Throat" not in text
    assert "Nosing" not in text
    assert "38 in" not in text
    assert recorded.pdf_bytes != alternate.pdf_bytes
    assert recorded.manifest["sheet_id"] != alternate.manifest["sheet_id"]
    assert _slope(recorded.manifest["placed_stringer"]) != _slope(alternate.manifest["placed_stringer"])


def test_missing_stair_geometry_produces_no_pdf():
    payload = _load("stair_detail_alternate.json")
    payload.pop("stair_geometry")
    result = render_plan_generation(payload)
    assert result.rendered is False
    assert result.pdf_bytes is None
    assert result.manifest is None
    assert result.issues[0].code == CODE_MISSING_STAIR_GEOMETRY


def test_rise_run_angle_and_counts_follow_supplied_geometry():
    payload = _load("stair_detail_recorded.json")
    result = render_plan_generation(payload)
    geometry = payload["stair_geometry"]
    placed = result.manifest["placed_stringer"]
    rise = placed[-1][1] - placed[0][1]
    run = placed[-1][0] - placed[0][0]
    assert math.isclose(rise / run, geometry["total_rise"] / geometry["total_run"], rel_tol=1e-9)
    assert math.isclose(
        math.degrees(math.atan2(rise, run)),
        geometry["angle_degrees"],
        abs_tol=1e-6,
    )
    assert result.manifest["riser_count"] == 5
    assert result.manifest["tread_count"] == 4
    assert len(result.manifest["placed_profile"]) == len(geometry["profile"])
    profile_rise = result.manifest["placed_profile"][-1][1] - result.manifest["placed_profile"][0][1]
    assert math.isclose(profile_rise, rise, rel_tol=1e-9)


def test_imperial_and_metric_keep_the_same_physical_geometry():
    imperial = render_plan_generation(_load("stair_detail_recorded.json"))
    metric = render_plan_generation(_metric_twin(_load("stair_detail_recorded.json")))
    assert metric.rendered is True
    assert "metric" in _text(metric.pdf_bytes)
    assert "Throat" in _text(metric.pdf_bytes)
    for key in ("placed_stringer", "placed_profile"):
        for imperial_point, metric_point in zip(imperial.manifest[key], metric.manifest[key]):
            assert math.isclose(imperial_point[0], metric_point[0], abs_tol=0.02)
            assert math.isclose(imperial_point[1], metric_point[1], abs_tol=0.02)


def test_supplied_fingerprint_is_echoed_and_not_computed():
    payload = _load("stair_detail_recorded.json")
    payload["stair_geometry"]["provenance"]["calculation_fingerprint"] = "echo-this-token"
    result = render_plan_generation(payload)
    assert result.manifest["calculation_fingerprint"] == "echo-this-token"
    assert result.manifest["calculation_provenance"]["calculation_fingerprint"] == "echo-this-token"


def test_same_stair_request_is_byte_stable():
    payload = _load("stair_detail_alternate.json")
    first = render_plan_generation(payload)
    second = render_plan_generation(payload)
    assert first.pdf_bytes == second.pdf_bytes
    assert first.manifest == second.manifest


def test_stair_package_does_not_import_foreign_stair_code():
    source = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    for token in (
        "stair_detail.py",
        "stair_detail_r2",
        "capability_test_plan",
        "StairDiagram",
        "stairs.mjs",
        "calculation_result_contract",
        "atan",
        "PlanDocument",
    ):
        assert token not in source


def test_stair_render_does_not_write_business_records():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-stair-render",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        before = (
            Project.query.count(),
            PlanDocument.query.count(),
            Estimate.query.count(),
            ProjectWorkPackage.query.count(),
        )
        render_plan_generation(_load("stair_detail_alternate.json"))
        validate_plan_generation_request(_load("stair_detail_recorded.json"))
        after = (
            Project.query.count(),
            PlanDocument.query.count(),
            Estimate.query.count(),
            ProjectWorkPackage.query.count(),
        )
        assert before == after
        db.session.remove()
        db.drop_all()

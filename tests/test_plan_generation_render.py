"""PGE-2: render an accepted dimensioned plan. No project drawing is stored."""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader
from io import BytesIO

from app import create_app, db
from app.models import Estimate, Project
from app.models.project_work_package import ProjectWorkPackage
from app.plan_intelligence.models import PlanDocument
from app.services.organizations import ensure_default_organization
from app.services.plan_generation import render_dimensioned_plan, validate_plan_generation_request
from app.services.plan_generation.render import DISCLAIMER
from app.services.plan_generation.validation import CODE_MISSING_TITLE, CODE_UNSUPPORTED_DRAWING_TYPE

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "plan_generation"
RENDERER = REPO_ROOT / "app" / "services" / "plan_generation" / "render.py"
FORBIDDEN_SOURCE = (
    "ALLOW_2X8_16",
    "ALLOW_2X6_16",
    "ALLOW_DBL_2X10",
    "ALLOW_DBL_2X6",
    "capability_test_plan",
    "stair_detail",
    "Linda",
    "Bushel",
    "10.5",
    "stringer",
    "PlanDocument",
)


def _load(name: str) -> dict:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    payload.pop("fixture_role", None)
    return payload


def _text(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _page_points(pdf_bytes: bytes) -> tuple:
    box = PdfReader(BytesIO(pdf_bytes)).pages[0].mediabox
    return float(box.width), float(box.height)


def test_bushel_fixture_renders_requested_content():
    payload = _load("bushel_dimensioned_plan.json")
    result = render_dimensioned_plan(payload)
    assert result.rendered is True
    assert result.pdf_bytes
    text = _text(result.pdf_bytes)
    assert payload["title"] in text
    assert payload["scale"]["statement"] in text
    assert payload["origin"] in text
    assert "imperial" in text
    assert DISCLAIMER in text
    for member in payload["members"]:
        assert member["id"] in text
        assert member["role"] in text
    assert "exclusion" in text
    assert "STRUCTURAL_VERIFICATION_REQUIRED" in text
    assert result.manifest["member_ids"] == [member["id"] for member in payload["members"]]
    assert result.manifest["exclusion_count"] == 1
    assert "south-sill" not in text


def test_rectangle_fixture_renders_and_differs():
    bushel = render_dimensioned_plan(_load("bushel_dimensioned_plan.json"))
    rectangle = render_dimensioned_plan(_load("rectangle_platform.json"))
    assert rectangle.rendered is True
    text = _text(rectangle.pdf_bytes)
    assert "Rectangle platform" in text
    assert "1:50" in text
    assert "southwest corner" in text
    assert "metric" in text
    assert DISCLAIMER in text
    assert "south-sill" in text
    assert "north-sill" in text
    assert "sill" in text
    assert "front-edge" not in text
    assert "exclusion" not in text
    assert bushel.pdf_bytes != rectangle.pdf_bytes
    assert bushel.manifest["sheet_id"] != rectangle.manifest["sheet_id"]
    width, height = _page_points(rectangle.pdf_bytes)
    assert abs(width - (420 * 72 / 25.4)) < 0.2
    assert abs(height - (297 * 72 / 25.4)) < 0.2


def test_bushel_paper_size():
    result = render_dimensioned_plan(_load("bushel_dimensioned_plan.json"))
    width, height = _page_points(result.pdf_bytes)
    assert abs(width - 17 * 72) < 0.2
    assert abs(height - 11 * 72) < 0.2
    assert len(PdfReader(BytesIO(result.pdf_bytes)).pages) == 1


def test_manifest_matches_validation_and_pdf():
    payload = _load("rectangle_platform.json")
    validation = validate_plan_generation_request(payload)
    result = render_dimensioned_plan(payload)
    assert result.manifest["request_fingerprint"] == validation.request_fingerprint
    assert result.manifest["drawing_type"] == "dimensioned_plan"
    assert result.manifest["engine_version"] == "pge-2"
    assert result.manifest["validation_engine_version"] == "pge-1"
    assert result.manifest["title"] == payload["title"]
    assert result.manifest["origin"] == payload["origin"]
    assert result.manifest["scale"] == payload["scale"]
    assert result.manifest["measurement_system"] == "metric"
    assert result.manifest["paper"] == payload["paper"]
    assert result.manifest["disclaimer"] == DISCLAIMER
    assert result.manifest["pdf_sha256"] == result.to_dict()["pdf_sha256"]
    assert result.manifest["page_count"] == 1


def test_same_request_is_byte_stable():
    payload = _load("bushel_dimensioned_plan.json")
    first = render_dimensioned_plan(payload)
    second = render_dimensioned_plan(payload)
    assert first.pdf_bytes == second.pdf_bytes
    assert first.manifest == second.manifest


def test_unsupported_type_produces_no_pdf():
    payload = _load("rectangle_platform.json")
    payload["drawing_type"] = "stair_detail"
    result = render_dimensioned_plan(payload)
    assert result.rendered is False
    assert result.pdf_bytes is None
    assert result.manifest is None
    assert result.issues[0].code == CODE_UNSUPPORTED_DRAWING_TYPE


def test_invalid_request_produces_no_pdf():
    payload = _load("rectangle_platform.json")
    payload["title"] = " "
    result = render_dimensioned_plan(payload)
    assert result.rendered is False
    assert result.pdf_bytes is None
    assert result.issues[0].code == CODE_MISSING_TITLE


def test_renderer_source_has_no_case_constants():
    source = RENDERER.read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE:
        assert token not in source


def test_render_does_not_write_business_records():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-plan-render",
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
        render_dimensioned_plan(_load("rectangle_platform.json"))
        after = (
            Project.query.count(),
            PlanDocument.query.count(),
            Estimate.query.count(),
            ProjectWorkPackage.query.count(),
        )
        assert before == after
        db.session.remove()
        db.drop_all()

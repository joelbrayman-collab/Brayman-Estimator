"""Our-crew ICF wall reaches an ordinary estimate line only after confirmation.

No drawing, no PlanDocument, and no second ICF formula.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app import create_app, db
from app.models import Client, CostItem, EstimateLineItem, Project
from app.models.calculation_estimate_mapping import (
    CalculationQuantityReview,
    CalculationResultIntake,
)
from app.models.project import DRAWING_REQUIREMENT_NOT_REQUIRED, ProjectLocation
from app.models.project_work_package import DELIVERY_INTERNAL, DELIVERY_SUBCONTRACT
from app.plan_intelligence.models import PlanDocument
from app.services.estimate_builder import create_section
from app.services.estimates import create_estimate
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.project_setup import ICF_AVAILABLE_COPY, NOT_APPLICABLE_COPY, NOT_DERIVABLE_COPY
from app.services.project_work_package import confirm_package
from app.services.start_project_walk import resolve_start_project_walk
from app.services.work_structure import (
    ICF_WALL_CODE,
    ICF_WALL_ENGINE_ID,
    ensure_baseline_work_catalog,
)
from app.models.work_structure import WorkElementTemplate
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-icf-path",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _baseline(code):
    return WorkElementTemplate.query.filter_by(code=code, organization_id=None).one()


def _project(name):
    row = Client(name=f"{name} Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
        drawing_requirement=DRAWING_REQUIREMENT_NOT_REQUIRED,
    )
    db.session.add(project)
    db.session.flush()
    db.session.add(
        ProjectLocation(
            project_id=project.id,
            organization_id=project.organization_id,
            street="8 ICF Road",
            municipality="Ottawa",
            province_state="Ontario",
            country="Canada",
        )
    )
    db.session.commit()
    return project


def _action(html):
    marker = 'class="button" href="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


def _post_wall(client, estimate_id, version_id, action):
    return client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/wall-form-quantities",
        data={
            "manufacturer_id": "logix",
            "net_wall_area": "10",
            "corner_90": "0",
            "corner_45": "0",
            "labour_hours": "",
            "action": action,
        },
        follow_redirects=False,
    )


def test_our_crew_icf_reaches_an_estimate_line_only_after_confirmation(client, app):
    with app.app_context():
        project = _project("ICF Path")
        confirm_package(
            organization_id=project.organization_id,
            project_id=project.id,
            work_element_template_id=_baseline(ICF_WALL_CODE).id,
            delivery=DELIVERY_INTERNAL,
            actor="Path Contractor",
        )
        walk = resolve_start_project_walk(project.organization_id, project.id)
        assert walk.platform_engine_id == ICF_WALL_ENGINE_ID
        assert "ENGINE_ELIGIBLE" in walk.evidence
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="ICF-PATH-1",
            title="ICF Path Estimate",
            organization_id=project.organization_id,
        )
        project_id = project.id
        estimate_id = estimate.id
        version_id = estimate.current_version_id
        assert PlanDocument.query.count() == 0

    setup = client.get(f"/projects/{project_id}/setup")
    html = setup.get_data(as_text=True)
    assert ICF_AVAILABLE_COPY in html
    wall_form = _action(html)
    assert wall_form == (
        f"/estimates/{estimate_id}/versions/{version_id}/wall-form-quantities"
    )
    assert "plan" not in wall_form

    calculated = _post_wall(client, estimate_id, version_id, "calculate")
    assert calculated.status_code == 200
    assert b"These quantities are not on the estimate" in calculated.data
    with app.app_context():
        assert CalculationResultIntake.query.count() == 0
        assert EstimateLineItem.query.count() == 0
        assert PlanDocument.query.count() == 0

    reviewed = _post_wall(client, estimate_id, version_id, "review")
    assert reviewed.status_code == 302
    review_url = reviewed.location
    assert "/calculations/" in review_url
    with app.app_context():
        assert CalculationResultIntake.query.count() == 1
        assert EstimateLineItem.query.count() == 0
        intake = CalculationResultIntake.query.one()
        assert intake.engine_id == "icf_wall"
        assert intake.frozen_result["contract_version"] == "1"
        concrete = next(
            row for row in intake.reviews if row.quantity_code == "concrete"
        )
        assert concrete.status == "open"
        assert concrete.unit_code == "yd3"
        version = intake.estimate_version
        section = create_section(version, name="Wall")
        item = CostItem(
            organization_id=DEFAULT_ORGANIZATION_ID,
            code="ICF-CONC",
            name="ICF concrete",
            category="Material",
            unit="yd3",
            unit_cost=Decimal("200.00"),
            default_markup_percent=Decimal("0"),
            is_active=True,
        )
        db.session.add(item)
        db.session.commit()
        review_id = concrete.id
        section_id = section.id
        item_id = item.id
        quantity_text = concrete.quantity_text
        intake_id = intake.id
    opened = client.get(review_url)
    assert opened.status_code == 200
    assert b"Add to estimate" in opened.data
    with app.app_context():
        assert EstimateLineItem.query.count() == 0

    confirmed = client.post(
        f"/estimates/{estimate_id}/versions/{version_id}/calculations/quantities/{review_id}/confirm",
        data={
            "section_id": section_id,
            "target": f"cost_item:{item_id}",
            "confirmed_quantity": quantity_text,
            "intake_id": intake_id,
        },
        follow_redirects=False,
    )
    assert confirmed.status_code == 302
    with app.app_context():
        lines = EstimateLineItem.query.all()
        assert len(lines) == 1
        assert lines[0].cost_item_id == item_id
        confirmed_review = CalculationQuantityReview.query.get(review_id)
        assert confirmed_review.status == "confirmed"
        assert confirmed_review.estimate_line_item_id == lines[0].id
        assert confirmed_review.quantity_text == quantity_text
        open_rows = CalculationQuantityReview.query.filter_by(status="open").count()
        assert open_rows >= 1
        assert PlanDocument.query.count() == 0
    estimate_page = client.get(f"/estimates/{estimate_id}")
    assert estimate_page.status_code == 200
    assert b"ICF Path Estimate" in estimate_page.data
    version_page = client.get(f"/estimates/{estimate_id}/versions/{version_id}")
    assert version_page.status_code == 200
    assert b"ICF concrete" in version_page.data
    assert b"Wall" in version_page.data


def test_unbound_and_subcontract_work_do_not_open_the_icf_calculation(client, app):
    with app.app_context():
        cases = []
        for code in ("SITE", "FOUND", "STRUCT"):
            project = _project(f"{code} Path")
            confirm_package(
                organization_id=project.organization_id,
                project_id=project.id,
                work_element_template_id=_baseline(code).id,
                delivery=DELIVERY_INTERNAL,
                actor="Path Contractor",
            )
            cases.append((project.id, "ENGINE_REQUIREMENT_NOT_DERIVABLE", NOT_DERIVABLE_COPY))
        subcontract = _project("ICF Subcontract Path")
        confirm_package(
            organization_id=subcontract.organization_id,
            project_id=subcontract.id,
            work_element_template_id=_baseline(ICF_WALL_CODE).id,
            delivery=DELIVERY_SUBCONTRACT,
            actor="Path Contractor",
        )
        cases.append((subcontract.id, "ENGINE_NOT_APPLICABLE", NOT_APPLICABLE_COPY))

    for project_id, token, copy in cases:
        with app.app_context():
            result = resolve_start_project_walk(DEFAULT_ORGANIZATION_ID, project_id)
            assert token in result.evidence
            assert result.platform_engine_id is None
        html = client.get(f"/projects/{project_id}/setup").get_data(as_text=True)
        assert copy in html
        assert ICF_AVAILABLE_COPY not in html
        assert "wall-form-quantities" not in html

    route = (REPO_ROOT / "app/routes/calculation_mapping.py").read_text()
    assert "construction_model" not in route
    assert "compose_construction_sheet" not in route
    assert "PlanDocument" not in route

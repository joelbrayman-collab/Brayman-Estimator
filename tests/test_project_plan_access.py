"""Plans up front and "View project plan" everywhere (23 Oct 2026)."""
from __future__ import annotations

import io

import pytest

from app import create_app, db
from app.models import Client, Project
from app.plan_intelligence.models import PlanDocument
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user


@pytest.fixture()
def env(tmp_path):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "k",
                              "PLAN_STORAGE_ROOT": str(tmp_path), "UPLOAD_FOLDER": str(tmp_path)})
    context = application.app_context()
    context.push()
    db.create_all()
    ensure_default_organization()
    ensure_office_user()
    client_row = Client(name="Synthetic Client", organization_id=ORG)
    db.session.add(client_row)
    db.session.commit()
    http = application.test_client()
    login_office_user(http)
    yield http, client_row
    db.session.remove()
    db.drop_all()
    context.pop()


def _new_project(http, client_row, **extra):
    data = {"name": "Synthetic Plan Job", "client_id": str(client_row.id), "status": "Estimating",
            "project_type": "New Build", "pricing_posture": "Competitive", "execution_risk": "Normal",
            "schedule_condition": "Normal", "site_condition": "Normal", "estimate_stage": "Preliminary",
            "delivery_model": "Self-Perform"}
    data.update(extra)
    return http.post("/projects/new", data=data, content_type="multipart/form-data")


def test_new_project_form_offers_upload_plan_and_generate_drawings(env):
    http, _ = env
    html = http.get("/projects/new").get_data(as_text=True)
    assert 'enctype="multipart/form-data"' in html
    assert "Upload plan" in html and "Generate drawings" in html
    assert 'name="plan_file"' in html
    assert ">Internal</option>" in html


def test_generate_drawings_goes_to_the_drawing_tools(env):
    http, client_row = env
    response = _new_project(http, client_row, plan_start="generate")
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    assert response.status_code == 302, response.get_data(as_text=True)[:500]
    assert response.headers["Location"].endswith(f"/projects/{project.id}/drawings")
    assert project.drawing_requirement == "REQUIRED"


def test_upload_without_a_file_keeps_the_project_and_asks_for_the_pdf(env):
    http, client_row = env
    response = _new_project(http, client_row, plan_start="upload")
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    assert response.headers["Location"].endswith(f"/projects/{project.id}/plans/upload")


def test_later_keeps_the_old_path(env):
    http, client_row = env
    response = _new_project(http, client_row, plan_start="later")
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    assert "/setup" in response.headers["Location"] or str(project.id) in response.headers["Location"]


def test_view_project_plan_button_on_project_pages(env):
    http, client_row = env
    _new_project(http, client_row, plan_start="later")
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    page = http.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "data-view-project-plan" in page and "Add project plan" in page
    db.session.add(PlanDocument(project_id=project.id, original_filename="plan.pdf", stored_filename="x.pdf",
                                content_type="application/pdf", byte_size=10, sha256_hex="0" * 64))
    db.session.commit()
    page = http.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "View project plan" in page
    assert "branding/icons/view-project-plan-96.png" in page  # Joel's View project plan icon (23 Oct 2026)
    assert "data-view-project-plan" not in http.get("/projects/").get_data(as_text=True)  # list page: no single project

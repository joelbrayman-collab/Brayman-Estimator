"""Minimum Home briefing, desk print, and Supplier Estimate Request Help."""

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

import pytest
from pypdf import PdfReader

from app import create_app, db
from app.models import Client, Project
from app.models.project import OPERATING_STATE_CLOSED
from app.presentation import contractor_copy, help_content
from app.services import create_estimate
from app.services.desk_print import render_fact_sheet
from app.services.estimate_builder import add_manual_line, create_section
from app.services.home_planning import assemble_home_planning
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.schedule import create_schedule_item
from app.services.work_structure import add_project_element, ensure_baseline_work_catalog
from tests.auth_fixtures import ensure_office_user


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-v1-gaps",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_baseline_work_catalog()
        ensure_office_user()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _project(name, number):
    client_row = Client(name=f"{name} Client", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(client_row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=client_row.id,
        organization_id=DEFAULT_ORGANIZATION_ID,
        status="Estimating",
        project_number=number,
    )
    db.session.add(project)
    db.session.commit()
    return project


def test_home_empty_briefing(client):
    html = client.get("/").get_data(as_text=True)
    assert contractor_copy.HOME_TODAY_EMPTY in html
    assert contractor_copy.HOME_COMING_EMPTY in html
    assert contractor_copy.HOME_ATTENTION_OFFICE in html
    assert "payroll" not in html.lower()
    assert "cash engine" not in html.lower()


def test_home_shows_today_and_coming_days_and_hides_closed(client, app):
    office_today = date.today()
    with app.app_context():
        live = _project("Briefing Live Job", "P-LIVE")
        closed = _project("Briefing Closed Job", "P-CLOSED")
        live_element = add_project_element(
            project_id=live.id,
            display_name="Slab",
            organization_id=live.organization_id,
        )
        closed_element = add_project_element(
            project_id=closed.id,
            display_name="Roofing",
            organization_id=closed.organization_id,
        )
        create_schedule_item(
            organization_id=live.organization_id,
            project_id=live.id,
            project_work_element_id=live_element.id,
            scheduled_start=office_today,
            scheduled_end=office_today + timedelta(days=2),
        )
        create_schedule_item(
            organization_id=closed.organization_id,
            project_id=closed.id,
            project_work_element_id=closed_element.id,
            scheduled_start=office_today,
            scheduled_end=office_today,
        )
        closed.operating_state = OPERATING_STATE_CLOSED
        db.session.commit()
        view = assemble_home_planning(
            DEFAULT_ORGANIZATION_ID,
            today=office_today,
            year=office_today.year,
            month=office_today.month,
            selected_day=office_today.day,
        )
        assert view["briefing"]["today_work"]
        assert any("Briefing Live Job" in row["label"] for row in view["briefing"]["today_work"])
        assert view["briefing"]["coming"]
        assert all(
            "Briefing Closed Job" not in row["label"]
            for day in view["briefing"]["coming"]
            for row in day["work"]
        )
    html = client.get("/").get_data(as_text=True)
    assert "Briefing Live Job" in html
    assert "Briefing Closed Job" not in html
    assert contractor_copy.HOME_TODAY in html
    assert contractor_copy.HOME_COMING in html


def test_fact_sheet_uses_letter_margins_and_breaks_pages():
    lines = [f"Board {index} — 12 ft" for index in range(80)]
    payload = render_fact_sheet("Oak Street", [("Lines", lines)])
    reader = PdfReader(BytesIO(payload))
    assert len(reader.pages) >= 2
    box = reader.pages[0].mediabox
    assert float(box.width) == 612
    assert float(box.height) == 792
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Oak Street" in text
    assert "Board 0" in text
    assert "Board 79" in text
    assert "Page 1" in text
    assert "Page 2" in text
    source = open(render_fact_sheet.__code__.co_filename, encoding="utf-8").read()
    assert "0.75 * inch" in source
    assert "db." not in source
    assert "sqlalchemy" not in source.lower()


def test_project_and_estimate_print_use_the_screen_facts(client, app):
    with app.app_context():
        project = _project("Print Job", "P-21")
        project_id = project.id
        estimate = create_estimate(
            project_id=project.id,
            estimate_number="EST-PRINT-1",
            title="Print estimate",
        )
        version = estimate.current_version
        section = create_section(version, name="Work")
        add_manual_line(
            section,
            line_type="Custom",
            description="Helical pier",
            quantity=15,
            unit="ea",
            unit_cost=400,
            markup_percent=10,
        )
        version_id = version.id
        estimate_id = estimate.id
        db.session.commit()
    project_pdf = client.get(f"/projects/{project_id}/print.pdf")
    assert project_pdf.status_code == 200
    assert project_pdf.mimetype == "application/pdf"
    project_text = "\n".join(
        page.extract_text() or ""
        for page in PdfReader(BytesIO(project_pdf.data)).pages
    )
    assert "Print Job" in project_text
    assert "P-21" in project_text
    estimate_pdf = client.get(f"/estimates/{estimate_id}/versions/{version_id}/print.pdf")
    assert estimate_pdf.status_code == 200
    estimate_text = "\n".join(
        page.extract_text() or ""
        for page in PdfReader(BytesIO(estimate_pdf.data)).pages
    )
    assert "Helical pier" in estimate_text
    assert "15" in estimate_text
    assert "400" not in estimate_text
    hub = client.get(f"/projects/{project_id}").get_data(as_text=True)
    assert f'href="/projects/{project_id}/print.pdf"' in hub
    assert contractor_copy.PRINT_LABEL in hub
    version_html = client.get(
        f"/estimates/{estimate_id}/versions/{version_id}"
    ).get_data(as_text=True)
    assert "print.pdf" in version_html
    assert 'href="/login"' not in version_html


def test_supplier_estimate_request_help_topic():
    topic = help_content.office_topic("supplier_estimate_request")
    assert "this project only" in topic.what
    assert "Supplier Package" in topic.do
    assert "does not approve Brayman's cost" in topic.do
    assert "give it to Joel" in topic.next
    assert topic.surface == help_content.SURFACE_OFFICE
    blob = "\n".join((topic.what, topic.do, topic.next))
    assert "FG-" not in blob
    assert "schema" not in blob.lower()

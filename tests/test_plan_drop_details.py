"""Drag the plan in; Calibrayt reads the address, designer and plan version for the person to check (Joel, 15 Nov 2026).

Observations 3 and 5: the plan upload offered Browse only, and nothing was read from the plan. The server side is a
suggestion service: it returns what the title block clearly says, saves nothing, and leaves out what is not there.
Synthetic plans and names only.
"""

from __future__ import annotations

import io

import pytest
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas

from app import db
from app.models import Project
from app.plan_intelligence.models import DrawingRevision, PlanDocument
from app.plan_intelligence.title_block import read_plan_details
from tests.test_project_plan_access import _new_project, env  # noqa: F401 - env is a fixture


def _plan(lines, *, protected=False):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(letter))
    y = 560
    for line in lines:
        pdf.drawString(40, y, line)
        y -= 18
    pdf.save()
    data = buffer.getvalue()
    if protected:
        writer = PdfWriter(clone_from=PdfReader(io.BytesIO(data)))
        writer.encrypt(user_password="", owner_password="designer-secret", algorithm="AES-256")
        out = io.BytesIO()
        writer.write(out)
        data = out.getvalue()
    return data


TITLE_BLOCK = ["SYNTHETIC DESIGN STUDIO", "Main Floor Plan",
               "12620 County Road 15, Merrickville, ON K0G 1N0",
               "Designed by: Sample Designer Inc.", "Drawn by: A. Draftsperson", "Revision: C", "Date: 2026-11-02"]


def test_the_title_block_gives_address_designer_and_version():
    details = read_plan_details(_plan(TITLE_BLOCK))
    assert details["street"] == "12620 County Road 15"
    assert details["municipality"] == "Merrickville"
    assert details["province_state"] == "Ontario"
    assert details["postal_zip"] == "K0G 1N0"
    assert details["designer"] == "Sample Designer Inc."
    assert details["version"] == "C"


def test_a_protected_plan_is_read_too():
    details = read_plan_details(_plan(TITLE_BLOCK, protected=True))
    assert details["street"] == "12620 County Road 15" and details["postal_zip"] == "K0G 1N0"


def test_what_is_not_there_is_left_out_never_guessed():
    details = read_plan_details(_plan(["Foundation detail", "Scale 1:50", "Sheet A-2"]))
    assert all(value is None for value in details.values()), details


def test_a_password_plan_or_unreadable_file_gives_nothing_and_no_error():
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(_plan(TITLE_BLOCK))))
    writer.encrypt(user_password="needs-a-password", owner_password="o", algorithm="AES-256")
    out = io.BytesIO()
    writer.write(out)
    assert all(value is None for value in read_plan_details(out.getvalue()).values())
    assert all(value is None for value in read_plan_details(b"not a pdf at all").values())


def test_the_route_returns_suggestions_and_saves_nothing(env):
    http, _client = env
    before = (Project.query.count(), PlanDocument.query.count())
    response = http.post("/projects/plan-details", data={"plan_file": (io.BytesIO(_plan(TITLE_BLOCK)), "plan.pdf")},
                         content_type="multipart/form-data")
    body = response.get_json()
    assert response.status_code == 200 and body["ok"] and body["found"]
    assert body["details"]["designer"] == "Sample Designer Inc." and body["details"]["version"] == "C"
    assert (Project.query.count(), PlanDocument.query.count()) == before


@pytest.mark.parametrize("payload", [None, b"", b"plain text, not a plan"])
def test_the_route_refuses_a_missing_or_non_pdf_file(env, payload):
    http, _client = env
    data = {} if payload is None else {"plan_file": (io.BytesIO(payload), "plan.pdf")}
    response = http.post("/projects/plan-details", data=data, content_type="multipart/form-data")
    assert response.status_code == 400 and response.get_json()["ok"] is False


def test_the_checked_designer_and_version_are_kept_with_the_plan(env):
    http, client_row = env
    response = _new_project(http, client_row, plan_start="upload", plan_designer="Sample Designer Inc.",
                            plan_version="C", plan_file=(io.BytesIO(_plan(TITLE_BLOCK)), "plan.pdf"))
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    document = PlanDocument.query.filter_by(project_id=project.id).one()
    assert "Designer: Sample Designer Inc." in document.notes and "Plan version: C." in document.notes
    assert DrawingRevision.query.join(DrawingRevision.package).filter_by(project_id=project.id).one().label == "C"
    assert response.headers["Location"].endswith(f"/plans/{document.id}/uploaded")


def test_blank_boxes_record_nothing(env):
    http, client_row = env
    _new_project(http, client_row, plan_start="upload", plan_designer="", plan_version="",
                 plan_file=(io.BytesIO(_plan(TITLE_BLOCK)), "plan.pdf"))
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    document = PlanDocument.query.filter_by(project_id=project.id).one()
    assert "Designer" not in (document.notes or "") and "Plan version" not in (document.notes or "")


def test_the_screen_carries_the_drop_hooks_and_the_two_boxes(env):
    http, _client = env
    html = http.get("/projects/new").get_data(as_text=True)
    for hook in ('data-plan-drop-hint', 'data-plan-drop', 'name="plan_designer"', 'name="plan_version"',
                 '/projects/plan-details', 'addEventListener("drop"', 'name="plan_file"'):
        assert hook in html, hook
    assert 'enctype="multipart/form-data"' in html


def test_the_drawings_page_and_the_upload_page_take_a_dropped_plan(env):
    """Joel, 16 Nov 2026: a plan can be dropped where it is uploaded, not only on Set Up This Project."""
    http, client_row = env
    _new_project(http, client_row)
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    for url in (f"/projects/{project.id}/plans", f"/projects/{project.id}/plans/upload"):
        html = http.get(url).get_data(as_text=True)
        for hook in ("data-plan-drop-zone", "data-plan-drop-form", "data-plan-drop-status", "Drop the plan PDF anywhere on this page"):
            assert hook in html, (url, hook)


def test_after_an_upload_the_landing_says_so_and_offers_two_choices(env):
    """Joel, 16 Nov 2026: 'Your plan uploaded successfully. What do you want to do next? Estimate costs / Add more plans.'"""
    http, client_row = env
    _new_project(http, client_row)
    project = Project.query.filter_by(name="Synthetic Plan Job").one()
    pdf = _plan(["FOUNDATION PLAN scale: 1/4\"=1'-0\""])
    response = http.post(f"/projects/{project.id}/plans/upload",
                         data={"plan_file": (io.BytesIO(pdf), "landing-plan.pdf"), "notes": ""},
                         content_type="multipart/form-data")
    assert response.status_code == 302 and response.headers["Location"].endswith("/uploaded")
    page = http.get(response.headers["Location"]).get_data(as_text=True)
    for text in ("Your plan uploaded successfully", "What do you want to do next?", "Estimate costs", "Add more plans",
                 "landing-plan.pdf"):
        assert text in page, text
    assert 'data-plan-next="estimate"' in page and f"/projects/{project.id}/guided" in page
    assert 'data-plan-next="more"' in page and f"/projects/{project.id}/plans/upload" in page
    # The estimate choice goes somewhere real.
    assert http.get(f"/projects/{project.id}/guided", follow_redirects=True).status_code == 200

"""Synthetic data for Site Plans (tests/test_site_plans.py and tests/site_plans_page_server.py). 23 Oct 2026.

Everything is invented and labelled synthetic. Seeds, in the app context it is called in:

* Organization A (the default): the owner (office), Kevin (Field-only, booked on Harbour Lane through a schedule
  item) and Lee (Field-only, booked on nothing).
* Harbour Lane deck (synthetic): a customer with an email and phone, a priced estimate whose line carries an
  internal cost, an uploaded three-page plan PDF whose first two pages are in the Sheet Index (A-101, A-201), and
  a generated construction drawing set (D-1, D-2) that was not saved to Project Plans.
* Maple Court garage (synthetic): active, its own plan PDF, nobody from the crew booked on it.
* Organization B (Rival Builders B): its own office user, project and plan PDF, which nobody in A may see.

The plans are drawn with reportlab here; nothing is uploaded except through Project Plans' own upload service.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO

from app import db

OWNER = ("owner.siteplans@example.invalid", "Synthetic-owner-sp-1", "Olive Owner (synthetic)")
KEVIN = ("kevin.siteplans@example.invalid", "Synthetic-crew-sp-1", "Kevin Crew (synthetic)")
LEE = ("lee.siteplans@example.invalid", "Synthetic-crew-sp-2", "Lee Crew (synthetic)")
BEA = ("bea.siteplans@example.invalid", "Synthetic-orgb-sp-1", "Bea OrgB (synthetic)")
ORG_B = ("ORG-SPB", "Rival Builders B (synthetic)")
ASSIGNED = "Harbour Lane deck (synthetic)"
UNASSIGNED = "Maple Court garage (synthetic)"
ORG_B_PROJECT = "OrgB Hidden Larkspur (synthetic)"
ORG_B_PLAN = "orgb-larkspur-secret-plan.pdf"
CUSTOMER = ("Pat Synthetic Customer", "pat.customer@example.invalid", "613-555-0199")
INTERNAL_COST = "8765.43"
PLAN_NAME = "harbour-lane-deck-plan.pdf"
OTHER_PLAN = "maple-court-garage-plan.pdf"
SHEETS = (("A-101", "Deck framing plan"), ("A-201", "Sections and details"))
DRAWING_SHEETS = (("D-1", "Deck plan"), ("D-2", "Framing sections"))


def synthetic_pdf(title: str, pages: int, labels=()) -> bytes:
    """A small landscape plan set: a title block and a few lines on each page. Synthetic."""
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.pdfgen import canvas

    out = BytesIO()
    c = canvas.Canvas(out, pagesize=landscape(letter))
    w, h = landscape(letter)
    for n in range(1, pages + 1):
        c.setLineWidth(2)
        c.rect(36, 36, w - 72, h - 72)
        c.setLineWidth(1)
        for i in range(6):
            c.line(90 + i * 90, 120, 90 + i * 90, h - 160)
        c.line(90, 120, 540, 120)
        c.line(90, h - 160, 540, h - 160)
        label = labels[n - 1] if n <= len(labels) else (f"P-{n}", "General notes")
        c.setFont("Helvetica-Bold", 22)
        c.drawString(60, h - 80, f"{label[0]}  {label[1]}")
        c.setFont("Helvetica", 12)
        c.drawString(60, h - 104, f"{title} (synthetic, for testing only)  page {n} of {pages}")
        c.drawString(w - 300, 52, "Scale 1/4 in = 1 ft  (synthetic)")
        c.showPage()
    c.save()
    return out.getvalue()


def _user(email, password, name, organization_id=None):
    from app.services.organizations import DEFAULT_ORGANIZATION_ID
    from tests.auth_fixtures import ensure_office_user

    return ensure_office_user(email=email, password=password, display_name=name,
                              organization_id=organization_id or DEFAULT_ORGANIZATION_ID)


def _project(name, organization_id, customer=None):
    from app.models import Client, Project

    client = Client(name=customer[0] if customer else f"{name} customer", organization_id=organization_id)
    if customer:
        client.email = customer[1]
        client.phone = customer[2]
    db.session.add(client)
    db.session.flush()
    project = Project(name=name, client_id=client.id, organization_id=organization_id, status="Estimating",
                      address="12 Synthetic Road, Kemptville")
    db.session.add(project)
    db.session.commit()
    return project


def _upload(project, name, data):
    from werkzeug.datastructures import FileStorage

    from app.plan_intelligence.services import upload_plan_pdf

    return upload_plan_pdf(project, FileStorage(stream=BytesIO(data), filename=name, content_type="application/pdf"),
                           notes="Synthetic plan for Site Plans checks")


def _sheet_index(project, document):
    from app.plan_intelligence.models import PlanSheet, PlanSheetPage
    from app.plan_intelligence.packages import ensure_default_revision

    revision = ensure_default_revision(project)
    for page_index, (number, title) in enumerate(SHEETS):
        sheet = PlanSheet(drawing_revision_id=revision.id, number=number, title=title, discipline_code="A",
                          drawing_status="issued", review_status="final")
        db.session.add(sheet)
        db.session.flush()
        db.session.add(PlanSheetPage(sheet_id=sheet.id, plan_document_id=document.id, page_index=page_index))
    db.session.commit()


def _drawing_set(project, organization_id):
    """A generated drawing set, as Construction drawings stores it (write-once PDF bytes and sheet index)."""
    import hashlib

    from app.models.construction_drawing import ConstructionDrawingSet
    from app.services.project_construction_model import save_construction_model_revision
    from tests.fixtures.construction_model.linda_j1_takeoff_fixture import SOURCE_REFERENCE, model

    revision = save_construction_model_revision(organization_id=organization_id, project_id=project.id,
                                                content=model(), source_kind="source_document",
                                                source_reference=SOURCE_REFERENCE,
                                                actor_display_name="Synthetic office")
    revision = revision[0] if isinstance(revision, tuple) else revision
    pdf = synthetic_pdf("Harbour Lane construction drawings", len(DRAWING_SHEETS), DRAWING_SHEETS)
    record = ConstructionDrawingSet(
        organization_id=organization_id, project_id=project.id, construction_model_revision_id=revision.id,
        model_revision_number=revision.revision_number, model_content_sha256="0" * 64, product_facts_version=None,
        takeoff_fingerprint="f" * 64, drawing_revision=1, drawing_type="pool_deck", engine_version="synthetic",
        input_fingerprint="1" * 64, status="PRELIMINARY", sheet_count=len(DRAWING_SHEETS),
        sheet_index_json=json.dumps([{"number": n, "title": t} for n, t in DRAWING_SHEETS]),
        pdf_bytes=pdf, pdf_sha256=hashlib.sha256(pdf).hexdigest(), dxf_bytes=b"0\nEOF\n",
        dxf_sha256=hashlib.sha256(b"0\nEOF\n").hexdigest(), created_by="Synthetic office",
        created_at=datetime.utcnow())
    db.session.add(record)
    db.session.commit()
    return record


def _priced_estimate(project, organization_id):
    from app.models import CostItem
    from app.models.estimate import EstimateSection
    from app.services.estimate_builder import add_cost_item_line
    from app.services.estimates import create_estimate

    item = CostItem(organization_id=organization_id, code="SP-INT-1", name="Synthetic crew allowance",
                    category="Labour", unit="ls", unit_cost=Decimal(INTERNAL_COST),
                    default_markup_percent=Decimal("41.25"))
    db.session.add(item)
    db.session.commit()
    estimate = create_estimate(project_id=project.id, estimate_number="EST-SP-1", title="Deck (synthetic)",
                               organization_id=organization_id)
    version = estimate.current_version
    section = EstimateSection(estimate_version_id=version.id, name="Deck", sort_order=1, subtotal=Decimal("0"))
    db.session.add(section)
    db.session.commit()
    add_cost_item_line(section, cost_item_id=item.id, quantity=1, notes="Internal note (synthetic)",
                       organization_id=organization_id)
    return estimate, version


def seed() -> dict:
    """Seed everything above; returns the facts the checks need (ids, names, passwords)."""
    from app.models.organization import Organization
    from app.models.user import UserMembership
    from app.services.access_domains import set_field_only
    from app.services.instance_authority import set_instance_owner
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
    from app.services.schedule import assign_user, create_schedule_item
    from app.services.work_structure import add_project_element, ensure_baseline_work_catalog

    ensure_default_organization()
    ensure_baseline_work_catalog()
    owner = _user(*OWNER)
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=owner.id, organization_id=ORG).one().id, owner.id)
    kevin = _user(*KEVIN)
    lee = _user(*LEE)
    for crew in (kevin, lee):
        set_field_only(UserMembership.query.filter_by(user_id=crew.id, organization_id=ORG).one(), True, owner)

    assigned = _project(ASSIGNED, ORG, CUSTOMER)
    unassigned = _project(UNASSIGNED, ORG)
    element = add_project_element(project_id=assigned.id, display_name="Deck framing (synthetic)", organization_id=ORG)
    today = date.today()
    item = create_schedule_item(project_id=assigned.id, project_work_element_id=element.id, scheduled_start=today,
                                scheduled_end=today + timedelta(days=2), organization_id=ORG)
    assign_user(item.id, worker_user_id=kevin.id, organization_id=ORG)

    plan = _upload(assigned, PLAN_NAME, synthetic_pdf("Harbour Lane deck plan", 3, SHEETS))
    _sheet_index(assigned, plan)
    drawing_set = _drawing_set(assigned, ORG)
    estimate, version = _priced_estimate(assigned, ORG)
    other_plan = _upload(unassigned, OTHER_PLAN, synthetic_pdf("Maple Court garage plan", 1))

    db.session.add(Organization(id=ORG_B[0], legal_name=ORG_B[1], display_name=ORG_B[1], is_active=True))
    db.session.commit()
    bea = _user(*BEA, organization_id=ORG_B[0])
    org_b_project = _project(ORG_B_PROJECT, ORG_B[0])
    org_b_plan = _upload(org_b_project, ORG_B_PLAN, synthetic_pdf("OrgB secret plan", 1))
    db.session.commit()
    return {
        "owner": list(OWNER[:2]), "kevin": list(KEVIN[:2]), "lee": list(LEE[:2]), "bea": list(BEA[:2]),
        "owner_id": owner.id, "kevin_id": kevin.id, "bea_id": bea.id,
        "assigned_id": assigned.id, "assigned": ASSIGNED, "unassigned_id": unassigned.id, "unassigned": UNASSIGNED,
        "plan_id": plan.id, "plan_name": PLAN_NAME, "plan_pages": 3, "drawing_set_id": drawing_set.id,
        "other_plan_id": other_plan.id, "other_plan_name": OTHER_PLAN,
        "org_b_project_id": org_b_project.id, "org_b_project": ORG_B_PROJECT, "org_b_plan_id": org_b_plan.id,
        "org_b_plan_name": ORG_B_PLAN, "estimate_id": estimate.id, "version_id": version.id,
        "customer": list(CUSTOMER), "internal_cost": INTERNAL_COST, "schedule_item_id": item.id,
        "sheets": [list(s) for s in SHEETS], "drawing_sheets": [list(s) for s in DRAWING_SHEETS],
    }

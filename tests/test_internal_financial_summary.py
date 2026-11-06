"""Internal Project Financial Summary, employee cost profiles and the estimate crew (Joel, 2 Nov 2026).

* Every employee has a cost profile (Loaded Labour Rate); one without cannot be put on an estimate crew, and the
  Employees area says "Cost profile required". Sign-in and time entry are not touched.
* The summary is produced for every estimate from the working figures: one row per work package, revenue equal to the
  estimate's selling price, materials / labour / subcontract pages (subcontracts only when there are any), long tables
  continued, "Page X of N". Real labour cost = hours x the crew's loaded rates; with no crew it says so and never
  invents a cost.
* Approving the estimate freezes the summary's figures and the crew's rates in the approval record and files the PDF
  in the project's Documents.
* Only the owner or a System Administrator (who may see wages) opens it or assigns the crew; office staff, field crew,
  suppliers and customers never see it.

Synthetic data only.
"""

from __future__ import annotations

import re
from decimal import Decimal as D
from io import BytesIO

import pytest
from pypdf import PdfReader

from app import create_app, db
from app.models import EstimateVersion
from app.models.documents import Document, DocumentLink
from app.models.estimate_approval import EstimateApproval
from app.models.person import EstimateCrewMember, OrganizationPerson, OrganizationPersonCostProfile
from app.models.pricing_engine import LABOUR_AT_RATE_MATERIAL_MARGIN
from app.services import guided_estimating as G
from app.services import internal_financial_summary as IFS
from app.services.estimate_crew import CREW_NOT_ASSIGNED, EstimateCrewError, set_crew
from app.services.instance_authority import set_instance_owner
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.guided_support import Driver, seed_company
from tests.test_guided_tasks import _priced_job, _template

OWNER = ("owner.ifs@example.invalid", "owner-ifs-password", "Owner Synthetic")
STAFF = ("staff.ifs@example.invalid", "staff-ifs-password", "Office Staff Synthetic")
CREW = ("crew.ifs@example.invalid", "crew-ifs-password", "Field Crew Synthetic")
WORKER_A = {"full_name": "Worker A (synthetic)", "address": "1 Synthetic Rd", "mobile_number": "555-0101",
            "email_address": "worker.a@example.invalid", "hourly_wage": "36", "truck_monthly": "1100",
            "fuel_monthly": "700", "tool_allowance_annual": "1000", "rrsp_percent": "2"}
WORKER_B = {"full_name": "Worker B (synthetic)", "address": "2 Synthetic Rd", "mobile_number": "555-0102",
            "email_address": "worker.b@example.invalid", "hourly_wage": "26"}


def _membership(user):
    from app.models.user import UserMembership

    return UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()


def _brayman_pricing():
    from app.services.labour_engine import promote_direct_labour_cost_rate
    from app.services.pricing_engine import approve_pricing_policy, create_pricing_policy, set_default_pricing_policy

    promote_direct_labour_cost_rate("80", approved_by="Joel Brayman", reason="Brayman $80 (synthetic seed)",
                                    organization_id=ORG)
    policy = create_pricing_policy(policy_code="ORG-001-LABOUR-80-MATERIALS-15", method=LABOUR_AT_RATE_MATERIAL_MARGIN,
                                   actor="Joel Brayman", target_gross_margin=D("0.15"), tax_jurisdiction="CA-ON",
                                   tax_percent=D("13"))
    approve_pricing_policy(policy.id, actor="Joel Brayman", organization_id=ORG)
    set_default_pricing_policy(policy.id, actor="Joel Brayman", organization_id=ORG)
    db.session.commit()


@pytest.fixture()
def env():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "k"})
    context = application.app_context()
    context.push()
    db.create_all()
    ensure_default_organization()
    seed_company()
    _brayman_pricing()
    owner = ensure_office_user(email=OWNER[0], password=OWNER[1], display_name=OWNER[2])
    set_instance_owner(ORG, _membership(owner).id, owner.id)
    staff = ensure_office_user(email=STAFF[0], password=STAFF[1], display_name=STAFF[2])
    crew = ensure_office_user(email=CREW[0], password=CREW[1], display_name=CREW[2])
    from app.services.access_domains import set_field_only

    set_field_only(_membership(crew), True, owner)
    db.session.commit()
    clients = {}
    for key, (email, password, _name) in (("owner", OWNER), ("staff", STAFF), ("crew", CREW)):
        driver = Driver(application.test_client())
        login_office_user(driver.http, email=email, password=password)  # the fresh client: no cached sign-in
        clients[key] = driver
    yield application, clients, {"owner": owner, "staff": staff, "crew": crew}
    db.session.remove()
    db.drop_all()
    context.pop()


def _add_employee(d, values):
    d.post("/settings/people/employees/new", data=dict(values, action="save"))
    return OrganizationPerson.query.filter_by(full_name=values["full_name"]).one()


def _job_with_labour(d):
    project, guided = _priced_job(d, "Synthetic siding summary")
    row = guided.top_stages[0]
    d.post(f"/projects/{project.id}/guided/stages/{row.id}/add_cost",
           data={"kind": "labour", "description": "Install siding (synthetic)", "quantity": "20"})
    d.post(f"/projects/{project.id}/guided/stages/{row.id}/add_cost",
           data={"kind": "equipment", "description": "Staging (synthetic)", "quantity": "1", "unit": "ls",
                 "unit_cost": "100"})
    d.post(f"/projects/{project.id}/guided/stages/{row.id}/routing")
    d.post(f"/projects/{project.id}/guided/stages/{row.id}/complete_next")
    db.session.expire_all()
    return project, G.get_guided(ORG, project.id)


def _pdf_text(payload: bytes):
    reader = PdfReader(BytesIO(payload))
    return [page.extract_text() for page in reader.pages]


def _approve_form(page):
    assert "data-approve-estimate-form" in page, re.sub(r"<[^>]+>", " ", page.split("data-review-decisions", 1)[-1])[:800]
    form = page.split("data-approve-estimate-form", 1)[1].split("</form>", 1)[0]
    return dict(re.findall(r'name="(version_id|expected_total|csrf_token)" value="([^"]*)"', form))


# ================================================================================================ employees
def test_the_owner_enters_employees_and_the_loaded_rates_reproduce_the_verified_cases(env):
    _app, c, _users = env
    page = c["owner"].get("/settings/people/employees")
    assert "Employees" in page and "Add an employee" in page
    a = _add_employee(c["owner"], WORKER_A)
    b = _add_employee(c["owner"], WORKER_B)
    profile_a = OrganizationPersonCostProfile.query.filter_by(person_id=a.id).one()
    profile_b = OrganizationPersonCostProfile.query.filter_by(person_id=b.id).one()
    assert (profile_a.annual_cost, profile_a.loaded_rate) == (D("107525.29"), D("55.77"))
    assert (profile_b.annual_cost, profile_b.loaded_rate) == (D("60243.46"), D("31.25"))
    assert profile_a.wsib_rate_per_100 == D("3.550") and not profile_a.wsib_is_override
    detail = c["owner"].get(f"/settings/people/employees/{a.id}")
    for text in ("$107,525.29", "$55.77", "Per working hour", "Per paid hour", "CPP2 (employer)", "$4,230.45"):
        assert text in detail, text
    # Calculate shows the breakdown without saving.
    preview = c["owner"].post(f"/settings/people/employees/{b.id}", data=dict(WORKER_B, action="calculate",
                                                                              health_premium_monthly="250"), status=200)
    assert "Calculated (not saved yet)" in preview.get_data(as_text=True)
    assert OrganizationPersonCostProfile.query.filter_by(person_id=b.id).count() == 1


def test_a_change_is_a_new_profile_and_the_history_is_kept(env):
    from app.models.person import OrganizationPersonWageEvent

    _app, c, _users = env
    b = _add_employee(c["owner"], WORKER_B)
    c["owner"].post(f"/settings/people/employees/{b.id}", data=dict(WORKER_B, hourly_wage="27", action="save",
                                                                   reason="Raise (synthetic)"))
    rows = OrganizationPersonCostProfile.query.filter_by(person_id=b.id).order_by(OrganizationPersonCostProfile.id).all()
    assert [r.hourly_wage for r in rows] == [D("26.00"), D("27.00")]
    assert db.session.get(OrganizationPerson, b.id).hourly_wage == D("27.00")
    event = OrganizationPersonWageEvent.query.filter_by(person_id=b.id).one()
    assert (event.previous_hourly_wage, event.hourly_wage) == (D("26.00"), D("27.00"))
    with pytest.raises(ValueError, match="append-only"):
        rows[0].loaded_rate = D("1")
        db.session.commit()
    db.session.rollback()


def test_employees_and_wages_are_for_the_owner_or_a_system_administrator_only(env):
    _app, c, _users = env
    b = _add_employee(c["owner"], WORKER_B)
    c["staff"].get("/settings/people/employees", status=403)
    c["staff"].get(f"/settings/people/employees/{b.id}", status=403)
    c["staff"].post(f"/settings/people/employees/{b.id}", data=dict(WORKER_B, action="save"), status=403)
    response = c["crew"].http.get("/settings/people/employees")
    assert response.status_code == 302 and "/field" in response.headers["Location"]


def test_an_employee_without_a_cost_profile_is_flagged_and_cannot_be_on_a_crew(env):
    from app.services.organization_people import create_person, update_person

    _app, c, users = env
    _project, guided = _job_with_labour(c["owner"])
    legacy = create_person(organization_id=ORG, actor=users["owner"], full_name="Worker C (synthetic)",
                           address="3 Synthetic Rd", mobile_number="555-0103", email_address="c@example.invalid",
                           hourly_wage="30")
    page = c["owner"].get("/settings/people/employees")
    assert 'data-cost-profile="required"' in page and "Cost profile required" in page
    assert 'data-cost-profile-missing="1"' in page
    assert "need" in c["owner"].get("/settings/people") and "data-employees-link" in c["owner"].get("/settings/people")
    with pytest.raises(EstimateCrewError, match="no complete cost profile"):
        set_crew(guided.estimate, organization_id=ORG, person_ids=[legacy.id], actor="Owner Synthetic")
    c["owner"].post(f"/projects/{guided.project_id}/guided/crew", data={"person_id": [str(legacy.id)]})
    assert any("no complete cost profile" in m for m in c["owner"].flashes())
    assert EstimateCrewMember.query.count() == 0
    # A wage changed outside the profile (the CLI) makes the profile incomplete again until it is saved.
    b = _add_employee(c["owner"], WORKER_B)
    update_person(organization_id=ORG, person_id=b.id, actor=users["owner"], hourly_wage="28")
    with pytest.raises(EstimateCrewError):
        set_crew(guided.estimate, organization_id=ORG, person_ids=[b.id], actor="Owner Synthetic")


# ================================================================================================ the summary
def test_the_summary_is_built_from_the_working_estimate_and_says_when_no_crew_is_assigned(env):
    _app, c, _users = env
    project, guided = _job_with_labour(c["owner"])
    version = G.current_version(guided)
    data = IFS.build_data(version)
    totals = IFS.totals(data)
    from app.services.estimate_economics import economics

    e = economics(version)
    assert e["pricing_method"] == LABOUR_AT_RATE_MATERIAL_MARGIN
    assert len(data["packages"]) == 1 and data["packages"][0]["name"] == guided.top_stages[0].display_name
    assert totals["revenue"] == e["selling_price"]  # the packages add up to the estimate's selling price
    assert totals["materials"] == D("1500.00") and totals["materials_with_margin"] == D("1764.71")
    assert totals["hours"] == D("20.00") and totals["labour_value"] == D("1600.00")
    assert totals["equipment"] == D("100.00")
    assert totals["labour_cost"] is None and totals["cost"] is None and totals["profit"] is None  # never invented
    assert data["crew_problem"] == CREW_NOT_ASSIGNED
    pages = _pdf_text(IFS.render_pdf(data))
    assert "Internal Project Financial Summary" in pages[0] and "By work package" in pages[0]
    assert "Crew not assigned — real labour cost not available" in pages[0]
    assert "How we price it internally" in pages[0] and "Contractor approval" in pages[0]
    assert any("MATERIALS – PROJECT SUMMARY" in p for p in pages)
    assert any("LABOUR – PROJECT SUMMARY" in p for p in pages)
    assert not any("SUBCONTRACTORS – PROJECT SUMMARY" in p for p in pages)  # no subcontracts on this job
    assert all(f"Page {i} of {len(pages)}" in p for i, p in enumerate(pages, 1))
    # Opened from Review This Estimate by the owner.
    review = c["owner"].get(f"/projects/{project.id}/guided/pricing")
    assert "data-financial-summary-pdf" in review and "data-crew-not-assigned" in review
    response = c["owner"].http.get(f"/projects/{project.id}/guided/internal-financial-summary.pdf")
    assert response.status_code == 200 and response.mimetype == "application/pdf"
    assert response.headers["Cache-Control"] == "no-store"


def test_with_a_crew_the_real_labour_cost_is_hours_times_the_loaded_rates(env):
    _app, c, _users = env
    project, guided = _job_with_labour(c["owner"])
    a = _add_employee(c["owner"], WORKER_A)
    b = _add_employee(c["owner"], WORKER_B)
    c["owner"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id), str(b.id)]})
    assert [r.share for r in EstimateCrewMember.query.order_by(EstimateCrewMember.id).all()] == [D("1"), D("1")]
    data = IFS.build_data(G.current_version(guided))
    totals = IFS.totals(data)
    # 20 h split equally: 10 h x $55.77 + 10 h x $31.25 = $870.20 (blended $43.51/h)
    assert totals["labour_cost"] == D("870.20") and [s["cost"] for s in totals["crew_split"]] == [D("557.70"), D("312.50")]
    assert totals["cost"] == D("1500.00") + D("870.20") + D("100.00")
    assert totals["profit"] == totals["revenue"] - totals["cost"]
    text = "\n".join(_pdf_text(IFS.render_pdf(data)))
    assert "Worker A (synthetic), 10.00 h at $55.77 loaded" in text and "Labour margin over loaded cost" in text
    # Changing the crew keeps who was on it before.
    c["owner"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id)], f"share_{a.id}": "2"})
    assert EstimateCrewMember.query.filter(EstimateCrewMember.removed_at.isnot(None)).count() == 2
    assert IFS.totals(IFS.build_data(G.current_version(guided)))["labour_cost"] == D("1115.40")


def test_subcontracts_get_their_page_and_long_tables_continue():
    data = {
        "project": {"short": "SYN-1", "name": "Synthetic long job", "revision": "EST-1 · v1", "date": "November 2, 2026",
                    "subtitle": "", "revenue_status": "", "company": "Synthetic Builder Inc.", "address": "1 Test Rd"},
        "settings": {"pricing_method": LABOUR_AT_RATE_MATERIAL_MARGIN, "labour_rate": "80", "material_margin": "0.15",
                     "hst": "0.13", "subcontract_markup": "0"},
        "crew": [{"name": "Worker A", "loaded_rate": "55.77", "share": "1"}],
        "packages": [{"name": f"Package {n}",
                      "revenue": [{"label": f"Package {n}", "amount": "20000.00"}],
                      "materials": [{"item": f"Material {n}-{i}", "takeoff": "10 ea", "qty": "10", "unit": "ea",
                                     "price": "10.00", "supplier": "Synthetic Supply", "cost": "100.00"}
                                    for i in range(30)],
                      "labour": [{"ref": str(n), "activity": "Install", "qty": "", "unit": "", "rate": "entered",
                                  "hours": "10.00", "value": "800.00"}],
                      "equipment": [],
                      "subcontracts": ([{"trade": f"Package {n}", "company": "Synthetic Electric", "scope": "Wiring",
                                         "cost": "5200.00", "ref": "Q-1"}] if n == 1 else [])}
                     for n in range(1, 4)],
    }
    pages = _pdf_text(IFS.render_pdf(data))
    assert any("MATERIALS – PROJECT SUMMARY (continued)" in p for p in pages)
    assert any("SUBCONTRACTORS – PROJECT SUMMARY" in p for p in pages)
    assert all(f"Page {i} of {len(pages)}" in p for i, p in enumerate(pages, 1))
    totals = IFS.totals(data)
    assert totals["subcontracts"] == D("5200.00") and totals["revenue"] == D("60000.00")


def test_a_manual_estimate_maps_its_sections_and_line_kinds(env):
    from app.models import Client, Project
    from app.services.estimate_builder import add_manual_line, create_section
    from app.services.estimates import create_estimate

    client = Client(name="Synthetic Client", organization_id=ORG)
    db.session.add(client)
    db.session.flush()
    project = Project(name="Manual synthetic", client_id=client.id, organization_id=ORG, status="Estimating")
    db.session.add(project)
    db.session.commit()
    estimate = create_estimate(project_id=project.id, estimate_number="EST-MAN-1", title="Manual")
    version = estimate.current_version
    walls = create_section(version, name="Walls")
    add_manual_line(walls, line_type="Custom", description="Studs", quantity=100, unit="ea", unit_cost=D("7.25"))
    elec = create_section(version, name="Electrical")
    add_manual_line(elec, line_type="Custom", description="Electrical (synthetic)", quantity=1, unit="ls",
                    unit_cost=D("5200"), code="GE-SUBCONTRACT")
    db.session.commit()
    data = IFS.build_data(version)
    assert [p["name"] for p in data["packages"]] == ["Walls", "Electrical"]
    assert data["packages"][0]["materials"][0]["cost"] == "725.00"
    assert data["packages"][1]["subcontracts"][0]["cost"] == "5200.00"
    assert any("SUBCONTRACTORS – PROJECT SUMMARY" in p for p in _pdf_text(IFS.render_pdf(data)))


# ================================================================================================ approval
def test_approval_freezes_the_figures_and_files_the_pdf_in_the_project_documents(env):
    _app, c, users = env
    _template()
    project, guided = _job_with_labour(c["owner"])
    a = _add_employee(c["owner"], WORKER_A)
    b = _add_employee(c["owner"], WORKER_B)
    c["owner"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(a.id), str(b.id)]})
    values = _approve_form(c["owner"].get(f"/projects/{project.id}/guided/pricing"))
    c["owner"].post(f"/projects/{project.id}/guided/approve", data=values)
    db.session.expire_all()
    version = db.session.get(EstimateVersion, int(values["version_id"]))
    approval = EstimateApproval.query.filter_by(estimate_version_id=version.id).one()
    frozen = approval.summary["internal_financial_summary"]
    assert [m["loaded_rate"] for m in frozen["crew"]] == ["55.77", "31.25"]
    assert IFS.totals(frozen)["revenue"] == version.pricing_snapshot.pre_tax_selling_price
    from app.services.estimate_approval import verify

    assert verify(version)["matches"]  # the Gate 1 fingerprint is unchanged by the frozen internal figures
    doc = (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
           .filter(Document.document_type == "INTERNAL_FINANCIAL_SUMMARY", DocumentLink.project_id == project.id,
                   DocumentLink.record_kind == "ESTIMATE_VERSION", DocumentLink.record_id == version.id).one())
    assert doc.sensitivity == "EMPLOYEE_COST"  # carries the crew's loaded rates: economics + employee cost only
    # A later wage change does not move the approved summary.
    c["owner"].post(f"/settings/people/employees/{a.id}", data=dict(WORKER_A, hourly_wage="40", action="save"))
    data = IFS.data_for(version)
    assert [m["loaded_rate"] for m in data["crew"]] == ["55.77", "31.25"]
    text = "\n".join(_pdf_text(IFS.render_pdf(data)))
    assert "Name: Owner Synthetic" in text and "Approved in CalibraytAI" in text
    # Filing is idempotent.
    assert IFS.file_approved_summary(version, approval).id == doc.id
    page = c["owner"].get(f"/projects/{project.id}/guided/pricing")
    assert "The approved figures are frozen with the approval." in page and "data-save-crew" not in page


def test_approval_without_a_crew_files_a_financial_document_with_no_invented_cost(env):
    _app, c, _users = env
    _template()
    project, guided = _job_with_labour(c["owner"])
    values = _approve_form(c["owner"].get(f"/projects/{project.id}/guided/pricing"))
    c["owner"].post(f"/projects/{project.id}/guided/approve", data=values)
    assert not any("Not approved" in m or "Nothing" in m for m in c["owner"].flashes()), c["owner"].flashes()
    db.session.expire_all()
    approval = EstimateApproval.query.one()
    frozen = approval.summary["internal_financial_summary"]
    assert frozen["crew"] == [] and frozen["crew_problem"] == CREW_NOT_ASSIGNED
    doc = Document.query.filter_by(document_type="INTERNAL_FINANCIAL_SUMMARY").one()
    assert doc.sensitivity == "ECONOMICS"


# ================================================================================================ who sees it
def test_office_staff_field_crew_and_customers_never_see_the_summary(env):
    _app, c, _users = env
    _template()
    project, guided = _job_with_labour(c["owner"])
    b = _add_employee(c["owner"], WORKER_B)
    c["owner"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(b.id)]})
    staff_review = c["staff"].get(f"/projects/{project.id}/guided/pricing")
    assert "data-financial-summary" not in staff_review and "loaded" not in staff_review.lower()
    c["staff"].get(f"/projects/{project.id}/guided/internal-financial-summary.pdf", status=403)
    c["staff"].post(f"/projects/{project.id}/guided/crew", data={"person_id": [str(b.id)]}, status=403)
    response = c["crew"].http.get(f"/projects/{project.id}/guided/internal-financial-summary.pdf")
    assert response.status_code == 302 and "/field" in response.headers["Location"]
    # The customer's proposal never carries it.
    values = _approve_form(c["owner"].get(f"/projects/{project.id}/guided/pricing"))
    response = c["owner"].post(f"/projects/{project.id}/guided/approve", data=values)
    proposal_page = c["owner"].get(response.headers["Location"])
    assert "Internal Project Financial Summary" not in proposal_page and "$31.25" not in proposal_page
    # The filed document (with the crew's rates) is not in office staff's document list.
    library = c["staff"].get(f"/projects/{project.id}/documents")
    assert "Internal Project Financial Summary" not in library
    owner_library = c["owner"].get(f"/projects/{project.id}/documents")
    assert "Internal Project Financial Summary" in owner_library

"""Joel's three approved wizard decisions (24 Oct 2026) — automated acceptance. Synthetic data only.

1. Project Lead: optional, one of the company's authorized people (office staff or crew; never deactivated, never
   another organization); existing projects unassigned; shown on the Project Hub, the Company Calendar and the
   Start a New Project / Manage a Project wizards; separate from crew assignments and appointment assignees; it
   grants NO permission (a Field-only lead gains no office access, an office lead gains nothing extra).
2. Supplier pickup and delivery: arranged in the store's own system. CalibraytAI keeps the quotation, the order,
   the requested method and the real order status, and never shows fulfilment complete without a recorded
   "marked delivered" (date and side).
3. Product availability: only from supplier-provided data, otherwise exactly "Availability not confirmed"; never
   a quantity, never implied stock.
"""

from __future__ import annotations

import re
from datetime import timedelta

import pytest

from app import db
from app.models import Project
from app.models.organization import Organization
from app.models.user import User, UserMembership
from app.presentation.availability import AVAILABILITY_NOT_CONFIRMED, availability_confirmed, availability_label
from app.services import guided_estimating as G
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.project_lead import ProjectLeadError, lead_choices, lead_name, set_project_lead
from tests.auth_fixtures import ensure_office_user
from tests.guided_support import client
from tests.test_guided_estimating import (  # noqa: F401
    BEN,
    KEVIN,
    _build_new_home,
    _cost_new_home,
    _field_only_kevin,
    _login,
    _other_company,
    env,
)
from tests.test_wizards import (  # noqa: F401
    _accept_and_build,
    _create_from_wizard,
    _events,
    _office_login,
    _run,
    _sstate,
    _start,
    _state,
    _step,
    _supplier_login,
    hub,
    pro_desk,
)

STAFF = ("sam.office@example.invalid", "sam-office-password", "Sam Office (synthetic)")
GONE = ("gone.person@example.invalid", "gone-person-password", "Gone Person (synthetic)")


SIGN = {"sign_consent": "yes", "signer_name": "Test Signer"}  # supplier Native Signing (FG-041): every order, confirmation and change asked on screen is signed


def _people(application, ben):
    """Ben (owner), Kevin (Field-only crew), Sam (office staff, not the owner), a deactivated person and another
    company's owner."""
    kevin_driver = _field_only_kevin(application, ben)
    kevin = User.query.filter_by(email=KEVIN[0]).one()
    sam = ensure_office_user(email=STAFF[0], password=STAFF[1], display_name=STAFF[2])
    gone = ensure_office_user(email=GONE[0], password=GONE[1], display_name=GONE[2])
    UserMembership.query.filter_by(user_id=gone.id, organization_id=ORG).one().is_active = False
    db.session.commit()
    _other_company(application)
    other = User.query.filter_by(email="other.guided@example.invalid").one()
    return {"kevin": kevin, "kevin_driver": kevin_driver, "sam": sam, "gone": gone, "other": other}


def _access(user, project_id):
    """Everything an access check in the platform reads for this person (Project Lead must change none of it)."""
    from app.services import access_domains as A
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    visible = A.field_visible_project_ids(user, ORG)
    return {
        "domains": {k: A.membership_has_access_domain(user, ORG, k) for k in sorted(A.RECOGNIZED_STORED_DOMAINS)},
        "field_only": A.user_is_field_only(user, ORG),
        "scheduling": A.has_office_scheduling_authority(user, ORG),
        "financial": A.has_office_financial_access(user, ORG),
        "owner": is_instance_owner(user, ORG),
        "sysadmin": is_system_administrator(user, ORG),
        "field_projects": None if visible is None else sorted(visible),
        "sees_project": None if visible is None else project_id in visible,
    }


# ====================================================================================== 1 Project Lead
def test_project_lead_choices_are_this_companys_active_people_only(env):
    application, d, ben = env
    p = _people(application, ben)
    choices = {c["id"]: c["label"] for c in lead_choices(ORG)}
    assert ben.id in choices and p["sam"].id in choices
    assert choices[p["kevin"].id].endswith("(Field crew)")       # crew members are authorized personnel
    assert p["gone"].id not in choices                           # deactivated: never offered
    assert p["other"].id not in choices                          # another organization: never offered
    project, _ = d.new_project("Lead Choices Home (synthetic)", "NEW_HOME", "GENERAL_CONTRACTOR")
    for bad in (p["gone"].id, p["other"].id, 999999):
        with pytest.raises(ProjectLeadError):
            set_project_lead(organization_id=ORG, project_id=project.id, user_id=bad)
    db.session.expire_all()
    assert db.session.get(Project, project.id).project_lead_user_id is None
    # Another company cannot set a lead on this company's project, even with this company's person.
    with pytest.raises(ProjectLeadError):
        set_project_lead(organization_id="ORG-GUIDED-OTHER", project_id=project.id, user_id=ben.id)
    # A lead who later leaves is named as such (the record is preserved, not silently cleared).
    assert set_project_lead(organization_id=ORG, project_id=project.id, user_id=p["sam"].id) is True
    UserMembership.query.filter_by(user_id=p["sam"].id, organization_id=ORG).one().is_active = False
    db.session.commit()
    assert lead_name(db.session.get(Project, project.id)) == "Sam Office (synthetic) (no longer active)"


def test_project_lead_on_the_new_project_form_the_hub_and_its_own_page(env):
    application, d, ben = env
    p = _people(application, ben)
    existing, _ = d.new_project("Existing Home (synthetic)", "NEW_HOME", "GENERAL_CONTRACTOR")
    assert existing.project_lead_user_id is None                 # default unassigned
    hub = d.get(f"/projects/{existing.id}")
    assert 'data-hub-project-lead' in hub and re.search(r'data-project-lead>Unassigned<', hub)
    form = d.get("/projects/new")
    assert 'name="project_lead_user_id"' in form and STAFF[2] in form and GONE[2] not in form
    # The New Project form sets it.
    from tests.guided_support import COMMERCIAL

    d.post("/projects/new", data=dict(COMMERCIAL, name="Form Lead Home (synthetic)", client_id=client().id,
                                      project_lead_user_id=str(p["sam"].id)))
    made = Project.query.filter_by(organization_id=ORG, name="Form Lead Home (synthetic)").one()
    assert made.project_lead_user_id == p["sam"].id
    assert f"data-project-lead>{STAFF[2]}<" in d.get(f"/projects/{made.id}")
    # Another company's person is refused by the form and nothing is created.
    r = d.post("/projects/new", data=dict(COMMERCIAL, name="Refused Home (synthetic)", client_id=client().id,
                                          project_lead_user_id=str(p["other"].id)), status=200)
    assert Project.query.filter_by(organization_id=ORG, name="Refused Home (synthetic)").count() == 0
    # The Project Lead page: change it, refuse a deactivated person, clear it.
    page = d.get(f"/projects/{existing.id}/lead")
    assert KEVIN[2] in page and GONE[2] not in page and "gives no access" in page
    d.post(f"/projects/{existing.id}/lead", data={"project_lead_user_id": str(p["kevin"].id)})
    db.session.expire_all()
    assert db.session.get(Project, existing.id).project_lead_user_id == p["kevin"].id
    d.post(f"/projects/{existing.id}/lead", data={"project_lead_user_id": str(p["gone"].id)}, status=400)
    db.session.expire_all()
    assert db.session.get(Project, existing.id).project_lead_user_id == p["kevin"].id
    d.post(f"/projects/{existing.id}/lead", data={"project_lead_user_id": ""})
    db.session.expire_all()
    assert db.session.get(Project, existing.id).project_lead_user_id is None
    # Another company cannot open or change it.
    other = _login(application, ("other.guided@example.invalid", "other-guided-password"))
    other.get(f"/projects/{existing.id}/lead", status=404)
    other.post(f"/projects/{existing.id}/lead", data={"project_lead_user_id": ""}, status=404)
    _ = r


def test_project_lead_grants_no_permission_to_field_or_office_people(env):
    application, d, ben = env
    p = _people(application, ben)
    project, _ = d.new_project("No Escalation Home (synthetic)", "NEW_HOME", "GENERAL_CONTRACTOR")
    kevin, sam = p["kevin"], p["sam"]
    before = {"kevin": _access(kevin, project.id), "sam": _access(sam, project.id), "ben": _access(ben, project.id)}
    # A Field-only crew member as Project Lead: no office access, no project on Field from the lead alone.
    set_project_lead(organization_id=ORG, project_id=project.id, user_id=kevin.id)
    assert _access(kevin, project.id) == before["kevin"]
    assert before["kevin"]["field_only"] is True and before["kevin"]["sees_project"] is False
    kd = p["kevin_driver"]
    for url in (f"/projects/{project.id}", f"/projects/{project.id}/lead", "/projects/", "/schedule",
                f"/projects/{project.id}/close"):
        r = kd.http.get(url)
        assert r.status_code in (302, 403) and "/projects/" not in (r.headers.get("Location") or ""), url
    assert kd.http.get(f"/field/projects/{project.id}").status_code in (302, 403, 404)
    assert kd.http.post(f"/projects/{project.id}/lead", data={"project_lead_user_id": ""}).status_code in (302, 403)
    db.session.expire_all()
    assert db.session.get(Project, project.id).project_lead_user_id == kevin.id  # Kevin could not change it
    # An office person (not the owner) as Project Lead gains nothing extra: still no close, no owner decisions.
    set_project_lead(organization_id=ORG, project_id=project.id, user_id=sam.id)
    assert _access(sam, project.id) == before["sam"] and before["sam"]["owner"] is False
    sd = _login(application, STAFF)
    close = sd.http.get(f"/projects/{project.id}/close")
    assert close.status_code in (302, 403), close.status_code
    assert _access(ben, project.id) == before["ben"]
    assert _access(kevin, project.id) == before["kevin"]


def test_project_lead_is_separate_from_crew_assignments_and_appointment_assignees(env):
    application, d, ben = env
    p = _people(application, ben)
    project = _build_new_home(d)
    _cost_new_home(d, project)
    version = G.current_version(G.get_guided(ORG, project.id))
    d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/approve-all-costing", data={})
    d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/apply-org-pricing", data={})
    _accept_and_build(d, project)
    from app.models.appointment import CompanyAppointment
    from app.models.schedule import WorkScheduleAssignment
    from app.services.local_time import local_today
    from app.services.schedule import create_schedule_item
    from app.services.work_structure import list_project_work_elements

    elements = list_project_work_elements(project.id, organization_id=ORG)
    start = local_today() + timedelta(days=5)
    item = create_schedule_item(project_id=project.id, project_work_element_id=elements[0].id,
                                scheduled_start=start, scheduled_end=start + timedelta(days=1), organization_id=ORG)
    assignments, appointments = WorkScheduleAssignment.query.count(), CompanyAppointment.query.count()
    set_project_lead(organization_id=ORG, project_id=project.id, user_id=p["sam"].id)
    assert WorkScheduleAssignment.query.count() == assignments and CompanyAppointment.query.count() == appointments
    # Manage a Project: the lead is shown first and never counts as an assignment.
    run_id = _start(d, "MANAGE_PROJECT", project_id=str(project.id))
    state, page = _state(d, run_id, "people")
    assert "Project Lead" in page and STAFF[2] in page and "0 of 1 scheduled item assigned" in page
    assert state == "todo"
    # The wizard sets it with the same service; the change is in the wizard's history.
    _step(d, run_id, "people", action="submit", project_lead_user_id=str(ben.id))
    db.session.expire_all()
    assert db.session.get(Project, project.id).project_lead_user_id == ben.id
    assert "PROJECT_LEAD_SET" in _events(run_id)
    _step(d, run_id, "people", action="submit", project_lead_user_id=str(p["other"].id))
    assert any("this company's people" in m for m in d.flashes())
    db.session.expire_all()
    assert db.session.get(Project, project.id).project_lead_user_id == ben.id
    # The Company Calendar shows the lead on the project's card, compactly.
    calendar = d.get(f"/schedule?project_id={project.id}&from={start.isoformat()}&to={(start + timedelta(days=3)).isoformat()}")
    assert re.search(r"data-calendar-project-lead>Project Lead: Ben Brayman \(synthetic\)<", calendar)
    _ = item


def test_start_a_new_project_sets_the_project_lead_in_its_lead_step(env):
    application, d, ben = env
    p = _people(application, ben)
    run_id = _start(d, "NEW_PROJECT")
    _create_from_wizard(d, run_id, name="Wizard Lead Home (synthetic)")
    project = Project.query.filter_by(organization_id=ORG, name="Wizard Lead Home (synthetic)").one()
    state, page = _state(d, run_id, "responsibility")
    assert state == "todo" and "Project Lead: Unassigned" in page and 'name="project_lead_user_id"' in page
    assert "Who is leading it, and when?" in page and GONE[2] not in page and "Other Company Owner" not in page
    _step(d, run_id, "responsibility", action="submit", project_lead_user_id=str(p["kevin"].id))
    db.session.expire_all()
    assert db.session.get(Project, project.id).project_lead_user_id == p["kevin"].id
    state, page = _state(d, run_id, "responsibility")
    assert state == "done" and f"Project Lead: {KEVIN[2]}" in page
    assert "PROJECT_LEAD_SET" in _events(run_id)
    # Optional: Next never needs it (cleared again, Next still moves on).
    _step(d, run_id, "responsibility", action="submit", project_lead_user_id="")
    _step(d, run_id, "responsibility")
    assert _run(run_id).current_step == "review"


# ====================================================================================== 3 availability
def test_availability_wording_only_from_supplier_data():
    for status in (None, "", "UNKNOWN", "unknown", "maybe", "12 on hand", "OUT_OF_STOCK"):
        assert availability_label(status) == AVAILABILITY_NOT_CONFIRMED == "Availability not confirmed"
        assert availability_confirmed(status) is False
    assert availability_label("IN_STOCK") == "In stock (supplier-reported)"
    assert availability_label("in stock") == "In stock (supplier-reported)"
    assert availability_label("LIMITED") == "Limited (supplier-reported)"
    assert availability_label("SPECIAL_ORDER") == "Special order (supplier-reported)"
    for label in map(availability_label, ("IN_STOCK", "LIMITED", "SPECIAL_ORDER", None)):
        assert not re.search(r"\d", label)  # never a quantity


_KEEP = object()


def _quick_quote(application, store_facts, *, availability=_KEEP):
    from app.models.supplier_quote import SupplierQuote, SupplierSellingPrice
    from tests.pro_desk_page_server import QUICK_FORM, STORE

    sid = store_facts["supplier_id"]
    if availability is not _KEEP:
        for row in SupplierSellingPrice.query.all():
            row.availability = availability
        db.session.commit()
    store = _supplier_login(application, *STORE)
    store.post(f"/supplier/{sid}/pro-desk/quick", data={
        "customer_name": "Pat Walk-in (synthetic)", "customer_phone": "613-555-0100", "customer_town": "Winchester",
        "demo_synthetic": "yes", "assembly_id": str(store_facts["standard_id"]), **QUICK_FORM})
    quote = SupplierQuote.query.filter_by(supplier_id=sid).order_by(SupplierQuote.id.desc()).first()
    r = store.post(f"/supplier/{sid}/wizards/start", data={})
    run_id = int(re.search(r"/wizards/run/(\d+)", r.headers["Location"]).group(1))
    store.post(f"/supplier/{sid}/wizards/run/{run_id}/step/open", data={"wizard_action": "submit",
                                                                        "record": f"quote:{quote.id}"})
    return store, sid, quote, run_id


def test_availability_not_confirmed_in_the_pro_desk_wizard_and_quick_quote_without_supplier_data(pro_desk):
    application, store_facts = pro_desk
    store, sid, quote, run_id = _quick_quote(application, store_facts, availability=None)
    state, page = _sstate(store, sid, run_id, "availability")
    assert state == "info" and "Availability not confirmed" in page
    assert "in stock" not in page.lower() and "not in stock" not in page.lower()
    # The quotation page Quick Quote lands on says the same for every priced line.
    qpage = store.get(f"/supplier/{sid}/pro-desk/{quote.id}")
    priced = qpage.count('data-price-status="PRICED"')
    assert priced and qpage.count('data-availability="NOT_CONFIRMED">Availability not confirmed<') == priced
    assert "(supplier-reported)" not in qpage


def test_availability_from_the_price_file_is_shown_as_the_suppliers_statement(pro_desk):
    application, store_facts = pro_desk
    store, sid, quote, run_id = _quick_quote(application, store_facts, availability="LIMITED")
    state, page = _sstate(store, sid, run_id, "availability")
    assert state == "info" and "Limited (supplier-reported)" in page and "from your price file" in page
    qpage = store.get(f"/supplier/{sid}/pro-desk/{quote.id}")
    assert 'data-availability="LIMITED">Limited (supplier-reported)<' in qpage
    # UNKNOWN in the price file is not availability.
    from app.models.supplier_quote import SupplierSellingPrice

    for row in SupplierSellingPrice.query.all():
        row.availability = "UNKNOWN"
    db.session.commit()
    assert "Availability not confirmed" in _sstate(store, sid, run_id, "availability")[1]


def test_contractor_facing_availability_says_not_confirmed_without_supplier_evidence(hub):
    application, facts, S = hub
    from flask import render_template_string

    from app.models.supplier_portal import SupplierRequestShare
    from app.services.deck_takeoff import storage

    office = _office_login(application)
    share = db.session.get(SupplierRequestShare, facts["earlier_share_id"])
    # The contractor's view of each supplier response: availability is the supplier's statement or exactly
    # "Availability not confirmed" — never the raw text or an invented value.
    seen = 0
    for response in storage.list_responses(ORG, share.project_id):
        if response.get("records_response"):
            continue  # a recording follow-up, not a supplier response page
        page = office.get(f"/projects/{share.project_id}/deck-takeoff/responses/{response['response_id']}")
        cells = re.findall(r"<td data-availability>([^<]*)</td>", page)
        for cell in cells:
            assert cell in (AVAILABILITY_NOT_CONFIRMED, "In stock (supplier-reported)", "Limited (supplier-reported)",
                            "Special order (supplier-reported)"), cell
        seen += len(cells)
        for row in response.get("results") or []:
            if row.get("availability_status") in (None, "UNKNOWN"):
                assert not cells or AVAILABILITY_NOT_CONFIRMED in cells
    with application.test_request_context():
        rendered = render_template_string("{{ none|availability_label }}|{{ 'UNKNOWN'|availability_label }}|"
                                          "{{ 'IN_STOCK'|availability_label }}", none=None)
    assert rendered == "Availability not confirmed|Availability not confirmed|In stock (supplier-reported)"
    _ = seen


# ====================================================================================== 2 pickup and delivery
def test_walk_in_pickup_or_delivery_is_recorded_and_never_shown_complete(pro_desk):
    application, store_facts = pro_desk
    from app.services import supplier_pro_desk as P

    store, sid, quote, run_id = _quick_quote(application, store_facts, availability="IN_STOCK")
    state, page = _sstate(store, sid, run_id, "delivery")
    assert state == "na" and "Arranged in the store&#39;s own system" in page
    assert "Pickup or delivery not recorded" in page
    # Recorded from the wizard step (the quotation's own record; no new column), and from the quotation page.
    store.post(f"/supplier/{sid}/wizards/run/{run_id}/step/delivery", data={"wizard_action": "submit",
                                                                            "fulfilment": "PICKUP"})
    db.session.expire_all()
    assert P.requested_fulfilment(P.supplier_quote(sid, quote.id))["method"] == "PICKUP"
    store.post(f"/supplier/{sid}/pro-desk/{quote.id}/fulfilment", data={"fulfilment": "DELIVERY"})
    db.session.expire_all()
    q = P.supplier_quote(sid, quote.id)
    assert P.requested_fulfilment(q)["label"] == "Delivery"
    assert any(e.event_type == "FULFILMENT_REQUESTED" for e in P.quote_events(q))
    store.post(f"/supplier/{sid}/pro-desk/{quote.id}/fulfilment", data={"fulfilment": "TELEPORT"})
    db.session.expire_all()
    assert P.requested_fulfilment(P.supplier_quote(sid, quote.id))["method"] == "DELIVERY"
    # Through issue, acceptance and the order package: the method is kept; nothing claims it happened.
    for row in P.price_quote(q)["rows"]:
        if row["code"].startswith("CAL-OB-TRUSS"):
            store.post(f"/supplier/{sid}/pro-desk/{quote.id}/line", data={"code": row["code"], "exclude_reason": "Truss quote to follow"})
    store.post(f"/supplier/{sid}/pro-desk/{quote.id}/issue")
    store.post(f"/supplier/{sid}/pro-desk/{quote.id}/accept", data={"method": "in_person", "customer_name": "Pat Walk-in"})
    store.post(f"/supplier/{sid}/pro-desk/{quote.id}/order-ready")
    db.session.expire_all()
    assert P.supplier_quote(sid, quote.id).order_ready_at is not None, store.flashes()
    order_page = store.get(f"/supplier/{sid}/pro-desk/{quote.id}/order")
    assert 'data-fulfilment="DELIVERY"' in order_page and "Arranged in the store's own system" in order_page
    state, page = _sstate(store, sid, run_id, "delivery")
    assert state == "info" and "not tracked in CalibraytAI" in page and "Delivery (recorded by" in page
    state, page = _sstate(store, sid, run_id, "close")
    assert state == "info" and "pickup or delivery not confirmed in CalibraytAI" in page
    for claim in ("Delivered", "delivered on", "Picked up", "picked up", "Fulfilled", "fulfilment complete"):
        assert claim not in page.replace("not confirmed", ""), claim


def test_contractor_order_is_delivery_to_site_and_done_only_when_marked_delivered(hub):
    application, facts, S = hub
    from app.models.supplier_portal import SupplierPurchaseOrder, SupplierRequestShare
    from app.services.deck_takeoff import storage
    from app.services.local_time import local_today

    sid, share_id = facts["bmr_id"], facts["earlier_share_id"]
    darcy = _supplier_login(application, S.DARCY[1], S.DARCY[2])
    r = darcy.post(f"/supplier/{sid}/wizards/start", data={"share_id": share_id})
    run_id = int(re.search(r"/wizards/run/(\d+)", r.headers["Location"]).group(1))
    state, page = _sstate(darcy, sid, run_id, "availability")
    assert state == "na" and "Availability not confirmed" in page
    state, page = _sstate(darcy, sid, run_id, "delivery")
    assert state == "waiting" and "Arranged in the store&#39;s own system" in page and "Delivery to the job site" in page
    office = _office_login(application)
    share = db.session.get(SupplierRequestShare, share_id)
    follow = next(x for x in storage.list_responses(ORG, share.project_id) if x.get("records_response") == share.response_ref)
    for result in follow["results"]:
        if result.get("recorded"):
            office.post(f"/projects/{share.project_id}/deck-takeoff/responses/{share.response_ref}/approve",
                        data={"canonical_material_id": result["canonical_material_id"], "status": "APPROVED"})
    office.post(f"/projects/{share.project_id}/supplier-requests/{share_id}/order",
                data={**SIGN, "delivery_date": (local_today() + timedelta(days=12)).isoformat(), "site_contact": "Ben"})
    order = SupplierPurchaseOrder.query.filter_by(share_id=share_id).one()
    darcy.post(f"/supplier/{sid}/orders/{order.id}/confirm",
               data={**SIGN, "action": "confirm", "expected_delivery": (local_today() + timedelta(days=12)).isoformat()})
    state, page = _sstate(darcy, sid, run_id, "delivery")
    assert state == "waiting" and "not marked delivered" in page and order.delivery_address in page
    assert _sstate(darcy, sid, run_id, "close")[0] == "todo"
    # A DELIVERED status with no recorded "marked delivered" is not a confirmation: never shown done.
    order.status = "DELIVERED"
    db.session.commit()
    for step in ("delivery", "close"):
        state, page = _sstate(darcy, sid, run_id, step)
        assert state == "info" and "no delivery confirmation is recorded" in page, step
    order.status = "CONFIRMED"
    db.session.commit()
    # The real confirmation: marked delivered, with its date and side.
    darcy.post(f"/supplier/{sid}/orders/{order.id}/delivered", data={"delivered_on": local_today().isoformat()})
    state, page = _sstate(darcy, sid, run_id, "delivery")
    assert state == "done" and "marked delivered" in page and "(supplier)" in page
    state, page = _sstate(darcy, sid, run_id, "close")
    assert state == "done" and "marked delivered" in page and "history are kept" in page
    _ = Organization

"""Guided Project Estimating & Universal Calculator Integration — automated acceptance (brief section 14).

The synthetic New Home / General Contractor project with the brief's 14 responsibilities exactly, driven through
the real pages: new project, scope, the generated workflow, internal calculators through the estimate review,
subcontract quotes with Pricing Decision A, labour and materials, allowances and an authorized no-cost decision,
save/exit/resume, out-of-sequence work, missing costs, scope revisions, costing approval, the internal cost
document, pricing (true gross margin and HST), the customer proposal, the hand-off into the build, roles,
organization isolation, the three calculator choices (Use Result Only, Add to Existing Project, Create New
Project) with cancellation and duplicate prevention, and a second project type (Garage / Outbuilding).
Synthetic data only. The browser walk (tools/release/evidence_guided_estimating.mjs) checks desktop and phone.
"""

from __future__ import annotations

import io
import re
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import EstimateLineItem, Project
from app.models.calculation_estimate_mapping import CalculationResultIntake
from app.models.guided_estimating import GuidedEstimate, GuidedEstimateEvent, GuidedEstimateStage
from app.models.organization import Organization
from app.models.project_calculation import ProjectCalculation
from app.services import guided_estimating as G
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.guided_support import NEW_HOME_NAMES, NEW_HOME_SCOPE, Driver, client, cost_item, seed_company

BEN = ("ben.guided@example.invalid", "ben-guided-password", "Ben Brayman (synthetic)")
KEVIN = ("kevin.guided@example.invalid", "kevin-guided-password", "Kevin Field (synthetic crew)")
OTHER = ("other.guided@example.invalid", "other-guided-password", "Other Company Owner (synthetic)")

FOOTING_FORM = {"unit_system": "imperial", "footing_length": ["120", "40"], "footing_width": ["2", "2"],
                "footing_thickness": ["10", "10"], "footing_count": ["", ""], "waste_percent": "5"}
WALL_FORM = {"length_ft": "40", "height_ft": "8", "spacing_in": "16", "stud_size": "2x6", "top_plate_count": "2",
             "bottom_plate_count": "1"}
FLOOR_FORM = {"unit_system": "imperial", "room_length": ["20", "14", "12"], "room_width": ["16", "12", "10"],
              "waste_percent": "8", "box_coverage": "20"}


@pytest.fixture()
def env():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "k"})
    context = application.app_context()
    context.push()
    db.create_all()
    ensure_default_organization()
    seed_company()
    ben = ensure_office_user(email=BEN[0], password=BEN[1], display_name=BEN[2])
    db.session.commit()
    http = application.test_client()
    login_office_user(http, email=BEN[0], password=BEN[1])
    yield application, Driver(http), ben
    db.session.remove()
    db.drop_all()
    context.pop()


def _login(application, who):
    from flask import g

    http = application.test_client()
    g.pop("_login_user", None)
    login_office_user(http, email=who[0], password=who[1])
    return Driver(http)


def _field_only_kevin(application, ben):
    from app.models.user import UserMembership
    from app.services.access_domains import set_field_only
    from app.services.instance_authority import set_instance_owner

    membership = UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one()
    set_instance_owner(ORG, membership.id, ben.id)
    db.session.commit()

    kevin = ensure_office_user(email=KEVIN[0], password=KEVIN[1], display_name=KEVIN[2])
    set_field_only(UserMembership.query.filter_by(user_id=kevin.id).one(), True, ben)
    db.session.commit()
    return _login(application, KEVIN)


def _make_owner(user):
    from app.models.user import UserMembership
    from app.services.instance_authority import set_instance_owner

    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()
    set_instance_owner(ORG, membership.id, user.id)
    db.session.commit()


def _other_company(application):
    if db.session.get(Organization, "ORG-GUIDED-OTHER") is None:
        db.session.add(Organization(id="ORG-GUIDED-OTHER", legal_name="Other Synthetic Builder",
                                    display_name="Other Synthetic Builder", is_active=True))
        db.session.commit()
    ensure_office_user(email=OTHER[0], password=OTHER[1], display_name=OTHER[2], organization_id="ORG-GUIDED-OTHER")
    db.session.commit()
    return _login(application, OTHER)


def _existing_job():
    """A project and estimate made before Guided Estimating, the old way. It must stay exactly as it is."""
    from app.services.estimate_builder import add_manual_line, create_section
    from app.services.estimates import create_estimate

    project = Project(name="Existing deck job (synthetic)", client_id=client("Morgan Existing (synthetic)").id,
                      organization_id=ORG, status="Estimating")
    db.session.add(project)
    db.session.commit()
    estimate = create_estimate(project_id=project.id, estimate_number="EST-EXIST-1", title="Existing deck")
    section = create_section(estimate.current_version, name="Deck")
    add_manual_line(section, line_type="Custom", description="Deck boards", quantity=40, unit="ea", unit_cost=12)
    return project, estimate


def _fingerprint(estimate):
    db.session.expire_all()
    rows = []
    for version in estimate.versions:
        rows.append((version.id, version.status, version.is_locked, str(version.subtotal), str(version.total)))
        for section in version.sections:
            for line in section.line_items:
                rows.append((line.id, line.description, str(line.quantity), str(line.unit_cost),
                             str(line.extended_cost), line.code))
    return rows


# --------------------------------------------------------------------------------------- stage costing helpers
def _quote(d, project, stage, *, reference, amount, name, code, select=True, apply=True):
    from app.services.subcontract_quote import quotes_for_line

    stage = db.session.get(GuidedEstimateStage, stage.id)
    if not [l for l in G.stage_lines(stage) if l.code == G.SUBCONTRACT_CODE]:
        d.action(project, stage, "subcontract", {"scope_description": f"{stage.section_name}: supply and install"})
    line = next(l for l in G.stage_lines(stage) if l.code == G.SUBCONTRACT_CODE)
    version = G.current_version(stage.guided_estimate)
    here = f"/projects/{project.id}/guided/stages/{stage.id}"
    response = d.post(f"/projects/{project.id}/scope-delivery/lines/{line.id}/quotes/receive",
                      data={"version_id": version.id, "estimate_id": version.estimate_id, "return_to": here,
                            "subcontractor_legal_name": name, "subcontractor_code": code, "quote_reference": reference,
                            "amount": amount, "quote_date": "2026-10-20", "included_scope": "Supply and install",
                            "exclusions": "Permits"})
    assert response.headers["Location"].endswith(here)  # back to the stage, not the Scope Delivery Review
    quote = [q for q in quotes_for_line(line) if q.quote_reference == reference][0]
    if select:
        d.post(f"/projects/{project.id}/scope-delivery/quotes/{quote.id}/select",
               data={"version_id": version.id, "estimate_id": version.estimate_id, "return_to": here})
    if apply:
        d.post(f"/projects/{project.id}/scope-delivery/lines/{line.id}/suggested-cost/apply",
               data={"version_id": version.id, "estimate_id": version.estimate_id, "kind": "labour", "return_to": here})
    return line, quote


def _complete(d, project, stage, expect_ok=True):
    response = d.action(project, stage, "complete_next")
    stage = db.session.get(GuidedEstimateStage, stage.id)
    db.session.refresh(stage)
    if expect_ok:
        assert stage.completion_basis, (stage.section_name, d.flashes(), G.stage_check(stage)["issues"])
    return response


def _calculator_to_stage(d, project, stage, slug, form, calculator, mapping):
    """Option B from the stage's own calculator link: calculate, add to the project and stage, review, confirm."""
    payload, html = d.calculator_result(f"{slug}?project={project.id}&stage={stage.id}", form)
    assert "What would you like to do with this result?" in html and "Add to Existing Project" in html
    assert f'value="{project.id}" selected' in html  # the stage's project is already chosen
    data = d.link(project, calculator, payload, stage=stage)
    assert data["ok"] and data["created"] and data["review_url"]
    review = d.send_to_review(project, data["calculation_id"])
    assert "section_id=" in review and f"return_to=/projects/{project.id}/guided/stages/{stage.id}" in review
    section = G.section_for(db.session.get(GuidedEstimateStage, stage.id), G.current_version(stage.guided_estimate))
    assert d.confirm_quantities(review, mapping, section.id) >= 1
    return payload, data


def _labour(d, project, stage, hours):
    stage = db.session.get(GuidedEstimateStage, stage.id)
    from app.services.estimate_labour_hours import is_labour_line

    items = [l for l in G.stage_lines(stage) if not is_labour_line(l) and l.code != G.SUBCONTRACT_CODE]
    d.action(project, stage, "labour_hours", {f"hours_{items[0].id}": str(hours)})


def _build_new_home(d):
    project, location = d.new_project("Avery New Home (synthetic)", "NEW_HOME", "GENERAL_CONTRACTOR")
    assert location.endswith(f"/projects/{project.id}/guided/scope")
    r = d.scope(project, NEW_HOME_SCOPE, action="finalize")
    assert r.headers["Location"].endswith(f"/projects/{project.id}/guided")
    return project


def _cost_new_home(d, project, *, skip=()):
    """Cost every stage the way Ben does, through the real pages. Returns {stage key: stage}."""
    s = {k: d.stage(project, k) for k in NEW_HOME_SCOPE}
    plan = [
        # Out of sequence on purpose: roofing (stage 5) and final cleanup (stage 14) first.
        ("roofing", lambda st: _quote(d, project, st, reference="RF-1188", amount="18400", name="Ridge Roofing (synthetic)", code="RIDGE")),
        ("final_cleanup", lambda st: (d.action(project, st, "add_cost", {"kind": "labour", "description": "Final clean", "quantity": "16"}),
                                      d.action(project, st, "add_cost", {"kind": "disposal", "description": "40 yd bin", "quantity": "1", "unit": "bin", "unit_cost": "650"}),
                                      d.action(project, st, "add_cost", {"kind": "equipment", "description": "Floor scrubber rental", "quantity": "1", "unit": "day", "unit_cost": "180"}),
                                      d.action(project, st, "routing"))),
        ("site_prep", lambda st: _quote(d, project, st, reference="SP-201", amount="6500", name="Valley Site Services (synthetic)", code="VALLEY")),
        ("excavation", lambda st: (_quote(d, project, st, reference="EX-14", amount="14200", name="Rideau Excavating (synthetic)", code="RIDEAU", select=False, apply=False),
                                   _quote(d, project, st, reference="EX-15", amount="12900", name="Valley Site Services (synthetic)", code="VALLEY"))),
        ("footings_foundation", lambda st: (_calculator_to_stage(d, project, st, "footing", FOOTING_FORM, "footing", {"concrete": "SYN-CONC-YD3"}),
                                            _labour(d, project, st, 40), d.action(project, st, "routing"))),
        ("framing", lambda st: (_framing(d, project, st), _labour(d, project, st, 120), d.action(project, st, "routing"))),
        ("windows_doors", lambda st: (d.action(project, st, "add_cost", {"kind": "material", "description": "Window and exterior door package (synthetic)", "quantity": "1", "unit": "lot", "unit_cost": "14800"}),
                                      d.action(project, st, "add_cost", {"kind": "labour", "description": "Install windows and doors", "quantity": "24"}),
                                      d.action(project, st, "routing"))),
        ("siding", lambda st: _quote(d, project, st, reference="SD-77", amount="21800", name="Clad Right (synthetic)", code="CLAD")),
        ("electrical", lambda st: _quote(d, project, st, reference="EL-9", amount="24500", name="Sparks Electric (synthetic)", code="SPARKS")),
        ("plumbing", lambda st: _quote(d, project, st, reference="PL-3", amount="19750", name="Flow Plumbing (synthetic)", code="FLOW")),
        ("hvac", lambda st: d.action(project, st, "allowance", {"amount": "16000", "description": "HVAC allowance (quote to follow)", "reason": "The HVAC quote is still to come"})),
        ("insulation", lambda st: _quote(d, project, st, reference="IN-5", amount="9800", name="Warm Walls (synthetic)", code="WARM")),
        ("drywall", lambda st: _quote(d, project, st, reference="DW-12", amount="17600", name="Smooth Board (synthetic)", code="SMOOTH")),
        ("interior_finishes", lambda st: (_calculator_to_stage(d, project, st, "flooring", FLOOR_FORM, "flooring", {"floor_area_to_order": "SYN-FLOOR-FT2"}),
                                          _set_aside_rest(d, project, st), _labour(d, project, st, 60), d.action(project, st, "routing"))),
    ]
    for key, work in plan:
        if key in skip:
            continue
        work(s[key])
        _complete(d, project, s[key])
    return s


def _framing(d, project, stage):
    _calculator_to_stage(d, project, stage, "wall-framing", WALL_FORM, "wall_framing", {"studs": "SYN-STUD-EA"})
    _set_aside_rest(d, project, stage)


def _set_aside_rest(d, project, stage):
    stage = db.session.get(GuidedEstimateStage, stage.id)
    for calc, intake, _count in G.stage_check(stage)["open_intakes"]:
        d.action(project, stage, "set_aside", {"intake_id": intake.id})


# ======================================================================================= the acceptance example
def test_new_project_type_role_and_the_fourteen_stage_scope(env):
    application, d, _ben = env
    # Home (compact, 27 Oct 2026): Estimate a Project, with Continue manually opening Start New Estimate.
    assert 'href="/estimating/start" data-continue-manually="GUIDED_ESTIMATING" data-home-start-estimate' in d.get("/")
    start = d.get("/estimating/start")
    assert "Create a new project" in start and "Estimate an existing project" in start
    client()
    form = d.get("/projects/new?guided=1")
    assert "New Home Construction" in form and "Garage / Outbuilding" in form and "General Contractor" in form
    project, location = d.new_project("Avery New Home (synthetic)", "NEW_HOME", "GENERAL_CONTRACTOR")
    guided = G.get_guided(ORG, project.id)
    assert (guided.project_type, guided.contractor_role, guided.scope_status) == ("NEW_HOME", "GENERAL_CONTRACTOR", "DRAFT")
    assert [s.display_name for s in guided.top_stages] == NEW_HOME_NAMES
    # Nothing defaults: no responsibility is recorded and no round choice is pre-selected.
    assert all(s.responsibility is None for s in guided.stages)
    page = d.get(location)
    assert page.count('type="radio"') >= 14 * 3 and "checked" not in re.sub(r"<details.*?</details>", "", page, flags=re.S).split("data-guided-scope")[1].split("Add a stage")[0]
    assert "INTERNAL" in page and "SUBCONTRACTED" in page and 'value="NA"' in page
    # Undecided is allowed in a draft, never at finalize.
    half = dict(list(NEW_HOME_SCOPE.items())[:7])
    d.scope(project, half, action="save")
    assert G.get_guided(ORG, project.id).scope_status == "DRAFT"
    d.scope(project, half, action="finalize")
    assert G.get_guided(ORG, project.id).scope_status == "DRAFT"
    assert any("Decide every stage" in m for m in d.flashes())
    d.scope(project, NEW_HOME_SCOPE, action="finalize")
    guided = G.get_guided(ORG, project.id)
    assert guided.scope_status == "FINALIZED"
    assert {s.stage_key: s.responsibility for s in guided.top_stages} == NEW_HOME_SCOPE  # exactly the 14
    # Each included stage is a section of the one estimate, in construction order.
    version = G.current_version(guided)
    assert [s.name for s in version.sections] == NEW_HOME_NAMES
    workflow = d.get(f"/projects/{project.id}/guided")
    assert "0 of 14 stages complete" in workflow
    for name in NEW_HOME_NAMES:
        assert name.replace("&", "&amp;") in workflow
    assert 'data-count-not_started="14"' in workflow


def test_the_whole_new_home_estimate_to_proposal_and_build(env):
    application, d, ben = env
    existing_project, existing_estimate = _existing_job()
    before = _fingerprint(existing_estimate)
    project = _build_new_home(d)
    guided = G.get_guided(ORG, project.id)

    # Waiting for a quote does not hold up the rest (out of sequence work).
    excavation = d.stage(project, "excavation")
    d.action(project, excavation, "request_quote")
    assert G.effective_status(db.session.get(GuidedEstimateStage, excavation.id)) == "WAITING_FOR_QUOTE"
    assert "Waiting for Quote" in d.get(f"/projects/{project.id}/guided/stages/{excavation.id}")

    # Missing costs stay visible and block completion.
    hvac = d.stage(project, "hvac")
    _complete(d, project, hvac, expect_ok=False)
    assert any("Not complete yet" in m for m in d.flashes())
    assert db.session.get(GuidedEstimateStage, hvac.id).completion_basis is None

    # Save & Exit, then Resume where Ben stopped.
    framing = d.stage(project, "framing")
    response = d.action(project, framing, "save_exit")
    assert response.headers["Location"].endswith(f"/projects/{project.id}")
    assert d.http.get(f"/projects/{project.id}/guided/resume").headers["Location"].endswith(f"/guided/stages/{framing.id}")

    s = _cost_new_home(d, project)
    db.session.expire_all()
    guided = G.get_guided(ORG, project.id)
    view = G.workflow_view(guided)
    assert (view["done"], view["included"]) == (14, 14)
    bases = {row.stage_key: row.completion_basis for row in guided.top_stages}
    assert bases["hvac"] == "APPROVED_ALLOWANCE" and bases["electrical"] == "CONFIRMED_COSTS"
    events = [e.event for e in GuidedEstimateEvent.query.filter_by(guided_estimate_id=guided.id)]
    assert events.index("COMPLETED") and "QUOTE_REQUESTED" in events

    version = G.current_version(guided)
    # Labour at the approved company rate, materials from the company costs, subcontracts from the quotes.
    from app.models.labour_engine import DirectLabourCostRateStandard

    rate = Decimal(str(DirectLabourCostRateStandard.query.filter_by(organization_id=ORG, approval_status="APPROVED").one().rate_per_man_hour))
    footing = G.section_for(s["footings_foundation"], version)
    labour = [l for l in footing.line_items if l.unit == "hr"][0]
    assert labour.unit_cost == rate and labour.quantity == Decimal("40")
    concrete = [l for l in footing.line_items if l.cost_item_id == cost_item("SYN-CONC-YD3").id][0]
    assert concrete.unit_cost == Decimal("210.00")
    excavation_line = [l for l in G.section_for(s["excavation"], version).line_items if l.code == G.SUBCONTRACT_CODE][0]
    assert excavation_line.extended_cost == Decimal("12900.00")  # the selected (lower) quote, applied by a person
    assert excavation_line.costing_override_by == BEN[2]

    # One authoritative internal cost estimate: every stage, counted once, equal to the estimate's direct cost.
    from app.services.estimate_output import version_direct_cost

    doc = G.internal_cost_document(guided)
    assert doc["direct_cost"] == version_direct_cost(version)
    totals = doc["totals"]
    assert totals["subcontract"] == Decimal("131250.00")  # 6500+12900+18400+21800+24500+19750+9800+17600
    assert totals["allowance"] == Decimal("16000.00")
    assert sum((totals[k] for k in ("material", "labour", "subcontract", "equipment", "delivery", "allowance", "other")),
               Decimal("0")) == doc["direct_cost"]
    html = d.get(f"/projects/{project.id}/guided/internal-cost")
    assert "INTERNAL — NOT FOR CUSTOMER DISTRIBUTION" in html and "DRAFT" in html and "Subcontract quote EX-15" in html
    pdf = d.http.get(f"/projects/{project.id}/guided/internal-cost.pdf")
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf"
    from pypdf import PdfReader

    text = "".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf.data)).pages)
    assert "INTERNAL" in text and "NOT FOR CUSTOMER DISTRIBUTION" in text and "Footings & foundation" in text

    # Review Pricing & Prepare Proposal: the existing costing approval and pricing engine, in order.
    pricing_url = f"/projects/{project.id}/guided/pricing"
    assert "Every included stage is complete" in d.get(pricing_url)
    back = d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/approve-all-costing",
                  data={"return_to": pricing_url})
    assert back.headers["Location"].endswith(pricing_url)
    back = d.post(f"/estimates/{version.estimate_id}/versions/{version.id}/apply-org-pricing", data={"return_to": pricing_url})
    assert back.headers["Location"].endswith(pricing_url)
    db.session.expire_all()
    version = G.current_version(G.get_guided(ORG, project.id))
    snapshot = version.pricing_snapshot
    assert snapshot.method == "TRUE_GROSS_MARGIN" and snapshot.target_gross_margin == Decimal("0.150000")
    assert snapshot.direct_cost_basis == doc["direct_cost"]
    expected_sell = (doc["direct_cost"] / Decimal("0.85")).quantize(Decimal("0.01"))
    assert abs(snapshot.pre_tax_selling_price - expected_sell) <= Decimal("0.01")
    assert snapshot.tax_percent == Decimal("13.00")
    page = d.get(pricing_url)
    assert "True gross margin" in page and "15.0%" in page
    assert "Costing approved" in d.get(f"/projects/{project.id}/guided/internal-cost")

    # The customer proposal: existing services; issue passes; nothing confidential on it.
    from app.services.proposals import create_proposal, create_proposal_template, update_proposal_status

    template = create_proposal_template(name="Synthetic standard", organization_id=ORG, is_default=True)
    proposal = create_proposal(estimate=version.estimate, version=version, template=template, organization_id=ORG)
    update_proposal_status(proposal, "Issued")
    assert proposal.total == snapshot.customer_total
    customer = d.get(f"/proposals/{proposal.id}/preview")  # what the customer sees
    customer_pdf = d.http.get(f"/proposals/{proposal.id}/pdf")
    customer += "".join(page.extract_text() for page in PdfReader(io.BytesIO(customer_pdf.data)).pages)
    assert "Footings &amp; foundation" in customer or "Footings & foundation" in customer
    for secret in ("INTERNAL — NOT FOR CUSTOMER", "per hour", "Manual entry by", "Subcontract quote applied",
                   "EX-15", "12,900.00", "$210.00", "Approved allowance"):
        assert secret not in customer, secret

    # Into the build: accepted, locked, and the same stage sections become the project's work items.
    update_proposal_status(proposal, "Accepted")
    from app.services.estimates import lock_version
    from app.services.work_structure import list_project_work_elements, seed_project_work_structure

    lock_version(version)
    seed_project_work_structure(project_id=project.id, estimate_version_id=version.id, seeded_by=BEN[2],
                                organization_id=ORG)
    names = [e.display_name for e in list_project_work_elements(project.id, organization_id=ORG)]
    assert names == ["Footings & foundation", "Framing", "Windows & exterior doors", "Interior finishes", "Final cleanup"]
    assert "Work plan built: 5 work items" in d.get(pricing_url)
    # After acceptance, changes go through change orders.
    d.action(project, s["windows_doors"], "add_cost", {"kind": "material", "description": "Extra window", "quantity": "1", "unit": "ea", "unit_cost": "900"})
    assert any("change order" in m for m in d.flashes())
    d.action(project, s["roofing"], "responsibility", {"responsibility": "INTERNAL"})
    assert any("change order" in m for m in d.flashes())
    assert db.session.get(GuidedEstimateStage, s["roofing"].id).responsibility == "SUBCONTRACTED"
    assert "change order" in d.get(f"/projects/{project.id}/guided/scope")

    # The existing project and its estimate are exactly as they were.
    assert _fingerprint(existing_estimate) == before
    assert G.get_guided(ORG, existing_project.id) is None


def test_missing_costs_block_the_proposal_until_an_allowance_or_exclusion_is_approved(env):
    application, d, _ben = env
    project = _build_new_home(d)
    s = _cost_new_home(d, project, skip=("hvac",))
    guided = G.get_guided(ORG, project.id)
    version = G.current_version(guided)
    blockers = G.guided_blockers(guided)
    assert blockers == ["HVAC is Not Started: its costs are not confirmed, and no allowance or exclusion was approved."]
    page = d.get(f"/projects/{project.id}/guided/pricing")
    assert "HVAC is Not Started" in page and "data-create-proposal" not in page
    from app.services.proposals import (ProposalServiceError, create_proposal, create_proposal_template,
                                        proposal_issue_blockers, update_proposal_status)
    from tests.proposal_issue_support import approve_for_issue

    approve_for_issue(version)
    assert any(b.startswith("Guided estimate: HVAC") for b in proposal_issue_blockers(version))
    template = create_proposal_template(name="Synthetic", organization_id=ORG, is_default=True)
    proposal = create_proposal(estimate=version.estimate, version=version, template=template, organization_id=ORG)
    with pytest.raises(ProposalServiceError, match="Guided estimate: HVAC"):
        update_proposal_status(proposal, "Issued")
    # A stage marked complete with no cost is refused; an explicitly approved allowance resolves it.
    _complete(d, project, s["hvac"], expect_ok=False)
    d.action(project, s["hvac"], "allowance", {"amount": "16000", "reason": "The HVAC quote is still to come"})
    _complete(d, project, s["hvac"])
    assert G.guided_blockers(G.get_guided(ORG, project.id)) == []


def test_completion_needs_confirmed_cost_an_approved_allowance_or_an_authorized_no_cost_decision(env):
    application, d, _ben = env
    project = _build_new_home(d)
    windows = d.stage(project, "windows_doors")
    # A line with no cost does not complete the stage.
    d.action(project, windows, "add_cost", {"kind": "material", "description": "Windows (price to come)", "quantity": "1", "unit": "lot", "unit_cost": "0"})
    d.action(project, windows, "routing")
    _complete(d, project, windows, expect_ok=False)
    issues = G.stage_check(db.session.get(GuidedEstimateStage, windows.id))["issues"]
    assert any("no cost yet" in i for i in issues)
    # A subcontract line with a quote that is selected but not used on the line is not a confirmed cost.
    electrical = d.stage(project, "electrical")
    _quote(d, project, electrical, reference="EL-1", amount="24000", name="Sparks Electric (synthetic)", code="SPARKS", apply=False)
    _complete(d, project, electrical, expect_ok=False)
    assert G.effective_status(db.session.get(GuidedEstimateStage, electrical.id)) == "NEEDS_REVIEW"
    line = next(l for l in G.stage_lines(electrical) if l.code == G.SUBCONTRACT_CODE)
    assert line.unit_cost == 0  # Decision A: the quote only suggested the cost
    page = d.get(f"/projects/{project.id}/guided/stages/{electrical.id}")
    assert "Suggested cost" in page and "Use this cost on the line" in page
    # An authorized no-cost decision on an added stage (owner-supplied), recorded with who and why.
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "add_stage", "custom_name": "Owner-supplied appliances"})
    guided = G.get_guided(ORG, project.id)
    assert guided.scope_status == "DRAFT"  # a new stage is undecided: the scope is a draft again
    added = next(st for st in guided.top_stages if st.is_custom)
    assert added.responsibility is None
    d.scope(project, dict(NEW_HOME_SCOPE, **{added.stage_key: "INTERNAL"}), action="finalize")
    _make_owner(_ben)  # an explicit no-cost decision is the owner's (Joel, 24 Oct 2026)
    d.action(project, added, "zero_cost", {"reason": "The owner buys and installs the appliances"})
    _complete(d, project, added)
    row = db.session.get(GuidedEstimateStage, added.id)
    assert row.completion_basis == "AUTHORIZED_ZERO_COST" and row.zero_cost_authorized_by == BEN[2]
    # A completed stage whose costs change is no longer complete until reviewed again.
    d.action(project, added, "add_cost", {"kind": "delivery", "description": "Appliance delivery", "quantity": "1", "unit": "trip", "unit_cost": "120"})
    assert G.effective_status(db.session.get(GuidedEstimateStage, added.id)) != "COMPLETE"


def test_scope_revisions_subcomponents_mixed_work_and_reopening(env):
    application, d, _ben = env
    project = _build_new_home(d)
    # Foundation walls internal while waterproofing is subcontracted: decided part by part.
    parts = {"footings_foundation.footings": "INTERNAL", "footings_foundation.foundation_walls": "INTERNAL",
             "footings_foundation.waterproofing": "SUBCONTRACTED", "footings_foundation.foundation_insulation": "NA",
             "footings_foundation.drainage": "INTERNAL", "footings_foundation.slab": "INTERNAL",
             "footings_foundation.foundation_labour": "INTERNAL"}
    d.scope(project, dict(NEW_HOME_SCOPE, **parts), split=["footings_foundation"], action="finalize",
            na_reasons={"footings_foundation.foundation_insulation": "ICF walls are already insulated"})
    guided = G.get_guided(ORG, project.id)
    foundation = d.stage(project, "footings_foundation")
    assert foundation.is_split and foundation.responsibility_label == "Mixed (by part)"
    names = [s.name for s in G.current_version(guided).sections]
    assert "Footings & foundation — Waterproofing and damp-proofing" in names
    assert "Footings & foundation — Insulation" not in names  # N/A: no section, no cost
    assert d.stage(project, "footings_foundation.foundation_insulation").na_reason == "ICF walls are already insulated"
    waterproofing = d.stage(project, "footings_foundation.waterproofing")
    page = d.get(f"/projects/{project.id}/guided/stages/{waterproofing.id}")
    assert "Record a quote" in page and "Printable quote request sheet" in page
    footings = d.stage(project, "footings_foundation.footings")
    page = d.get(f"/projects/{project.id}/guided/stages/{footings.id}")
    assert "Footing calculator" in page and f"/calculators/footing?project={project.id}&amp;stage={footings.id}" in page
    # Change responsibility from the workflow; it is in the history.
    roofing = d.stage(project, "roofing")
    d.action(project, roofing, "responsibility", {"responsibility": "INTERNAL", "reason": "Our crew is free"})
    assert db.session.get(GuidedEstimateStage, roofing.id).responsibility == "INTERNAL"
    event = GuidedEstimateEvent.query.filter_by(stage_id=roofing.id, event="RESPONSIBILITY").order_by(GuidedEstimateEvent.id.desc()).first()
    assert (event.from_value, event.to_value) == ("SUBCONTRACTED", "INTERNAL")
    assert "Roofing calculator" in d.get(f"/projects/{project.id}/guided/stages/{roofing.id}")
    # A stage with costs cannot be silently dropped to N/A.
    windows = d.stage(project, "windows_doors")
    d.action(project, windows, "add_cost", {"kind": "material", "description": "Windows", "quantity": "1", "unit": "lot", "unit_cost": "100"})
    d.action(project, windows, "responsibility", {"responsibility": "NA"})
    assert any("Remove them before marking it N/A" in m for m in d.flashes())
    # Reopen a completed stage.
    d.action(project, windows, "routing")
    _complete(d, project, windows)
    d.action(project, windows, "reopen", {"reason": "Customer changed the window brand"})
    assert db.session.get(GuidedEstimateStage, windows.id).completion_basis is None


def test_revisions_create_new_versions_and_the_issued_version_is_never_overwritten(env):
    application, d, _ben = env
    project = _build_new_home(d)
    s = _cost_new_home(d, project)
    guided = G.get_guided(ORG, project.id)
    v1 = G.current_version(guided)
    from app.services.estimates import lock_version

    lock_version(v1)
    v1_rows = _fingerprint(guided.estimate)
    page = d.get(f"/projects/{project.id}/guided/stages/{s['windows_doors'].id}")
    assert "issued or locked" in page
    d.action(project, s["windows_doors"], "add_cost", {"kind": "material", "description": "Extra", "quantity": "1", "unit": "ea", "unit_cost": "5"})
    assert any("Start a revision" in m for m in d.flashes())
    d.post(f"/projects/{project.id}/guided/revision", data={"reason": "Customer added a patio door"})
    db.session.expire_all()
    guided = G.get_guided(ORG, project.id)
    v2 = G.current_version(guided)
    assert v2.id != v1.id and G.version_is_editable(v2) and v2.revision_reason == "Customer added a patio door"
    assert [r for r in _fingerprint(guided.estimate) if r[0] in {x[0] for x in v1_rows}][:len(v1_rows)]  # still there
    windows = d.stage(project, "windows_doors")
    # The revision keeps every cost; who supplies and builds each line is confirmed again (existing clone rule).
    assert G.effective_status(windows) == "NEEDS_REVIEW"
    assert all("not confirmed" in i for i in G.stage_check(windows)["issues"])
    d.action(project, windows, "add_cost", {"kind": "material", "description": "Patio door (synthetic)", "quantity": "1", "unit": "ea", "unit_cost": "2400"})
    d.action(project, windows, "routing")
    _complete(d, project, windows)
    compare = d.get(f"/projects/{project.id}/guided/compare?older={v1.id}&newer={v2.id}")
    assert "Added: Patio door (synthetic)" in compare and "+2,400.00" in compare
    v1_after = [r for r in _fingerprint(guided.estimate)]
    v1_lines = {r for r in v1_rows}
    assert v1_lines <= set(v1_after)  # every v1 row unchanged


# ======================================================================================= the three choices
def test_use_result_only_creates_and_changes_nothing(env):
    application, d, _ben = env
    project = _build_new_home(d)
    before = (ProjectCalculation.query.count(), EstimateLineItem.query.count(), CalculationResultIntake.query.count())
    payload, html = d.calculator_result("footing", FOOTING_FORM)
    assert "Use Result Only" in html and "Add to Existing Project" in html and "Create New Project" in html
    assert payload["engine_id"] == "rectangular_footing"
    assert (ProjectCalculation.query.count(), EstimateLineItem.query.count(), CalculationResultIntake.query.count()) == before


def test_add_to_existing_project_carries_everything_once_and_only_through_the_review(env):
    application, d, _ben = env
    project = _build_new_home(d)
    stage = d.stage(project, "interior_finishes")
    payload, _html = d.calculator_result("flooring", FLOOR_FORM)
    first = d.link(project, "flooring", payload, stage=stage)
    again = d.link(project, "flooring", payload, stage=stage)
    assert first["created"] and not again["created"] and first["calculation_id"] == again["calculation_id"]
    # A second calculation of the same result (a new result id, same entries) is still the same record.
    payload2, _ = d.calculator_result("flooring", FLOOR_FORM)
    assert payload2["result_id"] != payload["result_id"]
    assert not d.link(project, "flooring", payload2, stage=stage)["created"]
    record = db.session.get(ProjectCalculation, first["calculation_id"])
    assert record.payload["inputs"] == payload["inputs"] and record.engine_id == "flooring_area"
    assert record.engine_version == "1.0.0" and record.guided_stage_id == stage.id
    assert {q["code"] for q in record.payload["quantities"]} >= {"floor_area_to_order", "flooring_boxes", "room_perimeter"}
    assert record.payload["assumptions"] == [{"code": "waste_percent", "value": "8", "unit_code": "percent"}]
    lines_before = EstimateLineItem.query.count()
    page = d.get(f"/projects/{project.id}/calculations/{record.id}")
    assert "Kept exactly as calculated" in page and "floor_area_to_order".replace("_", " ").capitalize() in page or "Floor area to order" in page
    review = d.send_to_review(project, record.id)
    review_again = d.send_to_review(project, record.id)
    assert CalculationResultIntake.query.count() == 1 and review.split("?")[0] == review_again.split("?")[0]
    assert EstimateLineItem.query.count() == lines_before  # nothing added before a person confirms
    section = G.section_for(stage, G.current_version(G.get_guided(ORG, project.id)))
    page = d.get(review)
    assert f'<option value="{section.id}" selected' in page and "Back to the estimating stage" in page
    d.confirm_quantities(review, {"floor_area_to_order": "SYN-FLOOR-FT2"}, section.id)
    d.confirm_quantities(review, {"floor_area_to_order": "SYN-FLOOR-FT2"}, section.id)  # pressed twice
    added = EstimateLineItem.query.filter_by(cost_item_id=cost_item("SYN-FLOOR-FT2").id).all()
    assert len(added) == 1 and added[0].estimate_section_id == section.id
    assert added[0].quantity == Decimal(next(q["quantity"] for q in payload["quantities"] if q["code"] == "floor_area_to_order"))
    # The project page lists it as before ("Link to a project"), with its way to the review.
    assert "calculations" in d.get(f"/projects/{project.id}")


def test_an_approved_or_issued_estimate_is_never_changed_by_a_calculator_result(env):
    application, d, _ben = env
    project = _build_new_home(d)
    guided = G.get_guided(ORG, project.id)
    from app.services.estimates import lock_version

    lock_version(G.current_version(guided))
    payload, _ = d.calculator_result("footing", FOOTING_FORM)
    data = d.link(project, "footing", payload, stage=d.stage(project, "footings_foundation"))
    response = d.post(f"/projects/{project.id}/calculations/{data['calculation_id']}/send")
    assert response.headers["Location"].endswith(f"/calculations/{data['calculation_id']}")
    assert any("never changed" in m for m in d.flashes())
    assert CalculationResultIntake.query.count() == 0


def test_create_new_project_from_a_calculator_keeps_the_result_and_cancel_returns_it_intact(env):
    application, d, _ben = env
    client()
    payload, html = d.calculator_result("footing", FOOTING_FORM)
    pairs = [[f"post:{k}", v] for k, values in FOOTING_FORM.items() for v in (values if isinstance(values, list) else [values])]
    carry = d.http.post("/calculators/carry", json={
        "calculator": "footing", "summary": "Footing concrete 8.765 yd³", "result_text": "Order 8.765 yd3",
        "entered": [{"label": "Footing 1 length", "value": "120 feet"}], "payload": payload, "form_state": pairs,
        "return_path": "/calculators/footing"}).get_json()
    assert carry["ok"] and "/projects/new?carry=" in carry["url"]
    token = carry["url"].split("carry=")[1]
    form = d.get(carry["url"])
    assert "Bringing your Footing result" in form and "Cancel and go back to the calculator" in form
    assert f'name="carry" value="{token}"' in form
    # Cancel: back to the calculator, which shows the same result again (no re-entry).
    cancel = re.search(r'href="([^"]+)" data-carry-cancel', form).group(1).replace("&amp;", "&")
    assert cancel == f"/calculators/footing?carry={token}"
    restore = d.get(cancel)
    assert "Showing your result again" in restore
    for name, value in (("footing_length", "120"), ("footing_length", "40"), ("waste_percent", "5")):
        assert f'name="{name}" value="{value}"' in restore
    action = re.search(r'action="([^"]+)"', restore).group(1).replace("&amp;", "&")
    shown = d.post(action, data=FOOTING_FORM, status=200).get_data(as_text=True)
    again = re.search(r'data-calculator-contract>(.*?)</script>', shown, re.S).group(1)
    import json

    assert json.loads(again)["quantities"] == payload["quantities"] and "Your result is back" in shown
    assert Project.query.count() == 0 and ProjectCalculation.query.count() == 0  # nothing was created
    # Now create the project: the result is on it, waiting for its stage, with every entry kept.
    project, location = d.new_project("Rivera Garage (synthetic)", "GARAGE_OUTBUILDING", "SELECTED_PORTIONS", carry=token)
    assert location.endswith(f"/projects/{project.id}/guided/scope")
    record = ProjectCalculation.query.filter_by(project_id=project.id).one()
    assert record.payload == payload and record.source == "NEW_PROJECT"
    # Attaching the same carry again (back button, double press) never makes a second record.
    from app.models.guided_estimating import CalculatorResultCarry
    from app.services.calculator_projects import attach_carry

    attach_carry(CalculatorResultCarry.query.filter_by(token=token).one(), project)
    assert ProjectCalculation.query.filter_by(project_id=project.id).count() == 1
    scope = {"site_prep": "NA", "excavation": "SUBCONTRACTED", "footings_foundation": "INTERNAL", "framing": "INTERNAL",
             "roofing": "SUBCONTRACTED", "windows_doors": "INTERNAL", "garage_door": "SUBCONTRACTED",
             "siding": "SUBCONTRACTED", "electrical": "SUBCONTRACTED", "final_cleanup": "INTERNAL"}
    d.scope(project, scope, action="finalize")
    workflow = d.get(f"/projects/{project.id}/guided")
    assert "Calculations waiting for a stage" in workflow
    page = d.get(f"/projects/{project.id}/calculations/{record.id}")
    footings = d.stage(project, "footings_foundation")
    assert f'<option value="{footings.id}" selected' in page  # the footing calculator's stage, pre-chosen
    review = d.send_to_review(project, record.id, stage=footings)
    section = G.section_for(footings, G.current_version(G.get_guided(ORG, project.id)))
    d.confirm_quantities(review, {"concrete": "SYN-CONC-YD3"}, section.id)
    lines = G.stage_lines(footings)
    assert len(lines) == 1 and str(lines[0].quantity.normalize()) == payload["quantities"][0]["quantity"]


def test_cancelling_project_selection_leaves_the_result_and_creates_nothing(env):
    """Choosing no project (or closing the choice) saves nothing; the link button needs a project and a result."""
    application, d, _ben = env
    _build_new_home(d)
    before = ProjectCalculation.query.count()
    payload, html = d.calculator_result("footing", FOOTING_FORM)
    assert "data-link-button disabled" in html  # nothing can be sent until a project is chosen
    response = d.http.post("/calculators/link-project", json={"calculator": "footing", "project_id": None,
                                                                 "summary": "x", "result_text": "y", "payload": payload})
    assert response.status_code == 400 and ProjectCalculation.query.count() == before


# ======================================================================================= roles and isolation
def test_field_only_crew_can_calculate_but_not_create_projects_or_touch_estimates(env):
    application, d, ben = env
    project = _build_new_home(d)
    kevin = _field_only_kevin(application, ben)
    page = kevin.get("/useful-calculators/footing")
    assert "data-result-options" not in page and "Create New Project" not in page
    result = kevin.post("/useful-calculators/footing", data=FOOTING_FORM, status=200).get_data(as_text=True)
    assert "data-result-options" not in result and "cc-result" in result  # the result, alone
    for url in (f"/projects/{project.id}/guided", "/estimating/start", "/projects/new",
                f"/projects/{project.id}/guided/internal-cost", f"/projects/{project.id}/guided/pricing"):
        response = kevin.http.get(url)
        assert response.status_code == 302 and response.headers["Location"].endswith("/field/today"), url
    payload = {"calculator": "footing", "project_id": project.id, "summary": "x", "result_text": "y"}
    assert kevin.http.post("/calculators/link-project", json=payload).status_code == 403
    assert kevin.http.post("/calculators/carry", json=payload).status_code == 403
    assert kevin.http.post(f"/projects/{project.id}/guided/scope", data={"action": "save"}).status_code == 403
    stage = d.stage(project, "windows_doors")
    assert kevin.http.post(f"/projects/{project.id}/guided/stages/{stage.id}/add_cost",
                           data={"kind": "material", "description": "x", "quantity": "1", "unit_cost": "1"}).status_code == 403
    assert ProjectCalculation.query.count() == 0 and not G.stage_lines(stage)


def test_organization_isolation(env):
    application, d, _ben = env
    project = _build_new_home(d)
    other = _other_company(application)
    for url in (f"/projects/{project.id}/guided", f"/projects/{project.id}/guided/scope",
                f"/projects/{project.id}/guided/internal-cost", f"/projects/{project.id}/guided/internal-cost.pdf",
                f"/calculators/project-stages/{project.id}"):
        assert other.http.get(url).status_code == 404, url
    payload, _ = d.calculator_result("footing", FOOTING_FORM)
    body = {"calculator": "footing", "project_id": project.id, "summary": "x", "result_text": "y", "payload": payload}
    assert other.http.post("/calculators/link-project", json=body).status_code == 404
    assert project.name not in other.get("/calculators/footing") and project.name not in other.get("/estimating/start")
    # A stage of this company cannot be used on the other company's project, nor a carry token by someone else.
    stage = d.stage(project, "footings_foundation")
    other_client = __import__("app.models", fromlist=["Client"]).Client(name="Their client", organization_id="ORG-GUIDED-OTHER")
    db.session.add(other_client)
    db.session.flush()
    theirs = Project(name="Their job", client_id=other_client.id, organization_id="ORG-GUIDED-OTHER", status="Estimating")
    db.session.add(theirs)
    db.session.commit()
    body = dict(body, project_id=theirs.id, stage_id=stage.id)
    assert other.http.post("/calculators/link-project", json=body).status_code == 404
    carry = d.http.post("/calculators/carry", json={"calculator": "footing", "summary": "s", "result_text": "r",
                                                     "payload": payload, "return_path": "/calculators/footing"}).get_json()
    assert "Bringing your" not in other.get(carry["url"])


# ======================================================================================= a second project type
def test_garage_outbuilding_selected_portions_with_mixed_framing_counted_once(env):
    application, d, _ben = env
    project, _ = d.new_project("Rivera Garage (synthetic)", "GARAGE_OUTBUILDING", "SELECTED_PORTIONS")
    guided = G.get_guided(ORG, project.id)
    keys = [s.stage_key for s in guided.top_stages]
    assert keys == ["site_prep", "excavation", "footings_foundation", "framing", "roofing", "windows_doors",
                    "garage_door", "siding", "electrical", "final_cleanup"]
    framing_parts = {"framing.floor_framing": "NA", "framing.wall_framing": "INTERNAL", "framing.roof_framing": "INTERNAL",
                     "framing.sheathing": "INTERNAL", "framing.connectors": "INTERNAL", "framing.framing_labour": "SUBCONTRACTED"}
    scope = {"site_prep": "NA", "excavation": "SUBCONTRACTED", "footings_foundation": "INTERNAL", "roofing": "SUBCONTRACTED",
             "windows_doors": "INTERNAL", "garage_door": "SUBCONTRACTED", "siding": "SUBCONTRACTED", "electrical": "NA",
             "final_cleanup": "INTERNAL"}
    d.scope(project, dict(scope, **framing_parts), split=["framing"], action="finalize",
            na_reasons={"site_prep": "Owner clears the lot", "electrical": "Owner's electrician"})
    guided = G.get_guided(ORG, project.id)
    assert guided.scope_status == "FINALIZED" and "Garage door" in [s.display_name for s in guided.top_stages]
    # Our materials, the subcontractor's installation: each cost once.
    wall = d.stage(project, "framing.wall_framing")
    _framing(d, project, wall)
    d.action(project, wall, "routing")
    stud_line = next(l for l in G.stage_lines(wall) if l.cost_item_id)
    from app.services.estimate_scope_delivery import get_scope_delivery_for_line

    routing = get_scope_delivery_for_line(stud_line)
    assert (routing.material_procurement, routing.labour_delivery, routing.status) == ("CONTRACTOR_PURCHASED", "SUBCONTRACT", "CONFIRMED")
    _complete(d, project, wall)
    labour_part = d.stage(project, "framing.framing_labour")
    page = d.get(f"/projects/{project.id}/guided/stages/{labour_part.id}")
    assert "Construction model takeoff and framing quote request" in page and "Compare supplier quotes" in page
    _quote(d, project, labour_part, reference="FR-LAB-2", amount="7600", name="Square Frame Crew (synthetic)", code="SQUARE")
    _complete(d, project, labour_part)
    doc = G.internal_cost_document(G.get_guided(ORG, project.id))
    framing_rows = [st for st in doc["stages"] if st["stage"].parent and st["stage"].parent.stage_key == "framing"]
    wall_doc = next(st for st in framing_rows if st["stage"].stage_key == "framing.wall_framing")
    labour_doc = next(st for st in framing_rows if st["stage"].stage_key == "framing.framing_labour")
    assert {l["bucket"] for l in wall_doc["lines"]} == {"material"}
    assert [l["bucket"] for l in labour_doc["lines"]] == ["subcontract"] and labour_doc["total"] == Decimal("7600.00")
    from app.services.estimate_output import version_direct_cost

    assert doc["direct_cost"] == version_direct_cost(G.current_version(G.get_guided(ORG, project.id)))
    workflow = G.workflow_view(G.get_guided(ORG, project.id))
    framing_row = next(r for r in workflow["rows"] if r["stage"].stage_key == "framing")
    assert framing_row["responsibility_label"] == "Mixed (by part)" and framing_row["status"] == "IN_PROGRESS"
    na = next(r for r in workflow["rows"] if r["stage"].stage_key == "site_prep")
    assert na["status"] == "EXCLUDED" and na["stage"].na_reason == "Owner clears the lot"


def test_a_subcontractor_template_leaves_out_the_general_contractors_own_stages(env):
    application, d, _ben = env
    project, _ = d.new_project("Foundation sub job (synthetic)", "FOUNDATION_ONLY", "SUBCONTRACTOR")
    keys = [s.stage_key for s in G.get_guided(ORG, project.id).top_stages]
    assert keys == ["excavation", "footings_foundation"]  # site preparation and final cleanup can be added


def test_existing_project_selection_starts_one_guided_estimate_only(env):
    application, d, _ben = env
    existing, estimate = _existing_job()
    start = d.get("/estimating/start")
    assert existing.name in start and "Start the estimate" in start
    d.post(f"/projects/{existing.id}/guided/start", data={"project_type": "ADDITION_RENOVATION", "contractor_role": "GENERAL_CONTRACTOR"})
    d.post(f"/projects/{existing.id}/guided/start", data={"project_type": "NEW_HOME", "contractor_role": "SUBCONTRACTOR"})
    assert GuidedEstimate.query.filter_by(project_id=existing.id).count() == 1
    guided = G.get_guided(ORG, existing.id)
    # Since 28 Oct 2026 a new scope is the selected work: nothing is listed until the work is chosen.
    assert guided.project_type == "ADDITION_RENOVATION" and guided.top_stages == []
    d.post(f"/projects/{existing.id}/guided/scope", data={"action": "add_work", "work": ["work_siding"]})
    guided = G.get_guided(ORG, existing.id)
    assert [s.stage_key for s in guided.top_stages] == ["work_siding"]
    assert guided.estimate_id != estimate.id  # its own estimate; the existing one is untouched
    assert Project.query.filter_by(name=existing.name).count() == 1


def test_the_migration_adds_exactly_the_guided_tables_and_columns(tmp_path):
    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from pathlib import Path

    from app.models import guided_estimating as models
    from app.models.project_calculation import ProjectCalculation as PC

    root = Path(__file__).resolve().parents[1]
    uri = f"sqlite:///{tmp_path}/m.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": uri})
    ctx = application.app_context()
    ctx.push()
    cfg = Config(str(root / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", uri)
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == ["q4c7l2n8t3a6"] and script.get_revision("g5e7c2a9d1b4").down_revision == "u7b3d9f2a4c6"
    command.upgrade(cfg, "u7b3d9f2a4c6")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:  # an existing linked result, made before this release (SQLite: no FK check here)
        conn.execute(sa.text("INSERT INTO project_calculations (organization_id, project_id, calculator, summary, entered, "
                             "result_text, actor_display_name, created_at) VALUES ('ORG-M', 1, 'concrete', 's', '[]', 'r', 'Ben', '2026-10-22')"))
    inspector = sa.inspect(engine)
    before = {t: [(c["name"], str(c["type"])) for c in inspector.get_columns(t)] for t in inspector.get_table_names()}
    before_indexes = {t: sorted(i["name"] for i in inspector.get_indexes(t)) for t in inspector.get_table_names()}
    with engine.connect() as conn:
        row_before = conn.execute(sa.text("SELECT * FROM project_calculations")).fetchall()
    engine.dispose()
    command.upgrade(cfg, "g5e7c2a9d1b4")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    after = {t: [(c["name"], str(c["type"])) for c in inspector.get_columns(t)] for t in inspector.get_table_names()}
    assert set(after) - set(before) == {"guided_estimates", "guided_estimate_stages", "guided_estimate_events",
                                        "calculator_result_carries"}
    for table in before:
        if table == "project_calculations":
            assert after[table][:len(before[table])] == before[table]
            added = [name for name, _t in after[table][len(before[table]):]]
            assert added == ["result_id", "engine_id", "engine_version", "payload", "source", "guided_stage_id",
                             "review_status", "estimate_version_id", "calculation_result_intake_id",
                             "sent_to_review_at", "sent_to_review_by"]
            assert all(c["nullable"] for c in inspector.get_columns(table) if c["name"] in added)
        else:
            assert after[table] == before[table], table
        assert sorted(i["name"] for i in inspector.get_indexes(table)) == before_indexes[table], table
    for model in (models.GuidedEstimate, models.GuidedEstimateStage, models.GuidedEstimateEvent,
                  models.CalculatorResultCarry, PC):
        table = model.__tablename__
        assert {c["name"] for c in inspector.get_columns(table)} == set(model.__table__.columns.keys()), table
    with engine.connect() as conn:
        row_after = conn.execute(sa.text("SELECT * FROM project_calculations")).fetchall()
    assert tuple(row_after[0])[:len(row_before[0])] == tuple(row_before[0])
    assert all(v is None for v in tuple(row_after[0])[len(row_before[0]):])
    engine.dispose()
    # Downgrade: refused while a row uses the new columns; allowed when they are empty.
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("UPDATE project_calculations SET review_status = 'AWAITING_REVIEW'"))
    engine.dispose()
    with pytest.raises(RuntimeError, match="Downgrade refused"):
        command.downgrade(cfg, "u7b3d9f2a4c6")
    engine = sa.create_engine(uri)
    with engine.begin() as conn:
        conn.execute(sa.text("UPDATE project_calculations SET review_status = NULL"))
    engine.dispose()
    command.downgrade(cfg, "u7b3d9f2a4c6")
    engine = sa.create_engine(uri)
    inspector = sa.inspect(engine)
    assert {t: [(c["name"], str(c["type"])) for c in inspector.get_columns(t)] for t in inspector.get_table_names()} == before
    with engine.connect() as conn:
        assert conn.execute(sa.text("SELECT * FROM project_calculations")).fetchall() == row_before
    engine.dispose()
    ctx.pop()

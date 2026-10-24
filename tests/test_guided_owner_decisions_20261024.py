"""Joel's v1rel9 owner decisions for Guided Estimating (approved 24 Oct 2026). Synthetic data only.

1. Allowances: a person with costing-approval authority approves a documented allowance, with a reason; who, when
   and why are kept in the stage history. An explicit no-cost decision for included work needs the instance owner
   or a System Administrator: an ordinary costing approver is refused with a plain message, and Field-only crew
   never reach the page.
2. A guided proposal is not issued while any included stage has unresolved costing, quotation or scope
   requirements: costing missing, a quote waiting or selected but not used, a stage changed after completion, or
   the scope undecided.
4. Stair materials: the Stairs part brings the stair calculator (a design check kept on the project as a record)
   and the governed manual material-cost lines. Nothing invents a stair material list.
"""

from __future__ import annotations

import pytest

from app import db
from app.models.guided_estimating import GuidedEstimateEvent, GuidedEstimateStage
from app.models.user import UserMembership
from app.services import guided_estimating as G
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.auth_fixtures import ensure_office_user
from tests.guided_support import NEW_HOME_SCOPE
from tests.test_guided_estimating import (  # noqa: F401
    _build_new_home,
    _complete,
    _cost_new_home,
    _field_only_kevin,
    _login,
    _make_owner,
    _quote,
    env,
)

OLIVIA = ("olivia.guided@example.invalid", "olivia-guided-password", "Olivia Office (synthetic)")
SAM = ("sam.guided@example.invalid", "sam-guided-password", "Sam Sysadmin (synthetic)")
REASON = "The owner buys and installs the appliances"


def _added_stage(d, project, name):
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "add_stage", "custom_name": name})
    guided = G.get_guided(ORG, project.id)
    added = next(st for st in guided.top_stages if st.is_custom and st.display_name == name)
    d.scope(project, dict(NEW_HOME_SCOPE, **{added.stage_key: "INTERNAL"}), action="finalize")
    return added


def _stage(stage):
    db.session.expire_all()
    return db.session.get(GuidedEstimateStage, stage.id)


# ------------------------------------------------------------------------------------------------ decision 1
def test_only_the_owner_or_a_system_administrator_decides_included_work_has_no_cost(env):
    application, d, ben = env
    project = _build_new_home(d)
    _make_owner(ben)
    olivia = ensure_office_user(email=OLIVIA[0], password=OLIVIA[1], display_name=OLIVIA[2])
    sam = ensure_office_user(email=SAM[0], password=SAM[1], display_name=SAM[2])
    db.session.commit()
    from app.services.instance_authority import appoint_system_administrator

    appoint_system_administrator(ORG, UserMembership.query.filter_by(user_id=sam.id).one().id, ben)
    db.session.commit()

    # An ordinary costing approver: the allowance is theirs to approve, the no-cost decision is not.
    od = _login(application, OLIVIA)
    hvac = d.stage(project, "hvac")
    page = od.get(f"/projects/{project.id}/guided/stages/{hvac.id}")
    assert "data-approve-allowance" in page and "data-authorize-zero" not in page
    assert "Only the owner or a System Administrator can decide that included work has no cost" in page
    appliances = _added_stage(d, project, "Owner-supplied appliances")
    od.action(project, appliances, "zero_cost", {"reason": REASON})
    assert any(G.ZERO_COST_REFUSED in m for m in od.flashes())
    row = _stage(appliances)
    assert row.zero_cost_authorized_at is None and row.zero_cost_authorized_by is None
    assert not GuidedEstimateEvent.query.filter_by(stage_id=row.id, event="ZERO_COST_AUTHORIZED").count()
    _complete(od, project, row, expect_ok=False)
    # The service refuses too, whatever page sent it.
    with pytest.raises(G.GuidedEstimatingError, match="Only the owner or a System Administrator"):
        G.authorize_zero_cost(G.get_guided(ORG, project.id), row, reason=REASON, approver=OLIVIA[2],
                              user_id=olivia.id)
    with pytest.raises(G.GuidedEstimatingError, match="Only the owner or a System Administrator"):
        G.authorize_zero_cost(G.get_guided(ORG, project.id), row, reason=REASON, approver="Someone", user_id=None)

    # Olivia approves the HVAC allowance: a reason is required, and who/when/why go into the stage history.
    od.action(project, hvac, "allowance", {"amount": "16000"})
    assert any(G.ALLOWANCE_REASON_REQUIRED in m for m in od.flashes())
    assert _stage(hvac).allowance_approved_at is None
    od.action(project, hvac, "allowance", {"amount": "16000", "description": "HVAC allowance",
                                            "reason": "The HVAC quote is still to come"})
    row = _stage(hvac)
    assert row.allowance_approved_by == OLIVIA[2] and row.allowance_approved_at is not None
    event = G.allowance_record(row)
    assert event.actor_display_name == OLIVIA[2] and event.user_id == olivia.id and event.created_at is not None
    assert event.to_value == "16000.00" and "Reason: The HVAC quote is still to come" in event.detail
    page = od.get(f"/projects/{project.id}/guided/stages/{hvac.id}")
    assert "approved by Olivia Office (synthetic) on" in page and "Reason: The HVAC quote is still to come" in page
    _complete(od, project, row)
    assert _stage(hvac).completion_basis == "APPROVED_ALLOWANCE"

    # A System Administrator (the delegated equivalent authority) may decide it.
    sd = _login(application, SAM)
    assert "data-authorize-zero" in sd.get(f"/projects/{project.id}/guided/stages/{appliances.id}")
    sd.action(project, appliances, "zero_cost", {"reason": REASON})
    row = _stage(appliances)
    assert row.zero_cost_authorized_by == SAM[2] and row.zero_cost_reason == REASON
    event = GuidedEstimateEvent.query.filter_by(stage_id=row.id, event="ZERO_COST_AUTHORIZED").one()
    assert event.user_id == sam.id and event.detail == REASON
    _complete(sd, project, row)

    # The owner may decide it.
    garage = _added_stage(d, project, "Owner-supplied shed kit")
    d.action(project, garage, "zero_cost", {"reason": "The owner supplies the shed kit"})
    assert _stage(garage).zero_cost_authorized_by == ben.display_name
    _complete(d, project, garage)


def test_field_only_crew_can_neither_approve_an_allowance_nor_decide_no_cost(env):
    application, d, ben = env
    project = _build_new_home(d)
    kd = _field_only_kevin(application, ben)
    hvac = d.stage(project, "hvac")
    for action, data in (("allowance", {"amount": "500", "reason": "Crew guess"}), ("zero_cost", {"reason": REASON})):
        response = kd.http.post(f"/projects/{project.id}/guided/stages/{hvac.id}/{action}", data=data)
        assert response.status_code in (302, 403, 404)
        assert "/guided/stages/" not in (response.headers.get("Location") or "")
    row = _stage(hvac)
    assert row.allowance_approved_at is None and row.zero_cost_authorized_at is None


# ------------------------------------------------------------------------------------------------ decision 2
def _issue_refused(proposal, needle):
    from app.services.proposals import ProposalServiceError, proposal_issue_blockers, update_proposal_status

    blockers = proposal_issue_blockers(proposal.estimate_version)
    assert any(b.startswith("Guided estimate:") and needle in b for b in blockers), blockers
    with pytest.raises(ProposalServiceError, match="Guided estimate:"):
        update_proposal_status(proposal, "Issued")
    db.session.rollback()


def test_the_proposal_waits_for_costing_quotation_and_scope_on_every_included_stage(env):
    application, d, ben = env
    from app.services.proposals import create_proposal, create_proposal_template
    from tests.proposal_issue_support import approve_for_issue

    project = _build_new_home(d)
    s = _cost_new_home(d, project, skip=("hvac",))
    guided = G.get_guided(ORG, project.id)
    version = G.current_version(guided)
    approve_for_issue(version)
    template = create_proposal_template(name="Synthetic", organization_id=ORG, is_default=True)
    proposal = create_proposal(estimate=version.estimate, version=version, template=template, organization_id=ORG)

    # Costing missing.
    _issue_refused(proposal, "HVAC is Not Started")
    # Quotation waiting.
    d.action(project, s["hvac"], "subcontract", {"scope_description": "HVAC: supply and install"})
    d.action(project, s["hvac"], "request_quote")
    assert G.effective_status(_stage(s["hvac"])) == "WAITING_FOR_QUOTE"
    _issue_refused(proposal, "HVAC is Waiting for Quote")
    # A quote recorded and selected but not used on the line is not a confirmed cost.
    _quote(d, project, s["hvac"], reference="HV-2", amount="16400", name="Cool Air (synthetic)", code="COOL",
           apply=False)
    assert G.effective_status(_stage(s["hvac"])) == "NEEDS_REVIEW"
    _issue_refused(proposal, "HVAC is Needs Review")
    # Used on the line and completed: the guided requirements are met.
    line = next(l for l in G.stage_lines(_stage(s["hvac"])) if l.code == G.SUBCONTRACT_CODE)
    here = f"/projects/{project.id}/guided/stages/{s['hvac'].id}"
    d.post(f"/projects/{project.id}/scope-delivery/lines/{line.id}/suggested-cost/apply",
           data={"version_id": version.id, "estimate_id": version.estimate_id, "kind": "labour", "return_to": here})
    _complete(d, project, s["hvac"])
    assert G.guided_blockers(G.get_guided(ORG, project.id)) == []
    # A completed stage changed afterwards needs review again.
    d.action(project, s["final_cleanup"], "add_cost", {"kind": "delivery", "description": "Extra bin", "quantity": "1",
                                                        "unit": "bin", "unit_cost": "650"})
    _issue_refused(proposal, "Final cleanup is Needs Review")
    d.action(project, s["final_cleanup"], "routing")
    _complete(d, project, s["final_cleanup"])
    assert G.guided_blockers(G.get_guided(ORG, project.id)) == []
    # Scope undecided: a new stage with no responsibility makes the scope a draft again.
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "add_stage", "custom_name": "Landscaping"})
    assert G.get_guided(ORG, project.id).scope_status == "DRAFT"
    _issue_refused(proposal, "Finalize the construction scope")


# ------------------------------------------------------------------------------------------------ decision 4
def test_stairs_use_governed_manual_material_lines_and_no_invented_stair_list(env):
    application, d, _ben = env
    project, _location = d.new_project("Stair New Home (synthetic)", "NEW_HOME", "GENERAL_CONTRACTOR")
    parts = {f"interior_finishes.{p.key}": "INTERNAL" for p in G.STAGES["interior_finishes"].parts}
    d.scope(project, dict(NEW_HOME_SCOPE, **parts), split=["interior_finishes"], action="finalize")
    stairs = d.stage(project, "interior_finishes.stairs_railings")
    tools = G.tools_for(stairs)
    assert [t.target for t in tools if t.kind == "calculator"] == ["stairs"]
    assert any(t.kind == "manual" for t in tools) and G.tool_limitation(stairs) == ""
    from app.services.calculator_contracts import RECORD_ONLY_REASON, REVIEWABLE

    assert "stairs" not in REVIEWABLE and "enter the stair materials as lines" in RECORD_ONLY_REASON["stairs"]
    page = d.get(f"/projects/{project.id}/guided/stages/{stairs.id}")
    assert "Stair calculator" in page and "enter the stair materials as lines" in page

    # The stair result is kept on the project as a record: it has nothing to send to the estimate review and adds
    # no lines.
    response = d.http.post("/calculators/link-project", json={
        "calculator": "stairs", "project_id": project.id, "summary": "Main stair: 14 risers (synthetic)",
        "entered": [{"label": "Total rise", "value": "105 in"}], "result_text": "14 risers at 7.5 in",
        "payload": None, "stage_id": stairs.id})
    data = response.get_json()
    assert data["ok"] and data["review_url"] is None
    d.post(f"/projects/{project.id}/calculations/{data['calculation_id']}/send", data={})
    assert any("no quantities for the estimate review" in m for m in d.flashes())
    assert G.stage_lines(_stage(stairs)) == []

    # The stair materials are governed manual material-cost lines that a person enters.
    d.action(project, stairs, "add_cost", {"kind": "material", "description": "Stair stringers 2x12 (synthetic)",
                                           "quantity": "3", "unit": "ea", "unit_cost": "48.50"})
    lines = G.stage_lines(_stage(stairs))
    assert [(l.description, l.code, l.line_type) for l in lines] == [
        ("Stair stringers 2x12 (synthetic)", "GE-MATERIAL", "Custom")]
    assert lines[0].notes.startswith("Manual entry by ")
    version = G.current_version(G.get_guided(ORG, project.id))
    all_lines = [l for section in version.sections for l in section.line_items]
    assert [l.description for l in all_lines] == ["Stair stringers 2x12 (synthetic)"]

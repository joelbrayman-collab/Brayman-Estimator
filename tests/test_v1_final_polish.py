"""V1 final bounded polish (Joel, 16 Oct 2026): one primary next action on the project hub and the
estimate, every existing action kept, clearer estimate totals, a card for the Projects register and
its empty state, and phone layouts that do not widen the page. No behaviour changes."""

from pathlib import Path

from app import db
from app.services.estimate_builder import add_manual_line, create_section
from app.services.estimates import lock_version
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.proposal_issue_support import approve_for_issue
from tests.test_approved_contractor_cost_snapshot import _estimate, app  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]


def _signed_in(app):
    ensure_office_user()
    db.session.commit()
    client = app.test_client()
    login_office_user(client)
    return client


def _priced_version(number):
    estimate = _estimate(number)
    version = estimate.current_version
    section = create_section(version, name="Work")
    add_manual_line(section, line_type="Custom", description="Footing concrete", quantity=3, unit="yd3", unit_cost=200)
    return estimate, version


def _actions(page):
    start = page.index('class="estimate-actions"')
    return page[start:page.index("</div>", start)]


def test_project_hub_has_one_primary_action_and_keeps_every_action(app):
    estimate = _estimate("POLISH-HUB")
    client = _signed_in(app)
    page = client.get(f"/projects/{estimate.project_id}").get_data(as_text=True)
    primary = page[page.index('class="action-group action-group-primary"'):]
    primary = primary[:primary.index("</div>")]
    assert primary.count('class="button"') == 1 and "Continue setup" in primary
    for label in ("Drawings", "Scope of work", "Enter construction information", "New Change Order", "Print"):
        assert f">{label}</a>" in page, label
        link = page[:page.index(f">{label}</a>")]
        assert "button-secondary" in link[link.rindex("<a "):], label


def test_estimate_names_costing_as_the_next_step_before_approval(app):
    estimate, version = _priced_version("POLISH-EST-1")
    client = _signed_in(app)
    page = client.get(f"/estimates/{estimate.id}/versions/{version.id}").get_data(as_text=True)
    actions = _actions(page)
    for label in ("Create Proposal", "Internal Detailed Cost Breakdown", "Edit Estimate", "Create Change Order", "Lock"):
        assert label in actions, label
    before = actions[:actions.index(">Create Proposal</a>")]
    assert "button-secondary" in before[before.rindex("<a "):]  # not yet the primary action
    assert 'class="estimate-next-step">Next step: review and approve the costing in <a href="#costing-review">' in page
    assert 'id="estimate-pricing"' in page


def test_once_costing_and_pricing_are_approved_create_proposal_is_the_primary_action(app):
    estimate, version = _priced_version("POLISH-EST-2")
    approve_for_issue(version)
    client = _signed_in(app)
    page = client.get(f"/estimates/{estimate.id}/versions/{version.id}").get_data(as_text=True)
    actions = _actions(page)
    # Joel, 17 Oct 2026: signing off the estimate is the primary action; it builds the proposal.
    assert '<button type="submit" class="button is-primary">Sign off estimate</button>' in actions
    assert actions.index("is-primary") < actions.index("Create Proposal")
    assert "Next step: sign off the estimate." in page
    totals = page[page.index('class="estimate-totals"'):]
    assert 'class="estimate-total is-grand"' in totals and "Customer total" in totals


def test_a_locked_version_names_no_next_step_and_keeps_unlock(app):
    estimate, version = _priced_version("POLISH-EST-3")
    lock_version(version)
    client = _signed_in(app)
    page = client.get(f"/estimates/{estimate.id}/versions/{version.id}").get_data(as_text=True)
    assert 'class="estimate-next-step"' not in page
    assert ">Unlock</button>" in _actions(page)


def test_projects_empty_state_is_a_card_and_start_new_project_stays(app):
    client = _signed_in(app)
    page = client.get("/projects/?view=closed").get_data(as_text=True)
    assert 'class="register-card projects-empty"' in page and 'class="projects-empty-title"' in page
    assert 'class="home-start" href="/projects/new"' in page


def test_phone_rules_keep_the_page_from_widening_and_touch_targets_at_44px():
    css = (ROOT / "app" / "static" / "css" / "v1-refinement.css").read_text()
    phone = css[css.index("Phones: wide tables scroll inside their own box"):]
    assert "overflow-x: auto" in phone and "min-height: 44px" in phone
    assert "Grid and flex children may shrink" in css

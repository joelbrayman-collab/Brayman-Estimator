"""Guided Tasks (Task-First UX, Slice C, 1 Nov 2026; docs/ux/task-first-ux-audit-2026-10-31.md sections 4 and 7.1).

Set Up This Project, Price This Job and Review This Estimate: one screen each, ONE primary action, details closed;
everything assembled from the existing pages and services. Review This Estimate's ONE Approve is the existing Gate 1
sign-off (the costing check and the pricing are run first by the same services, and nothing is approved if any of
them refuses or the figures changed). The three contractor wizards are retired as linear runs: their start links
open the Guided Task; a run started before keeps working. Field Today keeps the work list first, one primary action
and the rest closed. The Supplier Hub lists the documents waiting for the store's CaliSIGN signature, from the
provider registry. Synthetic data only.
"""

from __future__ import annotations

import re
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import EstimateVersion, Project, Proposal
from app.models.estimate_approval import EstimateApproval
from app.models.wizard import WizardRun
from app.services import guided_estimating as G
from app.services import guided_tasks as T
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.guided_support import COMMERCIAL, Driver, client as synthetic_client, seed_company

BEN = ("ben.tasks@example.invalid", "ben-tasks-password", "Ben Brayman (synthetic)")


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


def _main(page: str) -> str:
    return page.split("<main", 1)[1] if "<main" in page else page


def _primaries(page: str) -> int:
    """Primary actions on the screen: the Task Screen's one primary (link or button)."""
    return len(re.findall(r'class="ts-primary', _main(page)))


SITE = {"street": "12 Synthetic Lane", "municipality": "Merrickville", "province_state": "Ontario",
        "postal_zip": "K0G 1N0", "country": "Canada"}


def _project(d, name="Guided synthetic deck"):
    d.post("/projects/new", data=dict(COMMERCIAL, **SITE, name=name, client_id=synthetic_client().id))
    project = Project.query.filter_by(organization_id=ORG, name=name).one()
    from app.services.project_drawing_requirement import set_project_drawing_requirement

    set_project_drawing_requirement(organization_id=ORG, project_id=project.id, requirement="NOT_REQUIRED")
    return project


def _template():
    from app.services.proposals import create_proposal_template

    create_proposal_template(name="Synthetic standard", organization_id=ORG, is_default=True)


def _priced_job(d, name="Guided synthetic siding"):
    """One work item (siding), priced with a material line, complete: ready for Review This Estimate."""
    project = _project(d, name)
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "add_work", "work": ["work_siding"]})
    row = G.get_guided(ORG, project.id).top_stages[0]
    d.post(f"/projects/{project.id}/guided/stages/{row.id}/add_cost",
           data={"kind": "material", "description": "Siding (synthetic)", "quantity": "10", "unit": "sq",
                 "unit_cost": "150"})
    d.post(f"/projects/{project.id}/guided/stages/{row.id}/routing")
    d.post(f"/projects/{project.id}/guided/stages/{row.id}/complete_next")
    db.session.expire_all()
    return project, G.get_guided(ORG, project.id)


# ================================================================================ the band and the retired wizards
def test_home_start_something_offers_the_three_guided_tasks_and_no_wizard_fork(env):
    _app, d, _ben = env
    home = d.get("/")
    band = home.split("data-wizard-home", 1)[1].split("</section>", 1)[0]
    for key, name in (("set_up", "Set Up This Project"), ("price", "Price This Job"),
                      ("review", "Review This Estimate")):
        assert f'data-guided-task="{key}"' in band and name in band, key
    assert "Start something" in home
    # The "Start Guided Wizard / Continue Manually" fork is gone (audit 4.5): one way to do each task.
    assert "Continue manually" not in band and "What are Wizards?" not in band
    assert 'href="/projects/new"' in band and 'href="/estimating/start"' in band
    assert 'href="/tasks/review-this-estimate"' in band


@pytest.mark.parametrize("method", ["get", "post"])
def test_a_retired_wizard_start_opens_the_guided_task_and_starts_no_run(env, method):
    _app, d, _ben = env
    project = _project(d)
    send = getattr(d.http, method)
    assert send("/wizards/NEW_PROJECT/start").headers["Location"].endswith("/projects/new")
    assert send(f"/wizards/GUIDED_ESTIMATING/start?project_id={project.id}").headers["Location"].endswith(
        f"/projects/{project.id}/guided")
    assert send("/wizards/GUIDED_ESTIMATING/start").headers["Location"].endswith("/estimating/start")
    assert send(f"/wizards/MANAGE_PROJECT/start?project_id={project.id}").headers["Location"].endswith(
        f"/projects/{project.id}")
    assert WizardRun.query.count() == 0


def test_a_run_started_before_the_retirement_can_still_be_resumed_and_closed(env):
    from app.wizards import service as S

    _app, d, ben = env
    run = S.start_contractor_run("NEW_PROJECT", organization_id=ORG, actor=BEN[2], user_id=ben.id)
    response = d.http.get(f"/wizards/run/{run.id}")
    assert response.status_code == 302 and f"/wizards/run/{run.id}/step/" in response.headers["Location"]
    d.post(f"/wizards/run/{run.id}/end", data={"reason": "Done another way"})
    assert db.session.get(WizardRun, run.id).status == "ENDED"


def test_the_wizard_step_ledger_counts_the_audit_steps():
    counts = T.step_counts()
    assert {k: v["steps"] for k, v in counts.items()} == {"NEW_PROJECT": 5, "GUIDED_ESTIMATING": 15,
                                                         "MANAGE_PROJECT": 12}
    retired = sum(v["A"] + v["R"] + v["M"] for v in counts.values())
    kept = sum(v["K"] for v in counts.values())
    assert (retired, kept) == (21, 11)
    # The audit's per-wizard classification (section 4.5): A/R/M per wizard.
    assert (counts["NEW_PROJECT"]["R"], counts["GUIDED_ESTIMATING"]["R"], counts["MANAGE_PROJECT"]["R"]) == (1, 1, 1)


# ================================================================================ Set Up This Project
def test_set_up_this_project_is_one_screen_with_the_software_fields_closed(env):
    _app, d, _ben = env
    synthetic_client()
    page = d.get("/projects/new")
    main = _main(page)
    assert "Set Up This Project" in main and _primaries(page) == 1
    assert "data-set-up-project" in main and "Review" not in re.sub(r"<[^>]+>", " ", main).split()
    settings = main.split('data-ts-section="ts-project-settings"', 1)[1].split("</details>", 1)[0]
    for name in ("status", "project_type", "permit_context_class", "pricing_posture", "execution_risk",
                 "schedule_condition", "site_condition", "estimate_stage", "delivery_model", "justification_reason",
                 "project_lead_user_id"):
        assert f'name="{name}"' in settings, name
    # Closed by default; the human questions are visible.
    assert re.search(r'<details class="ts-details" id="ts-project-settings"[^>]*>', main).group(0).count(" open") == 0
    for name in ("name", "client_id", "guided_project_type", "contractor_role", "street", "plan_start"):
        assert f'name="{name}"' in main.split('data-ts-section="ts-project-settings"', 1)[0], name
    assert "Brayman Project #: assigned automatically" in main
    # The guided estimate starts on its own when the project is saved.
    assert re.search(r'name="start_guided" value="1"[^>]*checked', main)


def test_set_up_fills_the_software_only_fields_and_keeps_the_brayman_number(env):
    _app, d, _ben = env
    customer = synthetic_client()
    d.post("/projects/new", data={"name": "Addition (synthetic)", "client_id": customer.id,
                                   "guided_project_type": "ADDITION_RENOVATION", "contractor_role": "GENERAL_CONTRACTOR",
                                   "start_guided": "1", "street": "1 Synthetic Rd", "municipality": "Merrickville",
                                   "province_state": "Ontario", "country": "Canada"})
    project = Project.query.filter_by(name="Addition (synthetic)").one()
    assert re.fullmatch(r"BC-\d{4}-\d{4}", project.project_number)
    assert project.status == "Lead"
    context = project.current_commercial_context
    assert context.project_type == "Addition"  # from what is being built
    assert (context.pricing_posture, context.execution_risk, context.estimate_stage) == (
        "Competitive", "Normal", "Preliminary")
    assert G.get_guided(ORG, project.id) is not None


def test_set_up_keeps_every_validation(env):
    _app, d, _ben = env
    customer = synthetic_client()
    d.post("/projects/new", data={"name": "", "client_id": customer.id}, status=200)
    d.post("/projects/new", data={"name": "Premium (synthetic)", "client_id": customer.id,
                                   "pricing_posture": "Premium"}, status=200)
    assert Project.query.filter(Project.name.in_(("", "Premium (synthetic)"))).count() == 0
    d.post("/projects/new", data={"name": "Premium (synthetic)", "client_id": customer.id,
                                   "pricing_posture": "Premium", "justification_reason": "Custom millwork"})
    assert Project.query.filter_by(name="Premium (synthetic)").one().current_commercial_context.pricing_posture == "Premium"


def test_set_up_adds_a_new_customer_on_the_same_screen(env):
    from app.models import Client

    _app, d, _ben = env
    d.post("/projects/new", data={"name": "New customer job (synthetic)", "customer_mode": "new",
                                   "new_customer_name": "Riley Synthetic", "new_customer_email": "riley@example.invalid"})
    project = Project.query.filter_by(name="New customer job (synthetic)").one()
    assert project.client.name == "Riley Synthetic" and project.client.email == "riley@example.invalid"
    # A bad customer email refuses the whole thing: no customer and no project.
    d.post("/projects/new", data={"name": "Bad email (synthetic)", "customer_mode": "new",
                                   "new_customer_name": "Sam Synthetic", "new_customer_email": "not-an-email"},
           status=200)
    assert Project.query.filter_by(name="Bad email (synthetic)").count() == 0
    assert Client.query.filter_by(name="Sam Synthetic").count() == 0


def test_set_up_works_when_the_company_has_no_customers_yet(env):
    from app.models import Client

    _app, d, _ben = env
    Client.query.delete()
    db.session.commit()
    page = d.get("/projects/new")
    assert 'name="new_customer_name"' in page and "data-set-up-project" in page


# ================================================================================ Price This Job
def test_price_this_job_lists_the_work_and_opens_the_next_item(env):
    _app, d, _ben = env
    project = _project(d)
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "add_work", "work": ["work_siding", "work_windows"]})
    page = d.get(f"/projects/{project.id}/guided")
    main = _main(page)
    assert "Price This Job" in main and _primaries(page) == 1
    siding = next(r for r in G.get_guided(ORG, project.id).top_stages if r.display_name == "Siding")
    assert f'data-next-step-action>Price Siding</a>' in main
    assert f'href="/projects/{project.id}/guided/stages/{siding.id}"' in main
    # The earlier hooks stay on the screen (the work list, progress, links), the rest is in closed details.
    for hook in ("data-guided-workflow", "data-stage-list", 'data-progress="0/2"', "data-internal-cost-link",
                 "data-pricing-link", "data-add-work-link"):
        assert hook in main, hook
    assert 'data-ts-section="ts-price-details"' in main


def test_price_this_job_points_to_review_when_every_item_is_priced(env):
    _app, d, _ben = env
    project, _guided = _priced_job(d)
    page = d.get(f"/projects/{project.id}/guided")
    assert _primaries(page) == 1
    assert f'href="/projects/{project.id}/guided/pricing" data-next-step-action>Review This Estimate</a>' in page


# ================================================================================ Review This Estimate (Gate 1)
def _approve_form(page):
    form = re.search(r'<form[^>]*data-approve-estimate-form[^>]*>(.*?)</form>', page, re.S)
    assert form, "the Approve form"
    values = dict(re.findall(r'name="(version_id|expected_total)" value="([^"]*)"', form.group(1)))
    return values


def test_review_this_estimate_has_one_approve_with_its_consequence(env):
    _app, d, _ben = env
    _template()
    project, guided = _priced_job(d)
    page = d.get(f"/projects/{project.id}/guided/pricing")
    main = _main(page)
    assert "Review This Estimate" in main and _primaries(page) == 1
    assert "data-approve-estimate" in main
    values = _approve_form(page)
    version = G.current_version(guided)
    assert values["version_id"] == str(version.id)
    total = Decimal(values["expected_total"])
    assert f"${total:,.2f}" in main and "locks" in main  # what approving does, with the figure
    # The two software checks are no longer separate primary buttons; they stay reachable, closed.
    closed = main.split('data-ts-section="ts-approve-steps"', 1)[1].split("</details>", 1)[0]
    assert "data-approve-costing" in closed and "data-apply-pricing" in closed


def test_approve_is_the_gate_1_sign_off_and_builds_the_proposal(env):
    _app, d, ben = env
    _template()
    project, guided = _priced_job(d)
    values = _approve_form(d.get(f"/projects/{project.id}/guided/pricing"))
    response = d.post(f"/projects/{project.id}/guided/approve", data=values)
    db.session.expire_all()
    version = db.session.get(EstimateVersion, int(values["version_id"]))
    approval = EstimateApproval.query.filter_by(estimate_version_id=version.id).one()
    assert approval.approved_by_user_id == ben.id and approval.fingerprint
    assert version.is_locked and version.signed_off_at is not None
    assert version.pricing_snapshot is not None and version.pricing_snapshot.customer_total == Decimal(values["expected_total"])
    proposal = Proposal.query.filter_by(estimate_version_id=version.id).one()
    assert response.headers["Location"].endswith(f"/proposals/{proposal.id}")
    # Gate 1 is immutable: a second press approves nothing and the version is never unlocked.
    d.post(f"/projects/{project.id}/guided/approve", data=values)
    assert any("already approved" in m for m in d.flashes())
    assert EstimateApproval.query.count() == 1
    page = d.get(f"/projects/{project.id}/guided/pricing")
    assert "data-approve-estimate-form" not in page and "data-estimate-approved" in page


def test_approve_refuses_when_the_figures_changed_and_nothing_is_approved(env):
    _app, d, _ben = env
    _template()
    project, guided = _priced_job(d)
    values = _approve_form(d.get(f"/projects/{project.id}/guided/pricing"))
    stale = dict(values, expected_total=str(Decimal(values["expected_total"]) - Decimal("100")))
    d.post(f"/projects/{project.id}/guided/approve", data=stale)
    assert any("Nothing was approved" in m for m in d.flashes())
    db.session.expire_all()
    version = db.session.get(EstimateVersion, int(values["version_id"]))
    assert EstimateApproval.query.count() == 0 and not version.is_locked and version.signed_off_at is None
    # Nothing half-done was kept: no costing approval or pricing from the refused press.
    from app.services.estimate_costing import current_costing_snapshot

    assert current_costing_snapshot(version) is None and version.pricing_snapshot is None


def test_approve_is_not_offered_and_refused_while_work_is_unpriced(env):
    _app, d, _ben = env
    _template()
    project = _project(d)
    d.post(f"/projects/{project.id}/guided/scope", data={"action": "add_work", "work": ["work_siding"]})
    guided = G.get_guided(ORG, project.id)
    page = d.get(f"/projects/{project.id}/guided/pricing")
    assert "data-approve-estimate-form" not in page and "data-review-decisions" in page
    version = G.current_version(guided)
    if version is not None:
        d.post(f"/projects/{project.id}/guided/approve", data={"version_id": version.id, "expected_total": "0.00"})
        assert any("Not ready to approve" in m for m in d.flashes())
    assert EstimateApproval.query.count() == 0


def test_review_list_shows_the_jobs_ready_for_approval(env):
    _app, d, _ben = env
    project, _guided = _priced_job(d)
    page = d.get("/tasks/review-this-estimate")
    assert "Review This Estimate" in page and f'href="/projects/{project.id}/guided/pricing"' in page


# ================================================================================ surfaced from attention / next step
def test_the_project_next_step_and_attention_open_the_guided_tasks(env):
    _app, d, _ben = env
    project, _guided = _priced_job(d)
    hub = d.get(f"/projects/{project.id}")
    step = re.search(r'<section class="ts-next" data-next-step="([a-z]+)".*?</section>', hub, re.S)
    assert step.group(1) == "approve"
    assert f'href="/projects/{project.id}/guided/pricing" data-next-step-action>Review This Estimate</a>' in step.group(0)
    home = d.get("/")
    assert f'/projects/{project.id}/guided/pricing' in home and "Review This Estimate" in home
    other = _project(d, "Unpriced (synthetic)")
    d.post(f"/projects/{other.id}/guided/scope", data={"action": "add_work", "work": ["work_siding"]})
    hub = d.get(f"/projects/{other.id}")
    assert re.search(r'data-next-step="price".*?data-next-step-action>Price This Job</a>', hub, re.S)


# ================================================================================ Field Today
def test_field_today_leads_with_the_work_list_one_primary_and_the_rest_closed(env):
    from app.services.access_domains import FIELD_ONLY_ALLOWED_ENDPOINTS

    _app, d, _ben = env
    page = d.get("/field/today")
    main = page.split("data-field-quick-actions", 1)[1]
    # The one-time "text me schedule changes?" question (its own consent card, shown until answered) is not part of
    # the day's work; outside it there is exactly one primary action.
    if "data-field-texts-setup" in main:
        main = re.sub(r'<section[^>]*data-field-texts-setup.*?</form>', "", main, count=1, flags=re.S)
    assert len(re.findall(r'class="field-btn field-btn-primary', main)) == 1
    work = main.index("data-field-today-work")
    assert work < main.index("data-field-today-more")
    assert re.search(r'<details[^>]*data-field-today-more', main)
    # The seven quick actions (Magnificent Seven, owner approved) stay.
    for key in ("hours", "receipt", "materials", "extra_work", "delivery", "job_update", "schedule"):
        assert f'data-quick-action="{key}"' in page, key
    assert "Choose Project" in page  # the primary when no job is chosen
    assert "documents.field_project" in FIELD_ONLY_ALLOWED_ENDPOINTS  # the frozen list is unchanged by this slice


# ================================================================================ Supplier Hub: CaliSIGN awaiting
def test_the_supplier_attention_provider_is_registered_and_never_on_the_office_list():
    from app.services import needs_attention as NA

    provider = next(p for p in NA.all_providers() if p.key == "supplier_calisign_awaiting")
    assert provider.scope == NA.SCOPE_SUPPLIER and provider.kind == "signing"
    assert not NA.scope_allows(NA.SCOPE_SUPPLIER, {"office": True, "owner": True, "admin": True,
                                                   "company_management": True, "financial": True})


from tests.test_deck_takeoff_workflow import app, client  # noqa: E402,F401 - the Supplier Hub fixtures


def test_the_supplier_hub_lists_a_purchase_order_waiting_for_the_stores_signature(app, client):  # noqa: F811
    from app.models.supplier_portal import SupplierPurchaseOrder
    from app.services import supplier_signing as SS
    from app.services.supplier_insights import attention
    from tests.test_supplier_native_signing import STORE, _placed_concrete

    from flask import g

    # As tests/test_supplier_hub.py's autouse fixture does: one app context is shared by the office and store
    # clients, so flask-login's cached user is cleared before each request.
    def clear():
        g.pop("_login_user", None)

    app.before_request_funcs.setdefault(None, []).insert(0, clear)
    _project_row, tomlinson, store, share, delivery = _placed_concrete(app, client)
    order = SupplierPurchaseOrder.query.one()
    assert SS.order_signing(order).status == "SENT"
    found = attention(tomlinson.supplier_id)
    assert found["signing_count"] == 1
    row = found["signing"][0]
    assert row["what"].startswith("Purchase order") and order.number in row["what"]
    assert row["href"].endswith(f"/supplier/{tomlinson.supplier_id}/requests/{share.id}")
    inbox = store.get(f"/supplier/{tomlinson.supplier_id}/").get_data(as_text=True)
    assert 'data-attention-signing="1"' in inbox and "Waiting for your signature" in inbox
    # Once the store signs, it is no longer waiting.
    store.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/confirm",
               data={**STORE, "action": "confirm", "expected_delivery": delivery, "delivery_window": "7:00–9:00"})
    assert attention(tomlinson.supplier_id)["signing_count"] == 0
    # Another store never sees it.
    assert attention(tomlinson.supplier_id + 999)["signing_count"] == 0


def test_set_up_records_no_drawings_needed_on_the_same_screen(env):
    _app, d, _ben = env
    d.post("/projects/new", data={"name": "No plans (synthetic)", "client_id": synthetic_client().id,
                                   "plan_start": "none"})
    project = Project.query.filter_by(name="No plans (synthetic)").one()
    assert project.drawing_requirement == "NOT_REQUIRED"

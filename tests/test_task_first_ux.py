"""Task-First UX, first half (Joel's mandate, 31 Oct 2026; docs/ux/task-first-ux-audit-2026-10-31.md).

SIMPLE ON THE SURFACE, POWERFUL UNDERNEATH. A: one token file and the Task Screen standard. B: six primary
destinations + More + Admin, every earlier sidebar destination still reachable, the live attention bell. C: ONE
attention list built from a registry of providers, each item opening the exact task, scoped by the existing
permissions. Synthetic data only.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.user import UserMembership
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import create_membership, create_user, ensure_office_user, login_office_user

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "app" / "static" / "css"

# Every destination the office sidebar offered on 30 Oct 2026 (audit section 2.1, 28 rows). Each must still be
# reachable from the sidebar, the More page or the Admin gear.
SIDEBAR_30_OCT = (
    "main.dashboard", "schedule.company", "projects.list_projects", "clients.list_clients",
    "calculators.concrete", "calculators.stairs", "calculators.wall_form", "calculators.employment_vs_entrepreneurship",
    "calculators.wall_framing", "calculators.footing", "calculators.roofing", "calculators.siding",
    "calculators.drywall", "calculators.flooring", "costs_and_pricing.index", "cost_library.list_cost_items",
    "assemblies.list_assemblies", "pricing_engine.index", "proposal_templates.list_templates",
    "historical_estimates.index", "getting_started.index", "workflow_map.contractor", "company_attention.index",
    "people_access.index", "organization_crew.index", "supplier_office.suppliers", "accounting.index",
    "work_structure.catalog_index",
)


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "task-first-ux", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _html(response):
    assert response.status_code == 200, response.status_code
    return response.get_data(as_text=True)


def _make_owner():
    from app.models.organization import Organization

    user = ensure_office_user()
    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()
    org = db.session.get(Organization, ORG)
    org.instance_owner_membership_id = membership.id
    db.session.commit()
    return user


def _grant_company_management(user):
    from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, grant_access_domain

    membership = UserMembership.query.filter_by(user_id=user.id, organization_id=ORG).one()
    grant_access_domain(membership_id=membership.id, domain_key=ACCESS_DOMAIN_COMPANY_MANAGEMENT)
    db.session.commit()


def _project(name="TF synthetic deck", status="Estimating"):
    client = Client(name=f"{name} customer", organization_id=ORG, email="c@example.com", phone="555-0100",
                    address="1 Synthetic Rd")
    db.session.add(client)
    db.session.flush()
    project = Project(name=name, client_id=client.id, organization_id=ORG, status=status)
    db.session.add(project)
    db.session.commit()
    return project


def _second_office_user(email="staff@example.com"):
    user = create_user(email=email, password="staff-password-1", display_name="Staff Synthetic")
    create_membership(user, ORG)
    db.session.commit()
    return user


# ============================================================================================ A. design system
def test_one_token_file_defines_danger_spacing_and_type_and_the_old_split_is_gone():
    tokens = (CSS / "tokens.css").read_text(encoding="utf-8")
    for token in ("--danger:", "--danger-soft:", "--warning:", "--ok:", "--focus:", "--gold:", "--space-1:",
                  "--space-4:", "--space-8:", "--text-base:", "--text-sm:", "--radius-md:", "--touch-target:"):
        assert token in tokens, token
    app_css = (CSS / "app.css").read_text(encoding="utf-8")
    refinement = (CSS / "v1-refinement.css").read_text(encoding="utf-8")
    assert ":root" not in app_css and ":root" not in refinement
    first_rule = [line for line in app_css.splitlines() if line.strip() and not line.strip().startswith("/*")][0]
    assert first_rule == '@import url("tokens.css");'
    assert (CSS / "field.css").read_text(encoding="utf-8").startswith('@import url("tokens.css");')
    # --danger is defined now, so nothing needs a fallback for it.
    for path in list(CSS.glob("*.css")) + list((ROOT / "app" / "templates").rglob("*.html")):
        assert "var(--danger," not in path.read_text(encoding="utf-8"), path


def test_focus_is_visible_with_enough_contrast():
    tokens = (CSS / "tokens.css").read_text(encoding="utf-8")
    focus = re.search(r"--focus:\s*(#[0-9a-f]{6})", tokens).group(1)

    def lum(hex_colour):
        rgb = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    assert (lum("#ffffff") + 0.05) / (lum(focus) + 0.05) >= 4.5  # WCAG 1.4.11 needs 3:1; this is stronger
    task_css = (CSS / "task-screen.css").read_text(encoding="utf-8")
    assert ":focus-visible" in task_css and "outline: 3px solid var(--focus)" in task_css
    assert "max-width: 640px" in task_css  # the phone layout (390 px)


def test_task_screen_macros_render_the_hierarchy_with_one_primary_action(app):
    template = app.jinja_env.from_string(
        '{% import "partials/task_screen.html" as ts with context %}'
        '{{ ts.context("Smith deck", facts=["BC-2026-0001", "Linda Smith"], stage="Estimating") }}'
        '{{ ts.purpose("Price this job", "So you can approve it.") }}'
        '{{ ts.state([{"text": "Customer is on file", "status": "done"},'
        '             {"text": "Drawings needed", "status": "attention", "href": "/x", "link": "Add"}]) }}'
        '{{ ts.attention([]) }}'
        '{{ ts.next_step({"key": "price", "title": "Price the deck", "why": "3 work items", "label": "Price it",'
        '                 "url": "/go"}) }}'
        '{% call ts.details("Calculations", "ts-calc", hint="2 results") %}<p>inside</p>{% endcall %}')
    with app.test_request_context("/"):
        html = template.render()
    order = [html.index(hook) for hook in ("data-ts-context", "data-ts-purpose", "data-ts-state",
                                           "data-ts-attention", 'data-next-step="price"', 'data-ts-section="ts-calc"')]
    assert order == sorted(order)
    assert html.count("data-next-step-action") == 1 and 'class="ts-primary" href="/go"' in html
    assert '<details class="ts-details" id="ts-calc" data-ts-section="ts-calc" >' in html  # closed by default
    assert 'data-ts-state-row="attention"' in html and "Needs attention: " in html
    assert "Nothing here needs you right now." in html


def test_the_office_shell_links_the_task_screen_styles_and_behaviour(client):
    html = _html(client.get("/"))
    assert "css/task-screen.css" in html and "js/task_screen.js" in html and "css/needs_attention.css" in html


# ============================================================================================ B. navigation
def test_six_primary_destinations_then_more():
    from app.navigation import NAV_SECTIONS, PRIMARY_NAV

    assert [i["title"] for i in PRIMARY_NAV] == ["Attention", "Projects", "Calendar", "Customers", "Purchasing",
                                                 "Time & Money"]
    sidebar = [i["endpoint"] for s in NAV_SECTIONS for i in s["links"]]
    assert sidebar == ["main.dashboard", "projects.list_projects", "schedule.company", "clients.list_clients",
                       "main.purchasing", "main.time_and_money", "main.more"]


def test_every_destination_the_sidebar_had_is_still_reachable():
    from app.navigation import MORE_SECTIONS, reachable_endpoints

    reachable = reachable_endpoints()
    # The Company Attention page is folded into the attention list, which links it for the people who may see it.
    missing = [e for e in SIDEBAR_30_OCT if e not in reachable and e != "company_attention.index"]
    assert missing == []
    calculators = next(s for s in MORE_SECTIONS if s["title"] == "Calculators")
    assert len(calculators["links"]) == 10


def test_more_and_admin_pages_open_every_link_and_nothing_404s(client, app):
    with app.app_context():
        _make_owner()
    more = _html(client.get("/more"))
    admin = _html(client.get("/admin"))
    from app.navigation import ADMIN_ITEMS, MORE_SECTIONS

    for section in MORE_SECTIONS:
        for item in section["links"]:
            assert f'data-link-hub-item="{item["endpoint"]}"' in more, item
    for item in ADMIN_ITEMS:
        assert f'data-link-hub-item="{item["endpoint"]}"' in admin, item
    for href in set(re.findall(r'data-link-hub-item="[^"]+"[^>]*|href="(/[^"#?]*)"', more + admin)):
        if href and not href.startswith("/static"):
            status = client.get(href).status_code
            assert status in (200, 302), (href, status)


def test_people_and_access_is_offered_only_to_the_owner_or_an_administrator(client, app):
    admin = _html(client.get("/admin"))
    assert 'data-link-hub-item="people_access.index"' not in admin
    assert 'data-link-hub-item="organization_crew.index"' in admin  # every office member may view crews
    with app.app_context():
        _make_owner()
    assert 'data-link-hub-item="people_access.index"' in _html(client.get("/admin"))


def test_the_sidebar_highlights_the_area_you_are_in(client, app):
    concrete = _html(client.get("/calculators/concrete"))
    active = re.findall(r'class="sidebar-link is-active"[^>]*href="([^"]+)"|href="([^"]+)"\s+aria-current="page"',
                        concrete)
    assert concrete.count('class="sidebar-link is-active"') == 1
    assert 'href="/more"\n                        aria-current="page"' in concrete or any("/more" in "".join(a) for a in active)
    from app.navigation import nav_area

    assert nav_area("estimates.view_version") == "projects.list_projects"
    assert nav_area("operations.material_request") == "main.purchasing"
    assert nav_area("accounting.invoices") == "main.time_and_money"
    assert nav_area("pricing_engine.index") == "admin"
    assert nav_area("calculators.footing") == "more"


def test_the_bell_is_the_live_attention_count_and_the_gear_opens_admin(client, app):
    html = _html(client.get("/projects/"))
    assert "Notifications (coming soon)" not in html and "disabled aria-label" not in html
    assert 'href="/operations/attention" data-attention-bell data-attention-count-url="/attention/count"' in html
    assert 'href="/admin" data-admin-gear' in html
    with app.app_context():
        project = _project()
        from app.project_controls.models import ChangeOrder

        db.session.add(ChangeOrder(organization_id=ORG, project_id=project.id, number="CO-TF-1", title="Extra steps",
                                   status="Draft"))
        db.session.commit()
    data = client.get("/attention/count").get_json()
    assert data["count"] >= 1


def test_field_only_crew_keep_their_field_navigation(app):
    from app.services.access_domains import set_field_only

    with app.app_context():
        owner = _make_owner()
        crew = create_user(email="crew@example.com", password="crew-password-1", display_name="Crew Synthetic")
        membership = create_membership(crew, ORG)
        db.session.commit()
        set_field_only(membership, True, owner)
        db.session.commit()
    http = app.test_client()
    login_office_user(http, email="crew@example.com", password="crew-password-1")
    assert http.get("/more").status_code == 302 and http.get("/attention/count").status_code == 302
    today = http.get("/field/today", follow_redirects=True).get_data(as_text=True)
    assert "shell-sidebar" not in today and "data-admin-gear" not in today


def test_the_supplier_hub_navigation_is_unchanged_in_structure():
    base = (ROOT / "app" / "templates" / "supplier" / "base.html").read_text(encoding="utf-8")
    assert "app.navigation" not in base and "nav_sections" not in base
    assert 'class="supplier-nav"' in base


# ============================================================================================ C. attention
REQUIRED_PROVIDERS = (
    "estimate_ready_for_approval", "calculator_results_not_on_estimate", "subcontract_quotes",
    "supplier_prices_missing", "supplier_quotes_and_orders", "proposal_awaiting_customer", "calisign",
    "contract_not_generated", "subcontract_awaiting_gate3", "early_order_not_placed",
    "company_schedule_change_requests", "delivery_notices_to_send", "accepted_work_not_scheduled",
    "change_order_drafts", "walkthrough_returned", "ready_to_close",
    # every item surfaced before 31 Oct 2026
    "time_to_approve", "material_requests", "extra_work", "delivery_exceptions", "receipts", "quickbooks",
    "schedule_conflicts", "job_updates", "punch_list", "customers_incomplete", "company_facts",
    "schedule_texts_failed",
)


def test_the_attention_list_is_a_registry_of_scoped_providers():
    from app.services.needs_attention import PROVIDERS, SCOPES

    keys = [p.key for p in PROVIDERS]
    assert len(keys) == len(set(keys))
    for key in REQUIRED_PROVIDERS:
        assert key in keys, key
    assert all(p.scope in SCOPES and p.title for p in PROVIDERS)
    source = (ROOT / "app" / "services" / "needs_attention.py").read_text(encoding="utf-8")
    # Links are built from endpoints (url_for), never typed paths.
    assert not re.search(r'f?"/(time|operations|projects|accounting|clients|project-controls|work-structure)[/?"]',
                         source)


def test_another_feature_registers_its_provider_through_the_hook(app):
    from app.services.needs_attention import AttentionProvider, assemble, register_attention_provider

    with app.app_context():
        user = ensure_office_user()
        project = _project()

        def documents(ctx):
            return [ctx.item("documents", "Drawing revision to review", ctx.label(ctx.project(project.id)),
                             "New revision", "", ctx.link("projects.view_project", id=project.id), "Review",
                             project_id=project.id)]

        register_attention_provider(AttentionProvider("documents_review", "documents", "office", documents), app=app)
        with app.test_request_context("/"):
            view = assemble(ORG, user)
        row = next(i for i in view["items"] if i["provider"] == "documents_review")
        assert row["href"] == f"/projects/{project.id}" and row["title"] == "Drawing revision to review"
        with pytest.raises(ValueError):
            register_attention_provider(AttentionProvider("bad", "x", "everyone", documents), app=app)


def _seed_governed_events():
    """One synthetic record for each governed event added on 31 Oct 2026."""
    from app.models.estimate import EstimateLineItem
    from app.models.final_walkthrough import ProjectFinalWalkthroughInvitation, ProjectFinalWalkthroughItem
    from app.models.procurement_governance import EarlyProcurementException, SubcontractCommitment
    from app.models.project_calculation import ProjectCalculation
    from app.models.proposal import Proposal
    from app.models.schedule_governance import CompanyScheduleChangeRequest, ScheduleExternalDraft
    from app.models.subcontractor import SubcontractQuoteEvidence, Subcontractor
    from app.project_controls.models import ChangeOrder
    from app.models.proposal import ProposalTemplate
    from app.services.estimates import create_estimate

    template = ProposalTemplate(organization_id=ORG, name="TF template")
    db.session.add(template)
    db.session.flush()
    project = _project("TF governed events")
    estimate = create_estimate(project_id=project.id, estimate_number="EST-TF-1", title="TF estimate")
    version = estimate.current_version
    db.session.add(ProjectCalculation(organization_id=ORG, project_id=project.id, calculator="concrete",
                                      summary="3 yd3", entered=[], result_text="3 yd3", actor_display_name="Ben",
                                      payload={"x": 1}, review_status="AWAITING_REVIEW"))
    sub = Subcontractor(organization_id=ORG, code="SUB-TF", legal_name="Synthetic Electric")
    db.session.add(sub)
    db.session.flush()
    from app.services.estimate_builder import add_manual_line, create_section

    section = create_section(version, name="Electrical")
    line = add_manual_line(section, line_type="Custom", description="Electrical rough-in", quantity=1, unit="ls",
                           unit_cost=0)
    line = line if isinstance(line, EstimateLineItem) else EstimateLineItem.query.order_by(EstimateLineItem.id.desc()).first()
    db.session.add(SubcontractQuoteEvidence(organization_id=ORG, project_id=project.id, estimate_id=estimate.id,
                                            estimate_version_id=version.id, estimate_line_item_id=line.id,
                                            subcontractor_id=sub.id, quote_reference="Q-1", amount=Decimal("1800"),
                                            quote_date=date(2026, 10, 30), actor_display_name="Ben"))
    db.session.add(Proposal(organization_id=ORG, proposal_number="PR-TF-1", estimate_id=estimate.id,
                            estimate_version_id=version.id, title="TF proposal", status="Issued", proposal_template_id=template.id,
                            client_name="Customer", project_name=project.name, estimate_number="EST-TF-1",
                            estimate_version_number=1, issued_at=datetime.utcnow() - timedelta(days=2)))
    accepted = _project("TF accepted job", status="Contracted")
    est2 = create_estimate(project_id=accepted.id, estimate_number="EST-TF-2", title="TF accepted")
    db.session.add(Proposal(organization_id=ORG, proposal_number="PR-TF-2", estimate_id=est2.id,
                            estimate_version_id=est2.current_version.id, title="Accepted", status="Accepted", proposal_template_id=template.id,
                            client_name="Customer", project_name=accepted.name, estimate_number="EST-TF-2",
                            estimate_version_number=1))
    db.session.add(SubcontractCommitment(organization_id=ORG, project_id=project.id, subcontractor_name="Synthetic Framing",
                                         scope_text="Framing", amount=Decimal("18400"), proposed_by_name="Ben"))
    db.session.add(EarlyProcurementException(organization_id=ORG, project_id=project.id, reason="Long lead",
                                             proposed_commitment="Trusses", financial_exposure=Decimal("5000"),
                                             approving_authority="Owner", approved_by_name="Joel"))
    db.session.add(CompanyScheduleChangeRequest(organization_id=ORG, project_id=project.id, work_schedule_item_id=1,
                                                prior_start=date(2026, 11, 10), prior_end=date(2026, 11, 11),
                                                proposed_start=date(2026, 11, 12), proposed_end=date(2026, 11, 13),
                                                requested_by_name="Ben", reason="Rain", impact_json="{}"))
    db.session.add(ScheduleExternalDraft(organization_id=ORG, project_id=project.id, work_schedule_item_id=1,
                                         prior_start=date(2026, 11, 10), new_start=date(2026, 11, 12),
                                         summary="Trusses delivery"))
    db.session.add(ChangeOrder(organization_id=ORG, project_id=project.id, number="CO-TF-2", title="Second stair",
                               status="Draft"))
    closing = _project("TF closing job", status="Active")
    invitation = ProjectFinalWalkthroughInvitation(organization_id=ORG, project_id=closing.id, lookup_key="tf-walk-1",
                                                   token_hash="0" * 64, status="RESPONDED",
                                                   expires_at=datetime.utcnow() + timedelta(days=5),
                                                   responded_at=datetime.utcnow(), created_by_user_id=1)
    db.session.add(invitation)
    db.session.flush()
    db.session.add(ProjectFinalWalkthroughItem(invitation_id=invitation.id, organization_id=ORG,
                                               project_id=closing.id, description="Touch up the trim"))
    done = _project("TF done job", status="Active")
    db.session.add(ProjectFinalWalkthroughInvitation(organization_id=ORG, project_id=done.id, lookup_key="tf-walk-2",
                                                     token_hash="1" * 64, status="RESPONDED",
                                                     expires_at=datetime.utcnow() + timedelta(days=5),
                                                     responded_at=datetime.utcnow(), created_by_user_id=1))
    db.session.commit()
    return {"project": project, "accepted": accepted, "closing": closing, "done": done}


def test_governed_events_appear_in_plain_words_and_open_the_exact_task(client, app):
    with app.app_context():
        owner = _make_owner()
        _grant_company_management(owner)
        facts = {k: v.id for k, v in _seed_governed_events().items()}
        pid = facts["project"]
    page = _html(client.get("/operations/attention"))
    expected = {
        "calculator_results_not_on_estimate": "1 calculator result waiting to go on the estimate",
        "subcontract_quotes": "1 subcontract quote received for Electrical rough-in: choose one",
        "proposal_awaiting_customer": "Proposal PR-TF-1 sent: no answer yet",
        "contract_not_generated": "Customer accepted: contract not generated yet",
        "subcontract_awaiting_gate3": "Approve the Synthetic Framing subcontract ($18,400.00)",
        "early_order_not_placed": "Order approved before the customer signed: not placed yet",
        "company_schedule_change_requests": "Ben asks to move work to Thu Nov 12",
        "delivery_notices_to_send": "1 supplier delivery notice drafted: send?",
        "change_order_drafts": "Change order CO-TF-2 drafted, not sent: Second stair",
        "walkthrough_returned": "Customer returned the walkthrough: 1 item",
        "ready_to_close": "TF done job looks ready to close",
    }
    for provider, words in expected.items():
        assert f'data-attention-provider="{provider}"' in page, provider
        assert words in page, words
    assert "Waiting on others" in page  # the proposal sent to the customer waits on them
    assert f'href="/projects/{pid}/commitments#commitment-' in page
    assert f'href="/schedule/projects/{pid}/planning#change-request-' in page
    assert f'href="/schedule/projects/{pid}/planning#delivery-drafts"' in page
    assert f'href="/projects/{facts["accepted"]}/contract#contract-generate"' in page
    assert f'href="/projects/{facts["done"]}/close"' in page
    for href in set(re.findall(r'class="na-go" href="([^"]+)"', page)):
        assert client.get(href.split("#")[0]).status_code in (200, 302), href
    # Kind filters narrow the list; kind codes never show as words.
    narrowed = _html(client.get("/operations/attention?kind=planning"))
    assert "Dates to decide" in narrowed and "Proposal PR-TF-1" not in narrowed


def test_items_appear_only_for_people_who_may_act_on_them(app):
    from app.services.needs_attention import assemble

    with app.app_context():
        owner = _make_owner()
        staff = _second_office_user()
        _seed_governed_events()
        with app.test_request_context("/"):
            mine = {i["provider"] for i in assemble(ORG, owner)["items"]}
            theirs = {i["provider"] for i in assemble(ORG, staff)["items"]}
    assert "subcontract_awaiting_gate3" in mine and "subcontract_awaiting_gate3" not in theirs  # Gate 3: owner / CM
    assert "company_schedule_change_requests" in mine and "company_schedule_change_requests" not in theirs
    assert "ready_to_close" in mine and "ready_to_close" not in theirs                          # owner / SA closes
    assert "change_order_drafts" in theirs and "proposal_awaiting_customer" in theirs           # any office member


def test_home_and_the_full_list_are_one_list_including_company_facts(client, app):
    with app.app_context():
        owner = _make_owner()
        _grant_company_management(owner)
        _seed_governed_events()
    home = _html(client.get("/"))
    full = _html(client.get("/operations/attention"))
    assert "WHAT NEEDS MY ATTENTION?" in home and 'data-attention-all' in home
    shown = re.findall(r'data-attention-provider="([^"]+)"', home.split("data-attention-others")[0])
    assert len(shown) == 5
    for provider in shown:
        assert f'data-attention-provider="{provider}"' in full
    assert 'data-company-attention-details' in full  # the labour facts, job by job, for Company Management
    assert home.index("data-needs-attention") < home.index("data-wizard-home") < home.index("Today and coming days")
    assert "Start something" in home and "Guided Wizards" not in home


def test_the_company_attention_route_still_works_and_points_to_the_one_list(client, app):
    with app.app_context():
        owner = _make_owner()
        _grant_company_management(owner)
    assert client.get("/company-attention").status_code == 200


def test_purchasing_and_time_and_money_are_task_screens_over_every_page_of_their_area(client, app):
    from app.navigation import PURCHASING_LINKS, TIME_AND_MONEY_LINKS

    with app.app_context():
        _make_owner()
    for url, links, purpose in (("/purchasing", PURCHASING_LINKS, "Buy what&#39;s needed"),
                                ("/time-and-money", TIME_AND_MONEY_LINKS, "Keep time and money up to date")):
        page = _html(client.get(url))
        assert purpose in page and "data-ts-attention" in page
        for item in links:
            assert f'data-link-hub-item="{item["endpoint"]}"' in page
        for href in re.findall(r'data-link-hub-item="[^"]+"', page):
            pass
        for href in set(re.findall(r'<li><a href="(/[^"#]*)" data-link-hub-item', page)):
            assert client.get(href).status_code in (200, 302), href


# ============================================================================================ D. the Project page
HUB_HOOKS = ("data-project-identity", "data-brayman-project-number", "data-client-number-form", "data-hub-project-lead",
             "data-project-lead", "data-project-workflow-link", "data-hub-guided", "data-governed-links",
             "data-make-invoice", "data-hub-field-operations")
HUB_SECTIONS = ("ts-estimate", "ts-customer", "ts-purchasing", "ts-schedule", "ts-work", "ts-changes", "ts-money",
                "ts-closeout", "ts-documents", "ts-plans", "ts-details")


def test_the_project_page_is_a_task_screen_with_one_next_step_and_every_action_kept(client, app):
    with app.app_context():
        pid = _project("TF hub job", status="Lead").id
    page = _html(client.get(f"/projects/{pid}"))
    main = page[page.index('<main'):]
    assert main.count("data-next-step-action") == 1 and main.count('class="ts-primary"') == 1
    assert 'data-next-step="setup"' in main and ">Continue setup</a>" in main
    assert "What Calibrayt already knows" in main and "Needs you on this job" in main
    for section in HUB_SECTIONS:
        assert f'data-ts-section="{section}"' in main, section
        assert f'<details class="ts-details" id="{section}" data-ts-section="{section}" >' in main  # closed
    for hook in HUB_HOOKS:
        assert hook in main, hook
    # Every action the header offered on 30 Oct 2026 is still on the page (More actions or its section).
    for label in ("Drawings", "Scope of work", "Enter construction information", "New Change Order", "Print"):
        assert f">{label}</a>" in main, label
    assert "LEARN" not in main and "More about this page" not in main and "hub-lifecycle" not in main
    # The context header names the job, its stage and its Brayman Project #.
    head = main[main.index('data-ts-context'):main.index('data-next-step')]
    assert "TF hub job" in head and "data-project-stage" in head and "data-brayman-project-number" in head


def test_the_documents_section_links_the_jobs_documents_page(client, app):
    # RDIMS merged (1 Nov 2026): documents.project_documents is registered, so the section links the job's
    # Documents page directly (the placeholder sentence only shows when the endpoint is missing).
    with app.app_context():
        pid = _project().id
    page = _html(client.get(f"/projects/{pid}"))
    slot = page[page.index("data-project-documents-slot"):]
    assert f'href="/projects/{pid}/documents" data-project-documents-link' in slot[:600]
    assert "This job's documents will be listed here." not in slot[:600]


def test_next_step_follows_the_job_through_every_stage(app):
    from app.models.proposal import Proposal, ProposalTemplate
    from app.services.estimates import create_estimate
    from app.services.project_next_step import next_step

    with app.app_context():
        project = _project("TF stages", status="Estimating")
        pid = project.id
        with app.test_request_context("/"):
            assert next_step(project, ORG, is_closed=True, can_close=True)["key"] == "closed"
            assert next_step(project, ORG, is_closed=True, can_close=True)["url"] == f"/projects/{pid}/reopen"
            assert next_step(project, ORG, is_closed=True)["url"] is None
            assert next_step(project, ORG)["label"] == "Continue setup"  # location still needed: the setup resolver
            guided = {"guided": type("G", (), {"scope_status": "FINALIZED", "estimate": None})(), "selected": True,
                      "names": ["Deck"], "done": 1, "included": 3}
            step = next_step(project, ORG, guided_summary=guided)
        assert step["key"] in ("setup", "price")
        template = ProposalTemplate(organization_id=ORG, name="TF stages template")
        db.session.add(template)
        estimate = create_estimate(project_id=project.id, estimate_number="EST-TF-S", title="Stages")
        db.session.flush()
        proposal = Proposal(organization_id=ORG, proposal_number="PR-TF-S", estimate_id=estimate.id,
                            estimate_version_id=estimate.current_version.id, proposal_template_id=template.id,
                            title="Stages", status="Accepted", client_name="C", project_name=project.name,
                            estimate_number="EST-TF-S", estimate_version_number=1)
        db.session.add(proposal)
        estimate.current_version.is_locked = True
        db.session.commit()
        with app.test_request_context("/"):
            from app.services.start_project_walk import DEST_LOCATION  # noqa: F401  (the resolver stays in charge)

            items = [{"kind": "quotes", "what": "Price returned by BMR", "action": "Review and order",
                      "href": "/x", "waiting_on": "you"}]
            after_contract = dict(hub_contracts=[{"number": "CTR-1", "label": "Signed — executed"}])
            states = {
                "contract": next_step(project, ORG, hub_contracts=[]),
                "buy": next_step(project, ORG, attention_items=items, **after_contract),
                "close_punch": next_step(project, ORG, open_closeout_items=2, **after_contract),
                "close": next_step(project, ORG, walkthrough_answered=True, can_close=True, **after_contract),
                "ready": next_step(project, ORG, walkthrough_answered=True, **after_contract),
                "work": next_step(project, ORG, **after_contract),
            }
    if states["contract"]["key"] == "setup":
        pytest.fail("the setup resolver should not hold an accepted job: " + states["contract"]["title"])
    assert states["contract"]["key"] == "contract" and states["contract"]["url"].endswith("/contract")
    assert states["buy"]["key"] == "buy" and states["buy"]["url"] == "/x"
    assert states["close_punch"]["title"] == "Finish the punch list"
    assert states["close"]["url"] == f"/projects/{pid}/close"
    assert states["ready"]["url"] is None  # only the owner or a System Administrator closes
    assert states["work"]["key"] == "work"

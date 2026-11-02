"""Viewport-first density corrective (2 Nov 2026; docs/ux/viewport-density-audit-2026-11-02.md).

The behaviour behind the compact screens, at the HTML level (tools/release/evidence_density.mjs measures them in a
real browser at 1280 x 800 and 390 x 844):

* Set Up This Project (acceptance finding UX-DENSITY-001): with "A customer we have" the new-customer fields take no
  space; with "A new customer" only the fields that create one are shown and the customer list is put away. Both stay
  in the form (nothing submitted changes); the hidden part is switched by the page as the choice changes.
* Optional parts (a description, an address as written, the project settings) are closed until asked for, and open
  on their own when the screen comes back refused with something typed there or a problem in them.
* Field Today: today's work comes before the one-time "Get a text" question.
* Review This Estimate: the figures Ben approves on are on the screen, beside the approval, not in a closed section.

Synthetic data only.
"""

from __future__ import annotations

import re

import pytest

from app import create_app, db
from app.services.organizations import ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user
from tests.guided_support import Driver, client as synthetic_client, seed_company

BEN = ("ben.density@example.invalid", "ben-density-password", "Ben Brayman (synthetic)")


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


def _tag(page: str, hook: str) -> str:
    """The opening tag of the element carrying ``hook`` (e.g. data-su-new-customer)."""
    match = re.search(r"<[a-z]+\b[^>]*(?<![\w-])" + re.escape(hook) + r"(?![\w-])[^>]*>", page)
    assert match, hook
    return match.group(0)


def _hidden(page: str, hook: str) -> bool:
    return re.search(r"\shidden(\s|>|=)", _tag(page, hook)) is not None


def _open(page: str, hook: str) -> bool:
    return re.search(r"\sopen(\s|>|=)", _tag(page, hook)) is not None


# ================================================================================ Set Up This Project: the customer
def test_a_customer_we_have_puts_the_new_customer_fields_away(env):
    _app, d, _ben = env
    synthetic_client()
    page = _main(d.get("/projects/new"))
    assert re.search(r'name="customer_mode" value="existing" checked', page)
    assert not _hidden(page, "data-su-existing")
    assert _hidden(page, "data-su-new-customer"), "no space for a new customer's fields"
    # The fields are still in the form: the screen switches them, nothing submitted changes.
    for name in ("client_id", "new_customer_name", "new_customer_email", "new_customer_phone"):
        assert f'name="{name}"' in page, name
    assert not _hidden(page, "data-same-as-customer-label")


def test_a_new_customer_shows_only_what_creates_one(env):
    _app, d, _ben = env
    synthetic_client()
    # Refused (no customer name): the screen comes back on "A new customer" with what was typed.
    page = _main(d.post("/projects/new", data={"customer_mode": "new", "name": "Kept (synthetic)"}, status=200)
                 .get_data(as_text=True))
    assert re.search(r'name="customer_mode" value="new" checked', page)
    assert _hidden(page, "data-su-existing"), "the customer list is put away"
    assert not _hidden(page, "data-su-new-customer")
    assert _hidden(page, "data-same-as-customer-label"), "a new customer has no address to copy yet"
    assert 'value="Kept (synthetic)"' in page
    # The name is marked as the one thing needed; email and phone say they are optional.
    block = page.split("data-su-new-customer", 1)[1].split("</div>", 1)[0]
    assert "New customer&#39;s name *" in block or "New customer's name *" in block
    assert block.count("(optional)") == 2


def test_with_no_customers_yet_the_new_customer_fields_are_the_only_choice(env):
    _app, d, _ben = env
    page = _main(d.get("/projects/new"))
    assert 'name="customer_mode" value="new"' in page and 'type="hidden" name="customer_mode"' in page
    assert not _hidden(page, "data-su-new-customer")
    assert 'name="client_id"' not in page


def test_the_page_switches_the_customer_parts_as_the_choice_changes(env):
    _app, d, _ben = env
    synthetic_client()
    page = d.get("/projects/new")
    script = page.split("data-set-up-form", 1)[1]
    assert "data-customer-mode" in script and "data-su-new-customer" in script and ".hidden" in script


# ================================================================================ Set Up This Project: optional parts
def test_optional_parts_are_closed_until_asked_for(env):
    _app, d, _ben = env
    synthetic_client()
    page = _main(d.get("/projects/new"))
    assert not _open(page, 'id="ts-project-settings"')
    assert not _open(page, "data-su-description")
    assert not _open(page, "data-su-address-as-written")
    description = page.split("data-su-description", 1)[1].split("</details>", 1)[0]
    assert 'name="description"' in description
    # The questions every project needs stay in view.
    before_settings = page.split('id="ts-project-settings"', 1)[0]
    for name in ("name", "client_id", "guided_project_type", "contractor_role", "street", "municipality",
                 "plan_start"):
        assert f'name="{name}"' in before_settings, name


def test_refused_for_a_setting_opens_the_settings_with_the_reason_in_view(env):
    _app, d, _ben = env
    customer = synthetic_client()
    page = _main(d.post("/projects/new", data={"name": "Premium (synthetic)", "client_id": customer.id,
                                               "customer_mode": "existing", "pricing_posture": "Premium"},
                        status=200).get_data(as_text=True))
    assert _open(page, 'id="ts-project-settings"'), "the part with the problem is open"
    assert re.search(r'<option value="Premium" selected', page)


def test_refused_with_a_description_or_an_address_as_written_keeps_them_open(env):
    _app, d, _ben = env
    page = _main(d.post("/projects/new", data={"customer_mode": "new", "name": "",
                                               "description": "Rear deck (synthetic)",
                                               "address": "Lot 4, Concession 2 (synthetic)"},
                        status=200).get_data(as_text=True))
    assert _open(page, "data-su-description")
    assert _open(page, "data-su-address-as-written")
    assert "Rear deck (synthetic)" in page


def test_a_typed_setting_that_differs_from_the_default_keeps_the_settings_open(env):
    _app, d, _ben = env
    customer = synthetic_client()
    page = _main(d.post("/projects/new", data={"name": "", "client_id": customer.id, "customer_mode": "existing",
                                               "status": "Estimating"}, status=200).get_data(as_text=True))
    assert _open(page, 'id="ts-project-settings"')
    page = _main(d.post("/projects/new", data={"name": "", "client_id": customer.id, "customer_mode": "existing",
                                               "status": "Lead"}, status=200).get_data(as_text=True))
    assert not _open(page, 'id="ts-project-settings"'), "defaults sent back unchanged stay closed"



def test_the_commercial_type_filled_from_what_is_being_built_does_not_open_the_settings(env):
    """Review finding (2 Nov 2026): the page fills project_type from "What is being built", so a refusal that sends
    that hint back is not a change the user made; only a type that differs from the hint opens the settings."""
    from app.services.guided_estimating import COMMERCIAL_TYPE_HINT

    _app, d, _ben = env
    key, hint = next(iter(COMMERCIAL_TYPE_HINT.items()))
    page = _main(d.post("/projects/new", data={"customer_mode": "new", "name": "Refused (synthetic)",
                                               "guided_project_type": key, "project_type": hint},
                        status=200).get_data(as_text=True))
    assert not _open(page, 'id="ts-project-settings"'), "the filled-in hint is not a change"
    other = next(v for v in COMMERCIAL_TYPE_HINT.values() if v != hint)
    page = _main(d.post("/projects/new", data={"customer_mode": "new", "name": "Refused (synthetic)",
                                               "guided_project_type": key, "project_type": other},
                        status=200).get_data(as_text=True))
    assert _open(page, 'id="ts-project-settings"'), "a type the user changed keeps the settings open"

# ================================================================================ Review This Estimate
def test_review_this_estimate_keeps_the_figures_beside_the_approval(env):
    from tests.test_guided_tasks import _priced_job

    _app, d, _ben = env
    project, _guided = _priced_job(d)
    page = _main(d.get(f"/projects/{project.id}/guided/pricing"))
    figures = page.index("data-project-figures")
    # Not inside any closed section: every <details> opened before the figures is closed again before them.
    before = page[:figures]
    assert before.count("<details") == before.count("</details>")
    assert "data-project-pricing-form" in page
    # The decision comes first, then the figures it is made on.
    assert page.index('data-next-step="') < figures


# ================================================================================ Field Today
def test_field_today_puts_todays_work_before_the_texts_question(env):
    from app.models.user import UserMembership
    from app.services.access_domains import set_field_only
    from app.services.instance_authority import set_instance_owner
    from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG

    app, _d, ben = env
    set_instance_owner(ORG, UserMembership.query.filter_by(user_id=ben.id, organization_id=ORG).one().id, ben.id)
    crew = ensure_office_user(email="crew.density@example.invalid", password="crew-density-password",
                              display_name="Kevin Crew (synthetic)")
    set_field_only(UserMembership.query.filter_by(user_id=crew.id, organization_id=ORG).one(), True, ben)
    db.session.commit()
    http = app.test_client()
    login_office_user(http, email="crew.density@example.invalid", password="crew-density-password")
    today = http.get("/field/today").get_data(as_text=True)
    if "data-field-texts-setup" in today:
        assert today.index("data-field-today-work") < today.index("data-field-texts-setup")
    assert today.index("data-field-today-work") < today.index("data-field-today-more")

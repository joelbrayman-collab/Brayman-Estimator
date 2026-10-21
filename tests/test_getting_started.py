"""Ben's First Day guided checklist (Joel, 21 Oct 2026). Synthetic data only."""

from __future__ import annotations

import pytest

from app import create_app, db
from app.models import Client, Project
from app.models.onboarding import OrganizationOnboardingStep
from app.services.onboarding import STEPS
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization


@pytest.fixture
def app():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                              "SECRET_KEY": "test-getting-started", "WTF_CSRF_ENABLED": False})
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_fifteen_steps_link_to_real_pages_and_progress_is_saved(app, client):
    assert len(STEPS) == 15 and len({s.key for s in STEPS}) == 15
    page = client.get("/getting-started")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert 'data-getting-started="1/15"' in html  # signed in: step 1 is done by itself
    for step in STEPS:
        assert f'data-step="{step.key}"' in html
    # A step the platform can see ticks itself: a client and a project.
    c = Client(name="Synthetic Customer", organization_id=DEFAULT_ORGANIZATION_ID)
    db.session.add(c); db.session.flush()
    db.session.add(Project(name="Synthetic Job", client_id=c.id, organization_id=DEFAULT_ORGANIZATION_ID, status="Estimating"))
    db.session.commit()
    html = client.get("/getting-started").get_data(as_text=True)
    assert 'data-step="customers" data-done="yes"' in html
    # A step only a person can confirm is marked, saved, and can be undone.
    client.post("/getting-started/steps/phones", data={"done": "yes"})
    row = OrganizationOnboardingStep.query.filter_by(step_key="phones").one()
    assert row.organization_id == DEFAULT_ORGANIZATION_ID and row.done_by_name
    html = client.get("/getting-started").get_data(as_text=True)
    assert 'data-step="phones" data-done="yes"' in html and "Marked done by" in html
    client.post("/getting-started/steps/phones", data={"done": "no"})
    assert OrganizationOnboardingStep.query.filter_by(step_key="phones").count() == 0
    assert client.post("/getting-started/steps/nonsense", data={"done": "yes"}).status_code == 302
    assert OrganizationOnboardingStep.query.count() == 0


def test_every_go_there_link_opens(app, client):
    html = client.get("/getting-started").get_data(as_text=True)
    import re

    for href in sorted(set(re.findall(r'href="(/[^"#]*)"[^>]*>Go there', html))):
        expected = (200, 302, 403) if href.startswith("/settings/people") else (200, 302)  # People & Access: owner only
        assert client.get(href).status_code in expected, href


def test_company_step_ticks_only_when_the_brand_profile_is_saved(app, client):
    """Opening Brand profile creates version 1 from the organization record by itself; that is not Ben setting
    up his company (first-day walk, 21 Oct 2026). Saving the form is."""
    from app.models.brand_profile import OrganizationBrandProfile
    from tests.test_core_close_close_reopen_fg035 import _make_owner

    _make_owner()  # saving the brand profile is for the owner or a System Administrator
    assert client.get("/settings/brand-profile").status_code == 200
    assert OrganizationBrandProfile.query.filter_by(organization_id=DEFAULT_ORGANIZATION_ID).count() == 1
    assert 'data-step="company" data-done="no"' in client.get("/getting-started").get_data(as_text=True)
    saved = client.post("/settings/brand-profile", data={
        "legal_name": "Synthetic Builder Inc.", "customer_facing_name": "Synthetic Builder",
        "phone": "613-555-0100", "email": "office@example.invalid", "address": "1 Synthetic Road"})
    assert saved.status_code == 302
    assert 'data-step="company" data-done="yes"' in client.get("/getting-started").get_data(as_text=True)

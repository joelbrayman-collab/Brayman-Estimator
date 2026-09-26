"""Shared polish foundation — presentation only."""

from app import create_app, db
from app.models import Client, Project
from app.navigation import NAV_ITEMS, NAV_SECTIONS
from app.services.organization_crew import create_crew
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from tests.auth_fixtures import ensure_office_user, login_office_user


def _app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-uat3-polish",
            "WTF_CSRF_ENABLED": False,
        }
    )
    return application


def test_brand_is_not_in_the_daily_menu():
    titles = [item["title"] for section in NAV_SECTIONS for item in section["links"]]
    endpoints = {item["endpoint"] for item in NAV_ITEMS}
    assert "Brand" not in titles
    assert "settings.brand_profile" not in endpoints
    company = next(row for row in NAV_SECTIONS if row["title"] == "Company")
    assert [item["title"] for item in company["links"]] == [
        "Attention",
        "Crews",
        "Work catalog",
    ]


def test_home_and_projects_keep_their_presentation():
    application = _app()
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
        client_row = Client(
            name="Oak Client",
            company="Oak Co",
            organization_id=DEFAULT_ORGANIZATION_ID,
        )
        db.session.add(client_row)
        db.session.flush()
        db.session.add(
            Project(
                name="Oak House",
                client_id=client_row.id,
                organization_id=DEFAULT_ORGANIZATION_ID,
                status="Lead",
            )
        )
        db.session.commit()
        http = application.test_client()
        login_office_user(http)
        home = http.get("/").get_data(as_text=True)
        projects = http.get("/projects/").get_data(as_text=True)
        db.session.remove()
        db.drop_all()
    assert "home-greeting" in home
    assert "home-counts" in home
    assert "home-start" in home
    assert "home-calendar" in home
    assert "projects-row" in projects
    assert "projects-intro" in projects
    assert 'aria-label="Settings"' not in home
    assert "header-company" in home
    assert 'href="/settings/brand-profile"' in home


def test_clients_use_the_shared_header_and_register_table():
    application = _app()
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
        db.session.add(
            Client(
                name="Maple Client",
                company="Maple Co",
                email="maple@example.com",
                phone="613-555-0101",
                organization_id=DEFAULT_ORGANIZATION_ID,
            )
        )
        db.session.commit()
        http = application.test_client()
        login_office_user(http)
        html = http.get("/clients/").get_data(as_text=True)
        db.session.remove()
        db.drop_all()
    assert 'class="page-header"' in html
    assert 'class="page-title"' in html
    assert "People and companies you build jobs for." in html
    assert html.count("button-primary") == 1
    assert 'href="/clients/new"' in html
    assert "register-table" in html
    assert "Maple Client" in html
    assert ">CRM<" not in html
    assert "data-table" not in html
    assert ">Open<" not in html


def test_crews_use_the_shared_register_without_an_action_column():
    application = _app()
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        ensure_office_user()
        crew = create_crew(name="Foundation crew", organization_id=DEFAULT_ORGANIZATION_ID)
        http = application.test_client()
        login_office_user(http)
        html = http.get("/settings/crews").get_data(as_text=True)
        db.session.remove()
        db.drop_all()
    assert 'class="page-header"' in html
    assert html.count("button-primary") == 1
    assert "Add crew" in html
    assert "register-row" in html
    assert f'href="/settings/crews/{crew.id}"' in html
    assert "Foundation crew" in html
    assert "Active" in html
    assert ">Open<" not in html
    assert ">Settings<" not in html
    assert "data-table" not in html

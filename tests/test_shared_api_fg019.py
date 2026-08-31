"""Dedicated FG-019 Shared API Foundation V1 tests."""

import inspect
import re

import pytest

from app import create_app, db
from app.models import Client, Organization, Project
from app.models.user import UserMembership
from app.routes import api_v1 as api_v1_module
from app.services.organizations import DEFAULT_ORGANIZATION_ID, ensure_default_organization
from app.services.shared_api import (
    ME_FIELDS,
    PROJECT_FIELDS,
    get_organization_project,
    list_organization_projects,
)
from tests.auth_fixtures import (
    DEFAULT_OFFICE_DISPLAY_NAME,
    DEFAULT_OFFICE_EMAIL,
    DEFAULT_OFFICE_PASSWORD,
    create_membership,
    create_user,
    ensure_office_user,
    login_office_user,
    logout_office_user,
)


ME_ALLOW_LIST = set(ME_FIELDS)
PROJECT_ALLOW_LIST = set(PROJECT_FIELDS)
FORBIDDEN_ME_KEYS = {
    "is_active",
    "password_hash",
    "password",
    "memberships",
    "roles",
    "permissions",
}
FORBIDDEN_PROJECT_KEYS = {
    "address",
    "description",
    "organization_id",
    "created_at",
    "estimates",
    "proposals",
    "margin",
    "cost",
}


def _csrf_token(response):
    html = response.get_data(as_text=True)
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if match is None:
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match is not None, html[:800]
    return match.group(1)


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-fg019",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def org_b(app):
    org = Organization(
        id="ORG-002",
        legal_name="Apex Contracting Ltd.",
        display_name="Apex Contracting",
        primary_address="100 Bay St, Toronto, ON",
        default_region="Greater Toronto Area",
        currency="CAD",
        tax_jurisdiction="Ontario (HST 13%)",
        is_active=True,
    )
    db.session.add(org)
    db.session.commit()
    return org


@pytest.fixture
def csrf_app():
    application = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "csrf-test-fg019",
        }
    )
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


def _add_project(*, name, organization_id, client_name, project_number=None, status="Lead"):
    row = Client(name=client_name, organization_id=organization_id)
    db.session.add(row)
    db.session.flush()
    project = Project(
        name=name,
        client_id=row.id,
        organization_id=organization_id,
        status=status,
        project_number=project_number,
        address="must-not-leak",
        description="must-not-leak-description",
    )
    db.session.add(project)
    db.session.commit()
    return project, row


def _assert_json_error(response, status):
    assert response.status_code == status
    assert response.is_json
    payload = response.get_json()
    assert set(payload.keys()) == {"error"}
    assert isinstance(payload["error"], str)
    assert payload["error"]
    return payload


def test_me_authenticated_allow_list(app, client):
    payload = client.get("/api/v1/me").get_json()
    assert client.get("/api/v1/me").status_code == 200
    user = ensure_office_user()
    assert set(payload.keys()) == ME_ALLOW_LIST
    assert payload["user_id"] == user.id
    assert payload["email"] == DEFAULT_OFFICE_EMAIL
    assert payload["display_name"] == DEFAULT_OFFICE_DISPLAY_NAME
    assert payload["organization_id"] == DEFAULT_ORGANIZATION_ID
    assert payload["organization_display_name"] == "Brayman Construction"
    for key in FORBIDDEN_ME_KEYS:
        assert key not in payload


@pytest.mark.no_office_auth
def test_me_unauthenticated_401_json(app, client):
    response = client.get("/api/v1/me", follow_redirects=False)
    payload = _assert_json_error(response, 401)
    assert "login" not in (response.headers.get("Location") or "").lower()
    assert "<html" not in response.get_data(as_text=True).lower()
    assert payload["error"] == "Authentication required."


@pytest.mark.no_office_auth
def test_projects_unauthenticated_401_json(app, client):
    response = client.get("/api/v1/projects", follow_redirects=False)
    _assert_json_error(response, 401)
    assert response.headers.get("Location") is None


@pytest.mark.no_office_auth
def test_inactive_user_401(app, client):
    user = ensure_office_user()
    login_office_user(client)
    assert client.get("/api/v1/me").status_code == 200
    user.is_active = False
    db.session.commit()
    response = client.get("/api/v1/me", follow_redirects=False)
    _assert_json_error(response, 401)


@pytest.mark.no_office_auth
def test_zero_memberships_403(app, client):
    create_user(
        email="nomember@example.com",
        password="no-member-password",
        display_name="No Member",
    )
    db.session.commit()
    login_office_user(client, email="nomember@example.com", password="no-member-password")
    response = client.get("/api/v1/me")
    _assert_json_error(response, 403)


@pytest.mark.no_office_auth
def test_multiple_memberships_403(app, client, org_b):
    user = create_user(
        email="multi@example.com",
        password="multi-password",
        display_name="Multi Org",
    )
    create_membership(user, "ORG-001")
    create_membership(user, "ORG-002")
    db.session.commit()
    login_office_user(client, email="multi@example.com", password="multi-password")
    response = client.get("/api/v1/projects")
    _assert_json_error(response, 403)


def test_membership_derived_organization(app, client):
    payload = client.get("/api/v1/me").get_json()
    membership = UserMembership.query.filter_by(
        user_id=payload["user_id"],
        is_active=True,
    ).one()
    assert payload["organization_id"] == membership.organization_id
    assert payload["organization_id"] == DEFAULT_ORGANIZATION_ID


def test_project_list_current_org_only(app, client, org_b):
    ours, ours_client = _add_project(
        name="ORG-001 House",
        organization_id="ORG-001",
        client_name="Brayman Client",
        project_number="P-001",
        status="Active",
    )
    foreign, _ = _add_project(
        name="Apex Secret Project",
        organization_id="ORG-002",
        client_name="Apex Secret Client",
        project_number="P-FOREIGN",
    )
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    rows = response.get_json()
    assert isinstance(rows, list)
    ids = {row["id"] for row in rows}
    assert ours.id in ids
    assert foreign.id not in ids
    assert all(row["id"] != foreign.id for row in rows)
    ours_row = next(row for row in rows if row["id"] == ours.id)
    assert set(ours_row.keys()) == PROJECT_ALLOW_LIST
    assert ours_row["name"] == "ORG-001 House"
    assert ours_row["project_number"] == "P-001"
    assert ours_row["status"] == "Active"
    assert ours_row["client_id"] == ours_client.id
    assert ours_row["client_name"] == "Brayman Client"
    for key in FORBIDDEN_PROJECT_KEYS:
        assert key not in ours_row
    assert "must-not-leak" not in response.get_data(as_text=True)


def test_project_detail_current_org(app, client, org_b):
    project, client_row = _add_project(
        name="Detail House",
        organization_id="ORG-001",
        client_name="Detail Client",
        project_number="P-DETAIL",
    )
    response = client.get(f"/api/v1/projects/{project.id}")
    assert response.status_code == 200
    payload = response.get_json()
    assert set(payload.keys()) == PROJECT_ALLOW_LIST
    assert payload["id"] == project.id
    assert payload["name"] == "Detail House"
    assert payload["project_number"] == "P-DETAIL"
    assert payload["status"] == "Lead"
    assert payload["client_id"] == client_row.id
    assert payload["client_name"] == "Detail Client"
    for key in FORBIDDEN_PROJECT_KEYS:
        assert key not in payload


def test_cross_org_project_detail_404(app, client, org_b):
    foreign, _ = _add_project(
        name="Apex Hidden",
        organization_id="ORG-002",
        client_name="Apex Hidden Client",
        project_number="P-HIDDEN",
    )
    response = client.get(f"/api/v1/projects/{foreign.id}")
    payload = _assert_json_error(response, 404)
    body = response.get_data(as_text=True)
    assert "Apex Hidden" not in body
    assert "Apex Hidden Client" not in body
    assert payload["error"] == "Not found."


def test_missing_project_404(app, client):
    response = client.get("/api/v1/projects/999999")
    _assert_json_error(response, 404)


def test_malformed_project_id_404_json(app, client):
    response = client.get("/api/v1/projects/not-an-id")
    _assert_json_error(response, 404)


def test_caller_cannot_override_org_via_query(app, client, org_b):
    ours, _ = _add_project(
        name="Stay Home",
        organization_id="ORG-001",
        client_name="Home Client",
        project_number="P-HOME",
    )
    foreign, _ = _add_project(
        name="Should Stay Hidden",
        organization_id="ORG-002",
        client_name="Foreign Client",
        project_number="P-QUERY",
    )
    response = client.get("/api/v1/projects?organization_id=ORG-002")
    assert response.status_code == 200
    ids = {row["id"] for row in response.get_json()}
    assert ours.id in ids
    assert foreign.id not in ids
    me = client.get("/api/v1/me?organization_id=ORG-002").get_json()
    assert me["organization_id"] == "ORG-001"


def test_caller_cannot_override_org_via_headers(app, client, org_b):
    ours, _ = _add_project(
        name="Header Home",
        organization_id="ORG-001",
        client_name="Header Client",
        project_number="P-HEADER",
    )
    foreign, _ = _add_project(
        name="Header Foreign",
        organization_id="ORG-002",
        client_name="Header Foreign Client",
        project_number="P-HEADER-F",
    )
    response = client.get(
        "/api/v1/projects",
        headers={
            "X-Organization-Id": "ORG-002",
            "Organization-Id": "ORG-002",
        },
    )
    ids = {row["id"] for row in response.get_json()}
    assert ours.id in ids
    assert foreign.id not in ids
    me = client.get(
        "/api/v1/me",
        headers={"X-Organization-Id": "ORG-002"},
    ).get_json()
    assert me["organization_id"] == "ORG-001"


def test_caller_cannot_override_org_via_json_body(app, client, org_b):
    ours, _ = _add_project(
        name="Body Home",
        organization_id="ORG-001",
        client_name="Body Client",
        project_number="P-BODY",
    )
    foreign, _ = _add_project(
        name="Body Foreign",
        organization_id="ORG-002",
        client_name="Body Foreign Client",
        project_number="P-BODY-F",
    )
    response = client.get(
        "/api/v1/projects",
        json={"organization_id": "ORG-002"},
    )
    ids = {row["id"] for row in response.get_json()}
    assert ours.id in ids
    assert foreign.id not in ids


def test_no_arbitrary_model_serialization(app, client):
    _add_project(
        name="Serialize House",
        organization_id="ORG-001",
        client_name="Serialize Client",
        project_number="P-SER",
    )
    me = client.get("/api/v1/me").get_json()
    projects = client.get("/api/v1/projects").get_json()
    assert "password_hash" not in me
    assert not any("sa_" in key or key.endswith("_sa_instance_state") for key in me)
    for row in projects:
        assert set(row.keys()) == PROJECT_ALLOW_LIST


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize(
    "path",
    ["/api/v1/me", "/api/v1/projects", "/api/v1/projects/1"],
)
def test_mutating_methods_405(app, client, method, path):
    response = getattr(client, method.lower())(path)
    _assert_json_error(response, 405)


def test_no_build_routes(app, client):
    for path in (
        "/api/v1/build",
        "/api/v1/today",
        "/api/v1/field",
        "/api/v1/notes",
        "/api/v1/photos",
        "/api/v1/labour-actuals",
    ):
        response = client.get(path)
        _assert_json_error(response, 404)


def test_office_session_works_with_api(app, client):
    office = client.get("/")
    assert office.status_code == 200
    api = client.get("/api/v1/me")
    assert api.status_code == 200
    office_again = client.get("/projects/")
    assert office_again.status_code == 200


@pytest.mark.no_office_auth
def test_office_html_unauthenticated_still_redirects(app, client):
    office = client.get("/", follow_redirects=False)
    assert office.status_code == 302
    assert "/login" in office.headers["Location"]
    api = client.get("/api/v1/me", follow_redirects=False)
    _assert_json_error(api, 401)


@pytest.mark.no_office_auth
def test_logout_then_api_401(app, client):
    ensure_office_user()
    login_office_user(client)
    assert client.get("/api/v1/me").status_code == 200
    logout_office_user(client)
    _assert_json_error(client.get("/api/v1/me", follow_redirects=False), 401)


def test_api_uses_org_scoped_project_query():
    source = inspect.getsource(list_organization_projects)
    assert "Project.query.filter_by" in source
    assert "organization_id" in source
    assert "assemble_project_hub" not in inspect.getsource(api_v1_module)
    detail_source = inspect.getsource(get_organization_project)
    assert "Project.query.filter_by" in detail_source
    assert "organization_id" in detail_source


def test_get_api_succeeds_without_csrf_token(csrf_app, csrf_client):
    with csrf_app.app_context():
        ensure_office_user()
        _add_project(
            name="CSRF House",
            organization_id="ORG-001",
            client_name="CSRF Client",
            project_number="P-CSRF",
        )
    token = _csrf_token(csrf_client.get("/login"))
    login = csrf_client.post(
        "/login",
        data={
            "email": DEFAULT_OFFICE_EMAIL,
            "password": DEFAULT_OFFICE_PASSWORD,
            "csrf_token": token,
        },
    )
    assert login.status_code == 302
    me = csrf_client.get("/api/v1/me")
    assert me.status_code == 200
    assert set(me.get_json().keys()) == ME_ALLOW_LIST
    projects = csrf_client.get("/api/v1/projects")
    assert projects.status_code == 200
    post = csrf_client.post("/api/v1/me")
    _assert_json_error(post, 405)
    missing_csrf = csrf_client.post("/clients/new", data={"name": "Must Fail CSRF"})
    assert missing_csrf.status_code == 400

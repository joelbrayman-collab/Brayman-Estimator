"""Security: signed-out sweep of every registered route. Synthetic data only.

Walks app.url_map, fills every path converter with a plausible value and requests each
allowed method (HEAD/OPTIONS skipped) with a client that was never signed in. Only the
endpoints exempted by protect_office_routes (app/__init__.py) may answer; every other
endpoint must hit the exact wall protect_office_routes builds:

- office pages: 302 to /login?next=<path> (flask-login unauthorized())
- /api/* GET (and the allowed Build field-event POSTs): 401 JSON "Authentication required."
- /api/* other mutating methods: 405 JSON from reject_api_mutating_methods, which runs first
- supplier_portal.*: 302 to /supplier/login?next=<path>

The exemption list is frozen here twice: the literal lists in the protect_office_routes
source, and the concrete set of endpoints they exempt today. A new public endpoint or a
new exemption fails this test until it is reviewed and added on purpose.
"""

from __future__ import annotations

import inspect
import re
from urllib.parse import parse_qs, urlparse

import pytest

import app as app_package
from app import _BUILD_API_POST_RE, create_app, db
from app.services.organizations import ensure_default_organization

pytestmark = pytest.mark.no_office_auth

METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")

# Frozen copy of the literal lists inside protect_office_routes.
EXPECTED_EXEMPT_ENDPOINT_LITERALS = {
    "static",
    "field_service_worker",
    "auth.login",
    "auth.logout",
    "auth.forgot_password",
    "auth.forgot_password_sent",
    "auth.reset_password",
    # Added 22 Oct 2026: the set-password link's landing page. Its one-use credential travels after "#"
    # (never sent to a server, so never logged) and is posted in the form body; same checks as above.
    "auth.reset_password_form",
    "auth.reset_password_complete",
    "favicon",
    # Added 18 Oct 2026 for the inactivity warning; both check the sign-in themselves
    # (status reports signed_in false, keep-alive answers 401) and expose nothing else.
    "session_status.status",
    "session_status.keepalive",
    # Added 19 Oct 2026 (Joel: Outlook / Google / Apple Calendar): the private calendar feed. The
    # secret key in the address is the only credential; a wrong, replaced or turned-off key, or a
    # person who has left, gets 404 (tests/test_calendar_sync.py). It only reads.
    "calendar_feed.feed",
}
# supplier_quote_link. added 20 Oct 2026 (Supplier PRO Desk): a supplier's walk-in customer opens and answers
# an issued quotation. The secret in the address is the only credential; a wrong, replaced or expired link
# gets 410 (tests/test_supplier_pro_desk.py). It shows one frozen quotation and records one answer.
EXPECTED_EXEMPT_PREFIXES = {"sign.", "proposal_link.", "walkthrough.", "decision_tools.", "supplier_quote_link.",
                            "training."}  # training.: own guard, 404 off the training site (21 Oct 2026)
EXPECTED_SUPPLIER_EXEMPT = {"supplier_portal.login", "supplier_portal.logout"}

# Frozen concrete set of endpoints the lists above exempt today. A new route under an
# exempt prefix (a new public page) must be added here deliberately.
EXPECTED_PUBLIC_ENDPOINTS = {
    "static",
    "field_service_worker",
    "favicon",
    "auth.login",
    "auth.logout",
    "auth.forgot_password",
    "auth.forgot_password_sent",
    "auth.reset_password",
    # Added 22 Oct 2026: the set-password link's landing page. Its one-use credential travels after "#"
    # (never sent to a server, so never logged) and is posted in the form body; same checks as above.
    "auth.reset_password_form",
    "auth.reset_password_complete",
    "sign.ceremony",
    "sign.document",
    "sign.executed",
    "sign.sign_accept",
    "sign.decline",
    "proposal_link.view",
    "proposal_link.accept",
    "proposal_link.decline",  # Joel, 21 Oct 2026: the client may decline on the link
    "proposal_link.pdf",
    "proposal_link.logo",
    "supplier_quote_link.view",
    "supplier_quote_link.pdf",
    "supplier_quote_link.answer",
    "walkthrough.form",
    "walkthrough.submit",
    "decision_tools.decision_tools_index",
    "decision_tools.employment_vs_entrepreneurship",
    "decision_tools.calculate_assessment",
    "decision_tools.download_results_pdf",
    "supplier_portal.login",
    "supplier_portal.logout",
    "session_status.status",
    "session_status.keepalive",
    "calendar_feed.feed",
}


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-security-route-sweep",
            "WTF_CSRF_ENABLED": False,
        }
    )
    # Observe an unhandled error as a 500 response instead of a raised exception.
    application.config["PROPAGATE_EXCEPTIONS"] = False
    with application.app_context():
        db.create_all()
        ensure_default_organization()
        yield application
        db.session.remove()
        db.drop_all()


def _protect_source() -> str:
    source = inspect.getsource(app_package._register_office_auth)
    start = source.index("def protect_office_routes")
    end = source.index("@app.errorhandler(404)")
    return source[start:end]


def _is_public(endpoint: str) -> bool:
    if endpoint in EXPECTED_EXEMPT_ENDPOINT_LITERALS or endpoint in EXPECTED_SUPPLIER_EXEMPT:
        return True
    # training. skips the office wall but is not public: it has its own guard (tested below).
    return any(endpoint.startswith(prefix) for prefix in EXPECTED_EXEMPT_PREFIXES - {"training."})


def _fill(rule) -> dict:
    values = {}
    for name, converter in rule._converters.items():
        kind = type(converter).__name__
        if kind == "IntegerConverter":
            values[name] = 1
        elif kind == "FloatConverter":
            values[name] = 1.0
        elif kind == "UUIDConverter":
            values[name] = "00000000-0000-4000-8000-000000000001"
        else:
            values[name] = "x"
    return values


def _requests(application):
    """Yield (rule, method, path, matched_endpoint) for every rule and allowed method."""
    adapter = application.url_map.bind("localhost")
    for rule in application.url_map.iter_rules():
        values = _fill(rule)
        built = rule.build(values, append_unknown=False)
        assert built is not None, rule.rule
        path = built[1]
        for method in METHODS:
            if method not in rule.methods:
                continue
            matched_endpoint, _args = adapter.match(path, method=method)
            yield rule, method, path, matched_endpoint


def _next_of(location: str) -> tuple[str, list[str]]:
    parsed = urlparse(location)
    return parsed.path, parse_qs(parsed.query).get("next", [])


def test_exemption_lists_in_code_are_frozen():
    source = _protect_source()
    literal_block = re.search(r'endpoint in \((.*?)\):', source, re.S)
    assert literal_block is not None
    literals = set(re.findall(r'"([^"]+)"', literal_block.group(1)))
    assert literals == EXPECTED_EXEMPT_ENDPOINT_LITERALS
    prefixes = set(re.findall(r'endpoint\.startswith\("([^"]+\.)"\)', source))
    # supplier_portal. is not an exemption: it is the supplier wall.
    assert prefixes - {"supplier_portal."} == EXPECTED_EXEMPT_PREFIXES
    supplier_block = re.search(
        r'if endpoint in \(("supplier_portal\.[^)]*)\):\s*return None', source
    )
    assert supplier_block is not None
    assert set(re.findall(r'"([^"]+)"', supplier_block.group(1))) == EXPECTED_SUPPLIER_EXEMPT
    assert 'request.path == "/favicon.ico"' in source


def test_public_endpoint_set_is_frozen(app):
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    assert {e for e in endpoints if _is_public(e)} == EXPECTED_PUBLIC_ENDPOINTS


def test_every_non_public_route_refuses_a_signed_out_request(app):
    answered = set()
    failures = []
    exercised = 0
    for rule, method, path, endpoint in _requests(app):
        client = app.test_client()
        response = client.open(path, method=method, follow_redirects=False)
        exercised += 1
        if 200 <= response.status_code < 300:
            answered.add(endpoint)
        if response.status_code >= 500:
            failures.append(f"{method} {path} ({endpoint}): server error {response.status_code}")
        if _is_public(endpoint):
            continue
        status = response.status_code
        problem = None
        if 200 <= status < 300:
            problem = "answered 2xx signed out"
        elif path == "/api" or path.startswith("/api/"):
            body = response.get_json(silent=True)
            if method == "GET" or (method == "POST" and _BUILD_API_POST_RE.fullmatch(path)):
                if status != 401 or body != {"error": "Authentication required."}:
                    problem = f"expected 401 JSON, got {status} {body}"
            else:
                if status != 405 or body != {"error": "Method not allowed."}:
                    problem = f"expected 405 JSON, got {status} {body}"
        elif endpoint.startswith("training."):  # Training Centre: not on this office at all (21 Oct 2026)
            if status != 404:
                problem = f"expected 404 off the training site, got {status}"
        elif endpoint.startswith(("supplier_portal.", "supplier_pro_desk.")):  # the supplier wall (PRO Desk: 20 Oct 2026)
            target, nxt = _next_of(response.headers.get("Location", ""))
            if status != 302 or target != "/supplier/login" or nxt != [path]:
                problem = f"expected 302 /supplier/login, got {status} {response.headers.get('Location')}"
        else:
            target, nxt = _next_of(response.headers.get("Location", ""))
            if status != 302 or target != "/login" or nxt != [path]:
                problem = f"expected 302 /login, got {status} {response.headers.get('Location')}"
        if problem:
            failures.append(f"{method} {path} ({endpoint}): {problem}")
    assert exercised > 400
    assert failures == []
    assert answered <= EXPECTED_PUBLIC_ENDPOINTS, sorted(answered - EXPECTED_PUBLIC_ENDPOINTS)


def test_signed_out_supplier_pages_redirect_to_supplier_login(app):
    client = app.test_client()
    for path in ("/supplier/", "/supplier/1/", "/supplier/1/requests/1", "/supplier/1/logo"):
        response = client.get(path)
        assert response.status_code == 302, path
        target, nxt = _next_of(response.headers["Location"])
        assert target == "/supplier/login", path
        assert nxt == [path]
    assert client.get("/supplier/login").status_code == 200


# Added 21 Oct 2026 (People & Access, owner / System Administrator only): the new office pages are
# registered, none is public, and signed out each goes to the office sign-in.
EXPECTED_PEOPLE_ACCESS_ENDPOINTS = {
    "people_access.index",
    "people_access.new",
    "people_access.detail",
    "people_access.deactivate",
    "people_access.reactivate",
    "people_access.send_link",
    "people_access.access",
    "people_access.administrator",
    "people_access.field_only",
}


def test_people_access_pages_are_registered_and_never_public(app):
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules() if rule.endpoint.startswith("people_access.")}
    assert endpoints == EXPECTED_PEOPLE_ACCESS_ENDPOINTS
    assert not any(_is_public(e) for e in endpoints)
    client = app.test_client()
    for path, method in (("/settings/people", "GET"), ("/settings/people/new", "POST"), ("/settings/people/1/deactivate", "POST")):
        response = client.open(path, method=method)
        target, nxt = _next_of(response.headers.get("Location", ""))
        assert response.status_code == 302 and target == "/login" and nxt == [path], path


# ---------------------------------------------------------------------------------------------------
# Field-only members (Joel, 21 Oct 2026, V1 defect: crew reached office costs). A membership marked
# FIELD_ONLY (app/services/access_domains.py set_field_only) reaches only these endpoints besides the
# public ones above. Frozen: widening what crew can open must be a deliberate change here.
EXPECTED_FIELD_ONLY_ENDPOINTS = {
    "field.field_root",
    "field.today",
    "field.print_today",
    "field.week",
    "field.month",
    "field.schedule_today",
    "field.company_today",
    "field.projects",
    "field.project_confirm",
    "field.capture",
    "field.extra_work",
    "field.my_time",
    "field.time_entry",
    "field.drawings",  # job drawings and plans for assigned jobs, read only (Crew Access, 21 Oct 2026)
    "field.drawing_pdf",
    "field.plan_pdf",
    "field.workflow",  # the simplified Field workflow: Field destinations only (Workflow Maps, 21 Oct 2026)
    "auth.change_password",
    "help.ask_help",
    "api_v1.me",
    "api_v1.list_projects",
    "api_v1.get_project",
    "api_v1.field_events",
    "api_v1.field_event_detail",
    "api_v1.field_event_originals",
    "api_v1.field_event_original_detail",
    "api_v1.field_event_original_content",
    "api_v1.field_event_original_display",
}
FIELD_WALL_JSON = {"error": "Not available to field users."}


def test_field_only_endpoint_set_is_frozen(app):
    from app.services.access_domains import field_only_endpoint_allowed

    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}
    allowed = {e for e in endpoints if not _is_public(e) and field_only_endpoint_allowed(e)}
    assert allowed == EXPECTED_FIELD_ONLY_ENDPOINTS


def _field_only_client(app):
    from app.models.user import UserMembership
    from app.services.access_domains import set_field_only
    from app.services.instance_authority import set_instance_owner
    from app.services.organizations import DEFAULT_ORGANIZATION_ID
    from tests.auth_fixtures import ensure_office_user, login_office_user

    owner = ensure_office_user(email="owner.sweep@example.invalid", password="owner-pw", display_name="Owner")
    owner_membership = UserMembership.query.filter_by(user_id=owner.id).one()
    set_instance_owner(DEFAULT_ORGANIZATION_ID, owner_membership.id, owner.id)
    crew = ensure_office_user(email="crew.sweep@example.invalid", password="crew-pw", display_name="Crew")
    set_field_only(UserMembership.query.filter_by(user_id=crew.id).one(), True, owner)
    client = app.test_client()
    assert login_office_user(client, "crew.sweep@example.invalid", "crew-pw").status_code == 302
    return client


def test_every_office_route_refuses_a_signed_in_field_only_user(app):
    client = _field_only_client(app)
    failures = []
    exercised = 0
    for rule, method, path, endpoint in _requests(app):
        if _is_public(endpoint) or endpoint in EXPECTED_FIELD_ONLY_ENDPOINTS:
            continue
        response = client.open(path, method=method, follow_redirects=False)
        exercised += 1
        status = response.status_code
        problem = None
        if path == "/api" or path.startswith("/api/"):
            body = response.get_json(silent=True)
            if method == "GET" or (method == "POST" and _BUILD_API_POST_RE.fullmatch(path)):
                if status != 403 or body != FIELD_WALL_JSON:
                    problem = f"expected 403 field wall JSON, got {status} {body}"
            elif status != 405:
                problem = f"expected 405, got {status}"
        elif endpoint.startswith("training."):  # Training Centre: not on this office at all (21 Oct 2026)
            if status != 404:
                problem = f"expected 404 off the training site, got {status}"
        elif endpoint.startswith(("supplier_portal.", "supplier_pro_desk.")):
            if status != 403:
                problem = f"expected 403 (supplier wall), got {status}"
        elif method == "GET":
            # The office Workflow Guide sends a Field sign-in to the Field workflow instead (21 Oct 2026).
            expected = "/field/workflow" if endpoint == "workflow_map.contractor" else "/field/today"
            if status != 302 or urlparse(response.headers.get("Location", "")).path != expected:
                problem = f"expected 302 {expected}, got {status} {response.headers.get('Location')}"
        elif status != 403:
            problem = f"expected 403, got {status}"
        if problem:
            failures.append(f"{method} {path} ({endpoint}): {problem}")
    assert exercised > 400
    assert failures == []


def test_field_only_user_still_reaches_field_endpoints(app):
    client = _field_only_client(app)
    failures = []
    for rule, method, path, endpoint in _requests(app):
        if endpoint not in EXPECTED_FIELD_ONLY_ENDPOINTS or method != "GET":
            continue
        response = client.open(path, method=method, follow_redirects=False)
        if response.status_code == 403 or response.status_code >= 500:
            failures.append(f"{method} {path} ({endpoint}): {response.status_code}")
        if response.status_code == 302 and not urlparse(response.headers["Location"]).path.startswith("/field"):
            failures.append(f"{method} {path} ({endpoint}): left Field for {response.headers['Location']}")
    assert failures == []


# Added 21 Oct 2026 (Training & Acceptance Centre): on the training site, signed out goes to the training
# sign-in; a field-only crew member reaches their training but not the administrator page.
def test_training_centre_guard_on_the_training_site():
    from app import create_app, db
    from app.training import environment

    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "x",
                              "WTF_CSRF_ENABLED": False, "TRAINING_ENVIRONMENT": True})
    with application.app_context():
        db.create_all()
        pw = {k: f"Synthetic-{k}-sweep-1" for k in ("ben", "olivia", "kevin", "liam", "darcy", "pat")}
        environment.build(application, pw)
        rules = [r for r in application.url_map.iter_rules() if r.endpoint.startswith("training.")]
        client = application.test_client()
        for rule in rules:
            path = rule.rule.replace("<key>", "c01-sign-in")
            for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
                r = client.open(path, method=method)
                if rule.endpoint == "training.signin":
                    assert r.status_code == 200
                else:
                    assert r.status_code == 302 and r.headers["Location"].endswith("/training/signin"), (method, path)
        crew = application.test_client()
        crew.post("/login", data={"email": "kevin@training.calibraytai.invalid", "password": pw["kevin"]})
        assert crew.get("/training").status_code == 200
        assert crew.get("/training/admin").status_code == 403
        assert crew.get("/projects/").headers["Location"].endswith("/field/today")  # the field wall still holds
        db.drop_all()

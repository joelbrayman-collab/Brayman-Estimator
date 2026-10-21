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
EXPECTED_EXEMPT_PREFIXES = {"sign.", "proposal_link.", "walkthrough.", "decision_tools.", "supplier_quote_link."}
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
    return any(endpoint.startswith(prefix) for prefix in EXPECTED_EXEMPT_PREFIXES)


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

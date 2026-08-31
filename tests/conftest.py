"""Shared test fixtures. Auth helpers only — does not change collection semantics."""

import pytest

from tests.auth_fixtures import ensure_office_user, login_office_user


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_office_auth: do not auto-login the office HTTP test client",
    )


@pytest.fixture(autouse=True)
def _authenticate_office_http_client(request):
    if request.node.get_closest_marker("no_office_auth"):
        return
    if "client" not in request.fixturenames:
        return
    app = request.getfixturevalue("app")
    client = request.getfixturevalue("client")
    with app.app_context():
        ensure_office_user()
    login_office_user(client)

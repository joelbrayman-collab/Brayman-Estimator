"""Shared test fixtures. Auth helpers only — does not change collection semantics."""

import os
from pathlib import Path

import pytest

from tests.auth_fixtures import ensure_office_user, login_office_user


FAMILY_05_MASTER_ENV = "CALIBRAYTAI_FAMILY_05_MASTER_PATH"


def _point_tests_at_family_05_master():
    """Tests only: a machine without the office Mac's Documents folder (the cloud
    workspace) names its copy of the confidential Family 05 master here. The copy
    lives outside the repository and is never committed. Production code is
    unchanged: it still reads app config or the Mac default, and refuses on hosted.
    The tests still check the copy against the governed SHA-256."""
    configured = os.environ.get(FAMILY_05_MASTER_ENV, "").strip()
    if not configured:
        return
    from app.services import family_05_master

    family_05_master.DEFAULT_FAMILY_05_MASTER_PATH = Path(configured)


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_office_auth: do not auto-login the office HTTP test client",
    )
    _point_tests_at_family_05_master()


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

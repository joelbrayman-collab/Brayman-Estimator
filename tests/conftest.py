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


# Test files whose contract tests need the confidential Family 05 master (Joel, 20 Oct 2026: report the
# dependency clearly instead of letting it read as an application failure). Nothing is skipped.
FAMILY_05_DEPENDENT_FILES = frozenset({
    "test_account_recovery_auth_d_fg034.py", "test_contract_generation_fg024.py",
    "test_contract_generation_policy_fg024.py", "test_family_05_contract_merge_fg024.py",
    "test_native_signing_sign_a_fg033.py", "test_native_signing_sign_b_fg033.py",
    "test_native_signing_sign_e_fg033.py", "test_security_contract_download.py",
    "test_signing_mail_b_fg034.py", "test_synthetic_ontario_contract_uat_fg024.py",
})
_MASTER_STATE = {"status": None, "path": None, "failed": [], "other_failed": 0}


def family_05_master_status():
    """('present' | 'missing' | 'sha-mismatch', path) for the master the tests will read."""
    import hashlib

    from app.services import family_05_master

    path = Path(family_05_master.DEFAULT_FAMILY_05_MASTER_PATH)
    if not path.is_file():
        return "missing", path
    if hashlib.sha256(path.read_bytes()).hexdigest() != family_05_master.FAMILY_05_MASTER_SHA256:
        return "sha-mismatch", path
    return "present", path


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "no_office_auth: do not auto-login the office HTTP test client",
    )
    _point_tests_at_family_05_master()
    _MASTER_STATE["status"], _MASTER_STATE["path"] = family_05_master_status()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if not report.failed:
        return
    text = str(report.longrepr or "")
    if _MASTER_STATE["status"] != "present" and (
            Path(str(item.fspath)).name in FAMILY_05_DEPENDENT_FILES or "MISSING_PRESENTATION_MASTER" in text):
        _MASTER_STATE["failed"].append(item.nodeid)
        report.sections.append(("Missing test dependency", "The confidential Family 05 contract master is "
                                f"{_MASTER_STATE['status']} at {_MASTER_STATE['path']}. See docs/testing/test-environment.md."))
    else:
        _MASTER_STATE["other_failed"] += 1


def pytest_terminal_summary(terminalreporter):
    status, path = _MASTER_STATE["status"], _MASTER_STATE["path"]
    if status == "present":
        terminalreporter.write_line("FAMILY_05_MASTER=present (SHA-256 matches the governed file); contract tests ran normally")
        return
    tr = terminalreporter
    if not _MASTER_STATE["failed"]:
        tr.write_line(f"FAMILY_05_MASTER={status} at {path}; no test in this run needed it")
        return
    tr.section("MISSING TEST DEPENDENCY — not an application failure", sep="=", red=True, bold=True)
    tr.write_line(f"FAMILY_05_MASTER={status} at {path}")
    tr.write_line(f"Failures in the contract tests that need it: {len(_MASTER_STATE['failed'])}")
    tr.write_line(f"Other failures (NOT explained by this fixture): {_MASTER_STATE['other_failed']}")
    tr.write_line("The run still counts as failed. Fix: set CALIBRAYTAI_FAMILY_05_MASTER_PATH to a copy kept outside the "
                  "repository (never commit it); see docs/testing/test-environment.md. The Mac release gate requires it.")


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

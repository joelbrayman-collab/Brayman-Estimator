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
    # Approved Master Template Family V1 (27 Oct 2026): the real-master contract test reads the same
    # confidential folder (CALIBRAYTAI_APPROVED_MASTER_DIR on a machine without the office Mac's Documents).
    "test_approved_master_governance.py",
})
_MASTER_STATE = {"status": None, "path": None, "failed": [], "other_failed": 0, "worker": False}


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
    _MASTER_STATE["worker"] = _is_xdist_worker(config)
    # Faster gate (2 Nov 2026): db.create_all() on a fresh in-memory test database restores a cached copy of the
    # empty schema instead of re-running ~1,000 DDL statements, and the PBKDF2 password check is memoised per exact
    # (hash, password) pair. Neither changes what a test sees; see tests/fast_fixtures.py for when each applies.
    from app import db
    from tests import fast_fixtures

    fast_fixtures.install_schema_cache(db)
    fast_fixtures.install_password_check_cache()


def _is_xdist_worker(config) -> bool:
    """True inside a pytest-xdist worker process (the gate runs `-n auto`; faster gate, 2 Nov 2026)."""
    return hasattr(config, "workerinput")


def _master_dependent(nodeid: str, text: str) -> bool:
    return (Path(nodeid.split("::", 1)[0]).name in FAMILY_05_DEPENDENT_FILES
            or "MISSING_PRESENTATION_MASTER" in text)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach the missing-master explanation to the failure itself (runs where the test runs; under xdist the
    section travels back to the controller with the report)."""
    outcome = yield
    report = outcome.get_result()
    if not report.failed or _MASTER_STATE["status"] == "present":
        return
    if _master_dependent(item.nodeid, str(report.longrepr or "")):
        report.sections.append(("Missing test dependency", "The confidential Family 05 contract master is "
                                f"{_MASTER_STATE['status']} at {_MASTER_STATE['path']}. See docs/testing/test-environment.md."))


def pytest_runtest_logreport(report):
    """Count failures for the end-of-run summary. This hook runs in the process that prints the summary: the only
    process in a serial run, the controller under xdist (workers forward every report), so the totals cover all
    workers. Workers do not count, so nothing is counted twice."""
    if not report.failed or _MASTER_STATE.get("worker"):
        return
    if _MASTER_STATE["status"] != "present" and _master_dependent(report.nodeid, str(report.longrepr or "")):
        _MASTER_STATE["failed"].append(report.nodeid)
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

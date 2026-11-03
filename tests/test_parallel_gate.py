"""The release gate's parallel full regression (faster gate, 2 Nov 2026).

The gate runs the complete suite with pytest-xdist (`-n auto --dist loadfile`). Nothing is skipped or excluded:
these tests check that the gate still demands every test case in the junit XML, that the Family 05 missing-master
summary counts failures from every worker (and once only), and that test apps never share the repository's
instance/ folder, which parallel workers would otherwise write into at the same time.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app import create_app

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "tools" / "release" / "release_gate.sh"


def _code(path: Path) -> str:
    return "\n".join(line for line in path.read_text().splitlines() if not line.lstrip().startswith("#"))


def test_gate_runs_the_whole_suite_in_parallel_and_still_reads_every_case():
    code = _code(GATE)
    assert 'XDIST="-n ${PYTEST_WORKERS:-auto} --dist loadfile"' in code
    run = next(line for line in code.splitlines() if "$PYTEST -q" in line)
    assert run.startswith('$PYTEST -q -rfEs $XDIST --junitxml="$OUT-junit.xml" tests ')
    # Nothing narrows the run: no -k, -m, --deselect, --ignore or file list besides tests/.
    for narrowing in (" -k ", " -m ", "--deselect", "--ignore", "-x ", "--maxfail", "--lf"):
        assert narrowing not in run, narrowing
    # The XML must list as many passing test cases as the summary line counts, then the no-skip and walk checks.
    assert '"$OUT-junit.xml" "$OUT-full.txt"' in code and "int(summary[-1]) != listed" in code
    assert 'clean("tests.test_contractor_workflow_e2e") and clean("tests.test_cal_find_it")' in code


def test_xdist_is_a_pinned_dev_dependency():
    dev = (ROOT / "requirements-dev.txt").read_text()
    assert "pytest-xdist==3.8.0" in dev and "execnet==2.1.1" in dev
    assert "xdist" not in (ROOT / "requirements.txt").read_text()


def test_test_apps_keep_uploads_out_of_the_shared_instance_folder():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "x"})
    instance = Path(app.instance_path).resolve()
    for key in ("PLAN_UPLOAD_ROOT", "HISTORICAL_UPLOAD_ROOT", "DECK_TAKEOFF_ROOT", "DOCUMENT_ROOT",
                "MAIL_CAPTURE_ROOT", "BRAND_LOGO_ROOT", "SIGNING_ARTIFACT_ROOT", "CONTRACT_ARTIFACT_ROOT"):
        folder = Path(app.config[key]).resolve()
        assert folder.is_dir(), key
        assert instance not in folder.parents and folder != instance, key
    other = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "x"})
    assert other.config["PLAN_UPLOAD_ROOT"] != app.config["PLAN_UPLOAD_ROOT"]
    # An explicit folder is still used as given.
    named = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "x",
                        "PLAN_UPLOAD_ROOT": "/somewhere/plans"})
    assert named.config["PLAN_UPLOAD_ROOT"] == "/somewhere/plans"


def _run_inner_suite(tmp_path, *extra):
    """A tiny suite that uses this repository's conftest: one failure in a Family 05 dependent file, one elsewhere."""
    (tmp_path / "conftest.py").write_text("from tests.conftest import *  # noqa: F401,F403\n")
    (tmp_path / "test_contract_generation_fg024.py").write_text(
        "def test_needs_the_master():\n    assert False\n\ndef test_fine():\n    pass\n")
    (tmp_path / "test_unrelated.py").write_text(
        "def test_unrelated_failure():\n    assert False\n\ndef test_fine_too():\n    pass\n")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTEST_", "COV_"))}
    env["PYTHONPATH"] = str(ROOT)
    env["CALIBRAYTAI_FAMILY_05_MASTER_PATH"] = str(tmp_path / "absent-master.docx")
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--rootdir", str(tmp_path), *extra,
         str(tmp_path)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300,
    )


def _check_summary(result):
    out = result.stdout + result.stderr
    assert result.returncode == 1, out
    assert "2 failed, 2 passed" in out, out
    assert "MISSING TEST DEPENDENCY" in out, out
    assert "Failures in the contract tests that need it: 1" in out, out
    assert "Other failures (NOT explained by this fixture): 1" in out, out
    assert "Missing test dependency" in out, out  # the explanation attached to the failure itself


def test_missing_master_summary_serial(tmp_path):
    _check_summary(_run_inner_suite(tmp_path))


def test_missing_master_summary_counts_every_worker_once(tmp_path):
    _check_summary(_run_inner_suite(tmp_path, "-n", "2", "--dist", "loadfile"))


def _dump(app_):
    from app import db

    with app_.app_context():
        with db.engine.connect() as connection:
            raw = connection.connection.driver_connection
            return list(raw.iterdump()), raw.execute("PRAGMA user_version").fetchone()


def _fresh_app():
    return create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "x"})


def test_cached_schema_is_exactly_what_create_all_builds():
    from app import db
    from tests import fast_fixtures

    assert getattr(db, "_schema_cache_installed", False)
    first, second, real = _fresh_app(), _fresh_app(), _fresh_app()
    with first.app_context():
        db.create_all()  # real create_all, or a copy if an earlier test in this process made the template
    before = fast_fixtures.STATS["copied"]
    with second.app_context():
        db.create_all()
    assert fast_fixtures.STATS["copied"] == before + 1  # the copy path ran
    with real.app_context():
        type(db).create_all(db)  # the unwrapped Flask-SQLAlchemy create_all
    assert _dump(second) == _dump(real) == _dump(first)
    dump, _ = _dump(second)
    assert any("CREATE TRIGGER" in line and "document_events_no_update" in line for line in dump)
    with second.app_context():
        from sqlalchemy import inspect, text

        names = inspect(db.engine).get_table_names()
        assert len(names) >= len(db.metadata.tables)
        for name in db.metadata.tables:
            assert db.session.execute(text(f'SELECT count(*) FROM "{name}"')).scalar() == 0, name


def test_cached_schema_is_not_used_on_a_database_that_already_has_tables():
    from sqlalchemy import text

    from app import db
    from tests import fast_fixtures

    app_ = _fresh_app()
    with app_.app_context():
        db.create_all()
        db.session.execute(text("CREATE TABLE keep_me (x INTEGER)"))
        db.session.execute(text("INSERT INTO keep_me VALUES (7)"))
        db.session.commit()
        real_before = fast_fixtures.STATS["real"]
        db.create_all()  # not empty: the real create_all, which leaves existing tables and rows alone
        assert fast_fixtures.STATS["real"] == real_before + 1
        assert db.session.execute(text("SELECT x FROM keep_me")).scalar() == 7


def test_file_databases_never_use_the_cached_schema(tmp_path):
    from app import db
    from tests import fast_fixtures

    app_ = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "t.db"),
                       "SECRET_KEY": "x"})
    with app_.app_context():
        copied = fast_fixtures.STATS["copied"]
        db.create_all()
        assert fast_fixtures.STATS["copied"] == copied
        db.session.remove()
        db.engine.dispose()


def test_password_check_memo_gives_the_real_answer_for_every_pair():
    from werkzeug.security import check_password_hash as real_check

    from app.services import auth
    from tests import fast_fixtures

    assert getattr(auth.check_password_hash, "_test_memo", False)
    stored = fast_fixtures.office_password_hash("office-test-password")
    assert stored == fast_fixtures.office_password_hash("office-test-password")  # made once per process
    assert stored.startswith(auth.PASSWORD_HASH_METHOD + ":")
    assert real_check(stored, "office-test-password")
    fresh = auth.hash_password("office-test-password")  # the app's own hashing is untouched: a new salt each time
    assert fresh != stored and fresh.split("$")[0] == stored.split("$")[0]
    for pwhash, password in ((stored, "office-test-password"), (stored, "wrong-password"),
                             (fresh, "office-test-password"), (fresh, "Office-test-password"), (stored, "")):
        expected = real_check(pwhash, password)
        assert auth.verify_password(pwhash, password) is expected
        assert auth.verify_password(pwhash, password) is expected  # second answer comes from the memo


def test_a_test_app_leaves_no_calibai_folders_behind(tmp_path, monkeypatch):
    import gc
    import tempfile

    scratch = tmp_path / "tmp"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))
    app_ = _fresh_app()
    made = sorted(p.name for p in scratch.iterdir())
    assert len(made) == 11 and all(name.startswith("calibai-") for name in made), made
    (Path(app_.config["PLAN_UPLOAD_ROOT"]) / "1").mkdir()
    (Path(app_.config["PLAN_UPLOAD_ROOT"]) / "1" / "a.pdf").write_bytes(b"%PDF-1.4 synthetic")
    del app_
    gc.collect()
    assert list(scratch.iterdir()) == []


def test_test_app_folders_are_removed_at_process_exit_even_if_the_app_lives(tmp_path):
    scratch = tmp_path / "tmp"
    scratch.mkdir()
    code = ("import sys; sys.path.insert(0, %r)\n"
            "from app import create_app\n"
            "KEEP = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'SECRET_KEY': 'x'})\n"
            "import os; print(len(os.listdir(%r)))\n") % (str(ROOT), str(scratch))
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTEST_")}
    env["TMPDIR"] = str(scratch)
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "11"  # they existed while it ran
    assert list(scratch.iterdir()) == []


def test_a_page_server_removes_its_temporary_files_when_stopped(tmp_path):
    import signal
    import socket
    import time

    scratch = tmp_path / "tmp"
    scratch.mkdir()
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTEST_")}
    env.update(TMPDIR=str(scratch), CONCRETE_PAGE_PORT=str(port))
    server = subprocess.Popen([sys.executable, str(ROOT / "tests" / "concrete_page_server.py")], cwd=ROOT, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        line = server.stdout.readline()
        assert line.strip() == f"READY {port}", line
        assert [p.name.startswith("calibai-page-server-") for p in scratch.iterdir()] == [True]
        assert any(scratch.rglob("concrete-page-*.db"))
        server.send_signal(signal.SIGTERM)
        server.wait(timeout=60)
    finally:
        if server.poll() is None:
            server.kill()
            server.wait()
    deadline = time.time() + 10
    while list(scratch.iterdir()) and time.time() < deadline:
        time.sleep(0.2)
    assert list(scratch.iterdir()) == []


def test_every_callable_create_listener_has_been_reviewed_for_the_schema_cache():
    """Review, 3 Nov 2026: a create listener that decides its DDL at run time could make a cached copy differ from a
    real create_all(). Each one must be reviewed and named in tests/fast_fixtures.py before the cache may copy it."""
    from app import db
    from tests import fast_fixtures

    found = set()
    for dispatch in [db.metadata.dispatch] + [t.dispatch for t in db.metadata.sorted_tables]:
        for key in fast_fixtures._listener_keys(dispatch):
            if key[1] == "callable":
                found.add(key[2] + "." + key[3])
    assert found == fast_fixtures.REVIEWED_CALLABLE_CREATE_LISTENERS


def test_a_new_or_changed_create_listener_gets_a_real_create_all():
    """The fingerprint covers every table- and metadata-level create listener (the full DDL text, or a function's
    code), so a listener added or changed in the process is built for real, never served from an older copy."""
    from sqlalchemy import DDL, event, inspect

    from app import db
    from tests import fast_fixtures

    warm = _fresh_app()
    with warm.app_context():
        db.create_all()  # a template exists for the unchanged models
    table = db.metadata.tables["document_events"]
    for target, probe in ((table, "zz_table_listener_probe"), (db.metadata, "zz_metadata_listener_probe")):
        listener = DDL(f"CREATE TABLE {probe} (x INTEGER)")
        event.listen(target, "after_create", listener)
        try:
            app_ = _fresh_app()
            with app_.app_context():
                real = fast_fixtures.STATS["real"]
                db.create_all()
                assert fast_fixtures.STATS["real"] == real + 1, probe
                assert probe in inspect(db.engine).get_table_names()
        finally:
            event.remove(target, "after_create", listener)
    after = _fresh_app()
    with after.app_context():
        copied = fast_fixtures.STATS["copied"]
        db.create_all()  # listeners removed: the original template again, without the probe tables
        assert fast_fixtures.STATS["copied"] == copied + 1
        names = inspect(db.engine).get_table_names()
        assert "zz_table_listener_probe" not in names and "zz_metadata_listener_probe" not in names

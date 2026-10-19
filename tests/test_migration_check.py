"""tools/release/migration_check.py: rehearse and apply a release migration (Joel, 19 Oct 2026).

Synthetic databases only. The real rehearsal runs in the release gate on a copy of the fresh
production backup; the real apply runs on the Render instance after Joel's authorization.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from app import create_app

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "release" / "migration_check.py"
PRIOR, HEAD = "y2b3c4d5e6f7", "z3c4d5e6f7a8"
NEW = "company_appointments,company_appointment_attendees,company_appointment_history,calendar_feed_keys"


def _database_at_prior(path: Path) -> None:
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})
    with app.app_context():
        cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "migrations"))
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
        command.upgrade(cfg, PRIOR)
    con = sqlite3.connect(path)
    con.execute("INSERT INTO organizations (id, legal_name, display_name, primary_address, default_region, currency, "
                "tax_jurisdiction, is_active, created_at, updated_at) VALUES ('ORG-RH', 'Synthetic Ltd.', 'Synthetic', "
                "'1 Test Rd', 'Ontario', 'CAD', 'Ontario (HST 13%)', 1, '2026-10-19 00:00:00', '2026-10-19 00:00:00')")
    con.commit()
    con.close()


def _run(*args, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True,
                          env={**os.environ, **(env or {})}, timeout=300)


def _values(text):
    return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)


def test_rehearsal_proves_existing_records_unchanged_and_new_tables_empty(tmp_path):
    db = tmp_path / "copy.db"
    _database_at_prior(db)
    result = _run("rehearse", "--db", str(db), "--from", PRIOR, "--to", HEAD, "--new-tables", NEW)
    values = _values(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
    assert values["MIGRATION_REHEARSAL"] == "ok" and values["REVISION_AFTER"] == HEAD and values["INTEGRITY_AFTER"] == "ok"
    assert "schema and every row identical" in values["EXISTING_TABLES_UNCHANGED"]
    assert values["NEW_TABLES"].startswith("calendar_feed_keys,company_appointment_attendees")


def test_rehearsal_stops_on_the_wrong_starting_revision(tmp_path):
    db = tmp_path / "copy.db"
    _database_at_prior(db)
    result = _run("rehearse", "--db", str(db), "--from", "x1a2b3c4d5e6", "--to", HEAD, "--new-tables", NEW)
    assert result.returncode == 1 and "FAIL=copy is at y2b3c4d5e6f7" in result.stdout


def test_rehearsal_stops_when_the_expected_tables_differ(tmp_path):
    db = tmp_path / "copy.db"
    _database_at_prior(db)
    result = _run("rehearse", "--db", str(db), "--from", PRIOR, "--to", HEAD, "--new-tables", "company_appointments")
    assert result.returncode == 1 and "FAIL=new tables are" in result.stdout


def test_apply_backs_up_first_refuses_the_wrong_release_and_is_safe_to_repeat(tmp_path):
    instance = tmp_path / "instance"
    instance.mkdir()
    db = instance / "brayman_estimator.db"
    _database_at_prior(db)
    env = {"RELEASE_ROOT": str(tmp_path), "CALIBRAYTAI_DATABASE_URI": f"sqlite:///{db}", "RENDER_GIT_COMMIT": "a" * 40}
    wrong = _run("apply", "--from", PRIOR, "--to", HEAD, "--new-tables", NEW, "--expect-sha", "b" * 40, "--label", "t",
                 env=env)
    assert wrong.returncode == 1 and "not the authorized release" in wrong.stdout
    assert not (instance / "backups").exists()
    ok = _run("apply", "--from", PRIOR, "--to", HEAD, "--new-tables", NEW, "--expect-sha", "a" * 40, "--label", "t", env=env)
    values = _values(ok.stdout)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert values["MIGRATE"] == "ok" and values["REVISION_AFTER"] == HEAD
    backup = Path(values["PRE_MIGRATION_BACKUP"])
    assert backup.parent == instance / "backups" and backup.name.startswith("pre-migrate-t-")
    con = sqlite3.connect(backup)
    assert con.execute("SELECT version_num FROM alembic_version").fetchone()[0] == PRIOR  # the recovery point
    con.close()
    again = _run("apply", "--from", PRIOR, "--to", HEAD, "--new-tables", NEW, "--expect-sha", "a" * 40, "--label", "t", env=env)
    assert again.returncode == 0 and "ALREADY_MIGRATED=yes" in again.stdout
    assert len(list((instance / "backups").iterdir())) == 1

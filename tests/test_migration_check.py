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


def _instance_layout(tmp_path: Path) -> Path:
    """A folder shaped like the Render instance (/opt/render/project/src): the app, its migrations, the
    release helper and instance/brayman_estimator.db at the previous revision."""
    src = tmp_path / "opt" / "render" / "project" / "src"
    (src / "tools" / "release").mkdir(parents=True)
    (src / "tools" / "release" / "migration_check.py").write_bytes(SCRIPT.read_bytes())
    (src / "app").symlink_to(ROOT / "app")
    (src / "migrations").symlink_to(ROOT / "migrations")
    (src / "instance").mkdir()
    _database_at_prior(src / "instance" / "brayman_estimator.db")
    return src


def _hosted_env(src: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "RELEASE_ROOT"}
    env.update({"CALIBRAYTAI_DATABASE_URI": f"sqlite:///{src / 'instance' / 'brayman_estimator.db'}",
                "RENDER_GIT_COMMIT": "a" * 40})
    return env


APPLY = ["apply", "--from", PRIOR, "--to", HEAD, "--new-tables", NEW, "--expect-sha", "a" * 40, "--label", "t"]


def test_apply_run_as_the_instance_file_finds_the_live_database(tmp_path):
    # What release_migrate.sh runs on Render (20 Oct 2026): the deployed file itself, no RELEASE_ROOT.
    src = _instance_layout(tmp_path)
    result = subprocess.run([sys.executable, "tools/release/migration_check.py", *APPLY], cwd=src,
                            env=_hosted_env(src), capture_output=True, text=True)
    assert result.returncode == 0 and "MIGRATE=ok" in result.stdout, result.stdout + result.stderr
    assert len(list((src / "instance" / "backups").iterdir())) == 1


def test_apply_piped_from_the_instance_folder_finds_the_live_database(tmp_path):
    # Piped (python - < migration_check.py), Python names the file "<stdin>"; the root must be the
    # current folder, not two levels above it (the 20 Oct stop: "does not point at /opt/render/instance").
    src = _instance_layout(tmp_path)
    result = subprocess.run([sys.executable, "-", *APPLY], cwd=src, env=_hosted_env(src), input=SCRIPT.read_text(),
                            capture_output=True, text=True)
    assert result.returncode == 0 and "MIGRATE=ok" in result.stdout, result.stdout + result.stderr


def test_release_migrate_runs_the_verified_deployed_file():
    code = "\n".join(l for l in (ROOT / "tools/release/release_migrate.sh").read_text().splitlines()
                     if not l.lstrip().startswith("#"))
    assert '< "$SCRIPT"' not in code
    assert "sha256sum tools/release/migration_check.py" in code and "$CHECK_SHA" in code
    assert "tools/release/migration_check.py apply" in code.replace('migration_check.py"\nssh', "") or \
        "$REMOTE_RUN apply" in code


def test_a_declared_altered_table_may_change_its_schema_but_never_its_rows(tmp_path):
    # pd1a2b3c4d5e (Supplier PRO Desk, 20 Oct 2026) widens the canonical_materials category check.
    pd_new = ("supplier_customers,supplier_quotes,supplier_quote_files,supplier_quote_events,supplier_quote_links,"
              "supplier_price_imports,supplier_selling_prices,supplier_quote_settings,supplier_building_assemblies")
    for declared, ok in (([], False), (["--altered-tables", "canonical_materials"], True)):
        db_path = tmp_path / f"alt-{ok}.db"
        _database_at_prior(db_path)
        upgrade = subprocess.run([sys.executable, str(SCRIPT), "rehearse", "--db", str(db_path), "--from", PRIOR, "--to", HEAD,
                                  "--new-tables", NEW], cwd=ROOT, capture_output=True, text=True, timeout=300)
        assert upgrade.returncode == 0, upgrade.stdout + upgrade.stderr
        result = _run("rehearse", "--db", str(db_path), "--from", HEAD, "--to", "pd1a2b3c4d5e", "--new-tables", pd_new, *declared)
        values = _values(result.stdout)
        if ok:
            assert result.returncode == 0 and values["MIGRATION_REHEARSAL"] == "ok", result.stdout + result.stderr
            assert "schema altered as declared: canonical_materials" in values["EXISTING_TABLES_UNCHANGED"]
        else:
            assert result.returncode == 1 and "existing schema changed: table canonical_materials" in values["FAIL"]
    assert _run("rehearse", "--db", str(tmp_path / "alt-True.db"), "--from", "pd1a2b3c4d5e", "--to", "pd1a2b3c4d5e",
                "--new-tables", pd_new, "--altered-tables", "no_such_table").returncode == 1


def test_a_declared_altered_table_may_gain_an_empty_column_with_every_row_unchanged(tmp_path):
    # w2z9r4d7k1m6 (Guided Workflow Wizards, 24 Oct 2026) adds wizard_runs, wizard_run_events and the nullable
    # projects.project_lead_user_id. Existing projects keep every value; the new column starts empty.
    prior, head, new = "g5e7c2a9d1b4", "w2z9r4d7k1m6", "wizard_runs,wizard_run_events"
    for declared, ok in (([], False), (["--altered-tables", "projects"], True)):
        db_path = tmp_path / f"lead-{ok}.db"
        app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
        with app.app_context():
            cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
            cfg.set_main_option("script_location", str(ROOT / "migrations"))
            cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
            command.upgrade(cfg, prior)
        con = sqlite3.connect(db_path)
        con.execute("INSERT INTO organizations (id, legal_name, display_name, currency, is_active, created_at, updated_at) "
                    "VALUES ('ORG-L', 'Synthetic Ltd.', 'Synthetic', 'CAD', 1, '2026-10-24', '2026-10-24')")
        con.execute("INSERT INTO clients (id, name, organization_id, created_at) VALUES (1, 'C', 'ORG-L', '2026-10-24')")
        con.execute("INSERT INTO projects (id, organization_id, name, status, client_id, created_at, operating_state, "
                    "operating_state_changed_at, drawing_requirement) VALUES (1, 'ORG-L', 'Job (synthetic)', 'Lead', 1, "
                    "'2026-10-24', 'ACTIVE', '2026-10-24', 'UNKNOWN')")
        con.commit()
        con.close()
        result = _run("rehearse", "--db", str(db_path), "--from", prior, "--to", head, "--new-tables", new, *declared)
        values = _values(result.stdout)
        if ok:
            assert result.returncode == 0 and values["MIGRATION_REHEARSAL"] == "ok", result.stdout + result.stderr
            assert "added empty columns: projects.project_lead_user_id" in values["EXISTING_TABLES_UNCHANGED"]
        else:
            assert result.returncode == 1 and values["FAIL"] in ("existing records changed in: projects",
                                                                 "existing schema changed: table projects")

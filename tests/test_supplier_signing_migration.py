"""Migration a4d5e6f7a8b9 (supplier Native Signing), rehearsed on disposable synthetic databases only.

Three check constraints widen; every existing row, column, key and foreign key stays as it was.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db

REVISION = "a4d5e6f7a8b9"
PRIOR = "z3c4d5e6f7a8"
CHECKS = "ck_signing_frozen_artifacts_document_family,ck_signing_requests_document_family,ck_signing_participants_role"
ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "release" / "migration_check.py"


def _config(db_path):
    cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _at_prior_with_signing_rows(db_path):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        command.upgrade(_config(db_path), PRIOR)
    con = sqlite3.connect(db_path)
    con.execute("INSERT INTO signing_consent_versions (version_code, authority_class, body_text, created_by_identifier, created_at)"
                " VALUES ('C-1', 'SYNTHETIC_UAT', 'x', 'test', '2026-09-14 00:00:00')")
    con.execute("INSERT INTO signing_frozen_artifacts (organization_id, document_family, source_record_id, media_type,"
                " storage_key, sha256, created_at) VALUES ('ORG-1', 'CHANGE_ORDER', 7, 'application/pdf', 'k', ?, "
                "'2026-09-14 00:00:00')", ("a" * 64,))
    con.execute("INSERT INTO signing_requests (organization_id, request_number, document_family, source_record_id, project_id,"
                " client_id, frozen_artifact_id, authority_class, status, countersign_required, consent_version_id, expires_at,"
                " created_at, created_by_user_id, created_by_identifier) VALUES ('ORG-1', 'SIGN-2026-0001', 'CHANGE_ORDER', 7,"
                " 1, 1, 1, 'SYNTHETIC_UAT', 'EXECUTED', 1, 1, '2026-09-21 00:00:00', '2026-09-14 00:00:00', 1, 'joel')")
    con.execute("INSERT INTO signing_participants (signing_request_id, sequence, role, invited_name, invited_email, created_at)"
                " VALUES (1, 1, 'CUSTOMER', 'Synthetic Client', 'client@example.invalid', '2026-09-14 00:00:00')")
    con.commit()
    con.close()


def test_the_supplier_signing_revision_is_the_single_head():
    script = ScriptDirectory.from_config(_config(":memory:"))
    assert script.get_heads() == [REVISION]
    assert script.get_revision(REVISION).down_revision == PRIOR


def test_upgrade_keeps_every_row_and_key_and_only_widens_the_three_checks(tmp_path):
    path = tmp_path / "synthetic.db"
    _at_prior_with_signing_rows(path)
    result = subprocess.run([sys.executable, str(TOOL), "rehearse", "--db", str(path), "--from", PRIOR, "--to", REVISION,
                             "--new-tables", "", "--altered-checks", CHECKS], cwd=ROOT, capture_output=True, text=True,
                            timeout=300)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "MIGRATION_REHEARSAL=ok" in result.stdout and "every row identical" in result.stdout
    assert result.stdout.count("ALTERED_CHECK=") == 3 and "SUPPLIER_DELIVERY_CHANGE" in result.stdout
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})
    with application.app_context():
        inspector = sa.inspect(db.engine)
        for table in ("signing_frozen_artifacts", "signing_requests", "signing_participants"):
            assert {c["name"] for c in inspector.get_columns(table)} == {c.name for c in db.metadata.tables[table].columns}
        assert {u["name"] for u in inspector.get_unique_constraints("signing_participants")} == {"uq_signing_participants_request_sequence"}
        with db.engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            assert conn.execute(sa.text("SELECT COUNT(*) FROM signing_participants")).scalar() == 1


def test_the_release_tool_refuses_a_rebuild_it_was_not_told_about(tmp_path):
    path = tmp_path / "unannounced.db"
    _at_prior_with_signing_rows(path)
    result = subprocess.run([sys.executable, str(TOOL), "rehearse", "--db", str(path), "--from", PRIOR, "--to", REVISION,
                             "--new-tables", ""], cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert result.returncode == 1 and "FAIL=existing schema changed" in result.stdout


def test_new_values_are_accepted_others_still_refused_and_downgrade_is_guarded(tmp_path):
    path = tmp_path / "rules.db"
    _at_prior_with_signing_rows(path)
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})
    with application.app_context():
        cfg = _config(path)
        command.upgrade(cfg, REVISION)
        insert = sa.text("INSERT INTO signing_participants (signing_request_id, sequence, role, invited_name, invited_email,"
                         " created_at) VALUES (1, :seq, :role, 'X', '', '2026-10-20 00:00:00')")
        with pytest.raises(sa.exc.IntegrityError):
            with db.engine.begin() as conn:
                conn.execute(insert, {"seq": 5, "role": "BYSTANDER"})
        with db.engine.begin() as conn:
            conn.execute(insert, {"seq": 2, "role": "SUPPLIER"})
            conn.execute(sa.text("UPDATE signing_requests SET document_family = 'SUPPLIER_ORDER'"))
        with pytest.raises(RuntimeError, match="Supplier signing records exist"):
            command.downgrade(cfg, PRIOR)
        with db.engine.begin() as conn:
            conn.execute(sa.text("DELETE FROM signing_participants WHERE role = 'SUPPLIER'"))
            conn.execute(sa.text("UPDATE signing_requests SET document_family = 'CHANGE_ORDER'"))
        command.downgrade(cfg, PRIOR)
        with pytest.raises(sa.exc.IntegrityError):
            with db.engine.begin() as conn:
                conn.execute(insert, {"seq": 3, "role": "SUPPLIER"})

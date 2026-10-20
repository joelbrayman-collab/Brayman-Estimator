"""Migration z3c4d5e6f7a8 (company appointments), rehearsed on disposable synthetic databases only."""

from __future__ import annotations

import os
from datetime import date, datetime, time

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db

REVISION = "z3c4d5e6f7a8"
PRIOR = "y2b3c4d5e6f7"
NEW_TABLES = {"company_appointments", "company_appointment_attendees", "company_appointment_history", "calendar_feed_keys"}


def _config(db_path):
    cfg_path = "migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini"
    cfg = Config(cfg_path)
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _snapshot(engine, skip=()):
    out = {}
    with engine.connect() as conn:
        for table in sorted(set(sa.inspect(engine).get_table_names()) - {"alembic_version"} - set(skip)):
            out[table] = sorted(tuple(map(str, row)) for row in conn.execute(sa.text(f'SELECT * FROM "{table}"')))
    return out


def test_the_appointment_revision_sits_on_the_single_line_of_revisions():
    script = ScriptDirectory.from_config(_config(":memory:"))
    assert len(script.get_heads()) == 1  # later revisions (pd1a2b3c4d5e, 20 Oct 2026) follow it
    assert REVISION in {r.revision for r in script.walk_revisions()}
    assert script.get_revision(REVISION).down_revision == PRIOR


def test_upgrade_adds_two_tables_changes_nothing_else_and_matches_the_models(tmp_path):
    db_path = tmp_path / "synthetic.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        with db.engine.begin() as conn:  # a synthetic row in an existing table must survive untouched
            conn.execute(sa.text(
                "INSERT INTO organizations (id, legal_name, display_name, primary_address, default_region, currency, "
                "tax_jurisdiction, is_active, created_at, updated_at) VALUES ('ORG-MIG', 'Synthetic Ltd.', 'Synthetic', "
                "'1 Test Rd', 'Ontario', 'CAD', 'Ontario (HST 13%)', 1, '2026-10-19 00:00:00', '2026-10-19 00:00:00')"))
        before_tables = set(sa.inspect(db.engine).get_table_names())
        before = _snapshot(db.engine)
        command.upgrade(cfg, REVISION)
        after_tables = set(sa.inspect(db.engine).get_table_names())
        assert after_tables - before_tables == NEW_TABLES and before_tables <= after_tables
        assert _snapshot(db.engine, skip=NEW_TABLES) == before
        inspector = sa.inspect(db.engine)
        for table in NEW_TABLES:
            migrated = {c["name"] for c in inspector.get_columns(table)}
            modelled = {c.name for c in db.metadata.tables[table].columns}
            assert migrated == modelled, table
        with db.engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION


def test_database_rules_hold_and_downgrade_is_guarded(tmp_path):
    db_path = tmp_path / "rules.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, REVISION)
        insert = sa.text(
            "INSERT INTO company_appointments (organization_id, title, appointment_type, appointment_date, all_day, "
            "start_time, end_time, visibility, status, created_at, updated_at) VALUES ('ORG-MIG', 'T', :type, "
            "'2026-10-19', :all_day, :start, :end, :vis, 'ACTIVE', '2026-10-19 00:00:00', '2026-10-19 00:00:00')")
        with db.engine.begin() as conn:
            conn.execute(sa.text(
                "INSERT INTO organizations (id, legal_name, display_name, primary_address, default_region, currency, "
                "tax_jurisdiction, is_active, created_at, updated_at) VALUES ('ORG-MIG', 'Synthetic Ltd.', 'Synthetic', "
                "'1 Test Rd', 'Ontario', 'CAD', 'Ontario (HST 13%)', 1, '2026-10-19 00:00:00', '2026-10-19 00:00:00')"))
        for bad in (
            {"type": "PARTY", "all_day": 0, "start": "09:00:00.000000", "end": "10:00:00.000000", "vis": "COMPANY"},
            {"type": "GENERAL", "all_day": 0, "start": "10:00:00.000000", "end": "09:00:00.000000", "vis": "COMPANY"},
            {"type": "GENERAL", "all_day": 1, "start": "09:00:00.000000", "end": "10:00:00.000000", "vis": "COMPANY"},
            {"type": "GENERAL", "all_day": 0, "start": None, "end": None, "vis": "COMPANY"},
            {"type": "GENERAL", "all_day": 0, "start": "09:00:00.000000", "end": "10:00:00.000000", "vis": "SECRET"},
        ):
            with pytest.raises(sa.exc.IntegrityError):
                with db.engine.begin() as conn:
                    conn.execute(insert, bad)
        with db.engine.begin() as conn:
            conn.execute(insert, {"type": "SITE_VISIT", "all_day": 0, "start": "09:00:00.000000", "end": "10:00:00.000000", "vis": "PERSONAL"})
        with pytest.raises(RuntimeError, match="Downgrade refused"):
            command.downgrade(cfg, PRIOR)
        with db.engine.begin() as conn:
            conn.execute(sa.text("DELETE FROM company_appointments"))
        command.downgrade(cfg, PRIOR)
        assert not NEW_TABLES & set(sa.inspect(db.engine).get_table_names())

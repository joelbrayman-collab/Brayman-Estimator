"""FG-042 M2 (d3b6c9e2f5a7): the baseline tables and their immutability triggers, as migrated."""

from __future__ import annotations

import importlib.util
import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app

REVISION = "d3b6c9e2f5a7"
PRIOR = "c2a5b8d1e4f6"
NEW_TABLES = {"project_baselines", "project_baseline_labour_allocations", "project_baseline_person_rates",
              "project_baseline_lines", "project_baseline_open_items"}


def _config(db_path):
    cfg = Config("migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def test_revision_follows_m3():
    script = ScriptDirectory.from_config(_config(":memory:"))
    assert script.get_revision(REVISION).down_revision == PRIOR


def test_migration_triggers_are_exactly_the_models_triggers():
    from app.models.project_baseline import BASELINE_TRIGGERS

    path = "migrations/versions/d3b6c9e2f5a7_fg042_m2_project_baseline.py"
    spec = importlib.util.spec_from_file_location("m2_mig", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert list(module.TRIGGERS) == list(BASELINE_TRIGGERS)


def test_upgrade_adds_five_tables_touches_nothing_and_downgrade_is_guarded(tmp_path):
    db_path = tmp_path / "m2.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        before_tables = set(sa.inspect(engine).get_table_names())
        before = {}
        with engine.connect() as conn:
            for t in sorted(before_tables - {"alembic_version"}):
                before[t] = sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{t}"')))
        command.upgrade(cfg, REVISION)
        assert set(sa.inspect(engine).get_table_names()) - before_tables == NEW_TABLES
        with engine.connect() as conn:
            for t, rows in before.items():
                assert sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{t}"'))) == rows, t
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            triggers = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='trigger'"))}
            assert len({t for t in triggers if "baseline" in t}) == 18
            indexes = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index'"))}
            assert {"uq_project_baselines_one_frozen", "uq_project_baselines_approval"} <= indexes
        command.downgrade(cfg, PRIOR)  # empty tables: a clean rollback
        assert set(sa.inspect(engine).get_table_names()) == before_tables
        with engine.connect() as conn:
            assert not [r for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='trigger'"))
                        if "baseline" in r[0]]
        command.upgrade(cfg, REVISION)
        with engine.begin() as conn:
            conn.execute(sa.text("INSERT OR IGNORE INTO organizations (id, legal_name, display_name, currency, "
                                 "is_active, created_at, updated_at) VALUES ('ORG-001','S','S','CAD',1,'2026-11-24',"
                                 "'2026-11-24')"))
            conn.execute(sa.text("INSERT INTO users (email, display_name, password_hash, is_active, created_at, "
                                 "updated_at) VALUES ('o@example.invalid','O','x',1,'2026-11-24','2026-11-24')"))
        # a bad status and a bad pricing basis are refused by the table's own constraints
        # (parents are not needed: foreign keys are not enforced on this connection)
        bad = ("INSERT INTO project_baselines (organization_id, project_id, estimate_id, estimate_version_id, "
               "option_label, status, labour_selling_rate, pricing_basis, created_at, created_by_user_id) VALUES "
               "('ORG-001', 1, 1, 1, 'A', '{status}', {rate}, '{basis}', '2026-11-24', 1)")
        for status, rate, basis in (("DRAFT", 85, "MARKUP"), ("PROVISIONAL", -1, "MARKUP"),
                                    ("PROVISIONAL", 85, "MARGIN")):
            with pytest.raises(sa.exc.IntegrityError):
                with engine.begin() as conn:
                    conn.execute(sa.text(bad.format(status=status, rate=rate, basis=basis)))
        with engine.begin() as conn:
            conn.execute(sa.text(bad.format(status="PROVISIONAL", rate=85, basis="MARKUP")))
        with pytest.raises(RuntimeError, match="pre-migration backup"):
            command.downgrade(cfg, PRIOR)

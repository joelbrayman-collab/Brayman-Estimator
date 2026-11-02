"""Revision u8b9c0d1e2f3: employee cost profiles, estimate crews and the recorded pricing method (2 Nov 2026).

Disposable SQLite database upgraded from t7a8b9c0d1e2 with rows in existing tables: exactly the new tables and the five
new nullable columns appear, every existing row is unchanged (no backfill: the new columns are NULL), the insert-only
triggers exist, the downgrade refuses while anything new is held and otherwise restores the earlier schema exactly.
"""

from __future__ import annotations

import os
from datetime import datetime

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app

REVISION = "u8b9c0d1e2f3"
PRIOR = "t7a8b9c0d1e2"
NEW_TABLES = {"organization_person_cost_profiles", "organization_labour_cost_settings", "estimate_crew_members"}
NEW_COLUMNS = {("organization_pricing_policies", "subcontract_markup_rate"),
               ("estimate_pricing_snapshots", "labour_rate"),
               ("estimate_pricing_snapshots", "subcontract_markup_rate"),
               ("estimate_versions", "pricing_method"),
               ("estimate_versions", "package_pricing_json")}


def _config(db_path):
    cfg = Config("migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _tables(engine):
    with engine.connect() as conn:
        return {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type = 'table'"))}


def _columns(engine, tables):
    inspector = sa.inspect(engine)
    return {t: [(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)] for t in tables}


def _snapshot(engine, tables):
    out = {}
    with engine.connect() as conn:
        for t in sorted(tables - {"alembic_version"}):
            out[t] = sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{t}"')))
    return out


def test_graph_head_is_the_cost_profiles_revision():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        script = ScriptDirectory.from_config(_config(":memory:"))
        assert script.get_heads() == [REVISION]
        assert script.get_revision(REVISION).down_revision == PRIOR


def _seed(engine):
    now = datetime(2026, 11, 2, 12, 0, 0)
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT OR IGNORE INTO organizations (id, legal_name, display_name, currency, is_active, created_at, "
            "updated_at) VALUES ('ORG-001', 'Synthetic Builder', 'Synthetic', 'CAD', 1, :t, :t)"), {"t": now})
        conn.execute(sa.text("INSERT INTO clients (name, organization_id, created_at) VALUES "
                             "('Synthetic Client', 'ORG-001', :t)"), {"t": now})
        conn.execute(sa.text(
            "INSERT INTO organization_pricing_policies (organization_id, policy_code, version_number, method, "
            "target_gross_margin, overhead_treatment, profit_treatment, contingency_visibility, is_default, "
            "approval_status, created_at, updated_at) VALUES ('ORG-001', 'SYN-GM', 1, 'TRUE_GROSS_MARGIN', 0.15, "
            "'UNSPECIFIED', 'UNSPECIFIED', 'UNSPECIFIED', 1, 'ORG_APPROVED', :t, :t)"), {"t": now})
        conn.execute(sa.text(
            "INSERT INTO users (email, display_name, password_hash, is_active, created_at, updated_at) VALUES "
            "('owner@example.invalid', 'Owner Synthetic', 'x', 1, :t, :t)"), {"t": now})
    return now


def test_upgrade_is_additive_and_downgrade_is_guarded_and_reversible(tmp_path):
    db_path = tmp_path / "disposable.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        now = _seed(engine)
        before_tables = _tables(engine)
        before_columns = _columns(engine, before_tables)
        before = _snapshot(engine, before_tables)
        command.upgrade(cfg, REVISION)
        assert _tables(engine) - before_tables == NEW_TABLES
        after_columns = _columns(engine, before_tables)
        added = {(t, c[0]) for t in before_tables for c in after_columns[t] if c not in before_columns[t]}
        assert added == NEW_COLUMNS
        assert all(c[2] for t, cols in after_columns.items() for c in cols if (t, c[0]) in NEW_COLUMNS)  # nullable
        after = _snapshot(engine, before_tables)
        # Existing rows are unchanged apart from the new NULL columns (no backfill, no rewrite).
        assert after["clients"] == before["clients"] and after["organizations"] == before["organizations"]
        assert after["organization_pricing_policies"] == [r + ("None",) for r in before["organization_pricing_policies"]]
        with engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION
            assert conn.execute(sa.text("SELECT subcontract_markup_rate FROM organization_pricing_policies")).scalar() is None
            triggers = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='trigger'"))}
            assert {"organization_person_cost_profiles_no_update", "organization_person_cost_profiles_no_delete",
                    "organization_labour_cost_settings_no_update",
                    "organization_labour_cost_settings_no_delete"} <= triggers
        with engine.begin() as conn:
            conn.execute(sa.text(
                "INSERT INTO organization_labour_cost_settings (organization_id, wsib_rate_per_100, created_at, "
                "actor_user_id, actor_name) VALUES ('ORG-001', 3.55, :t, 1, 'Owner Synthetic')"), {"t": now})
        with pytest.raises(sa.exc.DatabaseError, match="insert-only"):
            with engine.begin() as conn:
                conn.execute(sa.text("UPDATE organization_labour_cost_settings SET wsib_rate_per_100 = 1"))
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):
            command.downgrade(cfg, PRIOR)
        with engine.begin() as conn:
            conn.execute(sa.text("DROP TRIGGER organization_labour_cost_settings_no_delete"))
            conn.execute(sa.text("DELETE FROM organization_labour_cost_settings"))
            conn.execute(sa.text("UPDATE organization_pricing_policies SET subcontract_markup_rate = 0.05"))
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):  # a new column holds a value
            command.downgrade(cfg, PRIOR)
        with engine.begin() as conn:
            conn.execute(sa.text("UPDATE organization_pricing_policies SET subcontract_markup_rate = NULL"))
        command.downgrade(cfg, PRIOR)
        assert _tables(engine) == before_tables
        assert _columns(engine, before_tables) == before_columns
        assert _snapshot(engine, before_tables) == before
        with engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
        command.upgrade(cfg, REVISION)
        assert NEW_TABLES <= _tables(engine)
        engine.dispose()


def test_models_match_the_migration_columns(tmp_path):
    """db.create_all() (tests) and the migration (production) build the same new tables and columns."""
    from app import db

    migrated = tmp_path / "migrated.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{migrated}"})
    with application.app_context():
        command.upgrade(_config(migrated), REVISION)
    created = tmp_path / "created.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{created}"})
    with application.app_context():
        db.create_all()

    def shape(path):
        engine = sa.create_engine(f"sqlite:///{path}")
        inspector = sa.inspect(engine)
        tables = {t: {(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)} for t in NEW_TABLES}
        idx = {t: {i["name"] for i in inspector.get_indexes(t)} for t in NEW_TABLES}
        cols = {(t, c): next((str(x["type"]), x["nullable"]) for x in inspector.get_columns(t) if x["name"] == c)
                for t, c in NEW_COLUMNS}
        engine.dispose()
        return tables, idx, cols

    assert shape(migrated) == shape(created)

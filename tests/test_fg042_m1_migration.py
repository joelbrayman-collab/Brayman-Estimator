"""FG-042 revision M1 (b1f4a9c2d7e3): Person-to-User link, cost-profile effective date, other employment cost.

Disposable SQLite database upgraded from the prior head with rows in existing tables: exactly four columns and two
indexes appear, every existing row is unchanged (no backfill), the insert-only triggers on cost profiles survive,
the downgrade refuses while anything new is used and otherwise restores the earlier schema.
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

REVISION = "b1f4a9c2d7e3"
PRIOR = "q1a2b3c4d5e6"
NEW_COLUMNS = {("organization_people", "user_id"), ("organization_person_cost_profiles", "effective_from"),
               ("organization_person_cost_profiles", "other_employment_cost_annual"),
               ("organization_person_cost_profiles", "other_employment_cost_note")}


def _config(db_path):
    cfg = Config("migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _snapshot(engine, tables):
    out = {}
    with engine.connect() as conn:
        for t in sorted(tables):
            out[t] = sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{t}"')))
    return out


def _columns(engine, table):
    return {c["name"] for c in sa.inspect(engine).get_columns(table)}


def test_revision_follows_the_prior_head():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        script = ScriptDirectory.from_config(_config(":memory:"))
        assert script.get_revision(REVISION).down_revision == PRIOR


def test_upgrade_is_additive_triggers_survive_and_downgrade_is_guarded(tmp_path):
    db_path = tmp_path / "disposable.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    now = datetime(2026, 11, 24, 12, 0, 0)
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        with engine.begin() as conn:
            conn.execute(sa.text(
                "INSERT OR IGNORE INTO organizations (id, legal_name, display_name, currency, is_active, created_at, "
                "updated_at) VALUES ('ORG-001', 'Synthetic Builder', 'Synthetic', 'CAD', 1, :t, :t)"), {"t": now})
            conn.execute(sa.text(
                "INSERT INTO users (email, display_name, password_hash, is_active, created_at, updated_at) VALUES "
                "('owner@example.invalid', 'Owner Synthetic', 'x', 1, :t, :t)"), {"t": now})
            conn.execute(sa.text(
                "INSERT INTO organization_people (organization_id, full_name, address, mobile_number, email_address, "
                "hourly_wage, is_active, created_at, created_by_user_id, updated_at, updated_by_user_id) VALUES "
                "('ORG-001', 'Synthetic Worker', '1 Rd', '613', 'w@example.invalid', 26, 1, :t, 1, :t, 1)"), {"t": now})
            conn.execute(sa.text(
                "INSERT INTO organization_person_cost_profiles (organization_id, person_id, hourly_wage, "
                "paid_hours_per_year, vacation_weeks, paid_holidays, truck_monthly, fuel_monthly, "
                "tool_allowance_annual, rrsp_percent, health_premium_monthly, wsib_rate_per_100, wsib_is_override, "
                "statutory_year, working_hours, annual_cost, loaded_rate, breakdown_json, created_at, actor_user_id, "
                "actor_name) VALUES ('ORG-001', 1, 26, 2080, 2, 9, 0, 0, 0, 0, 0, 3.55, 0, 2026, 1928, 60243.46, "
                "31.25, '{}', :t, 1, 'Owner Synthetic')"), {"t": now})
        tables = set(sa.inspect(engine).get_table_names()) - {"alembic_version"}
        before = _snapshot(engine, tables)
        before_cols = {t: _columns(engine, t) for t in tables}
        command.upgrade(cfg, REVISION)
        after_cols = {t: _columns(engine, t) for t in tables}
        added = {(t, c) for t in tables for c in after_cols[t] - before_cols[t]}
        assert added == NEW_COLUMNS
        after = _snapshot(engine, tables)
        # every existing row is unchanged apart from the new NULL column(s): no backfill, no rewrite
        assert after["organization_people"] == [r + ("None",) for r in before["organization_people"]]
        assert after["organization_person_cost_profiles"] == [
            r + ("None", "None", "None") for r in before["organization_person_cost_profiles"]]
        for t in tables - {"organization_people", "organization_person_cost_profiles"}:
            assert after[t] == before[t], t
        with engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION
            row = conn.execute(sa.text(
                "SELECT loaded_rate, effective_from, other_employment_cost_annual, other_employment_cost_note "
                "FROM organization_person_cost_profiles")).one()
            assert (str(row[0]), row[1], row[2], row[3]) == ("31.25", None, None, None)
            assert conn.execute(sa.text("SELECT user_id FROM organization_people")).scalar() is None
            triggers = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='trigger'"))}
            assert {"organization_person_cost_profiles_no_update",
                    "organization_person_cost_profiles_no_delete"} <= triggers
            indexes = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index'"))}
            assert {"uq_organization_people_org_user", "ix_person_cost_profiles_person_effective"} <= indexes
        # insert-only still holds
        with pytest.raises(sa.exc.DatabaseError, match="insert-only"):
            with engine.begin() as conn:
                conn.execute(sa.text("UPDATE organization_person_cost_profiles SET effective_from = '2026-01-01'"))
        # the unique partial index: one user per employee within an organization
        with engine.begin() as conn:
            conn.execute(sa.text("UPDATE organization_people SET user_id = 1"))
        with pytest.raises(RuntimeError, match="pre-migration backup"):
            command.downgrade(cfg, PRIOR)
        with engine.begin() as conn:
            conn.execute(sa.text("UPDATE organization_people SET user_id = NULL"))
        command.downgrade(cfg, PRIOR)
        assert {t: _columns(engine, t) for t in tables} == before_cols
        assert _snapshot(engine, tables) == before
        with engine.connect() as conn:
            triggers = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='trigger'"))}
            assert "organization_person_cost_profiles_no_update" in triggers

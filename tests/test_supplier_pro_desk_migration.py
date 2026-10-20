"""Migration pd1a2b3c4d5e (Supplier PRO Desk), rehearsed on disposable synthetic databases only."""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db

ROOT = Path(__file__).resolve().parents[1]
REVISION, PRIOR = "pd1a2b3c4d5e", "z3c4d5e6f7a8"
NEW_TABLES = {"supplier_customers", "supplier_quotes", "supplier_quote_files", "supplier_quote_events",
              "supplier_quote_links", "supplier_price_imports", "supplier_selling_prices", "supplier_quote_settings",
              "supplier_building_assemblies"}


def _config(path) -> Config:
    cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    return cfg


def _rows(engine, skip=()):
    out = {}
    with engine.connect() as conn:
        for table in sorted(set(sa.inspect(engine).get_table_names()) - {"alembic_version"} - set(skip)):
            out[table] = sorted(tuple(map(str, row)) for row in conn.execute(sa.text(f'SELECT * FROM "{table}"')))
    return out


def test_the_pro_desk_revision_follows_the_calendar_and_is_followed_by_supplier_signing():
    script = ScriptDirectory.from_config(_config(":memory:"))
    assert script.get_heads() == ["a4d5e6f7a8b9"]  # Supplier Native Signing (20 Oct 2026) follows it
    assert script.get_revision(REVISION).down_revision == PRIOR
    assert script.get_revision("a4d5e6f7a8b9").down_revision == REVISION


def test_upgrade_adds_nine_tables_keeps_every_existing_row_and_matches_the_models(tmp_path):
    db_path = tmp_path / "synthetic.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        with db.engine.begin() as conn:  # synthetic rows in existing tables must survive untouched
            conn.execute(sa.text(
                "INSERT INTO canonical_materials (code, display_name, status, kind, category, canonical_uom, "
                "substitution_policy, created_at, updated_at) VALUES ('CAL-SYN-1', 'Synthetic', 'ACTIVE', 'GENERIC', "
                "'FASTENER', 'EA', 'ALLOWED', '2026-10-20 00:00:00', '2026-10-20 00:00:00')"))
            conn.execute(sa.text("INSERT INTO suppliers (code, legal_name, status, demo_synthetic, created_at) "
                                 "VALUES ('SYN', 'Synthetic supply', 'ACTIVE', 1, '2026-10-20 00:00:00')"))
        before_tables = set(sa.inspect(db.engine).get_table_names())
        before = _rows(db.engine)
        command.upgrade(cfg, REVISION)
        after_tables = set(sa.inspect(db.engine).get_table_names())
        assert after_tables - before_tables == NEW_TABLES and before_tables <= after_tables
        assert _rows(db.engine, skip=NEW_TABLES) == before
        inspector = sa.inspect(db.engine)
        for table in NEW_TABLES:
            assert {c["name"] for c in inspector.get_columns(table)} == {c.name for c in db.metadata.tables[table].columns}, table
        with db.engine.begin() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            conn.execute(sa.text(  # a new category is now allowed
                "INSERT INTO canonical_materials (code, display_name, status, kind, category, canonical_uom, "
                "substitution_policy, created_at, updated_at) VALUES ('CAL-OB-SYN', 'Synthetic panel', 'ACTIVE', 'GENERIC', "
                "'ROOFING', 'LF', 'ALLOWED', '2026-10-20 00:00:00', '2026-10-20 00:00:00')"))
        with pytest.raises(sa.exc.IntegrityError):
            with db.engine.begin() as conn:
                conn.execute(sa.text(
                    "INSERT INTO supplier_quotes (supplier_id, customer_id, number, status, created_by_name, created_at, "
                    "updated_at, demo_synthetic) VALUES (1, 1, 'Q1', 'SHIPPED', 'x', '2026-10-20', '2026-10-20', 1)"))


def test_downgrade_refuses_while_pro_desk_rows_exist(tmp_path):
    db_path = tmp_path / "rules.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, REVISION)
        with db.engine.begin() as conn:
            conn.execute(sa.text("INSERT INTO suppliers (code, legal_name, status, demo_synthetic, created_at) "
                                 "VALUES ('SYN', 'Synthetic supply', 'ACTIVE', 1, '2026-10-20 00:00:00')"))
            conn.execute(sa.text("INSERT INTO supplier_customers (supplier_id, display_name, consent_email, consent_text, "
                                 "demo_synthetic, created_by_name, created_at) VALUES (1, 'S', 0, 0, 1, 'x', '2026-10-20')"))
        with pytest.raises(RuntimeError, match="Downgrade refused"):
            command.downgrade(cfg, PRIOR)
        with db.engine.begin() as conn:
            conn.execute(sa.text("DELETE FROM supplier_customers"))
        command.downgrade(cfg, PRIOR)
        assert not NEW_TABLES & set(sa.inspect(db.engine).get_table_names())

"""Revision u1b2c3d4e5f6: takeoff catalogue categories and the PKG unit.

Isolated, disposable SQLite database. Existing rows are copied unchanged,
the new categories are accepted only after the upgrade, and the downgrade
refuses while takeoff rows exist.
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

REVISION = "u1b2c3d4e5f6"
NEXT = "v2c3d4e5f6a7"
HEAD = "u7b3d9f2a4c6"
PRIOR = "t0a1b2c3d4e5"
WATCHED = (
    "canonical_materials",
    "suppliers",
    "supplier_locations",
    "supplier_products",
    "supplier_product_price_evidence",
    "canonical_material_supplier_maps",
    "material_requirements",
    "contractor_cost_approvals",
    "cost_items",
)


def _config(db_path):
    cfg_path = "migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini"
    alembic_cfg = Config(cfg_path)
    alembic_cfg.set_main_option("script_location", "migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return alembic_cfg


def _dump(engine):
    rows = {}
    with engine.connect() as conn:
        for table in WATCHED:
            rows[table] = [tuple(r) for r in conn.execute(sa.text(f"SELECT * FROM {table} ORDER BY id"))]
    return rows


def _insert_history(engine):
    now = datetime(2026, 10, 1, 12, 0, 0)
    with engine.begin() as conn:
        material = conn.execute(sa.text("SELECT id FROM canonical_materials WHERE code = 'CAL-LUM-2X8-12'")).scalar()
        conn.execute(sa.text(
            "INSERT INTO suppliers (code, legal_name, status, demo_synthetic, created_at) VALUES ('HIST', 'Historical yard', 'ACTIVE', 1, :t)"
        ), {"t": now})
        supplier = conn.execute(sa.text("SELECT id FROM suppliers WHERE code = 'HIST'")).scalar()
        conn.execute(sa.text(
            "INSERT INTO supplier_locations (supplier_id, code, display_name, status, demo_synthetic, created_at) "
            "VALUES (:s, 'MAIN', 'Main', 'ACTIVE', 1, :t)"
        ), {"s": supplier, "t": now})
        conn.execute(sa.text(
            "INSERT INTO supplier_products (supplier_id, sku, description, sales_uom, status, demo_synthetic, created_at) "
            "VALUES (:s, 'H-2812', '2x8 12 ft', 'EA', 'ACTIVE', 1, :t)"
        ), {"s": supplier, "t": now})
        product = conn.execute(sa.text("SELECT id FROM supplier_products WHERE sku = 'H-2812'")).scalar()
        conn.execute(sa.text(
            "INSERT INTO canonical_material_supplier_maps (canonical_material_id, supplier_product_id, status, demo_synthetic, created_at) "
            "VALUES (:m, :p, 'ACTIVE', 1, :t)"
        ), {"m": material, "p": product, "t": now})
        for amount in ("11.2500", "11.9000"):
            conn.execute(sa.text(
                "INSERT INTO supplier_product_price_evidence (supplier_product_id, price_class, amount, currency, unit, captured_at, source, "
                "actor_display_name, demo_synthetic, created_at) VALUES (:p, 'PUBLIC_LIST_PRICE', :a, 'CAD', 'EA', :t, 'MANUAL', 'History', 1, :t)"
            ), {"p": product, "a": amount, "t": now})


_NEW_ROW = sa.text(
    "INSERT INTO canonical_materials (code, display_name, status, kind, category, trade, canonical_uom, substitution_policy, created_at, updated_at) "
    "VALUES (:code, 'Test takeoff identity', 'ACTIVE', 'GENERIC', :category, 'Decks', :uom, 'ALLOWED', :t, :t)"
)


def test_graph_has_one_head_after_the_takeoff_revision():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        script = ScriptDirectory.from_config(_config(":memory:"))
        assert script.get_heads() == [HEAD]
        assert script.get_revision("w3d4e5f6a7b8").down_revision == NEXT
        assert script.get_revision(NEXT).down_revision == REVISION
        assert script.get_revision(REVISION).down_revision == PRIOR


def test_upgrade_preserves_history_accepts_new_categories_and_downgrade_is_guarded(tmp_path):
    db_path = tmp_path / "disposable.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        _insert_history(engine)
        before = _dump(engine)
        assert len(before["supplier_product_price_evidence"]) == 2
        now = datetime(2026, 10, 13)

        # Before the upgrade the catalogue refuses a takeoff category and PKG.
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(_NEW_ROW, {"code": "TEST-DECK", "category": "DECKING", "uom": "EA", "t": now})
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(_NEW_ROW, {"code": "TEST-PKG", "category": "DIMENSIONAL_LUMBER", "uom": "PKG", "t": now})

        command.upgrade(cfg, REVISION)
        assert _dump(engine) == before  # every existing row copied unchanged
        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            assert conn.execute(sa.text("PRAGMA foreign_key_check")).fetchall() == []
        for category in ("DECKING", "FASCIA", "RAILING", "GATE", "FOUNDATION", "CONNECTOR", "FASTENER"):
            with engine.begin() as conn:
                conn.execute(_NEW_ROW, {"code": f"TEST-{category}", "category": category, "uom": "PKG" if category == "FASTENER" else "EA", "t": now})
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(_NEW_ROW, {"code": "TEST-BAD", "category": "PLUMBING", "uom": "EA", "t": now})

        # Downgrade refuses while takeoff rows exist, and changes nothing.
        with pytest.raises(RuntimeError, match="Restore the pre-migration backup"):
            command.downgrade(cfg, PRIOR)
        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION
            assert conn.execute(sa.text("SELECT COUNT(*) FROM canonical_materials WHERE code LIKE 'TEST-%'")).scalar() == 7

        # With no takeoff rows, the downgrade restores the earlier rules exactly.
        with engine.begin() as conn:
            conn.execute(sa.text("DELETE FROM canonical_materials WHERE code LIKE 'TEST-%'"))
        command.downgrade(cfg, PRIOR)
        assert _dump(engine) == before
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(_NEW_ROW, {"code": "TEST-DECK", "category": "DECKING", "uom": "EA", "t": now})
        command.upgrade(cfg, REVISION)
        assert _dump(engine) == before
        engine.dispose()

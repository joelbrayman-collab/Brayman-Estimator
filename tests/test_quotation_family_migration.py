"""Revision q1a2b3c4d5e6: QUOTATION family, estimate_preparation_runs and project_exports (16 Nov 2026).

Disposable SQLite database upgraded from u8b9c0d1e2f3: the two new tables appear, existing signing rows are copied
unchanged, QUOTATION is accepted by the widened constraints (and refused before), and the downgrade refuses while a
QUOTATION row is held and otherwise restores the earlier constraint.
"""

from __future__ import annotations

import os

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

REVISION = "q1a2b3c4d5e6"
PRIOR = "u8b9c0d1e2f3"


def _config(db_path):
    cfg = Config("migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _tables(engine):
    with engine.connect() as conn:
        return {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type = 'table'"))}


def test_graph_head_follows_the_cost_profiles_revision():
    script = ScriptDirectory.from_config(_config(":memory:"))
    assert script.get_heads() == [REVISION]
    assert script.get_revision(REVISION).down_revision == PRIOR


def _insert_artifact(engine, family):
    with engine.begin() as conn:
        conn.execute(sa.text(
            "INSERT OR IGNORE INTO organizations (id, legal_name, display_name, currency, is_active, created_at, "
            "updated_at) VALUES ('ORG-001', 'Synthetic Builder', 'Synthetic', 'CAD', 1, datetime('now'), datetime('now'))"))
        conn.execute(sa.text(
            "INSERT INTO signing_frozen_artifacts (organization_id, document_family, source_record_id, media_type, "
            "storage_key, sha256, created_at) VALUES ('ORG-001', :f, 1, 'application/pdf', 'k', :h, datetime('now'))"),
            {"f": family, "h": "a" * 64})


def test_upgrade_adds_quotation_and_tables_then_downgrade_restores(tmp_path):
    from app import create_app

    db_path = tmp_path / "disposable.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        _insert_artifact(engine, "INTERNAL_APPROVAL")  # an existing row
        with pytest.raises(sa.exc.IntegrityError):
            _insert_artifact(engine, "QUOTATION")  # refused before
        command.upgrade(cfg, REVISION)
        assert {"estimate_preparation_runs", "project_exports"} <= _tables(engine)
        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT COUNT(*) FROM signing_frozen_artifacts WHERE document_family = "
                                        "'INTERNAL_APPROVAL'")).scalar() == 1  # copied unchanged
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
        _insert_artifact(engine, "QUOTATION")  # accepted now
        with pytest.raises(RuntimeError):
            command.downgrade(cfg, PRIOR)  # refuses while a QUOTATION row is held
        with engine.begin() as conn:
            conn.execute(sa.text("DELETE FROM signing_frozen_artifacts WHERE document_family = 'QUOTATION'"))
        command.downgrade(cfg, PRIOR)
        assert not ({"estimate_preparation_runs", "project_exports"} & _tables(engine))
        with pytest.raises(sa.exc.IntegrityError):
            _insert_artifact(engine, "QUOTATION")

"""Revision t7a8b9c0d1e2: company documents and the equipment register.

Disposable SQLite database upgraded from s6f7a8b9c0d1 with rows in existing tables: exactly the new tables appear,
every existing row is unchanged, the triggers and indexes exist, the FTS5 table exists iff the build supports it,
nothing is backfilled, and the downgrade refuses while any new table holds a row.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app

REVISION = "t7a8b9c0d1e2"
PRIOR = "s6f7a8b9c0d1"
NEW_TABLES = {"documents", "document_versions", "document_links", "document_dates", "document_events", "document_text",
              "organization_equipment", "organization_equipment_events"}
FTS_TABLES = {"document_search", "document_search_data", "document_search_idx", "document_search_content",
              "document_search_docsize", "document_search_config"}


def _config(db_path):
    cfg = Config("migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _tables(engine):
    with engine.connect() as conn:
        return {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type = 'table'"))}


def _snapshot(engine, tables):
    out = {}
    with engine.connect() as conn:
        for t in sorted(tables - {"alembic_version"}):
            out[t] = sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{t}"')))
    return out


def _fts5_supported() -> bool:
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE VIRTUAL TABLE p USING fts5(x)")
        return True
    except sqlite3.OperationalError:
        return False
    finally:
        conn.close()


def test_graph_head_is_the_documents_revision():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        script = ScriptDirectory.from_config(_config(":memory:"))
        # Cost profiles and pricing method (u8b9c0d1e2f3, 2 Nov 2026) follow this revision.
        assert script.get_heads() == ["u8b9c0d1e2f3"]
        assert script.get_revision("u8b9c0d1e2f3").down_revision == REVISION
        assert script.get_revision(REVISION).down_revision == PRIOR


def test_upgrade_is_additive_and_downgrade_is_guarded(tmp_path):
    db_path = tmp_path / "disposable.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        now = datetime(2026, 10, 31, 12, 0, 0)
        with engine.begin() as conn:
            conn.execute(sa.text(
                "INSERT OR IGNORE INTO organizations (id, legal_name, display_name, currency, is_active, created_at, updated_at) "
                "VALUES ('ORG-001', 'Synthetic Builder', 'Synthetic', 'CAD', 1, :t, :t)"), {"t": now})
            conn.execute(sa.text("INSERT INTO clients (name, organization_id, created_at) VALUES "
                                 "('Synthetic Client', 'ORG-001', :t)"), {"t": now})
        before_tables = _tables(engine)
        before = _snapshot(engine, before_tables)
        command.upgrade(cfg, REVISION)
        added = _tables(engine) - before_tables
        assert added == NEW_TABLES | (FTS_TABLES if _fts5_supported() else set())
        assert _snapshot(engine, before_tables) == before  # every existing row unchanged
        with engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION
            for table in NEW_TABLES:
                assert conn.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar() == 0, table  # no backfill
            triggers = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='trigger'"))}
            assert {"document_events_no_update", "document_events_no_delete", "organization_equipment_events_no_update",
                    "organization_equipment_events_no_delete"} <= triggers
            indexes = {r[0] for r in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='index'"))}
            assert {"uq_document_versions_one_current", "uq_document_versions_source", "uq_document_dates_confirmed",
                    "uq_document_links_primary", "ix_document_links_org_context_project",
                    "ix_documents_org_type", "uq_organization_equipment_unit"} <= indexes
            attached = {r[1] for r in conn.execute(sa.text("PRAGMA database_list"))}
            assert attached <= {"main", "temp"}  # no ATTACH DATABASE, no second store
        with engine.begin() as conn:
            conn.execute(sa.text(
                "INSERT INTO documents (public_id, organization_id, title, document_type, type_basis, status, "
                "sensitivity, origin, created_by_name, created_at, updated_at) VALUES ('a' || hex(randomblob(15)), "
                "'ORG-001', 'Synthetic', 'OTHER', 'SUGGESTED', 'ACTIVE', 'STANDARD', 'UPLOAD', 't', :t, :t)"), {"t": now})
            doc_id = conn.execute(sa.text("SELECT id FROM documents")).scalar()
            conn.execute(sa.text(
                "INSERT INTO document_events (organization_id, document_id, event_type, actor_name, at) "
                "VALUES ('ORG-001', :d, 'CREATED', 't', :t)"), {"d": doc_id, "t": now})
        with pytest.raises(sa.exc.DatabaseError, match="insert-only"):
            with engine.begin() as conn:
                conn.execute(sa.text("DELETE FROM document_events"))
        with pytest.raises(sa.exc.IntegrityError):  # the context rule: a COMPANY link names nothing else
            with engine.begin() as conn:
                conn.execute(sa.text(
                    "INSERT INTO document_links (organization_id, document_id, context_kind, project_id, is_primary, "
                    "linked_by_name, linked_at) VALUES ('ORG-001', :d, 'COMPANY', 1, 0, 't', :t)"),
                    {"d": doc_id, "t": now})
        with pytest.raises(RuntimeError, match="restore the pre-migration backup"):
            command.downgrade(cfg, PRIOR)
        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION
        # Empty the new tables (dropping the insert-only triggers first, rehearsal only) and the downgrade runs.
        with engine.begin() as conn:
            conn.execute(sa.text("DROP TRIGGER document_events_no_delete"))
            conn.execute(sa.text("DELETE FROM document_events"))
            conn.execute(sa.text("DELETE FROM documents"))
        command.downgrade(cfg, PRIOR)
        assert not (_tables(engine) & (NEW_TABLES | FTS_TABLES))
        assert _snapshot(engine, before_tables) == before
        command.upgrade(cfg, REVISION)
        assert NEW_TABLES <= _tables(engine)
        engine.dispose()


def test_models_match_the_migration_columns(tmp_path):
    """db.create_all() (tests) and the migration (production) build the same columns for the new tables."""
    from app import db

    migrated = tmp_path / "migrated.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{migrated}"})
    with application.app_context():
        command.upgrade(_config(migrated), REVISION)
    created = tmp_path / "created.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{created}"})
    with application.app_context():
        db.create_all()

    def columns(path):
        engine = sa.create_engine(f"sqlite:///{path}")
        inspector = sa.inspect(engine)
        out = {t: {(c["name"], str(c["type"]), c["nullable"]) for c in inspector.get_columns(t)} for t in NEW_TABLES}
        idx = {t: {i["name"] for i in inspector.get_indexes(t)} for t in NEW_TABLES}
        engine.dispose()
        return out, idx

    m_cols, m_idx = columns(migrated)
    c_cols, c_idx = columns(created)
    assert m_cols == c_cols
    assert m_idx == c_idx

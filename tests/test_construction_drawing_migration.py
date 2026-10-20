"""Revision v2c3d4e5f6a7: construction drawing sets and attachments.

Disposable SQLite database. Existing rows are untouched, the new tables
accept a drawing set and an attachment, the attachment target rule holds,
and the downgrade refuses while a drawing set exists.
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

REVISION = "v2c3d4e5f6a7"
PRIOR = "u1b2c3d4e5f6"
HEAD = "pd1a2b3c4d5e"  # decision 4 binding follows this revision


def _config(db_path):
    cfg_path = "migrations/alembic.ini" if os.path.exists("migrations/alembic.ini") else "alembic.ini"
    cfg = Config(cfg_path)
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def _tables(engine):
    return set(sa.inspect(engine).get_table_names())


def _snapshot(engine):
    out = {}
    with engine.connect() as conn:
        for t in sorted(_tables(engine) - {"alembic_version"}):
            out[t] = sorted(tuple(map(str, r)) for r in conn.execute(sa.text(f'SELECT * FROM "{t}"')))
    return out


def test_graph_head_is_the_drawing_revision():
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with application.app_context():
        script = ScriptDirectory.from_config(_config(":memory:"))
        assert script.get_heads() == [HEAD]
        assert script.get_revision("w3d4e5f6a7b8").down_revision == REVISION
        assert script.get_revision(REVISION).down_revision == PRIOR


def test_upgrade_adds_two_tables_only_and_downgrade_is_guarded(tmp_path):
    db_path = tmp_path / "disposable.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        engine = sa.create_engine(f"sqlite:///{db_path}")
        now = datetime(2026, 10, 14, 12, 0, 0)
        before_tables = _tables(engine)
        before = _snapshot(engine)
        command.upgrade(cfg, REVISION)
        assert _tables(engine) - before_tables == {"construction_drawing_sets", "construction_drawing_attachments"}
        after = _snapshot(engine)
        for table, rows in before.items():
            assert after[table] == rows, table
        with engine.connect() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION
        with engine.begin() as conn:
            # Synthetic ids: SQLite does not enforce the foreign keys on this raw connection.
            project_id, rev_id = 1, 1
            conn.execute(sa.text(
                "INSERT INTO construction_drawing_sets (organization_id, project_id, construction_model_revision_id, model_revision_number, model_content_sha256, "
                "takeoff_fingerprint, drawing_revision, drawing_type, engine_version, input_fingerprint, status, sheet_count, sheet_index_json, pdf_bytes, pdf_sha256, "
                "dxf_bytes, dxf_sha256, created_by, created_at) VALUES ('ORG-001', :p, :r, 1, :sha, :sha, 1, 'pool_deck', 'deck-drawings-1.0', :sha, 'PRELIMINARY', 7, '[]', "
                "x'25504446', :sha, x'30', :sha, 'Test', :t)"), {"p": project_id, "r": rev_id, "sha": "b" * 64, "t": now})
            set_id = conn.execute(sa.text("SELECT id FROM construction_drawing_sets")).scalar()
            conn.execute(sa.text(
                "INSERT INTO construction_drawing_attachments (organization_id, project_id, drawing_set_id, target_kind, supplier_request_id, drawing_pdf_sha256, attached_by, attached_at) "
                "VALUES ('ORG-001', :p, :s, 'supplier_request', 'DTR-TEST', :sha, 'Test', :t)"), {"p": project_id, "s": set_id, "sha": "b" * 64, "t": now})
        # The target rule: a supplier-request attachment cannot also name a proposal.
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(sa.text(
                    "INSERT INTO construction_drawing_attachments (organization_id, project_id, drawing_set_id, target_kind, supplier_request_id, proposal_id, drawing_pdf_sha256, attached_by, attached_at) "
                    "VALUES ('ORG-001', :p, :s, 'supplier_request', 'DTR-TEST', 1, :sha, 'Test', :t)"), {"p": project_id, "s": set_id, "sha": "b" * 64, "t": now})
        # A second set with the same drawing revision on the project is refused.
        with pytest.raises(sa.exc.IntegrityError):
            with engine.begin() as conn:
                conn.execute(sa.text(
                    "INSERT INTO construction_drawing_sets (organization_id, project_id, construction_model_revision_id, model_revision_number, model_content_sha256, "
                    "takeoff_fingerprint, drawing_revision, drawing_type, engine_version, input_fingerprint, status, sheet_count, sheet_index_json, pdf_bytes, pdf_sha256, "
                    "dxf_bytes, dxf_sha256, created_by, created_at) VALUES ('ORG-001', :p, :r, 1, :sha, :sha, 1, 'pool_deck', 'e', :fp, 'PRELIMINARY', 7, '[]', "
                    "x'25', :sha, x'30', :sha, 'Test', :t)"), {"p": project_id, "r": rev_id, "sha": "b" * 64, "fp": "c" * 64, "t": now})
        with pytest.raises(RuntimeError, match="Restore the pre-migration backup"):
            command.downgrade(cfg, PRIOR)
        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar() == REVISION
            assert conn.execute(sa.text("SELECT COUNT(*) FROM construction_drawing_sets")).scalar() == 1
        with engine.begin() as conn:
            conn.execute(sa.text("DELETE FROM construction_drawing_attachments"))
            conn.execute(sa.text("DELETE FROM construction_drawing_sets"))
        command.downgrade(cfg, PRIOR)
        assert "construction_drawing_sets" not in _tables(engine)
        command.upgrade(cfg, REVISION)
        assert {"construction_drawing_sets", "construction_drawing_attachments"} <= _tables(engine)
        engine.dispose()

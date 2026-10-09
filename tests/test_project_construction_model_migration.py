"""Isolated upgrade and downgrade for project construction-model revisions.

This test does not open the Mac office database or a hosted database.
"""

import os

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db


PRIOR = "s9f0a1b2c3d4"
HEAD = "t0a1b2c3d4e5"


def _cfg(db_uri):
    cfg_path = (
        "migrations/alembic.ini"
        if os.path.exists("migrations/alembic.ini")
        else "alembic.ini"
    )
    alembic_cfg = Config(cfg_path)
    alembic_cfg.set_main_option("script_location", "migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
    return alembic_cfg


def _has_table(conn, name):
    return bool(
        conn.execute(
            sa.text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": name},
        ).scalar()
    )


def _columns(conn, table_name):
    rows = conn.execute(sa.text(f'PRAGMA table_info("{table_name}")')).fetchall()
    return {row[1]: row for row in rows}


def test_revision_migration_upgrades_and_downgrades_on_an_isolated_database(tmp_path):
    db_path = tmp_path / "construction_model_revision.db"
    db_uri = f"sqlite:///{db_path}"
    assert "brayman_estimator.db" not in db_uri
    assert "instance/" not in db_uri
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        alembic_cfg = _cfg(db_uri)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == [HEAD]
        revision = script.get_revision(HEAD)
        assert revision.down_revision == PRIOR
        command.upgrade(alembic_cfg, PRIOR)
        engine = db.engine
        with engine.begin() as conn:
            assert not _has_table(conn, "project_construction_model_revisions")
            assert "construction_model_revision_id" not in _columns(
                conn, "calculation_result_intakes"
            )
            conn.execute(
                sa.text(
                    "INSERT INTO organizations ("
                    "id, legal_name, display_name, currency, is_active, "
                    "created_at, updated_at"
                    ") VALUES ("
                    "'ORG-CM', 'Synthetic', 'Synthetic', 'CAD', 1, "
                    "'2026-10-09 12:00:00', '2026-10-09 12:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO clients (name, organization_id, created_at) "
                    "VALUES ('Synthetic client', 'ORG-CM', '2026-10-09 12:00:00')"
                )
            )
            client_id = conn.execute(sa.text("SELECT id FROM clients")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO projects ("
                    "organization_id, name, status, client_id, created_at, "
                    "operating_state, operating_state_changed_at, drawing_requirement"
                    ") VALUES ("
                    "'ORG-CM', 'Synthetic deck', 'Estimating', :client_id, "
                    "'2026-10-09 12:00:00', 'ACTIVE', '2026-10-09 12:00:00', 'UNKNOWN')"
                ),
                {"client_id": client_id},
            )
            project_id = conn.execute(sa.text("SELECT id FROM projects")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO estimates ("
                    "organization_id, project_id, estimate_number, title, status, "
                    "created_at, updated_at"
                    ") VALUES ("
                    "'ORG-CM', :project_id, 'CM-1', 'Synthetic', 'Draft', "
                    "'2026-10-09 12:00:00', '2026-10-09 12:00:00')"
                ),
                {"project_id": project_id},
            )
            estimate_id = conn.execute(sa.text("SELECT id FROM estimates")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO estimate_versions ("
                    "estimate_id, version_number, status, subtotal, overhead_percent, "
                    "profit_percent, tax_percent, total, is_locked, created_at, updated_at"
                    ") VALUES ("
                    ":estimate_id, 1, 'Draft', 0, 0, 0, 0, 0, 0, "
                    "'2026-10-09 12:00:00', '2026-10-09 12:00:00')"
                ),
                {"estimate_id": estimate_id},
            )
            version_id = conn.execute(sa.text("SELECT id FROM estimate_versions")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO calculation_result_intakes ("
                    "organization_id, project_id, estimate_id, estimate_version_id, "
                    "result_id, fingerprint, engine_id, engine_version, "
                    "measurement_system, frozen_result, actor_display_name, ingested_at"
                    ") VALUES ("
                    "'ORG-CM', :project_id, :estimate_id, :version_id, "
                    "'historical', 'abc', 'engine', '1', 'imperial', "
                    "'{\"contract_version\":\"1\"}', 'Path Contractor', "
                    "'2026-10-09 12:00:00')"
                ),
                {
                    "project_id": project_id,
                    "estimate_id": estimate_id,
                    "version_id": version_id,
                },
            )

        command.upgrade(alembic_cfg, HEAD)
        with engine.begin() as conn:
            assert _has_table(conn, "project_construction_model_revisions")
            column = _columns(conn, "calculation_result_intakes")[
                "construction_model_revision_id"
            ]
            assert column[3] == 0
            linked = conn.execute(
                sa.text(
                    "SELECT construction_model_revision_id, frozen_result "
                    "FROM calculation_result_intakes"
                )
            ).fetchone()
            assert linked[0] is None
            assert "contract_version" in linked[1]

        command.downgrade(alembic_cfg, PRIOR)
        with engine.begin() as conn:
            assert [row[0] for row in conn.execute(sa.text("SELECT version_num FROM alembic_version"))] == [PRIOR]
            assert not _has_table(conn, "project_construction_model_revisions")
            assert "construction_model_revision_id" not in _columns(
                conn, "calculation_result_intakes"
            )
            kept = conn.execute(
                sa.text("SELECT result_id, frozen_result FROM calculation_result_intakes")
            ).fetchone()
            assert kept[0] == "historical"
            assert "contract_version" in kept[1]

        command.upgrade(alembic_cfg, HEAD)
        with engine.begin() as conn:
            assert [row[0] for row in conn.execute(sa.text("SELECT version_num FROM alembic_version"))] == [HEAD]
            again = conn.execute(
                sa.text(
                    "SELECT result_id, construction_model_revision_id "
                    "FROM calculation_result_intakes"
                )
            ).fetchone()
            assert again[0] == "historical"
            assert again[1] is None

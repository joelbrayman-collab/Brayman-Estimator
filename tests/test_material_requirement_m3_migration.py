"""The M3 check is additive. Existing requirement rows stay as they were."""

import os
from decimal import Decimal

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db


PRIOR = "q7d8e9f0a1b2"
M3_REVISION = "r8e9f0a1b2c3"
HEAD = "s9f0a1b2c3d4"
PRESERVED = (
    "organizations",
    "projects",
    "estimates",
    "estimate_line_items",
    "estimate_costing_snapshots",
    "estimate_costing_snapshot_lines",
    "supplier_packages",
    "supplier_package_lines",
    "supplier_product_price_evidence",
    "material_requirements",
    "canonical_materials",
)


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


def _counts(conn):
    return {
        name: conn.execute(sa.text("SELECT COUNT(*) FROM {0}".format(name))).scalar()
        for name in PRESERVED
    }


def _check_sql(conn, table):
    return conn.execute(
        sa.text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = :name"),
        {"name": table},
    ).scalar()


def test_m3_check_keeps_existing_requirements(tmp_path):
    db_path = tmp_path / "m3_migration.db"
    db_uri = "sqlite:///{0}".format(db_path)
    assert "brayman_estimator.db" not in db_uri
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    with test_app.app_context():
        alembic_cfg = _cfg(db_uri)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == [HEAD]
        command.upgrade(alembic_cfg, PRIOR)
        engine = db.engine
        with engine.begin() as conn:
            assert "M3" not in _check_sql(conn, "material_requirements")
            conn.execute(
                sa.text(
                    "INSERT INTO organizations ("
                    "id, legal_name, display_name, currency, is_active, "
                    "created_at, updated_at"
                    ") VALUES ("
                    "'ORG-M3', 'Synthetic', 'Synthetic', 'CAD', 1, "
                    "'2026-10-08 12:00:00', '2026-10-08 12:00:00')"
                )
            )
            conn.execute(
                sa.text(
                    "INSERT INTO clients ("
                    "name, organization_id, created_at"
                    ") VALUES ('Synthetic client', 'ORG-M3', '2026-10-08 12:00:00')"
                )
            )
            client_id = conn.execute(sa.text("SELECT id FROM clients")).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO projects ("
                    "organization_id, name, status, client_id, created_at, "
                    "operating_state, operating_state_changed_at, drawing_requirement"
                    ") VALUES ("
                    "'ORG-M3', 'Synthetic slab', 'Estimating', :client_id, "
                    "'2026-10-08 12:00:00', 'ACTIVE', '2026-10-08 12:00:00', 'UNKNOWN')"
                ),
                {"client_id": client_id},
            )
            project_id = conn.execute(sa.text("SELECT id FROM projects")).scalar()
            material_id = conn.execute(
                sa.text(
                    "SELECT id FROM canonical_materials WHERE canonical_uom = 'EA' LIMIT 1"
                )
            ).scalar()
            for index, unit in enumerate(("EA", "LF", "SF", "BF"), start=1):
                conn.execute(
                    sa.text(
                        "INSERT INTO material_requirements ("
                        "organization_id, project_id, canonical_material_id, quantity, "
                        "canonical_uom, status, source_kind, note, actor_display_name, "
                        "created_at, updated_at"
                        ") VALUES ("
                        "'ORG-M3', :project_id, :material_id, :quantity, :unit, "
                        "'DRAFT', 'DEMO_SYNTHETIC', :note, 'Joel Brayman', "
                        "'2026-10-08 12:00:00', '2026-10-08 12:00:00')"
                    ),
                    {
                        "project_id": project_id,
                        "material_id": material_id,
                        "quantity": "{0}.0000".format(index),
                        "unit": unit,
                        "note": "kept {0}".format(unit),
                    },
                )
            before_rows = conn.execute(
                sa.text(
                    "SELECT canonical_uom, quantity, note FROM material_requirements "
                    "ORDER BY canonical_uom"
                )
            ).fetchall()
            before_counts = _counts(conn)
            before_materials = conn.execute(
                sa.text(
                    "SELECT code, category, canonical_uom FROM canonical_materials "
                    "ORDER BY code"
                )
            ).fetchall()

        command.upgrade(alembic_cfg, M3_REVISION)
        with engine.begin() as conn:
            assert _counts(conn) == before_counts
            after_rows = conn.execute(
                sa.text(
                    "SELECT canonical_uom, quantity, note FROM material_requirements "
                    "ORDER BY canonical_uom"
                )
            ).fetchall()
            assert after_rows == before_rows
            after_materials = conn.execute(
                sa.text(
                    "SELECT code, category, canonical_uom FROM canonical_materials "
                    "ORDER BY code"
                )
            ).fetchall()
            assert after_materials == before_materials
            requirement_sql = _check_sql(conn, "material_requirements")
            canonical_sql = _check_sql(conn, "canonical_materials")
            for unit in ("EA", "LF", "SF", "BF", "M3"):
                assert unit in requirement_sql
                assert unit in canonical_sql
            assert "CONCRETE" in canonical_sql
            conn.execute(
                sa.text(
                    "INSERT INTO canonical_materials ("
                    "code, display_name, status, kind, category, canonical_uom, "
                    "substitution_policy, created_at, updated_at"
                    ") VALUES ("
                    "'CAL-CONC-VOL', 'Concrete', 'ACTIVE', 'GENERIC', 'CONCRETE', 'M3', "
                    "'ALLOWED', '2026-10-08 12:00:00', '2026-10-08 12:00:00')"
                )
            )
            concrete_id = conn.execute(
                sa.text("SELECT id FROM canonical_materials WHERE code = 'CAL-CONC-VOL'")
            ).scalar()
            conn.execute(
                sa.text(
                    "INSERT INTO material_requirements ("
                    "organization_id, project_id, canonical_material_id, quantity, "
                    "canonical_uom, status, source_kind, note, actor_display_name, "
                    "created_at, updated_at"
                    ") VALUES ("
                    "'ORG-M3', :project_id, :material_id, 45.3070, 'M3', "
                    "'DRAFT', 'DEMO_SYNTHETIC', 'purchasing cubic metres', "
                    "'Joel Brayman', '2026-10-08 12:00:00', '2026-10-08 12:00:00')"
                ),
                {"project_id": project_id, "material_id": concrete_id},
            )
            stored = conn.execute(
                sa.text(
                    "SELECT quantity, canonical_uom FROM material_requirements "
                    "WHERE canonical_uom = 'M3'"
                )
            ).fetchone()
            assert Decimal(str(stored[0])) == Decimal("45.3070")
            assert stored[1] == "M3"
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == [M3_REVISION]

        with engine.begin() as conn:
            conn.execute(
                sa.text("DELETE FROM material_requirements WHERE canonical_uom = 'M3'")
            )
            conn.execute(
                sa.text("DELETE FROM canonical_materials WHERE code = 'CAL-CONC-VOL'")
            )
        command.downgrade(alembic_cfg, PRIOR)
        with engine.begin() as conn:
            assert "M3" not in _check_sql(conn, "material_requirements")
            kept = conn.execute(
                sa.text(
                    "SELECT canonical_uom, note FROM material_requirements "
                    "ORDER BY canonical_uom"
                )
            ).fetchall()
            assert [row[0] for row in kept] == ["BF", "EA", "LF", "SF"]
            heads = conn.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()
            assert [row[0] for row in heads] == [PRIOR]

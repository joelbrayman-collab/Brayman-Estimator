"""PKG-S16 schema/migration regression. Disposable databases only.

Do not run against instance/brayman_estimator.db.
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.exc import IntegrityError

from app import create_app, db


PREV_HEAD = "g7b8c9d0e1f2"
S16_REVISION = "h8c9d0e1f2a3"
NOW = "2026-09-23 12:00:00"


def _alembic_cfg(db_uri):
    cfg_path = (
        "migrations/alembic.ini"
        if os.path.exists("migrations/alembic.ini")
        else "alembic.ini"
    )
    alembic_cfg = Config(cfg_path)
    alembic_cfg.set_main_option("script_location", "migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
    return alembic_cfg


def _disposable_app(tmp_path, name="s16.db"):
    db_path = tmp_path / name
    db_uri = f"sqlite:///{db_path}"
    assert "brayman_estimator.db" not in db_uri
    test_app = create_app({"SQLALCHEMY_DATABASE_URI": db_uri, "TESTING": True})
    return test_app, db_uri, db_path


def _unique_names(conn, table_name):
    insp = sa.inspect(conn)
    names = set()
    for uq in insp.get_unique_constraints(table_name):
        names.add(tuple(uq.get("column_names") or []))
    for ix in insp.get_indexes(table_name):
        if ix.get("unique"):
            names.add(tuple(ix.get("column_names") or []))
    rows = conn.execute(sa.text(f'PRAGMA index_list("{table_name}")')).fetchall()
    for row in rows:
        if not row[2]:
            continue
        info = conn.execute(sa.text(f'PRAGMA index_info("{row[1]}")')).fetchall()
        names.add(tuple(item[2] for item in info))
    return names


def _has_table(conn, name):
    return bool(
        conn.execute(
            sa.text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=:name"
            ),
            {"name": name},
        ).scalar()
    )


def _column_names(conn, table_name):
    rows = conn.execute(sa.text(f'PRAGMA table_info("{table_name}")')).fetchall()
    return {row[1] for row in rows}


def _sql_constraints(conn, table_name):
    row = conn.execute(
        sa.text(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=:name"
        ),
        {"name": table_name},
    ).scalar()
    return row or ""


def _assert_integrity_error(conn, fn):
    nested = conn.begin_nested()
    try:
        fn()
        nested.commit()
        pytest.fail("expected IntegrityError")
    except IntegrityError:
        nested.rollback()


def _insert_org(conn, org_id, name):
    conn.execute(
        sa.text(
            """
            INSERT INTO organizations (
                id, legal_name, display_name, currency, is_active,
                created_at, updated_at
            ) VALUES (
                :id, :name, :name, 'CAD', 1, :now, :now
            )
            """
        ),
        {"id": org_id, "name": name, "now": NOW},
    )


def _insert_user(conn, email):
    result = conn.execute(
        sa.text(
            """
            INSERT INTO users (
                email, display_name, password_hash, is_active,
                credentials_epoch, created_at, updated_at
            ) VALUES (
                :email, :email, 'hash', 1, 0, :now, :now
            )
            """
        ),
        {"email": email, "now": NOW},
    )
    return result.lastrowid


def _insert_client(conn, org_id, name):
    result = conn.execute(
        sa.text(
            """
            INSERT INTO clients (organization_id, name, created_at)
            VALUES (:org_id, :name, :now)
            """
        ),
        {"org_id": org_id, "name": name, "now": NOW},
    )
    return result.lastrowid


def _insert_project(conn, org_id, client_id, name, number):
    result = conn.execute(
        sa.text(
            """
            INSERT INTO projects (
                organization_id, name, project_number, status, client_id,
                created_at, operating_state, operating_state_changed_at
            ) VALUES (
                :org_id, :name, :number, 'Lead', :client_id,
                :now, 'ACTIVE', :now
            )
            """
        ),
        {
            "org_id": org_id,
            "name": name,
            "number": number,
            "client_id": client_id,
            "now": NOW,
        },
    )
    return result.lastrowid


def _insert_estimate(conn, project_id, number, title):
    result = conn.execute(
        sa.text(
            """
            INSERT INTO estimates (
                project_id, estimate_number, title, status,
                created_at, updated_at
            ) VALUES (
                :project_id, :number, :title, 'Draft', :now, :now
            )
            """
        ),
        {
            "project_id": project_id,
            "number": number,
            "title": title,
            "now": NOW,
        },
    )
    return result.lastrowid


def _insert_template(conn, org_id, name):
    columns = _column_names(conn, "proposal_templates")
    fields = {
        "name": name,
        "show_detailed_pricing": 1,
        "show_section_totals": 1,
        "show_allowances": 1,
        "show_tax": 1,
        "is_default": 0,
        "is_active": 1,
        "created_at": NOW,
        "updated_at": NOW,
    }
    if "organization_id" in columns:
        fields["organization_id"] = org_id
    keys = ", ".join(fields)
    params = ", ".join(f":{k}" for k in fields)
    result = conn.execute(
        sa.text(f"INSERT INTO proposal_templates ({keys}) VALUES ({params})"),
        fields,
    )
    return result.lastrowid


def _insert_proposal(conn, number, estimate_id, template_id, title):
    columns = _column_names(conn, "proposals")
    fields = {
        "proposal_number": number,
        "estimate_id": estimate_id,
        "proposal_template_id": template_id,
        "title": title,
        "status": "Draft",
        "client_name": "Client",
        "project_name": "Project",
        "estimate_number": "EST-X",
        "estimate_version_number": 1,
        "subtotal": 0,
        "overhead_amount": 0,
        "profit_amount": 0,
        "tax_amount": 0,
        "total": 0,
        "show_detailed_pricing": 1,
        "show_section_totals": 1,
        "show_allowances": 1,
        "show_tax": 1,
        "created_at": NOW,
        "updated_at": NOW,
    }
    if "estimate_version_id" in columns:
        fields["estimate_version_id"] = None
    for col, default in (
        ("overhead_percent", 0),
        ("profit_percent", 0),
        ("tax_percent", 0),
    ):
        if col in columns:
            fields[col] = default
    keys = ", ".join(fields)
    params = ", ".join(f":{k}" for k in fields)
    result = conn.execute(
        sa.text(f"INSERT INTO proposals ({keys}) VALUES ({params})"),
        fields,
    )
    return result.lastrowid


def _insert_change_order(conn, project_id, number, title, total="100.00"):
    result = conn.execute(
        sa.text(
            """
            INSERT INTO change_orders (
                project_id, number, title, status, created_at, updated_at,
                subtotal, markup_percent, markup, tax_percent, tax, total
            ) VALUES (
                :project_id, :number, :title, 'Approved', :now, :now,
                :total, 0, 0, 0, 0, :total
            )
            """
        ),
        {
            "project_id": project_id,
            "number": number,
            "title": title,
            "now": NOW,
            "total": total,
        },
    )
    return result.lastrowid


def _insert_person(conn, org_id, user_id, wage="25.00"):
    result = conn.execute(
        sa.text(
            """
            INSERT INTO organization_people (
                organization_id, full_name, address, mobile_number,
                email_address, hourly_wage, is_active, created_at,
                created_by_user_id, updated_at
            ) VALUES (
                :org_id, 'S16 Worker', '1 Street', '555-0000',
                's16-worker@example.com', :wage, 1, :now, :user_id, :now
            )
            """
        ),
        {"org_id": org_id, "wage": wage, "now": NOW, "user_id": user_id},
    )
    return result.lastrowid


def _seed_two_org_commercial_graph(conn):
    _insert_org(conn, "ORG-S16-A", "Org A")
    _insert_org(conn, "ORG-S16-B", "Org B")
    user_id = _insert_user(conn, "s16-actor@example.com")
    client_a = _insert_client(conn, "ORG-S16-A", "Client A")
    client_b = _insert_client(conn, "ORG-S16-B", "Client B")
    project_a = _insert_project(
        conn, "ORG-S16-A", client_a, "Job A", "PRJ-S16-A"
    )
    project_b = _insert_project(
        conn, "ORG-S16-B", client_b, "Job B", "PRJ-S16-B"
    )
    est_a = _insert_estimate(conn, project_a, "EST-1001", "Estimate A")
    est_b = _insert_estimate(conn, project_b, "EST-2002", "Estimate B")
    tmpl_a = _insert_template(conn, "ORG-S16-A", "Template A")
    tmpl_b = _insert_template(conn, "ORG-S16-B", "Template B")
    prop_a = _insert_proposal(conn, "PROP-1001", est_a, tmpl_a, "Proposal A")
    prop_b = _insert_proposal(conn, "PROP-2002", est_b, tmpl_b, "Proposal B")
    co_a = _insert_change_order(conn, project_a, "CO-1001", "CO A", "250.00")
    co_b = _insert_change_order(conn, project_b, "CO-2002", "CO B", "400.00")
    person_id = _insert_person(conn, "ORG-S16-A", user_id, "32.50")
    return {
        "user_id": user_id,
        "project_a": project_a,
        "project_b": project_b,
        "est_a": est_a,
        "est_b": est_b,
        "prop_a": prop_a,
        "prop_b": prop_b,
        "co_a": co_a,
        "co_b": co_b,
        "person_id": person_id,
    }


def test_s16_revision_down_revision_and_single_head():
    from migrations.versions.h8c9d0e1f2a3_s16_org_scoped_commercial_schema import (
        down_revision,
        revision,
    )

    assert revision == S16_REVISION
    assert down_revision == PREV_HEAD
    cfg = _alembic_cfg("sqlite:///:memory:")
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == [S16_REVISION]
    assert script.get_revision(S16_REVISION).down_revision == PREV_HEAD


def test_s16_upgrade_downgrade_reupgrade_and_schema_law(tmp_path):
    test_app, db_uri, db_path = _disposable_app(tmp_path)
    assert str(db_path).endswith("s16.db")
    with test_app.app_context():
        alembic_cfg = _alembic_cfg(db_uri)
        script = ScriptDirectory.from_config(alembic_cfg)
        assert script.get_heads() == [S16_REVISION]

        command.upgrade(alembic_cfg, PREV_HEAD)
        engine = db.engine
        with engine.begin() as conn:
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == [PREV_HEAD]
            assert not _has_table(conn, "organization_person_wage_events")
            seed = _seed_two_org_commercial_graph(conn)

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == [S16_REVISION]
            assert _has_table(conn, "organization_person_wage_events")
            wage_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM organization_person_wage_events")
            ).scalar()
            assert wage_count == 0

            est_orgs = {
                row[0]: row[1]
                for row in conn.execute(
                    sa.text(
                        "SELECT id, organization_id FROM estimates "
                        "ORDER BY id"
                    )
                )
            }
            assert est_orgs[seed["est_a"]] == "ORG-S16-A"
            assert est_orgs[seed["est_b"]] == "ORG-S16-B"
            missing_est = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM estimates WHERE organization_id IS NULL"
                )
            ).scalar()
            assert missing_est == 0

            prop_orgs = {
                row[0]: row[1]
                for row in conn.execute(
                    sa.text(
                        "SELECT id, organization_id FROM proposals ORDER BY id"
                    )
                )
            }
            assert prop_orgs[seed["prop_a"]] == "ORG-S16-A"
            assert prop_orgs[seed["prop_b"]] == "ORG-S16-B"
            missing_prop = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM proposals WHERE organization_id IS NULL"
                )
            ).scalar()
            assert missing_prop == 0

            co_rows = list(
                conn.execute(
                    sa.text(
                        "SELECT id, organization_id, approved_internal_direct_cost, "
                        "total FROM change_orders ORDER BY id"
                    )
                )
            )
            co_orgs = {row[0]: row[1] for row in co_rows}
            assert co_orgs[seed["co_a"]] == "ORG-S16-A"
            assert co_orgs[seed["co_b"]] == "ORG-S16-B"
            missing_co = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM change_orders "
                    "WHERE organization_id IS NULL"
                )
            ).scalar()
            assert missing_co == 0
            for row in co_rows:
                assert row[2] is None
                assert row[3] is not None

            est_uniques = _unique_names(conn, "estimates")
            assert ("organization_id", "estimate_number") in est_uniques
            assert ("estimate_number",) not in est_uniques
            prop_uniques = _unique_names(conn, "proposals")
            assert ("organization_id", "proposal_number") in prop_uniques
            assert ("proposal_number",) not in prop_uniques
            co_uniques = _unique_names(conn, "change_orders")
            assert ("organization_id", "number") in co_uniques
            assert ("number",) not in co_uniques

            co_sql = _sql_constraints(conn, "change_orders")
            assert (
                "ck_change_orders_approved_internal_direct_cost_non_negative"
                in co_sql
            )
            punch_sql = _sql_constraints(conn, "project_punch_list_items")
            assert "ck_project_punch_list_items_source_association" in punch_sql

            person_wage = conn.execute(
                sa.text(
                    "SELECT hourly_wage FROM organization_people WHERE id=:id"
                ),
                {"id": seed["person_id"]},
            ).scalar()
            assert Decimal(str(person_wage)) == Decimal("32.50")

            conn.execute(
                sa.text(
                    """
                    INSERT INTO estimates (
                        organization_id, project_id, estimate_number, title,
                        status, created_at, updated_at
                    ) VALUES (
                        'ORG-S16-B', :project_id, 'EST-1001', 'Cross-org',
                        'Draft', :now, :now
                    )
                    """
                ),
                {"project_id": seed["project_b"], "now": NOW},
            )
            _assert_integrity_error(
                conn,
                lambda: conn.execute(
                    sa.text(
                        """
                        INSERT INTO estimates (
                            organization_id, project_id, estimate_number, title,
                            status, created_at, updated_at
                        ) VALUES (
                            'ORG-S16-A', :project_id, 'EST-1001', 'Dup',
                            'Draft', :now, :now
                        )
                        """
                    ),
                    {"project_id": seed["project_a"], "now": NOW},
                ),
            )

            conn.execute(
                sa.text(
                    """
                    INSERT INTO proposals (
                        organization_id, proposal_number, estimate_id,
                        proposal_template_id, title, status, client_name,
                        project_name, estimate_number, estimate_version_number,
                        subtotal, overhead_percent, profit_percent, tax_percent,
                        overhead_amount, profit_amount, tax_amount, total,
                        show_detailed_pricing, show_section_totals,
                        show_allowances, show_tax, created_at, updated_at
                    ) VALUES (
                        'ORG-S16-B', 'PROP-1001', :estimate_id, :template_id,
                        'Cross-org', 'Draft', 'Client', 'Project', 'EST-X', 1,
                        0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, :now, :now
                    )
                    """
                ),
                {
                    "estimate_id": seed["est_b"],
                    "template_id": conn.execute(
                        sa.text(
                            "SELECT id FROM proposal_templates "
                            "WHERE organization_id='ORG-S16-B'"
                        )
                    ).scalar(),
                    "now": NOW,
                },
            )
            _assert_integrity_error(
                conn,
                lambda: conn.execute(
                    sa.text(
                        """
                        INSERT INTO proposals (
                            organization_id, proposal_number, estimate_id,
                            proposal_template_id, title, status, client_name,
                            project_name, estimate_number,
                            estimate_version_number, subtotal, overhead_percent,
                            profit_percent, tax_percent, overhead_amount,
                            profit_amount, tax_amount, total,
                            show_detailed_pricing, show_section_totals,
                            show_allowances, show_tax, created_at, updated_at
                        ) VALUES (
                            'ORG-S16-A', 'PROP-1001', :estimate_id,
                            :template_id, 'Dup', 'Draft', 'Client', 'Project',
                            'EST-X', 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
                            :now, :now
                        )
                        """
                    ),
                    {
                        "estimate_id": seed["est_a"],
                        "template_id": conn.execute(
                            sa.text(
                                "SELECT id FROM proposal_templates "
                                "WHERE organization_id='ORG-S16-A'"
                            )
                        ).scalar(),
                        "now": NOW,
                    },
                ),
            )

            conn.execute(
                sa.text(
                    """
                    INSERT INTO change_orders (
                        organization_id, project_id, number, title, status,
                        created_at, updated_at, subtotal, markup_percent,
                        markup, tax_percent, tax, total
                    ) VALUES (
                        'ORG-S16-B', :project_id, 'CO-1001', 'Cross-org',
                        'Draft', :now, :now, 0, 0, 0, 0, 0, 0
                    )
                    """
                ),
                {"project_id": seed["project_b"], "now": NOW},
            )
            _assert_integrity_error(
                conn,
                lambda: conn.execute(
                    sa.text(
                        """
                        INSERT INTO change_orders (
                            organization_id, project_id, number, title, status,
                            created_at, updated_at, subtotal, markup_percent,
                            markup, tax_percent, tax, total
                        ) VALUES (
                            'ORG-S16-A', :project_id, 'CO-1001', 'Dup',
                            'Draft', :now, :now, 0, 0, 0, 0, 0, 0
                        )
                        """
                    ),
                    {"project_id": seed["project_a"], "now": NOW},
                ),
            )

            conn.execute(
                sa.text(
                    """
                    UPDATE change_orders
                    SET approved_internal_direct_cost = NULL
                    WHERE id = :id
                    """
                ),
                {"id": seed["co_a"]},
            )
            conn.execute(
                sa.text(
                    """
                    UPDATE change_orders
                    SET approved_internal_direct_cost = 0
                    WHERE id = :id
                    """
                ),
                {"id": seed["co_a"]},
            )
            conn.execute(
                sa.text(
                    """
                    UPDATE change_orders
                    SET approved_internal_direct_cost = 12.50
                    WHERE id = :id
                    """
                ),
                {"id": seed["co_a"]},
            )
            _assert_integrity_error(
                conn,
                lambda: conn.execute(
                    sa.text(
                        """
                        UPDATE change_orders
                        SET approved_internal_direct_cost = -0.01
                        WHERE id = :id
                        """
                    ),
                    {"id": seed["co_a"]},
                ),
            )
            conn.execute(
                sa.text(
                    """
                    UPDATE change_orders
                    SET approved_internal_direct_cost = NULL
                    WHERE id = :id
                    """
                ),
                {"id": seed["co_a"]},
            )

            punch_base = {
                "organization_id": "ORG-S16-A",
                "project_id": seed["project_a"],
                "description": "Punch",
                "status": "OPEN",
                "origin_type": "CONTRACTOR",
                "created_at": NOW,
                "created_by_user_id": seed["user_id"],
                "updated_at": NOW,
            }

            def insert_punch(**extra):
                fields = dict(punch_base)
                fields.update(extra)
                keys = ", ".join(fields)
                params = ", ".join(f":{k}" for k in fields)
                conn.execute(
                    sa.text(
                        f"INSERT INTO project_punch_list_items ({keys}) "
                        f"VALUES ({params})"
                    ),
                    fields,
                )

            insert_punch(work_source_type="ORIGINAL_SCOPE")
            insert_punch(
                work_source_type="CHANGE_ORDER",
                source_change_order_id=seed["co_a"],
            )
            insert_punch(work_source_type="OTHER")
            _assert_integrity_error(
                conn,
                lambda: insert_punch(
                    work_source_type="ORIGINAL_SCOPE",
                    source_change_order_id=seed["co_a"],
                ),
            )
            _assert_integrity_error(
                conn,
                lambda: insert_punch(work_source_type="CHANGE_ORDER"),
            )
            _assert_integrity_error(
                conn,
                lambda: insert_punch(
                    work_source_type="CHANGE_ORDER",
                    source_change_order_id=seed["co_a"],
                    source_project_work_id=1,
                ),
            )
            _assert_integrity_error(
                conn,
                lambda: insert_punch(
                    work_source_type="OTHER",
                    source_change_order_id=seed["co_a"],
                ),
            )
            _assert_integrity_error(
                conn,
                lambda: insert_punch(
                    work_source_type="OTHER",
                    source_project_work_id=1,
                ),
            )

            conn.execute(
                sa.text(
                    """
                    INSERT INTO organization_person_wage_events (
                        organization_id, person_id, previous_hourly_wage,
                        hourly_wage, created_at, actor_user_id
                    ) VALUES (
                        'ORG-S16-A', :person_id, NULL, 40.00, :now, :user_id
                    )
                    """
                ),
                {
                    "person_id": seed["person_id"],
                    "now": NOW,
                    "user_id": seed["user_id"],
                },
            )
            conn.execute(
                sa.text(
                    """
                    INSERT INTO organization_person_wage_events (
                        organization_id, person_id, previous_hourly_wage,
                        hourly_wage, created_at, actor_user_id
                    ) VALUES (
                        'ORG-S16-A', :person_id, 40.00, 42.00, :now, :user_id
                    )
                    """
                ),
                {
                    "person_id": seed["person_id"],
                    "now": NOW,
                    "user_id": seed["user_id"],
                },
            )
            event_count = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM organization_person_wage_events "
                    "WHERE person_id=:id"
                ),
                {"id": seed["person_id"]},
            ).scalar()
            assert event_count == 2
            _assert_integrity_error(
                conn,
                lambda: conn.execute(
                    sa.text(
                        """
                        INSERT INTO organization_person_wage_events (
                            organization_id, person_id, previous_hourly_wage,
                            hourly_wage, created_at, actor_user_id
                        ) VALUES (
                            'ORG-S16-A', :person_id, NULL, -1, :now, :user_id
                        )
                        """
                    ),
                    {
                        "person_id": seed["person_id"],
                        "now": NOW,
                        "user_id": seed["user_id"],
                    },
                ),
            )
            _assert_integrity_error(
                conn,
                lambda: conn.execute(
                    sa.text(
                        """
                        INSERT INTO organization_person_wage_events (
                            organization_id, person_id, previous_hourly_wage,
                            hourly_wage, created_at, actor_user_id
                        ) VALUES (
                            'ORG-S16-A', :person_id, -0.01, 40.00, :now,
                            :user_id
                        )
                        """
                    ),
                    {
                        "person_id": seed["person_id"],
                        "now": NOW,
                        "user_id": seed["user_id"],
                    },
                ),
            )
            conn.execute(sa.text("DELETE FROM estimates WHERE title = 'Cross-org'"))
            conn.execute(sa.text("DELETE FROM proposals WHERE title = 'Cross-org'"))
            conn.execute(
                sa.text("DELETE FROM change_orders WHERE title = 'Cross-org'")
            )

        command.downgrade(alembic_cfg, PREV_HEAD)
        with engine.begin() as conn:
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == [PREV_HEAD]
            assert not _has_table(conn, "organization_person_wage_events")
            est_cols = _column_names(conn, "estimates")
            assert "organization_id" not in est_cols
            prop_cols = _column_names(conn, "proposals")
            assert "organization_id" not in prop_cols
            co_cols = _column_names(conn, "change_orders")
            assert "organization_id" not in co_cols
            assert "approved_internal_direct_cost" not in co_cols
            punch_sql = _sql_constraints(conn, "project_punch_list_items")
            assert "ck_project_punch_list_items_source_association" not in punch_sql
            est_uniques = _unique_names(conn, "estimates")
            assert ("estimate_number",) in est_uniques
            assert ("organization_id", "estimate_number") not in est_uniques
            prop_uniques = _unique_names(conn, "proposals")
            assert ("proposal_number",) in prop_uniques
            co_uniques = _unique_names(conn, "change_orders")
            assert ("number",) in co_uniques
            _assert_integrity_error(
                conn,
                lambda: conn.execute(
                    sa.text(
                        """
                        INSERT INTO estimates (
                            project_id, estimate_number, title, status,
                            created_at, updated_at
                        ) VALUES (
                            :project_id, 'EST-1001', 'Global dup', 'Draft',
                            :now, :now
                        )
                        """
                    ),
                    {"project_id": seed["project_b"], "now": NOW},
                ),
            )

        command.upgrade(alembic_cfg, "head")
        with engine.begin() as conn:
            heads = conn.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).fetchall()
            assert [row[0] for row in heads] == [S16_REVISION]
            assert _has_table(conn, "organization_person_wage_events")
            wage_count = conn.execute(
                sa.text("SELECT COUNT(*) FROM organization_person_wage_events")
            ).scalar()
            assert wage_count == 0
            missing = conn.execute(
                sa.text(
                    "SELECT COUNT(*) FROM estimates WHERE organization_id IS NULL"
                )
            ).scalar()
            assert missing == 0
            person_wage = conn.execute(
                sa.text(
                    "SELECT hourly_wage FROM organization_people WHERE id=:id"
                ),
                {"id": seed["person_id"]},
            ).scalar()
            assert Decimal(str(person_wage)) == Decimal("32.50")


def test_s16_unresolved_proposal_fails_upgrade(tmp_path):
    test_app, db_uri, _ = _disposable_app(tmp_path, "s16_fail.db")
    with test_app.app_context():
        alembic_cfg = _alembic_cfg(db_uri)
        command.upgrade(alembic_cfg, PREV_HEAD)
        engine = db.engine
        with engine.begin() as conn:
            _insert_org(conn, "ORG-S16-A", "Org A")
            _insert_user(conn, "s16-fail@example.com")
            client_id = _insert_client(conn, "ORG-S16-A", "Client A")
            project_id = _insert_project(
                conn, "ORG-S16-A", client_id, "Job A", "PRJ-S16-FAIL"
            )
            _insert_estimate(conn, project_id, "EST-FAIL", "Estimate")
            tmpl_id = _insert_template(conn, "ORG-S16-A", "Template")
            conn.execute(
                sa.text(
                    """
                    INSERT INTO proposals (
                        proposal_number, estimate_id, proposal_template_id,
                        title, status, client_name, project_name,
                        estimate_number, estimate_version_number, subtotal,
                        overhead_percent, profit_percent, tax_percent,
                        overhead_amount, profit_amount, tax_amount, total,
                        show_detailed_pricing, show_section_totals,
                        show_allowances, show_tax, created_at, updated_at
                    ) VALUES (
                        'PROP-ORPHAN', NULL, :template_id, 'Orphan', 'Draft',
                        'Client', 'Project', 'EST-X', 1, 0, 0, 0, 0, 0, 0, 0,
                        0, 1, 1, 1, 1, :now, :now
                    )
                    """
                ),
                {"template_id": tmpl_id, "now": NOW},
            )
        with pytest.raises(RuntimeError, match="could not resolve organization_id"):
            command.upgrade(alembic_cfg, "head")


def test_s16_generators_still_global():
    import inspect

    from app.project_controls import repository as co_repo
    from app.services import estimates as estimates_mod
    from app.services import proposals as proposals_mod

    estimate_src = inspect.getsource(estimates_mod.suggest_next_estimate_number)
    proposal_src = inspect.getsource(proposals_mod.suggest_next_proposal_number)
    co_src = inspect.getsource(co_repo.next_change_order_number)
    assert "organization_id" not in estimate_src
    assert "organization_id" not in proposal_src
    assert "organization_id" not in co_src
    assert "Estimate.query.filter" in estimate_src
    assert "Proposal.query.filter" in proposal_src

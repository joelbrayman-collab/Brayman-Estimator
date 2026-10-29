"""Purchase orders: the office cancels, either side marks delivered (Joel, 21 Oct 2026). Synthetic data only."""

from __future__ import annotations

from datetime import date, timedelta
from app.services.local_time import local_today
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app import create_app, db
from app.models.supplier_portal import SupplierDeliveryChange, SupplierPurchaseOrder, SupplierRequestEvent
from app.services import supplier_hub as H
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.test_supplier_hub import SIGN, _concrete_order, _fresh_login_per_request, app, client  # noqa: F401


def _order(order_id):
    return db.session.get(SupplierPurchaseOrder, order_id)


def test_the_office_cancels_a_confirmed_order_with_a_reason_and_the_supplier_sees_it(app, client):
    project, tomlinson, darcy, _user, order = _concrete_order(app, client)
    client.post(f"/projects/{project.id}/orders/{order.id}/delivery-change",
                data={**SIGN, "new_date": (order.scheduled_date + timedelta(days=1)).isoformat(), "reason": "Weather"})
    assert SupplierDeliveryChange.query.filter_by(status="PENDING").count() == 1
    from app.services import supplier_signing as SS
    waiting = SupplierDeliveryChange.query.filter_by(status="PENDING").one()
    assert SS.change_signing(waiting).status == "SENT"  # signed by the office, waiting for the store
    page = client.get(f"/projects/{project.id}/supplier-requests").get_data(as_text=True)
    assert f'data-cancel-order="{order.id}"' in page and f'data-mark-delivered="{order.id}"' in page
    refused = client.post(f"/projects/{project.id}/orders/{order.id}/cancel", data={"reason": " "}, follow_redirects=True)
    assert b"Say why the order is cancelled" in refused.data and _order(order.id).status == "CONFIRMED"
    client.post(f"/projects/{project.id}/orders/{order.id}/cancel", data={"reason": "Pour moved to the spring"})
    assert _order(order.id).status == "CANCELLED"
    assert SupplierDeliveryChange.query.filter_by(status="PENDING").count() == 0  # the waiting change is withdrawn
    # FG-041 reconciled with cancel (28 Oct 2026): the withdrawn change's signing is voided, never signed; the
    # fully signed order keeps its executed record.
    assert SS.change_signing(waiting).status == "VOIDED"
    assert SS.order_signing(_order(order.id)).executed_at is not None
    event = SupplierRequestEvent.query.filter_by(share_id=order.share_id, event_type="ORDER_CANCELLED").one()
    assert event.actor_side == "CONTRACTOR" and "Pour moved to the spring" in event.detail
    supplier_page = darcy.get(f"/supplier/{tomlinson.supplier_id}/requests/{order.share_id}").get_data(as_text=True)
    assert 'data-order-cancelled="true"' in supplier_page and "Pour moved to the spring" in supplier_page
    assert "Change the delivery" not in supplier_page
    deliveries = darcy.get(f"/supplier/{tomlinson.supplier_id}/deliveries").get_data(as_text=True)
    assert f'data-cancelled-delivery="{order.number}"' in deliveries and f'data-delivery="{order.number}"' not in deliveries
    assert H.upcoming_deliveries(organization_id=DEFAULT_ORGANIZATION_ID) == []
    with pytest.raises(H.SupplierHubError, match="already cancelled"):
        H.cancel_order(_order(order.id), user=None, reason="again")


def test_either_side_marks_a_confirmed_order_delivered_and_it_leaves_upcoming_deliveries(app, client):
    from tests.test_core_close_close_reopen_fg035 import _make_owner

    project, tomlinson, darcy, _user, order = _concrete_order(app, client)
    order.scheduled_date = local_today() + timedelta(days=2); db.session.commit()
    assert [r["order"].id for r in H.upcoming_deliveries(organization_id=DEFAULT_ORGANIZATION_ID)] == [order.id]
    _make_owner()
    assert 'data-open-orders="1"' in client.get(f"/projects/{project.id}/close").get_data(as_text=True)
    future = (local_today() + timedelta(days=1)).isoformat()
    refused = darcy.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/delivered", data={"delivered_on": future},
                         follow_redirects=True)
    assert b"cannot be in the future" in refused.data and _order(order.id).status == "CONFIRMED"
    darcy.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/delivered",
               data={"delivered_on": local_today().isoformat(), "note": "Pumped at 7:40"})
    delivered = _order(order.id)
    assert delivered.status == "DELIVERED"
    closure = H.order_closure(delivered)
    assert closure["day"] == local_today() and closure["note"] == "Pumped at 7:40" and closure["side"] == "SUPPLIER"
    assert H.upcoming_deliveries(organization_id=DEFAULT_ORGANIZATION_ID) == []  # Field and the calendar read this
    assert "data-open-orders" not in client.get(f"/projects/{project.id}/close").get_data(as_text=True)
    office = client.get(f"/projects/{project.id}/supplier-requests").get_data(as_text=True)
    assert f'data-po-delivered="{local_today().isoformat()}"' in office and "Pumped at 7:40" in office
    assert f'data-cancel-order="{order.id}"' not in office
    assert "Delivered" in client.get(f"/projects/{project.id}").get_data(as_text=True)
    with pytest.raises(H.SupplierHubError, match="cannot be cancelled"):
        H.cancel_order(delivered, user=None, reason="late")
    with pytest.raises(H.SupplierHubError, match="already marked delivered"):
        H.mark_order_delivered(delivered, side="CONTRACTOR", user=None)


def test_the_office_can_mark_delivered_but_only_a_confirmed_order(app, client):
    project, _tomlinson, _darcy, _user, order = _concrete_order(app, client)
    order.status = "PLACED"; db.session.commit()
    page = client.post(f"/projects/{project.id}/orders/{order.id}/delivered", data={}, follow_redirects=True)
    assert b"Only a confirmed order can be marked delivered" in page.data
    order = _order(order.id); order.status = "CONFIRMED"; db.session.commit()
    client.post(f"/projects/{project.id}/orders/{order.id}/delivered", data={"note": "Signed by Ben"})
    order = _order(order.id)
    assert order.status == "DELIVERED" and H.order_closure(order)["side"] == "CONTRACTOR"


# ------------------------------------------------------------------ migration v5c1a7e3d9b2 (V1 release 5; the
# purchase-order DELIVERED status is its first step; tests/test_accounting_quickbooks.py checks the new tables)

ROOT = Path(__file__).resolve().parents[1]
REVISION, PRIOR = "v5c1a7e3d9b2", "pd1a2b3c4d5e"
NEW_TABLES = {"proposal_declines", "people_access_events", "organization_onboarding_steps", "customer_invoices",
              "accounting_export_records", "accounting_events"}


def _config(path) -> Config:
    cfg = Config(str(ROOT / "migrations" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    return cfg


def _rows(engine):
    out = {}
    with engine.connect() as conn:
        for table in sorted(set(sa.inspect(engine).get_table_names()) - {"alembic_version"}):
            out[table] = sorted(tuple(map(str, row)) for row in conn.execute(sa.text(f'SELECT * FROM "{table}"')))
    return out


_SEED = (
    "INSERT INTO organizations (id, legal_name, display_name, primary_address, default_region, currency, tax_jurisdiction, "
    "is_active, created_at, updated_at) VALUES ('ORG-PO', 'Synthetic Ltd.', 'Synthetic', '1 Test Rd', 'Ontario', 'CAD', "
    "'Ontario (HST 13%)', 1, '2026-10-21', '2026-10-21')",
    "INSERT INTO clients (id, organization_id, name, created_at) VALUES (1, 'ORG-PO', 'Synthetic client', '2026-10-21')",
    "INSERT INTO projects (id, organization_id, name, status, client_id, created_at, operating_state, "
    "operating_state_changed_at, drawing_requirement) VALUES (1, 'ORG-PO', 'Synthetic job', 'Contracted', 1, '2026-10-21', "
    "'ACTIVE', '2026-10-21', 'UNKNOWN')",
    "INSERT INTO suppliers (id, code, legal_name, status, demo_synthetic, created_at) VALUES (1, 'SYN', 'Synthetic supply', "
    "'ACTIVE', 1, '2026-10-21')",
    "INSERT INTO supplier_locations (id, supplier_id, code, display_name, status, demo_synthetic, created_at) "
    "VALUES (1, 1, 'MAIN', 'Main', 'ACTIVE', 1, '2026-10-21')",
    "INSERT INTO contractor_supplier_accounts (id, organization_id, supplier_id, supplier_location_id, status, "
    "demo_synthetic, created_at) VALUES (1, 'ORG-PO', 1, 1, 'ACTIVE', 1, '2026-10-21')",
    "INSERT INTO supplier_request_shares (id, organization_id, project_id, supplier_id, contractor_supplier_account_id, "
    "number, request_kind, source_kind, source_ref, shared_json, status, sent_by_name, sent_at) VALUES "
    "(1, 'ORG-PO', 1, 1, 1, 'SR-1', 'CONCRETE', 'CONCRETE_REQUEST', '1', '{}', 'RETURNED', 'x', '2026-10-21'), "
    "(2, 'ORG-PO', 1, 1, 1, 'SR-2', 'CONCRETE', 'CONCRETE_REQUEST', '2', '{}', 'RETURNED', 'x', '2026-10-21')",
    "INSERT INTO supplier_purchase_orders (id, organization_id, project_id, share_id, supplier_id, number, quote_ref, "
    "lines_json, total, delivery_address, status, placed_by_name, placed_at) VALUES "
    "(1, 'ORG-PO', 1, 1, 1, 'PO-1', 'Q1', '[]', 945.00, '1 Test Rd', 'CONFIRMED', 'x', '2026-10-21'), "
    "(2, 'ORG-PO', 1, 2, 1, 'PO-2', 'Q2', '[]', 100.00, '1 Test Rd', 'CANCELLED', 'x', '2026-10-21')",
)


def _seed(engine):
    with engine.begin() as conn:
        for statement in _SEED:
            conn.execute(sa.text(statement))


def test_the_revision_follows_pro_desk():
    script = ScriptDirectory.from_config(_config(":memory:"))
    assert script.get_revision(REVISION).down_revision == PRIOR
    assert script.get_revision("t6a2c8e4f1b3").down_revision == REVISION  # v1rel6 (Training Centre) follows


def test_upgrade_only_widens_the_status_check_and_keeps_every_row(tmp_path):
    db_path = tmp_path / "po.db"
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"})
    with application.app_context():
        cfg = _config(db_path)
        command.upgrade(cfg, PRIOR)
        _seed(db.engine)
        before_rows = _rows(db.engine)
        before_columns = {t: [c["name"] for c in sa.inspect(db.engine).get_columns(t)]
                          for t in sa.inspect(db.engine).get_table_names()}
        with pytest.raises(sa.exc.IntegrityError):
            with db.engine.begin() as conn:
                conn.execute(sa.text("UPDATE supplier_purchase_orders SET status = 'DELIVERED' WHERE id = 1"))
        command.upgrade(cfg, REVISION)
        rows = _rows(db.engine)
        assert all(rows.pop(t) == [] for t in NEW_TABLES)
        assert rows == before_rows  # every existing row unchanged
        inspector = sa.inspect(db.engine)
        assert {t: [c["name"] for c in inspector.get_columns(t)] for t in inspector.get_table_names()
                if t not in NEW_TABLES} == before_columns
        with db.engine.begin() as conn:
            assert conn.execute(sa.text("PRAGMA integrity_check")).scalar() == "ok"
            conn.execute(sa.text("UPDATE supplier_purchase_orders SET status = 'DELIVERED' WHERE id = 1"))
        with pytest.raises(sa.exc.IntegrityError):
            with db.engine.begin() as conn:
                conn.execute(sa.text("UPDATE supplier_purchase_orders SET status = 'SHIPPED' WHERE id = 1"))
        with pytest.raises(RuntimeError, match="Downgrade refused"):
            command.downgrade(cfg, PRIOR)
        with db.engine.begin() as conn:
            conn.execute(sa.text("UPDATE supplier_purchase_orders SET status = 'CONFIRMED' WHERE id = 1"))
        command.downgrade(cfg, PRIOR)
        assert _rows(db.engine) == before_rows

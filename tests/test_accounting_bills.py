"""Bills and purchase orders for QuickBooks from a confirmed supplier order (Joel, 21 Oct 2026). Synthetic."""

from __future__ import annotations

import csv
import io
from decimal import Decimal

import pytest

from app import db
from app.services import accounting as svc
from app.services.organizations import DEFAULT_ORGANIZATION_ID as ORG
from tests.test_supplier_hub import _concrete_order, _fresh_login_per_request, app, client  # noqa: F401


def _rows(content):
    return list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))


def test_confirmed_order_becomes_a_draft_bill_once(app, client):
    project, _tomlinson, _darcy, user, order = _concrete_order(app, client)
    assert order.status == "CONFIRMED" and Decimal(order.total) > 0
    _, content, outcome = svc.export(ORG, "bills", user=user)
    bill = _rows(content)[0]
    assert outcome == {"new": 1, "again": 0}
    assert bill["BillNo"] == order.number and bill["LineAmount"] == str(Decimal(order.total).quantize(Decimal("0.01")))
    assert bill["LineTaxCode"] == "HST ON" and project.name in bill["Memo"]
    with pytest.raises(svc.AccountingError, match="Nothing new"):
        svc.export(ORG, "bills", user=user)
    _, vendors, _ = svc.export(ORG, "suppliers", user=user)
    assert "Tomlinson concrete (synthetic)" in [r["Name"] for r in _rows(vendors)]
    _, pos, _ = svc.export(ORG, "purchase_orders", user=user)
    assert _rows(pos)[0]["PO number"] == order.number and _rows(pos)[0]["Status"] == "Confirmed"
    order.status = "CANCELLED"
    db.session.commit()
    assert svc.preview(ORG, "bills", include_exported=True)["rows"] == []  # a cancelled order is never a bill

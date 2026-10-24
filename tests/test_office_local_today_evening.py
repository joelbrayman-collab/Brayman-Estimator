"""Evening dates use the office's day, not the server's UTC day (Joel, 24 Oct 2026). Synthetic data only.

The server runs UTC. At 21:30 in Toronto on 22 Oct it is already 01:30 on 23 Oct in UTC, so "today"
must come from :func:`app.services.local_time.local_today` and a stored (naive UTC) placed-at time
must be read as its office-local date. Each test runs with the process clock zone set to UTC and to
America/Toronto: the answer must not depend on the machine.
"""

from __future__ import annotations

import time
from datetime import date, datetime

import pytest

from app import db
from app.models.supplier_portal import SupplierPurchaseOrder
from app.services import local_time
from app.services import supplier_hub as H
from tests.test_supplier_hub import _concrete_order, _fresh_login_per_request, app, client  # noqa: F401

FROZEN_UTC = datetime(2026, 10, 23, 1, 30)  # = 21:30 EDT on Thursday 22 October 2026
OFFICE_DAY = date(2026, 10, 22)


@pytest.fixture(params=["UTC", "America/Toronto"])
def evening(request, monkeypatch):
    monkeypatch.setenv("TZ", request.param)
    time.tzset()
    monkeypatch.setattr(local_time, "utc_now", lambda: FROZEN_UTC)
    yield request.param
    monkeypatch.undo()
    time.tzset()


def _placed_just_now(order_id) -> SupplierPurchaseOrder:
    order = db.session.get(SupplierPurchaseOrder, order_id)
    order.placed_at = datetime(2026, 10, 23, 1, 20)  # 21:20 EDT on 22 Oct, ten minutes ago
    db.session.commit()
    return order


def test_the_clock_helper_gives_the_office_day_in_the_evening(app, evening):
    with app.app_context():
        assert local_time.local_today() == OFFICE_DAY
        assert local_time.local_now().hour == 21
        assert local_time.local_date(FROZEN_UTC) == OFFICE_DAY


def test_marking_delivered_right_after_placing_defaults_to_the_office_day(app, client, evening):
    project, tomlinson, darcy, _user, order = _concrete_order(app, client)
    order = _placed_just_now(order.id)
    page = darcy.get(f"/supplier/{tomlinson.supplier_id}/requests/{order.share_id}").get_data(as_text=True)
    assert f'name="delivered_on" value="{OFFICE_DAY.isoformat()}" max="{OFFICE_DAY.isoformat()}"' in page
    darcy.post(f"/supplier/{tomlinson.supplier_id}/orders/{order.id}/delivered", data={"delivered_on": ""})
    delivered = db.session.get(SupplierPurchaseOrder, order.id)
    assert delivered.status == "DELIVERED"
    assert H.order_closure(delivered)["day"] == OFFICE_DAY  # not 23 Oct, the UTC date


def test_marking_delivered_today_by_date_works_right_after_placing(app, client, evening):
    _project, _tomlinson, _darcy, _user, order = _concrete_order(app, client)
    order = _placed_just_now(order.id)
    H.mark_order_delivered(order, side="CONTRACTOR", user=None, delivered_on=OFFICE_DAY.isoformat())
    assert db.session.get(SupplierPurchaseOrder, order.id).status == "DELIVERED"


def test_a_genuinely_future_delivery_date_is_refused(app, client, evening):
    _project, _tomlinson, _darcy, _user, order = _concrete_order(app, client)
    order = _placed_just_now(order.id)
    with pytest.raises(H.SupplierHubError, match="cannot be in the future"):
        H.mark_order_delivered(order, side="CONTRACTOR", user=None, delivered_on="2026-10-23")
    assert db.session.get(SupplierPurchaseOrder, order.id).status == "CONFIRMED"


def test_a_delivery_before_the_office_day_the_order_was_placed_is_refused(app, client, evening):
    _project, _tomlinson, _darcy, _user, order = _concrete_order(app, client)
    order = _placed_just_now(order.id)
    with pytest.raises(H.SupplierHubError, match="before the order was placed"):
        H.mark_order_delivered(order, side="CONTRACTOR", user=None, delivered_on="2026-10-21")
    assert db.session.get(SupplierPurchaseOrder, order.id).status == "CONFIRMED"


def test_a_time_entry_for_the_office_day_is_not_in_the_future(app, evening):
    from app.services.time_entry import TimeEntryError, parse_work_date

    with app.app_context():
        assert parse_work_date(OFFICE_DAY.isoformat()) == OFFICE_DAY
        with pytest.raises(TimeEntryError):
            parse_work_date("2026-10-23")

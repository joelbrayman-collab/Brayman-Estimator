"""EST-08: an approved contractor cost reaches an estimate line from the office.

The estimator sees the current approved cost per material, uses it on the
existing line or adds one line with a quantity they confirm, and the version's
costing snapshot cites the approval. Nothing is added or approved without the
estimator. The approver recorded is the signed-in user, not a typed name.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app import db
from app.models import EstimateLineItem
from app.models.estimate_costing import SOURCE_APPROVED_CONTRACTOR_COST, EstimateCostingSnapshot
from app.services import approved_cost_estimate as approved
from app.services.material_catalogue import get_canonical_material_by_code
from app.services.organizations import DEFAULT_ORGANIZATION_ID
from tests.auth_fixtures import DEFAULT_OFFICE_DISPLAY_NAME, ensure_office_user, login_office_user
from tests.scope_delivery_support import ensure_confirmed_scope_routing
from tests.test_approved_contractor_cost_snapshot import (  # noqa: F401  (fixture)
    ACTOR,
    _approval,
    _estimate,
    _evidence,
    _line,
    _map,
    _supplier,
    app,
)

OPEN_FROM = datetime.utcnow() - timedelta(days=5)


def _approved_material(code="CAL-LUM-2X8-12", amount="8.00", supplier="PROVE-A"):
    material = get_canonical_material_by_code(code)
    _s, account, product = _supplier(supplier, f"{supplier}-{code}")
    _map(material, product)
    _evidence(product, amount, "CONTRACTOR_CONFIRMED_PRICE", account.id, OPEN_FROM, None)
    return material, account, _approval(material, account, datetime.utcnow())


def test_review_lists_the_current_approval_and_offers_nothing_without_a_takeoff(app):
    material, _account, approval = _approved_material()
    estimate = _estimate("EST-APP-1")
    rows = approved.review(estimate.current_version, DEFAULT_ORGANIZATION_ID)
    assert [r["approval"].id for r in rows] == [approval.id]
    assert rows[0]["material"].id == material.id
    assert rows[0]["lines"] == [] and rows[0]["offer"] is None and rows[0]["offer_prefill"] is None


def test_a_newer_approval_supersedes_an_older_one_for_the_same_material(app):
    material, account, first = _approved_material()
    second = _approval(material, account, datetime.utcnow())
    current = approved.current_approvals(DEFAULT_ORGANIZATION_ID)
    assert [a.id for a in current] == [second.id]
    estimate = _estimate("EST-APP-2")
    with pytest.raises(approved.ApprovedCostError, match="not the current approved cost"):
        approved.add_line(estimate.current_version, organization_id=DEFAULT_ORGANIZATION_ID, approval_id=first.id,
                          quantity="3", new_section_name="Materials", actor=ACTOR)


def test_use_on_an_existing_line_freezes_the_approved_cost(app):
    material, _account, approval = _approved_material(amount="9.50")
    estimate = _estimate("EST-APP-3")
    version, line = _line(estimate, material, "MAT-APP-3")
    snapshot = approved.use_on_line(version, organization_id=DEFAULT_ORGANIZATION_ID, approval_id=approval.id,
                                    line_id=line.id, actor=ACTOR)
    frozen = snapshot.lines[0]
    assert frozen.source_kind == SOURCE_APPROVED_CONTRACTOR_COST
    assert frozen.contractor_cost_approval_id == approval.id
    assert frozen.unit_cost == Decimal("9.5000")


def test_add_creates_one_line_then_freezes_once_scope_delivery_is_confirmed(app):
    material, _account, approval = _approved_material(amount="8.00")
    estimate = _estimate("EST-APP-4")
    version = estimate.current_version
    lines_before = EstimateLineItem.query.count()
    line, snapshot, waiting = approved.add_line(version, organization_id=DEFAULT_ORGANIZATION_ID,
                                                approval_id=approval.id, quantity="12", new_section_name="Materials",
                                                actor=ACTOR)
    assert EstimateLineItem.query.count() == lines_before + 1
    assert line.quantity == Decimal("12") and line.unit == approval.unit
    if snapshot is None:  # costing waits for the estimator's scope-delivery confirmation
        assert waiting
        ensure_confirmed_scope_routing(version, actor=ACTOR)
        db.session.commit()
        snapshot = approved.use_on_line(version, organization_id=DEFAULT_ORGANIZATION_ID, approval_id=approval.id,
                                        line_id=line.id, actor=ACTOR)
    frozen = [row for row in snapshot.lines if row.estimate_line_item_id == line.id][0]
    assert frozen.contractor_cost_approval_id == approval.id and frozen.unit_cost == Decimal("8.0000")
    # A second line for the same material is refused; the estimator uses the existing line.
    with pytest.raises(approved.ApprovedCostError, match="already has a line"):
        approved.add_line(version, organization_id=DEFAULT_ORGANIZATION_ID, approval_id=approval.id,
                          quantity="1", new_section_name="Materials", actor=ACTOR)
    assert EstimateLineItem.query.count() == lines_before + 1


@pytest.mark.parametrize("quantity", ["", "0", "-2", "abc", "NaN", "Infinity"])
def test_a_missing_or_impossible_quantity_is_refused_and_nothing_is_added(app, quantity):
    _material, _account, approval = _approved_material()
    estimate = _estimate("EST-APP-5")
    lines_before = EstimateLineItem.query.count()
    with pytest.raises(approved.ApprovedCostError):
        approved.add_line(estimate.current_version, organization_id=DEFAULT_ORGANIZATION_ID, approval_id=approval.id,
                          quantity=quantity, new_section_name="Materials", actor=ACTOR)
    assert EstimateLineItem.query.count() == lines_before


def test_another_organizations_approval_is_not_usable(app):
    _material, _account, approval = _approved_material()
    estimate = _estimate("EST-APP-6")
    with pytest.raises(approved.ApprovedCostError, match="not found"):
        approved.add_line(estimate.current_version, organization_id="ORG-002", approval_id=approval.id,
                          quantity="1", new_section_name="Materials", actor=ACTOR)
    assert approved.current_approvals("ORG-002") == []


def test_a_unit_mismatch_is_refused(app):
    material, _account, approval = _approved_material()
    estimate = _estimate("EST-APP-7")
    version, line = _line(estimate, material, "MAT-APP-7", unit="LF")
    with pytest.raises(approved.ApprovedCostError, match="unit"):
        approved.use_on_line(version, organization_id=DEFAULT_ORGANIZATION_ID, approval_id=approval.id,
                             line_id=line.id, actor=ACTOR)


def test_the_takeoff_offers_a_summed_final_quantity_only(app, monkeypatch):
    material, _account, approval = _approved_material()
    estimate = _estimate("EST-APP-8")
    lines = [
        {"canonical_material_code": material.code, "purchasing_quantity": 10, "purchasing_unit": approval.unit, "complete": True},
        {"canonical_material_code": material.code, "purchasing_quantity": 8, "purchasing_unit": approval.unit, "complete": True},
    ]
    monkeypatch.setattr(approved.storage, "list_requests",
                        lambda org, pid: [{"request_id": "DTR-1", "issued_at": "2026-10-14T10:00:00", "lines": lines}])
    row = approved.review(estimate.current_version, DEFAULT_ORGANIZATION_ID)[0]
    assert row["offer_prefill"] == Decimal("18")
    lines[1]["complete"] = False
    row = approved.review(estimate.current_version, DEFAULT_ORGANIZATION_ID)[0]
    assert row["offer"]["quantity"] == Decimal("18") and row["offer_prefill"] is None


def test_the_office_page_adds_the_line_and_records_the_signed_in_user(app):
    _material, _account, approval = _approved_material()
    estimate = _estimate("EST-APP-9")
    version = estimate.current_version
    ensure_office_user()
    db.session.commit()
    client = app.test_client()
    app.config["WTF_CSRF_ENABLED"] = False
    login_office_user(client)
    page = client.get(f"/estimates/{estimate.id}/versions/{version.id}/approved-costs")
    assert page.status_code == 200 and b"Use approved costs on this estimate" in page.data
    response = client.post(
        f"/estimates/{estimate.id}/versions/{version.id}/approved-costs/add",
        data={"approval_id": approval.id, "quantity": "4", "new_section_name": "Materials",
              "actor_display_name": "Someone Else", "approved_by": "Someone Else"},
        follow_redirects=True,
    )
    assert response.status_code == 200 and b"Added 4" in response.data
    line = EstimateLineItem.query.filter(EstimateLineItem.notes.like(f"Approved contractor cost #{approval.id}%")).one()
    assert DEFAULT_OFFICE_DISPLAY_NAME in line.notes and "Someone Else" not in line.notes
    ensure_confirmed_scope_routing(version, actor=ACTOR)
    db.session.commit()
    client.post(f"/estimates/{estimate.id}/versions/{version.id}/approved-costs/use",
                data={"approval_id": approval.id, "line_id": line.id, "approved_by": "Someone Else"})
    snapshot = EstimateCostingSnapshot.query.filter_by(estimate_version_id=version.id).order_by(EstimateCostingSnapshot.id.desc()).first()
    assert snapshot is not None and snapshot.actor_display_name == DEFAULT_OFFICE_DISPLAY_NAME

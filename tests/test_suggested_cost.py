"""A returned quote only SUGGESTS a cost; a person confirms it, and can undo it."""

from datetime import datetime
from decimal import Decimal

from app import db
from app.models.estimate_scope_delivery import LABOUR_SUBCONTRACT
from app.services.estimate_builder import add_manual_line, create_section
from app.services.estimate_scope_delivery import MATERIAL_SUBCONTRACTOR_SUPPLIED, save_scope_delivery
from app.services.material_catalogue import get_canonical_material_by_code
from app.services.subcontract_quote import receive_quote, select_quote
from app.services.suggested_cost import (
    SuggestedCostError, apply_labour_suggestion, labour_suggestion, material_suggestion,
    revert_labour_suggestion,
)
from tests.test_scope_delivery_fg031 import _estimate, app, client  # noqa: F401
from tests import test_approved_contractor_cost_snapshot as snap


def _labour_line(number):
    estimate = _estimate(number)
    version = estimate.current_version
    section = create_section(version, name="Direct")
    line = add_manual_line(section, line_type="Custom", description="Framing labour", quantity=4, unit="ls", unit_cost=100)
    save_scope_delivery(line, material_procurement=MATERIAL_SUBCONTRACTOR_SUPPLIED,
                        labour_delivery=LABOUR_SUBCONTRACT, actor="Joel Brayman")
    return estimate, version, line


def test_labour_quote_suggests_then_a_person_confirms_and_can_undo(app, client):  # noqa: F811
    estimate, version, line = _labour_line("EST-SUGG-1")
    q = receive_quote(line, actor="Joel Brayman", subcontractor_code="FR1", subcontractor_legal_name="Framers",
                      quote_reference="Q-1", amount="2400.00", currency="CAD", quote_date="2026-10-20")
    assert labour_suggestion(line) is None  # received, not selected
    select_quote(q.id, actor="Joel Brayman")
    sug = labour_suggestion(line)
    assert sug["suggested_unit_cost"] == Decimal("600.0000") and sug["differs"] and not sug["applied"]
    assert Decimal(str(line.unit_cost)) == Decimal("100")  # selecting changed nothing

    url = f"/projects/{estimate.project_id}/scope-delivery?version_id={version.id}&estimate_id={estimate.id}"
    page = client.get(url).get_data(as_text=True)
    assert "data-suggested-cost" in page and "data-cost-differs" in page and "data-confirm-suggested-cost" in page

    post = {"version_id": version.id, "estimate_id": estimate.id, "kind": "labour", "actor_display_name": "Joel Brayman"}
    client.post(f"/projects/{estimate.project_id}/scope-delivery/lines/{line.id}/suggested-cost/apply", data=post)
    db.session.refresh(line)
    assert Decimal(str(line.unit_cost)) == Decimal("600.0000") and Decimal(str(line.extended_cost)) == Decimal("2400.00")
    assert line.costing_override_by == "Joel Brayman" and line.costing_override_at and "prior unit cost 100" in line.costing_override_reason
    assert labour_suggestion(line)["applied"]
    shown = client.get(url).get_data(as_text=True)
    assert "data-revert-suggested-cost" in shown and "data-cost-differs" not in shown

    client.post(f"/projects/{estimate.project_id}/scope-delivery/lines/{line.id}/suggested-cost/revert", data=post)
    db.session.refresh(line)
    assert Decimal(str(line.unit_cost)) == Decimal("100.0000") and line.costing_override_by is None


def test_labour_suggestion_refuses_ai_actor_and_a_locked_version(app):  # noqa: F811
    _estimate_row, version, line = _labour_line("EST-SUGG-2")
    q = receive_quote(line, actor="Joel Brayman", subcontractor_code="FR1", subcontractor_legal_name="Framers",
                      quote_reference="Q-1", amount="800", currency="CAD", quote_date="2026-10-20")
    select_quote(q.id, actor="Joel Brayman")
    try:
        apply_labour_suggestion(line.id, actor="AI", version=version)
        raise AssertionError("AI applied a cost")
    except SuggestedCostError:
        pass
    try:
        revert_labour_suggestion(line.id, actor="Joel Brayman", version=version)
        raise AssertionError("reverted nothing")
    except SuggestedCostError:
        pass
    version.is_locked = True
    try:
        apply_labour_suggestion(line.id, actor="Joel Brayman", version=version)
        raise AssertionError("locked version changed")
    except SuggestedCostError:
        pass


def test_material_suggestion_comes_from_the_approved_supplier_cost_and_is_confirmed_on_the_line(app, client):  # noqa: F811
    material = get_canonical_material_by_code("CAL-LUM-2X8-12")
    _s, account, product = snap._supplier("SUGG-A", "SUGG-A-2X8-12")
    snap._map(material, product)
    snap._evidence(product, "8.00", "CONTRACTOR_CONFIRMED_PRICE", account.id, snap.OPEN_FROM, None)
    estimate = snap._estimate("EST-SUGG-M")
    version, line = snap._line(estimate, material, "MAT-SUGG")
    assert material_suggestion(line) is None  # price returned but not approved
    snap._approval(material, account, datetime(2026, 10, 15))
    sug = material_suggestion(line)
    assert sug["suggested_unit_cost"] == Decimal("8.0000") and not sug["applied"]
    before = Decimal(str(line.unit_cost))
    assert before != Decimal("8")
    post = {"version_id": version.id, "estimate_id": estimate.id, "kind": "material", "actor_display_name": "Joel Brayman"}
    client.post(f"/projects/{estimate.project_id}/scope-delivery/lines/{line.id}/suggested-cost/apply", data=post)
    db.session.refresh(line)
    assert Decimal(str(line.unit_cost)) == Decimal("8.0000") and material_suggestion(line)["applied"]

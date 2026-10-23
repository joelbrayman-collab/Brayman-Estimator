"""Suggested cost on an estimate line from a returned quote. A person confirms; nothing changes before.

Labour: the selected subcontract quote (evidence only) suggests a unit cost of quote amount / line
quantity. Confirming sets the line's working unit cost and records who, when and the prior unit cost
in the line's own override provenance. Reverting restores the prior unit cost. No table is added.

Materials: the latest APPROVED contractor cost for the line's canonical material suggests the unit
cost. Confirming uses the existing consume_approved_contractor_cost (approval, unit and currency
checks and the costing freeze are unchanged).
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from app import db
from app.models.contractor_cost_approval import (
    CONTRACTOR_COST_APPROVAL_APPROVED,
    ContractorCostApproval,
)
from app.models.estimate import EstimateLineItem
from app.services.estimate_builder import apply_line_item_calculations
from app.services.estimate_costing import (
    EstimateCostingError,
    assert_human_costing_actor,
    consume_approved_contractor_cost,
    version_is_costing_editable,
)
from app.services.subcontract_quote import selected_quote_for_line

SOURCE_LABOUR_QUOTE = "SUBCONTRACT_QUOTE_CONFIRMED"
_MARK = "Subcontract quote applied"
_PRIOR = re.compile(r"prior unit cost ([-0-9.]+)")


class SuggestedCostError(ValueError):
    pass


def _q4(value):
    return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def labour_suggestion(line):
    """The suggestion for a subcontract line, or None when no quote is selected."""
    quote = selected_quote_for_line(line)
    if quote is None or not line.quantity or Decimal(str(line.quantity)) <= 0:
        return None
    suggested = _q4(Decimal(str(quote.amount)) / Decimal(str(line.quantity)))
    applied = bool(line.costing_override_reason and line.costing_override_reason.startswith(_MARK))
    return {
        "kind": "labour",
        "quote_id": quote.id,
        "quote_amount": quote.amount,
        "currency": quote.currency,
        "suggested_unit_cost": suggested,
        "current_unit_cost": _q4(line.unit_cost),
        "applied": applied,
        "differs": _q4(line.unit_cost) != suggested,
        "applied_by": line.costing_override_by if applied else None,
        "applied_at": line.costing_override_at if applied else None,
    }


def apply_labour_suggestion(line_id, *, actor, version, commit=True):
    actor_name = _human(actor)
    line = _line(line_id, version)
    suggestion = labour_suggestion(line)
    if suggestion is None:
        raise SuggestedCostError("Select a quote on this line first.")
    if suggestion["applied"]:
        raise SuggestedCostError("This quote is already applied to the line.")
    quote = selected_quote_for_line(line)
    prior = _q4(line.unit_cost)
    line.unit_cost = suggestion["suggested_unit_cost"]
    apply_line_item_calculations(line)
    line.costing_override_reason = "{0}: {1} {2} from quote {3}; prior unit cost {4}".format(
        _MARK, quote.amount, quote.currency, quote.quote_reference, prior
    )
    line.costing_override_by = actor_name
    line.costing_override_at = datetime.utcnow()
    db.session.flush()
    if commit:
        db.session.commit()
    return line


def revert_labour_suggestion(line_id, *, actor, version, commit=True):
    actor_name = _human(actor)
    line = _line(line_id, version)
    reason = line.costing_override_reason or ""
    match = _PRIOR.search(reason) if reason.startswith(_MARK) else None
    if match is None:
        raise SuggestedCostError("No applied quote cost to revert on this line.")
    line.unit_cost = Decimal(match.group(1))
    apply_line_item_calculations(line)
    line.costing_override_reason = None
    line.costing_override_by = None
    line.costing_override_at = None
    db.session.flush()
    if commit:
        db.session.commit()
    return line


def material_suggestion(line):
    if (line.line_type or "") != "Cost Item" or line.cost_item is None or line.cost_item.canonical_material_id is None:
        return None
    approval = (
        ContractorCostApproval.query.filter_by(
            organization_id=line.cost_item.organization_id,
            canonical_material_id=line.cost_item.canonical_material_id,
            status=CONTRACTOR_COST_APPROVAL_APPROVED,
        )
        .order_by(ContractorCostApproval.id.desc())
        .first()
    )
    if approval is None or (approval.unit or "").strip().casefold() != (line.unit or "").strip().casefold():
        return None
    return {
        "kind": "material",
        "approval_id": approval.id,
        "suggested_unit_cost": _q4(approval.resolved_amount),
        "current_unit_cost": _q4(line.unit_cost),
        "applied": line.contractor_cost_approval_id == approval.id,
        "differs": _q4(line.unit_cost) != _q4(approval.resolved_amount),
    }


def apply_material_suggestion(line_id, *, actor, version, commit=True):
    line = _line(line_id, version)
    suggestion = material_suggestion(line)
    if suggestion is None:
        raise SuggestedCostError("There is no approved supplier cost for this line.")
    try:
        consume_approved_contractor_cost(
            version,
            estimate_line_item_id=line.id,
            contractor_cost_approval_id=suggestion["approval_id"],
            actor=actor,
            commit=commit,
        )
    except EstimateCostingError as exc:
        raise SuggestedCostError(str(exc)) from exc
    return line


def _human(actor):
    try:
        return assert_human_costing_actor(actor)
    except Exception as exc:
        raise SuggestedCostError(str(exc)) from exc


def _line(line_id, version):
    if not version_is_costing_editable(version):
        raise SuggestedCostError("This estimate version can no longer be changed.")
    for section in version.sections:
        for item in section.line_items:
            if item.id == line_id:
                return item
    raise SuggestedCostError("The estimate line is not on this estimate version.")

"""Contractor-entered labour hours per estimate item (Joel's decision 2, 14 Oct 2026).

The estimator types the labour hours for an item. The rate is the saved company
direct labour cost rate (``resolve_direct_labour_cost_rate``: the active approved
standard), or an authorized project override, which needs a reason. Nothing is
hard-coded here.

Each item's labour is one ordinary Custom line in the item's section, coded
``LAB-<item id>``: hours × rate, unit ``hr``, with the rate's source in its notes.
Because it is an ordinary line it enters costing approval and the existing gross
margin pricing exactly like every other cost. Changing hours changes the working
costing, so costing must be approved again, as for any edit.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from app.services.estimate_builder import add_manual_line, delete_line_item, update_line_item
from app.services.estimate_costing import iter_version_line_items
from app.services.estimates import EstimateServiceError, ensure_version_editable
from app.services.labour_engine import LabourEngineError, resolve_direct_labour_cost_rate

LABOUR_CODE_PREFIX = "LAB-"
LABOUR_UNIT = "hr"


class LabourHoursError(ValueError):
    pass


def _labour_code(item) -> str:
    return f"{LABOUR_CODE_PREFIX}{item.id}"


def is_labour_line(line) -> bool:
    return (line.code or "").startswith(LABOUR_CODE_PREFIX) and (line.unit or "") == LABOUR_UNIT


def resolve_rate(organization_id: str, *, override_rate="", override_reason="", persist_audit=False):
    """The rate used for labour hours, with where it came from."""
    try:
        result = resolve_direct_labour_cost_rate(
            organization_id=organization_id,
            override_rate=(override_rate or "").strip() or None,
            override_reason=override_reason,
            persist_audit=persist_audit,
        )
    except LabourEngineError as exc:
        raise LabourHoursError(str(exc)) from exc
    if result.rate_per_man_hour is None or result.requires_review:
        raise LabourHoursError(
            "No saved company labour rate is approved. Set it under How we price → labour, or enter a project rate with a reason."
        )
    if result.source_record_type == "project_override":
        source = f"Project rate {result.rate_per_man_hour} per hour — {result.override_reason}"
    else:
        source = (f"Company labour rate {result.rate_per_man_hour} per hour "
                  f"(standard {result.source_record_id}, version {result.standard_version})")
    return result, source


def rows(version) -> List[dict]:
    lines = list(iter_version_line_items(version))
    labour = {line.code: line for line in lines if is_labour_line(line)}
    out = []
    for item in lines:
        if is_labour_line(item):
            continue
        existing = labour.get(_labour_code(item))
        out.append({"item": item, "labour_line": existing,
                    "hours": None if existing is None else existing.quantity})
    return out


def _hours(raw) -> Optional[Decimal]:
    text = ("" if raw is None else str(raw)).strip()
    if text == "":
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise LabourHoursError(f"Labour hours must be a number (you entered “{text}”).") from None
    if not value.is_finite():
        raise LabourHoursError(f"Labour hours must be a number (you entered “{text}”).")
    if value < 0:
        raise LabourHoursError("Labour hours cannot be negative.")
    return value


def save_hours(version, *, organization_id: str, hours_by_item: Dict[int, str], actor: str,
               override_rate="", override_reason="") -> dict:
    """Create, update or remove each item's labour line. Blank leaves an item alone; 0 removes its labour."""
    try:
        ensure_version_editable(version)
    except EstimateServiceError as exc:
        raise LabourHoursError(str(exc)) from exc
    parsed = {int(item_id): _hours(raw) for item_id, raw in hours_by_item.items()}
    if not any(value is not None for value in parsed.values()):
        raise LabourHoursError("Enter labour hours for at least one item.")
    result, source = resolve_rate(organization_id, override_rate=override_rate,
                                  override_reason=override_reason, persist_audit=True)
    rate = result.rate_per_man_hour
    by_id = {row["item"].id: row for row in rows(version)}
    added = updated = removed = 0
    try:
        for item_id, hours in parsed.items():
            if hours is None:
                continue
            row = by_id.get(item_id)
            if row is None:
                raise LabourHoursError("That item is not on this estimate version.")
            item, existing = row["item"], row["labour_line"]
            notes = f"{source}. Hours entered by {actor}."
            if hours == 0:
                if existing is not None:
                    delete_line_item(existing)
                    removed += 1
                continue
            if existing is None:
                add_manual_line(item.section, line_type="Custom", description=f"Labour — {item.description}"[:255],
                                quantity=hours, unit=LABOUR_UNIT, unit_cost=rate, code=_labour_code(item), notes=notes)
                added += 1
            else:
                update_line_item(existing, quantity=hours, unit_cost=rate, notes=notes)
                updated += 1
    except EstimateServiceError as exc:
        raise LabourHoursError(str(exc)) from exc
    return {"added": added, "updated": updated, "removed": removed, "rate": rate, "source": source}

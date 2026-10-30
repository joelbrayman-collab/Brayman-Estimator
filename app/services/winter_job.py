"""Winter job (Joel, 30 Oct 2026; Paulusse REV3 is the acceptance reference).

A governed setting on the estimate version, not Paulusse logic:

- ``winter_job`` (default off), ``winter_time_increase_percent`` (default 20), ``propane_per_crew_day`` (default
  $35.00), ``hours_per_crew_day`` (8) and ``default_crew_size`` (for labour lines without their own crew size).
- Off: every labour line carries its entered hours and there is no winter heat.
- On: every labour line's hours = entered hours x (1 + increase), rounded to the cent of an hour. The entered hours
  stay on the line (``base_quantity``), so the lineage is entered hours -> winter adjustment -> adjusted hours.
- Crew days = sum over the labour lines in Brayman's price of adjusted hours / (crew x hours per crew day).
- Winter heat (propane) = crew days x propane per crew day: one calculated line in the shared general-conditions
  package (or its own section when no package is shared), so it enters costing, pricing, proposals and the
  approval like every other cost. Off: the line is not there.

The adjusted labour lines are the ordinary labour lines, so labour cost, the work plan, crew demand and the
preliminary schedule all use the adjusted hours. Nothing here is computed for a document only.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional

from app import db

PROPANE_CODE = "WINTER-PROPANE"
PROPANE_UNIT = "day"
PROPANE_DESCRIPTION = "Winter heat (propane)"
CENT = Decimal("0.01")
DAY_PLACES = Decimal("0.0001")


class WinterJobError(ValueError):
    pass


def _labour_lines(version):
    from app.services.estimate_labour_hours import is_labour_line

    return [line for section in version.sections for line in section.line_items if is_labour_line(line)]


def factor(version) -> Decimal:
    if not version.winter_job:
        return Decimal("1")
    return Decimal("1") + Decimal(str(version.winter_time_increase_percent or 0)) / Decimal("100")


def base_hours(line) -> Decimal:
    return Decimal(str(line.base_quantity if line.base_quantity is not None else line.quantity or 0))


def crew_of(line, version) -> int:
    return int(line.crew_size or version.default_crew_size or 1)


def line_crew_days(line, version) -> Decimal:
    hpd = Decimal(str(version.hours_per_crew_day or 8))
    return Decimal(str(line.quantity or 0)) / (Decimal(crew_of(line, version)) * hpd)


def crew_days(version) -> Decimal:
    """Crew days of the labour in Brayman's price (winter-adjusted hours when winter is on)."""
    from app.services.work_packages import line_participates

    return sum((line_crew_days(line, version) for line in _labour_lines(version) if line_participates(line)),
               Decimal("0"))


def _propane_line(version):
    for section in version.sections:
        for line in section.line_items:
            if (line.code or "") == PROPANE_CODE:
                return line
    return None


def _propane_section(version):
    from app.models import EstimateSection
    from app.services import work_packages as WP

    for section in version.sections:
        package = WP.package_of_section(section)
        if package is not None and WP.state_of(package, version).shared is not None \
                and WP.is_included(package, version):
            return section
    for section in version.sections:
        if section.name == "Winter conditions" and section.guided_stage_id is None:
            return section
    section = EstimateSection(estimate_version_id=version.id, name="Winter conditions",
                              sort_order=max([s.sort_order or 0 for s in version.sections] or [0]) + 10)
    db.session.add(section)
    db.session.flush()
    db.session.expire(version, ["sections"])
    return section


def _route_propane(line, actor):
    """Propane is bought by the contractor and needs no labour: the routing is recorded and confirmed by the person
    whose winter decision created the line."""
    from app.services.estimate_scope_delivery import (
        LABOUR_NO_LABOUR,
        MATERIAL_CONTRACTOR_PURCHASED,
        SUGGESTION_RULE,
        _new_routing_row,
        confirm_scope_delivery,
        get_scope_delivery_for_line,
    )

    if not actor or get_scope_delivery_for_line(line) is not None:
        return
    _new_routing_row(line, actor=actor, material=MATERIAL_CONTRACTOR_PURCHASED, labour=LABOUR_NO_LABOUR,
                     suggestion=SUGGESTION_RULE)
    db.session.flush()
    confirm_scope_delivery(line, actor=actor, commit=False)


def apply(version, *, actor: str = "") -> dict:
    """Bring the labour lines and the winter heat line in line with the version's winter settings. The caller owns
    the costing and pricing refresh and the commit."""
    from app.services.estimate_builder import apply_line_item_calculations

    f = factor(version)
    changed = 0
    for line in _labour_lines(version):
        base = base_hours(line)
        target = (base * f).quantize(CENT, ROUND_HALF_UP) if version.winter_job else base
        line.base_quantity = base if version.winter_job else None
        if Decimal(str(line.quantity or 0)) != target:
            line.quantity = target
            apply_line_item_calculations(line)
            changed += 1
    db.session.flush()
    propane = _propane_line(version)
    days = crew_days(version).quantize(DAY_PLACES, ROUND_HALF_UP)
    if version.winter_job and days > 0:
        rate = Decimal(str(version.propane_per_crew_day or 0)).quantize(CENT)
        if propane is None:
            from app.models import EstimateLineItem

            section = _propane_section(version)
            propane = EstimateLineItem(estimate_section_id=section.id, line_type="Custom", code=PROPANE_CODE,
                                       description=PROPANE_DESCRIPTION, quantity=days, unit=PROPANE_UNIT,
                                       unit_cost=rate, waste_percent=Decimal("0"), markup_percent=Decimal("0"),
                                       costing_source_kind="MANUAL_CUSTOM",
                                       notes="Calculated: winter-adjusted crew days x propane per crew day.",
                                       sort_order=9999)
            section.line_items.append(propane)  # in the session's view of the version at once
            apply_line_item_calculations(propane)
            db.session.flush()
            _route_propane(propane, actor)
            changed += 1
        elif Decimal(str(propane.quantity)) != days or Decimal(str(propane.unit_cost)) != rate:
            propane.quantity, propane.unit_cost = days, rate
            apply_line_item_calculations(propane)
            changed += 1
    elif propane is not None:
        from app.services.estimate_scope_delivery import get_scope_delivery_for_line

        routing = get_scope_delivery_for_line(propane)
        if routing is not None:
            db.session.delete(routing)
        propane.section.line_items.remove(propane)
        db.session.delete(propane)  # a calculated line; winter off means there is no winter heat
        changed += 1
    db.session.flush()
    from app.services.estimate_builder import recalculate_version

    recalculate_version(version)
    return {"changed": changed, "crew_days": days}


def summary(version) -> dict:
    """What the winter setting did to this version (for the approval record and the page)."""
    propane = _propane_line(version)
    lines = _labour_lines(version)
    return {
        "winter_job": bool(version.winter_job),
        "winter_time_increase_percent": str(Decimal(str(version.winter_time_increase_percent)).quantize(CENT)),
        "propane_per_crew_day": str(Decimal(str(version.propane_per_crew_day)).quantize(CENT)),
        "hours_per_crew_day": str(Decimal(str(version.hours_per_crew_day)).quantize(CENT)),
        "base_labour_hours": str(sum((base_hours(l) for l in lines), Decimal("0")).quantize(CENT)),
        "adjusted_labour_hours": str(sum((Decimal(str(l.quantity or 0)) for l in lines), Decimal("0")).quantize(CENT)),
        "crew_days": str(crew_days(version).quantize(DAY_PLACES)),
        "winter_heat_cost": str(Decimal(str(propane.extended_cost)).quantize(CENT)) if propane is not None else "0.00",
    }


def _parse(value, label, *, places=CENT, minimum=Decimal("0"), maximum=None) -> Decimal:
    try:
        number = Decimal(str(value).replace(",", "").replace("$", "").replace("%", "").strip())
        if not number.is_finite():
            raise InvalidOperation
    except (InvalidOperation, AttributeError):
        raise WinterJobError(f"Enter the {label} as a number.")
    if number < minimum or (maximum is not None and number > maximum):
        raise WinterJobError(f"The {label} is out of range.")
    return number.quantize(places)


def set_winter_settings(version, *, actor: str, winter_job: Optional[bool] = None, increase_percent=None,
                        propane_per_crew_day=None, user_id=None) -> dict:
    """Change the version's winter settings and recalculate through the ordinary costing and pricing steps."""
    from app.services.estimate_costing import (
        EstimateCostingError,
        approve_all_costing,
        current_costing_snapshot,
        working_matches_costing_snapshot,
    )
    from app.services.estimates import EstimateServiceError, ensure_version_editable
    from app.services.pricing_engine import PricingEngineError, apply_resolved_pricing_to_version
    from app.services.pricing_engine import record_pricing_audit

    name = " ".join((actor or "").split())[:150]
    if not name or name.lower() in {"system", "ai", "automatic", "calibraytai"}:
        raise WinterJobError("A person must change the winter settings.")
    try:
        ensure_version_editable(version)
    except EstimateServiceError as exc:
        raise WinterJobError(f"{exc} Make a new version to change the winter settings.") from exc
    costing = current_costing_snapshot(version)
    costing_was_current = costing is not None and working_matches_costing_snapshot(version, costing)
    had_pricing = getattr(version, "pricing_snapshot", None) is not None
    before = (version.winter_job, version.winter_time_increase_percent, version.propane_per_crew_day)
    if winter_job is not None:
        version.winter_job = bool(winter_job)
    if increase_percent not in (None, ""):
        version.winter_time_increase_percent = _parse(increase_percent, "winter time increase",
                                                      maximum=Decimal("200"))
    if propane_per_crew_day not in (None, ""):
        version.propane_per_crew_day = _parse(propane_per_crew_day, "propane per crew day",
                                              maximum=Decimal("100000"))
    after = (version.winter_job, version.winter_time_increase_percent, version.propane_per_crew_day)
    if tuple(map(str, before)) == tuple(map(str, after)):
        return {"changed": False}
    result = apply(version, actor=name)
    record_pricing_audit("estimate_winter_settings", "EstimateVersion", version.id, actor=name,
                         detail=f"Winter job {'on' if version.winter_job else 'off'}; time increase "
                                f"{version.winter_time_increase_percent}%; propane ${version.propane_per_crew_day} per "
                                f"crew day; crew days {result['crew_days']}",
                         organization_id=version.estimate.organization_id)
    try:
        if costing_was_current:
            approve_all_costing(version, actor=name, user_id=user_id, commit=False)
        costing_now = current_costing_snapshot(version)
        if had_pricing and costing_now is not None and working_matches_costing_snapshot(version, costing_now):
            apply_resolved_pricing_to_version(version, actor=name)
    except (EstimateCostingError, PricingEngineError) as exc:
        db.session.rollback()
        raise WinterJobError(str(exc)) from exc
    db.session.commit()
    return {"changed": True, **summary(version)}

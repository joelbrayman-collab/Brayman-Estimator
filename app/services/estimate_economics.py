"""Project labour rate and target gross margin: the two values Brayman adjusts project by project (Joel, 30 Oct 2026).

Company Default -> Project Estimate Value -> project-specific override if changed.

* Company defaults are the existing governed settings, not a second copy of them: the labour rate is the company's
  active approved direct labour cost rate (Labour rates, ``labour_engine``); the target gross margin is the default
  ORG-APPROVED pricing policy's margin (How we price, ``pricing_engine``).
* Each estimate version carries its own ``labour_rate`` and ``target_gross_margin``, captured from those defaults
  when the estimate (or a new version) is created, so a later change to a company default never reprices it.
* The estimator changes either value on the estimate. A value different from the company default needs a reason
  (the existing project labour-rate override rule, used for the margin too); going back to the default does not.
  Every change is recorded (previous value, new value, who, when, which estimate, reason).
* One calculation: labour lines are hours x the project labour rate; the price is the pricing engine's
  true gross margin on the direct cost (``true_gross_margin_pre_tax``) and tax after it (``apply_tax_after_pre_tax``),
  rounded half-up to the cent once. ``economics`` returns the frozen pricing snapshot's figures when pricing is
  current, so the review, the internal breakdown, the customer estimate and the proposal all read one value.

Changing the labour rate changes labour cost, never hours; changing the margin changes the price, never costs.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from app import db

HUNDRED = Decimal("100")
CENT = Decimal("0.01")


class EstimateEconomicsError(ValueError):
    pass


# ---------------------------------------------------------------------------------------------- company defaults
def company_defaults(organization_id: str) -> dict:
    """The company's current default labour rate and target gross margin (None where none is approved)."""
    from app.models.pricing_engine import OrganizationPricingPolicy
    from app.services.labour_engine import _active_org_approved_dlcrs

    standard = _active_org_approved_dlcrs(organization_id, None)
    policy = (OrganizationPricingPolicy.query
              .filter_by(organization_id=organization_id, approval_status="ORG_APPROVED", is_default=True).first())
    margin = None
    if policy is not None and policy.method == "TRUE_GROSS_MARGIN" and policy.target_gross_margin is not None:
        margin = Decimal(str(policy.target_gross_margin))
    return {
        "labour_rate": Decimal(str(standard.rate_per_man_hour)).quantize(CENT) if standard is not None else None,
        "labour_standard": standard,
        "target_gross_margin": margin,
        "pricing_policy": policy,
        "tax_percent": Decimal(str(policy.tax_percent)) if policy is not None and policy.tax_percent is not None else None,
    }


def capture_defaults(version, organization_id: str, *, from_version=None) -> None:
    """Give a new version its project values: the previous version's (a revision keeps the project's values),
    otherwise the company defaults. Never overwrites a value the version already has."""
    defaults = None
    if version.labour_rate is None:
        if from_version is not None and from_version.labour_rate is not None:
            version.labour_rate, version.labour_rate_reason = from_version.labour_rate, from_version.labour_rate_reason
        else:
            defaults = company_defaults(organization_id)
            version.labour_rate = defaults["labour_rate"]
    if version.target_gross_margin is None:
        if from_version is not None and from_version.target_gross_margin is not None:
            version.target_gross_margin = from_version.target_gross_margin
            version.target_gross_margin_reason = from_version.target_gross_margin_reason
        else:
            defaults = defaults or company_defaults(organization_id)
            version.target_gross_margin = defaults["target_gross_margin"]


def _org(version) -> str:
    return version.estimate.project.organization_id


def project_values(version, organization_id: Optional[str] = None) -> dict:
    """The version's labour rate and margin, the company defaults, and whether each is a project override."""
    org_id = organization_id or _org(version)
    defaults = company_defaults(org_id)
    rate = Decimal(str(version.labour_rate)).quantize(CENT) if version.labour_rate is not None else defaults["labour_rate"]
    margin = (Decimal(str(version.target_gross_margin)) if version.target_gross_margin is not None
              else defaults["target_gross_margin"])
    return {
        "labour_rate": rate,
        "labour_rate_default": defaults["labour_rate"],
        "labour_rate_is_override": rate is not None and defaults["labour_rate"] is not None and rate != defaults["labour_rate"],
        "labour_rate_reason": version.labour_rate_reason,
        "labour_rate_captured": version.labour_rate is not None,
        "target_gross_margin": margin,
        "margin_percent": (margin * HUNDRED).quantize(CENT) if margin is not None else None,
        "target_gross_margin_default": defaults["target_gross_margin"],
        "margin_default_percent": (defaults["target_gross_margin"] * HUNDRED).quantize(CENT)
        if defaults["target_gross_margin"] is not None else None,
        "margin_is_override": margin is not None and defaults["target_gross_margin"] is not None
        and margin != defaults["target_gross_margin"],
        "margin_reason": version.target_gross_margin_reason,
        "defaults": defaults,
    }


# ---------------------------------------------------------------------------------------------- validation
def parse_labour_rate(raw) -> Decimal:
    text = ("" if raw is None else str(raw)).strip().replace("$", "").replace(",", "")
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise EstimateEconomicsError(f"Labour rate must be an amount of money per hour (you entered “{raw}”).") from None
    if not value.is_finite() or value <= 0:
        raise EstimateEconomicsError("Labour rate must be more than $0.00 an hour.")
    if value != value.quantize(CENT):
        raise EstimateEconomicsError("Labour rate is dollars and cents (two decimal places at most).")
    return value.quantize(CENT)


def parse_margin_percent(raw) -> Decimal:
    """A percentage (15 or 15.00 is 15 %), returned as the fraction the pricing engine uses (0.15)."""
    text = ("" if raw is None else str(raw)).strip().replace("%", "")
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise EstimateEconomicsError(f"Target gross margin must be a percentage (you entered “{raw}”).") from None
    if not value.is_finite() or value < 0 or value >= HUNDRED:
        raise EstimateEconomicsError("Target gross margin must be at least 0% and less than 100%.")
    if value != value.quantize(Decimal("0.0001")):
        raise EstimateEconomicsError("Target gross margin can have at most four decimal places.")
    return (value / HUNDRED).quantize(Decimal("0.000001"))


# ---------------------------------------------------------------------------------------------- labour lines
def labour_lines(version):
    from app.services.estimate_labour_hours import is_labour_line

    return [line for section in version.sections for line in section.line_items if is_labour_line(line)]


def rate_source(version, organization_id: Optional[str] = None) -> str:
    values = project_values(version, organization_id)
    rate = values["labour_rate"]
    if values["labour_rate_is_override"]:
        if values["labour_rate_reason"]:
            return f"Project labour rate {rate} per hour — {values['labour_rate_reason']}"
        return f"Project labour rate {rate} per hour (the company rate when this estimate was created)"
    standard = values["defaults"]["labour_standard"]
    if standard is not None:
        return (f"Company labour rate {Decimal(str(standard.rate_per_man_hour))} per hour "
                f"(standard {standard.id}, version {standard.version_number})")
    return f"Project labour rate {rate} per hour"


def _rerate_labour_lines(version, rate: Decimal, actor: str) -> int:
    from app.services.estimate_builder import update_line_item

    source = rate_source(version)
    changed = 0
    for line in labour_lines(version):
        if Decimal(str(line.unit_cost)) != rate:
            update_line_item(line, unit_cost=rate, notes=f"{source}. Rate changed by {actor}.")
            changed += 1
    return changed


# ---------------------------------------------------------------------------------------------- the change
def set_project_pricing(version, *, actor: str, labour_rate=None, margin_percent=None, reason: str = "",
                        organization_id: Optional[str] = None, user_id=None) -> dict:
    """Set the version's labour rate and/or target gross margin and recalculate the estimate.

    Labour lines are re-rated (hours unchanged). If the costing was approved and current before the change, the
    change is the only difference, so the estimator's change re-approves it; if pricing had been applied, it is
    applied again with the new values. Otherwise the review shows the recalculated working figures and the usual
    steps (approve the costing, apply pricing) follow.
    """
    from app.services.estimate_costing import (
        EstimateCostingError,
        approve_all_costing,
        current_costing_snapshot,
        working_matches_costing_snapshot,
    )
    from app.services.estimates import EstimateServiceError, ensure_version_editable
    from app.services.pricing_engine import (
        PricingEngineError,
        apply_resolved_pricing_to_version,
        assert_human_actor,
        record_pricing_audit,
    )

    org_id = organization_id or _org(version)
    try:
        ensure_version_editable(version)
    except EstimateServiceError as exc:
        raise EstimateEconomicsError(str(exc)) from exc
    try:
        name = assert_human_actor(actor, action="Change the project labour rate or margin")
    except PricingEngineError as exc:
        raise EstimateEconomicsError(str(exc)) from exc
    reason_text = (reason or "").strip()
    before = project_values(version, org_id)
    defaults = before["defaults"]
    new_rate = parse_labour_rate(labour_rate) if labour_rate not in (None, "") else None
    new_margin = parse_margin_percent(margin_percent) if margin_percent not in (None, "") else None
    rate_changed = new_rate is not None and new_rate != before["labour_rate"]
    margin_changed = new_margin is not None and new_margin != before["target_gross_margin"]
    if not rate_changed and not margin_changed:
        # Capture the current values on an older version that had none, so it stops following the company default.
        if version.labour_rate is None and before["labour_rate"] is not None:
            version.labour_rate = before["labour_rate"]
        if version.target_gross_margin is None and before["target_gross_margin"] is not None:
            version.target_gross_margin = before["target_gross_margin"]
        return {"changed": False, "rerated": 0, "reapproved": False, "repriced": False}
    needs_reason = ((rate_changed and new_rate != defaults["labour_rate"])
                    or (margin_changed and new_margin != defaults["target_gross_margin"]))
    if needs_reason and not reason_text:
        raise EstimateEconomicsError(
            "Give a reason for using a value different from the company default (it is kept with the estimate).")

    costing = current_costing_snapshot(version)
    costing_was_current = costing is not None and working_matches_costing_snapshot(version, costing)
    had_pricing = getattr(version, "pricing_snapshot", None) is not None

    rerated = 0
    if rate_changed:
        version.labour_rate = new_rate
        version.labour_rate_reason = reason_text if new_rate != defaults["labour_rate"] else None
        record_pricing_audit("estimate_labour_rate_change", "EstimateVersion", version.id, actor=name,
                             detail=f"Labour rate {before['labour_rate']} -> {new_rate} per hour"
                                    + (f"; reason: {version.labour_rate_reason}" if version.labour_rate_reason
                                       else "; company default"), organization_id=org_id)
        rerated = _rerate_labour_lines(version, new_rate, name)
    elif version.labour_rate is None and before["labour_rate"] is not None:
        version.labour_rate = before["labour_rate"]
    if margin_changed:
        version.target_gross_margin = new_margin
        version.target_gross_margin_reason = reason_text if new_margin != defaults["target_gross_margin"] else None
        old = before["margin_percent"]
        record_pricing_audit("estimate_target_margin_change", "EstimateVersion", version.id, actor=name,
                             detail=f"Target gross margin {old}% -> {(new_margin * HUNDRED).quantize(CENT)}%"
                                    + (f"; reason: {version.target_gross_margin_reason}"
                                       if version.target_gross_margin_reason else "; company default"),
                             organization_id=org_id)
    elif version.target_gross_margin is None and before["target_gross_margin"] is not None:
        version.target_gross_margin = before["target_gross_margin"]
    db.session.flush()

    reapproved = repriced = False
    try:
        if rerated and costing_was_current:
            approve_all_costing(version, actor=name, user_id=user_id, commit=False)
            reapproved = True
        costing_now = current_costing_snapshot(version)
        if had_pricing and costing_now is not None and working_matches_costing_snapshot(version, costing_now):
            apply_resolved_pricing_to_version(version, actor=name, organization_id=org_id)
            repriced = True
    except (EstimateCostingError, PricingEngineError) as exc:
        raise EstimateEconomicsError(str(exc)) from exc
    db.session.flush()
    return {"changed": True, "rerated": rerated, "reapproved": reapproved, "repriced": repriced}


# ---------------------------------------------------------------------------------------------- the figures
def economics(version, organization_id: Optional[str] = None) -> dict:
    """Labour, direct cost, selling price, gross profit, true gross margin, tax and customer total for a version.

    ``applied`` is True when these are the frozen pricing snapshot's figures (pricing is current: the customer
    estimate and proposal show exactly these). Otherwise they are the same calculation on the working costs, for
    the estimator to see before approving and applying.
    """
    from app.services.estimate_costing import current_costing_snapshot, working_matches_costing_snapshot
    from app.services.pricing_engine import (
        apply_tax_after_pre_tax,
        as_money,
        resolve_pricing_policy,
        true_gross_margin_pre_tax,
        version_line_direct_cost,
    )

    org_id = organization_id or _org(version)
    values = project_values(version, org_id)
    lines = labour_lines(version)
    hours = sum((Decimal(str(line.quantity)) for line in lines), Decimal("0"))
    labour_cost = as_money(sum((Decimal(str(line.extended_cost or 0)) for line in lines), Decimal("0")))
    snapshot = getattr(version, "pricing_snapshot", None)
    costing = current_costing_snapshot(version)
    costing_current = costing is not None and working_matches_costing_snapshot(version, costing)
    applied = (snapshot is not None and costing_current and snapshot.method == "TRUE_GROSS_MARGIN"
               and snapshot.costing_snapshot_id == costing.id
               and snapshot.target_gross_margin is not None and values["target_gross_margin"] is not None
               and Decimal(str(snapshot.target_gross_margin)) == values["target_gross_margin"])
    if applied:
        direct = as_money(snapshot.direct_cost_basis)
        selling = as_money(snapshot.pre_tax_selling_price)
        tax, total = as_money(snapshot.tax_amount), as_money(snapshot.customer_total)
        tax_percent = Decimal(str(snapshot.tax_percent))
    else:
        direct = version_line_direct_cost(version)
        margin = values["target_gross_margin"]
        selling = true_gross_margin_pre_tax(direct, margin) if margin is not None else None
        try:
            policy = resolve_pricing_policy(version, organization_id=org_id).get("policy")
        except Exception:  # noqa: BLE001 - a preview never blocks the page
            policy = None
        tax_percent = (Decimal(str(policy.tax_percent)) if policy is not None and policy.tax_percent is not None
                       else values["defaults"]["tax_percent"] or Decimal("0"))
        tax, total = apply_tax_after_pre_tax(selling, tax_percent) if selling is not None else (None, None)
    profit = as_money(selling - direct) if selling is not None else None
    true_margin = ((profit / selling) * HUNDRED).quantize(CENT) if selling else None
    return {
        **values,
        "labour_hours": hours,
        "labour_cost": labour_cost,
        "direct_cost": direct,
        "selling_price": selling,
        "gross_profit": profit,
        "true_gross_margin_percent": true_margin,
        "tax_percent": tax_percent,
        "tax": tax,
        "customer_total": total,
        "applied": applied,
        "costing_current": costing_current,
        "has_pricing": snapshot is not None,
    }


# ---------------------------------------------------------------------------------------------- company defaults (set)
def set_company_labour_rate(rate, *, actor: str, reason: str, organization_id: str):
    """The company default labour rate: the next approved direct labour cost rate standard (Labour rates).
    New estimates take it; existing estimates keep their own."""
    from app.services.labour_engine import LabourEngineError, promote_direct_labour_cost_rate

    value = parse_labour_rate(rate)
    try:
        return promote_direct_labour_cost_rate(value, approved_by=actor, reason=reason, organization_id=organization_id)
    except LabourEngineError as exc:
        raise EstimateEconomicsError(str(exc)) from exc


def set_company_default_margin(margin_percent, *, actor: str, reason: str, organization_id: str):
    """The company default target gross margin: the next version of the default true-gross-margin pricing policy
    (How we price), approved and made the default in one step. New estimates take it; existing ones keep theirs."""
    from app.services.pricing_engine import (
        PricingEngineError,
        approve_pricing_policy,
        record_pricing_audit,
        set_default_pricing_policy,
        supersede_pricing_policy,
    )

    value = parse_margin_percent(margin_percent)
    if not (reason or "").strip():
        raise EstimateEconomicsError("Give a reason for changing the company default margin.")
    policy = company_defaults(organization_id)["pricing_policy"]
    if policy is None or policy.method != "TRUE_GROSS_MARGIN":
        raise EstimateEconomicsError("The company has no approved default gross margin pricing to change. Set one up under How we price.")
    if policy.target_gross_margin is not None and Decimal(str(policy.target_gross_margin)) == value:
        return policy
    try:
        new_policy = supersede_pricing_policy(policy.id, actor=actor, organization_id=organization_id,
                                              target_gross_margin=value,
                                              provenance=f"Company default margin {(value * HUNDRED).quantize(CENT)}%: {reason.strip()}")
        approve_pricing_policy(new_policy.id, actor=actor, organization_id=organization_id)
        set_default_pricing_policy(new_policy.id, actor=actor, organization_id=organization_id)
        record_pricing_audit("company_default_margin_change", "OrganizationPricingPolicy", new_policy.id, actor=actor,
                             detail=f"{(Decimal(str(policy.target_gross_margin)) * HUNDRED).quantize(CENT)}% -> "
                                    f"{(value * HUNDRED).quantize(CENT)}%; reason: {reason.strip()}",
                             organization_id=organization_id)
    except PricingEngineError as exc:
        raise EstimateEconomicsError(str(exc)) from exc
    db.session.flush()
    return new_policy

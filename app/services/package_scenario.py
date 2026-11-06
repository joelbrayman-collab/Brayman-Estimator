"""Change it on the fly: per-package decisions on a working estimate version (Joel, 2 Nov 2026, the Paulusse case).

When a client answers a quote with "the stone went to someone else, and our budget for soffit, fascia and trim is
$8,800 plus the lift at cost", the contractor decides on the spot. Per work package on an editable version:

* "By others": the existing exclusion (work_packages.exclude_work / include_work, By Others / Owner / a named party).
  The package keeps its lines; they drop out of revenue and cost.
* Client budget / fixed price: the package's revenue is that amount instead of the pricing method's result; its
  costs stay as estimated. Stored on the version (EstimateVersion.package_pricing_json), so each version keeps its
  own decisions and an approved version never changes (a change is the next revision).
* Pass-through billed at cost (e.g. a lift rental): an ordinary line of kind "passthrough" (GE-PASSTHROUGH) in the
  package; it adds the same amount to cost and to revenue and is never part of a budget.

Customer price: a fixed-price package's budget is spread over its lines (pass-throughs excluded) by extended cost, the
last line taking the remainder (pricing_engine.scenario_price), so line sell prices and customer documents agree.
Budgets apply with the "labour at rate, margin on materials" pricing method.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional

from app import db

PASSTHROUGH_CODE = "GE-PASSTHROUGH"


class PackageScenarioError(ValueError):
    """A plain-language refusal shown to the person."""


def package_key_of_section(section) -> str:
    from app.services.work_packages import package_of_section

    stage = package_of_section(section)
    if stage is not None:
        return f"stage:{stage.id}"
    return f"section:{(section.name or '').strip()}"


def package_key(stage) -> str:
    return f"stage:{stage.id}"


def is_passthrough(line) -> bool:
    return (line.code or "") == PASSTHROUGH_CODE


def records(version) -> Dict[str, dict]:
    try:
        return json.loads(getattr(version, "package_pricing_json", None) or "{}") or {}
    except ValueError:
        return {}


def budgets(version) -> Dict[str, Decimal]:
    out = {}
    for key, row in records(version).items():
        if row.get("budget") not in (None, ""):
            out[key] = Decimal(str(row["budget"])).quantize(Decimal("0.01"))
    return out


def budget_label(version, key) -> Optional[str]:
    row = records(version).get(key) or {}
    return row.get("label") or None


def _parse_budget(raw) -> Optional[Decimal]:
    text = ("" if raw is None else str(raw)).strip().replace("$", "").replace(",", "")
    if text == "":
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise PackageScenarioError(f"A client budget must be an amount of money (you entered “{raw}”).") from None
    if not value.is_finite() or value < 0:
        raise PackageScenarioError("A client budget cannot be negative.")
    if value != value.quantize(Decimal("0.01")):
        raise PackageScenarioError("A client budget is dollars and cents.")
    return value.quantize(Decimal("0.01"))


def _require_editable(version):
    from app.services.estimate_approval import is_approved

    if version is None:
        raise PackageScenarioError("There is no estimate to change yet.")
    if version.is_locked or is_approved(version) or version.status != "Draft":
        raise PackageScenarioError(f"{version.display_label} is approved, sent or locked and never changes. Start the "
                                   "next revision to change it.")


def set_budget(version, key: str, amount, *, actor: str, label: str = "", reason: str = "",
               organization_id: Optional[str] = None) -> Optional[Decimal]:
    """Set (or clear, with a blank amount) a package's client budget on an editable version, then re-price it."""
    from app.models.pricing_engine import LABOUR_AT_RATE_MATERIAL_MARGIN
    from app.services.pricing_engine import record_pricing_audit

    name = (actor or "").strip()[:150]
    if not name or name.lower() in {"system", "ai", "calibraytai", "automatic"}:
        raise PackageScenarioError("A person must set a client budget.")
    _require_editable(version)
    value = _parse_budget(amount)
    if value is not None and getattr(version, "pricing_method", None) != LABOUR_AT_RATE_MATERIAL_MARGIN:
        raise PackageScenarioError("A client budget per package needs the “labour at rate, margin on materials” "
                                   "pricing method on this estimate.")
    data = records(version)
    before = data.get(key, {}).get("budget")
    if value is None:
        data.pop(key, None)
    else:
        data[key] = {"budget": str(value), "label": " ".join((label or "").split())[:120] or "client budget",
                     "reason": (reason or "").strip()[:300] or None, "set_by": name,
                     "set_at": datetime.utcnow().isoformat(timespec="seconds")}
    if (before or None) == (str(value) if value is not None else None):
        return value
    version.package_pricing_json = json.dumps(data, sort_keys=True) if data else None
    org_id = organization_id or version.estimate.project.organization_id
    record_pricing_audit("package_client_budget", "EstimateVersion", version.id, actor=name,
                         detail=f"{key}: {before or 'priced by the method'} -> {value if value is not None else 'priced by the method'}"
                                + (f"; reason: {reason.strip()}" if (reason or "").strip() else ""),
                         organization_id=org_id)
    _reprice(version, name)
    db.session.commit()
    return value


def _reprice(version, actor):
    """Re-apply pricing if it had been applied (the costing is unchanged: a budget changes the price, never costs)."""
    from app.services.estimate_costing import current_costing_snapshot, working_matches_costing_snapshot
    from app.services.pricing_engine import PricingEngineError, apply_resolved_pricing_to_version

    db.session.flush()
    costing = current_costing_snapshot(version)
    if getattr(version, "pricing_snapshot", None) is not None and costing is not None and \
            working_matches_costing_snapshot(version, costing):
        try:
            apply_resolved_pricing_to_version(version, actor=actor)
        except PricingEngineError as exc:
            db.session.rollback()
            raise PackageScenarioError(f"The change was not made: {exc}") from exc


# ---------------------------------------------------------------------------------------------- the live preview
def scenario_rows(version, crew_rates=None) -> dict:
    """Every package of the version (in or out of Brayman's price) with what the live P&L preview needs: its costs by
    kind, hours, internal price (labour at the rate + materials at the margin + the rest), pass-through amount,
    client budget, and revenue / real cost / profit as the version stands. Real labour cost uses the crew's loaded
    rates (None when no crew is assigned)."""
    from app.models.guided_estimating import GuidedEstimate
    from app.services import work_packages as WP
    from app.services.estimate_economics import economics
    from app.services.pricing_engine import (
        AT_COST_BUCKETS,
        BUCKET_LABOUR,
        BUCKET_MATERIAL,
        BUCKET_SUBCONTRACT,
        as_money,
        labour_material_margin_price,
        pricing_bucket,
    )

    e = economics(version)
    margin = Decimal(str(e.get("target_gross_margin") or 0))
    markup = Decimal(str(e.get("subcontract_markup_rate") or 0))
    rate = Decimal(str(e.get("labour_rate") or 0))
    share_total = sum((Decimal(str(c["share"])) for c in (crew_rates or [])), Decimal("0"))
    blend = (sum((Decimal(str(c["loaded_rate"])) * Decimal(str(c["share"])) for c in crew_rates), Decimal("0"))
             / share_total) if crew_rates else None
    fixed = budgets(version)
    guided = GuidedEstimate.query.filter_by(estimate_id=version.estimate_id).first()
    groups, owned = [], set()
    for package in WP.packages_in(guided, version):
        lines = WP.package_lines(package, version)
        owned.update(l.id for l in lines)
        if lines:
            groups.append((package, package_key(package), package.display_name, lines,
                           WP.package_participates(package, version)))
    for section in sorted(version.sections, key=lambda s: (s.sort_order or 0, s.id)):
        lines = [l for l in section.line_items if l.id not in owned]
        if lines:
            groups.append((None, package_key_of_section(section), section.name or "Estimate lines", lines,
                           WP.section_participates(section)))
    rows = []
    for package, key, name, lines, included in groups:
        mat = labour_value = hours = at_cost = sub = through = Decimal("0")
        labour_cost = Decimal("0")
        for line in lines:
            cost = Decimal(str(line.extended_cost or 0))
            bucket = pricing_bucket(line)
            if is_passthrough(line):
                through += cost
            if bucket == BUCKET_LABOUR:
                hours += Decimal(str(line.quantity or 0))
                labour_value += cost
                if blend is not None:
                    labour_cost += as_money(Decimal(str(line.quantity or 0)) * blend)
            elif bucket == BUCKET_MATERIAL:
                mat += cost
            elif bucket == BUCKET_SUBCONTRACT:
                sub += cost
            elif bucket in AT_COST_BUCKETS:
                at_cost += cost
        # The internal price is the pricing method on the package's own lines (the same engine and company rules).
        internal = labour_material_margin_price(lines, margin, None, e.get("pricing_rules"))["pre_tax"]
        budget = fixed.get(key)
        revenue = (budget + through if budget is not None else internal) if included else Decimal("0")
        cost = (mat + (labour_cost if blend is not None else Decimal("0")) + at_cost + sub) if included else Decimal("0")
        rows.append({
            "key": key, "stage_id": package.id if package is not None else None, "name": name, "included": included,
            "responsible": WP.responsible_label(package, version) if package is not None and not included else "",
            "materials": as_money(mat), "hours": hours, "labour_value": as_money(labour_value),
            "labour_cost": as_money(labour_cost) if blend is not None else None, "at_cost": as_money(at_cost),
            "subcontracts": as_money(sub), "passthrough": as_money(through), "internal_price": as_money(internal),
            "budget": budget, "budget_label": budget_label(version, key),
            "revenue": as_money(revenue),
            "cost": as_money(cost) if blend is not None or not included else None,
            "profit": as_money(revenue - cost) if (blend is not None and included) else None,
        })
    inc = [r for r in rows if r["included"]]
    revenue = sum((r["revenue"] for r in inc), Decimal("0"))
    cost = sum((r["cost"] for r in inc), Decimal("0")) if blend is not None else None
    from app.services.pricing_engine import allowance_treatment

    allowances = [{"line": l, "treatment": allowance_treatment(l)} for l in allowance_lines(version)]
    return {"rows": rows, "blend": blend, "labour_rate": rate, "margin": margin, "markup": markup,
            "allowances": allowances,
            "revenue": as_money(revenue), "cost": as_money(cost) if cost is not None else None,
            "profit": as_money(revenue - cost) if cost is not None else None,
            "editable": version.status == "Draft" and not version.is_locked}


# ---------------------------------------------------------------------------------------------- allowances (ruling 2)
def allowance_lines(version) -> list:
    from app.services.guided_estimating import _line_kind

    return [line for section in version.sections for line in section.line_items if _line_kind(line) == "allowance"]


def set_allowance_treatment(version, line, treatment: str, *, actor: str, organization_id: Optional[str] = None) -> str:
    """An allowance is either a pass-through (at cost, no markup: the default) or priced like materials (the material
    margin) — Joel's ruling 2, 2 Nov 2026. Only on an editable version; audited; re-prices when pricing was applied."""
    from app.services.guided_estimating import _line_kind
    from app.services.pricing_engine import ALLOWANCE_TREATMENTS, allowance_treatment, record_pricing_audit

    name = (actor or "").strip()[:150]
    if not name:
        raise PackageScenarioError("A person must set how an allowance is priced.")
    _require_editable(version)
    if line is None or line.section is None or line.section.estimate_version_id != version.id or \
            _line_kind(line) != "allowance":
        raise PackageScenarioError("Choose an allowance on this estimate.")
    value = (treatment or "").strip().upper()
    if value not in ALLOWANCE_TREATMENTS:
        raise PackageScenarioError("Choose pass-through (at cost) or priced (the material margin).")
    before = allowance_treatment(line)
    if before == value and line.pricing_treatment == value:
        return value
    line.pricing_treatment = value
    record_pricing_audit("allowance_pricing_treatment", "EstimateLineItem", line.id, actor=name,
                         detail=f"{line.description}: {before} -> {value}",
                         organization_id=organization_id or version.estimate.project.organization_id)
    _reprice(version, name)
    db.session.commit()
    return value

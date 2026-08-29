"""Organization-Calibrated Pricing Engine (FG-009 / ADR-025 / ADR-030)."""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import event

from app import db
from app.models.estimate import AUTO_LOCK_VERSION_STATUSES, EstimateLineItem, EstimateVersion
from app.models.labour_engine import EstimateLabourSnapshot
from app.models.organization import Organization
from app.models.pricing_engine import (
    AI_ACTOR_TOKENS,
    CONTINGENCY_PRICING_TREATMENTS,
    CONTINGENCY_VISIBILITIES,
    NO_SELECTED_COMMERCIAL_LAYER,
    OVERHEAD_TREATMENTS,
    POLICY_APPROVAL_STATUSES,
    PRICING_METHODS,
    PROFIT_TREATMENTS,
    EstimatePricingSnapshot,
    OrganizationPricingPolicy,
    PricingAuditEvent,
)
from app.models.project import Project
from app.services.organizations import get_current_organization_id

MONEY = Decimal("0.01")
HUNDRED = Decimal("100")


class PricingEngineError(Exception):
    pass


def as_decimal(value, default="0"):
    if value is None or value == "":
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PricingEngineError("Enter a valid number.") from exc


def as_money(value):
    return as_decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def _org_id(organization_id=None):
    return organization_id or get_current_organization_id()


def _organization_exists(org_id: str) -> bool:
    return Organization.query.get(org_id) is not None


def assert_human_actor(actor: Optional[str], *, action: str) -> str:
    name = (actor or "").strip()
    if not name:
        raise PricingEngineError(f"{action} requires a human actor.")
    if name.upper() in AI_ACTOR_TOKENS:
        raise PricingEngineError("AI cannot approve or set ORG-APPROVED pricing policy.")
    return name


def record_pricing_audit(
    event_type: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    actor: Optional[str] = None,
    detail: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> PricingAuditEvent:
    org_id = _org_id(organization_id)
    if not _organization_exists(org_id):
        raise PricingEngineError(
            f"Cannot persist pricing audit for unknown organization '{org_id}'."
        )
    event = PricingAuditEvent(
        organization_id=org_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        detail=detail,
    )
    db.session.add(event)
    return event


def true_gross_margin_exact(direct_cost, target_gross_margin):
    """Unquantized PRE-TAX SELL = DIRECT COST / (1 - TARGET GROSS MARGIN). Margin is a fraction."""
    cost = as_decimal(direct_cost)
    gm = as_decimal(target_gross_margin)
    if gm < 0 or gm >= 1:
        raise PricingEngineError("Target gross margin must be >= 0 and < 1.")
    if gm == 0:
        return cost
    return cost / (Decimal("1") - gm)


def true_gross_margin_pre_tax(direct_cost, target_gross_margin):
    """Customer-money PRE-TAX SELL from true GM (rounded half-up to cents)."""
    return as_money(true_gross_margin_exact(direct_cost, target_gross_margin))


def cost_plus_markup_pre_tax(direct_cost, markup_rate):
    """PRE-TAX SELL = DIRECT COST × (1 + MARKUP RATE). Rate is a fraction (0.15)."""
    cost = as_decimal(direct_cost)
    rate = as_decimal(markup_rate)
    if rate < 0:
        raise PricingEngineError("Markup rate cannot be negative.")
    return as_money(cost * (Decimal("1") + rate))


def legacy_stack_pre_tax(sell_subtotal, overhead_percent, profit_percent):
    """Named COST_PLUS_MARKUP_STACK version totals (pre-tax). Percents are 0–100."""
    subtotal = as_money(sell_subtotal)
    overhead = as_money(subtotal * as_decimal(overhead_percent) / HUNDRED)
    profit = as_money((subtotal + overhead) * as_decimal(profit_percent) / HUNDRED)
    return subtotal, overhead, profit, as_money(subtotal + overhead + profit)


def apply_tax_after_pre_tax(pre_tax_selling_price, tax_percent):
    pre_tax = as_money(pre_tax_selling_price)
    tax = as_money(pre_tax * as_decimal(tax_percent) / HUNDRED)
    return tax, as_money(pre_tax + tax)


def apply_contingency(direct_cost, visibility, pricing_treatment, rate, base_pre_tax=None):
    """Return (contingency_amount, margin_basis, pre_tax_placeholder).

    INTERNAL_RESERVE is tracked and never enters customer pre-tax.
    """
    direct = as_money(direct_cost)
    vis = visibility or "UNSPECIFIED"
    if vis not in CONTINGENCY_VISIBILITIES:
        raise PricingEngineError("Invalid contingency visibility.")
    if vis in NO_SELECTED_COMMERCIAL_LAYER:
        return as_money(0), direct, as_money(
            base_pre_tax if base_pre_tax is not None else direct
        )
    if vis == "INTERNAL_RESERVE":
        amount = as_money(direct * as_decimal(rate or 0))
        return amount, direct, as_money(
            base_pre_tax if base_pre_tax is not None else direct
        )

    treatment = pricing_treatment
    if treatment not in CONTINGENCY_PRICING_TREATMENTS:
        raise PricingEngineError(
            "CUSTOMER_PRICED contingency requires INCLUDED_IN_MARGIN_BASIS or ADDED_AFTER_BASE_PRICING."
        )
    amount = as_money(direct * as_decimal(rate or 0))
    if treatment == "INCLUDED_IN_MARGIN_BASIS":
        basis = as_money(direct + amount)
        return amount, basis, as_money(
            base_pre_tax if base_pre_tax is not None else basis
        )
    return amount, direct, as_money(
        as_money(base_pre_tax if base_pre_tax is not None else direct) + amount
    )


def compute_named_method_pre_tax(
    *,
    method,
    direct_cost,
    target_gross_margin=None,
    markup_rate=None,
    contingency_visibility="UNSPECIFIED",
    contingency_pricing_treatment=None,
    contingency_rate=None,
):
    vis = contingency_visibility or "UNSPECIFIED"
    if vis == "CUSTOMER_PRICED" and contingency_pricing_treatment == "INCLUDED_IN_MARGIN_BASIS":
        amount, basis, _ = apply_contingency(
            direct_cost, vis, contingency_pricing_treatment, contingency_rate
        )
        working = basis
    else:
        amount, basis, _ = apply_contingency(
            direct_cost, vis, contingency_pricing_treatment, contingency_rate
        )
        working = as_money(direct_cost)

    if method == "TRUE_GROSS_MARGIN":
        if vis == "CUSTOMER_PRICED" and contingency_pricing_treatment == "INCLUDED_IN_MARGIN_BASIS":
            base = true_gross_margin_pre_tax(working, target_gross_margin)
            return amount, working, base
        base = true_gross_margin_pre_tax(working, target_gross_margin)
        if vis == "CUSTOMER_PRICED" and contingency_pricing_treatment == "ADDED_AFTER_BASE_PRICING":
            return amount, working, as_money(base + amount)
        return amount, working, base

    if method == "COST_PLUS_MARKUP":
        if vis == "CUSTOMER_PRICED" and contingency_pricing_treatment == "INCLUDED_IN_MARGIN_BASIS":
            base = cost_plus_markup_pre_tax(working, markup_rate)
            return amount, working, base
        base = cost_plus_markup_pre_tax(working, markup_rate)
        if vis == "CUSTOMER_PRICED" and contingency_pricing_treatment == "ADDED_AFTER_BASE_PRICING":
            return amount, working, as_money(base + amount)
        return amount, working, base

    raise PricingEngineError(f"Unsupported named method '{method}'.")


def labour_engine_direct_cost_total(estimate_version, organization_id=None):
    """Read-only consumption of FG-008 Direct Labour Cost. Does not modify labour records."""
    org_id = _org_id(organization_id)
    rows = EstimateLabourSnapshot.query.filter_by(
        estimate_version_id=estimate_version.id,
        organization_id=org_id,
    ).all()
    total = Decimal("0")
    for row in rows:
        total += as_decimal(row.direct_labour_cost)
    return as_money(total)


def version_line_direct_cost(version):
    """Sum of line extended_cost (waste already in extended_cost)."""
    total = Decimal("0")
    for section in version.sections:
        for item in section.line_items:
            total += as_decimal(item.extended_cost)
    return as_money(total)


def get_pricing_policy_for_org(policy_id, organization_id=None):
    org_id = _org_id(organization_id)
    if not _organization_exists(org_id):
        raise PricingEngineError(f"Unknown organization '{org_id}'.")
    policy = OrganizationPricingPolicy.query.filter_by(
        id=policy_id, organization_id=org_id
    ).first()
    if policy is None:
        raise PricingEngineError("Pricing policy not found in this organization.")
    return policy


def list_pricing_policies(organization_id=None):
    org_id = _org_id(organization_id)
    if not _organization_exists(org_id):
        raise PricingEngineError(f"Unknown organization '{org_id}'.")
    return (
        OrganizationPricingPolicy.query.filter_by(organization_id=org_id)
        .order_by(
            OrganizationPricingPolicy.policy_code.asc(),
            OrganizationPricingPolicy.version_number.desc(),
        )
        .all()
    )


def _validate_policy_fields(
    *,
    method,
    target_gross_margin,
    markup_rate,
    overhead_treatment,
    profit_treatment,
    contingency_visibility,
    contingency_pricing_treatment,
):
    if method not in PRICING_METHODS:
        raise PricingEngineError("Select a valid pricing method.")
    if overhead_treatment not in OVERHEAD_TREATMENTS:
        raise PricingEngineError("Select a valid overhead treatment.")
    if profit_treatment not in PROFIT_TREATMENTS:
        raise PricingEngineError("Select a valid profit treatment.")
    if contingency_visibility not in CONTINGENCY_VISIBILITIES:
        raise PricingEngineError("Select a valid contingency visibility.")
    if contingency_visibility == "CUSTOMER_PRICED":
        if contingency_pricing_treatment not in CONTINGENCY_PRICING_TREATMENTS:
            raise PricingEngineError(
                "Customer-priced contingency requires an explicit pricing treatment."
            )
    if method == "TRUE_GROSS_MARGIN":
        if target_gross_margin is None or target_gross_margin == "":
            raise PricingEngineError(
                "TRUE_GROSS_MARGIN requires an explicit target gross margin."
            )
        gm = as_decimal(target_gross_margin)
        if gm < 0 or gm >= 1:
            raise PricingEngineError("Target gross margin must be >= 0 and < 1.")
    if method == "COST_PLUS_MARKUP":
        if markup_rate is None or markup_rate == "":
            raise PricingEngineError("COST_PLUS_MARKUP requires an explicit markup rate.")
        if as_decimal(markup_rate) < 0:
            raise PricingEngineError("Markup rate cannot be negative.")


def create_pricing_policy(
    *,
    policy_code,
    method,
    actor,
    organization_id=None,
    target_gross_margin=None,
    markup_rate=None,
    stack_overhead_percent=None,
    stack_profit_percent=None,
    overhead_treatment="UNSPECIFIED",
    profit_treatment="UNSPECIFIED",
    contingency_source=None,
    contingency_visibility="UNSPECIFIED",
    contingency_pricing_treatment=None,
    contingency_rate=None,
    tax_jurisdiction=None,
    tax_percent=None,
    is_default=False,
    provenance=None,
    version_number=1,
):
    org_id = _org_id(organization_id)
    if not _organization_exists(org_id):
        raise PricingEngineError(f"Unknown organization '{org_id}'.")
    actor_name = assert_human_actor(actor, action="Create pricing policy")
    code = (policy_code or "").strip()
    if not code:
        raise PricingEngineError("Policy code is required.")
    _validate_policy_fields(
        method=method,
        target_gross_margin=target_gross_margin,
        markup_rate=markup_rate,
        overhead_treatment=overhead_treatment,
        profit_treatment=profit_treatment,
        contingency_visibility=contingency_visibility,
        contingency_pricing_treatment=contingency_pricing_treatment,
    )
    if OrganizationPricingPolicy.query.filter_by(
        organization_id=org_id, policy_code=code, version_number=version_number
    ).first():
        raise PricingEngineError("A policy with this code and version already exists.")
    policy = OrganizationPricingPolicy(
        organization_id=org_id,
        policy_code=code,
        version_number=int(version_number),
        method=method,
        target_gross_margin=as_decimal(target_gross_margin) if target_gross_margin is not None else None,
        markup_rate=as_decimal(markup_rate) if markup_rate is not None else None,
        stack_overhead_percent=as_decimal(stack_overhead_percent) if stack_overhead_percent is not None else None,
        stack_profit_percent=as_decimal(stack_profit_percent) if stack_profit_percent is not None else None,
        overhead_treatment=overhead_treatment,
        profit_treatment=profit_treatment,
        contingency_source=(contingency_source or "").strip() or None,
        contingency_visibility=contingency_visibility,
        contingency_pricing_treatment=contingency_pricing_treatment
        if contingency_visibility == "CUSTOMER_PRICED"
        else None,
        contingency_rate=as_decimal(contingency_rate) if contingency_rate not in (None, "") else None,
        tax_jurisdiction=(tax_jurisdiction or "").strip() or None,
        tax_percent=as_decimal(tax_percent) if tax_percent not in (None, "") else None,
        is_default=False,
        approval_status="DRAFT",
        provenance=provenance,
        created_by=actor_name,
    )
    db.session.add(policy)
    db.session.flush()
    record_pricing_audit(
        "policy_create",
        "OrganizationPricingPolicy",
        policy.id,
        actor=actor_name,
        detail=f"Created DRAFT {code} v{policy.version_number} {method}",
        organization_id=org_id,
    )
    if is_default:
        approve_pricing_policy(policy.id, actor=actor_name, organization_id=org_id)
        set_default_pricing_policy(policy.id, actor=actor_name, organization_id=org_id)
    return policy


def approve_pricing_policy(policy_id, *, actor, organization_id=None):
    actor_name = assert_human_actor(actor, action="Approve pricing policy")
    policy = get_pricing_policy_for_org(policy_id, organization_id)
    if policy.approval_status == "ORG_APPROVED":
        return policy
    if policy.approval_status not in ("DRAFT", "WITHDRAWN"):
        raise PricingEngineError("Only DRAFT or WITHDRAWN policies can be approved.")
    policy.approval_status = "ORG_APPROVED"
    policy.approved_by = actor_name
    policy.approved_at = datetime.utcnow()
    record_pricing_audit(
        "policy_approve",
        "OrganizationPricingPolicy",
        policy.id,
        actor=actor_name,
        detail=f"Approved {policy.policy_code} v{policy.version_number}",
        organization_id=policy.organization_id,
    )
    return policy


def withdraw_pricing_policy(policy_id, *, actor, organization_id=None):
    actor_name = assert_human_actor(actor, action="Withdraw pricing policy")
    policy = get_pricing_policy_for_org(policy_id, organization_id)
    if policy.approval_status == "SUPERSEDED":
        raise PricingEngineError("Superseded policies cannot be withdrawn.")
    policy.approval_status = "WITHDRAWN"
    policy.is_default = False
    record_pricing_audit(
        "policy_withdraw",
        "OrganizationPricingPolicy",
        policy.id,
        actor=actor_name,
        detail=f"Withdrew {policy.policy_code} v{policy.version_number}",
        organization_id=policy.organization_id,
    )
    return policy


def supersede_pricing_policy(policy_id, *, actor, organization_id=None, **create_kwargs):
    actor_name = assert_human_actor(actor, action="Supersede pricing policy")
    current = get_pricing_policy_for_org(policy_id, organization_id)
    next_version = (
        db.session.query(db.func.max(OrganizationPricingPolicy.version_number))
        .filter_by(organization_id=current.organization_id, policy_code=current.policy_code)
        .scalar()
        or current.version_number
    ) + 1
    new_policy = create_pricing_policy(
        policy_code=current.policy_code,
        method=create_kwargs.get("method", current.method),
        actor=actor_name,
        organization_id=current.organization_id,
        target_gross_margin=create_kwargs.get("target_gross_margin", current.target_gross_margin),
        markup_rate=create_kwargs.get("markup_rate", current.markup_rate),
        stack_overhead_percent=create_kwargs.get(
            "stack_overhead_percent", current.stack_overhead_percent
        ),
        stack_profit_percent=create_kwargs.get(
            "stack_profit_percent", current.stack_profit_percent
        ),
        overhead_treatment=create_kwargs.get("overhead_treatment", current.overhead_treatment),
        profit_treatment=create_kwargs.get("profit_treatment", current.profit_treatment),
        contingency_source=create_kwargs.get("contingency_source", current.contingency_source),
        contingency_visibility=create_kwargs.get(
            "contingency_visibility", current.contingency_visibility
        ),
        contingency_pricing_treatment=create_kwargs.get(
            "contingency_pricing_treatment", current.contingency_pricing_treatment
        ),
        contingency_rate=create_kwargs.get("contingency_rate", current.contingency_rate),
        tax_jurisdiction=create_kwargs.get("tax_jurisdiction", current.tax_jurisdiction),
        tax_percent=create_kwargs.get("tax_percent", current.tax_percent),
        provenance=create_kwargs.get("provenance", current.provenance),
        version_number=next_version,
    )
    current.approval_status = "SUPERSEDED"
    current.is_default = False
    current.superseded_by_id = new_policy.id
    current.effective_to = datetime.utcnow()
    record_pricing_audit(
        "policy_supersede",
        "OrganizationPricingPolicy",
        current.id,
        actor=actor_name,
        detail=f"Superseded v{current.version_number} with v{new_policy.version_number}",
        organization_id=current.organization_id,
    )
    return new_policy


def set_default_pricing_policy(policy_id, *, actor, organization_id=None):
    actor_name = assert_human_actor(actor, action="Set default pricing policy")
    policy = get_pricing_policy_for_org(policy_id, organization_id)
    if policy.approval_status != "ORG_APPROVED":
        raise PricingEngineError("Only ORG-APPROVED policies can be the organization default.")
    others = OrganizationPricingPolicy.query.filter_by(
        organization_id=policy.organization_id, is_default=True
    ).all()
    for other in others:
        other.is_default = False
    policy.is_default = True
    record_pricing_audit(
        "default_policy_selection",
        "OrganizationPricingPolicy",
        policy.id,
        actor=actor_name,
        detail=f"Set default {policy.policy_code} v{policy.version_number}",
        organization_id=policy.organization_id,
    )
    return policy


def resolve_pricing_policy(estimate_version, organization_id=None):
    """Deterministic resolution. Unknown org fail-closed. No Brayman silent fallback."""
    org_id = _org_id(organization_id)
    if not _organization_exists(org_id):
        raise PricingEngineError(f"Unknown organization '{org_id}'.")

    project = estimate_version.estimate.project
    if project.organization_id != org_id:
        raise PricingEngineError("Estimate does not belong to this organization.")

    if estimate_version.pricing_policy_override_id:
        policy = get_pricing_policy_for_org(
            estimate_version.pricing_policy_override_id, org_id
        )
        if policy.approval_status != "ORG_APPROVED":
            raise PricingEngineError("Estimate override must reference an ORG-APPROVED policy.")
        if not (estimate_version.pricing_override_reason or "").strip():
            raise PricingEngineError("Estimate pricing override requires a reason.")
        return {
            "policy": policy,
            "method": policy.method,
            "source": "ESTIMATE_OVERRIDE",
            "requires_review": False,
            "reason": estimate_version.pricing_override_reason,
        }

    context = estimate_version.commercial_context
    if context is not None and context.pricing_policy_id:
        policy = get_pricing_policy_for_org(context.pricing_policy_id, org_id)
        if policy.approval_status != "ORG_APPROVED":
            raise PricingEngineError(
                "Commercial context policy pointer must be ORG-APPROVED."
            )
        return {
            "policy": policy,
            "method": policy.method,
            "source": "COMMERCIAL_CONTEXT",
            "requires_review": False,
            "reason": None,
        }

    approved_default = OrganizationPricingPolicy.query.filter_by(
        organization_id=org_id,
        approval_status="ORG_APPROVED",
        is_default=True,
    ).first()
    if approved_default is not None:
        return {
            "policy": approved_default,
            "method": approved_default.method,
            "source": "ORG_APPROVED_ACTIVE",
            "requires_review": False,
            "reason": None,
        }

    org_default = OrganizationPricingPolicy.query.filter_by(
        organization_id=org_id, is_default=True
    ).first()
    if org_default is not None:
        return {
            "policy": org_default,
            "method": org_default.method,
            "source": "ORGANIZATION_DEFAULT",
            "requires_review": org_default.approval_status != "ORG_APPROVED",
            "reason": None,
        }

    return {
        "policy": None,
        "method": "COST_PLUS_MARKUP_STACK",
        "source": "PROVISIONAL_LEGACY_STACK",
        "requires_review": True,
        "reason": "No organization pricing policy resolved; using legacy stack.",
    }


def set_estimate_pricing_override(
    estimate_version, policy_id, *, actor, reason, organization_id=None
):
    actor_name = assert_human_actor(actor, action="Set estimate pricing override")
    reason_text = (reason or "").strip()
    if not reason_text:
        raise PricingEngineError("Estimate pricing override requires a reason.")
    policy = get_pricing_policy_for_org(policy_id, organization_id)
    if policy.approval_status != "ORG_APPROVED":
        raise PricingEngineError("Override must use an ORG-APPROVED policy.")
    estimate_version.pricing_policy_override_id = policy.id
    estimate_version.pricing_override_reason = reason_text
    estimate_version.pricing_override_by = actor_name
    record_pricing_audit(
        "estimate_specific_override",
        "EstimateVersion",
        estimate_version.id,
        actor=actor_name,
        detail=reason_text,
        organization_id=policy.organization_id,
    )
    return estimate_version


def _context_posture_risk(version):
    ctx = version.commercial_context
    if ctx is None:
        return None, None
    return ctx.pricing_posture, ctx.execution_risk


def _allocate_line_sell_prices(version, pre_tax_total, direct_total):
    """Spread version pre-tax sell across lines in proportion to extended_cost."""
    remaining = as_money(pre_tax_total)
    items = []
    for section in version.sections:
        for item in section.line_items:
            items.append(item)
    if not items:
        return
    if as_decimal(direct_total) == 0:
        share = as_money(as_decimal(pre_tax_total) / Decimal(len(items)))
        for item in items[:-1]:
            item.sell_price = share
            remaining -= share
        items[-1].sell_price = remaining
    else:
        for item in items[:-1]:
            share = as_money(
                as_decimal(pre_tax_total)
                * as_decimal(item.extended_cost)
                / as_decimal(direct_total)
            )
            item.sell_price = share
            remaining -= share
        items[-1].sell_price = remaining
    from app.services.estimate_builder import as_money as builder_money

    for section in version.sections:
        total = Decimal("0")
        for item in section.line_items:
            total += as_decimal(item.sell_price)
        section.subtotal = builder_money(total)


def apply_legacy_stack_totals(version):
    from app.services.estimate_builder import as_money as builder_money

    subtotal = Decimal("0")
    for section in version.sections:
        section_total = Decimal("0")
        for item in section.line_items:
            section_total += as_decimal(item.sell_price)
        section.subtotal = builder_money(section_total)
        subtotal += section.subtotal
    version.subtotal = builder_money(subtotal)
    overhead_percent = as_decimal(version.overhead_percent)
    profit_percent = as_decimal(version.profit_percent)
    tax_percent = as_decimal(version.tax_percent)
    _, _, _, pre_tax = legacy_stack_pre_tax(version.subtotal, overhead_percent, profit_percent)
    tax, total = apply_tax_after_pre_tax(pre_tax, tax_percent)
    version.total = builder_money(total)
    return version


def _snapshot_amounts_from_version_stack(version):
    subtotal, overhead, profit, pre_tax = legacy_stack_pre_tax(
        version.subtotal, version.overhead_percent, version.profit_percent
    )
    tax, total = apply_tax_after_pre_tax(pre_tax, version.tax_percent)
    return as_money(0), as_money(version_line_direct_cost(version)), pre_tax, tax, total


def persist_pricing_snapshot(
    version,
    *,
    resolved,
    actor,
    organization_id,
    direct_cost,
    contingency_amount,
    pre_tax,
    tax_amount,
    customer_total,
):
    policy = resolved.get("policy")
    posture, risk = _context_posture_risk(version)
    existing = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).first()
    if existing is not None and version.is_locked:
        raise PricingEngineError("Locked estimate pricing snapshots cannot be replaced.")
    payload = dict(
        organization_id=organization_id,
        estimate_version_id=version.id,
        policy_id=policy.id if policy else None,
        policy_code=policy.policy_code if policy else None,
        policy_version_number=policy.version_number if policy else None,
        method=resolved["method"],
        resolution_source=resolved["source"],
        requires_review=bool(resolved.get("requires_review")),
        override_reason=resolved.get("reason") or version.pricing_override_reason,
        direct_cost_basis=direct_cost,
        target_gross_margin=policy.target_gross_margin if policy else None,
        markup_rate=policy.markup_rate if policy else None,
        stack_overhead_percent=version.overhead_percent
        if resolved["method"] == "COST_PLUS_MARKUP_STACK"
        else (policy.stack_overhead_percent if policy else None),
        stack_profit_percent=version.profit_percent
        if resolved["method"] == "COST_PLUS_MARKUP_STACK"
        else (policy.stack_profit_percent if policy else None),
        contingency_source=policy.contingency_source if policy else None,
        contingency_visibility=(
            policy.contingency_visibility if policy else "UNSPECIFIED"
        ),
        contingency_pricing_treatment=(
            policy.contingency_pricing_treatment if policy else None
        ),
        contingency_rate=policy.contingency_rate if policy else None,
        contingency_amount=contingency_amount,
        overhead_treatment=policy.overhead_treatment if policy else "UNSPECIFIED",
        profit_treatment=policy.profit_treatment if policy else "UNSPECIFIED",
        pricing_posture=posture,
        execution_risk=risk,
        tax_jurisdiction=policy.tax_jurisdiction if policy else None,
        tax_percent=version.tax_percent,
        pre_tax_selling_price=pre_tax,
        tax_amount=tax_amount,
        customer_total=customer_total,
        provenance=(
            f"source={resolved['source']}; method={resolved['method']}; "
            f"posture={posture}; execution_risk={risk}"
        ),
        created_by=actor,
    )
    if existing is None:
        snapshot = EstimatePricingSnapshot(**payload)
        db.session.add(snapshot)
        db.session.flush()
        record_pricing_audit(
            "pricing_snapshot_creation",
            "EstimatePricingSnapshot",
            snapshot.id,
            actor=actor,
            detail=payload["provenance"],
            organization_id=organization_id,
        )
        return snapshot
    if version.status in AUTO_LOCK_VERSION_STATUSES or version.is_locked:
        raise PricingEngineError("Cannot mutate a locked estimate pricing snapshot.")
    for key, value in payload.items():
        if key in ("organization_id", "estimate_version_id", "created_by"):
            continue
        setattr(existing, key, value)
    return existing


def apply_resolved_pricing_to_version(
    version,
    *,
    actor,
    organization_id=None,
    include_labour_snapshot_direct_cost=False,
):
    """Create/update snapshot and set version totals from resolved method. Draft only."""
    from app.services.estimate_builder import (
        apply_line_item_calculations,
        as_money as builder_money,
        ensure_version_editable,
    )

    org_id = _org_id(organization_id)
    actor_name = assert_human_actor(actor, action="Apply pricing policy")
    ensure_version_editable(version)
    if version.estimate.project.organization_id != org_id:
        raise PricingEngineError("Estimate does not belong to this organization.")

    for section in version.sections:
        for item in section.line_items:
            apply_line_item_calculations(item)

    resolved = resolve_pricing_policy(version, organization_id=org_id)
    record_pricing_audit(
        "estimate_policy_resolution",
        "EstimateVersion",
        version.id,
        actor=actor_name,
        detail=f"{resolved['source']} {resolved['method']}",
        organization_id=org_id,
    )
    record_pricing_audit(
        "pricing_calculation_method",
        "EstimateVersion",
        version.id,
        actor=actor_name,
        detail=resolved["method"],
        organization_id=org_id,
    )

    line_direct = version_line_direct_cost(version)
    labour_direct = labour_engine_direct_cost_total(version, organization_id=org_id)
    direct = line_direct
    if include_labour_snapshot_direct_cost:
        direct = as_money(line_direct + labour_direct)

    policy = resolved["policy"]
    method = resolved["method"]

    if method == "COST_PLUS_MARKUP_STACK":
        if policy is not None:
            if policy.stack_overhead_percent is not None:
                version.overhead_percent = policy.stack_overhead_percent
            if policy.stack_profit_percent is not None:
                version.profit_percent = policy.stack_profit_percent
            if policy.tax_percent is not None:
                version.tax_percent = policy.tax_percent
        apply_legacy_stack_totals(version)
        tax_amount = version.tax_amount
        pre_tax = as_money(
            as_decimal(version.total) - as_decimal(tax_amount)
        )
        snapshot = persist_pricing_snapshot(
            version,
            resolved=resolved,
            actor=actor_name,
            organization_id=org_id,
            direct_cost=direct,
            contingency_amount=as_money(0),
            pre_tax=pre_tax,
            tax_amount=as_money(tax_amount),
            customer_total=as_money(version.total),
        )
        db.session.flush()
        return snapshot

    if method in ("TRUE_GROSS_MARGIN", "COST_PLUS_MARKUP"):
        if method == "TRUE_GROSS_MARGIN" and policy and policy.method == "TRUE_GROSS_MARGIN":
            if policy.overhead_treatment not in OVERHEAD_TREATMENTS:
                raise PricingEngineError("TRUE_GROSS_MARGIN overhead treatment must be explicit.")
        vis = policy.contingency_visibility if policy else "UNSPECIFIED"
        treatment = policy.contingency_pricing_treatment if policy else None
        rate = policy.contingency_rate if policy else None
        gm = policy.target_gross_margin if policy else None
        markup = policy.markup_rate if policy else None
        amount, _basis, pre_tax = compute_named_method_pre_tax(
            method=method,
            direct_cost=direct,
            target_gross_margin=gm,
            markup_rate=markup,
            contingency_visibility=vis,
            contingency_pricing_treatment=treatment,
            contingency_rate=rate,
        )
        tax_percent = policy.tax_percent if policy and policy.tax_percent is not None else Decimal("0")
        version.tax_percent = tax_percent
        version.overhead_percent = Decimal("0")
        version.profit_percent = Decimal("0")
        tax_amount, customer_total = apply_tax_after_pre_tax(pre_tax, tax_percent)
        _allocate_line_sell_prices(version, pre_tax, direct)
        version.subtotal = builder_money(pre_tax)
        version.total = builder_money(customer_total)
        snapshot = persist_pricing_snapshot(
            version,
            resolved=resolved,
            actor=actor_name,
            organization_id=org_id,
            direct_cost=direct,
            contingency_amount=amount,
            pre_tax=pre_tax,
            tax_amount=tax_amount,
            customer_total=customer_total,
        )
        db.session.flush()
        return snapshot

    raise PricingEngineError(f"Unsupported method '{method}'.")


def refresh_version_from_snapshot(version):
    """Recalc lines then re-apply frozen snapshot method/rates. Does not re-resolve org policy."""
    from app.services.estimate_builder import apply_line_item_calculations, as_money as builder_money

    snapshot = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=version.id
    ).first()
    if snapshot is None:
        apply_legacy_stack_totals(version)
        return version

    for section in version.sections:
        for item in section.line_items:
            apply_line_item_calculations(item)

    direct = version_line_direct_cost(version)
    method = snapshot.method
    if method == "COST_PLUS_MARKUP_STACK":
        if snapshot.stack_overhead_percent is not None:
            version.overhead_percent = snapshot.stack_overhead_percent
        if snapshot.stack_profit_percent is not None:
            version.profit_percent = snapshot.stack_profit_percent
        if snapshot.tax_percent is not None:
            version.tax_percent = snapshot.tax_percent
        apply_legacy_stack_totals(version)
        tax_amount = version.tax_amount
        pre_tax = as_money(as_decimal(version.total) - as_decimal(tax_amount))
        snapshot.direct_cost_basis = direct
        snapshot.pre_tax_selling_price = pre_tax
        snapshot.tax_amount = as_money(tax_amount)
        snapshot.customer_total = as_money(version.total)
        return version

    amount, _basis, pre_tax = compute_named_method_pre_tax(
        method=method,
        direct_cost=direct,
        target_gross_margin=snapshot.target_gross_margin,
        markup_rate=snapshot.markup_rate,
        contingency_visibility=snapshot.contingency_visibility,
        contingency_pricing_treatment=snapshot.contingency_pricing_treatment,
        contingency_rate=snapshot.contingency_rate,
    )
    tax_amount, customer_total = apply_tax_after_pre_tax(pre_tax, snapshot.tax_percent)
    _allocate_line_sell_prices(version, pre_tax, direct)
    version.overhead_percent = Decimal("0")
    version.profit_percent = Decimal("0")
    version.tax_percent = snapshot.tax_percent
    version.subtotal = builder_money(pre_tax)
    version.total = builder_money(customer_total)
    if not version.is_locked:
        snapshot.direct_cost_basis = direct
        snapshot.contingency_amount = amount
        snapshot.pre_tax_selling_price = pre_tax
        snapshot.tax_amount = tax_amount
        snapshot.customer_total = customer_total
    return version


def _change_order_organization_id(change_order):
    project = change_order.project
    if project is None:
        project = Project.query.get(change_order.project_id)
    if project is None:
        raise PricingEngineError("Change Order project not found.")
    return project.organization_id


def price_change_order_from_snapshot(change_order, snapshot=None):
    """Price a FG-009-aware Change Order using the attached snapshot's method.

    Direct Cost = Σ CO item totals (already stored on change_order.subtotal).
    Does not invent a second engine. Reuses named-method and legacy-stack helpers.
    """
    if snapshot is None:
        snapshot = change_order.pricing_snapshot
        if snapshot is None and change_order.pricing_snapshot_id:
            snapshot = EstimatePricingSnapshot.query.get(
                change_order.pricing_snapshot_id
            )
    if snapshot is None:
        raise PricingEngineError("Change Order pricing snapshot not found.")
    co_org = _change_order_organization_id(change_order)
    if snapshot.organization_id != co_org:
        raise PricingEngineError("Snapshot does not belong to this organization.")

    direct = as_money(change_order.subtotal)
    method = snapshot.method
    vis = snapshot.contingency_visibility or "UNSPECIFIED"

    if method == "COST_PLUS_MARKUP_STACK":
        amount, basis, _ = apply_contingency(
            direct,
            vis,
            snapshot.contingency_pricing_treatment,
            snapshot.contingency_rate,
        )
        if (
            vis == "CUSTOMER_PRICED"
            and snapshot.contingency_pricing_treatment == "INCLUDED_IN_MARGIN_BASIS"
        ):
            working = basis
        else:
            working = direct
        _, _, _, pre_tax = legacy_stack_pre_tax(
            working,
            snapshot.stack_overhead_percent or 0,
            snapshot.stack_profit_percent or 0,
        )
        if (
            vis == "CUSTOMER_PRICED"
            and snapshot.contingency_pricing_treatment == "ADDED_AFTER_BASE_PRICING"
        ):
            pre_tax = as_money(pre_tax + amount)
        # Do not flatten overhead+profit into a fake single markup percent.
        change_order.markup_percent = Decimal("0")
        change_order.markup = as_money(pre_tax - direct)
    elif method in ("TRUE_GROSS_MARGIN", "COST_PLUS_MARKUP"):
        amount, _, pre_tax = compute_named_method_pre_tax(
            method=method,
            direct_cost=direct,
            target_gross_margin=snapshot.target_gross_margin,
            markup_rate=snapshot.markup_rate,
            contingency_visibility=vis,
            contingency_pricing_treatment=snapshot.contingency_pricing_treatment,
            contingency_rate=snapshot.contingency_rate,
        )
        if method == "TRUE_GROSS_MARGIN":
            # Preserve method identity: never store GM as a markup percent.
            change_order.markup_percent = Decimal("0")
        else:
            rate = as_decimal(snapshot.markup_rate or 0)
            change_order.markup_percent = as_money(rate * HUNDRED)
        change_order.markup = as_money(pre_tax - direct)
    else:
        raise PricingEngineError(f"Unsupported named method '{method}'.")

    tax, total = apply_tax_after_pre_tax(pre_tax, snapshot.tax_percent or 0)
    change_order.tax_percent = as_decimal(snapshot.tax_percent or 0)
    change_order.tax = tax
    change_order.total = total
    return change_order


def inherit_snapshot_for_change_order(change_order, estimate_version, *, actor=None):
    snapshot = EstimatePricingSnapshot.query.filter_by(
        estimate_version_id=estimate_version.id
    ).first()
    if snapshot is None:
        return change_order
    org_id = estimate_version.estimate.project.organization_id
    co_org = _change_order_organization_id(change_order)
    if snapshot.organization_id != org_id or snapshot.organization_id != co_org:
        raise PricingEngineError("Snapshot does not belong to this organization.")
    change_order.pricing_snapshot_id = snapshot.id
    change_order.tax_percent = snapshot.tax_percent or Decimal("0")
    record_pricing_audit(
        "change_order_inherited_policy",
        "ChangeOrder",
        change_order.id,
        actor=actor,
        detail=(
            f"Inherited snapshot {snapshot.id} method={snapshot.method} "
            f"(method identity preserved; not flattened to markup percent)"
        ),
        organization_id=org_id,
    )
    return change_order


def override_change_order_snapshot(
    change_order, snapshot, *, actor, reason, organization_id=None
):
    actor_name = assert_human_actor(actor, action="Override change order pricing")
    reason_text = (reason or "").strip()
    if not reason_text:
        raise PricingEngineError("Change Order pricing override requires a reason.")
    org_id = _org_id(organization_id)
    co_org = _change_order_organization_id(change_order)
    if snapshot.organization_id != org_id or snapshot.organization_id != co_org:
        raise PricingEngineError("Snapshot does not belong to this organization.")
    change_order.pricing_snapshot_id = snapshot.id
    change_order.pricing_override_reason = reason_text
    change_order.pricing_override_by = actor_name
    change_order.tax_percent = snapshot.tax_percent or Decimal("0")
    record_pricing_audit(
        "change_order_override",
        "ChangeOrder",
        change_order.id,
        actor=actor_name,
        detail=f"{reason_text} (method={snapshot.method})",
        organization_id=org_id,
    )
    price_change_order_from_snapshot(change_order, snapshot)
    return change_order


@event.listens_for(EstimatePricingSnapshot, "before_update")
def _reject_locked_pricing_snapshot_update(mapper, connection, target):
    version = EstimateVersion.query.get(target.estimate_version_id)
    if version is not None and (
        version.is_locked or version.status in AUTO_LOCK_VERSION_STATUSES
    ):
        raise PricingEngineError(
            "Locked estimate pricing snapshots cannot be mutated."
        )


@event.listens_for(EstimatePricingSnapshot, "before_delete")
def _reject_locked_pricing_snapshot_delete(mapper, connection, target):
    version = EstimateVersion.query.get(target.estimate_version_id)
    if version is not None and (
        version.is_locked or version.status in AUTO_LOCK_VERSION_STATUSES
    ):
        raise PricingEngineError(
            "Locked estimate pricing snapshots cannot be deleted."
        )

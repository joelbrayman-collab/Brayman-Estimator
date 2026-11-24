"""Shared materials markup calculation (FG-042, Joel 24 Nov 2026).

One calculation for every place that prices materials, so the estimate, the Project baseline and the Living Project P&L
cannot disagree:

    selling = net cost x (1 + markup)        profit = selling - net cost        margin = profit / selling (revenue)

Money is rounded half-up to the cent per line; a package is the sum of its rounded lines and a project the sum of its
packages, so every total can be traced to the lines that make it up (no rounding is done on a total). A quoted price
may replace the calculated one only with a reason; the difference is shown as a discount (or premium) against the
calculated price. This module does not change any existing pricing method.

Which markup applies, most specific first: a PROJECT override, then a SUPPLIER override, then the company markup (the
organization's ORG-APPROVED default pricing policy). With none of these there is no markup: the caller is told, not
given a silent default.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Optional

from app import db
from app.models.pricing_engine import MARKUP_OVERRIDE_SCOPES, OrganizationPricingPolicy, PricingMarkupOverride

ZERO = Decimal("0.00")
CENT = Decimal("0.01")

SOURCE_PROJECT = "PROJECT_OVERRIDE"
SOURCE_SUPPLIER = "SUPPLIER_OVERRIDE"
SOURCE_COMPANY = "COMPANY_DEFAULT"


class MarkupError(ValueError):
    """A markup input is invalid or the actor may not set it."""


def _dec(value, what: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # noqa: BLE001
        raise MarkupError(f"{what} is not a valid number.") from exc


def _money(value: Decimal) -> Decimal:
    from decimal import ROUND_HALF_UP

    return value.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PricedLine:
    net_cost: Decimal
    markup_rate: Decimal
    calculated_selling: Decimal
    selling: Decimal
    profit: Decimal
    discount: Decimal  # calculated - quoted (positive = discounted, negative = premium); zero without a quote
    quoted: bool
    override_reason: Optional[str]

    @property
    def margin(self) -> Optional[Decimal]:
        return None if self.selling == 0 else self.profit / self.selling


def price_line(net_cost, markup_rate, *, quoted_price=None, override_reason: Optional[str] = None) -> PricedLine:
    net = _money(_dec(net_cost, "Net cost"))
    rate = _dec(markup_rate, "Markup")
    if net < 0:
        raise MarkupError("Net cost cannot be negative.")
    if rate < 0:
        raise MarkupError("Markup cannot be negative.")
    calculated = _money(net * (Decimal("1") + rate))
    if quoted_price is None or quoted_price == "":
        return PricedLine(net, rate, calculated, calculated, calculated - net, ZERO, False, None)
    reason = (override_reason or "").strip()
    if not reason:
        raise MarkupError("A quoted price that replaces the calculated price needs a reason.")
    quoted = _money(_dec(quoted_price, "Quoted price"))
    if quoted < 0:
        raise MarkupError("Quoted price cannot be negative.")
    return PricedLine(net, rate, calculated, quoted, quoted - net, calculated - quoted, True, reason)


@dataclass(frozen=True)
class Totals:
    net_cost: Decimal
    selling: Decimal
    profit: Decimal
    discount: Decimal
    line_count: int

    @property
    def margin(self) -> Optional[Decimal]:
        return None if self.selling == 0 else self.profit / self.selling


def total(lines: Iterable[PricedLine]) -> Totals:
    """Sum already-rounded lines. Revenue, cost, profit and margin come from the same lines, so they reconcile."""
    items = list(lines)
    net = sum((i.net_cost for i in items), ZERO)
    selling = sum((i.selling for i in items), ZERO)
    discount = sum((i.discount for i in items), ZERO)
    return Totals(net, selling, selling - net, discount, len(items))


def total_packages(packages: Iterable[Totals]) -> Totals:
    items = list(packages)
    net = sum((p.net_cost for p in items), ZERO)
    selling = sum((p.selling for p in items), ZERO)
    return Totals(net, selling, selling - net, sum((p.discount for p in items), ZERO),
                  sum(p.line_count for p in items))


# ----------------------------------------------------------------------------------------------- which markup
def _in_force(organization_id: str, scope: str, column, target_id: int, on_day: date):
    return (PricingMarkupOverride.query
            .filter(PricingMarkupOverride.organization_id == organization_id,
                    PricingMarkupOverride.scope == scope, column == target_id,
                    PricingMarkupOverride.effective_from <= on_day)
            .order_by(PricingMarkupOverride.effective_from.desc(), PricingMarkupOverride.id.desc())
            .first())


def company_markup_rate(organization_id: str) -> Optional[Decimal]:
    policy = OrganizationPricingPolicy.query.filter_by(
        organization_id=organization_id, approval_status="ORG_APPROVED", is_default=True).first()
    if policy is None or policy.markup_rate is None:
        return None
    return Decimal(str(policy.markup_rate))


def resolve_markup(organization_id: str, *, project_id: Optional[int] = None, supplier_id: Optional[int] = None,
                   on_day: Optional[date] = None):
    """Returns (rate, source, reason) or (None, None, None) when no markup is configured."""
    day = on_day or date.today()
    if project_id is not None:
        row = _in_force(organization_id, "PROJECT", PricingMarkupOverride.project_id, project_id, day)
        if row is not None:
            return Decimal(str(row.markup_rate)), SOURCE_PROJECT, row.reason
    if supplier_id is not None:
        row = _in_force(organization_id, "SUPPLIER", PricingMarkupOverride.supplier_id, supplier_id, day)
        if row is not None:
            return Decimal(str(row.markup_rate)), SOURCE_SUPPLIER, row.reason
    rate = company_markup_rate(organization_id)
    if rate is not None:
        return rate, SOURCE_COMPANY, None
    return None, None, None


def record_markup_override(organization_id: str, *, scope: str, target_id: int, markup_rate, reason: str,
                           effective_from: Optional[date] = None, actor) -> PricingMarkupOverride:
    """Owner or System Administrator only. Insert-only: a change is a new row with a later effective date."""
    from app.services.documents.access import is_people_admin

    if not is_people_admin(actor, organization_id):
        raise MarkupError("Only the owner or a System Administrator may set a markup override.")
    if scope not in MARKUP_OVERRIDE_SCOPES:
        raise MarkupError("Scope must be PROJECT or SUPPLIER.")
    rate = _dec(markup_rate, "Markup")
    if rate < 0:
        raise MarkupError("Markup cannot be negative.")
    why = (reason or "").strip()
    if not why:
        raise MarkupError("A markup override needs a reason.")
    if len(why) > 300:
        raise MarkupError("The reason is limited to 300 characters.")
    row = PricingMarkupOverride(
        organization_id=organization_id, scope=scope,
        project_id=target_id if scope == "PROJECT" else None,
        supplier_id=target_id if scope == "SUPPLIER" else None,
        markup_rate=rate, reason=why, effective_from=effective_from or date.today(),
        created_at=datetime.utcnow(), actor_user_id=actor.id,
        actor_name=getattr(actor, "display_name", None) or getattr(actor, "email", "") or "Unknown")
    db.session.add(row)
    db.session.commit()
    return row

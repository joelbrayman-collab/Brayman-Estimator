"""Business logic for Change Orders."""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from app import db
from app.project_controls import repository as repo
from app.project_controls.models import (
    CHANGE_ORDER_STATUSES,
    ChangeOrder,
    ChangeOrderItem,
)
from app.services.organization_records import (
    acting_organization_id,
    require_organization_change_order,
    require_organization_change_order_item,
    require_organization_estimate_version,
    require_organization_project,
)
from app.services.project_operating_lifecycle import (
    project_is_closed,
    raise_if_project_closed,
)
from app.presentation.contractor_copy import PROJECT_CLOSED_NEW_WORK

MONEY = Decimal("0.01")
HUNDRED = Decimal("100")


class ChangeOrderServiceError(Exception):
    pass


CHANGE_ORDER_CANNOT_MOVE = "That change order cannot be moved to another project."


ADMINISTRATIVE_CO_FIELDS = frozenset({"status", "notes"})


def as_decimal(value, default="0"):
    if value is None or value == "":
        value = default
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ChangeOrderServiceError("Enter a valid number.") from exc


def as_money(value):
    return as_decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def apply_item_calculations(item):
    quantity = as_decimal(item.quantity)
    unit_price = as_decimal(item.unit_price)
    item.quantity = quantity
    item.unit_price = unit_price
    item.total = as_money(quantity * unit_price)
    return item


def recalculate_change_order(change_order):
    subtotal = Decimal("0")
    for item in change_order.items:
        apply_item_calculations(item)
        subtotal += as_money(item.total)

    change_order.subtotal = as_money(subtotal)
    if change_order.pricing_snapshot_id:
        from app.services.pricing_engine import (
            PricingEngineError,
            price_change_order_from_snapshot,
        )

        try:
            price_change_order_from_snapshot(change_order)
        except PricingEngineError as exc:
            raise ChangeOrderServiceError(str(exc)) from exc
        change_order.updated_at = datetime.utcnow()
        return change_order

    markup_percent = as_decimal(change_order.markup_percent or 0)
    tax_percent = as_decimal(change_order.tax_percent or 0)
    if markup_percent < 0 or tax_percent < 0:
        raise ChangeOrderServiceError("Percents cannot be negative.")

    change_order.markup_percent = markup_percent
    change_order.tax_percent = tax_percent
    change_order.markup = as_money(change_order.subtotal * markup_percent / HUNDRED)
    taxable = change_order.subtotal + change_order.markup
    change_order.tax = as_money(taxable * tax_percent / HUNDRED)
    change_order.total = as_money(taxable + change_order.tax)
    change_order.updated_at = datetime.utcnow()
    return change_order


def create_change_order(
    *,
    project,
    title,
    description=None,
    reason=None,
    requested_by=None,
    requested_date=None,
    estimate_version=None,
    markup_percent=0,
    tax_percent=0,
    notes=None,
    copy_estimate_lines=False,
    number=None,
    status="Draft",
    organization_id=None,
    commit=True,
):
    title = (title or "").strip()
    if not title:
        raise ChangeOrderServiceError("Title is required.")
    if project is None:
        raise ChangeOrderServiceError("Project is required.")
    org_id = acting_organization_id(organization_id)
    project = require_organization_project(
        project,
        organization_id=org_id,
        error_class=ChangeOrderServiceError,
        message="Project not found.",
    )
    raise_if_project_closed(project, ChangeOrderServiceError)
    if status not in CHANGE_ORDER_STATUSES:
        raise ChangeOrderServiceError("Select a valid status.")

    if estimate_version is not None:
        estimate_version = require_organization_estimate_version(
            estimate_version,
            organization_id=org_id,
            error_class=ChangeOrderServiceError,
            message="Not found.",
        )
        estimate = estimate_version.estimate
        if estimate.project_id != project.id:
            raise ChangeOrderServiceError(
                "Estimate version does not belong to this project."
            )

    change_order = ChangeOrder(
        project_id=project.id,
        estimate_version_id=estimate_version.id if estimate_version else None,
        number=number or repo.next_change_order_number(),
        title=title,
        description=(description or "").strip() or None,
        reason=(reason or "").strip() or None,
        status=status,
        requested_by=(requested_by or "").strip() or None,
        requested_date=requested_date or date.today(),
        markup_percent=as_decimal(markup_percent),
        tax_percent=as_decimal(tax_percent),
        notes=(notes or "").strip() or None,
    )
    repo.add_change_order(change_order)
    db.session.flush()

    if estimate_version is not None:
        from app.services.pricing_engine import (
            PricingEngineError,
            inherit_snapshot_for_change_order,
        )

        try:
            inherit_snapshot_for_change_order(
                change_order, estimate_version, actor=requested_by
            )
        except PricingEngineError as exc:
            raise ChangeOrderServiceError(str(exc)) from exc

    if copy_estimate_lines and estimate_version is not None:
        use_direct_cost = change_order.pricing_snapshot_id is not None
        sort_order = 0
        for section in estimate_version.sections:
            for line in section.line_items:
                quantity = as_decimal(line.quantity)
                if use_direct_cost:
                    if quantity == 0:
                        unit_price = as_decimal(line.extended_cost)
                    else:
                        unit_price = as_decimal(line.extended_cost) / quantity
                elif quantity == 0:
                    unit_price = as_decimal(line.sell_price)
                else:
                    unit_price = as_decimal(line.sell_price) / quantity
                item = ChangeOrderItem(
                    change_order_id=change_order.id,
                    description=line.description,
                    quantity=quantity,
                    unit=line.unit,
                    unit_price=unit_price,
                    sort_order=sort_order,
                )
                apply_item_calculations(item)
                change_order.items.append(item)
                sort_order += 1

    recalculate_change_order(change_order)
    if commit:
        db.session.commit()
    else:
        db.session.flush()
    return change_order


def update_change_order(change_order, **fields):
    organization_id = fields.pop("organization_id", None)
    org_id = acting_organization_id(organization_id)
    change_order = require_organization_change_order(
        change_order,
        organization_id=org_id,
        error_class=ChangeOrderServiceError,
        message="Not found.",
    )
    if project_is_closed(change_order.project):
        extra = set(fields) - ADMINISTRATIVE_CO_FIELDS
        if extra:
            raise ChangeOrderServiceError(PROJECT_CLOSED_NEW_WORK)
    if "project_id" in fields and fields["project_id"]:
        posted_id = int(fields["project_id"])
        if posted_id != change_order.project_id:
            raise ChangeOrderServiceError(CHANGE_ORDER_CANNOT_MOVE)
    if "title" in fields:
        title = (fields["title"] or "").strip()
        if not title:
            raise ChangeOrderServiceError("Title is required.")
        change_order.title = title

    for field in ("description", "reason", "requested_by", "notes"):
        if field in fields:
            value = (fields.get(field) or "").strip() or None
            setattr(change_order, field, value)

    if "requested_date" in fields:
        change_order.requested_date = fields["requested_date"]

    if "estimate_version_id" in fields:
        version_id = fields["estimate_version_id"] or None
        if version_id:
            version = require_organization_estimate_version(
                version_id,
                organization_id=org_id,
                error_class=ChangeOrderServiceError,
                message="Not found.",
            )
            if version.estimate.project_id != change_order.project_id:
                raise ChangeOrderServiceError(
                    "Estimate version does not belong to this project."
                )
            change_order.estimate_version_id = version.id
        else:
            change_order.estimate_version_id = None

    if "markup_percent" in fields:
        change_order.markup_percent = as_decimal(fields["markup_percent"])
    if "tax_percent" in fields:
        change_order.tax_percent = as_decimal(fields["tax_percent"])

    if "status" in fields:
        update_change_order_status(change_order, fields["status"], commit=False)

    recalculate_change_order(change_order)
    db.session.commit()
    return change_order


def update_change_order_status(change_order, status, *, commit=True, organization_id=None):
    change_order = require_organization_change_order(
        change_order,
        organization_id=acting_organization_id(organization_id),
        error_class=ChangeOrderServiceError,
        message="Not found.",
    )
    if status not in CHANGE_ORDER_STATUSES:
        raise ChangeOrderServiceError("Select a valid status.")
    previous = change_order.status
    change_order.status = status
    if status == "Approved" and previous != "Approved":
        change_order.approved_date = date.today()
    if status != "Approved" and previous == "Approved" and status in (
        "Draft",
        "Pending Approval",
        "Rejected",
        "Cancelled",
    ):
        change_order.approved_date = None
    change_order.updated_at = datetime.utcnow()
    if commit:
        db.session.commit()
    return change_order


def add_change_order_item(
    change_order,
    *,
    description,
    quantity=1,
    unit="ea",
    unit_price=0,
    organization_id=None,
):
    change_order = require_organization_change_order(
        change_order,
        organization_id=acting_organization_id(organization_id),
        error_class=ChangeOrderServiceError,
        message="Not found.",
    )
    raise_if_project_closed(change_order.project, ChangeOrderServiceError)
    description = (description or "").strip()
    unit = (unit or "").strip()
    if not description:
        raise ChangeOrderServiceError("Description is required.")
    if not unit:
        raise ChangeOrderServiceError("Unit is required.")

    sort_order = 0
    if change_order.items:
        sort_order = max(item.sort_order for item in change_order.items) + 1

    item = ChangeOrderItem(
        change_order_id=change_order.id,
        description=description,
        quantity=as_decimal(quantity),
        unit=unit,
        unit_price=as_decimal(unit_price),
        sort_order=sort_order,
    )
    apply_item_calculations(item)
    change_order.items.append(item)
    recalculate_change_order(change_order)
    db.session.commit()
    return item


def update_change_order_item(
    item,
    *,
    description=None,
    quantity=None,
    unit=None,
    unit_price=None,
    organization_id=None,
):
    org_id = acting_organization_id(organization_id)
    item = require_organization_change_order_item(
        item,
        organization_id=org_id,
        error_class=ChangeOrderServiceError,
        message="Not found.",
    )
    raise_if_project_closed(item.change_order.project, ChangeOrderServiceError)
    if description is not None:
        description = description.strip()
        if not description:
            raise ChangeOrderServiceError("Description is required.")
        item.description = description
    if unit is not None:
        unit = unit.strip()
        if not unit:
            raise ChangeOrderServiceError("Unit is required.")
        item.unit = unit
    if quantity is not None:
        qty = as_decimal(quantity)
        if qty < 0:
            raise ChangeOrderServiceError("Quantity cannot be negative.")
        item.quantity = qty
    if unit_price is not None:
        price = as_decimal(unit_price)
        if price < 0:
            raise ChangeOrderServiceError("Unit price cannot be negative.")
        item.unit_price = price

    apply_item_calculations(item)
    recalculate_change_order(item.change_order)
    db.session.commit()
    return item


def delete_change_order_item(item, *, organization_id=None):
    org_id = acting_organization_id(organization_id)
    item = require_organization_change_order_item(
        item,
        organization_id=org_id,
        error_class=ChangeOrderServiceError,
        message="Not found.",
    )
    change_order = item.change_order
    raise_if_project_closed(change_order.project, ChangeOrderServiceError)
    change_order_id = change_order.id
    repo.delete_change_order_item(item)
    db.session.flush()
    db.session.expire(change_order, ["items"])
    change_order = repo.get_change_order(change_order_id, organization_id=org_id)
    recalculate_change_order(change_order)
    db.session.commit()
    return change_order

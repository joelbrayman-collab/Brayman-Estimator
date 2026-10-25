"""Confirm Delivery: what actually arrived at the jobsite, against the existing purchase order (25 Oct 2026).

A worker on the job (Field) picks the order and answers Received, Short or Damaged, with the quantity that arrived
for each line, a note and photos (kept as a Field capture). Who and when are recorded.

- Received, everything in full and undamaged: the order is marked delivered through the EXISTING "marked
  delivered" action (supplier_hub.mark_order_delivered), so the supplier and the calendar see it as before.
- Short or Damaged: an exception for the office (Needs My Attention). The order stays open — never complete while a
  quantity is outstanding — and its own lines and expected quantities are never changed.
- The office resolves the exception: the rest is coming (wait for the next delivery), a replacement was arranged
  with the supplier, or accept what came and close the order (marked delivered with the note).

No stock, inventory or supplier confirmation is invented: only what the worker counted is recorded, and an order
the supplier has not confirmed in CalibraytAI is never marked delivered here.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from app import db
from app.models.field_operations import (
    DELIVERY_DAMAGED,
    DELIVERY_OUTCOMES,
    DELIVERY_RECEIVED,
    DELIVERY_SHORT,
    EXCEPTION_NONE,
    EXCEPTION_OPEN,
    EXCEPTION_RESOLVED,
    RECORD_DELIVERY,
    DeliveryConfirmation,
)
from app.models.supplier_portal import PO_CONFIRMED, PO_DELIVERED, PO_PLACED, PO_PROBLEM, SupplierPurchaseOrder
from app.services.field_operations import FieldOperationError, actor_label, capture_photos, plain_quantity, record

OPEN_ORDER_STATUSES = (PO_PLACED, PO_CONFIRMED, PO_PROBLEM)
RESOLUTIONS = {
    "REST_COMING": "The rest is coming — wait for the next delivery",
    "REPLACEMENT": "Replacement arranged with the supplier",
    "ACCEPT_CLOSE": "Accept what came and close the order",
}


class DeliveryError(FieldOperationError):
    pass


def get(organization_id: str, confirmation_id: int) -> Optional[DeliveryConfirmation]:
    row = db.session.get(DeliveryConfirmation, int(confirmation_id))
    return row if row is not None and row.organization_id == organization_id else None


def order_for_project(organization_id: str, project_id: int, order_id: int) -> Optional[SupplierPurchaseOrder]:
    order = db.session.get(SupplierPurchaseOrder, int(order_id))
    if order is None or order.organization_id != organization_id or order.project_id != int(project_id):
        return None
    return order


def open_orders(organization_id: str, project_id: int) -> list:
    return (SupplierPurchaseOrder.query.filter(SupplierPurchaseOrder.organization_id == organization_id,
                                               SupplierPurchaseOrder.project_id == project_id,
                                               SupplierPurchaseOrder.status.in_(OPEN_ORDER_STATUSES))
            .order_by(SupplierPurchaseOrder.scheduled_date.asc(), SupplierPurchaseOrder.id.asc()).all())


def confirmations_for_order(order: SupplierPurchaseOrder) -> list:
    return (DeliveryConfirmation.query.filter_by(order_id=order.id)
            .order_by(DeliveryConfirmation.confirmed_at.asc(), DeliveryConfirmation.id.asc()).all())


def open_exception_for_order(order: SupplierPurchaseOrder) -> Optional[DeliveryConfirmation]:
    return DeliveryConfirmation.query.filter_by(order_id=order.id, exception_status=EXCEPTION_OPEN).first()


def field_lines(order: SupplierPurchaseOrder) -> list:
    """The order's lines for the crew: description, quantity and unit only (never a price), with what has already
    been counted as received on earlier confirmations."""
    received = received_by_line(order)
    out = []
    for line in order.lines_json or []:
        number = int(line.get("number") or 0)
        ordered = Decimal(str(line.get("quantity") or "0"))
        got = received.get(number, Decimal("0"))
        out.append({"number": number, "description": line.get("description") or "", "unit": line.get("unit") or "",
                    "ordered": ordered, "received": got, "outstanding": max(ordered - got, Decimal("0"))})
    return out


def received_by_line(order: SupplierPurchaseOrder) -> dict:
    """Good quantity counted so far per order line (damaged pieces are not counted as received)."""
    totals = {}
    for row in confirmations_for_order(order):
        for line in row.lines_json or []:
            good = Decimal(str(line.get("received") or "0")) - Decimal(str(line.get("damaged") or "0"))
            totals[int(line["number"])] = totals.get(int(line["number"]), Decimal("0")) + max(good, Decimal("0"))
    return totals


def outstanding(order: SupplierPurchaseOrder) -> list:
    return [l for l in field_lines(order) if l["outstanding"] > 0]


def _qty(raw, label) -> Decimal:
    text = str(raw if raw is not None else "").strip().replace(",", "")
    if text == "":
        return Decimal("0")
    try:
        value = Decimal(text)
    except Exception:
        raise DeliveryError(f"{label}: enter a number.") from None
    if not value.is_finite() or value < 0:
        raise DeliveryError(f"{label} cannot be negative.")
    return value


def confirm(order: SupplierPurchaseOrder, user, form, files=()) -> tuple[DeliveryConfirmation, bool]:
    from app.services.build import normalize_client_uuid
    from app.services.supplier_hub import SupplierHubError, mark_order_delivered

    org = order.organization_id
    try:
        uuid = normalize_client_uuid(form.get("client_uuid"), field_name="client_uuid")
    except Exception:
        uuid = None
    if uuid:
        existing = DeliveryConfirmation.query.filter_by(organization_id=org, client_uuid=uuid).first()
        if existing is not None:
            return existing, False
    if order.status not in OPEN_ORDER_STATUSES:
        raise DeliveryError("This order is already closed (delivered or cancelled).")
    outcome = (form.get("outcome") or "").strip().upper()
    if outcome not in DELIVERY_OUTCOMES:
        raise DeliveryError("Choose Received, Short or Damaged.")
    lines = []
    any_short = any_damaged = False
    for line in field_lines(order):
        n = line["number"]
        if outcome == DELIVERY_RECEIVED and form.get(f"received_{n}") in (None, ""):
            got = line["outstanding"]
        else:
            got = _qty(form.get(f"received_{n}"), f"Line {n} received")
        damaged = _qty(form.get(f"damaged_{n}"), f"Line {n} damaged")
        if damaged > got:
            raise DeliveryError(f"Line {n}: more damaged than received.")
        if got - damaged < line["outstanding"]:
            any_short = True
        if damaged > 0:
            any_damaged = True
        lines.append({"number": n, "description": line["description"], "unit": line["unit"],
                      "ordered": str(line["ordered"]), "outstanding_before": str(line["outstanding"]),
                      "received": str(got), "damaged": str(damaged)})
    note = (form.get("note") or "").strip()[:2000] or None
    if outcome == DELIVERY_RECEIVED and (any_short or any_damaged):
        raise DeliveryError("Some quantities are not all there or are damaged. Choose Short or Damaged.")
    if outcome == DELIVERY_DAMAGED and not any_damaged:
        raise DeliveryError("Enter how many arrived damaged on the line(s).")
    if outcome == DELIVERY_SHORT and not any_short:
        raise DeliveryError("Every quantity is here. Choose Received.")
    if outcome != DELIVERY_RECEIVED and not note:
        raise DeliveryError("Add a short note for the office (what is missing or damaged).")
    from app.models import Project

    project = db.session.get(Project, order.project_id)
    event = capture_photos(project, files, note=f"Delivery {order.number}: {outcome.title()}")
    row = DeliveryConfirmation(
        organization_id=org, project_id=order.project_id, order_id=order.id, client_uuid=uuid, outcome=outcome,
        lines_json=lines, note=note, field_event_id=event.id if event else None,
        confirmed_by_user_id=getattr(user, "id", None), confirmed_by_name=actor_label(user),
        exception_status=EXCEPTION_OPEN if outcome != DELIVERY_RECEIVED else EXCEPTION_NONE)
    db.session.add(row)
    db.session.flush()
    summary = ", ".join(f"line {l['number']}: {plain_quantity(Decimal(l['received']))} of "
                        f"{plain_quantity(Decimal(l['outstanding_before']))} {l['unit']}"
                        + (f" ({plain_quantity(Decimal(l['damaged']))} damaged)" if Decimal(l['damaged']) else "")
                        for l in lines)
    record(org, RECORD_DELIVERY, row.id, outcome, actor=user, project_id=order.project_id,
           detail=f"{order.number}: {summary}" + (f" · {note}" if note else ""))
    db.session.commit()
    if outcome == DELIVERY_RECEIVED and not outstanding(order):
        if order.status == PO_CONFIRMED:
            try:
                mark_order_delivered(order, side="CONTRACTOR", user=user, note=f"Confirmed on site in Field by "
                                     f"{actor_label(user)}" + (f": {note}" if note else ""))
                record(org, RECORD_DELIVERY, row.id, "ORDER_DELIVERED", actor=user, project_id=order.project_id,
                       detail=f"{order.number} marked delivered")
                db.session.commit()
            except SupplierHubError:
                db.session.rollback()
        else:
            record(org, RECORD_DELIVERY, row.id, "WAITING_SUPPLIER_CONFIRMATION", actor=user,
                   project_id=order.project_id, detail=f"{order.number} arrived in full; the supplier has not "
                   "confirmed the order in CalibraytAI, so the office closes it")
            db.session.commit()
    return row, True


def exceptions(organization_id: str, *, project_id: Optional[int] = None, open_only: bool = True) -> list:
    query = DeliveryConfirmation.query.filter(DeliveryConfirmation.organization_id == organization_id,
                                              DeliveryConfirmation.exception_status != EXCEPTION_NONE)
    if open_only:
        query = query.filter(DeliveryConfirmation.exception_status == EXCEPTION_OPEN)
    if project_id:
        query = query.filter(DeliveryConfirmation.project_id == int(project_id))
    return query.order_by(DeliveryConfirmation.confirmed_at.desc()).all()


def recent(organization_id: str, *, project_id: Optional[int] = None, limit: int = 30) -> list:
    query = DeliveryConfirmation.query.filter_by(organization_id=organization_id)
    if project_id:
        query = query.filter_by(project_id=int(project_id))
    return query.order_by(DeliveryConfirmation.confirmed_at.desc()).limit(limit).all()


def resolve(row: DeliveryConfirmation, actor, *, resolution: str, note: str = "") -> DeliveryConfirmation:
    from app.services.supplier_hub import SupplierHubError, mark_order_delivered

    if row.exception_status != EXCEPTION_OPEN:
        raise DeliveryError("This delivery problem is already resolved.")
    if resolution not in RESOLUTIONS:
        raise DeliveryError("Choose how it was resolved.")
    text = " ".join((note or "").split())[:2000]
    if resolution == "ACCEPT_CLOSE" and not text:
        raise DeliveryError("Say why the order is closed with less than was ordered (the supplier sees the note).")
    order = row.order
    if resolution == "ACCEPT_CLOSE":
        if order.status == PO_CONFIRMED:
            try:
                mark_order_delivered(order, side="CONTRACTOR", user=actor,
                                     note=f"Closed with an exception: {text}")
            except SupplierHubError as exc:
                raise DeliveryError(str(exc)) from None
        elif order.status != PO_DELIVERED:
            raise DeliveryError("The supplier has not confirmed this order in CalibraytAI; it cannot be marked delivered.")
    row.exception_status = EXCEPTION_RESOLVED
    row.resolution = resolution
    row.resolution_note = text or None
    row.resolved_by_name = actor_label(actor)
    row.resolved_at = datetime.utcnow()
    record(row.organization_id, RECORD_DELIVERY, row.id, "RESOLVED", actor=actor, project_id=row.project_id,
           detail=f"{RESOLUTIONS[resolution]}" + (f": {text}" if text else ""))
    db.session.commit()
    return row


def order_state(order: SupplierPurchaseOrder) -> str:
    """Plain order status including what the site counted."""
    if order.status == PO_DELIVERED:
        return "Delivered"
    if open_exception_for_order(order) is not None:
        return "Delivery problem — waiting for the office"
    if confirmations_for_order(order) and outstanding(order):
        return "Part delivered — the rest is outstanding"
    return {PO_PLACED: "Ordered — waiting for the supplier to confirm", PO_CONFIRMED: "Ordered — confirmed",
            PO_PROBLEM: "Supplier reported a problem"}.get(order.status, order.status.title())

"""Receipts: Field Add Receipt → Project Receipts → Suzanne's Receipts Inbox → QuickBooks Online (25 Oct 2026).

Enter once: the worker photographs the receipt in Field (the existing capture, with its offline keep-and-retry),
optionally types the supplier and amount, and chooses the job or Shop / Company Expense. The same record is the
project's receipt, the office's inbox row and the QuickBooks Online transfer. The original image is never changed.

Office review (owner, System Administrator or office member with accounting access — the /accounting rule;
Field-only crew never): confirm or correct supplier, date, subtotal, tax and total and the job or company expense,
link a purchase order or an existing QuickBooks transaction, then Approve for QuickBooks. Approval queues ONE
transfer (app/services/quickbooks_online.py); "Synced" is shown only when QuickBooks confirms it.

A receipt is evidence for accounting. It does NOT add a cost to the project's costing (no direct cost actual is
made), so a material already on a purchase order is never counted twice in CalibraytAI.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from app import db
from app.models import Project
from app.models.build import FieldCaptureEvent, FieldCaptureOriginal
from app.models.field_operations import (
    QBO_TXN_TYPES,
    RECEIPT_NEEDS_ATTENTION,
    RECEIPT_NEW,
    RECEIPT_READY,
    RECEIPT_REVIEWED,
    RECEIPT_STATUSES,
    RECEIPT_SYNC_FAILED,
    RECEIPT_SYNCED,
    RECORD_RECEIPT,
    SCOPE_COMPANY,
    SCOPE_PROJECT,
    FieldReceipt,
)
from app.models.supplier_portal import SupplierPurchaseOrder
from app.services.field_operations import FieldOperationError, actor_label, parse_day, parse_money, record

EDITABLE = (RECEIPT_NEW, RECEIPT_NEEDS_ATTENTION, RECEIPT_REVIEWED, RECEIPT_READY, RECEIPT_SYNC_FAILED)
OPEN_FOR_OFFICE = (RECEIPT_NEW, RECEIPT_NEEDS_ATTENTION, RECEIPT_REVIEWED, RECEIPT_SYNC_FAILED)
WORKER_LABELS = {
    RECEIPT_NEW: "Sent to the office",
    RECEIPT_NEEDS_ATTENTION: "The office is checking it",
    RECEIPT_REVIEWED: "Checked by the office",
    RECEIPT_READY: "Approved",
    RECEIPT_SYNCED: "In QuickBooks",
    RECEIPT_SYNC_FAILED: "Approved — the office is finishing it",
}


class ReceiptError(FieldOperationError):
    pass


def _is_company(project) -> bool:
    from app.services.time_entry import is_company_time_project

    return bool(project is not None and is_company_time_project(project))


def receipt_for(organization_id: str, receipt_id: int) -> Optional[FieldReceipt]:
    row = db.session.get(FieldReceipt, int(receipt_id))
    if row is None or row.organization_id != organization_id:
        return None
    return row


# ------------------------------------------------------------------------------------------------- Field side
def register(organization_id: str, user, *, client_capture_uuid: str, supplier: str = "", amount=None,
             note: str = "", visible_project_ids=None) -> tuple[FieldReceipt, bool]:
    """Make the uploaded Field capture a receipt. Idempotent on the capture: a phone that sends it again (after a
    lost connection) gets the same receipt back. Only the person who took the photo may do this."""
    from app.services.build import normalize_client_uuid

    try:
        uuid = normalize_client_uuid(client_capture_uuid, field_name="client_capture_uuid")
    except Exception:
        raise ReceiptError("This receipt could not be matched to its photo. Try again.") from None
    if not uuid:
        raise ReceiptError("This receipt could not be matched to its photo. Try again.")
    existing = FieldReceipt.query.filter_by(organization_id=organization_id, client_capture_uuid=uuid).first()
    if existing is not None:
        if existing.submitted_by_user_id != getattr(user, "id", None):
            raise ReceiptError("This receipt belongs to someone else.")
        return existing, False
    event = FieldCaptureEvent.query.filter_by(organization_id=organization_id, client_capture_uuid=uuid).first()
    if event is None:
        raise ReceiptError("The receipt photo has not reached the office yet. It will be sent again.")
    if event.user_id != getattr(user, "id", None):
        raise ReceiptError("This receipt belongs to someone else.")
    if visible_project_ids is not None and event.project_id not in visible_project_ids:
        raise ReceiptError("Choose one of your jobs or Shop / Company Expense.")
    image = (FieldCaptureOriginal.query.filter_by(field_event_id=event.id, kind="image")
             .order_by(FieldCaptureOriginal.id.asc()).first())
    if image is None:
        raise ReceiptError("Take a photo of the receipt before saving.")
    project = db.session.get(Project, event.project_id)
    entered_amount = parse_money(amount, "Amount")
    receipt = FieldReceipt(
        organization_id=organization_id, project_id=project.id,
        expense_scope=SCOPE_COMPANY if _is_company(project) else SCOPE_PROJECT,
        field_event_id=event.id, image_original_id=image.id, client_capture_uuid=uuid,
        submitted_by_user_id=getattr(user, "id", None), submitted_by_name=actor_label(user),
        submitted_at=event.created_at or datetime.utcnow(),
        entered_supplier=(supplier or "").strip()[:160] or None, entered_amount=entered_amount,
        entered_note=(note or "").strip()[:2000] or None, status=RECEIPT_NEW)
    db.session.add(receipt)
    db.session.flush()
    record(organization_id, RECORD_RECEIPT, receipt.id, "SUBMITTED", actor=user, project_id=project.id,
           detail=("Shop / Company expense" if receipt.expense_scope == SCOPE_COMPANY else project.name)
           + (f" · {receipt.entered_supplier}" if receipt.entered_supplier else "")
           + (f" · ${entered_amount}" if entered_amount is not None else ""))
    db.session.commit()
    return receipt, True


def worker_receipts(organization_id: str, user_id: int, limit: int = 12) -> list:
    return (FieldReceipt.query.filter_by(organization_id=organization_id, submitted_by_user_id=user_id)
            .order_by(FieldReceipt.submitted_at.desc(), FieldReceipt.id.desc()).limit(limit).all())


def worker_label(receipt: FieldReceipt) -> str:
    return WORKER_LABELS.get(receipt.status, receipt.status_label)


# ------------------------------------------------------------------------------------------------ office side
def inbox(organization_id: str, *, status: Optional[str] = None, project_id: Optional[int] = None) -> list:
    query = FieldReceipt.query.filter_by(organization_id=organization_id)
    if status in RECEIPT_STATUSES:
        query = query.filter_by(status=status)
    if project_id:
        query = query.filter_by(project_id=int(project_id))
    return query.order_by(FieldReceipt.submitted_at.desc(), FieldReceipt.id.desc()).all()


def counts(organization_id: str) -> dict:
    rows = db.session.query(FieldReceipt.status, db.func.count(FieldReceipt.id)).filter(
        FieldReceipt.organization_id == organization_id).group_by(FieldReceipt.status).all()
    out = {s: 0 for s in RECEIPT_STATUSES}
    out.update({s: n for s, n in rows})
    return out


def project_receipts(organization_id: str, project_id: int) -> list:
    return inbox(organization_id, project_id=project_id)


def project_choices(organization_id: str) -> list:
    """The jobs a receipt can belong to, and Shop / Company Expense (the company-time project) last."""
    from app.services.shared_api import list_current_operating_projects
    from app.services.time_entry import get_company_time_project

    rows = [p for p in list_current_operating_projects(organization_id) if not _is_company(p)]
    company = get_company_time_project(organization_id)
    if company is not None:
        rows.append(company)
    return rows


def purchase_order_choices(receipt: FieldReceipt) -> list:
    return (SupplierPurchaseOrder.query.filter_by(organization_id=receipt.organization_id,
                                                  project_id=receipt.project_id)
            .order_by(SupplierPurchaseOrder.placed_at.desc()).all())


def _require_editable(receipt: FieldReceipt):
    if receipt.status == RECEIPT_SYNCED:
        raise ReceiptError("This receipt is already in QuickBooks. Change it in QuickBooks; the history here is kept.")
    transfer = getattr(receipt, "qbo_transfer", None)
    if transfer is not None and transfer.status == "SENT":
        raise ReceiptError("This receipt was sent to QuickBooks and the answer is not known yet. Press Retry first: "
                           "CalibraytAI checks QuickBooks before doing anything again.")
    if transfer is not None and transfer.qbo_txn_id:
        raise ReceiptError(f"QuickBooks already has this receipt's {transfer.qbo_txn_type} {transfer.qbo_txn_id}; only "
                           "the image still has to be attached. Press Retry. Change the amounts in QuickBooks.")


def review(receipt: FieldReceipt, actor, form) -> FieldReceipt:
    """Confirm or correct what the receipt says. Saves as Reviewed (or back to Reviewed if it was approved)."""
    _require_editable(receipt)
    org = receipt.organization_id
    changes = []

    def set_field(name, value, label):
        old = getattr(receipt, name)
        if old != value:
            setattr(receipt, name, value)
            changes.append(f"{label}: {'' if old is None else old} → {'' if value is None else value}")

    vendor = (form.get("vendor_name") or "").strip()[:160] or None
    day = parse_day(form.get("receipt_date"), "Receipt date", not_future=True)
    subtotal = parse_money(form.get("subtotal"), "Subtotal")
    tax = parse_money(form.get("tax_amount"), "Tax")
    total = parse_money(form.get("total"), "Total")
    if total is None and subtotal is not None:
        total = subtotal + (tax or Decimal("0.00"))
    if subtotal is None and total is not None:
        subtotal = total - (tax or Decimal("0.00"))
        if subtotal < 0:
            raise ReceiptError("The tax is more than the total. Check the amounts.")
    if subtotal is not None and total is not None and subtotal + (tax or Decimal("0.00")) != total:
        raise ReceiptError(f"Subtotal ${subtotal} plus tax ${tax or Decimal('0.00')} is not the total ${total}. "
                           "Check the amounts on the receipt.")
    project_id = form.get("project_id")
    if project_id:
        project = db.session.get(Project, int(project_id))
        if project is None or project.organization_id != org:
            raise ReceiptError("Choose a job of this company or Shop / Company Expense.")
        if project.id != receipt.project_id:
            if receipt.purchase_order_id:
                receipt.purchase_order_id = None
                changes.append("Purchase order link removed (different job)")
            set_field("project_id", project.id, "Job")
            receipt.expense_scope = SCOPE_COMPANY if _is_company(project) else SCOPE_PROJECT
    po_id = (form.get("purchase_order_id") or "").strip()
    if po_id:
        order = db.session.get(SupplierPurchaseOrder, int(po_id))
        if order is None or order.organization_id != org or order.project_id != receipt.project_id:
            raise ReceiptError("Choose a purchase order of this job.")
        set_field("purchase_order_id", order.id, "Purchase order")
    elif "purchase_order_id" in form:
        set_field("purchase_order_id", None, "Purchase order")
    txn_type = (form.get("existing_qbo_txn_type") or "").strip() or None
    txn_id = (form.get("existing_qbo_txn_id") or "").strip()[:40] or None
    if txn_id and txn_type not in QBO_TXN_TYPES:
        raise ReceiptError("Say whether the existing QuickBooks transaction is an Expense or a Bill.")
    if txn_id and not txn_id.isdigit():
        raise ReceiptError("The QuickBooks transaction number is the number in its web address (digits only).")
    set_field("existing_qbo_txn_type", txn_type if txn_id else None, "Existing QuickBooks transaction type")
    set_field("existing_qbo_txn_id", txn_id, "Existing QuickBooks transaction")
    set_field("vendor_name", vendor, "Supplier")
    set_field("receipt_date", day, "Date")
    set_field("subtotal", subtotal, "Subtotal")
    set_field("tax_amount", tax, "Tax")
    set_field("total", total, "Total")
    receipt.status = RECEIPT_REVIEWED
    receipt.attention_reason = None
    receipt.reviewed_by_name = actor_label(actor)
    receipt.reviewed_at = datetime.utcnow()
    if receipt.approved_at is not None:
        receipt.approved_at = None
        receipt.approved_by_name = None
        receipt.approved_by_user_id = None
        changes.append("Approval withdrawn: approve again to send")
    from app.services import quickbooks_online as qbo

    qbo.reset_for_changes(receipt, actor)
    record(org, RECORD_RECEIPT, receipt.id, "REVIEWED", actor=actor, project_id=receipt.project_id,
           detail="; ".join(changes) or "Checked; nothing changed")
    db.session.commit()
    return receipt


def flag(receipt: FieldReceipt, actor, reason: str) -> FieldReceipt:
    _require_editable(receipt)
    text = " ".join((reason or "").split())
    if not text:
        raise ReceiptError("Say what needs attention (for example: amount not readable).")
    receipt.status = RECEIPT_NEEDS_ATTENTION
    receipt.attention_reason = text[:2000]
    record(receipt.organization_id, RECORD_RECEIPT, receipt.id, "NEEDS_ATTENTION", actor=actor,
           project_id=receipt.project_id, detail=text)
    db.session.commit()
    return receipt


def approval_blockers(receipt: FieldReceipt) -> list:
    out = []
    if not receipt.vendor_name:
        out.append("the supplier")
    if receipt.receipt_date is None:
        out.append("the receipt date")
    if receipt.total is None or receipt.subtotal is None:
        out.append("the subtotal and total")
    elif receipt.total <= 0:
        out.append("a total above zero")
    return out


def approve(receipt: FieldReceipt, actor) -> dict:
    """Approve for the accounting handoff: Ready for QuickBooks, one transfer queued, sent now when connected."""
    from app.services import quickbooks_online as qbo

    _require_editable(receipt)
    if receipt.status == RECEIPT_READY:
        raise ReceiptError("This receipt is already approved.")
    missing = approval_blockers(receipt)
    if missing:
        raise ReceiptError("Before approving, confirm " + ", ".join(missing) + ". Press Save review first.")
    receipt.status = RECEIPT_READY
    receipt.attention_reason = None
    receipt.approved_by_user_id = getattr(actor, "id", None)
    receipt.approved_by_name = actor_label(actor)
    receipt.approved_at = datetime.utcnow()
    transfer = qbo.ensure_transfer(receipt)
    record(receipt.organization_id, RECORD_RECEIPT, receipt.id, "APPROVED", actor=actor,
           project_id=receipt.project_id,
           detail=f"{receipt.vendor_name} · {receipt.receipt_date} · ${receipt.total} · sync id {transfer.sync_id}")
    db.session.commit()
    result = {"sent": False, "transfer": transfer, "message": None}
    if qbo.can_send(receipt.organization_id) and qbo.connection_auto_send(receipt.organization_id):
        qbo.send_transfer(transfer, actor=actor)
        result["sent"] = True
    else:
        qbo.note_waiting(transfer)
    db.session.refresh(receipt)
    result["message"] = qbo.outcome_message(receipt)
    return result


def history(receipt: FieldReceipt) -> list:
    from app.services.field_operations import history as h

    return h(receipt.organization_id, RECORD_RECEIPT, receipt.id)

"""Accounting alongside QuickBooks Online (Joel, 21 Oct 2026: QuickBooks is a V1 requirement).

CalibraytAI stays the commercial record; QuickBooks stays the books. What this does, without any
QuickBooks credential:

- Invoices: made from an Accepted proposal (deposit / progress / final, as an amount or a percent of the
  proposal before tax) or an Approved change order, with the project's HST. Numbered INV-YYYY-NNNN.
- Export files QuickBooks Online imports (Settings → Import data): customers, suppliers, invoices
  (one row per invoice; QBO Canada needs Invoice number, Customer, Invoice date, Due date, Item amount,
  Item tax code), and bills drafted from confirmed or delivered purchase orders. Purchase orders have no
  QBO import: they come as a list to enter by hand.
- No duplicates: each record has a stable CalibraytAI key; a record already exported is left out of the
  next file unless the office deliberately includes it again (with a reason, kept in the history).
- Reconciliation: upload QuickBooks' Invoice List report (CSV). Matched / amount differs / not in
  QuickBooks / not in CalibraytAI / in QuickBooks twice; payment status comes from the open balance.
- Every export, import, invoice action and correction is in accounting_events (append-only).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from datetime import date, datetime, timedelta
from app.services.local_time import local_date, local_today
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Dict, List, Optional

from app import db
from app.models.accounting import (
    EVENT_CORRECTION,
    EVENT_EXPORT,
    EVENT_IMPORT,
    EVENT_INVOICE,
    INVOICE_DRAFT,
    INVOICE_EXPORTED,
    INVOICE_KIND_CHANGE_ORDER,
    INVOICE_KIND_FINAL,
    INVOICE_KINDS,
    INVOICE_PAID,
    INVOICE_PARTLY_PAID,
    INVOICE_VOID,
    RECORD_BILL,
    RECORD_CUSTOMER,
    RECORD_INVOICE,
    RECORD_PURCHASE_ORDER,
    RECORD_VENDOR,
    AccountingEvent,
    AccountingExportRecord,
    CustomerInvoice,
)

CENT = Decimal("0.01")
QBO_HST_CODE = "HST ON"  # QuickBooks Online Canada's Ontario HST code; mapped once during import
DEFAULT_TERMS_DAYS = 30
MAX_INVOICES_PER_FILE = 100  # QuickBooks Online: up to 100 invoices per import
MAX_REPORT_BYTES = 5 * 1024 * 1024


class AccountingError(ValueError):
    pass


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENT, rounding=ROUND_HALF_UP)


def _actor(user) -> str:
    name = (getattr(user, "display_name", None) or getattr(user, "email", None) or "").strip()
    if not name:
        raise AccountingError("Sign in first.")
    return name[:160]


def _event(org, kind, subject, user, *, record_key=None, filename=None, content=None, rows=None, detail=None, note=None):
    db.session.add(AccountingEvent(
        organization_id=org, kind=kind, subject=subject, record_key=record_key, filename=filename,
        file_sha256=hashlib.sha256(content).hexdigest() if content else None, row_count=rows,
        detail_json=detail, note=note, actor_user_id=getattr(user, "id", None), actor_name=_actor(user),
        occurred_at=datetime.utcnow()))


def history(org, limit=100):
    return (AccountingEvent.query.filter_by(organization_id=org)
            .order_by(AccountingEvent.id.desc()).limit(limit).all())


# ------------------------------------------------------------------ invoices


def _next_number(org) -> str:
    year = local_today().year
    prefix = f"INV-{year}-"
    count = CustomerInvoice.query.filter(CustomerInvoice.organization_id == org,
                                         CustomerInvoice.number.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:04d}"


def job_reference(project) -> str:
    number = (getattr(project, "project_number", None) or "").strip()
    return f"{number} {project.name}".strip() if number else project.name


def accepted_proposals(org, project_id):
    from app.models import Estimate, Proposal

    return (Proposal.query.join(Estimate, Proposal.estimate_id == Estimate.id)
            .filter(Proposal.organization_id == org, Estimate.project_id == project_id, Proposal.status == "Accepted")
            .order_by(Proposal.id.desc()).all())


def approved_change_orders(org, project_id):
    from app.project_controls.models import ChangeOrder

    rows = ChangeOrder.query.filter_by(project_id=project_id).filter(ChangeOrder.status.in_(("Approved", "Invoiced"))).all()
    return [c for c in rows if getattr(c.project, "organization_id", org) == org]


def _proposal_subtotal_and_tax(proposal):
    """The contract price before HST is the proposal's total less its HST (the proposal's `subtotal` is
    before overhead and profit, so it is not the selling price)."""
    total = _money(proposal.total)
    tax = _money(proposal.tax_amount)
    return total - tax, Decimal(str(proposal.tax_percent or 0))


def _change_order_amounts(change_order):
    """A change order's price before HST is its subtotal plus markup; its HST is its own `tax`."""
    before_tax = _money(change_order.total) - _money(change_order.tax)
    return before_tax, Decimal(str(change_order.tax_percent or 0)), _money(change_order.tax)


def create_invoice(org, project, *, user, proposal_id=None, change_order_id=None, kind=None, amount=None,
                   percent=None, description="", invoice_date=None, terms_days=DEFAULT_TERMS_DAYS) -> CustomerInvoice:
    """One invoice from an Accepted proposal (an amount or a percent of it before tax) or an Approved
    change order (its full amount). HST follows the source document's rate."""
    actor = _actor(user)
    pct = None
    if project is None or project.organization_id != org:
        raise AccountingError("Choose one of your projects.")
    from app.services.time_entry import raise_if_company_time

    raise_if_company_time(project, AccountingError)  # Shop / Company Work is never invoiced
    proposal = change_order = None
    if change_order_id:
        change_order = next((c for c in approved_change_orders(org, project.id) if c.id == int(change_order_id)), None)
        if change_order is None:
            raise AccountingError("Choose an approved change order on this project.")
        if CustomerInvoice.query.filter(CustomerInvoice.organization_id == org,
                                        CustomerInvoice.change_order_id == change_order.id,
                                        CustomerInvoice.status != INVOICE_VOID).first():
            raise AccountingError("This change order is already invoiced.")
        subtotal, tax_percent, co_tax = _change_order_amounts(change_order)
        kind = INVOICE_KIND_CHANGE_ORDER
        text = description or f"Change order {getattr(change_order, 'number', change_order.id)}: {change_order.title}"
    else:
        proposal = next((p for p in accepted_proposals(org, project.id) if p.id == int(proposal_id or 0)), None)
        if proposal is None:
            raise AccountingError("Choose an accepted proposal on this project.")
        if kind not in INVOICE_KINDS or kind == INVOICE_KIND_CHANGE_ORDER:
            raise AccountingError("Choose deposit, progress or final.")
        contract, tax_percent = _proposal_subtotal_and_tax(proposal)
        invoiced = sum((_money(i.subtotal) for i in CustomerInvoice.query.filter(
            CustomerInvoice.organization_id == org, CustomerInvoice.proposal_id == proposal.id,
            CustomerInvoice.status != INVOICE_VOID).all()), Decimal("0"))
        if percent not in (None, ""):
            try:
                pct = Decimal(str(percent))
            except InvalidOperation:
                raise AccountingError("The percent must be a number.")
            if not Decimal("0") < pct <= Decimal("100"):
                raise AccountingError("The percent must be more than 0 and at most 100.")
            subtotal = (contract * pct / 100).quantize(CENT, rounding=ROUND_HALF_UP)
        elif amount in (None, "") and kind == INVOICE_KIND_FINAL:
            subtotal = contract - invoiced  # the final invoice is what is left
        else:
            try:
                subtotal = _money(str(amount).replace(",", "").replace("$", "").strip())
            except InvalidOperation:
                raise AccountingError("The amount must be a number.")
        if subtotal <= 0:
            raise AccountingError("Enter an amount or a percent.")
        if invoiced + subtotal > contract:
            raise AccountingError(f"That is more than is left to invoice on this proposal (${contract - invoiced:,.2f} before HST).")
        text = description or f"{kind.title()} on proposal {getattr(proposal, 'proposal_number', proposal.id)}"
    if subtotal <= 0:
        raise AccountingError("The amount must be more than zero.")
    # A change order is invoiced whole, so its own HST figure is used; part of a proposal is taxed at its rate.
    tax = co_tax if change_order is not None else (subtotal * tax_percent / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    day = invoice_date or local_today()
    invoice = CustomerInvoice(
        organization_id=org, project_id=project.id, client_id=project.client_id,
        proposal_id=proposal.id if proposal else None, change_order_id=change_order.id if change_order else None,
        number=_next_number(org), kind=kind, description=text[:2000],
        percent_of_contract=pct if proposal and pct is not None else None, subtotal=subtotal,
        tax_percent=tax_percent, tax_code=QBO_HST_CODE if tax_percent else "Exempt", tax_amount=tax,
        total=subtotal + tax, invoice_date=day, due_date=day + timedelta(days=int(terms_days)), status=INVOICE_DRAFT,
        created_by_user_id=getattr(user, "id", None), created_by_name=actor)
    db.session.add(invoice)
    db.session.flush()
    _event(org, EVENT_INVOICE, "created", user, record_key=invoice.number,
           detail={"subtotal": str(subtotal), "tax": str(tax), "total": str(invoice.total), "job": job_reference(project)})
    db.session.commit()
    return invoice


def void_invoice(org, invoice, *, user, reason):
    reason = " ".join((reason or "").split())
    if not reason:
        raise AccountingError("Say why the invoice is void.")
    if invoice.organization_id != org:
        raise AccountingError("Not found.")
    invoice.status = INVOICE_VOID
    invoice.void_reason = reason[:500]
    _event(org, EVENT_INVOICE, "voided", user, record_key=invoice.number, note=reason)
    db.session.commit()


def invoices(org, project_id=None):
    q = CustomerInvoice.query.filter_by(organization_id=org)
    if project_id:
        q = q.filter_by(project_id=project_id)
    return q.order_by(CustomerInvoice.id.desc()).all()


# ------------------------------------------------------------------ exports


def _sha(row) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()


def _register(org, record_type, key, ref, row, amount, user) -> str:
    """Record that a row went into a file. Returns 'new' or 'again'."""
    existing = AccountingExportRecord.query.filter_by(organization_id=org, record_type=record_type, record_key=key).first()
    now = datetime.utcnow()
    if existing is None:
        db.session.add(AccountingExportRecord(organization_id=org, record_type=record_type, record_key=key,
                                              quickbooks_ref=ref[:255], amount=amount, content_sha256=_sha(row),
                                              export_count=1, first_exported_at=now, last_exported_at=now,
                                              last_exported_by_name=_actor(user)))
        return "new"
    existing.export_count += 1
    existing.last_exported_at = now
    existing.last_exported_by_name = _actor(user)
    existing.content_sha256 = _sha(row)
    existing.amount = amount
    return "again"


def _already(org, record_type) -> set:
    if record_type == RECORD_TIME:
        return _time_keys_exported(org)
    return {r.record_key for r in AccountingExportRecord.query.filter_by(organization_id=org, record_type=record_type).all()}


def _csv(header, rows) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(header)
    for r in rows:
        w.writerow([r.get(h, "") for h in header])
    return buf.getvalue().encode("utf-8-sig")  # Excel and QuickBooks read the BOM as UTF-8


def _client_row(client) -> dict:
    return {"Name": client.name, "Company": getattr(client, "company", "") or "", "Email": getattr(client, "email", "") or "",
            "Phone": getattr(client, "phone", "") or "", "Street": getattr(client, "address", "") or "",
            "City": getattr(client, "city", "") or "", "Province": getattr(client, "province", "") or "",
            "Postal Code": getattr(client, "postal_code", "") or "", "Country": "Canada",
            "Notes": f"CalibraytAI customer C{client.id}"}


CUSTOMER_HEADER = ["Name", "Company", "Email", "Phone", "Street", "City", "Province", "Postal Code", "Country", "Notes"]
VENDOR_HEADER = ["Name", "Company", "Email", "Phone", "Street", "City", "Province", "Postal Code", "Country", "Notes"]
INVOICE_HEADER = ["InvoiceNo", "Customer", "InvoiceDate", "DueDate", "Terms", "Memo", "Item(Product/Service)",
                  "ItemDescription", "ItemQuantity", "ItemRate", "ItemAmount", "ItemTaxCode", "ItemTaxAmount", "Currency"]
BILL_HEADER = ["BillNo", "Supplier", "BillDate", "DueDate", "Terms", "Memo", "Account", "LineDescription",
               "LineAmount", "LineTaxCode", "LineTaxAmount", "Currency"]
PO_HEADER = ["PO number", "Supplier", "Job", "Placed", "Status", "Delivery", "Amount before tax", "Lines"]
DATE_FORMAT = "%d/%m/%Y"  # choose dd/MM/yyyy when QuickBooks asks for the date format


def preview(org, kind, *, include_exported=False) -> Dict:
    """Rows that would go into the next file of this kind, and which were exported before."""
    builders = {"customers": _customer_rows, "suppliers": _vendor_rows, "invoices": _invoice_rows,
                "bills": _bill_rows, "purchase_orders": _po_rows, "time": _time_rows}
    if kind not in builders:
        raise AccountingError("Unknown export.")
    record_type, header, rows = builders[kind](org)
    done = _already(org, record_type)
    fresh = [r for r in rows if r["_key"] not in done]
    again = [r for r in rows if r["_key"] in done]
    chosen = rows if include_exported else fresh
    if kind == "invoices" and len({r["InvoiceNo"] for r in chosen}) > MAX_INVOICES_PER_FILE:
        chosen = [r for r in chosen if r["InvoiceNo"] in sorted({x["InvoiceNo"] for x in chosen})[:MAX_INVOICES_PER_FILE]]
    result = {"kind": kind, "record_type": record_type, "header": header, "rows": chosen, "fresh": fresh, "again": again}
    if kind == "time":
        result["replaced"] = _time_replaced_after_export(org, done)
        result["hours"] = sum((Decimal(r["Hours"]) for r in chosen), Decimal("0"))
    return result


def export(org, kind, *, user, include_exported=False, reason="") -> tuple:
    """Build the file and record every row in it. Re-including exported rows needs a reason."""
    p = preview(org, kind, include_exported=include_exported)
    if include_exported and p["again"] and not " ".join((reason or "").split()):
        raise AccountingError("Say why records already in QuickBooks go into this file again.")
    if not p["rows"]:
        raise AccountingError("Nothing new to export. Everything here is already in a QuickBooks file.")
    outcome = {"new": 0, "again": 0}
    for r in p["rows"]:
        if p["record_type"] == RECORD_TIME:
            # Time has no export-record row (no schema change): the export event's keys are the record.
            outcome["again" if r in p["again"] else "new"] += 1
            continue
        outcome[_register(org, p["record_type"], r["_key"], r["_ref"], {h: r.get(h) for h in p["header"]}, r.get("_amount"), user)] += 1
        if p["record_type"] == RECORD_INVOICE:
            inv = CustomerInvoice.query.filter_by(organization_id=org, number=r["InvoiceNo"]).first()
            if inv is not None and inv.status == INVOICE_DRAFT:
                inv.status = INVOICE_EXPORTED
    content = _csv(p["header"], p["rows"])
    filename = f"calibraytai-{kind}-{datetime.utcnow():%Y%m%d-%H%M%S}.csv"
    _event(org, EVENT_EXPORT, kind, user, filename=filename, content=content, rows=len(p["rows"]),
           detail={"new": outcome["new"], "again": outcome["again"], "keys": [r["_key"] for r in p["rows"]]},
           note=" ".join((reason or "").split()) or None)
    db.session.commit()
    return filename, content, outcome


def _customer_rows(org):
    from app.models import Client
    from app.services.time_entry import company_time_client_id

    own_company = company_time_client_id(org)  # holds shop time; never a QuickBooks customer
    rows = []
    for c in Client.query.filter_by(organization_id=org).order_by(Client.name).all():
        if own_company is not None and c.id == own_company:
            continue
        row = _client_row(c)
        row.update(_key=f"C{c.id}", _ref=c.name)
        rows.append(row)
    return RECORD_CUSTOMER, CUSTOMER_HEADER, rows


def _vendor_rows(org):
    from app.models.supplier_catalogue import ContractorSupplierAccount

    rows, seen = [], set()
    for a in ContractorSupplierAccount.query.filter_by(organization_id=org).all():
        s = a.supplier
        if s is None or s.id in seen:
            continue
        seen.add(s.id)
        rows.append({"Name": s.legal_name, "Company": s.legal_name, "Country": "Canada",
                     "Notes": f"CalibraytAI supplier S{s.id}", "_key": f"S{s.id}", "_ref": s.legal_name})
    return RECORD_VENDOR, VENDOR_HEADER, rows


def _invoice_rows(org):
    rows = []
    for inv in CustomerInvoice.query.filter(CustomerInvoice.organization_id == org,
                                            CustomerInvoice.status != INVOICE_VOID).order_by(CustomerInvoice.id).all():
        job = job_reference(inv.project)
        rows.append({"InvoiceNo": inv.number, "Customer": inv.client.name,
                     "InvoiceDate": inv.invoice_date.strftime(DATE_FORMAT), "DueDate": inv.due_date.strftime(DATE_FORMAT),
                     "Terms": f"Net {(inv.due_date - inv.invoice_date).days}", "Memo": f"Job: {job}",
                     "Item(Product/Service)": "Construction services", "ItemDescription": f"{inv.description} (Job: {job})",
                     "ItemQuantity": "1", "ItemRate": str(inv.subtotal), "ItemAmount": str(inv.subtotal),
                     "ItemTaxCode": inv.tax_code, "ItemTaxAmount": str(inv.tax_amount), "Currency": "CAD",
                     "_key": inv.number, "_ref": inv.number, "_amount": inv.total})
    return RECORD_INVOICE, INVOICE_HEADER, rows


def _po_amount(order) -> Decimal:
    return _money(order.total)  # sum of the order lines, before tax


def _supplier_name(order) -> str:
    from app.models.supplier_catalogue import Supplier

    supplier = db.session.get(Supplier, order.supplier_id)
    return supplier.legal_name if supplier else f"Supplier {order.supplier_id}"


def _orders(org, statuses):
    from app.models.supplier_portal import SupplierPurchaseOrder

    return (SupplierPurchaseOrder.query.filter(SupplierPurchaseOrder.organization_id == org,
                                               SupplierPurchaseOrder.status.in_(statuses))
            .order_by(SupplierPurchaseOrder.id).all())


def _bill_rows(org):
    """Draft bills from confirmed or delivered orders: compare with the supplier's own invoice before
    importing. HST is the Ontario 13 % on the order amount."""
    from app.models import Project

    rows = []
    for o in _orders(org, ("CONFIRMED", "DELIVERED")):
        amount = _po_amount(o)
        if amount <= 0:
            continue
        project = db.session.get(Project, o.project_id)
        tax = (amount * Decimal("13") / 100).quantize(CENT, rounding=ROUND_HALF_UP)
        day = o.scheduled_date or o.delivery_date or (local_date(o.placed_at) if o.placed_at else local_today())
        rows.append({"BillNo": o.number, "Supplier": _supplier_name(o), "BillDate": day.strftime(DATE_FORMAT),
                     "DueDate": (day + timedelta(days=30)).strftime(DATE_FORMAT), "Terms": "Net 30",
                     "Memo": f"Job: {job_reference(project)} · PO {o.number}", "Account": "Job Materials",
                     "LineDescription": f"Materials, PO {o.number} (Job: {job_reference(project)})",
                     "LineAmount": str(amount), "LineTaxCode": QBO_HST_CODE, "LineTaxAmount": str(tax), "Currency": "CAD",
                     "_key": o.number, "_ref": o.number, "_amount": amount + tax})
    return RECORD_BILL, BILL_HEADER, rows


def _po_rows(org):
    from app.models import Project

    rows = []
    for o in _orders(org, ("PLACED", "CONFIRMED", "DELIVERED", "PROBLEM")):
        project = db.session.get(Project, o.project_id)
        rows.append({"PO number": o.number, "Supplier": _supplier_name(o), "Job": job_reference(project),
                     "Placed": o.placed_at.strftime(DATE_FORMAT) if o.placed_at else "", "Status": o.status.title(),
                     "Delivery": (o.scheduled_date or o.delivery_date).strftime(DATE_FORMAT) if (o.scheduled_date or o.delivery_date) else "",
                     "Amount before tax": str(_po_amount(o)), "Lines": len(o.lines_json or []),
                     "_key": o.number, "_ref": o.number, "_amount": _po_amount(o)})
    return RECORD_PURCHASE_ORDER, PO_HEADER, rows


# ------------------------------------------------------------------ reconciliation


_NUM_HEADERS = ("num", "no.", "invoice no", "invoice number", "invoiceno", "number", "no")
_CUSTOMER_HEADERS = ("customer", "name", "customer full name")
_AMOUNT_HEADERS = ("amount", "total", "total amount")
_OPEN_HEADERS = ("open balance", "balance", "open_balance", "balance due")
_TYPE_HEADERS = ("transaction type", "type")


def _find(header, names):
    lowered = [(h or "").strip().lower() for h in header]
    for n in names:
        if n in lowered:
            return lowered.index(n)
    return None


def _decimal(text) -> Optional[Decimal]:
    t = (text or "").strip().replace("$", "").replace(",", "").replace("CA", "")
    if t.startswith("(") and t.endswith(")"):
        t = "-" + t[1:-1]
    if not t:
        return None
    try:
        return Decimal(t).quantize(CENT)
    except InvalidOperation:
        return None


def reconcile(org, *, filename, content: bytes, user) -> Dict:
    """Read QuickBooks' Invoice List (or Transaction List by Customer) CSV and compare with CalibraytAI's
    exported invoices. Updates payment status from the open balance. Nothing is deleted or rewritten."""
    if not content:
        raise AccountingError("Choose the CSV you exported from QuickBooks.")
    if len(content) > MAX_REPORT_BYTES:
        raise AccountingError("The file is larger than 5 MB.")
    text = content.decode("utf-8-sig", errors="replace")
    reader = list(csv.reader(io.StringIO(text)))
    header_at = next((i for i, row in enumerate(reader[:15]) if _find(row, _NUM_HEADERS) is not None
                      and _find(row, _AMOUNT_HEADERS) is not None), None)
    if header_at is None:
        raise AccountingError("This does not look like a QuickBooks invoice list: it needs Num and Amount columns.")
    header = reader[header_at]
    i_num, i_amt = _find(header, _NUM_HEADERS), _find(header, _AMOUNT_HEADERS)
    i_open, i_cust, i_type = _find(header, _OPEN_HEADERS), _find(header, _CUSTOMER_HEADERS), _find(header, _TYPE_HEADERS)
    seen: Dict[str, List[dict]] = {}
    for row in reader[header_at + 1:]:
        if len(row) <= max(i_num, i_amt):
            continue
        if i_type is not None and len(row) > i_type and row[i_type].strip() and row[i_type].strip().lower() != "invoice":
            continue
        num = row[i_num].strip()
        if not num:
            continue
        seen.setdefault(num, []).append({"amount": _decimal(row[i_amt]),
                                         "open": _decimal(row[i_open]) if i_open is not None and len(row) > i_open else None,
                                         "customer": row[i_cust].strip() if i_cust is not None and len(row) > i_cust else ""})
    ours = {i.number: i for i in CustomerInvoice.query.filter(CustomerInvoice.organization_id == org,
                                                                  CustomerInvoice.status != INVOICE_VOID).all()}
    exported = _already(org, RECORD_INVOICE)
    result = {"matched": [], "differs": [], "missing_in_quickbooks": [], "unknown_in_calibraytai": [], "duplicates": [],
              "paid": [], "partly_paid": []}
    for num, hits in seen.items():
        if len(hits) > 1:
            result["duplicates"].append({"number": num, "count": len(hits)})
        inv = ours.get(num)
        if inv is None:
            result["unknown_in_calibraytai"].append({"number": num, "amount": str(hits[0]["amount"])})
            continue
        qb = hits[0]
        if qb["amount"] is None or abs(qb["amount"] - _money(inv.total)) > CENT / 2:
            result["differs"].append({"number": num, "ours": str(inv.total), "quickbooks": str(qb["amount"])})
        else:
            result["matched"].append(num)
        if qb["open"] is not None and qb["amount"] is not None:
            paid = (qb["amount"] - qb["open"]).quantize(CENT)
            inv.amount_paid = max(Decimal("0"), min(paid, _money(inv.total)))
            inv.payment_checked_at = datetime.utcnow()
            if qb["open"] <= 0:
                inv.status = INVOICE_PAID
                result["paid"].append(num)
            elif paid > 0:
                inv.status = INVOICE_PARTLY_PAID
                result["partly_paid"].append(num)
    for num, inv in ours.items():
        if num in exported and num not in seen:
            result["missing_in_quickbooks"].append(num)
    _event(org, EVENT_IMPORT, "invoice_list", user, filename=(filename or "quickbooks.csv")[:255], content=content,
           rows=sum(len(h) for h in seen.values()), detail={k: v for k, v in result.items()})
    db.session.commit()
    return result


def record_correction(org, invoice, *, user, note):
    """The office fixed a difference (in QuickBooks or here) and says what was done; kept in the history."""
    note = " ".join((note or "").split())
    if not note:
        raise AccountingError("Say what was corrected.")
    if invoice.organization_id != org:
        raise AccountingError("Not found.")
    _event(org, EVENT_CORRECTION, "invoice", user, record_key=invoice.number, note=note[:1000])
    db.session.commit()


def last_reconciliation(org):
    return (AccountingEvent.query.filter_by(organization_id=org, kind=EVENT_IMPORT, subject="invoice_list")
            .order_by(AccountingEvent.id.desc()).first())


# ------------------------------------------------------------------ approved time (Joel, 22 Oct 2026)
#
# Approved Time Entry hours for QuickBooks Online time / payroll, one row per approved entry. QuickBooks
# Online's Import data has no time-activity import, so this file is entered by hand (Weekly timesheet)
# or given to whoever runs payroll; CalibraytAI never posts it. No money in the file: hours only, so
# no costing rate or wage leaves CalibraytAI this way. Each row goes into a file once (its key is
# T<entry id>, kept in the export event); a correction after export is a new key and the replaced
# entry is listed so it can be changed in QuickBooks too. Checked against QuickBooks' time report
# (reconcile_time) by worker and day.

RECORD_TIME = "TIME"  # not an AccountingExportRecord type: kept in accounting_events (no schema change)
TIME_EXPORT_SUBJECT = "time"
TIME_RECONCILE_SUBJECT = "time_activities"
TIME_SERVICE_ITEM = "Labour"
TIME_HEADER = ["Activity Date", "Employee", "Customer", "Job", "Service Item", "Hours", "Duration (h:mm)",
               "Billable", "Kind of work", "Change order", "Work", "Description", "CalibraytAI ref"]


def _hours_hhmm(hours: Decimal) -> str:
    minutes = int((Decimal(hours) * 60).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return f"{minutes // 60}:{minutes % 60:02d}"


def _time_keys_exported(org) -> set:
    keys = set()
    for event in AccountingEvent.query.filter_by(organization_id=org, kind=EVENT_EXPORT, subject=TIME_EXPORT_SUBJECT).all():
        keys.update((event.detail_json or {}).get("keys") or [])
    return keys


def _time_kind_text(entry, company: bool):
    from app.services.work_scope import contractor_scope_label

    if company:
        return "Company time"
    return contractor_scope_label(entry.scope_origin)


def _time_rows(org):
    from app.models.time_entry import TIME_STATUS_APPROVED, LabourTimeEntry
    from app.services.time_entry import is_company_time_project

    from app.services.quickbooks_time import sent_entry_keys

    rows = []
    entries = (LabourTimeEntry.query.filter_by(organization_id=org, status=TIME_STATUS_APPROVED)
               .order_by(LabourTimeEntry.worker_display_name, LabourTimeEntry.work_date, LabourTimeEntry.id).all())
    in_quickbooks_time = sent_entry_keys(org)  # already sent by the QuickBooks Time connection: never by hand too
    for e in entries:
        if f"T{e.id}" in in_quickbooks_time:
            continue
        project = e.project
        company = is_company_time_project(project)
        job = project.name if company else job_reference(project)
        kind = _time_kind_text(e, company)
        co = e.change_order.number if (e.change_order is not None and not company) else ""
        hours = Decimal(str(e.hours)).quantize(CENT)
        rows.append({
            "Activity Date": e.work_date.strftime(DATE_FORMAT), "Employee": e.worker_display_name,
            "Customer": "" if company else (project.client.name if project.client else ""), "Job": job,
            "Service Item": TIME_SERVICE_ITEM, "Hours": str(hours), "Duration (h:mm)": _hours_hhmm(hours),
            "Billable": "Yes" if (e.scope_origin == "EXTRA_WORK" and not company) else "No",
            "Kind of work": kind, "Change order": co,
            "Work": f"{e.element_display_name} — {e.activity_display_name}",
            "Description": f"{kind}{' ' + co if co else ''}: {e.element_display_name} — {e.activity_display_name} (Job: {job}) [CT-T{e.id}]",
            "CalibraytAI ref": f"CT-T{e.id}",
            "_key": f"T{e.id}", "_ref": f"CT-T{e.id}", "_amount": None,
            "_worker": e.worker_display_name, "_date": e.work_date, "_hours": hours,
        })
    return RECORD_TIME, TIME_HEADER, rows


def _time_replaced_after_export(org, done) -> list:
    """Entries already in a QuickBooks file that were later corrected (replaced): change them there too."""
    from app.models.time_entry import TIME_STATUS_SUPERSEDED, LabourTimeEntry

    out = []
    for e in LabourTimeEntry.query.filter_by(organization_id=org, status=TIME_STATUS_SUPERSEDED).order_by(LabourTimeEntry.id).all():
        if f"T{e.id}" not in done:
            continue
        successor = LabourTimeEntry.query.filter_by(organization_id=org, supersedes_id=e.id).first()
        out.append({"ref": f"CT-T{e.id}", "employee": e.worker_display_name, "date": e.work_date.strftime(DATE_FORMAT),
                    "hours": str(Decimal(str(e.hours)).quantize(CENT)),
                    "now": (f"CT-T{successor.id}: {Decimal(str(successor.hours)).quantize(CENT)} hours"
                            if successor is not None else "")})
    return out


_T_DATE_HEADERS = ("activity date", "date", "txn date", "transaction date")
_T_EMPLOYEE_HEADERS = ("employee", "employee name", "name", "employee/vendor")
_T_HOURS_HEADERS = ("duration", "hours", "time", "qty", "quantity")
_T_MEMO_HEADERS = ("memo/description", "description", "memo", "notes")


def _parse_hours(text) -> Optional[Decimal]:
    t = (text or "").strip()
    if not t:
        return None
    if ":" in t:
        parts = t.split(":")
        try:
            h, m = int(parts[0] or 0), int(parts[1] or 0)
        except ValueError:
            return None
        return (Decimal(h) + Decimal(m) / 60).quantize(CENT, rounding=ROUND_HALF_UP)
    return _decimal(t)


def _parse_day(text) -> Optional[date]:
    t = (text or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            continue
    return None


def reconcile_time(org, *, filename, content: bytes, user) -> Dict:
    """Compare QuickBooks' time report CSV (Reports → Time Activities by Employee Detail → Export to CSV)
    with the approved hours CalibraytAI exported, by worker and day. Reads only; changes nothing."""
    if not content:
        raise AccountingError("Choose the CSV you exported from QuickBooks.")
    if len(content) > MAX_REPORT_BYTES:
        raise AccountingError("The file is larger than 5 MB.")
    text = content.decode("utf-8-sig", errors="replace")
    reader = list(csv.reader(io.StringIO(text)))
    header_at = next((i for i, row in enumerate(reader[:15]) if _find(row, _T_DATE_HEADERS) is not None
                      and _find(row, _T_HOURS_HEADERS) is not None), None)
    if header_at is None:
        raise AccountingError("This does not look like a QuickBooks time report: it needs Activity Date and Duration columns.")
    header = reader[header_at]
    i_date, i_hours = _find(header, _T_DATE_HEADERS), _find(header, _T_HOURS_HEADERS)
    i_emp, i_memo = _find(header, _T_EMPLOYEE_HEADERS), _find(header, _T_MEMO_HEADERS)
    theirs: Dict[tuple, Decimal] = {}
    refs_seen: Dict[str, int] = {}
    group_name = ""
    for row in reader[header_at + 1:]:
        cells = [c.strip() for c in row]
        if not any(cells):
            continue
        # QuickBooks groups the detail report: a row with only the employee's name, later "Total for ...".
        if cells[0] and not any(cells[1:]) and not cells[0].lower().startswith("total"):
            group_name = cells[0]
            continue
        if len(cells) <= max(i_date, i_hours):
            continue
        day = _parse_day(cells[i_date])
        hours = _parse_hours(cells[i_hours])
        if day is None or hours is None:
            continue
        name = cells[i_emp] if i_emp is not None and len(cells) > i_emp and cells[i_emp] else group_name
        key = (" ".join(name.split()).lower(), day)
        theirs[key] = theirs.get(key, Decimal("0")) + hours
        if i_memo is not None and len(cells) > i_memo:
            for ref in re.findall(r"CT-T\d+", cells[i_memo]):
                refs_seen[ref] = refs_seen.get(ref, 0) + 1
    exported = _time_keys_exported(org)
    _, _, rows = _time_rows(org)
    ours: Dict[tuple, Decimal] = {}
    names: Dict[tuple, str] = {}
    for r in rows:
        if r["_key"] not in exported:
            continue
        key = (" ".join(r["_worker"].split()).lower(), r["_date"])
        ours[key] = ours.get(key, Decimal("0")) + r["_hours"]
        names[key] = r["_worker"]
    result = {"matched": [], "differs": [], "missing_in_quickbooks": [], "unknown_in_calibraytai": [],
              "duplicates": [], "replaced": _time_replaced_after_export(org, exported)}
    for key, hours in sorted(ours.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        label = f"{names[key]}, {key[1].strftime(DATE_FORMAT)}"
        if key not in theirs:
            result["missing_in_quickbooks"].append({"who": label, "ours": str(hours)})
        elif abs(theirs[key] - hours) > CENT / 2:
            result["differs"].append({"who": label, "ours": str(hours), "quickbooks": str(theirs[key])})
        else:
            result["matched"].append(label)
    for key, hours in sorted(theirs.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        if key not in ours:
            result["unknown_in_calibraytai"].append({"who": f"{key[0]}, {key[1].strftime(DATE_FORMAT)}", "quickbooks": str(hours)})
    result["duplicates"] = [{"ref": ref, "count": n} for ref, n in sorted(refs_seen.items()) if n > 1]
    _event(org, EVENT_IMPORT, TIME_RECONCILE_SUBJECT, user, filename=(filename or "quickbooks-time.csv")[:255],
           content=content, rows=len(theirs), detail={k: v for k, v in result.items()})
    db.session.commit()
    return result


def last_time_reconciliation(org):
    return (AccountingEvent.query.filter_by(organization_id=org, kind=EVENT_IMPORT, subject=TIME_RECONCILE_SUBJECT)
            .order_by(AccountingEvent.id.desc()).first())

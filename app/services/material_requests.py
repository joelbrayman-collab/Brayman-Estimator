"""Need Materials: a request from the jobsite into the EXISTING supplier request and order path (25 Oct 2026).

The worker names the material (from the material catalogue, or in their own words), the quantity, the unit, when
it is needed, and an optional note or photo. Nothing is priced, ordered or sent from Field.

The office (Needs My Attention → Material requests) reviews and corrects the quantity, approves or declines, picks
the supplier (the contractor's own supplier accounts only), and presses Send to the supplier: CalibraytAI issues the
same supplier request the deck and framing takeoffs issue (the PDF, the stored manifest and the Supplier Hub share,
app/services/supplier_hub.py send_material_request), so the supplier's quote, the cost approval and the purchase
order follow the existing path without re-entry. One send per approved request (no duplicate requests or orders);
several approved requests for the same job and supplier may go together.

The worker sees their own request's status: Sent to the office → Approved / Declined → Asked for a price →
Price returned → Ordered → Delivered (read from the supplier request and its purchase order, never stored twice).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app import db
from app.models import Project
from app.models.canonical_material import CanonicalMaterial
from app.models.field_operations import (
    MR_APPROVED,
    MR_CANCELLED,
    MR_DECLINED,
    MR_REQUESTED,
    MR_SUBMITTED,
    RECORD_MATERIAL_REQUEST,
    FieldMaterialRequest,
)
from app.models.supplier_catalogue import ContractorSupplierAccount
from app.models.supplier_portal import (
    PO_CANCELLED,
    PO_DELIVERED,
    SHARE_RETURNED,
    SHARE_SUPERSEDED,
    SHARE_WITHDRAWN,
    SupplierPurchaseOrder,
)
from app.services.field_operations import (
    FieldOperationError,
    actor_label,
    capture_photos,
    parse_day,
    parse_quantity,
    plain_quantity,
    record,
)

# The catalogue's own units first (so a catalogue item's price can be recorded and ordered as it is), then the words
# crews use. The value is what is stored and sent; the label is what people read.
UNITS = (("EA", "each"), ("PKG", "box / package"), ("LF", "lineal ft"), ("SF", "sq ft"), ("BF", "board ft"),
         ("M3", "m³"), ("bags", "bags"), ("sheets", "sheets"), ("bundles", "bundles"), ("rolls", "rolls"),
         ("lengths", "lengths"), ("tubes", "tubes"), ("pails", "pails"), ("yd³", "yd³"))
_UNIT_LABELS = dict(UNITS)


def unit_label(value: str) -> str:
    return _UNIT_LABELS.get(value or "", value or "")
KIND = "field_material_request"


class MaterialRequestError(FieldOperationError):
    pass


def get(organization_id: str, request_id: int) -> Optional[FieldMaterialRequest]:
    row = db.session.get(FieldMaterialRequest, int(request_id))
    return row if row is not None and row.organization_id == organization_id else None


def catalogue_choices() -> list:
    return (CanonicalMaterial.query.filter_by(status="ACTIVE")
            .order_by(CanonicalMaterial.category.asc(), CanonicalMaterial.display_name.asc()).all())


def submit(project: Project, user, form, files=()) -> tuple[FieldMaterialRequest, bool]:
    from app.services.build import normalize_client_uuid

    org = project.organization_id
    uuid = None
    try:
        uuid = normalize_client_uuid(form.get("client_request_uuid"), field_name="client_request_uuid")
    except Exception:
        uuid = None
    if uuid:
        existing = FieldMaterialRequest.query.filter_by(organization_id=org, client_request_uuid=uuid).first()
        if existing is not None:
            return existing, False
    material = None
    material_id = (form.get("canonical_material_id") or "").strip()
    if material_id:
        material = db.session.get(CanonicalMaterial, int(material_id))
        if material is None or material.status != "ACTIVE":
            raise MaterialRequestError("Choose a material from the list, or describe it.")
    description = " ".join((form.get("description") or "").split())[:300]
    if not description and material is not None:
        description = material.display_name[:300]
    if not description:
        raise MaterialRequestError("Say what material you need (choose it from the list or type it).")
    quantity = parse_quantity(form.get("quantity"))
    unit = " ".join((form.get("unit") or "").split())[:20]
    if not unit:
        raise MaterialRequestError("Choose the unit (each, boxes, sheets…).")
    needed_by = parse_day(form.get("needed_by"), "Needed by", not_past=True)
    note = (form.get("note") or "").strip()[:2000] or None
    event = capture_photos(project, files, note="Material request photo")
    row = FieldMaterialRequest(
        organization_id=org, project_id=project.id, client_request_uuid=uuid,
        canonical_material_id=material.id if material else None, description=description, quantity=quantity,
        unit=unit, needed_by=needed_by, note=note, field_event_id=event.id if event else None,
        requested_by_user_id=getattr(user, "id", None), requested_by_name=actor_label(user), status=MR_SUBMITTED)
    db.session.add(row)
    db.session.flush()
    record(org, RECORD_MATERIAL_REQUEST, row.id, "SUBMITTED", actor=user, project_id=project.id,
           detail=f"{plain_quantity(quantity)} {unit} {description}" + (f", needed by {needed_by}" if needed_by else ""))
    db.session.commit()
    return row, True


def worker_requests(organization_id: str, user_id: int, limit: int = 15) -> list:
    return (FieldMaterialRequest.query.filter_by(organization_id=organization_id, requested_by_user_id=user_id)
            .order_by(FieldMaterialRequest.requested_at.desc(), FieldMaterialRequest.id.desc()).limit(limit).all())


def office_list(organization_id: str, *, project_id: Optional[int] = None, open_only: bool = False) -> list:
    query = FieldMaterialRequest.query.filter_by(organization_id=organization_id)
    if project_id:
        query = query.filter_by(project_id=int(project_id))
    if open_only:
        query = query.filter(FieldMaterialRequest.status.in_((MR_SUBMITTED, MR_APPROVED)))
    return query.order_by(FieldMaterialRequest.requested_at.desc(), FieldMaterialRequest.id.desc()).all()


def order_for(row: FieldMaterialRequest) -> Optional[SupplierPurchaseOrder]:
    if row.share_id is None:
        return None
    return SupplierPurchaseOrder.query.filter_by(share_id=row.share_id).first()


def status_label(row: FieldMaterialRequest) -> str:
    """The plain status, read from the supplier request and its purchase order (never stored twice)."""
    if row.status == MR_SUBMITTED:
        return "Sent to the office"
    if row.status == MR_DECLINED:
        return "Declined" + (f": {row.decline_reason}" if row.decline_reason else "")
    if row.status == MR_CANCELLED:
        return "Cancelled"
    if row.status == MR_APPROVED:
        return "Approved — the office is choosing the supplier"
    order = order_for(row)
    if order is not None:
        if order.status == PO_DELIVERED:
            return "Delivered"
        if order.status == PO_CANCELLED:
            return "Order cancelled — ask the office"
        from app.services.delivery_confirmations import open_exception_for_order

        if open_exception_for_order(order) is not None:
            return "Delivery problem reported — the office is on it"
        when = order.scheduled_date or order.delivery_date
        return "Ordered" + (f", delivery {when:%a %b} {when.day}" if when else "")
    share = row.share
    if share is not None and share.status == SHARE_RETURNED:
        return "Price returned — the office will order"
    if share is not None and share.status in (SHARE_WITHDRAWN, SHARE_SUPERSEDED):
        return "Supplier request closed — ask the office"
    return "Asked the supplier for a price"


def _require_office_open(row: FieldMaterialRequest):
    if row.status not in (MR_SUBMITTED, MR_APPROVED):
        raise MaterialRequestError("This request was already decided.")


def correct(row: FieldMaterialRequest, actor, form) -> FieldMaterialRequest:
    _require_office_open(row)
    quantity = parse_quantity(form.get("approved_quantity"), "Quantity")
    unit = " ".join((form.get("approved_unit") or row.unit).split())[:20]
    changes = []
    if quantity != row.order_quantity:
        changes.append(f"quantity {plain_quantity(row.order_quantity)} → {plain_quantity(quantity)}")
    if unit != row.order_unit:
        changes.append(f"unit {row.order_unit} → {unit}")
    row.approved_quantity = quantity
    row.approved_unit = unit
    material_id = (form.get("canonical_material_id") or "").strip()
    if material_id and (row.canonical_material_id is None or int(material_id) != row.canonical_material_id):
        material = db.session.get(CanonicalMaterial, int(material_id))
        if material is None or material.status != "ACTIVE":
            raise MaterialRequestError("Choose a catalogue item from the list.")
        changes.append(f"catalogue item: {material.display_name}")
        row.canonical_material_id = material.id
    note = (form.get("office_note") or "").strip()[:2000]
    if note:
        row.office_note = note
        changes.append("note added")
    record(row.organization_id, RECORD_MATERIAL_REQUEST, row.id, "CORRECTED", actor=actor, project_id=row.project_id,
           detail="; ".join(changes) or "checked; nothing changed")
    db.session.commit()
    return row


def approve(row: FieldMaterialRequest, actor) -> FieldMaterialRequest:
    if row.status != MR_SUBMITTED:
        raise MaterialRequestError("Only a request waiting for the office can be approved.")
    row.status = MR_APPROVED
    row.decided_by_name = actor_label(actor)
    row.decided_at = datetime.utcnow()
    record(row.organization_id, RECORD_MATERIAL_REQUEST, row.id, "APPROVED", actor=actor, project_id=row.project_id,
           detail=f"{plain_quantity(row.order_quantity)} {row.order_unit} {row.description}")
    db.session.commit()
    return row


def decline(row: FieldMaterialRequest, actor, reason: str) -> FieldMaterialRequest:
    _require_office_open(row)
    text = " ".join((reason or "").split())
    if not text:
        raise MaterialRequestError("Say why it is declined; the worker sees the reason.")
    row.status = MR_DECLINED
    row.decline_reason = text[:1000]
    row.decided_by_name = actor_label(actor)
    row.decided_at = datetime.utcnow()
    record(row.organization_id, RECORD_MATERIAL_REQUEST, row.id, "DECLINED", actor=actor, project_id=row.project_id,
           detail=text)
    db.session.commit()
    return row


def supplier_accounts(organization_id: str) -> list:
    return (ContractorSupplierAccount.query.filter_by(organization_id=organization_id, status="ACTIVE")
            .order_by(ContractorSupplierAccount.id.asc()).all())


def _rows_for_manifest(rows):
    from app.services.deck_takeoff.records import CALCULATED, fingerprint

    out = []
    for number, row in enumerate(rows, start=1):
        quantity = row.order_quantity
        qty_text = plain_quantity(quantity)
        line = {
            "key": f"field.request.{row.id}",
            "description": row.description + (f" — {row.office_note}" if row.office_note else ""),
            "purchasing_quantity": float(quantity),
            "purchasing_unit": row.order_unit,
            "stock_length_ft": None,
            "status": CALCULATED,
            "complete": True,
            "canonical_material_code": row.material.code if row.material is not None else None,
            "canonical_identity": None,
            "number": number,
            "item": row.description,
            "qty": qty_text,
            "unit": row.order_unit,
            "status_label": "FINAL",
        }
        line["signature"] = fingerprint({"key": line["key"], "qty": qty_text, "unit": row.order_unit,
                                         "request": row.id})[:24]
        out.append(line)
    return out


def send_to_supplier(rows: list, actor, *, account_id: int) -> dict:
    """Issue ONE supplier request (PDF, manifest, Supplier Hub share) for approved requests of one job."""
    from app.services.brayman_supplier_estimate import render_supplier_response_request
    from app.services.deck_takeoff import storage
    from app.services.deck_takeoff.records import fingerprint
    from app.services.deck_takeoff.supplier_request import CURRENT_RESPONSE_FORM, FINAL
    from app.services.supplier_hub import SupplierHubError, send_material_request, supplier_has_sign_in

    if not rows:
        raise MaterialRequestError("Choose at least one approved request.")
    org = rows[0].organization_id
    project_ids = {r.project_id for r in rows}
    if len(project_ids) != 1:
        raise MaterialRequestError("Send one job's requests at a time.")
    for row in rows:
        if row.organization_id != org:
            raise MaterialRequestError("Not found.")
        if row.status != MR_APPROVED:
            raise MaterialRequestError(f"{row.number} is not approved yet (or was already sent).")
    account = ContractorSupplierAccount.query.filter_by(id=int(account_id), organization_id=org,
                                                        status="ACTIVE").first()
    if account is None:
        raise MaterialRequestError("Choose one of your supplier accounts.")
    if not supplier_has_sign_in(account.supplier_id):
        raise MaterialRequestError(f"{account.supplier.legal_name} has no Supplier Hub sign-in yet. Add a supplier "
                                   "user first (Suppliers), or ask them by phone.")
    project = db.session.get(Project, project_ids.pop())
    lines = _rows_for_manifest(rows)
    needed = min((r.needed_by for r in rows if r.needed_by), default=None)
    issued_at = datetime.utcnow()
    request_id = "FMR-" + fingerprint({"requests": sorted(r.id for r in rows), "project": project.id,
                                       "organization": org, "account": account.id,
                                       "form": CURRENT_RESPONSE_FORM})[:16].upper()
    names = "; ".join(f"{r.number} from {r.requested_by_name}" for r in rows)
    intro = (
        "Please provide your current contractor pricing for the materials listed below (requested from the job site: "
        f"{names}). Brayman Construction set every quantity and unit on this request. Please do not change them.",
        "For each line, enter your SKU, the unit cost, and the contractor discount (enter 0 if there is none). "
        "Brayman calculates every total from its quantity when this PDF is returned. A blank discount is not zero.",
        f"{len(lines)} of {len(lines)} lines are marked {FINAL}. Prices are CAD before HST."
        + (f" Needed on site by {needed:%A %B} {needed.day}." if needed else ""),
    )
    manifest = {
        "request_id": request_id, "kind": KIND, "response_form": CURRENT_RESPONSE_FORM, "organization_id": org,
        "project_id": project.id, "supplier_id": account.supplier_id,
        "supplier_location_id": account.supplier_location_id, "contractor_supplier_account_id": account.id,
        "supplier_name": account.supplier.legal_name, "issued_at": issued_at.isoformat(timespec="seconds"),
        "issued_by": actor_label(actor), "takeoff_fingerprint": fingerprint({"lines": [l["key"] for l in lines]}),
        "rule": {"id": "field_material_request", "version": "1"},
        "source": {"kind": "field_material_request", "requests": [r.id for r in rows]},
        "product_facts": {}, "lines": lines,
    }
    if storage.load_request(org, project.id, request_id) is None:
        pdf = render_supplier_response_request(
            project_name=project.name, project_address=project.address or "",
            supplier_name=account.supplier.legal_name, issued_on=issued_at.strftime("%d %B %Y").lstrip("0"),
            intro=intro, rows=tuple({"number": l["number"], "item": l["item"], "status_label": l["status_label"],
                                     "qty": l["qty"], "unit": l["unit"], "key": l["key"], "signature": l["signature"]}
                                    for l in lines),
            request_id=request_id, project_id=project.id, layout=CURRENT_RESPONSE_FORM)
        storage.save_request(org, project.id, manifest, pdf)
    try:
        share = send_material_request(project=project, request_id=request_id, user=actor, needed_by=needed)
    except SupplierHubError as exc:
        raise MaterialRequestError(str(exc)) from None
    for row in rows:
        row.status = MR_REQUESTED
        row.contractor_supplier_account_id = account.id
        row.supplier_request_id = request_id
        row.share_id = share.id
        record(org, RECORD_MATERIAL_REQUEST, row.id, "SENT_TO_SUPPLIER", actor=actor, project_id=project.id,
               detail=f"Supplier request {share.number} to {account.supplier.legal_name}")
    db.session.commit()
    return {"share": share, "request_id": request_id, "supplier": account.supplier.legal_name}


def history(row: FieldMaterialRequest) -> list:
    from app.services.field_operations import history as h

    return h(row.organization_id, RECORD_MATERIAL_REQUEST, row.id)

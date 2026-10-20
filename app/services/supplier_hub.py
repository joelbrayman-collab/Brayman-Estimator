"""Supplier Hub services (Joel, 17 Oct 2026; ADR-047).

Principal classes: a signed-in user is a CONTRACTOR (office membership) or a
SUPPLIER (supplier membership), never both. A supplier sees only requests a
contractor sent to their supplier account, carrying only the shared fields.

A material request is an issued deck takeoff Form 2 request. The supplier
returns SKU, unit cost and discount per line on screen (or uploads the filled
PDF); the return goes through the same reconciliation and totals as an office
import and lands on the contractor's project, where Brayman records and approves
it as today. Concrete is its own request, sent to its own supplier account.
A quote is an offer; the contractor's purchase order accepts it; the supplier's
confirmation completes the agreement.
"""

from __future__ import annotations

import re
import secrets
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional

from app import db
from app.models.canonical_material import CanonicalMaterial
from app.models.contractor_cost_approval import ContractorCostApproval
from app.models.organization import Organization
from app.models.project import Project
from app.models.supplier_catalogue import ContractorSupplierAccount, Supplier
from app.models.supplier_portal import (
    CONCRETE_PLACEMENT,
    KIND_CONCRETE,
    KIND_MATERIAL,
    MEMBERSHIP_ACTIVE,
    PO_CONFIRMED,
    PO_PLACED,
    PO_PROBLEM,
    SHARE_OPENED,
    SHARE_RETURNED,
    SHARE_SENT,
    SHARE_SUPERSEDED,
    SHARE_WITHDRAWN,
    SOURCE_CONCRETE,
    SOURCE_DECK_FORM2,
    ConcreteRequest,
    SupplierPurchaseOrder,
    SupplierRequestEvent,
    SupplierRequestShare,
    SupplierUserMembership,
)
from app.models.user import User, UserMembership

CENT = Decimal("0.01")
OPEN_SHARE_STATUSES = (SHARE_SENT, SHARE_OPENED, SHARE_RETURNED)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SupplierHubError(Exception):
    """A supplier hub step that cannot be completed (message is shown to the person)."""


# ------------------------------------------------------------------ identity

def active_supplier_memberships(user) -> list[SupplierUserMembership]:
    if user is None or not getattr(user, "id", None):
        return []
    return (
        SupplierUserMembership.query.join(Supplier, Supplier.id == SupplierUserMembership.supplier_id)
        .filter(SupplierUserMembership.user_id == user.id,
                SupplierUserMembership.status == MEMBERSHIP_ACTIVE,
                Supplier.status == "ACTIVE")
        .order_by(Supplier.legal_name.asc()).all()
    )


def has_contractor_membership(user) -> bool:
    return UserMembership.query.filter_by(user_id=user.id, is_active=True).first() is not None


def principal_class(user) -> Optional[str]:
    """CONTRACTOR, SUPPLIER, CONFLICT (both: fail closed) or None."""
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    supplier = bool(active_supplier_memberships(user))
    contractor = has_contractor_membership(user)
    if supplier and contractor:
        return "CONFLICT"
    if supplier:
        return "SUPPLIER"
    if contractor:
        return "CONTRACTOR"
    return None


def require_supplier_membership(user, supplier_id: int) -> SupplierUserMembership:
    for membership in active_supplier_memberships(user):
        if membership.supplier_id == supplier_id:
            return membership
    raise SupplierHubError("Not found.")


def _display(user) -> str:
    return ((getattr(user, "display_name", None) or getattr(user, "email", "")) or "Unknown").strip()[:160]


def add_supplier_user(*, organization_id: str, supplier: Supplier, display_name: str, email: str,
                      actor_name: str) -> tuple[User, bool]:
    """Give a store person a supplier sign-in. Returns (user, created)."""
    from app.services.auth import hash_password

    name = (display_name or "").strip()
    address = (email or "").strip().lower()
    if not name:
        raise SupplierHubError("Enter the person's name.")
    if not _EMAIL_RE.match(address):
        raise SupplierHubError("Enter a valid email.")
    if ContractorSupplierAccount.query.filter_by(organization_id=organization_id, supplier_id=supplier.id).first() is None:
        raise SupplierHubError("This supplier has no account with your company.")
    user = User.query.filter_by(email=address).first()
    created = False
    if user is None:
        user = User(email=address, display_name=name[:150], password_hash=hash_password(secrets.token_urlsafe(24)),
                    is_active=True)
        db.session.add(user)
        db.session.flush()
        created = True
    elif has_contractor_membership(user):
        raise SupplierHubError("This email belongs to an office user. A person cannot be both office and supplier.")
    membership = SupplierUserMembership.query.filter_by(user_id=user.id, supplier_id=supplier.id).first()
    if membership is None:
        membership = SupplierUserMembership(user_id=user.id, supplier_id=supplier.id, status=MEMBERSHIP_ACTIVE,
                                            created_by_name=actor_name[:160], created_by_organization_id=organization_id)
        db.session.add(membership)
    else:
        membership.status = MEMBERSHIP_ACTIVE
        membership.revoked_at = None
    db.session.commit()
    return user, created


def revoke_supplier_user(membership: SupplierUserMembership) -> None:
    membership.status = "REVOKED"
    membership.revoked_at = datetime.utcnow()
    db.session.commit()


# ------------------------------------------------------------------ numbering and events

def _next_number(model, organization_id: str, prefix: str) -> str:
    year = datetime.utcnow().year
    stem = f"{prefix}-{year}-"
    rows = model.query.filter(model.organization_id == organization_id, model.number.like(stem + "%")).all()
    highest = 0
    for row in rows:
        try:
            highest = max(highest, int(row.number.rsplit("-", 1)[1]))
        except (ValueError, IndexError):
            continue
    return f"{stem}{highest + 1:04d}"


def _event(share: SupplierRequestShare, event_type: str, side: str, actor: str, detail: Optional[str] = None):
    db.session.add(SupplierRequestEvent(share_id=share.id, event_type=event_type, actor_side=side,
                                        actor_name=(actor or "Unknown")[:160], at=datetime.utcnow(), detail=detail))


def share_events(share: SupplierRequestShare) -> list[SupplierRequestEvent]:
    return SupplierRequestEvent.query.filter_by(share_id=share.id).order_by(SupplierRequestEvent.id.asc()).all()


# ------------------------------------------------------------------ the shared fields (approved 17 Oct)

def _company(organization_id: str) -> dict:
    org = db.session.get(Organization, organization_id)
    return {"company": getattr(org, "display_name", None) or getattr(org, "name", None) or "Brayman Construction"}


def _contact(user) -> dict:
    return {"contact_name": _display(user), "contact_email": getattr(user, "email", "") or ""}


def _delivery_town(project: Project) -> str:
    location = getattr(project, "location", None)
    town = (getattr(location, "municipality", None) or "").strip()
    province = (getattr(location, "province_state", None) or "").strip()
    return ", ".join(part for part in (town, province) if part) or "To be confirmed"


def _project_reference(project: Project) -> str:
    return f"Brayman project {project.id}"


def _base_shared(project: Project, user, needed_by: Optional[date]) -> dict:
    return {
        **_company(project.organization_id),
        **_contact(user),
        "project_reference": _project_reference(project),
        "delivery_town": _delivery_town(project),
        "needed_by": needed_by.isoformat() if needed_by else None,
    }


def _account(organization_id: str, account_id: int) -> ContractorSupplierAccount:
    account = ContractorSupplierAccount.query.filter_by(id=account_id, organization_id=organization_id,
                                                        status="ACTIVE").first()
    if account is None:
        raise SupplierHubError("Choose an active supplier account.")
    return account


def supplier_has_sign_in(supplier_id: int) -> bool:
    return SupplierUserMembership.query.filter_by(supplier_id=supplier_id, status=MEMBERSHIP_ACTIVE).first() is not None


def _supersede_open(organization_id, project_id, supplier_id, request_kind, keep_id=None):
    for old in SupplierRequestShare.query.filter(
        SupplierRequestShare.organization_id == organization_id,
        SupplierRequestShare.project_id == project_id,
        SupplierRequestShare.supplier_id == supplier_id,
        SupplierRequestShare.request_kind == request_kind,
        SupplierRequestShare.status.in_((SHARE_SENT, SHARE_OPENED)),
    ):
        if old.id != keep_id:
            old.status = SHARE_SUPERSEDED


# ------------------------------------------------------------------ material requests (deck Form 2)

def send_material_request(*, project: Project, request_id: str, user, needed_by: Optional[date] = None) -> SupplierRequestShare:
    from app.services.deck_takeoff import storage

    manifest = storage.load_request(project.organization_id, project.id, request_id)
    if manifest is None:
        raise SupplierHubError("Issue the supplier request first.")
    if int(manifest.get("response_form") or 1) != 2:
        raise SupplierHubError("Only the current supplier request form can be sent in CalibraytAI. Issue the request again.")
    account = _account(project.organization_id, int(manifest["contractor_supplier_account_id"]))
    if not supplier_has_sign_in(account.supplier_id):
        raise SupplierHubError(f"{account.supplier.legal_name} has no supplier sign-in yet. Add a supplier user first.")
    existing = SupplierRequestShare.query.filter(
        SupplierRequestShare.organization_id == project.organization_id,
        SupplierRequestShare.source_kind == SOURCE_DECK_FORM2,
        SupplierRequestShare.source_ref == request_id,
        SupplierRequestShare.status.in_(OPEN_SHARE_STATUSES),
    ).first()
    if existing is not None:
        raise SupplierHubError(f"This request is already with {account.supplier.legal_name} ({existing.number}).")
    lines = [
        {
            "number": int(line["number"]),
            "key": line["key"],
            "signature": line["signature"],
            "description": line.get("description") or line.get("item") or "",
            "qty": line.get("qty"),
            "purchasing_quantity": line.get("purchasing_quantity"),
            "unit": line.get("purchasing_unit") or line.get("unit") or "",
            "status_label": line.get("status_label") or "",
            "final": bool(line.get("complete")),
        }
        for line in manifest["lines"]
    ]
    shared = {**_base_shared(project, user, needed_by), "lines": lines}
    share = SupplierRequestShare(
        organization_id=project.organization_id,
        project_id=project.id,
        supplier_id=account.supplier_id,
        contractor_supplier_account_id=account.id,
        number=_next_number(SupplierRequestShare, project.organization_id, "SRQ"),
        request_kind=KIND_MATERIAL,
        source_kind=SOURCE_DECK_FORM2,
        source_ref=request_id,
        shared_json=shared,
        status=SHARE_SENT,
        sent_by_user_id=getattr(user, "id", None),
        sent_by_name=_display(user),
        sent_at=datetime.utcnow(),
    )
    db.session.add(share)
    db.session.flush()
    _supersede_open(project.organization_id, project.id, account.supplier_id, KIND_MATERIAL, keep_id=share.id)
    _event(share, "SENT", "CONTRACTOR", share.sent_by_name)
    db.session.commit()
    return share


def withdraw_share(share: SupplierRequestShare, *, user) -> None:
    if share.status in (SHARE_WITHDRAWN, SHARE_SUPERSEDED):
        raise SupplierHubError("This request is already closed.")
    if purchase_order_for(share) is not None:
        raise SupplierHubError("An order was placed on this request; it cannot be withdrawn.")
    share.status = SHARE_WITHDRAWN
    share.withdrawn_at = datetime.utcnow()
    _event(share, "WITHDRAWN", "CONTRACTOR", _display(user))
    db.session.commit()


def mark_opened(share: SupplierRequestShare, *, user) -> None:
    if share.status == SHARE_SENT:
        share.status = SHARE_OPENED
        share.opened_at = datetime.utcnow()
        _event(share, "OPENED", "SUPPLIER", _display(user))
        db.session.commit()


def _parse_minutes(raw) -> Optional[int]:
    text = (str(raw or "")).strip()
    if not text:
        return None
    try:
        value = int(text)
    except ValueError:
        raise SupplierHubError("Minutes spent must be a whole number.")
    if value < 0 or value > 24 * 60:
        raise SupplierHubError("Minutes spent must be between 0 and 1440.")
    return value


def return_material_quote(share: SupplierRequestShare, *, user, values: dict, pdf: Optional[bytes] = None) -> dict:
    """The supplier returns prices. Same reconciliation and totals as an office import."""
    from app.services.deck_takeoff import storage
    from app.services.deck_takeoff.intake import (
        SupplierResponseError,
        answers_from_values,
        read_response_pdf,
        reconcile,
    )

    if share.request_kind != KIND_MATERIAL:
        raise SupplierHubError("Not found.")
    if share.status not in (SHARE_SENT, SHARE_OPENED):
        raise SupplierHubError("This request is closed or already returned.")
    minutes = _parse_minutes(values.get("minutes_reported"))
    try:
        if pdf:
            raw = read_response_pdf(pdf)
            source = "returned PDF uploaded in CalibraytAI"
        else:
            raw = {k: v for k, v in values.items() if re.match(r"^(sku|unit_cost|discount)_\d{2,3}$", k)}
            for name in ("bmr_contact", "response_date", "valid_until", "general_notes"):
                raw[name] = values.get(name, "")
            source = "entered in CalibraytAI by the supplier"
        # Identity always comes from the shared request, never from what was typed.
        raw["request_id"] = share.source_ref
        raw["request_project"] = str(share.project_id)
        for line in share.shared_json.get("lines", []):
            n = f"{int(line['number']):02d}"
            raw[f"line_key_{n}"] = line["key"]
            raw[f"line_sig_{n}"] = line["signature"]
        answers = answers_from_values(raw)
        manifest = storage.load_request(share.organization_id, share.project_id, share.source_ref)
        if manifest is None:
            raise SupplierHubError("This request is no longer available.")
        codes = frozenset(code for (code,) in CanonicalMaterial.query.with_entities(CanonicalMaterial.code).all())
        reconciliation = reconcile(manifest, answers, project_id=share.project_id,
                                   organization_id=share.organization_id, catalogue_codes=codes)
    except SupplierResponseError as exc:
        raise SupplierHubError(str(exc)) from exc
    if reconciliation.get("no_prices_found"):
        raise SupplierHubError("No prices were entered. Enter at least one line's SKU, unit cost and discount.")
    actor = _display(user)
    supplier_name = share.supplier.legal_name if share.supplier else "Supplier"
    record = {
        **reconciliation,
        "stage": "IMPORTED",
        "source": f"{source} ({supplier_name}, {share.number})",
        "imported_by": f"{actor} ({supplier_name})",
        "imported_at": datetime.utcnow().isoformat(timespec="seconds"),
        "supplier_share_number": share.number,
    }
    stored = storage.save_response(share.organization_id, share.project_id, record, pdf)
    share.status = SHARE_RETURNED
    share.returned_at = datetime.utcnow()
    share.returned_by_name = actor
    share.response_ref = stored["response_id"]
    share.minutes_reported = minutes
    share.quote_json = {
        "recordable_quoted_total": str(reconciliation.get("recordable_quoted_total") or "0"),
        "lines_priced": sum(1 for r in reconciliation["rows"] if r.get("status") == "QUOTED"),
        "lines": len(reconciliation["rows"]),
        "valid_until": reconciliation.get("valid_until"),
    }
    _event(share, "RETURNED", "SUPPLIER", actor, f"Response {stored['response_id']}")
    db.session.commit()
    return stored


# ------------------------------------------------------------------ concrete (its own request)

def _decimal(raw, label, *, positive=True) -> Decimal:
    text = str(raw or "").replace("$", "").replace(",", "").strip()
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise SupplierHubError(f"{label} must be a number.")
    if not value.is_finite() or value < 0 or (positive and value == 0):
        raise SupplierHubError(f"{label} must be {'more than zero' if positive else 'zero or more'}.")
    return value


def _date(raw, label, *, required=True) -> Optional[date]:
    text = (str(raw or "")).strip()
    if not text:
        if required:
            raise SupplierHubError(f"Enter the {label}.")
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise SupplierHubError(f"The {label} must be a date (YYYY-MM-DD).")


def create_concrete_request(*, project: Project, user, form: dict) -> ConcreteRequest:
    volume = _decimal(form.get("volume_m3"), "Volume (m³)")
    try:
        strength = int(str(form.get("strength_mpa") or "").strip())
    except ValueError:
        raise SupplierHubError("Strength (MPa) must be a whole number.")
    if strength < 10 or strength > 80:
        raise SupplierHubError("Strength must be between 10 and 80 MPa.")
    slump_raw = str(form.get("slump_mm") or "").strip()
    slump = None
    if slump_raw:
        try:
            slump = int(slump_raw)
        except ValueError:
            raise SupplierHubError("Slump (mm) must be a whole number.")
    placement = (form.get("placement") or "").strip()
    if placement not in CONCRETE_PLACEMENT:
        raise SupplierHubError("Choose how the concrete is placed.")
    row = ConcreteRequest(
        organization_id=project.organization_id,
        project_id=project.id,
        number=_next_number(ConcreteRequest, project.organization_id, "CON"),
        volume_m3=volume.quantize(CENT),
        strength_mpa=strength,
        exposure_class=(form.get("exposure_class") or "").strip()[:20] or None,
        air_entrainment=(form.get("air_entrainment") or "").strip()[:40] or None,
        slump_mm=slump,
        delivery_date=_date(form.get("delivery_date"), "delivery date"),
        delivery_window=(form.get("delivery_window") or "").strip()[:60] or None,
        placement=placement,
        delivery_town=(form.get("delivery_town") or "").strip()[:120] or _delivery_town(project),
        notes=(form.get("notes") or "").strip() or None,
        created_by_name=_display(user),
        created_at=datetime.utcnow(),
    )
    db.session.add(row)
    db.session.commit()
    return row


def send_concrete_request(*, concrete: ConcreteRequest, account_id: int, user) -> SupplierRequestShare:
    project = db.session.get(Project, concrete.project_id)
    account = _account(concrete.organization_id, account_id)
    if not supplier_has_sign_in(account.supplier_id):
        raise SupplierHubError(f"{account.supplier.legal_name} has no supplier sign-in yet. Add a supplier user first.")
    existing = SupplierRequestShare.query.filter(
        SupplierRequestShare.organization_id == concrete.organization_id,
        SupplierRequestShare.source_kind == SOURCE_CONCRETE,
        SupplierRequestShare.source_ref == str(concrete.id),
        SupplierRequestShare.status.in_(OPEN_SHARE_STATUSES),
    ).first()
    if existing is not None:
        raise SupplierHubError(f"This concrete request is already with {existing.supplier.legal_name} ({existing.number}).")
    shared = {
        **_base_shared(project, user, concrete.delivery_date),
        "delivery_town": concrete.delivery_town,
        "concrete": {
            "request_number": concrete.number,
            "volume_m3": str(concrete.volume_m3),
            "strength_mpa": concrete.strength_mpa,
            "exposure_class": concrete.exposure_class,
            "air_entrainment": concrete.air_entrainment,
            "slump_mm": concrete.slump_mm,
            "delivery_date": concrete.delivery_date.isoformat(),
            "delivery_window": concrete.delivery_window,
            "placement": concrete.placement,
            "notes": concrete.notes,
        },
    }
    share = SupplierRequestShare(
        organization_id=concrete.organization_id,
        project_id=concrete.project_id,
        supplier_id=account.supplier_id,
        contractor_supplier_account_id=account.id,
        number=_next_number(SupplierRequestShare, concrete.organization_id, "SRQ"),
        request_kind=KIND_CONCRETE,
        source_kind=SOURCE_CONCRETE,
        source_ref=str(concrete.id),
        shared_json=shared,
        status=SHARE_SENT,
        sent_by_user_id=getattr(user, "id", None),
        sent_by_name=_display(user),
        sent_at=datetime.utcnow(),
    )
    db.session.add(share)
    db.session.flush()
    _event(share, "SENT", "CONTRACTOR", share.sent_by_name)
    db.session.commit()
    return share


CONCRETE_CHARGES = (
    ("pump_charge", "Pump charge"),
    ("short_load_charge", "Short-load charge"),
    ("seasonal_charge", "Winter heat or seasonal charge"),
    ("other_charge", "Other charges"),
)


def return_concrete_quote(share: SupplierRequestShare, *, user, values: dict) -> dict:
    if share.request_kind != KIND_CONCRETE:
        raise SupplierHubError("Not found.")
    if share.status not in (SHARE_SENT, SHARE_OPENED):
        raise SupplierHubError("This request is closed or already returned.")
    volume = Decimal(share.shared_json["concrete"]["volume_m3"])
    price = _decimal(values.get("price_per_m3"), "Price per m³")
    charges = {}
    for key, label in CONCRETE_CHARGES:
        raw = str(values.get(key) or "").strip()
        charges[key] = _decimal(raw, label, positive=False) if raw else Decimal("0")
    valid_until = _date(values.get("valid_until"), "price validity date")
    quote_number = (values.get("quote_number") or "").strip()[:40]
    concrete_value = (price * volume).quantize(CENT, rounding=ROUND_HALF_UP)
    total = (concrete_value + sum(charges.values(), Decimal("0"))).quantize(CENT, rounding=ROUND_HALF_UP)
    actor = _display(user)
    share.quote_json = {
        "quote_number": quote_number or share.number,
        "price_per_m3": str(price),
        "volume_m3": str(volume),
        "concrete_value": str(concrete_value),
        "charges": {key: str(value) for key, value in charges.items()},
        "total_before_tax": str(total),
        "valid_until": valid_until.isoformat(),
        "notes": (values.get("notes") or "").strip(),
        "returned_by": actor,
    }
    share.minutes_reported = _parse_minutes(values.get("minutes_reported"))
    share.status = SHARE_RETURNED
    share.returned_at = datetime.utcnow()
    share.returned_by_name = actor
    share.response_ref = share.quote_json["quote_number"]
    _event(share, "RETURNED", "SUPPLIER", actor, f"Concrete quote {share.response_ref}: ${total}")
    db.session.commit()
    return share.quote_json


# ------------------------------------------------------------------ purchase orders

def purchase_order_for(share: SupplierRequestShare) -> Optional[SupplierPurchaseOrder]:
    return SupplierPurchaseOrder.query.filter_by(share_id=share.id).first()


def _site_address(project: Project) -> str:
    from app.services.contract_generation import _location_address

    return (project.address or "").strip() or _location_address(project) or _delivery_town(project)


def material_order_lines(share: SupplierRequestShare) -> tuple[list[dict], list[str]]:
    """Order lines from the recorded, approved quote, and what still blocks the order."""
    from app.services.deck_takeoff import storage

    blockers = []
    if share.status != SHARE_RETURNED or not share.response_ref:
        return [], ["The supplier has not returned this request."]
    record = storage.load_response(share.organization_id, share.project_id, share.response_ref)
    if record is None:
        return [], ["The returned quote was not found."]
    followups = [r for r in storage.list_responses(share.organization_id, share.project_id)
                 if r.get("records_response") == share.response_ref and r.get("stage") == "RECORDED"]
    if not followups:
        blockers.append("Record the supplier's prices first (on the returned response).")
    recorded = {int(r["number"]): r for f in followups for r in f.get("results") or [] if r.get("recorded")}
    lines = []
    for row in record.get("rows") or []:
        if not row.get("in_recordable_total"):
            continue
        number = int(row["number"])
        material_id = (recorded.get(number) or {}).get("canonical_material_id")
        approved = False
        if material_id:
            latest = (ContractorCostApproval.query.filter_by(organization_id=share.organization_id,
                                                             canonical_material_id=material_id,
                                                             supplier_id=share.supplier_id)
                      .order_by(ContractorCostApproval.id.desc()).first())
            approved = latest is not None and latest.status == "APPROVED"
        lines.append({
            "number": number,
            "description": row.get("description"),
            "sku": (row.get("answers") or {}).get("sku", ""),
            "quantity": str(row.get("purchasing_quantity")),
            "unit": row.get("purchasing_unit") or "",
            "net_unit_cost": row.get("net_price"),
            "line_value": row.get("line_value"),
            "cost_approved": approved,
        })
    if not lines:
        blockers.append("No line on the returned quote can be ordered.")
    elif followups and not all(line["cost_approved"] for line in lines):
        blockers.append("Approve each line's cost first (on the returned response).")
    return lines, blockers


def concrete_order_lines(share: SupplierRequestShare) -> tuple[list[dict], list[str]]:
    if share.status != SHARE_RETURNED or not share.quote_json:
        return [], ["The supplier has not returned this request."]
    quote = share.quote_json
    concrete = share.shared_json["concrete"]
    lines = [{
        "number": 1,
        "description": f"Ready-mix concrete {concrete['strength_mpa']} MPa"
                       + (f", exposure {concrete['exposure_class']}" if concrete.get("exposure_class") else ""),
        "sku": quote.get("quote_number") or "",
        "quantity": quote["volume_m3"],
        "unit": "m³",
        "net_unit_cost": quote["price_per_m3"],
        "line_value": quote["concrete_value"],
        "cost_approved": True,
    }]
    for number, (key, label) in enumerate(CONCRETE_CHARGES, start=2):
        value = Decimal(quote["charges"].get(key) or "0")
        if value:
            lines.append({"number": number, "description": label, "sku": "", "quantity": "1", "unit": "EA",
                          "net_unit_cost": str(value), "line_value": str(value), "cost_approved": True})
    if quote.get("valid_until") and date.fromisoformat(quote["valid_until"]) < date.today():
        return lines, ["The supplier's price has expired. Ask for a new quote."]
    if not quote.get("approved_at"):
        return lines, ["Approve the concrete quote first."]
    return lines, []


def approve_concrete_quote(share: SupplierRequestShare, *, user) -> None:
    """Demo step 5: Ben reviews and approves the returned concrete quote before any order (a separate step)."""
    if share.request_kind != KIND_CONCRETE or share.status != SHARE_RETURNED or not share.quote_json:
        raise SupplierHubError("There is no returned concrete quote to approve.")
    if share.quote_json.get("approved_at"):
        raise SupplierHubError("This quote is already approved.")
    quote = dict(share.quote_json)
    quote["approved_by"] = _display(user)
    quote["approved_at"] = datetime.utcnow().isoformat(timespec="seconds")
    share.quote_json = quote
    _event(share, "QUOTE_APPROVED", "CONTRACTOR", quote["approved_by"],
           f"Concrete quote {quote.get('quote_number')}: ${quote.get('total_before_tax')} before tax")
    db.session.commit()


def order_lines(share):
    return concrete_order_lines(share) if share.request_kind == KIND_CONCRETE else material_order_lines(share)


def place_order(share: SupplierRequestShare, *, user, delivery_date=None, site_contact: str = "",
                notes: str = "", delivery_window: str = "", schedule_item_id=None, signature=None) -> SupplierPurchaseOrder:
    """Place the purchase order. With a signature (every order placed from the office), the contractor signs it."""
    from app.services import supplier_signing

    if signature is not None:
        supplier_signing._require_valid(signature)
    if purchase_order_for(share) is not None:
        raise SupplierHubError("An order was already placed on this request.")
    lines, blockers = order_lines(share)
    if blockers:
        raise SupplierHubError("The order cannot be placed yet. " + " ".join(blockers))
    project = db.session.get(Project, share.project_id)
    total = sum((Decimal(line["line_value"] or "0") for line in lines), Decimal("0")).quantize(CENT)
    order = SupplierPurchaseOrder(
        organization_id=share.organization_id,
        project_id=share.project_id,
        share_id=share.id,
        supplier_id=share.supplier_id,
        number=_next_number(SupplierPurchaseOrder, share.organization_id, "PO"),
        quote_ref=share.response_ref or share.number,
        lines_json=lines,
        total=total,
        delivery_date=_date(delivery_date, "delivery date", required=False) if isinstance(delivery_date, str) else delivery_date,
        delivery_window=(delivery_window or "").strip()[:60] or None,
        schedule_item_id=_schedule_item_for(project, schedule_item_id),
        delivery_address=_site_address(project)[:300],
        site_contact=(site_contact or "").strip()[:160] or None,
        notes=(notes or "").strip() or None,
        status=PO_PLACED,
        placed_by_user_id=getattr(user, "id", None),
        placed_by_name=_display(user),
        placed_at=datetime.utcnow(),
    )
    db.session.add(order)
    _event(share, "ORDER_PLACED", "CONTRACTOR", order.placed_by_name, f"{order.number}: ${total}")
    supplier_signing.open_order_signing(order, user=user, signature=signature)
    if signature is not None:
        _event(share, "ORDER_SIGNED", "CONTRACTOR", order.placed_by_name, f"{order.number} signed by {signature.name}")
    db.session.commit()
    _notify_supplier(order, f"New purchase order {order.number}",
                     f"{order.placed_by_name} placed purchase order {order.number} (${total} before tax)"
                     + (f" for delivery {_when(order.delivery_date, order.delivery_window)}" if order.delivery_date else "")
                     + ". Please confirm it in the Supplier Hub.")
    return order


def confirm_order(order: SupplierPurchaseOrder, *, user, expected_delivery=None, note: str = "",
                  delivery_window: str = "", signature=None) -> None:
    """Confirm the order. With a signature (every confirmation from the Supplier Hub), the store signs it."""
    from app.services import supplier_signing

    if order.status != PO_PLACED:
        raise SupplierHubError("This order has already been answered.")
    if signature is not None:
        supplier_signing._require_valid(signature)
    order.status = PO_CONFIRMED
    order.expected_delivery = _date(expected_delivery, "expected delivery date", required=False) if isinstance(expected_delivery, str) else expected_delivery
    order.supplier_note = (note or "").strip() or None
    order.supplier_responded_by_name = _display(user)
    order.supplier_responded_at = datetime.utcnow()
    order.scheduled_date = order.expected_delivery or order.delivery_date
    order.scheduled_window = (delivery_window or "").strip()[:60] or order.delivery_window
    _event(order.share, "ORDER_CONFIRMED", "SUPPLIER", order.supplier_responded_by_name,
           f"{order.number}" + (f", delivery {_when(order.scheduled_date, order.scheduled_window)}" if order.scheduled_date else ""))
    if signature is not None:
        supplier_signing.sign_order_confirmation(order, user=user, signature=signature)
        _event(order.share, "ORDER_SIGNED", "SUPPLIER", order.supplier_responded_by_name,
               f"{order.number} signed by {signature.name}; signed purchase order completed")
    db.session.commit()
    _notify_contractor(order, f"{order.number} confirmed by {order.supplier_responded_by_name}",
                       f"{order.supplier_responded_by_name} confirmed purchase order {order.number}"
                       + (f" for delivery {_when(order.scheduled_date, order.scheduled_window)}." if order.scheduled_date else "."))


def report_order_problem(order: SupplierPurchaseOrder, *, user, note: str) -> None:
    if order.status != PO_PLACED:
        raise SupplierHubError("This order has already been answered.")
    detail = (note or "").strip()
    if not detail:
        raise SupplierHubError("Describe the problem (for example a price change or an item out of stock).")
    order.status = PO_PROBLEM
    order.supplier_note = detail
    order.supplier_responded_by_name = _display(user)
    order.supplier_responded_at = datetime.utcnow()
    _event(order.share, "ORDER_PROBLEM", "SUPPLIER", order.supplier_responded_by_name, detail)
    from app.services.supplier_signing import void_order_signing

    void_order_signing(order, reason=f"Supplier reported a problem: {detail}", user=user)
    db.session.commit()


# ------------------------------------------------------------------ supplier-side queries (fail closed)

def supplier_shares(supplier_id: int, *, kind: Optional[str] = None):
    query = SupplierRequestShare.query.filter(SupplierRequestShare.supplier_id == supplier_id,
                                              SupplierRequestShare.status != SHARE_WITHDRAWN)
    if kind:
        query = query.filter(SupplierRequestShare.request_kind == kind)
    return query.order_by(SupplierRequestShare.sent_at.desc()).all()


def supplier_share(supplier_id: int, share_id: int) -> SupplierRequestShare:
    share = SupplierRequestShare.query.filter_by(id=share_id, supplier_id=supplier_id).first()
    if share is None or share.status == SHARE_WITHDRAWN:
        raise SupplierHubError("Not found.")
    return share


def supplier_order(supplier_id: int, order_id: int) -> SupplierPurchaseOrder:
    order = SupplierPurchaseOrder.query.filter_by(id=order_id, supplier_id=supplier_id).first()
    if order is None:
        raise SupplierHubError("Not found.")
    return order


def supplier_orders(supplier_id: int):
    return (SupplierPurchaseOrder.query.filter_by(supplier_id=supplier_id)
            .order_by(SupplierPurchaseOrder.placed_at.desc()).all())


def dashboard(supplier_id: int) -> dict:
    """Measured figures only, for one supplier account (assessment §4)."""
    from app.services.deck_takeoff import storage

    shares = SupplierRequestShare.query.filter_by(supplier_id=supplier_id).all()
    visible = [s for s in shares if s.status != SHARE_WITHDRAWN]
    returned = [s for s in visible if s.status == SHARE_RETURNED]
    orders = SupplierPurchaseOrder.query.filter_by(supplier_id=supplier_id).all()
    lines_requested = sum(len(s.shared_json.get("lines") or []) or 1 for s in visible)
    lines_recorded = 0
    costs_approved = 0
    for share in returned:
        if share.request_kind != KIND_MATERIAL or not share.response_ref:
            continue
        try:
            for follow in storage.list_responses(share.organization_id, share.project_id):
                if follow.get("records_response") == share.response_ref and follow.get("stage") == "RECORDED":
                    lines_recorded += sum(1 for r in follow.get("results") or [] if r.get("recorded"))
        except storage.TakeoffStorageError:
            continue
        lines, _ = material_order_lines(share)
        costs_approved += sum(1 for line in lines if line["cost_approved"])
    minutes = [s.minutes_reported for s in returned if s.minutes_reported is not None]
    contractors = {}
    for share in visible:
        org = db.session.get(Organization, share.organization_id)
        name = getattr(org, "display_name", None) or getattr(org, "name", None) or share.organization_id
        contractors[name] = contractors.get(name, 0) + 1
    return {
        "requests_received": len(visible),
        "quotes_returned": len(returned),
        "lines_requested": lines_requested,
        "lines_recorded": lines_recorded,
        "costs_approved": costs_approved,
        "orders_placed": len(orders),
        "orders_confirmed": sum(1 for o in orders if o.status == PO_CONFIRMED),
        "orders_with_problem": sum(1 for o in orders if o.status == PO_PROBLEM),
        "ordered_value": sum((Decimal(o.total) for o in orders if o.status in (PO_PLACED, PO_CONFIRMED)), Decimal("0")),
        "average_minutes": (sum(minutes) / len(minutes)) if minutes else None,
        "quotes_with_minutes": len(minutes),
        "lines_per_request": (lines_requested / len(visible)) if visible else None,
        "contractors": sorted(contractors.items()),
    }


# ------------------------------------------------------------------ supplier branding (Joel, 17 Oct 2026)

LOGO_MAX_BYTES = 2 * 1024 * 1024
_LOGO_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
)
_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def supplier_brand(supplier_id: int):
    from app.models.supplier_portal import SupplierBrandProfile

    return SupplierBrandProfile.query.filter_by(supplier_id=supplier_id).first()


def _logo_mime(data: bytes) -> str:
    for signature, mime in _LOGO_SIGNATURES:
        if data.startswith(signature):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise SupplierHubError("The logo must be a PNG, JPEG or WebP image.")


def save_supplier_brand(*, organization_id: str, supplier: Supplier, actor_name: str, display_name: str = "",
                        primary_color: str = "", logo: Optional[bytes] = None, remove_logo: bool = False):
    import hashlib

    from app.models.supplier_portal import SupplierBrandProfile

    if ContractorSupplierAccount.query.filter_by(organization_id=organization_id, supplier_id=supplier.id).first() is None:
        raise SupplierHubError("This supplier has no account with your company.")
    color = (primary_color or "").strip()
    if color and not _COLOR_RE.match(color):
        raise SupplierHubError("The colour must look like #1F4E8C.")
    brand = supplier_brand(supplier.id) or SupplierBrandProfile(supplier_id=supplier.id)
    brand.display_name = (display_name or "").strip()[:160] or None
    brand.primary_color = color.upper() or None
    if logo:
        if len(logo) > LOGO_MAX_BYTES:
            raise SupplierHubError("The logo is larger than 2 MB.")
        brand.logo_mime = _logo_mime(logo)
        brand.logo_bytes = logo
        brand.logo_sha256 = hashlib.sha256(logo).hexdigest()
    elif remove_logo:
        brand.logo_bytes = brand.logo_mime = brand.logo_sha256 = None
    brand.updated_by_name = (actor_name or "Office")[:160]
    brand.updated_by_organization_id = organization_id
    brand.updated_at = datetime.utcnow()
    db.session.add(brand)
    db.session.commit()
    return brand


def readable_text_color(hex_color: Optional[str]) -> str:
    """Dark or white text on the brand colour, whichever reads better (WCAG relative luminance)."""
    if not hex_color or not _COLOR_RE.match(hex_color):
        return "#ffffff"
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    luminance = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return "#111111" if luminance > 0.4 else "#ffffff"



# ------------------------------------------------------------------ delivery schedule (Joel, 17 Oct 2026)
# Either side may propose a change; nothing changes until the other side accepts. Notices go by email
# now; texts (SMS) will be added later through the same _notify functions.

def _when(day, window=None) -> str:
    if day is None:
        return "date to be set"
    text = day.strftime("%a %b %d, %Y").replace(" 0", " ")
    return f"{text}, {window}" if window else text


def current_schedule(order) -> dict:
    agreed = order.scheduled_date is not None
    return {
        "date": order.scheduled_date if agreed else order.delivery_date,
        "window": order.scheduled_window if agreed else order.delivery_window,
        "agreed": agreed,
    }


def concrete_delivery(concrete) -> dict:
    """A concrete request's delivery: the date first requested, and the order's current delivery if it was ordered.

    {"requested": (date, window), "order": order or None, "schedule": current_schedule or None, "pending": change or None}
    """
    from app.models.supplier_portal import SOURCE_CONCRETE, SupplierRequestShare

    order = (SupplierPurchaseOrder.query.join(SupplierRequestShare, SupplierPurchaseOrder.share_id == SupplierRequestShare.id)
             .filter(SupplierRequestShare.organization_id == concrete.organization_id,
                     SupplierRequestShare.source_kind == SOURCE_CONCRETE,
                     SupplierRequestShare.source_ref == str(concrete.id),
                     SupplierPurchaseOrder.status.in_((PO_PLACED, PO_CONFIRMED, PO_PROBLEM)))
             .order_by(SupplierPurchaseOrder.id.desc()).first())
    return {
        "requested": (concrete.delivery_date, concrete.delivery_window),
        "order": order,
        "schedule": current_schedule(order) if order is not None else None,
        "pending": pending_change(order) if order is not None else None,
    }


def pending_change(order):
    from app.models.supplier_portal import CHANGE_PENDING, SupplierDeliveryChange

    return (SupplierDeliveryChange.query.filter_by(order_id=order.id, status=CHANGE_PENDING)
            .order_by(SupplierDeliveryChange.id.desc()).first())


def change_history(order):
    from app.models.supplier_portal import SupplierDeliveryChange

    return SupplierDeliveryChange.query.filter_by(order_id=order.id).order_by(SupplierDeliveryChange.id.asc()).all()


def _other_side(side: str) -> str:
    return "SUPPLIER" if side == "CONTRACTOR" else "CONTRACTOR"


def request_delivery_change(order, *, side: str, user, new_date, new_window: str = "", reason: str = "",
                            note: str = "", counter_of=None, signature=None):
    """Ask for a new delivery. With a signature (every change asked for on screen), the asking side signs it.
    A change proposed automatically when the schedule moves carries no typed signature."""
    from app.models.supplier_portal import CHANGE_REASONS, SupplierDeliveryChange
    from app.services import supplier_signing

    if signature is not None:
        supplier_signing._require_valid(signature)

    if order.status not in (PO_PLACED, PO_CONFIRMED):
        raise SupplierHubError("Only an open order's delivery can be changed.")
    if counter_of is None and pending_change(order) is not None:
        raise SupplierHubError("A delivery change is already waiting for an answer. Answer or withdraw it first.")
    day = _date(new_date, "new delivery date") if isinstance(new_date, str) else new_date
    if reason not in CHANGE_REASONS:
        raise SupplierHubError("Choose a reason for the change.")
    schedule = current_schedule(order)
    change = SupplierDeliveryChange(
        order_id=order.id, requested_by_side=side, requested_by_name=_display(user), requested_at=datetime.utcnow(),
        previous_date=schedule["date"], previous_window=schedule["window"], new_date=day,
        new_window=(new_window or "").strip()[:60] or None, reason=reason, note=(note or "").strip() or None,
        status="PENDING", counter_of_id=counter_of.id if counter_of is not None else None,
    )
    db.session.add(change)
    _event(order.share, "DELIVERY_CHANGE_REQUESTED", side, change.requested_by_name,
           f"{order.number}: {_when(schedule['date'], schedule['window'])} → {_when(day, change.new_window)} ({reason})"
           + (f"; signed by {signature.name}" if signature is not None else ""))
    supplier_signing.open_change_signing(change, user=user, signature=signature)
    db.session.commit()
    message = (f"{change.requested_by_name} asks to move the delivery for {order.number} "
               f"from {_when(schedule['date'], schedule['window'])} to {_when(day, change.new_window)}. "
               f"Reason: {reason}." + (f" Note: {change.note}" if change.note else "")
               + " Please accept it, propose another time or decline.")
    subject = f"Delivery change requested: {order.number} → {_when(day, change.new_window)}"
    (_notify_supplier if side == "CONTRACTOR" else _notify_contractor)(order, subject, message)
    return change


def answer_delivery_change(change, *, side: str, user, action: str, note: str = "", counter_date=None,
                           counter_window: str = "", counter_reason: str = "Other", signature=None):
    """Accept (signed), decline, or propose another time (signed, as a new change). Accepting or proposing from a
    screen always carries a signature; declining needs none, because nothing is agreed."""
    from app.services import supplier_signing

    order = change.order
    if change.status != "PENDING":
        raise SupplierHubError("This change has already been answered.")
    if side != _other_side(change.requested_by_side):
        raise SupplierHubError("The other side answers this change.")
    if signature is not None and action in ("accept", "counter"):
        supplier_signing._require_valid(signature)
    who = _display(user)
    change.answered_by_name = who
    change.answered_at = datetime.utcnow()
    change.answer_note = (note or "").strip() or None
    if action == "accept":
        change.status = "ACCEPTED"
        order.scheduled_date = change.new_date
        order.scheduled_window = change.new_window
        order.delivery_date = change.new_date
        order.delivery_window = change.new_window
        if order.expected_delivery is not None:
            # Joel, 19 Oct 2026 (sync review G3): the date the supplier confirmed follows the agreed change, so no
            # screen shows the old one as current. The earlier dates stay in the change history.
            order.expected_delivery = change.new_date
        detail = f"{order.number}: now {_when(change.new_date, change.new_window)}"
        if signature is not None:
            supplier_signing.sign_change_acceptance(change, side=side, user=user, signature=signature)
            detail += f"; signed by {signature.name}; signed delivery change completed"
        _event(order.share, "DELIVERY_CHANGE_ACCEPTED", side, who, detail)
        db.session.commit()
        subject = f"Delivery change accepted: {order.number} is now {_when(change.new_date, change.new_window)}"
        body = f"{who} accepted the delivery change. {order.number} is now scheduled for {_when(change.new_date, change.new_window)}."
    elif action == "decline":
        if not change.answer_note:
            raise SupplierHubError("Say why you cannot accept the change.")
        change.status = "DECLINED"
        current = current_schedule(order)
        supplier_signing.void_change_signing(change, reason=f"Declined: {change.answer_note}", user=user)
        _event(order.share, "DELIVERY_CHANGE_DECLINED", side, who, f"{order.number}: {change.answer_note}")
        db.session.commit()
        subject = f"Delivery change declined: {order.number}"
        body = (f"{who} declined the delivery change: {change.answer_note}. "
                f"{order.number} stays scheduled for {_when(current['date'], current['window'])}.")
    elif action == "counter":
        change.status = "COUNTERED"
        supplier_signing.void_change_signing(change, reason="Another time was proposed", user=user)
        db.session.flush()
        counter = request_delivery_change(order, side=side, user=user, new_date=counter_date,
                                          new_window=counter_window, reason=counter_reason,
                                          note=note, counter_of=change, signature=signature)
        return counter
    else:
        raise SupplierHubError("Choose accept, propose another time or decline.")
    (_notify_contractor if side == "SUPPLIER" else _notify_supplier)(order, subject, body)
    return change


def withdraw_delivery_change(change, *, side: str, user):
    if change.status != "PENDING":
        raise SupplierHubError("This change has already been answered.")
    if side != change.requested_by_side:
        raise SupplierHubError("Only the side that asked can withdraw the change.")
    change.status = "WITHDRAWN"
    change.answered_by_name = _display(user)
    change.answered_at = datetime.utcnow()
    from app.services.supplier_signing import void_change_signing

    void_change_signing(change, reason="Withdrawn by the side that asked", user=user)
    _event(change.order.share, "DELIVERY_CHANGE_WITHDRAWN", side, change.answered_by_name, change.order.number)
    db.session.commit()


def _send(users, subject: str, body: str, link: str, order) -> None:
    """Email every recipient; also text those who entered a mobile number and agreed to texts."""
    from app.models.transactional_message import TEMPLATE_DELIVERY_SCHEDULE
    from app.services.text_messages import send_text_to_user
    from app.services.transactional_email import send_transactional_message

    seen = set()
    for user in users:
        if user is None or not user.is_active or user.id in seen:
            continue
        seen.add(user.id)
        try:
            send_transactional_message(TEMPLATE_DELIVERY_SCHEDULE, user.email,
                                       variables={"subject": subject, "body": body, "link": link},
                                       related_type="supplier_purchase_order", related_id=order.id)
        except Exception:
            pass  # a notice never blocks the schedule record itself
        try:
            send_text_to_user(user, f"{body} {link}", related_type="supplier_purchase_order", related_id=order.id)
        except Exception:
            pass


def _notify_supplier(order, subject: str, body: str) -> None:
    from app.services.signing_mail import public_signing_url

    members = SupplierUserMembership.query.filter_by(supplier_id=order.supplier_id, status=MEMBERSHIP_ACTIVE).all()
    link = public_signing_url(f"/supplier/{order.supplier_id}/requests/{order.share_id}")
    _send([m.user for m in members], subject, body, link, order)
    from app.models.supplier_portal import SupplierNotificationNumber
    from app.services.text_messages import send_text

    for extra in SupplierNotificationNumber.query.filter_by(supplier_id=order.supplier_id, active=True):
        try:
            send_text(extra.mobile_phone, f"{body} {link}", related_type="supplier_purchase_order", related_id=order.id)
        except Exception:
            pass


def _notify_contractor(order, subject: str, body: str) -> None:
    from app.services.signing_mail import public_signing_url

    ids = [i for i in (order.placed_by_user_id, order.share.sent_by_user_id) if i]
    link = public_signing_url(f"/projects/{order.project_id}/supplier-requests#share-{order.share_id}")
    _send([db.session.get(User, i) for i in ids], subject, body, link, order)


def upcoming_deliveries(*, organization_id: Optional[str] = None, supplier_id: Optional[int] = None,
                        project_id: Optional[int] = None):
    query = SupplierPurchaseOrder.query.filter(SupplierPurchaseOrder.status.in_((PO_PLACED, PO_CONFIRMED, PO_PROBLEM)))
    if organization_id:
        query = query.filter(SupplierPurchaseOrder.organization_id == organization_id)
    if supplier_id:
        query = query.filter(SupplierPurchaseOrder.supplier_id == supplier_id)
    if project_id:
        query = query.filter(SupplierPurchaseOrder.project_id == project_id)
    rows = []
    for order in query.all():
        schedule = current_schedule(order)
        rows.append({"order": order, "schedule": schedule, "pending": pending_change(order),
                     "project": db.session.get(Project, order.project_id)})
    rows.sort(key=lambda r: (r["schedule"]["date"] or date.max, r["order"].id))
    return rows


MAX_EXTRA_NUMBERS = 2


def supplier_extra_numbers(supplier_id: int):
    from app.models.supplier_portal import SupplierNotificationNumber

    return (SupplierNotificationNumber.query.filter_by(supplier_id=supplier_id, active=True)
            .order_by(SupplierNotificationNumber.id.asc()).all())


def add_supplier_extra_number(supplier_id: int, *, user, name: str, mobile_phone: str, consent: bool):
    from app.models.supplier_portal import SupplierNotificationNumber
    from app.services.text_messages import normalize_phone

    if len(supplier_extra_numbers(supplier_id)) >= MAX_EXTRA_NUMBERS:
        raise SupplierHubError("Remove a number before adding another.")
    who = (name or "").strip()
    if not who:
        raise SupplierHubError("Enter the person's name.")
    phone = normalize_phone(mobile_phone)
    if not phone:
        raise SupplierHubError("Enter the mobile number.")
    if not consent:
        raise SupplierHubError("Confirm that this person agreed to receive texts.")
    row = SupplierNotificationNumber(supplier_id=supplier_id, name=who[:160], mobile_phone=phone,
                                     consent_confirmed_by_name=_display(user), consent_confirmed_at=datetime.utcnow(),
                                     active=True)
    db.session.add(row)
    db.session.commit()
    return row


def remove_supplier_extra_number(supplier_id: int, number_id: int) -> None:
    from app.models.supplier_portal import SupplierNotificationNumber

    row = SupplierNotificationNumber.query.filter_by(id=number_id, supplier_id=supplier_id, active=True).first()
    if row is None:
        raise SupplierHubError("Not found.")
    row.active = False
    row.removed_at = datetime.utcnow()
    db.session.commit()



# ------------------------------------------------------------------ project schedule → delivery (Joel, 17 Oct 2026)

def _schedule_item_for(project, schedule_item_id):
    """Only an active schedule item on the same project may be linked."""
    if not schedule_item_id:
        return None
    from app.models.schedule import WorkScheduleItem

    try:
        item_id = int(schedule_item_id)
    except (TypeError, ValueError):
        return None
    item = WorkScheduleItem.query.filter_by(id=item_id, project_id=project.id,
                                            organization_id=project.organization_id).first()
    if item is None:
        raise SupplierHubError("Choose a schedule item on this project.")
    return item.id


def schedule_items_for_project(project):
    from app.models.schedule import WorkScheduleItem

    return (WorkScheduleItem.query.filter_by(project_id=project.id, organization_id=project.organization_id,
                                             status="ACTIVE")
            .order_by(WorkScheduleItem.scheduled_start.asc(), WorkScheduleItem.id.asc()).all())


def schedule_item_label(item) -> str:
    element = getattr(item, "element", None)
    activity = getattr(item, "activity", None)
    name = (getattr(activity, "display_name", None) or getattr(activity, "name", None)
            or getattr(element, "display_name", None) or f"Schedule item {item.id}")
    return f"{name} ({item.scheduled_start.isoformat()} – {item.scheduled_end.isoformat()})"


class _ScheduleActor:
    id = None
    email = ""
    display_name = "Project schedule"


def _schedule_actor():
    """The signed-in person who moved the schedule, or a neutral label outside a request."""
    from flask import has_request_context
    from flask_login import current_user

    if has_request_context() and getattr(current_user, "is_authenticated", False):
        return current_user
    return _ScheduleActor()


def _schedule_attention(message: str) -> None:
    """Tell the person who moved the schedule about a delivery they must answer themselves."""
    from flask import g, has_app_context

    if has_app_context():
        g.schedule_delivery_attention = getattr(g, "schedule_delivery_attention", []) + [message]


def propose_deliveries_for_schedule_moves(moves) -> list:
    """For each moved schedule item, propose moving its linked open deliveries by the same number of days.

    Proposed by the contractor side and sent to the supplier to accept, decline or counter; the agreed
    delivery stands until then.

    A move while a change is already waiting (Joel, 19 Oct 2026, release blocker found by the
    schedule synchronization review): the supplier must never be left answering a date the work no
    longer has.
    - Our own waiting request (the contractor's) is replaced: it is withdrawn and one fresh request
      for the new date goes to the supplier, saying which request it replaces. If the work is back
      on the agreed date, the request is withdrawn and the supplier is told the agreed delivery stands.
    - A change the supplier asked for is theirs to have answered: it is not touched, and the person
      who moved the work is told to answer it (the agreed delivery stands meanwhile).
    """
    from app.models.schedule import WorkScheduleItem

    proposed = []
    for item_id, prior_start in moves:
        item = db.session.get(WorkScheduleItem, item_id)
        if item is None or prior_start is None:
            continue
        delta = item.scheduled_start - prior_start
        if not delta.days:
            continue
        orders = SupplierPurchaseOrder.query.filter(
            SupplierPurchaseOrder.schedule_item_id == item.id,
            SupplierPurchaseOrder.status.in_((PO_PLACED, PO_CONFIRMED)),
        ).all()
        work = schedule_item_label(item).rsplit(" (", 1)[0]
        moved = (f"{work} moved from {prior_start.isoformat()} to {item.scheduled_start.isoformat()} "
                 f"({delta.days:+d} day{'s' if abs(delta.days) != 1 else ''}).")
        for order in orders:
            schedule = current_schedule(order)
            if schedule["date"] is None:
                continue
            waiting = pending_change(order)
            if waiting is not None and waiting.requested_by_side == "SUPPLIER":
                _event(order.share, "SCHEDULE_MOVED_CHANGE_PENDING", "CONTRACTOR", "CalibraytAI",
                       f"{order.number}: schedule item moved {delta.days:+d} days; the supplier's own change is waiting for an answer")
                db.session.commit()
                _schedule_attention(
                    f"{order.number} ({order.share.supplier.legal_name}): the supplier asked to move this delivery to "
                    f"{_when(waiting.new_date, waiting.new_window)} and is waiting for your answer. The work now starts "
                    f"{item.scheduled_start.isoformat()}. Answer it (accept, propose another time or decline) on the "
                    f"project's supplier requests page. Until then the agreed delivery stands.")
                continue
            if waiting is not None:
                replaced_date, replaced_window = waiting.new_date, waiting.new_window
                target = replaced_date + delta
                withdraw_delivery_change(waiting, side="CONTRACTOR", user=_schedule_actor())
                if target == schedule["date"]:
                    _notify_supplier(
                        order,
                        f"Delivery change withdrawn: {order.number} stays {_when(schedule['date'], schedule['window'])}",
                        f"The request to move {order.number} to {_when(replaced_date, replaced_window)} is withdrawn: "
                        f"{moved} The agreed delivery stands: {_when(schedule['date'], schedule['window'])}.",
                    )
                    continue
                change = request_delivery_change(
                    order, side="CONTRACTOR", user=_schedule_actor(), new_date=target,
                    new_window=replaced_window or schedule["window"] or "", reason="Project schedule change",
                    note=f"{moved} This replaces the earlier request for {_when(replaced_date, replaced_window)}.",
                )
                proposed.append(change)
                continue
            change = request_delivery_change(
                order, side="CONTRACTOR", user=_schedule_actor(), new_date=schedule["date"] + delta,
                new_window=schedule["window"] or "", reason="Project schedule change",
                note=moved,
            )
            proposed.append(change)
    return proposed

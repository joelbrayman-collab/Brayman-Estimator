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
    return lines, []


def order_lines(share):
    return concrete_order_lines(share) if share.request_kind == KIND_CONCRETE else material_order_lines(share)


def place_order(share: SupplierRequestShare, *, user, delivery_date=None, site_contact: str = "",
                notes: str = "") -> SupplierPurchaseOrder:
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
    db.session.commit()
    return order


def confirm_order(order: SupplierPurchaseOrder, *, user, expected_delivery=None, note: str = "") -> None:
    if order.status != PO_PLACED:
        raise SupplierHubError("This order has already been answered.")
    order.status = PO_CONFIRMED
    order.expected_delivery = _date(expected_delivery, "expected delivery date", required=False) if isinstance(expected_delivery, str) else expected_delivery
    order.supplier_note = (note or "").strip() or None
    order.supplier_responded_by_name = _display(user)
    order.supplier_responded_at = datetime.utcnow()
    _event(order.share, "ORDER_CONFIRMED", "SUPPLIER", order.supplier_responded_by_name,
           f"{order.number}" + (f", delivery {order.expected_delivery.isoformat()}" if order.expected_delivery else ""))
    db.session.commit()


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

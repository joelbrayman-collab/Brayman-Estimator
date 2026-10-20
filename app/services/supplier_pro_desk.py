"""Supplier PRO Desk: walk-in quotations owned by a supplier (ADR-047 Amendment 1; Joel, 20 Oct 2026).

Reuses: supplier identity and membership (supplier_hub), supplier products and canonical-to-product maps
(supplier_catalogue), canonical identities (the ADR-057 ``ensure_identity`` pattern), the outbuilding
takeoff, the drawing engine and the transactional email service. Adds only what a supplier's own customer
quotation needs.

Every function takes a supplier the caller has already been checked against, and every lookup filters by
it. Nothing here reads or writes a contractor organization's records.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import secrets
from datetime import date, datetime, timedelta
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple

from app import db
from app.models.canonical_material import CanonicalMaterial
from app.models.supplier_catalogue import CanonicalMaterialSupplierMap, SupplierLocation, SupplierProduct
from app.models.supplier_quote import (
    ACCEPT_EMAIL,
    ACCEPT_IN_PERSON,
    ACCEPT_LINK,
    ACCEPT_PHONE,
    QUOTE_ACCEPTED,
    QUOTE_CANCELLED,
    QUOTE_DECLINED,
    QUOTE_DRAFT,
    QUOTE_ISSUED,
    SupplierCustomer,
    SupplierPriceImport,
    SupplierQuote,
    SupplierQuoteEvent,
    SupplierQuoteFile,
    SupplierQuoteLink,
    SupplierQuoteSettings,
    SupplierSellingPrice,
    ASSEMBLY_ACTIVE,
    ASSEMBLY_RETIRED,
    SupplierBuildingAssembly,
)
from app.services.outbuilding import spec as S
from app.services.outbuilding import takeoff as T

CENT = Decimal("0.01")
MAX_SKETCH_BYTES = 10 * 1024 * 1024
MAX_SKETCHES = 6
MAX_PRICE_FILE_BYTES = 5 * 1024 * 1024
MAX_PRICE_ROWS = 20000
LINK_DAYS = 30
# Sales units that are sold whole: the converted quantity is rounded up to a whole unit.
WHOLE_UNITS = {"EA", "PC", "PCS", "PIECE", "PKG", "BOX", "BX", "BUNDLE", "BDL", "ROLL", "PAIL", "BAG", "SHEET", "LENGTH"}
SKETCH_TYPES = (
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"%PDF-", "application/pdf", ".pdf"),
)

PRICED = "PRICED"
NO_PRODUCT = "NO_PRODUCT"
NO_PRICE = "NO_PRICE"
NO_QUANTITY = "NO_QUANTITY"
EXCLUDED = "EXCLUDED"
BY_DESIGN = "BY_DESIGN"


class ProDeskError(ValueError):
    pass


def _now():
    return datetime.utcnow()


def _event(quote: SupplierQuote, event_type: str, actor: str, side: str = "SUPPLIER", **detail):
    db.session.add(SupplierQuoteEvent(quote_id=quote.id, event_type=event_type, actor_side=side,
                                      actor_name=(actor or "Unknown")[:160], at=_now(),
                                      detail_json=detail or None))


def _actor(user) -> str:
    name = (getattr(user, "display_name", None) or getattr(user, "email", None) or "").strip()
    if not name:
        raise ProDeskError("The person doing this must be signed in.")
    return name[:160]


# ------------------------------------------------------------------ settings


def settings_for(supplier_id: int) -> Optional[SupplierQuoteSettings]:
    return SupplierQuoteSettings.query.filter_by(supplier_id=supplier_id).first()


def _money(raw, label, *, allow_blank=True) -> Optional[Decimal]:
    text = (raw or "").strip().replace("$", "").replace(",", "")
    if not text:
        if allow_blank:
            return None
        raise ProDeskError(f"{label} is required.")
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ProDeskError(f"{label} must be a number.")
    if not value.is_finite() or value < 0:
        raise ProDeskError(f"{label} must be zero or more.")
    return value


def save_settings(supplier, form, *, user) -> SupplierQuoteSettings:
    actor = _actor(user)
    rate = _money(form.get("tax_rate_percent"), "Tax rate")
    if rate is not None and rate > 30:
        raise ProDeskError("Tax rate looks wrong: enter a percentage such as 13.")
    days_text = (form.get("validity_days") or "").strip()
    try:
        days = int(days_text) if days_text else None
    except ValueError:
        raise ProDeskError("Quote validity must be a whole number of days.")
    if days is not None and not 1 <= days <= 180:
        raise ProDeskError("Quote validity must be between 1 and 180 days.")
    row = settings_for(supplier.id) or SupplierQuoteSettings(supplier_id=supplier.id, updated_by_name=actor)
    row.tax_label = (form.get("tax_label") or "").strip()[:20] or None
    row.tax_rate_percent = rate
    row.validity_days = days
    row.default_delivery_charge = _money(form.get("default_delivery_charge"), "Default delivery charge")
    row.terms_text = (form.get("terms_text") or "").strip()[:4000] or None
    row.contact_line = (form.get("contact_line") or "").strip()[:300] or None
    row.updated_by_name = actor
    row.updated_at = _now()
    db.session.add(row)
    db.session.commit()
    return row


def settings_blockers(supplier_id: int) -> List[str]:
    row = settings_for(supplier_id)
    out = []
    if row is None or row.tax_rate_percent is None or not row.tax_label:
        out.append("Set the sales tax label and rate in Quote settings.")
    if row is None or not row.validity_days:
        out.append("Set how many days a quotation is valid in Quote settings.")
    return out


# ------------------------------------------------------------------ customers and quotes


def _clean(raw, limit):
    return " ".join((raw or "").split())[:limit] or None


def _next_number(supplier_id: int) -> str:
    year = date.today().year
    prefix = f"Q{year}-"
    count = SupplierQuote.query.filter(SupplierQuote.supplier_id == supplier_id,
                                       SupplierQuote.number.like(f"{prefix}%")).count()
    return f"{prefix}{count + 1:04d}"


def start_quote(supplier, form, *, user, demo_synthetic: bool = False) -> SupplierQuote:
    """A new walk-in customer and their draft quotation, with the consent they gave at the counter."""
    actor = _actor(user)
    name = _clean(form.get("customer_name"), 160)
    if not name:
        raise ProDeskError("Enter the customer's name.")
    email = (form.get("customer_email") or "").strip().lower()[:254] or None
    if email and ("@" not in email or " " in email or email.startswith("@") or email.endswith("@")):
        raise ProDeskError("The customer's email address does not look right.")
    phone = _clean(form.get("customer_phone"), 30)
    consent_email = form.get("consent_email") == "yes"
    consent_text = form.get("consent_text") == "yes"
    if consent_email and not email:
        raise ProDeskError("Email consent needs an email address.")
    if consent_text and not phone:
        raise ProDeskError("Text consent needs a phone number.")
    location = None
    location_id = (form.get("location_id") or "").strip()
    if location_id:
        location = SupplierLocation.query.filter_by(id=int(location_id) if location_id.isdigit() else -1,
                                                    supplier_id=supplier.id).first()
        if location is None:
            raise ProDeskError("Choose one of this supplier's stores.")
    else:
        location = (SupplierLocation.query.filter_by(supplier_id=supplier.id, status="ACTIVE")
                    .order_by(SupplierLocation.id).first())
    now = _now()
    customer = SupplierCustomer(
        supplier_id=supplier.id, display_name=name, phone=phone, email=email,
        address=_clean(form.get("customer_address"), 300), town=_clean(form.get("customer_town"), 120),
        consent_email=consent_email, consent_text=consent_text,
        consent_recorded_by_name=actor if (consent_email or consent_text) else None,
        consent_recorded_at=now if (consent_email or consent_text) else None,
        demo_synthetic=demo_synthetic, created_by_name=actor, created_at=now,
    )
    db.session.add(customer)
    db.session.flush()
    settings = settings_for(supplier.id)
    quote = SupplierQuote(
        supplier_id=supplier.id, supplier_location_id=location.id if location else None, customer_id=customer.id,
        number=_next_number(supplier.id), status=QUOTE_DRAFT, spec_json={"values": {}}, choices_json={},
        delivery_charge=settings.default_delivery_charge if settings else None,
        demo_synthetic=demo_synthetic, created_by_name=actor, created_at=now, updated_at=now,
    )
    db.session.add(quote)
    db.session.flush()
    _event(quote, "CREATED", actor, customer=name, consent_email=consent_email, consent_text=consent_text)
    db.session.commit()
    return quote


def supplier_quotes(supplier_id: int) -> List[SupplierQuote]:
    return (SupplierQuote.query.filter_by(supplier_id=supplier_id)
            .order_by(SupplierQuote.created_at.desc(), SupplierQuote.id.desc()).all())


def supplier_quote(supplier_id: int, quote_id: int) -> SupplierQuote:
    quote = SupplierQuote.query.filter_by(id=quote_id, supplier_id=supplier_id).first()
    if quote is None:
        raise ProDeskError("Not found.")
    return quote


def quote_events(quote: SupplierQuote) -> List[SupplierQuoteEvent]:
    return SupplierQuoteEvent.query.filter_by(quote_id=quote.id).order_by(SupplierQuoteEvent.at, SupplierQuoteEvent.id).all()


def _require_draft(quote: SupplierQuote):
    if quote.status != QUOTE_DRAFT:
        raise ProDeskError("This quotation has been issued. Start a revision to change it.")


# ------------------------------------------------------------------ sketch


def add_sketch(quote: SupplierQuote, *, filename: str, content: bytes, user) -> SupplierQuoteFile:
    """Keep a photo or PDF of the customer's sketch with the quote. Its type is read from its bytes."""
    actor = _actor(user)
    _require_draft(quote)
    if not content:
        raise ProDeskError("Choose a photo or PDF of the sketch.")
    if len(content) > MAX_SKETCH_BYTES:
        raise ProDeskError("The sketch file is larger than 10 MB. Take the photo at a lower size.")
    kind = next(((mime, ext) for magic, mime, ext in SKETCH_TYPES if content.startswith(magic)), None)
    if kind is None:
        raise ProDeskError("The sketch must be a JPEG or PNG photo, or a PDF.")
    if active_sketches(quote) and len(active_sketches(quote)) >= MAX_SKETCHES:
        raise ProDeskError(f"A quote keeps up to {MAX_SKETCHES} sketch files.")
    base = "".join(ch for ch in (filename or "sketch") if ch.isalnum() or ch in "-_ .")[:80].strip() or "sketch"
    row = SupplierQuoteFile(quote_id=quote.id, filename=base, mime=kind[0], size_bytes=len(content),
                            sha256=hashlib.sha256(content).hexdigest(), content=content, uploaded_by_name=actor,
                            uploaded_at=_now())
    db.session.add(row)
    db.session.flush()
    _event(quote, "SKETCH_ADDED", actor, file=base, sha256=row.sha256, bytes=len(content))
    db.session.commit()
    return row


def active_sketches(quote: SupplierQuote) -> List[SupplierQuoteFile]:
    return (SupplierQuoteFile.query.filter_by(quote_id=quote.id).filter(SupplierQuoteFile.removed_at.is_(None))
            .order_by(SupplierQuoteFile.id).all())


def sketch_for(quote: SupplierQuote, file_id: int) -> SupplierQuoteFile:
    row = SupplierQuoteFile.query.filter_by(id=file_id, quote_id=quote.id).filter(SupplierQuoteFile.removed_at.is_(None)).first()
    if row is None:
        raise ProDeskError("Not found.")
    return row


def remove_sketch(quote: SupplierQuote, file_id: int, *, user):
    actor = _actor(user)
    _require_draft(quote)
    row = sketch_for(quote, file_id)
    row.removed_at = _now()
    _event(quote, "SKETCH_REMOVED", actor, file=row.filename)
    db.session.commit()


# ------------------------------------------------------------------ building


def spec_values(quote: SupplierQuote) -> Dict:
    return dict((quote.spec_json or {}).get("values") or {})


def save_spec(quote: SupplierQuote, form, *, user) -> List[str]:
    """Save the guided answers. Returns the validation messages; valid answers are kept either way."""
    actor = _actor(user)
    _require_draft(quote)
    values, errors = S.read_answers(form)
    before = spec_values(quote)
    changed = sorted(k for k in set(before) | set(values) if before.get(k) != values.get(k))
    meta = {k: v for k, v in (quote.spec_json or {}).items() if k not in ("values", "confirmed_by", "confirmed_at")}
    assembly = meta.get("assembly")
    if assembly:  # say plainly where the detailed form departs from the store's standard
        overridden = sorted(set(meta.get("assembly_overridden") or []) |
                            {k for k in S.ASSEMBLY_KEYS if values.get(k) != (assembly.get("values") or {}).get(k)})
        meta["assembly_overridden"] = overridden
    quote.spec_json = {**meta, "values": values, "confirmed_by": actor,
                       "confirmed_at": _now().isoformat(timespec="seconds")}
    quote.building_system = values.get("building_system")
    quote.updated_at = _now()
    if changed:
        _event(quote, "BUILDING_CONFIRMED", actor, changed=changed)
    db.session.commit()
    return errors


def takeoff_for(quote: SupplierQuote) -> Dict:
    return T.takeoff(spec_values(quote))


# ------------------------------------------------------------------ standard assemblies and Quick Quote


def active_assemblies(supplier_id: int) -> List[SupplierBuildingAssembly]:
    return (SupplierBuildingAssembly.query.filter_by(supplier_id=supplier_id, status=ASSEMBLY_ACTIVE)
            .order_by(SupplierBuildingAssembly.name, SupplierBuildingAssembly.id).all())


def assembly_for(supplier_id: int, assembly_id) -> SupplierBuildingAssembly:
    try:
        ident = int(assembly_id)
    except (TypeError, ValueError):
        raise ProDeskError("Choose one of this store's standard buildings.")
    row = SupplierBuildingAssembly.query.filter_by(id=ident, supplier_id=supplier_id).first()
    if row is None:
        raise ProDeskError("Choose one of this store's standard buildings.")
    return row


def save_assembly(supplier, form, *, user, demo_synthetic: bool = False) -> Tuple[Optional[SupplierBuildingAssembly], List[str]]:
    """Record a store standard. Every answer is typed by the store; the basis says who it was checked with."""
    actor = _actor(user)
    values, errors = S.read_assembly(form)
    name = _clean(form.get("name"), 120)
    basis = _clean(form.get("basis"), 300)
    if not name:
        errors.insert(0, "Give the standard a name, e.g. \"Post-frame steel, 8 ft bays\".")
    if not basis:
        errors.insert(0, "Say what the standard is based on, e.g. who it was confirmed with.")
    if errors:
        return None, errors
    row = SupplierBuildingAssembly(supplier_id=supplier.id, name=name, building_system=values["building_system"],
                                   values_json=values, basis=basis, status=ASSEMBLY_ACTIVE, approved_by_name=actor,
                                   approved_at=_now(), demo_synthetic=demo_synthetic)
    db.session.add(row)
    db.session.commit()
    return row, []


def retire_assembly(supplier, assembly_id, *, user) -> SupplierBuildingAssembly:
    actor = _actor(user)
    row = assembly_for(supplier.id, assembly_id)
    if row.status != ASSEMBLY_RETIRED:
        row.status, row.retired_by_name, row.retired_at = ASSEMBLY_RETIRED, actor, _now()
        db.session.commit()
    return row


def _started_at(raw) -> Optional[str]:
    """When the Quick Quote page was opened (written by the server into the form), for the timing record."""
    try:
        at = datetime.fromisoformat((raw or "").strip())
    except ValueError:
        return None
    now = _now()
    return at.isoformat(timespec="seconds") if now - timedelta(hours=4) <= at <= now else None


def quick_quote(supplier, form, *, user, demo_synthetic: bool = False) -> Tuple[Optional[SupplierQuote], List[str]]:
    """Customer, standard building and the answers that change per building, in one step.

    Nothing is created when an answer is missing or wrong: the page comes back with the messages.
    """
    _actor(user)
    if not (form.get("assembly_id") or "").strip():
        return None, ["Choose one of this store's standard buildings, or use the detailed form."]
    try:
        assembly = assembly_for(supplier.id, form.get("assembly_id"))
    except ProDeskError as exc:
        return None, [str(exc)]
    if assembly.status != ASSEMBLY_ACTIVE:
        return None, ["That standard building has been retired. Choose a current one."]
    values, errors = S.read_quick(form, assembly.values_json or {})
    if not (form.get("customer_name") or "").strip():
        errors.insert(0, "Enter the customer's name.")
    if errors:
        return None, errors
    quote = start_quote(supplier, form, user=user, demo_synthetic=demo_synthetic)
    actor = _actor(user)
    quote.spec_json = {
        "values": values, "confirmed_by": actor, "confirmed_at": _now().isoformat(timespec="seconds"),
        "quick": True, "openings_placed": bool(values.get("openings")),
        "intake_started_at": _started_at(form.get("started_at")),
        "assembly": {"id": assembly.id, "name": assembly.name, "basis": assembly.basis,
                     "approved_by": assembly.approved_by_name,
                     "approved_at": assembly.approved_at.isoformat(timespec="seconds"),
                     "values": dict(assembly.values_json or {})},
    }
    quote.building_system = values.get("building_system")
    quote.updated_at = _now()
    _event(quote, "QUICK_QUOTE", actor, assembly=assembly.name, assembly_id=assembly.id,
           openings=len(values.get("openings") or []))
    db.session.commit()
    return quote, []


def record_printed(quote: SupplierQuote, *, user):
    """The first time the store opens the issued quotation PDF (the printable quotation) is timed."""
    if quote.status == QUOTE_DRAFT:
        return
    if SupplierQuoteEvent.query.filter_by(quote_id=quote.id, event_type="QUOTATION_PRINTED").first():
        return
    _event(quote, "QUOTATION_PRINTED", _actor(user))
    db.session.commit()


EXCEPTION_EVENTS = ("PRODUCT_MATCHED", "LINE_EXCLUDED", "LINE_RESET", "PRODUCT_CHOSEN")


def _seconds(a, b) -> Optional[int]:
    return round((b - a).total_seconds()) if a and b and b >= a else None


def quote_timing(quote: SupplierQuote) -> Dict:
    """Elapsed time per stage for one walk-in quotation, from what the store actually did (event times).

    Setup the store does once (price file, product matches, standard buildings) is not part of it; time
    spent matching products or leaving lines out during the quotation is reported as exception time.
    """
    events = quote_events(quote)
    first = {}
    for e in events:
        first.setdefault(e.event_type, e.at)
    meta = quote.spec_json or {}
    started = datetime.fromisoformat(meta["intake_started_at"]) if meta.get("intake_started_at") else None
    created = first.get("CREATED")
    confirmed = [e.at for e in events if e.event_type in ("BUILDING_CONFIRMED", "QUICK_QUOTE")]
    building_done = confirmed[-1] if confirmed else None
    issued = first.get("ISSUED")
    printed = first.get("QUOTATION_PRINTED")
    exceptions = [e for e in events if e.event_type in EXCEPTION_EVENTS and building_done and issued
                  and building_done <= e.at <= issued]
    exception_end = exceptions[-1].at if exceptions else None
    stages = [
        ("Customer and building answers", started, building_done if meta.get("quick") else created),
    ]
    if not meta.get("quick"):
        stages.append(("Building answers (detailed form)", created, building_done))
    stages += [
        ("Missing prices, product matches and lines left out (exceptions)", building_done, exception_end),
        ("Price review and issue", exception_end or building_done, issued),
        ("Open the printable quotation", issued, printed),
    ]
    rows = [{"stage": label, "seconds": _seconds(a, b), "from": a, "to": b} for label, a, b in stages]
    walk_in = _seconds(started or created, printed or issued)
    if walk_in is not None:  # shown as the sum of the stages, so the table adds up
        walk_in = sum(r["seconds"] or 0 for r in rows)
    exception_seconds = _seconds(building_done, exception_end) or 0
    return {"rows": rows, "walk_in_seconds": walk_in, "exception_seconds": exception_seconds,
            "exception_actions": len(exceptions), "started_recorded": started is not None,
            "quick": bool(meta.get("quick")), "printed": printed is not None}


def setup_record(supplier_id: int) -> Dict:
    """The one-time store setup behind quotations, kept apart from walk-in quotation time."""
    from app.models.supplier_catalogue import CanonicalMaterialSupplierMap as Map

    product_ids = [p.id for p in supplier_products_for(supplier_id)]
    maps = (Map.query.filter(Map.supplier_product_id.in_(product_ids)).all() if product_ids else [])
    imports = price_imports(supplier_id)
    assemblies = SupplierBuildingAssembly.query.filter_by(supplier_id=supplier_id).order_by(SupplierBuildingAssembly.id).all()
    return {"price_files": imports, "product_matches": len(maps), "assemblies": assemblies}


# ------------------------------------------------------------------ price file


PRICE_COLUMNS = ("sku", "description", "unit", "pack_qty", "price", "discount_percent", "discount_rule",
                 "effective_from", "effective_to", "availability", "store")
REQUIRED_PRICE_COLUMNS = ("sku", "description", "unit", "price", "effective_from")
AVAILABILITY = {"IN_STOCK", "LIMITED", "SPECIAL_ORDER", "UNKNOWN"}


def _date(text, label) -> Optional[date]:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"{label} must be a date like 2026-10-20")


def import_price_file(supplier, *, filename: str, content: bytes, authorized_by: str, user,
                      demo_synthetic: bool = False) -> SupplierPriceImport:
    """Load the supplier's own price file (CSV). Every row is checked; bad rows are listed, never guessed."""
    actor = _actor(user)
    authorized = " ".join((authorized_by or "").split())[:160]
    if not authorized:
        raise ProDeskError("Name the person at the supplier who authorized these prices.")
    if not content:
        raise ProDeskError("Choose the price file.")
    if len(content) > MAX_PRICE_FILE_BYTES:
        raise ProDeskError("The price file is larger than 5 MB.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ProDeskError("The price file must be a CSV saved as UTF-8.")
    reader = csv.DictReader(io.StringIO(text))
    headers = [(h or "").strip().lower() for h in (reader.fieldnames or [])]
    missing = [c for c in REQUIRED_PRICE_COLUMNS if c not in headers]
    if missing:
        raise ProDeskError("The price file needs these columns: " + ", ".join(missing) + ".")
    locations = {loc.code.upper(): loc for loc in SupplierLocation.query.filter_by(supplier_id=supplier.id).all()}
    record = SupplierPriceImport(supplier_id=supplier.id, filename=(filename or "prices.csv")[:200],
                                 file_sha256=hashlib.sha256(content).hexdigest(),
                                 source="DEMO_SYNTHETIC" if demo_synthetic else "SUPPLIER_FILE",
                                 authorized_by_name=authorized, imported_by_name=actor, imported_at=_now())
    db.session.add(record)
    db.session.flush()
    loaded, rejected = 0, []
    for n, raw in enumerate(reader, start=2):
        if n - 1 > MAX_PRICE_ROWS:
            rejected.append({"row": n, "reason": f"More than {MAX_PRICE_ROWS} rows; the rest were not read."})
            break
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items() if k}
        if not any(row.values()):
            continue
        try:
            sku = row.get("sku", "")[:80]
            if not sku:
                raise ValueError("SKU is blank")
            description = row.get("description", "")[:220]
            unit = row.get("unit", "").upper()[:20]
            if not description or not unit:
                raise ValueError("description and unit are required")
            try:
                price = Decimal(row.get("price", "").replace("$", "").replace(",", ""))
            except InvalidOperation:
                raise ValueError("price is not a number")
            if not price.is_finite() or price < 0:
                raise ValueError("price must be zero or more")
            pack = row.get("pack_qty", "")
            pack_qty = Decimal(pack) if pack else None
            disc = row.get("discount_percent", "")
            discount = Decimal(disc) if disc else None
            if discount is not None and not (0 <= discount <= 100):
                raise ValueError("discount_percent must be between 0 and 100")
            start = _date(row.get("effective_from"), "effective_from")
            if start is None:
                raise ValueError("effective_from is required")
            end = _date(row.get("effective_to"), "effective_to")
            if end is not None and end < start:
                raise ValueError("effective_to is before effective_from")
            availability = row.get("availability", "").upper().replace(" ", "_") or None
            if availability and availability not in AVAILABILITY:
                raise ValueError("availability must be IN_STOCK, LIMITED, SPECIAL_ORDER or UNKNOWN")
            store = row.get("store", "").upper()
            location = None
            if store:
                location = locations.get(store)
                if location is None:
                    raise ValueError(f"store {store} is not one of this supplier's stores")
        except (ValueError, InvalidOperation) as exc:
            rejected.append({"row": n, "sku": row.get("sku", ""), "reason": str(exc)})
            continue
        product = SupplierProduct.query.filter_by(supplier_id=supplier.id, sku=sku).first()
        if product is None:
            product = SupplierProduct(supplier_id=supplier.id, sku=sku, description=description, sales_uom=unit,
                                      pack_qty=pack_qty, status="ACTIVE", demo_synthetic=demo_synthetic,
                                      created_at=_now())
            db.session.add(product)
            db.session.flush()
        elif product.sales_uom.upper() != unit:
            rejected.append({"row": n, "sku": sku,
                             "reason": f"unit {unit} differs from this SKU's selling unit {product.sales_uom}"})
            continue
        db.session.add(SupplierSellingPrice(
            supplier_product_id=product.id, supplier_location_id=location.id if location else None,
            import_id=record.id, amount=price, currency="CAD", unit=unit, discount_percent=discount,
            discount_rule=row.get("discount_rule", "")[:160] or None, effective_from=start, effective_to=end,
            availability=availability, demo_synthetic=demo_synthetic, created_at=_now()))
        loaded += 1
    record.rows_read = loaded + len(rejected)
    record.rows_loaded = loaded
    record.rows_rejected = len(rejected)
    record.rejections_json = rejected[:500] or None
    db.session.commit()
    return record


def price_imports(supplier_id: int) -> List[SupplierPriceImport]:
    return SupplierPriceImport.query.filter_by(supplier_id=supplier_id).order_by(SupplierPriceImport.imported_at.desc()).all()


def current_price(product: SupplierProduct, location_id: Optional[int], on: date) -> Optional[SupplierSellingPrice]:
    """The newest price in effect on ``on``: this store's own price first, then the supplier-wide price."""
    query = (SupplierSellingPrice.query.filter_by(supplier_product_id=product.id)
             .filter(SupplierSellingPrice.effective_from <= on)
             .filter((SupplierSellingPrice.effective_to.is_(None)) | (SupplierSellingPrice.effective_to >= on)))
    for scope in ([location_id] if location_id else []) + [None]:
        row = (query.filter(SupplierSellingPrice.supplier_location_id.is_(scope) if scope is None
                            else SupplierSellingPrice.supplier_location_id == scope)
               .order_by(SupplierSellingPrice.created_at.desc(), SupplierSellingPrice.id.desc()).first())
        if row is not None:
            return row
    return None


# ------------------------------------------------------------------ products for takeoff lines


def _is_outbuilding_code(code: str) -> bool:
    return code.startswith("CAL-OB-") or code == "CAL-CONC"


def line_identity_seed(line: Dict) -> Dict:
    return {
        "code": line["code"], "display_name": line["item"][:220], "status": "ACTIVE", "kind": "GENERIC",
        "category": line.get("category") or T.category_for(line["code"]), "trade": "Outbuildings",
        "canonical_uom": line["uom"], "nominal_thickness_in": None, "nominal_width_in": None, "length_ft": None,
        "sheet_width_in": None, "sheet_length_in": None, "grade_species": None, "performance_class": None,
        "manufacturer": None, "specification_text": None, "substitution_policy": "ALLOWED",
        "description": "Outbuilding takeoff identity (Supplier PRO Desk). Supplier-neutral. No SKU or price.",
    }


def supplier_products_for(supplier_id: int) -> List[SupplierProduct]:
    return (SupplierProduct.query.filter_by(supplier_id=supplier_id, status="ACTIVE")
            .order_by(SupplierProduct.description).all())


def matches_for_code(supplier_id: int, code: str) -> List[Tuple[CanonicalMaterialSupplierMap, SupplierProduct]]:
    material = CanonicalMaterial.query.filter_by(code=code).first()
    if material is None:
        return []
    rows = (db.session.query(CanonicalMaterialSupplierMap, SupplierProduct)
            .join(SupplierProduct, CanonicalMaterialSupplierMap.supplier_product_id == SupplierProduct.id)
            .filter(CanonicalMaterialSupplierMap.canonical_material_id == material.id,
                    CanonicalMaterialSupplierMap.status == "ACTIVE",
                    SupplierProduct.supplier_id == supplier_id, SupplierProduct.status == "ACTIVE")
            .order_by(SupplierProduct.description).all())
    return rows


def match_product(supplier, line: Dict, *, product_id: int, sales_per_unit, user) -> CanonicalMaterialSupplierMap:
    """Record that one of this supplier's products serves a takeoff line, with its unit conversion.

    ``sales_per_unit`` is how many selling units one takeoff unit needs (e.g. 1/16 for lumber sold in
    16 ft pieces against a quantity in feet). Existing matches are never changed: a contractor's deck
    takeoff identities are out of reach, and an existing match with another conversion is refused.
    """
    from app.services.deck_takeoff.catalogue import ensure_identity
    from app.services.supplier_catalogue import approve_canonical_material_supplier_map

    actor = _actor(user)
    if not _is_outbuilding_code(line["code"]):
        raise ProDeskError("Only outbuilding takeoff lines are matched here.")
    product = SupplierProduct.query.filter_by(id=product_id, supplier_id=supplier.id, status="ACTIVE").first()
    if product is None:
        raise ProDeskError("Choose one of this supplier's products.")
    try:
        factor = Decimal(str(sales_per_unit))
    except InvalidOperation:
        raise ProDeskError("The conversion must be a number.")
    if not factor.is_finite() or factor <= 0:
        raise ProDeskError("The conversion must be more than zero.")
    material, _created = ensure_identity(line_identity_seed(line), actor_display_name=actor)
    existing = CanonicalMaterialSupplierMap.query.filter_by(canonical_material_id=material.id,
                                                            supplier_product_id=product.id).first()
    if existing is not None:
        current = Decimal(str(existing.requirement_to_sales_factor or 1))
        if current != factor:
            raise ProDeskError(f"{product.sku} is already matched to this line with a conversion of {current.normalize()}.")
        return existing
    return approve_canonical_material_supplier_map(canonical_material_id=material.id, supplier_product_id=product.id,
                                                   actor_display_name=actor, requirement_to_sales_factor=factor,
                                                   demo_synthetic=bool(product.demo_synthetic))


def choose_line(quote: SupplierQuote, *, code: str, product_id: Optional[int], exclude_reason: str, user):
    """Pick the product for a line on this quote, or leave the line out with a stated reason."""
    actor = _actor(user)
    _require_draft(quote)
    choices = dict(quote.choices_json or {})
    reason = " ".join((exclude_reason or "").split())[:200]
    if reason:
        choices[code] = {"excluded": reason}
        _event(quote, "LINE_EXCLUDED", actor, line=code, reason=reason)
    elif product_id:
        product = SupplierProduct.query.filter_by(id=product_id, supplier_id=quote.supplier_id).first()
        if product is None or not any(p.id == product.id for _m, p in matches_for_code(quote.supplier_id, code)):
            raise ProDeskError("Match the product to this line first.")
        before = (choices.get(code) or {}).get("product_id")
        choices[code] = {"product_id": product.id}
        _event(quote, "PRODUCT_CHOSEN", actor, line=code, sku=product.sku,
               substitution=bool(before and before != product.id))
    else:
        choices.pop(code, None)
        _event(quote, "LINE_RESET", actor, line=code)
    quote.choices_json = choices
    quote.updated_at = _now()
    db.session.commit()


def set_commercials(quote: SupplierQuote, form, *, user):
    actor = _actor(user)
    _require_draft(quote)
    delivery = _money(form.get("delivery_charge"), "Delivery charge")
    discount = _money(form.get("discount_percent"), "Quote discount")
    if discount is not None and discount > 50:
        raise ProDeskError("A quote discount over 50% is not accepted here.")
    quote.delivery_charge = delivery
    quote.discount_percent = discount
    quote.notes = (form.get("notes") or "").strip()[:2000] or None
    quote.updated_at = _now()
    _event(quote, "COMMERCIALS_SET", actor, delivery=str(delivery) if delivery is not None else None,
           discount_percent=str(discount) if discount is not None else None)
    db.session.commit()


# ------------------------------------------------------------------ pricing


def _round_sales(qty: Decimal, unit: str) -> Decimal:
    if unit.upper() in WHOLE_UNITS:
        return qty.to_integral_value(rounding=ROUND_CEILING)
    return qty.quantize(CENT, rounding=ROUND_CEILING)


def price_quote(quote: SupplierQuote, *, on: Optional[date] = None) -> Dict:
    """Every takeoff line with its product, converted quantity, price and status, and the totals.

    Nothing is filled in: a line without a product, a price or a quantity says so, and blocks issue unless
    staff leave it out with a reason. Lines that are by design (no quantity, technical review) are listed
    as not included.
    """
    on = on or date.today()
    result = takeoff_for(quote)
    choices = quote.choices_json or {}
    rows = []
    subtotal = Decimal("0")
    line_discounts = Decimal("0")
    for line in result.get("lines", []):
        row = dict(line)
        choice = choices.get(line["code"]) or {}
        matches = matches_for_code(quote.supplier_id, line["code"])
        row["matches"] = [{"product_id": p.id, "sku": p.sku, "description": p.description, "unit": p.sales_uom,
                           "factor": str(Decimal(str(m.requirement_to_sales_factor or 1)).normalize())} for m, p in matches]
        if choice.get("excluded"):
            row.update(price_status=EXCLUDED, reason=choice["excluded"])
            rows.append(row)
            continue
        if line["qty"] is None:
            row.update(price_status=BY_DESIGN if line["status"] == T.REVIEW else NO_QUANTITY)
            rows.append(row)
            continue
        chosen = None
        if choice.get("product_id"):
            chosen = next(((m, p) for m, p in matches if p.id == choice["product_id"]), None)
        elif len(matches) == 1:
            chosen = matches[0]
        if chosen is None:
            row.update(price_status=NO_PRODUCT)
            rows.append(row)
            continue
        mapping, product = chosen
        factor = Decimal(str(mapping.requirement_to_sales_factor or 1))
        sales_qty = _round_sales(Decimal(line["qty"]) * factor, product.sales_uom)
        price = current_price(product, quote.supplier_location_id, on)
        row.update(product_id=product.id, sku=product.sku, product_description=product.description,
                   sales_unit=product.sales_uom, factor=str(factor.normalize()), sales_qty=str(sales_qty),
                   substitution=bool(choice.get("product_id") and len(matches) > 1))
        if price is None:
            row.update(price_status=NO_PRICE)
            rows.append(row)
            continue
        unit_price = Decimal(price.amount)
        extended = (unit_price * sales_qty).quantize(CENT, rounding=ROUND_HALF_UP)
        discount = ((extended * Decimal(price.discount_percent or 0)) / 100).quantize(CENT, rounding=ROUND_HALF_UP)
        shown = unit_price.quantize(CENT) if unit_price == unit_price.quantize(CENT) else unit_price.quantize(Decimal("0.0001"))
        row.update(price_status=PRICED, unit_price=str(shown), extended=str(extended),
                   line_discount=str(discount), discount_percent=str(price.discount_percent or ""),
                   discount_rule=price.discount_rule or "", price_id=price.id, price_import_id=price.import_id,
                   price_effective_from=price.effective_from.isoformat(),
                   price_effective_to=price.effective_to.isoformat() if price.effective_to else "",
                   availability=price.availability or "", price_demo_synthetic=bool(price.demo_synthetic))
        subtotal += extended
        line_discounts += discount
        rows.append(row)
    settings = settings_for(quote.supplier_id)
    quote_discount = ((subtotal - line_discounts) * Decimal(quote.discount_percent or 0) / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    delivery = Decimal(quote.delivery_charge or 0).quantize(CENT)
    taxable = subtotal - line_discounts - quote_discount + delivery
    rate = Decimal(settings.tax_rate_percent) if settings and settings.tax_rate_percent is not None else None
    tax = (taxable * rate / 100).quantize(CENT, rounding=ROUND_HALF_UP) if rate is not None else None
    totals = {"subtotal": str(subtotal.quantize(CENT)), "line_discounts": str(line_discounts.quantize(CENT)),
              "quote_discount": str(quote_discount), "quote_discount_percent": str(quote.discount_percent or ""),
              "delivery": str(delivery), "taxable": str(taxable.quantize(CENT)),
              "tax_label": settings.tax_label if settings else "", "tax_rate_percent": str(rate) if rate is not None else "",
              "tax": str(tax) if tax is not None else "", "total": str((taxable + tax).quantize(CENT)) if tax is not None else ""}
    blockers = issue_blockers(quote, result, rows)
    return {"takeoff": result, "rows": rows, "totals": totals, "blockers": blockers, "priced_on": on.isoformat(),
            "demo_prices": any(r.get("price_demo_synthetic") for r in rows)}


def issue_blockers(quote: SupplierQuote, result: Dict, rows: List[Dict]) -> List[str]:
    out = []
    values = spec_values(quote)
    if not result.get("ready"):
        out.append("Describe the building: size, wall height and roof.")
    for label in S.missing_answers(values):
        out.append(f"Answer: {label}.")
    for row in rows:
        status = row.get("price_status")
        if status == NO_QUANTITY:
            out.append(f"{row['item']}: needs an answer, or leave it out with a reason.")
        elif status == NO_PRODUCT:
            out.append(f"{row['item']}: choose the product, or leave it out with a reason.")
        elif status == NO_PRICE:
            out.append(f"{row['item']} ({row.get('sku')}): no current price in the price file, or leave it out.")
    if not any(r.get("price_status") == PRICED for r in rows):
        out.append("At least one priced line is needed.")
    out.extend(settings_blockers(quote.supplier_id))
    return out


# ------------------------------------------------------------------ issue, approve, order


def _sha(data: Dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def issue_quote(quote: SupplierQuote, *, user, drawing_fingerprint: str = "") -> SupplierQuote:
    """Freeze the quotation: building, lines, prices, sources and totals. Refused while anything is open."""
    actor = _actor(user)
    _require_draft(quote)
    priced = price_quote(quote)
    if priced["blockers"]:
        raise ProDeskError("Not ready to issue: " + " ".join(priced["blockers"][:4]))
    settings = settings_for(quote.supplier_id)
    today = date.today()
    location = db.session.get(SupplierLocation, quote.supplier_location_id) if quote.supplier_location_id else None
    frozen = {
        "number": quote.number,
        "supplier": {"id": quote.supplier_id, "name": _supplier_name(quote.supplier_id),
                     "location": location.display_name if location else ""},
        "customer": {"name": quote.customer.display_name, "phone": quote.customer.phone or "",
                     "email": quote.customer.email or "", "address": quote.customer.address or "",
                     "town": quote.customer.town or ""},
        "building": spec_values(quote),
        "description": S.describe(spec_values(quote)),
        "ruleset": priced["takeoff"]["ruleset"],
        "areas": priced["takeoff"]["areas"],
        "rows": [_frozen_row(r) for r in priced["rows"]],
        "totals": priced["totals"],
        "terms": settings.terms_text or "",
        "contact": settings.contact_line or "",
        "priced_on": priced["priced_on"],
        "valid_until": (today + timedelta(days=int(settings.validity_days))).isoformat(),
        "drawing_fingerprint": drawing_fingerprint,
        "demo_prices": priced["demo_prices"],
        "standard": ({k: (quote.spec_json or {})["assembly"].get(k) for k in ("id", "name", "basis", "approved_by", "approved_at")}
                     | {"changed": list((quote.spec_json or {}).get("assembly_overridden") or []),
                        "openings_placed": bool((quote.spec_json or {}).get("openings_placed"))}
                     if (quote.spec_json or {}).get("assembly") else None),
        "demo_synthetic": bool(quote.demo_synthetic),
        "issued_by": actor,
        "issued_at": _now().isoformat(timespec="seconds"),
    }
    quote.issued_json = frozen
    quote.issued_sha256 = _sha(frozen)
    quote.issued_at = _now()
    quote.issued_by_name = actor
    quote.valid_until = today + timedelta(days=int(settings.validity_days))
    quote.total = Decimal(priced["totals"]["total"])
    quote.status = QUOTE_ISSUED
    quote.updated_at = _now()
    _event(quote, "ISSUED", actor, total=priced["totals"]["total"], sha256=quote.issued_sha256,
           valid_until=quote.valid_until.isoformat())
    db.session.commit()
    return quote


def _frozen_row(row: Dict) -> Dict:
    keep = ("code", "group", "item", "qty", "uom", "basis", "status", "note", "cut_list", "price_status", "reason",
            "sku", "product_description", "sales_unit", "factor", "sales_qty", "unit_price", "extended",
            "line_discount", "discount_percent", "discount_rule", "price_id", "price_import_id",
            "price_effective_from", "price_effective_to", "availability", "substitution", "price_demo_synthetic")
    return {k: row.get(k) for k in keep if k in row}


def _supplier_name(supplier_id: int) -> str:
    from app.models.supplier_catalogue import Supplier
    from app.services.supplier_hub import supplier_brand

    brand = supplier_brand(supplier_id)
    supplier = db.session.get(Supplier, supplier_id)
    return (brand.display_name if brand and brand.display_name else supplier.legal_name) if supplier else ""


def start_revision(quote: SupplierQuote, *, user) -> SupplierQuote:
    """A new draft copied from an issued quote; the issued one is cancelled and kept as issued."""
    actor = _actor(user)
    if quote.status != QUOTE_ISSUED:
        raise ProDeskError("Only an issued, not yet accepted quotation can be revised.")
    now = _now()
    copy = SupplierQuote(
        supplier_id=quote.supplier_id, supplier_location_id=quote.supplier_location_id, customer_id=quote.customer_id,
        number=f"{quote.number.split('-R')[0]}-R{_revision_number(quote) + 1}", status=QUOTE_DRAFT,
        building_system=quote.building_system, spec_json=quote.spec_json, choices_json=quote.choices_json,
        delivery_charge=quote.delivery_charge, discount_percent=quote.discount_percent, notes=quote.notes,
        demo_synthetic=quote.demo_synthetic, created_by_name=actor, created_at=now, updated_at=now)
    db.session.add(copy)
    quote.status = QUOTE_CANCELLED
    for link in SupplierQuoteLink.query.filter_by(quote_id=quote.id, revoked_at=None).all():
        link.revoked_at = now
    db.session.flush()
    for f in active_sketches(quote):
        db.session.add(SupplierQuoteFile(quote_id=copy.id, filename=f.filename, mime=f.mime, size_bytes=f.size_bytes,
                                         sha256=f.sha256, content=f.content, uploaded_by_name=f.uploaded_by_name,
                                         uploaded_at=f.uploaded_at))
    _event(quote, "REVISED", actor, new_number=copy.number)
    _event(copy, "CREATED", actor, revision_of=quote.number)
    db.session.commit()
    return copy


def _revision_number(quote) -> int:
    if "-R" in quote.number:
        try:
            return int(quote.number.rsplit("-R", 1)[1])
        except ValueError:
            return 0
    return 0


def _hash(secret: str) -> str:
    return hashlib.sha256((secret or "").encode("utf-8")).hexdigest()


def create_link(quote: SupplierQuote, *, user, days: int = LINK_DAYS) -> str:
    """A customer approval link. The credential is shown once; only its hash is kept."""
    actor = _actor(user)
    if quote.status != QUOTE_ISSUED:
        raise ProDeskError("Issue the quotation before sending it for approval.")
    now = _now()
    for link in SupplierQuoteLink.query.filter_by(quote_id=quote.id, revoked_at=None).all():
        link.revoked_at = now
    lookup = secrets.token_urlsafe(16)
    while SupplierQuoteLink.query.filter_by(lookup_key=lookup).first() is not None:
        lookup = secrets.token_urlsafe(16)
    secret = secrets.token_urlsafe(32)
    expires = min(now + timedelta(days=days),
                  datetime.combine(quote.valid_until, datetime.max.time()) if quote.valid_until else now + timedelta(days=days))
    db.session.add(SupplierQuoteLink(quote_id=quote.id, lookup_key=lookup, secret_sha256=_hash(secret),
                                     created_by_name=actor, created_at=now, expires_at=expires))
    _event(quote, "LINK_CREATED", actor, expires=expires.isoformat(timespec="minutes"))
    db.session.commit()
    return f"{lookup}.{secret}"


def resolve_link(credential: str, *, record_view: bool = True) -> SupplierQuoteLink:
    lookup, _, secret = (credential or "").partition(".")
    link = SupplierQuoteLink.query.filter_by(lookup_key=lookup).first() if lookup and secret else None
    if link is None or not secrets.compare_digest(link.secret_sha256, _hash(secret)):
        raise ProDeskError("This quotation link is not valid.")
    if link.revoked_at is not None:
        raise ProDeskError("This quotation link has been replaced. Ask the store for the current one.")
    if link.expires_at < _now():
        raise ProDeskError("This quotation link has expired. Ask the store for a new quotation.")
    if link.quote.status not in (QUOTE_ISSUED, QUOTE_ACCEPTED, QUOTE_DECLINED):
        raise ProDeskError("This quotation is no longer available.")
    if record_view:
        link.last_viewed_at = _now()
        db.session.commit()
    return link


def _expired(quote: SupplierQuote) -> bool:
    return bool(quote.valid_until and quote.valid_until < date.today())


def _accept(quote, *, method, name, recorded_by, side, accepted: bool):
    if quote.status != QUOTE_ISSUED:
        raise ProDeskError("This quotation has already been answered or is no longer open.")
    if _expired(quote):
        raise ProDeskError("This quotation has expired. The store can issue a new one.")
    typed = " ".join((name or "").split())[:160]
    if not typed:
        raise ProDeskError("Type the customer's full name to record the answer.")
    now = _now()
    quote.status = QUOTE_ACCEPTED if accepted else QUOTE_DECLINED
    quote.accepted_at = now
    quote.acceptance_method = method
    quote.accepted_by_name = typed
    quote.acceptance_recorded_by_name = recorded_by
    quote.accepted_sha256 = quote.issued_sha256
    quote.updated_at = now
    _event(quote, "ACCEPTED" if accepted else "DECLINED", recorded_by if side == "SUPPLIER" else typed, side=side,
           method=method, name=typed, sha256=quote.issued_sha256)
    db.session.commit()
    return quote


def accept_via_link(credential: str, *, name: str, accepted: bool) -> SupplierQuote:
    link = resolve_link(credential, record_view=False)
    if link.quote.issued_sha256 is None:
        raise ProDeskError("This quotation is no longer available.")
    return _accept(link.quote, method=ACCEPT_LINK, name=name, recorded_by=" ".join((name or "").split())[:160],
                   side="CUSTOMER", accepted=accepted)


def record_acceptance(quote: SupplierQuote, *, method: str, name: str, user, accepted: bool = True) -> SupplierQuote:
    if method not in (ACCEPT_IN_PERSON, ACCEPT_PHONE, ACCEPT_EMAIL):
        raise ProDeskError("Choose how the customer gave their answer.")
    return _accept(quote, method=method, name=name, recorded_by=_actor(user), side="SUPPLIER", accepted=accepted)


def mark_order_ready(quote: SupplierQuote, *, user) -> Dict:
    """The accepted quote, as an order-ready package for entry into the supplier's own sales system."""
    actor = _actor(user)
    if quote.status != QUOTE_ACCEPTED:
        raise ProDeskError("The customer must accept the quotation first.")
    if quote.order_ready_at is None:
        quote.order_ready_at = _now()
        quote.order_ready_by_name = actor
        _event(quote, "ORDER_READY", actor, sha256=quote.issued_sha256)
        db.session.commit()
    return order_package(quote)


def order_package(quote: SupplierQuote) -> Dict:
    frozen = quote.issued_json or {}
    lines = [r for r in frozen.get("rows", []) if r.get("price_status") == PRICED]
    return {"number": quote.number, "frozen": frozen, "lines": lines,
            "not_included": [r for r in frozen.get("rows", []) if r.get("price_status") != PRICED],
            "accepted_by": quote.accepted_by_name, "accepted_at": quote.accepted_at,
            "method": quote.acceptance_method, "sha256": quote.issued_sha256}


def order_csv(quote: SupplierQuote) -> str:
    package = order_package(quote)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["quote", "sku", "description", "quantity", "unit", "unit_price", "line_discount", "extended",
                "takeoff_item", "takeoff_quantity", "takeoff_unit"])
    for r in package["lines"]:
        w.writerow([quote.number, r.get("sku"), r.get("product_description"), r.get("sales_qty"), r.get("sales_unit"),
                    r.get("unit_price"), r.get("line_discount"), r.get("extended"), r.get("item"), r.get("qty"), r.get("uom")])
    t = package["frozen"].get("totals", {})
    for label, key in (("Delivery", "delivery"), ("Quote discount", "quote_discount"), (t.get("tax_label") or "Tax", "tax"),
                       ("Total", "total")):
        w.writerow([quote.number, "", label, "", "", "", "", t.get(key, ""), "", "", ""])
    return buf.getvalue()


def send_quote_email(quote: SupplierQuote, *, credential: str, base_url: str, user):
    """Email the approval link, only with the consent the customer gave at the counter."""
    from app.services.transactional_email import TEMPLATE_SUPPLIER_QUOTE, send_transactional_message

    actor = _actor(user)
    customer = quote.customer
    if not (customer.email and customer.consent_email):
        raise ProDeskError("The customer has not agreed to receive this quotation by email.")
    frozen = quote.issued_json or {}
    message = send_transactional_message(
        TEMPLATE_SUPPLIER_QUOTE, customer.email,
        {"supplier_name": frozen.get("supplier", {}).get("name", ""), "customer_name": customer.display_name,
         "quote_number": quote.number, "total": frozen.get("totals", {}).get("total", ""),
         "valid_until": frozen.get("valid_until", ""), "link": f"{base_url.rstrip('/')}/quote/{credential}"},
        related_type="supplier_quote", related_id=quote.id)
    _event(quote, "EMAILED", actor, to=customer.email, status=message.status)
    db.session.commit()
    return message

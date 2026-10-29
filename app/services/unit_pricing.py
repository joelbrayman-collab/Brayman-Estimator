"""Supplier Unit Pricing & Conversion (Joel, 29 Oct 2026).

Calibrayt accepts construction requirements in the units estimating and takeoff produce (SF, LF, pieces) and
supplier pricing in the units the supplier's POS sells in (a sheet, a 12 ft piece, a box, a tube). Calibrayt owns
the governed conversion between them:

    takeoff measurements → requirement per component (takeoff units)
    → Supplier Pricing Request (a template from the library, sent on the Supplier Connection workflow)
    → the supplier prices each component in its normal sell unit
    → governed conversion and purchasing-unit rounding (whole sell units, always up)
    → line extensions and the package price
    → the contractor reviews, resolves what is missing, approves
    → purchase order → the existing CaliSIGN purchase-order signing.

A conversion is used only when it has a stated basis: the product's own stated size in the template ("4 ft x 8 ft
sheet = 32 SF"), a conversion the supplier states on its quote, or one the contractor records with its source.
Missing product data is never guessed: such a line has no quantity, says what is missing, and the package cannot be
approved until a person records the conversion (with its source), the supplier states its quantity, or the
contractor takes the line out of the order (with a reason). Everything is kept on the request itself
(``SupplierRequestShare.shared_json`` / ``quote_json``); no new table.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Optional

from app import db
from app.models.project import Project
from app.models.supplier_portal import (
    KIND_MATERIAL,
    SHARE_OPENED,
    SHARE_RETURNED,
    SHARE_SENT,
    SHARE_SUPERSEDED,
    SupplierRequestShare,
)
from app.services import supplier_pricing_templates as T
from app.services.local_time import local_today

# The request's source_kind (a value of the existing column; no schema change).
SOURCE_UNIT_PRICING = "UNIT_PRICING"
CENT = Decimal("0.01")
HST_RATE = Decimal("0.13")
OTHER_UNIT = "OTHER"
SOURCE_TEMPLATE = "TEMPLATE"
SOURCE_SUPPLIER = "SUPPLIER"
SOURCE_CONTRACTOR = "CONTRACTOR"
SOURCE_IDENTITY = "SAME_UNIT"

PRICED = "PRICED"
CONVERSION_MISSING = "CONVERSION_MISSING"
NOT_PRICED = "NOT_PRICED"
EXCLUDED = "EXCLUDED"
STATUS_LABELS = {PRICED: "Priced", CONVERSION_MISSING: "Conversion missing", NOT_PRICED: "Not priced",
                 EXCLUDED: "Not ordered"}
SOURCE_LABELS = {SOURCE_TEMPLATE: "product size", SOURCE_SUPPLIER: "stated by the supplier",
                 SOURCE_CONTRACTOR: "recorded by the contractor", SOURCE_IDENTITY: "same unit"}


class UnitPricingError(ValueError):
    """A request, price or decision that cannot be accepted; the message is for the person."""


# ---------------------------------------------------------------------------------------------- numbers
def _dec(raw, label: str, *, positive: bool = False, allow_blank: bool = False) -> Optional[Decimal]:
    text = str(raw if raw is not None else "").replace("$", "").replace(",", "").strip()
    if not text:
        if allow_blank:
            return None
        raise UnitPricingError(f"{label} is required.")
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise UnitPricingError(f"{label} must be a number.") from None
    if not value.is_finite() or value < 0 or (positive and value == 0):
        raise UnitPricingError(f"{label} must be {'more than zero' if positive else 'zero or more'}.")
    return value


def fmt(value) -> str:
    """A quantity as a plain string: 1925, 1444.3, 0.5 (no exponent, no trailing zeros)."""
    if value is None:
        return ""
    d = Decimal(str(value))
    text = format(d.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def round_up(exact: Decimal) -> int:
    """Purchasing-unit rounding: a sell unit is not split, so any part of one is one more (1925 / 32 = 60.16 → 61).
    Six decimal places absorb arithmetic noise only (3520 / 32 = 110 exactly stays 110)."""
    return int(math.ceil(exact.quantize(Decimal("0.000001"))))


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------------------------- requirements
def _schema2(key: str) -> dict:
    template = T.load_template(key)
    if int(template.get("schema") or 1) < 2 or template.get("status") == "superseded":
        raise UnitPricingError("Choose a current template from the library.")
    return template


def requirement_lines(key: str, measurements: dict, choices: Optional[dict] = None) -> dict:
    """The package for one job: each component's requirement in takeoff units and Calibrayt's quantity in the
    default sell unit, where a verified conversion exists. Raises on missing, extra or bad measurements."""
    template = _schema2(key)
    known = [m["key"] for m in template["measurements"]]
    values = {}
    for k in known:
        values[k] = _dec(measurements.get(k), next(m["label"] for m in template["measurements"] if m["key"] == k))
    extra = sorted(set(measurements) - set(known))
    if extra:
        raise UnitPricingError("Not measurements of this template: " + ", ".join(extra))
    chosen = dict(template.get("choices", {}))
    unknown = sorted(set(choices or {}) - set(chosen))
    if unknown:
        raise UnitPricingError("Not choices of this template: " + ", ".join(unknown))
    chosen.update({k: str(v).strip() for k, v in (choices or {}).items() if str(v).strip()})
    fields = {k: fmt_thousands(v) for k, v in values.items()}
    fields.update(chosen)
    lines, by_key = [], {}
    for number, item in enumerate(template["items"], start=1):
        req = item["requirement"]
        if "measure" in req:
            qty = values[req["measure"]] * (Decimal(1) + Decimal(str(req.get("waste") or 0)))
            pct = int(Decimal(str(req.get("waste") or 0)) * 100)
            basis = f"{fmt_thousands(values[req['measure']])} {req['unit']}" + (f" + {pct}% waste" if pct else "")
        elif "fixed" in req:
            qty, basis = Decimal(str(req["fixed"])), f"{req['fixed']} {req['unit']}"
        elif "pieces_of" in req:
            parts = [by_key[k] for k in req["pieces_of"]]
            if any(p["qty"] is None for p in parts):
                qty, basis = None, "the pieces it fastens are not all counted yet"
            else:
                qty = sum((Decimal(p["qty"]) for p in parts), Decimal(0))
                basis = " + ".join(f"{p['qty']} {p['item']}" for p in parts)
        else:
            raise UnitPricingError(f"Template item {item['key']} has no requirement.")
        default = item["default_unit"]
        conversion = _template_conversion(item, default)
        sell_qty = exact = None
        if qty is not None and conversion is not None:
            exact = qty / Decimal(conversion["per"])
            sell_qty = round_up(exact)
        line = {
            "number": number, "key": item["key"], "group": item["group"], "item": item["item"],
            "spec": item["spec"].format(**fields, **{f"qty_{k}": v["qty"] for k, v in by_key.items()}),
            "requirement": {"qty": fmt(qty) if qty is not None else None, "unit": req["unit"], "basis": basis},
            "sell_units": item["sell_units"], "default_unit": default,
            "qty": str(sell_qty) if sell_qty is not None else None,
            "exact": fmt(exact.quantize(Decimal("0.01"))) if exact is not None else None,
            "unit": default,
            "conversion": conversion,
            "conversion_basis": next((u.get("basis") for u in item["sell_units"] if u["unit"] == default), ""),
        }
        lines.append(line)
        by_key[item["key"]] = line
    return {"template": template["key"], "title": template["title"], "scope": template.get("scope", ""),
            "groups": template["groups"], "measurements": {k: fmt(v) for k, v in values.items()},
            "measurement_labels": {m["key"]: f"{m['label']} ({m['unit']})" for m in template["measurements"]},
            "choices": chosen, "lines": lines}


def fmt_thousands(value: Decimal) -> str:
    whole = value == value.to_integral_value()
    return f"{value:,.0f}" if whole else f"{value:,.2f}".rstrip("0").rstrip(".")


def _template_conversion(item, unit) -> Optional[dict]:
    for u in item["sell_units"]:
        if u["unit"] == unit and u.get("per") not in (None, ""):
            return {"unit": unit, "per": str(u["per"]), "of": u["of"], "basis": u.get("basis", ""),
                    "source": SOURCE_TEMPLATE}
    return None


# ---------------------------------------------------------------------------------------------- the request
def create_request(*, project: Project, user, account_id: int, template_key: str, measurements: dict,
                   choices: Optional[dict] = None, needed_by: Optional[date] = None) -> SupplierRequestShare:
    """A Supplier Pricing Request for one template package and one supplier account, on the Supplier Connection
    workflow. A supplier with a Supplier Hub sign-in sees it at once; for one without, the contractor sends the
    approved PDF form and records the returned prices on the request."""
    from app.services.supplier_hub import (_account, _base_shared, _display, _event, _next_number,
                                           supplier_has_sign_in)

    package = requirement_lines(template_key, measurements, choices)
    account = _account(project.organization_id, int(account_id or 0))
    online = supplier_has_sign_in(account.supplier_id)
    shared = {**_base_shared(project, user, needed_by), "lines": package.pop("lines"),
              "unit_pricing": {**package, "online": online, "hst_rate": str(HST_RATE)}}
    share = SupplierRequestShare(
        organization_id=project.organization_id, project_id=project.id, supplier_id=account.supplier_id,
        contractor_supplier_account_id=account.id,
        number=_next_number(SupplierRequestShare, project.organization_id, "SRQ"),
        request_kind=KIND_MATERIAL, source_kind=SOURCE_UNIT_PRICING, source_ref=template_key,
        shared_json=shared, status=SHARE_SENT, sent_by_user_id=getattr(user, "id", None),
        sent_by_name=_display(user), sent_at=datetime.utcnow(),
    )
    db.session.add(share)
    db.session.flush()
    # A new package for the same supplier and template replaces the open one (a revised takeoff).
    for old in SupplierRequestShare.query.filter(
            SupplierRequestShare.organization_id == project.organization_id,
            SupplierRequestShare.project_id == project.id, SupplierRequestShare.supplier_id == account.supplier_id,
            SupplierRequestShare.source_kind == SOURCE_UNIT_PRICING, SupplierRequestShare.source_ref == template_key,
            SupplierRequestShare.status.in_((SHARE_SENT, SHARE_OPENED)), SupplierRequestShare.id != share.id):
        old.status = SHARE_SUPERSEDED
    _event(share, "SENT", "CONTRACTOR", share.sent_by_name,
           f"Unit pricing: {package['title']}" + ("" if online else " (supplier has no sign-in: PDF form)"))
    db.session.commit()
    return share


def is_unit_pricing(share) -> bool:
    return share is not None and share.source_kind == SOURCE_UNIT_PRICING


def unit_options(line: dict) -> list[dict]:
    """The units a line may be priced in: the template's sell units, the requirement unit itself (1 = 1), then
    any other unit the supplier names (which then needs a conversion or the supplier's quantity)."""
    out, seen = [], set()
    for u in line["sell_units"]:
        out.append({"unit": u["unit"], "label": u["unit"] + ("" if u.get("per") else " (conversion to confirm)")})
        seen.add(u["unit"])
    req_unit = line["requirement"]["unit"]
    if req_unit not in seen and line["requirement"]["qty"] is not None and " " not in req_unit:
        out.append({"unit": req_unit, "label": f"{req_unit} (priced per {req_unit})"})
    return out


# ---------------------------------------------------------------------------------------------- prices
def record_prices(share: SupplierRequestShare, *, user, values: dict, side: str) -> None:
    """The supplier's prices, entered in the Supplier Hub (side SUPPLIER) or, for a supplier without a sign-in, by
    the contractor from the returned form (side CONTRACTOR). Per line: unit, unit price, SKU, and where the unit
    has no verified conversion the supplier's own quantity or conversion. Nothing is calculated here."""
    from app.services.supplier_hub import _display, _event

    if not is_unit_pricing(share):
        raise UnitPricingError("Not a unit pricing request.")
    if share.status not in (SHARE_SENT, SHARE_OPENED):
        raise UnitPricingError("This request is closed or already returned.")
    valid_until = (values.get("valid_until") or "").strip()
    try:
        valid = date.fromisoformat(valid_until)
    except ValueError:
        raise UnitPricingError("Prices valid until is required (a date).") from None
    if valid < local_today():
        raise UnitPricingError("Prices valid until cannot be in the past.")
    lines, priced = {}, 0
    for line in share.shared_json["lines"]:
        n = f"{int(line['number']):02d}"
        price = _dec(values.get(f"unit_price_{n}"), f"Line {line['number']} unit price", allow_blank=True)
        unit = (values.get(f"sell_unit_{n}") or line["default_unit"]).strip()
        if unit == OTHER_UNIT:
            unit = (values.get(f"other_unit_{n}") or "").strip().upper()[:20]
            if not unit:
                raise UnitPricingError(f"Line {line['number']}: name the unit you sell it in.")
        entry = {"unit": unit, "unit_price": fmt(price) if price is not None else None,
                 "sku": (values.get(f"sku_{n}") or "").strip()[:60]}
        qty = _dec(values.get(f"supplier_qty_{n}"), f"Line {line['number']} quantity", positive=True, allow_blank=True)
        if qty is not None:
            if qty != qty.to_integral_value():
                raise UnitPricingError(f"Line {line['number']}: the quantity is a whole number of {unit}.")
            entry["supplier_qty"] = str(int(qty))
        per = _dec(values.get(f"supplier_per_{n}"), f"Line {line['number']} conversion", positive=True,
                   allow_blank=True)
        if per is not None:
            entry["supplier_conversion"] = {"unit": unit, "per": fmt(per), "of": line["requirement"]["unit"]}
        if price is not None:
            priced += 1
        lines[n] = entry
    if not priced:
        raise UnitPricingError("No prices were entered. Enter a unit price on at least one line.")
    who = _display(user)
    supplier_name = share.supplier.legal_name if share.supplier else "Supplier"
    share.quote_json = {
        "kind": "UNIT_PRICING", "lines": lines, "valid_until": valid.isoformat(),
        "quote_number": (values.get("quote_number") or "").strip()[:60],
        "notes": (values.get("notes") or "").strip()[:500],
        "entered_by": who, "entered_side": side, "supplier_name": supplier_name,
        "entered_at": datetime.utcnow().isoformat(timespec="seconds"),
        "conversions": {}, "exclusions": {},
    }
    share.status = SHARE_RETURNED
    share.returned_at = datetime.utcnow()
    share.returned_by_name = who if side == "SUPPLIER" else f"{who} (entered from {supplier_name}'s returned form)"
    share.response_ref = None
    _event(share, "RETURNED", side, who, f"{priced} of {len(lines)} lines priced in the supplier's units")
    db.session.commit()


def _conversion_for(line: dict, entry: dict, quote: dict) -> Optional[dict]:
    """The governed conversion for the unit the line is priced in, most specific first: one the contractor
    recorded, one the supplier stated, the template's product size, the same unit as the requirement."""
    n = f"{int(line['number']):02d}"
    unit = entry["unit"]
    recorded = (quote.get("conversions") or {}).get(n)
    if recorded and recorded.get("unit") == unit:
        return {**recorded, "source": SOURCE_CONTRACTOR}
    stated = entry.get("supplier_conversion")
    if stated and stated.get("unit") == unit:
        return {**stated, "source": SOURCE_SUPPLIER,
                "basis": f"Stated by {quote.get('supplier_name') or 'the supplier'} on the quote"}
    item = {"sell_units": line["sell_units"]}
    template = _template_conversion(item, unit)
    if template:
        return template
    if unit == line["requirement"]["unit"]:
        return {"unit": unit, "per": "1", "of": unit, "basis": "Priced in the requirement's own unit",
                "source": SOURCE_IDENTITY}
    return None


def price_package(share: SupplierRequestShare) -> dict:
    """The priced package: per line the requirement, the unit priced, the conversion used and its source, the
    exact and rounded purchasing quantity, the unit price and the extension; group totals, subtotal, HST, total;
    and what still stops approval. Read only; recalculated every time from the stored request and quote."""
    shared = share.shared_json
    up = shared.get("unit_pricing") or {}
    quote = share.quote_json if (share.quote_json or {}).get("kind") == "UNIT_PRICING" else None
    groups = {g["key"]: {"label": g["label"], "total": Decimal(0)} for g in up.get("groups", [])}
    rows, blockers = [], []
    subtotal = Decimal(0)
    for line in shared["lines"]:
        n = f"{int(line['number']):02d}"
        entry = (quote or {}).get("lines", {}).get(n) if quote else None
        row = {"n": n, "line": line, "entry": entry, "unit": (entry or {}).get("unit") or line["default_unit"],
               "conversion": None, "qty": None, "exact": None, "qty_source": None, "unit_price": None,
               "extension": None, "status": None, "missing": ""}
        excluded = (quote or {}).get("exclusions", {}).get(n) if quote else None
        if quote is None:
            row["conversion"] = line.get("conversion")
            row["qty"] = line.get("qty")
            row["status"] = None
            rows.append(row)
            continue
        if excluded:
            row["status"], row["excluded"] = EXCLUDED, excluded
            rows.append(row)
            continue
        if not entry or entry.get("unit_price") in (None, ""):
            row["status"], row["missing"] = NOT_PRICED, "No unit price on the quote."
            blockers.append(f"Line {line['number']} ({line['item']}) has no price: ask the supplier, or take it out "
                            "of the order.")
            rows.append(row)
            continue
        price = Decimal(entry["unit_price"])
        row["unit_price"] = price
        conversion = _conversion_for(line, entry, quote)
        row["conversion"] = conversion
        req = line["requirement"]["qty"]
        if entry.get("supplier_qty"):
            row["qty"], row["qty_source"] = int(entry["supplier_qty"]), SOURCE_SUPPLIER
        elif conversion is not None and req is not None:
            exact = Decimal(req) / Decimal(conversion["per"])
            row["exact"] = fmt(exact.quantize(Decimal("0.01")))
            row["qty"], row["qty_source"] = round_up(exact), conversion["source"]
        if row["qty"] is None:
            row["status"] = CONVERSION_MISSING
            row["missing"] = (f"How many {line['requirement']['unit']} one {row['unit']} covers is not known"
                              + (" (no verified product data)" if req is not None else "") + ".")
            blockers.append(f"Line {line['number']} ({line['item']}): record how many {line['requirement']['unit']} "
                            f"one {row['unit']} covers (with its source), or take it out of the order.")
            rows.append(row)
            continue
        row["extension"] = money(price * Decimal(row["qty"]))
        row["status"] = PRICED
        subtotal += row["extension"]
        if line["group"] in groups:
            groups[line["group"]]["total"] += row["extension"]
        rows.append(row)
    rate = Decimal(up.get("hst_rate") or HST_RATE)
    subtotal = money(subtotal)
    hst = money(subtotal * rate)
    if quote is not None and quote.get("valid_until") and date.fromisoformat(quote["valid_until"]) < local_today():
        blockers.append("The supplier's prices have expired. Ask for a new quote.")
    if quote is not None and not any(r["status"] == PRICED for r in rows):
        blockers.append("No line can be ordered.")
    return {"rows": rows, "groups": groups, "subtotal": subtotal, "hst": hst, "total": money(subtotal + hst),
            "hst_rate": rate, "blockers": blockers if quote is not None else ["The supplier has not returned prices."],
            "quote": quote, "approved": (quote or {}).get("approved"), "returned": quote is not None}


# ---------------------------------------------------------------------------------------------- the contractor's review
def _editable_quote(share) -> dict:
    from app.services.supplier_hub import purchase_order_for

    if not is_unit_pricing(share) or share.status != SHARE_RETURNED or not share.quote_json:
        raise UnitPricingError("There are no returned prices on this request.")
    if share.quote_json.get("approved") or purchase_order_for(share) is not None:
        raise UnitPricingError("The package is already approved; its prices and conversions are fixed.")
    return dict(share.quote_json)


def record_conversion(share, *, number: int, per, source: str, user) -> None:
    """The contractor records a verified conversion for one line, in the unit the supplier priced it in: one sell
    unit covers ``per`` requirement units. The source (spec sheet, the supplier by phone, …) is required."""
    from app.services.supplier_hub import _display, _event

    quote = _editable_quote(share)
    line = _line(share, number)
    n = f"{number:02d}"
    entry = (quote.get("lines") or {}).get(n)
    if not entry or entry.get("unit_price") in (None, ""):
        raise UnitPricingError("That line has no price yet.")
    value = _dec(per, "The conversion", positive=True)
    source = (source or "").strip()
    if len(source) < 3:
        raise UnitPricingError("Say where the conversion comes from (for example the manufacturer's sheet, or the "
                               "supplier by phone).")
    conversions = dict(quote.get("conversions") or {})
    conversions[n] = {"unit": entry["unit"], "per": fmt(value), "of": line["requirement"]["unit"],
                      "basis": source[:200], "by": _display(user),
                      "at": datetime.utcnow().isoformat(timespec="seconds")}
    quote["conversions"] = conversions
    share.quote_json = quote
    _event(share, "CONVERSION_RECORDED", "CONTRACTOR", _display(user),
           f"Line {number}: 1 {entry['unit']} = {fmt(value)} {line['requirement']['unit']} ({source[:120]})")
    db.session.commit()


def exclude_line(share, *, number: int, reason: str, user, include: bool = False) -> None:
    """Take a line out of the order (with a reason everyone sees), or put it back."""
    from app.services.supplier_hub import _display, _event

    quote = _editable_quote(share)
    _line(share, number)
    n = f"{number:02d}"
    exclusions = dict(quote.get("exclusions") or {})
    if include:
        exclusions.pop(n, None)
        detail = f"Line {number} back in the order"
    else:
        reason = (reason or "").strip()
        if len(reason) < 3:
            raise UnitPricingError("Say why this line is not ordered.")
        exclusions[n] = {"reason": reason[:200], "by": _display(user),
                         "at": datetime.utcnow().isoformat(timespec="seconds")}
        detail = f"Line {number} not ordered: {reason[:120]}"
    quote["exclusions"] = exclusions
    share.quote_json = quote
    _event(share, "LINE_EXCLUDED" if not include else "LINE_INCLUDED", "CONTRACTOR", _display(user), detail)
    db.session.commit()


def approve(share, *, user) -> dict:
    """Approve the priced package: the lines, quantities, prices and total are fixed for the purchase order."""
    from app.services.supplier_hub import _display, _event

    quote = _editable_quote(share)
    view = price_package(share)
    if view["blockers"]:
        raise UnitPricingError("The package cannot be approved yet. " + " ".join(view["blockers"]))
    lines = [{
        "number": r["line"]["number"], "description": f"{r['line']['item']} — {r['line']['spec']}",
        "sku": (r["entry"] or {}).get("sku", ""), "quantity": str(r["qty"]), "unit": r["unit"],
        "net_unit_cost": fmt(r["unit_price"]), "line_value": str(r["extension"]), "cost_approved": True,
        "requirement": f"{r['line']['requirement']['qty']} {r['line']['requirement']['unit']}",
        "conversion": (f"1 {r['conversion']['unit']} = {r['conversion']['per']} {r['conversion']['of']}"
                       if r.get("conversion") else "quantity stated by the supplier"),
    } for r in view["rows"] if r["status"] == PRICED]
    quote["approved"] = {"by": _display(user), "at": datetime.utcnow().isoformat(timespec="seconds"),
                         "subtotal": str(view["subtotal"]), "hst": str(view["hst"]), "total": str(view["total"]),
                         "lines": lines}
    share.quote_json = quote
    _event(share, "QUOTE_APPROVED", "CONTRACTOR", quote["approved"]["by"],
           f"Unit pricing package: {len(lines)} lines, ${view['subtotal']} before tax")
    db.session.commit()
    return quote["approved"]


def order_lines(share) -> tuple[list[dict], list[str]]:
    """The purchase order's lines: exactly the approved package (the existing place_order and CaliSIGN signing
    take them unchanged)."""
    if share.status != SHARE_RETURNED or not share.quote_json:
        return [], ["The supplier has not returned prices."]
    approved = share.quote_json.get("approved")
    if not approved:
        return [], ["Review the priced package and approve it first."]
    valid = share.quote_json.get("valid_until")
    if valid and date.fromisoformat(valid) < local_today():
        return approved["lines"], ["The supplier's prices have expired. Ask for a new quote."]
    return approved["lines"], []


def _line(share, number: int) -> dict:
    for line in share.shared_json["lines"]:
        if int(line["number"]) == int(number):
            return line
    raise UnitPricingError("No such line on this request.")


# ---------------------------------------------------------------------------------------------- the approved form
def form_request(share) -> dict:
    """The approved Supplier Pricing Request form for this request (the PDF a supplier without a sign-in fills):
    Calibrayt's quantity in the default sell unit, or blank with the reason where no verified conversion exists."""
    up = share.shared_json["unit_pricing"]
    items = []
    for line in share.shared_json["lines"]:
        spec = line["spec"]
        if line.get("qty") is None:
            spec = f"{spec} — quantity to confirm: {line['requirement']['qty'] or '?'} {line['requirement']['unit']}"
        items.append({"key": line["key"], "group": line["group"], "item": line["item"], "spec": spec[:110],
                      "qty": line.get("qty") or "", "unit": line["default_unit"]})
    supplier = share.supplier.legal_name if share.supplier else ""
    return {"project": share.shared_json.get("project_reference", ""), "supplier": supplier,
            "supplier_tag": supplier.upper()[:40] or "SUPPLIER", "requested": share.sent_at.strftime("%B %d, %Y"),
            "plans": "", "scope": up.get("scope", ""), "contact": {}, "prepared_by": "",
            "groups": up["groups"], "items": items}

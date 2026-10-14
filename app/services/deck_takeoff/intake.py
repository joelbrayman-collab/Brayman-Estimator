"""Supplier response intake for a pool-deck supplier request.

The supplier returns the approved page with the response boxes filled, or
Brayman types the same answers in. Each answer is matched to the line that
was issued, by request identity, line key, and line signature. Prices are
validated. Nothing here creates an estimate line or approves a cost.

Recording is a separate, human step. It appends supplier price evidence
through the existing supplier catalogue services, only for lines whose
material has a canonical identity in the catalogue. Every response is kept
as its own immutable record, so an earlier price is never overwritten.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from typing import Dict, List, Mapping, Optional

from pypdf import PdfReader

# Form 1: the historical eight boxes. Requests issued on it keep this mapping.
FIELDS = ("sku", "product_confirmed", "unit_price", "discount", "net_price", "availability", "lead_time", "substitution")
FIELDS_V1 = FIELDS
# Form 2 (14 Oct 2026): the supplier types SKU, unit cost, discount %. The PDF carries no
# calculations; every net, line total and grand total is calculated here (the sole authority).
FIELDS_V2 = ("sku", "unit_cost", "discount")
SUPPLIER_TYPED_V2 = FIELDS_V2
ALL_FIELDS = tuple(dict.fromkeys(FIELDS_V1 + FIELDS_V2))


NO_PRICES_WARNING = (
    "No SKU, unit cost or discount was found in this response. If the supplier typed prices, the PDF viewer "
    "may not have saved them: ask for the PDF to be saved again after typing, or enter the prices by hand."
)


def response_form(manifest: Mapping) -> int:
    """The form a request was issued on. Manifests stored before form 2 have no marker: form 1."""
    return 2 if int(manifest.get("response_form") or 1) == 2 else 1


def response_fields(manifest: Mapping):
    return FIELDS_V2 if response_form(manifest) == 2 else FIELDS_V1

QUOTED = "QUOTED"
NOT_QUOTED = "NOT_QUOTED"
INCOMPLETE = "INCOMPLETE"
PRICE_CONFLICT = "PRICE_CONFLICT"
SUBSTITUTION_REVIEW = "SUBSTITUTION_REVIEW"
INVALID = "INVALID"

READY_TO_RECORD = "READY_TO_RECORD"
KEPT_ON_RESPONSE = "KEPT_ON_RESPONSE"
NOT_RECORDABLE = "NOT_RECORDABLE"

CENT = Decimal("0.01")
TOLERANCE = Decimal("0.01")
# The evidence column is Numeric(12, 4).
MAX_AMOUNT = Decimal("100000000")


class SupplierResponseError(ValueError):
    pass


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def read_response_pdf(payload: bytes) -> Dict:
    """Field values from a returned PDF. The page itself is not trusted."""
    try:
        reader = PdfReader(BytesIO(payload))
        fields = reader.get_fields() or {}
    except Exception as exc:  # pypdf raises several error types for damaged files
        raise SupplierResponseError("The returned file is not a readable PDF form.") from exc
    values = {name: _text(field.get("/V")) for name, field in fields.items()}
    if not values.get("request_id"):
        raise SupplierResponseError(
            "The returned PDF is not a Brayman supplier request with response boxes. If the supplier's PDF viewer "
            "flattened or stripped the form, enter the prices by hand from the request's Enter page."
        )
    return values


def answers_from_values(values: Mapping) -> Dict:
    """Group flat form values into request identity, per-line answers, and closing."""
    lines: Dict[int, Dict[str, str]] = {}
    pattern = re.compile(r"^(line_key|line_sig|" + "|".join(ALL_FIELDS) + r")_(\d{2,3})$")
    for name, value in values.items():
        match = pattern.match(name)
        if not match:
            continue
        number = int(match.group(2))
        lines.setdefault(number, {})[match.group(1)] = _text(value)
    return {
        "request_id": _text(values.get("request_id")),
        "request_project": _text(values.get("request_project")),
        "lines": lines,
        "contact": _text(values.get("bmr_contact")),
        "response_date": _text(values.get("response_date")),
        "valid_until": _text(values.get("valid_until")),
        "general_notes": _text(values.get("general_notes")),
    }


def _money(raw: str):
    text = raw.replace("$", "").replace(",", "").replace("CAD", "").strip()
    if not text:
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise SupplierResponseError(f"'{raw}' is not an amount.")
    if not value.is_finite():
        raise SupplierResponseError(f"'{raw}' is not an amount.")
    if value < 0:
        raise SupplierResponseError(f"'{raw}' is negative.")
    if value >= MAX_AMOUNT:
        raise SupplierResponseError(f"'{raw}' is larger than a price can be stored.")
    return value


def _percent(raw: str):
    text = raw.replace("%", "").strip()
    if not text:
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise SupplierResponseError(f"'{raw}' is not a percentage.")
    if not value.is_finite():
        raise SupplierResponseError(f"'{raw}' is not a percentage.")
    if value < 0 or value > 100:
        raise SupplierResponseError(f"Discount '{raw}' must be between 0 and 100.")
    return value


_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d %B %Y", "%B %d, %Y", "%B %d %Y", "%d %b %Y", "%b %d, %Y", "%m/%d/%Y")


def parse_date(raw: str) -> Optional[datetime]:
    text = (raw or "").strip()
    if not text:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise SupplierResponseError(f"'{raw}' is not a date. Use YYYY-MM-DD.")


def _confirmed(raw: str) -> Optional[str]:
    text = raw.strip().lower()
    if not text:
        return None
    if text in ("yes", "y", "confirmed", "confirm", "ok", "x"):
        return "YES"
    if text.startswith("sub") or text in ("no", "n", "alternate", "alternative"):
        return "SUBSTITUTE"
    return "UNCLEAR"


def _availability(raw: str) -> str:
    text = raw.strip().lower()
    if text in ("in stock", "instock", "stock", "yes"):
        return "IN_STOCK"
    if text.startswith("limited"):
        return "LIMITED"
    return "UNKNOWN"


_NOTE_LINE = re.compile(r"\b(?:line|item|no\.?|#)\s*#?\s*(\d{1,3})\b", re.IGNORECASE)


def notes_line_numbers(notes: str) -> set:
    """Line numbers the supplier names in the general notes, e.g. "Line 9 - replacement SKU GATE-48"."""
    return {int(m.group(1)) for m in _NOTE_LINE.finditer(notes or "")}


def _finish(result: Dict, status: str, line: Mapping, valid_until, catalogue_codes) -> None:
    result["status"] = status
    if status != QUOTED:
        result["recording"] = NOT_RECORDABLE
    elif valid_until is None:
        result["recording"] = NOT_RECORDABLE
        result["problems"].append("Price validity is required before the price is recorded.")
    elif line.get("canonical_identity") or (
        line.get("canonical_material_code") and line["canonical_material_code"] in catalogue_codes
    ):
        result["recording"] = READY_TO_RECORD
    else:
        result["recording"] = KEPT_ON_RESPONSE
        result["problems"].append(
            "This line has no canonical material identity yet (a product fact is still missing). The price stays on this response record."
        )


def net_unit_cost(unit: Decimal, discount: Decimal) -> Decimal:
    """Unit cost less the discount, to the cent (half up). The PDF and the hand-entry page round the same way."""
    return (unit * (Decimal("100") - discount) / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)


def _evaluate_v2(result: Dict, a: Mapping, line: Mapping) -> str:
    """Form 2: SKU, unit cost, discount. Net and total are calculated here, independently of the PDF."""
    try:
        unit = _money(a.get("unit_cost", ""))
        discount = _percent(a.get("discount", ""))
    except SupplierResponseError as exc:
        result["problems"].append(str(exc))
        result.update(unit_price=None, discount_percent=None, net_price=None, net_source=None, line_value=None, availability_status=None)
        return INVALID
    status = QUOTED
    net = net_unit_cost(unit, discount) if unit is not None and discount is not None else None
    if unit is None:
        status = INCOMPLETE
        result["problems"].append("No unit cost.")
    if discount is None:
        status = INCOMPLETE
        result["problems"].append("The discount box is blank. A blank discount is not zero; enter 0 if there is none.")
    if not a.get("sku"):
        status = INCOMPLETE
        result["problems"].append("No SKU.")
    quantity = line.get("purchasing_quantity")
    line_value = None
    if net is not None and quantity is not None:
        line_value = (net * Decimal(str(quantity))).quantize(CENT, rounding=ROUND_HALF_UP)
    result["unit_price"] = str(unit) if unit is not None else None
    result["discount_percent"] = str(discount) if discount is not None else None
    result["net_price"] = str(net) if net is not None else None
    result["net_source"] = "calculated from the supplier's unit cost and discount" if net is not None else None
    result["line_value"] = str(line_value) if line_value is not None else None
    result["availability_status"] = None  # form 2 does not ask for availability
    return status


# Form 2 totals (Joel, 14 Oct 2026). The Recordable Quoted Total adds only complete, eligible
# supplier lines. It is not an approved cost: Brayman's cost approval stays a separate step.
EXCLUDE_IDENTITY = "Identity mismatch"
EXCLUDE_INVALID = "Invalid pricing"
EXCLUDE_SKU = "Missing SKU"
EXCLUDE_UNIT_COST = "Missing unit cost"
EXCLUDE_DISCOUNT = "Blank discount (a blank is not 0%)"
EXCLUDE_QTY = "Missing or TBD quantity"
EXCLUDE_NOT_FINAL = "Quantity not verified (line not marked FINAL QUANTITY)"
EXCLUDE_UOM = "Missing purchasing unit"
EXCLUDE_SUBSTITUTION = "Unresolved substitution"


def total_exclusions(row: Mapping) -> List[str]:
    """Why a form-2 line is not in the Recordable Quoted Total. Empty means it is included."""
    status = row.get("status")
    if status == NOT_QUOTED:
        return []
    if row.get("identity_failed"):
        return [EXCLUDE_IDENTITY]
    if status == INVALID:
        return [EXCLUDE_INVALID]
    answers = row.get("answers") or {}
    reasons = []
    if not (answers.get("sku") or "").strip():
        reasons.append(EXCLUDE_SKU)
    if row.get("unit_price") is None:
        reasons.append(EXCLUDE_UNIT_COST)
    if row.get("discount_percent") is None:
        reasons.append(EXCLUDE_DISCOUNT)
    if row.get("purchasing_quantity") is None:
        reasons.append(EXCLUDE_QTY)
    elif not row.get("quantity_final"):
        reasons.append(EXCLUDE_NOT_FINAL)
    if not (row.get("purchasing_unit") or "").strip():
        reasons.append(EXCLUDE_UOM)
    if status == SUBSTITUTION_REVIEW:
        reasons.append(EXCLUDE_SUBSTITUTION)
    if status not in (QUOTED, INCOMPLETE, SUBSTITUTION_REVIEW) and not reasons:
        reasons.append(EXCLUDE_INVALID)
    return reasons


def recordable_totals(rows: List[Dict]) -> Dict:
    """Recordable Quoted Total and the separate provisional value; marks every row."""
    recordable = Decimal("0")
    provisional = Decimal("0")
    included = excluded = provisional_lines = 0
    for row in rows:
        reasons = total_exclusions(row)
        quoted = row.get("status") != NOT_QUOTED
        row["in_recordable_total"] = quoted and not reasons and row.get("line_value") is not None
        row["total_exclusions"] = reasons
        row["partial_quote"] = quoted and bool(reasons)
        if row["in_recordable_total"]:
            recordable += Decimal(row["line_value"])
            included += 1
        elif quoted:
            excluded += 1
            if row.get("line_value") is not None:
                provisional += Decimal(row["line_value"])
                provisional_lines += 1
    return {
        "recordable_quoted_total": str(recordable.quantize(CENT)) if included else None,
        "recordable_lines": included,
        "excluded_lines": excluded,
        "provisional_value": str(provisional.quantize(CENT)) if provisional_lines else None,
        "provisional_lines": provisional_lines,
    }


def reconcile(manifest: Mapping, answers: Mapping, *, project_id: int, organization_id: str, catalogue_codes=frozenset()) -> Dict:
    """Match answers to the issued request. Refuse another project's response."""
    if answers.get("request_id") != manifest.get("request_id"):
        raise SupplierResponseError("This response is for a different supplier request.")
    if int(manifest.get("project_id")) != int(project_id) or manifest.get("organization_id") != organization_id:
        raise SupplierResponseError("This supplier request is not on this project.")
    if answers.get("request_project") and answers["request_project"] != str(int(project_id)):
        raise SupplierResponseError("This response is for a different project.")
    issues: List[str] = []
    try:
        valid_until = parse_date(answers.get("valid_until") or "")
    except SupplierResponseError as exc:
        valid_until = None
        issues.append(str(exc))
    try:
        response_date = parse_date(answers.get("response_date") or "")
    except SupplierResponseError as exc:
        response_date = None
        issues.append(str(exc))
    if valid_until is None:
        issues.append("The supplier did not state how long the prices are valid.")
    form = response_form(manifest)
    fields = response_fields(manifest)
    typed = SUPPLIER_TYPED_V2 if form == 2 else FIELDS_V1
    notes = answers.get("general_notes") or ""
    issued_numbers = {int(l["number"]) for l in manifest["lines"]}
    noted = notes_line_numbers(notes) & issued_numbers if form == 2 else set()
    notes_review_required = bool(form == 2 and notes.strip())
    if notes_review_required:
        issues.append(
            "The supplier wrote general notes. Brayman must read them and confirm before any price from this response is recorded."
            + (f" Lines named in the notes: {', '.join(str(n) for n in sorted(noted))}." if noted else " No line number was found in them.")
        )
    rows = []
    by_number = answers.get("lines") or {}
    for line in manifest["lines"]:
        number = int(line["number"])
        given = by_number.get(number, {})
        result = {
            "number": number,
            "key": line["key"],
            "description": line["description"],
            "purchasing_quantity": line["purchasing_quantity"],
            "purchasing_unit": line["purchasing_unit"],
            "stock_length_ft": line["stock_length_ft"],
            "takeoff_status": line["status"],
            "quantity_final": line["complete"],
            "canonical_material_code": line.get("canonical_material_code"),
            "canonical_identity": line.get("canonical_identity"),
            "answers": {name: given.get(name, "") for name in fields},
            "problems": [],
        }
        has_answer = any(given.get(name) for name in fields)
        if has_answer and (not given.get("line_key") or not given.get("line_sig")):
            result.update(status=INVALID, recording=NOT_RECORDABLE, identity_failed=True)
            result["problems"].append("The returned line has no line identity (the PDF viewer may have dropped it). It cannot be matched to the issued line; enter it by hand.")
            rows.append(result)
            continue
        if given.get("line_key") and given.get("line_key") != line["key"]:
            result.update(status=INVALID, recording=NOT_RECORDABLE, identity_failed=True)
            result["problems"].append("The line identity on the returned page does not match the issued line.")
            rows.append(result)
            continue
        if given.get("line_sig") and given.get("line_sig") != line["signature"]:
            result.update(status=INVALID, recording=NOT_RECORDABLE, identity_failed=True)
            result["problems"].append("The returned line does not match the issued quantity, unit, or stock length.")
            rows.append(result)
            continue
        a = result["answers"]
        if not any(a[name] for name in typed):
            result.update(status=NOT_QUOTED, recording=NOT_RECORDABLE)
            if form == 2 and number in noted:
                result.update(status=SUBSTITUTION_REVIEW)
                result["problems"].append("The supplier's general notes name this line. Brayman reviews it.")
            rows.append(result)
            continue
        if form == 2:
            status = _evaluate_v2(result, a, line)
            if number in noted and status in (QUOTED, INCOMPLETE):
                status = SUBSTITUTION_REVIEW
                result["problems"].append(
                    "The supplier's general notes name this line (a substitution). Brayman reviews it; this price is not recorded or approved from this response."
                )
            _finish(result, status, line, valid_until, catalogue_codes)
            rows.append(result)
            continue
        try:
            unit = _money(a["unit_price"])
            discount = _percent(a["discount"])
            net = _money(a["net_price"])
        except SupplierResponseError as exc:
            result.update(status=INVALID, recording=NOT_RECORDABLE)
            result["problems"].append(str(exc))
            rows.append(result)
            continue
        confirmed = _confirmed(a["product_confirmed"])
        net_source = "supplier"
        if net is None and unit is not None and discount is not None:
            net = (unit * (Decimal("100") - discount) / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
            net_source = "calculated from the supplier's unit price and discount"
        status = QUOTED
        if unit is not None and discount is not None and net is not None and net_source == "supplier":
            expected = (unit * (Decimal("100") - discount) / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP)
            if abs(expected - net) > TOLERANCE:
                status = PRICE_CONFLICT
                result["problems"].append(
                    f"Net {net} does not equal unit {unit} less {discount}% ({expected})."
                )
        if unit is not None and discount is None and net is not None:
            if net > unit:
                status = PRICE_CONFLICT
                result["problems"].append(f"Net {net} is above the unit price {unit}.")
            elif net < unit:
                implied = ((unit - net) * Decimal("100") / unit).quantize(CENT, rounding=ROUND_HALF_UP) if unit else None
                result["problems"].append(f"The discount box is blank. The net price implies {implied}%. Please confirm with the supplier.")
        if net is None:
            status = INCOMPLETE if status == QUOTED else status
            result["problems"].append("No net price. A blank discount is not zero.")
        if not a["sku"]:
            status = INCOMPLETE if status == QUOTED else status
            result["problems"].append("No product or SKU.")
        if confirmed in ("SUBSTITUTE", "UNCLEAR") or a["substitution"]:
            status = SUBSTITUTION_REVIEW if status in (QUOTED, INCOMPLETE) else status
            result["problems"].append("The supplier proposed a different product. Brayman decides before the price is used.")
        elif confirmed is None:
            status = INCOMPLETE if status == QUOTED else status
            result["problems"].append("The supplier did not confirm the product.")
        result["unit_price"] = str(unit) if unit is not None else None
        result["discount_percent"] = str(discount) if discount is not None else None
        result["net_price"] = str(net) if net is not None else None
        result["net_source"] = net_source if net is not None else None
        result["availability_status"] = _availability(a["availability"])
        if net is not None and line["purchasing_quantity"] is not None:
            result["line_value"] = str((net * Decimal(str(line["purchasing_quantity"]))).quantize(CENT, rounding=ROUND_HALF_UP))
        else:
            result["line_value"] = None
        _finish(result, status, line, valid_until, catalogue_codes)
        rows.append(result)
    extra = sorted(set(by_number) - {int(l["number"]) for l in manifest["lines"]})
    if extra:
        issues.append(f"Ignored response rows that were not issued: {', '.join(str(n) for n in extra)}.")
    summary = {}
    for row in rows:
        summary[row["status"]] = summary.get(row["status"], 0) + 1
    no_prices = form == 2 and all(r["status"] == NOT_QUOTED for r in rows)
    if no_prices:
        issues.insert(0, NO_PRICES_WARNING)
    totals = recordable_totals(rows) if form == 2 else {}
    return {
        "response_form": form,
        **totals,
        "notes_review_required": notes_review_required,
        "no_prices_found": no_prices,
        "notes_line_numbers": sorted(noted),
        "request_id": manifest["request_id"],
        "project_id": int(project_id),
        "organization_id": organization_id,
        "supplier_id": manifest["supplier_id"],
        "supplier_location_id": manifest["supplier_location_id"],
        "contractor_supplier_account_id": manifest["contractor_supplier_account_id"],
        "takeoff_fingerprint": manifest["takeoff_fingerprint"],
        "contact": answers.get("contact") or "",
        "response_date": response_date.date().isoformat() if response_date else None,
        "valid_until": valid_until.date().isoformat() if valid_until else None,
        "general_notes": answers.get("general_notes") or "",
        "issues": issues,
        "rows": rows,
        "summary": summary,
    }


def record_ready_lines(reconciliation: Mapping, *, actor_display_name: str, demo_synthetic: bool = False, notes_reviewed: bool = False) -> List[Dict]:
    """Append price and availability evidence for READY_TO_RECORD lines.

    Uses the existing supplier catalogue services. A new SKU becomes a
    supplier product. The supplier product is mapped to the line's canonical
    material by the person recording. A SKU already sold in another unit is
    refused. Nothing else is written.
    """
    from app import db
    from app.models.canonical_material import CanonicalMaterial
    from app.models.supplier_catalogue import CanonicalMaterialSupplierMap, SupplierProduct
    from app.services.supplier_catalogue import (
        SupplierCatalogueError,
        approve_canonical_material_supplier_map,
        create_supplier_product,
        record_availability_evidence,
        record_price_evidence,
    )

    actor = (actor_display_name or "").strip()
    if not actor:
        raise SupplierResponseError("The person recording supplier prices is required.")
    if reconciliation.get("notes_review_required") and not notes_reviewed:
        raise SupplierResponseError("Read the supplier's general notes and confirm you have reviewed them before recording prices.")
    valid_until = datetime.fromisoformat(reconciliation["valid_until"]) if reconciliation.get("valid_until") else None
    effective_from = datetime.fromisoformat(reconciliation["response_date"]) if reconciliation.get("response_date") else None
    if valid_until is not None:
        valid_until = valid_until.replace(hour=23, minute=59, second=59)
    if effective_from is not None and valid_until is not None and valid_until < effective_from:
        raise SupplierResponseError("The validity date is before the response date.")
    results = []
    for row in reconciliation["rows"]:
        if row.get("recording") != READY_TO_RECORD:
            continue
        material = CanonicalMaterial.query.filter_by(code=row["canonical_material_code"]).first()
        created_identity = False
        if material is None and row.get("canonical_identity"):
            from sqlalchemy.exc import IntegrityError

            from app.services.deck_takeoff.catalogue import ensure_identity

            try:
                material, created_identity = ensure_identity(row["canonical_identity"], actor_display_name=actor)
            except IntegrityError:
                db.session.rollback()
                results.append({"number": row["number"], "recorded": False, "reason": "The catalogue does not accept this category yet. Revision u1b2c3d4e5f6 is not applied."})
                continue
            except ValueError as exc:
                db.session.rollback()
                results.append({"number": row["number"], "recorded": False, "reason": str(exc)})
                continue
        if material is None:
            results.append({"number": row["number"], "recorded": False, "reason": "Canonical material not found."})
            continue
        sku = row["answers"]["sku"].strip()
        unit = row["purchasing_unit"]
        product = SupplierProduct.query.filter_by(supplier_id=reconciliation["supplier_id"], sku=sku).first()
        try:
            if product is None:
                product = create_supplier_product(
                    supplier_id=reconciliation["supplier_id"],
                    sku=sku,
                    description=row["description"][:220],
                    sales_uom=unit,
                    demo_synthetic=demo_synthetic,
                )
            elif product.sales_uom != unit:
                results.append({"number": row["number"], "recorded": False, "reason": f"SKU {sku} is sold by {product.sales_uom}, not {unit}."})
                continue
            mapped = CanonicalMaterialSupplierMap.query.filter_by(
                canonical_material_id=material.id, supplier_product_id=product.id, status="ACTIVE"
            ).first()
            if mapped is None:
                approve_canonical_material_supplier_map(
                    canonical_material_id=material.id,
                    supplier_product_id=product.id,
                    actor_display_name=actor,
                    demo_synthetic=demo_synthetic,
                )
            evidence = record_price_evidence(
                supplier_product_id=product.id,
                amount=row["net_price"],
                currency="CAD",
                unit=unit,
                price_class="CONTRACTOR_CONFIRMED_PRICE",
                actor_display_name=actor,
                contractor_supplier_account_id=reconciliation["contractor_supplier_account_id"],
                source="MANUAL",
                demo_synthetic=demo_synthetic,
                effective_from=effective_from,
                effective_to=valid_until,
            )
            availability = None
            if int(reconciliation.get("response_form") or 1) == 1:
                # Form 1 asked for availability. Form 2 does not, so nothing is recorded for it.
                availability = record_availability_evidence(
                    supplier_product_id=product.id,
                    supplier_location_id=reconciliation["supplier_location_id"],
                    status=row.get("availability_status") or "UNKNOWN",
                    actor_display_name=actor,
                    source="MANUAL",
                    demo_synthetic=demo_synthetic,
                )
        except SupplierCatalogueError as exc:
            db.session.rollback()
            results.append({"number": row["number"], "recorded": False, "reason": str(exc)})
            continue
        results.append(
            {
                "number": row["number"],
                "key": row["key"],
                "recorded": True,
                "canonical_material_id": material.id,
                "canonical_material_code": material.code,
                "canonical_identity_created": created_identity,
                "supplier_product_id": product.id,
                "price_evidence_id": evidence.id,
                "availability_evidence_id": availability.id if availability is not None else None,
            }
        )
    return results

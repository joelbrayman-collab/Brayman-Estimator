"""Job-specific supplier pricing request.

This is the manual transport over the best-available material read.
It does not write a MaterialRequirement, an estimate line, a costing
snapshot, a supplier product, or a price.
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

CONFIRMED_LABEL = "CONFIRMED"
CONTRACTOR_INPUT_LABEL = "CONTRACTOR INPUT REQUIRED"
SUPPLIER_PRODUCT_LABEL = "SUPPLIER PRODUCT REQUIRED"
SUPPLIER_PRICING_LABEL = "SUPPLIER PRICING REQUIRED"
SUPPLIER_AVAILABILITY_LABEL = "SUPPLIER AVAILABILITY REQUIRED"
SOURCE_GAP_LABEL = "MATERIAL / SOURCE GAP"
PUBLIC_LIST_LABEL = "PUBLIC / LIST PRICE"
PUBLIC_PRICE_NOT_AVAILABLE = "PUBLIC PRICE: NOT AVAILABLE"
TBD = "TBD"

RESPONSE_FIELDS = (
    ("product_confirmed", "BMR product confirmed"),
    ("sku", "BMR code / SKU"),
    ("availability", "Availability"),
    ("discount", "Contractor discount"),
    ("net_price", "Contractor net price"),
    ("quoted_price", "Quoted price"),
    ("substitute", "Substitute"),
    ("supplier_notes", "Supplier notes"),
)

ACCOUNT_FIELDS = (
    ("standard_discount", "Standard Brayman Winchester contractor discount"),
    ("category_exceptions", "Category exceptions"),
    ("net_exceptions", "Net-priced product exceptions"),
    ("quoted_products", "Quoted products"),
)

_ORDER = (
    ("joist", "Framing", "Joists"),
    ("stringer", "Framing", "Stair stringers"),
    ("post", "Framing", "Posts"),
    ("beam", "Framing", "Beams"),
    ("decking", "Decking", "Walking surface"),
    ("tread-boards", "Decking", "Stair treads"),
    ("veranda-kit", "Guards", "Veranda rail kit"),
    ("guard", "Guards", "Guard"),
    ("gate", "Guards", "Gate"),
    ("pier", "Foundation", "Helical piers"),
)


def build_job_supplier_pricing_request(
    readiness: Mapping,
    *,
    project_name: str,
    address: str,
    supplier_name: str,
    issued_on: str,
    model: Optional[Mapping] = None,
    public_prices: Optional[Mapping] = None,
) -> dict:
    """Shape one readiness read into a supplier request. Counts stay counts."""
    by_subject = {item["subject"]: item for item in readiness.get("items") or ()}
    lines = []
    for subject, category, title in _ORDER:
        item = by_subject.get(subject)
        if item is None:
            continue
        lines.append(_line(item, category, title, model, public_prices or {}))
    known_subjects = {subject for subject, _, _ in _ORDER}
    for item in readiness.get("items") or ():
        if item["subject"] in known_subjects:
            continue
        lines.append(_line(item, "Other", item.get("label") or item["subject"], model, public_prices or {}))
    return {
        "project_name": project_name,
        "address": address,
        "supplier_name": supplier_name,
        "issued_on": issued_on,
        "authority": (
            "The item lines are the response for this request. "
            "The account discount is supplementary."
        ),
        "lines": tuple(lines),
        "contractor_questions": tuple(
            line["contractor_action"] for line in lines if line["contractor_action"]
        ),
        "account_fields": ACCOUNT_FIELDS,
        "response_fields": RESPONSE_FIELDS,
    }


def _line(item, category, title, model, public_prices):
    quantity, unit, count_note = _count(item)
    return {
        "subject": item["subject"],
        "category": category,
        "title": title,
        "material": _material(item),
        "canonical_material_code": item.get("canonical_material_code"),
        "specification": _specification(item, model),
        "quantity": quantity,
        "unit": unit,
        "count_note": count_note,
        "sku": None,
        "public_price_label": _public_price(item, public_prices),
        "public_price_is_contractor_cost": False,
        "statuses": _statuses(item),
        "bmr_action": _bmr_action(item, title),
        "contractor_action": _contractor_action(item, title, quantity),
        "notes": _notes(item),
        "response_fields": RESPONSE_FIELDS,
    }


def _material(item) -> str:
    code = item.get("canonical_material_code")
    name = (item.get("material_name") or "").strip()
    if code and name:
        return f"{code} — {name}"
    if code:
        return code
    if name and name != item.get("subject"):
        return name
    return TBD


def _count(item):
    quantity = item.get("quantity")
    if quantity is None:
        return TBD, TBD, "Quantity is not stored."
    unit = item.get("unit") or TBD
    if item.get("quantity_meaning") == "member_count" and item.get("subject") == "decking":
        note = f"{quantity} member. This is the walking surface, not a board quantity."
    elif item.get("quantity_meaning") == "member_count":
        note = f"{quantity} members. This is not a purchase quantity."
    elif item.get("quantity_meaning") == "support_count":
        note = f"{quantity} locations. This is not a purchase quantity."
    else:
        note = "This count is not a purchase quantity."
    return str(quantity), unit, note


def _specification(item, model) -> str:
    subject = item.get("subject")
    stored = (item.get("specification") or "").strip()
    parts = []
    if subject == "joist":
        parts.append("Material TBD. Size TBD. Supplied length TBD.")
    elif subject == "stringer":
        parts.append("Material TBD. Size TBD. Supplied length TBD.")
        if stored:
            parts.append(stored + ".")
        parts.append("The throat and stair width are not a lumber purchase quantity.")
    elif subject == "decking":
        if stored:
            plain = stored.replace("lower-width", "Width").replace("lower-depth", "Depth")
            parts.append(plain + ".")
        height = _dimension(model, "lower-walking-surface-height")
        if height is not None:
            parts.append(f"Walking surface height {height}.")
        parts.append("These dimensions describe the walking surface. They are not a board quantity.")
    elif subject in {"post", "beam", "guard"}:
        parts.append("Material TBD. Size TBD. Supplied length TBD. Location TBD.")
    elif subject == "gate":
        opening = _dimension(model, "gate-clear")
        if opening is not None:
            parts.append(f"Clear opening {opening}.")
        parts.append("Location, size, and supplied length TBD.")
    elif subject == "tread-boards":
        if stored:
            parts.append(stored + ".")
        parts.append("Tread count TBD. Board length TBD.")
    elif subject == "veranda-kit":
        if stored:
            parts.append(stored + ".")
        parts.append("This name stays as stated. It is not a generic lumber identity. Kit count TBD.")
    elif subject == "pier":
        parts.append("Shaft TBD. Helix TBD. Length TBD. Product TBD.")
    elif stored:
        parts.append(stored)
    else:
        parts.append(TBD)
    return " ".join(parts)


def _dimension(model, identifier) -> Optional[str]:
    if not isinstance(model, Mapping):
        return None
    for dimension in model.get("dimensions") or []:
        if dimension.get("id") != identifier:
            continue
        value = dimension.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        unit = dimension.get("unit") or ""
        return f"{value} {unit}".strip()
    return None


def _statuses(item) -> tuple:
    labels = []
    requirement = item.get("requirement_status")
    if requirement == "CONFIRMED":
        labels.append(CONFIRMED_LABEL)
    elif requirement == "SOURCE_DATA":
        labels.append(SOURCE_GAP_LABEL)
        labels.append(CONTRACTOR_INPUT_LABEL)
    elif requirement == "CONTRACTOR_INPUT":
        labels.append(CONTRACTOR_INPUT_LABEL)
    if item.get("vocabulary_gap") and SOURCE_GAP_LABEL not in labels:
        labels.append(SOURCE_GAP_LABEL)
    if item.get("product_status") == "UNRESOLVED_SUPPLIER_PRODUCT":
        labels.append(SUPPLIER_PRODUCT_LABEL)
    if item.get("pricing_status") == "MISSING_CONTRACTOR_PRICE":
        labels.append(SUPPLIER_PRICING_LABEL)
    if not item.get("availability_status"):
        labels.append(SUPPLIER_AVAILABILITY_LABEL)
    return tuple(labels)


def _public_price(item, public_prices) -> str:
    code = item.get("canonical_material_code") or ""
    supplied = public_prices.get(code) if code else None
    if not supplied and item.get("public_price") not in (None, ""):
        supplied = {
            "amount": item.get("public_price"),
            "currency": item.get("currency") or "",
            "unit": item.get("public_price_unit") or "",
        }
    if not supplied:
        return PUBLIC_PRICE_NOT_AVAILABLE
    amount = supplied.get("amount")
    currency = supplied.get("currency") or ""
    unit = supplied.get("unit") or ""
    detail = " ".join(part for part in (str(amount), currency, f"per {unit}" if unit else "") if part)
    return f"{PUBLIC_LIST_LABEL} {detail}. This is not the contractor price."


def _bmr_action(item, title: str) -> str:
    subject = item.get("subject")
    if subject == "joist":
        return (
            "Identify the BMR product, SKU, availability, and current contractor price. "
            "Do not determine the number of joists."
        )
    if subject == "stringer":
        return (
            "Identify the BMR product, SKU, availability, and current contractor price. "
            "Do not turn the throat or the stair width into a purchase quantity."
        )
    if subject == "pier":
        return (
            "Identify the BMR pier product, SKU, availability, and current contractor price. "
            "Do not choose the shaft, helix, or length."
        )
    if subject == "veranda-kit":
        return (
            "Identify the BMR product, SKU, availability, and current contractor price "
            "for the named 37 in Veranda kit."
        )
    if subject == "tread-boards":
        return "Identify the BMR product, SKU, availability, and current contractor price."
    return f"Identify the BMR product, SKU, availability, and current contractor price for {title.lower()}."


def _contractor_action(item, title: str, quantity: str) -> str:
    subject = item.get("subject")
    if item.get("requirement_status") not in {"CONTRACTOR_INPUT", "SOURCE_DATA"}:
        if subject != "veranda-kit":
            return ""
    if subject == "joist":
        return f"Confirm joist material, size, and supplied length. The count of {quantity} members is already known."
    if subject == "stringer":
        return f"Confirm stringer material, size, and supplied length. The count of {quantity} members is already known."
    if subject == "decking":
        return "Confirm the deck board material, size, and quantity. The stored size is the walking surface, not a board count."
    if subject == "tread-boards":
        return "Confirm the tread count and the board length."
    if subject == "post":
        return "Confirm post material, size, location, and cut length."
    if subject == "beam":
        return "Confirm beam material, size, location, and supplied length."
    if subject == "guard":
        return "Confirm the guard location and layout. The named kit is a separate line."
    if subject == "gate":
        return "Confirm the gate location and construction. The clear opening is already recorded."
    if subject == "pier":
        return f"Confirm shaft, helix, and length. The count of {quantity} locations is already known."
    if subject == "veranda-kit":
        return "Confirm how many kits are required."
    return f"Confirm the missing project facts for {title.lower()}."


def _notes(item) -> str:
    parts = []
    if item.get("quantity_meaning") == "member_count":
        parts.append("Member count only.")
    elif item.get("quantity_meaning") == "support_count":
        parts.append("Location count only.")
    elif item.get("quantity") is None:
        parts.append("No quantity is stored.")
    if item.get("sku") in (None, ""):
        parts.append("No BMR SKU is stored.")
    if item.get("public_price") in (None, ""):
        parts.append("No public price is stored.")
    return " ".join(parts)

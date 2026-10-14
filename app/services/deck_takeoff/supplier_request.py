"""Supplier request rows and the issued-request manifest from a takeoff.

Brayman's quantities fill the approved page. The supplier fills the
response boxes. The manifest records exactly what was asked so a returned
PDF can be matched line by line.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Mapping, Optional

from app.services.deck_takeoff.records import (
    CALCULATED,
    ENGINEERING_REQUIRED,
    FIELD_VERIFICATION_REQUIRED,
    PRODUCT_DEPENDENT,
    fingerprint,
)

FINAL = "FINAL QUANTITY"
LABELS = {
    FIELD_VERIFICATION_REQUIRED: "CALCULATED — FIELD VERIFICATION BEFORE ORDERING",
    PRODUCT_DEPENDENT: "PRODUCT-DEPENDENT — NOT READY TO ORDER",
    ENGINEERING_REQUIRED: "ENGINEERING-DEPENDENT — NOT READY TO ORDER",
}


def status_label(item) -> str:
    if item["purchasing"]["complete"]:
        return FINAL
    if item["status"] == CALCULATED:
        return "PRODUCT-DEPENDENT — NOT READY TO ORDER"
    return LABELS[item["status"]]

SUPPLIER_NEEDED = "Supplier / manufacturer"
GROUP_ORDER = ("Decking", "Stairs", "Fascia", "Railing", "Structure", "Foundations", "Connectors", "Fasteners", "Skirting")


def _qty_text(value) -> str:
    if value is None:
        return "TBD"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def _unit_text(purchasing: Mapping) -> str:
    unit = purchasing.get("unit") or ""
    stock = purchasing.get("stock_length_ft")
    if stock:
        return f"{unit}\n{float(stock):g} ft stock"
    return unit


def request_rows(takeoff: Mapping) -> List[dict]:
    source = takeoff["source"]
    revision = source.get("construction_model_revision_number")
    sha = (source.get("construction_model_sha256") or "")[:8]
    rows = []
    ordered = sorted(
        (item for item in takeoff["lines"] if item["request"]),
        key=lambda item: GROUP_ORDER.index(item["group"]) if item["group"] in GROUP_ORDER else len(GROUP_ORDER),
    )
    for item in ordered:
        purchasing = item["purchasing"]
        parts = [item["description"]]
        if item.get("specification"):
            parts.append(item["specification"])
        asks = [f["fact"] for f in item["flags"] if f["needed_from"] == SUPPLIER_NEEDED]
        if asks:
            parts.append("PRODUCT FACT REQUIRED FIRST: " + "; ".join(dict.fromkeys(asks)) + ".")
        if purchasing["quantity"] is None:
            parts.append("Brayman will calculate the quantity once these facts are confirmed. Please price the product per unit.")
        elif any(f["status"] == ENGINEERING_REQUIRED for f in item["flags"]):
            parts.append("Specification is subject to Brayman confirmation before ordering.")
        parts.append(f"Source: project revision {revision} ({sha}), rule {takeoff['rule']['id']} v{takeoff['rule']['version']}.")
        row = {
            "key": item["key"],
            "item": " ".join(p.strip() for p in parts if p and p.strip()),
            "qty": _qty_text(purchasing["quantity"]),
            "unit": _unit_text(purchasing),
            "purchasing_quantity": purchasing["quantity"],
            "purchasing_unit": purchasing.get("unit"),
            "stock_length_ft": purchasing.get("stock_length_ft"),
            "status": item["status"],
            "complete": purchasing["complete"],
            "canonical_material_code": item.get("canonical_material_code"),
            "canonical_identity": item.get("canonical_identity"),
            "status_label": status_label(item),
            "description": item["description"],
        }
        row["signature"] = fingerprint(
            {
                "key": row["key"],
                "qty": row["purchasing_quantity"],
                "unit": row["purchasing_unit"],
                "stock": row["stock_length_ft"],
                "takeoff": takeoff["fingerprint"],
            }
        )[:24]
        rows.append(row)
    for number, row in enumerate(rows, start=1):
        row["number"] = number
    return rows


def build_request(
    *,
    takeoff: Mapping,
    project_id: int,
    organization_id: str,
    project_name: str,
    project_address: str,
    supplier_name: str,
    contractor_supplier_account_id: int,
    supplier_id: int,
    supplier_location_id: int,
    issued_by: str,
    issued_at: Optional[datetime] = None,
) -> Dict:
    issued_at = issued_at or datetime.utcnow()
    rows = request_rows(takeoff)
    request_id = "DTR-" + fingerprint(
        {
            "takeoff": takeoff["fingerprint"],
            "project": project_id,
            "organization": organization_id,
            "account": contractor_supplier_account_id,
        }
    )[:16].upper()
    complete = sum(1 for r in rows if r["complete"])
    intro = (
        "Please provide your current contractor pricing for the materials listed below. "
        "Brayman Construction calculated every quantity, unit, and stock length on this request. "
        f"Please do not change them. Where a line asks for a product fact first, please confirm that {supplier_name} product "
        "and price it per unit; Brayman will set the final quantity.",
        "For each line, enter the product or SKU, whether you confirm the product (Yes, or Substitute), the unit price, "
        "the contractor discount, the net price, availability, lead time, and any substitution. "
        "A blank is not zero. Please return this PDF to Brayman Construction.",
        f"{complete} of {len(rows)} lines have a final purchasing quantity and are marked FINAL QUANTITY. "
        "Only those lines are ready to order. Every other line is marked with what it is waiting for. Prices are CAD before HST.",
    )
    document = {
        "project_name": project_name,
        "project_address": project_address,
        "supplier_name": supplier_name,
        "issued_on": issued_at.strftime("%d %B %Y").lstrip("0"),
        "intro": intro,
        "rows": tuple({"number": r["number"], "item": r["item"], "status_label": r["status_label"], "qty": r["qty"], "unit": r["unit"], "key": r["key"], "signature": r["signature"]} for r in rows),
        "request_id": request_id,
        "project_id": project_id,
    }
    manifest = {
        "request_id": request_id,
        "kind": "pool_deck_supplier_request",
        "organization_id": organization_id,
        "project_id": project_id,
        "supplier_id": supplier_id,
        "supplier_location_id": supplier_location_id,
        "contractor_supplier_account_id": contractor_supplier_account_id,
        "supplier_name": supplier_name,
        "issued_at": issued_at.isoformat(timespec="seconds"),
        "issued_by": issued_by,
        "takeoff_fingerprint": takeoff["fingerprint"],
        "rule": takeoff["rule"],
        "source": takeoff["source"],
        "product_facts": takeoff["inputs"]["product_facts"],
        "lines": rows,
    }
    return {"document": document, "manifest": manifest}

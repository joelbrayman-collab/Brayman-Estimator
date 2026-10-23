"""Framing materials request for a straight wall: one supplier request from the count and the purchase.

The wall framing count and the purchase rules stay as they are
(``wall_framing`` and ``wall_framing_purchasing``). This module only turns
that purchase into the same supplier request the deck takeoff issues:
the same PDF, the same stored manifest, the same Supplier Hub share, the
same supplier price return and the same price evidence. No price, cost or
estimate line is created here, and no quantity rule is added.

A line carries a canonical material code only when the stock named in the
purchase is exactly a catalogued lumber item. Every other line is still
sent and priced, and its price cannot be recorded against a catalogue
identity until a person maps it. Nothing is guessed.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Mapping, Optional

from app.services.deck_takeoff.records import CALCULATED, PRODUCT_DEPENDENT, fingerprint
from app.services.deck_takeoff.supplier_request import (
    CURRENT_RESPONSE_FORM,
    FINAL,
    status_label,
)

KIND = "framing_supplier_request"
RULE = {"id": "straight_wall_framing_purchase", "version": "1"}

# Catalogued lumber, by nominal size and stock length. A precut stud has its own item.
_STOCK_CODES = {
    ("2X4", 8): "CAL-LUM-2X4-8",
    ("2X4", 10): "CAL-LUM-2X4-10",
    ("2X4", 12): "CAL-LUM-2X4-12",
    ("2X4", 16): "CAL-LUM-2X4-16",
    ("2X6", 8): "CAL-LUM-2X6-8",
    ("2X6", 12): "CAL-LUM-2X6-12",
    ("2X6", 16): "CAL-LUM-2X6-16",
    ("2X8", 12): "CAL-LUM-2X8-12",
    ("2X8", 16): "CAL-LUM-2X8-16",
    ("2X10", 12): "CAL-LUM-2X10-12",
    ("2X10", 16): "CAL-LUM-2X10-16",
    ("2X12", 16): "CAL-LUM-2X12-16",
}
_PRECUT_2X4_STUD = "CAL-LUM-2X4-STUD-9258"
_PRECUT_LENGTH_IN = Decimal("92.625")
FRAMING_CODES = frozenset(_STOCK_CODES.values()) | {_PRECUT_2X4_STUD}


class FramingRequestError(ValueError):
    pass


def _size(text) -> str:
    return "".join(str(text or "").upper().split()).replace("×", "X")


def _plain(value) -> str:
    text = format(Decimal(str(value)).normalize(), "f")
    return text


def _stock_code(size: str, stock_ft) -> Optional[str]:
    if stock_ft is None:
        return None
    feet = Decimal(str(stock_ft))
    if feet != feet.to_integral_value():
        return None
    return _STOCK_CODES.get((size, int(feet)))


def _stud_code(size: str, result: Mapping, bought: Mapping) -> Optional[str]:
    stock_in = bought.get("stud_stock_length_in")
    if stock_in is None:
        return None
    inches = Decimal(str(stock_in))
    if size == "2X4" and inches == _PRECUT_LENGTH_IN:
        return _PRECUT_2X4_STUD
    if inches % 12 != 0:
        return None
    return _stock_code(size, inches / 12)


def request_rows(result: Mapping, bought: Mapping) -> List[dict]:
    """The lines to buy, from the purchase. Quantity, unit and stock come from the purchase only."""
    size = _size(result["stud_size"])
    rows: List[dict] = []

    def add(key, description, quantity, unit, stock_ft, complete, code):
        rows.append(
            {
                "key": key,
                "description": description,
                "purchasing_quantity": quantity,
                "purchasing_unit": unit,
                "stock_length_ft": stock_ft,
                "status": CALCULATED if complete else PRODUCT_DEPENDENT,
                "complete": complete,
                "canonical_material_code": code,
                "canonical_identity": None,
            }
        )

    stud_stock_in = bought.get("stud_stock_length_in")
    add(
        "framing.studs",
        bought["displays"]["studs"],
        int(bought["stud_pieces"]),
        "EA",
        None if stud_stock_in is None else float(Decimal(str(stud_stock_in)) / 12),
        True,
        _stud_code(size, result, bought),
    )
    plate_stock = bought.get("plate_stock_length_ft")
    if bought.get("plate_pieces") is not None:
        add(
            "framing.plates",
            bought["displays"]["plates"],
            int(bought["plate_pieces"]),
            "EA",
            float(plate_stock),
            True,
            _stock_code(size, plate_stock),
        )
    else:
        add(
            "framing.plates",
            bought["displays"]["plates"] + " Please price per lineal foot and name your stock length.",
            float(bought["plate_order_lineal_ft"]),
            "LF",
            None,
            False,
            None,
        )
    for number, member in enumerate(bought.get("members") or (), start=1):
        add(
            "framing.member.{0}".format(number),
            "{0}, {1} ft".format(member["label"], _plain(member["length_ft"])),
            int(member["count"]),
            "EA",
            float(member["length_ft"]),
            True,
            None,
        )
    return rows


def build_framing_request(
    *,
    result: Mapping,
    bought: Mapping,
    project_id: int,
    organization_id: str,
    project_name: str,
    project_address: str,
    supplier_name: str,
    contractor_supplier_account_id: int,
    supplier_id: int,
    supplier_location_id: int,
    issued_by: str,
    estimate_reference: str = "",
    issued_at: Optional[datetime] = None,
) -> Dict:
    """Build the supplier request and the manifest that matches a returned price line by line."""
    issued_at = issued_at or datetime.utcnow()
    lines = request_rows(result, bought)
    basis = {
        "wall": {
            "length_ft": _plain(result["length_ft"]),
            "height_ft": _plain(result["height_ft"]),
            "spacing_in": _plain(result["spacing_in"]),
            "stud_size": result["stud_size"],
        },
        "purchase": {
            "waste_percent": _plain(bought["waste_percent"]),
            "stud_stock_length_in": None if bought["stud_stock_length_in"] is None else _plain(bought["stud_stock_length_in"]),
            "plate_stock_length_ft": None if bought["plate_stock_length_ft"] is None else _plain(bought["plate_stock_length_ft"]),
        },
        "lines": [(l["key"], l["purchasing_quantity"], l["purchasing_unit"]) for l in lines],
    }
    takeoff_fingerprint = fingerprint(basis)
    request_id = "FRQ-" + fingerprint(
        {"takeoff": takeoff_fingerprint, "project": project_id, "organization": organization_id,
         "account": contractor_supplier_account_id, "form": CURRENT_RESPONSE_FORM}
    )[:16].upper()
    rows = []
    for number, line in enumerate(lines, start=1):
        quantity = line["purchasing_quantity"]
        quantity_text = str(int(quantity)) if float(quantity).is_integer() else _plain(quantity)
        unit_text = line["purchasing_unit"]
        if line["stock_length_ft"]:
            unit_text = "{0}\n{1:g} ft stock".format(unit_text, float(line["stock_length_ft"]))
        label = status_label({"status": line["status"], "purchasing": {"complete": line["complete"]}})
        row = dict(line)
        row.update(
            number=number,
            item=line["description"],
            qty=quantity_text,
            unit=unit_text,
            status_label=label,
        )
        row["signature"] = fingerprint(
            {"key": row["key"], "qty": quantity, "unit": row["purchasing_unit"],
             "stock": row["stock_length_ft"], "takeoff": takeoff_fingerprint}
        )[:24]
        rows.append(row)
    final = sum(1 for r in rows if r["complete"])
    intro = (
        "Please provide your current contractor pricing for the framing materials listed below"
        + (" ({0}).".format(estimate_reference) if estimate_reference else ".")
        + " Brayman Construction counted every quantity, unit and stock length on this request. Please do not change them.",
        "For each line, enter your SKU, the unit cost, and the contractor discount (enter 0 if there is none). "
        "Brayman calculates every total from its quantity when this PDF is returned. A blank discount is not zero. "
        "For a substitution, write the original line number and your replacement SKU under General notes, "
        "and price the replacement on that line. Please return this PDF to Brayman Construction.",
        "{0} of {1} lines have a final purchasing quantity and are marked {2}. Every other line is marked with what it is "
        "waiting for. Prices are CAD before HST.".format(final, len(rows), FINAL),
    )
    document = {
        "project_name": project_name,
        "project_address": project_address,
        "supplier_name": supplier_name,
        "issued_on": issued_at.strftime("%d %B %Y").lstrip("0"),
        "intro": intro,
        "rows": tuple(
            {"number": r["number"], "item": r["item"], "status_label": r["status_label"], "qty": r["qty"],
             "unit": r["unit"], "key": r["key"], "signature": r["signature"]}
            for r in rows
        ),
        "request_id": request_id,
        "project_id": project_id,
        "layout": CURRENT_RESPONSE_FORM,
    }
    manifest = {
        "request_id": request_id,
        "kind": KIND,
        "response_form": CURRENT_RESPONSE_FORM,
        "organization_id": organization_id,
        "project_id": project_id,
        "supplier_id": supplier_id,
        "supplier_location_id": supplier_location_id,
        "contractor_supplier_account_id": contractor_supplier_account_id,
        "supplier_name": supplier_name,
        "issued_at": issued_at.isoformat(timespec="seconds"),
        "issued_by": issued_by,
        "takeoff_fingerprint": takeoff_fingerprint,
        "rule": RULE,
        "source": {"kind": "straight_wall_framing", "estimate": estimate_reference},
        "product_facts": {},
        "lines": rows,
    }
    return {"document": document, "manifest": manifest}


def _needed_by(text):
    from datetime import date

    text = (text or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise FramingRequestError("The needed-by date must be a date (YYYY-MM-DD).")


def issue_and_send_framing_request(
    *, project, account, result, bought, user, issued_by, estimate_reference="", needed_by=""
):
    """Issue the request (PDF and manifest, kept once) and send it to the supplier in CalibraytAI.

    The same call a second time returns the request already issued. A supplier that has no
    Supplier Hub sign-in cannot be sent to; the PDF is still kept so the office can send it.
    """
    from app.services.brayman_supplier_estimate import render_supplier_response_request
    from app.services.deck_takeoff import storage
    from app.services.supplier_hub import send_material_request

    built = build_framing_request(
        result=result,
        bought=bought,
        project_id=project.id,
        organization_id=project.organization_id,
        project_name=project.name,
        project_address=project.address or "",
        supplier_name=account.supplier.legal_name,
        contractor_supplier_account_id=account.id,
        supplier_id=account.supplier_id,
        supplier_location_id=account.supplier_location_id,
        issued_by=issued_by or "Office",
        estimate_reference=estimate_reference,
    )
    request_id = built["manifest"]["request_id"]
    if storage.load_request(project.organization_id, project.id, request_id) is None:
        storage.save_request(
            project.organization_id,
            project.id,
            built["manifest"],
            render_supplier_response_request(**built["document"]),
        )
    due = _needed_by(needed_by)
    share = send_material_request(project=project, request_id=request_id, user=user, needed_by=due)
    return {"request_id": request_id, "share": share, "supplier": account.supplier.legal_name}

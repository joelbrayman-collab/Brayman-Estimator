"""Standalone contractor calculators.

Concrete and Stair render the preserved Website engines in the browser.
The Employment vs Entrepreneurship page sends the preserved Website file.
The ICF page calls the existing 8-inch quantity service.
This module does not write a project or an estimate.
"""

import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import Blueprint, render_template, request, send_file

from app.services.icf_manufacturer_profiles import IcfProfileError, list_profiles
from app.services.icf_quantity import IcfQuantityInputError, build_icf_standard_quantities

calculators_bp = Blueprint(
    "calculators",
    __name__,
    url_prefix="/calculators",
)

_QUANTITY_LABELS = {
    "standard_forms": "Standard forms",
    "corner_90_8_forms": "90-degree corners",
    "corner_45_8_forms": "45-degree corners",
    "concrete": "Concrete",
}


@calculators_bp.get("/concrete")
def concrete():
    return render_template("calculators/concrete.html")


@calculators_bp.get("/stairs")
def stairs():
    return render_template("calculators/stairs.html")


_EMPLOYMENT_PAGE = (
    Path(__file__).resolve().parents[2]
    / "calculation-engines"
    / "employment-vs-entrepreneurship"
    / "website-source"
    / "public"
    / "employment-vs-entrepreneurship"
    / "index.html"
)


@calculators_bp.get("/employment-vs-entrepreneurship")
def employment_vs_entrepreneurship():
    """Send the preserved page. Do not recalculate it in Python."""
    return send_file(_EMPLOYMENT_PAGE, mimetype="text/html")


def _whole_number(text):
    cleaned = (text or "").strip()
    if cleaned == "":
        return None
    if not cleaned.isdigit():
        raise IcfQuantityInputError("Enter a whole number, including 0.")
    return int(cleaned)


def _wall_form_values():
    if request.method != "POST":
        return {
            "manufacturer_id": "",
            "net_wall_area": "",
            "corner_90": "",
            "corner_45": "",
        }
    return {
        "manufacturer_id": (request.form.get("manufacturer_id") or "").strip(),
        "net_wall_area": (request.form.get("net_wall_area") or "").strip(),
        "corner_90": (request.form.get("corner_90") or "").strip(),
        "corner_45": (request.form.get("corner_45") or "").strip(),
    }


def _quantity_rows(result):
    payload = result.get("payload") if result else None
    if not payload:
        return []
    return [
        {
            "label": _QUANTITY_LABELS.get(item["code"], item["code"]),
            "quantity": item["quantity"],
            "unit_code": item["unit_code"],
        }
        for item in payload["quantities"]
    ]


@calculators_bp.route("/wall-form", methods=["GET", "POST"])
def wall_form():
    """Ask for the existing 8-inch wall inputs. Do not open an estimate."""
    profiles = list_profiles()
    values = _wall_form_values()
    error = None
    result = None
    if request.method == "POST":
        try:
            if not values["manufacturer_id"]:
                raise IcfQuantityInputError("Choose a manufacturer.")
            corner_90 = _whole_number(values["corner_90"])
            corner_45 = _whole_number(values["corner_45"])
            if corner_90 is None or corner_45 is None:
                raise IcfQuantityInputError(
                    "Corner counts are required. Enter 0 when the wall has none."
                )
            if not values["net_wall_area"]:
                raise IcfQuantityInputError("Enter the net wall area.")
            try:
                Decimal(values["net_wall_area"])
            except InvalidOperation as exc:
                raise IcfQuantityInputError(
                    "Enter the net wall area as a decimal number."
                ) from exc
            result = build_icf_standard_quantities(
                manufacturer_id=values["manufacturer_id"],
                net_wall_area_ft2=values["net_wall_area"],
                corner_90_count=corner_90,
                corner_45_count=corner_45,
                result_id="office-icf-{0}".format(uuid.uuid4().hex),
            )
            result["blocked"] = any(
                item.get("classification") == "TRUE PLATFORM DEPENDENCY"
                for item in result["inputs_required"]
            )
        except (IcfQuantityInputError, IcfProfileError) as exc:
            error = str(exc)
            result = None
    return render_template(
        "calculators/icf_wall.html",
        profiles=profiles,
        values=values,
        error=error,
        result=result,
        quantity_rows=_quantity_rows(result),
    )

"""Live supplier-program economic model.

Office login is required. The page does not read contractor projects,
estimates, margins, or labour rates.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request

from app.services.supplier_economic_model import FIELD_LABELS, calculate

supplier_program_bp = Blueprint(
    "supplier_program",
    __name__,
    url_prefix="/supplier-program",
)

PAGE_PATH = "/economic-model"


@supplier_program_bp.get(PAGE_PATH)
def economic_model():
    return render_template(
        "supplier_program/economic_model.html",
        field_labels=FIELD_LABELS,
    )


@supplier_program_bp.post(PAGE_PATH + "/calculate")
def economic_model_calculate():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    return jsonify(calculate(payload))

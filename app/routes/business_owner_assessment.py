"""FG-039 Employment vs Entrepreneurship Decision Tool.

Public PLAN decision tool. No office chrome. No durable records. No DB writes.
Narrow login exemption via blueprint prefix.
"""

from __future__ import annotations

from datetime import date

from flask import Blueprint, jsonify, render_template, request, send_file

from app.services.business_owner_assessment import (
    DEFAULT_INPUTS,
    PRODUCT_NAME,
    TRADE_PROFILE_STARTING_ASSUMPTIONS,
    assert_finite_payload,
    calculate,
)
from app.services.business_owner_assessment_pdf import (
    assessment_pdf_filename,
    generate_assessment_pdf,
)

decision_tools_bp = Blueprint(
    "decision_tools",
    __name__,
    url_prefix="/decision-tools",
)

PAGE_PATH = "/employment-vs-entrepreneurship"


@decision_tools_bp.get("/")
def decision_tools_index():
    from flask import redirect, url_for

    return redirect(url_for("decision_tools.employment_vs_entrepreneurship"))


@decision_tools_bp.get(PAGE_PATH)
def employment_vs_entrepreneurship():
    return render_template(
        "decision_tools/employment_vs_entrepreneurship.html",
        product_name=PRODUCT_NAME,
        defaults=DEFAULT_INPUTS,
        profiles=TRADE_PROFILE_STARTING_ASSUMPTIONS,
    )


@decision_tools_bp.post(f"{PAGE_PATH}/calculate")
def calculate_assessment():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    result = assert_finite_payload(calculate(payload))
    return jsonify(result)


@decision_tools_bp.post(f"{PAGE_PATH}/results.pdf")
def download_results_pdf():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    calc_date = _iso_date(payload.pop("calculation_date", None)) or date.today().isoformat()
    result = assert_finite_payload(calculate(payload))
    buffer = generate_assessment_pdf(result, calculation_date=calc_date)
    filename = assessment_pdf_filename(result["inputs"].get("scenario_name"), calc_date)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


def _iso_date(value):
    if value is None or value == "":
        return None
    text = str(value).strip()[:10]
    try:
        date.fromisoformat(text)
    except ValueError:
        return None
    return text

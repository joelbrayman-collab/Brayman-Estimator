"""Supplier-program economic model for a live discussion.

Typed assumptions only. No contractor records. No stored supplier prices.
The formulas follow the operational ROI extension of the supplier-channel
specification. This module does not create a second commercial model.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

MODEL_ID = "supplier-program-economic-model"
MODEL_VERSION = "1"

CLASS_KNOWN = "known"
CLASS_ESTIMATED = "estimated"
CLASS_UNESTABLISHED = "unestablished"

STATUS_ESTABLISHED = "established"
STATUS_NOT_ESTABLISHED = "not_established"

MONEY = Decimal("0.01")
QUANTITY = Decimal("0.0001")
ZERO = Decimal("0")

FIELDS = (
    "active_contractor_accounts",
    "takeoff_share_percent",
    "takeoff_requests_per_month",
    "manual_hours_per_takeoff",
    "estimator_cost_per_hour",
    "validation_hours_per_takeoff",
    "hours_per_quote",
    "contribution_per_quote",
    "average_material_value",
    "quote_to_order_percent",
    "material_gross_margin_percent",
    "base_platform_cost",
    "active_contractor_cost",
)

PERCENT_FIELDS = frozenset(
    {
        "takeoff_share_percent",
        "quote_to_order_percent",
        "material_gross_margin_percent",
    }
)

FIELD_LABELS = {
    "active_contractor_accounts": "Active PRO / eligible contractor accounts",
    "takeoff_share_percent": "Expected adoption / CalibraytAI takeoff share",
    "takeoff_requests_per_month": "Takeoff requests per month",
    "manual_hours_per_takeoff": "Average manual hours per takeoff",
    "estimator_cost_per_hour": "Fully loaded estimator cost per hour",
    "validation_hours_per_takeoff": "Average CalibraytAI validation hours per takeoff",
    "hours_per_quote": "Average estimator hours per quote",
    "contribution_per_quote": "Incremental contribution per additional quote",
    "average_material_value": "Average material value per opportunity",
    "quote_to_order_percent": "Quote-to-order conversion",
    "material_gross_margin_percent": "Material gross margin",
    "base_platform_cost": "Base supplier platform cost",
    "active_contractor_cost": "Active contractor cost",
}


def calculate(payload):
    """Return the discussion result for supplier-entered assumptions."""
    if not isinstance(payload, dict):
        payload = {}
    parsed = {key: _parse_field(key, payload.get(key)) for key in FIELDS}
    results = _results(parsed)
    summary = _summary(parsed)
    return {
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "inputs": parsed,
        "summary": summary,
        "results": results,
        "separation": {
            "takeoff_labour_value": "direct operational labour economics",
            "capacity_value": "additional productive opportunity",
            "commercial_value": "supplier material economics",
            "same_hours_counted_once": True,
        },
    }


def _parse_field(key, raw):
    label = FIELD_LABELS[key]
    if not isinstance(raw, dict):
        raw = {}
    text = raw.get("value")
    if text is None:
        text = ""
    text = str(text).strip().replace(",", "").replace("$", "").replace("%", "")
    classification = raw.get("classification")
    if text == "":
        return {
            "label": label,
            "value": None,
            "classification": CLASS_UNESTABLISHED,
            "error": None,
        }
    if classification != CLASS_KNOWN:
        classification = CLASS_ESTIMATED
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        return {
            "label": label,
            "value": None,
            "classification": CLASS_UNESTABLISHED,
            "error": "Enter a number.",
        }
    if not number.is_finite():
        return {
            "label": label,
            "value": None,
            "classification": CLASS_UNESTABLISHED,
            "error": "Enter a number.",
        }
    if number < ZERO:
        return {
            "label": label,
            "value": None,
            "classification": CLASS_UNESTABLISHED,
            "error": "Enter a number that is zero or greater.",
        }
    if key in PERCENT_FIELDS and number > Decimal("100"):
        return {
            "label": label,
            "value": None,
            "classification": CLASS_UNESTABLISHED,
            "error": "Enter a percent from 0 to 100.",
        }
    return {
        "label": label,
        "value": format(number, "f"),
        "classification": classification,
        "error": None,
    }


def _dec(parsed, key):
    item = parsed[key]
    if item["value"] is None:
        return None
    return Decimal(item["value"])


def _class_of(parsed, keys):
    classes = [parsed[key]["classification"] for key in keys]
    if CLASS_ESTIMATED in classes:
        return CLASS_ESTIMATED
    return CLASS_KNOWN


def _established(value, classification, scale):
    quantized = value.quantize(scale, rounding=ROUND_HALF_UP)
    return {
        "status": STATUS_ESTABLISHED,
        "value": format(quantized, "f"),
        "classification": classification,
    }


def _missing():
    return {
        "status": STATUS_NOT_ESTABLISHED,
        "value": None,
        "classification": CLASS_UNESTABLISHED,
    }


def _results(parsed):
    requests = _dec(parsed, "takeoff_requests_per_month")
    share = _dec(parsed, "takeoff_share_percent")
    manual_hours = _dec(parsed, "manual_hours_per_takeoff")
    validation_hours = _dec(parsed, "validation_hours_per_takeoff")
    rate = _dec(parsed, "estimator_cost_per_hour")
    hours_per_quote = _dec(parsed, "hours_per_quote")
    contribution = _dec(parsed, "contribution_per_quote")
    material_value = _dec(parsed, "average_material_value")
    conversion = _dec(parsed, "quote_to_order_percent")
    margin = _dec(parsed, "material_gross_margin_percent")
    base_cost = _dec(parsed, "base_platform_cost")
    active_cost = _dec(parsed, "active_contractor_cost")

    annual = None
    if requests is not None:
        annual = _established(
            requests * Decimal("12"),
            _class_of(parsed, ("takeoff_requests_per_month",)),
            QUANTITY,
        )
    else:
        annual = _missing()

    originated = None
    share_ratio = None
    if requests is not None and share is not None:
        share_ratio = share / Decimal("100")
        originated_count = requests * Decimal("12") * share_ratio
        originated = _established(
            originated_count,
            _class_of(parsed, ("takeoff_requests_per_month", "takeoff_share_percent")),
            QUANTITY,
        )
    else:
        originated = _missing()
        originated_count = None

    if requests is not None and manual_hours is not None:
        manual_takeoff_hours = _established(
            requests * Decimal("12") * manual_hours,
            _class_of(parsed, ("takeoff_requests_per_month", "manual_hours_per_takeoff")),
            QUANTITY,
        )
    else:
        manual_takeoff_hours = _missing()

    if originated_count is not None and validation_hours is not None:
        validation_total = _established(
            originated_count * validation_hours,
            _class_of(
                parsed,
                (
                    "takeoff_requests_per_month",
                    "takeoff_share_percent",
                    "validation_hours_per_takeoff",
                ),
            ),
            QUANTITY,
        )
    else:
        validation_total = _missing()

    labour_keys = (
        "takeoff_requests_per_month",
        "takeoff_share_percent",
        "manual_hours_per_takeoff",
        "validation_hours_per_takeoff",
        "estimator_cost_per_hour",
    )
    if (
        originated_count is not None
        and manual_hours is not None
        and validation_hours is not None
        and rate is not None
    ):
        manual_cost = originated_count * manual_hours * rate
        validation_cost = originated_count * validation_hours * rate
        labour_value = manual_cost - validation_cost
        labour = _established(labour_value, _class_of(parsed, labour_keys), MONEY)
    else:
        manual_cost = None
        validation_cost = None
        labour_value = None
        labour = _missing()

    if originated_count is not None and manual_hours is not None and validation_hours is not None:
        released = originated_count * (manual_hours - validation_hours)
        hours_released = _established(
            released,
            _class_of(
                parsed,
                (
                    "takeoff_requests_per_month",
                    "takeoff_share_percent",
                    "manual_hours_per_takeoff",
                    "validation_hours_per_takeoff",
                ),
            ),
            QUANTITY,
        )
    else:
        released = None
        hours_released = _missing()

    if released is not None and hours_per_quote is not None and hours_per_quote != ZERO:
        quote_capacity_count = released / hours_per_quote
        quote_capacity = _established(
            quote_capacity_count,
            _class_of(
                parsed,
                (
                    "takeoff_requests_per_month",
                    "takeoff_share_percent",
                    "manual_hours_per_takeoff",
                    "validation_hours_per_takeoff",
                    "hours_per_quote",
                ),
            ),
            QUANTITY,
        )
    else:
        quote_capacity_count = None
        quote_capacity = _missing()

    if quote_capacity_count is not None and contribution is not None:
        capacity_amount = quote_capacity_count * contribution
        capacity = _established(
            capacity_amount,
            _class_of(
                parsed,
                (
                    "takeoff_requests_per_month",
                    "takeoff_share_percent",
                    "manual_hours_per_takeoff",
                    "validation_hours_per_takeoff",
                    "hours_per_quote",
                    "contribution_per_quote",
                ),
            ),
            MONEY,
        )
    else:
        capacity_amount = None
        capacity = _missing()

    commercial_keys = (
        "takeoff_requests_per_month",
        "average_material_value",
        "quote_to_order_percent",
        "material_gross_margin_percent",
    )
    if (
        requests is not None
        and material_value is not None
        and conversion is not None
        and margin is not None
    ):
        commercial_amount = (
            requests
            * Decimal("12")
            * material_value
            * (conversion / Decimal("100"))
            * (margin / Decimal("100"))
        )
        commercial = _established(
            commercial_amount, _class_of(parsed, commercial_keys), MONEY
        )
        commercial["formula"] = (
            "annual takeoff volume × average material value "
            "× quote-to-order conversion × material gross margin"
        )
        commercial["sales_are_not_profit"] = True
        commercial["actual_sales"] = False
    else:
        commercial_amount = None
        commercial = _missing()

    if base_cost is not None and active_cost is not None:
        program_amount = base_cost + active_cost
        program = _established(
            program_amount,
            _class_of(parsed, ("base_platform_cost", "active_contractor_cost")),
            MONEY,
        )
    else:
        program_amount = None
        program = _missing()

    if labour_value is not None:
        operational_amount = labour_value
        operational_keys = list(labour_keys)
        if capacity_amount is not None:
            operational_amount = labour_value + capacity_amount
            operational_keys.append("contribution_per_quote")
            operational_keys.append("hours_per_quote")
        operational = _established(
            operational_amount, _class_of(parsed, tuple(operational_keys)), MONEY
        )
        operational["includes_capacity_value"] = capacity_amount is not None
    else:
        operational_amount = None
        operational = _missing()

    if (
        operational_amount is not None
        and commercial_amount is not None
        and program_amount is not None
    ):
        net = _established(
            operational_amount + commercial_amount - program_amount,
            _broader_class(operational, commercial, program),
            MONEY,
        )
    else:
        net = _missing()

    if (
        operational_amount is not None
        and commercial_amount is not None
        and program_amount is not None
        and program_amount != ZERO
    ):
        roi = _established(
            (operational_amount + commercial_amount) / program_amount,
            _broader_class(operational, commercial, program),
            QUANTITY,
        )
    else:
        roi = _missing()

    if program_amount is not None and labour_value is not None:
        remaining_amount = program_amount - labour_value
        if capacity_amount is not None:
            remaining_amount = remaining_amount - capacity_amount
        if remaining_amount <= ZERO:
            break_even = {
                "status": "achieved",
                "remaining_value": format(ZERO.quantize(MONEY), "f"),
                "classification": _broader_class(labour, capacity if capacity_amount is not None else labour, program),
            }
        else:
            break_even = {
                "status": "remaining",
                "remaining_value": format(
                    remaining_amount.quantize(MONEY, rounding=ROUND_HALF_UP), "f"
                ),
                "classification": _broader_class(
                    labour,
                    capacity if capacity_amount is not None else labour,
                    program,
                ),
            }
    else:
        break_even = {
            "status": STATUS_NOT_ESTABLISHED,
            "remaining_value": None,
            "classification": CLASS_UNESTABLISHED,
        }

    if break_even["status"] == "achieved":
        additional_sales = _established(ZERO, break_even["classification"], MONEY)
    elif (
        break_even["status"] == "remaining"
        and margin is not None
        and margin != ZERO
    ):
        additional_sales = _established(
            Decimal(break_even["remaining_value"]) / (margin / Decimal("100")),
            _broader_class(break_even, {"classification": _class_of(parsed, ("material_gross_margin_percent",))}),
            MONEY,
        )
    else:
        additional_sales = _missing()

    return {
        "annual_takeoff_volume": annual,
        "calibraytai_originated_takeoff_volume": originated,
        "manual_takeoff_hours": manual_takeoff_hours,
        "validation_hours": validation_total,
        "takeoff_labour_value": labour,
        "hours_released": hours_released,
        "additional_quote_capacity": quote_capacity,
        "capacity_value": capacity,
        "commercial_value": commercial,
        "program_cost": program,
        "operational_value": operational,
        "net_supplier_value": net,
        "roi_multiple": roi,
        "break_even": break_even,
        "additional_material_sales": additional_sales,
        "manual_labour_cost": _money_or_missing(manual_cost, labour),
        "validation_labour_cost": _money_or_missing(validation_cost, labour),
    }


def _money_or_missing(amount, sibling):
    if amount is None:
        return _missing()
    return _established(amount, sibling["classification"], MONEY)


def _broader_class(*parts):
    classes = []
    for part in parts:
        if isinstance(part, dict) and part.get("classification"):
            classes.append(part["classification"])
    if CLASS_ESTIMATED in classes:
        return CLASS_ESTIMATED
    if classes and all(item == CLASS_KNOWN for item in classes):
        return CLASS_KNOWN
    return CLASS_UNESTABLISHED


def _summary(parsed):
    groups = {CLASS_KNOWN: [], CLASS_ESTIMATED: [], CLASS_UNESTABLISHED: []}
    for key in FIELDS:
        item = parsed[key]
        groups[item["classification"]].append(item["label"])
    return {
        "known": groups[CLASS_KNOWN],
        "estimated": groups[CLASS_ESTIMATED],
        "unestablished": groups[CLASS_UNESTABLISHED],
    }

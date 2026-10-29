"""The Supplier Pricing Request template library.

A template is a reusable package for one kind of job (the first: Hardie vertical siding with aluminum soffit,
fascia and trim). It holds the item list, specifications, units, summary groups and the rule that turns plan
measurements into a quantity for each item, so the next job of that kind only needs its measurements. Templates
hold no prices, no client and no supplier; they live in ``app/data/supplier_pricing_templates/`` (one JSON file
each, versioned in the key: a changed template is a new file) and fill the approved Supplier Pricing Request form
unchanged.

Rules (quantities round up; we lean slightly high so the supplier does no work):
* ``{"measure": m, "waste": w, "per_piece": p}``: ceil(measurement x (1 + w) / p)
* ``{"pieces_of": [item keys], "per_unit": n}``: ceil(sum of those items' quantities / n), e.g. nail boxes
* ``{"fixed": n}``: n
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

LIBRARY = Path(__file__).resolve().parents[1] / "data" / "supplier_pricing_templates"


class SupplierPricingTemplateError(ValueError):
    pass


def list_templates() -> list[dict]:
    """The library: key, title, trade and scope of each template, by title."""
    out = []
    for path in sorted(LIBRARY.glob("*.json")):
        t = json.loads(path.read_text())
        out.append({"key": t["key"], "title": t["title"], "trade": t.get("trade", ""), "scope": t.get("scope", "")})
    return sorted(out, key=lambda t: t["title"])


def load_template(key: str) -> dict:
    if not key.replace("-", "").isalnum():
        raise SupplierPricingTemplateError("Unknown template.")
    path = LIBRARY / f"{key}.json"
    if not path.is_file():
        raise SupplierPricingTemplateError(f"No template {key} in the library.")
    template = json.loads(path.read_text())
    if template.get("key") != key:
        raise SupplierPricingTemplateError(f"Template file {key}.json names another key.")
    return template


def quantities(template: dict, measurements: dict) -> dict:
    """Each item's quantity from the job's measurements, in item order."""
    known = {m["key"] for m in template["measurements"]}
    missing = sorted(k for k in known if k not in measurements)
    if missing:
        raise SupplierPricingTemplateError("Missing measurements: " + ", ".join(missing))
    extra = sorted(k for k in measurements if k not in known)
    if extra:
        raise SupplierPricingTemplateError("Not measurements of this template: " + ", ".join(extra))
    values = {}
    for k, v in measurements.items():
        try:
            values[k] = float(str(v).replace(",", ""))
        except ValueError:
            raise SupplierPricingTemplateError(f"Measurement {k} is not a number.") from None
        if values[k] < 0:
            raise SupplierPricingTemplateError(f"Measurement {k} cannot be negative.")
    qty = {}
    for item in template["items"]:
        rule = item["rule"]
        if "fixed" in rule:
            n = rule["fixed"]
        elif "measure" in rule:
            n = _up(values[rule["measure"]] * (1 + rule.get("waste", 0)) / rule["per_piece"])
        elif "pieces_of" in rule:
            n = _up(sum(qty[k] for k in rule["pieces_of"]) / rule["per_unit"])
        else:
            raise SupplierPricingTemplateError(f"Item {item['key']} has no rule.")
        qty[item["key"]] = int(n)
    return qty


def request_from_template(key: str, measurements: dict, *, project: str, supplier: str, supplier_tag: str,
                          requested: str, plans: str = "", choices: Optional[dict] = None,
                          contact: Optional[dict] = None, prepared_by: str = "") -> dict:
    """The approved form's request (what render_supplier_pricing_request_form takes) for one job."""
    template = load_template(key)
    chosen = dict(template.get("choices", {}))
    unknown = sorted(set(choices or {}) - set(chosen))
    if unknown:
        raise SupplierPricingTemplateError("Not choices of this template: " + ", ".join(unknown))
    chosen.update(choices or {})
    qty = quantities(template, measurements)
    fields = {k: _number(v) for k, v in measurements.items()}
    fields.update(chosen)
    fields.update({f"qty_{k}": v for k, v in qty.items()})
    items = [{"key": i["key"], "group": i["group"], "item": i["item"], "spec": i["spec"].format(**fields),
              "qty": qty[i["key"]], "unit": i["unit"]} for i in template["items"]]
    return {"project": project, "supplier": supplier, "supplier_tag": supplier_tag, "requested": requested,
            "plans": plans, "scope": template.get("scope", ""), "contact": contact or {}, "prepared_by": prepared_by,
            "groups": template["groups"], "items": items, "template": key}


def _up(x: float) -> int:
    return math.ceil(round(x, 6))


def _number(v) -> str:
    n = float(str(v).replace(",", ""))
    return f"{n:,.0f}" if n == int(n) else f"{n:,.2f}".rstrip("0").rstrip(".")

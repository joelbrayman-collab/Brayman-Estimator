"""Read-only comparison of the supplier quotes returned for one project.

Lines are matched by the request line key (the same material in the same request family). Nothing
is recorded, approved or priced here. Totals count only what the supplier actually priced.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Dict, List


def _num(value):
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None


def compare_responses(records: List[Dict]) -> Dict:
    suppliers = []
    for record in records:
        suppliers.append(
            {
                "response_id": record.get("response_id"),
                "label": record.get("source") or record.get("response_id"),
                "valid_until": record.get("valid_until"),
                "total": _num(record.get("recordable_quoted_total")),
            }
        )
    lines: Dict[str, Dict] = {}
    for index, record in enumerate(records):
        for row in record.get("rows") or ():
            key = row.get("key") or row.get("description")
            entry = lines.setdefault(
                key,
                {"key": key, "description": row.get("description"), "qty": row.get("purchasing_quantity"),
                 "unit": row.get("purchasing_unit"), "cells": {}},
            )
            net = _num(row.get("net_price"))
            entry["cells"][index] = {
                "net": net, "total": _num(row.get("line_value")), "sku": (row.get("answers") or {}).get("sku"),
            }
    for entry in lines.values():
        nets = [c["net"] for c in entry["cells"].values() if c["net"] is not None]
        low = min(nets) if len(nets) > 1 else None
        for c in entry["cells"].values():
            c["lowest"] = low is not None and c["net"] == low
    return {"suppliers": suppliers, "lines": list(lines.values())}

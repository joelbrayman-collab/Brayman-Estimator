"""Product availability wording (Joel, 24 Oct 2026, decision 3).

Availability is shown only when it is backed by data the supplier itself provided: an availability status on a
row of the supplier's own price file (supplier_selling_prices.availability, PRO Desk), or the supplier's returned
answer recorded as availability evidence (supplier_product_availability_evidence, contractor side). Everything
else — no data, UNKNOWN, an unreadable answer — reads exactly "Availability not confirmed".

CalibraytAI holds no inventory: it never shows a quantity on hand and never implies stock it was not told about.
A shown status is the supplier's own statement at the time it was given, not live inventory.
"""

from __future__ import annotations

AVAILABILITY_NOT_CONFIRMED = "Availability not confirmed"

CONFIRMED_AVAILABILITY = {
    "IN_STOCK": "In stock (supplier-reported)",
    "LIMITED": "Limited (supplier-reported)",
    "SPECIAL_ORDER": "Special order (supplier-reported)",
}


def _key(status) -> str:
    from jinja2 import Undefined

    if status is None or isinstance(status, Undefined):  # no data (or a record without the field)
        return ""
    if not isinstance(status, str):
        status = getattr(status, "status", "")  # an availability evidence row
    return str(status or "").strip().upper().replace(" ", "_")


def availability_confirmed(status) -> bool:
    """True only for a status the supplier itself gave (in stock, limited, special order)."""
    return _key(status) in CONFIRMED_AVAILABILITY


def availability_label(status) -> str:
    """The supplier-reported status, or exactly "Availability not confirmed"."""
    return CONFIRMED_AVAILABILITY.get(_key(status), AVAILABILITY_NOT_CONFIRMED)

"""Supplier Hub insights: what needs attention, period figures, material demand, remembered SKUs.

Read-only (Joel, 17 Oct 2026, owner review B–D). Every figure comes from records CalibraytAI
already keeps for this one supplier account: the requests contractors sent to it, the quotes it
returned, the purchase orders it received and the delivery changes on them. Nothing is estimated.
Requested is not ordered, and ordered through CalibraytAI is not a sale: the store's invoices and
payments are not in CalibraytAI. Nothing here writes to the database.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional
from zoneinfo import ZoneInfo

from app import db
from app.models.canonical_material import CanonicalMaterial
from app.models.supplier_portal import (
    KIND_CONCRETE,
    KIND_MATERIAL,
    PO_CANCELLED,
    PO_CONFIRMED,
    PO_PLACED,
    SHARE_OPENED,
    SHARE_RETURNED,
    SHARE_SENT,
    SHARE_SUPERSEDED,
    SHARE_WITHDRAWN,
    SupplierPurchaseOrder,
    SupplierRequestShare,
)

LOCAL_TZ = ZoneInfo("America/Toronto")
UPCOMING_DAYS = 14
ATTENTION_LIST_LIMIT = 5
CONVERSION_PERCENT_MIN = 5  # below this many returned quotes the page shows "x of y" only

PERIODS = (
    ("week", "This week"),
    ("month", "This month"),
    ("90d", "Last 90 days"),
    ("all", "All time"),
    ("custom", "Custom dates"),
)
DEFAULT_PERIOD = "90d"


# ------------------------------------------------------------------ periods


@dataclass(frozen=True)
class Period:
    key: str
    label: str
    start: Optional[date]  # first local day included; None = from the beginning
    end: Optional[date]  # last local day included; None = up to today

    def utc_bounds(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """Naive UTC datetimes (how the records are stored) for the local-day range."""
        lo = hi = None
        if self.start is not None:
            lo = datetime.combine(self.start, time.min, LOCAL_TZ).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        if self.end is not None:
            hi = datetime.combine(self.end + timedelta(days=1), time.min, LOCAL_TZ).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        return lo, hi

    def contains(self, moment: Optional[datetime]) -> bool:
        if moment is None:
            return False
        lo, hi = self.utc_bounds()
        return (lo is None or moment >= lo) and (hi is None or moment < hi)


def local_today() -> date:
    return datetime.now(LOCAL_TZ).date()


def _parse_day(raw) -> Optional[date]:
    try:
        return date.fromisoformat(str(raw or "").strip())
    except ValueError:
        return None


def resolve_period(key: Optional[str], start_raw=None, end_raw=None, *, today: Optional[date] = None) -> Period:
    """This week starts Monday (Toronto). Custom dates fall back to the default when unusable."""
    today = today or local_today()
    labels = dict(PERIODS)
    key = key if key in labels else DEFAULT_PERIOD
    if key == "week":
        return Period(key, labels[key], today - timedelta(days=today.weekday()), today)
    if key == "month":
        return Period(key, labels[key], today.replace(day=1), today)
    if key == "90d":
        return Period(key, labels[key], today - timedelta(days=89), today)
    if key == "all":
        return Period(key, labels[key], None, None)
    start, end = _parse_day(start_raw), _parse_day(end_raw)
    if start is None or end is None or end < start:
        return resolve_period(DEFAULT_PERIOD, today=today)
    label = f"{start.strftime('%b %d, %Y')} – {end.strftime('%b %d, %Y')}".replace(" 0", " ")
    return Period(key, label, start, end)


# ------------------------------------------------------------------ needs attention


def _visible_shares(supplier_id: int):
    return [s for s in SupplierRequestShare.query.filter_by(supplier_id=supplier_id)
            .order_by(SupplierRequestShare.sent_at.asc()).all() if s.status != SHARE_WITHDRAWN]


def _orders(supplier_id: int):
    return SupplierPurchaseOrder.query.filter_by(supplier_id=supplier_id).order_by(SupplierPurchaseOrder.id.asc()).all()


def attention(supplier_id: int, *, today: Optional[date] = None) -> dict:
    """What this store should act on now, oldest first. Counts plus up to five items each."""
    from app.services.supplier_hub import current_schedule, pending_change

    today = today or local_today()
    quotes = [s for s in _visible_shares(supplier_id) if s.status in (SHARE_SENT, SHARE_OPENED)]
    orders = _orders(supplier_id)
    to_confirm = [o for o in orders if o.status == PO_PLACED]
    changes = []
    upcoming = []
    horizon = today + timedelta(days=UPCOMING_DAYS)
    for order in orders:
        if order.status not in (PO_PLACED, PO_CONFIRMED):
            continue
        change = pending_change(order)
        if change is not None and change.requested_by_side == "CONTRACTOR":
            changes.append(change)
        schedule = current_schedule(order)
        if schedule["date"] is not None and today <= schedule["date"] <= horizon:
            upcoming.append({"order": order, "date": schedule["date"], "window": schedule["window"],
                             "agreed": schedule["agreed"], "change_pending": change is not None})
    upcoming.sort(key=lambda row: (row["date"], row["order"].id))
    changes.sort(key=lambda c: c.id)
    return {
        "quotes": quotes[:ATTENTION_LIST_LIMIT], "quotes_count": len(quotes),
        "orders": to_confirm[:ATTENTION_LIST_LIMIT], "orders_count": len(to_confirm),
        "changes": changes[:ATTENTION_LIST_LIMIT], "changes_count": len(changes),
        "upcoming": upcoming[:ATTENTION_LIST_LIMIT], "upcoming_count": len(upcoming),
        "upcoming_days": UPCOMING_DAYS,
        "total": len(quotes) + len(to_confirm) + len(changes),
    }


# ------------------------------------------------------------------ period figures


def period_figures(supplier_id: int, period: Period, *, today: Optional[date] = None) -> dict:
    """Actual records only. Each figure counts by its own event date inside the period."""
    shares = _visible_shares(supplier_id)
    orders = _orders(supplier_id)
    live_orders = [o for o in orders if o.status != PO_CANCELLED]
    ordered_share_ids = {o.share_id for o in live_orders}

    received = [s for s in shares if s.status != SHARE_SUPERSEDED and period.contains(s.sent_at)]
    returned = [s for s in shares if s.returned_at is not None and period.contains(s.returned_at)]
    converted = [s for s in returned if s.id in ordered_share_ids]
    placed = [o for o in live_orders if period.contains(o.placed_at)]
    confirmed = [o for o in orders if o.status == PO_CONFIRMED and period.contains(o.supplier_responded_at)]
    valued = [o for o in placed if o.status in (PO_PLACED, PO_CONFIRMED)]
    value_total = sum((Decimal(o.total) for o in valued), Decimal("0"))
    minutes = [s.minutes_reported for s in returned if s.minutes_reported is not None]
    returned_count = len(returned)
    conversion_percent = None
    if returned_count >= CONVERSION_PERCENT_MIN:
        conversion_percent = round(100 * len(converted) / returned_count)
    return {
        "period": period,
        "quotes_received": len(received),
        "quotes_returned": returned_count,
        "quotes_ordered": len(converted),
        "conversion_percent": conversion_percent,
        "conversion_percent_min": CONVERSION_PERCENT_MIN,
        "orders_placed": len(placed),
        "orders_confirmed": len(confirmed),
        "orders_with_problem": sum(1 for o in placed if o.status == "PROBLEM"),
        "orders_valued": len(valued),
        "ordered_value": value_total,
        "average_order_value": (value_total / len(valued)).quantize(Decimal("0.01")) if valued else None,
        "quotes_with_minutes": len(minutes),
        "average_minutes": (sum(minutes) / len(minutes)) if minutes else None,
        "hours_recorded": (Decimal(sum(minutes)) / Decimal(60)).quantize(Decimal("0.1")) if minutes else None,
        "upcoming_deliveries": attention(supplier_id, today=today)["upcoming_count"],
    }


# ------------------------------------------------------------------ material demand


def _manifest_lines(share) -> dict:
    """Server-side only: the contractor's own request lines, keyed by line number.

    Only the catalogue code and the purchasing quantity/unit are used. Nothing else from the
    contractor's estimate is read, and nothing from here is shown that was not already sent.
    """
    if share.request_kind != KIND_MATERIAL:
        return {}
    from app.services.deck_takeoff import storage

    try:
        manifest = storage.load_request(share.organization_id, share.project_id, share.source_ref)
    except Exception:  # a missing or unreadable request never breaks the page
        return {}
    if not manifest:
        return {}
    out = {}
    for line in manifest.get("lines") or []:
        try:
            out[int(line["number"])] = {
                "code": line.get("canonical_material_code") or (line.get("canonical_identity") or {}).get("code"),
                "category": (line.get("canonical_identity") or {}).get("category"),
                "quantity": line.get("purchasing_quantity"),
                "unit": line.get("purchasing_unit") or line.get("unit") or "",
            }
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _returned_rows(share) -> dict:
    """The store's own returned quote rows, keyed by line number."""
    if share.request_kind != KIND_MATERIAL or not share.response_ref:
        return {}
    from app.services.deck_takeoff import storage

    try:
        record = storage.load_response(share.organization_id, share.project_id, share.response_ref)
    except Exception:
        return {}
    rows = {}
    for row in (record or {}).get("rows") or []:
        try:
            rows[int(row["number"])] = row
        except (KeyError, TypeError, ValueError):
            continue
    return rows


def _decimal(value) -> Optional[Decimal]:
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except (InvalidOperation, ValueError):
        return None


def _plain(value: Decimal) -> str:
    """12, 12.5, 0 — never scientific notation."""
    if not value:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _material_lookup(codes) -> dict:
    codes = [c for c in set(codes) if c]
    if not codes:
        return {}
    return {m.code: m for m in CanonicalMaterial.query.filter(CanonicalMaterial.code.in_(codes)).all()}


def _confirmed_sku_material_ids(supplier_id: int) -> set:
    from app.models.supplier_catalogue import CanonicalMaterialSupplierMap, SupplierProduct

    rows = (db.session.query(CanonicalMaterialSupplierMap.canonical_material_id)
            .join(SupplierProduct, SupplierProduct.id == CanonicalMaterialSupplierMap.supplier_product_id)
            .filter(SupplierProduct.supplier_id == supplier_id, SupplierProduct.status == "ACTIVE",
                    CanonicalMaterialSupplierMap.status == "ACTIVE").all())
    return {row[0] for row in rows}


CATEGORY_LABELS = {
    "DIMENSIONAL_LUMBER": "Dimensional lumber", "SHEET_GOODS": "Sheet goods", "CONCRETE": "Concrete",
    "DECKING": "Decking", "FASCIA": "Fascia", "RAILING": "Railing", "GATE": "Gates",
    "FOUNDATION": "Foundation", "CONNECTOR": "Connectors", "FASTENER": "Fasteners",
}


def _category_label(raw) -> str:
    text = str(raw or "").strip()
    if not text:
        return "Other"
    return CATEGORY_LABELS.get(text.upper(), text.replace("_", " ").title())


def material_demand(supplier_id: int, period: Period) -> dict:
    """Requested materials from requests sent to THIS store in the period, grouped by product.

    Privacy: only requests shared with this supplier account; no project, address, customer or
    contractor name (contractors are counted, not named); never anything sent to another supplier.
    """
    shares = [s for s in _visible_shares(supplier_id)
              if s.status != SHARE_SUPERSEDED and period.contains(s.sent_at)]
    orders_by_share = {}
    for order in _orders(supplier_id):
        if order.status != PO_CANCELLED:
            orders_by_share[order.share_id] = order
    confirmed_ids = _confirmed_sku_material_ids(supplier_id)

    groups: dict = {}
    concrete: dict = {}
    contractors_all = set()
    line_total = 0
    for share in shares:
        contractors_all.add(share.organization_id)
        if share.request_kind == KIND_CONCRETE:
            c = (share.shared_json or {}).get("concrete") or {}
            key = f"{c.get('strength_mpa') or '?'} MPa"
            g = concrete.setdefault(key, {"label": f"Ready-mix concrete, {key}", "requests": 0, "contractors": set(),
                                          "volume": Decimal("0"), "quoted": 0, "ordered": 0})
            g["requests"] += 1
            g["contractors"].add(share.organization_id)
            g["volume"] += _decimal(c.get("volume_m3")) or Decimal("0")
            g["quoted"] += 1 if share.status == SHARE_RETURNED else 0
            g["ordered"] += 1 if share.id in orders_by_share else 0
            continue
        manifest = _manifest_lines(share)
        returned = _returned_rows(share) if share.status == SHARE_RETURNED else {}
        order = orders_by_share.get(share.id)
        ordered = {}
        if order is not None:
            for line in order.lines_json or []:
                try:
                    ordered[int(line["number"])] = _decimal(line.get("quantity"))
                except (KeyError, TypeError, ValueError):
                    continue
        for line in (share.shared_json or {}).get("lines") or []:
            try:
                number = int(line["number"])
            except (KeyError, TypeError, ValueError):
                continue
            line_total += 1
            facts = manifest.get(number, {})
            code = facts.get("code")
            unit = facts.get("unit") or line.get("unit") or ""
            key = (code, unit) if code else (None, (line.get("description") or "").strip().lower(), unit)
            g = groups.setdefault(key, {
                "code": code, "description": (line.get("description") or "").strip(), "unit": unit,
                "category_raw": facts.get("category"), "requests": 0, "share_ids": set(), "contractors": set(),
                "quantity": Decimal("0"), "without_quantity": 0, "quoted": 0, "not_priced": 0,
                "unpriced_shares": set(), "priced_shares": set(),
                "ordered_quantity": Decimal("0"), "ordered_lines": 0,
            })
            if share.id not in g["share_ids"]:
                g["share_ids"].add(share.id)
                g["requests"] += 1
            g["contractors"].add(share.organization_id)
            qty = _decimal(facts.get("quantity") if facts else line.get("purchasing_quantity"))
            if qty is None:
                g["without_quantity"] += 1
            else:
                g["quantity"] += qty
            if share.status == SHARE_RETURNED:
                row = returned.get(number)
                answers = (row or {}).get("answers") or {}
                priced = row is not None and row.get("status") == "QUOTED" and str(answers.get("sku") or "").strip()
                if priced:
                    g["quoted"] += 1
                    g["priced_shares"].add(share.id)
                else:
                    g["not_priced"] += 1
                    g["unpriced_shares"].add(share.id)
            if number in ordered:
                g["ordered_lines"] += 1
                g["ordered_quantity"] += ordered[number] or Decimal("0")

    materials = _material_lookup(g["code"] for g in groups.values())
    rows = []
    for g in groups.values():
        material = materials.get(g["code"]) if g["code"] else None
        confirmed_sku = material is not None and material.id in confirmed_ids
        rows.append({
            "name": material.display_name if material is not None else g["description"],
            "category": _category_label(material.category if material is not None else g["category_raw"]),
            "unit": g["unit"],
            "requests": g["requests"],
            "contractors": len(g["contractors"]),
            "quantity": _plain(g["quantity"]),
            "without_quantity": g["without_quantity"],
            "quoted": g["quoted"],
            "not_priced": g["not_priced"],
            "ordered_lines": g["ordered_lines"],
            "ordered_quantity": _plain(g["ordered_quantity"]),
            "confirmed_sku": confirmed_sku,
            "recurring": g["requests"] >= 2,
            "unpriced_requests": len(g["unpriced_shares"] - g["priced_shares"]),
            # A possible assortment gap: returned without a price in at least two separate requests and
            # never priced by this store. Shown as a prompt to look, never as a conclusion.
            "possible_gap": (len(g["unpriced_shares"]) >= 2 and not g["priced_shares"]),
        })
    rows.sort(key=lambda r: (r["category"], -r["requests"], r["name"].lower()))
    categories = []
    for row in rows:
        if not categories or categories[-1]["name"] != row["category"]:
            categories.append({"name": row["category"], "rows": []})
        categories[-1]["rows"].append(row)
    concrete_rows = [{"label": g["label"], "requests": g["requests"], "contractors": len(g["contractors"]),
                      "volume": _plain(g["volume"]), "quoted": g["quoted"], "ordered": g["ordered"]}
                     for _, g in sorted(concrete.items())]
    return {
        "period": period,
        "requests": len(shares),
        "contractors": len(contractors_all),
        "lines": line_total,
        "categories": categories,
        "concrete": concrete_rows,
        "recurring": [r for r in rows if r["recurring"]],
        "no_confirmed_sku": [r for r in rows if not r["confirmed_sku"]],
        "possible_gaps": [r for r in rows if r["possible_gap"]],
    }


# ------------------------------------------------------------------ remembered SKUs


def remembered_skus(share) -> dict:
    """{line number: {"sku": ..., "confirmed_at": ...}} from verified mappings for THIS store.

    A suggestion only: the line's catalogue material must have exactly one ACTIVE, human-approved
    mapping to an ACTIVE product of this supplier sold in the same unit. Prices and discounts are
    never suggested. Mappings are only ever created when a contractor records a returned quote.
    """
    if share.request_kind != KIND_MATERIAL or share.status not in (SHARE_SENT, SHARE_OPENED):
        return {}
    from app.models.supplier_catalogue import CanonicalMaterialSupplierMap, SupplierProduct

    manifest = _manifest_lines(share)
    materials = _material_lookup(f.get("code") for f in manifest.values())
    if not materials:
        return {}
    by_material: dict = {}
    rows = (db.session.query(CanonicalMaterialSupplierMap, SupplierProduct)
            .join(SupplierProduct, SupplierProduct.id == CanonicalMaterialSupplierMap.supplier_product_id)
            .filter(SupplierProduct.supplier_id == share.supplier_id, SupplierProduct.status == "ACTIVE",
                    CanonicalMaterialSupplierMap.status == "ACTIVE",
                    CanonicalMaterialSupplierMap.canonical_material_id.in_([m.id for m in materials.values()]))
            .all())
    for mapping, product in rows:
        by_material.setdefault(mapping.canonical_material_id, []).append((mapping, product))
    out = {}
    for number, facts in manifest.items():
        material = materials.get(facts.get("code"))
        if material is None:
            continue
        candidates = [(m, p) for m, p in by_material.get(material.id, []) if p.sales_uom == facts.get("unit")]
        skus = {p.sku for _, p in candidates}
        if len(skus) == 1:
            mapping, product = max(candidates, key=lambda mp: mp[0].approved_at or mp[0].created_at)
            out[number] = {"sku": product.sku, "confirmed_at": mapping.approved_at or mapping.created_at}
        elif len(skus) > 1:
            out[number] = {"sku": "", "several": sorted(skus)}
    return out

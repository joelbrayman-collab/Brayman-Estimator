"""Internal Project Financial Summary (layout approved by Joel, 2 Nov 2026).

An internal contractor document for every project and estimate, generated from the working estimate (or, once the
estimate is approved, from the figures frozen in its approval record). Never shown to customers, suppliers or field
crew: it carries costs, margins and the crew's Loaded Labour Rates.

Pages (landscape letter, flat PDF that opens in any viewer): 1 the summary (three totals; one row per work package;
profit and loss; how we price it internally; the contractor approval block); then MATERIALS – PROJECT SUMMARY,
LABOUR – PROJECT SUMMARY and, only when the estimate has subcontracts, SUBCONTRACTORS – PROJECT SUMMARY. Long tables
continue on "(continued)" pages; every page says Page X of N.

Data mapping (docs/implementation/internal-project-financial-summary-2026-11-02.md):
* packages: the guided work packages in Brayman's price (work_packages), in order; sections no package owns become
  their own package (a manual estimate's sections).
* revenue per package: the customer selling price of its lines (the frozen pricing when it is current, otherwise the
  same calculation on the working lines), so the packages add up to the estimate's selling price exactly.
* line kinds: guided_estimating._line_kind via pricing_engine.pricing_bucket: labour (LAB- lines), materials,
  subcontract (GE-SUBCONTRACT), at cost (equipment, delivery, disposal, allowances, other).
* real labour cost: hours x the estimate crew's Loaded Labour Rates (blended by share). With no crew assigned the
  summary says so and shows labour at the charge rate only: it never invents a cost.

This is not one of the governed DOCX Approved Masters.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app import db

SCHEMA = "calibrayt.internal-financial-summary.v1"
TITLE = "Internal Project Financial Summary"
DOCUMENT_TYPE = "INTERNAL_FINANCIAL_SUMMARY"
D = Decimal
ZERO = Decimal("0")

_BRANDING = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "branding")
BRAYMAN_LOGO = os.path.join(_BRANDING, "brayman-construction-logo.png")
CALIBRAYT_LOGO = os.path.join(_BRANDING, "calibraytai-logo-v2.png")

INK = colors.HexColor("#1F2328"); GREY = colors.HexColor("#52514e"); MUTED = colors.HexColor("#6B7280")
RULE = colors.HexColor("#D5DAE1"); NAVY = colors.HexColor("#173B5F"); RED = colors.HexColor("#A3201B")
TOTAL = colors.HexColor("#FBF1D9"); CALC = colors.HexColor("#F4F5F7"); BAND = colors.HexColor("#E9EEF4")


def q(x) -> Decimal:
    return D(x).quantize(D("0.01"), ROUND_HALF_UP)


def m(v) -> str:
    if v is None:
        return "—"
    v = D(v)
    return f"(${-v:,.2f})" if v < 0 else f"${v:,.2f}"


def pct(a, b) -> str:
    return f"{q(D(a) / D(b) * 100):.1f}%" if b and a is not None else "—"


def _s(value) -> Optional[str]:
    return None if value is None else str(value)


def _qty(value) -> str:
    v = D(str(value or 0))
    return f"{v.quantize(D('0.01')).normalize():f}" if v != v.to_integral_value() else f"{v.to_integral_value():,f}"


# ============================================================================================ data from the estimate
def _guided(version):
    from app.models.guided_estimating import GuidedEstimate

    return GuidedEstimate.query.filter_by(estimate_id=version.estimate_id).first()


def _packages(version):
    """[(name, stage or None, lines)] for the work in Brayman's price, in order."""
    from app.services import work_packages as WP

    guided = _guided(version)
    out, owned = [], set()
    for package in WP.packages_in(guided, version):
        lines = WP.package_lines(package, version)
        owned.update(line.id for line in lines)
        if WP.package_participates(package, version) and lines:
            out.append((package.display_name, package, lines))
    for section in sorted(version.sections, key=lambda s: (s.sort_order or 0, s.id)):
        lines = [line for line in section.line_items if line.id not in owned]
        if lines and WP.section_participates(section):
            out.append((section.name or "Estimate lines", None, lines))
    return out


RULE_OF_BUCKET = {"equipment": "equipment_markup", "delivery": "delivery_markup", "other": "other_markup",
                  "unclassified": "unclassified_markup"}


def _excluded_names(version):
    return [row["name"] for row in _excluded(version, None)]


def _quoted_price(package, version, e) -> Decimal:
    """What Brayman had quoted for an excluded package: its selling price on the newest earlier version that priced it
    in; otherwise its price by this estimate's pricing method (the internal price)."""
    from app.services import work_packages as WP
    from app.services.pricing_engine import as_money, labour_material_margin_price, true_gross_margin_pre_tax

    for earlier in sorted(version.estimate.versions, key=lambda v: v.version_number, reverse=True):
        if earlier.version_number >= version.version_number or getattr(earlier, "pricing_snapshot", None) is None:
            continue
        if WP.package_participates(package, earlier):
            sold = sum((D(str(l.sell_price or 0)) for l in WP.package_lines(package, earlier)), ZERO)
            if sold:
                return as_money(sold)
    lines = WP.package_lines(package, version)
    margin = e.get("target_gross_margin") if e else None
    if margin is None:
        return as_money(sum((D(str(l.extended_cost or 0)) for l in lines), ZERO))
    if (e or {}).get("pricing_method") == "LABOUR_AT_RATE_MATERIAL_MARGIN":
        return labour_material_margin_price(lines, margin, None, (e or {}).get("pricing_rules"))["pre_tax"]
    return true_gross_margin_pre_tax(sum((D(str(l.extended_cost or 0)) for l in lines), ZERO), margin)


def _excluded(version, e) -> list:
    """Packages of this version's scope not in Brayman's price (By Others / Owner / a named party)."""
    from app.services import work_packages as WP

    guided = _guided(version)
    out = []
    for package in WP.packages_in(guided, version):
        if WP.package_participates(package, version) or not WP.package_lines(package, version):
            continue
        out.append({"name": package.display_name, "responsible": WP.responsible_label(package, version),
                    "quoted": str(_quoted_price(package, version, e)) if e is not None else None})
    return out


def _line_sell_prices(version, e) -> dict:
    """{line id: customer selling price} for the lines in Brayman's price."""
    from app.services.pricing_engine import as_money, bucket_line_sell_prices
    from app.services.work_packages import participating_lines

    lines = list(participating_lines(version))
    if e.get("applied"):
        return {line.id: as_money(line.sell_price or 0) for line in lines}
    if e.get("pricing_breakdown") is not None:
        return bucket_line_sell_prices(e["pricing_breakdown"])
    selling, direct = e.get("selling_price"), e.get("direct_cost")
    if selling is None or not lines:
        return {}
    out, remaining = {}, as_money(selling)
    for line in lines[:-1]:
        share = (as_money(D(selling) * D(str(line.extended_cost or 0)) / D(direct)) if direct
                 else as_money(D(selling) / D(len(lines))))
        out[line.id] = share
        remaining -= share
    out[lines[-1].id] = as_money(remaining)
    return out


def _supplier(line) -> str:
    approval = getattr(line, "contractor_cost_approval", None)
    if approval is not None and approval.supplier_id:
        from app.models.supplier_catalogue import Supplier

        supplier = db.session.get(Supplier, approval.supplier_id)
        if supplier is not None:
            return supplier.legal_name
    item = getattr(line, "cost_item", None)
    if item is not None and (item.supplier or "").strip():
        return item.supplier.strip()
    return "—"


def _takeoff(version):
    from app.services.approved_cost_estimate import _takeoff_quantities

    project = version.estimate.project
    try:
        return _takeoff_quantities(project.organization_id, project.id)
    except Exception:  # noqa: BLE001 - a missing supplier request file never blocks the summary
        return {}


def _material_row(line, orders) -> dict:
    qty = D(str(line.quantity or 0))
    waste = D(str(line.waste_percent or 0))
    code = None
    item = getattr(line, "cost_item", None)
    if item is not None and getattr(item, "canonical_material", None) is not None:
        code = item.canonical_material.code
    order = orders.get(code) if code else None
    if order and order.get("quantity") is not None:
        order_qty, order_unit = D(str(order["quantity"])), order.get("unit") or line.unit
    else:
        order_qty, order_unit = qty * (1 + waste / 100), line.unit
    cost = q(line.extended_cost or 0)
    return {"item": line.description, "takeoff": f"{_qty(qty)} {line.unit}".strip(), "qty": _qty(order_qty),
            "unit": order_unit or "", "price": str(q(line.unit_cost or 0)), "supplier": _supplier(line),
            "cost": str(cost)}


def _labour_row(line, by_id, ref) -> dict:
    from app.services.estimate_labour_hours import LABOUR_CODE_PREFIX

    hours = D(str(line.quantity or 0))
    base = D(str(line.base_quantity)) if line.base_quantity is not None else hours
    activity = (line.description or "").replace("Labour — ", "", 1)
    qty = unit = rate = ""
    source_id = (line.code or "")[len(LABOUR_CODE_PREFIX):]
    if source_id.isdigit() and int(source_id) in by_id:
        item = by_id[int(source_id)]
        qty, unit = _qty(item.quantity), item.unit or ""
        if base:
            rate = f"{q(D(str(item.quantity or 0)) / base)}/h"
    else:
        rate = "entered"
    return {"ref": str(ref), "activity": activity, "qty": qty, "unit": unit, "rate": rate, "hours": str(q(hours)),
            "value": str(q(line.extended_cost or 0))}


def _subcontract_row(line, package_name) -> dict:
    from app.services.subcontract_quote import selected_quote_for_line

    quote = selected_quote_for_line(line)
    company = (quote.subcontractor.legal_name if quote is not None and quote.subcontractor is not None else "—")
    scope = (quote.included_scope if quote is not None and (quote.included_scope or "").strip() else line.description)
    return {"trade": package_name, "company": company, "scope": " ".join((scope or "").split())[:90],
            "cost": str(q(line.extended_cost or 0)), "ref": quote.quote_reference if quote is not None else ""}


def build_data(version, *, organization_id: Optional[str] = None, approval=None, crew_rates=None,
               today: Optional[datetime] = None) -> dict:
    """The summary's figures from the working estimate, as a JSON-ready dict (amounts as strings)."""
    from app.models import Organization
    from app.services.estimate_crew import crew_problem
    from app.services.estimate_crew import crew_rates as current_crew_rates
    from app.services.estimate_economics import economics
    from app.services.pricing_engine import BUCKET_LABOUR, BUCKET_MATERIAL, BUCKET_SUBCONTRACT, pricing_bucket

    project = version.estimate.project
    org_id = organization_id or project.organization_id
    org = db.session.get(Organization, org_id)
    e = economics(version, org_id)
    from app.services.package_scenario import budget_label, budgets, is_passthrough, package_key_of_section

    sells = _line_sell_prices(version, e)
    fixed = budgets(version)
    rules = e.get("pricing_rules") or {}
    by_id = {line.id: line for section in version.sections for line in section.line_items}
    orders = _takeoff(version)
    packages, ref = [], 0
    for name, _stage, lines in _packages(version):
        key = package_key_of_section(lines[0].section) if lines and lines[0].section is not None else None
        through = [l for l in lines if is_passthrough(l)]
        own = sum((sells.get(l.id, ZERO) for l in lines if not is_passthrough(l)), ZERO)
        if key in fixed:
            revenue = [{"label": f"{name} ({budget_label(version, key) or 'client budget'})", "amount": str(own)}]
        else:
            revenue = [{"label": name, "amount": str(own)}] if own or not through else []
        revenue += [{"label": f"{l.description} (billed at cost)", "amount": str(sells.get(l.id, ZERO))}
                    for l in through]
        pk = {"name": name, "revenue": revenue, "budget": str(fixed[key]) if key in fixed else None,
              "budget_label": budget_label(version, key) if key in fixed else None, "key": key,
              "materials": [], "labour": [], "equipment": [], "subcontracts": []}
        for line in lines:
            bucket = pricing_bucket(line)
            if bucket == BUCKET_LABOUR:
                ref += 1
                pk["labour"].append(_labour_row(line, by_id, ref))
            elif bucket == BUCKET_MATERIAL:
                pk["materials"].append(_material_row(line, orders))
            elif bucket == BUCKET_SUBCONTRACT:
                pk["subcontracts"].append(_subcontract_row(line, name))
            else:
                cost = q(line.extended_cost or 0)
                rule = rules.get(RULE_OF_BUCKET.get(bucket, ""), None) if rules else None
                pk["equipment"].append({"item": line.description, "cost": str(cost),
                                        "ip": str(q(cost * (1 + D(str(rule))))) if rule else str(cost)})
        packages.append(pk)
    rates = crew_rates if crew_rates is not None else current_crew_rates(version.estimate)
    problem = None if rates else crew_problem(version.estimate)
    method = e.get("pricing_method") or "TRUE_GROSS_MARGIN"
    margin = e.get("target_gross_margin")
    now = today or datetime.utcnow()
    excluded = _excluded(version, e)
    summary_notes = []
    if excluded:
        summary_notes.append("Excluded / by others (kept on the estimate, not in revenue or cost): " + "; ".join(
            f"{x['name']} — {x['responsible']}, quoted {m(x['quoted'])}" for x in excluded) + ".")
    if fixed:
        summary_notes.append("Client budget: the package's revenue is the client's budget; its costs are as estimated.")
    if not e.get("applied"):
        summary_notes.append("Working figures: pricing is applied when the estimate is approved.")
    labour_notes = ["Hours are person-hours and include any winter time increase. Rates are quantity per person-hour."]
    if rates:
        labour_notes.append("Crew cost = hours x the crew's Loaded Labour Rates, split by each member's share of the "
                            "hours.")
    data = {
        "schema": SCHEMA,
        "project": {
            "short": project.project_number or project.name,
            "name": project.name,
            "revision": f"{version.estimate.estimate_number} · {version.display_label}",
            "date": f"{now:%B} {now.day}, {now.year}",
            "subtitle": project.client.name if getattr(project, "client", None) is not None else "",
            "revenue_status": "" if e.get("applied") else "working figures",
            "company": org.legal_name if org is not None else "",
            "address": (org.primary_address or "") if org is not None else "",
        },
        "settings": {
            "pricing_method": method,
            "labour_rate": _s(e.get("labour_rate")) or "0",
            "material_margin": _s(margin) or "0",
            "hst": str(D(str(e.get("tax_percent") or 0)) / 100),
            "subcontract_markup": _s(e.get("subcontract_markup_rate")) or "0",
            "selling_price": _s(e.get("selling_price")),
            "direct_cost": _s(e.get("direct_cost")),
            # The pricing basis used (ruling 7): the labour SELLING rate above is never an employee's cost; the
            # crew's loaded COST rates are below. Both are frozen with the approval.
            "pricing_rules": {k: _s(v) for k, v in rules.items()} if rules else None,
        },
        "crew": [{"name": r["name"], "loaded_rate": str(r["loaded_rate"]), "share": str(r["share"])}
                 for r in (rates or [])],
        "crew_problem": problem,
        "packages": packages,
        "excluded": excluded,
        "summary_notes": summary_notes,
        "materials_notes": ["Cost is Brayman's cost for the estimate quantity (waste included); order quantities are "
                            "the supplier request's when there is one."],
        "labour_notes": labour_notes,
        "subcontract_notes": ["Subcontract cost is the selected quote used on the estimate."],
        "approval": {},
        "estimate_version_id": version.id,
    }
    if approval is not None:
        data["approval"] = approval_block(approval)
    return data


def approval_block(approval) -> dict:
    from app.services.local_time import format_local

    return {"name": approval.approved_by_name, "title": "Contractor",
            "approved_at": format_local(approval.approved_at, "%b %d, %Y %I:%M %p")}


def frozen_data(approval) -> Optional[dict]:
    data = (approval.summary or {}).get("internal_financial_summary") if approval is not None else None
    if not data:
        return None
    return dict(data, approval=approval_block(approval))


def data_for(version, *, organization_id: Optional[str] = None) -> dict:
    """The approved figures when the version is approved (frozen at approval); otherwise the working figures."""
    from app.services.estimate_approval import approval_for

    approval = approval_for(version)
    frozen = frozen_data(approval)
    if frozen is not None:
        return frozen
    return build_data(version, organization_id=organization_id, approval=approval)


# ============================================================================================ the calculation
def compute(data: dict):
    P = data
    S = dict(P["settings"])
    S["labour_rate"] = D(S["labour_rate"]); S["material_margin"] = D(S["material_margin"]); S["hst"] = D(S.get("hst", "0.13"))
    S["sub_markup"] = D(S.get("subcontract_markup") or "0")
    crew = P.get("crew") or []
    share_total = sum((D(c["share"]) for c in crew), ZERO)
    blend = (sum((D(c["loaded_rate"]) * D(c["share"]) for c in crew), ZERO) / share_total) if crew else None
    pk = []
    for k in P["packages"]:
        mats = [dict(r, qty_d=D(str(r["qty"]).replace(",", "") or "0"), price=D(r["price"]), cost=D(r["cost"]))
                for r in k.get("materials", [])]
        for r in mats:
            r["mk"] = q(r["cost"] / (1 - S["material_margin"]))
        labs = [dict(r, hours=D(r["hours"])) for r in k.get("labour", [])]
        for r in labs:
            r["v"] = D(r["value"]) if r.get("value") is not None else q(r["hours"] * S["labour_rate"])
            r["lc"] = q(r["hours"] * blend) if blend is not None else None
        eqs = [dict(r, cost=D(r["cost"])) for r in k.get("equipment", [])]
        for r in eqs:
            r["ip"] = D(r.get("ip") or r["cost"])
        subs = [dict(r, cost=D(r["cost"])) for r in k.get("subcontracts", [])]
        for r in subs:
            r["ip"] = q(r["cost"] * (1 + S["sub_markup"]))
        rev = [dict(r, amount=D(r["amount"])) for r in k.get("revenue", [])]
        T = dict(rev=sum((r["amount"] for r in rev), ZERO), mat=sum((r["cost"] for r in mats), ZERO),
                 mk=sum((r["mk"] for r in mats), ZERO), h=sum((r["hours"] for r in labs), ZERO),
                 v=sum((r["v"] for r in labs), ZERO),
                 lc=sum((r["lc"] for r in labs), ZERO) if blend is not None else None,
                 eq=sum((r["cost"] for r in eqs), ZERO), eqip=sum((r["ip"] for r in eqs), ZERO),
                 sub=sum((r["cost"] for r in subs), ZERO),
                 subip=sum((r["ip"] for r in subs), ZERO))
        known = T["mat"] + T["eq"] + T["sub"]
        T["cost"] = known + T["lc"] if T["lc"] is not None else None
        T["profit"] = T["rev"] - T["cost"] if T["cost"] is not None else None
        T["ip"] = T["mk"] + T["v"] + T["eqip"] + T["subip"]
        pk.append(dict(k, mats=mats, labs=labs, eqs=eqs, subs=subs, rev=rev, T=T))
    keys = ("rev", "mat", "mk", "h", "v", "lc", "eq", "eqip", "sub", "subip", "cost", "profit", "ip")
    tot = {}
    for key in keys:
        values = [p["T"][key] for p in pk]
        tot[key] = None if any(v is None for v in values) else sum(values, ZERO)
    if blend is None:
        tot["lc"] = tot["cost"] = tot["profit"] = None
    split = []
    acc = ZERO
    for i, cm in enumerate(crew):
        hrs = tot["h"] * D(cm["share"]) / share_total
        cost = q(hrs * D(cm["loaded_rate"])) if i < len(crew) - 1 else tot["lc"] - acc
        acc += cost
        split.append(dict(cm, hours=hrs, cost=cost))
    return P, S, pk, tot, split, blend


# ============================================================================================ the PDF
class _Doc:
    def __init__(self, P, out):
        self.P = P; self.c = canvas.Canvas(out, pagesize=landscape(letter), invariant=1); self.W, self.H = landscape(letter)
        self.L, self.R = 30, self.W - 30
        self.c.setTitle(f"{P['project']['short']} - {TITLE}")
        self.c.setAuthor(P["project"].get("company") or "")
        self.c.setSubject("Internal — not for customer")

    def t(self, x, y, s, size=8.5, bold=False, color=INK, align="l"):
        c = self.c; c.setFillColor(color); c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        {"l": c.drawString, "r": c.drawRightString}[align](x, y, s)

    def header(self, section):
        P, c, L, R, H = self.P["project"], self.c, self.L, self.R, self.H
        c.drawImage(ImageReader(BRAYMAN_LOGO), L, H - 62, 84, 38, mask="auto", preserveAspectRatio=True, anchor="w")
        main = section.replace(" (continued)", "")
        big = TITLE if main == "Project Summary" else f"{main.upper()} – PROJECT SUMMARY"
        cont = " (continued)" if "(continued)" in section else ""
        self.t(L + 94, H - 32, big + cont, 15, True, NAVY)
        self.t(L + 94, H - 46, (P["name"] if main == "Project Summary" else f"{TITLE} · {P['short']}"), 9.5, True)
        self.t(L + 94, H - 58, f"{P.get('company') or ''} · Internal — not for customer".lstrip(" ·"), 7.5, True, RED)
        self.t(R, H - 32, P["revision"], 9, True, align="r")
        self.t(R, H - 44, f"{P['date']} · amounts before HST", 7.5, color=GREY, align="r")
        self.t(R, H - 55, P.get("subtitle", ""), 7.5, color=GREY, align="r")

    def footer(self, n, total, notes):
        L, R, W = self.L, self.R, self.W
        P = self.P["project"]
        for i, ln in enumerate(notes[:3]):
            self.t(L, 44 - i * 9, ln[:190], 6.8, color=MUTED)
        company = " · ".join(x for x in (P.get("company"), P.get("address")) if x)
        self.t(L, 12, company, 6.8, color=MUTED)
        self.t(W / 2, 12, f"Page {n} of {total}", 7, color=MUTED)
        self.t(R - 74, 26, "Prepared with", 6.5, color=MUTED, align="r")
        self.c.drawImage(ImageReader(CALIBRAYT_LOGO), R - 70, 4, 70, 26, mask="auto", preserveAspectRatio=True, anchor="e")


def _fit(text, limit):
    text = str(text or "")
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _build(P, S, pk, tot, split, blend, out, total_pages=None) -> int:
    d = _Doc(P, out); c = d.c; L, R, W, H = d.L, d.R, d.W, d.H; t = d.t
    page_no = [0]
    BOTTOM = 70
    cur_notes = [[]]
    crew_text = P.get("crew_problem") or "Crew not assigned — real labour cost not available"
    no_crew = blend is None
    new_method = S.get("pricing_method") == "LABOUR_AT_RATE_MATERIAL_MARGIN"
    # Ruling 1: a viewer who may see project economics but not employee cost gets no crew names or loaded rates.
    detail = P.get("employee_detail", True) is not False

    def start(section, notes=()):
        if page_no[0]:
            d.footer(page_no[0], total_pages or 0, cur_notes[0]); c.showPage()
        page_no[0] += 1; cur_notes[0] = list(notes); d.header(section)
        return H - 86

    def head(y, cols):
        c.setFillColor(NAVY); c.rect(L, y - 5, R - L, 16, stroke=0, fill=1)
        for x, h_, a in cols:
            t(x + (6 if a == "l" else 0), y, h_, 7.8, True, colors.white, a)
        return y - 16

    def row(y, cols, vals, bold=False, size=8.2, color=INK, fill=None, line=True):
        if fill is not None:
            c.setFillColor(fill); c.rect(L, y - 5, R - L, 16, stroke=0, fill=1)
        for (x, _, a), v in zip(cols, vals):
            t(x + (6 if a == "l" else 0), y, v, size, bold, color, a)
        if line:
            c.setStrokeColor(RULE); c.setLineWidth(0.4); c.line(L, y - 5, R, y - 5)

    def table(section, notes, cols, groups, total_vals, step=14.2):
        y = start(section, notes); y = head(y, cols)
        for title, rows, sub in groups:
            if y < BOTTOM + 40:
                y = start(section + " (continued)", notes); y = head(y, cols)
            row(y, cols, [title.upper()] + [""] * (len(cols) - 1) if cols[0][1] != "#" else ["", title.upper()] + [""] * (len(cols) - 2),
                True, 7.8, NAVY, BAND, False); y -= 15
            for v in rows:
                if y < BOTTOM + 20:
                    y = start(section + " (continued)", notes); y = head(y, cols)
                row(y, cols, v, size=8); y -= step
            if sub:
                row(y, cols, sub, True, 8.2); y -= 17
        if total_vals:
            row(y, cols, total_vals, True, 9, NAVY, TOTAL, False); y -= 26
        return y

    margin_pct = f"{S['material_margin'] * 100:.0f}%"
    # ===== Summary =====
    y = start("Project Summary", P.get("summary_notes", []))
    HST = q(tot["rev"] * S["hst"]); status = P["project"].get("revenue_status", "")
    tw = (R - L - 20) / 3
    tiles = [(f"Revenue{' (' + status + ')' if status else ''}", m(tot["rev"]), f"{m(tot['rev'] + HST)} with HST"),
             ("Total cost", m(tot["cost"]) if not no_crew else "Not available",
              "materials, labour, subcontractors, equipment" if not no_crew else crew_text),
             ("Profit", m(tot["profit"]) if not no_crew else "Not available",
              f"{pct(tot['profit'], tot['rev'])} of revenue" if not no_crew else "needs the crew's loaded rates")]
    for i, (lab, val, sub) in enumerate(tiles):
        x = L + i * (tw + 10)
        c.setFillColor(TOTAL if i == 2 else CALC); c.roundRect(x, y + 6 - 44, tw, 46, 3, stroke=0, fill=1)
        t(x + 10, y - 6, lab, 8.5, True, GREY); t(x + 10, y - 24, val, 17, True, RED if (no_crew and i) else NAVY)
        t(x + 10, y - 34, _fit(sub, 62), 7.5, color=RED if (no_crew and i) else GREY)
    y -= 66
    t(L, y, "By work package", 10.5, True, NAVY)
    if no_crew:
        t(R, y, crew_text + ": labour is shown at the charge rate only", 8, True, RED, "r")
    y -= 18
    cols = [(L, "Work package", "l"), (L + 260, "Revenue", "r"), (L + 330, "Materials", "r"),
            (L + 395, "Labour" if not no_crew else "Labour at rate", "r"),
            (L + 470, "Subcontractors", "r"), (L + 535, "Equipment", "r"), (L + 605, "Total cost", "r"), (L + 675, "Profit", "r"),
            (R - 4, "Margin", "r")]
    y = head(y, cols)
    for p in pk:
        T = p["T"]
        if y < BOTTOM + 20:
            y = start("Project Summary (continued)", P.get("summary_notes", [])); y = head(y, cols)
        row(y, cols, [_fit(p["name"], 48), m(T["rev"]), m(T["mat"]), m(T["lc"] if not no_crew else T["v"]),
                      m(T["sub"]) if T["sub"] else "—", m(T["eq"]) if T["eq"] else "—",
                      m(T["cost"]), m(T["profit"]), pct(T["profit"], T["rev"])], size=8.3); y -= 16
    row(y, cols, ["Total", m(tot["rev"]), m(tot["mat"]), m(tot["lc"] if not no_crew else tot["v"]),
                  m(tot["sub"]) if tot["sub"] else "—", m(tot["eq"]),
                  m(tot["cost"]), m(tot["profit"]), pct(tot["profit"], tot["rev"])], True, 8.8, NAVY, TOTAL, False)
    y -= 16
    excluded = P.get("excluded") or []
    if excluded:
        row(y, cols, ["EXCLUDED / BY OTHERS — kept on the estimate, not in revenue or cost"] + [""] * (len(cols) - 1),
            True, 7.8, NAVY, BAND, False); y -= 15
        for x in excluded:
            row(y, cols, [_fit(x["name"], 48), "", "", "", "", "", "", "",  ""], size=8.2, color=GREY)
            t(L + 330, y, _fit(f"{x['responsible']} · we had quoted {m(x.get('quoted'))}", 80), 8.2, False, GREY)
            y -= 16
    y -= 14
    nrev0 = sum(len(p["rev"]) for p in pk)
    n_left = (nrev0 if nrev0 + len(split) <= 12 else len(pk)) + max(len(split), 1) + 7 + (1 if tot["sub"] else 0)
    if y - max(15 * n_left + 30, 262) < 62:
        y = start("Project Summary (continued)", P.get("summary_notes", []))
    bw = (R - L - 30) / 2; y0 = y
    t(L, y0, "Profit and loss", 10.5, True, NAVY); yy = y0 - 18
    lines = [("REVENUE", "", "head")]
    nrev = sum(len(p["rev"]) for p in pk)
    for p in pk:
        if nrev + len(split) <= 12:
            for r in p["rev"]:
                lines.append((_fit(r["label"], 60), m(r["amount"]), ""))
        else:
            lines.append((_fit(p["name"], 60), m(p["T"]["rev"]), ""))
    lines += [("Total revenue", m(tot["rev"]), "bold"), ("COSTS", "", "head"), ("Materials (all)", m(tot["mat"]), "")]
    if no_crew:
        lines.append((_fit("Labour: " + crew_text, 70), "—", "warn"))
    if detail:
        for cm in split:
            lines.append((f"Labour: {cm['name']}, {cm['hours']:.2f} h at ${D(cm['loaded_rate']):.2f} loaded", m(cm["cost"]), ""))
    elif split:
        lines.append((f"Labour (crew), {tot['h']:.2f} h", m(tot["lc"]), ""))
    if tot["sub"]:
        lines.append(("Subcontractors", m(tot["sub"]), ""))
    lines += [("Equipment", m(tot["eq"]), ""), ("Total cost", m(tot["cost"]), "bold"),
              ("Profit", f"{m(tot['profit'])}   ({pct(tot['profit'], tot['rev'])})" if not no_crew else "Not available",
               "total")]
    for lab, val, kind in lines:
        if kind == "head":
            t(L, yy, lab, 8, True, GREY); yy -= 13; continue
        if kind == "total":
            c.setFillColor(TOTAL); c.rect(L - 4, yy - 5, bw + 4, 16, stroke=0, fill=1)
        b = kind in ("bold", "total")
        color = RED if kind == "warn" else INK
        t(L + (0 if b else 8), yy, lab, 8.6 if b else 8.2, b, color); t(L + bw, yy, val, 8.6 if b else 8.2, b, color, align="r")
        c.setStrokeColor(RULE); c.setLineWidth(0.4); c.line(L, yy - 5, L + bw, yy - 5); yy -= 15
    x2 = L + bw + 30; yy = y0
    t(x2, yy, "How we price it internally", 10.5, True, NAVY); yy -= 18
    if new_method:
        ip = [(f"Materials + {margin_pct} margin", m(tot["mk"]), False),
              (f"Labour, {tot['h']:.2f} h at ${S['labour_rate']:.2f} (no margin)", m(tot["v"]), False)]
        if tot["sub"]:
            ip.append((f"Subcontractors + {S['sub_markup'] * 100:.0f}%", m(tot["subip"]), False))
        ip += [("Equipment at cost" if tot["eqip"] == tot["eq"] else "Equipment, delivery & other (company rules)",
                m(tot["eqip"]), False), ("Internal price", m(tot["ip"]), True)]
        internal = tot["ip"]
    else:
        direct = D(S.get("direct_cost") or (tot["mat"] + tot["v"] + tot["eq"] + tot["sub"]))
        selling = D(S.get("selling_price") or tot["rev"])
        ip = [(f"Direct cost (labour at ${S['labour_rate']:.2f}/h)", m(direct), False),
              (f"+ {margin_pct} true gross margin on all costs (this estimate's pricing method)", m(selling - direct), False),
              ("Internal price", m(selling), True)]
        internal = selling
    ip += [("Revenue", m(tot["rev"]), True), ("Revenue above / (below) internal price", m(tot["rev"] - internal), False)]
    for lab, val, b in ip:
        t(x2, yy, _fit(lab, 78), 8.2, b); t(x2 + bw, yy, val, 8.2, b, align="r")
        c.setStrokeColor(RULE); c.line(x2, yy - 5, x2 + bw, yy - 5); yy -= 15
    yy -= 4
    if split:
        crew_names = " and ".join(cm["name"] for cm in split) if detail else f"a crew of {len(split)}"
        t(x2, yy, _fit(f"Crew hours {tot['h']:.2f} · about {q(tot['h'] / (8 * len(split))):.1f} working days for "
                       f"{crew_names} together", 105), 7.5, color=GREY)
    else:
        t(x2, yy, _fit(f"Crew hours {tot['h']:.2f} · {crew_text}", 105), 7.5, True, RED)

    A = P.get("approval") or {}
    yy -= 22; bh = 104
    c.setStrokeColor(NAVY); c.setLineWidth(0.9); c.roundRect(x2 - 6, yy - bh + 12, bw + 12, bh, 3, stroke=1, fill=0)
    t(x2, yy, "Contractor approval", 10.5, True, NAVY)
    t(x2 + bw, yy, _fit(f"{m(tot['rev'])} revenue · "
                        f"{m(tot['profit']) + ' profit' if not no_crew else 'profit not available'}", 50), 7.5, True, GREY, "r")
    t(x2, yy - 14, "I have reviewed this Internal Project Financial Summary — revenue, materials, labour, subcontractors,", 7.5)
    t(x2, yy - 24, "equipment and profit — and approve it as the estimate for this project.", 7.5)
    t(x2, yy - 42, f"Name: {A.get('name', '')}", 8.5, True); t(x2 + bw * 0.55, yy - 42, A.get("title", "Contractor"), 8.5, color=GREY)
    c.setStrokeColor(INK); c.setLineWidth(0.6)
    c.line(x2 + 52, yy - 66, x2 + bw * 0.62, yy - 66); c.line(x2 + bw * 0.62 + 40, yy - 66, x2 + bw, yy - 66)
    t(x2, yy - 64, "Signature", 8); t(x2 + bw * 0.62 + 12, yy - 64, "Date", 8)
    if A.get("approved_at"):
        t(x2 + 56, yy - 62, "Approved in CalibraytAI", 8, True, NAVY)
        t(x2 + bw * 0.62 + 42, yy - 62, _fit(A["approved_at"], 30), 7.5, True, NAVY)
    t(x2, yy - 82, "Approval locks this version. Any later change to revenue, quantities, labour or pricing needs a new revision.", 6.8, color=MUTED)

    # ===== Materials & equipment =====
    cols = [(L, "Item", "l"), (L + 290, "Takeoff", "r"), (L + 340, "Order", "r"), (L + 345, "Unit", "l"), (L + 465, "Unit price", "r"),
            (L + 470, "Supplier", "l"), (L + 610, "Cost", "r"), (L + 690, f"Cost + {margin_pct}", "r")]
    groups = [(p["name"], [[_fit(r["item"], 52), _fit(r.get("takeoff", ""), 12), r["qty"], _fit(r["unit"], 8), m(r["price"]),
                            _fit(r["supplier"], 24), m(r["cost"]), m(r["mk"])] for r in p["mats"]],
               [f"Subtotal — {_fit(p['name'], 50)}", "", "", "", "", "", m(p["T"]["mat"]), m(p["T"]["mk"])])
              for p in pk if p["mats"]]
    y = table("Materials", P.get("materials_notes", []), cols, groups,
              ["TOTAL MATERIALS", "", "", "", "", "", m(tot["mat"]), m(tot["mk"])])
    eqs = [(p["name"], r) for p in pk for r in p["eqs"]]
    if eqs:
        if y < BOTTOM + 30 + 14 * min(len(eqs), 25):
            y = start("Materials (continued)", P.get("materials_notes", []))
        t(L, y, "Equipment & rentals (at cost)", 9.5, True, NAVY); y -= 16
        for pname, r in eqs:
            if y < BOTTOM + 20:
                y = start("Materials (continued)", P.get("materials_notes", []))
            t(L + 6, y, _fit(r["item"], 60), 8.2); t(L + 340, y, _fit(pname, 30), 8, color=GREY, align="r")
            t(L + 610, y, m(r["cost"]), 8.2, align="r")
            c.setStrokeColor(RULE); c.line(L, y - 5, L + 690, y - 5); y -= 14
        t(L + 6, y, "Total equipment", 8.5, True); t(L + 610, y, m(tot["eq"]), 8.5, True, align="r")

    # ===== Labour =====
    cols = [(L, "#", "l"), (L + 22, "Activity", "l"), (L + 410, "Qty", "r"), (L + 418, "Unit", "l"), (L + 500, "Rate", "r"),
            (L + 565, "Hours", "r"), (L + 640, f"At ${S['labour_rate']:.0f}/h", "r"), (R - 4, "Crew cost", "r")]
    groups = [(p["name"], [[r.get("ref", ""), _fit(r["activity"], 70), r.get("qty", ""), _fit(r.get("unit", ""), 10),
                            r.get("rate", ""), f"{r['hours']:.2f}", m(r["v"]), m(r["lc"])] for r in p["labs"]],
               ["", f"Subtotal — {_fit(p['name'], 50)}", "", "", "", f"{p['T']['h']:.2f}", m(p["T"]["v"]), m(p["T"]["lc"])])
              for p in pk if p["labs"]]
    y = table("Labour", P.get("labour_notes", []), cols, groups,
              ["", "TOTAL LABOUR", "", "", "", f"{tot['h']:.2f}", m(tot["v"]), m(tot["lc"])])
    if y < BOTTOM + 30 + 14 * (len(split) + 3):
        y = start("Labour (continued)", P.get("labour_notes", []))
    t(L, y, "Crew and loaded cost", 9.5, True, NAVY); y -= 16; bw3 = 340
    if no_crew:
        rows3 = [(crew_text, "—", True), (f"Labour value at ${S['labour_rate']:.2f}/h ({tot['h']:.2f} h)", m(tot["v"]), False)]
    else:
        rows3 = ([(f"{cm['name']} — {cm['hours']:.2f} h at ${D(cm['loaded_rate']):.2f}/h loaded", m(cm["cost"]), False)
                  for cm in split if detail] +
                 [("Labour cost", m(tot["lc"]), True), (f"Labour value at ${S['labour_rate']:.2f}/h ({tot['h']:.2f} h)", m(tot["v"]), False),
                  ("Labour margin over loaded cost", m(tot["v"] - tot["lc"]), True)])
    for lab, val, b in rows3:
        t(L + 6, y, _fit(lab, 70), 8.2, b, RED if (no_crew and b) else INK); t(L + bw3, y, val, 8.2, b, align="r")
        c.setStrokeColor(RULE); c.line(L, y - 5, L + bw3, y - 5); y -= 14

    # ===== Subcontractors (only when present) =====
    if any(p["subs"] for p in pk):
        cols = [(L, "Trade", "l"), (L + 130, "Subcontractor", "l"), (L + 290, "Scope", "l"), (L + 560, "Quote / cost", "r"),
                (L + 640, f"+ {S['sub_markup'] * 100:.0f}% markup", "r"), (R - 4, "Quote ref.", "r")]
        groups = [(p["name"], [[_fit(r["trade"], 24), _fit(r["company"], 28), _fit(r["scope"], 48), m(r["cost"]), m(r["ip"]),
                                _fit(r.get("ref", ""), 16)] for r in p["subs"]],
                   [f"Subtotal — {_fit(p['name'], 50)}", "", "", m(p["T"]["sub"]), m(p["T"]["subip"]), ""]) for p in pk if p["subs"]]
        table("Subcontractors", P.get("subcontract_notes", []), cols, groups,
              ["TOTAL SUBCONTRACTORS", "", "", m(tot["sub"]), m(tot["subip"]), ""])
    d.footer(page_no[0], total_pages or 0, cur_notes[0])
    c.showPage(); c.save()
    return page_no[0]


def render_pdf(data: dict) -> bytes:
    """The PDF: built twice, the first pass counts the pages for "Page X of N"."""
    P, S, pk, tot, split, blend = compute(data)
    if not pk:
        pk = [dict(name="No work in Brayman's price yet", mats=[], labs=[], eqs=[], subs=[], rev=[],
                   T={k: ZERO for k in ("rev", "mat", "mk", "h", "v", "eq", "eqip", "sub", "subip", "ip")}
                   | {"lc": ZERO if blend is not None else None, "cost": ZERO if blend is not None else None,
                      "profit": ZERO if blend is not None else None})]
    counter = BytesIO()
    n = _build(P, S, pk, tot, split, blend, counter)
    out = BytesIO()
    _build(P, S, pk, tot, split, blend, out, total_pages=n)
    return out.getvalue()


def totals(data: dict) -> dict:
    """The headline figures (for the screen and tests)."""
    _P, _S, pk, tot, split, blend = compute(data)
    return {"revenue": tot["rev"], "cost": tot["cost"], "profit": tot["profit"], "labour_cost": tot["lc"],
            "labour_value": tot["v"], "hours": tot["h"], "materials": tot["mat"], "materials_with_margin": tot["mk"],
            "subcontracts": tot["sub"], "equipment": tot["eq"], "internal_price": tot["ip"],
            "packages": [(p["name"], p["T"]["rev"]) for p in pk], "crew_split": split,
            "crew_assigned": blend is not None}


def filename(data: dict) -> str:
    P = data["project"]
    stem = f"{P['short']}_Internal_Project_Financial_Summary_{P['revision']}"
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in stem).strip("_")[:150] + ".pdf"


def freeze_for_approval(version) -> dict:
    """The summary's figures and the crew's loaded rates as they are at approval (stored in the approval record)."""
    return build_data(version)


def file_approved_summary(version, approval, *, user=None):
    """File the approved summary in the project's Documents (Internal financial summary; ECONOMICS, or EMPLOYEE_COST
    when it shows the crew's loaded rates). Idempotent."""
    from app.models.documents import CONTEXT_PROJECT, Document, DocumentLink
    from app.services.documents import ingest
    from app.services.documents.contexts import resolve_context

    data = frozen_data(approval)
    if data is None:
        return None
    existing = (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
                .filter(Document.organization_id == approval.organization_id,
                        Document.document_type == DOCUMENT_TYPE,
                        DocumentLink.record_kind == "ESTIMATE_VERSION",
                        DocumentLink.record_id == version.id).first())
    if existing is not None:
        return existing
    pdf = render_pdf(data)
    blob = ingest.prepare_upload(filename(data), pdf)
    project = version.estimate.project
    context = resolve_context(approval.organization_id, CONTEXT_PROJECT, project.id)
    actor = ingest.Actor.of(user) if user is not None else ingest.SYSTEM
    document = ingest.file_document(approval.organization_id, actor, blob=blob, context=context,
                                    title=f"{TITLE} — {data['project']['revision']} (approved)",
                                    type_code=DOCUMENT_TYPE, record_kind="ESTIMATE_VERSION", record_id=version.id,
                                    description="Internal contractor document: costs, margins and crew loaded rates. "
                                                "Not for customers, suppliers or field crew.",
                                    sensitivity=document_sensitivity(data), sensitivity_reason=sensitivity_reason(data))
    return document


def carries_wages(data: dict) -> bool:
    """Whether this summary shows the crew's names and Loaded Labour Rates (wage figures). One rule for the REV record
    and for filing (review M1, 3 Nov 2026): a crew is assigned and it is not the crew-total variant."""
    return bool(data.get("crew")) and data.get("employee_detail", True) is not False


def document_sensitivity(data: dict) -> str:
    """Who may read a filed copy (review B2/S1, 3 Nov 2026): EMPLOYEE_COST when it shows the crew's loaded rates,
    otherwise ECONOMICS. Set when the document is created, before it is indexed or committed."""
    from app.models.documents import SENSITIVITY_ECONOMICS, SENSITIVITY_EMPLOYEE_COST

    return SENSITIVITY_EMPLOYEE_COST if carries_wages(data) else SENSITIVITY_ECONOMICS


def sensitivity_reason(data: dict) -> str:
    if carries_wages(data):
        return ("Contains project economics and the crew's loaded labour rates (wage figures): project economics and "
                "employee cost access only.")
    return "Contains project economics (cost, price, margin): project economics access only."


def quoted_revisions(estimate) -> list:
    """Every price sent to the client, as the summary's REVs in the order sent (Joel, 2-3 Nov 2026). One REV series
    per estimate (app/models/internal_summary.py): the client's REVs and the REVs frozen for internal approval share
    it. Each is an approved, locked version (Gate 1) and never changes."""
    from app.models import Proposal
    from app.models.internal_summary import ORIGIN_SENT_TO_CLIENT, InternalSummaryRevision

    rows = (InternalSummaryRevision.query.filter_by(estimate_id=estimate.id, origin=ORIGIN_SENT_TO_CLIENT)
            .order_by(InternalSummaryRevision.revision_number.asc()).all())
    by_id = {v.id: v for v in estimate.versions}
    return [{"number": r.revision_number, "label": r.label, "version": by_id.get(r.estimate_version_id),
             "sent_at": r.created_at, "proposal": db.session.get(Proposal, r.proposal_id) if r.proposal_id else None,
             "revision": r} for r in rows]


def file_sent_summary(version, proposal, *, user=None, number=None):
    """When a price goes to the client: record it as the summary's next REV (its figures frozen at Ben's approval of
    that version, Gate 1, never recalculated) and file that REV's PDF in Documents. Idempotent per proposal.

    ``number``: when the customer estimate sent is the one Ben authorized for issue (customer estimate REVn), the
    summary's sent-to-client record is that same REVn (one revision, two documents); otherwise the next number."""
    from app.models.documents import CONTEXT_PROJECT, Document, DocumentLink
    from app.models.internal_summary import DOCUMENT_TYPE_FINANCIAL_SUMMARY, ORIGIN_SENT_TO_CLIENT, InternalSummaryRevision
    from app.services.documents import ingest
    from app.services.documents.contexts import resolve_context
    from app.services.estimate_approval import approval_for
    from app.services.internal_approval import record_sent_revision

    approval = approval_for(version)
    data = frozen_data(approval)
    if data is None:
        return None
    existing = (Document.query.join(DocumentLink, DocumentLink.document_id == Document.id)
                .filter(Document.organization_id == approval.organization_id,
                        Document.document_type == DOCUMENT_TYPE, DocumentLink.record_kind == "PROPOSAL",
                        DocumentLink.record_id == proposal.id).first())
    if existing is not None:
        return existing
    revision = InternalSummaryRevision.query.filter_by(estimate_id=version.estimate_id, proposal_id=proposal.id,
                                                       origin=ORIGIN_SENT_TO_CLIENT,
                                                       document_type=DOCUMENT_TYPE_FINANCIAL_SUMMARY).first()
    if revision is None:
        revision = record_sent_revision(version, proposal, data, user=user, number=number)
    labelled = revision.data
    blob = ingest.prepare_upload(filename(labelled), render_pdf(labelled))
    context = resolve_context(approval.organization_id, CONTEXT_PROJECT, version.estimate.project.id)
    actor = ingest.Actor.of(user) if user is not None else ingest.SYSTEM
    document = ingest.file_document(approval.organization_id, actor, blob=blob, context=context,
                                    title=f"{TITLE} — {revision.label} sent to client ({version.display_label})",
                                    type_code=DOCUMENT_TYPE, record_kind="PROPOSAL", record_id=proposal.id,
                                    description=f"What was quoted to the client as {revision.label}. Internal "
                                                "contractor document; not for customers, suppliers or field crew.",
                                    sensitivity=document_sensitivity(labelled),
                                    sensitivity_reason=sensitivity_reason(labelled))
    return document


def dumps(data: dict) -> str:
    return json.dumps(data, sort_keys=True)

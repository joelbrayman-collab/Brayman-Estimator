"""Brayman Construction supplier estimate request.

The page follows the approved cost-request sheet:
logo, company block, gold rule, navy table header, cream fields,
and the navy footer. The project and the rows change. The page does not.
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Mapping, Optional, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas

PRIMARY = colors.HexColor("#1f3a5f")
ACCENT = colors.HexColor("#c79a2b")
RULE = colors.HexColor("#d9d3c7")
HEAD = colors.HexColor("#f4efe6")
FIELD = colors.Color(1, 0.98, 0.92)
COMPANY = "Brayman Construction"
LEGAL = "Brayman Construction Inc."
OFFICE = "411 St. John Street, Merrickville, Ontario K0G 1N0"
TITLE = "SUPPLIER ESTIMATE REQUEST"

_NOTE = "BRAYMAN TO CONFIRM QTY"


def render_supplier_estimate_request(
    *,
    project_name: str,
    project_address: str,
    supplier_name: str,
    issued_on: str,
    intro: Sequence[str],
    rows: Sequence[Mapping],
    sku_label: str = "BMR Code / SKU",
    contact_label: str = "BMR contact",
) -> bytes:
    """Draw one supplier estimate request. Prices and SKUs stay empty."""
    from reportlab.platypus import Paragraph

    buffer = BytesIO()
    page_w, page_h = landscape(letter)
    form = Canvas(buffer, pagesize=landscape(letter))
    # PDF booleans are lower case. A Python True is written as an invalid token.
    form.acroForm.extras["NeedAppearances"] = "true"
    form.setTitle(f"{project_name} — {TITLE}")
    form.setAuthor(COMPANY)
    left = 0.4 * inch
    right = 0.4 * inch
    content_w = page_w - left - right
    columns, widths = _columns(left, content_w)
    item_style = ParagraphStyle("item", fontName="Times-Roman", fontSize=8, leading=10, textColor=colors.black)
    intro_style = ParagraphStyle("intro", fontName="Times-Roman", fontSize=8, leading=10, textColor=PRIMARY)
    page_no = 1

    def paint_columns(top: float) -> float:
        form.setFillColor(PRIMARY)
        form.rect(left, top - 16, content_w, 16, fill=1, stroke=0)
        form.setFillColor(colors.white)
        form.setFont("Times-Bold", 8)
        labels = (
            ("no", "No."),
            ("item", "Item"),
            ("qty", "Qty"),
            ("unit", "Unit Price"),
            ("line", "Line Price"),
            ("sku", sku_label),
            ("note", "Note"),
        )
        for key, label in labels:
            form.drawString(columns[key] + 2, top - 12, label)
        return top - 16

    def start_page(first: bool) -> float:
        _chrome(form, page_w, page_h, page_no, project_name, project_address, supplier_name, issued_on)
        top = page_h - 0.98 * inch
        if first:
            for line in intro:
                block = Paragraph(_xml(line), intro_style)
                _, height = block.wrap(content_w, 60)
                block.drawOn(form, left, top - height)
                top -= height + 2
            top -= 4
        return paint_columns(top)

    cursor = start_page(True)
    bottom = 0.55 * inch
    for row in rows:
        number = str(row["number"])
        block = Paragraph(_xml(str(row["item"])), item_style)
        _, text_h = block.wrap(widths["item"] - 6, 120)
        row_h = max(34, text_h + 8)
        if cursor - row_h < bottom:
            form.showPage()
            page_no += 1
            cursor = start_page(False)
        row_bottom = cursor - row_h
        if int(number) % 2 == 0:
            form.setFillColor(HEAD)
            form.rect(left, row_bottom, content_w, row_h, fill=1, stroke=0)
        form.setStrokeColor(RULE)
        form.setLineWidth(0.3)
        form.rect(left, row_bottom, content_w, row_h, fill=0, stroke=1)
        form.setFillColor(colors.black)
        form.setFont("Times-Roman", 8)
        form.drawString(columns["no"] + 2, row_bottom + 6, number)
        block.drawOn(form, columns["item"] + 2, row_bottom + 4)
        form.drawString(columns["qty"] + 2, row_bottom + 6, str(row.get("qty") or ""))
        field_y = row_bottom + 4
        for key, prefix in (
            ("unit", "unit_price"),
            ("line", "line_price"),
            ("sku", "sku"),
            ("note", "note"),
        ):
            form.acroForm.textfield(
                name=f"{prefix}_{int(number):02d}",
                tooltip=f"{prefix.replace('_', ' ')} for item {number}",
                x=columns[key] + 1,
                y=field_y,
                width=widths[key] - 2,
                height=22,
                borderWidth=0.6,
                borderColor=PRIMARY,
                fillColor=FIELD,
                textColor=colors.black,
                forceBorder=True,
                fontName="Times-Roman",
                fontSize=8,
                value=str(row.get("note") or "") if key == "note" else "",
                maxlen=220 if key == "note" else 40,
                fieldFlags="multiline" if key == "note" else "",
            )
        cursor = row_bottom

    if cursor - 52 < bottom:
        form.showPage()
        page_no += 1
        _chrome(form, page_w, page_h, page_no, project_name, project_address, supplier_name, issued_on)
        cursor = page_h - 0.98 * inch
    cursor -= 14
    form.setFillColor(PRIMARY)
    form.setFont("Times-Roman", 9)
    form.drawString(left, cursor - 12, contact_label)
    form.drawString(left + 3.5 * inch, cursor - 12, "Date")
    _closing_field(form, "bmr_contact", "BMR contact", left + 1.05 * inch, cursor - 16, 2.2 * inch)
    _closing_field(form, "response_date", "Date", left + 3.95 * inch, cursor - 16, 1.5 * inch)
    cursor -= 28
    form.setFillColor(PRIMARY)
    form.setFont("Times-Roman", 9)
    form.drawString(left, cursor - 12, "General notes")
    _closing_field(form, "general_notes", "General notes", left + 1.05 * inch, cursor - 16, content_w - 1.05 * inch, height=16)
    form.save()
    return buffer.getvalue()


def _plain_quantity(value) -> str:
    number = Decimal(str(value))
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def lines_from_material_requirements(requirements: Sequence) -> tuple:
    """Supplier lines from stored project requirements. Prices and SKUs stay off the sheet."""
    lines = []
    for requirement in requirements:
        material = requirement.canonical_material
        unit = "m³" if requirement.canonical_uom == "M3" else requirement.canonical_uom
        item = f"{material.code} — {material.display_name}. Unit {unit}."
        note = str(requirement.note or "").strip()
        if note:
            item = f"{item} {note}"
        lines.append(
            {
                "item": item,
                "qty": _plain_quantity(requirement.quantity),
                "note": "",
            }
        )
    return tuple(lines)


def job_supplier_estimate_request(
    *,
    project_name: str,
    project_address: str,
    supplier_name: str,
    issued_on: str,
    lines: Sequence[Mapping],
) -> dict:
    """One job fills the approved page. The page does not keep another job's address."""
    supplier = str(supplier_name or "").strip()
    rows = []
    for line in lines:
        qty = str(line.get("qty") or "").strip()
        note = str(line.get("note") or "").strip()
        if not qty:
            qty = "TBD"
            if "BRAYMAN TO CONFIRM QTY" not in note:
                note = "BRAYMAN TO CONFIRM QTY" if not note else f"{note}. BRAYMAN TO CONFIRM QTY"
        rows.append(
            {
                "number": len(rows) + 1,
                "item": str(line["item"]).strip(),
                "qty": qty,
                "note": note,
            }
        )
    return {
        "project_name": str(project_name or "").strip(),
        "project_address": str(project_address or "").strip(),
        "supplier_name": supplier,
        "issued_on": issued_on,
        "sku_label": "Code / SKU",
        "contact_label": "Supplier contact",
        "intro": (
            "Please provide your current contractor pricing for the materials listed below. "
            "Where a product or specification is not identified, please confirm the appropriate "
            f"{supplier} product. Quantities shown are based on the project information "
            "currently available to Brayman Construction.",
            "Please return this completed estimate request to Brayman Construction. "
            "A blank is not zero. No price on this sheet was filled in.",
        ),
        "rows": tuple(rows),
    }


def bushel_supplier_estimate_request(readiness: Mapping, model: Optional[Mapping] = None) -> dict:
    """Supplier lines from the Bushel readiness read. Counts are not purchase quantities."""
    by_subject = {item["subject"]: item for item in readiness.get("items") or ()}
    height = _dimension(model, "lower-walking-surface-height")
    opening = _dimension(model, "gate-clear")
    decking = by_subject.get("decking")
    deck_spec = (decking or {}).get("specification") or ""
    width = _piece(deck_spec, "lower-width")
    depth = _piece(deck_spec, "lower-depth")
    stringer = by_subject.get("stringer")
    stringer_spec = (stringer or {}).get("specification") or ""
    specs = (
        (
            "joist",
            "Joists. {count} member stations are recorded. Material, size, and supplied length are not identified.",
        ),
        (
            "stringer",
            "Stair stringers. {count} member stations are recorded. "
            + _kept(stringer_spec, ("Throat", "Stair width"))
            + " Material, size, and supplied length are not identified. "
            "The throat and the stair width are not a lumber quantity.",
        ),
        (
            "post",
            "Posts. Location, material, size, and cut length are not identified.",
        ),
        (
            "beam",
            "Beams. Location, material, size, and supplied length are not identified.",
        ),
        (
            "decking",
            "Walking surface. "
            + " ".join(
                part
                for part in (
                    f"Width {width}." if width else "",
                    f"Depth {depth}." if depth else "",
                    f"Height {height}." if height else "",
                )
                if part
            )
            + " This is the surface, not a board quantity.",
        ),
        (
            "tread-boards",
            "{material} Tread count and board length are not identified.",
        ),
        (
            "veranda-kit",
            "{material} Kit count is not identified. This name stays as stated.",
        ),
        (
            "guard",
            "Guard. Location and layout are not identified. The named kit is a separate line.",
        ),
        (
            "gate",
            "Gate. "
            + (f"Clear opening {opening}. " if opening else "")
            + "Location and construction are not identified.",
        ),
        (
            "pier",
            "Helical piers. {count} locations are recorded. Shaft, helix, length, and product are not identified.",
        ),
    )
    rows = []
    for subject, template in specs:
        item = by_subject.get(subject)
        if item is None:
            continue
        count = item.get("quantity")
        material = (item.get("material_name") or "").strip()
        code = item.get("canonical_material_code") or ""
        if code and material:
            material_text = f"{code} — {material}."
        elif material and material != subject:
            material_text = f"{material}."
        else:
            material_text = ""
        text = template.format(
            count="" if count is None else count,
            material=material_text,
        )
        text = " ".join(text.split())
        rows.append(
            {
                "number": len(rows) + 1,
                "item": text,
                "qty": "TBD",
                "note": _NOTE,
            }
        )
    return {
        "project_name": "Linda Bushel",
        "project_address": "12 D'Arcy's Way, Kemptville, ON",
        "supplier_name": "BMR Winchester",
        "issued_on": "7 October 2026",
        "intro": (
            "Please provide your current contractor pricing for the materials listed below. "
            "Where a product or specification is not identified, please confirm the appropriate "
            "BMR Winchester product. Quantities shown are based on the project information "
            "currently available to Brayman Construction.",
            "Please return this completed estimate request to Brayman Construction. "
            "Where the quantity is TBD, Brayman still has to confirm the purchase quantity. "
            "Please state availability in the note. A blank is not zero. No price on this sheet was filled in.",
        ),
        "rows": tuple(rows),
    }


def _columns(left: float, content_w: float):
    no_w = 0.36 * inch
    qty_w = 0.55 * inch
    unit_w = 0.88 * inch
    line_w = 0.88 * inch
    sku_w = 1.15 * inch
    note_w = 2.55 * inch
    item_w = content_w - (no_w + qty_w + unit_w + line_w + sku_w + note_w)
    columns = {"no": left}
    cursor = left + no_w
    columns["item"] = cursor
    cursor += item_w
    columns["qty"] = cursor
    cursor += qty_w
    columns["unit"] = cursor
    cursor += unit_w
    columns["line"] = cursor
    cursor += line_w
    columns["sku"] = cursor
    cursor += sku_w
    columns["note"] = cursor
    widths = {
        "item": item_w,
        "qty": qty_w,
        "unit": unit_w,
        "line": line_w,
        "sku": sku_w,
        "note": note_w,
    }
    return columns, widths


def _chrome(form, page_w, page_h, page_no, project_name, project_address, supplier_name, issued_on):
    logo = _logo()
    text_x = 0.55 * inch
    if logo is not None:
        form.drawImage(
            str(logo),
            0.5 * inch,
            page_h - 0.72 * inch,
            width=70,
            height=28,
            mask="auto",
            preserveAspectRatio=True,
            anchor="sw",
        )
        text_x = 1.55 * inch
    form.setFillColor(PRIMARY)
    form.setFont("Times-Bold", 11)
    form.drawString(text_x, page_h - 0.42 * inch, COMPANY)
    form.setFont("Times-Roman", 8)
    form.drawString(text_x, page_h - 0.56 * inch, LEGAL)
    form.drawString(text_x, page_h - 0.68 * inch, OFFICE)
    form.setFont("Times-Bold", 10)
    form.drawRightString(page_w - 0.45 * inch, page_h - 0.42 * inch, TITLE)
    form.setFont("Times-Roman", 8)
    form.drawRightString(
        page_w - 0.45 * inch,
        page_h - 0.58 * inch,
        f"For {supplier_name}. Type in the boxes and return this PDF.",
    )
    form.setStrokeColor(ACCENT)
    form.setLineWidth(2)
    form.line(0.45 * inch, page_h - 0.82 * inch, page_w - 0.45 * inch, page_h - 0.82 * inch)
    form.setFillColor(PRIMARY)
    form.rect(0, 0, page_w, 0.38 * inch, fill=1, stroke=0)
    form.setFillColor(colors.white)
    form.setFont("Times-Roman", 8)
    form.drawString(
        0.45 * inch,
        0.16 * inch,
        "  ·  ".join(
            part
            for part in (project_name, project_address, issued_on)
            if str(part or "").strip()
        ),
    )
    form.drawRightString(page_w - 0.45 * inch, 0.16 * inch, f"Page {page_no}")


def _closing_field(form, name, tooltip, x, y, width, height=16, read_only=False, maxlen=180, multiline=False):
    form.acroForm.textfield(
        name=name,
        tooltip=tooltip,
        x=x,
        y=y,
        width=width,
        height=height,
        borderWidth=0.6,
        borderColor=PRIMARY,
        fillColor=FIELD,
        textColor=colors.black,
        forceBorder=True,
        fontName="Times-Roman",
        fontSize=9,
        maxlen=maxlen,
        fieldFlags=" ".join(f for f in ("readOnly" if read_only else "", "multiline" if multiline else "") if f),
    )


def _logo() -> Optional[Path]:
    here = Path(__file__).resolve()
    for parent in here.parents:
        current = parent / "instance/brand_logos/ORG-001/948f96e08827f18d77b47538f65c8b98b45caaf9c981adccba0189976948efe9.png"
        fallback = parent / "app/static/branding/brayman-construction-logo.png"
        if current.is_file():
            return current
        if fallback.is_file():
            return fallback
    return None


def _dimension(model, identifier) -> str:
    if not isinstance(model, Mapping):
        return ""
    for dimension in model.get("dimensions") or []:
        if dimension.get("id") != identifier:
            continue
        value = dimension.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ""
        unit = dimension.get("unit") or ""
        return f"{value} {unit}".strip()
    return ""


def _facts(specification: str):
    return [chunk.strip() for chunk in specification.split(". ") if chunk.strip()]


def _piece(specification: str, label: str) -> str:
    for text in _facts(specification):
        if text.startswith(label):
            return text[len(label):].strip().rstrip(".")
    return ""


def _kept(specification: str, prefixes: Sequence[str]) -> str:
    kept = []
    for text in _facts(specification):
        if any(text.startswith(prefix) for prefix in prefixes):
            kept.append(text.rstrip(".") + ".")
    return (" ".join(kept) + " ") if kept else ""


def _xml(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# Supplier response fields on the approved page.
#
# The page, chrome, colours, fonts, table header, cream fields, and footer
# are the approved 7 Oct 2026 page. The row gains the supplier's response
# boxes in two tiers. Brayman's quantity, unit, and stock length are drawn
# text, not fields, so the supplier cannot change them. Hidden read-only
# fields carry the request and line identity back with the returned PDF.
# ---------------------------------------------------------------------------

RESPONSE_FIELDS = (
    ("sku", "Product / SKU", 40),
    ("product_confirmed", "Confirmed", 40),
    ("unit_price", "Unit price", 20),
    ("discount", "Discount %", 12),
    ("net_price", "Net price", 20),
    ("availability", "Availability", 60),
    ("lead_time", "Lead time", 40),
    ("substitution", "Substitution notes", 240),
    ("line_total", "Line total", 20),
)

# Calculated in the PDF itself. The supplier does not type these.
CALCULATED_FIELDS = ("line_total",)

# Form 2 (14 Oct 2026, Joel): the supplier enters the SKU, the unit cost and
# the discount. The Total column is printed, not a field: CalibraytAI calculates
# every line total and the grand total on the server when the PDF comes back.
# The PDF carries no JavaScript, so any viewer that saves form fields works.
# Requests issued before this keep form 1 above; their stored PDFs are never re-rendered.
RESPONSE_FIELDS_V2 = (
    ("sku", "SKU", 40),
    ("unit_cost", "Unit cost", 20),
    ("discount", "Discount %", 12),
)
RESPONSE_FORM_FIELDS = {1: RESPONSE_FIELDS, 2: RESPONSE_FIELDS_V2}
CALCULATED_BY_BRAYMAN = "Calculated by Brayman"


def _response_columns_v2(left: float, content_w: float):
    no_w = 0.36 * inch
    qty_w = 0.55 * inch
    unit_w = 0.7 * inch
    widths_in = (("sku", 1.75), ("unit_cost", 1.05), ("discount", 0.9))
    total_w = 1.2 * inch
    block = sum(w for _n, w in widths_in) * inch + total_w
    item_w = content_w - (no_w + qty_w + unit_w + block)
    x = left
    cols = {"no": x}
    x += no_w
    cols["item"] = x
    x += item_w
    cols["qty"] = x
    x += qty_w
    cols["unit"] = x
    x += unit_w
    cols["block"] = x
    fields = {}
    for name, width in widths_in:
        fields[name] = (x, width * inch, 1)
        x += width * inch
    cols["total"] = x
    return cols, {"item": item_w, "qty": qty_w, "unit": unit_w, "total": total_w}, fields


def _response_columns(left: float, content_w: float):
    no_w = 0.36 * inch
    qty_w = 0.5 * inch
    unit_w = 0.62 * inch
    block = 5.44 * inch
    item_w = content_w - (no_w + qty_w + unit_w + block)
    x = left
    cols = {"no": x}
    x += no_w
    cols["item"] = x
    x += item_w
    cols["qty"] = x
    x += qty_w
    cols["unit"] = x
    x += unit_w
    cols["block"] = x
    tier1 = (("sku", 1.5), ("product_confirmed", 0.9), ("unit_price", 1.0), ("discount", 0.9), ("net_price", 1.14))
    tier2 = (("availability", 1.5), ("lead_time", 0.9), ("substitution", 2.04), ("line_total", 1.0))
    fields = {}
    cursor = x
    for name, width in tier1:
        fields[name] = (cursor, width * inch, 1)
        cursor += width * inch
    cursor = x
    for name, width in tier2:
        fields[name] = (cursor, width * inch, 2)
        cursor += width * inch
    widths = {"item": item_w, "qty": qty_w, "unit": unit_w}
    return cols, widths, fields


def _hidden(form, name: str, value: str):
    form.acroForm.textfield(
        name=name,
        tooltip=name,
        x=0,
        y=0,
        width=1,
        height=1,
        borderWidth=0,
        fontName="Times-Roman",
        fontSize=6,
        value=value,
        annotationFlags="hidden",
        fieldFlags="readOnly",
        maxlen=200,
    )


def render_supplier_response_request(
    *,
    project_name: str,
    project_address: str,
    supplier_name: str,
    issued_on: str,
    intro: Sequence[str],
    rows: Sequence[Mapping],
    request_id: str,
    project_id: int,
    contact_label: str = "Supplier contact",
    layout: int = 2,
) -> bytes:
    """The approved page with the supplier's response boxes on each row.

    Layout 2 (current): SKU, unit cost, discount %, calculated total.
    Layout 1: the historical eight boxes, kept so earlier requests can be reproduced in tests.
    """
    from reportlab.platypus import Paragraph

    buffer = BytesIO()
    page_w, page_h = landscape(letter)
    form = Canvas(buffer, pagesize=landscape(letter))
    form.acroForm.extras["NeedAppearances"] = "true"
    form.setTitle(f"{project_name} — {TITLE}")
    form.setAuthor(COMPANY)
    form.setSubject(f"Request {request_id}")
    left = 0.4 * inch
    content_w = page_w - 0.8 * inch
    if layout not in RESPONSE_FORM_FIELDS:
        raise ValueError(f"Unknown supplier response layout {layout!r}.")
    spec = RESPONSE_FORM_FIELDS[layout]
    labels = dict((name, label) for name, label, _ in spec)
    maxlens = dict((name, m) for name, _, m in spec)
    cols, widths, fields = (_response_columns_v2 if layout == 2 else _response_columns)(left, content_w)
    item_style = ParagraphStyle("item", fontName="Times-Roman", fontSize=7.5, leading=9, textColor=colors.black)
    intro_style = ParagraphStyle("intro", fontName="Times-Roman", fontSize=8, leading=10, textColor=PRIMARY)
    page_no = 1
    _hidden(form, "request_id", request_id)
    _hidden(form, "request_project", str(int(project_id)))
    if layout == 2:
        _hidden(form, "response_form", "2")

    head_h = 26 if layout == 1 else 18

    def paint_header(top: float) -> float:
        form.setFillColor(PRIMARY)
        form.rect(left, top - head_h, content_w, head_h, fill=1, stroke=0)
        form.setFillColor(colors.white)
        form.setFont("Times-Bold", 8)
        form.drawString(cols["no"] + 2, top - 11, "No.")
        form.drawString(cols["item"] + 2, top - 11, "Item")
        form.drawString(cols["qty"] + 2, top - 11, "Qty")
        form.drawString(cols["unit"] + 2, top - 11, "Unit")
        for name, (x, _w, tier) in fields.items():
            form.drawString(x + 2, top - (11 if tier == 1 else 22), labels[name])
        if layout == 2:
            form.drawString(cols["total"] + 2, top - 11, "Total")
        return top - head_h

    def start_page(first: bool) -> float:
        _chrome(form, page_w, page_h, page_no, project_name, project_address, supplier_name, issued_on)
        top = page_h - 0.98 * inch
        if first:
            for text in intro:
                block = Paragraph(_xml(text), intro_style)
                _, height = block.wrap(content_w, 80)
                block.drawOn(form, left, top - height)
                top -= height + 2
            top -= 4
        return paint_header(top)

    cursor = start_page(True)
    bottom = 0.55 * inch
    for row in rows:
        number = int(row["number"])
        text = _xml(str(row["item"]))
        if row.get("status_label"):
            text = f"<b>{_xml(row['status_label'])}</b><br/>{text}"
        block = Paragraph(text, item_style)
        _, text_h = block.wrap(widths["item"] - 6, 400)
        row_h = max(48 if layout == 1 else 30, text_h + 8)
        if cursor - row_h < bottom:
            form.showPage()
            page_no += 1
            cursor = start_page(False)
        row_bottom = cursor - row_h
        if number % 2 == 0:
            form.setFillColor(HEAD)
            form.rect(left, row_bottom, content_w, row_h, fill=1, stroke=0)
        form.setStrokeColor(RULE)
        form.setLineWidth(0.3)
        form.rect(left, row_bottom, content_w, row_h, fill=0, stroke=1)
        form.setFillColor(colors.black)
        form.setFont("Times-Roman", 8)
        form.drawString(cols["no"] + 2, cursor - 12, str(number))
        block.drawOn(form, cols["item"] + 2, cursor - 4 - text_h)
        form.drawString(cols["qty"] + 2, cursor - 12, str(row.get("qty") or ""))
        unit_lines = str(row.get("unit") or "").split("\n")
        for i, text in enumerate(unit_lines[:3]):
            form.drawString(cols["unit"] + 2, cursor - 12 - 9 * i, text)
        for name, (x, width, tier) in fields.items():
            top_of_box = cursor - 14 - (tier - 1) * 20
            form.acroForm.textfield(
                name=f"{name}_{number:02d}",
                tooltip=f"{labels[name]} for item {number}",
                x=x + 1,
                y=top_of_box - 17,
                width=width - 2,
                height=17,
                borderWidth=0.6,
                borderColor=PRIMARY,
                fillColor=FIELD,
                textColor=colors.black,
                forceBorder=True,
                fontName="Times-Roman",
                fontSize=8,
                value="",
                maxlen=maxlens[name],
                fieldFlags="readOnly" if name in CALCULATED_FIELDS else "",
            )
        if layout == 2:
            # Printed, not a field: the supplier cannot type a total, and no viewer has to calculate one.
            form.setFillColor(colors.HexColor("#6b7280"))
            form.setFont("Times-Italic", 7.5)
            form.drawString(cols["total"] + 4, cursor - 26, CALCULATED_BY_BRAYMAN if row.get("qty") not in (None, "", "TBD") else "Qty TBD")
            form.setFillColor(colors.black)
        _hidden(form, f"line_key_{number:02d}", str(row["key"]))
        _hidden(form, f"line_sig_{number:02d}", str(row["signature"]))
        cursor = row_bottom

    if cursor - (70 if layout == 1 else 124) < bottom:
        form.showPage()
        page_no += 1
        _chrome(form, page_w, page_h, page_no, project_name, project_address, supplier_name, issued_on)
        cursor = page_h - 0.98 * inch
    cursor -= 14
    form.setFillColor(PRIMARY)
    form.setFont("Times-Roman", 9)
    form.drawString(left, cursor - 12, contact_label)
    form.drawString(left + 3.5 * inch, cursor - 12, "Date")
    form.drawString(left + 5.7 * inch, cursor - 12, "Prices valid until")
    _closing_field(form, "bmr_contact", contact_label, left + 1.05 * inch, cursor - 16, 2.2 * inch)
    _closing_field(form, "response_date", "Date", left + 3.95 * inch, cursor - 16, 1.5 * inch)
    _closing_field(form, "valid_until", "Prices valid until", left + 6.85 * inch, cursor - 16, 1.5 * inch)
    form.setFont("Times-Bold", 9)
    form.drawString(left + 8.5 * inch, cursor - 12, "Total")
    if layout == 2:
        form.setFillColor(colors.HexColor("#6b7280"))
        form.setFont("Times-Italic", 8)
        form.drawString(left + 8.9 * inch + 4, cursor - 12, CALCULATED_BY_BRAYMAN)
    else:
        _closing_field(form, "grand_total", "Total of the line totals", left + 8.9 * inch, cursor - 16, content_w - 8.9 * inch, read_only=True)
    cursor -= 28
    form.setFillColor(PRIMARY)
    form.setFont("Times-Roman", 9)
    form.drawString(left, cursor - 12, "General notes")
    if layout == 2:
        # Taller, multi-line notes box with the substitution instruction under it.
        _closing_field(form, "general_notes", "General notes. For a substitution: line number and replacement SKU.",
                       left + 1.05 * inch, cursor - 40, content_w - 1.05 * inch, height=40, maxlen=1000, multiline=True)
        form.setFont("Times-Bold", 8)
        form.drawString(
            left, cursor - 54,
            "Substitutions: write the original line number and your replacement SKU, one per line, for example "
            "\"Line 9 - replacement SKU GATE-48-BLK\".",
        )
        form.setFont("Times-Roman", 7.5)
        form.drawString(
            left, cursor - 65,
            "Price the replacement in that line's boxes. Brayman reviews every substitution before its price is used.",
        )
        form.drawString(
            left, cursor - 78,
            "Brayman calculates each line total (quantity x unit cost less the discount, the net rounded to the cent) and the grand total when this PDF is returned. "
            "Enter 0 for no discount; a blank discount is not zero.",
        )
        form.drawString(
            left, cursor - 89,
            "Any PDF viewer that saves form fields can be used (for example Apple Preview or Adobe Acrobat Reader). Save the PDF after typing. Prices CAD before HST.",
        )
    else:
        _closing_field(form, "general_notes", "General notes", left + 1.05 * inch, cursor - 16, content_w - 1.05 * inch, height=16)
        form.setFont("Times-Roman", 7.5)
        form.drawString(
            left, cursor - 30,
            "Net price fills in once a unit price and a discount (0 if none) are entered. Line totals use Brayman's quantity. "
            "The total adds every line total. Lines marked TBD have no total.",
        )
    form.save()
    if layout == 2:
        return buffer.getvalue()  # no embedded JavaScript
    return _add_live_calculations(buffer.getvalue(), rows)


def _quantity_number(text) -> Optional[float]:
    try:
        value = float(str(text).strip())
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def net_price_script(n: str) -> str:
    """Net = unit price less the discount, to the cent. Runs only when both are entered."""
    return (
        f'var u{n}=String(this.getField("unit_price_{n}").valueAsString).replace(/[$,\\s]/g,"");'
        f'var d{n}=String(this.getField("discount_{n}").valueAsString).replace(/[%\\s]/g,"");'
        f'if(u{n}!==""&&d{n}!==""&&!isNaN(u{n})&&!isNaN(d{n})&&Number(d{n})>=0&&Number(d{n})<=100)'
        f'{{event.value=(Math.round(Number(u{n})*(100-Number(d{n}))+1e-7)/100).toFixed(2);}}'
    )


def line_total_script(n: str, quantity: Optional[float]) -> str:
    if quantity is None:
        return 'event.value="";'
    return (
        f'var t{n}=String(this.getField("net_price_{n}").valueAsString).replace(/[$,\\s]/g,"");'
        f'if(t{n}!==""&&!isNaN(t{n})){{event.value=(Math.round(Number(t{n})*{quantity!r}*100+1e-7)/100).toFixed(2);}}'
        f'else{{event.value="";}}'
    )


def grand_total_script(numbers) -> str:
    names = ",".join(f'"line_total_{n}"' for n in numbers)
    return (
        f"var gtNames=[{names}],gt=0,gtCount=0;"
        "for(var gi=0;gi<gtNames.length;gi++){var gs=String(this.getField(gtNames[gi]).valueAsString);"
        'if(gs!==""&&!isNaN(gs)){gt+=Number(gs);gtCount++;}}'
        'event.value=gtCount?(Math.round(gt*100)/100).toFixed(2):"";'
    )


def _add_live_calculations(payload: bytes, rows) -> bytes:
    """Attach calculate actions and the calculation order to the form fields."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, DictionaryObject, NameObject, TextStringObject

    scripts = {}
    numbers = []
    for row in rows:
        n = f"{int(row['number']):02d}"
        numbers.append(n)
        scripts[f"net_price_{n}"] = net_price_script(n)
        scripts[f"line_total_{n}"] = line_total_script(n, _quantity_number(row.get("qty")))
    scripts["grand_total"] = grand_total_script(numbers)
    writer = PdfWriter(clone_from=PdfReader(BytesIO(payload)))
    refs = {}
    for page in writer.pages:
        for annot_ref in page.get("/Annots") or []:
            annot = annot_ref.get_object()
            name = annot.get("/T")
            if name in scripts:
                annot[NameObject("/AA")] = DictionaryObject(
                    {
                        NameObject("/C"): DictionaryObject(
                            {
                                NameObject("/S"): NameObject("/JavaScript"),
                                NameObject("/JS"): TextStringObject(scripts[name]),
                            }
                        )
                    }
                )
                refs[name] = annot_ref
    order = [f"net_price_{n}" for n in numbers] + [f"line_total_{n}" for n in numbers] + ["grand_total"]
    missing = [name for name in order if name not in refs]
    if missing:
        raise RuntimeError(f"Calculated fields not found: {missing[:3]}")
    acro = writer._root_object["/AcroForm"]
    acro[NameObject("/CO")] = ArrayObject([refs[name] for name in order])
    out = BytesIO()
    writer.write(out)
    return out.getvalue()

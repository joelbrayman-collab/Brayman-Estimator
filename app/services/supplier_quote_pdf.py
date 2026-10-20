"""Supplier material quotation PDF (Supplier PRO Desk, 20 Oct 2026).

Built with the same ReportLab pipeline and money/escaping helpers as the contractor proposal PDF, but it
is a different document: materials only, the supplier's own brand, no labour, no contract. It is drawn
only from the frozen issued record, so the PDF a customer sees always matches what was issued.
"""

from __future__ import annotations

import tempfile
from decimal import Decimal
from io import BytesIO
from typing import Dict, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.proposal_pdf import _escape, _money, _parse_color

TITLE = "MATERIAL QUOTATION"
DEFAULT_COLOR = "#1f3a5f"
ASSUMPTIONS = (
    "Materials only. Labour, installation, equipment, permits and site work are not included.",
    "Quantities come from the dimensions and specifications confirmed with the customer at the counter and shown on "
    "the preliminary sales drawing. Verify on site before ordering or cutting.",
    "The drawing is a preliminary sales drawing, not for construction, not engineered and not a permit drawing.",
    "Roof trusses are designed by the truss manufacturer. Posts, footings, door headers and connections need technical "
    "review by a qualified designer or engineer.",
    "Prices are the store's prices on the date of this quotation and hold until the valid-until date.",
)


def _styles(primary):
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle("brand", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=primary),
        "small": ParagraphStyle("small", parent=base["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#3a414b")),
        "title": ParagraphStyle("title", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=13, leading=16),
        "h": ParagraphStyle("h", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13, spaceBefore=8, spaceAfter=4,
                            textColor=primary),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=8.6, leading=11),
        "cell": ParagraphStyle("cell", parent=base["Normal"], fontSize=7.6, leading=9.2),
        "cellr": ParagraphStyle("cellr", parent=base["Normal"], fontSize=7.6, leading=9.2, alignment=TA_RIGHT),
        "banner": ParagraphStyle("banner", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12,
                                 textColor=colors.HexColor("#9b1c1c")),
    }


def _m(value) -> str:
    return _money(Decimal(value)) if value not in (None, "") else "—"


def _qty(value) -> str:
    if value in (None, ""):
        return "—"
    return format(Decimal(str(value)).normalize(), "f")


def render_quote_pdf(frozen: Dict, *, logo_bytes: Optional[bytes] = None, brand_color: Optional[str] = None,
                     drawing_png: Optional[bytes] = None, approval_note: str = "") -> bytes:
    primary = _parse_color(brand_color, DEFAULT_COLOR)
    st = _styles(primary)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch, topMargin=0.55 * inch,
                            bottomMargin=0.6 * inch, title=f"{TITLE} {frozen.get('number', '')}",
                            author=frozen.get("supplier", {}).get("name", ""), creator="CalibraytAI")
    story = []
    supplier = frozen.get("supplier", {})
    customer = frozen.get("customer", {})
    totals = frozen.get("totals", {})

    if frozen.get("demo_synthetic") or frozen.get("demo_prices"):
        story.append(Paragraph("SYNTHETIC DEMONSTRATION DATA — not a real quotation and not the store's real prices.", st["banner"]))
        story.append(Spacer(1, 4))

    head_left = []
    if logo_bytes:
        try:
            head_left.append(Image(BytesIO(logo_bytes), width=1.6 * inch, height=0.6 * inch, kind="proportional"))
        except Exception:  # noqa: BLE001 - an unreadable logo falls back to the name
            pass
    head_left.append(Paragraph(_escape(supplier.get("name", "")), st["brand"]))
    if supplier.get("location"):
        head_left.append(Paragraph(_escape(supplier["location"]), st["small"]))
    if frozen.get("contact"):
        head_left.append(Paragraph(_escape(frozen["contact"]), st["small"]))
    head_right = [Paragraph(TITLE, st["title"]),
                  Paragraph(f"Quotation <b>{_escape(frozen.get('number', ''))}</b>", st["body"]),
                  Paragraph(f"Date {_escape((frozen.get('issued_at') or '')[:10])}", st["body"]),
                  Paragraph(f"Valid until <b>{_escape(frozen.get('valid_until', ''))}</b>", st["body"])]
    head = Table([[head_left, head_right]], colWidths=[4.3 * inch, 3.0 * inch])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 1.2, primary),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story += [head, Spacer(1, 8)]

    cust_lines = [customer.get("name", ""), customer.get("address", ""), customer.get("town", ""), customer.get("phone", ""),
                  customer.get("email", "")]
    story.append(Table([[Paragraph("<b>Customer</b><br/>" + "<br/>".join(_escape(x) for x in cust_lines if x), st["body"]),
                         Paragraph("<b>Building</b><br/>" + _escape(frozen.get("description", "")) +
                                   f"<br/>Floor area {_escape(frozen.get('areas', {}).get('floor_sqft', ''))} sq ft", st["body"])]],
                       colWidths=[3.6 * inch, 3.7 * inch],
                       style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9ced6")),
                                         ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9ced6")),
                                         ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 5)])))

    rows = frozen.get("rows", [])
    priced = [r for r in rows if r.get("price_status") == "PRICED"]
    story.append(Paragraph("Materials", st["h"]))
    data = [[Paragraph("<b>Item</b>", st["cell"]), Paragraph("<b>SKU</b>", st["cell"]), Paragraph("<b>Qty</b>", st["cellr"]),
             Paragraph("<b>Unit</b>", st["cell"]), Paragraph("<b>Unit price</b>", st["cellr"]),
             Paragraph("<b>Discount</b>", st["cellr"]), Paragraph("<b>Extended</b>", st["cellr"])]]
    group = None
    style = [("LINEBELOW", (0, 0), (-1, 0), 0.8, primary), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    for r in priced:
        if r.get("group") != group:
            group = r.get("group")
            data.append([Paragraph(f"<b>{_escape(group)}</b>", st["cell"]), "", "", "", "", "", ""])
            style.append(("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), colors.HexColor("#f1f3f6")))
            style.append(("SPAN", (0, len(data) - 1), (-1, len(data) - 1)))
        item = _escape(r.get("product_description") or r.get("item"))
        sub = _escape(r.get("item", ""))
        if r.get("cut_list"):
            sub += "<br/>Cut list: " + ", ".join(f"{n} @ {_escape(length)}" for length, n in r["cut_list"])
        disc = _m(r.get("line_discount")) if r.get("line_discount") not in (None, "", "0.00") else ""
        data.append([Paragraph(f"{item}<br/><font size='6.6' color='#59606b'>{sub}</font>", st["cell"]),
                     Paragraph(_escape(r.get("sku", "")), st["cell"]), Paragraph(_qty(r.get("sales_qty")), st["cellr"]),
                     Paragraph(_escape(r.get("sales_unit", "")), st["cell"]), Paragraph(_m(r.get("unit_price")), st["cellr"]),
                     Paragraph(disc, st["cellr"]), Paragraph(_m(r.get("extended")), st["cellr"])])
    widths = [2.9 * inch, 0.9 * inch, 0.55 * inch, 0.45 * inch, 0.8 * inch, 0.7 * inch, 0.9 * inch]
    story.append(Table(data, colWidths=widths, repeatRows=1, style=TableStyle(style)))

    tot = [["Materials", _m(totals.get("subtotal"))]]
    if totals.get("line_discounts") not in (None, "", "0.00"):
        tot.append(["Line discounts", "−" + _m(totals.get("line_discounts"))])
    if totals.get("quote_discount") not in (None, "", "0.00"):
        tot.append([f"Quotation discount ({_qty(totals.get('quote_discount_percent'))}%)", "−" + _m(totals.get("quote_discount"))])
    tot.append(["Delivery", _m(totals.get("delivery"))])
    tot.append([f"{totals.get('tax_label') or 'Tax'} ({_qty(totals.get('tax_rate_percent'))}%)", _m(totals.get("tax"))])
    tot.append(["Total", _m(totals.get("total"))])
    tt = Table([[Paragraph(_escape(a), st["body"]), Paragraph(b, st["cellr"])] for a, b in tot],
               colWidths=[2.4 * inch, 1.2 * inch], hAlign="RIGHT")
    tt.setStyle(TableStyle([("LINEABOVE", (0, -1), (-1, -1), 1, primary), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")]))
    story += [Spacer(1, 6), KeepTogether(tt)]

    out = [r for r in rows if r.get("price_status") != "PRICED"]
    if out:
        story.append(Paragraph("Not included in this quotation", st["h"]))
        for r in out:
            why = r.get("reason") or r.get("note") or "By design: not counted here."
            story.append(Paragraph(f"• <b>{_escape(r.get('item'))}</b> — {_escape(why)}", st["body"]))
    story.append(Paragraph("Assumptions and exclusions", st["h"]))
    for a in ASSUMPTIONS:
        story.append(Paragraph("• " + _escape(a), st["body"]))
    if frozen.get("terms"):
        story.append(Paragraph("Terms", st["h"]))
        story.append(Paragraph(_escape(frozen["terms"]).replace("\n", "<br/>"), st["body"]))

    story.append(Paragraph("Customer approval", st["h"]))
    story.append(Paragraph(_escape(approval_note or "To accept, sign below or use the approval link sent by the store."), st["body"]))
    story.append(Spacer(1, 14))
    story.append(Table([["Name", "", "Signature", "", "Date", ""]],
                       colWidths=[0.5 * inch, 2.0 * inch, 0.7 * inch, 2.0 * inch, 0.4 * inch, 1.3 * inch],
                       style=TableStyle([("LINEBELOW", (1, 0), (1, 0), 0.5, colors.black), ("LINEBELOW", (3, 0), (3, 0), 0.5, colors.black),
                                         ("LINEBELOW", (5, 0), (5, 0), 0.5, colors.black), ("FONTSIZE", (0, 0), (-1, -1), 8)])))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Quotation record {_escape((frozen.get('_sha256') or '')[:16])} · prepared by "
                           f"{_escape(frozen.get('issued_by', ''))} with CalibraytAI", st["small"]))

    sheets = [drawing_png] if isinstance(drawing_png, (bytes, bytearray)) else list(drawing_png or [])
    for png in sheets:  # one page per drawing sheet (A-1 floor plan, A-2 elevations)
        story += [PageBreak(), Paragraph("Preliminary sales drawing — not for construction", st["h"]),
                  Image(BytesIO(png), width=7.3 * inch, height=7.3 * inch * 11 / 17)]
    doc.build(story)
    return buf.getvalue()

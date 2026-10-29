"""The documents a contractor and a store sign in the Supplier Hub (Joel, 20 Oct 2026).

Two documents, each rendered once and frozen by the signing engine before anyone signs:
- the purchase order (what is ordered, at what price, delivered where and when);
- a delivery change (the order, the delivery before and after, the reason).
Plain ReportLab, letter size, no logos: the record is the agreement, not a sales sheet.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#14284b")


def _esc(text) -> str:
    return (str(text or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _money(value) -> str:
    try:
        return "${:,.2f}".format(Decimal(str(value)))
    except (InvalidOperation, TypeError, ValueError):
        return _esc(value)


def _day(value) -> str:
    if value is None:
        return "To be set"
    return value.strftime("%a %b %d, %Y").replace(" 0", " ")


def _when(day, window) -> str:
    text = _day(day)
    return f"{text}, {window}" if day is not None and window else text


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=16, leading=20,
                                textColor=NAVY, spaceAfter=4),
        "sub": ParagraphStyle("s", parent=base["Normal"], fontName="Helvetica", fontSize=9, leading=12,
                              textColor=colors.HexColor("#555555")),
        "body": ParagraphStyle("b", parent=base["Normal"], fontName="Helvetica", fontSize=9, leading=12),
        "label": ParagraphStyle("l", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12),
        "cell": ParagraphStyle("c", parent=base["Normal"], fontName="Helvetica", fontSize=8, leading=10),
        "head": ParagraphStyle("h", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10,
                               textColor=colors.white),
    }


def _facts(rows, st):
    table = Table([[Paragraph(_esc(a), st["label"]), Paragraph(_esc(b) or "—", st["body"])] for a, b in rows],
                  colWidths=[1.8 * inch, 5.1 * inch])
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return table


def _build(title: str, flowables) -> bytes:
    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.8 * inch, rightMargin=0.8 * inch, topMargin=0.7 * inch,
                      bottomMargin=0.7 * inch, title=title, author="CalibraytAI").build(flowables)
    return buffer.getvalue()


def purchase_order_pdf(order, *, buyer_name: str, supplier_name: str, project_name: str) -> bytes:
    st = _styles()
    flow = [
        Paragraph(f"Purchase order {_esc(order.number)}", st["title"]),
        Paragraph(f"From {_esc(buyer_name)} to {_esc(supplier_name)}, through CalibraytAI", st["sub"]),
        Spacer(1, 10),
        _facts([
            ("Buyer", buyer_name),
            ("Supplier", supplier_name),
            ("Project reference", project_name),
            ("Against quote", order.quote_ref),
            ("Placed by", f"{order.placed_by_name} on {_day(order.placed_at)}"),
            ("Deliver to", order.delivery_address),
            ("Requested delivery", _when(order.delivery_date, order.delivery_window)),
            ("Site contact", order.site_contact or ""),
            ("Notes", order.notes or ""),
        ], st),
        Spacer(1, 12),
    ]
    data = [[Paragraph(h, st["head"]) for h in ("No.", "Item", "SKU", "Qty", "Unit", "Net unit cost", "Total")]]
    for line in order.lines_json or []:
        data.append([Paragraph(_esc(line.get("number")), st["cell"]), Paragraph(_esc(line.get("description")), st["cell"]),
                     Paragraph(_esc(line.get("sku")), st["cell"]), Paragraph(_esc(line.get("quantity")), st["cell"]),
                     Paragraph(_esc(line.get("unit")), st["cell"]), Paragraph(_money(line.get("net_unit_cost")), st["cell"]),
                     Paragraph(_money(line.get("line_value")), st["cell"])])
    data.append(["", Paragraph("<b>Total before tax</b>", st["cell"]), "", "", "", "", Paragraph(f"<b>{_money(order.total)}</b>", st["cell"])])
    lines = Table(data, colWidths=[0.4 * inch, 2.75 * inch, 0.95 * inch, 0.55 * inch, 0.45 * inch, 0.9 * inch, 0.9 * inch],
                  repeatRows=1)
    lines.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, colors.HexColor("#cccccc")), ("LINEABOVE", (0, -1), (-1, -1), 0.8, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    flow += [lines, Spacer(1, 14), Paragraph(
        "This purchase order is placed against the supplier's quote at the prices shown, under the account terms "
        "already in place between the buyer and the supplier. It is agreed when both sides have signed: the buyer "
        "when placing it and the supplier when confirming it. The signing record is added as the last page.", st["body"])]
    return _build(f"Purchase order {order.number}", flow)


def delivery_change_pdf(change, *, order, buyer_name: str, supplier_name: str, project_name: str,
                        requested_by_company: str) -> bytes:
    st = _styles()
    flow = [
        Paragraph(f"Delivery change for purchase order {_esc(order.number)}", st["title"]),
        Paragraph(f"Between {_esc(buyer_name)} and {_esc(supplier_name)}, through CalibraytAI", st["sub"]),
        Spacer(1, 10),
        _facts([
            ("Purchase order", order.number),
            ("Project reference", project_name),
            ("Deliver to", order.delivery_address),
            ("Delivery before the change", _when(change.previous_date, change.previous_window)),
            ("New delivery", _when(change.new_date, change.new_window)),
            ("Reason", change.reason),
            ("Note", change.note or ""),
            ("Requested by", f"{change.requested_by_name} ({requested_by_company}) on "
                             f"{change.requested_at.strftime('%b %d, %Y at %H:%M UTC').replace(' 0', ' ')}"
             if isinstance(change.requested_at, datetime) else change.requested_by_name),
        ], st),
        Spacer(1, 14),
        Paragraph("The delivery for this purchase order moves to the new date and time when both sides have signed this "
                  "change. Until then the earlier delivery stands. Everything else on the purchase order is unchanged. "
                  "The signing record is added as the last page.", st["body"]),
    ]
    return _build(f"Delivery change for {order.number}", flow)

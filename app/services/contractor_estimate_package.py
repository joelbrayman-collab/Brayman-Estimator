"""The Contractor Estimate Package (decision 2, Joel 30 Oct 2026; Paulusse REV2 is the reference).

A governed, landscape (legal) internal package for the contractor: every work package with its status (in Brayman's
price, or excluded and by whom), delivery, hours, direct cost and selling price; the line detail per package; and
the customer view (included work at selling price, then Excluded / By Others). Every page is landscape so the set
prints and binds as one. Plain PDF with no form fields or scripts, so it opens the same in any viewer.

Figures come only from the application (estimate_economics, the priced lines and work_packages). Nothing is
computed here that the estimate does not already hold.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, legal
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

TITLE = "Contractor Estimate Package"
INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#5f6b7a")
RULE = colors.HexColor("#c8ced6")
BAND = colors.HexColor("#eef1f4")
EXCLUDED_INK = colors.HexColor("#8a5a00")


def _money(value) -> str:
    if value is None:
        return "—"
    v = Decimal(str(value)).quantize(Decimal("0.01"))
    return ("-" if v < 0 else "") + f"${abs(v):,.2f}"


def _hours(value) -> str:
    if value is None:
        return "—"
    return f"{Decimal(str(value)).quantize(Decimal('0.01')):,.2f}"


def _esc(text) -> str:
    return (str(text or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _styles():
    return {
        "title": ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=16, leading=19, textColor=INK),
        "flag": ParagraphStyle("f", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=EXCLUDED_INK),
        "meta": ParagraphStyle("m", fontName="Helvetica", fontSize=9, leading=12, textColor=MUTED),
        "h2": ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=INK,
                             spaceBefore=8, spaceAfter=4),
        "cell": ParagraphStyle("c", fontName="Helvetica", fontSize=8.5, leading=10.5, textColor=INK),
        "cellb": ParagraphStyle("cb", fontName="Helvetica-Bold", fontSize=8.5, leading=10.5, textColor=INK),
        "body": ParagraphStyle("b", fontName="Helvetica", fontSize=9.5, leading=12.5, textColor=INK),
    }


def package_rows(version) -> list:
    """One row per governed work package (and one 'Other' row for sections no package owns)."""
    from app.models.guided_estimating import GuidedEstimate
    from app.services import work_packages as WP

    guided = GuidedEstimate.query.filter_by(estimate_id=version.estimate_id).first()
    hours_by_line = _line_hours(version)
    rows, owned = [], set()
    for package in WP.packages(guided):
        lines = WP.package_lines(package, version)
        owned.update(line.id for line in lines)
        participates = WP.package_participates(package)
        rows.append({
            "name": package.display_name,
            "status": ("In Brayman's price" if participates else
                       ("Shared: no other work included" if WP.is_included(package) else
                        f"Excluded · {WP.responsible_label(package)}")),
            "participates": participates,
            "shared": package.shared_rule is not None,
            "delivery": WP.delivery_label(package),
            "hours": sum((hours_by_line.get(line.id, Decimal("0")) for line in lines), Decimal("0")),
            "direct": sum((Decimal(line.extended_cost or 0) for line in lines), Decimal("0")),
            "sell": sum((Decimal(line.sell_price or 0) for line in lines), Decimal("0")),
            "lines": lines,
            "exclusion_text": None if participates else WP.customer_exclusion_text(package),
        })
    loose = [line for section in version.sections for line in section.line_items if line.id not in owned]
    if loose:
        rows.append({"name": "Other estimate lines", "status": "In Brayman's price", "participates": True,
                     "shared": False, "delivery": "—",
                     "hours": sum((hours_by_line.get(line.id, Decimal("0")) for line in loose), Decimal("0")),
                     "direct": sum((Decimal(line.extended_cost or 0) for line in loose), Decimal("0")),
                     "sell": sum((Decimal(line.sell_price or 0) for line in loose), Decimal("0")),
                     "lines": loose, "exclusion_text": None})
    return rows


def _line_hours(version) -> dict:
    """Labour hours per estimate line: a labour line holds its hours as its quantity (estimate_labour_hours)."""
    from app.services.estimate_labour_hours import is_labour_line

    return {line.id: Decimal(str(line.quantity or 0)) for section in version.sections for line in section.line_items
            if is_labour_line(line)}


def _table(data, widths, *, header=True, total=False, muted_rows=()):
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), BAND), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    if total:
        style += [("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("LINEABOVE", (0, -1), (-1, -1), 1.2, INK)]
    for r in muted_rows:
        style.append(("TEXTCOLOR", (0, r), (-1, r), EXCLUDED_INK))
    table.setStyle(TableStyle(style))
    return table


def build_contractor_estimate_package(version, *, generated_by: str = "") -> bytes:
    from app.services.estimate_approval import approval_for
    from app.services.estimate_economics import economics

    estimate = version.estimate
    project = estimate.project
    client = getattr(project, "client", None)
    e = economics(version)
    rows = package_rows(version)
    approval = approval_for(version)
    s = _styles()
    page_w, _page_h = landscape(legal)
    usable = page_w - 1.0 * inch

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(legal), leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                            topMargin=0.55 * inch, bottomMargin=0.6 * inch, title=TITLE,
                            author="Brayman Construction")

    def header(flag):
        meta = (f"{_esc(project.name)}"
                + (f" · {_esc(client.name)}" if client is not None else "")
                + f" · {_esc(estimate.estimate_number)} {_esc(version.display_label)}"
                + f" · generated {datetime.utcnow():%Y-%m-%d %H:%M} UTC" + (f" by {_esc(generated_by)}" if generated_by else ""))
        return [Paragraph(TITLE, s["title"]), Paragraph(flag, s["flag"]), Paragraph(meta, s["meta"]), Spacer(1, 6)]

    story = header("INTERNAL — CONTRACTOR COPY. Contains cost, labour and margin. Not for the customer.")
    if approval is not None:
        story.append(Paragraph(f"Approved by {_esc(approval.approved_by_name)} on {approval.approved_at:%Y-%m-%d %H:%M} "
                               f"UTC · fingerprint {approval.fingerprint[:16]}", s["meta"]))
    else:
        story.append(Paragraph("Not yet approved (Gate 1). Figures may still change.", s["meta"]))
    story.append(Spacer(1, 6))

    # 1. Work packages
    story.append(Paragraph("1. Work packages", s["h2"]))
    data = [["Work package", "Status", "Delivery", "Hours", "Direct cost", "Selling price"]]
    muted = []
    for i, row in enumerate(rows, start=1):
        data.append([Paragraph(_esc(row["name"]) + (" <font color='#5f6b7a'>(shared)</font>" if row["shared"] else ""),
                               s["cell"]),
                     Paragraph(_esc(row["status"]), s["cell"]), Paragraph(_esc(row["delivery"]), s["cell"]),
                     _hours(row["hours"]), _money(row["direct"]),
                     _money(row["sell"]) if row["participates"] else "not priced"])
        if not row["participates"]:
            muted.append(i)
    data.append(["Brayman's price", "", "", _hours(e.get("labour_hours")), _money(e.get("direct_cost")),
                 _money(e.get("selling_price"))])
    widths = [usable * f for f in (0.30, 0.22, 0.14, 0.09, 0.125, 0.125)]
    t = _table(data, widths, total=True, muted_rows=muted)
    t.setStyle(TableStyle([("ALIGN", (3, 0), (-1, -1), "RIGHT")]))
    story.append(t)
    story.append(Spacer(1, 8))

    summary = [["Labour rate", _money(e.get("labour_rate")) + " / h"],
               ["Target gross margin", (f"{Decimal(str(e['target_gross_margin'])) * 100:.2f}%"
                                        if e.get("target_gross_margin") is not None else "—")],
               ["Direct cost", _money(e.get("direct_cost"))],
               ["Selling price (before tax)", _money(e.get("selling_price"))],
               [f"Tax ({e.get('tax_percent') or 0}%)", _money(e.get("tax"))],
               ["Customer total", _money(e.get("customer_total"))]]
    st = _table(summary, [usable * 0.25, usable * 0.15], header=False, total=True)
    st.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "RIGHT")]))
    st.hAlign = "RIGHT"
    story.append(st)

    # 2. Line detail
    story.append(PageBreak())
    story += header("INTERNAL — CONTRACTOR COPY · Line detail by work package")
    hours_by_line = _line_hours(version)
    for row in rows:
        data = [["Line", "Qty", "Unit", "Unit cost", "Extended cost", "Hours", "Selling price"]]
        for line in row["lines"]:
            data.append([Paragraph(_esc(line.description), s["cell"]), f"{Decimal(str(line.quantity or 0)):,.2f}",
                         _esc(line.unit), _money(line.unit_cost), _money(line.extended_cost),
                         _hours(hours_by_line.get(line.id)),
                         _money(line.sell_price) if row["participates"] else "not priced"])
        if len(data) == 1:
            data.append([Paragraph("No lines yet.", s["cell"]), "", "", "", "", "", ""])
        widths = [usable * f for f in (0.40, 0.08, 0.07, 0.11, 0.12, 0.08, 0.14)]
        t = _table(data, widths, muted_rows=range(1, len(data)) if not row["participates"] else ())
        t.setStyle(TableStyle([("ALIGN", (1, 0), (-1, -1), "RIGHT")]))
        heading = _esc(row["name"]) + f" — {_esc(row['status'])}"
        story.append(KeepTogether([Paragraph(heading, s["h2"]), t]))

    # 3. Customer view
    story.append(PageBreak())
    story += header("Customer view: what the customer is offered (selling prices only)")
    data = [["Included in Brayman Construction scope", "Selling price"]]
    for row in rows:
        if row["participates"]:
            data.append([Paragraph(_esc(row["name"]), s["cell"]), _money(row["sell"])])
    data.append(["Selling price (before tax)", _money(e.get("selling_price"))])
    t = _table(data, [usable * 0.6, usable * 0.2], total=True)
    t.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "RIGHT")]))
    story.append(t)
    excluded = [row for row in rows if row["exclusion_text"]]
    if excluded:
        story.append(Paragraph("Excluded / By Others", s["h2"]))
        data = [["Work", "Responsibility"]] + [[Paragraph(_esc(r["name"]), s["cell"]),
                                                Paragraph(_esc(r["exclusion_text"]), s["cell"])] for r in excluded]
        story.append(_table(data, [usable * 0.35, usable * 0.45]))

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(0.5 * inch, 0.35 * inch, f"{estimate.estimate_number} {version.display_label} · {TITLE}")
        canvas.drawRightString(page_w - 0.5 * inch, 0.35 * inch, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()

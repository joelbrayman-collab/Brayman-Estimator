"""The internal cost estimate as a PDF (Guided Estimating, 23 Oct 2026). ReportLab, like the other office PDFs.

Every page carries INTERNAL — NOT FOR CUSTOMER DISTRIBUTION in its header and footer. It shows the contractor's
confidential costs, rates and supplier prices, so it is an office document only; the customer's document is the
proposal, which never shows them.
"""

from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

RED = colors.HexColor("#b42318")
INK = colors.HexColor("#1c1f24")


def _money(value) -> str:
    try:
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        return str(value or "")


def _qty(value) -> str:
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return str(value or "")


def render_internal_cost_pdf(doc: dict) -> bytes:
    styles = getSampleStyleSheet()
    body = ParagraphStyle("IcBody", parent=styles["Normal"], fontSize=8, leading=10.5, textColor=INK)
    small = ParagraphStyle("IcSmall", parent=body, fontSize=7, leading=9)
    head = ParagraphStyle("IcHead", parent=styles["Heading2"], fontSize=11, spaceBefore=8, spaceAfter=3)
    title = ParagraphStyle("IcTitle", parent=styles["Heading1"], fontSize=15, spaceAfter=2)
    mark = ParagraphStyle("IcMark", parent=body, fontSize=10, textColor=RED, alignment=1, fontName="Helvetica-Bold")
    marking = doc["marking"]
    buffer = BytesIO()

    def frame(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(RED)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawCentredString(letter[0] / 2, letter[1] - 0.45 * inch, marking)
        canvas.drawCentredString(letter[0] / 2, 0.4 * inch, f"{marking} — page {canvas.getPageNumber()}")
        canvas.restoreState()

    pdf = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.7 * inch,
                            title=f"Internal cost estimate — {doc['project'].name}", author="CalibraytAI")
    story = [Paragraph(escape(marking), mark), Spacer(1, 6),
             Paragraph(escape(f"Internal cost estimate — {doc['project'].name}"), title)]
    guided, version = doc["guided"], doc["version"]
    meta = f"{guided.project_type_label} · {guided.contractor_role_label}"
    if version is not None:
        meta += f" · Estimate {guided.estimate.estimate_number} {version.display_label} ({version.status})"
    meta += f" · prepared {doc['generated_at']:%Y-%m-%d %H:%M} UTC"
    story.append(Paragraph(escape(meta), small))
    state = (f"Costing approved (snapshot {doc['snapshot'].id})" if doc["costing_approved"]
             else "DRAFT — the costing is not approved for this version yet.")
    story += [Paragraph(escape(state), body), Spacer(1, 6)]

    totals = doc["totals"]
    rows = [["Materials", _money(totals["material"])],
            [f"Labour ({_qty(totals['labour_hours'])} hours)", _money(totals["labour"])],
            ["Subcontracts", _money(totals["subcontract"])], ["Equipment", _money(totals["equipment"])],
            ["Delivery", _money(totals["delivery"])], ["Allowances", _money(totals["allowance"])],
            ["Other direct costs", _money(totals["other"])], ["Direct cost", _money(doc["direct_cost"])]]
    table = Table(rows, colWidths=[3.2 * inch, 1.6 * inch])
    table.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 8), ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                               ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                               ("LINEABOVE", (0, -1), (-1, -1), 0.5, INK)]))
    story.append(table)
    if doc["blockers"]:
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Missing information</b>", body))
        for blocker in doc["blockers"]:
            story.append(Paragraph(escape("• " + blocker), small))

    for stage in doc["stages"]:
        row = stage["stage"]
        story.append(Paragraph(escape(f"{row.section_name} — {row.responsibility_label} — {stage['status_label']}"),
                               head))
        if row.scope_description:
            story.append(Paragraph(escape("Scope: " + row.scope_description), small))
        if stage["lines"]:
            data = [["Item", "Type", "Qty", "Unit cost", "Cost", "Source"]]
            for line in stage["lines"]:
                item = line["line"]
                data.append([Paragraph(escape(item.description), small), line["bucket"],
                             f"{_qty(item.quantity)} {item.unit}", _money(item.unit_cost), _money(line["amount"]),
                             Paragraph(escape(line["provenance"]), small)])
            lines = Table(data, colWidths=[2.3 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1.8 * inch],
                          repeatRows=1)
            lines.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 7), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                       ("ALIGN", (2, 1), (4, -1), "RIGHT"),
                                       ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK)]))
            story.append(lines)
        if not stage["excluded"]:
            story.append(Paragraph(escape(f"Stage cost {_money(stage['total'])}"), body))
        for issue in stage["issues"]:
            story.append(Paragraph(escape("Missing: " + issue), small))
    story += [Spacer(1, 10), Paragraph(escape(marking), mark)]
    pdf.build(story, onFirstPage=frame, onLaterPages=frame)
    return buffer.getvalue()

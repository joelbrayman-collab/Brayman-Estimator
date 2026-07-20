"""Generate Change Order PDFs with ReportLab Platypus."""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DEFAULT_LOGO_STATIC_PATH = "branding/brayman-construction-logo.png"
DEFAULT_PRIMARY = "#1f3a5f"
DEFAULT_ACCENT = "#c79a2b"
PRODUCT_NAME = "Brayman Construction Platform"


def _static_root() -> Path:
    return Path(current_app.static_folder)


def _money(value) -> str:
    amount = Decimal(str(value if value is not None else 0)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return f"${amount:,.2f}"


def _qty(value) -> str:
    quantity = Decimal(str(value if value is not None else 0))
    text = format(quantity.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _escape(text) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def sanitize_change_order_filename(change_order) -> str:
    number = re.sub(r"[^A-Za-z0-9._-]+", "-", change_order.number or "CO")
    number = number.strip("-._") or "CO"
    label = change_order.project.name if change_order.project else "project"
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-._")
    label = (label or "project")[:60]
    return f"{number}-{label}.pdf"


def _logo_flowable():
    path = _static_root() / DEFAULT_LOGO_STATIC_PATH
    if not path.is_file():
        return None
    try:
        probe = Image(str(path))
        width = float(probe.imageWidth)
        height = float(probe.imageHeight)
        if width <= 0 or height <= 0:
            return None
        scale = min((2.4 * inch) / width, (0.85 * inch) / height, 1.0)
        return Image(str(path), width=width * scale, height=height * scale)
    except Exception:
        return None


def generate_change_order_pdf(change_order) -> BytesIO:
    styles_base = getSampleStyleSheet()
    primary = colors.HexColor(DEFAULT_PRIMARY)
    accent = colors.HexColor(DEFAULT_ACCENT)

    styles = {
        "title": ParagraphStyle(
            "COTitle",
            parent=styles_base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=primary,
            alignment=TA_RIGHT,
        ),
        "meta": ParagraphStyle(
            "COMeta",
            parent=styles_base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#555555"),
            leading=12,
        ),
        "right": ParagraphStyle(
            "CORight",
            parent=styles_base["Normal"],
            fontSize=9,
            alignment=TA_RIGHT,
            leading=12,
        ),
        "heading": ParagraphStyle(
            "COHeading",
            parent=styles_base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=primary,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "COBody",
            parent=styles_base["Normal"],
            fontSize=10,
            leading=14,
        ),
        "label": ParagraphStyle(
            "COLabel",
            parent=styles_base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.HexColor("#666666"),
        ),
        "cell": ParagraphStyle(
            "COCell",
            parent=styles_base["Normal"],
            fontSize=8,
            leading=10,
        ),
        "header_cell": ParagraphStyle(
            "COHeaderCell",
            parent=styles_base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.white,
        ),
        "product": ParagraphStyle(
            "COProduct",
            parent=styles_base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=primary,
        ),
        "center": ParagraphStyle(
            "COCenter",
            parent=styles_base["Normal"],
            fontSize=9,
            alignment=TA_CENTER,
        ),
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.75 * inch,
        title=change_order.title,
        author=PRODUCT_NAME,
    )

    story = []
    logo = _logo_flowable()
    if logo:
        story.append(logo)
        story.append(Spacer(1, 6))

    project = change_order.project
    client = project.client if project else None
    left = [
        Paragraph(PRODUCT_NAME, styles["product"]),
        Paragraph("Change Order", styles["meta"]),
    ]
    if client:
        left.append(Paragraph(f"Customer: {_escape(client.name)}", styles["meta"]))
        if client.company:
            left.append(Paragraph(_escape(client.company), styles["meta"]))
    if project:
        left.append(Paragraph(f"Project: {_escape(project.name)}", styles["meta"]))
        if project.address:
            left.append(Paragraph(_escape(project.address), styles["meta"]))

    right = [
        Paragraph(_escape(change_order.title), styles["title"]),
        Paragraph(_escape(change_order.number), styles["right"]),
        Paragraph(f"Status: {_escape(change_order.status)}", styles["right"]),
    ]
    if change_order.requested_date:
        right.append(
            Paragraph(
                f"Requested: {change_order.requested_date.strftime('%B %d, %Y')}",
                styles["right"],
            )
        )
    if change_order.approved_date:
        right.append(
            Paragraph(
                f"Approved: {change_order.approved_date.strftime('%B %d, %Y')}",
                styles["right"],
            )
        )
    if change_order.estimate_version:
        version = change_order.estimate_version
        right.append(
            Paragraph(
                f"Estimate: {_escape(version.estimate.estimate_number)} / "
                f"{_escape(version.display_label)}",
                styles["right"],
            )
        )

    header = Table(
        [
            [
                Table([[b] for b in left], colWidths=[4.0 * inch]),
                Table([[b] for b in right], colWidths=[3.2 * inch]),
            ]
        ],
        colWidths=[4.0 * inch, 3.2 * inch],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 8))
    story.append(
        HRFlowable(width="100%", thickness=2.5, color=accent, spaceBefore=2, spaceAfter=12)
    )

    if change_order.description:
        story.append(Paragraph("Description", styles["heading"]))
        story.append(Paragraph(_escape(change_order.description), styles["body"]))
    if change_order.reason:
        story.append(Paragraph("Reason", styles["heading"]))
        story.append(Paragraph(_escape(change_order.reason), styles["body"]))

    story.append(Paragraph("Line Items", styles["heading"]))
    story.append(
        HRFlowable(width="100%", thickness=1.5, color=accent, spaceBefore=0, spaceAfter=8)
    )

    table_data = [
        [
            Paragraph("Description", styles["header_cell"]),
            Paragraph("Qty", styles["header_cell"]),
            Paragraph("Unit", styles["header_cell"]),
            Paragraph("Unit Price", styles["header_cell"]),
            Paragraph("Amount", styles["header_cell"]),
        ]
    ]
    if change_order.items:
        for item in change_order.items:
            table_data.append(
                [
                    Paragraph(_escape(item.description), styles["cell"]),
                    Paragraph(_qty(item.quantity), styles["cell"]),
                    Paragraph(_escape(item.unit), styles["cell"]),
                    Paragraph(_money(item.unit_price), styles["cell"]),
                    Paragraph(_money(item.total), styles["cell"]),
                ]
            )
    else:
        table_data.append(
            [
                Paragraph("No line items", styles["cell"]),
                "",
                "",
                "",
                "",
            ]
        )

    items_table = Table(
        table_data,
        colWidths=[3.2 * inch, 0.7 * inch, 0.7 * inch, 1.0 * inch, 1.0 * inch],
        repeatRows=1,
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), primary),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (2, 1), (2, -1), "LEFT"),
            ]
        )
    )
    story.append(items_table)

    totals = Table(
        [
            ["Subtotal", _money(change_order.subtotal)],
            [
                f"Markup ({Decimal(str(change_order.markup_percent)):.2f}%)",
                _money(change_order.markup),
            ],
            [
                f"Tax ({Decimal(str(change_order.tax_percent)):.2f}%)",
                _money(change_order.tax),
            ],
            ["Grand Total", _money(change_order.total)],
        ],
        colWidths=[2.2 * inch, 1.3 * inch],
        hAlign="RIGHT",
    )
    totals.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, -1), (-1, -1), primary),
                ("LINEABOVE", (0, -1), (-1, -1), 1.5, accent),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(Spacer(1, 12))
    story.append(totals)

    if change_order.notes:
        story.append(Paragraph("Notes", styles["heading"]))
        story.append(Paragraph(_escape(change_order.notes), styles["body"]))

    story.append(Spacer(1, 28))
    story.append(Paragraph("Authorization", styles["heading"]))
    sig = Table(
        [
            [
                Paragraph("Owner / Client Signature", styles["label"]),
                Paragraph("Contractor Signature", styles["label"]),
            ],
            [
                Paragraph("<br/><br/>_______________________________<br/>Date ______________", styles["meta"]),
                Paragraph("<br/><br/>_______________________________<br/>Date ______________", styles["meta"]),
            ],
        ],
        colWidths=[3.5 * inch, 3.5 * inch],
    )
    sig.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(sig)

    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(0.7 * inch, 0.4 * inch, change_order.number or "")
        canvas.drawCentredString(letter[0] / 2, 0.4 * inch, f"Page {doc_.page}")
        canvas.drawRightString(letter[0] - 0.7 * inch, 0.4 * inch, PRODUCT_NAME)
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer

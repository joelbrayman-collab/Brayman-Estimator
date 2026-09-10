"""Private QuickBooks-ready PDFs (FG-032). ReportLab; not WeasyPrint."""

from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.supplier_catalogue import contractor_identity

NAVY = colors.HexColor("#1f3a5f")


def _styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "QbTitle",
            parent=styles["Heading1"],
            fontSize=14,
            textColor=NAVY,
            spaceAfter=4,
        ),
        "eyebrow": ParagraphStyle(
            "QbEyebrow",
            parent=styles["Normal"],
            fontSize=8,
            textColor=NAVY,
            leading=10,
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "QbBody",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
        ),
        "small": ParagraphStyle(
            "QbSmall",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#333333"),
        ),
        "warn": ParagraphStyle(
            "QbWarn",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#7a4b00"),
        ),
    }


def _money(value) -> str:
    try:
        return f"${value:,.2f}"
    except (TypeError, ValueError):
        return str(value or "")


def _meta_table(rows, styles):
    data = [
        [
            Paragraph(escape(str(label)), styles["small"]),
            Paragraph(escape(str(value or "—")), styles["body"]),
        ]
        for label, value in rows
    ]
    table = Table(data, colWidths=[1.8 * inch, 5.4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
            ]
        )
    )
    return table


def generate_sales_entry_pdf(package) -> BytesIO:
    """Artifact A. Selling facts only. Family 04 internal entry reference."""
    contractor = contractor_identity(package.organization_id)
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f"QuickBooks Estimate Entry {package.package_number}",
    )
    story = []
    story.append(Paragraph("INTERNAL ENTRY REFERENCE", styles["eyebrow"]))
    story.append(
        Paragraph(
            escape(contractor["customer_facing_name"] or contractor["legal_name"]),
            styles["title"],
        )
    )
    story.append(Paragraph("QUICKBOOKS ESTIMATE / ENTRY SHEET", styles["title"]))
    story.append(
        Paragraph(
            "QuickBooks-ready for manual office entry. Not posted to QuickBooks. "
            "Not an import file. Download does not confirm entry. "
            "Internal office / accounting use only. Not a customer Proposal.",
            styles["small"],
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        _meta_table(
            [
                ("Customer", package.client_name),
                ("Customer company", package.client_company),
                ("Project", package.project_name),
                ("Project number", package.project_number),
                ("Project / billing address", package.project_address),
                ("Estimate number", package.estimate_number),
                ("Estimate version", package.estimate_version_number),
                ("Proposal", package.proposal_number),
                (
                    "Estimate date",
                    package.estimate_date.isoformat() if package.estimate_date else "",
                ),
                ("Tax", package.tax_label or package.tax_jurisdiction),
                ("Tax percent", f"{package.tax_percent}%"),
                ("Customer message", package.customer_message),
                ("Package", package.package_number),
                ("Package status", package.status),
                (
                    "Issue date",
                    package.issued_at.strftime("%Y-%m-%d") if package.issued_at else "",
                ),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 10))
    header = [
        Paragraph("Product/Service", styles["small"]),
        Paragraph("Customer Description", styles["small"]),
        Paragraph("Qty", styles["small"]),
        Paragraph("Unit", styles["small"]),
        Paragraph("Rate", styles["small"]),
        Paragraph("Amount", styles["small"]),
        Paragraph("Tax", styles["small"]),
    ]
    data = [header]
    for line in package.sales_lines:
        data.append(
            [
                Paragraph(escape(line.product_service_label or ""), styles["small"]),
                Paragraph(escape(line.description or ""), styles["small"]),
                Paragraph(escape(str(line.quantity)), styles["small"]),
                Paragraph(escape(line.unit or ""), styles["small"]),
                Paragraph(_money(line.unit_price), styles["small"]),
                Paragraph(_money(line.amount), styles["small"]),
                Paragraph(escape(line.tax_label or ""), styles["small"]),
            ]
        )
    table = Table(
        data,
        colWidths=[
            1.1 * inch,
            2.3 * inch,
            0.6 * inch,
            0.6 * inch,
            0.85 * inch,
            0.9 * inch,
            0.85 * inch,
        ],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c5d0dc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 10))
    story.append(
        _meta_table(
            [
                ("Pre-tax selling total", _money(package.pre_tax)),
                ("Tax amount", _money(package.tax_amount)),
                ("Customer total", _money(package.customer_total)),
                ("Currency", package.currency),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Separately quoted work stays outside this estimate unless listed above. "
            "This sheet is a governed copy of the customer Proposal selling lines "
            "for QuickBooks Estimate typing. It is not attached to the customer PDF.",
            styles["small"],
        )
    )
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_cost_class_pdf(package) -> BytesIO:
    """Artifact B. Planned cost class only. Not a second sales total."""
    contractor = contractor_identity(package.organization_id)
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=f"Planned Cost Classification {package.package_number}",
    )
    story = []
    story.append(Paragraph("INTERNAL / PLANNED COST-CLASSIFICATION", styles["eyebrow"]))
    story.append(
        Paragraph(
            escape(contractor["customer_facing_name"] or contractor["legal_name"]),
            styles["title"],
        )
    )
    story.append(Paragraph("PLANNED COST-CLASSIFICATION COMPANION", styles["title"]))
    story.append(
        Paragraph(
            "Internal office only. Not a customer Proposal. Not a Supplier Package. "
            "Not posted to QuickBooks. Download does not confirm entry. "
            "Approved direct cost classified from frozen FG-031 routing. "
            "This is not a second sales-estimate total.",
            styles["small"],
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        _meta_table(
            [
                ("Project", package.project_name),
                ("Project number", package.project_number),
                ("Estimate", package.estimate_number),
                ("Package", package.package_number),
                ("Package status", package.status),
                ("Costing snapshot", package.costing_snapshot_id),
                ("Pricing snapshot", package.pricing_snapshot_id),
                ("Proposal", package.proposal_number),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 10))
    header = [
        Paragraph("Description", styles["small"]),
        Paragraph("Qty", styles["small"]),
        Paragraph("Unit", styles["small"]),
        Paragraph("Approved cost", styles["small"]),
        Paragraph("Material", styles["small"]),
        Paragraph("Labour", styles["small"]),
        Paragraph("Class", styles["small"]),
        Paragraph("Flags", styles["small"]),
    ]
    data = [header]
    for line in package.cost_class_lines:
        flags = []
        if line.is_hybrid:
            flags.append("HYBRID unsplit")
        if line.is_allowance:
            flags.append("ALLOWANCE")
        data.append(
            [
                Paragraph(escape(line.description or ""), styles["small"]),
                Paragraph(escape(str(line.quantity)), styles["small"]),
                Paragraph(escape(line.unit or ""), styles["small"]),
                Paragraph(_money(line.extended_cost), styles["small"]),
                Paragraph(escape(line.material_procurement or ""), styles["small"]),
                Paragraph(escape(line.labour_delivery or ""), styles["small"]),
                Paragraph(escape(line.planned_class or ""), styles["small"]),
                Paragraph(escape(", ".join(flags)), styles["small"]),
            ]
        )
    table = Table(
        data,
        colWidths=[
            1.9 * inch,
            0.55 * inch,
            0.5 * inch,
            0.95 * inch,
            1.15 * inch,
            0.9 * inch,
            0.85 * inch,
            0.9 * inch,
        ],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efe8dc")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d4c7b0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 10))
    story.append(
        _meta_table(
            [
                (
                    "Approved direct-cost total",
                    _money(package.approved_direct_cost_total),
                ),
                ("Currency", package.currency),
            ],
            styles,
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Hybrid CONTRACTOR_PURCHASED + SUBCONTRACT lines include the one "
            "approved extended cost exactly once. No invented material/labour split. "
            "Allowance lines keep the FG-031 routing exception.",
            styles["small"],
        )
    )
    doc.build(story)
    buffer.seek(0)
    return buffer

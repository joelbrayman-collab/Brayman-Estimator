"""Supplier Package PDF (FG-029). Same frozen facts as HTML. No order side effect."""

from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.supplier_catalogue import contractor_identity, package_readiness_label


def generate_supplier_package_pdf(package) -> BytesIO:
    contractor = contractor_identity(package.organization_id)
    supplier = package.supplier
    location = package.supplier_location
    project = package.project
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"Supplier Package {package.id}",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "SupplierPkgTitle",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#1f3a5f"),
        spaceAfter=6,
    )
    heading = ParagraphStyle(
        "SupplierPkgHeading",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#1f3a5f"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body = ParagraphStyle("SupplierPkgBody", parent=styles["Normal"], fontSize=8, leading=11)
    small = ParagraphStyle(
        "SupplierPkgSmall",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#333333"),
    )
    story = []
    story.append(Paragraph(escape(contractor["product_name"]) + " — Supplier Package", title))
    if package.demo_synthetic:
        story.append(Paragraph("<b>DEMO / SYNTHETIC</b> — not live BMR price, inventory, or API.", small))
    story.append(
        Paragraph(
            "Supplier-facing package. Inform-only price and availability. "
            "Not a submitted purchase order. Not a customer estimate.",
            small,
        )
    )
    story.append(Spacer(1, 8))
    meta = [
        ["Contractor", contractor["customer_facing_name"]],
        ["Project", project.name if project is not None else str(package.project_id)],
        ["Supplier", supplier.legal_name if supplier is not None else str(package.supplier_id)],
        ["Branch", location.display_name if location is not None else str(package.supplier_location_id)],
        ["Package status", package.status],
        ["Readiness", package_readiness_label(package)],
        [
            "Issued",
            package.issued_at.strftime("%Y-%m-%d %H:%M UTC") if package.issued_at else "—",
        ],
        ["Issued by", package.issued_by_display_name or "—"],
    ]
    table = Table(meta, colWidths=[1.6 * inch, 5.4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(table)
    story.append(Paragraph("Package lines", heading))
    header = [
        "Requirement",
        "SKU",
        "Qty / UOM",
        "Pick qty",
        "Price evidence",
        "Availability",
        "Map",
        "Delivery",
    ]
    data = [header]
    unresolved = []
    for line in package.lines:
        if line.mapping_status != "MAPPED":
            unresolved.append(line)
        price = "—"
        if line.price_amount is not None:
            captured = (
                line.price_captured_at.strftime("%Y-%m-%d")
                if line.price_captured_at
                else ""
            )
            price = f"{line.price_currency} {line.price_amount} {line.requirement_uom} {captured}".strip()
        avail = line.availability_status or "—"
        pick = "—"
        if line.sales_qty is not None:
            pick = f"{line.sales_qty} {line.sales_uom or ''}".strip()
        sku = line.supplier_sku or "—"
        if line.demo_synthetic:
            sku = f"{sku} (DEMO)"
        data.append(
            [
                Paragraph(
                    escape(f"{line.canonical_material_code} {line.canonical_material_name}"),
                    body,
                ),
                Paragraph(escape(sku), body),
                Paragraph(escape(f"{line.requirement_qty} {line.requirement_uom}"), body),
                Paragraph(escape(pick), body),
                Paragraph(escape(price), body),
                Paragraph(escape(str(avail)), body),
                Paragraph(escape(line.mapping_status), body),
                Paragraph(escape(line.delivery_stage or "—"), body),
            ]
        )
    lines_table = Table(
        data,
        colWidths=[
            1.5 * inch,
            0.9 * inch,
            0.8 * inch,
            0.8 * inch,
            1.2 * inch,
            0.8 * inch,
            0.8 * inch,
            0.7 * inch,
        ],
    )
    lines_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(lines_table)
    story.append(Paragraph("Unresolved items", heading))
    if unresolved:
        for line in unresolved:
            story.append(
                Paragraph(
                    escape(
                        f"{line.canonical_material_code} — {line.requirement_qty} "
                        f"{line.requirement_uom} — {line.mapping_status}"
                    ),
                    body,
                )
            )
    else:
        story.append(Paragraph("None.", body))
    story.append(Paragraph("Pick / load grouping", heading))
    story.append(
        Paragraph(
            "Grouped by delivery stage, SKU, sales quantity, sales UOM, and branch. "
            "Not fleet, routing, warehouse, or live delivery booking.",
            small,
        )
    )
    doc.build(story)
    buffer.seek(0)
    return buffer

"""Brayman V1 contract presentation.

Renders the frozen agreement already selected by the contract engine.
Does not select a package, change a snapshot, or send a signing link.
"""

from __future__ import annotations

import hashlib
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.brayman_v1_interim_contract import INTERIM_PACKAGE_CODE

BRAYMAN_V1_PRESENTATION_FILENAME = "brayman-v1-contract-presentation.pdf"
BRAYMAN_V1_PRESENTATION_VERSION = "V1"
BRAYMAN_V1_PRESENTATION_STATUS = "BRAYMAN_V1_INTERIM"
BRAYMAN_V1_PRESENTATION_MEDIA_TYPE = "application/pdf"
_PRESENTATION_IDENTITY = (
    "BRAYMAN V1 CONTRACT PRESENTATION V1. "
    "Frozen agreement text. Signature lines are not a signature."
)
BRAYMAN_V1_PRESENTATION_SHA256 = hashlib.sha256(
    _PRESENTATION_IDENTITY.encode("utf-8")
).hexdigest()

PRIMARY = colors.HexColor("#1f3a5f")
ACCENT = colors.HexColor("#c79a2b")
RULE = colors.HexColor("#d7deE6")


def brayman_v1_presentation_master() -> dict:
    return {
        "family_code": "05",
        "version": BRAYMAN_V1_PRESENTATION_VERSION,
        "filename": BRAYMAN_V1_PRESENTATION_FILENAME,
        "sha256": BRAYMAN_V1_PRESENTATION_SHA256,
        "legal_status": BRAYMAN_V1_PRESENTATION_STATUS,
    }


def _escape(value) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _document_title(package_code: str) -> str:
    if package_code == INTERIM_PACKAGE_CODE:
        return "BRAYMAN V1 INTERIM CONTRACT"
    return "BRAYMAN V1 CONTRACT"


def render_brayman_v1_contract_pdf(
    *,
    commercial: dict,
    legal_objects: list,
    package_code: str,
    package_version,
    effective_from: str,
    contract_number: str,
) -> bytes:
    """Letter PDF of the frozen contract. Generated is not signed."""
    title = _document_title(package_code)
    owner = str(commercial.get("client_name") or "").strip()
    project = str(commercial.get("project_name") or "").strip()
    site = str(commercial.get("site") or commercial.get("project_address") or "").strip()
    amount = str(commercial.get("total") or "").strip()
    contract_date = str(commercial.get("contract_date") or "").strip()
    provision = ""
    warranty = ""
    for item in legal_objects:
        kind = item.get("kind")
        body = (item.get("body") or "").strip()
        if kind == "contract_provision" and body:
            provision = body
        elif kind == "warranty" and body:
            warranty = body

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.68 * inch,
        title=title,
        author="Brayman Construction",
    )
    title_style = ParagraphStyle(
        "V1ContractTitle",
        fontName="Times-Bold",
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        alignment=TA_LEFT,
        spaceAfter=2,
    )
    kicker = ParagraphStyle(
        "V1ContractKicker",
        fontName="Times-Bold",
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=2,
        spaceAfter=8,
    )
    label = ParagraphStyle(
        "V1ContractLabel",
        fontName="Times-Bold",
        fontSize=10,
        leading=13,
        textColor=PRIMARY,
    )
    value = ParagraphStyle(
        "V1ContractValue",
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
    )
    body = ParagraphStyle(
        "V1ContractBody",
        fontName="Times-Roman",
        fontSize=11,
        leading=15,
        spaceAfter=6,
    )
    section = ParagraphStyle(
        "V1ContractSection",
        fontName="Times-Bold",
        fontSize=12,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=8,
        spaceAfter=6,
    )
    sign_label = ParagraphStyle(
        "V1ContractSignLabel",
        fontName="Times-Bold",
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=4,
        spaceAfter=2,
    )

    def _paint(canvas, doc):
        canvas.saveState()
        width, height = letter
        canvas.setFillColor(PRIMARY)
        canvas.rect(0, height - 0.38 * inch, width, 0.38 * inch, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Times-Roman", 9)
        canvas.drawString(0.75 * inch, height - 0.24 * inch, "Brayman Construction")
        canvas.drawRightString(width - 0.75 * inch, height - 0.24 * inch, "Contract / Agreement")
        canvas.setFillColor(ACCENT)
        canvas.rect(0, 0.46 * inch, width, 2.5, fill=1, stroke=0)
        canvas.setFillColor(PRIMARY)
        canvas.setFont("Times-Roman", 9)
        canvas.drawString(0.75 * inch, 0.26 * inch, title)
        canvas.drawRightString(width - 0.75 * inch, 0.26 * inch, f"Page {doc.page}")
        canvas.restoreState()

    facts = [
        ("Contract", contract_number),
        ("Owner", owner),
        ("Project", project),
        ("Site", site),
        ("Contract amount", amount),
        ("Package", package_code),
        ("Version", str(package_version or "")),
        ("Effective date", effective_from),
        ("Date", contract_date),
        ("Jurisdiction", "Ontario"),
        ("Status", "Generated"),
    ]
    fact_rows = [
        [
            Paragraph(_escape(name), label),
            Paragraph(_escape(shown), value),
        ]
        for name, shown in facts
        if shown
    ]
    fact_table = Table(fact_rows, colWidths=[1.7 * inch, 5.3 * inch])
    fact_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -2), 0.25, RULE),
            ]
        )
    )

    story = [
        Paragraph(_escape(title), title_style),
        Paragraph("Contract / Agreement", kicker),
        HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=10),
        fact_table,
        Spacer(1, 12),
        Paragraph("Agreement", section),
    ]
    for line in provision.splitlines():
        cleaned = line.strip()
        if not cleaned:
            story.append(Spacer(1, 4))
            continue
        story.append(Paragraph(_escape(cleaned), body))
    if warranty:
        story.append(Paragraph("Warranty", section))
        for line in warranty.splitlines():
            cleaned = line.strip()
            if not cleaned:
                story.append(Spacer(1, 4))
                continue
            story.append(Paragraph(_escape(cleaned), body))

    signature = [
        Paragraph("Signatures", section),
        Paragraph(
            "This contract is generated. It is not signed. "
            "A signature, when it is used, is a separate signing step.",
            body,
        ),
        Spacer(1, 8),
        Paragraph("Owner", sign_label),
        Paragraph(f"Name: {_escape(owner)}", value),
        Spacer(1, 16),
        Paragraph("Signature ________________________________", value),
        Spacer(1, 10),
        Paragraph("Date ________________________________", value),
        Spacer(1, 14),
        Paragraph("Contractor", sign_label),
        Paragraph("Name: Brayman Construction Inc.", value),
        Spacer(1, 16),
        Paragraph("Signature ________________________________", value),
        Spacer(1, 10),
        Paragraph("Date ________________________________", value),
    ]
    story.append(KeepTogether(signature))
    document.build(story, onFirstPage=_paint, onLaterPages=_paint)
    return buffer.getvalue()

"""Assemble a SIGN-C executed PDF from an immutable pre-sign PDF plus an audit page.

Does not re-render the commercial document. The executed SHA is not printed on
the audit page (circular). Raw tokens and internal database ids are omitted.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Optional

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.signing import DOCUMENT_FAMILY_CHANGE_ORDER, ROLE_CUSTOMER


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


def _format_utc(value: Optional[datetime]) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")


def _audit_page_pdf(*, rows: list[tuple[str, str]], is_synthetic: bool) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="Signing completion record",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "SignCTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "SignCBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
    )
    label = ParagraphStyle(
        "SignCLabel",
        parent=body,
        fontName="Helvetica-Bold",
    )
    flowables = [
        Paragraph("Signing completion record", title),
        Paragraph(
            "This page is appended to the frozen pre-sign document. "
            "The commercial pages above were not re-rendered.",
            body,
        ),
        Spacer(1, 10),
    ]
    if is_synthetic:
        flowables.append(
            Paragraph(
                "SYNTHETIC / TECHNICAL UAT ONLY. NOT FOR EXECUTION. NOT A CUSTOMER SEND.",
                body,
            )
        )
        flowables.append(Spacer(1, 10))
    table_data = [
        [Paragraph(_escape(name), label), Paragraph(_escape(value) or "—", body)]
        for name, value in rows
    ]
    table = Table(table_data, colWidths=[2.3 * inch, 4.6 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    flowables.append(table)
    document.build(flowables)
    return buffer.getvalue()


def assemble_executed_pdf(
    frozen_pdf_bytes: bytes,
    request,
    *,
    document_reference: str,
    executed_at: datetime,
) -> bytes:
    """Return new executed PDF bytes. Caller retains them separately from the freeze."""
    if not frozen_pdf_bytes:
        raise ValueError("Frozen pre-sign PDF is empty.")
    customer = next(
        (row for row in request.participants if row.role == ROLE_CUSTOMER),
        None,
    )
    consent = request.consent_version
    family = request.document_family or ""
    source_label = "Change Order" if family == DOCUMENT_FAMILY_CHANGE_ORDER else "Contract"
    rows = [
        ("Signing request", request.request_number or ""),
        ("Document family", family),
        ("Document reference", document_reference or request.request_number or ""),
        ("Source kind", source_label),
        ("Pre-sign SHA-256", request.frozen_artifact.sha256 if request.frozen_artifact else ""),
        (
            "Customer signer name",
            (customer.confirmed_signer_name if customer else "") or "",
        ),
        ("Customer signer email", (customer.invited_email if customer else "") or ""),
        ("Customer signed at", _format_utc(customer.signed_at if customer else None)),
        ("Consent version", consent.version_code if consent else ""),
        (
            "Customer IP",
            (customer.completion_ip if customer else "") or "",
        ),
        (
            "Customer user-agent",
            (customer.user_agent if customer else "") or "",
        ),
    ]
    if request.countersign_required:
        rows.extend(
            [
                (
                    "Organization countersigner",
                    request.countersigned_by_identifier or "",
                ),
                ("Countersigned at", _format_utc(request.countersigned_at)),
            ]
        )
    else:
        rows.append(("Organization countersign", "Not required"))
    rows.append(("Executed at", _format_utc(executed_at)))
    audit_bytes = _audit_page_pdf(
        rows=rows,
        is_synthetic=(request.authority_class or "") == "SYNTHETIC_UAT",
    )
    writer = PdfWriter()
    for page in PdfReader(BytesIO(frozen_pdf_bytes)).pages:
        writer.add_page(page)
    for page in PdfReader(BytesIO(audit_bytes)).pages:
        writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()

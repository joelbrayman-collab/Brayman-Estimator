"""Neutral CalibAi Permit & Approvals Report PDF (FG-016). Same snapshot as HTML."""

from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.permit_intelligence import ADVISORY_AUTHORITY_LANGUAGE, PermitAnalysis


def generate_permit_report_pdf(analysis: PermitAnalysis) -> BytesIO:
    """Render the pinned analysis. No Brayman logo. No Brand Profile."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=f"Permit & Approvals Report v{analysis.version_number}",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "PermitTitle",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#1f3a5f"),
        spaceAfter=6,
    )
    heading = ParagraphStyle(
        "PermitHeading",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#1f3a5f"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body = ParagraphStyle("PermitBody", parent=styles["Normal"], fontSize=9, leading=12)
    small = ParagraphStyle(
        "PermitSmall",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#333333"),
    )
    story = []
    story.append(Paragraph("CalibAi — Permit &amp; Approvals Report", title))
    story.append(Paragraph("ADVISORY ONLY — not AHJ approval", small))
    story.append(Spacer(1, 8))
    meta = [
        ["Project", str(analysis.project.name if analysis.project else analysis.project_id)],
        ["Report version", str(analysis.version_number)],
        ["Generated", analysis.generated_at.strftime("%Y-%m-%d %H:%M UTC") if analysis.generated_at else ""],
        [
            "Location",
            ", ".join(
                part
                for part in (
                    analysis.street_snapshot,
                    analysis.municipality_snapshot,
                    analysis.province_state_snapshot,
                    analysis.country_snapshot,
                )
                if part
            )
            or "—",
        ],
        ["Jurisdiction", analysis.resolved_jurisdiction_name or "unresolved"],
        ["Permit context", analysis.permit_context_class or "—"],
        ["Coverage", analysis.coverage_status],
        [
            "Plan / site basis",
            analysis.plan_revision_label
            or analysis.plan_document_names
            or analysis.site_plan_identity
            or "not identified",
        ],
    ]
    table = Table(meta, colWidths=[1.6 * inch, 5.2 * inch])
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
    story.append(Paragraph("Authority", heading))
    story.append(Paragraph(ADVISORY_AUTHORITY_LANGUAGE, body))
    story.append(Paragraph("Checks / findings", heading))
    for finding in analysis.findings:
        topic = escape(finding.topic or "")
        status = escape((finding.status or "").replace("_", " "))
        story.append(Paragraph(f"<b>{topic}</b> — {status}", body))
        if finding.requirement_snapshot:
            story.append(
                Paragraph(f"Requirement: {escape(finding.requirement_snapshot)}", small)
            )
        if finding.evidence_snapshot:
            story.append(Paragraph(f"Evidence: {escape(finding.evidence_snapshot)}", small))
        story.append(Paragraph(escape(finding.explanation or ""), small))
        story.append(Paragraph(f"Action: {escape(finding.recommended_action or '')}", small))
        if finding.citation_snapshot:
            story.append(Paragraph(f"Source: {escape(finding.citation_snapshot)}", small))
        story.append(Spacer(1, 6))
    story.append(Paragraph("Disclaimer", heading))
    story.append(Paragraph(ADVISORY_AUTHORITY_LANGUAGE, small))
    doc.build(story)
    buffer.seek(0)
    return buffer

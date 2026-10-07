"""Letter sheets for screens a contractor would carry on paper.

The caller passes the facts already on the screen. This module does not
read the database and does not keep a second copy of those facts.
"""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.presentation import contractor_copy


def render_fact_sheet(title: str, sections: list[tuple[str, list[str]]]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=title,
    )
    styles = getSampleStyleSheet()
    heading = ParagraphStyle(
        "DeskPrintHeading",
        parent=styles["Heading1"],
        fontName="Times-Bold",
        fontSize=16,
        leading=20,
        spaceAfter=8,
    )
    section = ParagraphStyle(
        "DeskPrintSection",
        parent=styles["Heading2"],
        fontName="Times-Bold",
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "DeskPrintBody",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=11,
        leading=14,
    )

    def _footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Times-Roman", 9)
        canvas.drawString(0.75 * inch, 0.45 * inch, f"Page {document.page}")
        canvas.restoreState()

    story = [Paragraph(_escape(title), heading), Spacer(1, 6)]
    for name, lines in sections:
        story.append(Paragraph(_escape(name), section))
        if not lines:
            story.append(Paragraph("—", body))
            continue
        for line in lines:
            story.append(Paragraph(_escape(line), body))
    story.append(Spacer(1, 8))
    story.append(Paragraph(_escape(contractor_copy.PRINT_LABEL), body))
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def _escape(value: str) -> str:
    return (
        (value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

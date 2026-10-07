"""Draw the V1 operator pack on the approved Brayman page.

Reads the markdown in this folder. Writes portrait letter PDFs beside it.
Does not open the office database.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)

# Same Brayman page identity as the approved supplier estimate request.
PRIMARY = colors.HexColor("#1f3a5f")
ACCENT = colors.HexColor("#c79a2b")
COMPANY = "Brayman Construction"
LEGAL = "Brayman Construction Inc."
OFFICE = "411 St. John Street, Merrickville, Ontario K0G 1N0"


def _logo() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        current = parent / (
            "instance/brand_logos/ORG-001/"
            "948f96e08827f18d77b47538f65c8b98b45caaf9c981adccba0189976948efe9.png"
        )
        fallback = parent / "app/static/branding/brayman-construction-logo.png"
        if current.is_file():
            return current
        if fallback.is_file():
            return fallback
    return None

HERE = Path(__file__).resolve().parent
PAGES = (
    ("v1-operator-recovery-guide.md", "v1-operator-recovery-guide.pdf", False),
    ("v1-first-day-checklist.md", "v1-first-day-checklist.pdf", True),
    ("v1-backup-restore-checklist.md", "v1-backup-restore-checklist.pdf", True),
)

_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _inline(text: str) -> str:
    plain = text.strip().replace("`", "")
    escaped = html.escape(plain)
    return _BOLD.sub(r"<b>\1</b>", escaped)


def _styles(compact: bool) -> dict:
    body_size = 10 if compact else 11
    leading = 13 if compact else 14
    return {
        "h1": ParagraphStyle(
            "op-h1",
            fontName="Times-Bold",
            fontSize=16 if compact else 18,
            leading=20,
            textColor=PRIMARY,
            spaceAfter=4,
        ),
        "h2": ParagraphStyle(
            "op-h2",
            fontName="Times-Bold",
            fontSize=12 if compact else 13,
            leading=16,
            textColor=PRIMARY,
            spaceBefore=8,
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "op-body",
            fontName="Times-Roman",
            fontSize=body_size,
            leading=leading,
            textColor=PRIMARY,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "code": ParagraphStyle(
            "op-code",
            fontName="Times-Roman",
            fontSize=8,
            leading=10,
            textColor=PRIMARY,
            leftIndent=8,
            spaceAfter=2,
        ),
    }


def _story(markdown: str, compact: bool):
    styles = _styles(compact)
    story = []
    bullet = []
    code = []

    def flush_bullet():
        if not bullet:
            return
        items = [
            ListItem(Paragraph(_inline(line), styles["body"]), leftIndent=12)
            for line in bullet
        ]
        story.append(
            ListFlowable(
                items,
                bulletType="bullet",
                start="•",
                leftIndent=14,
                bulletFontName="Times-Roman",
                bulletFontSize=styles["body"].fontSize,
                spaceBefore=0,
                spaceAfter=4,
            )
        )
        bullet.clear()

    def flush_code():
        if not code:
            return
        story.append(Preformatted("\n".join(code), styles["code"]))
        story.append(Spacer(1, 4))
        code.clear()

    in_code = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_bullet()
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not line.strip():
            flush_bullet()
            continue
        if line.startswith("# "):
            flush_bullet()
            story.append(Paragraph(_inline(line[2:]), styles["h1"]))
            continue
        if line.startswith("## "):
            flush_bullet()
            story.append(Paragraph(_inline(line[3:]), styles["h2"]))
            continue
        if line.startswith("- "):
            bullet.append(line[2:])
            continue
        flush_bullet()
        story.append(Paragraph(_inline(line), styles["body"]))
    flush_bullet()
    flush_code()
    return story


def _paint(canvas, doc):
    canvas.saveState()
    width, height = letter
    logo = _logo()
    if logo is not None:
        canvas.drawImage(
            str(logo),
            0.65 * inch,
            height - 0.72 * inch,
            width=0.42 * inch,
            height=0.42 * inch,
            mask="auto",
            preserveAspectRatio=True,
        )
    canvas.setFillColor(PRIMARY)
    canvas.setFont("Times-Bold", 11)
    canvas.drawString(1.2 * inch, height - 0.48 * inch, COMPANY)
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(1.2 * inch, height - 0.62 * inch, f"{LEGAL}  ·  {OFFICE}")
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(2)
    canvas.line(0.65 * inch, height - 0.78 * inch, width - 0.65 * inch, height - 0.78 * inch)
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, 0, width, 0.42 * inch, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0.42 * inch, width, 2, fill=1, stroke=0)
    canvas.setFillColor(PRIMARY)
    canvas.setFillColorRGB(1, 1, 1)
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(0.65 * inch, 0.18 * inch, "Calibrayt office guide  ·  not a contract")
    canvas.drawRightString(width - 0.65 * inch, 0.18 * inch, f"Page {doc.page}")
    canvas.restoreState()


def render_pack(folder: Path | None = None) -> list[Path]:
    target = folder or HERE
    written = []
    for source_name, pdf_name, compact in PAGES:
        source = (HERE / source_name).read_text(encoding="utf-8")
        pdf_path = target / pdf_name
        frame_top = 0.95 * inch
        frame_bottom = 0.62 * inch
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            leftMargin=0.65 * inch,
            rightMargin=0.65 * inch,
            topMargin=frame_top,
            bottomMargin=frame_bottom,
            title=source_name.replace(".md", "").replace("-", " "),
            author=COMPANY,
        )
        doc.build(_story(source, compact), onFirstPage=_paint, onLaterPages=_paint)
        written.append(pdf_path)
    return written


if __name__ == "__main__":
    for path in render_pack():
        print(path)

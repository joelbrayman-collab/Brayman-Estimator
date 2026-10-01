"""Interim J1 PDFs that use the governed Brayman identity.

This is not a second document architecture. Colours and the logo path are the
same fallback named in app/services/proposal_pdf.py and
app/services/brand_profile.py. The ORG-001 CURRENT logo file is preferred.
A later platform renderer replaces this script.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from issue_j1 import brand_logo_path

PRIMARY = colors.HexColor("#1f3a5f")
ACCENT = colors.HexColor("#c79a2b")
RULE = colors.HexColor("#d9d3c7")
HEAD = colors.HexColor("#f4efe6")
CASE = Path(__file__).resolve().parents[1]
COMPANY = "Brayman Construction"
LEGAL = "Brayman Construction Inc."
ADDRESS = "411 St. John Street, Merrickville, Ontario K0G 1N0"


def _styles():
    return {
        "h1": ParagraphStyle("h1", fontName="Times-Bold", fontSize=14, leading=18, textColor=PRIMARY, spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName="Times-Bold", fontSize=12, leading=15, textColor=PRIMARY, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", fontName="Times-Roman", fontSize=10, leading=13, spaceAfter=3),
        "cell": ParagraphStyle("cell", fontName="Times-Roman", fontSize=8, leading=10),
        "headcell": ParagraphStyle("headcell", fontName="Times-Bold", fontSize=8, leading=10, textColor=colors.white),
    }


def _clean(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("`", "")


def _parse_table(lines, index, sheet_styles):
    rows = []
    while index < len(lines) and lines[index].startswith("|"):
        cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
        if not all(set(cell) <= set("-: ") and cell for cell in cells):
            rows.append(cells)
        index += 1
    if not rows:
        return index, None
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    data = []
    for row_index, row in enumerate(rows):
        style = sheet_styles["headcell"] if row_index == 0 else sheet_styles["cell"]
        data.append([Paragraph(_clean(cell) or " ", style) for cell in row])
    return index, data


def _on_page(canvas, doc, document_title: str, status: str) -> None:
    canvas.saveState()
    page_w, page_h = doc.pagesize
    logo = brand_logo_path()
    text_x = 0.6 * inch
    if logo is not None:
        canvas.drawImage(str(logo), 0.55 * inch, page_h - 0.72 * inch, width=70, height=28, mask="auto", preserveAspectRatio=True, anchor="sw")
        text_x = 1.6 * inch
    canvas.setFillColor(PRIMARY)
    canvas.setFont("Times-Bold", 11)
    canvas.drawString(text_x, page_h - 0.42 * inch, COMPANY)
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(text_x, page_h - 0.56 * inch, LEGAL)
    canvas.drawString(text_x, page_h - 0.68 * inch, ADDRESS)
    canvas.setFont("Times-Bold", 10)
    canvas.drawRightString(page_w - 0.55 * inch, page_h - 0.42 * inch, document_title)
    canvas.setFont("Times-Roman", 8)
    canvas.drawRightString(page_w - 0.55 * inch, page_h - 0.58 * inch, status)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(2)
    canvas.line(0.55 * inch, page_h - 0.82 * inch, page_w - 0.55 * inch, page_h - 0.82 * inch)
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, 0, page_w, 0.38 * inch, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Times-Roman", 8)
    canvas.drawString(0.55 * inch, 0.16 * inch, "Linda Bushel  ·  12 D'Arcy's Way, Kemptville, ON K0G 1J0  ·  Issue J1  ·  2026-10-01")
    canvas.drawRightString(page_w - 0.55 * inch, 0.16 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build(md_path: Path, pdf_path: Path, document_title: str, status: str, pagesize=letter) -> None:
    sheet_styles = _styles()
    lines = md_path.read_text(encoding="utf-8").splitlines()
    story = []
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        if not line.strip():
            index += 1
            continue
        if line.startswith("|"):
            index, data = _parse_table(lines, index, sheet_styles)
            if data:
                usable = pagesize[0] - 1.2 * inch
                column = usable / len(data[0])
                table = Table(data, colWidths=[column] * len(data[0]), repeatRows=1)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                    ("GRID", (0, 0), (-1, -1), 0.3, RULE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]))
                story.append(table)
                story.append(Spacer(1, 8))
            continue
        if line.startswith("# "):
            story.append(Paragraph(_clean(line[2:]), sheet_styles["h1"]))
        elif line.startswith("## "):
            story.append(Paragraph(_clean(line[3:]), sheet_styles["h2"]))
        elif line.startswith("- "):
            story.append(Paragraph("•  " + _clean(line[2:]), sheet_styles["body"]))
        else:
            story.append(Paragraph(_clean(line), sheet_styles["body"]))
        index += 1
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=pagesize,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=1.05 * inch,
        bottomMargin=0.55 * inch,
        title=document_title,
        author=COMPANY,
    )
    document.build(story, onFirstPage=lambda c, d: _on_page(c, d, document_title, status), onLaterPages=lambda c, d: _on_page(c, d, document_title, status))


def write_issue_pdfs() -> list[Path]:
    jobs = [
        (CASE / "takeoff/2026-10-01-j1-material-takeoff.md", CASE / "takeoff/2026-10-01-j1-material-takeoff.pdf", "MATERIAL TAKE-OFF", "Preliminary. Not a price.", letter),
        (CASE / "estimates/internal/2026-10-01-j1-ben-internal-cost.md", CASE / "estimates/internal/2026-10-01-j1-ben-internal-cost.pdf", "INTERNAL DETAILED COST", "INTERNAL / FOR BEN. Not a customer document.", letter),
        (CASE / "supplier/bmr-winchester/2026-10-01-j1-darcy-request-for-quotation.md", CASE / "supplier/bmr-winchester/2026-10-01-j1-darcy-request-for-quotation.pdf", "REQUEST FOR QUOTATION", "Not a quotation received. Awaiting Darcy.", landscape(letter)),
        (CASE / "estimates/customer/2026-10-01-j1-preliminary-customer-estimate.md", CASE / "estimates/customer/2026-10-01-j1-preliminary-customer-estimate.pdf", "CONSTRUCTION ESTIMATE", "PRELIMINARY / BUDGET ESTIMATE. SELLING PRICE NOT ISSUED.", letter),
    ]
    written = []
    for source, destination, title, status, pagesize in jobs:
        build(source, destination, title, status, pagesize)
        written.append(destination)
    return written


def write_desktop_package() -> Path:
    desk = Path("/Users/joelbrayman/Desktop/LINDA_BUSHEL_POOL_DECK_J1")
    if desk.exists():
        shutil.rmtree(desk)
    mapping = {
        "DRAWINGS/2026-10-01-j1-preliminary-11x17.pdf": CASE / "drawings/2026-10-01-j1-preliminary-11x17.pdf",
        "TAKEOFF/Linda-Bushel-J1-material-takeoff.pdf": CASE / "takeoff/2026-10-01-j1-material-takeoff.pdf",
        "ESTIMATE/Linda-Bushel-J1-internal-cost-FOR-BEN.pdf": CASE / "estimates/internal/2026-10-01-j1-ben-internal-cost.pdf",
        "SUPPLIER/Linda-Bushel-J1-BMR-request-for-quotation.pdf": CASE / "supplier/bmr-winchester/2026-10-01-j1-darcy-request-for-quotation.pdf",
        "CUSTOMER/Linda-Bushel-J1-preliminary-customer-estimate.pdf": CASE / "estimates/customer/2026-10-01-j1-preliminary-customer-estimate.pdf",
    }
    for relative, source in mapping.items():
        target = desk / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    readme = Path("/tmp/bushel-branded-readme.md")
    readme.write_text(
        "\n".join([
            "# Linda Bushel — Pool Deck",
            "",
            "Issue J1. 1 Oct 2026.",
            "",
            "Every file in this folder is a PDF. Open it in Preview.",
            "",
            "Identity: Brayman Construction. Organization Brand Profile ORG-001.",
            "",
            "DRAWINGS — preliminary 11 by 17 set. Not a permit approval.",
            "",
            "TAKEOFF — quantities. Not a price.",
            "",
            "ESTIMATE — internal cost for Ben. Not a customer document.",
            "",
            "SUPPLIER — request for quotation for Darcy. Not a quotation received.",
            "",
            "CUSTOMER — construction estimate draft. Selling price is not issued.",
            "",
            "Foundations are 15 helical piers. No sonotubes and no concrete.",
        ]),
        encoding="utf-8",
    )
    build(readme, desk / "README.pdf", "PACKAGE INDEX", "Preliminary. Selling price not issued.", letter)
    zip_path = Path("/Users/joelbrayman/Desktop/LINDA_BUSHEL_POOL_DECK_J1_BEN_PACKAGE.zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(desk.rglob("*.pdf")):
            archive.write(path, Path("LINDA_BUSHEL_POOL_DECK_J1") / path.relative_to(desk))
    case_zip = CASE / "delivery/LINDA_BUSHEL_POOL_DECK_J1_BEN_PACKAGE.zip"
    case_zip.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(zip_path, case_zip)
    return zip_path


if __name__ == "__main__":
    for path in write_issue_pdfs():
        print(f"wrote {path}")
    print(f"package {write_desktop_package()}")

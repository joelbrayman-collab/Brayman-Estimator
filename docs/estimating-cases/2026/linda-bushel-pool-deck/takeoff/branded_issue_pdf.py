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


def _on_page(canvas, doc, document_title: str, status: str, footer_date: str = "1 Oct 2026") -> None:
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
    canvas.drawString(0.55 * inch, 0.16 * inch, f"Linda Bushel  ·  12 D'Arcy's Way, Kemptville, ON K0G 1J0  ·  {footer_date}")
    canvas.drawRightString(page_w - 0.55 * inch, 0.16 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build(md_path: Path, pdf_path: Path, document_title: str, status: str, pagesize=letter, footer_date: str = "1 Oct 2026") -> None:
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
    document.build(
        story,
        onFirstPage=lambda c, d: _on_page(c, d, document_title, status, footer_date),
        onLaterPages=lambda c, d: _on_page(c, d, document_title, status, footer_date),
    )


COST_REQUEST_ROWS = (
    ("1", "Helical pier. Shaft, helix, length, torque, and capacity are not chosen.", "15"),
    ("2", "Helical-pier bracket, unless the pier price includes it.", "15"),
    ("3", "PT 6×6 × 8 ft. Lower posts are ordered uncut.", "11"),
    ("4", "Post-to-beam connector. Brand is not chosen.", "15"),
    ("5", "PT 2×10 × 10 ft", "4"),
    ("6", "PT 2×10 × 12 ft", "7"),
    ("7", "PT 2×8 × 12 ft", "20"),
    ("8", "PT 2×12 × 8 ft stringer stock", "10"),
    ("9", "Trex composite deck board × 20 ft. Upper deck, cut to 18 ft. One row ripped to 5 in width. Colour and product line are not chosen.", "11"),
    ("10", "Trex composite deck board × 10 ft. Lower deck, stair treads, and pieces beside the pool. Colour and product line are not chosen. Say if this length is not sold.", "17"),
    ("11", "Trex composite deck board × 8 ft. Shorter pieces beside the pool. Colour and product line are not chosen. Say if this length is not sold.", "7"),
    ("12", "Trex fascia. Upper sides 10.092 ft each, upper front returns 4 ft each, lower sides 3 ft each, lower front 10 ft. The open pool edge has no fascia. The stair stringer faces have no fascia. Colour, width, and stock length are not chosen.", "44.184 ft"),
    ("13", "PT 1×6 × 8 ft skirt", "5"),
    ("14", "Veranda 37 in × 6 ft, matching the named look. The Home Depot number is not a confirmed BMR item.", "10 kits"),
    ("15", "Custom stair guards. These are not a 6 ft kit.", "2"),
    ("16", "PT 4×4 × 8 ft guard posts", "14"),
    ("17", "Gate, 42 in clear", "1"),
    ("18", "Gate latch, and hinges. Latch count is 1. Hinge count is not stated.", "Latch 1"),
    ("19", "Stitch bolts, nuts, and washers. 76 bolts, 76 nuts, 152 washers. Diameter is not chosen. Count is for pricing, not an engineered layout.", "76 / 76 / 152"),
    ("20", "Header connectors. Brand is not chosen.", "16"),
    ("21", "Stringer connectors. Brand is not chosen.", "10"),
    ("22", "Structural screws", "100"),
    ("23", "Fasteners for the Trex boards. The count is two fasteners at each board crossing. The Trex fastener is not chosen.", "798"),
    ("24", "Labour for this deck. No hours are on file. State the hours and the rate, or one labour amount.", ""),
    ("25", "Equipment. None is listed. Name each item and its cost, or write none.", ""),
    ("26", "Delivery to 12 D'Arcy's Way, Kemptville, ON K0G 1J0", ""),
    ("27", "Disposal", ""),
    ("28", "Permit fees. The customer estimate excludes them. Say whether Brayman pays them.", ""),
)


def write_ben_cost_request() -> Path:
    """Fillable price sheet for Ben. Quantities are the 1 Oct J1 issue. No dollar is filled in."""
    from reportlab.pdfgen.canvas import Canvas

    destination = CASE / "estimates/internal/2026-10-06-ben-items-that-need-a-cost.pdf"
    destination.parent.mkdir(parents=True, exist_ok=True)
    page_w, page_h = landscape(letter)
    form = Canvas(str(destination), pagesize=landscape(letter))
    form.acroForm.extras["NeedAppearances"] = True
    form.setTitle("Linda Bushel — items that need a cost")
    form.setAuthor(COMPANY)

    left = 0.45 * inch
    columns = {
        "no": left,
        "item": left + 0.38 * inch,
        "qty": left + 5.55 * inch,
        "unit": left + 6.45 * inch,
        "line": left + 7.55 * inch,
        "note": left + 8.65 * inch,
    }
    widths = {
        "no": 0.38 * inch,
        "item": 5.17 * inch,
        "qty": 0.9 * inch,
        "unit": 1.1 * inch,
        "line": 1.1 * inch,
        "note": page_w - 0.45 * inch - (left + 8.65 * inch),
    }
    item_style = ParagraphStyle("item", fontName="Times-Roman", fontSize=8, leading=10, textColor=colors.black)
    small = ParagraphStyle("small", fontName="Times-Roman", fontSize=8, leading=10, textColor=PRIMARY)
    title = "ITEMS THAT NEED A COST"
    status = "For Ben. Type in the boxes and send this PDF back."
    footer = "6 Oct 2026"

    class _Page:
        pagesize = landscape(letter)
        page = 1

    page = _Page()

    def paint_chrome():
        _on_page(form, page, title, status, footer)

    def paint_columns(top):
        labels = (("no", "No."), ("item", "Item"), ("qty", "Qty"), ("unit", "Unit price"), ("line", "Line price"), ("note", "Note"))
        form.setFillColor(PRIMARY)
        form.rect(left, top - 16, page_w - 0.9 * inch, 16, fill=1, stroke=0)
        form.setFillColor(colors.white)
        form.setFont("Times-Bold", 8)
        for key, label in labels:
            form.drawString(columns[key] + 2, top - 12, label)
        return top - 16

    def start_page(first):
        paint_chrome()
        top = page_h - 0.98 * inch
        if first:
            intro = [
                "Linda Bushel — items that need a cost. For Ben only. Not a customer document.",
                "Quantities are the 1 Oct 2026 preliminary issue: 15 helical piers, 16 joist lines, 10 stringers. No sonotubes and no concrete. The walking surface and the stair treads are Trex. Fascia is added on the exposed rim.",
                "Type in the boxes. Save this PDF and send it back. A blank is not zero. No price on this sheet was filled in for you.",
                "No extra waste percentage is added. Leftover length stays on the cut lists and is not deducted from these quantities.",
            ]
            for line in intro:
                block = Paragraph(_clean(line), small)
                _, height = block.wrap(page_w - 0.9 * inch, 40)
                block.drawOn(form, left, top - height)
                top -= height + 2
            top -= 6
        return paint_columns(top)

    cursor = start_page(True)
    bottom = 0.85 * inch
    for number, item, qty in COST_REQUEST_ROWS:
        block = Paragraph(_clean(item), item_style)
        _, text_h = block.wrap(widths["item"] - 6, 80)
        row_h = max(18, text_h + 6)
        if cursor - row_h < bottom:
            form.showPage()
            page.page += 1
            cursor = start_page(False)
        row_bottom = cursor - row_h
        if int(number) % 2 == 0:
            form.setFillColor(HEAD)
            form.rect(left, row_bottom, page_w - 0.9 * inch, row_h, fill=1, stroke=0)
        form.setStrokeColor(RULE)
        form.setLineWidth(0.3)
        form.rect(left, row_bottom, page_w - 0.9 * inch, row_h, fill=0, stroke=1)
        form.setFillColor(colors.black)
        form.setFont("Times-Roman", 8)
        form.drawString(columns["no"] + 2, row_bottom + 4, number)
        block.drawOn(form, columns["item"] + 2, row_bottom + 3)
        form.drawString(columns["qty"] + 2, row_bottom + 4, qty)
        field_h = max(12, row_h - 4)
        field_y = row_bottom + 2
        for key, prefix in (("unit", "unit_price"), ("line", "line_price"), ("note", "note")):
            form.acroForm.textfield(
                name=f"{prefix}_{int(number):02d}",
                tooltip=f"{prefix.replace('_', ' ')} for item {number}",
                x=columns[key] + 1,
                y=field_y,
                width=widths[key] - 2,
                height=field_h,
                borderWidth=0.6,
                borderColor=PRIMARY,
                fillColor=colors.Color(1, 0.98, 0.92),
                textColor=colors.black,
                forceBorder=True,
                fontName="Times-Roman",
                fontSize=8,
                maxlen=160 if key == "note" else 24,
                fieldFlags="multiline" if key == "note" else "",
            )
        cursor = row_bottom

    sign_h = 22
    if cursor - sign_h - 8 < bottom:
        form.showPage()
        page.page += 1
        paint_chrome()
        cursor = page_h - 0.98 * inch
    cursor -= 10
    form.setFillColor(PRIMARY)
    form.setFont("Times-Roman", 9)
    form.drawString(left, cursor - 14, "Priced by")
    form.drawString(left + 3.2 * inch, cursor - 14, "Date")
    form.acroForm.textfield(
        name="priced_by",
        tooltip="Your name",
        x=left + 0.7 * inch,
        y=cursor - 18,
        width=2.2 * inch,
        height=16,
        borderWidth=0.6,
        borderColor=PRIMARY,
        fillColor=colors.Color(1, 0.98, 0.92),
        textColor=colors.black,
        forceBorder=True,
        fontName="Times-Roman",
        fontSize=9,
        maxlen=80,
    )
    form.acroForm.textfield(
        name="priced_on",
        tooltip="Date you priced this sheet",
        x=left + 3.6 * inch,
        y=cursor - 18,
        width=1.4 * inch,
        height=16,
        borderWidth=0.6,
        borderColor=PRIMARY,
        fillColor=colors.Color(1, 0.98, 0.92),
        textColor=colors.black,
        forceBorder=True,
        fontName="Times-Roman",
        fontSize=9,
        maxlen=20,
    )
    form.save()
    desktop = Path("/Users/joelbrayman/Desktop/Linda-Bushel-items-that-need-a-cost.pdf")
    shutil.copyfile(destination, desktop)
    return destination


def write_issue_pdfs() -> list[Path]:
    jobs = [
        (CASE / "takeoff/2026-10-01-j1-material-takeoff.md", CASE / "takeoff/2026-10-01-j1-material-takeoff.pdf", "MATERIAL TAKE-OFF", "Preliminary. Not a price.", letter),
        (CASE / "estimates/internal/2026-10-01-j1-ben-internal-cost.md", CASE / "estimates/internal/2026-10-01-j1-ben-internal-cost.pdf", "COST SHEET FOR BEN", "For Ben only. Not a customer document.", letter),
        (CASE / "supplier/bmr-winchester/2026-10-01-j1-darcy-request-for-quotation.md", CASE / "supplier/bmr-winchester/2026-10-01-j1-darcy-request-for-quotation.pdf", "REQUEST FOR A PRICE", "Not a quotation. Not yet sent to Darcy.", landscape(letter)),
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
            "1 Oct 2026. Preliminary set.",
            "",
            "Every file in this folder is a PDF. Open it in Preview.",
            "",
            "DRAWINGS — 11 by 17 set. Not a permit.",
            "",
            "TAKEOFF — quantities. Not a price.",
            "",
            "ESTIMATE — cost sheet for Ben. Not a customer document.",
            "",
            "SUPPLIER — request for a price from Darcy. Not a quotation.",
            "",
            "CUSTOMER — estimate draft. The selling price is not issued.",
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

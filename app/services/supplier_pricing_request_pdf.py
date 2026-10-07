"""Fillable PDF for one job-specific supplier pricing request.

Manual transport only. No portal, no email send, and no price is written
into the commercial records.
"""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.pdfgen.canvas import Canvas

from app.services.supplier_pricing_request import (
    CONTRACTOR_INPUT_LABEL,
    PUBLIC_PRICE_NOT_AVAILABLE,
    SOURCE_GAP_LABEL,
    SUPPLIER_AVAILABILITY_LABEL,
    SUPPLIER_PRICING_LABEL,
    SUPPLIER_PRODUCT_LABEL,
)

NAVY = HexColor("#1f3a5f")
RULE = HexColor("#c5ced8")
CREAM = Color(1, 0.98, 0.93)
INK = HexColor("#1c1c1c")
MUTED = HexColor("#3d4a57")

PAGE_W, PAGE_H = letter
LEFT = 0.55 * inch
RIGHT = 0.55 * inch
TOP = 0.48 * inch
BOTTOM = 0.46 * inch
CONTENT_W = PAGE_W - LEFT - RIGHT


def render_supplier_pricing_request_pdf(request: dict) -> bytes:
    buffer = BytesIO()
    form = Canvas(buffer, pagesize=letter)
    form.acroForm.extras["NeedAppearances"] = True
    form.setTitle(f"{request['project_name']} — supplier pricing request")
    form.setAuthor("Brayman Construction")
    state = {"page": 1, "cursor": 0.0}
    _start_page(form, request, state, first=True)
    _intro(form, request, state)
    current_category = None
    for line in request["lines"]:
        heading = 22 if line["category"] != current_category else 0
        card_h = _card_height(line)
        _ensure(form, request, state, heading + card_h + 8)
        if heading:
            current_category = line["category"]
            state["cursor"] -= 16
            form.setFillColor(NAVY)
            form.setFont("Times-Bold", 11)
            form.drawString(LEFT, state["cursor"], current_category)
            state["cursor"] -= 6
        _item_card(form, request, state, line, card_h)
    _contractor_section(form, request, state)
    form.save()
    return buffer.getvalue()


def _start_page(form, request, state, first):
    if not first:
        form.showPage()
        state["page"] += 1
    form.setFillColor(NAVY)
    form.rect(0, PAGE_H - 32, PAGE_W, 32, fill=1, stroke=0)
    form.setFillColor(white)
    form.setFont("Times-Bold", 11)
    form.drawString(LEFT, PAGE_H - 21, "Supplier pricing request")
    form.setFont("Times-Roman", 8)
    form.drawRightString(PAGE_W - RIGHT, PAGE_H - 20, request["issued_on"])
    form.setFillColor(MUTED)
    form.setFont("Times-Roman", 8)
    form.drawString(LEFT, 18, f"{request['project_name']}  ·  {request['supplier_name']}")
    form.drawRightString(PAGE_W - RIGHT, 18, f"Page {state['page']}")
    form.setStrokeColor(RULE)
    form.setLineWidth(0.4)
    form.line(LEFT, 30, PAGE_W - RIGHT, 30)
    state["cursor"] = PAGE_H - TOP - 28


def _ensure(form, request, state, height):
    if state["cursor"] - height < BOTTOM + 8:
        _start_page(form, request, state, first=False)


def _paragraph(text, size=8.5, leading=11, color=INK, bold=False):
    style = ParagraphStyle(
        "req",
        fontName="Times-Bold" if bold else "Times-Roman",
        fontSize=size,
        leading=leading,
        textColor=color,
    )
    return Paragraph(_xml(text), style)


def _draw_paragraph(form, text, x, y, width, size=8.5, leading=11, color=INK, bold=False):
    block = _paragraph(text, size, leading, color, bold)
    _, height = block.wrap(width, 400)
    block.drawOn(form, x, y - height)
    return height


def _intro(form, request, state):
    state["cursor"] -= _draw_paragraph(
        form,
        request["project_name"],
        LEFT,
        state["cursor"],
        CONTENT_W,
        size=14,
        leading=17,
        color=NAVY,
        bold=True,
    )
    state["cursor"] -= 4
    for line in (
        request["address"],
        f"Supplier: {request['supplier_name']}",
        "Brayman Construction. Not a purchase order. Not a customer price.",
    ):
        state["cursor"] -= _draw_paragraph(form, line, LEFT, state["cursor"], CONTENT_W, size=9, leading=12)
        state["cursor"] -= 1
    state["cursor"] -= 8
    for line in (
        "Here is what we know. Here is what remains unresolved.",
        "Here is what we need from Brayman. Here is what we need from BMR.",
        "BMR names the product, the SKU, availability, and the current contractor price. "
        "BMR does not perform the takeoff, does not set Brayman's quantities, and does not approve Brayman's cost.",
        "A member count or a location count is not a purchase quantity. A blank is not zero.",
        request["authority"],
    ):
        height = _draw_paragraph(form, line, LEFT, state["cursor"], CONTENT_W)
        state["cursor"] -= height + 3
    state["cursor"] -= 4
    state["cursor"] -= _draw_paragraph(
        form,
        "Account pricing — supplementary",
        LEFT,
        state["cursor"],
        CONTENT_W,
        size=10,
        leading=13,
        color=NAVY,
        bold=True,
    )
    state["cursor"] -= 4
    state["cursor"] -= _draw_paragraph(
        form,
        "Use this only for the Brayman account at BMR Winchester. The item lines below are the response for this job.",
        LEFT,
        state["cursor"],
        CONTENT_W,
    )
    state["cursor"] -= 8
    field_w = (CONTENT_W - 12) / 2
    fields = request["account_fields"]
    for row in range(0, len(fields), 2):
        _ensure(form, request, state, 36)
        pair = fields[row:row + 2]
        for index, (key, label) in enumerate(pair):
            x = LEFT + index * (field_w + 12)
            form.setFillColor(MUTED)
            form.setFont("Times-Roman", 8)
            form.drawString(x, state["cursor"] - 10, label)
            _field(
                form,
                name=f"account_{key}",
                tooltip=label,
                x=x,
                y=state["cursor"] - 32,
                width=field_w,
                height=18,
            )
        state["cursor"] -= 40
    state["cursor"] -= 6
    legend = (
        f"{CONTRACTOR_INPUT_LABEL}: Brayman still confirms a project fact. "
        f"{SUPPLIER_PRODUCT_LABEL}: BMR names the product and SKU. "
        f"{SUPPLIER_PRICING_LABEL}: BMR gives the current contractor price. "
        f"{SUPPLIER_AVAILABILITY_LABEL}: BMR states availability. "
        f"{SOURCE_GAP_LABEL}: the material or the source fact is not stored. "
        f"{PUBLIC_PRICE_NOT_AVAILABLE} means no public price is on file. "
        "A public price is not the contractor price."
    )
    height = _draw_paragraph(form, legend, LEFT, state["cursor"], CONTENT_W, size=8, leading=10, color=MUTED)
    state["cursor"] -= height + 8


def _card_height(line) -> float:
    spec_h = _paragraph(line["specification"], size=8.5, leading=11).wrap(CONTENT_W - 16, 300)[1]
    status_text = "  ·  ".join(line["statuses"])
    status_h = _paragraph(status_text, size=8, leading=10, bold=True).wrap(CONTENT_W - 16, 200)[1]
    bmr_h = _paragraph("BMR: " + line["bmr_action"], size=8, leading=10).wrap(CONTENT_W - 16, 200)[1]
    return 16 + 14 + spec_h + 36 + status_h + bmr_h + 86


def _item_card(form, request, state, line, card_h):
    header_h = 16
    status_text = "  ·  ".join(line["statuses"])
    top = state["cursor"]
    bottom = top - card_h
    form.setStrokeColor(RULE)
    form.setLineWidth(0.6)
    form.setFillColor(Color(0.97, 0.98, 0.99))
    form.roundRect(LEFT, bottom, CONTENT_W, card_h, 4, fill=1, stroke=1)
    form.setFillColor(NAVY)
    form.rect(LEFT, top - header_h, CONTENT_W, header_h, fill=1, stroke=0)
    form.setFillColor(white)
    form.setFont("Times-Bold", 9)
    form.drawString(LEFT + 8, top - 12, f"{line['category']}  —  {line['title']}")
    y = top - header_h - 12
    form.setFillColor(INK)
    form.setFont("Times-Roman", 8.5)
    form.drawString(LEFT + 8, y, f"Material: {line['material']}")
    y -= 4
    y -= _draw_paragraph(form, line["specification"], LEFT + 8, y, CONTENT_W - 16, size=8.5, leading=11)
    y -= 12
    form.setFont("Times-Roman", 8.5)
    form.setFillColor(INK)
    form.drawString(LEFT + 8, y, f"Known count: {line['quantity']}    Unit: {line['unit']}")
    y -= 11
    form.setFillColor(MUTED)
    form.setFont("Times-Italic", 8)
    form.drawString(LEFT + 8, y, line["count_note"][:110])
    y -= 12
    form.setFillColor(INK)
    form.setFont("Times-Roman", 8.5)
    form.drawString(LEFT + 8, y, line["public_price_label"][:140])
    y -= 4
    y -= _draw_paragraph(form, status_text, LEFT + 8, y, CONTENT_W - 16, size=8, leading=10, color=NAVY, bold=True)
    y -= 3
    y -= _draw_paragraph(form, "BMR: " + line["bmr_action"], LEFT + 8, y, CONTENT_W - 16, size=8, leading=10)
    y -= 8
    _response_fields(form, line, LEFT + 8, y, CONTENT_W - 16)
    state["cursor"] = bottom - 8


def _response_fields(form, line, x, y, width):
    fields = line["response_fields"]
    gap = 6
    columns = 4
    field_w = (width - gap * (columns - 1)) / columns
    form.setFillColor(MUTED)
    form.setFont("Times-Roman", 7)
    for index, (key, label) in enumerate(fields):
        column = index % columns
        row = index // columns
        fx = x + column * (field_w + gap)
        label_y = y - row * 36
        form.drawString(fx, label_y, label)
        _field(
            form,
            name=f"{line['subject']}_{key}",
            tooltip=f"{line['title']}: {label}",
            x=fx,
            y=label_y - 22,
            width=field_w,
            height=14,
        )


def _contractor_section(form, request, state):
    _ensure(form, request, state, 78)
    top = state["cursor"]
    form.setFillColor(NAVY)
    form.rect(LEFT, top - 16, CONTENT_W, 16, fill=1, stroke=0)
    form.setFillColor(white)
    form.setFont("Times-Bold", 9)
    form.drawString(LEFT + 8, top - 12, "BRAYMAN INFORMATION REQUIRED")
    state["cursor"] = top - 22
    intro = (
        "This section is for Brayman. Darcy does not answer these questions. "
        "They are not mixed with the BMR price fields above."
    )
    state["cursor"] -= _draw_paragraph(form, intro, LEFT, state["cursor"], CONTENT_W, size=9, leading=12)
    state["cursor"] -= 6
    for question in request["contractor_questions"]:
        height = _paragraph(question, size=8.5, leading=11).wrap(CONTENT_W - 12, 120)[1] + 4
        if state["cursor"] - (height + 2) < BOTTOM + 8:
            _start_page(form, request, state, first=False)
            form.setFillColor(NAVY)
            form.setFont("Times-Bold", 9)
            form.drawString(LEFT, state["cursor"], "Brayman information required, continued")
            state["cursor"] -= 16
        state["cursor"] -= _draw_paragraph(
            form,
            "• " + question,
            LEFT + 4,
            state["cursor"],
            CONTENT_W - 8,
            size=8.5,
            leading=11,
        )
        state["cursor"] -= 3


def _field(form, *, name, tooltip, x, y, width, height):
    form.acroForm.textfield(
        name=name,
        tooltip=tooltip,
        x=x,
        y=y,
        width=width,
        height=height,
        borderWidth=0.6,
        borderColor=NAVY,
        fillColor=CREAM,
        textColor=INK,
        forceBorder=True,
        fontName="Times-Roman",
        fontSize=8,
        maxlen=180,
    )


def _xml(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

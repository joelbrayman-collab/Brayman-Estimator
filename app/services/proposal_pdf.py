"""Generate client-facing proposal PDFs from snapshot data via ReportLab Platypus."""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.brand_profile import (
    brand_logo_filesystem_path,
    get_proposal_brand_render_context,
)

DEFAULT_LOGO_STATIC_PATH = "branding/brayman-construction-logo.png"
DEFAULT_PRIMARY_COLOR = "#1f3a5f"
DEFAULT_ACCENT_COLOR = "#c79a2b"
MAX_LOGO_BYTES = 5 * 1024 * 1024
SUPPORTED_LOGO_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif"}


def _static_root() -> Path:
    return Path(current_app.static_folder)


def default_logo_filesystem_path() -> Path:
    return _static_root() / DEFAULT_LOGO_STATIC_PATH


def _is_safe_relative_static_path(value: str) -> bool:
    if not value or value.startswith(("http://", "https://", "/")):
        return False
    if ".." in Path(value).parts:
        return False
    return True


def resolve_logo_filesystem_path(logo_path: str | None) -> Path | None:
    """Resolve a readable local logo path for PDF embedding.

    Prefers a valid template logo under the static folder, then the default
    Brayman branding asset. Never follows remote URLs.
    """
    candidates: list[Path] = []

    if logo_path:
        value = logo_path.strip()
        if value and _is_safe_relative_static_path(value):
            candidates.append((_static_root() / value).resolve())

    candidates.append(default_logo_filesystem_path().resolve())

    static_root = _static_root().resolve()
    for path in candidates:
        try:
            path.relative_to(static_root)
        except ValueError:
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_LOGO_SUFFIXES:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size <= 0 or size > MAX_LOGO_BYTES:
            continue
        try:
            with path.open("rb") as handle:
                handle.read(16)
        except OSError:
            continue
        return path
    return None


def resolve_preview_logo_url(logo_path: str | None, url_for) -> str | None:
    """Browser preview logo URL with template override and default fallback."""
    if logo_path:
        value = logo_path.strip()
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith("/"):
            return value
        if _is_safe_relative_static_path(value):
            candidate = (_static_root() / value).resolve()
            try:
                candidate.relative_to(_static_root().resolve())
            except ValueError:
                pass
            else:
                if (
                    candidate.is_file()
                    and candidate.suffix.lower() in SUPPORTED_LOGO_SUFFIXES
                ):
                    try:
                        if 0 < candidate.stat().st_size <= MAX_LOGO_BYTES:
                            return url_for("static", filename=value)
                    except OSError:
                        pass

    default_path = default_logo_filesystem_path()
    if default_path.is_file():
        return url_for("static", filename=DEFAULT_LOGO_STATIC_PATH)
    return None


def _money(value) -> str:
    amount = Decimal(str(value if value is not None else 0)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return f"${amount:,.2f}"


def _qty(value) -> str:
    quantity = Decimal(str(value if value is not None else 0))
    text = format(quantity.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _percent(value) -> str:
    amount = Decimal(str(value if value is not None else 0)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return f"{amount:.2f}%"


def _parse_color(value: str | None, default: str) -> colors.Color:
    raw = (value or "").strip() or default
    if not raw.startswith("#"):
        raw = f"#{raw}"
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", raw):
        raw = default
    return colors.HexColor(raw)


def _escape(text: str | None) -> str:
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def sanitize_pdf_filename(proposal) -> str:
    number = re.sub(r"[^A-Za-z0-9._-]+", "-", proposal.proposal_number or "PROP")
    number = number.strip("-._") or "PROP"
    label = proposal.client_name or proposal.project_name or "proposal"
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-._")
    label = (label or "proposal")[:60]
    return f"{number}-{label}.pdf"


def _visible_line_items(proposal, section):
    items = []
    for item in section.line_items:
        if proposal.show_allowances or item.item_type != "Allowance":
            items.append(item)
    return items


def _build_styles(primary, accent):
    base = getSampleStyleSheet()
    styles = {
        "company": ParagraphStyle(
            "ProposalCompany",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=primary,
            spaceAfter=4,
        ),
        "meta": ParagraphStyle(
            "ProposalMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#555555"),
            leading=12,
        ),
        "title": ParagraphStyle(
            "ProposalTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=primary,
            spaceAfter=4,
            alignment=TA_RIGHT,
        ),
        "right_meta": ParagraphStyle(
            "ProposalRightMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#333333"),
            alignment=TA_RIGHT,
            leading=12,
        ),
        "label": ParagraphStyle(
            "ProposalLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.HexColor("#666666"),
            spaceBefore=2,
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "ProposalBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#222222"),
        ),
        "heading": ParagraphStyle(
            "ProposalHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=primary,
            spaceBefore=14,
            spaceAfter=6,
            borderPadding=2,
        ),
        "section_title": ParagraphStyle(
            "ProposalSectionTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=primary,
            spaceBefore=8,
            spaceAfter=2,
        ),
        "table_cell": ParagraphStyle(
            "ProposalTableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
        ),
        "table_header": ParagraphStyle(
            "ProposalTableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.white,
            leading=10,
        ),
        "footer": ParagraphStyle(
            "ProposalFooter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#666666"),
        ),
    }
    styles["accent"] = accent
    return styles


def _logo_flowable(logo_path: Path | None):
    if logo_path is None:
        return None
    try:
        probe = Image(str(logo_path))
        width = float(probe.imageWidth)
        height = float(probe.imageHeight)
    except Exception:
        return None
    max_width = 2.4 * inch
    max_height = 0.85 * inch
    if width <= 0 or height <= 0:
        return None
    scale = min(max_width / width, max_height / height, 1.0)
    try:
        return Image(
            str(logo_path),
            width=width * scale,
            height=height * scale,
        )
    except Exception:
        return None


def _narrative_block(title, text, styles):
    if not text or not str(text).strip():
        return None
    return KeepTogether(
        [
            Paragraph(title, styles["heading"]),
            HRFlowable(
                width="100%",
                thickness=1.5,
                color=styles["accent"],
                spaceBefore=0,
                spaceAfter=6,
            ),
            Paragraph(_escape(text), styles["body"]),
        ]
    )


def _pricing_table(items, styles, *, detailed: bool):
    if detailed:
        headers = ["Description", "Qty", "Unit", "Unit Price", "Amount"]
        col_widths = [3.2 * inch, 0.7 * inch, 0.7 * inch, 1.0 * inch, 1.0 * inch]
    else:
        headers = ["Description", "Qty", "Unit"]
        col_widths = [5.0 * inch, 0.9 * inch, 0.9 * inch]

    data = [
        [Paragraph(_escape(header), styles["table_header"]) for header in headers]
    ]
    for item in items:
        description = _escape(item.description)
        if item.item_type == "Allowance":
            description = f"{description} (Allowance)"
        if item.notes:
            description = f"{description}<br/><font color='#666666'>{_escape(item.notes)}</font>"
        row = [
            Paragraph(description, styles["table_cell"]),
            Paragraph(_qty(item.quantity), styles["table_cell"]),
            Paragraph(_escape(item.unit), styles["table_cell"]),
        ]
        if detailed:
            row.extend(
                [
                    Paragraph(_money(item.unit_price), styles["table_cell"]),
                    Paragraph(_money(item.extended_price), styles["table_cell"]),
                ]
            )
        data.append(row)

    table = Table(data, colWidths=col_widths, repeatRows=1)
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), styles["_primary"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
    ]
    if detailed:
        style_commands.append(("ALIGN", (3, 1), (-1, -1), "RIGHT"))
    table.setStyle(TableStyle(style_commands))
    return table


def generate_proposal_pdf(proposal) -> BytesIO:
    """Build a PDF for ``proposal`` using snapshot values only."""
    brand = get_proposal_brand_render_context(proposal)
    primary = _parse_color(brand.primary_color, DEFAULT_PRIMARY_COLOR)
    accent = _parse_color(brand.accent_color, DEFAULT_ACCENT_COLOR)
    styles = _build_styles(primary, accent)
    styles["_primary"] = primary

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.75 * inch,
        title=proposal.title or proposal.proposal_number,
        author=brand.customer_facing_name or "Brayman Construction Platform",
    )

    story = []
    logo = _logo_flowable(brand_logo_filesystem_path(brand))
    if logo is not None:
        story.append(logo)
        story.append(Spacer(1, 6))

    company_lines = []
    if brand.customer_facing_name:
        company_lines.append(
            Paragraph(_escape(brand.customer_facing_name), styles["company"])
        )
    contact_bits = []
    for value in (
        brand.address,
        brand.phone,
        brand.email,
        brand.website,
    ):
        if value:
            contact_bits.append(_escape(value))
    if contact_bits:
        company_lines.append(Paragraph("<br/>".join(contact_bits), styles["meta"]))

    created = (
        proposal.created_at.strftime("%B %d, %Y")
        if proposal.created_at
        else "—"
    )
    valid_until = (
        proposal.valid_until.strftime("%B %d, %Y")
        if proposal.valid_until
        else "—"
    )
    right_block = [
        Paragraph(_escape(proposal.title), styles["title"]),
        Paragraph(_escape(proposal.proposal_number), styles["right_meta"]),
        Paragraph(f"Status: {_escape(proposal.status)}", styles["right_meta"]),
        Paragraph(f"Date: {_escape(created)}", styles["right_meta"]),
        Paragraph(f"Valid until: {_escape(valid_until)}", styles["right_meta"]),
    ]

    left_block = company_lines or [Paragraph("&nbsp;", styles["body"])]
    left_inner = Table([[item] for item in left_block], colWidths=[4.0 * inch])
    left_inner.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    right_inner = Table([[item] for item in right_block], colWidths=[3.2 * inch])
    right_inner.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ]
        )
    )

    header_table = Table(
        [[left_inner, right_inner]],
        colWidths=[4.0 * inch, 3.2 * inch],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 8))
    story.append(
        HRFlowable(
            width="100%",
            thickness=2.5,
            color=accent,
            spaceBefore=2,
            spaceAfter=12,
        )
    )

    client_lines = [Paragraph("CLIENT", styles["label"])]
    client_lines.append(Paragraph(_escape(proposal.client_name), styles["body"]))
    if proposal.client_company:
        client_lines.append(Paragraph(_escape(proposal.client_company), styles["body"]))
    for value in (
        proposal.client_address,
        proposal.client_email,
        proposal.client_phone,
    ):
        if value:
            client_lines.append(Paragraph(_escape(value), styles["meta"]))

    project_lines = [Paragraph("PROJECT", styles["label"])]
    project_lines.append(Paragraph(_escape(proposal.project_name), styles["body"]))
    if proposal.project_address:
        project_lines.append(Paragraph(_escape(proposal.project_address), styles["meta"]))

    estimate_ref = f"{proposal.estimate_number} / v{proposal.estimate_version_number}"
    if proposal.estimate_version_label:
        estimate_ref = f"{estimate_ref} — {proposal.estimate_version_label}"
    project_lines.append(Paragraph("ESTIMATE REFERENCE", styles["label"]))
    project_lines.append(Paragraph(_escape(estimate_ref), styles["meta"]))

    client_inner = Table([[item] for item in client_lines], colWidths=[3.6 * inch])
    client_inner.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    project_inner = Table([[item] for item in project_lines], colWidths=[3.6 * inch])
    project_inner.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    info_table = Table(
        [[client_inner, project_inner]],
        colWidths=[3.6 * inch, 3.6 * inch],
    )
    info_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(info_table)

    for title, field in (
        ("Introduction", proposal.intro_text),
        ("Scope of Work", proposal.scope_intro),
    ):
        block = _narrative_block(title, field, styles)
        if block is not None:
            story.append(block)

    story.append(Paragraph("Proposal Pricing", styles["heading"]))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=accent,
            spaceBefore=0,
            spaceAfter=8,
        )
    )

    if not proposal.sections:
        story.append(Paragraph("No pricing sections on this proposal.", styles["meta"]))
    else:
        for section in proposal.sections:
            items = _visible_line_items(proposal, section)
            section_bits = [
                Paragraph(_escape(section.name), styles["section_title"]),
            ]
            if section.description:
                section_bits.append(
                    Paragraph(_escape(section.description), styles["meta"])
                )
            if proposal.show_section_totals:
                section_bits.append(
                    Paragraph(
                        f"Section total: {_money(section.subtotal)}",
                        styles["body"],
                    )
                )
            if items:
                section_bits.append(Spacer(1, 4))
                section_bits.append(
                    _pricing_table(
                        items,
                        styles,
                        detailed=bool(proposal.show_detailed_pricing),
                    )
                )
            story.append(KeepTogether(section_bits))
            story.append(Spacer(1, 10))

    totals_data = [
        ["Subtotal", _money(proposal.subtotal)],
    ]
    if proposal.show_tax:
        totals_data.append(
            [
                f"Tax ({_percent(proposal.tax_percent)})",
                _money(proposal.tax_amount),
            ]
        )
    totals_data.append(["Grand Total", _money(proposal.total)])

    totals_table = Table(totals_data, colWidths=[2.2 * inch, 1.3 * inch], hAlign="RIGHT")
    totals_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TEXTCOLOR", (0, -1), (-1, -1), primary),
                ("LINEABOVE", (0, -1), (-1, -1), 1.5, accent),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(totals_table)

    for title, field in (
        ("Clarifications", proposal.clarifications),
        ("Exclusions", proposal.exclusions),
        ("Schedule", proposal.schedule_text),
        ("Payment Terms", proposal.payment_terms),
        ("Warranty", proposal.warranty_text),
        ("Acceptance", proposal.acceptance_text),
    ):
        block = _narrative_block(title, field, styles)
        if block is not None:
            story.append(block)

    company_name = brand.customer_facing_name or ""

    def _add_page_number(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        page_label = f"Page {doc_.page}"
        left = proposal.proposal_number or ""
        right = company_name
        canvas.drawString(0.7 * inch, 0.4 * inch, left)
        canvas.drawCentredString(letter[0] / 2, 0.4 * inch, page_label)
        canvas.drawRightString(letter[0] - 0.7 * inch, 0.4 * inch, right)
        canvas.restoreState()

    doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    buffer.seek(0)
    return buffer

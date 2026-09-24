"""FG-039 Results PDF renderer.

Formats an already-calculated assessment result. Does not recalculate economics.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.business_owner_assessment import (
    FALLBACK_SCENARIO_TITLE,
    PRODUCT_NAME,
    resolved_scenario_title,
)

LOGO_V2 = (
    Path(__file__).resolve().parents[1] / "static" / "branding" / "calibraytai-logo-v2.png"
)
NAVY = colors.HexColor("#141414")
GOLD = colors.HexColor("#c79a2b")
MUTED = colors.HexColor("#6b6f76")
CREAM = colors.HexColor("#f4f2ee")
ZERO = Decimal("0")

COVER_DESCRIPTION = (
    "This analysis compares employment and entrepreneurship economics using the "
    "assumptions entered by the user. It is a decision-support analysis, not a "
    "recommendation."
)
ASSUMPTIONS_NOTE = (
    "Results depend on the assumptions entered. This analysis does not predict "
    "business success. Tax consequences are not calculated. The tool does not "
    "recommend employment or entrepreneurship."
)


def generate_assessment_pdf(result, *, calculation_date=None) -> BytesIO:
    """Render the already-computed assessment result. Do not recompute economics."""
    if not isinstance(result, dict):
        raise TypeError("PDF renderer requires the assessment result object")
    calc_date = _iso_date(calculation_date) or date.today().isoformat()
    inputs = result.get("inputs") or {}
    title = resolved_scenario_title(inputs.get("scenario_name"))
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.7 * inch,
        title=f"CalibraytAI — {title}",
        author="CalibraytAI",
    )
    styles = _styles()
    story = []
    logo = _logo_flowable()
    if logo is not None:
        story.append(logo)
        story.append(Spacer(1, 8))
    story.append(Paragraph("CalibraytAI", styles["kicker"]))
    story.append(Paragraph(escape(PRODUCT_NAME), styles["title"]))
    story.append(Paragraph(escape(title), styles["scenario"]))
    story.append(Paragraph(f"Calculation date: {escape(calc_date)}", styles["meta"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(escape(COVER_DESCRIPTION), styles["body"]))
    story.append(Spacer(1, 10))

    story.extend(_employment_block(result, styles))
    story.extend(_business_block(result, styles))
    story.extend(_startup_block(result, styles))
    story.extend(_results_block(result, styles))
    story.extend(_stress_block(result, styles))
    story.extend(_truth_block(result, styles))
    story.append(Paragraph("Assumptions / note", styles["heading"]))
    story.append(Paragraph(escape(ASSUMPTIONS_NOTE), styles["small"]))
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer


def assessment_pdf_filename(scenario_name, calculation_date):
    date_part = _iso_date(calculation_date) or date.today().isoformat()
    slug = _filename_slug(scenario_name)
    if slug:
        return f"CalibraytAI_Employment_vs_Entrepreneurship_{slug}_{date_part}.pdf"
    return f"CalibraytAI_Employment_vs_Entrepreneurship_{date_part}.pdf"


def format_money(value):
    parsed = _decimal(value)
    if parsed is None:
        return "—"
    sign = "-" if parsed < ZERO else ""
    return f"{sign}${abs(parsed):,.2f}"


def format_hours(value):
    parsed = _decimal(value)
    if parsed is None:
        return "—"
    return f"{parsed:,.2f} hours"


def format_percent(value):
    parsed = _decimal(value)
    if parsed is None:
        return "—"
    return f"{parsed:,.2f}%"


def format_weeks(value):
    parsed = _decimal(value)
    if parsed is None:
        return "—"
    return f"{parsed:,.2f}"


def format_count(value):
    parsed = _decimal(value)
    if parsed is None:
        return "—"
    return str(int(parsed))


def _iso_date(value):
    if value is None or value == "":
        return None
    text = str(value).strip()[:10]
    try:
        date.fromisoformat(text)
    except ValueError:
        return None
    return text


def _filename_slug(scenario_name):
    text = resolved_scenario_title(scenario_name)
    provided = "" if scenario_name is None else str(scenario_name).strip()
    if text == FALLBACK_SCENARIO_TITLE and not provided:
        return ""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return slug[:40]


def _decimal(value):
    if value is None or value == "":
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, ArithmeticError):
        return None
    if not parsed.is_finite():
        return None
    return parsed


def _positive(value):
    parsed = _decimal(value)
    return parsed is not None and parsed > ZERO


def _styles():
    base = getSampleStyleSheet()
    return {
        "kicker": ParagraphStyle(
            "BoaKicker",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=GOLD,
            spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "BoaTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=NAVY,
            spaceAfter=4,
            leading=20,
        ),
        "scenario": ParagraphStyle(
            "BoaScenario",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=NAVY,
            spaceAfter=2,
        ),
        "meta": ParagraphStyle(
            "BoaMeta",
            parent=base["Normal"],
            fontSize=9,
            textColor=MUTED,
            spaceAfter=6,
        ),
        "heading": ParagraphStyle(
            "BoaHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BoaBody",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=NAVY,
        ),
        "small": ParagraphStyle(
            "BoaSmall",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
        "cell": ParagraphStyle(
            "BoaCell",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            textColor=NAVY,
        ),
        "cell_bold": ParagraphStyle(
            "BoaCellBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=NAVY,
        ),
    }


def _logo_flowable():
    if not LOGO_V2.is_file():
        return None
    try:
        probe = Image(str(LOGO_V2))
        width = float(probe.imageWidth)
        height = float(probe.imageHeight)
        if width <= 0 or height <= 0:
            return None
        scale = min((2.2 * inch) / width, (0.72 * inch) / height, 1.0)
        return Image(str(LOGO_V2), width=width * scale, height=height * scale)
    except Exception:
        return None


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.25)
    canvas.line(0.7 * inch, 0.52 * inch, letter[0] - 0.7 * inch, 0.52 * inch)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(
        0.7 * inch,
        0.36 * inch,
        "CalibraytAI — Employment vs Entrepreneurship Decision Tool",
    )
    canvas.drawRightString(letter[0] - 0.7 * inch, 0.36 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _table(rows, styles, highlight_last=False):
    data = [
        [
            Paragraph(escape(str(label)), styles["cell"]),
            Paragraph(escape(str(value)), styles["cell_bold"]),
        ]
        for label, value in rows
    ]
    table = Table(data, colWidths=[4.2 * inch, 2.6 * inch])
    commands = [
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#e2ddd4")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]
    if highlight_last and data:
        commands.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#efe6c8")))
        commands.append(("LINEABOVE", (0, -1), (-1, -1), 1.25, GOLD))
    table.setStyle(TableStyle(commands))
    return table


def _section(heading, rows, styles, highlight_last=False):
    if not rows:
        return []
    return [
        KeepTogether(
            [
                Paragraph(heading, styles["heading"]),
                _table(rows, styles, highlight_last=highlight_last),
            ]
        )
    ]


def _employment_block(result, styles):
    inputs = result.get("inputs") or {}
    employment = result.get("employment") or {}
    rows = []
    mode = inputs.get("employment_pay_mode") or "annual"
    rows.append(
        (
            "Pay entry",
            "Hourly wage" if mode == "hourly" else "Annual salary / wages",
        )
    )
    if mode == "hourly":
        rows.append(("Hourly wage", format_money(inputs.get("employment_hourly_wage"))))
    else:
        rows.append(("Annual salary / wages", format_money(employment.get("annual_wages"))))
    rows.append(("Employment hours / week", format_hours(employment.get("hours_per_week"))))
    rows.append(("Working weeks / year", format_weeks(employment.get("weeks_per_year"))))
    if _positive(employment.get("paid_time_off_weeks")):
        rows.append(
            (
                "Paid vacation / paid time weeks",
                format_weeks(employment.get("paid_time_off_weeks")),
            )
        )
    if _positive(employment.get("benefits_annual")):
        rows.append(("Employer-paid benefits", format_money(employment.get("benefits_annual"))))
    if _positive(employment.get("retirement_annual")):
        rows.append(
            (
                "Employer retirement / pension contribution",
                format_money(employment.get("retirement_annual")),
            )
        )
    if _positive(employment.get("other_compensation_annual")):
        rows.append(
            (
                "Other employer-paid compensation",
                format_money(employment.get("other_compensation_annual")),
            )
        )
    rows.append(("Employment economic value", format_money(employment.get("economic_value"))))
    return _section("Employment assumptions", rows, styles, highlight_last=True)


def _business_block(result, styles):
    inputs = result.get("inputs") or {}
    business = result.get("business") or {}
    rows = []
    if inputs.get("trade_profile") and inputs.get("trade_profile") != "custom":
        rows.append(("Starting trade / profile", inputs.get("trade_profile_label") or inputs.get("trade_profile")))
    rows.append(("Realized selling rate", format_money(business.get("realized_hourly_rate"))))
    rows.append(
        (
            "Owner available hours / week",
            format_hours(business.get("owner_available_hours_per_week")),
        )
    )
    rows.append(("Utilization / productive-time percent", format_percent(business.get("utilization_percent"))))
    rows.append(
        (
            "Owner productive / billable hours / week",
            format_hours(business.get("owner_productive_hours_per_week")),
        )
    )
    rows.append(
        (
            "Owner administration / non-billable hours / week",
            format_hours(business.get("owner_admin_hours_per_week")),
        )
    )
    rows.append(("Business working weeks / year", format_weeks(business.get("weeks_per_year"))))
    if business.get("helper_used"):
        rows.append(("Helper / employee count", format_count(business.get("helper_count"))))
        rows.append(("Helper hours / week", format_hours(business.get("helper_hours_per_week"))))
        rows.append(("Helper wage", format_money(business.get("helper_hourly_wage"))))
        rows.append(("Helper productivity / contribution percent", format_percent(business.get("helper_productivity_percent"))))
        rows.append(("Payroll burden percent", format_percent(business.get("payroll_burden_percent"))))
        rows.append(("Helper labour (annual)", format_money(business.get("helper_labour_annual"))))
        rows.append(("Payroll burden (annual)", format_money(business.get("helper_payroll_burden_annual"))))
        rows.append(("Helper cash cost (annual)", format_money(business.get("helper_cash_cost_annual"))))
    cost_lines = (
        ("Insurance (annual)", inputs.get("insurance_annual")),
        ("Vehicle (annual)", inputs.get("vehicle_annual")),
        ("Tools / equipment operating (annual)", inputs.get("tools_and_equipment_operating_annual")),
        ("Marketing (annual)", inputs.get("marketing_annual")),
        ("Professional fees (annual)", inputs.get("professional_fees_annual")),
        ("Other operating costs (annual)", inputs.get("other_operating_costs_annual")),
    )
    for label, value in cost_lines:
        if _positive(value):
            rows.append((label, format_money(value)))
    rows.append(("Operating overhead (annual)", format_money(business.get("operating_overhead_annual"))))
    return _section("Entrepreneurship assumptions", rows, styles, highlight_last=True)


def _startup_block(result, styles):
    startup = result.get("startup") or {}
    rows = []
    lines = (
        ("Equipment / tools / vehicle startup purchases", startup.get("startup_equipment")),
        ("Business setup / licensing / legal / accounting", startup.get("startup_setup_licensing")),
        ("Initial insurance / deposits / setup", startup.get("startup_insurance_deposits")),
        ("Initial working capital", startup.get("working_capital")),
        ("Personal income runway", startup.get("personal_income_runway")),
        ("Existing usable assets / equipment already owned", startup.get("existing_usable_assets")),
    )
    for label, value in lines:
        if _positive(value):
            rows.append((label, format_money(value)))
    rows.append(
        (
            "Cash required to make the transition",
            format_money(startup.get("cash_required_to_make_transition")),
        )
    )
    return _section("Startup & transition", rows, styles, highlight_last=True)


def _results_block(result, styles):
    comparison = result.get("comparison") or {}
    business = result.get("business") or {}
    workload = result.get("workload") or {}
    employment = result.get("employment") or {}
    truth = result.get("what_has_to_be_true") or {}
    rows = [
        ("Employment economic value", format_money(comparison.get("employment_economic_value"))),
        (
            "Entrepreneurship economic value",
            format_money(comparison.get("entrepreneurship_economic_value")),
        ),
        ("Difference", format_money(comparison.get("difference"))),
        (
            "Cash available to owner before personal income tax",
            format_money(business.get("cash_available_to_owner")),
        ),
        ("Effective owner hourly return", format_money(business.get("effective_owner_hourly_return"))),
        ("Employment effective hourly value", format_money(employment.get("effective_hourly_value"))),
        (
            "Owner productive / billable hours per week",
            format_hours(workload.get("owner_productive_hours_per_week")),
        ),
        (
            "Owner admin / non-billable hours per week",
            format_hours(workload.get("owner_admin_hours_per_week")),
        ),
        ("Total owner hours per week", format_hours(workload.get("owner_total_hours_per_week"))),
        ("Break-even selling rate", format_money(truth.get("break_even_selling_rate"))),
    ]
    return _section("Core results", rows, styles)


def _stress_block(result, styles):
    stress = result.get("stress") or {}
    order = (
        "base",
        "fewer_productive_hours",
        "lower_realized_rate",
        "higher_operating_costs",
    )
    rows = []
    for key in order:
        item = stress.get(key) or {}
        label = item.get("label") or key
        rows.append((f"{label} — entrepreneurship economic value", format_money(item.get("entrepreneurship_economic_value"))))
        rows.append((f"{label} — difference vs employment", format_money(item.get("difference"))))
        rows.append((f"{label} — cash available to owner", format_money(item.get("cash_available_to_owner"))))
    return _section("Downside stress test", rows, styles)


def _truth_block(result, styles):
    truth = result.get("what_has_to_be_true") or {}
    rows = [
        ("Required realized selling rate", format_money(truth.get("required_realized_selling_rate"))),
        (
            "Break-even selling rate at current productive hours",
            format_money(truth.get("break_even_selling_rate")),
        ),
        (
            "Required productive / billable hours per week",
            format_hours(truth.get("required_productive_hours_per_week")),
        ),
        (
            "Required owner productive hours per week",
            format_hours(truth.get("required_owner_productive_hours_per_week")),
        ),
        ("Required utilization / productivity", format_percent(truth.get("required_utilization_percent"))),
        (
            "Required total owner hours per week (productive + admin)",
            format_hours(truth.get("required_total_owner_hours_per_week")),
        ),
    ]
    return _section("What has to be true", rows, styles)


__all__ = [
    "generate_assessment_pdf",
    "assessment_pdf_filename",
    "format_money",
    "format_hours",
    "format_percent",
    "COVER_DESCRIPTION",
    "ASSUMPTIONS_NOTE",
]

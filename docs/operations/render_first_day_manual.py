"""Build the illustrated Ben's First Day manual (PDF) from the Getting started steps and the screenshots
of the real browser walk (tools/release/evidence_first_day.mjs with EVIDENCE_SHOTS=<folder>).

    ./venv/bin/python docs/operations/render_first_day_manual.py <shots folder> <release label> <commit> <out.pdf>

The step titles and directions come from app/services/onboarding.py itself, so the manual cannot drift
from the checklist. Every picture is a real screen of a synthetic company; nothing is drawn or edited
apart from cropping long pages to their top.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Pictures for each step, in order (file stems without "-desktop.png" / "-phone.png").
PICTURES = {
    "sign_in": ["01-sign-in-desktop", "01-sign-in-checklist-desktop"],
    "company": ["02-company-form-desktop"],
    "finance": ["03-finance-form-desktop", "03-finance-policy-desktop"],
    "accounting": ["04-accounting-make-invoice-desktop", "04-accounting-page-desktop", "04-accounting-nothing-new-desktop"],
    "people": ["05-people-add-desktop", "05-people-person-desktop"],
    "phones": ["06-phones-set-password-phone", "06-phones-password-set-phone", "06-phones-field-today-phone"],
    "calendars": ["07-calendars-company-form-desktop", "07-calendars-day-phone"],
    "subscribe": ["08-subscribe-address-desktop"],
    "suppliers": ["09-suppliers-add-desktop", "09-suppliers-added-desktop"],
    "customers": ["10-customers-client-desktop", "10-customers-project-hub-desktop"],
    "estimate": ["11-estimate-lines-desktop", "11-estimate-priced-desktop"],
    "proposal": ["12-proposal-template-desktop", "12-proposal-sent-desktop", "12-proposal-customer-phone",
                 "12-proposal-accepted-phone"],
    "purchase_order": ["13-purchase-order-request-desktop", "13-purchase-order-supplier-quote-desktop",
                       "13-purchase-order-approve-and-order-desktop", "13-purchase-order-confirmed-desktop"],
    "crew_schedule": ["14-crew-schedule-set-dates-desktop", "14-crew-schedule-assigned-desktop",
                      "14-crew-schedule-field-today-phone", "14-crew-schedule-field-job-phone"],
    "hours_policy": ["15-hours-policy-filled-desktop", "15-hours-policy-saved-desktop",
                     "15-hours-policy-field-today-phone"],
    "working_day": ["16-working-day-home-desktop", "16-working-day-time-review-desktop",
                    "16-working-day-field-week-phone", "16-working-day-time-sent-phone"],
}
EVERYDAY_SHOTS = ROOT / "app" / "static" / "training" / "shots"
EVERYDAY_PICTURES = ["m7-field-quick-actions-phone.png", "m7-receipt-capture-phone.png", "m7-delivery-short-phone.png",
                     "m7-job-update-phone.png", "m7-home-attention-desktop.png", "m7-receipts-inbox-desktop.png",
                     "m7-qbo-projects-desktop.png"]
EVERYDAY_TEXT = [
    "<b>Morning:</b> open Home. <b>WHAT NEEDS MY ATTENTION?</b> lists what is waiting — time to approve, material "
    "requests, extra work, short or damaged deliveries, receipts, QuickBooks items, job problems. Press an item: it "
    "opens the screen where you deal with it, and it leaves the list when it is done.",
    "<b>On site:</b> the crew use the seven buttons at the top of Field Today — My Hours, Add Receipt, Need Materials, "
    "Extra Work, Confirm Delivery, Job Update, My Schedule. Nothing they send is approved until the office approves it, "
    "and Field never shows money.",
    "<b>Suzanne:</b> Accounting → Receipts Inbox: check each receipt against its photo and approve it for QuickBooks "
    "Online (entered once, with the image). Projects in QuickBooks shows each job's customer, project and job code; "
    "a job QuickBooks already had is matched once when she confirms it.",
    "<b>End of day:</b> CalibraytAI reminds whoever still has hours or a job update to send, and gives you the counts "
    "still waiting — in the app, and by text only once texting is switched on.",
]
DESKTOP_CROP = 1500  # pixels of a long desktop page kept from the top
PHONE_CROP = 1500


def _picture(path: Path, max_width: float, crop: int):
    img = Image.open(path).convert("RGB")
    if img.height > crop:
        img = img.crop((0, 0, img.width, crop))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=72, optimize=True)
    buf.seek(0)
    width = max_width
    height = width * img.height / img.width
    if height > 7.2 * inch:
        height = 7.2 * inch
        width = height * img.width / img.height
    flow = RLImage(buf, width=width, height=height)
    flow.hAlign = "CENTER"
    return flow


def build(shots: Path, label: str, commit: str, out: Path) -> None:
    import app.models  # noqa: F401  (loads the models in their order first)
    from app.services.onboarding import STEPS

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=24, leading=28, spaceAfter=10)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=16, leading=20, spaceBefore=4, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=11, leading=15)
    small = ParagraphStyle("small", parent=body, fontSize=9, leading=12, textColor=colors.HexColor("#555555"))
    story = [
        Paragraph("Ben's First Day", h1),
        Paragraph("Setting up CalibraytAI and running a real working day, step by step", styles["Heading3"]),
        Spacer(1, 10),
        Paragraph("In CalibraytAI: <b>Company → Getting started</b>. The same sixteen steps are there, each with a "
                  "<b>Go there</b> button. Steps tick themselves when the work is in CalibraytAI; the others you "
                  "tick with <b>Mark done</b>. Your progress is saved for the whole company.", body),
        Spacer(1, 8),
        Paragraph("Every picture is a real screen from a synthetic company (Brayman Construction training data, "
                  "a synthetic customer, crew and supplier). No real customer or price appears.", body),
        Spacer(1, 8),
        Paragraph(f"Screens and steps verified on {label}, commit {commit[:12]}. Where this manual and the "
                  "screen differ, the screen is right; tell Joel.", small),
        PageBreak(),
    ]
    missing = []
    for number, step in enumerate(STEPS, 1):
        head = [Paragraph(f"{number}. {step.title}", h2), Paragraph(f"<i>{step.why}</i>", body), Spacer(1, 4),
                Paragraph(step.how, body), Spacer(1, 8)]
        desktops, phones = [], []
        for stem in PICTURES.get(step.key, []):
            path = shots / f"{stem}.png"
            if not path.exists():
                missing.append(path.name)
                continue
            (phones if stem.endswith("-phone") else desktops).append(path)
        flows = []
        for path in desktops:
            flows.append(_picture(path, 6.8 * inch, DESKTOP_CROP))
            flows.append(Spacer(1, 8))
        if phones:
            cells = [_picture(p, 1.6 * inch, PHONE_CROP) for p in phones]
            table = Table([cells], colWidths=[1.75 * inch] * len(cells))
            table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            flows.append(table)
        story.append(KeepTogether(head + flows[:1]))
        story.extend(flows[1:])
        story.append(PageBreak())
    # After the first day: the everyday routine (Magnificent Seven, 25 Oct 2026), from the real screens of its own
    # browser walk (tools/release/evidence_magnificent_seven.mjs; the same pictures the Training Centre uses).
    story.append(Paragraph("Every day after that", h2))
    for text in EVERYDAY_TEXT:
        story.append(Paragraph(text, body))
        story.append(Spacer(1, 4))
    every_desk, every_phone = [], []
    for name in EVERYDAY_PICTURES:
        path = EVERYDAY_SHOTS / name
        if not path.exists():
            missing.append(path.name)
            continue
        (every_phone if name.endswith("-phone.png") else every_desk).append(path)
    if every_phone:
        cells = [_picture(p, 1.6 * inch, PHONE_CROP) for p in every_phone[:4]]
        table = Table([cells], colWidths=[1.75 * inch] * len(cells))
        table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(table)
    for path in every_desk:
        story.append(PageBreak())
        story.append(_picture(path, 6.8 * inch, DESKTOP_CROP))
    if missing:
        raise SystemExit("Missing screenshots: " + ", ".join(missing))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#777777"))
        canvas.drawString(0.75 * inch, 0.5 * inch, f"CalibraytAI · Ben's First Day · {label} ({commit[:12]})")
        canvas.drawRightString(7.75 * inch, 0.5 * inch, str(doc.page))
        canvas.restoreState()

    doc = SimpleDocTemplate(str(out), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.8 * inch, title="Ben's First Day — CalibraytAI",
                            author="Brayman Construction")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    build(Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4]))

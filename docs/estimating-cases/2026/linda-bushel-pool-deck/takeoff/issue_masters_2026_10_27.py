"""Linda Bushel documents from Approved Master Template Family V1 (27 Oct 2026).

Master 01 Labour Calculation Detail, Master 02 Internal Detailed Cost Breakdown and Master 03 Customer
Facing Estimate, populated through app/services/approved_masters.py (the only governed route). The data
comes from price_2026_10_27.py; the format is the master's. Writes the DOCX files into the case and,
when LibreOffice is available, a preview PDF beside each one for checking. The approved PDF route is
Microsoft Word for Mac "Save as PDF" (FG-022 register); the released PDFs are exported there.

Run from the repository root:  python docs/estimating-cases/2026/linda-bushel-pool-deck/takeoff/issue_masters_2026_10_27.py
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(HERE)]

import price_2026_10_27 as P  # noqa: E402
import app.models  # noqa: E402,F401  (initialise the package in the order the application does)
from app.services import approved_masters as AM  # noqa: E402

CASE = HERE.parent
OUT = {
    AM.LABOUR_CALCULATION_DETAIL: CASE / "estimates/internal/2026-10-27-linda-bushel-01-labour-calculation-detail.docx",
    AM.INTERNAL_DETAILED_COST_BREAKDOWN: CASE / "estimates/internal/2026-10-27-linda-bushel-02-internal-detailed-cost-breakdown.docx",
    AM.CUSTOMER_FACING_ESTIMATE: CASE / "estimates/customer/2026-10-27-linda-bushel-03-customer-facing-estimate.docx",
}
TOKENS = {"CLIENT": "Linda Bushel", "PROJECT": "Bushel Rear Deck (pool deck)",
          "SITE": "12 D'Arcy's Way, Kemptville, ON K0G 1J0", "DATE": "2026-10-27"}
F = P.fmt


def _priced():
    return P.price(P.PROPOSED_HOURS)


def labour_detail():
    p = _priced()
    rate, keep = P.LABOUR_RATE, Decimal(1) - P.MARGIN
    rows = [(task, basis, str(hours), F(rate * hours), F(rate * hours / keep)) for task, basis, hours in P.LABOUR_TASKS]
    rows.append(("Total", "Two-person crew", str(P.PROPOSED_HOURS), F(p["labour"]), F(p["labour"] / keep)))
    control = [
        ("Total man-hours", str(P.PROPOSED_HOURS)),
        ("Direct labour rate", f"{F(rate)} per man-hour (Brayman rate from 27 Oct 2026)"),
        ("Direct labour", F(p["labour"])),
        ("GM reference sell (15% true gross margin)", F(p["labour"] / keep)),
        ("Crew and duration", f"Two-person crew, about {(Decimal(P.PROPOSED_HOURS) / 16).quantize(Decimal('0.1'))} working days"),
        ("Helical piles", "Supplied and installed by Pro Post Foundations (OT-2236); no pile installation in Brayman labour"),
        ("Basis", "Joel's estimating allowance (27 Oct 2026) from the J1 take-off and supplier quantities"),
        ("For Ben", "Review each line; adjust the hours of any task from your experience and the price is recalculated"),
    ]
    return AM.populate(AM.LABOUR_CALCULATION_DETAIL, tokens=TOKENS, tables={
        ("Labour Task", "Basis / Scope", "Hours", "Direct labour", "GM reference sell"): rows,
        ("Metric", "Amount"): control})


def internal_breakdown():
    p = _priced()
    material = [
        ("Framing lumber — BMR estimate 237147/1", "$1,361.71", "Written quote; Darcy's price is Brayman's cost. EXPIRES 28 OCT 2026 — confirm/order promptly"),
        ("Structural hardware — BMR", "$389.35", "Written quote"),
        ("Trex Select Island Mist decking — BMR", "$4,827.20", "Written quote"),
        ("Trex Island Mist fascia — BMR", "$1,666.80", "Written quote"),
        ("Trex fasteners and fascia screw kit — BMR", "$431.03", "Written quote"),
        ("Vista 42 in railing and gate — quote 87915-165209", F(P.VISTA), "Written quote, ADDITIONAL to BMR (Joel confirmed). Quoted price is Brayman's cost"),
        ("Helical piles, 11 — Pro Post OT-2236, SUPPLY AND INSTALL", "$3,265.00", "Written quote; installation included, so no Brayman pile labour. 11 piles govern; J1 15-pier evidence kept. QUOTE EXPIRED 21 OCT — reconfirm before commitment"),
        ("Pro Post travel fee", "$85.00", "Written quote"),
        ("Pro Post engineer report and compliance letter", "$400.00", "Written quote. Included as quoted; required if the town asks"),
        ("Delivery and carrying — BMR", "$0.00", "BMR: extra; no amount on any document. Absorbed"),
        ("Equipment", "$0.00", "None: Pro Post brings its own machine"),
        ("Town permit fee", "Excluded", "Not in the customer price; billed at cost"),
        ("Total materials and subcontract", F(P.BMR + P.VISTA + P.PRO_POST), "BMR $8,676.09 + Vista $3,851.49 + Pro Post $3,750.00"),
    ]
    labour = [(task, str(hours), F(P.LABOUR_RATE * hours)) for task, _basis, hours in P.LABOUR_TASKS]
    labour.append(("Total Brayman labour at $75.00 per man-hour", str(P.PROPOSED_HOURS), F(p["labour"])))
    pricing = [
        ("Materials and subcontract", F(P.BMR + P.VISTA + P.PRO_POST)),
        (f"Brayman labour ({P.PROPOSED_HOURS} man-hours × {F(P.LABOUR_RATE)})", F(p["labour"])),
        ("Total direct cost", F(p["direct"])),
        ("Pricing method", "True gross margin 15% (not markup): selling price = direct cost ÷ 0.85"),
        ("Gross profit", F(p["profit"])),
        ("Selling price before HST", F(p["selling"])),
        ("HST 13%", F(p["hst"])),
        ("Total including HST", F(p["total"])),
        ("Resulting true gross margin", f"{p['margin']}%"),
        ("Quote status", "BMR/Darcy pricing expires 28 Oct 2026 — confirm/order promptly. Pro Post OT-2236 expired 21 Oct — reconfirm before commitment"),
        ("Status", "For Ben's review. Customer estimate not sent to Linda"),
    ]
    return AM.populate(AM.INTERNAL_DETAILED_COST_BREAKDOWN, tokens=TOKENS, tables={
        ("Material / Package", "Direct Cost", "Status"): material,
        ("Task", "Hours", "Direct Cost"): labour,
        ("Component", "Amount"): pricing})


SCOPE = [
    ("Helical pile foundation", "Galvanized steel helical piles with adjustable brackets, supplied and installed by a specialist foundation contractor; engineer's report and compliance letter if the town asks for it. No concrete footings."),
    ("Structural framing", "Pressure-treated built-up 2×10 beams, 2×8 joists and 6×6 posts, with galvanized connectors, hangers, bolts and structural screws. Freestanding; not attached to the pool."),
    ("Upper deck", "About 18 ft wide, with the inner edge following the curve of the pool and about 5 ft of clear deck at the centre."),
    ("Stairs", "10 ft wide, pressure-treated 2×12 stringers, Trex Island Mist treads and risers."),
    ("Lower deck", "10 ft wide by 3 ft deep."),
    ("Composite decking", "Trex Select composite decking in Island Mist on the upper deck, the lower deck and the stairs, with Trex deck fasteners."),
    ("Fascia", "Trex Island Mist fascia on the exposed edges, with colour-matched screws."),
    ("Railing and gate", "Vista 42 in aluminium railing, textured black, standard pickets, on the upper deck sides and front, both sides of the stairs and the lower deck; matching 42 in high, 48 in wide gate centred on the lower deck."),
    ("Installation", "Complete installation by Brayman Construction, including clean-up of construction debris."),
]
EXCLUSIONS = [
    "Town building-permit fee (Brayman can apply for the permit; the town's fee is billed at cost).",
    "Electrical work.",
    "Plumbing and HVAC work.",
    "Painting and decorative finishes.",
    "Site grading, landscaping and drainage work.",
    "A guard along the open pool edge, and skirting under either deck.",
    "Pile extensions, if the foundation contractor must go deeper to reach the required resistance (agreed with you first).",
    "Owner to provide about 46 in of access for the pile machine and to point out private buried services.",
    "Owner-requested changes, concealed conditions and revisions to drawings/engineering after acceptance.",
    "This estimate is valid for 7 days; supplier prices are time-limited.",
    "Project-specific inclusions are listed in the included-scope table.",
]


def customer_estimate():
    p = _priced()
    tokens = dict(TOKENS)
    tokens.update({"PRICE + HST": f"{F(p['selling'])} + HST", "AMOUNT": F(p["total"])})
    return AM.populate(AM.CUSTOMER_FACING_ESTIMATE, tokens=tokens, bullets=EXCLUSIONS, tables={
        ("Included Scope", "Description"): SCOPE,
        ("Price Component", "Amount"): [("Estimate subtotal", F(p["selling"])), ("HST 13%", F(p["hst"])),
                                        ("Total including HST", F(p["total"]))]})


BUILDERS = {AM.LABOUR_CALCULATION_DETAIL: labour_detail, AM.INTERNAL_DETAILED_COST_BREAKDOWN: internal_breakdown,
            AM.CUSTOMER_FACING_ESTIMATE: customer_estimate}


def main(preview: bool = True) -> None:
    for document_type, path in OUT.items():
        AM.assert_governed_route(document_type, AM.__name__)
        data = BUILDERS[document_type]()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print("wrote", path.relative_to(CASE), "from master", AM.master_for(document_type).family)
        if preview:
            import shutil
            import subprocess
            import tempfile

            soffice = shutil.which("soffice")
            if soffice:
                with tempfile.TemporaryDirectory() as tmp:
                    src = Path(tmp) / path.name
                    src.write_bytes(data)
                    subprocess.run([soffice, "--headless", "--norestore", "--convert-to", "pdf", "--outdir", tmp, str(src)],
                                   check=True, capture_output=True, timeout=180)
                    preview_path = path.with_suffix(".preview.pdf")
                    preview_path.write_bytes((Path(tmp) / (path.stem + ".pdf")).read_bytes())
                    print("   preview", preview_path.relative_to(CASE))


if __name__ == "__main__":
    main()

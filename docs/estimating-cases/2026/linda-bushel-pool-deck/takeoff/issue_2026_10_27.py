"""27 Oct 2026 costing issue: PDFs of the supplier reconciliation, Ben's internal cost and Linda's estimate,
and the package for Ben. Uses the same interim Brayman-branded writer as issue J1 (branded_issue_pdf.build).
Supplier originals are copied into the package unchanged; nothing here regenerates them.

Run from this folder:  python issue_2026_10_27.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from reportlab.lib.pagesizes import landscape, letter

from branded_issue_pdf import CASE, build

FOOTER = "27 Oct 2026"
JOBS = [
    ("takeoff/2026-10-27-supplier-quote-reconciliation.md", "takeoff/2026-10-27-supplier-quote-reconciliation.pdf",
     "SUPPLIER QUOTE RECONCILIATION", "Internal. Not for the customer.", landscape(letter)),
    ("estimates/internal/2026-10-27-ben-internal-cost.md", "estimates/internal/2026-10-27-ben-internal-cost.pdf",
     "INTERNAL COST FOR BEN", "INTERNAL — NOT FOR CUSTOMER", letter),
    ("estimates/customer/2026-10-27-linda-bushel-estimate.md", "estimates/customer/2026-10-27-linda-bushel-estimate.pdf",
     "POOL DECK ESTIMATE", "Estimate for Linda Bushel.", letter),
]
PACKAGE = {
    "Linda Bushel — Ben Internal Cost.pdf": "estimates/internal/2026-10-27-ben-internal-cost.pdf",
    "Linda Bushel — Customer Estimate.pdf": "estimates/customer/2026-10-27-linda-bushel-estimate.pdf",
    "Linda Bushel — Supplier Quote Reconciliation.pdf": "takeoff/2026-10-27-supplier-quote-reconciliation.pdf",
    "SUPPLIER/BMR estimate 237147-1 (26 Oct 2026).pdf": "supplier/bmr-winchester/2026-10-26-darcy-bmr-estimate-237147-1.pdf",
    "SUPPLIER/Vista rail quote 87915-165209 (26 Oct 2026, MSRP).pdf": "supplier/bmr-winchester/2026-10-26-vista-rail-quote-87915-165209.pdf",
    "SUPPLIER/Pro Post OT-2236 (6 Oct 2026).pdf": "supplier/pro-post-foundations/2026-10-06-pro-post-OT-2236-estimate.pdf",
    "SUPPLIER/Pro Post OT-2236 pile locations.png": "supplier/pro-post-foundations/2026-10-06-pro-post-OT-2236-pile-locations.png",
    "DRAWINGS/J1 preliminary 11x17 (1 Oct 2026, 15 piers).pdf": "drawings/2026-10-01-j1-preliminary-11x17.pdf",
}
ZIP = CASE / "delivery/LINDA_BUSHEL_POOL_DECK_2026-10-27_BEN_PACKAGE.zip"


def main() -> None:
    for source, target, title, status, size in JOBS:
        if not (CASE / source).exists():
            print("skipped (not issued yet)", source)
            continue
        build(CASE / source, CASE / target, title, status, size, footer_date=FOOTER)
        print("wrote", target)
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, relative in PACKAGE.items():
            if not (CASE / relative).exists():
                continue
            archive.write(CASE / relative, Path("LINDA_BUSHEL_POOL_DECK_2026-10-27") / name)
    print("package", ZIP.relative_to(CASE))


if __name__ == "__main__":
    main()

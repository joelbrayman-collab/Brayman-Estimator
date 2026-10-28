"""27 Oct 2026 costing issue: the package for Ben.

The four governed documents are populated from Approved Master Template Family V1 by
issue_masters_2026_10_27.py (Masters 01, 02, 03 and 08 through app/services/approved_masters.py). Their PDFs are
exported with Microsoft Word for Mac "Save as PDF", the approved route in the FG-022 register. This script
does not write any document: it packages the master outputs and the supplier originals unchanged.

The package is not built from LibreOffice previews or from the retired interim writer. If a Word-exported PDF
is missing, the script stops.

The supplier reconciliation has no approved master; it travels as the internal case record (Markdown).

Run from this folder:  python issue_2026_10_27.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

CASE = Path(__file__).resolve().parents[1]
INTERNAL = "estimates/internal/2026-10-27-linda-bushel-"
CUSTOMER = "estimates/customer/2026-10-27-linda-bushel-"
GOVERNED = {
    "Linda Bushel - 01 Labour Calculation Detail": INTERNAL + "01-labour-calculation-detail",
    "Linda Bushel - 02 Internal Detailed Cost Breakdown": INTERNAL + "02-internal-detailed-cost-breakdown",
    "Linda Bushel - 03 Customer Facing Estimate": CUSTOMER + "03-customer-facing-estimate",
    "Linda Bushel - 08 Customer Detailed Cost Estimate": CUSTOMER + "08-customer-detailed-cost-estimate",
}
RECORDS = {
    "INTERNAL RECORD/Supplier quote reconciliation (27 Oct 2026).md": "takeoff/2026-10-27-supplier-quote-reconciliation.md",
    "SUPPLIER/BMR estimate 237147-1 (26 Oct 2026).pdf": "supplier/bmr-winchester/2026-10-26-darcy-bmr-estimate-237147-1.pdf",
    "SUPPLIER/Vista rail quote 87915-165209 (26 Oct 2026, MSRP).pdf": "supplier/bmr-winchester/2026-10-26-vista-rail-quote-87915-165209.pdf",
    "SUPPLIER/Pro Post OT-2236 (6 Oct 2026).pdf": "supplier/pro-post-foundations/2026-10-06-pro-post-OT-2236-estimate.pdf",
    "SUPPLIER/Pro Post OT-2236 pile locations.png": "supplier/pro-post-foundations/2026-10-06-pro-post-OT-2236-pile-locations.png",
    "DRAWINGS/Linda Bushel - Construction Drawings J2 (27 Oct 2026).pdf": "drawings/2026-10-27-j2-construction-drawings-11x17.pdf",
}
ZIP = CASE / "delivery/LINDA_BUSHEL_POOL_DECK_2026-10-27_BEN_PACKAGE.zip"


def main() -> None:
    entries = {}
    missing = []
    for name, stem in GOVERNED.items():
        for suffix in (".docx", ".pdf"):
            path = CASE / (stem + suffix)
            (entries.__setitem__(name + suffix, path) if path.exists() else missing.append(stem + suffix))
    for name, relative in RECORDS.items():
        path = CASE / relative
        (entries.__setitem__(name, path) if path.exists() else missing.append(relative))
    if missing:
        sys.exit("STOP: not packaged; missing " + ", ".join(missing))
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in entries.items():
            archive.write(path, Path("LINDA_BUSHEL_POOL_DECK_2026-10-27") / name)
    print("package", ZIP.relative_to(CASE), len(entries), "files")


if __name__ == "__main__":
    main()

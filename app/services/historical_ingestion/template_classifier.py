"""Template Family Classifier for Historical Brayman Workbooks (FG-006 / Phase A).

Classifies workbooks deterministically into one of the 5 governed families:
- FAMILY_A: Slab-on-Grade / Thickened Edge Slab (9 workbooks)
- FAMILY_B: Standard ICF Foundation (5 workbooks)
- FAMILY_C: Extended Multi-Trade ICF (1 workbook)
- FAMILY_D: Comprehensive Build Package (1 workbook)
- FAMILY_E: Ad-Hoc / Standalone Flat Sheet (4 workbooks)
"""

from typing import Tuple

from app.services.historical_ingestion.openxml_reader import WorkbookData

FAMILY_A = "FAMILY_A"  # Slab-on-Grade / TES
FAMILY_B = "FAMILY_B"  # Standard ICF Foundation
FAMILY_C = "FAMILY_C"  # Extended Multi-Trade ICF
FAMILY_D = "FAMILY_D"  # Comprehensive Build Package
FAMILY_E = "FAMILY_E"  # Ad-Hoc / Standalone Flat Sheet


def classify_template_family(wb: WorkbookData) -> Tuple[str, float, str]:
    """Deterministically classify a workbook into its template family.

    Returns:
        (family_code, confidence, reasoning)
    """
    vis_sheets = set(wb.visible_sheet_names)
    vis_upper = {s.upper() for s in wb.visible_sheet_names}

    # Family D: Master SUMMARY sheet with multi-trade sub-sheets
    if "SUMMARY" in vis_upper and ("BC INTERNAL WORK" in vis_upper or "SUB-TRADES" in vis_upper):
        return (
            FAMILY_D,
            1.0,
            "Master SUMMARY sheet detected with internal trade divisions (Comprehensive Build Package)",
        )

    # Family C: Extended Multi-Trade ICF with extensive trade sheets
    if "SUB-FLOOR CALCS" in vis_upper or len(vis_sheets) >= 8:
        if "WORKSHEET FOUNDATION" in vis_upper:
            return (
                FAMILY_C,
                1.0,
                f"Extended multi-trade ICF package detected with {len(vis_sheets)} visible sheets",
            )

    # Family B: Standard ICF Foundation (5 visible sheets)
    if "WORKSHEET FOUNDATION" in vis_upper:
        return (
            FAMILY_B,
            1.0,
            "Standard ICF foundation template with Worksheet FOUNDATION and ICF Contract",
        )

    # Family A: Slab-on-Grade / Thickened Edge Slab
    slab_sheet_names = {"HOUSE TES", "WORKSHEET GARAGE SLAB", "WORKSHEET SLAB"}
    if vis_upper.intersection(slab_sheet_names) or (
        "COST DATA" in vis_upper and any("SLAB" in s or "TES" in s for s in vis_upper)
    ):
        return (
            FAMILY_A,
            1.0,
            "Slab-on-grade / Thickened Edge Slab template detected with dedicated slab calculation sheet",
        )

    # Family E: Ad-hoc / Standalone flat sheets (usually .xlsx with Sheet1/Sheet2)
    if not wb.hidden_sheet_names and ("SHEET1" in vis_upper or len(vis_sheets) <= 2):
        return (
            FAMILY_E,
            1.0,
            "Standalone ad-hoc flat sheet without hidden template layers",
        )

    # Fallback / Review required
    return (
        FAMILY_E,
        0.5,
        f"Ad-hoc fallback for workbook with sheets {wb.visible_sheet_names}",
    )

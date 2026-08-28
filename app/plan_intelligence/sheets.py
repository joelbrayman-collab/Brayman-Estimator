"""Sheet Intelligence service layer — Sheet CRUD, page mapping, suggestions, review, uniqueness, finalization."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app import db
from app.plan_intelligence.audit import record_plan_audit
from app.plan_intelligence.models import (
    DrawingPackage,
    DrawingRevision,
    PlanDocument,
    PlanPage,
    PlanSheet,
    PlanSheetPage,
    PlanSheetSuggestion,
    ProcessingAttempt,
)
from app.plan_intelligence.services import PlanIntelligenceServiceError


DISCIPLINE_CODES = [
    "ARCH",
    "STR",
    "MECH",
    "ELEC",
    "PLUMB",
    "CIVIL",
    "FIRE",
    "OTHER",
    "COVER",
    "INDEX",
    "SPEC",
    "NON_DRAWING",
]

REVIEW_STATUSES = ["draft", "suggested", "reviewed", "void"]
DRAWING_STATUSES = ["unreviewed", "reviewed", "void", "superseded-in-set"]
SUGGESTION_STATUSES = ["open", "accepted", "rejected"]


def get_sheet_or_404(project_id: int, sheet_id: int) -> PlanSheet:
    """Retrieve a sheet verifying project isolation."""
    sheet = (
        PlanSheet.query.join(DrawingRevision)
        .join(DrawingPackage)
        .filter(
            PlanSheet.id == sheet_id,
            DrawingPackage.project_id == project_id,
        )
        .first()
    )
    if sheet is None:
        raise PlanIntelligenceServiceError("Sheet not found for this project.")
    return sheet


def list_sheets_for_revision(
    revision_id: int, *, include_void: bool = True
) -> List[PlanSheet]:
    query = PlanSheet.query.filter_by(drawing_revision_id=revision_id)
    if not include_void:
        query = query.filter(PlanSheet.review_status != "void")
    return query.order_by(PlanSheet.number.asc().nullslast(), PlanSheet.id.asc()).all()


def create_sheet(
    revision: DrawingRevision,
    *,
    number: Optional[str] = None,
    title: Optional[str] = None,
    discipline_code: str = "OTHER",
    drawing_status: str = "unreviewed",
    review_status: str = "draft",
    plan_document_id: Optional[int] = None,
    page_index: Optional[int] = None,
    commit: bool = True,
) -> PlanSheet:
    """Create a new construction Sheet within a DrawingRevision."""
    if discipline_code not in DISCIPLINE_CODES:
        discipline_code = "OTHER"
    if review_status not in REVIEW_STATUSES:
        raise PlanIntelligenceServiceError(f"Invalid review status: {review_status}")
    if drawing_status not in DRAWING_STATUSES:
        raise PlanIntelligenceServiceError(f"Invalid drawing status: {drawing_status}")

    clean_num = number.strip() if number and number.strip() else None
    clean_title = title.strip() if title and title.strip() else None

    sheet = PlanSheet(
        drawing_revision_id=revision.id,
        number=clean_num,
        title=clean_title,
        discipline_code=discipline_code,
        drawing_status=drawing_status,
        review_status=review_status,
    )
    db.session.add(sheet)
    db.session.flush()

    project_id = revision.package.project_id

    if plan_document_id is not None and page_index is not None:
        doc = PlanDocument.query.filter_by(
            id=plan_document_id, project_id=project_id
        ).first()
        if doc is None:
            raise PlanIntelligenceServiceError("Plan document not found in project.")
        page_mapping = PlanSheetPage(
            sheet_id=sheet.id,
            plan_document_id=doc.id,
            page_index=page_index,
            order_index=0,
        )
        db.session.add(page_mapping)
        db.session.flush()

    record_plan_audit(
        project_id=project_id,
        plan_document_id=plan_document_id,
        sheet_id=sheet.id,
        event_type="sheet_created",
        detail={
            "sheet_id": sheet.id,
            "revision_id": revision.id,
            "number": sheet.number,
            "title": sheet.title,
            "discipline_code": sheet.discipline_code,
            "review_status": sheet.review_status,
        },
    )

    if commit:
        db.session.commit()

    return sheet


def map_page_to_sheet(
    sheet: PlanSheet,
    *,
    plan_document_id: int,
    page_index: int,
    order_index: Optional[int] = None,
    commit: bool = True,
) -> PlanSheetPage:
    """Map a PDF page (0-based) to a construction Sheet."""
    project_id = sheet.revision.package.project_id
    doc = PlanDocument.query.filter_by(
        id=plan_document_id, project_id=project_id
    ).first()
    if doc is None:
        raise PlanIntelligenceServiceError("Plan document not found for this project.")

    existing = PlanSheetPage.query.filter_by(
        sheet_id=sheet.id,
        plan_document_id=plan_document_id,
        page_index=page_index,
    ).first()
    if existing is not None:
        return existing

    if order_index is None:
        max_order = (
            db.session.query(db.func.max(PlanSheetPage.order_index))
            .filter_by(sheet_id=sheet.id)
            .scalar()
        )
        order_index = (max_order + 1) if max_order is not None else 0

    mapping = PlanSheetPage(
        sheet_id=sheet.id,
        plan_document_id=plan_document_id,
        page_index=page_index,
        order_index=order_index,
    )
    db.session.add(mapping)
    db.session.flush()

    record_plan_audit(
        project_id=project_id,
        plan_document_id=plan_document_id,
        sheet_id=sheet.id,
        event_type="sheet_page_mapped",
        detail={
            "sheet_id": sheet.id,
            "document_id": plan_document_id,
            "page_index": page_index,
            "order_index": order_index,
        },
    )

    if commit:
        db.session.commit()

    return mapping


def unmap_page_from_sheet(
    sheet: PlanSheet,
    *,
    plan_document_id: int,
    page_index: int,
    commit: bool = True,
) -> bool:
    """Remove a page mapping from a Sheet."""
    mapping = PlanSheetPage.query.filter_by(
        sheet_id=sheet.id,
        plan_document_id=plan_document_id,
        page_index=page_index,
    ).first()
    if mapping is None:
        return False

    project_id = sheet.revision.package.project_id
    db.session.delete(mapping)

    record_plan_audit(
        project_id=project_id,
        plan_document_id=plan_document_id,
        sheet_id=sheet.id,
        event_type="sheet_page_unmapped",
        detail={
            "sheet_id": sheet.id,
            "document_id": plan_document_id,
            "page_index": page_index,
        },
    )

    if commit:
        db.session.commit()

    return True


def infer_discipline_from_text(text: str, sheet_num: Optional[str] = None) -> str:
    """Deterministic discipline classification heuristic from sheet number / text."""
    if sheet_num:
        s = sheet_num.upper().strip()
        if s.startswith("ARCH") or s.startswith("A-") or s.startswith("A") and len(s) > 1 and s[1].isdigit():
            return "ARCH"
        if s.startswith("STR") or s.startswith("S-") or s.startswith("S") and len(s) > 1 and s[1].isdigit():
            return "STR"
        if s.startswith("MECH") or s.startswith("M-") or s.startswith("M") and len(s) > 1 and s[1].isdigit():
            return "MECH"
        if s.startswith("ELEC") or s.startswith("E-") or s.startswith("E") and len(s) > 1 and s[1].isdigit():
            return "ELEC"
        if s.startswith("PLUMB") or s.startswith("P-") or s.startswith("P") and len(s) > 1 and s[1].isdigit():
            return "PLUMB"
        if s.startswith("CIV") or s.startswith("C-") or s.startswith("C") and len(s) > 1 and s[1].isdigit():
            return "CIVIL"
        if s.startswith("FIRE") or s.startswith("FP") or s.startswith("F-") or s.startswith("F") and len(s) > 1 and s[1].isdigit():
            return "FIRE"
        if "COVER" in s or "TITLE" in s:
            return "COVER"
        if "INDEX" in s:
            return "INDEX"
        if "SPEC" in s:
            return "SPEC"

    t_upper = text.upper()
    if "ARCHITECTURAL" in t_upper or "FLOOR PLAN" in t_upper or "ELEVATION" in t_upper:
        return "ARCH"
    if "STRUCTURAL" in t_upper or "FOUNDATION PLAN" in t_upper or "FRAMING" in t_upper:
        return "STR"
    if "MECHANICAL" in t_upper or "HVAC" in t_upper:
        return "MECH"
    if "ELECTRICAL" in t_upper or "LIGHTING PLAN" in t_upper or "POWER PLAN" in t_upper:
        return "ELEC"
    if "PLUMBING" in t_upper:
        return "PLUMB"
    if "CIVIL" in t_upper or "SITE PLAN" in t_upper or "GRADING" in t_upper:
        return "CIVIL"
    if "FIRE PROTECTION" in t_upper or "SPRINKLER" in t_upper:
        return "FIRE"
    if "COVER SHEET" in t_upper or "TITLE SHEET" in t_upper:
        return "COVER"
    if "SHEET INDEX" in t_upper or "DRAWING INDEX" in t_upper:
        return "INDEX"
    if "SPECIFICATIONS" in t_upper:
        return "SPEC"

    return "OTHER"


def extract_sheet_suggestion_from_page(page: PlanPage) -> Optional[Dict[str, Any]]:
    """Heuristic extraction of sheet number, title, and discipline from page text."""
    text = page.extracted_text or ""
    if not text.strip():
        return None

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Regex for typical construction sheet numbers: A-101, A101, S-101, M-2.1, E-01, etc.
    sheet_num_pattern = re.compile(
        r"\b([A-Z]{1,3}\s*[-.]?\s*\d{1,4}(?:\.\d{1,2})?[A-Za-z]?)\b"
    )

    candidate_num = None
    candidate_title = None

    for line in lines:
        match = sheet_num_pattern.search(line)
        if match:
            candidate_num = match.group(1).replace(" ", "")
            # If the line contains more text, it might be the title
            rest = line.replace(match.group(0), "").strip(" -:|,")
            if rest and len(rest) > 3 and not candidate_title:
                candidate_title = rest
            break

    if not candidate_num:
        # Check cover / index keywords
        if "COVER" in text.upper():
            candidate_num = "COVER"
        elif "INDEX" in text.upper():
            candidate_num = "INDEX"

    if not candidate_num:
        return None

    # Try to find title if still missing
    if not candidate_title:
        for line in lines:
            if line != candidate_num and len(line) > 3:
                l_up = line.upper()
                if any(
                    kw in l_up
                    for kw in [
                        "PLAN",
                        "ELEVATION",
                        "SECTION",
                        "DETAIL",
                        "SCHEDULE",
                        "LAYOUT",
                        "DIAGRAM",
                        "COVER",
                    ]
                ):
                    candidate_title = line
                    break

    discipline = infer_discipline_from_text(text, candidate_num)

    confidence = 0.85 if candidate_num and candidate_title else 0.70

    return {
        "suggested_number": candidate_num,
        "suggested_title": candidate_title,
        "suggested_discipline_code": discipline,
        "confidence": confidence,
    }


def generate_suggestions_for_sheet(
    sheet: PlanSheet,
    *,
    source_attempt_id: Optional[int] = None,
    force: bool = False,
    commit: bool = True,
) -> Optional[PlanSheetSuggestion]:
    """Generate or refresh open suggestion for a Sheet from its mapped page(s)."""
    if not sheet.page_mappings:
        return None

    first_map = sheet.page_mappings[0]
    page = PlanPage.query.filter_by(
        plan_document_id=first_map.plan_document_id,
        page_index=first_map.page_index,
    ).first()
    if page is None:
        return None

    data = extract_sheet_suggestion_from_page(page)
    if not data:
        return None

    # Check if identical open suggestion already exists
    existing = PlanSheetSuggestion.query.filter_by(
        sheet_id=sheet.id,
        status="open",
        suggested_number=data["suggested_number"],
        suggested_title=data["suggested_title"],
        suggested_discipline_code=data["suggested_discipline_code"],
    ).first()
    if existing and not force:
        return existing

    suggestion = PlanSheetSuggestion(
        sheet_id=sheet.id,
        source_attempt_id=source_attempt_id,
        suggested_number=data["suggested_number"],
        suggested_title=data["suggested_title"],
        suggested_discipline_code=data["suggested_discipline_code"],
        confidence=data["confidence"],
        status="open",
    )
    db.session.add(suggestion)

    if sheet.review_status == "draft":
        sheet.review_status = "suggested"

    project_id = sheet.revision.package.project_id
    record_plan_audit(
        project_id=project_id,
        plan_document_id=first_map.plan_document_id,
        sheet_id=sheet.id,
        event_type="sheet_suggestion_generated",
        detail={
            "suggestion_id": suggestion.id,
            "sheet_id": sheet.id,
            "suggested_number": suggestion.suggested_number,
            "suggested_title": suggestion.suggested_title,
            "confidence": suggestion.confidence,
        },
    )

    if commit:
        db.session.commit()

    return suggestion


def generate_default_sheets_for_revision(
    revision: DrawingRevision,
    *,
    commit: bool = True,
) -> List[PlanSheet]:
    """Ensure every page in the revision has at least one draft/suggested sheet, without auto-accepting SoR."""
    created_sheets = []
    # Collect all pages of documents attached to revision
    for doc in revision.documents:
        if doc.is_archived:
            continue
        for page in doc.pages:
            # Check if this page is already mapped to any sheet in this revision
            existing_mapping = (
                PlanSheetPage.query.join(PlanSheet)
                .filter(
                    PlanSheet.drawing_revision_id == revision.id,
                    PlanSheetPage.plan_document_id == doc.id,
                    PlanSheetPage.page_index == page.page_index,
                )
                .first()
            )
            if existing_mapping is None:
                # Create a draft sheet for this page
                sheet = create_sheet(
                    revision=revision,
                    number=None,
                    title=None,
                    discipline_code="OTHER",
                    drawing_status="unreviewed",
                    review_status="draft",
                    plan_document_id=doc.id,
                    page_index=page.page_index,
                    commit=False,
                )
                # Generate open suggestion from text if possible
                generate_suggestions_for_sheet(sheet, commit=False)
                created_sheets.append(sheet)

    if commit:
        db.session.commit()

    return created_sheets


def accept_suggestion(
    suggestion: PlanSheetSuggestion,
    *,
    number: Optional[str] = None,
    title: Optional[str] = None,
    discipline_code: Optional[str] = None,
    commit: bool = True,
) -> PlanSheet:
    """Human Accept action: applies suggestion/overrides to Sheet SoR and marks reviewed (ADR-017)."""
    if suggestion.status != "open":
        raise PlanIntelligenceServiceError("Cannot accept a closed suggestion.")

    sheet = suggestion.sheet
    final_number = number.strip() if number and number.strip() else suggestion.suggested_number
    final_title = title.strip() if title and title.strip() else suggestion.suggested_title
    final_disc = discipline_code if discipline_code in DISCIPLINE_CODES else (
        suggestion.suggested_discipline_code or sheet.discipline_code
    )

    sheet.number = final_number
    sheet.title = final_title
    sheet.discipline_code = final_disc or "OTHER"
    sheet.review_status = "reviewed"
    sheet.drawing_status = "reviewed"

    suggestion.status = "accepted"
    suggestion.decided_at = datetime.utcnow()

    # Reject other open suggestions for this sheet
    for other in sheet.suggestions:
        if other.id != suggestion.id and other.status == "open":
            other.status = "rejected"
            other.decided_at = datetime.utcnow()

    project_id = sheet.revision.package.project_id
    record_plan_audit(
        project_id=project_id,
        sheet_id=sheet.id,
        event_type="sheet_suggestion_accepted",
        detail={
            "suggestion_id": suggestion.id,
            "sheet_id": sheet.id,
            "number": sheet.number,
            "title": sheet.title,
            "discipline_code": sheet.discipline_code,
        },
    )

    if commit:
        db.session.commit()

    return sheet


def reject_suggestion(
    suggestion: PlanSheetSuggestion,
    *,
    commit: bool = True,
) -> PlanSheetSuggestion:
    """Human Reject action: dismisses suggestion while preserving history and source data."""
    if suggestion.status != "open":
        raise PlanIntelligenceServiceError("Suggestion is already closed.")

    suggestion.status = "rejected"
    suggestion.decided_at = datetime.utcnow()

    sheet = suggestion.sheet
    # If no other open suggestions remain and sheet was 'suggested', revert to 'draft'
    has_other_open = any(
        s.id != suggestion.id and s.status == "open" for s in sheet.suggestions
    )
    if not has_other_open and sheet.review_status == "suggested":
        sheet.review_status = "draft"

    project_id = sheet.revision.package.project_id
    record_plan_audit(
        project_id=project_id,
        sheet_id=sheet.id,
        event_type="sheet_suggestion_rejected",
        detail={
            "suggestion_id": suggestion.id,
            "sheet_id": sheet.id,
        },
    )

    if commit:
        db.session.commit()

    return suggestion


def edit_sheet(
    sheet: PlanSheet,
    *,
    number: Optional[str],
    title: Optional[str],
    discipline_code: str,
    drawing_status: Optional[str] = None,
    review_status: str = "reviewed",
    commit: bool = True,
) -> PlanSheet:
    """Human Edit+Save action: human values become authoritative Sheet SoR (ADR-017)."""
    if discipline_code not in DISCIPLINE_CODES:
        raise PlanIntelligenceServiceError(f"Invalid discipline code: {discipline_code}")
    if review_status not in REVIEW_STATUSES:
        raise PlanIntelligenceServiceError(f"Invalid review status: {review_status}")
    if drawing_status and drawing_status not in DRAWING_STATUSES:
        raise PlanIntelligenceServiceError(f"Invalid drawing status: {drawing_status}")

    sheet.number = number.strip() if number and number.strip() else None
    sheet.title = title.strip() if title and title.strip() else None
    sheet.discipline_code = discipline_code
    sheet.review_status = review_status
    sheet.drawing_status = drawing_status or (
        "reviewed" if review_status == "reviewed" else sheet.drawing_status
    )

    # If sheet is explicitly edited and marked reviewed, close any open suggestions
    if review_status == "reviewed":
        for sug in sheet.suggestions:
            if sug.status == "open":
                sug.status = "rejected"
                sug.decided_at = datetime.utcnow()

    project_id = sheet.revision.package.project_id
    record_plan_audit(
        project_id=project_id,
        sheet_id=sheet.id,
        event_type="sheet_edited",
        detail={
            "sheet_id": sheet.id,
            "number": sheet.number,
            "title": sheet.title,
            "discipline_code": sheet.discipline_code,
            "review_status": sheet.review_status,
            "drawing_status": sheet.drawing_status,
        },
    )

    if commit:
        db.session.commit()

    return sheet


def void_sheet(sheet: PlanSheet, *, commit: bool = True) -> PlanSheet:
    """Mark a sheet as void, excluding it from take-off eligibility."""
    sheet.review_status = "void"
    sheet.drawing_status = "void"

    # Close any open suggestions
    for sug in sheet.suggestions:
        if sug.status == "open":
            sug.status = "rejected"
            sug.decided_at = datetime.utcnow()

    project_id = sheet.revision.package.project_id
    record_plan_audit(
        project_id=project_id,
        sheet_id=sheet.id,
        event_type="sheet_voided",
        detail={"sheet_id": sheet.id},
    )

    if commit:
        db.session.commit()

    return sheet


def validate_revision_sheet_index(revision: DrawingRevision) -> Dict[str, Any]:
    """Validate sheet index uniqueness and completeness within a DrawingRevision (ADR-018).

    Returns a dict with:
      - is_valid: bool (True if no blocking errors)
      - errors: list of blocker messages
      - warnings: list of non-blocking warning messages
      - duplicate_numbers: dict of number -> list of sheet_ids
      - unreviewed_sheet_ids: list of sheet_ids
      - empty_number_sheet_ids: list of sheet_ids
    """
    sheets = list_sheets_for_revision(revision.id, include_void=False)

    errors = []
    warnings = []
    number_counts: Dict[str, List[int]] = {}
    empty_number_sheet_ids: List[int] = []
    unreviewed_sheet_ids: List[int] = []

    for s in sheets:
        if s.review_status in ("draft", "suggested"):
            unreviewed_sheet_ids.append(s.id)

        if not s.number or not s.number.strip():
            empty_number_sheet_ids.append(s.id)
            errors.append(f"Sheet (ID {s.id}) has no assigned sheet number.")
        else:
            norm = s.number.strip().upper()
            number_counts.setdefault(norm, []).append(s.id)

    duplicates = {num: ids for num, ids in number_counts.items() if len(ids) > 1}
    for num, ids in duplicates.items():
        errors.append(
            f"Duplicate sheet number '{num}' found on {len(ids)} sheets (IDs: {', '.join(map(str, ids))})."
        )

    if unreviewed_sheet_ids:
        warnings.append(
            f"{len(unreviewed_sheet_ids)} sheet(s) are still in draft/suggested status."
        )

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "duplicate_numbers": duplicates,
        "empty_number_sheet_ids": empty_number_sheet_ids,
        "unreviewed_sheet_ids": unreviewed_sheet_ids,
        "total_sheets": len(sheets),
    }


def finalize_revision_sheet_index(
    revision: DrawingRevision, *, commit: bool = True
) -> Dict[str, Any]:
    """Finalize/mark sheet index complete for a DrawingRevision (ADR-018). Fails closed on errors."""
    validation = validate_revision_sheet_index(revision)
    if not validation["is_valid"]:
        raise PlanIntelligenceServiceError(
            f"Cannot finalize sheet index: {'; '.join(validation['errors'])}"
        )

    project_id = revision.package.project_id
    record_plan_audit(
        project_id=project_id,
        event_type="sheet_index_finalized",
        detail={
            "revision_id": revision.id,
            "total_sheets": validation["total_sheets"],
        },
    )

    if commit:
        db.session.commit()

    return validation

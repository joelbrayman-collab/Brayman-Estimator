"""FG-010 / M012 take-off services — extraction runs, review, packages.

Provider-neutral. No estimate, labour, or pricing writes. No external AI calls.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from app import db
from app.models import Project
from app.plan_intelligence.audit import record_plan_audit
from app.plan_intelligence.models import (
    TAKEOFF_ELEMENT_INTERIOR_DOOR,
    DrawingPackage,
    DrawingRevision,
    PlanDocument,
    PlanPage,
    PlanSheet,
    PlanSheetPage,
    TakeoffCandidate,
    TakeoffExtractionRun,
    TakeoffPackage,
    TakeoffPackageItem,
)
from app.plan_intelligence.services import PlanIntelligenceServiceError
from app.plan_intelligence.takeoff_extractors import (
    confidence_band_for,
    extractor_config_hash,
    get_extractor,
)

MAX_SHEETS_PER_RUN = 2
INCLUDED_PACKAGE_STATUSES = frozenset({"accepted", "adjusted"})
TERMINAL_CANDIDATE_STATUSES = frozenset(
    {"accepted", "adjusted", "rejected", "duplicate", "not_applicable"}
)
FORBIDDEN_APPROVER_ACTORS = frozenset(
    {
        "",
        "system",
        "ai",
        "mock-extractor",
        "calibai-mock",
        "extractor",
    }
)


def _require_actor(actor: Optional[str], *, for_approval: bool = False) -> str:
    value = (actor or "").strip()
    if not value:
        raise PlanIntelligenceServiceError("A human actor string is required.")
    if for_approval and value.lower() in FORBIDDEN_APPROVER_ACTORS:
        raise PlanIntelligenceServiceError(
            "AI/system actor cannot approve a take-off package."
        )
    if value.lower() in FORBIDDEN_APPROVER_ACTORS and for_approval:
        raise PlanIntelligenceServiceError(
            "AI/system actor cannot approve a take-off package."
        )
    return value


def _require_review_actor(actor: Optional[str]) -> str:
    value = (actor or "").strip()
    if not value:
        raise PlanIntelligenceServiceError("A human actor string is required.")
    if value.lower() in FORBIDDEN_APPROVER_ACTORS:
        raise PlanIntelligenceServiceError("AI/system actor cannot review candidates.")
    return value


def validate_normalized_bbox(geometry: Any) -> Dict[str, Any]:
    """ADR-027: bbox coordinates must lie in [0,1]×[0,1]."""
    if not isinstance(geometry, dict):
        raise PlanIntelligenceServiceError("Geometry must be a bbox object.")
    try:
        x1 = float(geometry["x1"])
        y1 = float(geometry["y1"])
        x2 = float(geometry["x2"])
        y2 = float(geometry["y2"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PlanIntelligenceServiceError(
            "Geometry bbox requires numeric x1, y1, x2, y2."
        ) from exc
    for name, val in (("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2)):
        if val < 0.0 or val > 1.0:
            raise PlanIntelligenceServiceError(
                f"Geometry {name}={val} is outside normalized [0.0, 1.0]."
            )
    if x2 < x1 or y2 < y1:
        raise PlanIntelligenceServiceError("Geometry bbox must have x2>=x1 and y2>=y1.")
    return {"type": "bbox", "x1": x1, "y1": y1, "x2": x2, "y2": y2}


def _project_for_org(organization_id: str, project_id: int) -> Project:
    if not organization_id:
        raise PlanIntelligenceServiceError("Unknown organization.")
    project = Project.query.filter_by(
        id=project_id, organization_id=organization_id
    ).first()
    if project is None:
        raise PlanIntelligenceServiceError("Project not found for this organization.")
    return project


def _get_run(organization_id: str, run_id: int) -> TakeoffExtractionRun:
    run = TakeoffExtractionRun.query.filter_by(
        id=run_id, organization_id=organization_id
    ).first()
    if run is None:
        raise PlanIntelligenceServiceError("Take-off run not found.")
    return run


def _get_candidate(organization_id: str, candidate_id: int) -> TakeoffCandidate:
    cand = TakeoffCandidate.query.filter_by(
        id=candidate_id, organization_id=organization_id
    ).first()
    if cand is None:
        raise PlanIntelligenceServiceError("Take-off candidate not found.")
    return cand


def _get_package(organization_id: str, package_id: int) -> TakeoffPackage:
    pkg = TakeoffPackage.query.filter_by(
        id=package_id, organization_id=organization_id
    ).first()
    if pkg is None:
        raise PlanIntelligenceServiceError("Take-off package not found.")
    return pkg


def _eligible_architectural_mappings(
    document: PlanDocument,
    revision: DrawingRevision,
    sheet_ids: Optional[Sequence[int]] = None,
) -> List[Dict[str, Any]]:
    if document.is_archived:
        raise PlanIntelligenceServiceError("Archived plan documents are ineligible.")
    if not document.has_text_layer:
        raise PlanIntelligenceServiceError(
            "Plan document is not a searchable PDF (no text layer)."
        )
    if document not in revision.documents:
        raise PlanIntelligenceServiceError(
            "Plan document is not a member of the requested drawing revision."
        )

    mappings = (
        PlanSheetPage.query.join(PlanSheet)
        .filter(
            PlanSheet.drawing_revision_id == revision.id,
            PlanSheetPage.plan_document_id == document.id,
            PlanSheet.discipline_code == "ARCH",
            PlanSheet.review_status != "void",
        )
        .order_by(PlanSheet.id, PlanSheetPage.page_index)
        .all()
    )
    if sheet_ids:
        wanted = set(int(s) for s in sheet_ids)
        mappings = [m for m in mappings if m.sheet_id in wanted]
        missing = wanted - {m.sheet_id for m in mappings}
        if missing:
            raise PlanIntelligenceServiceError(
                "Requested sheets are not eligible architectural floor-plan sheets."
            )

    unique_sheet_ids = []
    for m in mappings:
        if m.sheet_id not in unique_sheet_ids:
            unique_sheet_ids.append(m.sheet_id)
    if len(unique_sheet_ids) == 0:
        raise PlanIntelligenceServiceError(
            "No eligible architectural sheets mapped to this document."
        )
    if len(unique_sheet_ids) > MAX_SHEETS_PER_RUN:
        raise PlanIntelligenceServiceError(
            f"POC runs may include at most {MAX_SHEETS_PER_RUN} sheets."
        )

    scope = []
    for m in mappings:
        page = PlanPage.query.filter_by(
            plan_document_id=document.id, page_index=m.page_index
        ).first()
        if page is None or not page.has_text:
            raise PlanIntelligenceServiceError(
                "Mapped page is not searchable/text-capable."
            )
        scope.append(
            {
                "plan_sheet_id": m.sheet_id,
                "plan_page_id": page.id,
                "page_index": m.page_index,
                "sheet_number": m.sheet.number,
                "sheet_title": m.sheet.title,
            }
        )
    return scope


def start_extraction_run(
    *,
    organization_id: str,
    project_id: int,
    plan_document_id: int,
    drawing_revision_id: int,
    created_by: str,
    element_type: str = TAKEOFF_ELEMENT_INTERIOR_DOOR,
    sheet_ids: Optional[Sequence[int]] = None,
) -> TakeoffExtractionRun:
    """Create a new extraction run and execute the authorized mock extractor."""
    actor = _require_actor(created_by)
    project = _project_for_org(organization_id, project_id)
    if element_type != TAKEOFF_ELEMENT_INTERIOR_DOOR:
        raise PlanIntelligenceServiceError(
            f"Element type '{element_type}' is not authorized for M012."
        )

    document = PlanDocument.query.filter_by(
        id=plan_document_id, project_id=project.id
    ).first()
    if document is None:
        raise PlanIntelligenceServiceError("Plan document not found.")

    revision = (
        DrawingRevision.query.join(DrawingPackage)
        .filter(
            DrawingRevision.id == drawing_revision_id,
            DrawingPackage.project_id == project.id,
        )
        .first()
    )
    if revision is None:
        raise PlanIntelligenceServiceError("Drawing revision not found.")

    scope = _eligible_architectural_mappings(document, revision, sheet_ids)
    extractor = get_extractor(element_type)
    config = extractor.config_payload()
    config_hash = extractor_config_hash(config)

    run = TakeoffExtractionRun(
        organization_id=organization_id,
        project_id=project.id,
        plan_document_id=document.id,
        drawing_revision_id=revision.id,
        element_type=element_type,
        eligible_scope=scope,
        extraction_method=extractor.extraction_method,
        provider=extractor.provider,
        model_name=extractor.model_name,
        model_version=extractor.model_version,
        config_hash=config_hash,
        status="queued",
        created_by=actor,
    )
    db.session.add(run)
    db.session.flush()
    record_plan_audit(
        project_id=project.id,
        event_type="takeoff.run.create",
        plan_document_id=document.id,
        extraction_run_id=run.id,
        detail={"element_type": element_type, "created_by": actor},
    )

    run.status = "running"
    run.started_at = datetime.utcnow()
    record_plan_audit(
        project_id=project.id,
        event_type="takeoff.run.start",
        plan_document_id=document.id,
        extraction_run_id=run.id,
        detail={"provider": extractor.provider, "model": extractor.model_name},
    )

    try:
        extracted = extractor.extract(element_type=element_type, eligible_scope=scope)
        for item in extracted:
            geom = validate_normalized_bbox(item.geometry_data)
            numeric = float(item.confidence_numeric)
            if numeric < 0.0 or numeric > 1.0:
                raise PlanIntelligenceServiceError(
                    "Confidence must be in [0.0, 1.0]."
                )
            cand = TakeoffCandidate(
                organization_id=organization_id,
                project_id=project.id,
                takeoff_run_id=run.id,
                plan_document_id=document.id,
                drawing_revision_id=revision.id,
                plan_page_id=item.plan_page_id,
                plan_sheet_id=item.plan_sheet_id,
                element_type=item.element_type,
                quantity_contribution=float(item.quantity_contribution),
                geometry_data=geom,
                confidence_numeric=numeric,
                confidence_band=confidence_band_for(numeric),
                source_evidence=item.source_evidence,
                status="suggested",
            )
            db.session.add(cand)
            db.session.flush()
            record_plan_audit(
                project_id=project.id,
                event_type="takeoff.candidate.create",
                plan_document_id=document.id,
                sheet_id=item.plan_sheet_id,
                extraction_run_id=run.id,
                takeoff_candidate_id=cand.id,
                detail={
                    "confidence": numeric,
                    "band": cand.confidence_band,
                    "status": "suggested",
                },
            )
        run.candidate_count = len(extracted)
        run.status = "succeeded"
        run.finished_at = datetime.utcnow()
        record_plan_audit(
            project_id=project.id,
            event_type="takeoff.run.complete",
            plan_document_id=document.id,
            extraction_run_id=run.id,
            detail={"candidate_count": run.candidate_count},
        )
    except Exception as exc:
        run.status = "failed"
        run.finished_at = datetime.utcnow()
        run.error_summary = str(exc)
        record_plan_audit(
            project_id=project.id,
            event_type="takeoff.run.fail",
            plan_document_id=document.id,
            extraction_run_id=run.id,
            detail={"error": str(exc)},
        )
        db.session.commit()
        if isinstance(exc, PlanIntelligenceServiceError):
            raise
        raise PlanIntelligenceServiceError(f"Extraction failed: {exc}") from exc

    db.session.commit()
    return run


def list_runs_for_project(organization_id: str, project_id: int) -> List[TakeoffExtractionRun]:
    _project_for_org(organization_id, project_id)
    return (
        TakeoffExtractionRun.query.filter_by(
            organization_id=organization_id, project_id=project_id
        )
        .order_by(TakeoffExtractionRun.id.desc())
        .all()
    )


def get_run_or_404(organization_id: str, run_id: int) -> TakeoffExtractionRun:
    return _get_run(organization_id, run_id)


def get_candidate_or_404(organization_id: str, candidate_id: int) -> TakeoffCandidate:
    return _get_candidate(organization_id, candidate_id)


def get_package_or_404(organization_id: str, package_id: int) -> TakeoffPackage:
    return _get_package(organization_id, package_id)


def review_candidate(
    *,
    organization_id: str,
    candidate_id: int,
    action: str,
    reviewed_by: str,
    review_reason: Optional[str] = None,
    reviewed_quantity: Optional[float] = None,
    reviewed_geometry: Optional[Dict[str, Any]] = None,
    canonical_candidate_id: Optional[int] = None,
) -> TakeoffCandidate:
    actor = _require_review_actor(reviewed_by)
    cand = _get_candidate(organization_id, candidate_id)
    action = (action or "").strip().lower()
    if action not in ("accept", "adjust", "reject", "duplicate", "not_applicable"):
        raise PlanIntelligenceServiceError(f"Unknown review action: {action}")

    if action == "accept":
        cand.status = "accepted"
        cand.reviewed_quantity = cand.quantity_contribution
        cand.reviewed_geometry = None
        cand.review_reason = (review_reason or "").strip() or None
        event = "takeoff.candidate.accept"
    elif action == "adjust":
        reason = (review_reason or "").strip()
        if not reason:
            raise PlanIntelligenceServiceError(
                "Adjustment reason is required when quantity or geometry changes."
            )
        if reviewed_quantity is None and reviewed_geometry is None:
            raise PlanIntelligenceServiceError(
                "Adjust requires a reviewed quantity and/or geometry."
            )
        qty = (
            float(reviewed_quantity)
            if reviewed_quantity is not None
            else float(cand.quantity_contribution)
        )
        if qty < 0:
            raise PlanIntelligenceServiceError("Reviewed quantity cannot be negative.")
        geom = (
            validate_normalized_bbox(reviewed_geometry)
            if reviewed_geometry is not None
            else None
        )
        cand.status = "adjusted"
        cand.reviewed_quantity = qty
        cand.reviewed_geometry = geom
        cand.review_reason = reason
        event = "takeoff.candidate.adjust"
    elif action == "reject":
        cand.status = "rejected"
        cand.reviewed_quantity = 0.0
        cand.review_reason = (review_reason or "").strip() or None
        event = "takeoff.candidate.reject"
    elif action == "duplicate":
        if canonical_candidate_id is None:
            raise PlanIntelligenceServiceError(
                "Duplicate decisions require a canonical_candidate_id."
            )
        if int(canonical_candidate_id) == cand.id:
            raise PlanIntelligenceServiceError(
                "A candidate cannot be a duplicate of itself."
            )
        canonical = _get_candidate(organization_id, int(canonical_candidate_id))
        if canonical.takeoff_run_id != cand.takeoff_run_id:
            raise PlanIntelligenceServiceError(
                "Duplicate canonical candidate must belong to the same extraction run."
            )
        if canonical.drawing_revision_id != cand.drawing_revision_id:
            raise PlanIntelligenceServiceError(
                "Cannot merge duplicates across drawing revisions."
            )
        reason = (review_reason or "").strip()
        if not reason:
            raise PlanIntelligenceServiceError("Duplicate decisions require a reason.")
        cand.status = "duplicate"
        cand.canonical_candidate_id = canonical.id
        cand.reviewed_quantity = 0.0
        cand.review_reason = reason
        event = "takeoff.candidate.duplicate"
    else:
        cand.status = "not_applicable"
        cand.reviewed_quantity = 0.0
        cand.review_reason = (review_reason or "").strip() or None
        event = "takeoff.candidate.not_applicable"

    cand.reviewed_by = actor
    cand.reviewed_at = datetime.utcnow()
    record_plan_audit(
        project_id=cand.project_id,
        event_type=event,
        plan_document_id=cand.plan_document_id,
        sheet_id=cand.plan_sheet_id,
        extraction_run_id=cand.takeoff_run_id,
        takeoff_candidate_id=cand.id,
        detail={
            "status": cand.status,
            "reviewed_by": actor,
            "reviewed_quantity": cand.reviewed_quantity,
            "canonical_candidate_id": cand.canonical_candidate_id,
            "reason": cand.review_reason,
        },
        commit=True,
    )
    return cand


def included_quantity_for_candidate(cand: TakeoffCandidate) -> float:
    if cand.status not in INCLUDED_PACKAGE_STATUSES:
        return 0.0
    if cand.reviewed_quantity is None:
        return float(cand.quantity_contribution)
    return float(cand.reviewed_quantity)


def compute_run_reviewed_total(run: TakeoffExtractionRun) -> float:
    return sum(included_quantity_for_candidate(c) for c in run.candidates)


def _assert_run_review_complete(run: TakeoffExtractionRun) -> None:
    unresolved = [c for c in run.candidates if c.status == "suggested"]
    if unresolved:
        raise PlanIntelligenceServiceError(
            "Cannot approve a package while candidates remain suggested."
        )


def _next_package_version(
    organization_id: str, project_id: int, drawing_revision_id: int, element_type: str
) -> int:
    existing = (
        TakeoffPackage.query.filter_by(
            organization_id=organization_id,
            project_id=project_id,
            drawing_revision_id=drawing_revision_id,
            element_type=element_type,
        )
        .order_by(TakeoffPackage.version_number.desc())
        .first()
    )
    return 1 if existing is None else existing.version_number + 1


def _freeze_items(package: TakeoffPackage, run: TakeoffExtractionRun) -> None:
    included = [c for c in run.candidates if c.status in INCLUDED_PACKAGE_STATUSES]
    for cand in included:
        page = cand.page
        sheet = cand.sheet
        geom = cand.reviewed_geometry or cand.geometry_data
        item = TakeoffPackageItem(
            organization_id=package.organization_id,
            project_id=package.project_id,
            takeoff_package_id=package.id,
            takeoff_candidate_id=cand.id,
            takeoff_run_id=run.id,
            plan_document_id=cand.plan_document_id,
            drawing_revision_id=cand.drawing_revision_id,
            plan_page_id=cand.plan_page_id,
            plan_sheet_id=cand.plan_sheet_id,
            page_index=page.page_index if page is not None else 0,
            sheet_number=sheet.number if sheet is not None else None,
            sheet_name=sheet.title if sheet is not None else None,
            element_type=cand.element_type,
            review_status=cand.status,
            quantity_contribution=cand.quantity_contribution,
            reviewed_quantity=included_quantity_for_candidate(cand),
            geometry_data=geom,
            confidence_numeric=cand.confidence_numeric,
            confidence_band=cand.confidence_band,
            source_evidence=cand.source_evidence,
            reviewed_by=cand.reviewed_by,
            review_reason=cand.review_reason,
        )
        db.session.add(item)


def create_draft_package(
    *,
    organization_id: str,
    run_id: int,
    created_by: str,
    notes: Optional[str] = None,
) -> TakeoffPackage:
    actor = _require_actor(created_by)
    run = _get_run(organization_id, run_id)
    if run.status != "succeeded":
        raise PlanIntelligenceServiceError("Only succeeded runs can form a package.")
    version = _next_package_version(
        organization_id, run.project_id, run.drawing_revision_id, run.element_type
    )
    total = compute_run_reviewed_total(run)
    package = TakeoffPackage(
        organization_id=organization_id,
        project_id=run.project_id,
        drawing_revision_id=run.drawing_revision_id,
        takeoff_run_id=run.id,
        element_type=run.element_type,
        version_number=version,
        status="draft",
        approved_total=total,
        approved_unit="count",
        notes=notes,
        provenance={
            "run_id": run.id,
            "provider": run.provider,
            "model_name": run.model_name,
            "model_version": run.model_version,
            "config_hash": run.config_hash,
            "plan_document_id": run.plan_document_id,
        },
        created_by=actor,
    )
    db.session.add(package)
    db.session.flush()
    _freeze_items(package, run)
    record_plan_audit(
        project_id=run.project_id,
        event_type="takeoff.package.create",
        plan_document_id=run.plan_document_id,
        extraction_run_id=run.id,
        takeoff_package_id=package.id,
        detail={"version": version, "draft_total": total, "created_by": actor},
        commit=True,
    )
    return package


def approve_package(
    *,
    organization_id: str,
    package_id: int,
    approved_by: str,
) -> TakeoffPackage:
    actor = _require_actor(approved_by, for_approval=True)
    package = _get_package(organization_id, package_id)
    if package.status != "draft":
        raise PlanIntelligenceServiceError("Only draft packages can be approved.")
    run = package.run
    _assert_run_review_complete(run)
    total = compute_run_reviewed_total(run)
    # Re-freeze so approval snapshot matches current reviewed state
    for item in list(package.items):
        db.session.delete(item)
    db.session.flush()
    _freeze_items(package, run)
    package.approved_total = total
    package.status = "approved"
    package.approved_by = actor
    package.approved_at = datetime.utcnow()

    prior = (
        TakeoffPackage.query.filter(
            TakeoffPackage.organization_id == organization_id,
            TakeoffPackage.project_id == package.project_id,
            TakeoffPackage.drawing_revision_id == package.drawing_revision_id,
            TakeoffPackage.element_type == package.element_type,
            TakeoffPackage.status == "approved",
            TakeoffPackage.id != package.id,
        ).all()
    )
    for old in prior:
        old.status = "superseded"
        old.superseded_by_id = package.id
        record_plan_audit(
            project_id=package.project_id,
            event_type="takeoff.package.supersede",
            plan_document_id=run.plan_document_id,
            extraction_run_id=run.id,
            takeoff_package_id=old.id,
            detail={"superseded_by": package.id, "approved_by": actor},
        )

    record_plan_audit(
        project_id=package.project_id,
        event_type="takeoff.package.approve",
        plan_document_id=run.plan_document_id,
        extraction_run_id=run.id,
        takeoff_package_id=package.id,
        detail={"approved_total": total, "approved_by": actor},
        commit=True,
    )
    return package


def assert_package_immutable(package: TakeoffPackage) -> None:
    if package.status in ("approved", "superseded"):
        raise PlanIntelligenceServiceError(
            "Approved take-off packages are immutable."
        )


def mutate_package(
    *,
    organization_id: str,
    package_id: int,
    **_kwargs: Any,
) -> TakeoffPackage:
    """Refuse writes to approved/superseded packages (item, quantity, geometry, reviewer)."""
    package = _get_package(organization_id, package_id)
    assert_package_immutable(package)
    raise PlanIntelligenceServiceError("Draft package mutation is not exposed in FG-010.")


def list_packages_for_project(
    organization_id: str, project_id: int
) -> List[TakeoffPackage]:
    _project_for_org(organization_id, project_id)
    return (
        TakeoffPackage.query.filter_by(
            organization_id=organization_id, project_id=project_id
        )
        .order_by(TakeoffPackage.id.desc())
        .all()
    )

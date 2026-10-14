"""Generate, store, save and attach construction drawing sets.

One drawing set comes from one construction model revision and the current
product facts, through the same basis and takeoff the deck takeoff page uses.
The drawing engine lays that out; it calculates no quantity of its own.

Sets are write-once. Generating again from the same inputs returns the
existing set. A set whose model revision or product facts are no longer the
project's current ones is outdated: it stays readable but cannot be attached.
"""

from __future__ import annotations

import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pypdf import PdfReader, PdfWriter

from app import db
from app.models import Project
from app.models.construction_drawing import (
    ATTACH_ESTIMATE_VERSION,
    ATTACH_PROPOSAL,
    ATTACH_SUPPLIER_REQUEST,
    ATTACHMENT_KINDS,
    ConstructionDrawingAttachment,
    ConstructionDrawingSet,
)
from app.models.estimate import Estimate, EstimateVersion
from app.models.project_construction_model import ProjectConstructionModelRevision
from app.models.proposal import Proposal
from app.services.deck_takeoff import storage
from app.services.deck_takeoff.basis import read_basis, source_record
from app.services.deck_takeoff.geometry import GeometryRefusal
from app.services.deck_takeoff.product_facts import ProductFactError
from app.services.deck_takeoff.takeoff import calculate_pool_deck_takeoff
from app.services.project_construction_model import load_current_revision

ENGINE_VERSION = "deck-drawings-1.1"  # 1.1: stair nosing past the riser, back gap (14 Oct 2026)
ATTACHABLE_PROPOSAL_STATUSES = ("Draft", "Ready")
LOGO = Path(__file__).resolve().parents[1] / "static" / "branding" / "brayman-construction-logo.png"


class DrawingError(ValueError):
    """A drawing set cannot be generated, saved or attached. The message says why."""


@dataclass
class DrawingState:
    current: bool
    reasons: List[str]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _project(organization_id: str, project_id: int) -> Project:
    project = Project.query.filter_by(id=project_id, organization_id=organization_id).one_or_none()
    if project is None:
        raise DrawingError("The project was not found.")
    return project


def model_revisions(organization_id: str, project_id: int) -> List[ProjectConstructionModelRevision]:
    return (
        ProjectConstructionModelRevision.query.filter_by(organization_id=organization_id, project_id=project_id)
        .order_by(ProjectConstructionModelRevision.revision_number.desc())
        .all()
    )


def drawing_sets(organization_id: str, project_id: int) -> List[ConstructionDrawingSet]:
    return (
        ConstructionDrawingSet.query.filter_by(organization_id=organization_id, project_id=project_id)
        .order_by(ConstructionDrawingSet.drawing_revision.desc())
        .all()
    )


def get_drawing_set(organization_id: str, project_id: int, set_id: int) -> ConstructionDrawingSet:
    found = ConstructionDrawingSet.query.filter_by(id=set_id, organization_id=organization_id, project_id=project_id).one_or_none()
    if found is None:
        raise DrawingError("The drawing set was not found on this project.")
    return found


def _inputs(project: Project, revision, facts_record) -> Tuple[object, Dict, Dict, Optional[float]]:
    facts = (facts_record or {}).get("facts") or {}
    content = revision.content_json or {}
    basis, missing = read_basis(content, source_record(project_id=project.id, revision=revision))
    if basis is None:
        raise DrawingError("The construction model is missing facts the drawings need: " + "; ".join(missing) + ".")
    try:
        takeoff = calculate_pool_deck_takeoff(basis, facts)
    except (GeometryRefusal, ProductFactError) as exc:
        raise DrawingError(str(exc)) from exc
    lower = None
    for level in content.get("levels") or []:
        if level.get("id") == "lower-walk" and isinstance(level.get("elevation"), (int, float)):
            lower = float(level["elevation"]) * 12.0
    if lower is None:
        for dim in content.get("dimensions") or []:
            if dim.get("id") == "lower-walking-surface-height" and dim.get("unit") == "in":
                lower = float(dim["value"])
    return basis, takeoff, facts, lower


def input_fingerprint(project: Project, revision, facts_record) -> str:
    payload = {
        "engine": ENGINE_VERSION,
        "model_sha256": revision.content_sha256,
        "model_revision": revision.revision_number,
        "facts": (facts_record or {}).get("facts") or {},
        "facts_version": (facts_record or {}).get("version"),
        "project": [project.name, project.address or ""],
    }
    return _sha(json.dumps(payload, sort_keys=True, default=str).encode("utf-8"))


def render_set(project: Project, revision, facts_record, *, drawing_revision: int, fingerprint: str, date: str):
    """Build the sheets and render PDF and DXF. Pure: writes nothing."""
    from app.services.drawings.deck import DeckDrawingInput, DeckDrawingSet
    from app.services.drawings.dxf import render_dxf
    from app.services.drawings.pdf import render_pdf

    basis, takeoff, facts, lower = _inputs(project, revision, facts_record)
    data = DeckDrawingInput(
        basis=basis,
        takeoff=takeoff,
        facts=facts,
        project_name=project.name,
        project_address=project.address or "",
        model_revision=f"R{revision.revision_number}",
        drawing_revision=f"D{drawing_revision}",
        date=date,
        fingerprint=fingerprint[:10].upper(),
        lower_walk_in=lower,
        logo_path=str(LOGO) if LOGO.exists() else None,
    )
    data.stair_results = (revision.content_json or {}).get("stair_results") or []
    try:
        builder = DeckDrawingSet(data)
        sheets = builder.sheets()
    except (ValueError, GeometryRefusal) as exc:
        raise DrawingError(str(exc)) from exc
    title = f"{project.name} — construction drawings D{drawing_revision}"
    pdf = render_pdf(sheets, title=title, logo_path=data.logo_path)
    dxf = render_dxf(sheets, title=title)
    index = [{"number": s.number, "title": s.title} for s in sheets]
    return {"sheets": sheets, "pdf": pdf, "dxf": dxf, "index": index, "takeoff": takeoff, "basis": basis}


def generate_drawing_set(*, organization_id: str, project_id: int, actor: str, revision_id: Optional[int] = None):
    """Generate (or return the existing) drawing set. Returns (set, created)."""
    actor = (actor or "").strip()
    if not actor:
        raise DrawingError("The person generating the drawings is required.")
    project = _project(organization_id, project_id)
    if revision_id:
        revision = ProjectConstructionModelRevision.query.filter_by(
            id=revision_id, organization_id=organization_id, project_id=project.id
        ).one_or_none()
        if revision is None:
            raise DrawingError("That construction model revision is not on this project.")
    else:
        revision = load_current_revision(organization_id=organization_id, project_id=project.id)
        if revision is None:
            raise DrawingError("This project has no stored construction model revision.")
    facts_record = storage.current_product_facts(organization_id, project.id)
    fingerprint = input_fingerprint(project, revision, facts_record)
    existing = ConstructionDrawingSet.query.filter_by(project_id=project.id, input_fingerprint=fingerprint).one_or_none()
    if existing is not None:
        return existing, False
    last = db.session.query(db.func.max(ConstructionDrawingSet.drawing_revision)).filter_by(project_id=project.id).scalar() or 0
    number = last + 1
    now = datetime.utcnow()
    rendered = render_set(project, revision, facts_record, drawing_revision=number, fingerprint=fingerprint, date=now.date().isoformat())
    record = ConstructionDrawingSet(
        organization_id=organization_id,
        project_id=project.id,
        construction_model_revision_id=revision.id,
        model_revision_number=revision.revision_number,
        model_content_sha256=revision.content_sha256,
        product_facts_version=(facts_record or {}).get("version"),
        takeoff_fingerprint=rendered["takeoff"]["fingerprint"],
        drawing_revision=number,
        drawing_type="pool_deck",
        engine_version=ENGINE_VERSION,
        input_fingerprint=fingerprint,
        sheet_count=len(rendered["index"]),
        sheet_index_json=json.dumps(rendered["index"]),
        pdf_bytes=rendered["pdf"],
        pdf_sha256=_sha(rendered["pdf"]),
        dxf_bytes=rendered["dxf"],
        dxf_sha256=_sha(rendered["dxf"]),
        created_by=actor[:120],
        created_at=now,
    )
    db.session.add(record)
    db.session.commit()
    return record, True


def drawing_state(drawing_set: ConstructionDrawingSet) -> DrawingState:
    reasons = []
    current = load_current_revision(organization_id=drawing_set.organization_id, project_id=drawing_set.project_id)
    if current is None or current.id != drawing_set.construction_model_revision_id:
        reasons.append(
            f"The construction model is now revision R{current.revision_number}." if current is not None else "The construction model revision is gone."
        )
    facts = storage.current_product_facts(drawing_set.organization_id, drawing_set.project_id)
    if (facts or {}).get("version") != drawing_set.product_facts_version:
        reasons.append("The product facts have changed since these drawings were generated.")
    return DrawingState(current=not reasons, reasons=reasons)


def save_to_plans(drawing_set: ConstructionDrawingSet):
    """Register the drawing PDF as a project plan. A second call returns the same plan."""
    from app.plan_intelligence.services import PlanIntelligenceServiceError, store_generated_plan_pdf

    if drawing_set.plan_document_id is not None:
        return drawing_set.plan_document_id, False
    project = _project(drawing_set.organization_id, drawing_set.project_id)
    try:
        document = store_generated_plan_pdf(project, drawing_set.pdf_bytes, f"construction-drawings-{drawing_set.label}.pdf")
    except PlanIntelligenceServiceError as exc:
        db.session.rollback()
        raise DrawingError(str(exc)) from exc
    drawing_set.plan_document_id = document.id
    drawing_set.saved_to_plans_at = datetime.utcnow()
    db.session.commit()
    return document.id, True


def _target_filter(kind: str, target):
    if kind == ATTACH_ESTIMATE_VERSION:
        return {"estimate_version_id": int(target)}
    if kind == ATTACH_PROPOSAL:
        return {"proposal_id": int(target)}
    return {"supplier_request_id": str(target)}


def _check_target(drawing_set: ConstructionDrawingSet, kind: str, target) -> None:
    org, project_id = drawing_set.organization_id, drawing_set.project_id
    if kind == ATTACH_ESTIMATE_VERSION:
        version = EstimateVersion.query.filter_by(id=int(target)).one_or_none()
        estimate = Estimate.query.filter_by(id=version.estimate_id).one_or_none() if version else None
        if version is None or estimate is None or estimate.project_id != project_id or getattr(estimate, "organization_id", org) != org:
            raise DrawingError("That estimate version is not on this project.")
        if version.is_locked:
            raise DrawingError("That estimate version is locked. Attach the drawings to a new version.")
    elif kind == ATTACH_PROPOSAL:
        proposal = Proposal.query.filter_by(id=int(target), organization_id=org).one_or_none()
        estimate = Estimate.query.filter_by(id=proposal.estimate_id).one_or_none() if proposal else None
        if proposal is None or estimate is None or estimate.project_id != project_id:
            raise DrawingError("That proposal is not on this project.")
        if proposal.status not in ATTACHABLE_PROPOSAL_STATUSES:
            raise DrawingError(f"That proposal is {proposal.status}. Issued proposals keep the drawings they were issued with.")
    elif kind == ATTACH_SUPPLIER_REQUEST:
        try:
            manifest = storage.load_request(org, project_id, str(target))
        except storage.TakeoffStorageError:
            manifest = None
        if manifest is None:
            raise DrawingError("That supplier request was not issued on this project.")
        if manifest.get("takeoff_fingerprint") != drawing_set.takeoff_fingerprint:
            raise DrawingError("These drawings were not generated from the takeoff that supplier request was issued from. Generate drawings from the same takeoff first.")
    else:
        raise DrawingError("Unknown attachment target.")


def attach(drawing_set: ConstructionDrawingSet, kind: str, target, actor: str) -> Tuple[ConstructionDrawingAttachment, bool]:
    if kind not in ATTACHMENT_KINDS:
        raise DrawingError("Unknown attachment target.")
    actor = (actor or "").strip()
    if not actor:
        raise DrawingError("The person attaching the drawings is required.")
    state = drawing_state(drawing_set)
    if not state.current:
        raise DrawingError("These drawings are outdated: " + " ".join(state.reasons) + " Generate a new drawing revision first.")
    _check_target(drawing_set, kind, target)
    flt = _target_filter(kind, target)
    active = ConstructionDrawingAttachment.query.filter_by(target_kind=kind, superseded_at=None, **flt).all()
    for row in active:
        if row.drawing_set_id == drawing_set.id:
            return row, False
    now = datetime.utcnow()
    for row in active:
        row.superseded_at = now
    row = ConstructionDrawingAttachment(
        organization_id=drawing_set.organization_id,
        project_id=drawing_set.project_id,
        drawing_set_id=drawing_set.id,
        target_kind=kind,
        drawing_pdf_sha256=drawing_set.pdf_sha256,
        attached_by=actor[:120],
        attached_at=now,
        **flt,
    )
    db.session.add(row)
    db.session.commit()
    return row, True


def current_attachment(kind: str, target) -> Optional[ConstructionDrawingAttachment]:
    """The drawing set currently attached to an estimate version, proposal or supplier request.

    Estimate print and proposal PDF call this on every download. If the drawing tables do
    not exist yet (the moments between a deploy and migration v2c3d4e5f6a7), the document
    is served without drawings instead of failing.
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError

    try:
        return (
            ConstructionDrawingAttachment.query.filter_by(target_kind=kind, superseded_at=None, **_target_filter(kind, target))
            .order_by(ConstructionDrawingAttachment.id.desc())
            .first()
        )
    except (OperationalError, ProgrammingError):
        db.session.rollback()
        return None


def attachments_for_set(drawing_set: ConstructionDrawingSet) -> List[ConstructionDrawingAttachment]:
    return ConstructionDrawingAttachment.query.filter_by(drawing_set_id=drawing_set.id).order_by(ConstructionDrawingAttachment.id).all()


def append_drawings(base_pdf: bytes, attachment: Optional[ConstructionDrawingAttachment]) -> bytes:
    """Return ``base_pdf`` with the attached drawing pages after it.

    The base document keeps its own pages and form fields; the drawing pages
    follow. The attached copy is checked against the SHA-256 recorded when it
    was attached.
    """
    if attachment is None:
        return base_pdf
    drawing = attachment.drawing_set
    if _sha(drawing.pdf_bytes) != attachment.drawing_pdf_sha256:
        raise DrawingError("The attached drawing PDF does not match the copy recorded when it was attached.")
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(base_pdf)))
    for page in PdfReader(io.BytesIO(drawing.pdf_bytes)).pages:
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()

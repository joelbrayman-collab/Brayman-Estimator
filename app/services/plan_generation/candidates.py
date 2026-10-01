"""Persist a rendered drawing, then register it only on explicit use.

Rendering does not create a PlanDocument. Use does.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app import db
from app.models import Project
from app.models.plan_generation_candidate import PlanGenerationCandidate
from app.plan_intelligence.models import PLAN_ORIGIN_GENERATED
from app.plan_intelligence.services import (
    PlanIntelligenceServiceError,
    store_generated_plan_pdf,
)
from app.services.plan_generation.render import render_plan_generation

CODE_PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
CODE_CANDIDATE_NOT_RENDERED = "CANDIDATE_NOT_RENDERED"
CODE_CANDIDATE_NOT_FOUND = "CANDIDATE_NOT_FOUND"
CODE_CANDIDATE_NOT_IN_PROJECT = "CANDIDATE_NOT_IN_PROJECT"
CODE_CANDIDATE_NOT_USABLE = "CANDIDATE_NOT_USABLE"


@dataclass(frozen=True)
class CandidatePersistResult:
    persisted: bool
    candidate: Optional[PlanGenerationCandidate]
    issues: tuple
    code: Optional[str] = None


@dataclass(frozen=True)
class CandidateUseResult:
    used: bool
    candidate_id: Optional[int]
    plan_document_id: Optional[int]
    created: bool
    code: Optional[str] = None


def persist_generated_candidate(
    organization_id: str,
    project_id: int,
    request: Any,
) -> CandidatePersistResult:
    """Render and store a candidate. This does not register a project plan."""
    project = _project(organization_id, project_id)
    if project is None:
        return CandidatePersistResult(
            persisted=False,
            candidate=None,
            issues=(),
            code=CODE_PROJECT_NOT_FOUND,
        )
    rendered = render_plan_generation(request)
    if not rendered.rendered or not rendered.pdf_bytes or rendered.manifest is None:
        return CandidatePersistResult(
            persisted=False,
            candidate=None,
            issues=rendered.issues,
            code=CODE_CANDIDATE_NOT_RENDERED,
        )
    manifest = rendered.manifest
    candidate = PlanGenerationCandidate(
        organization_id=organization_id,
        project_id=project.id,
        drawing_type=manifest["drawing_type"],
        engine_version=manifest["engine_version"],
        validation_engine_version=manifest["validation_engine_version"],
        request_fingerprint=manifest["request_fingerprint"],
        manifest_json=_json(manifest),
        uncertainty_flags_json=_json(list(manifest.get("uncertainty_flags") or [])),
        pdf_sha256=manifest["pdf_sha256"],
        pdf_bytes=rendered.pdf_bytes,
        created_at=datetime.utcnow(),
    )
    db.session.add(candidate)
    db.session.commit()
    return CandidatePersistResult(
        persisted=True,
        candidate=candidate,
        issues=(),
        code=None,
    )


def use_generated_candidate(
    organization_id: str,
    project_id: int,
    candidate_id: int,
) -> CandidateUseResult:
    """Register one candidate as a project plan. A second call returns the same plan."""
    project = _project(organization_id, project_id)
    if project is None:
        return CandidateUseResult(
            used=False,
            candidate_id=None,
            plan_document_id=None,
            created=False,
            code=CODE_PROJECT_NOT_FOUND,
        )
    candidate = PlanGenerationCandidate.query.filter_by(
        id=candidate_id,
        organization_id=organization_id,
    ).one_or_none()
    if candidate is None:
        return CandidateUseResult(
            used=False,
            candidate_id=None,
            plan_document_id=None,
            created=False,
            code=CODE_CANDIDATE_NOT_FOUND,
        )
    if candidate.project_id != project.id:
        return CandidateUseResult(
            used=False,
            candidate_id=candidate.id,
            plan_document_id=None,
            created=False,
            code=CODE_CANDIDATE_NOT_IN_PROJECT,
        )
    if candidate.plan_document_id is not None:
        return CandidateUseResult(
            used=True,
            candidate_id=candidate.id,
            plan_document_id=candidate.plan_document_id,
            created=False,
            code=None,
        )
    if not candidate.pdf_bytes or not candidate.pdf_bytes.startswith(b"%PDF"):
        return CandidateUseResult(
            used=False,
            candidate_id=candidate.id,
            plan_document_id=None,
            created=False,
            code=CODE_CANDIDATE_NOT_USABLE,
        )
    try:
        document = store_generated_plan_pdf(
            project,
            candidate.pdf_bytes,
            f"{candidate.drawing_type}.pdf",
        )
    except PlanIntelligenceServiceError:
        db.session.rollback()
        return CandidateUseResult(
            used=False,
            candidate_id=candidate.id,
            plan_document_id=None,
            created=False,
            code=CODE_CANDIDATE_NOT_USABLE,
        )
    if document.origin != PLAN_ORIGIN_GENERATED:
        db.session.rollback()
        return CandidateUseResult(
            used=False,
            candidate_id=candidate.id,
            plan_document_id=None,
            created=False,
            code=CODE_CANDIDATE_NOT_USABLE,
        )
    candidate.plan_document_id = document.id
    candidate.used_at = datetime.utcnow()
    db.session.commit()
    return CandidateUseResult(
        used=True,
        candidate_id=candidate.id,
        plan_document_id=document.id,
        created=True,
        code=None,
    )


def _project(organization_id: str, project_id: int):
    if not organization_id or project_id is None:
        return None
    return Project.query.filter_by(
        id=project_id,
        organization_id=organization_id,
    ).one_or_none()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

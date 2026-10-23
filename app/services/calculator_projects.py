"""Universal calculator-to-project connection (Guided Estimating, 23 Oct 2026).

After any calculator gives a result the person chooses:

A. Use Result Only — nothing is saved; no project or estimate changes (the calculator's own behaviour).
B. Add to Existing Project — the result (entries, units, quantities, assumptions, engine and version) is kept on
   a project the person may open, optionally on one estimating stage, using the existing "Link to a project"
   record (project_calculations). It reaches the estimate only through the existing estimate review: "Send to
   estimate review" puts it on an editable estimate version as a calculation intake, and a person confirms each
   quantity there. An issued, accepted or locked version is never changed.
C. Create New Project — the result is kept (calculator_result_carries) while the existing New Project form is
   filled in; the new project receives it as in B. Cancelling returns to the calculator with the result shown.

The same calculation is never added twice: one result_id is one record per project, and an identical result
(same Contract V1 fingerprint) on the same project and stage is the same record. The estimate review itself
refuses the same result on the same version.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app import db
from app.models.guided_estimating import RESP_NA, CalculatorResultCarry, GuidedEstimateStage
from app.models.project_calculation import (
    CALCULATORS,
    REVIEW_AWAITING,
    REVIEW_SENT,
    SOURCE_CALCULATORS,
    ProjectCalculation,
)

CARRY_LIFETIME = timedelta(days=2)
RETURN_PREFIXES = ("/calculators/", "/useful-calculators/")


class CalculatorProjectError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _clean(text, limit):
    return " ".join(str(text or "").split())[:limit]


def clean_entered(rows):
    entered = []
    for row in (rows or [])[:60]:
        if isinstance(row, dict):
            label, value = _clean(row.get("label"), 120), _clean(row.get("value"), 200)
            if label and value:
                entered.append({"label": label, "value": value})
    return entered


def _validated_payload(payload):
    if payload in (None, "", {}):
        return None
    from app.services.calculation_result_contract import validate_contract_v1

    if not isinstance(payload, dict):
        raise CalculatorProjectError("The calculation could not be read.")
    errors = validate_contract_v1(payload)
    if errors:
        raise CalculatorProjectError("This calculation cannot be carried: " + "; ".join(errors[:3]))
    return payload


def stage_for_project(organization_id, project_id, stage_id) -> Optional[GuidedEstimateStage]:
    if not stage_id:
        return None
    from app.models.guided_estimating import GuidedEstimate

    stage = GuidedEstimateStage.query.filter_by(id=int(stage_id), organization_id=organization_id).first()
    if stage is None:
        raise CalculatorProjectError("That estimating stage is not on this project.", 404)
    guided = db.session.get(GuidedEstimate, stage.guided_estimate_id)
    if guided is None or guided.project_id != project_id:
        raise CalculatorProjectError("That estimating stage is not on this project.", 404)
    if stage.parent is None and stage.is_split:
        raise CalculatorProjectError("Choose one part of that stage.")
    if stage.responsibility == RESP_NA:
        raise CalculatorProjectError("That stage is N/A on this project.")
    return stage


def stage_choices(organization_id, project_id):
    """[(stage id, label)] for the stages a result can go to on this project (none when not guided)."""
    from app.services.guided_estimating import get_guided, leaf_stages

    guided = get_guided(organization_id, project_id)
    if guided is None:
        return []
    return [(row.id, row.section_name + ("" if row.responsibility else " (not decided yet)"))
            for row in leaf_stages(guided, include_na=False)]


def save_to_project(*, organization_id, project, calculator, summary, result_text, entered, reference=None,
                    payload=None, stage_id=None, source=SOURCE_CALCULATORS, user_id=None,
                    actor_display_name="Office") -> Tuple[ProjectCalculation, bool]:
    """Option B. Returns (record, created). An identical result already on the project is returned, not doubled."""
    if calculator not in CALCULATORS:
        raise CalculatorProjectError("This calculator cannot be linked.")
    summary = _clean(summary, 600)
    result_text = str(result_text or "").strip()[:20000]
    if not summary or not result_text:
        raise CalculatorProjectError("Calculate first, then link the result.")
    payload = _validated_payload(payload)
    stage = stage_for_project(organization_id, project.id, stage_id)
    existing = _duplicate(organization_id, project.id, calculator, payload, stage, summary, result_text)
    if existing is not None:
        if stage is not None and existing.guided_stage_id is None:
            existing.guided_stage_id = stage.id
            db.session.commit()
        return existing, False
    record = ProjectCalculation(
        organization_id=organization_id, project_id=project.id, calculator=calculator,
        reference=_clean(reference, 160) or None, summary=summary, entered=clean_entered(entered),
        result_text=result_text, user_id=user_id, actor_display_name=_clean(actor_display_name, 150) or "Office",
        result_id=(payload or {}).get("result_id"), engine_id=(payload or {}).get("engine_id"),
        engine_version=(payload or {}).get("engine_version"), payload=payload, source=source,
        guided_stage_id=stage.id if stage is not None else None,
        review_status=REVIEW_AWAITING if payload else None,
    )
    db.session.add(record)
    if stage is not None:
        from app.models.guided_estimating import STATUS_NOT_STARTED, STATUS_IN_PROGRESS

        if stage.status == STATUS_NOT_STARTED:
            stage.status = STATUS_IN_PROGRESS
    db.session.commit()
    return record, True


def _duplicate(organization_id, project_id, calculator, payload, stage, summary, result_text):
    rows = ProjectCalculation.query.filter_by(organization_id=organization_id, project_id=project_id,
                                              calculator=calculator).all()
    if payload:
        from app.services.calculation_result_contract import calculation_fingerprint

        fingerprint = calculation_fingerprint(payload)
        for row in rows:
            if row.result_id and row.result_id == payload.get("result_id"):
                return row
            if row.payload and calculation_fingerprint(row.payload) == fingerprint and \
                    row.guided_stage_id == (stage.id if stage is not None else None):
                return row
        return None
    for row in rows:
        if row.payload is None and row.summary == summary and row.result_text == result_text and \
                row.guided_stage_id == (stage.id if stage is not None else None):
            return row
    return None


def target_version(organization_id, record: ProjectCalculation):
    """The editable estimate version a result goes to: the guided estimate's, or the project's only draft."""
    from app.models.estimate import Estimate
    from app.services.guided_estimating import editable_version, get_guided, version_is_editable

    guided = get_guided(organization_id, record.project_id)
    if guided is not None and guided.estimate is not None:
        version = editable_version(guided)
        if version is None:
            raise CalculatorProjectError("The project's estimate is issued or locked. Start a revision of the "
                                         "estimate first; an issued estimate is never changed.", 409)
        return version
    drafts = [e.current_version for e in Estimate.query.filter_by(organization_id=organization_id,
                                                                  project_id=record.project_id).all()
              if version_is_editable(e.current_version)]
    if len(drafts) == 1:
        return drafts[0]
    if not drafts:
        raise CalculatorProjectError("This project has no draft estimate yet. Start the project's estimate first "
                                     "(Start New Estimate), then send the result to its review.", 409)
    raise CalculatorProjectError("This project has more than one draft estimate. Open the estimate and use Add "
                                 "from calculation there.", 409)


def send_to_review(*, organization_id, record: ProjectCalculation, actor, user_id=None):
    """Put the result on the estimate review (a calculation intake). Nothing is added to the estimate here."""
    from app.models.calculation_estimate_mapping import CalculationResultIntake
    from app.services.calculation_estimate_mapping import CalculationEstimateMappingError, ingest_contract_result

    if record.organization_id != organization_id:
        raise CalculatorProjectError("Calculation not found.", 404)
    if not record.payload:
        raise CalculatorProjectError(
            "This result has no quantities for the estimate review. It stays on the project as a record.")
    version = target_version(organization_id, record)
    if record.calculation_result_intake_id:
        intake = db.session.get(CalculationResultIntake, record.calculation_result_intake_id)
        if intake is not None and intake.estimate_version_id == version.id:
            return intake  # already there: no duplicate
    existing = CalculationResultIntake.query.filter_by(organization_id=organization_id,
                                                       estimate_version_id=version.id,
                                                       result_id=record.payload["result_id"]).first()
    if existing is not None:
        intake = existing
    else:
        try:
            intake = ingest_contract_result(organization_id=organization_id, estimate_version_id=version.id,
                                            payload=record.payload, actor=actor, user_id=user_id)
        except CalculationEstimateMappingError as exc:
            raise CalculatorProjectError(str(exc)) from exc
    record.calculation_result_intake_id = intake.id
    record.estimate_version_id = version.id
    record.review_status = REVIEW_SENT
    record.sent_to_review_at = datetime.utcnow()
    record.sent_to_review_by = (actor or "")[:150]
    db.session.commit()
    return intake


# ---------------------------------------------------------------------------------------------- Option C: carry
def safe_return_path(path):
    text = (path or "").strip()
    if not text.startswith(RETURN_PREFIXES) or text.startswith("//") or "\\" in text or "://" in text:
        return "/calculators/concrete"
    return text.split("#", 1)[0][:300]


def create_carry(*, organization_id, user_id, calculator, summary, result_text, entered, payload=None,
                 form_state=None, return_path="") -> CalculatorResultCarry:
    if calculator not in CALCULATORS:
        raise CalculatorProjectError("This calculator cannot be carried to a new project.")
    summary = _clean(summary, 600)
    result_text = str(result_text or "").strip()[:20000]
    if not summary or not result_text:
        raise CalculatorProjectError("Calculate first, then create the project.")
    state = []
    for pair in (form_state or [])[:200]:
        if isinstance(pair, (list, tuple)) and len(pair) == 2:
            state.append([_clean(pair[0], 120), str(pair[1] if pair[1] is not None else "")[:500]])
    carry = CalculatorResultCarry(
        organization_id=organization_id, user_id=user_id, token=secrets.token_urlsafe(24), calculator=calculator,
        summary=summary, entered=clean_entered(entered), result_text=result_text,
        payload=_validated_payload(payload), form_state=state, return_path=safe_return_path(return_path),
        created_at=datetime.utcnow())
    db.session.add(carry)
    db.session.commit()
    return carry


def get_carry(*, organization_id, user_id, token) -> Optional[CalculatorResultCarry]:
    """The person's own unexpired carry. Another person's or another company's token finds nothing."""
    if not token:
        return None
    carry = CalculatorResultCarry.query.filter_by(token=str(token)[:64]).first()
    if carry is None or carry.organization_id != organization_id or carry.user_id != user_id:
        return None
    if carry.created_at < datetime.utcnow() - CARRY_LIFETIME:
        return None
    return carry


def attach_carry(carry: CalculatorResultCarry, project, *, user_id=None, actor_display_name="Office",
                 stage_id=None) -> ProjectCalculation:
    """The new project receives the carried result (once; a second attach returns the same record)."""
    if carry.project_calculation_id:
        record = db.session.get(ProjectCalculation, carry.project_calculation_id)
        if record is not None:
            return record
    from app.models.project_calculation import SOURCE_NEW_PROJECT

    record, _created = save_to_project(
        organization_id=carry.organization_id, project=project, calculator=carry.calculator, summary=carry.summary,
        result_text=carry.result_text, entered=carry.entered, payload=carry.payload, stage_id=stage_id,
        source=SOURCE_NEW_PROJECT, user_id=user_id, actor_display_name=actor_display_name)
    carry.project_calculation_id = record.id
    carry.consumed_at = datetime.utcnow()
    db.session.commit()
    return record


def restore_url(carry: CalculatorResultCarry) -> str:
    joiner = "&" if "?" in carry.return_path else "?"
    return f"{carry.return_path}{joiner}carry={carry.token}"


def suggested_stage_for(record: ProjectCalculation):
    """The guided stage a calculator's result usually belongs to (a pre-selection the person can change)."""
    from app.services.guided_estimating import get_guided, leaf_stages, tools_for

    guided = get_guided(record.organization_id, record.project_id)
    if guided is None:
        return None
    key = "wall_form" if record.calculator == "icf_wall" else record.calculator
    for row in leaf_stages(guided, include_na=False):
        if row.responsibility is None:
            continue
        if any(t.kind == "calculator" and t.target == key for t in tools_for(row)):
            return row
    return None


__all__ = ["CalculatorProjectError", "save_to_project", "send_to_review", "create_carry", "get_carry",
           "attach_carry", "restore_url", "stage_choices", "target_version", "safe_return_path",
           "suggested_stage_for", "stage_for_project", "clean_entered", "REVIEW_AWAITING", "REVIEW_SENT"]

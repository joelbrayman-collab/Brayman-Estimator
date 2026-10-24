"""Wizard runs: start, find, resume, save a draft, finish (Joel, 24 Oct 2026).

Every lookup is scoped: a contractor run by the signed-in person's company, a supplier run by a supplier the
signed-in person belongs to. A run stores where the person is and which records it works on, nothing more.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional

from sqlalchemy import update

from app import db
from app.models.wizard import (
    RUN_ACTIVE,
    RUN_COMPLETED,
    RUN_ENDED,
    SIDE_CONTRACTOR,
    SIDE_SUPPLIER,
    WIZARD_GUIDED_ESTIMATING,
    WIZARD_KEYS,
    WIZARD_MANAGE_PROJECT,
    WIZARD_NEW_PROJECT,
    WIZARD_SUPPLIER_PRO_DESK,
    WizardRun,
    WizardRunEvent,
)

PROJECT_WIZARDS = (WIZARD_GUIDED_ESTIMATING, WIZARD_MANAGE_PROJECT)
_REJECTED_ACTORS = {"", "system", "ai", "automatic", "calibraytai"}


class WizardError(ValueError):
    """A wizard action that cannot be done; the message is for the person."""


def _now():
    return datetime.utcnow()


def _actor(actor: str) -> str:
    name = (actor or "").strip()
    if name.lower() in _REJECTED_ACTORS:
        raise WizardError("A signed-in person must do this.")
    return name[:150]


def record(run: WizardRun, event: str, *, actor: str, step: Optional[str] = None, detail: Optional[str] = None,
           user_id=None) -> WizardRunEvent:
    row = WizardRunEvent(run_id=run.id, event=event[:40], step=(step or None) and step[:60],
                         detail=(detail or None) and str(detail)[:600], user_id=user_id,
                         actor_display_name=_actor(actor), created_at=_now())
    db.session.add(row)
    return row


# ------------------------------------------------------------------------------------------------ start
def start_contractor_run(wizard_key: str, *, organization_id: str, actor: str, user_id=None,
                         project_id: Optional[int] = None) -> WizardRun:
    """Begin a contractor wizard, or return the unfinished one it would duplicate.

    * Guided Estimating and Manage a Project: one active run per project in the company (a second Start on the
      same project resumes it).
    * Not bound to a project yet: one unfinished run per person and wizard.
    """
    name = _actor(actor)
    if wizard_key not in (WIZARD_NEW_PROJECT, WIZARD_GUIDED_ESTIMATING, WIZARD_MANAGE_PROJECT):
        raise WizardError("That guided wizard is not available here.")
    if wizard_key in PROJECT_WIZARDS and project_id:
        from app.models.project import Project

        project = Project.query.filter_by(id=project_id, organization_id=organization_id).first()
        if project is None:
            raise WizardError("Project not found.")
        existing = (WizardRun.query.filter_by(wizard_key=wizard_key, side=SIDE_CONTRACTOR,
                                              organization_id=organization_id, project_id=project.id,
                                              status=RUN_ACTIVE).order_by(WizardRun.id.asc()).first())
        if existing is not None:
            return existing
    else:
        # Not yet bound to a project (Start a New Project, or a wizard started from Home whose first step asks
        # for the project): one such unfinished run per person and wizard.
        project_id = None
        if user_id:
            existing = (WizardRun.query.filter_by(wizard_key=wizard_key, side=SIDE_CONTRACTOR,
                                                  organization_id=organization_id, user_id=user_id,
                                                  status=RUN_ACTIVE, project_id=None)
                        .order_by(WizardRun.id.asc()).first())
            if existing is not None:
                return existing
    now = _now()
    run = WizardRun(wizard_key=wizard_key, side=SIDE_CONTRACTOR, organization_id=organization_id,
                    supplier_id=None, user_id=user_id, actor_display_name=name, status=RUN_ACTIVE,
                    project_id=project_id, created_at=now, updated_at=now)
    db.session.add(run)
    db.session.flush()
    record(run, "STARTED", actor=name, user_id=user_id)
    db.session.commit()
    return run


def start_supplier_run(*, supplier_id: int, actor: str, user_id=None, share_id: Optional[int] = None,
                       quote_id: Optional[int] = None) -> WizardRun:
    """Begin the Supplier Pro Desk wizard; one active run per request or quotation (a second Start resumes)."""
    name = _actor(actor)
    if share_id and quote_id:
        raise WizardError("Choose either the contractor request or the quotation.")
    query = WizardRun.query.filter_by(wizard_key=WIZARD_SUPPLIER_PRO_DESK, side=SIDE_SUPPLIER,
                                      supplier_id=supplier_id, status=RUN_ACTIVE)
    if share_id:
        existing = query.filter_by(supplier_share_id=share_id).order_by(WizardRun.id.asc()).first()
    elif quote_id:
        existing = query.filter_by(supplier_quote_id=quote_id).order_by(WizardRun.id.asc()).first()
    else:
        existing = (query.filter_by(user_id=user_id, supplier_share_id=None, supplier_quote_id=None)
                    .order_by(WizardRun.id.asc()).first()) if user_id else None
    if existing is not None:
        return existing
    now = _now()
    run = WizardRun(wizard_key=WIZARD_SUPPLIER_PRO_DESK, side=SIDE_SUPPLIER, organization_id=None,
                    supplier_id=supplier_id, user_id=user_id, actor_display_name=name, status=RUN_ACTIVE,
                    supplier_share_id=share_id, supplier_quote_id=quote_id, created_at=now, updated_at=now)
    db.session.add(run)
    db.session.flush()
    record(run, "STARTED", actor=name, user_id=user_id)
    db.session.commit()
    return run


# ------------------------------------------------------------------------------------------------ find
def contractor_run(organization_id: str, run_id: int) -> WizardRun:
    run = WizardRun.query.filter_by(id=run_id, side=SIDE_CONTRACTOR, organization_id=organization_id).first()
    if run is None:
        raise WizardError("Not found.")
    return run


def supplier_run(supplier_id: int, run_id: int) -> WizardRun:
    run = WizardRun.query.filter_by(id=run_id, side=SIDE_SUPPLIER, supplier_id=supplier_id).first()
    if run is None:
        raise WizardError("Not found.")
    return run


def active_contractor_runs(organization_id: str, *, wizard_key: Optional[str] = None,
                           project_id: Optional[int] = None) -> List[WizardRun]:
    query = WizardRun.query.filter_by(side=SIDE_CONTRACTOR, organization_id=organization_id, status=RUN_ACTIVE)
    if wizard_key:
        query = query.filter_by(wizard_key=wizard_key)
    if project_id:
        query = query.filter_by(project_id=project_id)
    return query.order_by(WizardRun.updated_at.desc(), WizardRun.id.desc()).all()


def active_supplier_runs(supplier_id: int) -> List[WizardRun]:
    return (WizardRun.query.filter_by(side=SIDE_SUPPLIER, supplier_id=supplier_id, status=RUN_ACTIVE)
            .order_by(WizardRun.updated_at.desc(), WizardRun.id.desc()).all())


def history(run: WizardRun, limit: int = 30) -> List[WizardRunEvent]:
    return (WizardRunEvent.query.filter_by(run_id=run.id).order_by(WizardRunEvent.id.desc()).limit(limit).all())


def has_event(run: WizardRun, event: str, step: Optional[str] = None) -> Optional[WizardRunEvent]:
    query = WizardRunEvent.query.filter_by(run_id=run.id, event=event)
    if step:
        query = query.filter_by(step=step)
    return query.order_by(WizardRunEvent.id.desc()).first()


# ------------------------------------------------------------------------------------------------ progress
def _require_active(run: WizardRun):
    if run.status != RUN_ACTIVE:
        raise WizardError("This guided wizard is finished. Start it again to go through it once more; the records "
                          "it worked on are kept.")


def set_step(run: WizardRun, step: str, *, actor: str, user_id=None, event: Optional[str] = None,
             detail: Optional[str] = None) -> None:
    """Remember where the person is (Resume). ``event`` adds a history row (Save, Save & Exit)."""
    if run.status != RUN_ACTIVE:
        return
    run.current_step = step[:60]
    run.updated_at = _now()
    if event:
        record(run, event, actor=actor, step=step, detail=detail, user_id=user_id)
    db.session.commit()


def save_draft(run: WizardRun, values: Dict[str, str], *, allowed: Iterable[str], step: str, actor: str,
               user_id=None, event: Optional[str] = None) -> Dict[str, str]:
    """Keep answers typed before their record exists (only the fields the step allows; text only)."""
    _require_active(run)
    if run.project_id:
        raise WizardError("The project is already created. Change it on the project's own pages.")
    allowed = set(allowed)
    draft = dict((run.draft_json or {}).get("fields") or {})
    for key, value in values.items():
        if key in allowed:
            draft[key] = " ".join(str(value or "").split())[:500] if key != "description" else str(value or "")[:2000]
    run.draft_json = {"fields": draft}
    run.current_step = step[:60]
    run.updated_at = _now()
    if event:
        record(run, event, actor=actor, step=step, user_id=user_id)
    db.session.commit()
    return draft


def draft_fields(run: WizardRun) -> Dict[str, str]:
    return dict((run.draft_json or {}).get("fields") or {})


def claim_project(run_id: int, organization_id: str, project_id: int) -> bool:
    """Point a Start a New Project run at the project it just created, exactly once.

    A conditional update in the project's own transaction: if the run already has a project (a second press of
    Create, or the form sent twice), nothing is claimed and the caller rolls the new project back.
    """
    result = db.session.execute(
        update(WizardRun)
        .where(WizardRun.id == run_id, WizardRun.organization_id == organization_id,
               WizardRun.side == SIDE_CONTRACTOR, WizardRun.wizard_key == WIZARD_NEW_PROJECT,
               WizardRun.status == RUN_ACTIVE, WizardRun.project_id.is_(None))
        .values(project_id=project_id, updated_at=_now())
        .execution_options(synchronize_session=False))
    return result.rowcount == 1


def attach(run: WizardRun, *, actor: str, user_id=None, share_id: Optional[int] = None,
           quote_id: Optional[int] = None, project_id: Optional[int] = None) -> None:
    """Point a run at the record it works on (once chosen it stays; start another run for another record)."""
    _require_active(run)
    if share_id:
        if run.supplier_share_id or run.supplier_quote_id:
            raise WizardError("This wizard already works on a request or quotation.")
        other = WizardRun.query.filter_by(wizard_key=run.wizard_key, side=run.side, supplier_id=run.supplier_id,
                                          supplier_share_id=share_id, status=RUN_ACTIVE).first()
        if other is not None and other.id != run.id:
            raise WizardError("Another guided wizard is already open on that request. Resume it instead.")
        run.supplier_share_id = share_id
        record(run, "ATTACHED", actor=actor, detail=f"Contractor request {share_id}", user_id=user_id)
    elif quote_id:
        if run.supplier_share_id or run.supplier_quote_id:
            raise WizardError("This wizard already works on a request or quotation.")
        other = WizardRun.query.filter_by(wizard_key=run.wizard_key, side=run.side, supplier_id=run.supplier_id,
                                          supplier_quote_id=quote_id, status=RUN_ACTIVE).first()
        if other is not None and other.id != run.id:
            raise WizardError("Another guided wizard is already open on that quotation. Resume it instead.")
        run.supplier_quote_id = quote_id
        record(run, "ATTACHED", actor=actor, detail=f"Quotation {quote_id}", user_id=user_id)
    elif project_id:
        if run.project_id:
            raise WizardError("This wizard already works on a project.")
        run.project_id = project_id
        record(run, "ATTACHED", actor=actor, detail=f"Project {project_id}", user_id=user_id)
    run.updated_at = _now()
    db.session.commit()


def confirm(run: WizardRun, step: str, *, actor: str, detail: str, user_id=None) -> WizardRunEvent:
    """A person's confirmation made in the wizard (e.g. 'I reviewed the drawings; no measurement is reliable')."""
    _require_active(run)
    text = " ".join((detail or "").split())
    if not text:
        raise WizardError("Say what you confirmed.")
    row = record(run, "CONFIRMED", actor=actor, step=step, detail=text, user_id=user_id)
    run.updated_at = _now()
    db.session.commit()
    return row


def finish(run: WizardRun, *, actor: str, user_id=None) -> None:
    _require_active(run)
    run.status = RUN_COMPLETED
    run.completed_at = _now()
    run.updated_at = run.completed_at
    record(run, "COMPLETED", actor=actor, step=run.current_step, user_id=user_id)
    db.session.commit()


def end(run: WizardRun, *, actor: str, reason: str = "", user_id=None) -> None:
    """Stop using the wizard for this activity. The records it pointed at are untouched."""
    _require_active(run)
    run.status = RUN_ENDED
    run.completed_at = _now()
    run.updated_at = run.completed_at
    record(run, "ENDED", actor=actor, step=run.current_step, detail=reason or None, user_id=user_id)
    db.session.commit()


__all__ = [n for n in dir() if not n.startswith("_")]
_ = (WIZARD_KEYS, RUN_ENDED, SIDE_SUPPLIER)

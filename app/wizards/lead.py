"""The Project Lead in the wizards (Joel, 24 Oct 2026, decision 1).

Start a New Project (step "Project Lead and first dates") and Manage a Project (step "Employees, crews and
subcontractors") show the project's Project Lead and set it with a small form that calls the existing service
(app/services/project_lead.py). The Project Lead is a name on the project only: it grants no permission and is
kept apart from scheduled-work assignments and appointment assignees.
"""

from __future__ import annotations

from flask import url_for

from app.wizards.framework import DONE, TODO, Item


def lead_item(ctx) -> Item:
    from app.services.project_lead import lead_name

    assigned = bool(ctx.project is not None and ctx.project.project_lead_user_id)
    return Item("Project Lead", DONE if assigned else TODO, lead_name(ctx.project),
                url_for("projects.edit_project_lead", id=ctx.project.id) if ctx.project is not None else "")


def lead_form_ctx(ctx) -> dict:
    from app.services.project_lead import lead_choices

    return {"people": lead_choices(ctx.organization_id),
            "current": ctx.project.project_lead_user_id if ctx.project is not None else None}


def save_lead(ctx, form, *, step: str) -> str:
    from app.services.project_lead import ProjectLeadError, lead_name, set_project_lead
    from app.wizards.service import WizardError, record

    if ctx.project is None:
        raise WizardError("Create the project first.")
    try:
        changed = set_project_lead(organization_id=ctx.organization_id, project_id=ctx.project.id,
                                   user_id=form.get("project_lead_user_id"), commit=False)
    except ProjectLeadError as exc:
        raise WizardError(str(exc)) from exc
    name = lead_name(ctx.project)
    if not changed:
        return f"The Project Lead is unchanged ({name})."
    from app import db

    record(ctx.run, "PROJECT_LEAD_SET", actor=ctx.actor, step=step, detail=f"Project Lead: {name}",
           user_id=ctx.user_id)
    db.session.commit()
    return f"Project Lead: {name}."

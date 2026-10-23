""""View project plan" (23 Oct 2026): one button, on every project screen, that opens the job's plan.

Office: the newest plan or drawing on the project (or the plans page when there are several or none).
Field: the job's Drawings and plans page (crew see only jobs they may see; no costs).
"""

from flask import url_for


def office_plan_link(project):
    """{url, label, count} for the header button, or None when there is no project."""
    if project is None or getattr(project, "id", None) is None or not hasattr(project, "organization_id"):
        return None
    try:
        from app.services.organizations import get_current_organization_id

        if project.organization_id != get_current_organization_id():
            return None  # e.g. a supplier looking at a contractor's job: not their plans
    except Exception:
        return None
    from app.plan_intelligence.models import PlanDocument

    documents = (PlanDocument.query.filter_by(project_id=project.id, archived_at=None)
                 .order_by(PlanDocument.id.desc()).all())
    if len(documents) == 1:
        url = url_for("plan_intelligence.view_plan", project_id=project.id, document_id=documents[0].id)
    else:
        url = url_for("plan_intelligence.list_plans", project_id=project.id)
    return {
        "url": url,
        "label": "View project plan" if documents else "Add project plan",
        "count": len(documents),
        "project_name": project.name,
    }


def field_plan_link(project_id):
    if not project_id:
        return None
    return url_for("field.drawings", project_id=project_id)

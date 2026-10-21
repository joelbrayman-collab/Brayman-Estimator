"""Who is looking at a Workflow Map: one function per place the map is shown (Joel, 21 Oct 2026).

Each reads only what the signed-in person may already see: their company's own projects (to choose one),
their own access, their own training record.
"""

from __future__ import annotations

from typing import Optional, Tuple

from flask_login import current_user

from app.models.training import ROLE_FIELD, ROLE_OFFICE, ROLE_OWNER
from app.workflow_map import definition as D
from app.workflow_map.build import KIND_FIELD, KIND_OFFICE, KIND_SUPPLIER, Viewer

MAX_PROJECT_CHOICES = 300


def _training():
    from app.training import service as svc

    if not svc.enabled():
        return False, None
    try:
        return True, svc.trainee_for(current_user)
    except Exception:
        return True, None


def _office_access(org_id: str) -> Tuple[bool, bool]:
    from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT, membership_has_access_domain
    from app.services.instance_authority import is_instance_owner, is_system_administrator

    people_admin = bool(is_instance_owner(current_user, org_id) or is_system_administrator(current_user, org_id))
    return people_admin, bool(membership_has_access_domain(current_user, org_id, ACCESS_DOMAIN_COMPANY_MANAGEMENT))


def office_viewer(project_id: Optional[int]) -> Viewer:
    """An office member of the contractor company. The project is used only if it is this company's."""
    from app.models import Project
    from app.services.organizations import get_current_organization_id

    org_id = get_current_organization_id()
    people_admin, company_management = _office_access(org_id)
    training, trainee = _training()
    project = None
    if project_id:
        project = Project.query.filter_by(id=project_id, organization_id=org_id).first()
    choices = [{"id": p.id, "name": p.name} for p in
               Project.query.filter_by(organization_id=org_id).order_by(Project.name.asc()).limit(MAX_PROJECT_CHOICES)]
    role = trainee.role if trainee is not None else (ROLE_OWNER if people_admin else ROLE_OFFICE)
    return Viewer(kind=KIND_OFFICE, people_admin=people_admin, company_management=company_management,
                  project_id=project.id if project else None, project_name=project.name if project else "",
                  training=training, trainee=trainee, role=role if training else None, projects=choices,
                  default_stage=D.stage_for_project_status(project.status) if project else None)


def field_viewer(project) -> Viewer:
    """Field: anyone in the contractor company on the phone. ``project`` is the job confirmed on Field (already
    limited to the jobs a field-only person is assigned to)."""
    training, trainee = _training()
    return Viewer(kind=KIND_FIELD, project_id=project.id if project else None,
                  project_name=project.name if project else "", training=training, trainee=trainee,
                  role=(trainee.role if trainee is not None else ROLE_FIELD) if training else None, projects=None)


def supplier_viewer(supplier) -> Viewer:
    training, trainee = _training()
    return Viewer(kind=KIND_SUPPLIER, supplier_id=supplier.id, training=training, trainee=trainee,
                  role=trainee.role if (training and trainee is not None) else None, projects=None)


def training_viewer(trainee) -> Tuple[str, Viewer]:
    """The Training Centre's map: the trainee's own side, with their lessons and results."""
    from app.models.training import PATHWAY_SUPPLIER
    from app.training import service as svc

    pathway, org_id, supplier_id, field_only = svc.principal(current_user)
    if trainee.pathway == PATHWAY_SUPPLIER:
        if pathway != PATHWAY_SUPPLIER or not supplier_id:
            return D.MAP_SUPPLIER, Viewer(kind=KIND_SUPPLIER, training=True, trainee=trainee, role=trainee.role,
                                          projects=None)
        return D.MAP_SUPPLIER, Viewer(kind=KIND_SUPPLIER, supplier_id=supplier_id,
                                      training=True, trainee=trainee, role=trainee.role, projects=None)
    people_admin = company_management = False
    if org_id and not field_only:
        people_admin, company_management = _office_access(org_id)
    kind = KIND_FIELD if field_only else KIND_OFFICE
    map_key = D.MAP_FIELD if (field_only or trainee.role == ROLE_FIELD) else D.MAP_CONTRACTOR
    return map_key, Viewer(kind=kind, people_admin=people_admin, company_management=company_management,
                           training=True, trainee=trainee, role=trainee.role, projects=None)

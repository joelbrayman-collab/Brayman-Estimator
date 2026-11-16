"""Template context helpers for the application shell (UI only)."""

from flask import request
from flask_login import current_user
from sqlalchemy import or_

from app.navigation import ADMIN_SECTIONS, MORE_SECTIONS, NAV_SECTIONS, is_nav_item_active
from app.presentation import cal_copy, contractor_copy, help_content


def register_shell_context(app):
    @app.context_processor
    def inject_shell_context():
        endpoint = request.endpoint
        authenticated = getattr(current_user, "is_authenticated", False)
        nav_sections = []
        for section in NAV_SECTIONS:
            links = []
            for item in section["links"]:
                if not _nav_item_visible(item, authenticated):
                    continue
                links.append(
                    {
                        **item,
                        "active": is_nav_item_active(item, endpoint),
                    }
                )
            if links:
                nav_sections.append(
                    {
                        "title": section["title"],
                        "links": links,
                        "collapsible": bool(section.get("collapsible")),
                        "has_active": any(link["active"] for link in links),
                        "class": section.get("class", ""),
                    }
                )

        recent_estimates = []
        recent_proposals = []
        if authenticated and endpoint not in ("auth.login", "auth.logout"):
            try:
                from app.models import Estimate, Project, Proposal, ProposalTemplate
                from app.services.organizations import get_current_organization_id

                org_id = get_current_organization_id()
                recent_estimates = (
                    Estimate.query.join(Project)
                    .filter(Project.organization_id == org_id)
                    .order_by(Estimate.updated_at.desc())
                    .limit(5)
                    .all()
                )
                recent_proposals = (
                    Proposal.query.outerjoin(Estimate, Proposal.estimate_id == Estimate.id)
                    .outerjoin(Project, Estimate.project_id == Project.id)
                    .outerjoin(
                        ProposalTemplate,
                        Proposal.proposal_template_id == ProposalTemplate.id,
                    )
                    .filter(
                        or_(
                            Project.organization_id == org_id,
                            ProposalTemplate.organization_id == org_id,
                        )
                    )
                    .order_by(Proposal.updated_at.desc())
                    .limit(5)
                    .all()
                )
            except Exception:
                # Tables may not exist yet, or membership cannot resolve.
                pass

        company_name = ""
        if authenticated:
            try:
                from app.services.brand_profile import office_company_name
                from app.services.organizations import get_current_organization_id

                company_name = office_company_name(get_current_organization_id())
            except Exception:
                company_name = ""

        return {
            "nav_sections": nav_sections,
            "admin_active": endpoint is not None and is_nav_item_active({"endpoint": "main.admin"}, endpoint),
            "shell_recent_estimates": recent_estimates,
            "shell_recent_proposals": recent_proposals,
            "company_name": company_name,
            "product_name": "Brayman Construction Platform",
            "contractor_copy": contractor_copy,
            "help_content": help_content,
            "cal_copy": cal_copy,
            "step_bar": _step_bar(endpoint, authenticated),
        }


def _nav_item_visible(item, authenticated) -> bool:
    if item.get("requires_people_admin"):
        if not authenticated:
            return False
        try:
            from app.services.instance_authority import is_instance_owner, is_system_administrator
            from app.services.organizations import get_current_organization_id

            org_id = get_current_organization_id()
            return is_instance_owner(current_user, org_id) or is_system_administrator(current_user, org_id)
        except Exception:
            return False
    domain = item.get("requires_access_domain")
    if not domain:
        return True
    if not authenticated:
        return False
    try:
        from app.services.access_domains import membership_has_access_domain
        from app.services.organizations import get_current_organization_id

        org_id = get_current_organization_id()
        return membership_has_access_domain(current_user, org_id, domain)
    except Exception:
        return False


def visible_sections(sections, authenticated=True, endpoint=None):
    """MORE_SECTIONS or ADMIN_SECTIONS for the current person: the same visibility rules as the sidebar."""
    out = []
    for section in sections:
        links = [{**item, "active": bool(endpoint) and item["endpoint"] == endpoint}
                 for item in section["links"] if _nav_item_visible(item, authenticated)]
        if links:
            out.append({**section, "links": links})
    return out


def more_sections(endpoint=None):
    return visible_sections(MORE_SECTIONS, getattr(current_user, "is_authenticated", False), endpoint)


def admin_sections(endpoint=None):
    return visible_sections(ADMIN_SECTIONS, getattr(current_user, "is_authenticated", False), endpoint)


_STEP_BAR_PREFIXES = ("projects.", "guided.", "guided_tasks.", "plan_intelligence.")


def _step_bar(endpoint, authenticated):
    """The Set up / Plan / Price / Review / Quote bar for an office project page (Joel, 16 Nov 2026), or None."""
    if not authenticated or not endpoint or request.method != "GET" or not endpoint.startswith(_STEP_BAR_PREFIXES):
        return None
    args = request.view_args or {}
    project_id = args.get("project_id") if "project_id" in args else args.get("id") if endpoint.startswith("projects.") else None
    if not isinstance(project_id, int):
        return None
    try:
        from app.models import Project
        from app.services import project_steps
        from app.services.organizations import get_current_organization_id

        project = Project.query.filter_by(id=project_id, organization_id=get_current_organization_id()).first()
        return project_steps.build(project, endpoint) if project is not None else None
    except Exception:  # noqa: BLE001 - the bar never breaks a page
        from flask import current_app

        if current_app.testing:
            raise
        return None

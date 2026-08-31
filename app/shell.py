"""Template context helpers for the application shell (UI only)."""

from flask import request
from flask_login import current_user
from sqlalchemy import or_

from app.navigation import NAV_SECTIONS, is_nav_item_active


def register_shell_context(app):
    @app.context_processor
    def inject_shell_context():
        endpoint = request.endpoint
        nav_sections = []
        for section in NAV_SECTIONS:
            links = []
            for item in section["links"]:
                links.append(
                    {
                        **item,
                        "active": is_nav_item_active(item, endpoint),
                    }
                )
            nav_sections.append(
                {
                    "title": section["title"],
                    "links": links,
                }
            )

        recent_estimates = []
        recent_proposals = []
        authenticated = getattr(current_user, "is_authenticated", False)
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

        return {
            "nav_sections": nav_sections,
            "shell_recent_estimates": recent_estimates,
            "shell_recent_proposals": recent_proposals,
            "product_name": "Brayman Construction Platform",
        }

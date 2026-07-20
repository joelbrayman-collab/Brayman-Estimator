"""Template context helpers for the application shell (UI only)."""

from flask import request

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
        try:
            from app.models import Estimate, Proposal

            recent_estimates = (
                Estimate.query.order_by(Estimate.updated_at.desc()).limit(5).all()
            )
            recent_proposals = (
                Proposal.query.order_by(Proposal.updated_at.desc()).limit(5).all()
            )
        except Exception:
            # Tables may not exist yet during early migrate/create_all edge cases.
            pass

        return {
            "nav_sections": nav_sections,
            "shell_recent_estimates": recent_estimates,
            "shell_recent_proposals": recent_proposals,
            "product_name": "Brayman Construction Platform",
        }

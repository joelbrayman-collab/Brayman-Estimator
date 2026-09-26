"""Single source of truth for application shell navigation."""

from app.presentation.contractor_copy import (
    ATTENTION_NAV_TITLE,
    COMPANY_CALENDAR_HEADING,
    COMPANY_LIBRARY_NAV_TITLE,
    COSTS_AND_PRICING_NAV_TITLE,
    HOW_WE_PRICE_NAV_TITLE,
    PAST_JOBS_NAV_TITLE,
    PROPOSALS_NAV_TITLE,
    REUSABLE_WORK_NAV_TITLE,
    TEMPLATES_NAV_TITLE,
    WHAT_WE_PAY_NAV_TITLE,
    WORK_CATALOG_NAV_TITLE,
)
from app.services.access_domains import ACCESS_DOMAIN_COMPANY_MANAGEMENT

# Daily work is the first group. Estimating inputs and company setup stay
# underneath it. Unfinished routes stay in the application; they are not peers here.
NAV_SECTIONS = (
    {
        "title": None,
        "links": (
            {
                "title": "Home",
                "endpoint": "main.dashboard",
                "icon": "bi-speedometer2",
                "enabled": True,
            },
            {
                "title": COMPANY_CALENDAR_HEADING,
                "endpoint": "schedule.company",
                "icon": "bi-calendar3",
                "enabled": True,
            },
            {
                "title": "Projects",
                "endpoint": "projects.list_projects",
                "icon": "bi-building",
                "enabled": True,
            },
            {
                "title": "Clients",
                "endpoint": "clients.list_clients",
                "icon": "bi-people",
                "enabled": True,
            },
        ),
    },
    {
        "title": COSTS_AND_PRICING_NAV_TITLE,
        "links": (
            {
                "title": WHAT_WE_PAY_NAV_TITLE,
                "endpoint": "cost_library.list_cost_items",
                "icon": "bi-box-seam",
                "enabled": True,
            },
            {
                "title": REUSABLE_WORK_NAV_TITLE,
                "endpoint": "assemblies.list_assemblies",
                "icon": "bi-layers",
                "enabled": True,
            },
            {
                "title": HOW_WE_PRICE_NAV_TITLE,
                "endpoint": "pricing_engine.index",
                "icon": "bi-percent",
                "enabled": True,
            },
        ),
    },
    {
        "title": PROPOSALS_NAV_TITLE,
        "links": (
            {
                "title": TEMPLATES_NAV_TITLE,
                "endpoint": "proposal_templates.list_templates",
                "icon": "bi-file-earmark-richtext",
                "enabled": True,
            },
        ),
    },
    {
        "title": COMPANY_LIBRARY_NAV_TITLE,
        "links": (
            {
                "title": PAST_JOBS_NAV_TITLE,
                "endpoint": "historical_estimates.index",
                "icon": "bi-archive",
                "enabled": True,
            },
        ),
    },
    {
        "title": "Company",
        "links": (
            {
                "title": ATTENTION_NAV_TITLE,
                "endpoint": "company_attention.index",
                "icon": "bi-exclamation-circle",
                "enabled": True,
                "requires_access_domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT,
            },
            {
                "title": "Crews",
                "endpoint": "organization_crew.index",
                "icon": "bi-people-fill",
                "enabled": True,
            },
            {
                "title": WORK_CATALOG_NAV_TITLE,
                "endpoint": "work_structure.catalog_index",
                "icon": "bi-diagram-3",
                "enabled": True,
            },
        ),
    },
)

# Flat list retained for callers that only need items.
NAV_ITEMS = tuple(item for section in NAV_SECTIONS for item in section["links"])


def is_nav_item_active(item, endpoint):
    if not endpoint or not item.get("endpoint"):
        return False
    target = item["endpoint"]
    if endpoint == target:
        return True
    # Highlight parent module for nested routes (e.g. estimates.view_version)
    prefix = target.rsplit(".", 1)[0]
    return endpoint.startswith(f"{prefix}.")

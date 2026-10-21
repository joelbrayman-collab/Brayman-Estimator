"""Single source of truth for application shell navigation."""

from app.presentation.contractor_copy import (
    ATTENTION_NAV_TITLE,
    CALENDAR_NAV_TITLE,
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
                "title": CALENDAR_NAV_TITLE,
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
        "title": "Calculators",
        # Joel, 15 Oct 2026: collapsible, closed unless a calculator is open; remembered.
        "collapsible": True,
        "links": (
            {
                "title": "Concrete calculator",
                "endpoint": "calculators.concrete",
                "icon": "bi-calculator",
                "enabled": True,
            },
            {
                "title": "Stair calculator",
                "endpoint": "calculators.stairs",
                "icon": "bi-bar-chart-steps",
                "enabled": True,
            },
            {
                "title": "ICF wall calculator",
                "endpoint": "calculators.wall_form",
                "icon": "bi-bricks",
                "enabled": True,
            },
            {
                "title": "Employment vs Entrepreneurship",
                "endpoint": "calculators.employment_vs_entrepreneurship",
                "icon": "bi-briefcase",
                "enabled": True,
            },
            {
                "title": "Wall framing calculator",
                "endpoint": "calculators.wall_framing",
                "icon": "bi-columns",
                "enabled": True,
            },
            {
                "title": "Footing calculator",
                "endpoint": "calculators.footing",
                "icon": "bi-bounding-box",
                "enabled": True,
            },
            {
                "title": "Roofing calculator",
                "endpoint": "calculators.roofing",
                "icon": "bi-house",
                "enabled": True,
            },
            {
                "title": "Siding calculator",
                "endpoint": "calculators.siding",
                "icon": "bi-grid-3x3",
                "enabled": True,
            },
            {
                "title": "Drywall calculator",
                "endpoint": "calculators.drywall",
                "icon": "bi-square",
                "enabled": True,
            },
            {
                "title": "Flooring calculator",
                "endpoint": "calculators.flooring",
                "icon": "bi-grid",
                "enabled": True,
            },
        ),
    },
    {
        "title": COSTS_AND_PRICING_NAV_TITLE,
        "endpoint": "costs_and_pricing.index",
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
                "title": "Getting started",
                "endpoint": "getting_started.index",
                "icon": "bi-list-check",
                "enabled": True,
            },
            {
                # Joel, 21 Oct 2026: the Contractor Workflow Map (app/workflow_map).
                "title": "Workflow Guide",
                "endpoint": "workflow_map.contractor",
                "icon": "bi-signpost-split",
                "enabled": True,
            },
            {
                "title": ATTENTION_NAV_TITLE,
                "endpoint": "company_attention.index",
                "icon": "bi-exclamation-circle",
                "enabled": True,
                "requires_access_domain": ACCESS_DOMAIN_COMPANY_MANAGEMENT,
            },
            {
                "title": "People & Access",
                "endpoint": "people_access.index",
                "icon": "bi-person-badge",
                "enabled": True,
                # Shown only to the owner or a System Administrator (app/shell.py).
                "requires_people_admin": True,
            },
            {
                "title": "Crews",
                "endpoint": "organization_crew.index",
                "icon": "bi-people-fill",
                "enabled": True,
            },
            {
                "title": "Suppliers",
                "endpoint": "supplier_office.suppliers",
                "icon": "bi-shop",
                "enabled": True,
            },
            {
                "title": "Accounting",
                "endpoint": "accounting.index",
                "icon": "bi-journal-text",
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


_NAV_ENDPOINTS = frozenset(item["endpoint"] for item in NAV_ITEMS if item.get("endpoint"))


def is_nav_item_active(item, endpoint):
    if not endpoint or not item.get("endpoint"):
        return False
    target = item["endpoint"]
    if endpoint == target:
        return True
    # A page that has its own menu entry highlights only that entry (one calculator,
    # not every calculator in the same blueprint).
    if endpoint in _NAV_ENDPOINTS:
        return False
    # Highlight parent module for nested routes (e.g. estimates.view_version)
    prefix = target.rsplit(".", 1)[0]
    return endpoint.startswith(f"{prefix}.")

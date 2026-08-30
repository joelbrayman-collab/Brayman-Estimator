"""Single source of truth for application shell navigation."""

# Navigation is grouped into platform modules.
# Each item: title, endpoint (or None), icon (Bootstrap Icons class), enabled
NAV_SECTIONS = (
    {
        "title": None,
        "links": (
            {
                "title": "Dashboard",
                "endpoint": "main.dashboard",
                "icon": "bi-speedometer2",
                "enabled": True,
            },
            {
                "title": "Clients",
                "endpoint": "clients.list_clients",
                "icon": "bi-people",
                "enabled": True,
            },
            {
                "title": "Projects",
                "endpoint": "projects.list_projects",
                "icon": "bi-building",
                "enabled": True,
            },
        ),
    },
    {
        "title": "Estimating",
        "links": (
            {
                "title": "Assemblies",
                "endpoint": "assemblies.list_assemblies",
                "icon": "bi-layers",
                "enabled": True,
            },
            {
                "title": "Cost Items",
                "endpoint": "cost_library.list_cost_items",
                "icon": "bi-box-seam",
                "enabled": True,
            },
            {
                "title": "Material Catalogue",
                "endpoint": "material_catalogue.list_materials",
                "icon": "bi-grid-3x3-gap",
                "enabled": True,
            },
            {
                "title": "Estimates",
                "endpoint": "estimates.list_estimates",
                "icon": "bi-calculator",
                "enabled": True,
            },
            {
                "title": "Historical Evidence",
                "endpoint": "historical_estimates.index",
                "icon": "bi-archive",
                "enabled": True,
            },
            {
                "title": "Labour Engine",
                "endpoint": "labour_engine.index",
                "icon": "bi-stopwatch",
                "enabled": True,
            },
            {
                "title": "Pricing Engine",
                "endpoint": "pricing_engine.index",
                "icon": "bi-percent",
                "enabled": True,
            },
            {
                "title": "Proposals",
                "endpoint": "proposals.list_proposals",
                "icon": "bi-file-earmark-text",
                "enabled": True,
            },
            {
                "title": "Proposal Templates",
                "endpoint": "proposal_templates.list_templates",
                "icon": "bi-file-earmark-richtext",
                "enabled": True,
            },
        ),
    },
    {
        "title": "Project Controls",
        "links": (
            {
                "title": "Change Orders",
                "endpoint": "project_controls.list_change_orders",
                "icon": "bi-arrow-left-right",
                "enabled": True,
            },
            {
                "title": "Purchase Orders",
                "endpoint": None,
                "icon": "bi-cart3",
                "enabled": False,
            },
            {
                "title": "Job Costing",
                "endpoint": None,
                "icon": "bi-cash-stack",
                "enabled": False,
            },
        ),
    },
    {
        "title": None,
        "links": (
            {
                "title": "Reports",
                "endpoint": None,
                "icon": "bi-bar-chart-line",
                "enabled": False,
            },
            {
                "title": "AI Assistant",
                "endpoint": None,
                "icon": "bi-stars",
                "enabled": False,
            },
            {
                "title": "Settings",
                "endpoint": None,
                "icon": "bi-gear",
                "enabled": False,
            },
        ),
    },
)

# Flat list retained for callers that only need items.
NAV_ITEMS = tuple(
    item for section in NAV_SECTIONS for item in section["links"]
)


def is_nav_item_active(item, endpoint):
    if not endpoint or not item.get("endpoint"):
        return False
    target = item["endpoint"]
    if endpoint == target:
        return True
    # Highlight parent module for nested routes (e.g. estimates.view_version)
    prefix = target.rsplit(".", 1)[0]
    return endpoint.startswith(f"{prefix}.")

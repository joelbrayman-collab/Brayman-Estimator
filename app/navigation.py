"""Single source of truth for application shell navigation.

Task-First UX (Joel's mandate, 31 Oct 2026; docs/ux/task-first-ux-audit-2026-10-31.md sections 2 and 6):
SIMPLE ON THE SURFACE, POWERFUL UNDERNEATH. The office sidebar keeps six primary destinations (what a contractor
does every day). Everything else is still one click away and nothing was removed:

    NAV_SECTIONS    the sidebar: Attention · Projects · Calendar · Customers · Purchasing · Time & Money, then More
    MORE_SECTIONS   the More page (main.more): calculators, prices & costs, lists, past jobs, business tools, help
    ADMIN_SECTIONS  the Admin page behind the header gear (main.admin): company settings, people, pricing policy,
                    document templates, work catalog, labour rates

Every endpoint that was in the sidebar on 30 Oct 2026 is in one of the three (tests/test_task_first_navigation.py).
Visibility uses the existing permission model only (requires_people_admin, requires_access_domain); the pages keep
their own checks. Field-only crew and Supplier Hub users have their own shells and are unchanged.
"""

from app.presentation.contractor_copy import (
    CALENDAR_NAV_TITLE,
    COMPANY_LIBRARY_NAV_TITLE,
    COSTS_AND_PRICING_NAV_TITLE,
    HOW_WE_PRICE_NAV_TITLE,
    PAST_JOBS_NAV_TITLE,
    REUSABLE_WORK_NAV_TITLE,
    WHAT_WE_PAY_NAV_TITLE,
    WORK_CATALOG_NAV_TITLE,
)

ATTENTION_PRIMARY_TITLE = "Attention"
CUSTOMERS_NAV_TITLE = "Customers"
PURCHASING_NAV_TITLE = "Purchasing"
TIME_AND_MONEY_NAV_TITLE = "Time & Money"
MORE_NAV_TITLE = "More"
ADMIN_NAV_TITLE = "Admin"
CALCULATORS_SECTION_TITLE = "Calculators"
DOCUMENT_TEMPLATES_NAV_TITLE = "Document templates"

# ---------------------------------------------------------------------------------------------- the sidebar
# "areas" are the endpoint prefixes that belong to a primary destination, so the page you are on highlights the
# destination it lives under (an estimate highlights Projects, an invoice Time & Money).
PRIMARY_NAV = (
    {
        "title": ATTENTION_PRIMARY_TITLE,
        "endpoint": "main.dashboard",
        "icon": "bi-exclamation-circle",
        "enabled": True,
        "areas": ("operations.attention", "company_attention."),
    },
    {
        "title": "Projects",
        "endpoint": "projects.list_projects",
        "icon": "bi-building",
        "enabled": True,
        "areas": ("projects.", "estimates.", "estimate_labour.", "estimate_quickbooks.", "approved_costs.", "guided.",
                  "proposals.", "project_controls.", "plan_intelligence.", "construction_drawings.",
                  "deck_takeoff.", "scope_delivery.", "supplier_package.", "work_structure.project",
                  "calculation_mapping.", "build.", "final_walkthrough.", "signing_office."),
    },
    {
        "title": CALENDAR_NAV_TITLE,
        "endpoint": "schedule.company",
        "icon": "bi-calendar3",
        "enabled": True,
        "areas": ("schedule.", "appointments."),
    },
    {
        "title": CUSTOMERS_NAV_TITLE,
        "endpoint": "clients.list_clients",
        "icon": "bi-people",
        "enabled": True,
        "areas": ("clients.",),
    },
    {
        "title": PURCHASING_NAV_TITLE,
        "endpoint": "main.purchasing",
        "icon": "bi-cart3",
        "enabled": True,
        "areas": ("supplier_office.", "operations.material_request", "operations.deliver"),
    },
    {
        "title": TIME_AND_MONEY_NAV_TITLE,
        "endpoint": "main.time_and_money",
        "icon": "bi-cash-coin",
        "enabled": True,
        "areas": ("accounting.", "time_entry.", "payroll_time.", "receipts_office."),
    },
)

MORE_LINK = {
    "title": MORE_NAV_TITLE,
    "endpoint": "main.more",
    "icon": "bi-grid-3x3-gap",
    "enabled": True,
}

NAV_SECTIONS = (
    {"title": None, "links": PRIMARY_NAV},
    {"title": None, "links": (MORE_LINK,), "class": "sidebar-more"},
)

# ---------------------------------------------------------------------------------------------- More (reference)
MORE_SECTIONS = (
    {
        "title": CALCULATORS_SECTION_TITLE,
        "key": "calculators",
        "why": "Quantities for a job. On a project, open the calculator from the work item so the result goes "
               "straight to that estimate.",
        "links": (
            {"title": "Concrete calculator", "endpoint": "calculators.concrete", "icon": "bi-calculator", "enabled": True},
            {"title": "Stair calculator", "endpoint": "calculators.stairs", "icon": "bi-bar-chart-steps", "enabled": True},
            {"title": "ICF wall calculator", "endpoint": "calculators.wall_form", "icon": "bi-bricks", "enabled": True},
            {"title": "Employment vs Entrepreneurship", "endpoint": "calculators.employment_vs_entrepreneurship",
             "icon": "bi-briefcase", "enabled": True},
            {"title": "Wall framing calculator", "endpoint": "calculators.wall_framing", "icon": "bi-columns", "enabled": True},
            {"title": "Footing calculator", "endpoint": "calculators.footing", "icon": "bi-bounding-box", "enabled": True},
            {"title": "Roofing calculator", "endpoint": "calculators.roofing", "icon": "bi-house", "enabled": True},
            {"title": "Siding calculator", "endpoint": "calculators.siding", "icon": "bi-grid-3x3", "enabled": True},
            {"title": "Drywall calculator", "endpoint": "calculators.drywall", "icon": "bi-square", "enabled": True},
            {"title": "Flooring calculator", "endpoint": "calculators.flooring", "icon": "bi-grid", "enabled": True},
        ),
    },
    {
        "title": COSTS_AND_PRICING_NAV_TITLE,
        "key": "costs",
        "endpoint": "costs_and_pricing.index",
        "why": "What the company pays for materials and work it reuses.",
        "links": (
            {"title": WHAT_WE_PAY_NAV_TITLE, "endpoint": "cost_library.list_cost_items", "icon": "bi-box-seam",
             "enabled": True},
            {"title": REUSABLE_WORK_NAV_TITLE, "endpoint": "assemblies.list_assemblies", "icon": "bi-layers",
             "enabled": True},
            {"title": "Materials catalogue", "endpoint": "material_catalogue.list_materials", "icon": "bi-boxes",
             "enabled": True},
        ),
    },
    {
        "title": "Lists",
        "key": "lists",
        "why": "Every record of one kind across all jobs. Day to day, open them from the project or the attention list.",
        "links": (
            {"title": "Estimates", "endpoint": "estimates.list_estimates", "icon": "bi-calculator", "enabled": True},
            {"title": "Proposals", "endpoint": "proposals.list_proposals", "icon": "bi-file-earmark-text", "enabled": True},
            {"title": "Change orders", "endpoint": "project_controls.list_change_orders", "icon": "bi-arrow-left-right",
             "enabled": True},
            {"title": "Extra work", "endpoint": "operations.extra_work", "icon": "bi-plus-square", "enabled": True},
            {"title": "Job updates", "endpoint": "operations.job_updates", "icon": "bi-chat-square-text",
             "enabled": True},
        ),
    },
    {
        "title": COMPANY_LIBRARY_NAV_TITLE,
        "key": "library",
        "why": "Finished jobs the company learns from, and the company's documents.",
        "links": (
            {"title": PAST_JOBS_NAV_TITLE, "endpoint": "historical_estimates.index", "icon": "bi-archive",
             "enabled": True},
            # Company documents (RDIMS, 31 Oct 2026). Keep the endpoint name stable: documents.library.
            {"title": "Documents", "endpoint": "documents.library", "icon": "bi-folder2-open", "enabled": True},
        ),
    },
    {
        "title": "Business tools",
        "key": "business",
        "why": "Decisions about the business, not one job.",
        "links": (
            {"title": "Decision tools", "endpoint": "decision_tools.decision_tools_index", "icon": "bi-signpost",
             "enabled": True},
            {"title": "Supplier economics", "endpoint": "supplier_program.economic_model", "icon": "bi-graph-up",
             "enabled": True},
        ),
    },
    {
        "title": "Help",
        "key": "help",
        "why": "How Calibrayt works, step by step.",
        "links": (
            {"title": "Getting started", "endpoint": "getting_started.index", "icon": "bi-list-check", "enabled": True},
            # Joel, 21 Oct 2026: the Contractor Workflow Map (app/workflow_map).
            {"title": "Workflow Guide", "endpoint": "workflow_map.contractor", "icon": "bi-signpost-split",
             "enabled": True},
        ),
    },
)

# ---------------------------------------------------------------------------------------------- Admin (the gear)
ADMIN_SECTIONS = (
    {
        "title": "Company",
        "key": "company",
        "links": (
            {"title": "Company profile", "endpoint": "settings.brand_profile", "icon": "bi-building", "enabled": True},
            {
                "title": "People & Access",
                "endpoint": "people_access.index",
                "icon": "bi-person-badge",
                "enabled": True,
                # Shown only to the owner or a System Administrator (app/shell.py); the page refuses everyone else.
                "requires_people_admin": True,
            },
            {"title": "Crews", "endpoint": "organization_crew.index", "icon": "bi-people-fill", "enabled": True},
            {"title": "Hours policy", "endpoint": "payroll_time.hours_policy", "icon": "bi-clock-history",
             "enabled": True},
            {"title": "Text messages", "endpoint": "supplier_office.text_settings", "icon": "bi-chat-dots",
             "enabled": True},
            {"title": "Crew text notices", "endpoint": "sms_notifications.office_notices", "icon": "bi-phone",
             "enabled": True},
            {"title": "Calendar feed", "endpoint": "schedule.calendar_feed_settings", "icon": "bi-calendar-check",
             "enabled": True},
            {"title": "End-of-day reminders", "endpoint": "operations.reminders", "icon": "bi-alarm", "enabled": True},
        ),
    },
    {
        "title": "Pricing and documents",
        "key": "pricing",
        "links": (
            {"title": HOW_WE_PRICE_NAV_TITLE, "endpoint": "pricing_engine.index", "icon": "bi-percent", "enabled": True},
            {"title": "Labour rates", "endpoint": "labour_engine.index", "icon": "bi-person-gear", "enabled": True},
            {"title": DOCUMENT_TEMPLATES_NAV_TITLE, "endpoint": "proposal_templates.list_templates",
             "icon": "bi-file-earmark-richtext", "enabled": True},
            {"title": WORK_CATALOG_NAV_TITLE, "endpoint": "work_structure.catalog_index", "icon": "bi-diagram-3",
             "enabled": True},
        ),
    },
)

# ---------------------------------------------------------------------------------------------- landing pages
# The Purchasing and Time & Money destinations (main.purchasing, main.time_and_money) open a Task Screen whose
# lower half lists every page of that area.
PURCHASING_LINKS = (
    {"title": "Suppliers", "endpoint": "supplier_office.suppliers", "icon": "bi-shop"},
    {"title": "Orders and deliveries", "endpoint": "supplier_office.deliveries", "icon": "bi-truck"},
    {"title": "Material requests from the crew", "endpoint": "operations.material_requests", "icon": "bi-box"},
    {"title": "Deliveries the crew confirmed", "endpoint": "operations.deliveries", "icon": "bi-clipboard-check"},
)
TIME_AND_MONEY_LINKS = (
    {"title": "Approve time", "endpoint": "time_entry.review", "icon": "bi-check2-square"},
    {"title": "Record time", "endpoint": "time_entry.new_entry", "icon": "bi-clock"},
    {"title": "Company time (not on a job)", "endpoint": "payroll_time.company_work", "icon": "bi-briefcase"},
    {"title": "Banked hours", "endpoint": "payroll_time.banked_hours_index", "icon": "bi-piggy-bank"},
    {"title": "Receipts Inbox", "endpoint": "accounting.receipts_inbox", "icon": "bi-receipt"},
    {"title": "Invoices", "endpoint": "accounting.invoices", "icon": "bi-file-earmark-text"},
    {"title": "Accounting", "endpoint": "accounting.index", "icon": "bi-journal-text"},
    {"title": "QuickBooks Online", "endpoint": "accounting.quickbooks_online", "icon": "bi-cloud-arrow-up"},
    {"title": "QuickBooks Time", "endpoint": "payroll_time.quickbooks_time", "icon": "bi-stopwatch"},
    {"title": "Reconcile", "endpoint": "accounting.reconcile", "icon": "bi-arrow-repeat"},
    {"title": "Reconcile time", "endpoint": "accounting.reconcile_time", "icon": "bi-arrow-repeat"},
)


def reachable_endpoints() -> frozenset:
    """Every page a contractor can reach from the shell: sidebar, More (sections and items), Admin, landings."""
    sections = tuple(s.get("endpoint") for s in MORE_SECTIONS + ADMIN_SECTIONS if s.get("endpoint"))
    return frozenset(tuple(i["endpoint"] for i in ALL_NAV_ITEMS) + sections
                     + tuple(i["endpoint"] for i in PURCHASING_LINKS + TIME_AND_MONEY_LINKS))


# Flat lists retained for callers that only need items. NAV_ITEMS: everything a contractor reaches from the
# sidebar (primary + More). ADMIN_ITEMS: the gear. ALL_NAV_ITEMS: both.
NAV_ITEMS = tuple(item for section in NAV_SECTIONS + MORE_SECTIONS for item in section["links"])
ADMIN_ITEMS = tuple(item for section in ADMIN_SECTIONS for item in section["links"])
ALL_NAV_ITEMS = NAV_ITEMS + ADMIN_ITEMS

_MORE_ENDPOINTS = frozenset(item["endpoint"] for section in MORE_SECTIONS for item in section["links"])
_ADMIN_ENDPOINTS = frozenset(item["endpoint"] for item in ADMIN_ITEMS)
_MORE_AREAS = ("calculators.", "cost_library.", "assemblies.", "costs_and_pricing.", "material_catalogue.",
               "historical_estimates.", "decision_tools.", "getting_started.", "workflow_map.", "supplier_program.",
               "calculation_history.")
_ADMIN_AREAS = ("settings.", "people_access.", "organization_crew.", "pricing_engine.", "labour_engine.",
                "proposal_templates.", "work_structure.catalog", "sms_notifications.")


def nav_area(endpoint):
    """'more', 'admin', a primary endpoint, or None: where the page you are on lives."""
    if not endpoint:
        return None
    if endpoint in _ADMIN_ENDPOINTS or endpoint.startswith(_ADMIN_AREAS) or endpoint == "main.admin":
        return "admin"
    if endpoint in _MORE_ENDPOINTS or endpoint.startswith(_MORE_AREAS) or endpoint == "main.more":
        return "more"
    for item in PRIMARY_NAV:
        if endpoint == item["endpoint"]:
            return item["endpoint"]
    # Longest matching area wins (operations.material_request before operations.).
    best, best_len = None, 0
    for item in PRIMARY_NAV:
        for area in item.get("areas", ()):
            if endpoint.startswith(area) and len(area) > best_len:
                best, best_len = item["endpoint"], len(area)
    return best


def is_nav_item_active(item, endpoint):
    if not endpoint or not item.get("endpoint"):
        return False
    target = item["endpoint"]
    if endpoint == target:
        return True
    area = nav_area(endpoint)
    if target == "main.more":
        return area == "more"
    if target == "main.admin":
        return area == "admin"
    return area == target

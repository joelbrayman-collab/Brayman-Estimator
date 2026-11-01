"""Office navigation after Human Experience UAT 2 Waves A and B, reorganised by the Task-First UX (Joel's mandate,
31 Oct 2026): six primary destinations in the sidebar, then More (reference) and the Admin gear (administrative).
The same destinations are asserted below in their new homes; nothing was removed."""

from app.navigation import ADMIN_SECTIONS, MORE_SECTIONS, NAV_SECTIONS

# "Calendar" since 19 Oct 2026 (Joel); Task-First (31 Oct 2026): Home is "Attention", Clients are "Customers", and
# Purchasing and Time & Money join the daily destinations.
PRIMARY_TITLES = ("Attention", "Projects", "Calendar", "Customers", "Purchasing", "Time & Money")
REMOVED_FROM_DAILY_NAV = (
    "Purchase Orders",
    "Job Costing",
    "Reports",
    "AI Assistant",
    "Estimates",
    "Proposals",
    "Schedule",
    "Materials",
    "Labour rates",
    "Cost items",
    "Settings",
    "Brand",
)


def _titles():
    return [
        item["title"]
        for section in NAV_SECTIONS
        for item in section["links"]
    ]


def _endpoints():
    return {
        item["endpoint"]
        for section in NAV_SECTIONS
        for item in section["links"]
    }


def _section(sections, title):
    return next(row for row in sections if row["title"] == title)


def test_daily_navigation_is_the_six_task_first_destinations():
    assert tuple(item["title"] for item in NAV_SECTIONS[0]["links"]) == PRIMARY_TITLES
    assert NAV_SECTIONS[0]["title"] is None
    assert [item["endpoint"] for item in NAV_SECTIONS[1]["links"]] == ["main.more"]


def test_costs_and_pricing_maps_existing_destinations():
    section = _section(MORE_SECTIONS, "Costs & pricing")
    by_title = {item["title"]: item["endpoint"] for item in section["links"]}
    assert section["endpoint"] == "costs_and_pricing.index"
    assert list(by_title) == ["What we pay", "Reusable work", "Materials catalogue"]
    assert by_title["What we pay"] == "cost_library.list_cost_items"
    assert by_title["Reusable work"] == "assemblies.list_assemblies"
    # How we price is company policy: Admin › Pricing and documents.
    pricing = _section(ADMIN_SECTIONS, "Pricing and documents")
    assert {i["title"]: i["endpoint"] for i in pricing["links"]}["How we price"] == "pricing_engine.index"
    assert "material_catalogue.list_materials" not in _endpoints()  # not a daily destination
    assert "labour_engine.index" not in _endpoints()


def test_past_jobs_and_templates_leave_costs_and_pricing():
    costs = _section(MORE_SECTIONS, "Costs & pricing")
    cost_endpoints = {item["endpoint"] for item in costs["links"]}
    assert "historical_estimates.index" not in cost_endpoints
    assert "proposal_templates.list_templates" not in cost_endpoints
    library = _section(MORE_SECTIONS, "Company library")
    assert library["links"][0]["title"] == "Past jobs"
    assert library["links"][0]["endpoint"] == "historical_estimates.index"
    pricing = {i["title"]: i["endpoint"] for i in _section(ADMIN_SECTIONS, "Pricing and documents")["links"]}
    assert pricing["Document templates"] == "proposal_templates.list_templates"


def test_company_setup_is_under_admin_not_a_second_calendar():
    company = _section(ADMIN_SECTIONS, "Company")
    by_title = {item["title"]: item["endpoint"] for item in company["links"]}
    # People & Access added 21 Oct 2026 (shown only to the owner or a System Administrator).
    assert by_title["People & Access"] == "people_access.index"
    assert by_title["Crews"] == "organization_crew.index"
    assert by_title["Company profile"] == "settings.brand_profile"
    pricing = {i["title"]: i["endpoint"] for i in _section(ADMIN_SECTIONS, "Pricing and documents")["links"]}
    assert pricing["Work catalog"] == "work_structure.catalog_index"
    # Workflow Guide (21 Oct 2026) and Getting started are Help, under More.
    help_links = {i["title"]: i["endpoint"] for i in _section(MORE_SECTIONS, "Help")["links"]}
    assert help_links == {"Getting started": "getting_started.index", "Workflow Guide": "workflow_map.contractor"}
    # Suppliers and Accounting are inside the Purchasing and Time & Money destinations.
    from app.navigation import PURCHASING_LINKS, TIME_AND_MONEY_LINKS

    assert "supplier_office.suppliers" in {i["endpoint"] for i in PURCHASING_LINKS}
    assert "accounting.index" in {i["endpoint"] for i in TIME_AND_MONEY_LINKS}
    assert "settings.brand_profile" not in _endpoints()  # the company box and Admin open it, not the sidebar
    assert "schedule.company" not in {item["endpoint"] for item in company["links"]}


def test_unfinished_items_are_not_navigation_peers():
    titles = _titles()
    for label in REMOVED_FROM_DAILY_NAV:
        assert label not in titles
    assert "decision_tools.employment_vs_entrepreneurship" not in _endpoints()
    calculators = {i["endpoint"] for i in _section(MORE_SECTIONS, "Calculators")["links"]}
    assert "calculators.employment_vs_entrepreneurship" in calculators
    assert "estimates.list_estimates" not in _endpoints()
    assert "proposals.list_proposals" not in _endpoints()
    assert "projects.list_projects" in _endpoints()

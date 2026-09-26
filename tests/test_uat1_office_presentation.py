"""Office navigation after Human Experience UAT 2 Waves A and B."""

from app.navigation import NAV_SECTIONS

PRIMARY_TITLES = ("Home", "Company Calendar", "Projects", "Clients")
REMOVED_FROM_DAILY_NAV = (
    "Purchase Orders",
    "Job Costing",
    "Reports",
    "AI Assistant",
    "Employment vs Entrepreneurship",
    "Estimates",
    "Proposals",
    "Schedule",
    "Materials",
    "Labour rates",
    "Cost items",
    "Settings",
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


def test_daily_navigation_is_company_home_calendar_projects_clients():
    assert tuple(item["title"] for item in NAV_SECTIONS[0]["links"]) == PRIMARY_TITLES
    assert NAV_SECTIONS[0]["title"] is None


def test_costs_and_pricing_maps_existing_destinations_without_materials():
    section = next(row for row in NAV_SECTIONS if row["title"] == "Costs & pricing")
    by_title = {item["title"]: item["endpoint"] for item in section["links"]}
    assert list(by_title) == ["What we pay", "Reusable work", "How we price"]
    assert by_title["What we pay"] == "cost_library.list_cost_items"
    assert by_title["Reusable work"] == "assemblies.list_assemblies"
    assert by_title["How we price"] == "pricing_engine.index"
    assert "material_catalogue.list_materials" not in _endpoints()
    assert "labour_engine.index" not in _endpoints()


def test_past_jobs_and_templates_leave_costs_and_pricing():
    costs = next(row for row in NAV_SECTIONS if row["title"] == "Costs & pricing")
    cost_endpoints = {item["endpoint"] for item in costs["links"]}
    assert "historical_estimates.index" not in cost_endpoints
    assert "proposal_templates.list_templates" not in cost_endpoints
    library = next(row for row in NAV_SECTIONS if row["title"] == "Company library")
    assert library["links"][0]["title"] == "Past jobs"
    assert library["links"][0]["endpoint"] == "historical_estimates.index"
    proposals = next(row for row in NAV_SECTIONS if row["title"] == "Proposals")
    assert proposals["links"][0]["title"] == "Templates"
    assert proposals["links"][0]["endpoint"] == "proposal_templates.list_templates"


def test_company_group_is_setup_not_a_second_calendar():
    company = next(row for row in NAV_SECTIONS if row["title"] == "Company")
    by_title = {item["title"]: item["endpoint"] for item in company["links"]}
    assert by_title["Attention"] == "company_attention.index"
    assert by_title["Crews"] == "organization_crew.index"
    assert by_title["Brand"] == "settings.brand_profile"
    assert by_title["Work catalog"] == "work_structure.catalog_index"
    assert "schedule.company" not in {item["endpoint"] for item in company["links"]}


def test_unfinished_items_are_not_navigation_peers():
    titles = _titles()
    for label in REMOVED_FROM_DAILY_NAV:
        assert label not in titles
    assert "decision_tools.employment_vs_entrepreneurship" not in _endpoints()
    assert "estimates.list_estimates" not in _endpoints()
    assert "proposals.list_proposals" not in _endpoints()
    assert "projects.list_projects" in _endpoints()

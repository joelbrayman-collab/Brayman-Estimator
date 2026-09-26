"""UAT 1 office presentation — navigation, Home, Projects, and Estimates."""

from app.navigation import NAV_SECTIONS

PRIMARY_TITLES = ("Home", "Projects", "Estimates", "Proposals", "Schedule")
REMOVED_FROM_DAILY_NAV = (
    "Purchase Orders",
    "Job Costing",
    "Reports",
    "AI Assistant",
    "Employment vs Entrepreneurship",
)


def _titles():
    return [
        item["title"]
        for section in NAV_SECTIONS
        for item in section["links"]
    ]


def test_daily_navigation_is_five_primary_destinations():
    assert tuple(item["title"] for item in NAV_SECTIONS[0]["links"]) == PRIMARY_TITLES
    assert NAV_SECTIONS[0]["title"] is None


def test_assemblies_remain_under_cost_library():
    library = next(section for section in NAV_SECTIONS if section["title"] == "Cost library")
    titles = [item["title"] for item in library["links"]]
    assert "Assemblies" in titles
    assert "Cost items" in titles
    assert titles.index("Assemblies") > titles.index("Cost items")
    assemblies = next(item for item in library["links"] if item["title"] == "Assemblies")
    assert assemblies["endpoint"] == "assemblies.list_assemblies"


def test_unfinished_items_are_not_navigation_peers():
    titles = _titles()
    for label in REMOVED_FROM_DAILY_NAV:
        assert label not in titles
    endpoints = {
        item["endpoint"]
        for section in NAV_SECTIONS
        for item in section["links"]
    }
    assert "decision_tools.employment_vs_entrepreneurship" not in endpoints


def test_clients_stay_reachable_outside_the_daily_row():
    company = next(section for section in NAV_SECTIONS if section["title"] == "Company")
    assert any(item["endpoint"] == "clients.list_clients" for item in company["links"])
    assert "Clients" not in [item["title"] for item in NAV_SECTIONS[0]["links"]]

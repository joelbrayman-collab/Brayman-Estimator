"""Reusable contractor-facing Help content authority.

Presentation only. Static copy. No database, CMS, schema, LLM, or mutation.
D1 ships Project Hub topics. D3 ships office topics on the same authority.
Later Voice must consume this module rather than invent a second knowledge base.
Field (D4) remains empty.
"""

from __future__ import annotations

from dataclasses import dataclass

HELP_CONTROL_LABEL = "Help"
WHAT_LABEL = "What is this?"
DO_LABEL = "What should I do here?"
NEXT_LABEL = "What happens next?"
FUTURE_LABEL = "Future"

SURFACE_HUB = "hub"
SURFACE_OFFICE = "office"
SURFACE_FIELD = "field"


@dataclass(frozen=True)
class HelpTopic:
    """One contextual Help topic for a contractor-facing surface."""

    key: str
    title: str
    what: str
    do: str | None = None
    next: str | None = None
    future: bool = False
    surface: str = SURFACE_HUB


HUB_PLAN = HelpTopic(
    key="plan",
    title="PLAN",
    what=(
        "Planning is where you keep the job drawings, site location, and permit "
        "context for this Project."
    ),
    do=(
        "Review the job address, upload plan PDFs, and read the permit report. "
        "A permit report is not municipal approval."
    ),
    next="When the job information is in place, price the work under PRICE.",
)

HUB_PRICE = HelpTopic(
    key="price",
    title="PRICE",
    what="Pricing is where you build and review the estimate for this Project.",
    do=(
        "Open the related estimates, review costing, and keep the customer price "
        "consistent before you issue."
    ),
    next="When the estimate is ready, create or issue a proposal under CONTRACT.",
)

HUB_CONTRACT = HelpTopic(
    key="contract",
    title="CONTRACT",
    what=(
        "Contract is where you see customer proposals and whether a production "
        "contract can be used for this Project."
    ),
    do=(
        "Review related proposals. Production contract generation is not available "
        "yet. This Hub shows whether a production contract can be used, or why it "
        "cannot yet. It does not create a contract."
    ),
    next=(
        "After the customer has committed, run the job from BUILD and compare "
        "estimated versus actual under MONITOR."
    ),
)

HUB_BUILD = HelpTopic(
    key="build",
    title="BUILD",
    what=(
        "Build is the working job: project work, schedule, time, Punch List, "
        "client Final Walkthrough, Change Orders, and field observations."
    ),
    do=(
        "Keep the work list current, record time, and use the Punch List for "
        "unfinished physical work. Invite the client to Final Walkthrough when "
        "you are near completion. Client comments are not the Punch List until "
        "you accept them."
    ),
    next=(
        "Use MONITOR to compare estimated versus actual. Closing the Project is a "
        "separate office action."
    ),
)

HUB_MONITOR = HelpTopic(
    key="monitor",
    title="MONITOR",
    what=(
        "Monitor compares the committed estimate to actual direct costs recorded "
        "in the office. It is not a profit figure."
    ),
    do=(
        "Follow the What / Why / Next messages already on this section. Record "
        "actual direct costs when they are known. Field observations stay evidence "
        "only."
    ),
    next=(
        "Keep recording actuals as the job proceeds. LEARN is not available on "
        "this Project yet."
    ),
)

HUB_LEARN = HelpTopic(
    key="learn",
    title="LEARN",
    what=(
        "LEARN is Future. This Hub does not recommend work, compare past jobs, "
        "or treat historical labour as this Project’s operating data."
    ),
    future=True,
)

HUB_TOPICS: dict[str, HelpTopic] = {
    topic.key: topic
    for topic in (
        HUB_PLAN,
        HUB_PRICE,
        HUB_CONTRACT,
        HUB_BUILD,
        HUB_MONITOR,
        HUB_LEARN,
    )
}

OFFICE_DASHBOARD = HelpTopic(
    key="dashboard",
    title="Dashboard",
    what=(
        "You are on the office home. It is a snapshot of clients, projects, "
        "estimates, and proposals so you can see current work at a glance. It is "
        "not a report and not a score."
    ),
    do=(
        "Open a recent estimate or proposal, or start from Clients and Projects. "
        "Side-menu items marked coming soon are not available."
    ),
    next="Open a current Project to plan, price, and run the job from the Project Hub.",
    surface=SURFACE_OFFICE,
)

OFFICE_CLIENTS = HelpTopic(
    key="clients",
    title="Clients",
    what=(
        "Clients holds the people and companies you build jobs for. A Client "
        "record is not a customer login and is not the Final Walkthrough link."
    ),
    do="Add or review a Client, then create Projects for that Client.",
    next="Open Projects to start or continue a job.",
    surface=SURFACE_OFFICE,
)

OFFICE_PROJECTS_CURRENT = HelpTopic(
    key="projects_current",
    title="Current Projects",
    what=(
        "Current Projects are the jobs you are still operating. This list is not "
        "the CRM status label on a Project."
    ),
    do=(
        "Open a Project Hub to plan, price, contract, and build. Create a new "
        "Project when you have a Client."
    ),
    next="Work from the Project Hub. Closed jobs are on the Closed list.",
    surface=SURFACE_OFFICE,
)

OFFICE_PROJECTS_CLOSED = HelpTopic(
    key="projects_closed",
    title="Closed Projects",
    what=(
        "Closed Projects are jobs that are no longer operating. Their history "
        "stays available. Closed is not the same as the CRM status field."
    ),
    do=(
        "Open a Closed Project to review history. Reopen it before adding new "
        "operational work such as time, Punch List changes, or Change Orders."
    ),
    next=(
        "If the job is active again, reopen it from the Project Hub, then "
        "continue work."
    ),
    surface=SURFACE_OFFICE,
)

OFFICE_SCHEDULE = HelpTopic(
    key="schedule",
    title="Schedule",
    what="Schedule is the company view of planned work dates across Projects.",
    do=(
        "Filter by date or Project, add dates, and open a Project Hub schedule "
        "when you need the job view. Schedule does not move work automatically."
    ),
    next="Keep dates current, then record time against the work.",
    surface=SURFACE_OFFICE,
)

OFFICE_COMPANY_ATTENTION = HelpTopic(
    key="company_attention",
    title="Company Attention",
    what=(
        "Company Attention answers: where does my business need attention? It "
        "gathers current Project attention facts in one place."
    ),
    do=(
        "Read the warnings and open Review to go to the related Project. "
        "Warnings inform. You decide what to do. This page does not assign a score."
    ),
    next="Open the Project it points to and handle the work there.",
    surface=SURFACE_OFFICE,
)

OFFICE_ESTIMATING = HelpTopic(
    key="estimating",
    title="Estimates",
    what=(
        "Estimates is the office list of current job estimates. This is live "
        "estimating, not Previous estimates."
    ),
    do=(
        "Open an estimate to review costing and Gross Margin Pricing. Pricing "
        "recorded and Labour rates recorded stay on the related specialist "
        "screens. This list does not change calculations."
    ),
    next=(
        "When the estimate is ready, issue a proposal from the Project Hub "
        "CONTRACT section."
    ),
    surface=SURFACE_OFFICE,
)

OFFICE_PREVIOUS_ESTIMATES = HelpTopic(
    key="previous_estimates",
    title="Previous estimates",
    what=(
        "Previous estimates holds uploaded Excel workbooks from past jobs. "
        "Loaded files are evidence. Some need review. Workbook A–E describes "
        "the layout family."
    ),
    do=(
        "Upload Excel workbooks and review files that need review. Historical "
        "estimate information may inform current work but is not automatically "
        "a current estimate."
    ),
    next=(
        "After a file is loaded, use it as reference. Create a current estimate "
        "from a Project when you are pricing new work."
    ),
    surface=SURFACE_OFFICE,
)

OFFICE_COST_LIBRARY = HelpTopic(
    key="cost_library",
    title="Cost library",
    what=(
        "Cost library stores reusable unit costs for estimating. Stored costs "
        "are not estimate line items, not actual Project costs, and not "
        "accounting."
    ),
    do=(
        "Add or update stored costs, then use them when you build an estimate. "
        "This screen does not create an estimate."
    ),
    next="Open Estimates or a Project Hub PRICE section to apply costs on a live job.",
    surface=SURFACE_OFFICE,
)

OFFICE_SETTINGS_BRAND_PROFILE = HelpTopic(
    key="settings_brand_profile",
    title="Brand Profile",
    what=(
        "Settings currently opens Brand Profile: the names, contact details, "
        "colours, and logo used on customer documents."
    ),
    do=(
        "Update the Brand Profile fields on this screen. This is Brand Profile "
        "only. People & Access and other Settings products are not on this screen."
    ),
    next="Return to the Dashboard or a Project when branding is current.",
    surface=SURFACE_OFFICE,
)

OFFICE_PERMIT_REPORT = HelpTopic(
    key="permit_report",
    title="Permit report",
    what=(
        "This permit report is advisory information for the job location. A "
        "passing check does not mean municipal approval. Calibrayt does not "
        "issue permits."
    ),
    do=(
        "Review the job location, create a permit report, and read findings. "
        "Treat municipality and permit office language as guidance only."
    ),
    next=(
        "Confirm requirements with the municipality or permit office. Use the "
        "Project Hub PLAN section to keep drawings and location together."
    ),
    surface=SURFACE_OFFICE,
)

OFFICE_JOB_LOCATION = HelpTopic(
    key="job_location",
    title="Job location",
    what=(
        "Job location is the civic address used for permit context. Saving an "
        "address is not municipal approval."
    ),
    do=(
        "Enter street, municipality, province, and country. Incomplete location "
        "is allowed."
    ),
    next="Create a permit report from PLAN when you want advisory permit information.",
    surface=SURFACE_OFFICE,
)

OFFICE_TIME_REVIEW = HelpTopic(
    key="time_review",
    title="Time",
    what=(
        "Time review is where submitted labour hours are checked. Submitted "
        "time is not approved labour until someone else reviews it."
    ),
    do=(
        "Filter by date, worker, or Project. Record time, then review and "
        "approve when you are authorized. This screen does not show wages or "
        "payroll."
    ),
    next="Keep current hours reviewed so the job record stays accurate.",
    surface=SURFACE_OFFICE,
)

OFFICE_CHANGE_ORDERS = HelpTopic(
    key="change_orders",
    title="Change Orders",
    what=(
        "Change Orders are administrative changes to the contracted work. "
        "Physical work completion is not the same as administrative Change "
        "Order completion."
    ),
    do=(
        "Find, open, or create a Change Order. Completing Punch List items does "
        "not automatically complete a Change Order."
    ),
    next="Keep the Change Order current, then return to the Project Hub BUILD section.",
    surface=SURFACE_OFFICE,
)

OFFICE_TOPICS: dict[str, HelpTopic] = {
    topic.key: topic
    for topic in (
        OFFICE_DASHBOARD,
        OFFICE_CLIENTS,
        OFFICE_PROJECTS_CURRENT,
        OFFICE_PROJECTS_CLOSED,
        OFFICE_SCHEDULE,
        OFFICE_COMPANY_ATTENTION,
        OFFICE_ESTIMATING,
        OFFICE_PREVIOUS_ESTIMATES,
        OFFICE_COST_LIBRARY,
        OFFICE_SETTINGS_BRAND_PROFILE,
        OFFICE_PERMIT_REPORT,
        OFFICE_JOB_LOCATION,
        OFFICE_TIME_REVIEW,
        OFFICE_CHANGE_ORDERS,
    )
}

_SURFACE_TOPICS: dict[str, dict[str, HelpTopic]] = {
    SURFACE_HUB: HUB_TOPICS,
    SURFACE_OFFICE: OFFICE_TOPICS,
    SURFACE_FIELD: {},
}


def hub_topic(key: str) -> HelpTopic:
    """Return one Project Hub Help topic. Fail closed on unknown keys."""
    try:
        return HUB_TOPICS[key]
    except KeyError as exc:
        raise KeyError(f"Unknown Hub Help topic: {key}") from exc


def office_topic(key: str) -> HelpTopic:
    """Return one office Help topic. Fail closed on unknown keys."""
    try:
        return OFFICE_TOPICS[key]
    except KeyError as exc:
        raise KeyError(f"Unknown office Help topic: {key}") from exc


def topic_for_context(surface: str, key: str) -> HelpTopic | None:
    """Return one Help topic or None. Missing Help fails quietly.

    Later Voice must ask this same function. Do not duplicate Help copy elsewhere.
    """
    catalog = _SURFACE_TOPICS.get(surface)
    if catalog is None:
        return None
    return catalog.get(key)


def help_payload(surface: str, key: str) -> dict | None:
    """Reusable Help/context payload for a later Voice interface.

    Voice consumes this authority. It must not create a second knowledge base.
    """
    topic = topic_for_context(surface, key)
    if topic is None:
        return None
    return {
        "surface": topic.surface,
        "key": topic.key,
        "title": topic.title,
        "purpose": topic.what,
        "capability": topic.do,
        "next_step": topic.next,
        "future": topic.future,
    }


def topics_for_surface(surface: str) -> tuple[HelpTopic, ...]:
    """Return Help topics for Hub, office, Field, or unknown surfaces."""
    if surface == SURFACE_HUB:
        return tuple(
            HUB_TOPICS[key]
            for key in ("plan", "price", "contract", "build", "monitor", "learn")
        )
    if surface == SURFACE_OFFICE:
        return tuple(OFFICE_TOPICS.values())
    return ()


def all_help_text() -> str:
    """Concatenated Help copy for governance/language tests."""
    parts: list[str] = []
    for topic in (*HUB_TOPICS.values(), *OFFICE_TOPICS.values()):
        parts.extend(
            part
            for part in (topic.title, topic.what, topic.do, topic.next)
            if part
        )
    return "\n".join(parts)

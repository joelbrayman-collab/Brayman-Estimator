"""Reusable contractor-facing Help content authority.

Presentation only. Static copy. No database, CMS, schema, LLM, or mutation.
D1 ships Project Hub topics. D3 ships office topics. D4 ships Field topics.
D5 Voice is an interface to this same authority via answer_help_question().
Do not invent a second knowledge base.
"""

from __future__ import annotations

from dataclasses import dataclass

HELP_CONTROL_LABEL = "Help"
WHAT_LABEL = "What is this?"
DO_LABEL = "What should I do here?"
NEXT_LABEL = "What happens next?"
FUTURE_LABEL = "Future"
HELP_ASK_LABEL = "Ask about this screen"
HELP_ASK_PLACEHOLDER = "Type a question"
HELP_ASK_BUTTON = "Ask"
HELP_VOICE_LABEL = "Ask by speaking"
HELP_SPEAK_LABEL = "Speak answer"
HELP_STOP_SPEAK_LABEL = "Stop speaking"
HELP_MIC_DENIED = (
    "Microphone access isn't available. You can type your question instead."
)
HELP_MIC_UNSUPPORTED = (
    "Voice isn't available in this browser. You can type your question instead."
)
HELP_NO_SPEECH = "No speech was heard. You can type your question instead."
HELP_VOICE_ERROR = "Voice couldn't be used. You can type your question instead."
HELP_ASK_UNAVAILABLE = (
    "Help couldn't answer right now. You can still read the Help on this screen."
)
HELP_EMPTY_QUESTION = "Type a question about this screen."
HELP_MISSING_CONTEXT = "Help isn't available for this screen."
HELP_GENERIC_REFUSAL = (
    "This Help answers questions about this Calibrayt screen, not general "
    "construction work."
)
HELP_NO_MUTATION = "Help explains. It does not change the job."
HELP_FIELD_ATTENTION = (
    "Company today shows what the company has scheduled today. It does not "
    "change dates. That is not the office Company Attention screen."
)

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
    title="Home",
    what=(
        "You are on Home. It shows where current projects, estimates, and "
        "proposals stand, and it is the place to start a project. "
        "The month schedule lives on Schedule. This is not a report and not a score."
    ),
    do=(
        "Start a project, or open Projects, Estimates, or Proposals. "
        "Open Schedule when you need the calendar."
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

FIELD_TODAY = HelpTopic(
    key="today",
    title="Today",
    what="Today shows the work scheduled for you today.",
    do=(
        "Confirm the Project you are standing on. Capture notes or photos, "
        "enter Time, or record Extra work. This screen does not change dates."
    ),
    next="If nothing is listed, open This week or choose a Project.",
    surface=SURFACE_FIELD,
)

FIELD_WEEK = HelpTopic(
    key="week",
    title="This week",
    what="This week shows your scheduled work for the current week.",
    do="Open a day to see assigned work. Enter Time from a listed job. This view does not move dates.",
    next="Use Today for today’s jobs, or This month for a wider look.",
    surface=SURFACE_FIELD,
)

FIELD_MONTH = HelpTopic(
    key="month",
    title="This month",
    what="This month shows your scheduled work on a calendar.",
    do="Tap a day to see that day’s work. Marks show days with scheduled work. This does not change dates.",
    next="Open Today or a Project when you are ready to capture or enter Time.",
    surface=SURFACE_FIELD,
)

FIELD_COMPANY_TODAY = HelpTopic(
    key="company_today",
    title="Company today",
    what="Company today shows what the company has scheduled today. It does not change dates.",
    do="Review who is planned where. This is a schedule view, not a place to edit dates.",
    next="Your own jobs remain on Today.",
    surface=SURFACE_FIELD,
)

FIELD_PROJECTS = HelpTopic(
    key="projects",
    title="Projects",
    what="Choose the Project you are standing on. Capture and Time apply to that Project.",
    do="Select a current job, then confirm it. Closed jobs are not operated from Field.",
    next="After you confirm, Capture, enter Time, or return to Today.",
    surface=SURFACE_FIELD,
)

FIELD_CAPTURE = HelpTopic(
    key="capture",
    title="Capture",
    what="Capture saves notes, photos, and recordings to this Project’s job record.",
    do="Add a note, take or choose a photo, or record audio, then save. Confirm the Project first.",
    next="Saved observations stay on this Project. Return to Today when you are done.",
    surface=SURFACE_FIELD,
)

FIELD_TIME = HelpTopic(
    key="time",
    title="Time",
    what="Time is where you send hours for the work you did on this Project.",
    do=(
        "Choose the work, enter hours, and send time. Returned time can be fixed "
        "and sent again. This screen records hours only."
    ),
    next="Open My time to see what you sent.",
    surface=SURFACE_FIELD,
)

FIELD_MY_TIME = HelpTopic(
    key="my_time",
    title="My time",
    what="My time lists hours you already sent, including items waiting or returned.",
    do="Open Time to send more hours. Fix returned items and send again.",
    next="Return to Today when you are done.",
    surface=SURFACE_FIELD,
)

FIELD_EXTRA_WORK = HelpTopic(
    key="extra_work",
    title="Extra work",
    what="Extra work records something the customer asked for that is not already on this Project.",
    do="Describe the request. You may attach it to an existing work item or name a new one.",
    next="Extra work is recorded on this Project. Time is entered separately.",
    surface=SURFACE_FIELD,
)

FIELD_TOPICS: dict[str, HelpTopic] = {
    topic.key: topic
    for topic in (
        FIELD_TODAY,
        FIELD_WEEK,
        FIELD_MONTH,
        FIELD_COMPANY_TODAY,
        FIELD_PROJECTS,
        FIELD_CAPTURE,
        FIELD_TIME,
        FIELD_MY_TIME,
        FIELD_EXTRA_WORK,
    )
}

_SURFACE_TOPICS: dict[str, dict[str, HelpTopic]] = {
    SURFACE_HUB: HUB_TOPICS,
    SURFACE_OFFICE: OFFICE_TOPICS,
    SURFACE_FIELD: FIELD_TOPICS,
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


def field_topic(key: str) -> HelpTopic:
    """Return one Field Help topic. Fail closed on unknown keys."""
    try:
        return FIELD_TOPICS[key]
    except KeyError as exc:
        raise KeyError(f"Unknown Field Help topic: {key}") from exc


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
    if surface == SURFACE_FIELD:
        return tuple(
            FIELD_TOPICS[key]
            for key in (
                "today",
                "week",
                "month",
                "company_today",
                "projects",
                "capture",
                "time",
                "my_time",
                "extra_work",
            )
        )
    return ()


def all_help_text() -> str:
    """Concatenated Help copy for governance/language tests."""
    parts: list[str] = []
    for topic in (
        *HUB_TOPICS.values(),
        *OFFICE_TOPICS.values(),
        *FIELD_TOPICS.values(),
    ):
        parts.extend(
            part
            for part in (topic.title, topic.what, topic.do, topic.next)
            if part
        )
    return "\n".join(parts)


def _normalize_question(question: str) -> str:
    return " ".join((question or "").lower().split())


def _question_intent(normalized: str) -> str:
    if not normalized:
        return "empty"
    if "company attention" in normalized:
        return "company_attention"
    if "close" in normalized and "project" in normalized:
        return "close_project"
    if "reopen" in normalized and "project" in normalized:
        return "reopen_project"
    if "approve" in normalized and "time" in normalized:
        return "approve_time"
    if "punch list" in normalized and any(
        word in normalized for word in ("add", "create", "complete")
    ):
        return "punch"
    if "walkthrough" in normalized and any(
        word in normalized for word in ("send", "invite", "create")
    ):
        return "walkthrough"
    if any(
        phrase in normalized
        for phrase in ("how do i frame", "how to frame", "pour concrete", "build a wall")
    ):
        return "generic"
    if any(
        phrase in normalized
        for phrase in ("why can't", "why cant", "why can i not", "blocked", "not allowed")
    ):
        return "why"
    if any(
        phrase in normalized
        for phrase in ("what next", "what should i do next", "what happens next", "do next")
    ):
        return "next"
    if any(
        phrase in normalized
        for phrase in ("what can i do", "what do i do", "how do i", "how can i")
    ):
        return "do"
    if any(
        phrase in normalized
        for phrase in ("what is this", "what's this", "what is this screen", "what does this")
    ):
        return "what"
    if "learn" in normalized:
        return "learn"
    if "completion sign-off" in normalized or "completion sign off" in normalized:
        return "sign_off"
    if "people & access" in normalized or "people and access" in normalized:
        return "people_access"
    return "grounded"


def answer_help_question(surface: str, key: str, question: str) -> dict:
    """Bounded Help question layer. Voice and typed questions share this path.

    Grounded in help_payload() only. Does not mutate product state.
    Does not call a provider. Does not create a second knowledge base.
    """
    normalized = _normalize_question(question)
    intent = _question_intent(normalized)
    payload = help_payload(surface, key)
    result = {
        "surface": surface,
        "key": key,
        "title": None if payload is None else payload["title"],
        "intent": intent,
        "mutates": False,
        "answer": HELP_MISSING_CONTEXT,
    }
    if intent == "empty":
        result["answer"] = HELP_EMPTY_QUESTION
        return result
    if payload is None:
        return result
    purpose = payload["purpose"] or ""
    capability = payload["capability"] or ""
    next_step = payload["next_step"] or ""
    future = bool(payload["future"])

    if surface == SURFACE_FIELD and intent == "company_attention":
        result["answer"] = HELP_FIELD_ATTENTION
        return result

    if intent == "close_project":
        result["answer"] = (
            f"{next_step or purpose} Help does not close a Project. {HELP_NO_MUTATION}"
        )
        return result
    if intent == "reopen_project":
        result["answer"] = (
            f"{capability or purpose} Help does not reopen a Project. {HELP_NO_MUTATION}"
        )
        return result
    if intent == "approve_time":
        result["answer"] = (
            f"{capability or purpose} Help does not approve Time. {HELP_NO_MUTATION}"
        )
        return result
    if intent == "punch":
        result["answer"] = (
            f"{capability or purpose} Help does not add or complete Punch List "
            f"items. {HELP_NO_MUTATION}"
        )
        return result
    if intent == "walkthrough":
        result["answer"] = (
            f"{capability or purpose} Help does not send Final Walkthrough. "
            f"{HELP_NO_MUTATION}"
        )
        return result
    if intent == "learn":
        if future or key == "learn":
            result["answer"] = purpose
        else:
            result["answer"] = "LEARN is not available on this screen yet."
        return result
    if intent == "sign_off":
        result["answer"] = "Project Completion Sign-Off is not on this screen."
        return result
    if intent == "people_access":
        if "People & Access" in f"{purpose} {capability} {next_step}":
            result["answer"] = capability or purpose
        else:
            result["answer"] = "People & Access is not on this screen."
        return result
    if intent == "generic":
        result["answer"] = HELP_GENERIC_REFUSAL
        return result
    if intent == "what" or "what does" in normalized:
        result["answer"] = purpose
        return result
    if intent == "do":
        result["answer"] = capability or purpose
        return result
    if intent == "why":
        result["answer"] = capability or purpose
        return result
    if intent == "next":
        result["answer"] = next_step or purpose
        return result
    if future:
        result["answer"] = purpose
        return result
    result["answer"] = " ".join(part for part in (purpose, next_step) if part)
    return result
